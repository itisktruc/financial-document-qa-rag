"""
Smoke-test luồng retrieval Financial RAG.

Chạy từ root project (thư mục có package app/):

  python -m app.services.test_retrieval_flow
  python -m app.services.test_retrieval_flow --skip-llm
  python -m app.services.test_retrieval_flow --query "Doanh thu công ty 32 năm 2025"
  python -m app.services.test_retrieval_flow --ticker A32 --year 2025

Copy file này vào: app/services/test_retrieval_flow.py
"""

from __future__ import annotations

import argparse
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap path (khi chạy trực tiếp hoặc python -m)
# ---------------------------------------------------------------------------

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if os.path.basename(os.path.dirname(__file__)) == "services":
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
elif os.path.basename(os.path.dirname(__file__)) == "app":
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
else:
    # artifacts/ hoặc chỗ khác: thử cwd
    ROOT = os.path.abspath(os.getcwd())

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
    pass


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _info(msg: str) -> None:
    print(f"  [INFO] {msg}")


def _section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# 1. Stopwords
# ---------------------------------------------------------------------------

def test_stopwords() -> bool:
    _section("1. Vietnamese stopwords")
    try:
        from app.retrieval.hybrid_search import VI_STOPWORDS

        n = len(VI_STOPWORDS)
        _info(f"Loaded {n} stopwords")
        _info(f"Sample: {VI_STOPWORDS[:15]}")
        if n < 10:
            _fail("Stopwords list quá ngắn — kiểm tra path file vietnamese-stopwords.txt")
            return False
        _ok("Stopwords OK")
        return True
    except FileNotFoundError as e:
        _fail(f"Không tìm thấy file stopwords: {e}")
        _info("Đặt file tại app/retrieval/data/vietnamese-stopwords.txt")
        return False
    except Exception as e:
        _fail(f"Import/load stopwords: {e}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# 2. Glossary expand
# ---------------------------------------------------------------------------

def test_glossary() -> bool:
    _section("2. Glossary expand_query")
    try:
        from app.retrieval.glossary import expand_query

        samples = [
            ("LNST của FPT", "Lợi nhuận sau thuế"),
            ("ROE và ROA", "Return On Equity"),
            ("Doanh thu thuần", None),  # không bắt buộc expand
        ]
        all_ok = True
        for q, expect_substr in samples:
            out = expand_query(q)
            _info(f"{q!r} -> {out!r}")
            if expect_substr and expect_substr not in out:
                _fail(f"Expected substring {expect_substr!r} in expanded query")
                all_ok = False
        if all_ok:
            _ok("expand_query OK")
        return all_ok
    except Exception as e:
        _fail(f"glossary error: {e}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# 3. Router + Rewriter (LLM)
# ---------------------------------------------------------------------------

ROUTE_CASES: List[Tuple[str, str]] = [
    ("Xin chào bạn", "chitchat"),
    ("LNST là gì?", "term_definition"),
    ("Doanh thu FPT năm 2024", "financial_search"),
    ("Tính ROE của FPT năm 2024", "calculation"),
]


def test_router(skip_llm: bool = False) -> bool:
    _section("3. QueryRouter")
    if skip_llm:
        _info("Skipped (--skip-llm)")
        return True
    try:
        from app.retrieval.query_router import QueryRouter

        router = QueryRouter()
        all_ok = True
        for q, expected in ROUTE_CASES:
            got = router.route(q)
            if got == expected:
                _ok(f"{q!r} -> {got}")
            else:
                _fail(f"{q!r} -> {got} (expected {expected})")
                all_ok = False
        return all_ok
    except Exception as e:
        _fail(f"Router error: {e}")
        traceback.print_exc()
        return False


def test_rewriter(skip_llm: bool = False) -> bool:
    _section("4. QueryRewriter")
    if skip_llm:
        _info("Skipped (--skip-llm)")
        return True
    try:
        from app.retrieval.query_rewriter import QueryRewriter

        rewriter = QueryRewriter()
        q = "Doanh thu FPT năm 2024 là bao nhiêu?"
        out = rewriter.rewrite_and_extract_metadata(q)
        _info(f"ticker={out.get('ticker')!r} year={out.get('year')!r}")
        _info(f"rewritten={out.get('rewritten_queries')}")

        ok = True
        if not out.get("rewritten_queries"):
            _fail("rewritten_queries rỗng")
            ok = False
        ticker = (out.get("ticker") or "").upper()
        if ticker and ticker != "FPT":
            _fail(f"Expected ticker FPT, got {ticker!r}")
            ok = False
        elif ticker == "FPT":
            _ok("ticker=FPT")
        year = str(out.get("year") or "")
        if year and "2024" not in year:
            _fail(f"Expected year 2024, got {year!r}")
            ok = False
        elif "2024" in year:
            _ok("year~2024")
        if ok:
            _ok("Rewriter OK")
        return ok
    except Exception as e:
        _fail(f"Rewriter error: {e}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# 4. BM25 index
# ---------------------------------------------------------------------------

def test_bm25(ticker: Optional[str] = None, year: Optional[int] = None) -> bool:
    _section("5. BM25 index (Mongo child chunks)")
    try:
        from app.retrieval.hybrid_search import (
            _get_bm25_index,
            refresh_bm25_index,
            HybridSearchPipeline,
        )

        refresh_bm25_index()
        retriever, corpus_ids, lookup = _get_bm25_index(ticker=ticker, year=year)
        _info(f"filter ticker={ticker!r} year={year!r}")
        _info(f"corpus size={len(corpus_ids)}")

        if not retriever or not corpus_ids:
            _fail("BM25 corpus rỗng — kiểm tra Mongo chunks_* / filter")
            return False

        sample_id = corpus_ids[0]
        _info(f"sample id={sample_id} keys={list(lookup.get(sample_id, {}).keys())}")

        pipe = HybridSearchPipeline()
        hits = pipe.bm25_search(
            "doanh thu",
            k=5,
            metadata_filter={"ticker": ticker, "year": year} if ticker or year else None,
        )
        _info(f"bm25_search('doanh thu') -> {len(hits)} hits")
        if hits:
            _info(f"top1 id={hits[0][0]} score={hits[0][1]:.4f}")
        _ok("BM25 OK")
        return True
    except Exception as e:
        _fail(f"BM25 error: {e}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# 5. Dense (Qdrant)
# ---------------------------------------------------------------------------

def test_dense(ticker: Optional[str] = None, year: Optional[int] = None) -> bool:
    _section("6. Dense search (Qdrant)")
    try:
        from app.retrieval.hybrid_search import HybridSearchPipeline

        pipe = HybridSearchPipeline()
        mf = {}
        if ticker:
            mf["ticker"] = ticker
        if year is not None:
            mf["year"] = year

        hits = pipe.dense_search(
            "doanh thu thuần",
            k=5,
            metadata_filter=mf or None,
        )
        _info(f"filter={mf} hits={len(hits)}")
        if hits:
            cid, score, payload = hits[0]
            _info(f"top1 id={cid} score={score:.4f} payload_keys={list(payload.keys())[:8]}")
            _ok("Dense OK")
            return True
        _fail("Dense trả 0 hits — kiểm tra Qdrant collection / filter / embedding")
        return False
    except Exception as e:
        _fail(f"Dense error: {e}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# 6. Full retrieve + RAGController
# ---------------------------------------------------------------------------

def test_retrieve(
    query: str,
    expect_search: bool = True,
) -> bool:
    _section("7. HybridSearchPipeline.retrieve")
    try:
        from app.retrieval.hybrid_search import HybridSearchPipeline

        pipe = HybridSearchPipeline()
        out = pipe.retrieve(query)
        flags = {
            "is_chitchat": out.get("is_chitchat"),
            "is_definition": out.get("is_definition"),
            "is_calculation": out.get("is_calculation"),
        }
        n_chunks = len(out.get("chunk_ids") or [])
        n_ctx = len(out.get("context") or [])
        _info(f"query={query!r}")
        _info(f"flags={flags}")
        _info(f"chunk_ids={n_chunks} context={n_ctx}")

        if out.get("context"):
            c0 = out["context"][0]
            text = (c0.get("content") or "")[:160]
            _info(f"context[0] text[:160]={text!r}")
            _info(f"context[0] citation={c0.get('citation')}")

        if expect_search:
            if flags.get("is_chitchat") or flags.get("is_definition") or flags.get("is_calculation"):
                _fail("Expected financial_search path, got non-search intent")
                return False
            if n_chunks == 0 and n_ctx == 0:
                _fail("Search path nhưng không có chunk/context")
                return False
        _ok("retrieve OK")
        return True
    except Exception as e:
        _fail(f"retrieve error: {e}")
        traceback.print_exc()
        return False


def test_intent_flags(skip_llm: bool = False) -> bool:
    _section("8. Intent flags (4 nhánh)")
    if skip_llm:
        _info("Skipped (--skip-llm)")
        return True
    try:
        from app.retrieval.hybrid_search import HybridSearchPipeline

        pipe = HybridSearchPipeline()
        cases = [
            ("Xin chào", "is_chitchat"),
            ("ROE là gì?", "is_definition"),
            ("Tính ROE FPT 2024", "is_calculation"),
        ]
        all_ok = True
        for q, flag in cases:
            out = pipe.retrieve(q)
            if out.get(flag):
                _ok(f"{q!r} -> {flag}=True")
            else:
                _fail(f"{q!r} expected {flag}=True, got flags="
                      f"chitchat={out.get('is_chitchat')} def={out.get('is_definition')} "
                      f"calc={out.get('is_calculation')}")
                all_ok = False
        return all_ok
    except Exception as e:
        _fail(f"intent flags error: {e}")
        traceback.print_exc()
        return False


def test_rag_controller(query: str) -> bool:
    _section("9. RAGController.execute_search")
    try:
        from app.retrieval.hybrid_search import HybridSearchPipeline
        from app.retrieval.rag_pipeline import RAGController

        ctrl = RAGController(HybridSearchPipeline(), top_k=10)
        out = ctrl.execute_search(query)
        _info(f"keys={sorted(out.keys())}")
        _info(
            f"chitchat={out.get('is_chitchat')} def={out.get('is_definition')} "
            f"calc={out.get('is_calculation')} ctx={len(out.get('context') or [])}"
        )
        _ok("RAGController OK")
        return True
    except Exception as e:
        _fail(f"RAGController error: {e}")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Test Financial RAG retrieval flow")
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Bỏ Router/Rewriter/intent (không cần GROQ)",
    )
    parser.add_argument(
        "--skip-dense",
        action="store_true",
        help="Bỏ dense/Qdrant/embedding",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Câu financial_search để retrieve (mặc định theo ticker/year)",
    )
    parser.add_argument("--ticker", type=str, default=None, help="VD: A32")
    parser.add_argument("--year", type=int, default=None, help="VD: 2025")
    parser.add_argument(
        "--bm25-only",
        action="store_true",
        help="Chỉ chạy stopwords + glossary + BM25",
    )
    args = parser.parse_args()

    print("Financial RAG — retrieval flow smoke test")
    print(f"CWD: {os.getcwd()}")
    print(f"ROOT on path: {ROOT}")

    results: Dict[str, bool] = {}

    results["stopwords"] = test_stopwords()
    results["glossary"] = test_glossary()

    if args.bm25_only:
        results["bm25"] = test_bm25(ticker=args.ticker, year=args.year)
        _section("SUMMARY")
        for k, v in results.items():
            print(f"  {k:16s}: {'PASS' if v else 'FAIL'}")
        sys.exit(0 if all(results.values()) else 1)

    results["router"] = test_router(skip_llm=args.skip_llm)
    results["rewriter"] = test_rewriter(skip_llm=args.skip_llm)
    results["bm25"] = test_bm25(ticker=args.ticker, year=args.year)

    if not args.skip_dense:
        results["dense"] = test_dense(ticker=args.ticker, year=args.year)
    else:
        _section("6. Dense search (Skipped)")
        results["dense"] = True

    search_q = args.query
    if not search_q:
        if args.ticker and args.year:
            search_q = f"Doanh thu {args.ticker} năm {args.year}"
        elif args.ticker:
            search_q = f"Doanh thu {args.ticker}"
        else:
            search_q = "Doanh thu công ty 32 năm 2025"

    results["retrieve"] = test_retrieve(search_q, expect_search=True)
    results["intents"] = test_intent_flags(skip_llm=args.skip_llm)
    results["controller"] = test_rag_controller(search_q)

    _section("SUMMARY")
    for k, v in results.items():
        print(f"  {k:16s}: {'PASS' if v else 'FAIL'}")

    if all(results.values()):
        print("\nAll checks passed.")
        sys.exit(0)

    print("\nSome checks failed. Xem log phía trên.")
    sys.exit(1)


if __name__ == "__main__":
    main()
