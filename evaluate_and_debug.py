"""
evaluate_and_debug.py

Script Debug & Đánh Giá Độ Chính Xác Toàn Diện Chuỗi Retrieval RAG:
Hiển thị chi tiết Đầu Vào (Input) -> Xử Lý (Processing) -> Đầu Ra (Output)
cho từng giai đoạn của từng câu hỏi test.
"""

import sys
import os
import time
from typing import Dict, List, Any

# Đảm bảo UTF-8 cho Windows Terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.retrieval.hybrid_search import HybridSearchPipeline
from app.retrieval.glossary import expand_query, FINANCIAL_GLOSSARY

# Tập câu hỏi thử nghiệm và nhãn kỳ vọng (Expected Labels)
TEST_BENCHMARK = [
    {
        "query": "Xin chào bạn là ai?",
        "expected_type": "chitchat",
        "expected_ticker": None,
        "expected_year": None,
    },
    {
        "query": "LNST và ROE nghĩa là gì?",
        "expected_type": "term_definition",
        "expected_ticker": None,
        "expected_year": None,
    },
    {
        "query": "Doanh thu thuần năm 2024 của FPT đạt bao nhiêu?",
        "expected_type": "financial_search",
        "expected_ticker": "FPT",
        "expected_year": "2024",
    },
    {
        "query": "Tổng tài sản của VNM năm 2023 tăng trưởng thế nào?",
        "expected_type": "financial_search",
        "expected_ticker": "VNM",
        "expected_year": "2023",
    },
    {
        "query": "EBITDA được tính như thế nào?",
        "expected_type": "term_definition",
        "expected_ticker": None,
        "expected_year": None,
    }
]

def format_box(title: str, content: str, char="="):
    line = char * 85
    print(f"\n{line}\n  {title}\n{line}\n{content}")

def evaluate_single_query(pipeline: HybridSearchPipeline, test_case: dict, index: int):
    query = test_case["query"]
    exp_type = test_case.get("expected_type")
    exp_ticker = test_case.get("expected_ticker")
    exp_year = test_case.get("expected_year")

    print("\n" + "#" * 90)
    print(f" TEST CASE #{index}: '{query}'")
    print("#" * 90)

    start_time = time.time()

    # --- GIAI ĐOẠN 1 & 2: ROUTING & REWRITING ---
    print("\n[GIAI ĐOẠN 1] -> QUERY ROUTING")
    prep = pipeline.process_user_query(query)
    actual_type = prep.get("type")
    route_pass = (actual_type == exp_type) if exp_type else True
    status_str = "PASSED" if route_pass else f"FAILED (Kỳ vọng: {exp_type})"
    print(f"  * Input Query       : '{query}'")
    print(f"  * Output Route Type : '{actual_type}'")
    print(f"  * Trạng Thái Route  : [{status_str}]")

    if actual_type == "chitchat":
        print("\n[KẾT QUẢ] Câu hỏi giao tiếp xã giao (Chitchat) -> Dừng tại bước routing.")
        return {"route_pass": route_pass, "ticker_pass": True, "time": time.time() - start_time}

    if actual_type == "term_definition":
        print("\n[KẾT QUẢ] Câu hỏi giải thích thuật ngữ tài chính -> Chuyển sang LLM Definition Generator.")
        return {"route_pass": route_pass, "ticker_pass": True, "time": time.time() - start_time}

    # --- GIAI ĐOẠN 3: REWRITING & METADATA EXTRACTION ---
    print("\n[GIAI ĐOẠN 2] -> REWRITING & METADATA EXTRACTION")
    meta = prep.get("metadata_filter", {})
    actual_ticker = meta.get("ticker")
    actual_year = str(meta.get("year")) if meta.get("year") else None
    search_queries = prep.get("search_queries", [query])

    ticker_pass = (actual_ticker == exp_ticker) if exp_ticker else True
    print(f"  * Input Query         : '{query}'")
    print(f"  * Extracted Ticker    : '{actual_ticker}' (Kỳ vọng: '{exp_ticker}') -> [{'MATCH' if ticker_pass else 'MISMATCH'}]")
    print(f"  * Extracted Year      : '{actual_year}' (Kỳ vọng: '{exp_year}')")
    print(f"  * Rewritten Queries   : {search_queries}")

    # --- GIAI ĐOẠN 4: GLOSSARY EXPANSION ---
    print("\n[GIAI ĐOẠN 3] -> GLOSSARY TERM EXPANSION")
    qdrant_filter = pipeline._qdrant_filter(meta)
    expanded_queries = []
    for sq in search_queries:
        eq = expand_query(sq)
        expanded_queries.append(eq)
        print(f"  * Gốc: '{sq}' --> Mở Rộng: '{eq}'")

    # --- GIAI ĐOẠN 5: CANDIDATE SEARCH (BM25 + DENSE) ---
    print("\n[GIAI ĐOẠN 4] -> CANDIDATE RETRIEVAL (BM25 LEXICAL + DENSE VECTOR)")
    total_bm25 = 0
    total_dense = 0
    for eq in expanded_queries:
        bm25_hits = pipeline.bm25_search(eq)
        dense_hits = pipeline.dense_search(eq, qdrant_filter=qdrant_filter)
        total_bm25 += len(bm25_hits)
        total_dense += len(dense_hits)
        print(f"  * BM25 Candidates    : {len(bm25_hits)} chunks | Top 2 IDs: {[h[0] for h in bm25_hits[:2]]}")
        print(f"  * Dense Candidates   : {len(dense_hits)} chunks | Top 2 IDs: {[h[0] for h in dense_hits[:2]]}")

    # --- GIAI ĐOẠN 6: RRF RANK FUSION ---
    print("\n[GIAI ĐOẠN 5] -> RECIPROCAL RANK FUSION (RRF)")
    RRF_ids, content_lookup = pipeline.RRF_fuse(search_queries, qdrant_filter=qdrant_filter)
    print(f"  * RRF Fused Candidates : Tổng cộng {len(RRF_ids)} chunks được gộp thứ hạng")
    print(f"  * Top 3 RRF Chunk IDs   : {RRF_ids[:3]}")

    # --- GIAI ĐOẠN 7: CROSSENCODER RERANKER ---
    print("\n[GIAI ĐOẠN 6] -> CROSSENCODER RERANKER & PARENT EXPANSION")
    top_chunk_ids = pipeline.rerank(query, RRF_ids, content_lookup, top_k=5)
    print(f"  * Top Chunk IDs chọn   : {top_chunk_ids}")

    retrieve_res = pipeline.retrieve(query, top_k=5)
    contexts = retrieve_res.get("context", [])
    print(f"  * Parent Contexts      : Thu được {len(contexts)} đoạn văn bản ngữ cảnh từ MongoDB")

    for i, ctx in enumerate(contexts[:2], 1):
        snippet = ctx[:120].replace("\n", " ")
        print(f"    [{i}] Snippet: {snippet}...")

    elapsed = time.time() - start_time
    print(f"\n⏱️ Thời gian xử lý: {elapsed:.2f}s")
    
    return {
        "route_pass": route_pass,
        "ticker_pass": ticker_pass,
        "time": elapsed,
        "contexts_count": len(contexts)
    }

