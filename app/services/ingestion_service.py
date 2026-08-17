import os
import traceback
from typing import Dict, Any, Optional
from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk_document
from app.ingestion.metadata_extractor import extract_metadata_from_filename
from app.services.mongo_client import upsert_document, replace_chunks_for_document
from app.services.embedding_client import attach_embeddings_to_chunks, to_qdrant_points
from app.services.qdrant_store import store_in_qdrant
from app.retrieval.hybrid_search import refresh_bm25_index

def process_document_pipeline(document_id: str, file_path: str, extra_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Chạy toàn bộ pipeline nạp tài liệu:
    1. Update status -> PROCESSING
    2. Parse PDF (Docling / OCR)
    3. Chunking
    4. Store chunks in MongoDB
    5. Embed + Store vectors in Qdrant
    6. Invalidate BM25 cache
    7. Update status -> COMPLETED
    """
    try:
        upsert_document(document_id, {"status": "PROCESSING", "file_path": file_path})
        
        # 1. Metadata từ file
        file_meta = extract_metadata_from_filename(os.path.basename(file_path))
        if extra_meta:
            file_meta.update({k: v for k, v in extra_meta.items() if v is not None})
            
        upsert_document(document_id, file_meta)
        
        # 2. Parse PDF
        print(f"[*] [Ingestion] Đang parse file: {file_path}")
        parsed_doc = parse_pdf(file_path)
        
        # 3. Chunking
        print(f"[*] [Ingestion] Đang phân đoạn (chunking)...")
        chunks = chunk_document(parsed_doc, document_id=document_id, extra_metadata=file_meta)
        chunk_dicts = [c.to_dict() for c in chunks]
        
        # Sửa lại _id thành chunk_id cho Mongo document
        for cd in chunk_dicts:
            cd["_id"] = cd["chunk_id"]
            
        # 4. Save MongoDB
        inserted_count = replace_chunks_for_document(document_id, chunk_dicts)
        print(f"[✓] [Ingestion] Đã lưu {inserted_count} chunk vào MongoDB.")
        
        # 5. Embed & Qdrant (chỉ embed text_child và table)
        print(f"[*] [Ingestion] Đang tạo vector embedding (BGE-M3)...")
        embedded_chunks = attach_embeddings_to_chunks(chunk_dicts, return_sparse=False)
        qdrant_points = to_qdrant_points(embedded_chunks)
        
        print(f"[*] [Ingestion] Đang lưu {len(qdrant_points)} points vào Qdrant...")
        store_in_qdrant(qdrant_points)
        
        # 6. Clear BM25 cache để tìm kiếm cập nhật dữ liệu mới
        refresh_bm25_index()
        print(f"[✓] [Ingestion] Đã làm mới chỉ mục BM25.")
        
        # 7. Update status -> COMPLETED
        upsert_document(document_id, {
            "status": "COMPLETED",
            "chunk_count": len(chunk_dicts),
            "vector_count": len(qdrant_points)
        })
        return {
            "document_id": document_id,
            "status": "COMPLETED",
            "chunk_count": len(chunk_dicts),
            "vector_count": len(qdrant_points)
        }
    except Exception as e:
        print(f"[-] [Ingestion] Lỗi khi xử lý tài liệu {document_id}: {e}")
        traceback.print_exc()
        upsert_document(document_id, {"status": "FAILED", "error": str(e)})
        raise e
