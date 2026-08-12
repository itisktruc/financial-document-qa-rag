from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
# Import RAGPipeline đã khởi tạo ở file dependency của bạn
# from app.dependencies import get_rag_pipeline 

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    # Khởi tạo hoặc lấy instance RAGPipeline
    # rag = get_rag_pipeline()
    
    # Hàm generator để stream
    def event_stream():
        for chunk in rag.generate_response(request.query):
            yield chunk
            
    return StreamingResponse(event_stream(), media_type="text/plain")