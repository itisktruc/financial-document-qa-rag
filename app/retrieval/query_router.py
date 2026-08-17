import re
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def _heuristic_route(query: str) -> str:
    lower = query.lower()
    # Word boundary regex matching to prevent false substring matches (e.g. 'hi' in 'nhiêu')
    if re.search(r'\b(chào|hi|hello)\b', lower) or "bạn là ai" in lower or "tên bạn" in lower:
        return "chitchat"
    if any(phrase in lower for phrase in ["là gì", "nghĩa là gì", "giải thích", "khái niệm", "tính thế nào", "tính như thế nào"]):
        return "term_definition"
    return "financial_search"

class QueryRouter:
    def __init__(self):
        self.llm = None
        if settings.GROQ_API_KEY:
            try:
                self.llm = ChatGroq(
                    temperature=0, 
                    model_name="llama-3.3-70b-versatile", 
                    groq_api_key=settings.GROQ_API_KEY
                )
            except Exception as e:
                logger.warning(f"Could not initialize ChatGroq QueryRouter: {e}")
                self.llm = None
        
    def route(self, query: str) -> str:
        if not self.llm:
            return _heuristic_route(query)

        prompt = PromptTemplate(
            template="""Bạn là trợ lý phân loại câu hỏi cho hệ thống RAG tài chính.
Hãy phân loại câu hỏi sau đây vào đúng 1 trong 3 nhóm:
1. 'chitchat': Nếu là câu chào hỏi, xã giao, hoặc câu hỏi chung không liên quan đến dữ liệu tài chính (ví dụ: 'Chào bạn', 'Bạn tên gì?').
2. 'financial_search': Nếu câu hỏi yêu cầu tra cứu thông tin báo cáo tài chính, doanh thu, lợi nhuận, chỉ số công ty (ví dụ: 'Doanh thu FPT năm 2023').
3. 'term_definition': hỏi về Ý NGHĨA/GIẢI THÍCH khái niệm của một thuật ngữ, từ viết tắt, khái niệm tài chính chung (ví dụ 'LNST là gì', 'ROE nghĩa là gì',
   'EPS được tính như thế nào') -- KHÔNG hỏi số liệu cụ thể của công ty nào.

Chỉ trả về đúng 1 từ: 'chitchat', 'financial_search', hoặc 'term_definition'.

Câu hỏi: {query}
Phân loại:""",
            input_variables=["query"]
        )
        try:
            chain = prompt | self.llm
            response = chain.invoke({"query": query}).content.strip().lower()
            if "term_definition" in response or "definition" in response:
                return "term_definition"
            if "chitchat" in response:
                return "chitchat"
            return "financial_search"
        except Exception as e:
            logger.warning(f"Error invoking ChatGroq QueryRouter: {e}. Falling back to heuristic.")
            return _heuristic_route(query)