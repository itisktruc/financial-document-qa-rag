from FlagEmbedding import FlagReranker
from app.config import settings

class DocumentReranker:
    def __init__(self):
        # Load mô hình Reranker BGE M3 chạy local
        self.reranker = FlagReranker(settings.RERANKER_MODEL_NAME, use_fp16=True)

    def rerank(self, query: str, documents: List[str], top_k: int = 3) -> List[str]:
        if not documents:
            return []
            
        # Tạo cặp (Query, Document) để chấm điểm tương quan
        pairs = [[query, doc] for doc in documents]
        scores = self.reranker.compute_score(pairs)
        
        # Sắp xếp danh sách document theo điểm số giảm dần
        doc_score_pairs = list(zip(documents, scores))
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Lấy top K văn bản có điểm cao nhất
        return [doc for doc, score in doc_score_pairs[:top_k]]