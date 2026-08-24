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
from app.services.embedding_client import parse_document_metadata
import os

# _DOC_TYPE_LABELS = {
#     "BCTC_Nam": "Báo cáo tài chính năm",
#     "BCTC_Quy": "Báo cáo tài chính quý",
#     "BCTN": "Báo cáo thường niên",
# }

def build_citation(matched_chunk_id: str, parent_doc: Dict[str, Any]) -> Dict[str, Any]:
    """parent_doc: dict lấy từ get_parent_chunk() (Mongo) -- đã có sẵn
    document_id, section_path, page_start, page_end.

    company/ticker/year/quarter/document_type KHÔNG lưu trực tiếp trên chunk
    (xem app/models/chunk_schema.py) nên suy lại từ document_id qua
    parse_document_metadata() -- ĐÚNG hàm mà embedding_client.to_qdrant_points()
    đã dùng lúc ingest, đảm bảo nhất quán giữa metadata trong Qdrant payload
    và citation hiển thị ở đây (tránh 2 nơi suy metadata theo 2 cách khác nhau).
    """
    # document_id = parent_doc.get("document_id", "") or ""
    # meta = parent_doc.get("metadata", {}) or {}
    # doc_meta = parse_document_metadata(
    #     document_id, meta.get("source_file", ""), ticker_hint=meta.get("ticker")
    #)
    doc_id = parent_doc.get("doc_id", "") or parent_doc.get("_id", "")

    # return {
    #     "chunk_id": matched_chunk_id,
    #     "parent_id": parent_doc.get("_id"),
    #     "document_id": document_id,
    #     "company": doc_meta["company"],
    #     "ticker": doc_meta["ticker"],
    #     "year": doc_meta["year"],
    #     "quarter": doc_meta["quarter"],
    #     "document_type": doc_meta["document_type"],
    #     "section_path": parent_doc.get("section_path", []),
    #     "page_start": parent_doc.get("page_start"),
    #     "page_end": parent_doc.get("page_end"),
    # }
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
    }


def format_citation_label(citation: Dict[str, Any], index: int) -> str:
    """Nhãn ngắn hiển thị cho người dùng, vd:
    '[1] FPT - Báo cáo tài chính năm 2024, trang 12'
    '[2] HPG - Báo cáo tài chính quý 2024 (Q2), trang 5-6'
    '[3] VNM_BCTC_2023 (không rõ loại tài liệu)'  -- fallback khi thiếu metadata
    """
    # parts = []
    # if citation.get("company"):
    #     parts.append(str(citation["company"]))
    # elif citation.get("ticker"):
    #     parts.append(str(citation["ticker"]))

    # doc_label = _DOC_TYPE_LABELS.get(citation.get("document_type"), "")
    # year = citation.get("year")
    # quarter = citation.get("quarter")
    # if doc_label or year:
    #     time_part = doc_label
    #     if year:
    #         time_part = f"{time_part} {year}" if time_part else str(year)
    #     if quarter:
    #         time_part += f" (Q{quarter})"
    #     parts.append(time_part)

    # label = " - ".join(p for p in parts if p) or citation.get("document_id") or "Không rõ nguồn"
    """Tạo nhãn trích dẫn dạng: [1] A32_BaoCaoTaiChinh_2025.pdf (Trang 11)"""
    file_path = citation.get("source_file") or citation.get("doc_id", "Tài liệu không tên")
    file_name = os.path.basename(str(file_path))
    
    # Loại bỏ các hậu tố file tạm nếu có
    file_name = file_name.replace("_extracted.txt", ".pdf")

    p_start = citation.get("page_start")
    p_end = citation.get("page_end")

    if p_start and p_end:
        page_str = f"Trang {p_start}" if p_start == p_end else f"Trang {p_start}-{p_end}"
    elif p_start:
        page_str = f"Trang {p_start}"
    else:
        page_str = "Trang N/A"

    return f"[{index}] {file_name} ({page_str})"


def format_citations_footer(citations: List[Dict[str, Any]]) -> str:
    """Tạo khối Nguồn tham khảo nối vào cuối câu trả lời."""
    if not citations:
        return ""
    
    lines = ["\n\n---", "**Nguồn tham khảo:**"]
    for c in citations:
        idx = c.get("index", 1)
        label = format_citation_label(c, idx)
        section = c.get("section")
        sec_str = f" — *Mục: {section}*" if section else ""
        lines.append(f"* **{label}**{sec_str}")
        
    return "\n".join(lines)