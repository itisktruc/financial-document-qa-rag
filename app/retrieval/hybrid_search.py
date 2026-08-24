from typing import List, Dict, Any, Optional
from app.retrieval.query_router import QueryRouter
from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.reranker import DocumentReranker
from app.retrieval.glossary import expand_query
from app.generation.citation import build_citation
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

VI_STOPWORDS = {"là", "của", "và", "các", "một", "những", "cho", "về", "trong", "đã", "này", "được"}  # bổ sung thêm nếu cần
TICKER_MAPPING = {
    "32": "A32",
    "CL3": "A32",
    "công ty cổ phần 32": "A32",
    "cty 32": "A32",
    "a32": "A32",
    "công ty A32": "A32",
}

K_RRF = 60                     # hằng số k trong công thức RRF: 1 / (k + rank)
BM25_TOP_K = 50                # số ứng viên BM25 lấy mỗi query
DENSE_TOP_K = 100               # số ứng viên Dense lấy mỗi query
FUSION_TOP_K = 50              # số chunks sau RRF đưa vào reranker
TOP_K = 20                     # số chunks cuối cùng sau reranker

CHILD_IDS_DEBUG = {
    "8a2cb86f9c084bd2f09673ee067c34da",
    "9b4a7279f470c574c4c9e5384b51a0f8",
    "74b8d4489ccb84290e1f9f09d529de9d",
    "89a797efa3156c3e98d4ac6f07a894c7",
    "60944a6793f6545b7b0add443578acca",
    "b1ab7dd6a6f558786fc266a13eff73e9",
    "01cc9903f2e1d1e30d17931a037a858a",
}

def _load_bm25_corpus():
    # Sửa chunk_type thành "child" và đổi "content" thành "text"
    # docs = get_chunks_collection().find(
    #     {"chunk_type": {"$in": ["child", "parent"]}},
    #     {"text": 1, "parent_id": 1},
    # )
    docs = get_chunks_collection().find({}, {"chunks": 1})
    corpus_ids: List[str] = []
    corpus_texts: List[str] = []
    lookup: Dict[str, dict] = {}

    # for doc in docs:
    #     cid = str(doc["_id"])
    #     text = doc.get("text", "") or ""
    #     corpus_ids.append(cid)
    #     corpus_texts.append(text)
    #     lookup[cid] = {"content": text, "parent_id": doc.get("parent_id")}
    # return corpus_ids, corpus_texts, lookup

    for doc in docs:
        chunks = doc.get("chunks", [])
        for chunk in chunks:
            cid = str(chunk.get("_id") or chunk.get("chunk_id"))
            text = (chunk.get("text") or "").strip()
            if text:
                corpus_ids.append(cid)
                corpus_texts.append(text)
                lookup[cid] = {
                    "content": text, 
                    "parent_id": chunk.get("parent_id") or cid,
                    "ticker": chunk.get("ticker"),
                    "year": chunk.get("year"),
                }
                    
    return corpus_ids, corpus_texts, lookup

