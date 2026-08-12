"""
FastAPI entrypoint cho Financial RAG Chatbot backend.
Hiện tại chỉ có skeleton + health check, sẽ bổ sung dần các route
theo pipeline: ingest -> retrieve -> calculate -> generate.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.routers import documents
from app.retrieval.hybrid_search import HybridSearchPipeline
from app.services.embedding_client import embed_query
from app.retrieval.rag_pipeline import RAGController
from app.generation.answer_generator import AnswerGenerator
from app.config import settings
from qdrant_client import QdrantClient, models
from pymongo import MongoClient
from FlagEmbedding import FlagModel
import uvicorn
import traceback

app = FastAPI(
    title="Financial RAG Chatbot API",
    version="0.1.0",
)

app.include_router(documents.router)
search_pipeline = None      # thêm lại biến này
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
    Placeholder endpoint cho main RAG pipeline.
    TODO: query contextualization -> route -> retrieve -> rerank
          -> (calculate nếu cần) -> generate -> citation
    """
    global rag_controller, answer_generator, search_pipeline

    if search_pipeline is None:
        search_pipeline = HybridSearchPipeline()
    
    # LAZY LOADING: Chỉ khởi tạo khi có request đầu tiên tới endpoint /chat
    if rag_controller is None or answer_generator is None:
        print("[*] Đang khởi tạo toàn bộ hệ thống RAG (Qdrant, MongoDB, Embedding, Reranker, GPT-4o-mini)")
        
        # 1. Kết nối Qdrant Client
        qdrant_client = QdrantClient(
            url=getattr(settings, "QDRANT_URL", "http://qdrant:6333"),
            api_key=getattr(settings, "QDRANT_API_KEY", None),
            timeout=30,
        )
        qdrant_client.update_collection_aliases(
            change_aliases_operations=[
            models.CreateAliasOperation(
                create_alias=models.CreateAlias(
                    collection_name="fpt_bctc_blocks",
                    alias_name="financial_rag",
                    )
                )
            ]
        )
        # 2. Kết nối MongoDB Client
        mongo_client = MongoClient(getattr(settings, "MONGO_URI", "mongodb://mongo:27017"))
        mongo_db = mongo_client[getattr(settings, "MONGO_DB_NAME", "financial_rag_db")]
        # 3. Khởi tạo Embedding Model (Dùng chung model BGE-M3 với quá trình Ingestion)
        print("[*] Đang load Embedding Model")
        embedding_model = FlagModel(
            getattr(settings, "EMBEDDING_MODEL_NAME", "BAAI/bge-m3"), 
            use_fp16=True
        )
        # 4. Khởi tạo RAGController (Quản lý nửa đầu: Router, Rewriter, Qdrant, Rerank, MongoDB)
        rag_controller = RAGController(
            qdrant_client=qdrant_client,
            mongo_db=mongo_db,
            pipeline=search_pipeline,
        )
        # 5. Khởi tạo AnswerGenerator (Quản lý nửa sau: GPT-4o-mini Generation)
        answer_generator = AnswerGenerator()
        print("Khởi tạo thành công toàn bộ RAG Pipeline!")

    raw_query = request.query
    session_id = request.session_id

    print(f"\n{'='*50}")
    print(f"[{session_id}] NHẬN CÂU HỎI MỚI: '{raw_query}'")

    try:
        # ==========================================
        # BƯỚC 1: XỬ LÝ QUERY (ROUTING & REWRITING)
        # ==========================================
        print("Đang thực thi Hybrid Search & Rerank Pipeline")
        search_result = rag_controller.execute_search(raw_query)
        
        # Xử lý trường hợp CHITCHAT (Câu hỏi giao tiếp thông thường)
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
        traceback.print_exc()   # đã import sẵn ở đầu file rồi
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)