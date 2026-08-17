"""
Embed child chunks (bge-m3) và đẩy lên Qdrant.
Tối ưu cho RTX 3090 (24GB).

Input  : MongoDB  financial_rag_corrected.chunks_{TICKER}_{YEAR}
Output : Qdrant   collection "financial_chunks"
"""

from __future__ import annotations

import argparse
import logging
import re
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27018"
MONGO_DB = "financial_rag_corrected"

QDRANT_URL = "http://localhost:6334"
QDRANT_COLLECTION = "financial_chunks"

MODEL_NAME = "BAAI/bge-m3"
VECTOR_SIZE = 1024
BATCH_SIZE = 48          # tối ưu cho 3090
UPSERT_BATCH = 200
MAX_LENGTH = 1024


def get_mongo():
    return MongoClient(MONGO_URI)[MONGO_DB]


def list_chunk_collections(db) -> List[str]:
    cols = []
    for name in db.list_collection_names():
        if re.match(r"^chunks_[A-Z0-9]+(_\d{4})?$", name, re.I):
            cols.append(name)
    return sorted(cols)


def ensure_qdrant_collection(client: QdrantClient, collection: str):
    exists = client.collection_exists(collection)
    if not exists:
        logger.info("Creating Qdrant collection: %s", collection)
        client.create_collection(
            collection_name=collection,
            vectors_config=qmodels.VectorParams(
                size=VECTOR_SIZE,
                distance=qmodels.Distance.COSINE,
            ),
            optimizers_config=qmodels.OptimizersConfigDiff(
                indexing_threshold=10000,
            ),
        )
    else:
        logger.info("Qdrant collection already exists: %s", collection)

    for field, schema in [
        ("ticker", qmodels.PayloadSchemaType.KEYWORD),
        ("year", qmodels.PayloadSchemaType.INTEGER),
        ("chunk_type", qmodels.PayloadSchemaType.KEYWORD),
        ("doc_id", qmodels.PayloadSchemaType.KEYWORD),
        ("parent_id", qmodels.PayloadSchemaType.KEYWORD),
        ("section", qmodels.PayloadSchemaType.KEYWORD),
    ]:
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name=field,
                field_schema=schema,
            )
        except Exception:
            pass


def load_model():
    from FlagEmbedding import BGEM3FlagModel

    logger.info("Loading model %s ...", MODEL_NAME)
    model = BGEM3FlagModel(MODEL_NAME, use_fp16=True)
    logger.info("Model loaded.")
    return model


def embed_texts(model, texts: List[str]) -> List[List[float]]:
    out = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        max_length=MAX_LENGTH,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )
    dense = out["dense_vecs"]
    return [v.tolist() if hasattr(v, "tolist") else list(v) for v in dense]


def chunk_to_point(chunk: Dict[str, Any], vector: List[float]) -> qmodels.PointStruct:
    payload = {
        "chunk_id": chunk.get("chunk_id") or chunk.get("_id"),
        "doc_id": chunk.get("doc_id"),
        "parent_id": chunk.get("parent_id"),
        "chunk_type": chunk.get("chunk_type"),
        "ticker": chunk.get("ticker"),
        "year": chunk.get("year"),
        "company": chunk.get("company"),
        "section": chunk.get("section"),
        "subsection": chunk.get("subsection"),
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "order_index": chunk.get("order_index"),
        "heading_path": chunk.get("heading_path") or [],
        "text": chunk.get("text"),
        "source_file": chunk.get("source_file"),
        "block_type": chunk.get("block_type"),
    }
    point_id = chunk.get("chunk_id") or chunk["_id"]
    return qmodels.PointStruct(
        id=point_id,
        vector=vector,
        payload=payload,
    )


def process(
    limit_per_collection: Optional[int] = None,
    dry_run: bool = False,
    collections: Optional[List[str]] = None,
):
    db = get_mongo()
    qdrant = QdrantClient(url=QDRANT_URL)

    if not dry_run:
        ensure_qdrant_collection(qdrant, QDRANT_COLLECTION)

    col_names = collections or list_chunk_collections(db)
    if not col_names:
        logger.warning("Không tìm thấy collection chunks_* nào.")
        return

    logger.info("Found %d chunk collections: %s", len(col_names), col_names)

    model = None if dry_run else load_model()
    total_points = 0

    for col_name in col_names:
        col = db[col_name]
        query = {"chunk_type": "child"}
        cursor = col.find(query)
        if limit_per_collection:
            cursor = cursor.limit(limit_per_collection)

        buffer_chunks: List[Dict] = []
        buffer_texts: List[str] = []

        def flush():
            nonlocal total_points, buffer_chunks, buffer_texts
            if not buffer_chunks:
                return

            if dry_run:
                logger.info(
                    "[dry-run] would embed + upsert %d points from %s",
                    len(buffer_chunks),
                    col_name,
                )
            else:
                vectors = embed_texts(model, buffer_texts)
                points = [
                    chunk_to_point(c, v)
                    for c, v in zip(buffer_chunks, vectors)
                ]
                for i in range(0, len(points), UPSERT_BATCH):
                    batch = points[i : i + UPSERT_BATCH]
                    qdrant.upsert(
                        collection_name=QDRANT_COLLECTION,
                        points=batch,
                        wait=True,
                    )
                total_points += len(points)
                logger.info(
                    "Upserted %d points from %s (total %d)",
                    len(points),
                    col_name,
                    total_points,
                )

            buffer_chunks = []
            buffer_texts = []

        count = 0
        for chunk in cursor:
            text = (chunk.get("text") or "").strip()
            if not text:
                continue
            buffer_chunks.append(chunk)
            buffer_texts.append(text)
            count += 1

            if len(buffer_chunks) >= BATCH_SIZE:
                flush()

        flush()
        logger.info("Finished collection %s (%d child chunks)", col_name, count)

    logger.info("Done. Total points upserted: %d", total_points)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số child chunk mỗi collection")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--collections", nargs="*", default=None, help="Chỉ xử lý collection này")
    args = parser.parse_args()

    process(
        limit_per_collection=args.limit,
        dry_run=args.dry_run,
        collections=args.collections,
    )