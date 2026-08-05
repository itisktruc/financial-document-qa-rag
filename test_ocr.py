# test_OCR.py
"""
Script test thủ công: CHỈ chạy bước parse_pdf() (docling / Qwen3-VL OCR),
KHÔNG chunk. Dùng khi chỉ muốn kiểm tra nhanh chất lượng parse/OCR (đọc file
*_ocr.md để rà soát bằng mắt) mà không phải đợi bước chunk chạy theo.

Chạy: python test_OCR.py

Muốn chạy cả parse + chunk trong 1 lần, dùng test_parse_chunk.py.
Muốn chunk lại (dùng JSON đã parse sẵn, không parse lại), dùng test_chunking.py.
"""

import json
import os
import sys
import time

# File này nằm ở ROOT của repo (cùng cấp với thư mục app/) -- chỉ cần add
# chính thư mục chứa file này vào sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ingestion.parser import parse_pdf, save_markdown

# ==== CHỌN FILE PDF THẬT ĐỂ TEST ====
PDF_PATH = "data/raw/FPT/FPT_BCTC_2024.pdf"   # đổi thành file bạn muốn test

# ==== THƯ MỤC OUTPUT ====
OUTPUT_DIR = "data/processed/FPT"             # đổi theo công ty nếu test file khác


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
    parsed_path = os.path.join(OUTPUT_DIR, f"{file_name}_parsed.json")
    ocr_markdown_path = os.path.join(OUTPUT_DIR, f"{file_name}_ocr.md")

    print(f"[*] Đang parse: {PDF_PATH}")
    t0 = time.time()
    result = parse_pdf(PDF_PATH)
    parse_elapsed = time.time() - t0

    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    save_markdown(result, ocr_markdown_path)

    print(f"[✓] Kết quả parse (JSON) đã lưu tại: {parsed_path}")
    print(f"[✓] Bản markdown dễ đọc đã lưu tại:   {ocr_markdown_path}")
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


if __name__ == "__main__":
    main()