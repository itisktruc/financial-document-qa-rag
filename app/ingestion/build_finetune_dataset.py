"""
build_finetune_dataset.py

Trích xuất crop ảnh (chữ ngoài bảng + từng ô bảng) từ các PDF trong data/raw/
để chuẩn bị dataset fine-tune vietocr đọc bảng biểu tài chính tốt hơn.

QUAN TRỌNG: script này TÁI SỬ DỤNG ĐÚNG logic render (OCR_DPI), lọc bbox nhiễu
(_bbox_too_small, _bbox_is_likely_punch_hole) và NHẤT LÀ đúng hàm crop
(p._crop_for_recognition - ưu tiên get_rotate_crop_image theo polygon quad
nếu có, fallback _crop_axis_aligned nếu không) đang có trong parser.py -
KHÔNG viết lại logic cắt ảnh riêng. Lý do: nếu ảnh dùng để fine-tune được cắt
theo 1 cách khác so với lúc chạy thật, model học được trên 1 phân bố ảnh khác
với ảnh nó sẽ thấy lúc inference -> fine-tune xong vẫn không cải thiện, đây
là lỗi rất hay gặp và khó phát hiện. Bản trước của script này TỰ CẮT ẢNH
RIÊNG (hàm _crop_bbox cục bộ, chỉ dùng CROP_PADDING_PX cố định) - đây chính
là nguyên nhân khiến crop "cắt ngang mất chữ" mà không hề khớp với cách
parser.py thực sự cắt (đã có polygon quad + đệm không đều) - ĐÃ SỬA.

CHIẾN LƯỢC LẤY MẪU (không lấy hết mọi bbox của mọi trang - sẽ ra hàng triệu
ảnh, phần lớn dư thừa):
  - Ô bảng bị coi là "khó" (điều kiện y hệt logic fallback trong
    parser.py._fill_table_html: vietocr rỗng dù paddle có chữ, HOẶC
    prob < CONF_FALLBACK_THRESHOLD, HOẶC khớp _is_suspicious_hallucination)
    -> LẤY HẾT, vì đây chính xác là các trường hợp model đang yếu, có giá trị
    huấn luyện cao nhất.
  - Ô bảng "bình thường" + chữ ngoài bảng -> chỉ lấy 1 mẫu ngẫu nhiên
    (--sample-normal-rate) để dataset vẫn có ví dụ "dễ", tránh model chỉ học
    toàn ca khó rồi quên mất cách đọc chữ bình thường (catastrophic forgetting
    cục bộ).

CÁCH DÙNG:
    python build_finetune_dataset.py \
        --data-dirs data/raw/FPT data/raw/Vinamilk data/raw/TheGioiDiDong data/raw/HoaPhat \
        --out-dir dataset_finetune \
        --max-pages-per-doc 30 \
        --max-docs-per-company 5 \
        --sample-normal-rate 0.08

    Khuyến nghị: chạy thử với --max-docs-per-company nhỏ (2-3) trước để ước
    lượng thời gian/số lượng crop, rồi mới chạy full (mỗi trang cần 1 lượt gọi
    PPStructureV3 thật qua worker - CHI PHÍ TƯƠNG ĐƯƠNG lúc parse tài liệu thật,
    không hề rẻ, với hàng chục PDF có thể mất nhiều giờ).

KẾT QUẢ:
    dataset_finetune/
      images/*.png     - ảnh crop đã cắt sẵn (đúng cách parser.py sẽ cắt)
      manifest.csv      - metadata + nhãn GỢI Ý (vietocr_guess/paddle_guess),
                          cột "label" để TRỐNG - đây KHÔNG phải nhãn đúng, cần
                          gán nhãn thật bằng label_tool.html trước khi train.

Đặt file này CÙNG THƯ MỤC với parser.py (hoặc chỉnh IMPORT bên dưới cho khớp
cấu trúc project thật của bạn, vd `from app.ingestion import parser as p`).
"""
import argparse
import collections
import csv
import glob
import os
import random
import sys
import uuid

import numpy as np
from PIL import Image
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import parser as p  # đặt cùng thư mục với parser.py
except ImportError:
    from app.ingestion import parser as p  # fallback nếu chạy trong cấu trúc app/ingestion/

import pypdfium2 as pdfium

MANIFEST_FIELDS = [
    "image", "company", "source_pdf", "page", "kind", "priority", "crop_method",
    "vietocr_guess", "vietocr_prob", "paddle_guess", "label",
]


def _iter_pdfs_by_company(data_dirs, max_docs_per_company):
    """Duyệt PDF theo từng công ty (thư mục cha), giới hạn số file/công ty để
    lần chạy đầu không bị quá tải."""
    for d in data_dirs:
        company = os.path.basename(os.path.normpath(d))
        pdf_paths = sorted(glob.glob(os.path.join(d, "**", "*.pdf"), recursive=True))
        if max_docs_per_company is not None:
            pdf_paths = pdf_paths[:max_docs_per_company]
        for path in pdf_paths:
            yield company, path


