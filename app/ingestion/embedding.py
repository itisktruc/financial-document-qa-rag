"""
Batch embed child chunks -> đẩy lên Qdrant Cloud.

Input  : Mongo  financial_rag_corrected.chunks_{TICKER}_{YEAR}
Output : Qdrant financial_chunks

Chạy:
  python -m app.scripts.embedding
  python -m app.scripts.embedding --limit 50
  python -m app.scripts.embedding --collections chunks_BVB_2025
  python -m app.scripts.embedding --dry-run
"""

from __future__ import annotations

import argparse
import logging
from typing import List, Optional

from app.services.mongo_client import list_chunk_collections, get_child_chunks
from app.services.embedding_client import attach_embeddings_to_chunks, to_qdrant_points
from app.services.qdrant_service import init_collection, store_in_qdrant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 48


def process(
    limit_per_collection: Optional[int] = None,
    dry_run: bool = False,
    collections: Optional[List[str]] = None,
) -> None:
    if not dry_run:
        init_collection()

    col_names = collections or list_chunk_collections()
    if not col_names:
        logger.warning("Không tìm thấy collection chunks_*")
        return

    logger.info("Collections: %s", col_names)
    total = 0

    for col_name in col_names:
        chunks = get_child_chunks(col_name, limit=limit_per_collection)
        logger.info("%s → %d child chunks", col_name, len(chunks))

        if not chunks:
            continue

        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]

            if dry_run:
                logger.info("[dry-run] embed %d chunks từ %s", len(batch), col_name)
                continue

            embedded = attach_embeddings_to_chunks(batch)
            points = to_qdrant_points(embedded)

            if points:
                n = store_in_qdrant(points)
                total += n
                logger.info("Upserted %d | %s | total=%d", n, col_name, total)

        logger.info("Xong %s", col_name)

    logger.info("Hoàn tất. Tổng points: %d", total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--collections", nargs="*", default=None)
    args = parser.parse_args()

    process(
        limit_per_collection=args.limit,
        dry_run=args.dry_run,
        collections=args.collections,
    )