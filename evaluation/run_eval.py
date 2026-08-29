"""
Master evaluation CLI for the Financial RAG Chatbot.

Orchestrates the five evaluation modules in this directory:

    retrieval_eval.py      -> Hit Rate@K, Precision@K, Recall@K
    generation_eval.py     -> BLEU, ROUGE-1/2/L, METEOR, EM, Levenshtein, BGE-M3 cosine sim
    ragas_eval.py           -> Faithfulness, Answer Relevancy, Context Precision/Recall
    citation_validator.py  -> Citation Precision/Recall, Uncited Claims, Grounding Rate
    performance_eval.py    -> Latency p50/p90/p95, TTFT, Token Usage

Each module is invoked as a subprocess (so a crash in one never takes down
the others), with --dataset/--out/--limit passed through. After all
requested stages finish, this script reads back each module's output JSON,
computes/extracts aggregate scores, writes a consolidated
`<out-dir>/master_eval_report.json`, and prints an executive summary table.

Usage:
    python evaluation/run_eval.py --all
    python evaluation/run_eval.py --retrieval --generation
    python evaluation/run_eval.py --all --limit 5 --out-dir evaluation/results_smoke

Dependencies:
    pip install tabulate --break-system-packages
    (plus whatever each individual module needs — see their own docstrings)

NOTE on NDCG@K: the current evaluation/retrieval_eval.py computes Hit
Rate@K, Precision@K, and Recall@K only — it does not compute NDCG@K. This
runner reports NDCG@K as "N/A" rather than fabricate a number; add NDCG
scoring to retrieval_eval.py if you need it in the master report.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from tabulate import tabulate

SCRIPT_DIR = Path(__file__).resolve().parent

# Stage order matters for both execution and the executive summary table.
STAGE_ORDER = ["retrieval", "generation", "ragas", "citation", "performance"]

STAGE_CONFIG = {
    "retrieval": {
        "script": "retrieval_eval.py",
        "out_file": "retrieval_results.json",
        "label": "Retrieval Evaluation",
    },
    "generation": {
        "script": "generation_eval.py",
        "out_file": "generation_results.json",
        "label": "Generation Evaluation",
    },
    "ragas": {
        "script": "ragas_eval.py",
        "out_file": "ragas_results.json",
        "label": "Ragas Semantic Evaluation",
    },
    "citation": {
        "script": "citation_validator.py",
        "out_file": "citation_results.json",
        "label": "Citation Validation",
    },
    "performance": {
        "script": "performance_eval.py",
        "out_file": "performance_results.json",
        "label": "Performance Benchmark",
    },
}


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Master CLI runner for the RAG chatbot evaluation suite.")
    parser.add_argument("--all", action="store_true", help="Run all 5 evaluation stages sequentially.")
    parser.add_argument("--retrieval", action="store_true", help="Run retrieval_eval.py")
    parser.add_argument("--generation", action="store_true", help="Run generation_eval.py")
    parser.add_argument("--ragas", action="store_true", help="Run ragas_eval.py")
    parser.add_argument("--citation", action="store_true", help="Run citation_validator.py")
    parser.add_argument("--performance", action="store_true", help="Run performance_eval.py")

    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/benchmark_dataset/finance_benchmark.json"),
        help="Path to benchmark dataset JSON.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("evaluation/results"),
        help="Directory where individual module outputs and the master report are written.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only the first N items (quick run).")

    # performance_eval.py-specific pass-through, since it needs a mode/base-url
    # that the other four stages don't. Kept optional with a safe default so
    # `--all` still works with zero extra flags when no server is running.
    parser.add_argument(
        "--perf-mode",
        choices=["local", "ttft", "all"],
        default="local",
        help="Mode passed to performance_eval.py. 'ttft'/'all' require a running server (see --base-url).",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the running FastAPI server, used only if --perf-mode is 'ttft' or 'all'.",
    )

    args = parser.parse_args()

    selected = args.all or any([args.retrieval, args.generation, args.ragas, args.citation, args.performance])
    if not selected:
        print("[INFO] No stage flags given — defaulting to --all.\n")
        args.all = True

    return args


def resolve_stages(args: argparse.Namespace) -> list[str]:
    if args.all:
        return list(STAGE_ORDER)
    flags = {
        "retrieval": args.retrieval,
        "generation": args.generation,
        "ragas": args.ragas,
        "citation": args.citation,
        "performance": args.performance,
    }
    return [s for s in STAGE_ORDER if flags[s]]


# ----------------------------------------------------------------------------
# Stage execution
# ----------------------------------------------------------------------------

def build_command(stage: str, args: argparse.Namespace) -> list[str]:
    cfg = STAGE_CONFIG[stage]
    script_path = SCRIPT_DIR / cfg["script"]
    out_path = args.out_dir / cfg["out_file"]

    cmd = [
        sys.executable,
        str(script_path),
        "--dataset", str(args.dataset),
        "--out", str(out_path),
    ]
    if args.limit is not None:
        cmd += ["--limit", str(args.limit)]

    if stage == "performance":
        cmd += ["--mode", args.perf_mode]
        if args.perf_mode in ("ttft", "all"):
            cmd += ["--base-url", args.base_url]

    return cmd


def run_stage(stage: str, args: argparse.Namespace) -> dict[str, Any]:
    cfg = STAGE_CONFIG[stage]
    script_path = SCRIPT_DIR / cfg["script"]

    header = f" STAGE: {cfg['label']} ({cfg['script']}) "
    print("\n" + "#" * 90)
    print(f"#{header.center(88)}#")
    print("#" * 90)

    if not script_path.exists():
        msg = f"Script not found: {script_path}"
        print(f"[ERROR] {msg}")
        return {"stage": stage, "status": "error", "duration_s": 0.0, "error": msg}

    cmd = build_command(stage, args)
    print(f"$ {' '.join(cmd)}\n")

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=str(SCRIPT_DIR.parent))
        duration = time.perf_counter() - t0
        if proc.returncode != 0:
            print(f"\n[ERROR] {cfg['label']} exited with code {proc.returncode} after {duration:.1f}s.")
            return {"stage": stage, "status": "error", "duration_s": duration, "error": f"exit code {proc.returncode}"}
        print(f"\n[OK] {cfg['label']} completed in {duration:.1f}s.")
        return {"stage": stage, "status": "ok", "duration_s": duration, "error": None}
    except Exception as e:
        duration = time.perf_counter() - t0
        print(f"\n[ERROR] {cfg['label']} raised an exception after {duration:.1f}s: {e}")
        return {"stage": stage, "status": "error", "duration_s": duration, "error": str(e)}


# ----------------------------------------------------------------------------
# Aggregation — each module's output JSON has a different shape, so each
# gets its own small aggregator that extracts/derives the headline numbers.
# ----------------------------------------------------------------------------

def _mean(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return statistics.mean(vals) if vals else None


def _percentiles(values: list[float], ps=(50, 90, 95)) -> dict[int, float | None]:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return {p: None for p in ps}
    if len(vals) == 1:
        return {p: vals[0] for p in ps}
    qs = statistics.quantiles(vals, n=100, method="inclusive")
    return {p: qs[p - 1] for p in ps}


def aggregate_retrieval(data: Any) -> dict[str, Any]:
    # retrieval_eval.py writes a flat list of per-question rows with hit@K/precision@K/recall@K.
    if not isinstance(data, list) or not data:
        return {}
    ks = [3, 5, 10]
    out = {}
    for k in ks:
        out[f"hit_rate@{k}"] = _mean([r.get(f"hit@{k}") for r in data])
        out[f"precision@{k}"] = _mean([r.get(f"precision@{k}") for r in data])
        out[f"recall@{k}"] = _mean([r.get(f"recall@{k}") for r in data])
        out[f"ndcg@{k}"] = None  # not computed by retrieval_eval.py — see module docstring
    out["n_questions"] = len(data)
    return out


def aggregate_generation(data: Any) -> dict[str, Any]:
    # generation_eval.py writes a flat list of per-item rows with each metric.
    if not isinstance(data, list) or not data:
        return {}
    keys = ["bleu", "rouge1", "rouge2", "rougeL", "meteor", "exact_match", "levenshtein_sim", "cosine_sim"]
    out = {k: _mean([r.get(k) for r in data]) for k in keys}
    out["n_questions"] = len(data)
    return out


def aggregate_ragas(data: Any) -> dict[str, Any]:
    # ragas_eval.py writes {"overall": {...}, "per_question": [...]}
    if not isinstance(data, dict):
        return {}
    overall = data.get("overall", {})
    out = dict(overall)
    out["n_questions"] = len(data.get("per_question", []))
    return out


def aggregate_citation(data: Any) -> dict[str, Any]:
    # citation_validator.py writes a flat list of per-question rows with nested dicts.
    if not isinstance(data, list) or not data:
        return {}
    precisions = [r.get("precision", {}).get("precision") for r in data]
    recalls = [r.get("recall", {}).get("recall") for r in data]
    grounding = [r.get("grounding", {}).get("grounding_rate") for r in data]
    total_hallucinated = sum(len(r.get("precision", {}).get("hallucinated_markers", [])) for r in data)
    total_uncited = sum(len(r.get("uncited_numeric_claims", [])) for r in data)

    return {
        "citation_precision": _mean(precisions),
        "citation_recall": _mean(recalls),
        "claim_grounding_rate": _mean(grounding),
        "total_hallucinated_markers": total_hallucinated,
        "total_uncited_numeric_claims": total_uncited,
        "n_questions": len(data),
    }


def aggregate_performance(data: Any) -> dict[str, Any]:
    # performance_eval.py writes {"local": [...], "ttft": [...]} (keys depend on --mode used).
    if not isinstance(data, dict):
        return {}
    out: dict[str, Any] = {}

    local = data.get("local")
    if local:
        for metric, label in [
            ("retrieval_latency_s", "retrieval_latency_s"),
            ("generation_latency_s", "generation_latency_s"),
            ("e2e_latency_s", "e2e_latency_s"),
        ]:
            values = [r.get(metric) for r in local]
            p = _percentiles(values)
            out[f"{label}_p50"] = p[50]
            out[f"{label}_p90"] = p[90]
            out[f"{label}_p95"] = p[95]
        out["avg_prompt_tokens"] = _mean([r.get("prompt_tokens") for r in local])
        out["avg_completion_tokens"] = _mean([r.get("completion_tokens") for r in local])
        out["avg_total_tokens"] = _mean([r.get("total_tokens") for r in local])
        out["n_local_runs"] = len(local)

    ttft = data.get("ttft")
    if ttft:
        ttft_values = [r.get("ttft_s") for r in ttft if r.get("error") is None]
        p = _percentiles(ttft_values)
        out["ttft_p50"] = p[50]
        out["ttft_p90"] = p[90]
        out["ttft_p95"] = p[95]
        out["n_ttft_runs"] = len(ttft)
        out["n_ttft_failed"] = sum(1 for r in ttft if r.get("error") is not None)

    return out


AGGREGATORS = {
    "retrieval": aggregate_retrieval,
    "generation": aggregate_generation,
    "ragas": aggregate_ragas,
    "citation": aggregate_citation,
    "performance": aggregate_performance,
}


def consolidate(stage_run_log: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    master: dict[str, Any] = {"run_log": stage_run_log, "stages": {}}

    for stage in STAGE_ORDER:
        cfg = STAGE_CONFIG[stage]
        out_path = args.out_dir / cfg["out_file"]
        entry: dict[str, Any] = {"output_file": str(out_path)}

        if not out_path.exists():
            entry["status"] = "no_data"
            master["stages"][stage] = entry
            continue

        try:
            with open(out_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            entry["status"] = "ok"
            entry["aggregate"] = AGGREGATORS[stage](raw)
        except Exception as e:
            entry["status"] = "parse_error"
            entry["error"] = str(e)

        master["stages"][stage] = entry

    return master


# ----------------------------------------------------------------------------
# Executive summary
# ----------------------------------------------------------------------------

def _fmt(v: Any, digits: int = 3) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def print_executive_summary(master: dict[str, Any]) -> None:
    print("\n" + "=" * 100)
    print("EXECUTIVE SUMMARY — Financial RAG Chatbot Evaluation")
    print("=" * 100)

    # --- Run log (timing + status) ---
    log_rows = [
        [r["stage"], STAGE_CONFIG[r["stage"]]["label"], r["status"].upper(), f"{r['duration_s']:.1f}s", r["error"] or ""]
        for r in master["run_log"]
    ]
    print("\nStage execution log:")
    print(tabulate(log_rows, headers=["Stage", "Module", "Status", "Duration", "Error"], tablefmt="grid"))

    # --- Retrieval ---
    r = master["stages"].get("retrieval", {}).get("aggregate", {})
    if r:
        rows = [[k, _fmt(r.get(f"{k}@5"))] for k in ("hit_rate", "precision", "recall", "ndcg")]
        print(f"\nRetrieval (K=5, n={r.get('n_questions', 'N/A')}):")
        print(tabulate(rows, headers=["Metric", "Score"], tablefmt="simple"))

    # --- Generation ---
    g = master["stages"].get("generation", {}).get("aggregate", {})
    if g:
        rows = [
            ["BLEU", _fmt(g.get("bleu"))],
            ["ROUGE-1", _fmt(g.get("rouge1"))],
            ["ROUGE-2", _fmt(g.get("rouge2"))],
            ["ROUGE-L", _fmt(g.get("rougeL"))],
            ["METEOR", _fmt(g.get("meteor"))],
            ["Exact Match", _fmt(g.get("exact_match"))],
            ["Levenshtein Sim.", _fmt(g.get("levenshtein_sim"))],
            ["BGE-M3 Cosine Sim.", _fmt(g.get("cosine_sim"))],
        ]
        print(f"\nGeneration (n={g.get('n_questions', 'N/A')}):")
        print(tabulate(rows, headers=["Metric", "Score"], tablefmt="simple"))

    # --- Ragas ---
    rg = master["stages"].get("ragas", {}).get("aggregate", {})
    if rg:
        rows = [
            [m, _fmt(rg.get(m))]
            for m in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
        ]
        print(f"\nRagas Semantic Evaluation (n={rg.get('n_questions', 'N/A')}):")
        print(tabulate(rows, headers=["Metric", "Score"], tablefmt="simple"))

    # --- Citation ---
    c = master["stages"].get("citation", {}).get("aggregate", {})
    if c:
        rows = [
            ["Citation Precision", _fmt(c.get("citation_precision"))],
            ["Citation Recall", _fmt(c.get("citation_recall"))],
            ["Claim Grounding Rate", _fmt(c.get("claim_grounding_rate"))],
            ["Total Hallucinated Markers", _fmt(c.get("total_hallucinated_markers"), 0)],
            ["Total Uncited Numeric Claims", _fmt(c.get("total_uncited_numeric_claims"), 0)],
        ]
        print(f"\nCitation Validation (n={c.get('n_questions', 'N/A')}):")
        print(tabulate(rows, headers=["Metric", "Score"], tablefmt="simple"))

    # --- Performance ---
    p = master["stages"].get("performance", {}).get("aggregate", {})
    if p:
        rows = []
        if "e2e_latency_s_p50" in p:
            rows += [
                ["Retrieval latency p50/p90/p95 (s)", f"{_fmt(p.get('retrieval_latency_s_p50'))} / {_fmt(p.get('retrieval_latency_s_p90'))} / {_fmt(p.get('retrieval_latency_s_p95'))}"],
                ["Generation latency p50/p90/p95 (s)", f"{_fmt(p.get('generation_latency_s_p50'))} / {_fmt(p.get('generation_latency_s_p90'))} / {_fmt(p.get('generation_latency_s_p95'))}"],
                ["E2E latency p50/p90/p95 (s)", f"{_fmt(p.get('e2e_latency_s_p50'))} / {_fmt(p.get('e2e_latency_s_p90'))} / {_fmt(p.get('e2e_latency_s_p95'))}"],
                ["Avg prompt / completion / total tokens", f"{_fmt(p.get('avg_prompt_tokens'), 1)} / {_fmt(p.get('avg_completion_tokens'), 1)} / {_fmt(p.get('avg_total_tokens'), 1)}"],
            ]
        if "ttft_p50" in p:
            rows.append(["TTFT p50/p90/p95 (s)", f"{_fmt(p.get('ttft_p50'))} / {_fmt(p.get('ttft_p90'))} / {_fmt(p.get('ttft_p95'))}"])
        if rows:
            print(f"\nPerformance:")
            print(tabulate(rows, headers=["Metric", "Value"], tablefmt="simple"))

    print("\n" + "=" * 100 + "\n")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    stages = resolve_stages(args)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Dataset : {args.dataset}")
    print(f"Out dir : {args.out_dir}")
    print(f"Limit   : {args.limit if args.limit is not None else 'none (full dataset)'}")
    print(f"Stages  : {', '.join(stages)}")

    run_log = []
    suite_start = time.perf_counter()
    for stage in stages:
        result = run_stage(stage, args)
        run_log.append(result)
    suite_duration = time.perf_counter() - suite_start

    master = consolidate(run_log, args)
    master["dataset"] = str(args.dataset)
    master["out_dir"] = str(args.out_dir)
    master["limit"] = args.limit
    master["total_duration_s"] = suite_duration

    print_executive_summary(master)

    out_path = args.out_dir / "master_eval_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)
    print(f"Master report written to {out_path}")

    n_failed = sum(1 for r in run_log if r["status"] != "ok")
    if n_failed:
        print(f"\n[SUMMARY] {n_failed}/{len(run_log)} stage(s) failed — see run log above and in the master report.")
        sys.exit(1)


if __name__ == "__main__":
    main()
