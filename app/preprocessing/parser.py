from __future__ import annotations

import logging
import re
from typing import Iterator

from .models import Page

logger = logging.getLogger(__name__)

# Matches lines like "===== PAGE 12 =====", tolerating extra/missing
# whitespace and varying run lengths of '='.
_PAGE_MARKER_RE = re.compile(
    r"^[ \t]*=+[ \t]*PAGE[ \t]+(\d+)[ \t]*=+[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)


class PageParsingError(ValueError):
    """Raised when the input text contains no recognizable page markers."""


class PageParser:
    """Splits raw OCR text into :class:`Page` objects.

    Parameters
    ----------
    require_markers:
        If True (default), raise :class:`PageParsingError` when no page
        markers are found at all. If False, a markerless document is
        treated as a single page (page 1) — useful for ad-hoc/short inputs.
    """

    def __init__(self, require_markers: bool = True) -> None:
        self.require_markers = require_markers

    def iter_pages(self, raw_text: str) -> Iterator[Page]:
        """Yield :class:`Page` objects in document order.

        Never drops page information: if the OCR emitted a page marker with
        no following content, an empty-text ``Page`` is still yielded so
        page numbering downstream (page_start/page_end on blocks) stays
        accurate even across blank pages.
        """
        matches = list(_PAGE_MARKER_RE.finditer(raw_text))

        if not matches:
            if self.require_markers:
                raise PageParsingError(
                    "No '===== PAGE X =====' markers found in input text."
                )
            logger.warning("No page markers found; treating input as a single page.")
            yield Page(page_number=1, raw_text=raw_text, text=raw_text)
            return

        for i, match in enumerate(matches):
            page_number = int(match.group(1))
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            body = raw_text[start:end].strip("\n")
            yield Page(page_number=page_number, raw_text=body, text=body)

        logger.info("Parsed %d page(s) from OCR text.", len(matches))

    def parse(self, raw_text: str) -> list[Page]:
        """Eagerly parse into a list. Convenience wrapper around
        :meth:`iter_pages` for callers that need random access (most of the
        downstream pipeline does, for cross-page merging).
        """
        return list(self.iter_pages(raw_text))