def _save_row(rows, out_images_dir, company, doc_stem, page, kind, crop,
              vietocr_text, prob, paddle_text, priority, crop_method):
    fname = f"{company}_{doc_stem}_{page:03d}_{uuid.uuid4().hex[:8]}.png"
    Image.fromarray(crop).save(os.path.join(out_images_dir, fname))
    rows.append({
        "image": f"images/{fname}",
        "company": company,
        "source_pdf": doc_stem,
        "page": page,
        "kind": kind,
        "priority": priority,
        # "quad_warp" = ĐÃ THỰC SỰ dùng get_rotate_crop_image (polygon 4 điểm
        # thật từ PP-StructureV3, do parser.py._crop_for_recognition_with_method
        # BÁO CÁO LẠI CHÍNH XÁC - không phải suy đoán từ việc có truyền quad hay
        # không). "axis_aligned" = đã thực sự dùng crop bbox trục thẳng (luôn
        # đúng cho ô bảng - grid vốn thẳng trục; với text_box, nếu THẤY
        # "axis_aligned" Ở CẢ text_box, nghĩa là hoặc PP-StructureV3 trên máy
        # bạn không trả quad hợp lệ, hoặc quad đó suy biến thành hình chữ nhật
        # trục thẳng, hoặc cv2 không có/lỗi - kiểm tra lại field "dt_polys"/
        # "rec_boxes" thật trong ppv3_worker.py nếu muốn get_rotate_crop_image
        # thực sự phát huy tác dụng).
        "crop_method": crop_method,
        "vietocr_guess": vietocr_text,
        "vietocr_prob": round(prob, 4) if prob is not None else "",
        "paddle_guess": paddle_text,
        "label": "",  # để trống - gán nhãn thật bằng label_tool.html
    })


def process_pdf(pdf_path, company, out_images_dir, max_pages, sample_normal_rate, rows, stats):
    doc_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    try:
        pdf = pdfium.PdfDocument(pdf_path)
    except Exception as e:
        print(f"  [!] Không mở được file: {e}", flush=True)
        return
    num_pages = len(pdf)
    pages_done = 0

    for i in range(num_pages):
        if pages_done >= max_pages:
            break
        page = pdf[i]
        has_native, _ = p.has_text_layer(page)
        if has_native:
            # Trang có text layer thật -> parser.py không bao giờ đưa qua
            # vietocr, nên không có giá trị cho dataset fine-tune vietocr.
            continue

        img = p._render_page_array(page, p.OCR_DPI)
        try:
            structure = p._ppv3_worker.get_structure(img)
        except Exception as e:
            print(f"  [!] Trang {i + 1}: lỗi lấy structure - {e}", flush=True)
            continue
        if "error" in structure:
            print(f"  [!] Trang {i + 1}: {structure['error']}", flush=True)
            continue

        pages_done += 1
        page_width = img.shape[1]

        # ---- chữ ngoài bảng ----
        for tb in structure.get("text_boxes", []):
            bbox = tb["bbox"]
            quad = tb.get("quad")  # polygon 4 điểm nếu ppv3_worker.py giữ lại được
            if p._bbox_too_small(bbox) or p._bbox_is_likely_punch_hole(bbox, page_width=page_width):
                continue
            if random.random() > sample_normal_rate:
                continue
            # FIX (chính xác hoá crop_method): dùng _crop_for_recognition_with_method
            # để biết THẬT SỰ đã dùng quad_warp hay axis_aligned - suy đoán cũ
            # ("quad_warp" chỉ vì `quad is not None`) SAI khi _crop_region_with_method
            # tự rớt về axis_aligned bên trong (quad suy biến thành hình chữ nhật
            # trục thẳng, hoặc cv2 lỗi/không có, hoặc perspective crop rỗng) - lúc đó
            # nhãn "quad_warp" là sai, làm méo số liệu kiểm tra n_quad ở cuối script.
            crop, crop_method = p._crop_for_recognition_with_method(img, bbox, quad=quad)
            if crop is None:
                continue
            vietocr_text, prob = p._recognize_crop(img, bbox, quad=quad)
            _save_row(rows, out_images_dir, company, doc_stem, i + 1, "text_box", crop,
                      vietocr_text, prob, "", priority="normal",
                      crop_method=crop_method)
            stats["text_box"] += 1

        # ---- ô bảng: LẤY HẾT ô khó, lấy mẫu ô bình thường ----
        # (cell KHÔNG có quad - lưới bảng vốn thẳng trục, xem ppv3_worker.py -
        # luôn dùng fallback axis_aligned, đây là điều BÌNH THƯỜNG cho kind=table_cell)
        for tbl in structure.get("tables", []):
            pred_html = tbl.get("pred_html", "")
            cells = tbl.get("cells", [])
            if not pred_html or not cells:
                continue
            soup = BeautifulSoup(pred_html, "html.parser")
            cell_tags = soup.find_all(["td", "th"])
            if len(cell_tags) != len(cells):
                # Giống hệt điều kiện bail-out trong parser._fill_table_html -
                # không tin thứ tự cells khớp pred_html, bỏ qua cả bảng để
                # tránh gán nhầm bbox cho ô sai.
                continue

            for tag, cell in zip(cell_tags, cells):
                bbox = cell.get("bbox", [0, 0, 0, 0])
                if bbox == [0, 0, 0, 0] or p._bbox_too_small(bbox):
                    continue
                if p._bbox_is_likely_punch_hole(bbox, page_width=page_width):
                    continue

                paddle_text = tag.get_text(strip=True)
                vietocr_text, prob = p._recognize_crop(img, bbox)

                is_hard = (
                    (not vietocr_text and bool(paddle_text))
                    or prob < p.CONF_FALLBACK_THRESHOLD
                    or p._is_suspicious_hallucination(vietocr_text or "")
                )
                if not is_hard and random.random() > sample_normal_rate:
                    continue

                crop, crop_method = p._crop_for_recognition_with_method(img, bbox)
                if crop is None:
                    continue
                priority = "hard" if is_hard else "normal"
                _save_row(rows, out_images_dir, company, doc_stem, i + 1, "table_cell", crop,
                          vietocr_text, prob, paddle_text, priority=priority, crop_method=crop_method)
                stats["table_cell_hard" if is_hard else "table_cell_normal"] += 1

    pdf.close()


