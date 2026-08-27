"""
app/services/embedding_client.py

BGE-M3 Embedding Client & Qdrant PointStruct Generator.
"""

from __future__ import annotations

import logging
import os
import sys
from functools import lru_cache
from typing import Any, Dict, List, Optional

from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)


def _ensure_utf8_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


_ensure_utf8_stdio()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "BAAI/bge-m3")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "48"))
EMBEDDING_MAX_LENGTH = int(os.getenv("EMBEDDING_MAX_LENGTH", "1024"))
EMBEDDING_USE_FP16 = os.getenv("EMBEDDING_USE_FP16", "true")

DENSE_DIM = 1024
RETRIEVABLE_CHUNK_TYPES = {"child", "table"}


# ---------------------------------------------------------------------------
# Model Singleton
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_model():
    import torch
    from FlagEmbedding import BGEM3FlagModel

    device = EMBEDDING_DEVICE or ("cuda" if torch.cuda.is_available() else "cpu")
    use_fp16 = device.startswith("cuda") if EMBEDDING_USE_FP16 == "auto" else EMBEDDING_USE_FP16.lower() == "true"

    logger.info("Loading %s | device=%s | fp16=%s", EMBEDDING_MODEL_ID, device, use_fp16)
    return BGEM3FlagModel(EMBEDDING_MODEL_ID, use_fp16=use_fp16, device=device)


def _to_native(vec: Any) -> List[float]:
    return vec.tolist() if hasattr(vec, "tolist") else [float(x) for x in vec]


def _chunk_text(c: Dict[str, Any]) -> str:
    return (c.get("text") or "").strip()


# ---------------------------------------------------------------------------
# Embedding Operations
# ---------------------------------------------------------------------------

def embed_texts(
    texts: List[str],
    batch_size: int = EMBEDDING_BATCH_SIZE,
    max_length: int = EMBEDDING_MAX_LENGTH,
    return_sparse: bool = False,
) -> Dict[str, Any]:
    """Generates dense (and optional sparse) embeddings for a list of texts."""
    if not texts:
        return {"dense": [], "sparse": [] if return_sparse else None}

    model = _load_model()
    output = model.encode(
        texts,
        batch_size=batch_size,
        max_length=max_length,
        return_dense=True,
        return_sparse=return_sparse,
        return_colbert_vecs=False,
    )

    dense = [_to_native(v) for v in output["dense_vecs"]]
    sparse = None
    if return_sparse:
        sparse = [{str(k): float(v) for k, v in lw.items()} for lw in output["lexical_weights"]]

    return {"dense": dense, "sparse": sparse}


def embed_query(query: str, return_sparse: bool = False) -> Dict[str, Any]:
    """Embeds a single search query."""
    result = embed_texts([query], batch_size=1, return_sparse=return_sparse)
    return {
        "dense": result["dense"][0],
        "sparse": result["sparse"][0] if return_sparse else None,
    }


def attach_embeddings_to_chunks(
    chunks: List[Dict[str, Any]],
    batch_size: int = EMBEDDING_BATCH_SIZE,
    return_sparse: bool = False,
    include_parent: bool = False,
) -> List[Dict[str, Any]]:
    """Generates and binds vector embeddings to retrievable chunks."""
    targets = [c for c in chunks if include_parent or c.get("chunk_type") in RETRIEVABLE_CHUNK_TYPES]
    texts = [_chunk_text(c) for c in targets]
    
    if not texts:
        return []

    result = embed_texts(texts, batch_size=batch_size, return_sparse=return_sparse)

    out = []
    for i, c in enumerate(targets):
        new_c = dict(c)
        new_c["dense_vector"] = result["dense"][i]
        if return_sparse and result["sparse"]:
            new_c["sparse_vector"] = result["sparse"][i]
        out.append(new_c)

    return out


# ---------------------------------------------------------------------------
# Qdrant Point Mapping
# ---------------------------------------------------------------------------

def chunk_to_point(chunk: Dict[str, Any], vector: List[float]) -> qmodels.PointStruct:
    """Converts a single chunk dict and its vector into a Qdrant PointStruct."""
    point_id = str(chunk.get("chunk_id") or chunk.get("_id")).strip()
    payload = {
        "chunk_id": point_id,
        "doc_id": chunk.get("doc_id"),
        "parent_id": chunk.get("parent_id"),
        "chunk_type": chunk.get("chunk_type"),
        "ticker": chunk.get("ticker"),
        "year": chunk.get("year"),
        "company": chunk.get("company"),
        "section": chunk.get("section"),
        "subsection": chunk.get("subsection"),
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "order_index": chunk.get("order_index"),
        "heading_path": chunk.get("heading_path") or [],
        "text": _chunk_text(chunk),
        "source_file": chunk.get("source_file"),
        "block_type": chunk.get("block_type"),
    }
    return qmodels.PointStruct(
        id=point_id,
        vector=vector,
        payload=payload,
    )


def to_qdrant_points(embedded_chunks: List[Dict[str, Any]]) -> List[qmodels.PointStruct]:
    """Transforms a batch of embedded chunks into a list of PointStruct objects."""
    points: List[qmodels.PointStruct] = []
    for chunk in embedded_chunks:
        vector = chunk.get("dense_vector")
        if not vector:
            continue
        points.append(chunk_to_point(chunk, vector))
    return points