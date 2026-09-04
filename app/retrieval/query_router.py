from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.config import settings

class QueryRouter:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0, 
            model_name="openai/gpt-oss-120b", 
            groq_api_key=settings.GROQ_API_KEY
        )
        
    def route(self, query: str) -> str:
        prompt = PromptTemplate(
            template="""Bạn là trợ lý phân loại câu hỏi cho hệ thống RAG tài chính.
Hãy phân loại câu hỏi sau đây vào đúng 1 trong 4 nhóm:
1. 'chitchat': Nếu là câu chào hỏi, xã giao, hoặc câu hỏi chung không liên quan đến dữ liệu tài chính (ví dụ: 'Chào bạn', 'Bạn tên gì?').
2. 'financial_search': Nếu câu hỏi yêu cầu tra cứu SỐ LIỆU THÔ có sẵn trong báo cáo (doanh thu, lợi nhuận, tổng tài sản, vốn điều lệ...),
bất kỳ câu hỏi nào truy vấn dữ liệu, số liệu, trách nhiệm, báo cáo của MỘT hoặc NHIỀU công ty cụ thể, CÓ hoặc KHÔNG có năm/quý, kể cả câu hỏi
SO SÁNH nhiều công ty hoặc nhiều năm/quý (ví dụ "Doanh thu FPT năm 2024", "So sánh Tổng tài sản của BIDV và ACB năm 2025",
"Lợi nhuận VNM năm 2023 so với 2024") -- miễn là KHÔNG cần tính ra 1 chỉ số phái sinh mới (xem nhóm 4) thì vẫn thuộc financial_search.
3. 'term_definition': hỏi về Ý NGHĨA/GIẢI THÍCH khái niệm của một thuật ngữ, từ viết tắt, khái niệm tài chính chung (ví dụ 'LNST là gì', 'ROE nghĩa là gì',
   'EPS được tính như thế nào') -- KHÔNG hỏi số liệu cụ thể của công ty nào.
4. 'calculation': yêu cầu TÍNH TOÁN một hoặc NHIỀU chỉ số PHÁI SINH từ số liệu thô (ví dụ: 'Tính ROE của FPT năm 2024',
   'Biên lợi nhuận gộp của HPG quý 2/2024', 'Tăng trưởng doanh thu YoY của MWG', 'Debt-to-Equity của VNM năm 2023',
   'Tính cả ROE và ROA của FPT năm 2024').
   Từ khoá gợi ý (không bắt buộc phải xuất hiện): 'tính', 'tỷ suất', 'biên lợi nhuận', 'hệ số', 'tăng trưởng', ROE, ROA, Gross Margin,
   Net Margin, Current Ratio, Debt-to-Equity, YoY, QoQ, CAGR.

   QUAN TRỌNG -- người dùng có thể KHÔNG gọi tên chỉ số trực tiếp mà chỉ mô tả GIÁN TIẾP Ý NGHĨA của chỉ số đó; những câu như vậy
   VẪN thuộc nhóm 'calculation' (hãy suy luận theo ngữ nghĩa, không chỉ khớp từ khoá). Một vài ví dụ mô tả gián tiếp:
     - "Khả năng trả nợ ngắn hạn của X có tốt không?", "X có đủ tài sản ngắn hạn để trả nợ không?" -> vẫn là 'calculation' (current ratio).
     - "X có đang dùng nhiều nợ vay để tài trợ hoạt động không?", "mức độ đòn bẩy tài chính của X" -> 'calculation' (debt-to-equity).
     - "Mỗi đồng vốn cổ đông bỏ ra thì X sinh lời bao nhiêu?", "hiệu quả sinh lời trên vốn chủ sở hữu của X" -> 'calculation' (ROE).
     - "X sử dụng tài sản hiệu quả đến đâu để tạo ra lợi nhuận?" -> 'calculation' (ROA).
     - "Lợi nhuận của X có tăng trưởng tốt so với cùng kỳ năm ngoái không?" -> 'calculation' (tăng trưởng YoY).
   Ngược lại, nếu câu hỏi chỉ cần TRA CỨU một con số có sẵn (không cần chia/nhân/so sánh tỷ lệ) thì vẫn là 'financial_search'.

Chỉ trả về đúng 1 từ: 'chitchat', 'financial_search', 'term_definition', hoặc 'calculation'.

Câu hỏi: {query}
Phân loại:""",
            input_variables=["query"]
        )
        chain = prompt | self.llm
        response = chain.invoke({"query": query}).content.strip().lower()
        if "term_definition" in response or "definition" in response:
            return "term_definition"
        if "chitchat" in response:
            return "chitchat"
        if "calculation" in response:
            return "calculation"
        return "financial_search"