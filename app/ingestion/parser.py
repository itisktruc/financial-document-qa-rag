"""
app/ingestion/parser.py

Entry point ingestion: parse 1 file PDF tài chính -> dict output chuẩn hoá
cho app/ingestion/chunker.py.

Chiến lược hiện tại (document-level, chưa phải per-page hybrid):
  - has_text_layer() lấy mẫu vài trang để đoán PDF có text layer thật hay
    là ảnh scan thuần.
  - Có text layer  -> Docling (DocumentConverter), giữ nguyên nhánh cũ
    (source="docling_native").
  - Không có text layer (scan) -> render từng trang thành ảnh, OCR bằng
    Qwen3-VL. Đây là điểm THAY ĐỔI CHÍNH so với bản trước: bỏ hoàn toàn
    pipeline PPStructureV3 (subprocess riêng, venv riêng /opt/venv-paddle)
    + VietOCR per-cell, theo kết quả thử nghiệm tốt ở
    qwen3vl_ocr_colab.ipynb.

Vì sao bỏ được subprocess isolation: PaddlePaddle-GPU và PyTorch từng phải
tách process vì tranh CUDA context (Paddle âm thầm fallback CPU nếu Torch
init CUDA trước). Qwen3-VL chạy hoàn toàn qua transformers/PyTorch, không
còn Paddle trong pipeline nữa -> hết xung đột, có thể gỡ paddlepaddle-gpu /
paddleocr / paddlex khỏi requirements.txt và xoá ppv3_worker.py.

Khác biệt quan trọng với chunker.py so với bản cũ: nhánh OCR giờ trả
"pages_markdown" (markdown RIÊNG cho từng trang, do Qwen3-VL tự nhận diện
heading/bảng) thay vì "pages_text" (text thô, không có cấu trúc). Nhờ vậy
nhánh OCR có citation theo trang CHÍNH XÁC hơn cả nhánh docling_native
(xem _blocks_from_pages_markdown trong chunker.py).
"""

from __future__ import annotations

import locale
import os
import sys
import io
import requests
import json

# ---------------------------------------------------------------------------
# Ép UTF-8 TOÀN CỤC ngay khi module này được import -- TRƯỚC bất kỳ import
# nào khác (pypdfium2, docling, và về sau là torch/transformers trong
# _load_qwen_model()).
#
# NGUYÊN NHÂN THẬT SỰ của lỗi "'ascii' codec can't encode character ...":
# reconfigure sys.stdout/sys.stderr (bản cũ) chỉ sửa được I/O ra console.
# Nhưng exception thực tế bị bắt trong vòng lặp OCR (_parse_with_qwen_vlm)
# không đến từ print() của parser.py -- nó đến từ SÂU BÊN TRONG
# transformers/huggingface_hub: các thư viện này tự mở file cache/log bằng
# open(path, "w") KHÔNG chỉ định encoding, nên Python dùng
# locale.getpreferredencoding() làm mặc định. Trên máy này hàm đó trả về
# "ascii" (không phải cp1252 như Windows hay có) -> bất kỳ ký tự tiếng Việt
# có dấu nào (vd 'ỉ' = U+1EC9) ghi qua đường này đều crash, và bị try/except
# trong vòng lặp OCR nuốt lại thành lỗi chung chung cho MỌI trang.
#
# Monkeypatch locale.getpreferredencoding() ở đây (trước khi torch/
# transformers được import, kể cả import trễ/lazy) để mọi open() phía sau
# không chỉ định encoding đều mặc định ra "utf-8" thay vì "ascii".
# ---------------------------------------------------------------------------
locale.getpreferredencoding = lambda do_setlocale=True: "utf-8"

# Set thêm để mọi subprocess con (nếu có thư viện nào spawn subprocess) cũng
# kế thừa UTF-8 mode, phòng trường hợp monkeypatch ở trên không phủ hết.
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def _ensure_utf8_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass  # môi trường không cho reconfigure (vd stdout bị redirect đặc biệt) -> bỏ qua, không chặn pipeline


