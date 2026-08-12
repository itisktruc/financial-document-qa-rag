import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "financial_rag")

# Khởi tạo client kết nối (PyMongo tự quản lý connection pool)
_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
_db = _client[MONGO_DB]

def get_documents_collection(collection_name: str = "documents"):
    """Trả về collection tương ứng từ database"""
    return _db[collection_name]

def get_chunks_collection() -> Collection:
    """Trả về collection "chunks" (output của chunker.chunk_document())."""
    return _db["chunks"]
 
 
def ensure_indexes() -> None:
    """
    Gọi 1 lần lúc app khởi động (vd app/main.py, event "startup"/lifespan).
    create_index là no-op nếu index cùng tên đã tồn tại nên gọi lại nhiều
    lần (mỗi lần app restart) vẫn an toàn, không cần guard thêm.
    """
    docs = get_documents_collection()
    docs.create_index(
        [("ticker", ASCENDING), ("document_type", ASCENDING),
         ("year", ASCENDING), ("quarter", ASCENDING)],
        name="ticker_type_year_quarter",
    )
    docs.create_index([("status", ASCENDING)], name="status")
 
    chunks = get_chunks_collection()
    chunks.create_index([("document_id", ASCENDING)], name="document_id")
    chunks.create_index(
        [("document_id", ASCENDING), ("chunk_type", ASCENDING)],
        name="document_id_chunk_type",
    )
    chunks.create_index([("parent_id", ASCENDING)], name="parent_id")
 
 
# ---------------------------------------------------------------------------
# documents
# ---------------------------------------------------------------------------
 
def upsert_document(document_id: str, fields: dict[str, Any]) -> None:
    """Merge field mới vào document (KHÔNG replace toàn bộ document) -- dùng
    để cập nhật status theo từng bước pipeline mà không mất field đã ghi
    trước đó (vd khi PROCESSING chỉ set status, không đụng company/ticker
    đã ghi lúc UPLOADED)."""
    now = datetime.now(timezone.utc)
    get_documents_collection().update_one(
        {"_id": document_id},
        {
            "$set": {**fields, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
 
 
def get_document(document_id: str) -> Optional[dict]:
    return get_documents_collection().find_one({"_id": document_id})
 
 
# ---------------------------------------------------------------------------
# chunks
# ---------------------------------------------------------------------------
 
def replace_chunks_for_document(document_id: str, chunk_docs: Iterable[dict]) -> int:
    """
    Xoá hết chunk cũ của document_id rồi insert lại toàn bộ chunk mới.
 
    KHÔNG upsert theo chunk_id: chunk_id = uuid4().hex được sinh MỚI mỗi lần
    gọi chunk_document(), kể cả parse lại đúng 1 file với nội dung giống hệt.
    Upsert theo chunk_id sẽ không match được chunk cũ -> chunk cũ nằm rác
    lại trong Mongo sau mỗi lần re-chunk (rất hay xảy ra lúc debug OCR/logic
    chunking). Replace-toàn-bộ tốn 1 delete_many + insert_many mỗi lần
    re-process (rẻ, 1 tài liệu tài chính chỉ vài trăm chunk) nhưng đảm bảo
    Mongo luôn khớp đúng 1-1 với lần chunk gần nhất.
 
    insert_many(..., ordered=False): không dừng lại nếu 1 document lỗi
    (thực tế khó xảy ra vì _id là uuid4 mới toàn bộ), đổi lại Mongo có thể
    thực thi các insert không theo đúng thứ tự -- chấp nhận được vì thứ tự
    ghi vào DB không ảnh hưởng gì (không phải thứ tự hiển thị/retrieval).
    """
    chunks = get_chunks_collection()
    chunks.delete_many({"document_id": document_id})
    chunk_docs = list(chunk_docs)
    if not chunk_docs:
        return 0
    chunks.insert_many(chunk_docs, ordered=False)
    return len(chunk_docs)
 
 
def get_chunks_by_ids(chunk_ids: list[str]) -> list[dict]:
    """Tra cứu nội dung đầy đủ theo danh sách chunk_id (vd sau khi Qdrant trả
    top-k). Kết quả được SẮP LẠI đúng thứ tự chunk_ids đầu vào -- $in của
    Mongo không đảm bảo giữ thứ tự, mà thứ tự đó chính là ranking điểm
    similarity/rerank, để Mongo tự sắp là hỏng luôn kết quả retrieval."""
    if not chunk_ids:
        return []
    found = {d["_id"]: d for d in get_chunks_collection().find({"_id": {"$in": chunk_ids}})}
    return [found[cid] for cid in chunk_ids if cid in found]
 
 
def get_parent_chunk(parent_id: str) -> Optional[dict]:
    """Mở rộng ngữ cảnh: lấy toàn bộ parent chunk (cả section) từ id của 1
    text_child/table đã match lúc retrieval."""
    return get_chunks_collection().find_one({"_id": parent_id})
 
 
def get_chunks_for_document(document_id: str, chunk_type: Optional[str] = None) -> list[dict]:
    """Lấy toàn bộ chunk của 1 document -- dùng cho debug/QA thủ công hoặc
    re-embed theo document. Lọc thêm theo chunk_type nếu cần."""
    query: dict[str, Any] = {"document_id": document_id}
    if chunk_type is not None:
        query["chunk_type"] = chunk_type
    return list(get_chunks_collection().find(query))