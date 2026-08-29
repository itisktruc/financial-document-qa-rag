from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.retrieval.hybrid_search import HybridSearchPipeline

TOP_K = 10  # số chunk cuối cùng lấy sau rerank, dùng làm context cho generation

class RAGController:
    def __init__(self, pipeline: HybridSearchPipeline, top_k: int = TOP_K):
        self.pipeline = pipeline
        self.top_k = top_k

    def execute_search(self, user_query: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Gọi toàn bộ hybrid pipeline (routing -> BM25+Dense -> RRF ->
        rerank -> parent-expansion) và trả kết quả đúng format cũ cho
        app/main.py: {"context": list[str], "is_chitchat": bool}."""
        result = self.pipeline.retrieve(user_query, top_k=self.top_k, history=history)
        return {
            "context": result.get("context", []),
            "is_chitchat": result.get("is_chitchat", False),
            "is_definition": result.get("is_definition", False),
            "is_calculation": result.get("is_calculation", False),
        }