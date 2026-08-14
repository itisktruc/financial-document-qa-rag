import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from qdrant_client import QdrantClient
from config import QDRANT_URL, QDRANT_API_KEY

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def get_qdrant_client():
    return qdrant_client