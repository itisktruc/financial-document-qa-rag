import json
import zipfile
from pymongo import MongoClient
from pathlib import Path

# ============ CẤU HÌNH ============
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "financial_rag"
COLLECTION = "documents_2025"

ZIP_PATH = Path("./documents_2025.zip")
# ==================================

def main():
    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION]

    total = collection.count_documents({})
    print(f"Tìm thấy {total} document(s). Bắt đầu ghi trực tiếp vào ZIP...")

    # Mở file ZIP để ghi
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, doc in enumerate(collection.find({}), start=1):
            # Xử lý tên file trong zip từ _id
            doc_id = str(doc["_id"]).replace("/", "_").replace("\\", "_")
            file_name_in_zip = f"{doc_id}.json"

            # Chuyển document thành chuỗi JSON
            json_bytes = json.dumps(doc, ensure_ascii=False, indent=2, default=str).encode("utf-8")

            # Ghi trực tiếp chuỗi JSON vào ZIP mà không cần lưu ổ đĩa
            zf.writestr(file_name_in_zip, json_bytes)

            if i % 50 == 0 or i == total:
                print(f"  [{i}/{total}] Đã nén: {file_name_in_zip}")

    print(f"\n Xong! File zip: {ZIP_PATH.resolve()}")
    print(f"Kích thước: {ZIP_PATH.stat().st_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    main()