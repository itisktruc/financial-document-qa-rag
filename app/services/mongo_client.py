"""
app/services/mongo_client.py
  - financial_rag            → documents_2025, documents_pre_bank_2025
  - financial_rag_corrected  → chunks_{TICKER}_{YEAR} (flat documents)
  - chunk_type = "child" | "parent"
  - field chính: doc_id, chunk_id, parent_id, ticker, year
  Chat History
  - MONGO_URI_HISTORY + MONGO_DB_HISTORY → chỉ dùng cho chat_sessions
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()
# ---------------------------------------------------------------------------
# Config – Documents & Chunks (DB chính)
# ---------------------------------------------------------------------------

MONGO_URI_CLOUD = os.getenv("MONGO_URI_CLOUD")
MONGO_DB_DOCUMENTS = os.getenv("MONGO_DB_DOCUMENTS", "financial_rag")
MONGO_DB_CHUNKS = os.getenv("MONGO_DB_CHUNKS", "financial_rag_corrected")
DOCUMENTS_COLLECTION = os.getenv("DOCUMENTS_COLLECTION", "documents_2025")

# ---------------------------------------------------------------------------
# Config – Chat History (DB riêng, không lẫn với documents)
# ---------------------------------------------------------------------------

MONGO_URI_HISTORY = os.getenv("MONGO_URI_HISTORY")
MONGO_DB_HISTORY = os.getenv("MONGO_DB_HISTORY", "fin_rag_history")
CHAT_SESSIONS_COLLECTION = "chat_sessions"

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

_client: Optional[MongoClient] = None
_history_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    """Client cho Documents + Chunks (DB chính)."""
    global _client
    if _client is not None:
        return _client
    if not MONGO_URI_CLOUD:
        raise RuntimeError("MONGO_URI_CLOUD chưa được set trong môi trường")
    try:
        client = MongoClient(MONGO_URI_CLOUD, serverSelectionTimeoutMS=8000)
        client.admin.command("ping")
        print("[mongo] Connected to CLOUD (documents/chunks)")
        _client = client
        return _client
    except Exception as e:
        raise RuntimeError(f"Không kết nối được Cloud (documents): {e}")


def get_history_mongo_client() -> MongoClient:
    """Client riêng chỉ dùng cho Chat History."""
    global _history_client
    if _history_client is not None:
        return _history_client
    if not MONGO_URI_HISTORY:
        raise RuntimeError("MONGO_URI_HISTORY chưa được set trong môi trường")
    try:
        client = MongoClient(MONGO_URI_HISTORY, serverSelectionTimeoutMS=8000)
        client.admin.command("ping")
        print("[mongo] Connected to HISTORY DB")
        _history_client = client
        return _history_client
    except Exception as e:
        raise RuntimeError(f"Không kết nối được History DB: {e}")


# ---------------------------------------------------------------------------
# Database helpers – Documents & Chunks
# ---------------------------------------------------------------------------

def get_documents_db() -> Database:
    return get_mongo_client()[MONGO_DB_DOCUMENTS]


def get_chunks_db() -> Database:
    return get_mongo_client()[MONGO_DB_CHUNKS]


def get_documents_collection(name: str = DOCUMENTS_COLLECTION) -> Collection:
    return get_documents_db()[name]


def get_chunks_collection(name: str) -> Collection:
    """Lấy collection chunks cụ thể, ví dụ: chunks_BVB_2025"""
    return get_chunks_db()[name]


# ---------------------------------------------------------------------------
# Database helpers – Chat History (tách riêng)
# ---------------------------------------------------------------------------

def get_history_db() -> Database:
    return get_history_mongo_client()[MONGO_DB_HISTORY]


def get_chat_sessions_collection() -> Collection:
    return get_history_db()[CHAT_SESSIONS_COLLECTION]


# ---------------------------------------------------------------------------
# Chunk collections
# ---------------------------------------------------------------------------

_CHUNK_COL_RE = re.compile(r"^chunks_[A-Z0-9]+(_\d{4})?$", re.IGNORECASE)


def list_chunk_collections() -> List[str]:
    """Danh sách collection dạng chunks_{TICKER}_{YEAR}."""
    names = get_chunks_db().list_collection_names()
    return sorted(n for n in names if _CHUNK_COL_RE.match(n))


def get_child_chunks(
    collection_name: str,
    limit: Optional[int] = None,
    projection: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """Lấy tất cả chunk_type = 'child'."""
    col = get_chunks_collection(collection_name)
    cursor = col.find({"chunk_type": "child"}, projection=projection)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def get_chunk_by_id(collection_name: str, chunk_id: str) -> Optional[Dict]:
    col = get_chunks_collection(collection_name)
    doc = col.find_one({"_id": chunk_id})
    if doc:
        return doc
    return col.find_one({"chunk_id": chunk_id})


def get_parent_chunk(collection_name: str, parent_id: str) -> Optional[Dict]:
    """
    Parent nằm flat cùng collection, chunk_type = 'parent'.
    (Không còn nested array như bản cũ)
    """
    col = get_chunks_collection(collection_name)
    return col.find_one({"_id": parent_id, "chunk_type": "parent"})


def get_chunks_by_ids(collection_name: str, chunk_ids: List[str]) -> List[Dict]:
    """Lấy nhiều chunk, giữ đúng thứ tự đầu vào (quan trọng cho retrieval)."""
    if not chunk_ids:
        return []
    col = get_chunks_collection(collection_name)
    found = {
        str(d.get("_id") or d.get("chunk_id")): d
        for d in col.find({
            "$or": [
                {"_id": {"$in": chunk_ids}},
                {"chunk_id": {"$in": chunk_ids}},
            ]
        })
    }
    return [found[cid] for cid in chunk_ids if cid in found]


def get_chunks_for_document(
    collection_name: str,
    doc_id: str,
    chunk_type: Optional[str] = None,
) -> List[Dict]:
    """Lấy toàn bộ chunk của 1 document (theo field doc_id)."""
    query: Dict[str, Any] = {"doc_id": doc_id}
    if chunk_type is not None:
        query["chunk_type"] = chunk_type
    return list(get_chunks_collection(collection_name).find(query))


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def get_document(document_id: str, collection_name: str = DOCUMENTS_COLLECTION) -> Optional[Dict]:
    return get_documents_collection(collection_name).find_one({"_id": document_id})


def upsert_document(
    document_id: str,
    fields: Dict[str, Any],
    collection_name: str = DOCUMENTS_COLLECTION,
) -> None:
    """Merge field mới vào document (không replace toàn bộ)."""
    now = datetime.now(timezone.utc)
    get_documents_collection(collection_name).update_one(
        {"_id": document_id},
        {
            "$set": {**fields, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------

def ensure_indexes() -> None:
    """Gọi 1 lần lúc startup. An toàn khi gọi nhiều lần."""
    # Documents
    docs = get_documents_collection()
    docs.create_index(
        [("ticker", ASCENDING), ("year", ASCENDING)],
        name="ticker_year",
    )
    docs.create_index([("status", ASCENDING)], name="status")

    for col_name in list_chunk_collections():
        col = get_chunks_collection(col_name)
        col.create_index([("chunk_type", ASCENDING)], name="chunk_type")
        col.create_index([("parent_id", ASCENDING)], name="parent_id")
        col.create_index([("doc_id", ASCENDING)], name="doc_id")
        col.create_index(
            [("ticker", ASCENDING), ("year", ASCENDING)],
            name="ticker_year",
        )

    # Chat history indexes (nếu muốn)
    try:
        chat_col = get_chat_sessions_collection()
        chat_col.create_index([("updated_at", ASCENDING)], name="updated_at")
    except Exception:
        pass  # không bắt buộc


# ---------------------------------------------------------------------------
# Debug helpers
# ---------------------------------------------------------------------------

def count_child_chunks(collection_name: str) -> int:
    return get_chunks_collection(collection_name).count_documents({"chunk_type": "child"})


def summary() -> Dict[str, Any]:
    chunk_cols = list_chunk_collections()
    return {
        "documents_db": MONGO_DB_DOCUMENTS,
        "chunks_db": MONGO_DB_CHUNKS,
        "documents_collection": DOCUMENTS_COLLECTION,
        "chunk_collections": chunk_cols,
        "total_chunk_collections": len(chunk_cols),
        "history_db": MONGO_DB_HISTORY,
        "history_collection": CHAT_SESSIONS_COLLECTION,
    }