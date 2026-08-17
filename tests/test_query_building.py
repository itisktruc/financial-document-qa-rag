import pytest
from unittest.mock import MagicMock, patch
from app.retrieval.query_router import QueryRouter
from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.glossary import expand_query, FINANCIAL_GLOSSARY
from langchain_core.messages import AIMessage

class TestGlossary:
    def test_expand_query_known_terms(self):
        query = "Cho biết LNST và ROE của FPT năm 2024"
        expanded = expand_query(query)
        assert "lợi nhuận sau thuế" in expanded.lower()
        assert "tỷ suất lợi nhuận trên vốn chủ sở hữu" in expanded.lower()

    def test_expand_query_unknown_terms(self):
        query = "Doanh thu năm 2024"
        expanded = expand_query(query)
        assert expanded == query

class TestQueryRouter:
    @patch("app.retrieval.query_router.ChatGroq")
    def test_route_chitchat(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="chitchat")
        mock_llm.side_effect = lambda *args, **kwargs: AIMessage(content="chitchat")
        mock_chat_groq.return_value = mock_llm

        router = QueryRouter()
        with patch.object(router.llm, "invoke", return_value=AIMessage(content="chitchat")):
            with patch("langchain_core.prompts.PromptTemplate.__or__") as mock_or:
                mock_chain = MagicMock()
                mock_chain.invoke.return_value = AIMessage(content="chitchat")
                mock_or.return_value = mock_chain
                result = router.route("Xin chào bạn là ai?")
                assert result == "chitchat"

    @patch("app.retrieval.query_router.ChatGroq")
    def test_route_term_definition(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm

        router = QueryRouter()
        with patch("langchain_core.prompts.PromptTemplate.__or__") as mock_or:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = AIMessage(content="term_definition")
            mock_or.return_value = mock_chain
            result = router.route("EBITDA là gì?")
            assert result == "term_definition"

    @patch("app.retrieval.query_router.ChatGroq")
    def test_route_financial_search(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm

        router = QueryRouter()
        with patch("langchain_core.prompts.PromptTemplate.__or__") as mock_or:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = AIMessage(content="financial_search")
            mock_or.return_value = mock_chain
            result = router.route("Doanh thu FPT năm 2024")
            assert result == "financial_search"

class TestQueryRewriter:
    @patch("app.retrieval.query_rewriter.ChatGroq")
    def test_rewrite_and_extract_metadata_success(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm

        rewriter = QueryRewriter()
        with patch("langchain_core.prompts.PromptTemplate.__or__") as mock_or:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = AIMessage(
                content='{"ticker": "FPT", "year": "2024", "rewritten_queries": ["Doanh thu FPT 2024", "Lợi nhuận FPT 2024", "Kết quả kinh doanh FPT 2024"]}'
            )
            mock_or.return_value = mock_chain
            res = rewriter.rewrite_and_extract_metadata("Doanh thu FPT 2024 thế nào?")
            assert res["ticker"] == "FPT"
            assert res["year"] == "2024"
            assert len(res["rewritten_queries"]) == 3

    @patch("app.retrieval.query_rewriter.ChatGroq")
    def test_rewrite_and_extract_metadata_json_error_fallback(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm

        rewriter = QueryRewriter()
        with patch("langchain_core.prompts.PromptTemplate.__or__") as mock_or:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = AIMessage(content="Invalid json response")
            mock_or.return_value = mock_chain
            res = rewriter.rewrite_and_extract_metadata("Câu hỏi bất kỳ")
            assert res["ticker"] is None
            assert res["year"] is None
            assert res["rewritten_queries"] == ["Câu hỏi bất kỳ"]
