from sentence_transformers import CrossEncoder
from app.config import settings
from typing import List
import torch

class DocumentReranker:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reranker = CrossEncoder(
            settings.RERANKER_MODEL_NAME,
            max_length=512,
            device=device,
        )
        if device == "cuda":
            self.reranker.model.half() 

    def rerank(self, query: str, documents: List[str], top_k: int = 3) -> List[str]:
        if not documents:
            return []
            
        # Tạo cặp (Query, Document) để chấm điểm tương quan
        pairs = [[query, doc] for doc in documents]
        scores = self.reranker.predict(pairs, batch_size=len(pairs), show_progress_bar=False)
        #scores = self.reranker.compute_score(pairs)
        
        # Sắp xếp danh sách document theo điểm số giảm dần
        ranked = sorted(range(len(documents)), key=lambda i: scores[i], reverse=True)
        
        # Lấy top K văn bản có điểm cao nhất
        return ranked[:top_k]
