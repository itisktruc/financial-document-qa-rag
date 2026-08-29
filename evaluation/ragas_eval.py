"""
End-to-end semantic RAG evaluation using Ragas.

Runs the full pipeline (retrieval -> generation) for every question in the
benchmark dataset, assembles a HF Dataset in the shape Ragas expects, and
scores it with faithfulness, answer_relevancy, context_precision, and
context_recall using gpt-4o-mini as the evaluator LLM.

Usage:
    python evaluation/ragas_eval.py [--dataset PATH] [--out PATH] [--limit N]

Dependencies:
    pip install ragas datasets langchain-openai tabulate --break-system-packages

Requires OPENAI_API_KEY to be set in the environment (Ragas' default LLM
metrics call OpenAI directly under the hood via the LangChain wrapper).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from tabulate import tabulate

# ----------------------------------------------------------------------------
# Optional heavy deps — fail fast with an actionable message.
# ----------------------------------------------------------------------------


def _require(module_name: str, pip_name: str | None = None):
    try:
        return __import__(module_name)
    except ImportError:
        pip_name = pip_name or module_name
        print(
            f"[FATAL] Missing dependency '{module_name}'. Install with:\n"
            f"    pip install {pip_name} --break-system-packages",
            file=sys.stderr,
        )
        sys.exit(1)


_require("datasets")
_require("ragas")
_require("langchain_openai", "langchain-openai")

from datasets import Dataset  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
from ragas import evaluate  # noqa: E402
from ragas.metrics import (  # noqa: E402
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# ----------------------------------------------------------------------------
# Backend under test
# ----------------------------------------------------------------------------
try:
    from app.retrieval.hybrid_search import HybridSearchPipeline
    from app.generation.answer_generator import AnswerGenerator
except ImportError:
    print(
        "[FATAL] Could not import HybridSearchPipeline / AnswerGenerator.\n"
        "        Run this script from the project root (the folder containing 'app/'),\n"
        "        or make sure it's on PYTHONPATH.",
        file=sys.stderr,
    )
    sys.exit(1)


# ----------------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------------

def load_dataset_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"[FATAL] Dataset not found at {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("[FATAL] Dataset JSON must be a list of items.", file=sys.stderr)
        sys.exit(1)
    return data


def format_contexts_for_generator(contexts: list[str]) -> list[dict[str, Any]]:
    """Adapt raw context strings into the shape AnswerGenerator.generate() expects."""
    return [{"content": c} for c in (contexts or [])]


# ----------------------------------------------------------------------------
# End-to-end pipeline run
# ----------------------------------------------------------------------------

def run_pipeline(dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pipeline = HybridSearchPipeline()
    generator = AnswerGenerator()

    rows = []
    for i, item in enumerate(dataset, 1):
        question = item.get("question", "")
        ground_truth = item.get("ground_truth", "")
        evolution_type = item.get("evolution_type", "unknown")

        print(f"[{i}/{len(dataset)}] {question[:70]}...")

        # --- Retrieval ---
        try:
            retrieval_result = pipeline.retrieve(question)
            retrieved_contexts = [c["content"] for c in retrieval_result.get("context", [])]
        except Exception as e:
            print(f"    [WARN] retrieval failed: {e}", file=sys.stderr)
            retrieved_contexts = []

        # --- Generation ---
        try:
            formatted_contexts = format_contexts_for_generator(retrieved_contexts)
            gen_result = generator.generate(question, formatted_contexts)
            answer = (gen_result or {}).get("answer", "") if isinstance(gen_result, dict) else str(gen_result)
        except Exception as e:
            print(f"    [WARN] generation failed: {e}", file=sys.stderr)
            answer = ""

        # Ragas requires non-empty contexts/answer per row to score reliably;
        # keep placeholders rather than dropping the row so nothing silently
        # disappears from the report.
        if not retrieved_contexts:
            retrieved_contexts = [""]

        rows.append({
            "question": question,
            "answer": answer,
            "contexts": retrieved_contexts,
            "ground_truth": ground_truth,
            "evolution_type": evolution_type,
        })

    return rows


# ----------------------------------------------------------------------------
# Ragas evaluation
# ----------------------------------------------------------------------------

def run_ragas(rows: list[dict[str, Any]]) -> Any:
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "[FATAL] OPENAI_API_KEY is not set. Ragas' LLM-based metrics "
            "(faithfulness, answer_relevancy, context_precision, context_recall) "
            "call gpt-4o-mini and need it.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Ragas dataset only needs question/answer/contexts/ground_truth;
    # evolution_type is dropped for scoring but kept in our own row dicts
    # for the per-question breakdown printed/saved afterward.
    ragas_dataset = Dataset.from_list([
        {
            "question": r["question"],
            "answer": r["answer"],
            "contexts": r["contexts"],
            "ground_truth": r["ground_truth"],
        }
        for r in rows
    ])

    evaluator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    print("\nRunning Ragas evaluation (gpt-4o-mini as evaluator LLM)...")
    result = evaluate(
        dataset=ragas_dataset,
        metrics=metrics,
        llm=evaluator_llm,
    )
    return result


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

METRIC_NAMES = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def print_summary(result_df) -> None:
    headers = ["Metric", "Mean Score"]
    rows = []
    for m in METRIC_NAMES:
        if m in result_df.columns:
            mean_val = result_df[m].dropna().mean()
            rows.append([m, f"{mean_val:.3f}" if mean_val == mean_val else "N/A"])  # NaN check
        else:
            rows.append([m, "N/A"])

    print("\n" + "=" * 70)
    print("RAGAS EVALUATION SUMMARY (overall)")
    print("=" * 70)
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    if "evolution_type" in result_df.columns:
        print("\nBy evolution_type:")
        for et in sorted(result_df["evolution_type"].dropna().unique()):
            subset = result_df[result_df["evolution_type"] == et]
            sub_rows = []
            for m in METRIC_NAMES:
                if m in subset.columns:
                    mean_val = subset[m].dropna().mean()
                    sub_rows.append([m, f"{mean_val:.3f}" if mean_val == mean_val else "N/A"])
            print(f"\n  -- {et} (n={len(subset)}) --")
            print(tabulate(sub_rows, headers=headers, tablefmt="simple"))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ragas end-to-end evaluation on the RAG chatbot.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/benchmark_dataset/finance_benchmark.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evaluation/results/ragas_results.json"),
    )
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N items (quick run).")
    args = parser.parse_args()

    dataset = load_dataset_json(args.dataset)
    if args.limit:
        dataset = dataset[: args.limit]
    print(f"Loaded {len(dataset)} items from {args.dataset}")

    rows = run_pipeline(dataset)
    ragas_result = run_ragas(rows)

    result_df = ragas_result.to_pandas()
    # attach evolution_type back for the per-group breakdown (row order is preserved)
    result_df["evolution_type"] = [r["evolution_type"] for r in rows]

    print_summary(result_df)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    per_question = []
    for i, r in enumerate(rows):
        record = {
            "question": r["question"],
            "answer": r["answer"],
            "contexts": r["contexts"],
            "ground_truth": r["ground_truth"],
            "evolution_type": r["evolution_type"],
        }
        for m in METRIC_NAMES:
            if m in result_df.columns:
                val = result_df.iloc[i][m]
                record[m] = None if val != val else float(val)  # NaN -> None
        per_question.append(record)

    overall = {
        m: (float(result_df[m].dropna().mean()) if m in result_df.columns and not result_df[m].dropna().empty else None)
        for m in METRIC_NAMES
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"overall": overall, "per_question": per_question}, f, ensure_ascii=False, indent=2)
    print(f"Detailed per-question results written to {args.out}")


if __name__ == "__main__":
    main()
