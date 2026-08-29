"""
Embed every "child" chunk in MongoDB (chunked_documents_2025) and index the
resulting vectors into Qdrant's `financial_chunks` collection.

WHY THIS SCRIPT EXISTS
-----------------------
chunker.py has already written parent+child chunks into Mongo (confirmed:
~770K entries in the BM25 corpus), but nothing has ever successfully
embedded and pushed vectors into Qdrant -- count_points() returns 0.

Root cause: app/services/embedding_client.py's attach_embeddings_to_chunks()
filters on chunk_type in {"text_child", "table"}, and to_qdrant_points()
expects document_id / nested metadata{} / section_path / token_count.
chunker.py's actual output uses chunk_type in {"child", "parent"}, doc_id,
flat fields, and heading_path -- none of which match. So every chunk has
always been silently filtered out before embedding ever ran.

This script does NOT modify embedding_client.py. It reads raw chunks from
Mongo, adapts each CHILD chunk (parents are intentionally skipped -- see
embedding_client.py's own docstring: parents are context-expansion-only,
looked up via Mongo by parent_id, never embedded/searched directly) into
the shape attach_embeddings_to_chunks()/to_qdrant_points() expect, then
calls those functions unchanged.

RESUMABILITY
------------
Progress is checkpointed to disk (top-level Mongo document _id) after every
flushed batch, so a killed/interrupted run can resume with --resume
(default) instead of restarting from zero. Use --reset to ignore an
existing checkpoint and start over.

RUNTIME WARNING
----------------
770K+ source chunks (roughly half will be "child" type) on CPU (BGE-M3) can
take a long time -- easily hours. Recommended first step:

    python ingest_qdrant.py --dry-run --limit 20      # sanity check, no embedding
    python ingest_qdrant.py --limit 20                # real smoke test, small
    python ingest_qdrant.py                            # full run (consider nohup/tmux)

Usage:
    python ingest_qdrant.py [--limit N] [--batch-size N] [--dry-run]
                             [--reset] [--checkpoint PATH]

Run from the project root (same convention as test_embedding.py) so the
`app.*` imports resolve.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    from app.services.mongo_client import get_chunks_collection
    from app.services.embedding_client import attach_embeddings_to_chunks, to_qdrant_points
    from app.services.qdrant_store import store_in_qdrant, count_points
except ImportError as e:
    print(
        f"[FATAL] Could not import backend modules ({e}).\n"
        "        Run this script from the project root (the folder containing 'app/').",
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_CHECKPOINT = Path(".qdrant_ingest_checkpoint.json")


# ----------------------------------------------------------------------------
# Schema adapter: chunker.py's chunk dict -> embedding_client.py's expected shape
# ----------------------------------------------------------------------------

def adapt_chunk(child: dict) -> dict | None:
    """Map one chunker.py 'child' chunk dict onto the field names/shape
    attach_embeddings_to_chunks() / to_qdrant_points() expect. Returns None
    for chunks with no usable text (mirrors chunker.py's own skip logic)."""
    text = (child.get("text") or "").strip()
    if not text:
        return None

    # embedding_client.py only embeds chunk_type in {"text_child", "table"}.
    # chunker.py doesn't distinguish at the chunk_type level, but its child
    # dicts carry block_type, which does.
    adapted_chunk_type = "table" if child.get("block_type") == "table" else "text_child"

    return {
        "chunk_id": child.get("chunk_id") or child.get("_id"),
        "chunk_type": adapted_chunk_type,
        "embedding_text": text,
        "content": text,
        "document_id": child.get("doc_id"),
        "parent_id": child.get("parent_id"),
        "section_path": child.get("heading_path") or [],
        "page_start": child.get("page_start"),
        "page_end": child.get("page_end"),
        "token_count": len(text.split()),
        "metadata": {
            "source_file": child.get("source_file"),
            "ticker": child.get("ticker"),
            "year": child.get("year"),        # <-- Add this
            "company": child.get("company"),  # <-- Add this
        },
    }


# ----------------------------------------------------------------------------
# Checkpointing
# ----------------------------------------------------------------------------

def load_checkpoint(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("processed_doc_ids", []))
    except Exception as e:
        print(f"[WARN] Could not read checkpoint {path} ({e}) -- starting fresh.", file=sys.stderr)
        return set()


def save_checkpoint(path: Path, processed_doc_ids: set[str]) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"processed_doc_ids": sorted(processed_doc_ids)}, f)
    tmp.replace(path)  # atomic-ish swap, avoids a half-written checkpoint on crash


# ----------------------------------------------------------------------------
# Main ingestion loop
# ----------------------------------------------------------------------------

