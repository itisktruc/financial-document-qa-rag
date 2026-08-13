from sentence_transformers import CrossEncoder
from app.config import settings
from typing import List
import torch

class DocumentReranker:
    #def __init__(self):
        # Load mô hình Reranker BGE M3 chạy local
    #    self.reranker = FlagReranker(settings.RERANKER_MODEL_NAME, use_fp16=True)

    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reranker = CrossEncoder(
            settings.RERANKER_MODEL_NAME,   # đổi thành "BAAI/bge-reranker-v2-m3" trong config.py
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
        #doc_score_pairs = list(zip(documents, scores))
        #doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
        ranked = sorted(range(len(documents)), key=lambda i: scores[i], reverse=True)
        
        # Lấy top K văn bản có điểm cao nhất
        #return [doc for doc, score in doc_score_pairs[:top_k]]
        return ranked[:top_k]   # trả về list index
