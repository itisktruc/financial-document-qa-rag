from app.ingestion.parser import parse_pdf, save_markdown

# 1. Đường dẫn tới 1 file PDF scan/BCTC bất kỳ để test
pdf_path = "data/raw/FPT/FPT_BCTC_2024.pdf"

print("Đang gửi file lên Vast.ai để OCR")
parsed_result = parse_pdf(pdf_path)

# 2. Xuất kết quả OCR ra file .md
output_path = save_markdown(parsed_result, "qwen3_ocr_fpt_result.md")
print(f"Đã OCR xong! Hãy mở file '{output_path}' để kiểm tra kết quả.")