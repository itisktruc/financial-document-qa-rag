import logging
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.config import settings

logger = logging.getLogger(__name__)


class QueryRouter:
    # Định hướng câu hỏi người dùng về luồng chitchat hoặc tra cứu tài chính.

    def __init__(self, model_name: str = "llama-3.3-70b-versatile") -> None:
        self.llm = ChatGroq(
            temperature=0.0,
            model_name=model_name,
            groq_api_key=settings.GROQ_API_KEY,
        )
        self.prompt = PromptTemplate(
            template=(
                "Bạn là trợ lý phân loại câu hỏi cho hệ thống RAG tài chính.\n"
                "Hãy phân loại câu hỏi sau đây vào đúng 1 trong 2 nhóm:\n"
                "1. 'chitchat': Câu chào hỏi, xã giao, hoặc không liên quan đến dữ liệu tài chính.\n"
                "2. 'financial_search': Yêu cầu tra cứu báo cáo tài chính, doanh thu, lợi nhuận, chỉ số doanh nghiệp.\n\n"
                "Chỉ trả về duy nhất một từ 'chitchat' hoặc 'financial_search'.\n\n"
                "Câu hỏi: {query}\n"
                "Phân loại:"
            ),
            input_variables=["query"],
        )
        self.chain = self.prompt | self.llm

    def route(self, query: str) -> str:
        """Phân loại câu hỏi thành 'chitchat' hoặc 'financial_search'."""
        if not query or not query.strip():
            return "chitchat"

        try:
            response = self.chain.invoke({"query": query}).content.strip().lower()
            return "chitchat" if "chitchat" in response else "financial_search"
        except Exception as err:
            logger.error(f"Lỗi khi routing query: {err}")
            return "financial_search"