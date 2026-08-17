import pytest
from unittest.mock import MagicMock
from app.retrieval.rag_pipeline import RAGController

class TestRAGController:
    def test_execute_search_chitchat(self):
        mock_pipeline = MagicMock()
        mock_pipeline.retrieve.return_value = {
            "is_chitchat": True,
            "chunk_ids": [],
            "context": []
        }
        controller = RAGController(pipeline=mock_pipeline, top_k=5)
        res = controller.execute_search("Xin chào")
        assert res["is_chitchat"] is True
        assert res["context"] == []

    def test_execute_search_financial(self):
        mock_pipeline = MagicMock()
        mock_pipeline.retrieve.return_value = {
            "is_chitchat": False,
            "is_definition": False,
            "chunk_ids": ["c1", "c2"],
            "context": ["Context 1", "Context 2"]
        }
        controller = RAGController(pipeline=mock_pipeline, top_k=5)
        res = controller.execute_search("Doanh thu FPT năm 2024")
        assert res["is_chitchat"] is False
        assert res["is_definition"] is False
        assert len(res["context"]) == 2
