import logging
from collections import defaultdict
from typing import Any, Dict, List

from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.query_router import QueryRouter
from app.retrieval.reranker import DocumentReranker

logger = logging.getLogger(__name__)


class HybridSearchPipeline:
    # Pipeline kết hợp Query Processing, Hybrid Search RRF và Reranking.

    def __init__(self) -> None:
        self.router = QueryRouter()
        self.rewriter = QueryRewriter()
        self.reranker = DocumentReranker()

    @staticmethod
    def reciprocal_rank_fusion(
        results_list: List[List[str]], 
        k: int = 60
    ) -> List[str]:
        # Thuật toán gộp danh sách kết quả tìm kiếm Reciprocal Rank Fusion (RRF).
        rrf_scores: Dict[str, float] = defaultdict(float)

        for docs in results_list:
            for rank, doc in enumerate(docs, start=1):
                rrf_scores[doc] += 1.0 / (k + rank)

        sorted_docs = sorted(
            rrf_scores.items(), 
            key=lambda item: item[1], 
            reverse=True
        )
        return [doc for doc, _ in sorted_docs]

    def process_and_search(
        self,
        user_query: str,
        dense_results: List[str],
        sparse_results: List[str],
        top_k: int = 3,
    ) -> Dict[str, Any]:
        # Điều phối toàn bộ quy trình nhận truy vấn và trích xuất văn bản tối ưu.
        route_type = self.router.route(user_query)
        if route_type == "chitchat":
            return {"type": "chitchat", "final_context": []}

        extracted_info = self.rewriter.rewrite_and_extract_metadata(user_query)
        fused_documents = self.reciprocal_rank_fusion([dense_results, sparse_results])
        
        final_ranked_docs = self.reranker.rerank(
            query=user_query,
            documents=fused_documents,
            top_k=top_k,
        )

        return {
            "type": "financial_search",
            "extracted_metadata": extracted_info,
            "final_context": final_ranked_docs,
        }