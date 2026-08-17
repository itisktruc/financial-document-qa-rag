"""
app/services/test_integration.py

Script CHỈ KẾT NỐI VỚI QDRANT SERVER:
1. Kiểm tra kết nối Qdrant Server và hiển thị danh sách Collections.
2. Nhúng câu hỏi tìm kiếm thành Vector 1024 chiều (dùng BGE-M3).
3. Gửi Vector sang Qdrant Server để tìm kiếm điểm số tương quan Cosine (Similarity Score).
4. Lấy lại Vector đã lưu & Payload dữ liệu để so sánh.
"""

import sys
from pathlib import Path

# Đảm bảo UTF-8 cho Windows Console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Đảm bảo import được module app
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.qdrant_store import get_qdrant, search_similar_blocks
from app.services.embedding_client import embed_query
from app.config import settings

def test_qdrant_only(query_text: str = "Doanh thu FPT năm 2024 đạt bao nhiêu?"):
    print("=" * 85)
    print("1. KIEM TRA KET NOI CHI VOI QDRANT SERVER")
    print("=" * 85)
    print(f"   * Qdrant URL         : {settings.QDRANT_URL}")
    print(f"   * Qdrant Collection  : {settings.QDRANT_COLLECTION}")
    
    # 1. Kết nối Qdrant Server
    qdrant = get_qdrant()
    if not qdrant:
        print("❌ Loi: Khong the ket noi toi Qdrant Server!")
        return

    try:
        collections = [c.name for c in qdrant.get_collections().collections]
        print(f"   * Collections kha dung: {collections}")
        print("-> Ket noi Qdrant Server THANH CONG!\n")
    except Exception as e:
        print(f"❌ Loi truy van Collections tu Qdrant Server: {e}\n")
        return

    # 2. Tạo Vector đại diện cho câu hỏi (Embedding)
    print("=" * 85)
    print(f"2. TAO VECTOR CHO CAU HOI: '{query_text}'")
    print("=" * 85)
    embedding_res = embed_query(query_text)
    query_vector = embedding_res["dense"]
    print(f"   * So chieu Vector sinh ra : {len(query_vector)} dimensions")
    print(f"   * Mau 5 phan tu dau tien  : {query_vector[:5]}\n")

    # 3. Gửi Vector sang Qdrant để so sánh độ tương đồng (Cosine Similarity)
    print("=" * 85)
    print("3. TIM KIEM & SO SANH VECTOR TREN QDRANT SERVER")
    print("=" * 85)
    
    # with_vectors=True: Yêu cầu Qdrant trả lại cả Vector lưu trữ trong DB để so sánh
    hits = search_similar_blocks(
        vector=query_vector,
        limit=5,
        collection_name=settings.QDRANT_COLLECTION,
        with_vectors=True
    )

    print(f"   * So luong diem du lieu (Points) tim thay: {len(hits)}\n")

    if not hits:
        print("⚠️ Qdrant Collection dang trong hoac chua co du lieu nao khop!")
        print("-> Goi y: Hay chay 'python app/ingestion/embedding.py' de nap du lieu vector len Qdrant.")
        return

    for idx, hit in enumerate(hits, 1):
        doc_id = hit.id
        score = hit.score  # Điểm tương quan Cosine Similarity (gần 1.0 là càng giống)
        payload = hit.payload or {}
        text_snippet = (payload.get("text") or payload.get("content") or "")[:120].replace("\n", " ")
        doc_vector = hit.vector if hasattr(hit, "vector") else None

        print(f"--- [POINT #{idx}] ---")
        print(f"   * Point ID           : {doc_id}")
        print(f"   * Cosine Score       : {score:.4f} (Do tuong dong ngu nghia)")
        print(f"   * Ticker / Year      : {payload.get('ticker')} / {payload.get('year')}")
        print(f"   * Noi dung Payload   : {text_snippet}...")
        if doc_vector:
            doc_vec_list = list(doc_vector) if hasattr(doc_vector, "tolist") else doc_vector
            print(f"   * Document Vector    : {len(doc_vec_list)} dims | Mau 3 so dau: {doc_vec_list[:3]}")
        print()

if __name__ == "__main__":
    test_qdrant_only()