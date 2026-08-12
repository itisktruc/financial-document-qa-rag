# test_mongo_store.py
"""
Script test thủ công: đọc lại *_chunks.json đã sinh bởi test_chunking.py
(khỏi phải re-run chunker) rồi lưu vào MongoDB qua app/ingestion/store.py.

Yêu cầu: MongoDB đang chạy (vd `docker compose up -d mongodb`) và biến môi
trường MONGO_URI trỏ đúng (mặc định mongodb://localhost:27017 khi chạy
ngoài Docker, khớp README).

Chạy độc lập:
    python test_mongo_store.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ingestion.chunker import Chunk, ChunkType
from app.services.mongo_store import mark_processing, save_chunks
from app.services.mongo_client import ensure_indexes, get_chunks_by_ids, get_document

DOCUMENT_ID = "FPT_BCTC_2024"
CHUNKS_JSON = "data/processed/FPT/FPT_BCTC_2024_chunks.json"


def _load_chunks_from_json(path: str) -> list[Chunk]:
    """Đọc lại file *_chunks.json (output của Chunk.to_dict()) và dựng lại
    thành list[Chunk] -- test_chunking.py đã json.dump() sẵn nên khỏi phải
    parse+chunk lại từ đầu (tốn thời gian load Qwen3-VL nếu rơi vào OCR)."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [
        Chunk(
            chunk_id=d["chunk_id"],
            document_id=d["document_id"],
            chunk_type=ChunkType(d["chunk_type"]),
            content=d["content"],
            embedding_text=d["embedding_text"],
            parent_id=d["parent_id"],
            section_path=d["section_path"],
            page_start=d["page_start"],
            page_end=d["page_end"],
            token_count=d["token_count"],
            metadata=d.get("metadata", {}),
        )
        for d in raw
    ]


def main():
    ensure_indexes()

    if not os.path.exists(CHUNKS_JSON):
        print(f"[!] Chưa có {CHUNKS_JSON} -- chạy test_chunking.py trước.")
        return

    chunks = _load_chunks_from_json(CHUNKS_JSON)
    print(f"[*] Đọc {len(chunks)} chunk từ {CHUNKS_JSON}")

    mark_processing(DOCUMENT_ID)
    saved = save_chunks(chunks, document_id=DOCUMENT_ID, parser_source="docling_native")
    print(f"[✓] Đã lưu {saved} chunk vào Mongo cho document_id={DOCUMENT_ID}")

    doc = get_document(DOCUMENT_ID)
    print(f"[i] Document status: {doc.get('status')}, num_chunks: {doc.get('num_chunks')}")

    # mô phỏng bước sau khi Qdrant trả top-k id: tra ngược nội dung + kiểm
    # tra thứ tự có bị Mongo xáo lại không
    sample_ids = [c.chunk_id for c in chunks if c.chunk_type == ChunkType.TEXT_CHILD][:3]
    fetched = get_chunks_by_ids(sample_ids)
    order_ok = [d["_id"] for d in fetched] == sample_ids
    print(f"[i] Tra cứu {len(sample_ids)} id -> nhận lại {len(fetched)} chunk, "
          f"giữ đúng thứ tự đầu vào: {order_ok}")


if __name__ == "__main__":
    main()