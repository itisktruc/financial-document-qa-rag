from typing import List, Dict, Any
from app.retrieval.query_router import QueryRouter
from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.reranker import DocumentReranker

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