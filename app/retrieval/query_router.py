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
2. 'financial_search': Nếu câu hỏi yêu cầu tra cứu thông tin báo cáo tài chính, doanh thu, lợi nhuận, chỉ số công ty (ví dụ: 'Doanh thu FPT năm 2023'),
bất kỳ câu hỏi nào truy vấn dữ liệu, số liệu, trách nhiệm, báo cáo của MỘT CÔNG TY CỤ THỂ hoặc CÓ NĂM/QUÝ (Ví dụ: "Doanh thu FPT năm 2024", "Trách nhiệm Ban điều hành Công ty 32 năm 2025") thì cũng vào 
nhánh financial_search và cần truy vấn.
3. 'term_definition': hỏi về Ý NGHĨA/GIẢI THÍCH khái niệm của một thuật ngữ, từ viết tắt, khái niệm tài chính chung (ví dụ 'LNST là gì', 'ROE nghĩa là gì',
   'EPS được tính như thế nào') -- KHÔNG hỏi số liệu cụ thể của công ty nào.
4. 'calculation': yêu cầu TÍNH TOÁN 1 chỉ số PHÁI SINH từ số liệu thô (ví dụ: 'Tính ROE của FPT năm 2024',
   'Biên lợi nhuận gộp của HPG quý 2/2024', 'Tăng trưởng doanh thu YoY của MWG', 'Debt-to-Equity của VNM năm 2023').
   Từ khoá gợi ý: 'tính', 'tỷ suất', 'biên lợi nhuận', 'hệ số', 'tăng trưởng', ROE, ROA, Gross Margin,
   Net Margin, Current Ratio, Debt-to-Equity, YoY, QoQ, CAGR.

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