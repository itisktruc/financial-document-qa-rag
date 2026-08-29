"""
Performance evaluation for the Financial RAG Chatbot.

Measures, over a sample of benchmark queries:
    - Retrieval latency        (HybridSearchPipeline.retrieve)
    - Generation latency       (AnswerGenerator.generate)
    - End-to-end latency       (retrieval + generation, sequential)
    - Token usage              (prompt / completion / total, via LangChain
                                 callback when available, else tiktoken estimate)
    - Time to First Token      (TTFT) against the live FastAPI streaming
                                 endpoint POST /chat, measured separately over HTTP

p50 / p90 / p95 are reported for every latency-type metric.

Usage:
    # Local pipeline latency + token benchmark (no server needed):
    python performance_eval.py --mode local --n 20

    # TTFT benchmark against a running server:
    python performance_eval.py --mode ttft --base-url http://localhost:8000 --n 20

    # Both:
    python performance_eval.py --mode all --base-url http://localhost:8000 --n 20

Dependencies:
    pip install tiktoken httpx tabulate --break-system-packages
    # optional, only needed for real (non-estimated) token counts:
    pip install tiktoken httpx tabulate --break-system-packages
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from tabulate import tabulate

# ----------------------------------------------------------------------------
# Optional deps
# ----------------------------------------------------------------------------

try:
    import tiktoken
except ImportError:
    tiktoken = None
    print("[WARN] tiktoken not installed — token counts will be unavailable. "
          "pip install tiktoken --break-system-packages", file=sys.stderr)

try:
    import httpx
except ImportError:
    httpx = None  # only required for --mode ttft/all

try:
    from langchain_community.callbacks import get_openai_callback
    _HAS_LC_CALLBACK = True
except ImportError:
    _HAS_LC_CALLBACK = False


# ----------------------------------------------------------------------------
# Dataset loading
# ----------------------------------------------------------------------------

def load_queries(dataset_path: Path, n: int) -> list[str]:
    if not dataset_path.exists():
        print(f"[FATAL] Dataset not found at {dataset_path}", file=sys.stderr)
        sys.exit(1)
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = [item["question"] for item in data if item.get("question")]
    if len(questions) < n:
        print(f"[WARN] Dataset only has {len(questions)} questions; using all of them.", file=sys.stderr)
    # Cycle through if the dataset is smaller than n, so we always benchmark n runs.
    if not questions:
        print("[FATAL] Dataset has no questions.", file=sys.stderr)
        sys.exit(1)
    return [questions[i % len(questions)] for i in range(n)]


# ----------------------------------------------------------------------------
# Token counting
# ----------------------------------------------------------------------------

_ENCODING = None
if tiktoken is not None:
    try:
        _ENCODING = tiktoken.encoding_for_model("gpt-4o-mini")
    except KeyError:
        _ENCODING = tiktoken.get_encoding("cl100k_base")


def estimate_tokens(text: str) -> int:
    """Fallback token estimate via tiktoken when real usage isn't reported."""
    if not text:
        return 0
    if _ENCODING is not None:
        return len(_ENCODING.encode(text))
    # crude fallback: ~4 chars/token for English, worse for Vietnamese, but
    # better than nothing if tiktoken isn't installed at all.
    return max(1, len(text) // 3)


def build_prompt_text(query: str, contexts: list[dict[str, Any]] | list[str]) -> str:
    """Reconstruct an approximation of the prompt sent to the LLM, for
    estimating input tokens when real usage isn't available."""
    ctx_text = "\n".join(
        c.get("content", "") if isinstance(c, dict) else str(c) for c in (contexts or [])
    )
    return f"{ctx_text}\n\nQuestion: {query}"


# ----------------------------------------------------------------------------
# Local latency + token benchmark
# ----------------------------------------------------------------------------

def run_local_benchmark(queries: list[str], top_k: int = 5) -> list[dict[str, Any]]:
    from app.retrieval.hybrid_search import HybridSearchPipeline
    from app.generation.answer_generator import AnswerGenerator

    pipeline = HybridSearchPipeline()
    generator = AnswerGenerator()

    results = []

    for i, query in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {query[:70]}...")
        row: dict[str, Any] = {"query": query}

        # --- Retrieval ---
        t0 = time.perf_counter()
        try:
            retrieval_result = pipeline.retrieve(query, top_k)
        except Exception as e:
            print(f"    [WARN] retrieval failed: {e}", file=sys.stderr)
            retrieval_result = {"context": []}
        t1 = time.perf_counter()
        row["retrieval_latency_s"] = t1 - t0

        contexts = retrieval_result.get("context", []) if isinstance(retrieval_result, dict) else retrieval_result

        # --- Generation ---
        prompt_tokens = completion_tokens = total_tokens = None
        t2 = time.perf_counter()
        try:
            if _HAS_LC_CALLBACK:
                with get_openai_callback() as cb:
                    gen_result = generator.generate(query, contexts)
                if cb.total_tokens:  # only trust it if the callback actually captured a call
                    prompt_tokens = cb.prompt_tokens
                    completion_tokens = cb.completion_tokens
                    total_tokens = cb.total_tokens
            else:
                gen_result = generator.generate(query, contexts)
        except Exception as e:
            print(f"    [WARN] generation failed: {e}", file=sys.stderr)
            gen_result = {"answer": ""}
        t3 = time.perf_counter()
        row["generation_latency_s"] = t3 - t2
        row["e2e_latency_s"] = t3 - t0

        answer = (gen_result or {}).get("answer", "") if isinstance(gen_result, dict) else str(gen_result)

        # Fall back to tiktoken estimate if the callback didn't capture real usage
        # (e.g. generator doesn't route through a LangChain ChatOpenAI callback handler).
        if total_tokens is None:
            prompt_text = build_prompt_text(query, contexts)
            prompt_tokens = estimate_tokens(prompt_text)
            completion_tokens = estimate_tokens(answer)
            total_tokens = prompt_tokens + completion_tokens
            row["token_source"] = "tiktoken_estimate"
        else:
            row["token_source"] = "langchain_callback_actual"

        row["prompt_tokens"] = prompt_tokens
        row["completion_tokens"] = completion_tokens
        row["total_tokens"] = total_tokens
        row["answer_len_chars"] = len(answer)

        results.append(row)

    return results


# ----------------------------------------------------------------------------
# TTFT benchmark (async, against the live streaming endpoint)
# ----------------------------------------------------------------------------
#
# This measures wall-clock time from request send to the first bytes/chunk
# received from POST /chat, assuming the endpoint streams its response
# (e.g. StreamingResponse / SSE from FastAPI). If /chat is not currently
# streaming, TTFT == full response latency, which still gives a useful
# upper-bound baseline until streaming is added.

async def _measure_ttft_once(client: "httpx.AsyncClient", base_url: str, query: str) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/chat"
    payload = {"query": query}  # adjust field name to match your /chat request schema

    t0 = time.perf_counter()
    first_chunk_time = None
    total_bytes = 0

    try:
        async with client.stream("POST", url, json=payload, timeout=60.0) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                if not chunk:
                    continue
                if first_chunk_time is None:
                    first_chunk_time = time.perf_counter()
                total_bytes += len(chunk)
        t_end = time.perf_counter()
        ttft = (first_chunk_time - t0) if first_chunk_time is not None else None
        total_latency = t_end - t0
        return {"query": query, "ttft_s": ttft, "total_latency_s": total_latency, "bytes": total_bytes, "error": None}
    except Exception as e:
        return {"query": query, "ttft_s": None, "total_latency_s": None, "bytes": 0, "error": str(e)}


async def run_ttft_benchmark(queries: list[str], base_url: str, concurrency: int = 1) -> list[dict[str, Any]]:
    if httpx is None:
        print("[FATAL] httpx not installed. pip install httpx --break-system-packages", file=sys.stderr)
        sys.exit(1)

    results = []
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient() as client:
        async def bound_measure(q: str, idx: int):
            async with sem:
                print(f"[TTFT {idx}/{len(queries)}] {q[:70]}...")
                return await _measure_ttft_once(client, base_url, q)

        tasks = [bound_measure(q, i + 1) for i, q in enumerate(queries)]
        results = await asyncio.gather(*tasks)

    return list(results)


# ----------------------------------------------------------------------------
# Percentiles + reporting
# ----------------------------------------------------------------------------

def percentiles(values: list[float], ps: tuple[int, ...] = (50, 90, 95)) -> dict[int, float]:
    values = sorted(v for v in values if v is not None)
    if not values:
        return {p: float("nan") for p in ps}
    out = {}
    for p in ps:
        # nearest-rank method via statistics.quantiles (n=100) for stability on small N
        if len(values) == 1:
            out[p] = values[0]
            continue
        qs = statistics.quantiles(values, n=100, method="inclusive")
        out[p] = qs[p - 1]
    return out


def print_local_report(results: list[dict[str, Any]]) -> None:
    retrieval = [r["retrieval_latency_s"] for r in results]
    generation = [r["generation_latency_s"] for r in results]
    e2e = [r["e2e_latency_s"] for r in results]
    prompt_toks = [r["prompt_tokens"] for r in results]
    completion_toks = [r["completion_tokens"] for r in results]
    total_toks = [r["total_tokens"] for r in results]

    def row_for(name: str, values: list[float], unit: str = "s") -> list[str]:
        p = percentiles(values)
        return [
            name,
            f"{statistics.mean(values):.3f}",
            f"{min(values):.3f}",
            f"{p[50]:.3f}",
            f"{p[90]:.3f}",
            f"{p[95]:.3f}",
            f"{max(values):.3f}",
        ]

    headers = ["Metric", "Mean", "Min", "p50", "p90", "p95", "Max"]
    rows = [
        row_for("Retrieval latency (s)", retrieval),
        row_for("Generation latency (s)", generation),
        row_for("End-to-end latency (s)", e2e),
    ]

    print("\n" + "=" * 90)
    print("LOCAL PIPELINE LATENCY REPORT")
    print("=" * 90)
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    tok_source = results[0].get("token_source", "unknown") if results else "unknown"
    tok_rows = [
        ["Prompt tokens", f"{statistics.mean(prompt_toks):.1f}", min(prompt_toks), max(prompt_toks)],
        ["Completion tokens", f"{statistics.mean(completion_toks):.1f}", min(completion_toks), max(completion_toks)],
        ["Total tokens", f"{statistics.mean(total_toks):.1f}", min(total_toks), max(total_toks)],
    ]
    print(f"\nTOKEN USAGE (source: {tok_source})")
    print(tabulate(tok_rows, headers=["Metric", "Mean", "Min", "Max"], tablefmt="grid"))
    print()


def print_ttft_report(results: list[dict[str, Any]]) -> None:
    ok = [r for r in results if r["error"] is None]
    failed = [r for r in results if r["error"] is not None]

    ttft_vals = [r["ttft_s"] for r in ok if r["ttft_s"] is not None]
    total_vals = [r["total_latency_s"] for r in ok if r["total_latency_s"] is not None]

    print("\n" + "=" * 90)
    print("TTFT (TIME TO FIRST TOKEN) REPORT — via POST /chat streaming")
    print("=" * 90)

    if not ttft_vals:
        print("No successful streaming responses captured.")
    else:
        p_ttft = percentiles(ttft_vals)
        p_total = percentiles(total_vals)
        rows = [
            ["TTFT (s)", f"{statistics.mean(ttft_vals):.3f}", f"{p_ttft[50]:.3f}", f"{p_ttft[90]:.3f}", f"{p_ttft[95]:.3f}", f"{max(ttft_vals):.3f}"],
            ["Total stream latency (s)", f"{statistics.mean(total_vals):.3f}", f"{p_total[50]:.3f}", f"{p_total[90]:.3f}", f"{p_total[95]:.3f}", f"{max(total_vals):.3f}"],
        ]
        print(tabulate(rows, headers=["Metric", "Mean", "p50", "p90", "p95", "Max"], tablefmt="grid"))

    print(f"\nSuccessful: {len(ok)}/{len(results)}   Failed: {len(failed)}")
    for r in failed[:5]:
        print(f"    [FAIL] {r['query'][:50]}... -> {r['error']}")
    print()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark latency, TTFT, and token usage of the RAG chatbot.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/benchmark_dataset/finance_benchmark.json"),
        help="Path to the benchmark dataset JSON.",
    )
    parser.add_argument("--n", type=int, default=20, help="Number of sample queries to benchmark.")
    parser.add_argument("--top-k", type=int, default=5, help="top_k passed to pipeline.retrieve().")
    parser.add_argument(
        "--mode",
        choices=["local", "ttft", "all"],
        default="local",
        help="'local' = retrieval/generation/e2e latency + tokens (in-process). "
             "'ttft' = TTFT against a running server. 'all' = both.",
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the running FastAPI server (for --mode ttft/all).")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent in-flight requests for the TTFT benchmark.")
    parser.add_argument("--out", type=Path, default=Path("evaluation/benchmark_dataset/performance_eval_results.json"))
    args = parser.parse_args()

    queries = load_queries(args.dataset, args.n)
    print(f"Loaded {len(queries)} sample queries from {args.dataset}\n")

    output: dict[str, Any] = {}

    if args.mode in ("local", "all"):
        local_results = run_local_benchmark(queries, top_k=args.top_k)
        print_local_report(local_results)
        output["local"] = local_results

    if args.mode in ("ttft", "all"):
        ttft_results = asyncio.run(run_ttft_benchmark(queries, args.base_url, concurrency=args.concurrency))
        print_ttft_report(ttft_results)
        output["ttft"] = ttft_results

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Detailed results written to {args.out}")


if __name__ == "__main__":
    main()
