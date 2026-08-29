"""Từ điển viết tắt tài chính tiếng Việt phổ biến -- dùng để (1) mở rộng
câu hỏi trước khi search, (2) trả lời trực tiếp câu hỏi định nghĩa."""

FINANCIAL_GLOSSARY: dict[str, str] = {
    "LNST": "Lợi nhuận sau thuế",
    "LNTT": "Lợi nhuận trước thuế",
    "DTT": "Doanh thu thuần",
    "DT": "Doanh thu",
    "GVHB": "Giá vốn hàng bán",
    "CPBH": "Chi phí bán hàng",
    "CPQLDN": "Chi phí quản lý doanh nghiệp",
    "VCSH": "Vốn chủ sở hữu",
    "TSCĐ": "Tài sản cố định",
    "TSNH": "Tài sản ngắn hạn",
    "TSDH": "Tài sản dài hạn",
    "BCTC": "Báo cáo tài chính",
    "BCTN": "Báo cáo thường niên",
    "CDKT": "Bảng cân đối kế toán",
    "KQKD": "Báo cáo kết quả hoạt động kinh doanh",
    "LCTT": "Báo cáo lưu chuyển tiền tệ",
    "EPS": "Lãi cơ bản trên mỗi cổ phiếu (Earnings Per Share)",
    "ROE": "Tỷ suất lợi nhuận trên vốn chủ sở hữu (Return On Equity)",
    "ROA": "Tỷ suất lợi nhuận trên tổng tài sản (Return On Assets)",
    "P/E": "Hệ số giá trên lợi nhuận (Price to Earnings)",
    "YoY": "So với cùng kỳ năm trước (Year over Year)",
    "QoQ": "So với quý trước (Quarter over Quarter)",
}
def expand_query(query: str) -> str:
    expanded = query
    for abbr, full in sorted(FINANCIAL_GLOSSARY.items(), key=lambda x: -len(x[0])):
        if full in expanded:
            continue
        parts = expanded.split()
        new_parts = []
        for p in parts:
            core = p.strip(".,;:()[]")
            if core.upper() == abbr.upper() or core == abbr:
                new_parts.append(f"{p} ({full})" if p == core else p.replace(core, f"{core} ({full})"))
            else:
                new_parts.append(p)
        expanded = " ".join(new_parts)
    return expanded