def run(batch_size: int, limit: int | None, dry_run: bool, reset: bool, checkpoint_path: Path) -> None:
    if reset and checkpoint_path.exists():
        checkpoint_path.unlink()
        print(f"[*] --reset: removed existing checkpoint {checkpoint_path}")

    processed_doc_ids = load_checkpoint(checkpoint_path)
    if processed_doc_ids:
        print(f"[*] Resuming: {len(processed_doc_ids)} documents already indexed, will be skipped.")

    coll = get_chunks_collection()
    total_docs = coll.count_documents({})
    print(f"[*] Source collection: {coll.name} ({total_docs} documents total)")

    cursor = coll.find({}, {"chunks": 1})
    if limit:
        cursor = cursor.limit(limit)
        print(f"[*] --limit {limit}: only scanning the first {limit} documents.")

    pending_adapted: list[dict] = []
    pending_doc_ids: list[str] = []

    docs_seen = 0
    docs_skipped_checkpoint = 0
    chunks_skipped_empty = 0
    total_chunks_indexed = 0
    t_start = time.perf_counter()

    def flush() -> None:
        nonlocal pending_adapted, pending_doc_ids, total_chunks_indexed
        if not pending_doc_ids:
            return

        if dry_run:
            if pending_adapted:
                print(f"    [dry-run] would embed+upsert {len(pending_adapted)} chunks "
                      f"from {len(pending_doc_ids)} documents")
            # Deliberately NOT checkpointing here: dry-run never writes to
            # Qdrant, so marking these documents "processed" would cause a
            # real run afterward to skip them and index nothing.
        else:
            if pending_adapted:
                embedded = attach_embeddings_to_chunks(pending_adapted, include_parent=False)
                points = to_qdrant_points(embedded)
                
                # Defend against None returns
                if points is None:
                    print(f"    [WARN] to_qdrant_points returned None for batch of {len(pending_adapted)}. Skipping.")
                    points = []
                
                if points:
                    store_in_qdrant(points)
                    total_chunks_indexed += len(points)

            processed_doc_ids.update(pending_doc_ids)
            save_checkpoint(checkpoint_path, processed_doc_ids)

        elapsed = time.perf_counter() - t_start
        rate = (total_chunks_indexed / elapsed) if (elapsed > 0 and not dry_run) else 0.0
        print(f"    [progress] docs_seen={docs_seen}/{total_docs} | "
              f"chunks_indexed={total_chunks_indexed} | rate={rate:.1f} chunks/s | "
              f"elapsed={elapsed:.0f}s")

        pending_adapted = []
        pending_doc_ids = []

    for doc in cursor:
        docs_seen += 1
        doc_id = str(doc["_id"])

        if doc_id in processed_doc_ids:
            docs_skipped_checkpoint += 1
            continue

        children = [c for c in doc.get("chunks", []) if c.get("chunk_type") == "child"]
        for child in children:
            adapted = adapt_chunk(child)
            if adapted is None:
                chunks_skipped_empty += 1
                continue
            pending_adapted.append(adapted)

        pending_doc_ids.append(doc_id)

        if len(pending_adapted) >= batch_size:
            flush()

        if docs_seen % 50 == 0:
            print(f"[*] Scanned {docs_seen}/{total_docs} documents so far "
                  f"(skipped via checkpoint: {docs_skipped_checkpoint})...")

    flush()  # final partial batch

    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)
    print(f"Documents scanned this run : {docs_seen}")
    print(f"Documents skipped (resume) : {docs_skipped_checkpoint}")
    print(f"Child chunks skipped (empty text): {chunks_skipped_empty}")
    print(f"Chunks embedded+indexed this run : {total_chunks_indexed}")

    if not dry_run:
        try:
            print(f"Qdrant collection point count now: {count_points()}")
        except Exception as e:
            print(f"[WARN] Could not fetch point count: {e}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed child chunks and index them into Qdrant.")
    parser.add_argument("--limit", type=int, default=None, help="Only scan the first N source documents.")
    parser.add_argument("--batch-size", type=int, default=200,
                         help="Number of child chunks to accumulate before each embed+upsert flush "
                              "(checkpoint granularity). Not the same as EMBEDDING_BATCH_SIZE, which "
                              "controls the model's internal encode batch size.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Scan and count chunks without calling the embedding model or Qdrant.")
    parser.add_argument("--reset", action="store_true", help="Ignore any existing checkpoint, start over.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT,
                         help=f"Checkpoint file path (default: {DEFAULT_CHECKPOINT}).")
    args = parser.parse_args()

    run(
        batch_size=args.batch_size,
        limit=args.limit,
        dry_run=args.dry_run,
        reset=args.reset,
        checkpoint_path=args.checkpoint,
    )


if __name__ == "__main__":
    main()