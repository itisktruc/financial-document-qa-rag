import os
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

from app.services.qdrant_store import get_qdrant_client, QDRANT_COLLECTION

client = get_qdrant_client()

# 1. Kiểm tra danh sách collection hiện có
collections = client.get_collections().collections
collection_names = [c.name for c in collections]
print(f"[*] Các collection hiện có trong DB: {collection_names}")

# 2. Inspect payload sample nếu collection tồn tại
if QDRANT_COLLECTION in collection_names:
    points, _ = client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=3,
        with_payload=True,
        with_vectors=False
    )
    print(f"\n[*] Đã tìm thấy {len(points)} point mẫu trong '{QDRANT_COLLECTION}':\n")
    for idx, pt in enumerate(points, 1):
        print(f"--- Point {idx} (ID: {pt.id}) ---")
        for key, val in pt.payload.items():
            print(f"  - {key} ({type(val).__name__}): {val}")
else:
    print(f"\n[!] Collection '{QDRANT_COLLECTION}' chưa có trong DB này.")
    print("    Vui lòng kiểm tra lại cấu hình QDRANT_HOST/QDRANT_URL hoặc chạy script ingest dữ liệu.")