"""
FastAPI entrypoint cho Financial RAG Chatbot backend.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.routers import documents
from typing import Optional
from app.retrieval.hybrid_search import HybridSearchPipeline
from app.retrieval.rag_pipeline import RAGController
from app.generation.answer_generator import AnswerGenerator
from app.calculation.calculation_service import CalculationService

import uvicorn
import traceback

app = FastAPI(
    title="Financial RAG Chatbot API",
    version="0.1.0",
)

app.include_router(documents.router)
search_pipeline = None
rag_controller = None
answer_generator = None
calculation_service = None      


@app.get("/health")
def health_check():
    """Dùng để kiểm tra container backend đã start thành công."""
    return {"status": "ok"}


class ChatRequest(BaseModel):
    session_id: str
    query: str


class ChatResponse(BaseModel):
    answer: str
    citations: list = []
    intent: Optional[dict] = None
    metric_spec: Optional[dict] = None
    calculation: Optional[dict] = None


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint chính: query -> Hybrid Search (BM25 + Dense + RRF + Rerank,
    xem app/retrieval/hybrid_search.py) -> generation.
    """
    global rag_controller, answer_generator, search_pipeline, calculation_service

    if search_pipeline is None:
        print("[*] Đang khởi tạo HybridSearchPipeline (Router, Rewriter, BM25, Dense, RRF, Rerank)")
        search_pipeline = HybridSearchPipeline()

    if rag_controller is None:
        rag_controller = RAGController(pipeline=search_pipeline, top_k=10)

    if answer_generator is None:
        print("[*] Đang khởi tạo AnswerGenerator (GPT-4o-mini)")
        answer_generator = AnswerGenerator()
        print("Khởi tạo thành công toàn bộ RAG Pipeline!")

    if calculation_service is None:                                   
        print("[*] Đang khởi tạo CalculationService (Financial Calculator)")
        calculation_service = CalculationService(search_pipeline=search_pipeline)

    raw_query = request.query
    session_id = request.session_id

    print(f"\n{'='*50}")
    print(f"[{session_id}] NHẬN CÂU HỎI MỚI: '{raw_query}'")

    try:
        # ==========================================
        # NỬA ĐẦU: HYBRID SEARCH (BM25 + Dense + RRF + Rerank + Parent-expansion)
        # ==========================================
        print("Đang bắt đầu thực thi Hybrid Search & Rerank Pipeline")
        search_result = rag_controller.execute_search(raw_query, session_id=session_id)

        # Nhánh 1: CHITCHAT (Câu hỏi giao tiếp thông thường)
        if search_result.get("is_chitchat", False):
            print("Phân loại: CHITCHAT")
            chitchat_answer = (
                "Đây có vẻ là câu hỏi giao tiếp thông thường. "
                "Mình là trợ lý AI phân tích tài chính doanh nghiệp. "
                "Bạn hãy hỏi mình các câu liên quan đến số liệu, báo cáo tài chính nhé!"
            )
            return ChatResponse(
                answer=chitchat_answer,
                citations=[]
            )

        #Nhánh 2: Nhánh Definition
        if search_result.get("is_definition", False):
            print("Phân loại: TERM_DEFINITION")
            definition_answer = answer_generator.generate_definition(raw_query)
            return ChatResponse(
                answer=definition_answer["answer"],
                citations=definition_answer["citations"]
            )

        #Nhánh 3: Calculation 
        if search_result.get("is_calculation", False):
            print("Phân loại: CALCULATION")
            calc_result = calculation_service.calculate(raw_query,  session_id=session_id)
            return ChatResponse(answer=calc_result.answer, citations=calc_result.citations,
                                intent=calc_result.intent,
                                metric_spec=calc_result.metric_spec,
                                calculation=calc_result.calculation.model_dump() if calc_result.calculation else None,)

        #Nhánh 4 (nhánh chính): Nhánh Finance Search
        print("Phân loại: Financial Search")
        # Lấy danh sách ngữ cảnh (Parent Documents từ MongoDB đã qua Rerank)
        contexts = search_result.get("context", [])
        print(f"Truy xuất thành công {len(contexts)} đoạn văn bản ngữ cảnh liên quan.")
        # ==========================================
        # NỬA SAU: SINH CÂU TRẢ LỜI (GENERATION)
        # ==========================================
        print("Đang gửi ngữ cảnh và câu hỏi cho GPT-4o-mini")
        final_answer = answer_generator.generate(raw_query, contexts)
        print(f"Sinh câu trả lời hoàn tất kèm {len(final_answer['citations'])} citation")

        return ChatResponse(
            answer=final_answer["answer"],
            citations=final_answer["citations"],
        )

    except Exception as e:
        print(f"[-] Lỗi tại bước Query: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)