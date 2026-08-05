# test_chunking.py
"""
Script test thủ công: chạy app/ingestion/chunker.chunk_document() cho 1 file PDF.

Ưu tiên dùng lại kết quả parse đã lưu ở data/processed/{ten_file}_parsed.json
(từ lần chạy test_OCR.py trước đó) thay vì parse lại từ đầu -- vì nhánh OCR
giờ dùng Qwen3-VL (load model nặng, chạy GPU), không muốn tốn thời gian đó
mỗi lần chỉ đang sửa logic chunking.

Chạy độc lập:
    python test_chunking.py

Cũng được test_OCR.py gọi lại (qua hàm run_chunking) ngay sau khi parse
xong, dùng thẳng dict trong bộ nhớ, không phải ghi/đọc lại đĩa.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ingestion.chunker import Chunk, chunk_document

# ==== CHỌN FILE PDF THẬT ĐỂ TEST (khớp với test_OCR.py) ====
PDF_PATH = "data/raw/FPT/FPT_BCTC_2024.pdf"
OUTPUT_DIR = "data/processed/FPT"


def _guess_metadata_from_filename(pdf_path: str) -> dict:
    """
    Đoán vài field metadata cơ bản từ tên file để test nhanh (vd 'FPT_BCTC_2024'
    -> ticker='FPT'). Đây CHỈ là tiện ích cho script test thủ công -- pipeline
    thật nên dùng app/ingestion/metadata_extractor.py (LLM extract business
    metadata) như mô tả trong README, không nên đoán bằng regex tên file.
    """
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    ticker = name.split("_")[0] if name else None
    return {"ticker": ticker, "source_file": os.path.basename(pdf_path)}


def print_chunk_summary(chunks: list[Chunk]) -> None:
    print(f"\n[i] Tổng số chunk: {len(chunks)}")

    by_type: dict[str, int] = {}
    tokens_by_type: dict[str, int] = {}
    for c in chunks:
        by_type[c.chunk_type.value] = by_type.get(c.chunk_type.value, 0) + 1
        tokens_by_type[c.chunk_type.value] = tokens_by_type.get(c.chunk_type.value, 0) + c.token_count

    for t, count in sorted(by_type.items()):
        avg_tokens = tokens_by_type[t] / count if count else 0
        print(f"    - {t:11s}: {count:4d} chunk, trung bình ~{avg_tokens:.0f} token/chunk")

    # cảnh báo sớm nếu có chunk retrieval-được (text_child/table) mà thiếu số trang
    # -- ảnh hưởng trực tiếp tới "traceable citation" của README
    retrievable = [c for c in chunks if c.chunk_type.value in ("text_child", "table")]
    missing_page = [c for c in retrievable if c.page_start is None]
    if missing_page:
        print(
            f"[!] {len(missing_page)}/{len(retrievable)} chunk (text_child/table) KHÔNG có "
            "số trang -- citation sẽ không trỏ được đến đúng trang cho các chunk này."
        )
    else:
        print(f"[i] Tất cả {len(retrievable)} chunk text_child/table đều có số trang.")

    print("\n[i] 3 chunk đầu tiên (xem nhanh nội dung):")
    for c in retrievable[:3]:
        preview = c.content.strip().replace("\n", " ")[:100]
        print(f"    [{c.chunk_type.value}] trang {c.page_start} | {c.section_path} | {preview}...")


def run_chunking(
    parsed: dict,
    document_id: str,
    output_path: str,
    extra_metadata: Optional[dict] = None,
) -> list[Chunk]:
    """Chunk + lưu ra JSON + in tóm tắt. Tách riêng hàm này để test_OCR.py
    gọi lại được mà không phải copy-paste logic."""
    chunks = chunk_document(parsed, document_id=document_id, extra_metadata=extra_metadata)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in chunks], f, ensure_ascii=False, indent=2, default=str)

    print(f"[✓] {len(chunks)} chunk đã lưu tại: {output_path}")
    print_chunk_summary(chunks)
    return chunks


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
    parsed_path = os.path.join(OUTPUT_DIR, f"{file_name}_parsed.json")
    chunks_path = os.path.join(OUTPUT_DIR, f"{file_name}_chunks.json")

    if os.path.exists(parsed_path):
        print(f"[*] Dùng lại kết quả parse đã có tại: {parsed_path} (không parse lại từ đầu)")
        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
    else:
        print(f"[*] Chưa có kết quả parse sẵn -- đang parse: {PDF_PATH}")
        print("[i] (chậm hơn nếu rơi vào nhánh OCR Qwen3-VL vì phải load model lần đầu)")
        from app.ingestion.parser import parse_pdf  # import trễ: tránh load docling/transformers

        parsed = parse_pdf(PDF_PATH)
        with open(parsed_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2, default=str)
        print(f"[✓] Kết quả parse đã lưu tại: {parsed_path}")

    run_chunking(
        parsed,
        document_id=file_name,
        output_path=chunks_path,
        extra_metadata=_guess_metadata_from_filename(PDF_PATH),
    )


if __name__ == "__main__":
    main()
