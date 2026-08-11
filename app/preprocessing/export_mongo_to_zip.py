"""
Mongo to ZIP Exporter Module.

Exports JSON documents from a target MongoDB collection into a single,
compressed ZIP archive without saving temporary files on disk.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator

from pymongo import MongoClient
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExporterConfig:
    """Configuration settings for Mongo-to-ZIP export pipeline."""

    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "financial_rag"
    collection_name: str = "documents_2025"
    output_zip_path: Path = Path("./documents_2025.zip")
    batch_size: int = 100
    compress_level: int = 9
    max_filename_length: int = 180


class MongoZipExporter:
    """Handles streaming MongoDB documents into a compressed ZIP file."""

    def __init__(self, config: ExporterConfig) -> None:
        self.config = config
        self._client: MongoClient[dict[str, Any]] = MongoClient(self.config.mongo_uri)
        self._collection: Collection[dict[str, Any]] = self._client[self.config.db_name][
            self.config.collection_name
        ]

    def _sanitize_filename(self, repo_path: str) -> str:
        """Sanitizes document IDs or paths into safe, cross-platform filenames."""
        clean_name = repo_path.replace("\\", "/").strip("/")
        if clean_name.lower().endswith(".txt"):
            clean_name = clean_name[:-4]

        safe_name = re.sub(r"[^\w.\-]+", "_", clean_name)
        if len(safe_name) > self.config.max_filename_length:
            safe_name = safe_name[-self.config.max_filename_length :]

        return f"{safe_name}.json"

    def _stream_documents(self) -> Generator[dict[str, Any], None, None]:
        """Yields documents from MongoDB with an optimized batch cursor."""
        cursor = self._collection.find({}, batch_size=self.config.batch_size)
        try:
            yield from cursor
        finally:
            cursor.close()

    def run(self) -> None:
        """Executes the export process."""
        total_docs = self._collection.count_documents({})
        if total_docs == 0:
            logger.warning(
                "No documents found in target collection '%s'. Aborting export.",
                self.config.collection_name,
            )
            return

        logger.info("Found %d document(s). Starting direct-to-ZIP stream export...", total_docs)
        self.config.output_zip_path.parent.mkdir(parents=True, exist_ok=True)

        n_exported = 0
        try:
            with zipfile.ZipFile(
                self.config.output_zip_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=self.config.compress_level,
            ) as zf:
                for idx, doc in enumerate(self._stream_documents(), start=1):
                    raw_id = str(doc.get("_id", f"doc_{idx}"))
                    filename = self._sanitize_filename(raw_id)

                    payload = json.dumps(
                        doc, ensure_ascii=False, indent=2, default=str
                    ).encode("utf-8")

                    zf.writestr(filename, payload)
                    n_exported += 1

                    if idx % 50 == 0 or idx == total_docs:
                        logger.info("  [%d/%d] Compressed: %s", idx, total_docs, filename)

            zip_size_mb = self.config.output_zip_path.stat().st_size / (1024 * 1024)
            logger.info(
                "Export complete. Encapsulated %d/%d files -> %s (Size: %.2f MB)",
                n_exported,
                total_docs,
                self.config.output_zip_path.resolve(),
                zip_size_mb,
            )

        except KeyboardInterrupt:
            logger.warning("Export interrupted by user. Removing incomplete output archive...")
            if self.config.output_zip_path.exists():
                self.config.output_zip_path.unlink()
            sys.exit(1)

        except Exception as err:
            logger.exception("Unexpected error during export execution: %s", err)
            raise


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
        stream=sys.stdout,
    )

    config = ExporterConfig()
    exporter = MongoZipExporter(config)
    exporter.run()


if __name__ == "__main__":
    main()