from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.retrieval.glossary import FINANCIAL_GLOSSARY
from app.generation.citation import format_citation_label, format_citations_footer
from typing import List, Dict, Any

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
- Mỗi đoạn ngữ cảnh dưới đây đã được đánh số [1], [2], ... kèm theo nguồn. Khi dùng thông tin từ đoạn nào, 
hãy CHÈN đúng ký hiệu [n] tương ứng ngay sau câu/số liệu đó (ví dụ: "Doanh thu thuần đạt 10.000 tỷ đồng [1].").
- Nếu 1 câu dùng thông tin từ nhiều nguồn, ghi liền các ký hiệu (ví dụ "[1][2]").
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

    def generate(self, user_query: str, retrieved_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Nếu Qdrant và MongoDB không tìm thấy bất kỳ tài liệu nào
        if not retrieved_contexts:
            return {
                "answer": "Hệ thống chưa có báo cáo tài chính khớp với bộ lọc (Công ty/Năm) hoặc nội dung bạn tìm kiếm.",
                "citations": [],
            }
            
        # Gộp tất cả các Parent Document lại thành một chuỗi lớn
        numbered_blocks: List[str] = []
        citations: List[Dict[str, Any]] = []
        for i, ctx in enumerate(retrieved_contexts, start=1):
            citation = dict(ctx.get("citation", {}))
            label = format_citation_label(citation, i)
            numbered_blocks.append(f"{label}\n{ctx['content']}")
            citation["index"] = i
            citation["label"] = label
            citations.append(citation)
 
        joined_context = "\n\n".join(numbered_blocks)
        print("="*50)
        print("[DEBUG CONTEXT SENT TO GPT]:")
        print(joined_context[:1000]) # In 1000 ký tự đầu tiên
        print("="*50)
 
        # Gửi Context (đã đánh số) và Query cho GPT-4o-mini
        response = self.chain.invoke({
            "context": joined_context,
            "query": user_query,
        })

        footer = format_citations_footer(citations)
        final_answer = response.content + footer
        
        return {"answer": final_answer, "citations": citations}

    def generate_definition(self, user_query: str) -> Dict[str, Any]:
        hint = next(
            (f"{abbr}: {full}" for abbr, full in FINANCIAL_GLOSSARY.items() if abbr.lower() in user_query.lower()),
            None,
        )
        prompt = f"""Bạn là chuyên gia tài chính. Hãy giải thích ngắn gọn, dễ hiểu khái niệm và từ viết tắt của các thuật ngữ tài chính
        {f"Gợi ý: {hint}" if hint else ""}
        Câu hỏi: {user_query}
        (Lưu ý cho người dùng: đây là kiến thức tài chính phổ thông, không phải trích từ tài liệu đã tải lên.)"""
        response = self.llm.invoke(prompt)
        return {"answer": response.content, "citations": []}

   