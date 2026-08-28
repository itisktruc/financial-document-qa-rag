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
DENSE_TOP_K = 50               # số ứng viên Dense lấy mỗi query
FUSION_TOP_K = 50              # số chunks sau RRF đưa vào reranker
TOP_K = 20                     # số chunks cuối cùng sau reranker

def _normalize_cid(cid: Any) -> str:
    """Chuẩn hoá chunk_id/parent_id về dạng hex thô không gạch ngang (đồng bộ với MongoDB),
    loại bỏ hoàn toàn dấu gạch ngang do Qdrant tự động ép sang định dạng UUID chuẩn.
    """
    if not cid:
        return ""
    return str(cid).replace("-", "").strip()

def ticker_year_filter(metadata_filter: Optional[dict]) -> tuple[dict, Optional[qmodels.Filter]]:
    """
    Chuẩn hóa ticker/year và trả về đồng thời:
    - mongo_query: Dict điều kiện lọc cho MongoDB (dùng trong BM25)
    - qdrant_filter: Object qmodels.Filter cho Qdrant (dùng trong Dense)
    """
    if not metadata_filter:
        return {}, None

    mongo_query = {}
    must_qdrant = []

    # 1. Chuẩn hóa Ticker
    raw_ticker = metadata_filter.get("ticker")
    if raw_ticker:
        ticker_str = str(raw_ticker).strip().upper()
        clean_ticker = TICKER_MAPPING.get(ticker_str, ticker_str)
        
        mongo_query["ticker"] = clean_ticker
        must_qdrant.append(
            qmodels.FieldCondition(
                key="ticker", match=qmodels.MatchValue(value=clean_ticker)
            )
        )

    # 2. Chuẩn hóa Year
    raw_year = metadata_filter.get("year")
    if raw_year:
        try:
            clean_year = int(raw_year)
        except (ValueError, TypeError):
            clean_year = raw_year
            
        mongo_query["year"] = clean_year
        must_qdrant.append(
            qmodels.FieldCondition(
                key="year", match=qmodels.MatchValue(value=clean_year)
            )
        )

    qdrant_filter = qmodels.Filter(must=must_qdrant) if must_qdrant else None
    return mongo_query, qdrant_filter

def _load_bm25_corpus(ticker: Optional[str] = None, year: Optional[int] = None):
    mongo_query: dict = {}
    if ticker:
        mongo_query["ticker"] = ticker
    if year:
        mongo_query["year"] = year
    docs = list(
        get_chunks_collection().find(
            mongo_query, {"chunks": 1, "ticker": 1, "year": 1, "source_file": 1}
        )
    )
    print(f"[BM25] Đã lọc ra {len(docs)} file khớp với công ty và năm {mongo_query}:")
    for doc in docs:
        print(f"File ID: {doc['_id']}")
    corpus_ids: List[str] = []
    corpus_texts: List[str] = []
    lookup: Dict[str, dict] = {}

    for doc in docs:
        chunks = doc.get("chunks", [])
        for local_idx, chunk in enumerate(chunks):            
            raw_cid = str(chunk.get("_id") or chunk.get("chunk_id"))
            cid = _normalize_cid(raw_cid)
            text = (chunk.get("text") or "").strip()
            if text:
                corpus_ids.append(cid)
                corpus_texts.append(text)
                lookup[cid] = {
                    "content": text, 
                    "parent_id": _normalize_cid(chunk.get("parent_id")) or cid,
                    "ticker": chunk.get("ticker"),
                    "year": chunk.get("year"),
                    "order_index": local_idx
                }
                    
    return corpus_ids, corpus_texts, lookup