_ensure_utf8_stdio()

from functools import lru_cache
from typing import Optional

import pypdfium2 as pdfium
from docling.document_converter import DocumentConverter

VAST_OCR_URL = os.getenv("VAST_OCR_URL", "http://localhost:8000/ocr")


# ---------------------------------------------------------------------------
# Config (đọc trực tiếp từ env cho gọn; có thể chuyển sang app/config.py
# / Pydantic Settings sau khi config.py được triển khai đầy đủ)
# ---------------------------------------------------------------------------

TEXT_LAYER_SAMPLE_PAGES = int(os.getenv("PARSER_TEXT_LAYER_SAMPLE_PAGES", "3"))
TEXT_LAYER_MIN_CHARS = int(os.getenv("PARSER_TEXT_LAYER_MIN_CHARS", "20"))

# Mặc định model 2B vì máy local đang dùng GTX 1660 (6GB VRAM) -- đổi sang
# 4B/8B qua biến môi trường khi chạy trên máy/Colab có nhiều VRAM hơn (đã
# test 4B ổn định trên Colab T4 15GB trong qwen3vl_ocr_colab.ipynb).
QWEN_MODEL_ID = os.getenv("QWEN_OCR_MODEL_ID", "Qwen/Qwen3-VL-4B-Instruct")
QWEN_OCR_DPI = int(os.getenv("QWEN_OCR_DPI", "200"))
QWEN_OCR_MAX_NEW_TOKENS = int(os.getenv("QWEN_OCR_MAX_NEW_TOKENS", "4096"))
QWEN_OCR_LOAD_4BIT = os.getenv("QWEN_OCR_LOAD_4BIT", "false").lower() == "true"
QWEN_OCR_MIN_PIXELS = 256 * 28 * 28
QWEN_OCR_MAX_PIXELS = 1280 * 28 * 28

OCR_PROMPT = (
    "Bạn là một công cụ OCR chuyên nghiệp cho tài liệu tài chính tiếng Việt. "
    "Hãy trích xuất TOÀN BỘ nội dung văn bản trong hình ảnh này, giữ nguyên tiếng Việt có dấu.\n"
    "Yêu cầu:\n"
    "1. Giữ nguyên cấu trúc bảng biểu bằng định dạng Markdown table (| cột 1 | cột 2 | ...).\n"
    "2. Giữ nguyên số liệu chính xác, không làm tròn, không tự sửa số.\n"
    "3. Giữ đúng thứ tự đọc từ trên xuống, trái sang phải, kể cả tiêu đề/đề mục.\n"
    "4. Không thêm bình luận, giải thích hay tóm tắt -- chỉ xuất nội dung đã OCR.\n"
    "5. Nếu có chú thích/footnote thì đặt ở cuối.\n"
    "6. Dùng '#', '##', '###' cho tiêu đề/đề mục nếu nhận ra cấp bậc, để giữ cấu trúc tài liệu.\n"
    "7. Hãy tự động xoay và đọc nội dung văn bản theo đúng chiều đọc tự nhiên nếu trang ảnh bị lật ngược hoặc nghiêng."
)
# Yêu cầu (6) thêm so với bản gốc trong notebook: nhắc Qwen3-VL dùng markdown
# heading nhất quán, để app/ingestion/chunker.py (heading-aware) nhận diện
# đúng cấp mục lục thay vì coi cả trang là 1 khối text phẳng.


# ---------------------------------------------------------------------------
# Bước 0: kiểm tra PDF có text layer thật hay là ảnh scan thuần
# ---------------------------------------------------------------------------

