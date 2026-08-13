"""
Tải OCR .txt (tất cả năm TRỪ 2025) từ HF cho các ticker:
Agribank, ACB, BaoVietBank, BID
preprocess → lưu Mongo + (tùy chọn) JSON.

- JSON: app/preprocessing/mongo_json/  (đang comment, bật lại nếu cần)
- Mongo: resume theo _id = repo path
- Download tạm qua tempfile

Ví dụ:
python -m preprocessing.hf_to_mongo_selected --db-name financial_rag --collection documents_pre_2025 --limit 1
python -m preprocessing.hf_to_mongo_selected --db-name financial_rag --collection documents_pre_2025
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download
from pymongo import MongoClient
from pymongo.collection import Collection

from preprocessing.pipeline import DocumentPreprocessingPipeline, PipelineConfig
from preprocessing.serialization import document_to_dict

logger = logging.getLogger(__name__)

REPO_ID = "tinixai/ocr_annual_financials"
REPO_TYPE = "dataset"
JSON_DIR = Path(__file__).resolve().parent / "mongo_json"

# Chỉ lấy các ticker này, và loại bỏ năm 2025
TARGET_TICKERS = {"Agribank", "ACB", "BaoVietBank", "BID"}
EXCLUDE_YEAR = "2025"


def list_txt_selected(
    repo_id: str = REPO_ID,
    repo_type: str = REPO_TYPE,
    tickers: set[str] | None = None,
    exclude_year: str = EXCLUDE_YEAR,
) -> list[str]:
    """Liệt kê .txt của các ticker chỉ định, loại bỏ năm exclude_year."""
    if tickers is None:
        tickers = TARGET_TICKERS

    api = HfApi()
    all_paths = api.list_repo_files(repo_id=repo_id, repo_type=repo_type)

    selected: list[str] = []
    for p in all_paths:
        if not p.endswith(".txt"):
            continue
        # Kỳ vọng path: ocr_results/{TICKER}/{YEAR}/...
        parts = p.replace("\\", "/").split("/")
        if len(parts) < 3 or parts[0] != "ocr_results":
            continue
        ticker, year = parts[1], parts[2]
        if ticker not in tickers:
            continue
        if year == exclude_year:
            continue
        # Chỉ nhận year dạng 4 chữ số (tránh path lạ)
        if not (year.isdigit() and len(year) == 4):
            continue
        selected.append(p)

    selected.sort()
    logger.info(
        "Found %d .txt file(s) for tickers=%s excluding year=%s in %s.",
        len(selected),
        sorted(tickers),
        exclude_year,
        repo_id,
    )
    return selected


def already_processed(collection: Collection, doc_id: str) -> bool:
    return collection.find_one({"_id": doc_id}, {"_id": 1}) is not None


def _json_filename(repo_path: str) -> str:
    name = repo_path.replace("\\", "/").rstrip("/")
    name = name[:-4] if name.lower().endswith(".txt") else name
    name = re.sub(r"[^\w.\-]+", "_", name)
    return name + ".json"


def save_json(payload: dict, repo_path: str) -> Path:
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    out_path = JSON_DIR / _json_filename(repo_path)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return out_path


def run(
    mongo_uri: str,
    db_name: str,
    collection_name: str,
    limit: int | None = None,
    hf_token: str | None = None,
) -> None:
    client = MongoClient(mongo_uri)
    collection: Collection = client[db_name][collection_name]
    collection.create_index("metadata.source_file")
    collection.create_index("metadata.report_year")
    collection.create_index("quality.overall_risk")

    pipeline = DocumentPreprocessingPipeline(config=PipelineConfig())
    txt_paths = list_txt_selected()
    if limit is not None:
        txt_paths = txt_paths[:limit]

    n_total = len(txt_paths)
    n_skipped = n_done = n_failed = 0

    for i, repo_path in enumerate(txt_paths, start=1):
        doc_id = repo_path

        if already_processed(collection, doc_id):
            n_skipped += 1
            logger.info("[%d/%d] SKIP (already in Mongo): %s", i, n_total, repo_path)
            continue

        try:
            logger.info("[%d/%d] Downloading: %s", i, n_total, repo_path)
            with tempfile.TemporaryDirectory(prefix="hf_ocr_") as tmp:
                downloaded = hf_hub_download(
                    repo_id=REPO_ID,
                    repo_type=REPO_TYPE,
                    filename=repo_path,
                    local_dir=tmp,
                    token=hf_token,
                )
                document = pipeline.process_file(Path(downloaded))

            payload = document_to_dict(document, doc_id=doc_id)
            payload.pop("pages", None)

            collection.replace_one({"_id": doc_id}, payload, upsert=True)
            # json_path = save_json(payload, repo_path)  # bật nếu cần lưu JSON
            n_done += 1

            risk = (
                getattr(document.quality, "overall_risk", None)
                if document.quality
                else None
            )
            logger.info(
                "[%d/%d] Saved Mongo: %s (pages=%d, blocks=%d, risk=%s)",
                i,
                n_total,
                repo_path,
                len(document.pages),
                len(document.blocks),
                risk,
            )
        except Exception:
            n_failed += 1
            logger.exception(
                "[%d/%d] FAILED %s; will retry next run (not saved).",
                i,
                n_total,
                repo_path,
            )

    logger.info(
        "Done. total=%d done=%d skipped=%d failed=%d. JSON dir=%s",
        n_total,
        n_done,
        n_skipped,
        n_failed,
        JSON_DIR.resolve(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
    parser.add_argument("--db-name", required=True)
    parser.add_argument("--collection", default="documents_pre_bank_2025")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    run(
        mongo_uri=args.mongo_uri,
        db_name=args.db_name,
        collection_name=args.collection,
        limit=args.limit,
        hf_token=args.hf_token,
    )


if __name__ == "__main__":
    main()