def main():
    print("=" * 90)
    print(" CHƯƠNG TRÌNH DEBUG & ĐÁNH GIÁ ĐỘ CHÍNH XÁC CHUỖI RETRIEVAL RAG")
    print("=" * 90)

    pipeline = HybridSearchPipeline()
    results = []

    for idx, tc in enumerate(TEST_BENCHMARK, 1):
        res = evaluate_single_query(pipeline, tc, idx)
        results.append(res)

    # --- BẢNG TỔNG HỢP ĐÁNH GIÁ (SUMMARY EVALUATION TABLE) ---
    print("\n" + "=" * 90)
    print(" BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ ĐỘ CHÍNH XÁC HÀM (EVALUATION SUMMARY)")
    print("=" * 90)
    print(f"{'STT':<5} | {'Query Test':<40} | {'Routing Check':<15} | {'Ticker Check':<15} | {'Thời gian':<10}")
    print("-" * 90)

    route_passed_count = 0
    for idx, (tc, res) in enumerate(zip(TEST_BENCHMARK, results), 1):
        q_text = tc['query'][:38]
        r_str = "PASSED" if res["route_pass"] else "FAILED"
        t_str = "PASSED" if res["ticker_pass"] else "FAILED"
        if res["route_pass"]:
            route_passed_count += 1
        print(f"{idx:<5} | {q_text:<40} | {r_str:<15} | {t_str:<15} | {res['time']:.2f}s")

    accuracy = (route_passed_count / len(TEST_BENCHMARK)) * 100
    print("-" * 90)
    print(f"📊 ĐỘ CHÍNH XÁC PHÂN LOẠI ROUTING: {accuracy:.1f}% ({route_passed_count}/{len(TEST_BENCHMARK)} PASSED)")
    print("=" * 90)

if __name__ == "__main__":
    main()
