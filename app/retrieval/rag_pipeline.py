"""
app/retrieval/rag_pipeline.py

RAGController giờ CHỈ còn là lớp gọi mỏng (thin wrapper) sang
HybridSearchPipeline.retrieve() -- xem app/retrieval/hybrid_search.py.

Toàn bộ logic retrieval thật sự (dense search qua Qdrant, BM25 qua Mongo,
RRF fusion, rerank bằng BGE CrossEncoder, mở rộng parent qua MongoDB) đã
nằm hết trong HybridSearchPipeline, và pipeline đó tự quản lý kết nối
Qdrant (qua app.services.qdrant_store) + MongoDB (qua app.services.mongo_client)
của riêng nó -- nên RAGController KHÔNG cần nhận qdrant_client/mongo_db từ
bên ngoài nữa.

CẬP NHẬT: execute_search() giờ nhận thêm session_id (chuyển tiếp cho
HybridSearchPipeline.retrieve() để pipeline nhớ được công ty/năm/report_scope
đang thảo luận theo từng session -- xem HybridSearchPipeline._session_state)
và trả về thêm "entities" (danh sách công ty/năm/report_scope thực sự đã
dùng để lọc -- có thể nhiều hơn 1 với câu hỏi so sánh nhiều công ty), để
tầng generation phía sau (nếu cần) biết ngữ cảnh trả về gồm những công ty
nào.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from app.retrieval.hybrid_search import HybridSearchPipeline

TOP_K = 10  # số chunk cuối cùng lấy sau rerank, dùng làm context cho generation

class RAGController:
    def __init__(self, pipeline: HybridSearchPipeline, top_k: int = TOP_K):
        self.pipeline = pipeline
        self.top_k = top_k

    def execute_search(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Gọi toàn bộ hybrid pipeline (routing -> BM25+Dense -> RRF ->
        rerank -> parent-expansion) và trả kết quả đúng format cũ cho
        app/main.py: {"context": list[str], "is_chitchat": bool, ...},
        cộng thêm "entities" cho câu hỏi so sánh nhiều công ty."""
        result = self.pipeline.retrieve(user_query, top_k=self.top_k, session_id=session_id)
        return {
            "context": result.get("context", []),
            "is_chitchat": result.get("is_chitchat", False),
            "is_definition": result.get("is_definition", False),
            "is_calculation": result.get("is_calculation", False),
            "entities": result.get("entities", []),
        }