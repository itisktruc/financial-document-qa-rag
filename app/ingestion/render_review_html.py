"""
render_review_html.py

Dựng lại TOÀN BỘ tài liệu đã parse thành 1 file HTML để xem/soát bằng mắt:
  - Số "trang" (section) trong HTML = ĐÚNG BẰNG số trang của PDF gốc (đảm bảo
    bằng cách duyệt trực tiếp theo `pages_markdown` - không gộp/bỏ trang nào).
  - Bảng biểu được render là <table> THẬT (đúng số hàng/cột paddle suy luận),
    không phải text phẳng - xem trực quan được ngay cấu trúc bảng có đúng
    không, không cần đọc JSON.
  - Ô bị fallback (nghi vietocr hallucination) và bảng bị nghi sai cấu trúc
    (cv2 cross-check) được TÔ MÀU riêng để soát nhanh, không phải dò từng ô.
  - (Tuỳ chọn) hiện kèm ảnh scan gốc của từng trang cạnh bản dựng lại, để đối
    chiếu trực quan 2 bên.

CÁCH DÙNG:
    # Chỉ cần JSON kết quả parse (đủ để xem cấu trúc dựng lại, không có ảnh gốc)
    python render_review_html.py --json FPT_BCTC_2024_parsed.json --out review.html

    # Kèm ảnh scan gốc để đối chiếu trực quan (cần pypdfium2 - đã có sẵn
    # trong requirements.txt, KHÔNG cần GPU/paddle/vietocr chạy)
    python render_review_html.py --json FPT_BCTC_2024_parsed.json \\
        --pdf data/raw/FPT/FPT_BCTC_2024.pdf --out review.html

Xuất ra .pdf thật (giữ đúng số trang) - 2 cách:
  1. Mở review.html bằng Chrome/Edge -> Ctrl+P -> "Save as PDF" (đơn giản nhất,
     không cần cài thêm gì).
  2. Tự động hoá bằng playwright (nếu đã có sẵn hoặc muốn cài thêm):
        pip install playwright && playwright install chromium
        python -c "from playwright.sync_api import sync_playwright; \\
            p = sync_playwright().start(); b = p.chromium.launch(); \\
            pg = b.new_page(); pg.goto('file://' + __import__('os').path.abspath('review.html')); \\
            pg.pdf(path='review.pdf', print_background=True); b.close(); p.stop()"
"""
import argparse
import base64
import html
import json
import os
from io import BytesIO


CSS = """
body { font-family: -apple-system, "Segoe UI", Roboto, Arial, sans-serif; background: #e9e9ee; margin: 0; }
.doc-header { padding: 16px 24px; background: #22232a; color: #fff; }
.doc-header h1 { margin: 0; font-size: 16px; }
.doc-header .sub { font-size: 12.5px; color: #b7b7c2; margin-top: 4px; }

.page {
  background: #fff; margin: 24px auto; max-width: 1400px; padding: 20px 24px;
  border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.15);
  page-break-after: always;
}
.page-head {
  display: flex; align-items: center; gap: 14px; font-size: 12.5px; color: #555;
  border-bottom: 1px solid #ddd; padding-bottom: 8px; margin-bottom: 14px; flex-wrap: wrap;
}
.page-head b { color: #111; }
.badge { padding: 2px 8px; border-radius: 10px; font-size: 11.5px; font-weight: 600; }
.badge.ok { background: #d9f2e6; color: #1b6b45; }
.badge.warn { background: #ffe9b8; color: #8a5b00; }
.badge.err { background: #ffd9d9; color: #a3241f; }

.error-banner {
  background: #ffe0e0; border: 1px solid #e88; color: #a3241f; padding: 10px 14px;
  border-radius: 6px; font-size: 13px; margin-bottom: 12px;
}

.split { display: flex; gap: 20px; align-items: flex-start; }
.split .orig { flex: 0 0 38%; }
.split .orig img { width: 100%; border: 1px solid #ccc; border-radius: 4px; }
.split .recon { flex: 1; min-width: 0; }

.recon-content { font-size: 13.5px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
.recon-content table {
  border-collapse: collapse; margin: 10px 0; font-size: 12.5px; white-space: normal;
}
.recon-content table td, .recon-content table th {
  border: 1px solid #999; padding: 4px 8px; vertical-align: top;
}
.recon-content table .ocr-flagged {
  background: #fff3b0 !important; outline: 2px solid #e0a64c; outline-offset: -2px;
}
.structure-warning {
  background: #ffe9b8; border: 1px solid #d99b2b; color: #6b4700; padding: 6px 10px;
  border-radius: 5px; font-size: 12px; margin: 6px 0;
}

@media print {
  body { background: #fff; }
  .page { box-shadow: none; margin: 0; border-radius: 0; }
}
"""


def render_page_preview_b64(pdf_path, page_index, dpi):
    """Render ảnh preview 1 trang PDF -> base64 JPEG (chỉ dùng pypdfium2 - nhẹ,
    KHÔNG cần GPU/paddle/vietocr). Trả về None nếu không render được."""
    try:
        import pypdfium2 as pdfium
        from PIL import Image
    except ImportError:
        return None
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        page = pdf[page_index]
        bitmap = page.render(scale=dpi / 72)
        pil_image = bitmap.to_pil().convert("RGB")
        buf = BytesIO()
        pil_image.save(buf, format="JPEG", quality=78)
        pdf.close()
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        print(f"  [!] Không render được ảnh preview trang {page_index + 1}: {e}")
        return None


