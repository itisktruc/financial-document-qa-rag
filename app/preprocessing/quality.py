from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .cleaner import CleaningStats
from .diacritic_corrector import DiacriticStats
from .models import Block, BlockType, Document, Page, TableBlock


@dataclass(slots=True)
class QualityScorecard:
    """Compact, serialisable quality summary for one processed document."""

    page_count: int = 0
    block_count: int = 0
    table_count: int = 0
    heading_count: int = 0
    paragraph_count: int = 0
    list_count: int = 0
    signature_count: int = 0
    merged_table_count: int = 0

    # From OCRCleaner
    artifact_chars_removed: int = 0
    cjk_chars_removed: int = 0
    watermark_lines_removed: int = 0
    garbage_lines_removed: int = 0
    symbol_noise_lines_removed: int = 0
    gibberish_lines_removed: int = 0
    duplicate_lines_removed: int = 0
    punctuation_runs_collapsed: int = 0

    # From DiacriticCorrector
    phrases_corrected: int = 0
    tokens_corrected: int = 0
    numbers_protected: int = 0

    # Derived risk flags (string enums kept simple for Mongo serialisation)
    # "low" | "medium" | "high"
    noise_risk: str = "low"
    diacritic_activity: str = "low"
    structure_risk: str = "low"
    overall_risk: str = "low"


def build_scorecard(
    document: Document,
    cleaning_stats: Optional[CleaningStats] = None,
    diacritic_stats: Optional[DiacriticStats] = None,
) -> QualityScorecard:
    """Assemble a :class:`QualityScorecard` from a finished ``Document``
    plus the optional per-run stats objects produced by earlier pipeline
    stages.
    """
    cs = cleaning_stats or CleaningStats()
    ds = diacritic_stats or DiacriticStats()

    blocks = document.blocks
    type_counts = {
        BlockType.HEADING: 0,
        BlockType.PARAGRAPH: 0,
        BlockType.TABLE: 0,
        BlockType.LIST: 0,
        BlockType.SIGNATURE: 0,
        BlockType.UNKNOWN: 0,
    }
    merged_tables = 0
    for b in blocks:
        type_counts[b.block_type] = type_counts.get(b.block_type, 0) + 1
        if isinstance(b, TableBlock) and b.merged:
            merged_tables += 1

    # --- noise risk: OCR artifact volume relative to page count --------------
    noise_total = (
        cs.gibberish_lines_removed
        + cs.garbage_lines_removed
        + cs.watermark_lines_removed
        + cs.symbol_noise_lines_removed
        + cs.cjk_chars_removed
    )
    pages = max(len(document.pages), 1)
    noise_per_page = noise_total / pages
    if noise_per_page >= 5 or cs.gibberish_lines_removed >= 10:
        noise_risk = "high"
    elif noise_per_page >= 1.5:
        noise_risk = "medium"
    else:
        noise_risk = "low"

    # --- diacritic activity: how much the corrector rewrote ------------------
    diacritic_total = ds.phrases_corrected + ds.tokens_corrected
    if diacritic_total >= 50:
        diacritic_activity = "high"
    elif diacritic_total >= 10:
        diacritic_activity = "medium"
    else:
        diacritic_activity = "low"

    # --- structure risk: empty pages, zero headings, untyped blocks ----------
    empty_pages = sum(1 for p in document.pages if not p.text.strip())
    structure_risk = "low"
    if type_counts.get(BlockType.UNKNOWN, 0) >= 5:
        structure_risk = "high"
    elif empty_pages >= max(2, pages // 5):
        structure_risk = "medium"
    elif type_counts.get(BlockType.HEADING, 0) == 0 and pages >= 5:
        structure_risk = "medium"

    # --- overall: worst of the three -----------------------------------------
    rank = {"low": 0, "medium": 1, "high": 2}
    overall = max(
        (noise_risk, diacritic_activity, structure_risk),
        key=lambda r: rank[r],
    )

    return QualityScorecard(
        page_count=len(document.pages),
        block_count=len(blocks),
        table_count=type_counts.get(BlockType.TABLE, 0),
        heading_count=type_counts.get(BlockType.HEADING, 0),
        paragraph_count=type_counts.get(BlockType.PARAGRAPH, 0),
        list_count=type_counts.get(BlockType.LIST, 0),
        signature_count=type_counts.get(BlockType.SIGNATURE, 0),
        merged_table_count=merged_tables,
        artifact_chars_removed=cs.artifact_chars_removed,
        cjk_chars_removed=cs.cjk_chars_removed,
        watermark_lines_removed=cs.watermark_lines_removed,
        garbage_lines_removed=cs.garbage_lines_removed,
        symbol_noise_lines_removed=cs.symbol_noise_lines_removed,
        gibberish_lines_removed=cs.gibberish_lines_removed,
        duplicate_lines_removed=cs.duplicate_consecutive_lines_removed,
        punctuation_runs_collapsed=cs.punctuation_runs_collapsed,
        phrases_corrected=ds.phrases_corrected,
        tokens_corrected=ds.tokens_corrected,
        numbers_protected=ds.numbers_protected,
        noise_risk=noise_risk,
        diacritic_activity=diacritic_activity,
        structure_risk=structure_risk,
        overall_risk=overall,
    )