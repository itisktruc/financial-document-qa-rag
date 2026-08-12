"""
app/ingestion/store.py

Cầu nối giữa app/ingestion/chunker.chunk_document() và MongoDB
(app/services/mongo_client.py). Gọi hàm save_chunks() ở đây ngay sau
chunk_document() trong pipeline thật (routers/documents.py), thay vì chỉ
json.dump() ra đĩa như test_chunking.py đang làm cho mục đích debug thủ công.

Xem rationale đầy đủ về chiến lược "replace toàn bộ chunk theo document_id"
(thay vì upsert theo chunk_id) trong docstring của
mongo_client.replace_chunks_for_document().
"""

from __future__ import annotations

from typing import Optional

from app.ingestion.chunker import Chunk
from app.models.chunk_schema import ChunkDocument
from app.services.mongo_client import replace_chunks_for_document, upsert_document


def save_chunks(
    chunks: list[Chunk],
    document_id: str,
    parser_source: Optional[str] = None,
    num_pages: Optional[int] = None,
) -> int:
    """
    Lưu list[Chunk] (output của chunk_document()) vào Mongo, đồng thời cập
    nhật document sang status="READY". Trả về số chunk đã lưu.

    Nếu về sau muốn tách rời "lưu chunk" và "đánh dấu document READY" (vd
    còn chờ bước embedding xong mới coi là sẵn sàng trả lời), tách hàm này
    làm 2 -- hiện tại gộp chung vì bước embedding/Qdrant chưa được cắm vào
    pipeline.
    """
    chunk_docs = [
        ChunkDocument.from_chunk_dict(c.to_dict()).to_mongo() for c in chunks
    ]
    saved = replace_chunks_for_document(document_id, chunk_docs)

    upsert_document(document_id, {
        "status": "READY",
        "parser_source": parser_source,
        "num_pages": num_pages,
        "num_chunks": saved,
        "error_message": None,
    })
    return saved


def mark_processing(document_id: str) -> None:
    """Gọi ngay trước khi bắt đầu parse+chunk 1 document (theo pipeline
    UPLOADED -> PROCESSING -> READY/FAILED)."""
    upsert_document(document_id, {"status": "PROCESSING", "error_message": None})


def mark_failed(document_id: str, error_message: str) -> None:
    """Gọi trong except của pipeline parse/chunk -- giữ lại error_message để
    hiển thị lý do fail cho user (vd UnicodeEncodeError đang debug ở OCR)."""
    upsert_document(document_id, {"status": "FAILED", "error_message": str(error_message)})