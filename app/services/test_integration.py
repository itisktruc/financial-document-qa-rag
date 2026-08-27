"""
Smoke-test pipeline Financial RAG: Mongo → Embedding → Qdrant.

Chạy:
  python -m app.services.test_integration
  python -m app.services.test_integration --with-embed
  python -m app.services.test_integration --collection chunks_A32_2025 --limit 5
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from typing import Optional

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # optional; env có thể được inject từ shell


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _info(msg: str) -> None:
    print(f"  [INFO] {msg}")


def _section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# 1. MongoDB
# ---------------------------------------------------------------------------

def test_mongo(collection_name: Optional[str] = None, limit: int = 3) -> bool:
    _section("1. MongoDB Connection")

    try:
        from app.services.mongo_client import (
            count_child_chunks,
            get_child_chunks,
            get_mongo_client,
            list_chunk_collections,
            summary,
        )
    except ImportError as e:
        _fail(f"Import mongo_client failed: {e}")
        return False

    try:
        get_mongo_client().admin.command("ping")
        _ok("Ping Mongo OK")
    except Exception as e:
        _fail(f"Mongo connection failed: {e}")
        traceback.print_exc()
        return False

    try:
        info = summary()
        _info(f"Documents DB : {info['documents_db']}")
        _info(f"Chunks DB    : {info['chunks_db']}")
        _info(f"Documents col: {info['documents_collection']}")
        _info(f"Chunk cols   : {info['total_chunk_collections']}")
    except Exception as e:
        _fail(f"summary() error: {e}")
        return False

    try:
        cols = list_chunk_collections()
        if not cols:
            _fail("No chunks_* collection found")
            return False

        _ok(f"Found {len(cols)} collections")
        for name in cols[:15]:
            try:
                n = count_child_chunks(name)
                print(f"      • {name:30s} -> {n:>6} child")
            except Exception as e:
                print(f"      • {name:30s} -> count error: {e}")
        if len(cols) > 15:
            print(f"      ... {len(cols) - 15} more")
    except Exception as e:
        _fail(f"list_chunk_collections error: {e}")
        traceback.print_exc()
        return False

    target = collection_name or cols[0]
    _info(f"Checking sample chunks from: {target} (limit={limit})")

    try:
        chunks = get_child_chunks(target, limit=limit)
        if not chunks:
            _fail(f"No child chunks in {target}")
            return False

        _ok(f"Fetched {len(chunks)} chunks")
        sample = chunks[0]
        _info(f"Sample keys: {sorted(sample.keys())}")

        # Schema Mongo: text + chunk_type=child, id = chunk_id | _id
        has_id = bool(sample.get("chunk_id") or sample.get("_id"))
        has_text = bool(
            sample.get("text")
            or sample.get("content")
            or sample.get("embedding_text")
        )
        chunk_type = sample.get("chunk_type")

        if not has_id:
            _fail("Missing chunk_id / _id")
            return False
        if not has_text:
            _fail("Missing text field (expected 'text' per Mongo schema)")
            return False
        if chunk_type != "child":
            _fail(f"Expected chunk_type='child', got {chunk_type!r}")
            return False

        _ok("Schema validation OK (Mongo: text + chunk_type=child)")

        cid = sample.get("chunk_id") or sample.get("_id")
        preview = (
            sample.get("text")
            or sample.get("content")
            or sample.get("embedding_text")
            or ""
        )[:120]
        print(f"      sample id={cid} type={chunk_type}")
        print(f"      text[:120]={preview!r}...")

    except Exception as e:
        _fail(f"get_child_chunks error: {e}")
        traceback.print_exc()
        return False

    return True


# ---------------------------------------------------------------------------
# 2. Qdrant
# ---------------------------------------------------------------------------

def test_qdrant() -> bool:
    _section("2. Qdrant Connection")

    try:
        from app.services import qdrant_service
        from app.services.qdrant_service import (
            count_points,
            get_qdrant_client,
            init_collection,
        )
    except ImportError as e:
        _fail(f"Import qdrant_service failed: {e}")
        return False

    # Single source of truth: config nằm trong qdrant_service, không tự getenv
    url = qdrant_service.QDRANT_URL
    api_key = qdrant_service.QDRANT_API_KEY
    col = qdrant_service.QDRANT_COLLECTION

    if not url:
        _fail("Missing QDRANT_URL (set env or .env; loaded by qdrant_service)")
        return False

    _info(f"QDRANT_URL       = {url[:50]}..." if len(url) > 50 else f"QDRANT_URL = {url}")
    _info(f"QDRANT_COLLECTION= {col}")
    _info(f"API key          = {'***' + api_key[-4:] if api_key else 'None'}")

    try:
        client = get_qdrant_client()
        names = [c.name for c in client.get_collections().collections]
        _ok(f"Qdrant connected. Collections: {names}")
    except Exception as e:
        _fail(f"Qdrant connection failed: {e}")
        traceback.print_exc()
        return False

    try:
        init_collection()
        _ok(f"Collection '{col}' ready")
    except Exception as e:
        _fail(f"init_collection error: {e}")
        traceback.print_exc()
        return False

    try:
        n = count_points()
        _ok(f"Points in '{col}': {n}")
    except Exception as e:
        _fail(f"count_points error: {e}")
        return False

    return True


# ---------------------------------------------------------------------------
# 3. Embedding
# ---------------------------------------------------------------------------
def test_embedding(collection_name: Optional[str] = None, limit: int = 2) -> bool:
    """Dry-run BGE-M3 theo API embedding_client hiện tại (không upsert)."""
    _section("3. Embedding Model (BGE-M3)")

    try:
        from app.services.embedding_client import (
            DENSE_DIM,
            EMBEDDING_MODEL_ID,
            attach_embeddings_to_chunks,
            to_qdrant_points,
        )
        from app.services.mongo_client import get_child_chunks, list_chunk_collections
    except ImportError as e:
        _fail(f"Import embedding_client failed: {e}")
        return False

    _info(f"Model: {EMBEDDING_MODEL_ID}")

    # Device check inline (embedding_client không còn get_device_info)
    try:
        import torch

        cuda = torch.cuda.is_available()
        _ok(
            f"Device: {'cuda — ' + torch.cuda.get_device_name(0) if cuda else 'cpu'}"
        )
        if not cuda:
            _info("Running on CPU (sẽ chậm hơn GPU)")
    except Exception as e:
        _fail(f"Device check error: {e}")
        traceback.print_exc()
        return False

    cols = list_chunk_collections()
    target = collection_name or (cols[0] if cols else None)
    if not target:
        _fail("No collection available for testing")
        return False

    try:
        chunks = get_child_chunks(target, limit=limit)
        if not chunks:
            _fail(f"No child chunks found in {target}")
            return False
        _info(f"Testing embedding on {len(chunks)} chunks from {target}")
    except Exception as e:
        _fail(f"Fetch chunks error: {e}")
        return False

    try:
        embedded = attach_embeddings_to_chunks(chunks, return_sparse=False)
        _ok(f"Embedded {len(embedded)} chunks")
        if not embedded:
            _fail("attach_embeddings_to_chunks returned empty list")
            return False
        dim = len(embedded[0].get("dense_vector") or [])
        _info(f"Vector dim: {dim}")
        if dim != DENSE_DIM:
            _fail(f"Unexpected dim: {dim} (expected {DENSE_DIM})")
            return False
    except Exception as e:
        _fail(f"attach_embeddings_to_chunks error: {e}")
        traceback.print_exc()
        return False

    try:
        # API mới: trả về List[PointStruct], không còn dict id/vector/payload
        points = to_qdrant_points(embedded)
        _ok(f"Generated {len(points)} Qdrant points (dry-run)")
        if points:
            p0 = points[0]
            payload = p0.payload or {}
            _info(f"Sample point ID : {p0.id}")
            _info(f"Payload keys    : {sorted(payload.keys())}")
            if "text" not in payload:
                _fail("Payload missing 'text' field")
                return False
    except Exception as e:
        _fail(f"to_qdrant_points error: {e}")
        traceback.print_exc()
        return False

    return True

# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test Mongo, Qdrant, and Embedding pipeline",
    )
    parser.add_argument("--collection", type=str, default=None)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument(
        "--with-embed",
        action="store_true",
        help="Run embedding model dry-run (no upsert)",
    )
    args = parser.parse_args()

    print("Checking Financial RAG Pipeline...")
    print(f"CWD: {os.getcwd()}")

    mongo_ok = test_mongo(collection_name=args.collection, limit=args.limit)
    qdrant_ok = test_qdrant()

    if args.with_embed:
        embed_ok = test_embedding(
            collection_name=args.collection,
            limit=min(args.limit, 3),
        )
    else:
        _section("3. Embedding (Skipped)")
        _info("Pass --with-embed to run model dry-run")
        embed_ok = True

    _section("SUMMARY")
    print(f"  Mongo   : {'PASS' if mongo_ok else 'FAIL'}")
    print(f"  Qdrant  : {'PASS' if qdrant_ok else 'FAIL'}")
    if args.with_embed:
        print(f"  Embed   : {'PASS' if embed_ok else 'FAIL'}")
    else:
        print("  Embed   : SKIPPED")

    if mongo_ok and qdrant_ok and embed_ok:
        print("\nPipeline check passed.")
        sys.exit(0)

    print("\nPipeline check failed. Check logs above.")
    sys.exit(1)


if __name__ == "__main__":
    main()