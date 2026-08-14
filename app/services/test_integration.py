import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from services.mongo_client import get_mongo_client
from services.qdrant import get_qdrant_client
from config import MONGO_URI, QDRANT_URL, QDRANT_API_KEY

def test_all():
    print("1. Checking config...")
    assert MONGO_URI is not None
    assert QDRANT_URL is not None
    assert QDRANT_API_KEY is not None
    print("Config OK")

    print("\n2. Testing MongoDB...")
    mongo = get_mongo_client()
    print("Databases:", mongo.list_database_names())
    print("MongoDB OK")

    print("\n3. Testing Qdrant...")
    qdrant = get_qdrant_client()
    collections = [c.name for c in qdrant.get_collections().collections]
    print("Collections:", collections)
    print("Qdrant OK")

if __name__ == "__main__":
    test_all()