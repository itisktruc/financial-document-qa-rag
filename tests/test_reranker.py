import pytest
from app.retrieval.reranker import DocumentReranker

class TestDocumentReranker:
    def test_rerank_empty_documents(self):
        reranker = DocumentReranker()
        result = reranker.rerank("Query", [], top_k=3)
        assert result == []

    def test_rerank_ordering(self):
        reranker = DocumentReranker()
        query = "Doanh thu FPT năm 2024"
        docs = [
            "Công ty FPT công bố doanh thu năm 2024 đạt mốc mới tăng trưởng mạnh.",
            "Thời tiết hôm nay rất đẹp và nắng ấm.",
            "Báo cáo tài chính của công ty FPT ghi nhận doanh thu và lợi nhuận hợp nhất."
        ]
        indices = reranker.rerank(query, docs, top_k=2)
        assert len(indices) <= 2
        # Index 1 ("Thời tiết...") should not be ranked higher than index 0 or 2
        assert 1 not in indices[:1]
