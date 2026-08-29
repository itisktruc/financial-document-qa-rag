import json
from typing import Any, Dict, List, Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.config import settings


class QueryRewriter:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1,
            model_name="openai/gpt-oss-120b",
            groq_api_key=settings.GROQ_API_KEY,
        )

    def rewrite_and_extract_metadata(
        self,
        query: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        history = history or []
        history_text = self._format_history(history)

        prompt = PromptTemplate(
            template="""Bạn là chuyên gia phân tích truy vấn tài chính.

Dựa vào LỊCH SỬ HỘI THOẠI (nếu có) và CÂU HỎI HIỆN TẠI:
1. Giải quyết tham chiếu ("nó", "công ty đó", "năm đó",...) bằng context.
2. Trích xuất ticker (viết hoa, VD: FPT, VNM, A32) và year — ưu tiên câu hiện tại, thiếu thì lấy từ lịch sử. Nếu trong câu hỏi có nhắc đến nhiều ticker hoặc năm thì phải tách ra thành các câu hỏi riêng biệt, mỗi câu hỏi chỉ có 1 ticker và 1 năm.
3. Tạo 3 câu hỏi độc lập, ĐẦY ĐỦ ngữ cảnh (không dùng đại từ mơ hồ), bằng tiếng Việt để search.

Trả về ĐÚNG 1 JSON:
{{
    "ticker": "MÃ" hoặc null,
    "year": "NĂM" hoặc null,
    "rewritten_queries": ["câu 1", "câu 2", "câu 3"]
}}

LỊCH SỬ HỘI THOẠI:
{history}

CÂU HỎI HIỆN TẠI: {query}
JSON Output:""",
            input_variables=["query", "history"],
        )
        chain = prompt | self.llm
        response = chain.invoke(
            {"query": query, "history": history_text}
        ).content.strip()

        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            return json.loads(response[start_idx:end_idx])
        except Exception:
            return {
                "ticker": None,
                "year": None,
                "rewritten_queries": [query],
            }

    @staticmethod
    def _format_history(history: List[Dict[str, Any]]) -> str:
        if not history:
            return "(không có lịch sử)"
        lines = []
        for m in history:
            role = m.get("role", "user")
            content = (m.get("content") or "").strip()
            if not content:
                continue
            label = "User" if role == "user" else "Assistant"
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"{label}: {content}")
        return "\n".join(lines) if lines else "(không có lịch sử)"