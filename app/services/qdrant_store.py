from typing import List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_qdrant_client: Optional[QdrantClient] = None

def get_qdrant():
    global _qdrant_client
    if _qdrant_client is None:
        try:
            if settings.QDRANT_API_KEY:
                _qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=5.0)
            else:
                _qdrant_client = QdrantClient(url=settings.QDRANT_URL, timeout=5.0)
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant at {settings.QDRANT_URL}: {e}")
            _qdrant_client = None
    return _qdrant_client

def search_similar_blocks(
    vector: List[float],
    limit: int = 10,
    filter_conditions: Optional[qmodels.Filter] = None,
    collection_name: Optional[str] = None,
    with_vectors: bool = False
) -> List[Any]:
    """Tìm kiếm vector tương đồng trên Qdrant collection."""
    col = collection_name or settings.QDRANT_COLLECTION
    client = get_qdrant()
    if not client:
        return []
    
    try:
        if hasattr(client, "search"):
            results = client.search(
                collection_name=col,
                query_vector=vector,
                query_filter=filter_conditions,
                limit=limit,
                with_vectors=with_vectors,
                with_payload=True
            )
            return results
    except Exception as e:
        logger.warning(f"Qdrant search failed or collection '{col}' not found: {e}")
        return []
        
    return []
