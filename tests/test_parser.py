from app.ingestion.parser import parse_all_pdfs_in_dir

def test_ocr_parser_directory():
    # Chỉ cần truyền đường dẫn thư mục gốc data/raw
    raw_dir = "data/raw"
    
    # Tự động đọc tất cả PDF trong data/raw/FPT/, data/raw/Viettel/,...
    parsed_documents = parse_all_pdfs_in_dir(raw_dir)
    
    assert len(parsed_documents) > 0, "Không tìm thấy file PDF nào trong thư mục!"
    
    print(f"\n🎉 Test thành công! Đã parse tổng cộng {len(parsed_documents)} tài liệu.")

if __name__ == "__main__":
    test_ocr_parser_directory()