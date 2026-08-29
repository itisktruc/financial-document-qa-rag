"""
FastAPI entrypoint for Financial RAG Chatbot backend.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from app.routers import documents
from app.retrieval.hybrid_search import HybridSearchPipeline
from app.retrieval.rag_pipeline import RAGController
from app.generation.answer_generator import AnswerGenerator
from app.calculation.calculation_service import CalculationService
from app.services.chat_history import get_history, append_message

logger = logging.getLogger("rag_backend")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

from dotenv import load_dotenv

load_dotenv()
class Container:
    search_pipeline: HybridSearchPipeline
    rag_controller: RAGController
    answer_generator: AnswerGenerator
    calculation_service: CalculationService


services = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RAG Pipeline components...")
    services.search_pipeline = HybridSearchPipeline()
    services.rag_controller = RAGController(pipeline=services.search_pipeline, top_k=10)
    services.answer_generator = AnswerGenerator()
    services.calculation_service = CalculationService(search_pipeline=services.search_pipeline)

    logger.info("Warming up models (BAAI/bge-m3 + reranker)...")
    try:
        # 1. Force load embedding model
        from app.services.embedding_client import embed_query
        embed_query("warmup embedding", return_sparse=False)
        logger.info("Embedding model loaded.")

        # 2. Force load reranker
        if hasattr(services.search_pipeline, "reranker"):
            services.search_pipeline.reranker.rerank(
                "warmup query",
                ["Đây là đoạn văn bản thử nghiệm để load reranker."],
                top_k=1,
            )
            logger.info("Reranker loaded.")

        # 3. Chạy 1 lượt retrieve thật (để warm BM25 cache nếu có)
        services.rag_controller.execute_search(
            "doanh thu công ty A32 năm 2024",  # query financial thật, tránh bị route chitchat
            history=[],
        )
        logger.info("Full retrieve warmup done.")
    except Exception as e:
        logger.error("Warmup FAILED: %s", e, exc_info=True)  # log rõ, đừng chỉ warning

    logger.info("RAG Pipeline initialization completed successfully.")
    yield


app = FastAPI(
    title="Financial RAG Chatbot API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(documents.router)


class ChatRequest(BaseModel):
    session_id: str
    query: str


class ChatResponse(BaseModel):
    answer: str
    citations: list = []
    intent: Optional[dict] = None
    metric_spec: Optional[dict] = None
    calculation: Optional[dict] = None


CHITCHAT_REPLY = (
    "Đây có vẻ là câu hỏi giao tiếp thông thường. "
    "Mình là trợ lý AI phân tích tài chính doanh nghiệp. "
    "Bạn hãy hỏi mình các câu liên quan đến số liệu, báo cáo tài chính nhé!"
)

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    raw_query = request.query
    session_id = request.session_id
    history = get_history(session_id, limit=4)
    logger.info("[%s] Incoming query: %r", session_id, raw_query)

    try:
        search_result = services.rag_controller.execute_search(raw_query, history=history)

        # ---------- CHITCHAT ----------
        if search_result.get("is_chitchat", False):
            answer = CHITCHAT_REPLY
            append_message(session_id, "user", raw_query)
            append_message(session_id, "assistant", answer)
            return ChatResponse(answer=answer, citations=[])

        # ---------- DEFINITION ----------
        if search_result.get("is_definition", False):
            definition_answer = services.answer_generator.generate_definition(raw_query)
            answer = definition_answer["answer"]
            append_message(session_id, "user", raw_query)
            append_message(session_id, "assistant", answer)
            return ChatResponse(
                answer=answer,
                citations=definition_answer.get("citations", []),
            )

        # ---------- CALCULATION ----------
        if search_result.get("is_calculation", False):
            logger.info("[%s] Intent: CALCULATION", session_id)
            calc_result = services.calculation_service.calculate(raw_query)
            answer = calc_result.answer
            append_message(session_id, "user", raw_query)
            append_message(session_id, "assistant", answer)
            return ChatResponse(
                answer=answer,
                citations=calc_result.citations,
                intent=calc_result.intent,
                metric_spec=calc_result.metric_spec,
                calculation=(
                    calc_result.calculation.model_dump()
                    if calc_result.calculation
                    else None
                ),
            )

        # ---------- FINANCIAL SEARCH ----------
        logger.info("[%s] Intent: FINANCIAL_SEARCH", session_id)
        contexts = search_result.get("context", [])
        logger.info("[%s] Retrieved %d context items", session_id, len(contexts))

        final_answer = services.answer_generator.generate(raw_query, contexts)
        answer = final_answer["answer"]
        append_message(session_id, "user", raw_query)
        append_message(session_id, "assistant", answer)
        return ChatResponse(
            answer=answer,
            citations=final_answer.get("citations", []),
        )

    except Exception as e:
        logger.error("[%s] Query processing failed: %s", session_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)