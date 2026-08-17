import pytest
from unittest.mock import patch, MagicMock
from app.retrieval.hybrid_search import HybridSearchPipeline, reciprocal_rank_fusion

class TestReciprocalRankFusion:
    def test_rrf_scoring(self):
        ranking1 = ["doc_a", "doc_b", "doc_c"]
        ranking2 = ["doc_b", "doc_a", "doc_d"]
        fused = reciprocal_rank_fusion([ranking1, ranking2], k=60)
        
        fused_ids = [doc_id for doc_id, score in fused]
        # doc_a: 1/(60+1) + 1/(60+2)
        # doc_b: 1/(60+2) + 1/(60+1)
        # Both doc_a and doc_b should be at top
        assert set(fused_ids[:2]) == {"doc_a", "doc_b"}
        assert len(fused) == 4

class TestHybridSearchPipeline:
    @patch("app.retrieval.hybrid_search.QueryRouter")
    @patch("app.retrieval.hybrid_search.QueryRewriter")
    @patch("app.retrieval.hybrid_search.DocumentReranker")
    def test_process_user_query_chitchat(self, mock_reranker, mock_rewriter, mock_router):
        mock_router_inst = MagicMock()
        mock_router_inst.route.return_value = "chitchat"
        mock_router.return_value = mock_router_inst

        pipeline = HybridSearchPipeline()
        res = pipeline.process_user_query("Xin chào!")
        assert res["type"] == "chitchat"

    @patch("app.retrieval.hybrid_search.QueryRouter")
    @patch("app.retrieval.hybrid_search.QueryRewriter")
    @patch("app.retrieval.hybrid_search.DocumentReranker")
    def test_process_user_query_term_definition(self, mock_reranker, mock_rewriter, mock_router):
        mock_router_inst = MagicMock()
        mock_router_inst.route.return_value = "term_definition"
        mock_router.return_value = mock_router_inst

        pipeline = HybridSearchPipeline()
        res = pipeline.process_user_query("ROE là gì?")
        assert res["type"] == "term_definition"

    @patch("app.retrieval.hybrid_search.QueryRouter")
    @patch("app.retrieval.hybrid_search.QueryRewriter")
    @patch("app.retrieval.hybrid_search.DocumentReranker")
    def test_process_user_query_financial_search(self, mock_reranker, mock_rewriter, mock_router):
        mock_router_inst = MagicMock()
        mock_router_inst.route.return_value = "financial_search"
        mock_router.return_value = mock_router_inst

        mock_rewriter_inst = MagicMock()
        mock_rewriter_inst.rewrite_and_extract_metadata.return_value = {
            "ticker": "FPT",
            "year": "2024",
            "rewritten_queries": ["Doanh thu FPT 2024"]
        }
        mock_rewriter.return_value = mock_rewriter_inst

        pipeline = HybridSearchPipeline()
        res = pipeline.process_user_query("Doanh thu FPT năm 2024")
        assert res["type"] == "financial_search"
        assert res["metadata_filter"]["ticker"] == "FPT"
        assert res["metadata_filter"]["year"] == "2024"

    @patch.object(HybridSearchPipeline, "RRF_fuse")
    @patch.object(HybridSearchPipeline, "rerank")
    @patch("app.retrieval.hybrid_search.QueryRouter")
    @patch("app.retrieval.hybrid_search.QueryRewriter")
    @patch("app.retrieval.hybrid_search.DocumentReranker")
    def test_retrieve_end_to_end(self, mock_reranker, mock_rewriter, mock_router, mock_rerank_method, mock_rrf_fuse_method):
        mock_router_inst = MagicMock()
        mock_router_inst.route.return_value = "financial_search"
        mock_router.return_value = mock_router_inst

        mock_rewriter_inst = MagicMock()
        mock_rewriter_inst.rewrite_and_extract_metadata.return_value = {
            "ticker": "FPT", "year": "2024", "rewritten_queries": ["Query 1"]
        }
        mock_rewriter.return_value = mock_rewriter_inst

        mock_rrf_fuse_method.return_value = (["chunk_1", "chunk_2"], {"chunk_1": {"content": "C1", "parent_id": "p1"}})
        mock_rerank_method.return_value = ["chunk_1"]

        pipeline = HybridSearchPipeline()
        with patch("app.retrieval.hybrid_search.get_parent_chunk") as mock_get_parent:
            mock_get_parent.return_value = {"content": "Parent Content FPT 2024"}
            res = pipeline.retrieve("Doanh thu FPT 2024", top_k=5)

            assert res["is_chitchat"] is False
            assert res["chunk_ids"] == ["chunk_1"]
            assert res["context"] == ["Parent Content FPT 2024"]
