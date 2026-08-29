"""
Citation validation for the Financial RAG Chatbot.

For every benchmark question, runs the end-to-end pipeline (retrieve ->
generate) and checks the inline `[n]` citation markers in the answer
against the `citations` list returned by AnswerGenerator.generate():

    - Citation Precision   : share of inline `[n]` markers that point to a
                              real entry in `citations` (hallucinated-marker
                              detector).
    - Citation Recall      : share of the context chunks provided to the
                              generator that actually got cited somewhere
                              in the answer.
    - Uncited Claim Detector: sentences containing a numeric figure but no
                              `[n]` marker at all (unsupported numeric claim).
    - Claim Grounding Rate  : for each cited sentence, ask gpt-4o-mini
                              whether the cited context snippet actually
                              supports the claim ("LLM-as-a-judge").

Usage:
    python evaluation/citation_validator.py [--dataset PATH] [--out PATH] [--limit N]

Dependencies:
    pip install openai tabulate --break-system-packages

Requires OPENAI_API_KEY in the environment for the grounding judge step.

NOTE on extract_cited_indices(): this script assumes
`app.generation.citation.extract_cited_indices(answer_text)` returns the
1-based marker numbers found in the text, in order of appearance
(duplicates included if a marker like [1] is reused). If your actual
implementation instead returns a de-duplicated set, Citation Precision
below will be computed over unique markers rather than every occurrence —
still directionally correct, just worth knowing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from tabulate import tabulate

try:
    from openai import OpenAI
except ImportError:
    print(
        "[FATAL] Missing dependency 'openai'. Install with:\n"
        "    pip install openai --break-system-packages",
        file=sys.stderr,
    )
    sys.exit(1)

# ----------------------------------------------------------------------------
# Backend under test
# ----------------------------------------------------------------------------
try:
    from app.retrieval.hybrid_search import HybridSearchPipeline
    from app.generation.answer_generator import AnswerGenerator
    from app.generation.citation import extract_cited_indices
except ImportError:
    print(
        "[FATAL] Could not import HybridSearchPipeline / AnswerGenerator / "
        "extract_cited_indices.\n"
        "        Run this script from the project root (the folder containing 'app/'),\n"
        "        or make sure it's on PYTHONPATH.",
        file=sys.stderr,
    )
    sys.exit(1)


MARKER_RE = re.compile(r"\[(\d+)\]")
# Vietnamese-style numbers use '.' as thousands separator and ',' as decimal
# (e.g. 110.365.851.927.250 or 3,5%). This matches any run of digits that
# includes at least 2 digits, optionally with . or , separators, so we don't
# flag lone single digits like ordinal "1." list markers as financial claims.
NUMBER_RE = re.compile(r"\b\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?\b|\b\d+[.,]\d+\b|\b\d{2,}\b")


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
    return [{"content": c} for c in (contexts or [])]


# ----------------------------------------------------------------------------
# Sentence splitting that doesn't break on periods inside numbers
# ----------------------------------------------------------------------------

_NUM_DOT_PLACEHOLDER = "\uE000"  # private-use codepoint, won't collide with real text


def split_sentences(text: str) -> list[str]:
    if not text:
        return []

    # Protect periods that sit inside numbers (thousands separators) so they
    # aren't mistaken for sentence boundaries.
    def _protect(m: re.Match) -> str:
        return m.group(0).replace(".", _NUM_DOT_PLACEHOLDER)

    protected = re.sub(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", _protect, text)

    # Split on '.', '!', '?' followed by whitespace + capital/number, or end of string.
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ỵ0-9]|$)", protected)

    sentences = [s.replace(_NUM_DOT_PLACEHOLDER, ".").strip() for s in raw_sentences if s.strip()]
    return sentences


# ----------------------------------------------------------------------------
# Citation object helpers
# ----------------------------------------------------------------------------

def get_citation_text(citation: Any) -> str:
    """citations[] entries may key the snippet text differently depending on
    how citation.py builds them — try the common candidates."""
    if isinstance(citation, dict):
        for key in ("content", "text", "snippet", "context", "chunk"):
            if citation.get(key):
                return str(citation[key])
        return json.dumps(citation, ensure_ascii=False)
    return str(citation)


# ----------------------------------------------------------------------------
# Metric 1: Citation Precision (hallucinated marker detection)
# ----------------------------------------------------------------------------

def compute_citation_precision(answer: str, citations: list[Any]) -> dict[str, Any]:
    try:
        cited_indices = list(extract_cited_indices(answer))
    except Exception as e:
        print(f"    [WARN] extract_cited_indices failed, falling back to regex: {e}", file=sys.stderr)
        cited_indices = [int(m) for m in MARKER_RE.findall(answer)]

    n_citations = len(citations)
    valid = [idx for idx in cited_indices if isinstance(idx, int) and 1 <= idx <= n_citations]
    hallucinated = [idx for idx in cited_indices if idx not in valid]

    total = len(cited_indices)
    precision = (len(valid) / total) if total > 0 else None  # None = no markers to judge

    return {
        "total_markers": total,
        "valid_markers": len(valid),
        "hallucinated_markers": sorted(set(hallucinated)),
        "precision": precision,
    }


# ----------------------------------------------------------------------------
# Metric 2: Citation Recall (share of provided chunks actually cited)
# ----------------------------------------------------------------------------

def compute_citation_recall(retrieved_contexts: list[str], answer: str) -> dict[str, Any]:
    try:
        cited_indices = set(extract_cited_indices(answer))
    except Exception:
        cited_indices = set(int(m) for m in MARKER_RE.findall(answer))

    n_provided = len(retrieved_contexts)
    if n_provided == 0:
        return {"provided_chunks": 0, "cited_chunks": 0, "recall": None}

    # citations are 1-indexed and assumed to map 1:1 onto the order of
    # retrieved_contexts passed into generate().
    cited_in_range = {idx for idx in cited_indices if 1 <= idx <= n_provided}
    recall = len(cited_in_range) / n_provided

    return {
        "provided_chunks": n_provided,
        "cited_chunks": len(cited_in_range),
        "recall": recall,
    }


# ----------------------------------------------------------------------------
# Metric 3: Uncited Claim Detector
# ----------------------------------------------------------------------------

def detect_uncited_numeric_claims(answer: str) -> list[dict[str, Any]]:
    flagged = []
    for sentence in split_sentences(answer):
        # Strip existing markers before checking for numbers so "[1]" itself
        # never counts as a numeric claim.
        sentence_wo_markers = MARKER_RE.sub("", sentence)
        has_number = bool(NUMBER_RE.search(sentence_wo_markers))
        has_marker = bool(MARKER_RE.search(sentence))
        if has_number and not has_marker:
            flagged.append({"sentence": sentence, "numbers_found": NUMBER_RE.findall(sentence_wo_markers)})
    return flagged


# ----------------------------------------------------------------------------
# Metric 4: Claim Grounding Rate (LLM-as-a-judge)
# ----------------------------------------------------------------------------

_JUDGE_SYSTEM_PROMPT = (
    "You are a strict fact-checking assistant for a financial RAG system. "
    "You will be given a CLAIM (a sentence from a generated answer) and a "
    "SOURCE SNIPPET (the cited context). Decide whether the SOURCE SNIPPET "
    "actually supports the CLAIM. Respond with exactly one word, YES or NO, "
    "on the first line, followed by a one-sentence reason on the next line."
)


def judge_claim_grounding(client: "OpenAI", claim: str, source_snippet: str) -> dict[str, Any]:
    prompt = f"CLAIM:\n{claim}\n\nSOURCE SNIPPET:\n{source_snippet}"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        content = resp.choices[0].message.content.strip()
        first_line = content.splitlines()[0].strip().upper() if content else ""
        supported = first_line.startswith("YES")
        reason = content.splitlines()[1].strip() if len(content.splitlines()) > 1 else ""
        return {"supported": supported, "reason": reason, "raw": content}
    except Exception as e:
        return {"supported": None, "reason": f"judge call failed: {e}", "raw": None}


def compute_claim_grounding_rate(
    client: "OpenAI", answer: str, citations: list[Any]
) -> dict[str, Any]:
    judged = []
    for sentence in split_sentences(answer):
        markers = [int(m) for m in MARKER_RE.findall(sentence)]
        if not markers:
            continue  # only cited sentences are judged here
        # Use the first valid cited index's snippet as the grounding source.
        valid_markers = [m for m in markers if 1 <= m <= len(citations)]
        if not valid_markers:
            judged.append({
                "sentence": sentence,
                "markers": markers,
                "supported": False,
                "reason": "all markers hallucinated (no matching citation object)",
            })
            continue
        snippet = get_citation_text(citations[valid_markers[0] - 1])
        verdict = judge_claim_grounding(client, sentence, snippet)
        judged.append({
            "sentence": sentence,
            "markers": markers,
            "supported": verdict["supported"],
            "reason": verdict["reason"],
        })

    scored = [j for j in judged if j["supported"] is not None]
    rate = (sum(1 for j in scored if j["supported"]) / len(scored)) if scored else None

    return {"judged_sentences": judged, "grounding_rate": rate}


# ----------------------------------------------------------------------------
# End-to-end run
# ----------------------------------------------------------------------------

def run_pipeline_and_validate(dataset: list[dict[str, Any]], client: "OpenAI") -> list[dict[str, Any]]:
    pipeline = HybridSearchPipeline()
    generator = AnswerGenerator()

    results = []
    for i, item in enumerate(dataset, 1):
        question = item.get("question", "")
        evolution_type = item.get("evolution_type", "unknown")
        print(f"[{i}/{len(dataset)}] {question[:70]}...")

        try:
            retrieval_result = pipeline.retrieve(question)
            retrieved_contexts = [c["content"] for c in retrieval_result.get("context", [])]
        except Exception as e:
            print(f"    [WARN] retrieval failed: {e}", file=sys.stderr)
            retrieved_contexts = []

        try:
            formatted_contexts = format_contexts_for_generator(retrieved_contexts)
            gen_result = generator.generate(question, formatted_contexts)
            answer = (gen_result or {}).get("answer", "")
            citations = (gen_result or {}).get("citations", [])
        except Exception as e:
            print(f"    [WARN] generation failed: {e}", file=sys.stderr)
            answer, citations = "", []

        precision_info = compute_citation_precision(answer, citations)
        recall_info = compute_citation_recall(retrieved_contexts, answer)
        uncited_claims = detect_uncited_numeric_claims(answer)
        grounding_info = compute_claim_grounding_rate(client, answer, citations)

        results.append({
            "question": question,
            "evolution_type": evolution_type,
            "answer": answer,
            "n_citations_returned": len(citations),
            "n_context_chunks_provided": len(retrieved_contexts),
            "precision": precision_info,
            "recall": recall_info,
            "uncited_numeric_claims": uncited_claims,
            "grounding": grounding_info,
        })

    return results


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def _safe_mean(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return (sum(vals) / len(vals)) if vals else None


def print_report(results: list[dict[str, Any]]) -> None:
    precisions = [r["precision"]["precision"] for r in results]
    recalls = [r["recall"]["recall"] for r in results]
    grounding_rates = [r["grounding"]["grounding_rate"] for r in results]
    total_uncited = sum(len(r["uncited_numeric_claims"]) for r in results)
    total_hallucinated = sum(len(r["precision"]["hallucinated_markers"]) for r in results)

    summary_rows = [
        ["Citation Precision", f"{_safe_mean(precisions):.3f}" if _safe_mean(precisions) is not None else "N/A"],
        ["Citation Recall", f"{_safe_mean(recalls):.3f}" if _safe_mean(recalls) is not None else "N/A"],
        ["Claim Grounding Rate", f"{_safe_mean(grounding_rates):.3f}" if _safe_mean(grounding_rates) is not None else "N/A"],
        ["Total hallucinated markers", total_hallucinated],
        ["Total uncited numeric claims", total_uncited],
        ["Questions evaluated", len(results)],
    ]

    print("\n" + "=" * 80)
    print("CITATION VALIDATION SUMMARY")
    print("=" * 80)
    print(tabulate(summary_rows, headers=["Metric", "Value"], tablefmt="grid"))

    print("\n" + "=" * 80)
    print("ERROR LOG — hallucinated citation markers")
    print("=" * 80)
    any_halluc = False
    for r in results:
        halluc = r["precision"]["hallucinated_markers"]
        if halluc:
            any_halluc = True
            print(f"\nQ: {r['question'][:80]}")
            print(f"   Hallucinated markers: {halluc}  (only {r['n_citations_returned']} citations returned)")
    if not any_halluc:
        print("None found.")

    print("\n" + "=" * 80)
    print("ERROR LOG — uncited numeric claims")
    print("=" * 80)
    any_uncited = False
    for r in results:
        for claim in r["uncited_numeric_claims"]:
            any_uncited = True
            print(f"\nQ: {r['question'][:80]}")
            print(f"   Sentence: {claim['sentence']}")
            print(f"   Numbers found without a citation marker: {claim['numbers_found']}")
    if not any_uncited:
        print("None found.")

    print("\n" + "=" * 80)
    print("ERROR LOG — ungrounded cited claims (LLM judge said NO)")
    print("=" * 80)
    any_ungrounded = False
    for r in results:
        for j in r["grounding"]["judged_sentences"]:
            if j["supported"] is False:
                any_ungrounded = True
                print(f"\nQ: {r['question'][:80]}")
                print(f"   Sentence: {j['sentence']}")
                print(f"   Cited marker(s): {j['markers']}")
                print(f"   Judge reason: {j['reason']}")
    if not any_ungrounded:
        print("None found.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate citation correctness in the RAG chatbot's answers.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/benchmark_dataset/finance_benchmark.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evaluation/results/citation_validation_results.json"),
    )
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N items (quick run).")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "[FATAL] OPENAI_API_KEY is not set. The Claim Grounding Rate step "
            "calls gpt-4o-mini and needs it.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = OpenAI()

    dataset = load_dataset_json(args.dataset)
    if args.limit:
        dataset = dataset[: args.limit]
    print(f"Loaded {len(dataset)} items from {args.dataset}")

    results = run_pipeline_and_validate(dataset, client)
    print_report(results)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Detailed per-question results written to {args.out}")


if __name__ == "__main__":
    main()
