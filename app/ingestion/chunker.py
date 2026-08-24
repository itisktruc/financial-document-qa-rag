"""
Hierarchical chunking: heading-aware + table-aware + parent-child.

Input  : financial_rag_corrected.documents
Output : financial_rag_corrected.chunks_{TICKER}_{YEAR}
         ví dụ: chunks_SSI_2025, chunks_VNM_2024, ...
"""

from __future__ import annotations

import hashlib
import logging
import re
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://admin:changeme@mongodb:27017")
DB_NAME = "financial_rag"
SOURCE_COLLECTION = "documents_2025"
DESTINATION_COLLECTION = "chunked_documents_2025"

# Block types đưa vào chunk
CONTENT_TYPES = {"paragraph", "list", "table"}
# Block types bỏ qua
SKIP_TYPES = {"heading", "signature"}


def get_db():
    return MongoClient(MONGO_URI)[DB_NAME]


def make_id(*parts: str) -> str:
    raw = "||".join(str(p) for p in parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def extract_ticker(doc: Dict[str, Any]) -> Optional[str]:
    """
    Lấy ticker từ folder ngay sau 'ocr_results' trong path.
    Ưu tiên source_file (metadata), fallback sang doc_id.
    Ví dụ:
      .../ocr_results/SSI/2025/...  -> SSI
      ocr_results/SSI/2025/...      -> SSI
    """
    meta = doc.get("metadata") or {}
    candidates = [
        meta.get("source_file"),
        doc.get("_id"),
        meta.get("source_path"),
    ]

    for raw in candidates:
        if not raw or not isinstance(raw, str):
            continue
        path = raw.replace("\\", "/")
        m = re.search(r"(?i)(?:^|/)ocr_results/([^/]+)", path)
        if m:
            ticker = m.group(1).strip()
            if ticker:
                return ticker.upper()
    return None


def get_collection_name(ticker: Optional[str], year: Any) -> str:
    """
    Tên collection theo ticker + year.
    Fallback: chunks_UNKNOWN hoặc chunks_UNKNOWN_YYYY
    """
    t = (ticker or "UNKNOWN").upper().replace(" ", "_")
    if year is not None:
        try:
            y = int(year)
            return f"chunks_{t}_{y}"
        except (TypeError, ValueError):
            pass
    return f"chunks_{t}"


def block_to_child(
    block: Dict[str, Any],
    doc: Dict[str, Any],
    parent_id: str,
    child_idx: int,
    ticker: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    meta = doc.get("metadata") or {}
    doc_id = doc["_id"]

    text = (block.get("text") or "").strip()
    if not text:
        return None

    chunk_id = make_id(doc_id, "child", block.get("order_index", child_idx), text[:80])

    return {
        "_id": chunk_id,
        "chunk_id": chunk_id,
        "chunk_type": "child",
        "parent_id": parent_id,
        "doc_id": doc_id,
        "text": text,
        "block_type": block.get("block_type"),
        "page_start": block.get("page_start"),
        "page_end": block.get("page_end"),
        "order_index": block.get("order_index"),
        "heading_path": block.get("heading_path") or [],
        "section": block.get("section"),
        "subsection": block.get("subsection"),
        "company": meta.get("company_name"),
        "ticker": ticker,
        "year": meta.get("report_year"),
        "source_file": meta.get("source_file"),
        "html": block.get("html"),
        "level": block.get("level"),
        #"_is_corrected": True,
        "_batch_id": doc.get("_batch_id"),
    }


def build_parent(
    children: List[Dict[str, Any]],
    doc: Dict[str, Any],
    section: Optional[str],
    heading_path: List[str],
    ticker: Optional[str] = None,
) -> Dict[str, Any]:
    meta = doc.get("metadata") or {}
    doc_id = doc["_id"]

    texts = [c["text"] for c in children if c.get("text")]
    parent_text = "\n\n".join(texts)

    first = children[0]
    last = children[-1]

    parent_id = make_id(
        doc_id,
        "parent",
        section or "root",
        first.get("order_index"),
        last.get("order_index"),
    )

    return {
        "_id": parent_id,
        "chunk_id": parent_id,
        "chunk_type": "parent",
        "parent_id": None,
        "children_ids": [c["chunk_id"] for c in children],
        "doc_id": doc_id,
        "text": parent_text,
        "block_type": "section",
        "page_start": first.get("page_start"),
        "page_end": last.get("page_end"),
        "order_index": first.get("order_index"),
        "heading_path": heading_path,
        "section": section,
        "subsection": None,
        "company": meta.get("company_name"),
        "ticker": ticker,
        "year": meta.get("report_year"),
        "source_file": meta.get("source_file"),
        "child_count": len(children),
       # "_is_corrected": True,
        "_batch_id": doc.get("_batch_id"),
    }


def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks = doc.get("blocks") or []
    if not blocks:
        return []

    blocks = sorted(blocks, key=lambda b: b.get("order_index", 0))
    ticker = extract_ticker(doc)

    chunks: List[Dict[str, Any]] = []
    current_group: List[Dict[str, Any]] = []
    current_section: Optional[str] = None
    current_path: List[str] = []

    def flush_group():
        nonlocal current_group, current_section, current_path
        if not current_group:
            return

        children = []
        for idx, raw_block in enumerate(current_group):
            child = block_to_child(
                raw_block, doc, parent_id="TEMP", child_idx=idx, ticker=ticker
            )
            if child:
                children.append(child)

        if not children:
            current_group = []
            return

        parent = build_parent(
            children, doc, current_section, current_path, ticker=ticker
        )
        parent_id = parent["chunk_id"]

        for child in children:
            child["parent_id"] = parent_id

        chunks.append(parent)
        chunks.extend(children)
        current_group = []

    for block in blocks:
        btype = block.get("block_type")

        if btype in SKIP_TYPES:
            if btype == "heading":
                flush_group()
                current_section = block.get("section") or block.get("text")
                current_path = block.get("heading_path") or [current_section]
            continue

        if btype not in CONTENT_TYPES:
            continue

        section = block.get("section")
        path = block.get("heading_path") or []

        if current_group and section != current_section:
            flush_group()
            current_section = section
            current_path = path

        if not current_group:
            current_section = section
            current_path = path

        current_group.append(block)

    flush_group()
    return chunks


# def ensure_indexes(col: Collection):
#     col.create_index("doc_id")
#     col.create_index("chunk_type")
#     col.create_index("parent_id")
#     col.create_index("company")
#     col.create_index("ticker")
#     col.create_index("year")
#     col.create_index("section")
#     col.create_index([("doc_id", 1), ("chunk_type", 1)])
#     col.create_index([("ticker", 1), ("year", 1)])

def ensure_indexes(col: Collection):
    col.create_index("ticker")
    col.create_index("year")
    col.create_index([("ticker", 1), ("year", 1)])


def process(
    limit: Optional[int] = None,
    batch_size: int = 100,
    dry_run: bool = False,
):
    db = get_db()
    src = db[SOURCE_COLLECTION]
    dest = db[DESTINATION_COLLECTION]

    #query = {"_is_corrected": True}
    query = {}
    cursor = src.find(query)
    if limit:
        cursor = cursor.limit(limit)

    # Buffer theo từng collection: { collection_name: [chunks...] }
    # buffers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    # indexed_collections: set = set()

    buffers: List[Dict[str, Any]] = []
    total_docs = 0

    # total_docs = 0
    # total_chunks = 0

    # def flush_all():
    #     nonlocal total_chunks
    #     for col_name, buf in list(buffers.items()):
    #         if not buf:
    #             continue
    #         if dry_run:
    #             logger.info("[dry-run] would upsert %d chunks → %s", len(buf), col_name)
    #         else:
    #             col = db[col_name]
    #             if col_name not in indexed_collections:
    #                 ensure_indexes(col)
    #                 indexed_collections.add(col_name)

    #             ops = [
    #                 UpdateOne({"_id": c["_id"]}, {"$set": c}, upsert=True)
    #                 for c in buf
    #             ]
    #             result = col.bulk_write(ops, ordered=False)
    #             written = result.upserted_count + result.modified_count
    #             total_chunks += written
    #             logger.info("Wrote %d chunks → %s", written, col_name)
    #         buffers[col_name] = []
    def flush_buffer():
        if not buffers:
            return
        if dry_run:
            logger.info("[dry-run] would upsert %d files to %s", len(buffers), DESTINATION_COLLECTION)
        else:
            ensure_indexes(dest)
            ops = [
                UpdateOne({"_id": d["_id"]}, {"$set": d}, upsert=True) 
                for d in buffers
            ]
            result = dest.bulk_write(ops, ordered=False)
            logger.info("Wrote %d files to %s", len(buffers), DESTINATION_COLLECTION)
        buffers.clear()

    for doc in cursor:
        doc_chunks = chunk_document(doc)
        if not doc_chunks:
            total_docs += 1
            continue

        # Lấy ticker + year từ chunk đầu tiên (cùng doc thì giống nhau)
        sample = doc_chunks[0]

        # ticker = sample.get("ticker")
        # year = sample.get("year")
        # col_name = get_collection_name(ticker, year)

        # buffers[col_name].extend(doc_chunks)
        # total_docs += 1

        file_document = {
            "_id": doc["_id"],
            "ticker": sample.get("ticker"),
            "year": sample.get("year"),
            "company": sample.get("company"),
            "source_file": sample.get("source_file"),
            "chunks": doc_chunks 
        }

        buffers.append(file_document)
        total_docs += 1

        if total_docs % 10 == 0:
            logger.info("Processed %d documents...", total_docs)

        if len(buffers) >= batch_size:
            flush_buffer()

    flush_buffer()
    logger.info("Done. Total files processed: %d", total_docs)

        # Flush khi tổng buffer vượt batch_size
    #     total_buffered = sum(len(v) for v in buffers.values())
    #     if total_buffered >= batch_size:
    #         flush_all()

    # flush_all()
    # logger.info(
    #     "Done. Documents: %d | Chunks written: %d | Collections: %s",
    #     total_docs,
    #     total_chunks,
    #     sorted(indexed_collections) if indexed_collections else "dry-run",
    # )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Chỉ xử lý N document đầu")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    process(limit=args.limit, batch_size=args.batch_size, dry_run=args.dry_run)