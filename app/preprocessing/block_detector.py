from __future__ import annotations

import logging
import re

from .heading_detector import HeadingDetector
from .models import (
    Block,
    HeadingBlock,
    ListBlock,
    ParagraphBlock,
    SignatureBlock,
    TableBlock,
)
from .models import Page

logger = logging.getLogger(__name__)

_TABLE_OPEN_RE = re.compile(r"<table\b", re.IGNORECASE)
_TABLE_CLOSE_RE = re.compile(r"</table\s*>", re.IGNORECASE)

_LIST_ITEM_RE = re.compile(
    r"^\s*(?:[-•*‣▪–]|\(?[a-zđ]\)|\(?[a-zđ]\.)\s+\S", re.IGNORECASE
)

# Vocabulary that marks the signature/sign-off area of a report or note.
# Matched case-insensitively against Vietnamese text; deliberately a fixed
# small list rather than an attempt to "detect signatures" generically,
# since this is genuinely a closed vocabulary in these documents.
_SIGNATURE_KEYWORDS = (
    "người lập biểu",
    "kế toán trưởng",
    "tổng giám đốc",
    "giám đốc",
    "người đại diện theo pháp luật",
    "chữ ký",
    "ký tên",
    "đóng dấu",
    "người lập",
)


# Real signature-block labels are short stand-alone lines ("Kế toán
# trưởng", "Tổng Giám đốc"), not the keyword appearing incidentally inside
# a long sentence ("Ban Giám đốc Công ty ... trân trọng trình bày Báo cáo
# này ..."). Capping word count avoids classifying ordinary prose that
# happens to mention a title as a signature block.
_SIGNATURE_LINE_MAX_WORDS = 8


def _is_signature_line(line: str) -> bool:
    stripped = line.strip()
    if len(stripped.split()) > _SIGNATURE_LINE_MAX_WORDS:
        return False
    lower = stripped.lower()
    return any(kw in lower for kw in _SIGNATURE_KEYWORDS)


def _is_list_item(line: str) -> bool:
    return bool(_LIST_ITEM_RE.match(line))


class _PendingTable:
    __slots__ = ("html", "page_start", "last_page")

    def __init__(self, html: str, page_start: int) -> None:
        self.html = html
        self.page_start = page_start
        self.last_page = page_start


