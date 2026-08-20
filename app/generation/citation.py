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
from typing import Any, Dict
from app.services.embedding_client import parse_document_metadata

_DOC_TYPE_LABELS = {
    "BCTC_Nam": "Báo cáo tài chính năm",
    "BCTC_Quy": "Báo cáo tài chính quý",
    "BCTN": "Báo cáo thường niên",
}

def build_citation(matched_chunk_id: str, parent_doc: Dict[str, Any]) -> Dict[str, Any]:
    """parent_doc: dict lấy từ get_parent_chunk() (Mongo) -- đã có sẵn
    document_id, section_path, page_start, page_end.

    company/ticker/year/quarter/document_type KHÔNG lưu trực tiếp trên chunk
    (xem app/models/chunk_schema.py) nên suy lại từ document_id qua
    parse_document_metadata() -- ĐÚNG hàm mà embedding_client.to_qdrant_points()
    đã dùng lúc ingest, đảm bảo nhất quán giữa metadata trong Qdrant payload
    và citation hiển thị ở đây (tránh 2 nơi suy metadata theo 2 cách khác nhau).
    """
    document_id = parent_doc.get("document_id", "") or ""
    meta = parent_doc.get("metadata", {}) or {}
    doc_meta = parse_document_metadata(
        document_id, meta.get("source_file", ""), ticker_hint=meta.get("ticker")
    )

    return {
        "chunk_id": matched_chunk_id,
        "parent_id": parent_doc.get("_id"),
        "document_id": document_id,
        "company": doc_meta["company"],
        "ticker": doc_meta["ticker"],
        "year": doc_meta["year"],
        "quarter": doc_meta["quarter"],
        "document_type": doc_meta["document_type"],
        "section_path": parent_doc.get("section_path", []),
        "page_start": parent_doc.get("page_start"),
        "page_end": parent_doc.get("page_end"),
    }


def format_citation_label(citation: Dict[str, Any], index: int) -> str:
    """Nhãn ngắn hiển thị cho người dùng, vd:
    '[1] FPT - Báo cáo tài chính năm 2024, trang 12'
    '[2] HPG - Báo cáo tài chính quý 2024 (Q2), trang 5-6'
    '[3] VNM_BCTC_2023 (không rõ loại tài liệu)'  -- fallback khi thiếu metadata
    """
    parts = []
    if citation.get("company"):
        parts.append(str(citation["company"]))
    elif citation.get("ticker"):
        parts.append(str(citation["ticker"]))

    doc_label = _DOC_TYPE_LABELS.get(citation.get("document_type"), "")
    year = citation.get("year")
    quarter = citation.get("quarter")
    if doc_label or year:
        time_part = doc_label
        if year:
            time_part = f"{time_part} {year}" if time_part else str(year)
        if quarter:
            time_part += f" (Q{quarter})"
        parts.append(time_part)

    label = " - ".join(p for p in parts if p) or citation.get("document_id") or "Không rõ nguồn"

    page_start = citation.get("page_start")
    page_end = citation.get("page_end")
    if page_start:
        if page_end and page_end != page_start:
            label += f", trang {page_start}-{page_end}"
        else:
            label += f", trang {page_start}"

    return f"[{index}] {label}"