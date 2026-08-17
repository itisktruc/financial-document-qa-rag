import logging
from pathlib import Path
import sys

from preprocessing.pipeline import DocumentPreprocessingPipeline, PipelineConfig

# --- Thư mục chứa file test và output ---
TEST_DIR = Path(__file__).resolve().parent / "test"

if not TEST_DIR.exists():
    raise FileNotFoundError(f"Không tìm thấy thư mục: {TEST_DIR}")

# Khởi tạo pipeline (dùng chung cho các file)
cfg = PipelineConfig(debug_pages={7, 8})
pipeline = DocumentPreprocessingPipeline(config=cfg)

# Duyệt qua tất cả các file .txt trong thư mục test
txt_files = list(TEST_DIR.glob("*.txt"))

# Lọc bỏ các file output debug từ lần chạy trước (nếu có)
input_files = [f for f in txt_files if not f.name.startswith("debug_output_")]

if not input_files:
    print(f"Không tìm thấy file .txt hợp lệ nào trong {TEST_DIR}")
    sys.exit(0)

for txt_path in input_files:
    # Tên file log tương ứng: debug_output_<tên_file_gốc>.txt
    log_file = TEST_DIR / f"debug_output_{txt_path.stem}.txt"

    # Lấy root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Xóa các handler cũ để tránh ghi đè/nhân bản log giữa các file
    logger.handlers.clear()

    # Định dạng log
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Handler ghi file riêng cho file txt hiện tại
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Handler in ra terminal
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    print(f"\n================ Đang xử lý: {txt_path.name} ================")

    try:
        doc = pipeline.process_file(txt_path)
        print(f"Done. Pages = {len(doc.pages)}, Blocks = {len(doc.blocks)}")
        print(f"Debug log đã ghi vào: {log_file}")
    except Exception as e:
        logging.error(f"Lỗi khi xử lý file {txt_path.name}: {e}", exc_info=True)