@lru_cache(maxsize=1)
def _get_bm25_index():
    corpus_ids, corpus_texts, lookup = _load_bm25_corpus()
    corpus_tokens = bm25s.tokenize(corpus_texts, stopwords=list(VI_STOPWORDS))
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    if not corpus_ids or not corpus_texts:
        return None, [], {}
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
        if not metadata_filter:
            return None
        must = []
        raw_ticker = metadata_filter.get("ticker")
        if raw_ticker:
            ticker_str = str(raw_ticker).strip().upper()
            clean_ticker = TICKER_MAPPING.get(ticker_str, ticker_str)

            must.append(
            qmodels.FieldCondition(
                key="ticker", 
                match=qmodels.MatchValue(value=clean_ticker)
                )   
            )
        raw_year = metadata_filter.get("year")
        if raw_year:
            try:
                must.append(
                qmodels.FieldCondition(
                    key="year", 
                    match=qmodels.MatchValue(value=int(raw_year))
                )
            )
            except (ValueError, TypeError):
                pass  
        return qmodels.Filter(must=must) if must else None
        # must = []
        # if metadata_filter.get("ticker"):
        #     must.append(
        #         qmodels.FieldCondition(
        #             key="ticker", match=qmodels.MatchValue(value=metadata_filter["ticker"])
        #         )
        #     )
        # if metadata_filter.get("year"):
        #     must.append(
        #         qmodels.FieldCondition(
        #             key="year", match=qmodels.MatchValue(value=int(metadata_filter["year"]))
        #         )
        #     )
        # return qmodels.Filter(must=must) if must else None

    def bm25_search(self, query: str, k: int = BM25_TOP_K, metadata_filter: Optional[dict] = None):
        # retriever, corpus_ids, _ = _get_bm25_index()
        # if not retriever or not corpus_ids:
        #     return []
        # query_tokens = bm25s.tokenize([query], stopwords=list(VI_STOPWORDS))
        # indices, scores = retriever.retrieve(query_tokens, k=min(k, len(corpus_ids)))
        # return [(corpus_ids[idx], float(score)) for idx, score in zip(indices[0], scores[0])]
        retriever, corpus_ids, lookup = _get_bm25_index()
        if not retriever or not corpus_ids:
            return []
        query_tokens = bm25s.tokenize([query], stopwords=list(VI_STOPWORDS))
        indices, scores = retriever.retrieve(query_tokens, k=min(k, len(corpus_ids)))
        hits = [(corpus_ids[idx], float(score)) for idx, score in zip(indices[0], scores[0])]

        if metadata_filter:
            want_ticker = metadata_filter.get("ticker")
            want_year = metadata_filter.get("year")
            def matches(cid):
                info = lookup.get(cid, {})
                if want_ticker and str(info.get("ticker") or "").upper() != str(want_ticker).upper():
                    return False
                if want_year and str(info.get("year") or "") != str(want_year):
                    return False
                return True
            hits = [h for h in hits if matches(h[0])]
        return hits[:k]

    def dense_search(
        self,
        query: str,
        k: int = DENSE_TOP_K,
        qdrant_filter: Optional[qmodels.Filter] = None,
    ) -> List[tuple[str, float, dict]]:
        vector = embed_query(query, return_sparse=False)["dense"]
        hits = search_similar_blocks(vector, limit=k, filter_conditions=qdrant_filter)
        result = [(str(hit.id), float(hit.score), hit.payload or {}) for hit in hits]

        hit_children = [(cid, score) for cid, score, _ in result if cid in CHILD_IDS_DEBUG]
        print(f"[dense_search] query={query!r} | trả về {len(result)} hit | "
          f"child của parent 108 xuất hiện: {hit_children}")
        return result
        
        #return [(str(hit.id), float(hit.score), hit.payload or {}) for hit in hits]
 
    def RRF_fuse(
        self,
        search_queries: List[str],
        qdrant_filter: Optional[qmodels.Filter] = None,
        metadata_filter=None,
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
            bm25_hits = self.bm25_search(q_expanded, metadata_filter=metadata_filter)
            rankings.append([cid for cid, _ in bm25_hits])
            for cid, _ in bm25_hits:
                if cid not in content_lookup and cid in bm25_lookup:
                    content_lookup[cid] = bm25_lookup[cid]
 
            dense_hits = self.dense_search(q_expanded, qdrant_filter=qdrant_filter)
            rankings.append([cid for cid, _, _ in dense_hits])
            for cid, _, payload in dense_hits:
                if cid not in content_lookup:
                    text_content = payload.get("text") or payload.get("content", "")
                    content_lookup[cid] = {
                        "content": text_content,
                        "parent_id": payload.get("parent_id"),
                    }
 
        fused = reciprocal_rank_fusion(rankings)
        RRF_ids = [cid for cid, _ in fused][:FUSION_TOP_K]
        ranks_in_fused = {cid: (i, score) for i, (cid, score) in enumerate(fused) if cid in CHILD_IDS_DEBUG}
        print(f"[RRF_fuse] child của parent 108 trong fused (trước cắt top {FUSION_TOP_K}): {ranks_in_fused}")
        print(f"[RRF_fuse] có lọt vào RRF_ids (top {FUSION_TOP_K}) không: "
          f"{[cid for cid in RRF_ids if cid in CHILD_IDS_DEBUG]}")
        return RRF_ids, content_lookup

    def rerank(
        self,
        original_query: str,
        candidate_ids: List[str],
        content_lookup: Dict[str, dict],
        top_k: int = TOP_K,
    ) -> List[str]:
        # valid_ids = [cid for cid in candidate_ids if content_lookup.get(cid, {}).get("content")]
        # if not valid_ids:
        #     return []
        # documents = [content_lookup[cid]["content"] for cid in valid_ids]
        # ranked_indices = self.reranker.rerank(original_query, documents, top_k=top_k)
        # return [valid_ids[i] for i in ranked_indices]

        valid_ids = [cid for cid in candidate_ids if content_lookup.get(cid, {}).get("content")]
        print(f"[rerank] child của parent 108 có mặt trong candidate đưa vào reranker: "
            f"{[cid for cid in valid_ids if cid in CHILD_IDS_DEBUG]}")
        if not valid_ids:
            return []
        documents = [content_lookup[cid]["content"] for cid in valid_ids]
        ranked_indices = self.reranker.rerank(original_query, documents, top_k=top_k)
        result = [valid_ids[i] for i in ranked_indices]
        print(f"[rerank] child của parent 108 sống sót sau rerank (top {top_k}): "
        f"{[cid for cid in result if cid in CHILD_IDS_DEBUG]}")
        return result

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
        metadata_filter = prep.get("metadata_filter", {})
        if prep["type"] == "chitchat":
            return {"is_chitchat": True, "chunk_ids": [], "context": []}
        if prep["type"] == "term_definition":
            return {"is_chitchat": False, "is_definition": True, "chunk_ids": [], "context": []}
 
        qdrant_filter = self._qdrant_filter(prep["metadata_filter"])
        print(f"[retrieve] metadata_filter trích được: {metadata_filter}")
        print(f"[retrieve] qdrant_filter build ra: {qdrant_filter}")
        RRF_ids, content_lookup = self.RRF_fuse(prep["search_queries"], qdrant_filter=qdrant_filter, metadata_filter=metadata_filter)
        if not RRF_ids and metadata_filter.get("ticker"):
            print("[*] Lần 1 không thấy data. Tiến hành Fallback: Bỏ lọc Year, BẮT BUỘC giữ Ticker...")
        
            # Tạo bộ lọc cứng chỉ chứa duy nhất Ticker
            raw_ticker = str(metadata_filter["ticker"]).strip().upper()
            clean_ticker = TICKER_MAPPING.get(raw_ticker, raw_ticker)
            
            strict_ticker_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="ticker",
                        match=qmodels.MatchValue(value=clean_ticker)
                    )
                ]
            )
            # Chạy RRF Lần 2 với bộ lọc cứng Ticker
            RRF_ids, content_lookup = self.RRF_fuse(prep["search_queries"], qdrant_filter=strict_ticker_filter)

        top_chunk_ids = self.rerank(user_query, RRF_ids, content_lookup, top_k=top_k)
 
        seen_parents = set()
        contexts: List[str] = []
        for cid in top_chunk_ids:
            chunk_info = content_lookup.get(cid, {})
            target_parent_id = chunk_info.get("parent_id") or cid
            if target_parent_id in seen_parents:
                continue
            seen_parents.add(target_parent_id)

            # Truy vấn Parent Document từ Mongo
            parent_doc = get_parent_chunk(target_parent_id)
            if parent_doc:
                text_content = parent_doc.get("text") or parent_doc.get("content", "")
                citation_info = {
                    "doc_id": parent_doc.get("doc_id"),
                    "source_file": parent_doc.get("source_file"),
                    "page_start": parent_doc.get("page_start"),
                    "page_end": parent_doc.get("page_end"),
                    "section": parent_doc.get("section") or parent_doc.get("heading"),
                    "ticker": parent_doc.get("ticker"),
                    "year": parent_doc.get("year"),
                }
            else:
                # Fallback lấy trực tiếp nội dung từ content_lookup nếu Mongo chưa bóc tách xong
                text_content = chunk_info.get("content", "")
                citation_info = {
                    "doc_id": cid,
                    "source_file": "Báo cáo tài chính",
                    "page_start": None,
                    "page_end": None,
                    "section": None,
                }

            if text_content and not any(c["content"] == text_content for c in contexts):
                contexts.append({
                    "content": text_content,
                    "citation": citation_info
                })

        return {
            "is_chitchat": False,
            "is_definition": False,
            "chunk_ids": top_chunk_ids,
            "context": contexts,
        }
