import os
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, PaddleOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

def parse_pdf_with_paddleocr(pdf_path: str):
    """Hàm xử lý cho 1 file PDF đơn lẻ"""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = PaddleOcrOptions(lang=["vi", "en"])
    
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    result = doc_converter.convert(pdf_path)
    return result.document.export_to_markdown()


def parse_all_pdfs_in_dir(root_dir: str = "data/raw"):
    """
    Hàm tự động quét toàn bộ thư mục root_dir và các thư mục con (FPT, Viettel,...)
    để đọc tất cả các file .pdf bằng PaddleOCR.
    """
    root_path = Path(root_dir)
    
    # rglob("*.pdf") giúp duyệt đệ quy qua tất cả thư mục con để tìm file .pdf
    pdf_files = list(root_path.rglob("*.pdf"))
    
    print(f"🔍 Đã tìm thấy tổng cộng {len(pdf_files)} file PDF trong thư mục '{root_dir}'.\n")
    
    results = {}
    for index, pdf_path in enumerate(pdf_files, 1):
        print(f"[{index}/{len(pdf_files)}] Đang xử lý: {pdf_path}...")
        try:
            # Gọi hàm parse cho từng file
            markdown_content = parse_pdf_with_paddleocr(str(pdf_path))
            
            # Lưu kết quả theo đường dẫn file
            results[str(pdf_path)] = markdown_content
            print(f"   ---> ✅ Hoàn thành parse file: {pdf_path.name}")
        except Exception as e:
            print(f"   ---> ❌ Lỗi khi xử lý file {pdf_path.name}: {e}")
            
    return results