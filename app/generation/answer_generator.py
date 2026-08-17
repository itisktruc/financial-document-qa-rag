from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.retrieval.glossary import FINANCIAL_GLOSSARY
from typing import List

class AnswerGenerator:
    def __init__(self):
        # Khởi tạo mô hình GPT-4o-mini chuyên đảm nhận phần Generation
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.1, # Giữ mức thấp để AI bám sát số liệu tài chính
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Xây dựng Prompt rào chắn (Guardrails) nghiêm ngặt
        self.prompt = PromptTemplate(
            template="""Bạn là chuyên gia tư vấn tài chính doanh nghiệp.
Dựa vào CÁC THÔNG TIN NGỮ CẢNH ĐƯỢC CUNG CẤP TRÍCH XUẤT TỪ BÁO CÁO TÀI CHÍNH sau đây, hãy trả lời câu hỏi của người dùng.
- Hãy tổng hợp số liệu một cách rõ ràng, có thể dùng bullet point hoặc bảng nếu cần thiết.
- Tuyệt đối KHÔNG tự sáng tạo, KHÔNG lấy thông tin ngoài ngữ cảnh.
- Nếu ngữ cảnh không chứa thông tin để trả lời, hãy nói: "Dữ liệu hiện tại trong hệ thống không đủ để trả lời câu hỏi này."

--- NGỮ CẢNH (CONTEXT) ---
{context}

---
Câu hỏi của người dùng: {query}
Câu trả lời của bạn:""",
            input_variables=["context", "query"]
        )
        self.chain = self.prompt | self.llm

    def generate(self, user_query: str, retrieved_contexts: List[str]) -> str:
        # Nếu Qdrant và MongoDB không tìm thấy bất kỳ tài liệu nào
        if not retrieved_contexts:
            return "Hệ thống chưa có báo cáo tài chính khớp với bộ lọc (Công ty/Năm) hoặc nội dung bạn tìm kiếm."
            
        # Gộp tất cả các Parent Document lại thành một chuỗi lớn
        joined_context = "\n\n".join(retrieved_contexts)
        
        # Gửi Context và Query cho GPT-4o-mini
        response = self.chain.invoke({
            "context": joined_context, 
            "query": user_query
        })
        
        return response.content

    def generate_definition(self, user_query: str) -> str:
        hint = next(
            (f"{abbr}: {full}" for abbr, full in FINANCIAL_GLOSSARY.items() if abbr.lower() in user_query.lower()),
            None,
        )
        prompt = f"""Bạn là chuyên gia tài chính. Hãy giải thích ngắn gọn, dễ hiểu khái niệm và từ viết tắt của các thuật ngữ tài chính
        {f"Gợi ý: {hint}" if hint else ""}
        Câu hỏi: {user_query}
        (Lưu ý cho người dùng: đây là kiến thức tài chính phổ thông, không phải trích từ tài liệu đã tải lên.)"""
        return self.llm.invoke(prompt).content