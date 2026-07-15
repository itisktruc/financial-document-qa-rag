import os 

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data", "material")

BASE_DOWNLOAD_DIR = os.path.join(ROOT_DIR, "data", "material")

CSV_FILENAME = os.path.join(ROOT_DIR, "data", "RenameList.csv")
JSON_FILENAME = os.path.join(ROOT_DIR, "data", "RenameList.json")

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

TASKS = [
    {
        "company": "Vinamilk",
        # Sinh URL tự động cho các năm và quý
        "urls": [
            f"https://www.vinamilk.com.vn/investor/reports/financial?year={year}&quarter={quarter}"
            for year in range(2024, 2027) 
            for quarter in range(1, 5)
        ] + [
            f"https://www.vinamilk.com.vn/investor/reports/annual"
        ] + [
            f"https://www.vinamilk.com.vn/investor/reports/governance?year={year}"
            for year in range(2024, 2027)
        ],
        "click_years": [], # Không cần click, vì web load theo URL
        "files_to_download": [] 
    },
    {
        "company": "HoaPhat",
        # Sinh URL tự động cho các trang
        "urls": [
            f"https://www.hoaphat.com.vn/quan-he-co-dong/bao-cao-thuong-nien?page={page}"
            for page in range(1, 3)
        ] +[
            f"https://www.hoaphat.com.vn/quan-he-co-dong/bao-cao-tai-chinh?page={page}"
            for page in range(1, 3)
        ] + [
            f"https://www.hoaphat.com.vn/quan-he-co-dong/cao-bach"
        ],
        "click_years": [],
        "files_to_download": []
    },
    {
        "company": "TheGioiDiDong",
        "urls": [
            "https://mwg.vn/cong-bo-thong-tin"
        ],
        # Web tĩnh URL, cần click vào các tab/năm để load dữ liệu
        "click_years": ["2026", "2025", "2024"], 
        "files_to_download": []
    }
]

