"""
Retrieval-phase evaluation for the Financial RAG Chatbot.

Đánh giá bằng CHUNK ID, không dùng text-overlap/Jaccard nữa:
  - Ground truth mỗi câu hỏi là 1 danh sách chunk_id (của (các) chunk chứa
    đúng thông tin để trả lời câu hỏi đó) -- đọc từ dataset qua
    get_expected_chunk_ids() (xem field name được chấp nhận bên dưới).
  - Retrieved là list[chunk_id] mà HybridSearchPipeline.retrieve() trả về
    trong result["chunk_ids"] (ĐÃ rerank, TRƯỚC khi gộp/mở rộng sang parent
    -- đúng đơn vị retrieval cần đánh giá, không phải text của parent).
  - So khớp = so ID sau khi chuẩn hoá (dùng lại đúng hàm _normalize_cid()
    của app/retrieval/hybrid_search.py để đảm bảo cùng 1 cách chuẩn hoá
    với pipeline, tránh chunk_id lệch định dạng gạch ngang/hex).

Cách này tách biệt hẳn "khả năng truy xuất đúng chunk" khỏi "khả năng câu
trả lời cuối cùng giống ground truth" -- không còn phụ thuộc vào việc câu
chữ trong context có "giống" ground truth text hay không.

Tính Hit Rate@K, Precision@K, Recall@K, và MRR@K cho K = [3, 5, 10].

Câu hỏi bị QueryRouter phân loại "calculation" (hoặc có evolution_type=
"calculation" trong benchmark) được định tuyến sang CalculationService --
giống hệt luồng production trong app/main.py -- thay vì gọi thẳng
pipeline.retrieve() (nhánh đó LUÔN trả context=[]/chunk_ids=[] cho route
"calculation" theo đúng thiết kế, xem app/retrieval/hybrid_search.py).

LƯU Ý về nhánh Calculation: CalculationService hiện KHÔNG trả chunk_id thật
sự nhất quán trong citations (xem docstring của _retrieve_via_calculation()
bên dưới) -- kết quả eval cho evolution_type="calculation" nên được đọc
với sự dè dặt nhất định, đây là hạn chế của calculation_service.py chứ
không phải của cách tính metric ở đây.

Dataset format (mỗi item) -- KHỚP ĐÚNG format thực tế đang dùng
(vd evaluation/benchmark_dataset/A32.json):
    {
        "question": "...",
        "evolution_type": "simple" | "calculation" | "hallucination" | ...,
        "ground_truth": "<chunk_id>"
                          hoặc "<chunk_id_1>, <chunk_id_2>, ..." (1 STRING,
                          nhiều chunk_id ngăn cách bởi dấu phẩy -- KHÔNG
                          phải JSON list),
        "contexts": [...],   # text thô, KHÔNG dùng để so khớp retrieval nữa
        "citation": "..."    # nhãn hiển thị cho người đọc, KHÔNG phải chunk_id
    }
Script cũng chấp nhận field "expected_chunk_ids"/"chunk_ids"/
"ground_truth_chunk_ids" (dạng JSON list) để tương thích ngược, xem
_EXPECTED_ID_KEYS/get_expected_chunk_ids().

Vài item có evolution_type="hallucination" (đôi khi cả evolution_type khác
do lỗi gán nhãn dataset) mang "ground_truth" là CÂU VĂN, không phải chunk_id
-- đây là item test "hệ thống có tránh bịa số liệu khi không có dữ liệu để
trả lời không", không có chunk đúng nào để retrieve. Các item này được tách
riêng khỏi bảng OVERALL (không có target thì không thể tính Hit/Precision/
Recall/MRR có ý nghĩa), nhưng vẫn được liệt kê ở breakdown theo
evolution_type và trong file --out để không mất thông tin.

Usage:
    python evaluation/retrieval_eval.py [--dataset PATH] [--out PATH] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean
from typing import Any
from tabulate import tabulate

try:
    from app.retrieval.hybrid_search import HybridSearchPipeline, _normalize_cid as normalize_chunk_id
    from app.calculation.calculation_service import CalculationService
except ImportError:
    print(
        "[FATAL] Could not import HybridSearchPipeline.\n"
        "        Run this script from the project root (the folder containing 'app/'),\n"
        "        or make sure it's on PYTHONPATH.",
        file=sys.stderr,
    )
    sys.exit(1)

K_VALUES = [3, 5, 10]

# Thứ tự ưu tiên các tên field trong dataset chứa ground-truth chunk_id.
# "ground_truth" là tên field THỰC TẾ đang dùng trong benchmark hiện có
# (A32.json...) -- ưu tiên cao nhất. KHÔNG dùng "contexts" làm fallback vì
# field đó hiện đang chứa TEXT THÔ (bảng HTML/đoạn văn), không phải chunk_id
# -- coi nó là chunk_id sẽ so khớp sai hoàn toàn.
_EXPECTED_ID_KEYS = ("ground_truth", "expected_chunk_ids", "chunk_ids", "ground_truth_chunk_ids")

# chunk_id trong hệ thống luôn là hex 32 ký tự (md5 hexdigest -- xem
# make_id() trong app/ingestion/chunker.py, hoặc uuid4().hex ở chunker cũ),
# không dấu gạch ngang sau khi qua normalize_chunk_id(). Dùng để phát hiện
# giá trị "ground_truth" KHÔNG phải chunk_id (vd câu trả lời dạng văn bản
# của item evolution_type="hallucination", hoặc lỗi gán nhãn dataset).
_CHUNK_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def _split_ground_truth_value(value: Any) -> list[str]:
    """Ground truth có thể là:
      - list[str]: mỗi phần tử 1 chunk_id (format JSON "chuẩn").
      - str: 1 chunk_id đơn, HOẶC NHIỀU chunk_id ngăn cách bởi dấu phẩy
        trong CÙNG 1 chuỗi -- đúng format thực tế của A32.json, vd:
        "989d210db3d2acfb1fc6e5eda6fb5906, 73b1ec9dbbe433164bab76c1df7ecc6c".
        Tuyệt đối KHÔNG lặp qua str này bằng `for v in value` (sẽ lặp theo
        TỪNG KÝ TỰ) -- phải split(",") trước.
    """
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    if isinstance(value, str):
        return [p.strip() for p in value.split(",") if p.strip()]
    return []


def get_expected_chunk_ids(item: dict[str, Any]) -> tuple[list[str], str]:
    """Lấy danh sách chunk_id đúng (ground truth) của 1 câu hỏi -- CÓ THỂ
    LÀ NHIỀU chunk_id (câu hỏi cần tổng hợp thông tin từ nhiều đoạn/nhiều
    bảng mới trả lời đủ), không giả định chỉ có đúng 1 chunk đúng.

    Trả về (chunk_ids, status):
      - status="ok"      : tìm được >=1 chunk_id hợp lệ (khớp _CHUNK_ID_RE).
      - status="invalid" : field ground-truth CÓ tồn tại/không rỗng, nhưng
                            không parse được chunk_id hợp lệ nào (vd câu văn
                            của item hallucination, hoặc lỗi gán nhãn).
      - status="missing" : không field nào trong _EXPECTED_ID_KEYS tồn tại.

    Duyệt _EXPECTED_ID_KEYS theo thứ tự ưu tiên, DỪNG NGAY ở field ĐẦU TIÊN
    có giá trị không rỗng (không fallback tiếp sang field khác nếu field đó
    tồn tại nhưng không chứa chunk_id hợp lệ -- tránh vô tình lấy nhầm field
    khác không liên quan). Mỗi chunk_id được chuẩn hoá bằng normalize_chunk_id()
    (= _normalize_cid() của hybrid_search.py) để khớp định dạng với chunk_id
    pipeline trả về lúc retrieve, dedupe nhưng GIỮ THỨ TỰ xuất hiện gốc.
    """
    for key in _EXPECTED_ID_KEYS:
        raw_value = item.get(key)
        if not raw_value:
            continue
        pieces = _split_ground_truth_value(raw_value)
        if not pieces:
            continue

        seen: set[str] = set()
        valid_ids: list[str] = []
        for p in pieces:
            cid = normalize_chunk_id(p)
            if cid and _CHUNK_ID_RE.match(cid) and cid not in seen:
                seen.add(cid)
                valid_ids.append(cid)

        if valid_ids:
            return valid_ids, "ok"
        return [], "invalid"

    return [], "missing"


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


def evaluate_query(expected_ids: list[str], retrieved_ids: list[str], k: int) -> dict[str, float]:
    """Tính Hit/Precision/Recall/MRR @K dựa trên so khớp chunk_id (exact
    match sau chuẩn hoá), không còn dựa vào độ tương đồng văn bản."""
    expected_set = set(expected_ids)
    top_k = retrieved_ids[:k]

    if not expected_set:
        return {"hit": 0.0, "precision": 0.0, "recall": 0.0, "mrr": 0.0}

    matched_retrieved = sum(1 for cid in top_k if cid in expected_set)
    precision = matched_retrieved / k if k > 0 else 0.0

    matched_expected = len(expected_set & set(top_k))
    recall = matched_expected / len(expected_set)

    hit = 1.0 if matched_expected > 0 else 0.0

    mrr = 0.0
    for rank, cid in enumerate(top_k, start=1):
        if cid in expected_set:
            mrr = 1.0 / rank
            break

    return {"hit": hit, "precision": precision, "recall": recall, "mrr": mrr}


def _retrieve_via_calculation(calc_pipeline: "CalculationService", question: str) -> list[str]:
    """Chạy nhánh CalculationService cho 1 câu hỏi, trả về list chunk_id
    (đã chuẩn hoá, dedup, giữ thứ tự xuất hiện) suy ra từ citations trả về.

    Dùng field 'chunk_id' (đã được calculation_service.py._fetch_operand()
    gán ĐÚNG chunk/parent_id thật đã match, xem fix trong
    app/calculation/calculation_service.py) -- KHÔNG dùng 'doc_id' nữa
    (field đó là document_id của cả file nguồn, không phải chunk_id, dù
    trước đây bị dùng nhầm làm proxy). Nếu chưa deploy bản calculation_service.py
    đã fix, fallback về 'doc_id' để script vẫn chạy được (kết quả khi đó
    vẫn mang giới hạn cũ).
    """
    calc_result = calc_pipeline.calculate(question)
    retrieved_ids: list[str] = []
    seen: set[str] = set()
    for cit in (calc_result.citations or []):
        raw_id = cit.get("chunk_id") or cit.get("doc_id")
        cid = normalize_chunk_id(raw_id)
        if not cid or cid in seen:
            continue
        seen.add(cid)
        retrieved_ids.append(cid)
    return retrieved_ids


def run_evaluation(dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pipeline = HybridSearchPipeline()
    calc_pipeline = CalculationService(search_pipeline=pipeline)
    max_k = max(K_VALUES)
    results = []
    n_missing = 0            # không field ground-truth nào tồn tại -- nghi vấn lỗi dataset
    n_invalid_other = 0      # có field nhưng không parse được chunk_id, evolution_type != hallucination -- nghi vấn lỗi gán nhãn
    n_hallucination_empty = 0  # evolution_type=hallucination + không có chunk_id -- ĐÚNG THIẾT KẾ, không phải lỗi

    for i, item in enumerate(dataset, 1):
        question = item.get("question", "")
        evolution_type = item.get("evolution_type", "unknown")
        expected_ids, gt_status = get_expected_chunk_ids(item)

        if gt_status == "missing":
            n_missing += 1
            print(f"    [WARN] Không tìm thấy field ground-truth nào trong {_EXPECTED_ID_KEYS}.", file=sys.stderr)
        elif gt_status == "invalid":
            if evolution_type == "hallucination":
                n_hallucination_empty += 1
            else:
                n_invalid_other += 1
                raw_gt = item.get("ground_truth")
                print(f"    [WARN] ground_truth không parse được thành chunk_id hợp lệ "
                      f"(evolution_type={evolution_type!r}): {str(raw_gt)[:80]!r}", file=sys.stderr)

        print(f"[{i}/{len(dataset)}] {question[:70]}...")

        retrieved_ids: list[str] = []
        routed_to_calculation = False
        try:
            route_info = pipeline.process_user_query(question)
            routed_to_calculation = (
                route_info.get("type") == "calculation" or evolution_type == "calculation"
            )

            if routed_to_calculation:
                print("    -> [Routing] Kích hoạt nhánh CalculationService.")
                retrieved_ids = _retrieve_via_calculation(calc_pipeline, question)
            else:
                # Lấy top_k tối đa (10) sau đó slice lại để tính điểm cho K=3, K=5.
                # result["chunk_ids"]: list chunk_id ĐÃ rerank, TRƯỚC khi mở
                # rộng/dedup sang parent -- đúng đơn vị cần đánh giá retrieval,
                # không phải "context" (parent text) như bản cũ.
                result = pipeline.retrieve(question, top_k=max_k, prep=route_info)
                raw_ids = result.get("chunk_ids", []) if isinstance(result, dict) else []
                retrieved_ids = [normalize_chunk_id(cid) for cid in raw_ids]
        except Exception as e:
            print(f"    [WARN] retrieval failed: {e}", file=sys.stderr)
            retrieved_ids = []

        row: dict[str, Any] = {
            "question": question,
            "evolution_type": evolution_type,
            "routed_to_calculation": routed_to_calculation,
            "ground_truth_status": gt_status,  # "ok" | "invalid" | "missing"
            "expected_chunk_ids": expected_ids,
            "retrieved_chunk_ids": retrieved_ids,
            "n_expected": len(expected_ids),
            "n_retrieved": len(retrieved_ids),
        }

        for k in K_VALUES:
            metrics = evaluate_query(expected_ids, retrieved_ids, k)
            row[f"hit@{k}"] = metrics["hit"]
            row[f"precision@{k}"] = metrics["precision"]
            row[f"recall@{k}"] = metrics["recall"]
            row[f"mrr@{k}"] = metrics["mrr"]

        # In log debug nếu miss kết quả để dễ trace
        if row[f"hit@{max_k}"] == 0 and expected_ids:
            print(f"    -> [MISS] Không tìm thấy expected chunk_id trong top {max_k}.")

        results.append(row)

    if n_missing:
        print(
            f"\n[WARN] {n_missing}/{len(dataset)} câu hỏi KHÔNG có field ground-truth nào "
            f"(kiểm tra dataset có field {_EXPECTED_ID_KEYS} chưa).",
            file=sys.stderr,
        )
    if n_invalid_other:
        print(
            f"[WARN] {n_invalid_other}/{len(dataset)} câu hỏi có field ground-truth nhưng "
            "KHÔNG parse được chunk_id hợp lệ nào (evolution_type khác 'hallucination' -- "
            "nghi ngờ lỗi gán nhãn dataset, xem log [WARN] phía trên để biết item cụ thể).",
            file=sys.stderr,
        )
    if n_hallucination_empty:
        print(
            f"[INFO] {n_hallucination_empty}/{len(dataset)} câu hỏi evolution_type='hallucination' "
            "không có chunk_id đúng -- ĐÚNG THIẾT KẾ (test hệ thống nhận biết không có dữ liệu để "
            "trả lời), không phải lỗi dataset. Các câu này bị loại khỏi bảng OVERALL.",
        )

    return results


def print_report(results: list[dict[str, Any]]) -> None:
    headers = ["K", "Hit Rate@K", "Precision@K", "Recall@K", "MRR@K", "N"]
    answerable = [r for r in results if r.get("ground_truth_status") == "ok"]
    n_excluded = len(results) - len(answerable)

    rows = []
    for k in K_VALUES:
        hit = mean(r[f"hit@{k}"] for r in answerable) if answerable else 0.0
        prec = mean(r[f"precision@{k}"] for r in answerable) if answerable else 0.0
        rec = mean(r[f"recall@{k}"] for r in answerable) if answerable else 0.0
        mrr = mean(r[f"mrr@{k}"] for r in answerable) if answerable else 0.0
        rows.append([k, f"{hit:.3f}", f"{prec:.3f}", f"{rec:.3f}", f"{mrr:.3f}", len(answerable)])

    print("\n" + "=" * 80)
    print("RETRIEVAL PHASE EVALUATION — OVERALL (chunk-id based)")
    print("=" * 80)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    if n_excluded:
        print(f"\n(Đã loại {n_excluded}/{len(results)} câu KHÔNG có chunk_id ground-truth hợp lệ "
              f"khỏi bảng OVERALL -- xem log [WARN]/[INFO] phía trên hoặc breakdown theo "
              f"evolution_type bên dưới.)")

    n_calc = sum(1 for r in results if r.get("routed_to_calculation"))
    if n_calc:
        print(f"\n(Trong đó {n_calc}/{len(results)} câu được định tuyến qua CalculationService "
              f"thay vì hybrid search trực tiếp -- xem giới hạn về chunk_id ở docstring "
              f"_retrieve_via_calculation().)")

    evolution_types = sorted(set(r["evolution_type"] for r in results))
    for et in evolution_types:
        subset = [r for r in results if r["evolution_type"] == et]
        sub_rows = []
        for k in K_VALUES:
            hit = mean(r[f"hit@{k}"] for r in subset)
            prec = mean(r[f"precision@{k}"] for r in subset)
            rec = mean(r[f"recall@{k}"] for r in subset)
            mrr = mean(r[f"mrr@{k}"] for r in subset)
            sub_rows.append([k, f"{hit:.3f}", f"{prec:.3f}", f"{rec:.3f}", f"{mrr:.3f}", len(subset)])
        n_no_target = sum(1 for r in subset if r.get("ground_truth_status") != "ok")
        note = f"  ({n_no_target} câu không có chunk_id ground-truth hợp lệ)" if n_no_target else ""
        print(f"\n-- evolution_type: {et} (n={len(subset)}){note} --")
        print(tabulate(sub_rows, headers=headers, tablefmt="simple"))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Retrieval phase of the RAG chatbot (chunk-id based).")
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
    parser.add_argument("--index", type=int, default=None, help="Chỉ đánh giá 1 câu cụ thể theo chỉ số (1-indexed, ví dụ --index 21).")
    parser.add_argument("--from", type=int, default=None, dest="from_idx", help="Chạy từ câu có chỉ số N (1-indexed, ví dụ --from 21).")
    parser.add_argument("--to", type=int, default=None, dest="to_idx", help="Chạy đến câu có chỉ số M (1-indexed, bao gồm M, ví dụ --to 23).")
    args = parser.parse_args()

    dataset = load_dataset_json(args.dataset)
    total_items = len(dataset)

    for idx, item in enumerate(dataset, 1):
        item["_orig_idx"] = idx

    if args.index is not None:
        if 1 <= args.index <= total_items:
            dataset = [dataset[args.index - 1]]
        else:
            print(f"[FATAL] Index {args.index} nằm ngoài phạm vi dataset (1 đến {total_items}).", file=sys.stderr)
            sys.exit(1)
    else:
        start_idx = (args.from_idx - 1) if (args.from_idx is not None and args.from_idx >= 1) else 0
        end_idx = args.to_idx if (args.to_idx is not None) else total_items

        if args.from_idx or args.to_idx:
            dataset = dataset[start_idx:end_idx]

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