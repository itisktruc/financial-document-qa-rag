"""
FastAPI entrypoint for Financial RAG Chatbot backend.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from app.routers import documents
from app.retrieval.hybrid_search import HybridSearchPipeline
from app.retrieval.rag_pipeline import RAGController
from app.generation.answer_generator import AnswerGenerator
from app.calculation.calculation_service import CalculationService

logger = logging.getLogger("rag_backend")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)


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
    citations: List[Dict[str, Any]] = Field(default_factory=list)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    raw_query = request.query
    session_id = request.session_id

    logger.info("[%s] Incoming query: '%s'", session_id, raw_query)

    try:
        search_result = services.rag_controller.execute_search(raw_query)

        # 1. Chitchat intent
        if search_result.get("is_chitchat", False):
            return ChatResponse(
                answer=(
                    "Đây có vẻ là câu hỏi giao tiếp thông thường. "
                    "Mình là trợ lý AI phân tích tài chính doanh nghiệp. "
                    "Bạn hãy hỏi mình các câu liên quan đến số liệu, báo cáo tài chính nhé!"
                ),
                citations=[],
            )

        # 2. Term Definition intent
        if search_result.get("is_definition", False):
            definition_answer = services.answer_generator.generate_definition(raw_query)
            return ChatResponse(
                answer=definition_answer["answer"],
                citations=definition_answer.get("citations", []),
            )

        # 3. Calculation intent
        if search_result.get("is_calculation", False):
            calc_result = services.calculation_service.calculate(raw_query)
            return ChatResponse(
                answer=calc_result.answer,
                citations=calc_result.citations,
            )

        # 4. Standard RAG Search intent
        contexts = search_result.get("context", [])
        logger.info("[%s] Retrieved %d context items", session_id, len(contexts))

        final_answer = services.answer_generator.generate(raw_query, contexts)
        return ChatResponse(
            answer=final_answer["answer"],
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