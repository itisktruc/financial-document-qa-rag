from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

_SLOTS_SUPPORTED = sys.version_info >= (3, 10)


def _dataclass(*args, **kwargs):
    """Wrapper so every model below opts into slots when available."""
    if _SLOTS_SUPPORTED:
        kwargs.setdefault("slots", True)
    return dataclass(*args, **kwargs)


class BlockType(str, Enum):
    """Enumerates the structural role of a parsed content block."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST = "list"
    SIGNATURE = "signature"
    UNKNOWN = "unknown"


@_dataclass(frozen=True)
class Page:
    """A single OCR page, exactly as delimited by the ``===== PAGE X =====``
    markers. ``raw_text`` is preserved verbatim (pre-cleaning); ``text`` is
    the working copy that later stages mutate/clean. Keeping both means no
    step is destructive to the original OCR capture.
    """

    page_number: int
    raw_text: str
    text: str


@_dataclass
class Block:
    """Base class for a structural unit of content within a page.

    Concrete block kinds (heading, paragraph, table, ...) subclass this to
    add type-specific fields. ``block_type`` is always set so a consumer can
    branch on it without isinstance-checking every subclass.
    """

    text: str
    page_start: int
    page_end: int
    order_index: int = 0  # position within the document's block sequence
    heading_path: tuple[str, ...] = field(default_factory=tuple)
    section: Optional[str] = None
    subsection: Optional[str] = None
    # Defaulted and placed last so concrete subclasses never need to pass
    # it explicitly — each subclass's __post_init__ sets its true value.
    block_type: BlockType = BlockType.UNKNOWN


@_dataclass
class HeadingBlock(Block):
    """A detected heading/title line, with its resolved hierarchy level.

    ``level`` is 1-indexed (1 = top-level heading, e.g. "I."). ``numbering``
    keeps the raw matched numbering token (e.g. "2.1", "III.") for citation
    purposes; it is ``None`` for un-numbered all-caps section titles such as
    "BẢNG CÂN ĐỐI KẾ TOÁN".
    """

    level: int = 1
    numbering: Optional[str] = None

    def __post_init__(self) -> None:
        self.block_type = BlockType.HEADING


@_dataclass
class ParagraphBlock(Block):
    """A body-text paragraph."""

    def __post_init__(self) -> None:
        self.block_type = BlockType.PARAGRAPH


@_dataclass
class ListBlock(Block):
    """A bulleted/numbered list rendered as a single block (items kept
    together rather than split, since financial-note lists are usually
    meant to be read/cited as a unit).
    """

    items: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self.block_type = BlockType.LIST


@_dataclass
class TableBlock(Block):
    """An HTML table, preserved byte-for-byte from the OCR output.

    ``html`` always holds the exact original markup — never re-serialized —
    so no cell content is ever altered by cleaning/normalization. ``merged``
    is True when this table was assembled from a cross-page merge (see
    ``block_detector.merge_cross_page_blocks``).
    """

    html: str = ""
    merged: bool = False

    def __post_init__(self) -> None:
        self.block_type = BlockType.TABLE


@_dataclass
class SignatureBlock(Block):
    """Signature blocks (e.g. "Người lập biểu / Kế toán trưởng / Giám đốc"
    triads with names/dates) — kept distinct from paragraphs since they
    carry no citable financial content and downstream chunkers typically
    want to exclude or specially tag them.
    """

    def __post_init__(self) -> None:
        self.block_type = BlockType.SIGNATURE


@_dataclass
class UnknownBlock(Block):
    """Fallback for content that doesn't match any detector — kept rather
    than dropped, so nothing from the source OCR silently disappears.
    """

    def __post_init__(self) -> None:
        self.block_type = BlockType.UNKNOWN


@_dataclass
class DocumentMetadata:
    """Document-level metadata inferred from the report itself."""

    company_name: Optional[str] = None
    report_year: Optional[int] = None
    source_file: Optional[str] = None
    page_count: int = 0
    detected_headers: tuple[str, ...] = field(default_factory=tuple)
    detected_footers: tuple[str, ...] = field(default_factory=tuple)

@_dataclass
class Document:
    """Top-level container for a fully processed report."""

    pages: list[Page]
    blocks: list[Block]
    metadata: DocumentMetadata
    quality: Optional[object] = None

    def tables(self) -> list[TableBlock]:
        """Convenience accessor: all table blocks, in document order."""
        return [b for b in self.blocks if isinstance(b, TableBlock)]

    def headings(self) -> list[HeadingBlock]:
        """Convenience accessor: all heading blocks, in document order."""
        return [b for b in self.blocks if isinstance(b, HeadingBlock)]