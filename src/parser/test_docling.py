import sys
from pathlib import Path


def test_environment():
    print("=== KIỂM TRA MÔI TRƯỜNG HOẠT ĐỘNG ===")
    try:
        import pymupdf4llm

        print("✅ Thư viện 'pymupdf4llm' đã được cài đặt thành công!")
        print(f"Phiên bản hệ thống Python: {sys.version}")
    except ImportError:
        print(
            "❌ Chưa tìm thấy thư viện 'pymupdf4llm'. Vui lòng chạy lệnh: py -m pip install pymupdf4llm"
        )


if __name__ == "__main__":
    test_environment()