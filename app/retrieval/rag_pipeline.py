from qdrant_client import QdrantClient
from qdrant_client.http import models
# Import các class đã có
from app.retrieval.query_router import QueryRouter
from app.retrieval.query_rewriter import QueryRewriter
from app.retrieval.reranker import DocumentReranker
from app.retrieval.hybrid_search import HybridSearchPipeline
from app.services.embedding_client import embed_query


class RAGController:
    def __init__(self, qdrant_client, mongo_db, pipeline: HybridSearchPipeline):
        self.pipeline = pipeline
        self.reranker = pipeline.reranker
        self.qdrant = qdrant_client
        self.mongo = mongo_db                  # Kết nối MongoDB đã làm trước đó

    def execute_search(self, user_query: str):
        # 1. Chạy Pipeline tiền xử lý (Router & Rewriter)
        prep_result = self.pipeline.process_user_query(user_query)
        
        # Nếu chỉ là chitchat, trả thẳng cho LLM trả lời, bỏ qua Qdrant
        if prep_result["type"] == "chitchat":
            return {"context": [], "is_chitchat": True}

        # 2. Xây dựng bộ lọc Metadata cho Qdrant từ kết quả LLM trích xuất
        meta_filter = prep_result["metadata_filter"]
        must_conditions = []
        if meta_filter.get("ticker"):
            must_conditions.append(
                models.FieldCondition(key="ticker", match=models.MatchValue(value=meta_filter["ticker"]))
            )
        if meta_filter.get("year"):
            must_conditions.append(
                models.FieldCondition(key="year", match=models.MatchValue(value=int(meta_filter["year"])))
            )
        qdrant_filter = models.Filter(must=must_conditions) if must_conditions else None

        # 3. Vector Search trên Qdrant cho tất cả các rewritten_queries
        all_retrieved_chunks = []
        for q in prep_result["search_queries"]:
            vector = embed_query(q)["dense"]   # thay cho self.embedding.encode(q).tolist()
            # Biến câu query thành vector
            
            search_hits = self.qdrant.query_points(
                collection_name="financial_rag",
                query=vector,                              # đổi query_vector= -> query=
                query_filter=qdrant_filter,
                limit=5
            ).points   
            all_retrieved_chunks.extend(search_hits)

        # Loại bỏ các chunk trùng lặp (vì có 3 query phụ có thể tìm ra chung 1 chunk)
        unique_chunks = list({hit.id: hit for hit in all_retrieved_chunks}.values())   # thêm list(...)   

        # Lấy nội dung text_child từ Qdrant để đem đi Rerank
        documents_for_rerank = [hit.payload["content"] for hit in unique_chunks]

        # 4. Reranking: Chấm điểm lại bằng Cross-Encoder để loại nhiễu
        top_k_docs = self.reranker.rerank(
            query=user_query, # Dùng câu hỏi GỐC để đối chiếu
            documents=documents_for_rerank, 
            top_k=3
        )
        top_indices = self.reranker.rerank(user_query, documents_for_rerank, top_k=3)
        # 5. Parent-Document Retrieval từ MongoDB
        seen_parents = set()
        final_contexts = []
        for idx in top_indices:
            parent_id = unique_chunks[idx].payload["parent_id"]
            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)
        # Cầm parent_id sang MongoDB bốc nguyên đoạn văn lớn
            parent_doc = self.mongo.chunks.find_one({"_id": parent_id})
            if parent_doc:
                final_contexts.append(parent_doc["content"])
                
        #final_contexts = []
        #for hit in unique_chunks:
        #    if hit.payload["content"] in top_k_docs:
        #        parent_id = hit.payload["parent_id"]
        #        parent_doc = self.mongo.chunks.find_one({"_id": parent_id})
        #        if parent_doc:
        #            final_contexts.append(parent_doc["content"])

        return {"context": final_contexts, "is_chitchat": False}