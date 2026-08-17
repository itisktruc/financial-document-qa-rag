import json
import re
from typing import Dict, List, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class QueryRewriter:
    def __init__(self):
        self.llm = None
        if settings.GROQ_API_KEY:
            try:
                self.llm = ChatGroq(
                    temperature=0.1, 
                    model_name="llama-3.3-70b-versatile", 
                    groq_api_key=settings.GROQ_API_KEY
                )
            except Exception as e:
                logger.warning(f"Could not initialize ChatGroq QueryRewriter: {e}")
                self.llm = None

    def rewrite_and_extract_metadata(self, query: str) -> Dict[str, Any]:
        """Viết lại câu hỏi thành các dạng tìm kiếm khác nhau và trích xuất bộ lọc Metadata."""
        if not self.llm or not settings.GROQ_API_KEY:
            ticker = None
            year = None
            ticker_match = re.search(r'\b[A-Z]{3,4}\b', query)
            if ticker_match:
                ticker = ticker_match.group(0)
            year_match = re.search(r'\b(20\d{2})\b', query)
            if year_match:
                year = year_match.group(0)
            return {
                "ticker": ticker,
                "year": year,
                "rewritten_queries": [query]
            }

        prompt = PromptTemplate(
            template="""Bạn là chuyên gia phân tích truy vấn tài chính.
Nhiệm vụ của bạn:
1. Trích xuất tên mã cổ phiếu/công ty (ticker - viết hoa, ví dụ: FPT, VNM, VIC) và năm (year) từ câu hỏi nếu có.
2. Tạo 3 câu hỏi tương đương (rewritten_queries) bằng tiếng Việt để hỗ trợ tìm kiếm ngữ nghĩa tốt hơn.

Trả về kết quả dưới dạng định dạng JSON duy nhất với cấu trúc:
{{
    "ticker": "TÊN_MÃ_CỔ_PHIẾU" hoặc null,
    "year": "NĂM" hoặc null,
    "rewritten_queries": ["câu 1", "câu 2", "câu 3"]
}}

Câu hỏi của người dùng: {query}
JSON Output:""",
            input_variables=["query"]
        )
        try:
            chain = prompt | self.llm
            response = chain.invoke({"query": query}).content.strip()
            
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Error in QueryRewriter invoke: {e}. Falling back to default.")
            return {
                "ticker": None,
                "year": None,
                "rewritten_queries": [query]
            }