def main():
    ap = argparse.ArgumentParser(
        description="Trích xuất crop ảnh từ PDF để chuẩn bị dataset fine-tune vietocr."
    )
    ap.add_argument("--data-dirs", nargs="+", required=True,
                     help="Vd: data/raw/FPT data/raw/Vinamilk data/raw/TheGioiDiDong data/raw/HoaPhat")
    ap.add_argument("--out-dir", default="dataset_finetune")
    ap.add_argument("--max-pages-per-doc", type=int, default=30)
    ap.add_argument("--max-docs-per-company", type=int, default=5,
                     help="Giới hạn số PDF/công ty cho lần chạy thử đầu tiên. Đặt 0 = không giới hạn.")
    ap.add_argument("--sample-normal-rate", type=float, default=0.08,
                     help="Tỉ lệ lấy mẫu cho box/ô KHÔNG bị nghi vấn (0.08 = 8%%). Ô 'khó' luôn lấy hết.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    max_docs = None if args.max_docs_per_company == 0 else args.max_docs_per_company

    out_images_dir = os.path.join(args.out_dir, "images")
    os.makedirs(out_images_dir, exist_ok=True)

    rows = []
    stats = collections.Counter()
    company_pdfs = list(_iter_pdfs_by_company(args.data_dirs, max_docs))
    print(f"Sẽ xử lý {len(company_pdfs)} file PDF (giới hạn {max_docs or 'không giới hạn'} file/công ty).\n")

    for idx, (company, pdf_path) in enumerate(company_pdfs, 1):
        print(f"[{idx}/{len(company_pdfs)}] ({company}) {pdf_path}")
        try:
            process_pdf(pdf_path, company, out_images_dir, args.max_pages_per_doc,
                        args.sample_normal_rate, rows, stats)
        except Exception as e:
            print(f"  [!] Bỏ qua file này do lỗi: {e}", flush=True)
        print(f"  -> lũy kế: {len(rows)} crop "
              f"(hard={stats['table_cell_hard']}, table_normal={stats['table_cell_normal']}, "
              f"text_box={stats['text_box']})", flush=True)

    manifest_path = os.path.join(args.out_dir, "manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    n_quad = sum(1 for r in rows if r["crop_method"] == "quad_warp")
    n_text_box = sum(1 for r in rows if r["kind"] == "text_box")

    print(f"\n=== XONG ===")
    print(f"Tổng số crop: {len(rows)}")
    print(f"  - ô bảng 'khó' (ưu tiên gán nhãn trước): {stats['table_cell_hard']}")
    print(f"  - ô bảng bình thường (lấy mẫu):          {stats['table_cell_normal']}")
    print(f"  - chữ ngoài bảng (lấy mẫu):               {stats['text_box']}")
    print(f"Ảnh crop: {out_images_dir}")
    print(f"Manifest: {manifest_path}")

    print(f"\n[KIỂM TRA QUAN TRỌNG] Trong {n_text_box} crop 'text_box', có {n_quad} dùng được "
          f"quad_warp (get_rotate_crop_image).")
    if n_text_box > 0 and n_quad == 0:
        print(
            "  [!] CẢNH BÁO: 0/không có crop nào dùng quad_warp - nghĩa là PP-StructureV3 trên "
            "máy bạn KHÔNG trả polygon 4 điểm hợp lệ (dt_polys/rec_boxes), toàn bộ đang rơi về "
            "fallback axis_aligned - cơ chế crop mới CHƯA thực sự phát huy tác dụng. Kiểm tra lại "
            "cấu trúc thật của overall_ocr_res bằng cách in res.json ra 1 lần (xem ghi chú trong "
            "ppv3_worker.py) để xác nhận field nào đang thực sự tồn tại trên bản paddleocr bạn cài."
        )

    print(f"\nBước tiếp theo: mở label_tool.html, nạp thư mục '{out_images_dir}' + "
          f"file '{manifest_path}' để bắt đầu gán nhãn thật.")


if __name__ == "__main__":
    main()