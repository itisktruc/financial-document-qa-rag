import os
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http import models as qmodels

# ==========================================
# CẤU HÌNH QDRANT
# ==========================================
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST")   # fallback cho ai vẫn chạy docker-compose local
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_PATH = os.getenv("QDRANT_PATH", "./qdrant_db_storage")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "financial_chunks")
VECTOR_SIZE = 1024

# ==========================================
# KHỞI TẠO CLIENT & COLLECTION
# ==========================================
if QDRANT_URL:
    _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=30)
elif QDRANT_HOST:
    _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
else:
    _client = QdrantClient(path=QDRANT_PATH)

def create_payload_indexes():
    """Tạo Payload Index cho các trường cần dùng trong bộ lọc (Metadata Filter)."""
    indexes = [
        ("parent_id", qmodels.PayloadSchemaType.KEYWORD),
        ("ticker", qmodels.PayloadSchemaType.KEYWORD),
        ("year", qmodels.PayloadSchemaType.INTEGER),
        ("doc_id", qmodels.PayloadSchemaType.KEYWORD),
        ("company", qmodels.PayloadSchemaType.KEYWORD),
        ("chunk_id", qmodels.PayloadSchemaType.KEYWORD),
        ("chunk_type", qmodels.PayloadSchemaType.KEYWORD),
        ("source_file", qmodels.PayloadSchemaType.KEYWORD),
        ("block_type", qmodels.PayloadSchemaType.KEYWORD),
        ("section", qmodels.PayloadSchemaType.KEYWORD),
        ("subsection", qmodels.PayloadSchemaType.KEYWORD),
        ("page_start", qmodels.PayloadSchemaType.INTEGER),
        ("page_end", qmodels.PayloadSchemaType.INTEGER),
        ("order_index", qmodels.PayloadSchemaType.INTEGER),
        ("heading_path", qmodels.PayloadSchemaType.KEYWORD),
        ("text", qmodels.PayloadSchemaType.KEYWORD),
    ]
    
    for field_name, field_type in indexes:
        try:
            _client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name=field_name,
                field_schema=field_type,
            )
            print(f"[*] Đã khởi tạo Payload Index cho: {field_name}")
        except Exception as e:
            # Bỏ qua nếu index đã tồn tại
            pass

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
    create_payload_indexes()
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
def search_similar_blocks(query_vector: list, limit: int = 5, filter_conditions=None, score_threshold: float = 0.0):
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
        limit=limit,
        with_payload=True,     # [BỔ SUNG 1] Ép buộc lấy Metadata để trả về cho Mongo/Reranker
        with_vectors=False,    # [BỔ SUNG 2] Bỏ qua mảng Vector (1024 float) để tiết kiệm băng thông
        score_threshold=score_threshold if score_threshold > 0 else None
    )
    return response.points

def count_points() -> int:
    """Tiện ích nhỏ để test/debug: đếm tổng số point hiện có trong collection."""
    return _client.count(collection_name=QDRANT_COLLECTION, exact=True).count