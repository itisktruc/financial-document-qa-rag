import os
from pathlib import Path

ROOT_DIR = str(Path(__file__).resolve().parent.parent)
DATA_DIR = os.path.join(ROOT_DIR, "data", "raw")

BASE_DOWNLOAD_DIR = os.path.join(ROOT_DIR, "data", "raw")

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

TASKS = [
    {
        "company": "Vinamilk",
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
        "click_years": [],
        "files_to_download": [] 
    },
    # {
    #     "company": "HoaPhat",
    #     "urls": [
    #         f"https://www.hoaphat.com.vn/quan-he-co-dong/bao-cao-thuong-nien?page={page}"
    #         for page in range(1, 3)
    #     ] +[
    #         f"https://www.hoaphat.com.vn/quan-he-co-dong/bao-cao-tai-chinh?page={page}"
    #         for page in range(1, 3)
    #     ] + [
    #         f"https://www.hoaphat.com.vn/quan-he-co-dong/cao-bach"
    #     ],
    #     "click_years": [],
    #     "files_to_download": []
    # },
    # {
    #     "company": "TheGioiDiDong",
    #     "urls": [
    #         "https://mwg.vn/cong-bo-thong-tin"
    #     ],
    #     "click_years": ["2026", "2025", "2024"], 
    #     "files_to_download": []
    # }
]

