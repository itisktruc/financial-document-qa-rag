"""Cach dung: from app.services.mongo_client import get_mongo_client
from app.services.qdrant_client import get_qdrant_client

mongo = get_mongo_client()
qdrant = get_qdrant_client()"""

from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")