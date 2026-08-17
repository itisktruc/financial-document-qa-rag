import json
from typing import Dict, List, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.config import settings

class QueryRewriter:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1, 
            model_name="llama-3.3-70b-versatile", 
            groq_api_key=settings.GROQ_API_KEY
        )

    def rewrite_and_extract_metadata(self, query: str) -> Dict[str, Any]:
        """Viết lại câu hỏi thành các dạng tìm kiếm khác nhau và trích xuất bộ lọc Metadata."""
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
        chain = prompt | self.llm
        response = chain.invoke({"query": query}).content.strip()
        
        try:
            # Tìm chuỗi JSON trong phản hồi của LLM
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            json_str = response[start_idx:end_idx]
            return json.loads(json_str)
        except Exception:
            return {
                "ticker": None,
                "year": None,
                "rewritten_queries": [query]
            }