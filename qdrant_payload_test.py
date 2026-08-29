import sys
import inspect
from pathlib import Path

try:
    import app.services.qdrant_store as qdrant_store
except ImportError:
    print("[ERROR] Cannot import app.services.qdrant_store. Ensure you are running from project root.", file=sys.stderr)
    sys.exit(1)


def find_qdrant_client(module):
    """Dynamically locates any client function or object exposed by qdrant_store."""
    # Check common variable or function names
    candidate_names = ["get_client", "get_qdrant_client", "get_store", "client", "qdrant_client", "store"]
    for attr in candidate_names:
        if hasattr(module, attr):
            obj = getattr(module, attr)
            if callable(obj):
                try:
                    res = obj()
                    if hasattr(res, "scroll"):
                        return res
                except Exception:
                    pass
            elif hasattr(obj, "scroll"):
                return obj

    # Fallback inspection: search for any member with 'scroll' method
    for name, obj in inspect.getmembers(module):
        if callable(obj):
            try:
                res = obj()
                if hasattr(res, "scroll"):
                    return res
            except Exception:
                continue
        elif hasattr(obj, "scroll"):
            return obj

    return None


client = find_qdrant_client(qdrant_store)

if client is None:
    print("[ERROR] Could not automatically find a Qdrant client in app.services.qdrant_store.")
    print("\nAvailable attributes in app.services.qdrant_store:")
    for name in dir(qdrant_store):
        if not name.startswith("_"):
            print(f"  • {name}")
    sys.exit(1)

COLLECTION_NAME = "financial_chunks"

try:
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=5,
        with_payload=True,
        with_vectors=False,
    )

    if not points:
        print(f"[WARN] Collection '{COLLECTION_NAME}' is empty or does not exist.")
    else:
        print(f"\n[SUCCESS] Retrieved {len(points)} sample points from '{COLLECTION_NAME}':\n")
        print("=" * 70)
        for i, point in enumerate(points, 1):
            payload = point.payload or {}
            print(f"Point #{i} | ID: {point.id}")
            print("-" * 70)
            for key, val in payload.items():
                val_repr = repr(val)
                if len(val_repr) > 100:
                    val_repr = val_repr[:97] + "..."
                print(f"  • {key:<15} ({type(val).__name__:<5}) : {val_repr}")
            print("=" * 70)

except Exception as e:
    err_msg = str(e)
    print(f"[ERROR] Failed to query collection '{COLLECTION_NAME}': {e}", file=sys.stderr)

    if "Connection refused" in err_msg or "[Errno 61]" in err_msg or "ConnectError" in err_msg:
        print("\n" + "=" * 70)
        print("🔍 NGUYÊN NHÂN VÀ HƯỚNG DẪN KHẮC PHỤC [Errno 61 Connection refused]:")
        print("=" * 70)
        print("Lỗi này xảy ra do Qdrant Server trên máy bạn chưa chạy hoặc port 6333 bị từ chối kết nối.\n")
        print("1. Nếu bạn chạy Qdrant bằng Docker Server:")
        print("   Bật container Qdrant bằng lệnh:")
        print("   👉  docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        print("   Hoặc nếu có file docker-compose.yml:")
        print("   👉  docker compose up -d\n")
        print("2. Nếu dự án của bạn lưu Qdrant dưới dạng Local File (Disk Mode):")
        print("   Hãy kiểm tra biến môi trường hoặc path cấu hình trong 'app/services/qdrant_store.py'.")
        print("=" * 70)

        possible_paths = ["./qdrant_data", "./qdrant_db", "./data/qdrant", "./storage/qdrant", "./qdrant_storage"]
        found_local = False
        for p in possible_paths:
            path_obj = Path(p)
            if path_obj.exists() and path_obj.is_dir():
                found_local = True
                print(f"\n[*] Phát hiện thư mục lưu trữ Qdrant Local tại: {path_obj.resolve()}")
                print(f"[*] Thử kết nối trực tiếp đến file database local...")
                try:
                    from qdrant_client import QdrantClient
                    local_client = QdrantClient(path=str(path_obj))
                    p_pts, _ = local_client.scroll(collection_name=COLLECTION_NAME, limit=5, with_payload=True)
                    if not p_pts:
                        print(f"[WARN] Collection '{COLLECTION_NAME}' trong thư mục local khả thi nhưng đang rỗng.")
                    else:
                        print(f"\n[SUCCESS] Đọc thành công {len(p_pts)} sample points từ Local Storage ({p}):\n")
                        print("=" * 70)
                        for i, point in enumerate(p_pts, 1):
                            payload = point.payload or {}
                            print(f"Point #{i} | ID: {point.id}")
                            print("-" * 70)
                            for key, val in payload.items():
                                val_repr = repr(val)
                                if len(val_repr) > 100:
                                    val_repr = val_repr[:97] + "..."
                                print(f"  • {key:<15} ({type(val).__name__:<5}) : {val_repr}")
                            print("=" * 70)
                    break
                except Exception as local_err:
                    print(f"    [WARN] Thử kết nối local {p} không thành công: {local_err}")

        if not found_local:
            print("\n[!] Không tìm thấy thư mục local database nào. Hãy khởi chạy Docker Qdrant Server rồi chạy lại script này.")