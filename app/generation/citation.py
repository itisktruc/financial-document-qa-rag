"""
app/generation/citation.py

Xây dựng object citation (nguồn: công ty/ticker/năm/quý/trang/section) cho
mỗi context chunk dùng trong generation, và format thành nhãn ngắn gọn hiển
thị cho người dùng (vd "[1] FPT - Báo cáo tài chính năm 2024, trang 12").

Dùng chung bởi:
  - app/retrieval/hybrid_search.py     -- gắn citation vào từng context khi
    retrieve() trả về (context giờ là list[dict] thay vì list[str])
  - app/generation/answer_generator.py -- đánh số [1],[2]... vào context gửi
    cho LLM, và trả citations list kèm answer cho main.py
"""

from __future__ import annotations
from typing import Any, Dict, List
#from app.services.embedding_client import parse_document_metadata
import os
import re

# _DOC_TYPE_LABELS = {
#     "BCTC_Nam": "Báo cáo tài chính năm",
#     "BCTC_Quy": "Báo cáo tài chính quý",
#     "BCTN": "Báo cáo thường niên",
# }
def clean_source_filename(raw: str) -> str:
    if not raw:
        return "Tài liệu không tên"
    normalized = str(raw).replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1].strip()
    return name or str(raw)

def build_citation(matched_chunk_id: str, parent_doc: Dict[str, Any]) -> Dict[str, Any]:
    """parent_doc: dict lấy từ get_parent_chunk() (Mongo) -- đã có sẵn
    document_id, section_path, page_start, page_end.

    company/ticker/year/quarter/document_type KHÔNG lưu trực tiếp trên chunk
    (xem app/models/chunk_schema.py) nên suy lại từ document_id qua
    parse_document_metadata() -- ĐÚNG hàm mà embedding_client.to_qdrant_points()
    đã dùng lúc ingest, đảm bảo nhất quán giữa metadata trong Qdrant payload
    và citation hiển thị ở đây (tránh 2 nơi suy metadata theo 2 cách khác nhau).
    """
    doc_id = parent_doc.get("doc_id", "") or parent_doc.get("_id", "")

    return {
        "chunk_id": matched_chunk_id,
        "parent_id": parent_doc.get("_id"),
        "document_id": doc_id,
        "company": parent_doc.get("company"),
        "ticker": parent_doc.get("ticker"),
        "year": parent_doc.get("year"),
        "quarter": parent_doc.get("quarter"),
        "document_type": parent_doc.get("document_type"),
        "section_path": parent_doc.get("heading_path", []),  # Sửa section_path -> heading_path
        "page_start": parent_doc.get("page_start"),
        "page_end": parent_doc.get("page_end"),
        "source_file": parent_doc.get("source_file"),
    }

def format_citation_label(citation: Dict[str, Any], index: int) -> str:
    """
    Nhãn gọn cho user, ví dụ:
      [1] ACL · 2025 · Trang 13
      [2] ACB · 2025 · Trang 5-6 · I. ĐẶC ĐIỂM HOẠT ĐỘNG
    """
    parts: List[str] = []

    ticker = citation.get("ticker")
    if ticker:
        parts.append(str(ticker).upper())

    year = citation.get("year")
    if year is not None and str(year).strip() != "":
        parts.append(str(year))

    # Trang
    p_start = citation.get("page_start")
    p_end = citation.get("page_end")
    if p_start and p_end:
        page_str = f"Trang {p_start}" if p_start == p_end else f"Trang {p_start}-{p_end}"
    elif p_start:
        page_str = f"Trang {p_start}"
    else:
        page_str = None
    if page_str:
        parts.append(page_str)

    # Section ngắn (lấy phần cuối heading_path hoặc section)
    section = citation.get("section") or citation.get("section_path")
    if isinstance(section, list) and section:
        section_str = str(section[-1]).strip()  # chỉ mục gần nhất
    elif isinstance(section, str) and section.strip():
        section_str = section.strip()
    else:
        section_str = None
    if section_str and len(section_str) <= 60:
        parts.append(section_str)

    body = " · ".join(parts) if parts else "Nguồn không rõ"
    return f"[{index}] {body}"

def format_citations_footer(citations: List[Dict[str, Any]]) -> str:
    """Tạo khối Nguồn tham khảo nối vào cuối câu trả lời."""
    if not citations:
        return ""
    
    lines = ["\n\n---", "**Nguồn tham khảo:**"]
    for c in citations:
        idx = c.get("index", 1)
        label = format_citation_label(c, idx) or c.get("label")
        section = c.get("section") or c.get("section_path")
        section_str = ""
        if isinstance(section, list) and section:
            section_str = f" — *Mục: {' > '.join(section)}*"
        elif isinstance(section, str) and section:
            section_str = f" — *Mục: {section}*"
        lines.append(f"* **{label}**{section_str}")
    return "\n".join(lines)

_CITATION_MARKER_RE = re.compile(r"\[(\d+)\]")

def extract_cited_indices(answer_text: str) -> set[int]:
    """Tìm toàn bộ số thứ tự [n] mà LLM đã chèn THẬT vào câu trả lời."""
    return {int(m) for m in _CITATION_MARKER_RE.findall(answer_text or "")}

def citations_filter(
    citations: List[Dict[str, Any]], answer_text: str
) -> List[Dict[str, Any]]:
    """Chỉ giữ citation có index THỰC SỰ xuất hiện trong answer_text (dạng
    [n]) -- GIỮ NGUYÊN số index gốc để khớp đúng với ký hiệu [n] hiển thị
    trong câu trả lời. Không tìm thấy marker nào (LLM quên chèn) -> fallback
    giữ nguyên toàn bộ, tránh mất nguồn."""
    cited = extract_cited_indices(answer_text)
    if not cited:
        print(f"[Citation] LLM không chèn ký hiệu [n] nào trong câu trả lời, "
              f"giữ nguyên toàn bộ {len(citations)} citation.")
        return citations
    kept_citation = [c for c in citations if c.get("index") in cited]
    print(f"[Citation] LLM trích dẫn được {sorted(cited)} trên tổng {len(citations)} nguồn,"
          f"giữ lại {len(kept_citation)} citation.")
    return kept_citation