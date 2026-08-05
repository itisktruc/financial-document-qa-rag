"""
app/ingestion/chunker.py

Hierarchical Parent-Child Chunking cho tài liệu tài chính tiếng Việt.

Input: dict trả về từ app.ingestion.parser.parse_pdf(), hiện có 2 dạng:
  1) source == "docling_native"  -> có 'markdown' (str), 'tables' (list), 'pages' (int)
  2) source == "paddleocr"       -> có 'pages_text' (dict[int, str]), 'pages' (int)

Thiết kế: cả 2 nhánh đều được chuẩn hoá về một danh sách "blocks" trung
gian (_Block) trước khi chunk, để sau này dễ cắm thêm nguồn OCR/VLM khác
(vd Qwen-VL) mà không phải viết lại logic chunking. Nếu về sau parser.py
xuất thêm field "items" (list các block có kèm số trang thật, lấy từ
docling_document.iterate_items()), chunker sẽ tự ưu tiên dùng field đó để
có citation theo trang chính xác hơn — xem ghi chú ở normalize_parsed_output().
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class ChunkerConfig:
    child_chunk_size: int = 400        # số token xấp xỉ cho mỗi child chunk (dùng để embed)
    child_chunk_overlap: int = 60      # số token overlap giữa 2 child chunk liền kề
    min_chunk_size: int = 15           # đoạn ngắn hơn mức này bị coi là rác (vd mảnh câu vụn khi cắt),
                                        # KHÔNG áp dụng cho parent chỉ có duy nhất 1 đoạn ngắn -> vẫn
                                        # được giữ lại làm child (xem fallback trong build_chunks)
    max_heading_level: int = 4         # từ mức này trở đi (vd #####) không coi là heading thật nữa


# ---------------------------------------------------------------------------
# Data model đầu ra
# ---------------------------------------------------------------------------

class ChunkType(str, Enum):
    PARENT = "parent"          # chunk cấp section, dùng làm ngữ cảnh mở rộng khi generate câu trả lời
    TEXT_CHILD = "text_child"  # đoạn text nhỏ, dùng để embed + retrieve
    TABLE = "table"            # 1 bảng nguyên vẹn, không cắt nhỏ, giữ chính xác số liệu


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    chunk_type: ChunkType
    content: str                       # nội dung hiển thị / trích dẫn, giữ nguyên định dạng gốc
    embedding_text: str                # nội dung dùng để embed (có thêm breadcrumb ngữ cảnh)
    parent_id: Optional[str]
    section_path: list[str]            # breadcrumb heading, vd ["II. BCTC hợp nhất", "2.1 Bảng CĐKT"]
    page_start: Optional[int]
    page_end: Optional[int]
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["chunk_type"] = self.chunk_type.value
        return d


# ---------------------------------------------------------------------------
# Biểu diễn trung gian
# ---------------------------------------------------------------------------

@dataclass
class _Block:
    """Đơn vị trung gian sau khi chuẩn hoá từ bất kỳ nguồn parser nào."""
    kind: str                  # "heading" | "text" | "table"
    text: str                  # markdown/html cho table, plain text cho heading/text
    level: int = 0             # heading level (1 = #, 2 = ##...), 0 nếu không phải heading
    page: Optional[int] = None


# ---------------------------------------------------------------------------
# Đếm token xấp xỉ (không phụ thuộc network / tải model tokenizer)
# ---------------------------------------------------------------------------

def _approx_token_count(text: str) -> int:
    """
    Ước lượng số token cho tiếng Việt + tiếng Anh mà không cần load tokenizer.
    Đếm theo "word-ish" (tách theo khoảng trắng) rồi nhân hệ số an toàn 1.3,
    vì BPE thường tách 1 từ tiếng Việt có dấu thành nhiều hơn 1 token.
    """
    if not text:
        return 0
    words = re.findall(r"\S+", text)
    return max(1, int(len(words) * 1.3))


# ---------------------------------------------------------------------------
# Bước 1: chuẩn hoá output của parser.py -> list[_Block]
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


def _blocks_from_markdown(markdown: str, max_heading_level: int) -> list[_Block]:
    """
    Parse markdown output của docling thành block heading/text/table.
    Bảng markdown (nhiều dòng bắt đầu/kết thúc bằng '|') được gom thành
    1 block "table" duy nhất thay vì bị cắt rời theo từng dòng.

    Hạn chế: docling.export_to_markdown() không kèm số trang theo từng
    đoạn -> page của các block "heading"/"text" sẽ là None ở nhánh này.
    Muốn có trang chính xác, xem gợi ý nâng cấp parser.py ở cuối file.
    """
    blocks: list[_Block] = []
    lines = markdown.splitlines()
    buffer: list[str] = []
    in_table = False

    def flush_text() -> None:
        nonlocal buffer
        text = "\n".join(buffer).strip()
        if text:
            blocks.append(_Block(kind="text", text=text))
        buffer = []

    for line in lines:
        heading_match = _HEADING_RE.match(line)
        is_table_row = bool(_TABLE_ROW_RE.match(line))

        if heading_match:
            if in_table:
                table_text = "\n".join(buffer).strip()
                if table_text:
                    blocks.append(_Block(kind="table", text=table_text))
                buffer = []
                in_table = False
            else:
                flush_text()

            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if level <= max_heading_level:
                blocks.append(_Block(kind="heading", text=title, level=level))
            else:
                # heading quá sâu -> coi như text in đậm, tránh sinh quá nhiều node cha
                buffer.append(f"**{title}**")
            continue

        if is_table_row:
            if not in_table:
                flush_text()
                in_table = True
            buffer.append(line)
            continue
        else:
            if in_table:
                table_text = "\n".join(buffer).strip()
                if table_text:
                    blocks.append(_Block(kind="table", text=table_text))
                buffer = []
                in_table = False

        buffer.append(line)

    if in_table:
        table_text = "\n".join(buffer).strip()
        if table_text:
            blocks.append(_Block(kind="table", text=table_text))
    else:
        flush_text()

    return blocks


def _blocks_from_docling_tables(tables: Iterable[Any]) -> list[_Block]:
    """
    Tuỳ chọn: dùng list `tables` (docling TableItem, từ result.document.tables)
    thay cho bảng markdown đã nhúng sẵn trong text — hữu ích khi cần giữ
    HTML table (merged cell chính xác hơn markdown thuần). Hiện KHÔNG được
    gọi mặc định trong normalize_parsed_output() để tránh trùng lặp bảng
    với bảng đã có trong markdown; bật lên nếu đổi export mode của parser.
    """
    blocks: list[_Block] = []
    for t in tables or []:
        text = None
        for attr in ("export_to_markdown", "export_to_html"):
            fn = getattr(t, attr, None)
            if callable(fn):
                try:
                    text = fn()
                    break
                except Exception:
                    continue
        if text is None:
            text = str(t)
        page = None
        prov = getattr(t, "prov", None)
        if prov:
            try:
                page = prov[0].page_no
            except Exception:
                page = None
        blocks.append(_Block(kind="table", text=text, page=page))
    return blocks


def _sorted_page_keys(pages: dict) -> list:
    """
    Trả về key trang đã sort ĐÚNG theo số, bất kể dict đang có key là int
    (gọi trực tiếp từ parser.py) hay str (sau khi round-trip qua JSON/Mongo,
    vốn luôn ép key dict về string) -- tránh bug "10" đứng trước "2" nếu
    sort thẳng theo string.
    """
    return sorted(pages.keys(), key=lambda k: int(k))


def _blocks_from_paddleocr_pages(pages_text: dict) -> list[_Block]:
    """
    Nhánh OCR hiện tại chỉ có text thô theo từng trang, KHÔNG có heading
    structure đáng tin cậy. Mỗi trang được coi là 1 "heading" (page marker)
    để breadcrumb/citation vẫn có ngữ cảnh trang, text trang đó là 1 block
    con bên dưới. Khi đổi sang VLM khác có structure tốt hơn, chỉ cần thêm
    1 hàm _blocks_from_xxx() mới và nhánh trong normalize_parsed_output().
    """
    blocks: list[_Block] = []
    for page_key in _sorted_page_keys(pages_text):
        page_num = int(page_key)
        text = (pages_text[page_key] or "").strip()
        if not text:
            continue
        blocks.append(_Block(kind="heading", text=f"Trang {page_num}", level=1, page=page_num))
        blocks.append(_Block(kind="text", text=text, page=page_num))
    return blocks


def _blocks_from_pages_markdown(pages_markdown: dict, max_heading_level: int) -> list[_Block]:
    """
    Nhánh Qwen3-VL (OCR bằng VLM): mỗi trang trả về 1 chuỗi markdown RIÊNG
    (có thể có heading/bảng do model tự nhận diện), khác với nhánh docling
    vốn gộp cả file thành 1 markdown duy nhất.

    Parse từng trang bằng đúng logic _blocks_from_markdown() rồi gắn số
    trang thật cho MỌI block sinh ra từ trang đó -- đây là điểm khác biệt
    quan trọng so với nhánh docling_native (không có số trang theo đoạn),
    nên nhánh OCR bằng VLM cho citation chính xác hơn cả nhánh text-layer
    hiện tại.

    Lưu ý: nếu 1 bảng bị OCR tách làm 2 vì nó nằm vắt qua 2 trang scan liên
    tiếp, hàm này sẽ tạo ra 2 block "table" riêng biệt (mỗi trang OCR độc
    lập) thay vì 1 bảng liền mạch -- hạn chế cố hữu của việc OCR từng trang.
    """
    blocks: list[_Block] = []
    for page_key in _sorted_page_keys(pages_markdown):
        page_num = int(page_key)
        page_md = (pages_markdown[page_key] or "").strip()
        if not page_md:
            continue
        page_blocks = _blocks_from_markdown(page_md, max_heading_level)
        for b in page_blocks:
            b.page = page_num
        blocks.extend(page_blocks)
    return blocks


def _blocks_from_items(items: list) -> list[_Block]:
    """Dùng khi parser.py đã xuất sẵn danh sách block có kèm số trang thật."""
    blocks: list[_Block] = []
    for it in items:
        blocks.append(
            _Block(
                kind=it.get("type") or it.get("kind") or "text",
                text=it.get("text", ""),
                level=it.get("level", 0),
                page=it.get("page"),
            )
        )
    return blocks


def normalize_parsed_output(parsed: dict, config: ChunkerConfig) -> list[_Block]:
    """Entry point chuẩn hoá: nhận dict trả về từ parser.parse_pdf()."""
    # Ưu tiên field "items" nếu parser.py đã nâng cấp để trả về block có
    # kèm trang thật (xem gợi ý ở cuối file) -> citation chính xác hơn.
    if parsed.get("items"):
        return _blocks_from_items(parsed["items"])

    source = parsed.get("source")

    if source == "docling_native":
        return _blocks_from_markdown(parsed.get("markdown", ""), config.max_heading_level)

    if source == "qwen_vlm":
        return _blocks_from_pages_markdown(parsed.get("pages_markdown", {}), config.max_heading_level)

    if source == "paddleocr":
        # Giữ lại để tương thích ngược, dù parser.py hiện đã chuyển nhánh
        # OCR sang Qwen3-VL (source="qwen_vlm").
        return _blocks_from_paddleocr_pages(parsed.get("pages_text", {}))

    # Nguồn lạ (vd đổi sang VLM/engine khác nữa sau này) -> đoán theo field
    # có sẵn thay vì raise cứng, để không chặn toàn bộ pipeline.
    if "pages_markdown" in parsed:
        return _blocks_from_pages_markdown(parsed["pages_markdown"], config.max_heading_level)
    if "markdown" in parsed:
        return _blocks_from_markdown(parsed["markdown"], config.max_heading_level)
    if "pages_text" in parsed:
        return _blocks_from_paddleocr_pages(parsed["pages_text"])

    raise ValueError(
        f"Không nhận diện được định dạng parser output (source={source!r}). "
        "Cần field 'items', 'pages_markdown', 'markdown' hoặc 'pages_text'."
    )


# ---------------------------------------------------------------------------
# Bước 2: cắt text dài thành child chunk (theo câu, có overlap)
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?…])\s+|\n{2,}")


def _split_text_into_children(text: str, config: ChunkerConfig) -> list[str]:
    """Cắt 1 đoạn text dài thành các child chunk có overlap, cắt theo ranh
    giới câu để không vỡ câu giữa chừng."""
    text = text.strip()
    if not text:
        return []
    if _approx_token_count(text) <= config.child_chunk_size:
        return [text]

    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _approx_token_count(sentence)

        if current and current_tokens + sentence_tokens > config.child_chunk_size:
            chunks.append(" ".join(current))

            # overlap: giữ lại vài câu cuối làm phần đầu chunk kế tiếp
            overlap_sentences: list[str] = []
            overlap_tokens = 0
            for s in reversed(current):
                t = _approx_token_count(s)
                if overlap_tokens + t > config.child_chunk_overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_tokens += t
            current = overlap_sentences
            current_tokens = overlap_tokens

        current.append(sentence)
        current_tokens += sentence_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks


def _build_table_embedding_text(table_markdown: str, breadcrumb: list[str]) -> str:
    prefix = " > ".join(breadcrumb)
    return f"{prefix}\n{table_markdown}" if prefix else table_markdown


def _build_text_embedding_text(text: str, breadcrumb: list[str]) -> str:
    prefix = " > ".join(breadcrumb)
    return f"{prefix}\n{text}" if prefix else text


def _new_id() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Bước 3: build hierarchical parent-child chunk từ list[_Block]
# ---------------------------------------------------------------------------

def build_chunks(
    blocks: list[_Block],
    document_id: str,
    config: ChunkerConfig,
    extra_metadata: Optional[dict] = None,
) -> list[Chunk]:
    """
    - Mỗi heading mở ra 1 "parent" chunk mới, chứa toàn bộ nội dung dưới
      heading đó cho tới heading cùng cấp/hơn cấp tiếp theo.
    - Trong parent đó, text được cắt thành các "text_child" nhỏ để embed.
    - Table luôn là 1 chunk riêng (type="table"), KHÔNG bị cắt nhỏ, để
      không phá vỡ số liệu — vẫn gắn parent_id + section_path để biết
      bảng thuộc mục nào (quan trọng cho citation + calculation).
    """
    extra_metadata = extra_metadata or {}
    chunks: list[Chunk] = []

    heading_stack: list[tuple[int, str]] = []  # (level, title), dùng build breadcrumb
    current_page: Optional[int] = None

    def section_path() -> list[str]:
        return [title for _, title in heading_stack]

    def open_new_parent(page: Optional[int]) -> Chunk:
        parent = Chunk(
            chunk_id=_new_id(),
            document_id=document_id,
            chunk_type=ChunkType.PARENT,
            content="",
            embedding_text="",
            parent_id=None,
            section_path=section_path(),
            page_start=page,
            page_end=page,
            token_count=0,
            metadata=dict(extra_metadata),
        )
        chunks.append(parent)
        return parent

    # đảm bảo luôn có 1 parent (trường hợp có text trước heading đầu tiên)
    current_parent = open_new_parent(page=None)

    for block in blocks:
        if block.page is not None:
            current_page = block.page

        if block.kind == "heading":
            level = block.level
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, block.text))
            current_parent = open_new_parent(page=current_page)
            continue

        if block.kind == "table":
            table_chunk = Chunk(
                chunk_id=_new_id(),
                document_id=document_id,
                chunk_type=ChunkType.TABLE,
                content=block.text,
                embedding_text=_build_table_embedding_text(block.text, section_path()),
                parent_id=current_parent.chunk_id,
                section_path=section_path(),
                page_start=block.page or current_page,
                page_end=block.page or current_page,
                token_count=_approx_token_count(block.text),
                metadata=dict(extra_metadata),
            )
            chunks.append(table_chunk)
            current_parent.content += f"\n\n[BẢNG]\n{block.text}\n"
            if table_chunk.page_end is not None:
                current_parent.page_end = table_chunk.page_end
            continue

        # block.kind == "text"
        current_parent.content += ("\n\n" if current_parent.content else "") + block.text
        if block.page is not None:
            current_parent.page_end = block.page
            if current_parent.page_start is None:
                current_parent.page_start = block.page

        for child_text in _split_text_into_children(block.text, config):
            if _approx_token_count(child_text) < config.min_chunk_size:
                continue  # đoạn quá ngắn -> đã có sẵn trong nội dung parent, không tách chunk riêng
            chunks.append(
                Chunk(
                    chunk_id=_new_id(),
                    document_id=document_id,
                    chunk_type=ChunkType.TEXT_CHILD,
                    content=child_text,
                    embedding_text=_build_text_embedding_text(child_text, section_path()),
                    parent_id=current_parent.chunk_id,
                    section_path=section_path(),
                    page_start=block.page or current_page,
                    page_end=block.page or current_page,
                    token_count=_approx_token_count(child_text),
                    metadata=dict(extra_metadata),
                )
            )

    for c in chunks:
        if c.chunk_type == ChunkType.PARENT:
            c.token_count = _approx_token_count(c.content)

    # Fallback: đảm bảo mọi parent có nội dung đều có ít nhất 1 child để
    # embed/retrieve. Nếu không, nội dung parent bị min_chunk_size lọc hết
    # (vd 1 trang OCR rất ngắn) sẽ "biến mất" khỏi retrieval dù vẫn còn
    # trong parent.content -- vì pipeline chỉ embed text_child/table, không
    # embed parent trực tiếp (parent chỉ dùng để mở rộng ngữ cảnh sau khi
    # tìm được child/table match).
    parents_with_children = {
        c.parent_id for c in chunks if c.chunk_type in (ChunkType.TEXT_CHILD, ChunkType.TABLE)
    }
    fallback_children: list[Chunk] = []
    for c in chunks:
        if c.chunk_type != ChunkType.PARENT:
            continue
        if c.chunk_id in parents_with_children:
            continue
        if not c.content.strip():
            continue
        fallback_children.append(
            Chunk(
                chunk_id=_new_id(),
                document_id=document_id,
                chunk_type=ChunkType.TEXT_CHILD,
                content=c.content.strip(),
                embedding_text=_build_text_embedding_text(c.content.strip(), c.section_path),
                parent_id=c.chunk_id,
                section_path=c.section_path,
                page_start=c.page_start,
                page_end=c.page_end,
                token_count=_approx_token_count(c.content),
                metadata=dict(extra_metadata),
            )
        )
    chunks.extend(fallback_children)

    # bỏ parent rỗng (vd parent mặc định ban đầu nếu tài liệu bắt đầu ngay bằng heading)
    chunks = [c for c in chunks if not (c.chunk_type == ChunkType.PARENT and not c.content.strip())]

    return chunks


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def chunk_document(
    parsed: dict,
    document_id: str,
    config: Optional[ChunkerConfig] = None,
    extra_metadata: Optional[dict] = None,
) -> list[Chunk]:
    """
    Entry point chính, gọi ngay sau parser.parse_pdf().

        from app.ingestion.parser import parse_pdf
        from app.ingestion.chunker import chunk_document

        parsed = parse_pdf("data/raw/FPT/FPT_BCTC_2024.pdf")
        chunks = chunk_document(
            parsed,
            document_id="FPT_BCTC_2024",
            extra_metadata={"company": "FPT", "ticker": "FPT", "year": 2024},
        )
    """
    config = config or ChunkerConfig()
    blocks = normalize_parsed_output(parsed, config)
    return build_chunks(blocks, document_id=document_id, config=config, extra_metadata=extra_metadata)