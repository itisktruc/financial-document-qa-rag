"""
Generation-phase evaluation for the Financial RAG Chatbot.

Loads the benchmark dataset, runs each question through
AnswerGenerator.generate(), and scores the generated answer against
ground_truth using BLEU, ROUGE-1/2/L, METEOR, Exact Match, Normalized
Levenshtein Similarity, and BGE-M3 embedding cosine similarity.

Usage:
    python generation_eval.py [--dataset PATH] [--out PATH] [--limit N]

Dependencies (install once):
    pip install nltk rouge-score python-Levenshtein sentence-transformers tabulate --break-system-packages
    python -m nltk.downloader punkt punkt_tab wordnet omw-1.4
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from statistics import mean
from typing import Any

from tabulate import tabulate

# ----------------------------------------------------------------------------
# Optional heavy deps — imported lazily with clear error messages so the
# script fails fast with an actionable hint rather than a bare ImportError.
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


nltk = _require("nltk")
from rouge_score import rouge_scorer  # noqa: E402
import Levenshtein  # noqa: E402  (package name: python-Levenshtein, import name: Levenshtein)

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    from nltk.translate.meteor_score import meteor_score
    from nltk.tokenize import word_tokenize
except ImportError as e:
    print(f"[FATAL] nltk submodule import failed: {e}", file=sys.stderr)
    sys.exit(1)


def _ensure_nltk_data() -> None:
    """Download required NLTK corpora on first run, silently."""
    needed = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
    ]
    for path, pkg in needed:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg, quiet=True)


_ensure_nltk_data()

# sentence-transformers is the heaviest dep — import lazily, only if the
# backend generator module itself is importable (avoids failing on unrelated
# environments that just want to smoke-test the script).
_st = _require("sentence_transformers", "sentence-transformers")
from sentence_transformers import SentenceTransformer, util as st_util  # noqa: E402


# ----------------------------------------------------------------------------
# Backend under test
# ----------------------------------------------------------------------------
try:
    from app.generation.answer_generator import AnswerGenerator
except ImportError:
    print(
        "[FATAL] Could not import app.generation.answer_generator.AnswerGenerator.\n"
        "        Run this script from the project root (the folder containing 'app/'),\n"
        "        or make sure it's on PYTHONPATH.",
        file=sys.stderr,
    )
    sys.exit(1)


# ----------------------------------------------------------------------------
# Text normalization / metric helpers
# ----------------------------------------------------------------------------

_smoothing = SmoothingFunction().method1
_rouge = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False)


def normalize_text(text: str) -> str:
    """Lowercase, strip acc*punctuation* (keep Vietnamese diacritics), collapse whitespace."""
    text = unicodedata.normalize("NFC", text or "")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u00C0-\u1EF9]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    try:
        return word_tokenize(text)
    except LookupError:
        return text.split()


def compute_bleu(reference: str, hypothesis: str) -> float:
    ref_tokens = [tokenize(normalize_text(reference))]
    hyp_tokens = tokenize(normalize_text(hypothesis))
    if not hyp_tokens or not ref_tokens[0]:
        return 0.0
    return sentence_bleu(ref_tokens, hyp_tokens, smoothing_function=_smoothing)


def compute_rouge(reference: str, hypothesis: str) -> dict[str, float]:
    scores = _rouge.score(reference or "", hypothesis or "")
    return {
        "rouge1": scores["rouge1"].fmeasure,
        "rouge2": scores["rouge2"].fmeasure,
        "rougeL": scores["rougeL"].fmeasure,
    }


def compute_meteor(reference: str, hypothesis: str) -> float:
    ref_tokens = tokenize(normalize_text(reference))
    hyp_tokens = tokenize(normalize_text(hypothesis))
    if not ref_tokens or not hyp_tokens:
        return 0.0
    return meteor_score([ref_tokens], hyp_tokens)


def compute_exact_match(reference: str, hypothesis: str) -> float:
    return 1.0 if normalize_text(reference) == normalize_text(hypothesis) else 0.0


def compute_norm_levenshtein_sim(reference: str, hypothesis: str) -> float:
    a, b = normalize_text(reference), normalize_text(hypothesis)
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 1.0
    dist = Levenshtein.distance(a, b)
    return 1.0 - (dist / max_len)


# ----------------------------------------------------------------------------
# Core evaluation
# ----------------------------------------------------------------------------

def format_contexts(contexts: list[str]) -> list[dict[str, Any]]:
    """Adapt raw context strings from the dataset to the generator's expected
    input shape: a list of dicts with a 'content' key."""
    return [{"content": c} for c in (contexts or [])]


def load_dataset(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        print(f"[FATAL] Dataset not found at {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("[FATAL] Dataset JSON must be a list of items.", file=sys.stderr)
        sys.exit(1)
    return data


def run_evaluation(dataset: list[dict[str, Any]], embed_model: SentenceTransformer) -> list[dict[str, Any]]:
    generator = AnswerGenerator()
    results = []

    for i, item in enumerate(dataset, 1):
        question = item.get("question", "")
        ground_truth = item.get("ground_truth", "")
        contexts = item.get("contexts", [])
        evolution_type = item.get("evolution_type", "unknown")

        formatted_contexts = format_contexts(contexts)

        print(f"[{i}/{len(dataset)}] Generating answer for: {question[:70]}...")
        try:
            gen_result = generator.generate(question, formatted_contexts)
            answer = (gen_result or {}).get("answer", "") if isinstance(gen_result, dict) else str(gen_result)
        except Exception as e:
            print(f"    [WARN] generation failed: {e}", file=sys.stderr)
            answer = ""

        rouge_scores = compute_rouge(ground_truth, answer)

        # Embedding cosine similarity (BGE-M3)
        try:
            embs = embed_model.encode([ground_truth or "", answer or ""], normalize_embeddings=True)
            cos_sim = float(st_util.cos_sim(embs[0], embs[1]).item())
        except Exception as e:
            print(f"    [WARN] embedding similarity failed: {e}", file=sys.stderr)
            cos_sim = 0.0

        row = {
            "question": question,
            "evolution_type": evolution_type,
            "answer": answer,
            "ground_truth": ground_truth,
            "bleu": compute_bleu(ground_truth, answer),
            "rouge1": rouge_scores["rouge1"],
            "rouge2": rouge_scores["rouge2"],
            "rougeL": rouge_scores["rougeL"],
            "meteor": compute_meteor(ground_truth, answer),
            "exact_match": compute_exact_match(ground_truth, answer),
            "levenshtein_sim": compute_norm_levenshtein_sim(ground_truth, answer),
            "cosine_sim": cos_sim,
        }
        results.append(row)

    return results


METRIC_KEYS = [
    "bleu", "rouge1", "rouge2", "rougeL", "meteor",
    "exact_match", "levenshtein_sim", "cosine_sim",
]


def aggregate(results: list[dict[str, Any]]) -> dict[str, float]:
    return {k: mean(r[k] for r in results) if results else 0.0 for k in METRIC_KEYS}


def print_report(results: list[dict[str, Any]]) -> None:
    headers = ["Group", "N", "BLEU", "ROUGE-1", "ROUGE-2", "ROUGE-L", "METEOR", "EM", "Lev.Sim", "Cos.Sim"]
    rows = []

    overall = aggregate(results)
    rows.append([
        "OVERALL", len(results),
        f"{overall['bleu']:.3f}", f"{overall['rouge1']:.3f}", f"{overall['rouge2']:.3f}",
        f"{overall['rougeL']:.3f}", f"{overall['meteor']:.3f}", f"{overall['exact_match']:.3f}",
        f"{overall['levenshtein_sim']:.3f}", f"{overall['cosine_sim']:.3f}",
    ])

    evolution_types = sorted(set(r["evolution_type"] for r in results))
    for et in evolution_types:
        subset = [r for r in results if r["evolution_type"] == et]
        agg = aggregate(subset)
        rows.append([
            et, len(subset),
            f"{agg['bleu']:.3f}", f"{agg['rouge1']:.3f}", f"{agg['rouge2']:.3f}",
            f"{agg['rougeL']:.3f}", f"{agg['meteor']:.3f}", f"{agg['exact_match']:.3f}",
            f"{agg['levenshtein_sim']:.3f}", f"{agg['cosine_sim']:.3f}",
        ])

    print("\n" + "=" * 100)
    print("GENERATION PHASE EVALUATION REPORT")
    print("=" * 100)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Generation phase of the RAG chatbot.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/benchmark_dataset/finance_benchmark.json"),
        help="Path to the benchmark dataset JSON.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evaluation/benchmark_dataset/generation_eval_results.json"),
        help="Where to write the detailed per-item results JSON.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N items (for a quick run).")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    if args.limit:
        dataset = dataset[: args.limit]

    print(f"Loaded {len(dataset)} items from {args.dataset}")
    print("Loading embedding model BAAI/bge-m3 (this can take a while on first run)...")
    embed_model = SentenceTransformer("BAAI/bge-m3")

    results = run_evaluation(dataset, embed_model)
    print_report(results)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Detailed per-item results written to {args.out}")


if __name__ == "__main__":
    main()