def build_page_head(page_no, confidence, n_flagged_cells, structure_flags, error):
    parts = [f"<span>Trang <b>{page_no}</b></span>"]
    if error:
        parts.append('<span class="badge err">LỖI PARSE</span>')
    else:
        if confidence >= 0.999:
            parts.append('<span class="badge ok">native text (100%)</span>')
        elif confidence >= 0.85:
            parts.append(f'<span class="badge ok">confidence {confidence:.2f}</span>')
        else:
            parts.append(f'<span class="badge warn">confidence {confidence:.2f} - cần review</span>')
    if n_flagged_cells:
        parts.append(f'<span class="badge warn">{n_flagged_cells} ô bị flag nội dung</span>')
    if structure_flags:
        parts.append(f'<span class="badge warn">{len(structure_flags)} bảng nghi sai cấu trúc</span>')
    return '<div class="page-head">' + " ".join(parts) + "</div>"


def build_structure_warnings(structure_flags):
    if not structure_flags:
        return ""
    lines = []
    for chk in structure_flags:
        lines.append(
            f'<div class="structure-warning">⚠ cv2 đếm được <b>{chk["cv2_rows"]}</b> hàng x '
            f'<b>{chk["cv2_cols"]}</b> cột, nhưng paddle suy luận <b>{chk["paddle_rows"]}</b> hàng x '
            f'<b>{chk["paddle_cols"]}</b> cột - nên đối chiếu lại bảng này với ảnh gốc.</div>'
        )
    return "".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", required=True, help="File JSON do parse_pdf() xuất ra")
    ap.add_argument("--out", default="review.html")
    ap.add_argument("--pdf", default=None, help="(Tuỳ chọn) đường dẫn PDF gốc để hiện ảnh scan đối chiếu")
    ap.add_argument("--preview-dpi", type=int, default=110, help="DPI ảnh preview (thấp = nhẹ/nhanh, chỉ để xem)")
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as f:
        data = json.load(f)

    pages_markdown = data.get("pages_markdown", {})
    pages_confidence = data.get("pages_confidence", {})
    pages_error = data.get("pages_error", {})
    pages_flagged_cells = data.get("pages_flagged_cells", {})
    pages_structure_flags = data.get("pages_structure_flags", {})
    total_pages_declared = data.get("pages", len(pages_markdown))

    page_keys = sorted(pages_markdown.keys(), key=lambda k: int(k))

    # Kiểm tra ngay: số section HTML sắp dựng PHẢI khớp số trang gốc - đây là
    # yêu cầu cốt lõi ("đúng số trang tài liệu gốc"), không âm thầm bỏ qua.
    if len(page_keys) != total_pages_declared:
        print(
            f"[!] CẢNH BÁO: JSON khai báo {total_pages_declared} trang nhưng "
            f"pages_markdown chỉ có {len(page_keys)} trang - kiểm tra lại file JSON đầu vào."
        )

    sections = []
    for key in page_keys:
        page_no = int(key)
        markdown = pages_markdown[key]
        confidence = pages_confidence.get(key, pages_confidence.get(page_no, 0.0))
        error = pages_error.get(key, pages_error.get(page_no))
        flagged = pages_flagged_cells.get(key, pages_flagged_cells.get(page_no, []))
        structure_flags = pages_structure_flags.get(key, pages_structure_flags.get(page_no, []))

        head_html = build_page_head(page_no, confidence, len(flagged), structure_flags, error)
        warn_html = build_structure_warnings(structure_flags)
        error_html = f'<div class="error-banner">Lỗi khi parse trang này: {html.escape(error)}</div>' if error else ""

        # markdown đã LÀ chuỗi HTML hợp lệ (bảng thật + text thường) do
        # parser.py tự build - inject thẳng, KHÔNG escape lại (sẽ làm hỏng thẻ
        # <table> đã render sẵn). Rủi ro đã biết: nếu rác OCR vô tình chứa
        # ký tự "<"/"&" ngoài ngữ cảnh bảng, phần đó có thể hiển thị lệch -
        # chấp nhận được cho 1 công cụ review, không phải pipeline chính.
        recon_html = f'<div class="recon-content">{markdown}</div>' if markdown else "<i>(trang trống)</i>"

        img_b64 = None
        if args.pdf and confidence < 0.999:  # trang native text (1.0) không cần đối chiếu ảnh
            img_b64 = render_page_preview_b64(args.pdf, page_no - 1, args.preview_dpi)

        if img_b64:
            body = (
                '<div class="split">'
                f'<div class="orig"><img src="data:image/jpeg;base64,{img_b64}" alt="Trang {page_no} gốc"></div>'
                f'<div class="recon">{recon_html}</div>'
                "</div>"
            )
        else:
            body = recon_html

        sections.append(f'<section class="page">{head_html}{warn_html}{error_html}{body}</section>')

    doc_name = os.path.splitext(os.path.basename(args.json))[0]
    html_doc = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Review: {html.escape(doc_name)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="doc-header">
  <h1>📄 {html.escape(doc_name)}</h1>
  <div class="sub">{len(page_keys)} trang - {len(pages_flagged_cells)} trang có ô bị flag -
    {len(pages_structure_flags)} trang có bảng nghi sai cấu trúc -
    {len(pages_error)} trang lỗi parse</div>
</div>
{''.join(sections)}
</body>
</html>"""

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"\nĐã dựng {len(page_keys)}/{total_pages_declared} trang -> {args.out}")
    print("Mở file này bằng trình duyệt để xem. Muốn xuất .pdf: Ctrl+P -> Save as PDF "
          "(xem thêm cách tự động hoá bằng playwright trong docstring đầu file).")


if __name__ == "__main__":
    main()
