"""
Qdrant service – collection financial_chunks (cloud).
Payload schema hiện tại: chunk_id, doc_id, parent_id, chunk_type, ticker, year...
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.models import Distance, PointStruct, VectorParams
from dotenv import load_dotenv
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "financial_chunks")
VECTOR_SIZE = 1024

_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        if not QDRANT_URL:
            raise RuntimeError("Thiếu QDRANT_URL")
        _client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            timeout=30,
        )
    return _client


def init_collection() -> None:
    client = get_qdrant_client()

    if not client.collection_exists(QDRANT_COLLECTION):
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        print(f"[qdrant] Created collection: {QDRANT_COLLECTION}")
    else:
        print(f"[qdrant] Collection ready: {QDRANT_COLLECTION}")

    _create_payload_indexes()


def _create_payload_indexes() -> None:
    client = get_qdrant_client()
    indexes = [
        ("parent_id", qmodels.PayloadSchemaType.KEYWORD),
        ("ticker", qmodels.PayloadSchemaType.KEYWORD),
        ("year", qmodels.PayloadSchemaType.INTEGER),
        ("doc_id", qmodels.PayloadSchemaType.KEYWORD),
        ("company", qmodels.PayloadSchemaType.KEYWORD),
        ("chunk_type", qmodels.PayloadSchemaType.KEYWORD),
    ]

    for field, schema in indexes:
        try:
            client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name=field,
                field_schema=schema,
            )
        except Exception:
            pass  # index đã tồn tại


def store_in_qdrant(points: List[Dict[str, Any]]) -> int:
    """
    points: list dict có key id / vector / payload
    (khớp PointStruct)
    """
    if not points:
        return 0

    client = get_qdrant_client()
    structs = [PointStruct(**p) for p in points]

    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=structs,
        wait=True,
    )
    print(f"[qdrant] Upserted {len(structs)} points")
    return len(structs)


def search_similar(
    query_vector: List[float],
    limit: int = 5,
    query_filter: Optional[qmodels.Filter] = None,
    score_threshold: Optional[float] = None,
) -> List:
    client = get_qdrant_client()
    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
        with_vectors=False,
        score_threshold=score_threshold,
    )
    return response.points


def count_points() -> int:
    return get_qdrant_client().count(
        collection_name=QDRANT_COLLECTION,
        exact=True,
    ).count