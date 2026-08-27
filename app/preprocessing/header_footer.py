from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .models import Page

logger = logging.getLogger(__name__)

_DIGIT_RUN_RE = re.compile(r"\d+")
_WS_RE = re.compile(r"\s+")


def _normalize_line(line: str) -> str:
    """Collapse a line to a frequency-comparison key: lowercased, digit runs
    replaced with a placeholder, whitespace collapsed. Two lines that differ
    only by a page number or minor OCR whitespace noise map to the same key.
    """
    key = line.strip().lower()
    key = _DIGIT_RUN_RE.sub("<NUM>", key)
    key = _WS_RE.sub(" ", key)
    return key


@dataclass(slots=True)
class HeaderFooterResult:
    """Outcome of header/footer detection, kept for logging and for callers
    who want to inspect *what* was identified as boilerplate before it was
    stripped.
    """

    header_keys: set[str] = field(default_factory=set)
    footer_keys: set[str] = field(default_factory=set)
    examples: dict[str, str] = field(default_factory=dict)  # key -> sample raw line
    removed_header_lines: int = 0
    removed_footer_lines: int = 0


class HeaderFooterDetector:
    """Detects and strips repeated headers/footers via margin-zone frequency
    analysis.

    Parameters
    ----------
    zone_lines:
        How many lines from the top (header zone) and bottom (footer zone)
        of each page are considered candidates. Financial report letterheads
        and footers are rarely more than a few lines.
    min_frequency_ratio:
        A candidate line must recur (after normalization) on at least this
        fraction of pages to be classified as a header/footer. Defaults to
        0.3 (30%) — deliberately lower than "most pages" because scanned
        reports often have a handful of pages (cover, section dividers)
        with no letterhead at all.
    min_page_count_for_detection:
        Documents with fewer pages than this are too small for frequency
        analysis to be reliable; detection is skipped and pages are
        returned unchanged.
    """

    def __init__(
        self,
        zone_lines: int = 5,
        min_frequency_ratio: float = 0.3,
        min_page_count_for_detection: int = 3,
    ) -> None:
        self.zone_lines = zone_lines
        self.min_frequency_ratio = min_frequency_ratio
        self.min_page_count_for_detection = min_page_count_for_detection

    def detect(self, pages: list[Page]) -> HeaderFooterResult:
        """Analyze margin zones across all pages and return the set of
        normalized keys classified as headers/footers. Does not mutate
        ``pages``.
        """
        result = HeaderFooterResult()
        if len(pages) < self.min_page_count_for_detection:
            logger.info(
                "Only %d page(s); skipping header/footer detection (min=%d).",
                len(pages),
                self.min_page_count_for_detection,
            )
            return result

        header_counts: Counter[str] = Counter()
        footer_counts: Counter[str] = Counter()

        for page in pages:
            lines = page.text.split("\n")
            non_empty = [l for l in lines if l.strip()]
            for line in non_empty[: self.zone_lines]:
                key = _normalize_line(line)
                if key:
                    header_counts[key] += 1
                    result.examples.setdefault(key, line.strip())
            for line in non_empty[-self.zone_lines :]:
                key = _normalize_line(line)
                if key:
                    footer_counts[key] += 1
                    result.examples.setdefault(key, line.strip())

        threshold = max(2, int(len(pages) * self.min_frequency_ratio))

        result.header_keys = {k for k, c in header_counts.items() if c >= threshold}
        result.footer_keys = {k for k, c in footer_counts.items() if c >= threshold}

        logger.info(
            "Header/footer detection: %d header pattern(s), %d footer pattern(s) "
            "found across %d pages (threshold=%d occurrences).",
            len(result.header_keys),
            len(result.footer_keys),
            len(pages),
            threshold,
        )
        return result

    def remove(
        self, pages: list[Page], result: HeaderFooterResult | None = None
    ) -> list[Page]:
        """Return new :class:`Page` objects with detected header/footer
        lines stripped from ``text``. ``raw_text`` is left untouched so the
        original OCR capture is always recoverable. Page metadata
        (page_number) is always preserved even if a page becomes empty.
        """
        if result is None:
            result = self.detect(pages)
        if not result.header_keys and not result.footer_keys:
            return pages

        cleaned_pages: list[Page] = []
        for page in pages:
            lines = page.text.split("\n")
            keep: list[str] = []
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if not stripped:
                    keep.append(line)
                    continue
                key = _normalize_line(line)
                in_header_zone = idx < self.zone_lines
                in_footer_zone = idx >= len(lines) - self.zone_lines
                if in_header_zone and key in result.header_keys:
                    result.removed_header_lines += 1
                    continue
                if in_footer_zone and key in result.footer_keys:
                    result.removed_footer_lines += 1
                    continue
                keep.append(line)
            cleaned_pages.append(
                Page(
                    page_number=page.page_number,
                    raw_text=page.raw_text,
                    text="\n".join(keep).strip("\n"),
                )
            )

        logger.info(
            "Removed %d header line(s) and %d footer line(s) across %d pages.",
            result.removed_header_lines,
            result.removed_footer_lines,
            len(pages),
        )
        return cleaned_pages