class BlockDetector:
    """Stateful block segmenter — one instance per document (state persists
    across pages for cross-page table merge and heading hierarchy).
    """

    def __init__(self, heading_detector: HeadingDetector | None = None) -> None:
        self.heading_detector = heading_detector or HeadingDetector()
        self._pending_table: _PendingTable | None = None

    def reset(self) -> None:
        """Reset all cross-page state. Call between independent documents."""
        self._pending_table = None
        self.heading_detector.reset_hierarchy()

    def detect_blocks(self, page: Page) -> list[Block]:
        """Detect all blocks on ``page``, given cleaned ``page.text``.

        May return a merged :class:`TableBlock` whose ``page_start`` is an
        earlier page if this page closes a table opened previously; may
        also return an *empty* list if this entire page is consumed by an
        still-unclosed table continuation (nothing to emit yet).
        """
        text = page.text
        blocks: list[Block] = []

        if self._pending_table is not None:
            close_match = _TABLE_CLOSE_RE.search(text)
            if close_match is None:
                # Whole page is still inside the open table; keep buffering.
                self._pending_table.html += "\n" + text
                self._pending_table.last_page = page.page_number
                return blocks
            end = close_match.end()
            self._pending_table.html += "\n" + text[:end]
            blocks.append(
                TableBlock(
                    text=self._pending_table.html,
                    html=self._pending_table.html,
                    page_start=self._pending_table.page_start,
                    page_end=page.page_number,
                    merged=True,
                )
            )
            logger.info(
                "Merged cross-page table: pages %d-%d.",
                self._pending_table.page_start,
                page.page_number,
            )
            text = text[end:]
            self._pending_table = None

        blocks.extend(self._detect_blocks_in_text(text, page.page_number))
        return blocks

    def flush_pending(self) -> Block | None:
        """Call after the last page of a document has been processed.

        If a ``<table>`` was opened but never closed anywhere in the
        document (truncated/corrupted OCR), returns it as an unclosed
        :class:`TableBlock` rather than silently discarding its content —
        every character of the source OCR must end up in some block.
        Returns ``None`` if there is nothing pending.
        """
        if self._pending_table is None:
            return None
        logger.warning(
            "Document ended with an unclosed <table> opened on page %d; "
            "emitting it as-is rather than discarding its content.",
            self._pending_table.page_start,
        )
        block = TableBlock(
            text=self._pending_table.html,
            html=self._pending_table.html,
            page_start=self._pending_table.page_start,
            page_end=self._pending_table.last_page,
            merged=self._pending_table.last_page != self._pending_table.page_start,
        )
        self._pending_table = None
        return block

    def _detect_blocks_in_text(self, text: str, page_number: int) -> list[Block]:
        blocks: list[Block] = []
        pos = 0
        for open_match in _TABLE_OPEN_RE.finditer(text):
            if open_match.start() < pos:
                continue  # inside an already-consumed table span
            close_match = _TABLE_CLOSE_RE.search(text, open_match.end())
            preceding = text[pos : open_match.start()]
            blocks.extend(self._detect_non_table_blocks(preceding, page_number))

            if close_match is None:
                # Table opens but never closes on this page: buffer it for
                # the next page (cross-page merge) and stop processing —
                # any text after an unclosed <table> is assumed to be more
                # table content, not independent prose.
                fragment = text[open_match.start() :]
                self._pending_table = _PendingTable(
                    html=fragment, page_start=page_number
                )
                logger.info(
                    "Table opened but not closed on page %d; deferring for "
                    "cross-page merge.",
                    page_number,
                )
                return blocks

            table_html = text[open_match.start() : close_match.end()]
            blocks.append(
                TableBlock(
                    text=table_html,
                    html=table_html,
                    page_start=page_number,
                    page_end=page_number,
                    merged=False,
                )
            )
            pos = close_match.end()

        blocks.extend(self._detect_non_table_blocks(text[pos:], page_number))
        return blocks
    def _detect_non_table_blocks(self, text: str, page_number: int) -> list[Block]:
        blocks: list[Block] = []
        para_buffer: list[str] = []
        list_buffer: list[str] = []
        sig_buffer: list[str] = []

        def current_path() -> tuple[str, ...]:
            return self.heading_detector.current_path()

        def flush_paragraph() -> None:
            if para_buffer:
                content = "\n".join(para_buffer).strip()
                if content:
                    path = current_path()
                    blocks.append(
                        ParagraphBlock(
                            text=content,
                            page_start=page_number,
                            page_end=page_number,
                            heading_path=path,
                        )
                    )
                para_buffer.clear()

        def flush_list() -> None:
            if list_buffer:
                content = "\n".join(list_buffer).strip()
                if content:
                    path = current_path()
                    blocks.append(
                        ListBlock(
                            text=content,
                            items=tuple(list_buffer),
                            page_start=page_number,
                            page_end=page_number,
                            heading_path=path,
                        )
                    )
                list_buffer.clear()

        def flush_signature() -> None:
            if sig_buffer:
                content = "\n".join(sig_buffer).strip()
                if content:
                    path = current_path()
                    blocks.append(
                        SignatureBlock(
                            text=content,
                            page_start=page_number,
                            page_end=page_number,
                            heading_path=path,
                        )
                    )
                sig_buffer.clear()

        def flush_all() -> None:
            flush_paragraph()
            flush_list()
            flush_signature()

        for idx, line in enumerate(text.split("\n")):
            if not line.strip():
                flush_all()
                continue

            heading = self.heading_detector.recognize_line(line, idx)
            if heading is not None:
                flush_all()
                path = self.heading_detector.resolve_path(heading)
                blocks.append(
                    HeadingBlock(
                        text=heading.text,
                        level=heading.level,
                        numbering=heading.numbering,
                        page_start=page_number,
                        page_end=page_number,
                        heading_path=path,
                    )
                )
                continue

            if _is_signature_line(line):
                flush_paragraph()
                flush_list()
                sig_buffer.append(line.strip())
                continue

            if _is_list_item(line):
                flush_paragraph()
                flush_signature()
                list_buffer.append(line.strip())
                continue

            flush_list()
            flush_signature()
            para_buffer.append(line)

        flush_all()
        return blocks