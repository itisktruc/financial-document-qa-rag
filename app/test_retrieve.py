"""
scripts/test_retrieve.py
Chạy thử Hybrid Search + xem context/citation chi tiết.

Cách chạy (trong container backend):
  docker compose exec backend python -m scripts.test_retrieve

Hoặc local (đã set .env + PYTHONPATH):
  python -m scripts.test_retrieve
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_retrieve")


def pretty(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


def test_retrieve(query: str, history: List[Dict] | None = None) -> None:
    from app.retrieval.hybrid_search import HybridSearchPipeline
    from app.services.mongo_client import list_chunk_collections, get_parent_chunk

    pipeline = HybridSearchPipeline()

    print("\n" + "=" * 70)
    print(f"QUERY : {query!r}")
    print("=" * 70)

    # 1) Routing + rewrite
    prep = pipeline.process_user_query(query, history=history or [])
    print("\n[1] process_user_query:")
    print(pretty(prep))

    if prep.get("type") != "financial_search":
        print(f"\n→ Không phải financial_search (type={prep.get('type')}). Dừng.")
        return

    # 2) Full retrieve
    result = pipeline.retrieve(query, top_k=10, history=history or [])
    contexts = result.get("context") or []
    chunk_ids = result.get("chunk_ids") or []

    print(f"\n[2] retrieve: {len(chunk_ids)} chunk_ids, {len(contexts)} contexts")
    print(f"    chunk_ids = {chunk_ids[:15]}{'...' if len(chunk_ids) > 15 else ''}")

    # 3) Chi tiết từng context + citation
    print("\n[3] Contexts & Citations:")
    for i, ctx in enumerate(contexts, 1):
        cit = ctx.get("citation") or {}
        text = (ctx.get("content") or "").strip()
        print("-" * 70)
        print(f"CTX [{i}]")
        print(f"  ticker      : {cit.get('ticker')}")
        print(f"  year        : {cit.get('year')}")
        print(f"  source_file : {cit.get('source_file')}")
        print(f"  page        : {cit.get('page_start')} – {cit.get('page_end')}")
        print(f"  section     : {cit.get('section')}")
        print(f"  doc_id      : {cit.get('doc_id')}")
        print(f"  text[:300]  : {text[:300]!r}")

    # 4) List chunk collections (debug BM25 empty)
    print("\n[4] Chunk collections trong Mongo:")
    try:
        cols = list_chunk_collections()
        print(f"  total = {len(cols)}")
        for name in cols:
            print(f"   - {name}")
    except Exception as e:
        print(f"  ERROR list_chunk_collections: {e}")

    # 5) Thử tìm parent của context đầu (nếu có)
    if contexts:
        cit0 = contexts[0].get("citation") or {}
        # parent_id không nằm trong citation hiện tại → lấy từ chunk_ids + content_lookup khó
        # Chỉ log doc_id để bạn tự check Mongo
        print("\n[5] Gợi ý check Mongo:")
        print(f"  db.<collection>.findOne({{ doc_id: {cit0.get('doc_id')!r}, chunk_type: 'parent' }})")
        print(f"  db.<collection>.findOne({{ _id: {cit0.get('doc_id')!r} }})")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


def main():
    # Đổi query tại đây hoặc truyền argv
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Doanh thu ACB nam 2025 la bao nhieu"
    test_retrieve(query)


if __name__ == "__main__":
    main()