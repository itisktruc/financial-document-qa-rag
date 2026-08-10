import json
import logging
from typing import Any, Dict, List

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.config import settings

logger = logging.getLogger(__name__)


class QueryRewriter:
    # Viết lại truy vấn và trích xuất thông tin metadata phục vụ tìm kiếm.

    def __init__(self, model_name: str = "llama-3.3-70b-versatile") -> None:
        self.llm = ChatGroq(
            temperature=0.1,
            model_name=model_name,
            groq_api_key=settings.GROQ_API_KEY,
        )
        self.prompt = PromptTemplate(
            template=(
                "Bạn là chuyên gia phân tích truy vấn tài chính.\n"
                "Nhiệm vụ của bạn:\n"
                "1. Trích xuất tên mã cổ phiếu/công ty (ticker - viết hoa, ví dụ: FPT, VNM) và năm (year) từ câu hỏi nếu có.\n"
                "2. Tạo 3 câu hỏi tương đương (rewritten_queries) bằng tiếng Việt giúp cải thiện ngữ nghĩa tìm kiếm.\n\n"
                "Trả về kết quả chuẩn định dạng JSON duy nhất:\n"
                "{{\n"
                '  "ticker": "TÊN_MÃ_CỔ_PHIẾU" hoặc null,\n'
                '  "year": "NĂM" hoặc null,\n'
                '  "rewritten_queries": ["câu 1", "câu 2", "câu 3"]\n'
                "}}\n\n"
                "Câu hỏi: {query}\n"
                "JSON Output:"
            ),
            input_variables=["query"],
        )
        self.chain = self.prompt | self.llm

    def rewrite_and_extract_metadata(self, query: str) -> Dict[str, Any]:
        """Tạo các truy vấn mở rộng và rút trích các bộ lọc Metadata."""
        fallback_res = {
            "ticker": None,
            "year": None,
            "rewritten_queries": [query],
        }

        if not query or not query.strip():
            return fallback_res

        try:
            response = self.chain.invoke({"query": query}).content.strip()
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx != -1 and end_idx != -1:
                return json.loads(response[start_idx:end_idx])
            return fallback_res
        except Exception as err:
            logger.error(f"Lỗi khi rewrite query: {err}")
            return fallback_res