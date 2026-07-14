import time
import os
from docling.document_converter import DocumentConverter


def parse_pdf_to_markdown(file_path, output_dir):
    """Hàm xử lý từng file PDF và xuất ra file Markdown tương ứng"""
    print(f"\n--- Đang xử lý file: {os.path.basename(file_path)} ---")
    start_time = time.time()

    try:
        # Khởi tạo bộ chuyển đổi Docling
        converter = DocumentConverter()

        # Thực hiện chuyển đổi PDF
        result = converter.convert(file_path)

        # Xuất nội dung ra định dạng Markdown (giúp giữ nguyên cấu trúc bảng số liệu)
        markdown_text = result.document.export_to_markdown()

        # Tạo tên file đầu ra (.md) giữ nguyên tên file cũ
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file_path = os.path.join(output_dir, f"{base_name}_parsed.md")

        # Lưu kết quả text vào thư mục data/processed
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        elapsed_time = time.time() - start_time
        print(f"✅ Hoàn thành! Thời gian: {elapsed_time:.2f} giây.")
        print(f"💾 Đã lưu kết quả tại: {output_file_path}")

    except Exception as e:
        print(f"❌ Lỗi khi xử lý file {os.path.basename(file_path)}: {str(e)}")


if __name__ == "__main__":
    # 1. Định nghĩa chính xác các đường dẫn thư mục dựa trên cấu trúc máy bạn
    RAW_DATA_DIR = "data/raw"
    PROCESSED_DATA_DIR = "data/processed"

    # Các thư mục con cần quét dữ liệu
    sub_folders = ["vietnam", "sec-edgar-filings"]

    # Tự động tạo thư mục processed nếu chưa có
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    total_files_processed = 0

    # 2. Vòng lặp quét qua từng thư mục con để tìm file PDF
    for folder in sub_folders:
        current_dir = os.path.join(RAW_DATA_DIR, folder)
        print(f"\n=== Đang quét thư mục: {current_dir} ===")

        if not os.path.exists(current_dir):
            print(
                f"⚠️ Cảnh báo: Thư mục '{current_dir}' không tồn tại. Hãy kiểm tra lại!"
            )
            continue

        # Lấy danh sách tất cả các file trong thư mục con
        files = os.listdir(current_dir)
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]

        if not pdf_files:
            print(f"ℹ️ Không tìm thấy file PDF nào trong thư mục '{folder}'.")
            continue

        print(f"Tìm thấy {len(pdf_files)} file PDF cần xử lý.")

        # Tiến hành trích xuất lần lượt từng file
        for pdf_file in pdf_files:
            full_pdf_path = os.path.join(current_dir, pdf_file)
            parse_pdf_to_markdown(full_pdf_path, PROCESSED_DATA_DIR)
            total_files_processed += 1

    print(
        f"\n🚀 TẤT CẢ HOÀN THÀNH! Đã xử lý tổng cộng {total_files_processed} file tài liệu."
    )