def has_text_layer(
    pdf_path: str,
    sample_pages: int = TEXT_LAYER_SAMPLE_PAGES,
    min_chars: int = TEXT_LAYER_MIN_CHARS,
) -> bool:
    """Kiểm tra nhanh: PDF có text layer thật hay là ảnh scan thuần."""
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        pages_to_check = min(sample_pages, len(pdf))
        text_found = 0
        for i in range(pages_to_check):
            page = pdf[i]
            textpage = page.get_textpage()
            text = textpage.get_text_range().strip()
            if len(text) >= min_chars:
                text_found += 1
        return text_found >= (pages_to_check // 2 + 1)
    finally:
        pdf.close()


# ---------------------------------------------------------------------------
# Nhánh text-layer: Docling
# ---------------------------------------------------------------------------

def _parse_with_docling(pdf_path: str) -> dict:
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return {
        "source": "docling_native",
        "markdown": result.document.export_to_markdown(),
        "tables": result.document.tables,
        "pages": result.document.num_pages(),
        "pages_error": {},
    }


# ---------------------------------------------------------------------------
# Nhánh scan: Qwen3-VL (thay thế hoàn toàn PPStructureV3 + VietOCR)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _render_page_to_pil(pdf_path: str, page_index: int, dpi: int):
    """Render 1 trang PDF thành PIL Image, giữ trong bộ nhớ (không ghi PNG
    ra đĩa) -- theo nguyên tắc in-memory processing đã áp dụng cho pipeline."""
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        page = pdf[page_index]
        bitmap = page.render(scale=dpi / 72)
        return bitmap.to_pil().convert("RGB")
    finally:
        pdf.close()


def _ocr_page_with_qwen(pil_image, max_new_tokens: int = QWEN_OCR_MAX_NEW_TOKENS) -> str:
    """
    Thay vì chạy model cục bộ, hàm này sẽ nén ảnh thành bytes, 
    gửi POST request lên Google Colab (GPU T4) và nhận về kết quả Markdown.
    """
    # Chuyển PIL Image thành định dạng JPEG bytes để truyền qua mạng
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format="JPEG", quality=95)
    img_byte_arr.seek(0)

    files = {"file": ("page.jpg", img_byte_arr, "image/jpeg")}
    data = {"prompt": OCR_PROMPT}

    try:
        # Gửi request lên Colab (timeout 180s cho mỗi trang tài liệu phức tạp)
        response = requests.post(VAST_OCR_URL, files=files, data=data, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        return result.get("markdown", "")
    except Exception as e:
        raise RuntimeError(f"Lỗi kết nối tới Colab OCR Server: {e}")

def _parse_with_qwen_vlm(pdf_path: str, dpi: int = QWEN_OCR_DPI) -> dict:
    import traceback

    pdf = pdfium.PdfDocument(pdf_path)
    num_pages = len(pdf)
    pdf.close()

    pages_markdown: dict[int, str] = {}
    pages_error: dict[int, str] = {}

    for i in range(num_pages):
        page_num = i + 1
        try:
            pil_image = _render_page_to_pil(pdf_path, i, dpi)
            pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
            print(f"Đang OCR Qwen3-VL ở trang {page_num}/{num_pages}")
        except Exception as e:
            # QUAN TRỌNG: không được nuốt lỗi âm thầm -- đây chính là bug cũ
            # (pages_error bị swallow, cả trang trả về rỗng + confidence 0.0
            # mà không rõ lý do). Luôn ghi rõ trang nào lỗi + loại lỗi gì.
            #
            # DEBUG: lưu full traceback (không chỉ str(e)) -- str(e) không
            # cho biết dòng/file nào thực sự ném lỗi encode ascii, mà lỗi
            # này gần như chắc chắn xảy ra SÂU bên trong 1 thư viện phụ
            # thuộc (transformers/huggingface_hub/pdfium), không phải ở
            # chính parser.py. Cần traceback để tìm đúng chỗ mới vá được.
            tb_str = traceback.format_exc()
            pages_markdown[page_num] = ""
            pages_error[page_num] = f"{type(e).__name__}: {e}\n{tb_str}"
            # dùng try/except khi in log phòng trường hợp _ensure_utf8_stdio()
            # vẫn không reconfigure được (vd stdout bị pipe/redirect đặc
            # biệt) -- không để việc IN LOG bị lỗi làm crash cả vòng lặp OCR.
            try:
                print(f"[parser] Lỗi OCR Qwen3-VL ở trang {page_num}/{num_pages}: {e}")
                print(tb_str)
            except UnicodeEncodeError:
                safe_msg = f"[parser] Loi OCR Qwen3-VL o trang {page_num}/{num_pages}: {e}"
                print(safe_msg.encode("ascii", "replace").decode())
                print(tb_str.encode("ascii", "replace").decode())

    return {
        "source": "qwen_vlm",
        "pages_markdown": pages_markdown,
        "pages": num_pages,
        "pages_error": pages_error,
        "model_id": QWEN_MODEL_ID,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: str) -> dict:
    """
    Entry point chính: parse 1 file PDF -> dict output chuẩn cho
    app/ingestion/chunker.chunk_document().

        from app.ingestion.parser import parse_pdf
        from app.ingestion.chunker import chunk_document

        parsed = parse_pdf("data/raw/FPT/FPT_BCTC_2024.pdf")
        chunks = chunk_document(parsed, document_id="FPT_BCTC_2024")

    - Có text layer      -> source="docling_native" (markdown gộp cả file,
      CHƯA có số trang theo từng đoạn -- hạn chế đã biết).
    - Scan (không có text layer) -> source="qwen_vlm" (markdown THEO TỪNG
      TRANG, có số trang chính xác cho từng heading/đoạn/bảng).
    """
    if has_text_layer(pdf_path):
        return _parse_with_docling(pdf_path)
    return _parse_with_qwen_vlm(pdf_path)


# ---------------------------------------------------------------------------
# Xuất markdown dễ đọc cho con người (KHÔNG dùng cho chunker.py -- chỉ để
# mở file .md lên xem/rà soát chất lượng OCR bằng mắt, giống bước cuối của
# qwen3vl_ocr_colab.ipynb)
# ---------------------------------------------------------------------------

def export_markdown(parsed: dict) -> str:
    """
    Ghép output của parse_pdf() thành 1 chuỗi markdown liền mạch, dễ đọc:
      - source="qwen_vlm": mỗi trang 1 heading "## Trang N", các trang cách
        nhau bằng "---" (đúng format bước 6 trong notebook), kèm cảnh báo
        ngay tại chỗ nếu trang đó nằm trong pages_error (không phải lục JSON
        riêng mới biết trang nào OCR lỗi).
      - source="docling_native": trả thẳng markdown đã có sẵn (docling đã
        gộp thành 1 khối, không tách theo trang).
    """
    source = parsed.get("source")

    if source == "docling_native":
        return parsed.get("markdown", "")

    pages_markdown = parsed.get("pages_markdown")
    if source == "qwen_vlm" or pages_markdown is not None:
        pages_markdown = pages_markdown or {}
        pages_error = parsed.get("pages_error") or {}
        parts = []
        for page_key in sorted(pages_markdown.keys(), key=lambda k: int(k)):
            page_num = int(page_key)
            page_md = (pages_markdown[page_key] or "").strip()
            header = f"## Trang {page_num}"
            err = pages_error.get(page_key) or pages_error.get(page_num) or pages_error.get(str(page_num))
            if err:
                header += f"\n\n> ⚠️ **LỖI OCR ở trang này:** {err}"
            body = page_md if page_md else "*(trang rỗng / OCR không trả về nội dung)*"
            parts.append(f"{header}\n\n{body}")
        return "\n\n---\n\n".join(parts)

    # nhánh cũ pages_text (paddleocr) hoặc nguồn lạ khác -> vẫn cố xuất được
    pages_text = parsed.get("pages_text")
    if pages_text:
        parts = [
            f"## Trang {int(k)}\n\n{(v or '').strip()}"
            for k, v in sorted(pages_text.items(), key=lambda kv: int(kv[0]))
        ]
        return "\n\n---\n\n".join(parts)

    return parsed.get("markdown", "")


def save_markdown(parsed: dict, output_path: str) -> str:
    """Xuất + lưu markdown dễ đọc ra file (vd data/processed/xxx_ocr.md),
    trả về chính output_path để tiện in log."""
    markdown = export_markdown(parsed)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return output_path

