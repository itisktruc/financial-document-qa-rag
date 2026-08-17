from pymongo import MongoClient
from app.config import settings
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

_mongo_client: Optional[MongoClient] = None

def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB at {settings.MONGO_URI}: {e}")
            _mongo_client = MongoClient(settings.MONGO_URI)
    return _mongo_client

def get_db():
    client = get_mongo_client()
    return client[settings.MONGO_DB_NAME]

def get_chunks_collection():
    db = get_db()
    return db["chunks"]

def get_parent_chunk(parent_id: str) -> Optional[Dict[str, Any]]:
    """Tìm parent document theo parent_id từ MongoDB."""
    if not parent_id:
        return None
    try:
        db = get_db()
        # Tìm trong collection "parents" trước nếu có
        if "parents" in db.list_collection_names():
            parent = db["parents"].find_one({"_id": parent_id}) or db["parents"].find_one({"doc_id": parent_id})
            if parent:
                return parent

        # Hoặc tìm trong collection "chunks"
        if "chunks" in db.list_collection_names():
            parent = db["chunks"].find_one({"_id": parent_id}) or db["chunks"].find_one({"chunk_id": parent_id})
            if parent:
                return parent

        # Hoặc duyệt qua các collection dạng chunks_*
        for col_name in db.list_collection_names():
            if col_name.startswith("chunks_"):
                doc = db[col_name].find_one({"_id": parent_id}) or db[col_name].find_one({"chunk_id": parent_id})
                if doc:
                    return doc
    except Exception as e:
        logger.warning(f"Error fetching parent chunk {parent_id}: {e}")
    return None