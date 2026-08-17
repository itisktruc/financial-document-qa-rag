from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from .block_detector import BlockDetector
from .cleaner import CleaningConfig, CleaningStats, OCRCleaner
from .diacritic_corrector import (
    DiacriticCorrector,
    DiacriticCorrectorConfig,
    DiacriticStats,
)
from .header_footer import HeaderFooterDetector
from .heading_detector import HeadingDetector
from .metadata import MetadataExtractor
from .models import Document
from .parser import PageParser
from .quality import QualityScorecard, build_scorecard

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineConfig:
    """All tunables for a pipeline run, grouped in one picklable object so
    a pipeline can be reconstructed identically inside a worker process.
    """

    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    diacritic: DiacriticCorrectorConfig = field(default_factory=DiacriticCorrectorConfig)
    header_footer_zone_lines: int = 5
    header_footer_min_frequency_ratio: float = 0.3
    header_footer_min_page_count: int = 3
    caps_title_max_words: int = 10
    cover_page_scan_limit: int = 3
    require_page_markers: bool = True
    # When True, attach a QualityScorecard to Document.quality.
    collect_quality_scorecard: bool = True
    remove_headers_footers: bool = False


class DocumentPreprocessingPipeline:
    """Runs the full preprocessing pipeline over one document's raw OCR
    text and returns a structured :class:`Document`.

    Steps
    -----
    1. Parse ``===== PAGE N =====`` markers into :class:`Page` objects
    2. Detect & strip repeating headers/footers
    3. OCR cleaning (Unicode NFC, CJK/LaTeX, garbage, watermarks, ...)
    4. Vietnamese diacritic / common-OCR-spelling correction
       (tables + numeric tokens protected)
    5-7. Block detection, heading hierarchy, cross-page table merge
    8. Metadata extraction + section assignment
    9. Quality scorecard + structured :class:`Document` assembly
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()
        self._page_parser = PageParser(require_markers=self.config.require_page_markers)
        self._header_footer_detector = HeaderFooterDetector(
            zone_lines=self.config.header_footer_zone_lines,
            min_frequency_ratio=self.config.header_footer_min_frequency_ratio,
            min_page_count_for_detection=self.config.header_footer_min_page_count,
        )
        self._cleaner = OCRCleaner(config=self.config.cleaning)
        self._diacritic_corrector = DiacriticCorrector(config=self.config.diacritic)
        self._metadata_extractor = MetadataExtractor(
            cover_page_scan_limit=self.config.cover_page_scan_limit
        )

    def process_text(self, raw_text: str, source_file: str | None = None) -> Document:
        """Run the full pipeline over already-loaded OCR text."""
        # --- Step 1: parse pages -------------------------------------------------
        pages = self._page_parser.parse(raw_text)
        logger.info("[%s] Step 1/9: parsed %d page(s).", source_file, len(pages))

        # --- Step 2: header/footer detection & removal ---------------------------
        hf_result = self._header_footer_detector.detect(pages)
        if self.config.remove_headers_footers:
            pages = self._header_footer_detector.remove(pages, hf_result)
            logger.info(
                "[%s] Step 2/9: removed %d header line(s), %d footer line(s).",
                source_file,
                hf_result.removed_header_lines,
                hf_result.removed_footer_lines,
            )
        else:
            logger.info("[%s] Step 2/9: header/footer removal disabled.", source_file)

        # --- Step 3: OCR cleaning -------------------------------------------------
        total_cleaning_stats = CleaningStats()
        cleaned_pages = []
        for page in pages:
            cleaned_text, stats = self._cleaner.clean(page.text)
            total_cleaning_stats += stats
            cleaned_pages.append(
                type(page)(
                    page_number=page.page_number,
                    raw_text=page.raw_text,
                    text=cleaned_text,
                )
            )
        pages = cleaned_pages
        artifacts_removed = (
            total_cleaning_stats.artifact_chars_removed
            + total_cleaning_stats.watermark_lines_removed
            + total_cleaning_stats.garbage_lines_removed
            + total_cleaning_stats.duplicate_consecutive_lines_removed
            + total_cleaning_stats.symbol_noise_lines_removed
            + total_cleaning_stats.gibberish_lines_removed
        )
        logger.info(
            "[%s] Step 3/9: cleaned OCR text (%d artifact chars, %d CJK "
            "stamp/seal chars, %d watermark lines, %d garbage lines, %d "
            "symbol-noise lines, %d gibberish lines, %d duplicate lines "
            "removed; %d punctuation runs collapsed; %d OCR artifacts "
            "removed in total).",
            source_file,
            total_cleaning_stats.artifact_chars_removed,
            total_cleaning_stats.cjk_chars_removed,
            total_cleaning_stats.watermark_lines_removed,
            total_cleaning_stats.garbage_lines_removed,
            total_cleaning_stats.symbol_noise_lines_removed,
            total_cleaning_stats.gibberish_lines_removed,
            total_cleaning_stats.duplicate_consecutive_lines_removed,
            total_cleaning_stats.punctuation_runs_collapsed,
            artifacts_removed,
        )

        # --- Step 4: diacritic / spelling correction -----------------------------
        total_diacritic_stats = DiacriticStats()
        if self.config.diacritic.enabled:
            corrected_pages = []
            for page in pages:
                corrected_text, d_stats = self._diacritic_corrector.correct(page.text)
                total_diacritic_stats += d_stats
                corrected_pages.append(
                    type(page)(
                        page_number=page.page_number,
                        raw_text=page.raw_text,
                        text=corrected_text,
                    )
                )
            pages = corrected_pages
            logger.info(
                "[%s] Step 4/9: diacritic correction "
                "(%d phrase(s), %d token(s) corrected; %d numeric token(s) protected).",
                source_file,
                total_diacritic_stats.phrases_corrected,
                total_diacritic_stats.tokens_corrected,
                total_diacritic_stats.numbers_protected,
            )
        else:
            logger.info("[%s] Step 4/9: diacritic correction disabled.", source_file)

        # --- Steps 5-7: block detection, heading hierarchy, cross-page merge -----
        heading_detector = HeadingDetector(
            caps_title_max_words=self.config.caps_title_max_words
        )
        block_detector = BlockDetector(heading_detector=heading_detector)
        block_detector.reset()  # fresh per-document state (see module docstring)

        all_blocks = []
        for page in pages:
            all_blocks.extend(block_detector.detect_blocks(page))
        trailing_table = block_detector.flush_pending()
        if trailing_table is not None:
            all_blocks.append(trailing_table)
        logger.info(
            "[%s] Steps 5-7/9: detected %d block(s) after cross-page merge.",
            source_file,
            len(all_blocks),
        )

        for i, block in enumerate(all_blocks):
            block.order_index = i
            #self._dump_blocks_around_keywords(all_blocks, source_file)

        # --- Step 8: metadata extraction ------------------------------------------
        doc_metadata = self._metadata_extractor.extract_document_metadata(
            pages, hf_result, source_file=source_file
        )
        self._metadata_extractor.assign_block_sections(all_blocks)
        logger.info(
            "[%s] Step 8/9: metadata extracted (company_name=%r, report_year=%r).",
            source_file,
            doc_metadata.company_name,
            doc_metadata.report_year,
        )

        # --- Step 9: quality scorecard + structured output -----------------------
        document = Document(pages=pages, blocks=all_blocks, metadata=doc_metadata)
        if self.config.collect_quality_scorecard:
            scorecard = build_scorecard(
                document,
                cleaning_stats=total_cleaning_stats,
                diacritic_stats=total_diacritic_stats,
            )
            document.quality = scorecard
            logger.info(
                "[%s] Step 9/9: document assembled (%d pages, %d blocks, "
                "overall_risk=%s).",
                source_file,
                len(document.pages),
                len(document.blocks),
                scorecard.overall_risk,
            )
        else:
            logger.info(
                "[%s] Step 9/9: document assembled (%d pages, %d blocks).",
                source_file,
                len(document.pages),
                len(document.blocks),
            )
        return document

    def process_file(self, path: str | Path) -> Document:
        """Read a single OCR ``.txt`` file and process it."""
        path = Path(path)
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        return self.process_text(raw_text, source_file=str(path))

    def process_files_multiprocessing(
        self,
        paths: Iterable[str | Path],
        max_workers: int | None = None,
    ) -> Iterator[Document]:
        """Process many files in parallel worker processes.

        Each worker builds its own :class:`DocumentPreprocessingPipeline`
        from ``self.config`` (which must be picklable — it is, by
        construction) rather than sharing ``self``, avoiding any shared
        mutable state across processes. Results are yielded in the order
        ``paths`` were submitted (via ``executor.map``), not completion
        order, so callers can zip them back against ``paths`` safely.
        """
        str_paths = [str(p) for p in paths]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            yield from executor.map(
                _worker_process_file, str_paths, [self.config] * len(str_paths)
            )


def _worker_process_file(path: str, config: PipelineConfig) -> Document:
    """Module-level function (required for picklability with
    ``ProcessPoolExecutor``) that builds a fresh pipeline in the worker
    process and processes one file.
    """
    pipeline = DocumentPreprocessingPipeline(config=config)
    return pipeline.process_file(path)