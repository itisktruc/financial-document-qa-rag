import os
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# ==========================================
# CẤU HÌNH QDRANT
# ==========================================
# Bạn có thể thay đổi đường dẫn hoặc URL kết nối thông qua biến môi trường
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_db_storage")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "fpt_bctc_blocks")
QDRANT_HOST = os.getenv("QDRANT_HOST")  # có set -> ưu tiên connect qua host/port (docker-compose)
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
VECTOR_SIZE = 1024  # Đảm bảo kích thước này khớp với model embedding bạn đang dùng

# ==========================================
# KHỞI TẠO CLIENT & COLLECTION
# ==========================================
if QDRANT_HOST:
    _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
else:
    _client = QdrantClient(path=QDRANT_PATH)


def init_collection():
    """Kiểm tra và tạo Collection nếu chưa tồn tại."""
    if not _client.collection_exists(collection_name=QDRANT_COLLECTION):
        _client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=VECTOR_SIZE, 
                distance=Distance.COSINE
            )
        )
        print(f"[*] Đã tạo mới collection: {QDRANT_COLLECTION}")
    else:
        print(f"[*] Collection '{QDRANT_COLLECTION}' đã sẵn sàng.")

# Khởi tạo ngay khi module được import
init_collection()

# ==========================================
# HÀM XỬ LÝ LƯU TRỮ (UPSERT)
# ==========================================

def store_in_qdrant(qdrant_points: list):
    """
    qdrant_points: list[dict], mỗi dict khớp 100% kwargs của PointStruct
    (id/vector/payload) -- lấy trực tiếp từ
    app.services.embedding_client.to_qdrant_points(embedded_chunks).
    """
    if not qdrant_points:
        print("Không có dữ liệu.")
        return
 
    # Dùng toán tử ** (kwargs unpacking) để nạp thẳng dữ liệu
    points = [PointStruct(**item) for item in qdrant_points]
 
    try:
        _client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points
        )
        print(f"Đã lưu thành công {len(points)} vector vào Qdrant.")
    except Exception as e:
        print(f"Lỗi khi đẩy dữ liệu vào Qdrant: {e}")
# ==========================================
# CÁC HÀM HỖ TRỢ TRUY VẤN (Tùy chọn)
# ==========================================
def search_similar_blocks(query_vector: list, limit: int = 5, filter_conditions=None):
    """
    Truy vấn các block có vector tương đồng nhất với câu hỏi.
    (Dùng cho Bước 2 trong pipeline RAG).
 
    LƯU Ý: qdrant-client >= 1.10 đã bỏ hẳn QdrantClient.search() (không chỉ
    deprecate) để chuyển sang query_points() -- .search() giờ raise
    AttributeError thẳng, không phải warning. Dùng query_points() ở đây và
    trả về .points để interface (list các object có .id/.score/.payload)
    giữ nguyên như code cũ gọi .search(), không phải sửa gì ở nơi gọi hàm này.
    """
    response = _client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=filter_conditions,  # Thêm bộ lọc metadata nếu cần
        limit=limit
    )
    return response.points

def count_points() -> int:
    """Tiện ích nhỏ để test/debug: đếm tổng số point hiện có trong collection."""
    return _client.count(collection_name=QDRANT_COLLECTION, exact=True).count