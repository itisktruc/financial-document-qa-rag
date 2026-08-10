import logging
from typing import List

from FlagEmbedding import FlagReranker

from app.config import settings

logger = logging.getLogger(__name__)


class DocumentReranker:
    # Tái xếp hạng danh sách văn bản bằng mô hình Cross-Encoder

    def __init__(self, model_name: str | None = None) -> None:
        target_model = model_name or settings.RERANKER_MODEL_NAME
        try:
            self.reranker = FlagReranker(target_model, use_fp16=True)
        except Exception as err:
            logger.error(f"Lỗi load model Reranker {target_model}: {err}")
            self.reranker = None

    def rerank(self, query: str, documents: List[str], top_k: int = 3) -> List[str]:
        """Tính điểm tương quan và lấy ra top_k văn bản phù hợp nhất."""
        if not documents:
            return []
            
        if not self.reranker:
            return documents[:top_k]

        try:
            pairs = [[query, doc] for doc in documents]
            scores = self.reranker.compute_score(pairs)
            
            if isinstance(scores, (float, int)):
                scores = [scores]

            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            return [doc for doc, _ in doc_score_pairs[:top_k]]
        except Exception as err:
            logger.error(f"Lỗi khi thực hiện Rerank: {err}")
            return documents[:top_k]