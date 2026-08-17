from typing import List, Dict, Any, Optional
from app.retrieval.query_router import QueryRouter
from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.reranker import DocumentReranker
from app.retrieval.glossary import expand_query
from pymongo import MongoClient
from app.config import settings
from functools import lru_cache
from collections import defaultdict
from app.services.embedding_client import embed_query
from app.services.qdrant_store import search_similar_blocks
from qdrant_client.http import models as qmodels
from app.services.mongo_client import get_chunks_collection, get_parent_chunk

import bm25s
import numpy as np

mongo_client = MongoClient(getattr(settings, "MONGO_URI", "mongodb://mongo:27017"))
mongo_db = mongo_client[getattr(settings, "MONGO_DB_NAME", "financial_rag")]

VI_STOPWORDS = {"là", "của", "và", "các", "một", "những", "cho", "về", "trong", "đã", "này", "được"}  # bổ sung thêm nếu cần

K_RRF = 60                     # hằng số k trong công thức RRF: 1 / (k + rank)
BM25_TOP_K = 20                # số ứng viên BM25 lấy mỗi query
DENSE_TOP_K = 20               # số ứng viên Dense lấy mỗi query
FUSION_TOP_K = 30              # số chunks sau RRF đưa vào reranker
TOP_K = 10                     # số chunks cuối cùng sau reranker

def _load_bm25_corpus():
    docs = get_chunks_collection().find(
        {"chunk_type": {"$in": ["text_child", "table"]}},
        {"content": 1, "parent_id": 1},
    )
    corpus_ids: List[str] = []
    corpus_texts: List[str] = []
    lookup: Dict[str, dict] = {}

    for doc in docs:
        cid = str(doc["_id"])
        text = doc.get("content", "") or ""
        corpus_ids.append(cid)
        corpus_texts.append(text)
        lookup[cid] = {"content": text, "parent_id": doc.get("parent_id")}
    return corpus_ids, corpus_texts, lookup

@lru_cache(maxsize=1)
def _get_bm25_index():
    corpus_ids, corpus_texts, lookup = _load_bm25_corpus()
    corpus_tokens = bm25s.tokenize(corpus_texts, stopwords=list(VI_STOPWORDS))
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    return retriever, corpus_ids, lookup

def refresh_bm25_index() -> None:
    """Gọi hàm này sau khi ingest/xoá tài liệu (vd cuối
    app/routers/documents.py) -- lru_cache ở trên không tự biết Mongo vừa
    đổi nên phải invalidate thủ công, nếu không BM25 sẽ tìm trên corpus cũ."""
    _get_bm25_index.cache_clear()


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = K_RRF) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, corpus_id in enumerate(ranking, start=1):
            scores[corpus_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])

