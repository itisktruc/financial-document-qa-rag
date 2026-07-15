"""
FastAPI entrypoint cho Financial RAG Chatbot backend.
Hiện tại chỉ có skeleton + health check, sẽ bổ sung dần các route
theo pipeline: ingest -> retrieve -> calculate -> generate.
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Financial RAG Chatbot API",
    version="0.1.0",
)


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
    return ChatResponse(
        answer=f"[Chưa triển khai RAG pipeline] Bạn hỏi: {request.query}",
        citations=[],
    )