from typing import List
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentReranker:
    def __init__(self):
        self.reranker = None
        try:
            import torch
            from sentence_transformers import CrossEncoder
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Reranker model '{settings.RERANKER_MODEL_NAME}' on {device}...")
            self.reranker = CrossEncoder(
                settings.RERANKER_MODEL_NAME,
                max_length=512,
                device=device,
            )
            if device == "cuda":
                self.reranker.model.half()
        except Exception as e:
            logger.warning(f"Could not initialize CrossEncoder reranker ({e}). Using length & keyword fallback reranker.")
            self.reranker = None

    def rerank(self, query: str, documents: List[str], top_k: int = 3) -> List[int]:
        """Trả về danh sách các chỉ số (indices) của documents theo thứ tự giảm dần tương quan."""
        if not documents:
            return []

        if self.reranker is not None:
            try:
                pairs = [[query, doc] for doc in documents]
                scores = self.reranker.predict(pairs, batch_size=len(pairs), show_progress_bar=False)
                ranked = sorted(range(len(documents)), key=lambda i: scores[i], reverse=True)
                return ranked[:top_k]
            except Exception as e:
                logger.error(f"Error during CrossEncoder predict: {e}")

        # Fallback scoring: count term overlap between query and doc
        query_words = set(query.lower().split())
        scores = []
        for doc in documents:
            doc_words = set(doc.lower().split())
            overlap = len(query_words.intersection(doc_words))
            scores.append(overlap)

        ranked = sorted(range(len(documents)), key=lambda i: scores[i], reverse=True)
        return ranked[:top_k]
