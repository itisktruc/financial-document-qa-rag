"""Load spell-corrected documents into dedicated MongoDB collection."""

from __future__ import annotations

import argparse
import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Tuple

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

DEFAULT_MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DEFAULT_DB_NAME = os.getenv("MONGO_CORRECTED_DB", "financial_rag_corrected")
DEFAULT_COLLECTION = os.getenv("MONGO_CORRECTED_COLLECTION", "documents")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_collection(
    uri: str = DEFAULT_MONGO_URI,
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DEFAULT_COLLECTION,
) -> Collection:
    client = MongoClient(uri)
    client.admin.command("ping")
    collection = client[db_name][collection_name]
    logger.info("Connected to Mongo: %s.%s", db_name, collection_name)
    return collection


def ensure_indexes(collection: Collection) -> None:
    collection.create_index("metadata.company_name")
    collection.create_index("metadata.report_year")
    collection.create_index("metadata.source_file")
    collection.create_index("_batch_id")
    collection.create_index("_is_corrected")


def iter_json_from_dir(dir_path: Path) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    for file_path in sorted(dir_path.rglob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as err:
            logger.warning("Failed to read %s: %s", file_path, err)
            continue

        if isinstance(data, dict) and "blocks" in data:
            yield str(file_path.relative_to(dir_path)), data
        else:
            logger.warning("Missing 'blocks' key in %s", file_path)


def iter_json_from_zip(zip_path: Path) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".json") or name.endswith("/"):
                continue
            try:
                with zf.open(name) as f:
                    data = json.load(f)
            except Exception as err:
                logger.warning("Failed to read %s in %s: %s", name, zip_path.name, err)
                continue

            if isinstance(data, dict) and "blocks" in data:
                yield name, data
            else:
                logger.warning("Missing 'blocks' key in %s/%s", zip_path.name, name)


def normalize_doc(
    doc: Dict[str, Any],
    source: str,
    batch_id: str,
) -> Dict[str, Any]:
    normalized = dict(doc)
    normalized["_batch_id"] = batch_id
    normalized["_source_in_batch"] = source
    normalized["_is_corrected"] = True

    if not normalized.get("_id"):
        meta = normalized.get("metadata") or {}
        src = meta.get("source_file") or source
        normalized["_id"] = f"{batch_id}::{src}"

    normalized["_id"] = str(normalized["_id"])
    return normalized


def collect_batches(
    processed_dir: Path,
    zip_only: bool = False,
    dir_only: bool = False,
) -> List[Tuple[str, Iterable[Tuple[str, Dict[str, Any]]]]]:
    batches: List[Tuple[str, Iterable[Tuple[str, Dict[str, Any]]]]] = []

    if not processed_dir.exists():
        logger.error("Processed directory does not exist: %s", processed_dir)
        return batches

    if not zip_only:
        for d in sorted(processed_dir.iterdir()):
            if d.is_dir() and d.name.startswith("corrected_batch_"):
                batches.append((d.name, iter_json_from_dir(d)))
                logger.info("Discovered directory batch: %s", d.name)

    if not dir_only:
        for z in sorted(processed_dir.glob("corrected_batch_*.zip")):
            batches.append((z.stem, iter_json_from_zip(z)))
            logger.info("Discovered zip batch: %s", z.name)

    return batches


def bulk_upsert(
    collection: Collection,
    docs: List[Dict[str, Any]],
    dry_run: bool = False,
) -> int:
    if not docs:
        return 0

    if dry_run:
        logger.info("[DRY-RUN] Sample _id: %s (total: %d)", docs[0].get("_id"), len(docs))
        return len(docs)

    operations = [
        UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        for doc in docs
    ]

    try:
        res = collection.bulk_write(operations, ordered=False)
        return res.upserted_count + res.modified_count + res.matched_count
    except BulkWriteError as err:
        logger.error("BulkWriteError details: %s", err.details)
        details = err.details or {}
        return (
            details.get("nUpserted", 0) 
            + details.get("nModified", 0) 
            + details.get("nMatched", 0)
        )


def load_all(
    processed_dir: Path = PROCESSED_DIR,
    mongo_uri: str = DEFAULT_MONGO_URI,
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DEFAULT_COLLECTION,
    batch_size: int = 50,
    zip_only: bool = False,
    dir_only: bool = False,
    dry_run: bool = False,
) -> None:
    collection = get_collection(mongo_uri, db_name, collection_name)
    if not dry_run:
        ensure_indexes(collection)

    batches = collect_batches(processed_dir, zip_only=zip_only, dir_only=dir_only)
    if not batches:
        logger.warning("No corrected batches found in %s", processed_dir)
        return

    total_docs = 0
    for batch_id, items in batches:
        buffer: List[Dict[str, Any]] = []
        batch_count = 0

        for source, raw_doc in items:
            doc = normalize_doc(raw_doc, source=source, batch_id=batch_id)
            buffer.append(doc)

            if len(buffer) >= batch_size:
                written = bulk_upsert(collection, buffer, dry_run=dry_run)
                total_docs += written
                batch_count += written
                buffer.clear()

        if buffer:
            written = bulk_upsert(collection, buffer, dry_run=dry_run)
            total_docs += written
            batch_count += written

        logger.info("Batch %-22s -> %d docs", batch_id, batch_count)

    logger.info("Completed. Total documents processed: %d", total_docs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load corrected JSON dataset to MongoDB.")
    parser.add_argument("--uri", default=DEFAULT_MONGO_URI)
    parser.add_argument("--db", default=DEFAULT_DB_NAME)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--zip-only", action="store_true")
    parser.add_argument("--dir-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    load_all(
        processed_dir=args.processed_dir,
        mongo_uri=args.uri,
        db_name=args.db,
        collection_name=args.collection,
        batch_size=args.batch_size,
        zip_only=args.zip_only,
        dir_only=args.dir_only,
        dry_run=args.dry_run,
    )