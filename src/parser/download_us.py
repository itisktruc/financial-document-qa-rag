import os
from pathlib import Path
from sec_edgar_downloader import Downloader


def tai_bao_cao_my():
    # Quy định bắt buộc của SEC: Thay tên nhóm và email của bạn vào đây
    USER_AGENT = "FinLensRAGTeam/1.0 (your-email@domain.com)"

    # Định vị thư mục data/raw trong dự án của bạn
    thu_muc_goc = Path(__file__).parent.parent.parent / "data" / "raw"

    # Khởi tạo công cụ tải
    dl = Downloader("FinLensRAGTeam", "your-email@domain.com", str(thu_muc_goc))

    # Danh sách 5 công ty Mỹ cần tải theo yêu cầu đề bài
    cac_cong_ty = ["AAPL", "MSFT", "NVDA", "JPM", "TSLA"]

    for ticker in cac_cong_ty:
        print(f"--- Đang tải dữ liệu cho {ticker} ---")
        # Đã đổi sau_date="2024-01-01" thành after="2024-01-01"
        # Tải báo cáo năm 10-K từ năm 2024 đến nay
        dl.get("10-K", ticker, after="2024-01-01")
        # Tải báo cáo quý 10-Q từ năm 2024 đến nay
        dl.get("10-Q", ticker, after="2024-01-01")


if __name__ == "__main__":
    tai_bao_cao_my()
    print("🎉 Đã tải xong toàn bộ báo cáo từ SEC EDGAR!")
