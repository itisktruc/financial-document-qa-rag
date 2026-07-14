import os
from pathlib import Path
import pymupdf4llm


def run_benchmarks_all_companies():
    # Định vị các thư mục gốc dựa trên vị trí của file này (src/parser/doc_parser.py)
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"

    # Tự động tạo thư mục processed nếu chưa có
    os.makedirs(processed_dir, exist_ok=True)

    print("=== BẮT ĐẦU QUÉT VÀ PARSE TỰ ĐỘNG TOÀN BỘ DATASET (MỸ & VIỆT NAM) ===")

    # =========================================================================
    # PHẦN 1: XỬ LÝ TOÀN BỘ FILE SEC EDGAR THÔ (MỸ)
    # =========================================================================
    sec_dir = raw_dir / "sec-edgar-filings"
    if sec_dir.exists():
        print("\n🔍 Đang tìm kiếm tài liệu SEC Mỹ...")
        sec_files = list(sec_dir.glob("**/full-submission.txt"))
        print(f"📌 Tìm thấy {len(sec_files)} file từ SEC.")

        for index, file_path in enumerate(sec_files, 1):
            ticker = file_path.parts[-4]
            doc_type = file_path.parts[-3]

            print(
                f"⏳ [{index}/{len(sec_files)}] Đang đọc file {doc_type} của {ticker}..."
            )

            try:
                # File SEC thô dạng text/html, đọc trực tiếp không cần qua pymupdf4llm
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                output_name = f"US_{ticker}_{doc_type}_parsed.md"
                with open(processed_dir / output_name, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý file SEC {ticker}: {e}")
    else:
        print("\n❌ Thư mục 'sec-edgar-filings' không tồn tại.")

    # =========================================================================
    # PHẦN 2: XỬ LÝ TOÀN BỘ FILE PDF CỦA CÁC CÔNG TY VIỆT NAM (ĐỆ QUY SÂU)
    # =========================================================================
    vietnam_dir = raw_dir / "vietnam"
    if vietnam_dir.exists():
        print("\n🔍 Đang tìm kiếm tài liệu các công ty Việt Nam...")
        # Tìm tất cả file PDF ở mọi cấp thư mục con (ví dụ: vietnam/FPT/file.pdf)
        vn_files = list(vietnam_dir.glob("**/*.pdf")) + list(
            vietnam_dir.glob("**/*.PDF")
        )
        print(f"📌 Tìm thấy {len(vn_files)} file PDF Việt Nam.")

        for index, file_path in enumerate(vn_files, 1):
            # Tên thư mục chứa trực tiếp file PDF chính là tên công ty (Ví dụ: FPT)
            company_name = file_path.parent.name
            file_name_clean = file_path.stem

            print(
                f"⏳ [{index}/{len(vn_files)}] Đang parse file {file_path.name} bằng pymupdf4llm..."
            )

            try:
                # Chuyển đổi PDF sang Markdown bằng pymupdf4llm
                markdown_output = pymupdf4llm.to_markdown(str(file_path))

                # Đặt tên file kết quả: VN_FPT_FPT_BCTN_2025_parsed.md
                output_name = f"VN_{company_name}_{file_name_clean}_parsed.md"
                with open(processed_dir / output_name, "w", encoding="utf-8") as f:
                    f.write(markdown_output)
                print(f"💾 Đã lưu: {output_name}")
            except Exception as e:
                print(f"❌ Lỗi khi xử lý file {file_path.name}: {e}")
    else:
        print(
            "\n❌ Thư mục 'vietnam' không tồn tại. Hãy kiểm tra lại cấu trúc data/raw/"
        )

    print("\n🚀 HOÀN THÀNH TOÀN BỘ PIPELINE PARSING!")


if __name__ == "__main__":
    run_benchmarks_all_companies()