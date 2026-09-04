import os
from functools import lru_cache
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://admin:changeme@mongodb:27017")
MONGO_DB = os.getenv("MONGO_DB", "financial_rag")

# Khởi tạo client kết nối (PyMongo tự quản lý connection pool)
_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
_db = _client[MONGO_DB]

def get_documents_collection(collection_name: str = "documents"):
    """Trả về collection tương ứng từ database"""
    return _db[collection_name]


def get_chunks_collection() -> Collection:
    """Trả về đúng collection mà chunker.py đã ghi dữ liệu vào."""
    return _db["chunked_documents_2025"]  # Sửa "chunks" -> "chunked_documents_2025"
 
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
 
 
# def get_parent_chunk(parent_id: str) -> Optional[dict]:
#     """Mở rộng ngữ cảnh: lấy toàn bộ parent chunk (cả section) từ id của 1
#     text_child/table đã match lúc retrieval."""
    # return get_chunks_collection().find_one({"_id": parent_id})
def get_parent_chunk(parent_id: str) -> Optional[dict]:
    """Truy vấn chính xác parent chunk nằm trong mảng `chunks` lồng nhau."""
    doc = get_chunks_collection().find_one(
        {"chunks._id": parent_id},
        {"chunks": {"$elemMatch": {"_id": parent_id}}}  # Chỉ trả về đúng element khớp parent_id
    )
    if doc and "chunks" in doc and len(doc["chunks"]) > 0:
        return doc["chunks"][0]
    return None
 
 
# ---------------------------------------------------------------------------
# known tickers -- dùng làm ngữ cảnh cho LLM (gpt-4o-mini) tự chuẩn hoá
# ticker/report_scope trong câu hỏi người dùng, THAY cho TICKER_MAPPING
# viết tay trước đây trong app/retrieval/hybrid_search.py (mỗi công ty/
# biến thể tên gọi mới đều phải sửa code). Dùng bởi:
#   - app/retrieval/query_rewriter.py   (nhánh financial_search)
#   - app/calculation/calculation_service.py (nhánh calculation)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_known_tickers() -> list[dict]:
    """
    Danh sách {ticker, company} hiện có trong hệ thống, suy trực tiếp từ dữ
    liệu đã ingest (collection chunks) -- tự cập nhật theo dữ liệu thật,
    không cần đụng code khi ingest thêm công ty mới.

    Cache bằng lru_cache (không TTL) vì list này chỉ đổi khi ingest/xoá tài
    liệu -- gọi refresh_known_tickers() ngay sau các thao tác đó để
    invalidate (app/retrieval/hybrid_search.refresh_bm25_index() đã gọi hộ).
    """
    pipeline = [
        {"$match": {"ticker": {"$ne": None}}},
        {"$group": {"_id": "$ticker", "company": {"$first": "$company"}}},
        {"$sort": {"_id": 1}},
    ]
    try:
        rows = list(get_chunks_collection().aggregate(pipeline))
    except Exception as e:
        print(f"[mongo_client] Không lấy được danh sách ticker: {e}")
        return []
    return [{"ticker": r["_id"], "company": r.get("company")} for r in rows if r.get("_id")]


def known_tickers_prompt_text(limit: int = 200) -> str:
    """Format sẵn danh sách ticker/company thành text ngắn gọn để nhúng vào
    prompt LLM -- dùng chung bởi QueryRewriter và CalculationService, tránh
    trùng lặp logic format ở 2 nơi. `limit` để tránh phình prompt nếu hệ
    thống có rất nhiều công ty."""
    known = get_known_tickers()
    if not known:
        return "(Chưa có dữ liệu công ty nào trong hệ thống)"
    lines = [
        f"- {item['ticker']}" + (f": {item['company']}" if item.get("company") else "")
        for item in known[:limit]
    ]
    return "\n".join(lines)


def refresh_known_tickers() -> None:
    """Gọi sau khi ingest/xoá tài liệu để invalidate cache get_known_tickers()
    -- nếu không, LLM sẽ không "thấy" được ticker vừa được ingest thêm."""
    get_known_tickers.cache_clear()


def get_chunks_for_document(document_id: str, chunk_type: Optional[str] = None) -> list[dict]:
    """Lấy toàn bộ chunk của 1 document -- dùng cho debug/QA thủ công hoặc
    re-embed theo document. Lọc thêm theo chunk_type nếu cần."""
    query: dict[str, Any] = {"document_id": document_id}
    if chunk_type is not None:
        query["chunk_type"] = chunk_type
    return list(get_chunks_collection().find(query))