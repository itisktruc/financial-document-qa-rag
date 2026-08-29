"""
Retrieval-phase evaluation for the Financial RAG Chatbot.

Since the benchmark dataset has no ground-truth chunk IDs, relevance is
judged by text-overlap matching: a retrieved context "hits" an expected
context if one string contains the other (after normalization) or their
token-level Jaccard similarity exceeds 0.8.

Computes Hit Rate@K, Precision@K, and Recall@K for K = [3, 5, 10].

Usage:
    python evaluation/retrieval_eval.py [--dataset PATH] [--out PATH] [--limit N]
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

try:
    from app.retrieval.hybrid_search import HybridSearchPipeline
except ImportError:
    print(
        "[FATAL] Could not import HybridSearchPipeline.\n"
        "        Run this script from the project root (the folder containing 'app/'),\n"
        "        or make sure it's on PYTHONPATH.",
        file=sys.stderr,
    )
    sys.exit(1)

K_VALUES = [3, 5, 10]
JACCARD_THRESHOLD = 0.8

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^\w\s\u00C0-\u1EF9]", flags=re.UNICODE)


def normalize(text: str) -> str:
    """Strip HTML tags, normalize Unicode (NFC), lowercase, strip punctuation, collapse whitespace."""
    if not text:
        return ""
    
    # 1. Xóa HTML tags (tránh lỗi khi text chứa <table><tr>...)
    text = _TAG_RE.sub(" ", text)
    
    # 2. Chuẩn hóa Unicode tiếng Việt về chuẩn tổ hợp (NFC)
    # Cực kỳ quan trọng để "Tiếng Việt" và "Tiếng Việt" được xem là giống nhau
    text = unicodedata.normalize("NFC", text)
    
    # 3. Đưa về in thường
    text = text.lower()
    
    # 4. Xóa ký tự đặc biệt (giữ lại chữ tiếng Việt và số)
    text = _NON_WORD_RE.sub(" ", text)
    
    # 5. Xóa khoảng trắng thừa
    text = _WS_RE.sub(" ", text).strip()
    return text


def jaccard_similarity(a: str, b: str) -> float:
    set_a, set_b = set(a.split()), set(b.split())
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


def is_match(expected: str, retrieved: str) -> bool:
    """Kiểm tra xem chunk trả về có khớp với ground truth context không."""
    e, r = normalize(expected), normalize(retrieved)
    if not e or not r:
        return False
        
    # Cách 1: Substring thông thường
    if e in r or r in e:
        return True
        
    # Cách 2: Jaccard Similarity (Token level)
    if jaccard_similarity(e, r) > JACCARD_THRESHOLD:
        return True
        
    # Cách 3: Fallback mạnh tay (Dành cho lỗi bóc HTML Table dính chữ)
    # Ví dụ: HTML bóc ra "Số cuối nămTriệu đồng", nhưng expected là "Số cuối năm Triệu đồng"
    e_nospace = e.replace(" ", "")
    r_nospace = r.replace(" ", "")
    if e_nospace in r_nospace or r_nospace in e_nospace:
        return True
        
    return False


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


def extract_context_text(entry: Any) -> str:
    """Trích xuất text từ kết quả trả về của pipeline."""
    if isinstance(entry, dict):
        # Ưu tiên các key phổ biến chứa text
        for key in ("content", "text", "chunk", "context"):
            if entry.get(key):
                return str(entry[key])
        return json.dumps(entry, ensure_ascii=False)
    return str(entry)


def evaluate_query(expected_contexts: list[str], retrieved_texts: list[str], k: int) -> dict[str, float]:
    """Tính toán metrics dựa trên tập top-k text trả về."""
    top_k = retrieved_texts[:k]

    if not expected_contexts:
        return {"hit": 0.0, "precision": 0.0, "recall": 0.0}

    # Tính Precision@K
    matched_retrieved = sum(
        1 for r in top_k if any(is_match(exp, r) for exp in expected_contexts)
    )
    precision = matched_retrieved / k if k > 0 else 0.0

    # Tính Recall@K
    matched_expected = sum(
        1 for exp in expected_contexts if any(is_match(exp, r) for r in top_k)
    )
    recall = matched_expected / len(expected_contexts)

    # Tính Hit Rate@K
    hit = 1.0 if matched_expected > 0 else 0.0

    return {"hit": hit, "precision": precision, "recall": recall}


def run_evaluation(dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pipeline = HybridSearchPipeline()
    max_k = max(K_VALUES)
    results = []

    for i, item in enumerate(dataset, 1):
        question = item.get("question", "")
        expected_contexts = item.get("contexts", [])
        evolution_type = item.get("evolution_type", "unknown")

        print(f"[{i}/{len(dataset)}] {question[:70]}...")

        try:
            # Lấy top_k tối đa (10) sau đó slice lại để tính điểm cho K=3, K=5
            result = pipeline.retrieve(question, top_k=max_k)
            raw_contexts = result.get("context", []) if isinstance(result, dict) else result
        except Exception as e:
            print(f"    [WARN] retrieval failed: {e}", file=sys.stderr)
            raw_contexts = []

        retrieved_texts = [extract_context_text(c) for c in raw_contexts]

        row: dict[str, Any] = {
            "question": question,
            "evolution_type": evolution_type,
            "n_expected": len(expected_contexts),
            "n_retrieved": len(retrieved_texts),
        }
        
        for k in K_VALUES:
            metrics = evaluate_query(expected_contexts, retrieved_texts, k)
            row[f"hit@{k}"] = metrics["hit"]
            row[f"precision@{k}"] = metrics["precision"]
            row[f"recall@{k}"] = metrics["recall"]

        # In log debug nếu miss kết quả để dễ trace
        if row[f"hit@{max_k}"] == 0 and expected_contexts:
            print(f"    -> [MISS] Không tìm thấy expected context trong top {max_k}.")

        results.append(row)

    return results


def print_report(results: list[dict[str, Any]]) -> None:
    headers = ["K", "Hit Rate@K", "Precision@K", "Recall@K", "N"]
    rows = []
    for k in K_VALUES:
        hit = mean(r[f"hit@{k}"] for r in results) if results else 0.0
        prec = mean(r[f"precision@{k}"] for r in results) if results else 0.0
        rec = mean(r[f"recall@{k}"] for r in results) if results else 0.0
        rows.append([k, f"{hit:.3f}", f"{prec:.3f}", f"{rec:.3f}", len(results)])

    print("\n" + "=" * 80)
    print("RETRIEVAL PHASE EVALUATION — OVERALL")
    print("=" * 80)
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    evolution_types = sorted(set(r["evolution_type"] for r in results))
    for et in evolution_types:
        subset = [r for r in results if r["evolution_type"] == et]
        sub_rows = []
        for k in K_VALUES:
            hit = mean(r[f"hit@{k}"] for r in subset)
            prec = mean(r[f"precision@{k}"] for r in subset)
            rec = mean(r[f"recall@{k}"] for r in subset)
            sub_rows.append([k, f"{hit:.3f}", f"{prec:.3f}", f"{rec:.3f}", len(subset)])
        print(f"\n-- evolution_type: {et} (n={len(subset)}) --")
        print(tabulate(sub_rows, headers=headers, tablefmt="simple"))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Retrieval phase of the RAG chatbot.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation/benchmark_dataset/finance_benchmark.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evaluation/results/retrieval_eval_results.json"),
    )
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N items.")
    args = parser.parse_args()

    dataset = load_dataset_json(args.dataset)
    if args.limit:
        dataset = dataset[: args.limit]
    print(f"Loaded {len(dataset)} items from {args.dataset}")

    results = run_evaluation(dataset)
    print_report(results)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Detailed per-question results written to {args.out}")


if __name__ == "__main__":
    main()