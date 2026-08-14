"""
FastAPI entrypoint cho Financial RAG Chatbot backend.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.routers import documents
from app.retrieval.hybrid_search import HybridSearchPipeline
from app.retrieval.rag_pipeline import RAGController
from app.generation.answer_generator import AnswerGenerator
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


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint chính: query -> Hybrid Search (BM25 + Dense + RRF + Rerank,
    xem app/retrieval/hybrid_search.py) -> generation.
    """
    global rag_controller, answer_generator, search_pipeline

    # LAZY LOADING: chỉ khởi tạo khi có request đầu tiên tới /chat.
    #
    # QUAN TRỌNG (khác bản cũ): KHÔNG còn tự tạo QdrantClient/MongoClient
    # riêng ở đây nữa. HybridSearchPipeline tự lo toàn bộ kết nối bên trong
    # nó (Qdrant qua app.services.qdrant_store, MongoDB qua
    # app.services.mongo_client, embedding qua app.services.embedding_client).
    #
    # Bản cũ tạo 1 QdrantClient riêng trong main.py rồi set alias
    # "financial_rag" -> "fpt_bctc_blocks" để rag_pipeline.py query theo tên
    # alias đó -- trong khi qdrant_store.py (dùng cho cả bước ingestion lẫn
    # bước dense-search mới trong hybrid_search.py) lại trỏ thẳng vào
    # QDRANT_COLLECTION (biến môi trường, mặc định "fpt_bctc_blocks") của
    # RIÊNG NÓ. Hai client trỏ 2 "tên" khác nhau cho cùng 1 collection là
    # nguồn dễ gây lệch dữ liệu nếu sau này đổi 1 bên mà quên đổi bên kia.
    # Giờ mọi thứ đi qua đúng 1 client Qdrant / 1 client Mongo duy nhất
    # (định nghĩa trong qdrant_store.py / mongo_client.py), không cần alias.
    if search_pipeline is None:
        print("[*] Đang khởi tạo HybridSearchPipeline (Router, Rewriter, BM25, Dense, RRF, Rerank)")
        search_pipeline = HybridSearchPipeline()

    if rag_controller is None:
        rag_controller = RAGController(pipeline=search_pipeline, top_k=10)

    if answer_generator is None:
        print("[*] Đang khởi tạo AnswerGenerator (GPT-4o-mini)")
        answer_generator = AnswerGenerator()
        print("Khởi tạo thành công toàn bộ RAG Pipeline!")

    raw_query = request.query
    session_id = request.session_id

    print(f"\n{'='*50}")
    print(f"[{session_id}] NHẬN CÂU HỎI MỚI: '{raw_query}'")

    try:
        # ==========================================
        # NỬA ĐẦU: HYBRID SEARCH (BM25 + Dense + RRF + Rerank + Parent-expansion)
        # ==========================================
        print("Đang thực thi Hybrid Search & Rerank Pipeline")
        search_result = rag_controller.execute_search(raw_query)

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
                answer=definition_answer,
                citations=[]
            )

        #Nhánh 3: Nhánh Finance Search
        # Lấy danh sách ngữ cảnh (Parent Documents từ MongoDB đã qua Rerank)
        contexts = search_result.get("context", [])
        print(f"Truy xuất thành công {len(contexts)} đoạn văn bản ngữ cảnh liên quan.")
        # ==========================================
        # NỬA SAU: SINH CÂU TRẢ LỜI (GENERATION)
        # ==========================================
        print("Đang gửi ngữ cảnh và câu hỏi cho GPT-4o-mini")
        final_answer = answer_generator.generate(raw_query, contexts)
        print("Sinh câu trả lời hoàn tất!")

        return ChatResponse(
            answer=final_answer,
            citations=[],
        )
    
    except Exception as e:
        print(f"[-] Lỗi tại bước Query: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)