class HybridSearchPipeline:
    def __init__(self):
        self.router = QueryRouter()
        self.rewriter = QueryRewriter()
        self.reranker = DocumentReranker()

    def process_user_query(self, query: str) -> Dict[str, Any]:
        # 1. Routing câu hỏi
        route = self.router.route(query)
        if route == "chitchat":
            return {"type": "chitchat", "queries": [query], "metadata": {}}
        if route == "term_definition":
            return {"type": "term_definition", "original_query": query}
        
        # 2. Rewrite & Extract Metadata
        extracted_info = self.rewriter.rewrite_and_extract_metadata(query)
        return {
            "type": "financial_search",
            "original_query": query,
            "search_queries": extracted_info.get("rewritten_queries", [query]),
            "metadata_filter": {
                "ticker": extracted_info.get("ticker"),
                "year": extracted_info.get("year")
            }
        }
    
    @staticmethod
    def _qdrant_filter(metadata_filter: dict) -> Optional[qmodels.Filter]:
        must = []
        if metadata_filter.get("ticker"):
            must.append(
                qmodels.FieldCondition(
                    key="ticker", match=qmodels.MatchValue(value=metadata_filter["ticker"])
                )
            )
        if metadata_filter.get("year"):
            must.append(
                qmodels.FieldCondition(
                    key="year", match=qmodels.MatchValue(value=int(metadata_filter["year"]))
                )
            )
        return qmodels.Filter(must=must) if must else None

    def bm25_search(self, query: str, k: int = BM25_TOP_K) -> List[tuple[str, float]]:
        retriever, corpus_ids, _ = _get_bm25_index()
        if not corpus_ids:
            return []
        query_tokens = bm25s.tokenize([query], stopwords=list(VI_STOPWORDS))
        indices, scores = retriever.retrieve(query_tokens, k=min(k, len(corpus_ids)))
        return [(corpus_ids[idx], float(score)) for idx, score in zip(indices[0], scores[0])]

    def dense_search(
        self,
        query: str,
        k: int = DENSE_TOP_K,
        qdrant_filter: Optional[qmodels.Filter] = None,
    ) -> List[tuple[str, float, dict]]:
        vector = embed_query(query, return_sparse=False)["dense"]
        hits = search_similar_blocks(vector, limit=k, filter_conditions=qdrant_filter)
        return [(str(hit.id), float(hit.score), hit.payload or {}) for hit in hits]
 
    def RRF_fuse(
        self,
        search_queries: List[str],
        qdrant_filter: Optional[qmodels.Filter] = None,
    ) -> tuple[List[str], Dict[str, dict]]:
        """Chạy BM25 + Dense cho từng rewritten query, gộp toàn bộ ranking
        (2 x số rewritten_queries ranking) bằng 1 lần RRF duy nhất -- RRF hỗ
        trợ fuse nhiều ranking cùng lúc nên không cần fuse riêng từng cặp.
 
        Trả về:
          fused_ids     : list[chunk_id] top FUSION_CANDIDATE_LIMIT, đã sort
                          theo rrf_score giảm dần
          content_lookup: dict[chunk_id -> {"content", "parent_id"}]
        """
        _, _, bm25_lookup = _get_bm25_index()
        rankings: List[List[str]] = []
        content_lookup: Dict[str, dict] = {}
 
        for q in search_queries:
            q_expanded = expand_query(q)          # xử lí từ viết, thuật ngữ tài chính
            bm25_hits = self.bm25_search(q_expanded)
            rankings.append([cid for cid, _ in bm25_hits])
            for cid, _ in bm25_hits:
                if cid not in content_lookup and cid in bm25_lookup:
                    content_lookup[cid] = bm25_lookup[cid]
 
            dense_hits = self.dense_search(q_expanded, qdrant_filter=qdrant_filter)
            rankings.append([cid for cid, _, _ in dense_hits])
            for cid, _, payload in dense_hits:
                if cid not in content_lookup:
                    content_lookup[cid] = {
                        "content": payload.get("content", ""),
                        "parent_id": payload.get("parent_id"),
                    }
 
        fused = reciprocal_rank_fusion(rankings)
        RRF_ids = [cid for cid, _ in fused][:FUSION_TOP_K]
        return RRF_ids, content_lookup

    def rerank(
        self,
        original_query: str,
        candidate_ids: List[str],
        content_lookup: Dict[str, dict],
        top_k: int = TOP_K,
    ) -> List[str]:
        valid_ids = [cid for cid in candidate_ids if content_lookup.get(cid, {}).get("content")]
        if not valid_ids:
            return []
        documents = [content_lookup[cid]["content"] for cid in valid_ids]
        ranked_indices = self.reranker.rerank(original_query, documents, top_k=top_k)
        return [valid_ids[i] for i in ranked_indices]

    def retrieve(self, user_query: str, top_k: int = TOP_K) -> Dict[str, Any]:
        """Entry point chính -- gọi hàm NÀY từ RAGController.execute_search()
        thay vì tự làm dense-search riêng như code cũ.
 
        Trả về:
          {
            "is_chitchat": bool,
            "chunk_ids": list[str],   # top_k chunk_id sau rerank
            "context": list[str],     # nội dung parent tương ứng, đã dedup
          }
        """
        prep = self.process_user_query(user_query)
        if prep["type"] == "chitchat":
            return {"is_chitchat": True, "chunk_ids": [], "context": []}
        if prep["type"] == "term_definition":
            return {"is_chitchat": False, "is_definition": True, "chunk_ids": [], "context": []}
 
        qdrant_filter = self._qdrant_filter(prep["metadata_filter"])
        RRF_ids, content_lookup = self.RRF_fuse(prep["search_queries"], qdrant_filter=qdrant_filter)
        top_chunk_ids = self.rerank(user_query, RRF_ids, content_lookup, top_k=top_k)
 
        seen_parents = set()
        contexts: List[str] = []
        for cid in top_chunk_ids:
            parent_id = content_lookup.get(cid, {}).get("parent_id")
            if not parent_id or parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)
            parent_doc = get_parent_chunk(parent_id)
            if parent_doc:
                contexts.append(parent_doc["content"])
 
        return {"is_chitchat": False, "chunk_ids": top_chunk_ids, "context": contexts}