@lru_cache(maxsize=64)
def _get_bm25_index(ticker: Optional[str] = None, year: Optional[int] = None):
    corpus_ids, corpus_texts, lookup = _load_bm25_corpus(ticker=ticker, year=year)
    corpus_tokens = bm25s.tokenize(corpus_texts, stopwords=list(VI_STOPWORDS))
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    if not corpus_ids or not corpus_texts:
        print("[BM25] Không tìm thấy tài liệu phù hợp trong MongoDB")
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
        if route == "calculation":
            # Không đi qua rewrite/RRF ở đây -- xử lý riêng bởi
            # nhánh app.calculation.calculation_service.
            return {"type": "calculation", "original_query": query}
        
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
    
    def bm25_search(self, query: str, k: int = BM25_TOP_K, metadata_filter: Optional[dict] = None):
        mongo_query, _ = ticker_year_filter(metadata_filter)
        ticker, year = mongo_query.get("ticker"), mongo_query.get("year")

        retriever, corpus_ids, lookup = _get_bm25_index(ticker=ticker, year=year)        
        if not retriever or not corpus_ids:
            return []
        
        print(f"[BM25] Đang phân tách chuỗi (split strings) và tokenize query người dùng: (filter ticker={ticker}, year={year})")
        query_tokens = bm25s.tokenize([query], stopwords=list(VI_STOPWORDS))

        print("[BM25] Đang truy vấn BM25 index")
        indices, scores = retriever.retrieve(query_tokens, k=min(k, len(corpus_ids)))
        hits = [(_normalize_cid(corpus_ids[idx]), float(score)) for idx, score in zip(indices[0], scores[0])]

        bm25_mongo_indices = [lookup[cid]["order_index"] for cid, _ in hits[:k] if cid in lookup]
        print(f"[BM25] Đã lọc ra {len(hits)} chunk trong MongoDB có các index: {bm25_mongo_indices}")
        return hits[:k]

    def dense_search(
        self,
        query: str,
        k: int = DENSE_TOP_K,
        metadata_filter: Optional[dict] = None,
    ) -> List[tuple[str, float, dict]]:
        _, qdrant_filter = ticker_year_filter(metadata_filter)

        print("[Dense] Đang tạo Vector Embedding cho câu hỏi")
        vector = embed_query(query, return_sparse=False)["dense"]

        hits = search_similar_blocks(vector, limit=k, filter_conditions=qdrant_filter)
        result = [(_normalize_cid(hit.id), float(hit.score), hit.payload or {}) for hit in hits]

        dense_order_indices = [
            hit.payload.get("order_index")
            for hit in hits if hit.payload
        ]
        print(f"[Dense] Đã lọc ra top {len(result)} vector point tốt nhất trên Qdrant với order_index: {dense_order_indices}")
        return result
         
    def RRF_fuse(
        self,
        search_queries: List[str],
        metadata_filter: Optional[dict] = None,  
    ) -> tuple[List[str], Dict[str, dict]]:
        """Chạy BM25 + Dense cho từng rewritten query, gộp toàn bộ ranking
        (2 x số rewritten_queries ranking) bằng 1 lần RRF duy nhất -- RRF hỗ
        trợ fuse nhiều ranking cùng lúc nên không cần fuse riêng từng cặp.
 
        Trả về:
          fused_ids     : list[chunk_id] top FUSION_CANDIDATE_LIMIT, đã sort
                          theo rrf_score giảm dần
          content_lookup: dict[chunk_id -> {"content", "parent_id"}]
        """
        mongo_query, _ = ticker_year_filter(metadata_filter)
        ticker, year = mongo_query.get("ticker"), mongo_query.get("year")

        _, corpus_ids, bm25_lookup = _get_bm25_index(ticker=ticker, year=year)
        rankings: List[List[str]] = []
        content_lookup: Dict[str, dict] = {}
        qdrant_cid_to_order_idx: Dict[str, Any] = {}  # Lưu order_index của các chunk xuất hiện từ Qdrant
 
        for q in search_queries:
            q_expanded = expand_query(q)          # xử lí từ viết, thuật ngữ tài chính
            
            bm25_hits = self.bm25_search(q_expanded, metadata_filter=metadata_filter)
            rankings.append([_normalize_cid(cid) for cid, _ in bm25_hits])
            for cid, _ in bm25_hits:
                norm_cid = _normalize_cid(cid)
                if norm_cid not in content_lookup and norm_cid in bm25_lookup:
                    content_lookup[norm_cid] = bm25_lookup[norm_cid]
 
            dense_hits = self.dense_search(q_expanded, metadata_filter=metadata_filter)
            rankings.append([_normalize_cid(cid) for cid, _, _ in dense_hits])            
            for cid, _, payload in dense_hits:
                norm_cid = _normalize_cid(cid)
                if norm_cid not in content_lookup:
                    text_content = payload.get("text") or payload.get("content", "")
                    content_lookup[norm_cid] = {
                        "content": text_content,
                        "parent_id": _normalize_cid(payload.get("parent_id")) if payload.get("parent_id") else None,
                        "order_index": payload.get("order_index")
                    }
                if norm_cid not in qdrant_cid_to_order_idx:
                    qdrant_cid_to_order_idx[norm_cid] = payload.get("order_index")
 
        fused = reciprocal_rank_fusion(rankings)
        RRF_ids = [_normalize_cid(cid) for cid, _ in fused][:FUSION_TOP_K]
        
        cid_to_mongo_idx = {cid: idx for idx, cid in enumerate(corpus_ids)} if corpus_ids else {}
        RRF_mongo_indices = [cid_to_mongo_idx[cid] for cid in RRF_ids if cid in cid_to_mongo_idx]

        RRF_qdrant_indices = [qdrant_cid_to_order_idx[cid] for cid in RRF_ids if cid in qdrant_cid_to_order_idx and qdrant_cid_to_order_idx[cid] is not None]
        
        print(f"[RRF_Fusion] Đã chạy RRF trên quy trình BM25 song song Dense Vector (filter ticker={ticker}, year={year}). Top {len(RRF_ids)} chunk ID chọn ra: {RRF_ids}")
        if RRF_mongo_indices:
            print(f"[RRF_Fusion] Vị trí index tương ứng của top {len(RRF_mongo_indices)} chunk trong MongoDB: {RRF_mongo_indices}")
        if RRF_qdrant_indices:
            print(f"[RRF_Fusion] Vị trí order_index tương ứng của top {len(RRF_qdrant_indices)} chunk từ Qdrant: {RRF_qdrant_indices}")
        return RRF_ids, content_lookup

    def rerank(
        self,
        original_query: str,
        candidate_ids: List[str],
        content_lookup: Dict[str, dict],
        top_k: int = TOP_K,
    ) -> List[str]:
        valid_ids = [_normalize_cid(cid) for cid in candidate_ids if content_lookup.get(cid, {}).get("content")]
        if not valid_ids:
            return []
        documents = [content_lookup[cid]["content"] for cid in valid_ids]
        print(f"[Reranker] Đang tính điểm Rerank cho {len(documents)} tài liệu")
        ranked_indices = self.reranker.rerank(original_query, documents, top_k=top_k)
        result = [valid_ids[i] for i in ranked_indices]

        print(f"[Reranker] Top {len(result)} chunk ID cuối cùng được giữ lại: {result}")
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
        if prep["type"] == "calculation":
            return {"is_chitchat": False, "is_definition": False, "is_calculation": True, "chunk_ids": [], "context": []}
 
        mongo_query, qdrant_filter = ticker_year_filter(metadata_filter)
        print(f"[retrieve] metadata_filter trích được: {metadata_filter}")
        print(f"[retrieve] Áp dụng lọc công ty={metadata_filter.get('ticker')}, năm={metadata_filter.get('year')} "
              f"cho cả BM25 (mongo_query={mongo_query}) và Dense Vector "
              f"(qdrant_filter={qdrant_filter.model_dump(exclude_none=True) if qdrant_filter else None})")
        RRF_ids, content_lookup = self.RRF_fuse(prep["search_queries"], metadata_filter=metadata_filter)
        if not RRF_ids and metadata_filter.get("ticker"):
            print("[*] Lần 1 không thấy data. Tiến hành Fallback: Bỏ lọc Year, BẮT BUỘC giữ Ticker...")
            fallback_filter = {"ticker": metadata_filter["ticker"]}
            RRF_ids, content_lookup = self.RRF_fuse(prep["search_queries"], metadata_filter=fallback_filter)

        top_chunk_ids = self.rerank(user_query, RRF_ids, content_lookup, top_k=top_k)
 
        seen_parents = set()
        contexts: List[str] = []
        for cid in top_chunk_ids:
            norm_cid = _normalize_cid(cid)
            chunk_info = content_lookup.get(norm_cid, {})
            target_parent_id = _normalize_cid(chunk_info.get("parent_id")) or norm_cid            
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
                    "doc_id": norm_cid,
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
