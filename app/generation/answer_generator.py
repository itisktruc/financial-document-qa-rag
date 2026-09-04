from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.retrieval.glossary import FINANCIAL_GLOSSARY
from app.generation.citation import format_citation_label, citations_filter
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
- Mỗi đoạn ngữ cảnh dưới đây đã được đánh số [1], [2], ... kèm theo nguồn (VÀ kèm theo tên công ty/năm nếu có). Khi dùng thông tin từ đoạn nào,
hãy CHÈN đúng ký hiệu [n] tương ứng ngay sau câu/số liệu đó (ví dụ: "Doanh thu thuần đạt 10.000 tỷ đồng [1].").
- Nếu 1 câu dùng thông tin từ nhiều nguồn, ghi liền các ký hiệu (ví dụ "[1][2]").
- NẾU câu hỏi yêu cầu SO SÁNH/TỔNG HỢP nhiều công ty: PHẢI trình bày rõ số liệu của TỪNG công ty riêng biệt
(vd dùng bảng, hoặc từng đoạn/bullet riêng cho mỗi công ty) trước khi đưa ra nhận xét so sánh -- không được
gộp lẫn số liệu của các công ty khác nhau vào chung 1 câu mơ hồ không rõ của công ty nào.
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

    @staticmethod
    def _entity_header(citation: Dict[str, Any]) -> str:
        """Nhãn ngắn 'Công ty: X, Năm: Y' gắn ngay dưới label nguồn của mỗi
        đoạn ngữ cảnh -- giúp LLM (và người đọc log) phân biệt RÕ đoạn nào
        thuộc công ty/năm nào, đặc biệt quan trọng với câu hỏi so sánh
        nhiều công ty (retrieve() gắn "matched_entity" cho từng context
        trong trường hợp đó, xem app/retrieval/hybrid_search.py). Với câu
        hỏi 1 công ty vẫn hiển thị được nếu citation có sẵn ticker/year."""
        entity = citation.get("matched_entity") or {}
        ticker = entity.get("ticker") or citation.get("ticker")
        year = entity.get("year") or citation.get("year")
        if not ticker and not year:
            return ""
        parts = []
        if ticker:
            parts.append(f"Công ty: {ticker}")
        if year:
            parts.append(f"Năm: {year}")
        return " (" + ", ".join(parts) + ")"

    def generate(self, user_query: str, retrieved_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Nếu Qdrant và MongoDB không tìm thấy bất kỳ tài liệu nào
        if not retrieved_contexts:
            return {
                "answer": "Hệ thống chưa có báo cáo tài chính khớp với bộ lọc (Công ty/Năm) hoặc nội dung bạn tìm kiếm.",
                "citations": [],
            }
        print(f"[Generation] Đang tổng hợp câu trả lời từ {len(retrieved_contexts)} đoạn ngữ cảnh (GPT-4o-mini)")
            
        # Gộp tất cả các Parent Document lại thành một chuỗi lớn
        numbered_blocks: List[str] = []
        citations: List[Dict[str, Any]] = []
        for i, ctx in enumerate(retrieved_contexts, start=1):
            citation = dict(ctx.get("citation", {}))
            label = format_citation_label(citation, i)
            entity_header = self._entity_header(citation)
            numbered_blocks.append(f"{label}{entity_header}\n{ctx['content']}")
            citation["index"] = i
            citation["label"] = label
            citations.append(citation)
 
        joined_context = "\n\n".join(numbered_blocks)
 
        # Gửi Context (đã đánh số) và Query cho GPT-4o-mini
        response = self.chain.invoke({
            "context": joined_context,
            "query": user_query,
        })

        used_citations = citations_filter(citations, response.content)
        print(f"[Generation] Sinh câu trả lời xong ({len(response.content)} ký tự), "
              f"{len(used_citations)}/{len(citations)} citation được giữ lại.")
        return {"answer": response.content, "citations": used_citations}

    def generate_definition(self, user_query: str) -> Dict[str, Any]:
        hint = next(
            (f"{abbr}: {full}" for abbr, full in FINANCIAL_GLOSSARY.items() if abbr.lower() in user_query.lower()),
            None,
        )
        print(f"[Generation] Câu hỏi định nghĩa: {user_query!r} về glossary: {hint}")
        prompt = f"""Bạn là chuyên gia tài chính. Hãy giải thích ngắn gọn, dễ hiểu khái niệm và từ viết tắt của các thuật ngữ tài chính
        {f"Gợi ý: {hint}" if hint else ""}
        Câu hỏi: {user_query}
        (Lưu ý cho người dùng: đây là kiến thức tài chính phổ thông, không phải trích từ tài liệu đã tải lên.)"""
        response = self.llm.invoke(prompt)
        return {"answer": response.content, "citations": []}