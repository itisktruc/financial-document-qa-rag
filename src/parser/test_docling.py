import os
from pathlib import Path
from docling.document_converter import DocumentConverter

def run_benchmarks_all_companies():
    # Khởi tạo công cụ Docling
    converter = DocumentConverter()
    
    # Định vị các thư mục trong dự án
    base_dir = Path(__file__).parent.parent.parent
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    
    # Tạo thư mục processed để lưu kết quả nếu chưa có
    os.makedirs(processed_dir, exist_ok=True)
    
    print("=== BẮT ĐẦU QUÉT VÀ PARSE TỰ ĐỘNG TOÀN BỘ DATASET (MỸ & VIỆT NAM) ===")

    # =========================================================================
    # PHẦN 1: TỰ ĐỘNG QUÉT VÀ XỬ LÝ TOÀN BỘ FILE SEC EDGAR (MỸ)
    # =========================================================================
    sec_dir = raw_dir / "sec-edgar-filings"
    if sec_dir.exists():
        print("\n🔍 Đang tìm kiếm tài liệu SEC Mỹ...")
        # Tìm tất cả các file full-submission.txt nằm sâu bên trong thư mục SEC
        sec_files = list(sec_dir.glob("**/full-submission.txt"))
        print(f"📌 Tìm thấy {len(sec_files)} file từ SEC.")
        
        for index, file_path in enumerate(sec_files, 1):
            # Lấy tên công ty (ví dụ: AAPL, MSFT) từ đường dẫn thư mục cha
            ticker = file_path.parts[-4] 
            # Lấy loại báo cáo (10-K hoặc 10-Q)
            doc_type = file_path.parts[-3]
            
            print(f"⏳ [{index}/{len(sec_files)}] Đang parse file {doc_type} của {ticker}...")
            
            try:
                result = converter.convert(file_path)
                markdown_output = result.document.export_to_markdown()
                
                # Đặt tên file kết quả: ví dụ US_AAPL_10K_parsed.md
                output_name = f"US_{ticker}_{doc_type}_parsed.md"
                with open(processed_dir / output_name, "w", encoding="utf-8") as f:
                    f.write(markdown_output)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý file SEC {ticker}: {e}")
    else:
        print("\n❌ Thư mục 'sec-edgar-filings' không tồn tại.")

    # =========================================================================
    # PHẦN 2: TỰ ĐỘNG QUÉT VÀ XỬ LÝ TOÀN BỘ FILE CỦA CÁC CÔNG TY VIỆT NAM
    # =========================================================================
    vietnam_dir = raw_dir / "vietnam"
    if vietnam_dir.exists():
        print("\n🔍 Đang tìm kiếm tài liệu các công ty Việt Nam...")
        # Tìm tất cả các file có đuôi .pdf hoặc .PDF trong thư mục vietnam
        vn_files = list(vietnam_dir.glob("**/*.pdf")) + list(vietnam_dir.glob("**/*.PDF"))
        print(f"📌 Tìm thấy {len(vn_files)} file PDF Việt Nam.")
        
        for index, file_path in enumerate(vn_files, 1):
            # Lấy tên thư mục cha trực tiếp của file làm tên công ty (ví dụ: FPT, MWG, HPG)
            company_name = file_path.parent.name
            # Lấy tên file gốc (bỏ đuôi .pdf)
            file_name_clean = file_path.stem
            
            print(f"⏳ [{index}/{len(vn_files)}] Đang parse file {file_path.name} của {company_name}...")
            
            try:
                result = converter.convert(file_path)
                markdown_output = result.document.export_to_markdown()
                
                # Đặt tên file kết quả: ví dụ VN_FPT_FPT_BCTC_2025_parsed.md
                output_name = f"VN_{company_name}_{file_name_clean}_parsed.md"
                with open(processed_dir / output_name, "w", encoding="utf-8") as f:
                    f.write(markdown_output)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý file {file_path.name}: {e}")
    else:
        print("\n❌ Thư mục 'vietnam' không tồn tại. Hãy tạo thư mục này trong data/raw/")

    print("\n🎉 HOÀN THÀNH TOÀN BỘ PIPELINE PARSING!")

if __name__ == "__main__":
    run_benchmarks_all_companies()