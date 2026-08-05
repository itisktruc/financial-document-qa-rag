import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
_client = MongoClient(MONGO_URI)
_db = _client["financial_rag"]

def get_documents_collection():
    return _db["documents"]