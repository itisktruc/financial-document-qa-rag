import importlib.util
import sys


def test_environment():
    print("=== KIỂM TRA MÔI TRƯỜNG HOẠT ĐỘNG ===")
    # Sử dụng importlib để kiểm tra sự tồn tại của package mà không bị lỗi Ruff F401
    pymupdf_installed = importlib.util.find_spec("pymupdf4llm") is not None

    if pymupdf_installed:
        print("✅ Thư viện 'pymupdf4llm' đã được cài đặt thành công!")
        print(f"Phiên bản hệ thống Python: {sys.version}")
    else:
        print(
            "❌ Chưa tìm thấy thư viện 'pymupdf4llm'. Vui lòng chạy lệnh: py -m pip install pymupdf4llm"
        )


if __name__ == "__main__":
    test_environment()
