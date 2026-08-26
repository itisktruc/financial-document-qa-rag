"""
app/retrieval/rag_pipeline.py

RAGController giờ CHỈ còn là lớp gọi mỏng (thin wrapper) sang
HybridSearchPipeline.retrieve() -- xem app/retrieval/hybrid_search.py.

Toàn bộ logic retrieval thật sự (dense search qua Qdrant, BM25 qua Mongo,
RRF fusion, rerank bằng BGE CrossEncoder, mở rộng parent qua MongoDB) đã
nằm hết trong HybridSearchPipeline, và pipeline đó tự quản lý kết nối
Qdrant (qua app.services.qdrant_store) + MongoDB (qua app.services.mongo_client)
của riêng nó -- nên RAGController KHÔNG cần nhận qdrant_client/mongo_db từ
bên ngoài nữa (bản cũ nhận nhưng thực chất self.qdrant/self.mongo chỉ được
dùng ngay trong execute_search(), giờ đã chuyển hết qua pipeline).

Giữ lại class này (thay vì gọi thẳng pipeline.retrieve() từ main.py) để:
  - main.py không cần biết cấu trúc trả về nội bộ của HybridSearchPipeline
    (chunk_ids, content_lookup...) -- chỉ nhận đúng {"context", "is_chitchat"}
    như API cũ, không phải sửa phần generation phía sau.
  - Có 1 chỗ duy nhất để chỉnh top_k mặc định cho toàn hệ thống.
"""

from __future__ import annotations
from typing import Any, Dict
from app.retrieval.hybrid_search import HybridSearchPipeline

TOP_K = 10  # số chunk cuối cùng lấy sau rerank, dùng làm context cho generation

class RAGController:
    def __init__(self, pipeline: HybridSearchPipeline, top_k: int = TOP_K):
        self.pipeline = pipeline
        self.top_k = top_k

    def execute_search(self, user_query: str) -> Dict[str, Any]:
        """Gọi toàn bộ hybrid pipeline (routing -> BM25+Dense -> RRF ->
        rerank -> parent-expansion) và trả kết quả đúng format cũ cho
        app/main.py: {"context": list[str], "is_chitchat": bool}."""
        result = self.pipeline.retrieve(user_query, top_k=self.top_k)
        return {
            "context": result.get("context", []),
            "is_chitchat": result.get("is_chitchat", False),
            "is_definition": result.get("is_definition", False),
            "is_calculation": result.get("is_calculation", False),
        }