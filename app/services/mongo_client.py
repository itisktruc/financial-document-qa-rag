import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from pymongo import MongoClient
from config import MONGO_URI

mongo_client = MongoClient(MONGO_URI)

def get_mongo_client():
    return mongo_client