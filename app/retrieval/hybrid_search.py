"""
app/retrieval/hybrid_search.py

Hybrid retrieval: BM25 (Mongo flat child chunks) + Dense (Qdrant) + RRF + Rerank
+ parent-document expansion.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import bm25s
from qdrant_client.http import models as qmodels

from app.retrieval.glossary import expand_query
from app.retrieval.query_router import QueryRouter
from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.reranker import DocumentReranker
from app.services.embedding_client import embed_query
from app.services.mongo_client import (
    get_chunks_collection,
    get_parent_chunk,
    list_chunk_collections,
)
from app.services.qdrant_service import search_similar_blocks

logger = logging.getLogger(__name__)

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent

_STOPWORDS_FILE = _DATA_DIR / "vietnamese-stopwords.txt"

TICKER_MAPPING = {
    "32": "A32",
    "CL3": "A32",
    "công ty cổ phần 32": "A32",
    "cty 32": "A32",
    "a32": "A32",
    "công ty A32": "A32",
}

K_RRF = 60
BM25_TOP_K = 50
DENSE_TOP_K = 50
FUSION_TOP_K = 50
TOP_K = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_vi_stopwords(path: Path = _STOPWORDS_FILE) -> list[str]:
    words: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            w = line.strip().lower()
            if not w or w.startswith("#"):
                continue
            words.add(w)
            # thêm từng token nếu là cụm nhiều từ
            for part in w.split():
                if part:
                    words.add(part)
    return sorted(words)

VI_STOPWORDS: list[str] = _load_vi_stopwords()

def _normalize_cid(cid: Any) -> str:
    """Đồng bộ id: bỏ dấu '-' (Qdrant UUID) để khớp Mongo hex."""
    if not cid:
        return ""
    return str(cid).replace("-", "").strip()


def _collection_from_payload(payload: dict) -> Optional[str]:
    if payload.get("collection"):
        return str(payload["collection"])
    ticker = payload.get("ticker")
    year = payload.get("year")
    if ticker is not None and year is not None:
        return f"chunks_{str(ticker).upper()}_{year}"
    return None


def ticker_year_filter(
    metadata_filter: Optional[dict],
) -> Tuple[dict, Optional[qmodels.Filter]]:
    """
    Chuẩn hóa ticker/year → (mongo_query, qdrant_filter) dùng chung BM25 + Dense.
    """
    if not metadata_filter:
        return {}, None

    mongo_query: Dict[str, Any] = {}
    must_qdrant: List[qmodels.FieldCondition] = []

    raw_ticker = metadata_filter.get("ticker")
    if raw_ticker:
        ticker_str = str(raw_ticker).strip().upper()
        # mapping key có thể mixed-case / cụm từ
        clean_ticker = TICKER_MAPPING.get(str(raw_ticker).strip(), None)
        if clean_ticker is None:
            clean_ticker = TICKER_MAPPING.get(ticker_str, ticker_str)
        mongo_query["ticker"] = clean_ticker
        must_qdrant.append(
            qmodels.FieldCondition(
                key="ticker",
                match=qmodels.MatchValue(value=clean_ticker),
            )
        )

    raw_year = metadata_filter.get("year")
    if raw_year is not None and str(raw_year).strip() != "":
        try:
            clean_year = int(raw_year)
        except (ValueError, TypeError):
            clean_year = raw_year
        mongo_query["year"] = clean_year
        must_qdrant.append(
            qmodels.FieldCondition(
                key="year",
                match=qmodels.MatchValue(value=clean_year),
            )
        )

    qdrant_filter = qmodels.Filter(must=must_qdrant) if must_qdrant else None
    return mongo_query, qdrant_filter


# ---------------------------------------------------------------------------
# BM25 corpus / index
# ---------------------------------------------------------------------------

def _load_bm25_corpus(
    ticker: Optional[str] = None,
    year: Optional[int] = None,
) -> Tuple[List[str], List[str], Dict[str, dict]]:
    """Load child chunks flat; optional filter ticker/year."""
    corpus_ids: List[str] = []
    corpus_texts: List[str] = []
    lookup: Dict[str, dict] = {}

    for col_name in list_chunk_collections():
        # Nếu đã biết ticker/year, chỉ quét collection khớp tên (nhanh hơn)
        if ticker and year is not None:
            expected = f"chunks_{ticker}_{year}"
            if col_name.upper() != expected.upper():
                # vẫn cho phép chunks_TICKER không có year trong tên
                if not col_name.upper().startswith(f"CHUNKS_{ticker.upper()}"):
                    continue

        query: Dict[str, Any] = {"chunk_type": "child"}
        if ticker:
            query["ticker"] = ticker
        if year is not None:
            query["year"] = year

        col = get_chunks_collection(col_name)
        cursor = col.find(
            query,
            {
                "text": 1,
                "parent_id": 1,
                "ticker": 1,
                "year": 1,
                "chunk_id": 1,
                "order_index": 1,
            },
        )
        for doc in cursor:
            cid = _normalize_cid(doc.get("chunk_id") or doc.get("_id"))
            text = (doc.get("text") or "").strip()
            if not cid or not text:
                continue
            corpus_ids.append(cid)
            corpus_texts.append(text)
            lookup[cid] = {
                "content": text,
                "parent_id": _normalize_cid(doc.get("parent_id")) or cid,
                "ticker": doc.get("ticker"),
                "year": doc.get("year"),
                "collection": col_name,
                "order_index": doc.get("order_index"),
            }

    return corpus_ids, corpus_texts, lookup


@lru_cache(maxsize=64)
def _get_bm25_index(
    ticker: Optional[str] = None,
    year: Optional[int] = None,
):
    """
    Cache theo (ticker, year). year=None và ticker=None → full corpus.
    Gọi refresh_bm25_index() sau ingest.
    """
    corpus_ids, corpus_texts, lookup = _load_bm25_corpus(ticker=ticker, year=year)
    if not corpus_ids or not corpus_texts:
        logger.warning(
            "[BM25] Empty corpus (ticker=%s, year=%s)", ticker, year
        )
        return None, tuple(), {}

    corpus_tokens = bm25s.tokenize(corpus_texts, stopwords=list(VI_STOPWORDS))
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    # tuple để hash-safe với lru_cache return; lookup giữ dict
    return retriever, tuple(corpus_ids), lookup


def refresh_bm25_index() -> None:
    """Invalidate BM25 cache sau khi ingest/xóa document."""
    _get_bm25_index.cache_clear()
    logger.info("[BM25] cache cleared")


def reciprocal_rank_fusion(
    rankings: List[List[str]],
    k: int = K_RRF,
) -> List[Tuple[str, float]]:
    scores: Dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, corpus_id in enumerate(ranking, start=1):
            if not corpus_id:
                continue
            scores[corpus_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class HybridSearchPipeline:
    def __init__(self) -> None:
        self.router = QueryRouter()
        self.rewriter = QueryRewriter()
        self.reranker = DocumentReranker()

    # ----- routing / rewrite -----

    def process_user_query(self, query: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        route = self.router.route(query)
        if route == "chitchat":
            return {"type": "chitchat", "queries": [query], "metadata": {}}
        if route == "term_definition":
            return {"type": "term_definition", "original_query": query}
        if route == "calculation":
            return {"type": "calculation", "original_query": query}

        extracted = self.rewriter.rewrite_and_extract_metadata(query, history)
        return {
            "type": "financial_search",
            "original_query": query,
            "search_queries": extracted.get("rewritten_queries") or [query],
            "metadata_filter": {
                "ticker": extracted.get("ticker"),
                "year": extracted.get("year"),
            },
        }

    # ----- BM25 -----

    def bm25_search(
        self,
        query: str,
        k: int = BM25_TOP_K,
        metadata_filter: Optional[dict] = None,
    ) -> List[Tuple[str, float]]:
        mongo_query, _ = ticker_year_filter(metadata_filter)
        ticker = mongo_query.get("ticker")
        year = mongo_query.get("year")
        if year is not None:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None

        retriever, corpus_ids, lookup = _get_bm25_index(ticker=ticker, year=year)
        if not retriever or not corpus_ids:
            return []

        query_tokens = bm25s.tokenize([query], stopwords=list(VI_STOPWORDS))
        indices, scores = retriever.retrieve(
            query_tokens, k=min(k, len(corpus_ids))
        )
        hits = [
            (_normalize_cid(corpus_ids[idx]), float(score))
            for idx, score in zip(indices[0], scores[0])
        ]
        logger.debug("[BM25] ticker=%s year=%s hits=%d", ticker, year, len(hits))
        return hits[:k]

    # ----- Dense -----

    def dense_search(
        self,
        query: str,
        k: int = DENSE_TOP_K,
        metadata_filter: Optional[dict] = None,
    ) -> List[Tuple[str, float, dict]]:
        _, qdrant_filter = ticker_year_filter(metadata_filter)
        vector = embed_query(query, return_sparse=False)["dense"]
        hits = search_similar_blocks(
            vector, limit=k, query_filter=qdrant_filter
        )
        result = [
            (_normalize_cid(hit.id), float(hit.score), hit.payload or {})
            for hit in hits
        ]
        logger.debug("[Dense] hits=%d filter=%s", len(result), bool(qdrant_filter))
        return result

    # ----- RRF -----

    def RRF_fuse(
        self,
        search_queries: List[str],
        metadata_filter: Optional[dict] = None,
    ) -> Tuple[List[str], Dict[str, dict]]:
        mongo_query, _ = ticker_year_filter(metadata_filter)
        ticker = mongo_query.get("ticker")
        year = mongo_query.get("year")
        if year is not None:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None

        _, _, bm25_lookup = _get_bm25_index(ticker=ticker, year=year)

        rankings: List[List[str]] = []
        content_lookup: Dict[str, dict] = {}

        for q in search_queries:
            q_expanded = expand_query(q)

            # BM25
            bm25_hits = self.bm25_search(
                q_expanded, metadata_filter=metadata_filter
            )
            rankings.append([cid for cid, _ in bm25_hits])
            for cid, _ in bm25_hits:
                if cid not in content_lookup and cid in bm25_lookup:
                    content_lookup[cid] = dict(bm25_lookup[cid])

            # Dense
            dense_hits = self.dense_search(
                q_expanded, metadata_filter=metadata_filter
            )
            rankings.append([cid for cid, _, _ in dense_hits])
            for cid, _, payload in dense_hits:
                if cid not in content_lookup:
                    content_lookup[cid] = {
                        "content": payload.get("text")
                        or payload.get("content")
                        or "",
                        "parent_id": _normalize_cid(payload.get("parent_id"))
                        or cid,
                        "ticker": payload.get("ticker"),
                        "year": payload.get("year"),
                        "collection": _collection_from_payload(payload),
                        "order_index": payload.get("order_index"),
                        "source_file": payload.get("source_file"),
                        "page_start": payload.get("page_start"),
                        "page_end": payload.get("page_end"),
                        "heading_path": payload.get("heading_path") or [],
                        "doc_id": payload.get("doc_id"),
                        "company": payload.get("company"),
                    }
                else:
                    # bổ sung collection nếu BM25 chưa có
                    if not content_lookup[cid].get("collection"):
                        content_lookup[cid]["collection"] = _collection_from_payload(
                            payload
                        )

        fused = reciprocal_rank_fusion(rankings)
        rrf_ids = [cid for cid, _ in fused if cid][:FUSION_TOP_K]
        logger.info(
            "[RRF] queries=%d rankings=%d fused_top=%d ticker=%s year=%s",
            len(search_queries),
            len(rankings),
            len(rrf_ids),
            ticker,
            year,
        )
        return rrf_ids, content_lookup

    # ----- Rerank -----

    def rerank(
        self,
        original_query: str,
        candidate_ids: List[str],
        content_lookup: Dict[str, dict],
        top_k: int = TOP_K,
    ) -> List[str]:
        valid_ids = [
            cid
            for cid in candidate_ids
            if (content_lookup.get(cid) or {}).get("content")
        ]
        if not valid_ids:
            return []

        documents = [content_lookup[cid]["content"] for cid in valid_ids]
        ranked_indices = self.reranker.rerank(
            original_query, documents, top_k=top_k
        )
        return [valid_ids[i] for i in ranked_indices if i < len(valid_ids)]

    # ----- Entry -----

    def retrieve(self, user_query: str, top_k: int = TOP_K,history: Optional[List[Dict[str, Any]]] = None,) -> Dict[str, Any]:
        prep = self.process_user_query(user_query, history)

        if prep["type"] == "chitchat":
            return {"is_chitchat": True, "chunk_ids": [], "context": []}
        if prep["type"] == "term_definition":
            return {
                "is_chitchat": False,
                "is_definition": True,
                "chunk_ids": [],
                "context": [],
            }
        if prep["type"] == "calculation":
            return {
                "is_chitchat": False,
                "is_definition": False,
                "is_calculation": True,
                "chunk_ids": [],
                "context": [],
            }

        metadata_filter = prep.get("metadata_filter") or {}
        logger.info("[retrieve] metadata_filter=%s", metadata_filter)

        rrf_ids, content_lookup = self.RRF_fuse(
            prep["search_queries"],
            metadata_filter=metadata_filter,
        )

        # Fallback: bỏ year, giữ ticker
        if not rrf_ids and metadata_filter.get("ticker"):
            logger.info("[retrieve] fallback: drop year, keep ticker")
            rrf_ids, content_lookup = self.RRF_fuse(
                prep["search_queries"],
                metadata_filter={"ticker": metadata_filter["ticker"]},
            )

        top_chunk_ids = self.rerank(
            user_query, rrf_ids, content_lookup, top_k=top_k
        )

        seen_parents: set = set()
        contexts: List[dict] = []

        for cid in top_chunk_ids:
            chunk_info = content_lookup.get(cid) or {}
            parent_id = _normalize_cid(chunk_info.get("parent_id")) or cid
            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)

            col_name = chunk_info.get("collection")
            parent_doc = None
            if col_name and parent_id:
                try:
                    parent_doc = get_parent_chunk(col_name, parent_id)
                except TypeError:
                    # tương thích signature cũ get_parent_chunk(parent_id) nếu chưa upgrade mongo_client
                    parent_doc = get_parent_chunk(parent_id)  # type: ignore

            if parent_doc:
                text_content = (
                    parent_doc.get("text") or parent_doc.get("content") or ""
                )
                citation_info = {
                    "doc_id": parent_doc.get("doc_id"),
                    "source_file": parent_doc.get("source_file"),
                    "page_start": parent_doc.get("page_start"),
                    "page_end": parent_doc.get("page_end"),
                    "section": parent_doc.get("section")
                    or parent_doc.get("heading"),
                    "ticker": parent_doc.get("ticker"),
                    "year": parent_doc.get("year"),
                }
            else:
                text_content = chunk_info.get("content") or ""
                citation_info = {
                    "doc_id": cid,
                    #"source_file": "Báo cáo tài chính",
                    "page_start": None,
                    "page_end": None,
                    "section": None,
                    "ticker": chunk_info.get("ticker"),
                    "year": chunk_info.get("year"),
                }

            if text_content and not any(
                c["content"] == text_content for c in contexts
            ):
                contexts.append(
                    {"content": text_content, "citation": citation_info}
                )

        return {
            "is_chitchat": False,
            "is_definition": False,
            "is_calculation": False,
            "chunk_ids": top_chunk_ids,
            "context": contexts,
        }