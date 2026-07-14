import os
from pathlib import Path
from sec_edgar_downloader import Downloader


def tai_bao_cao_my():
    # Định vị thư mục data/raw trong dự án
    thu_muc_goc = Path(__file__).parent.parent.parent / "data" / "raw"

    # Đảm bảo thư mục raw tồn tại trước khi tải
    os.makedirs(thu_muc_goc, exist_ok=True)

    # Khởi tạo công cụ tải với User-Agent hợp lệ theo quy định của SEC
    dl = Downloader("FinLensRAGTeam", "your-email@domain.com", str(thu_muc_goc))

    # Danh sách các công ty Mỹ cần tải
    cac_cong_ty = ["AAPL", "MSFT", "NVDA", "JPM", "TSLA"]

    for ticker in cac_cong_ty:
        print(f"--- Đang tải dữ liệu cho {ticker} ---")
        try:
            # Tải báo cáo năm 10-K từ năm 2024 đến nay
            dl.get("10-K", ticker, after="2024-01-01")
            # Tải báo cáo quý 10-Q từ năm 2024 đến nay
            dl.get("10-Q", ticker, after="2024-01-01")
        except Exception as e:
            print(f"❌ Lỗi khi tải dữ liệu của {ticker}: {e}")


if __name__ == "__main__":
    tai_bao_cao_my()
    print("🎉 Đã hoàn thành tiến trình tải từ SEC EDGAR!")
