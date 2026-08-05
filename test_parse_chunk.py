# test_OCR.py
"""
Script test thủ công: chạy TOÀN BỘ pipeline parse_pdf() -> chunk_document()
cho 1 file PDF thật, lưu cả 2 kết quả (parsed + chunks) ra data/processed/
để kiểm tra bằng mắt.

Chạy: python test_OCR.py

Đổi PDF_PATH bên dưới nếu muốn test file khác. Sau khi đã có
data/processed/{ten_file}_parsed.json, có thể chỉnh sửa app/ingestion/chunker.py
rồi chạy riêng `python test_chunking.py` để chunk lại NHANH mà không cần
parse/OCR lại từ đầu.
"""

import json
import os
import sys
import time

# Lưu ý: file này nằm ở ROOT của repo (cùng cấp với thư mục app/), nên chỉ
# cần add chính thư mục chứa file này vào sys.path -- KHÔNG đi lên 1 cấp
# như bản cũ (bản cũ giả định file nằm trong scripts/, gây lỗi import khi
# chạy từ root).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ingestion.parser import parse_pdf, save_markdown
from test_chunking import _guess_metadata_from_filename, run_chunking

# ==== CHỌN FILE PDF THẬT ĐỂ TEST ====
PDF_PATH = "data/raw/FPT/FPT_BCTC_2024.pdf"   # đổi thành file bạn muốn test

# ==== THƯ MỤC OUTPUT ====
OUTPUT_DIR = "data/processed/FPT"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
    parsed_path = os.path.join(OUTPUT_DIR, f"{file_name}_parsed.json")
    chunks_path = os.path.join(OUTPUT_DIR, f"{file_name}_chunks.json")
    ocr_markdown_path = os.path.join(OUTPUT_DIR, f"{file_name}_ocr.md")

    # ---- Bước 1: Parse ----
    print(f"[*] Đang parse: {PDF_PATH}")
    t0 = time.time()
    result = parse_pdf(PDF_PATH)
    parse_elapsed = time.time() - t0

    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    save_markdown(result, ocr_markdown_path)

    print(f"[✓] Kết quả parse đã lưu tại: {parsed_path}")
    print(f"[i] Nguồn xử lý (docling_native / qwen_vlm): {result.get('source')}")
    print(f"[i] Số trang: {result.get('pages')}")
    print(f"[i] Thời gian parse: {parse_elapsed:.1f}s")

    pages_error = result.get("pages_error") or {}
    if pages_error:
        print(f"[!] {len(pages_error)} trang báo lỗi khi parse/OCR:")
        for page, err in pages_error.items():
            print(f"    - Trang {page}: {err}")
    else:
        print("[i] Không có trang nào báo lỗi.")

    # ---- Bước 2: Chunk ----
    print("\n[*] Đang chunk...")
    t1 = time.time()
    run_chunking(
        result,
        document_id=file_name,
        output_path=chunks_path,
        extra_metadata=_guess_metadata_from_filename(PDF_PATH),
    )
    print(f"[i] Thời gian chunk: {time.time() - t1:.1f}s")


if __name__ == "__main__":
    main()