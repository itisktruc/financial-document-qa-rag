"""
Parse one financial PDF into a normalized dict for chunker.py.

Strategy (document-level, not per-page hybrid):
  - Text layer present  -> Docling  (source="docling_native")
  - Scanned pages only  -> Qwen3-VL via remote OCR server (source="qwen_vlm")

The OCR branch returns per-page markdown so citation can be page-accurate.
"""

from __future__ import annotations

import io
import locale
import os
import sys
import traceback
from functools import lru_cache
from typing import Any

import pypdfium2 as pdfium
import requests
from docling.document_converter import DocumentConverter

locale.getpreferredencoding = lambda do_setlocale=True: "utf-8"
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def _ensure_utf8_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


_ensure_utf8_stdio()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VAST_OCR_URL = os.getenv("VAST_OCR_URL", "http://localhost:8000/ocr")

TEXT_LAYER_SAMPLE_PAGES = int(os.getenv("PARSER_TEXT_LAYER_SAMPLE_PAGES", "3"))
TEXT_LAYER_MIN_CHARS = int(os.getenv("PARSER_TEXT_LAYER_MIN_CHARS", "20"))

QWEN_MODEL_ID = os.getenv("QWEN_OCR_MODEL_ID", "Qwen/Qwen3-VL-4B-Instruct")
QWEN_OCR_DPI = int(os.getenv("QWEN_OCR_DPI", "200"))
QWEN_OCR_MAX_NEW_TOKENS = int(os.getenv("QWEN_OCR_MAX_NEW_TOKENS", "4096"))

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
    "7. Hãy tự động xoay và đọc nội dung văn bản theo đúng chiều đọc tự nhiên "
    "nếu trang ảnh bị lật ngược hoặc nghiêng."
)


# ---------------------------------------------------------------------------
# Text-layer detection
# ---------------------------------------------------------------------------

def has_text_layer(
    pdf_path: str,
    sample_pages: int = TEXT_LAYER_SAMPLE_PAGES,
    min_chars: int = TEXT_LAYER_MIN_CHARS,
) -> bool:
    """Return True if a majority of sampled pages contain real text."""
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        n = min(sample_pages, len(pdf))
        hits = 0
        for i in range(n):
            text = pdf[i].get_textpage().get_text_range().strip()
            if len(text) >= min_chars:
                hits += 1
        return hits >= (n // 2 + 1)
    finally:
        pdf.close()


# ---------------------------------------------------------------------------
# Docling branch (native text layer)
# ---------------------------------------------------------------------------

def _parse_with_docling(pdf_path: str) -> dict[str, Any]:
    result = DocumentConverter().convert(pdf_path)
    doc = result.document
    return {
        "source": "docling_native",
        "text": doc.export_to_text(),
        "pages": doc.num_pages(),
        "pages_error": {},
    }


# ---------------------------------------------------------------------------
# Qwen3-VL branch (scanned PDFs, remote OCR)
# ---------------------------------------------------------------------------

def _render_page_to_pil(pdf_path: str, page_index: int, dpi: int):
    """Render a single page to an in-memory RGB PIL image."""
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        bitmap = pdf[page_index].render(scale=dpi / 72)
        return bitmap.to_pil().convert("RGB")
    finally:
        pdf.close()


def _ocr_page_with_qwen(pil_image) -> str:
    """Send page image to the remote OCR server; return markdown text."""
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG", quality=95)
    buf.seek(0)

    try:
        resp = requests.post(
            VAST_OCR_URL,
            files={"file": ("page.jpg", buf, "image/jpeg")},
            data={"prompt": OCR_PROMPT},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json().get("markdown", "")
    except Exception as e:
        raise RuntimeError(f"OCR server error ({VAST_OCR_URL}): {e}") from e


def _parse_with_qwen_vlm(pdf_path: str, dpi: int = QWEN_OCR_DPI) -> dict[str, Any]:
    pdf = pdfium.PdfDocument(pdf_path)
    num_pages = len(pdf)
    pdf.close()

    text: dict[int, str] = {}
    pages_error: dict[int, str] = {}

    for i in range(num_pages):
        page_num = i + 1
        try:
            image = _render_page_to_pil(pdf_path, i, dpi)
            text[page_num] = _ocr_page_with_qwen(image)
            print(f"[parser] OCR page {page_num}/{num_pages}")
        except Exception as e:
            tb = traceback.format_exc()
            text[page_num] = ""
            pages_error[page_num] = f"{type(e).__name__}: {e}\n{tb}"
            _safe_print(f"[parser] OCR failed on page {page_num}/{num_pages}: {e}")
            _safe_print(tb)

    return {
        "source": "qwen_vlm",
        "text": text,
        "pages": num_pages,
        "pages_error": pages_error,
        "model_id": QWEN_MODEL_ID,
    }


def _safe_print(msg: str) -> None:
    """Print without crashing if stdout is not UTF-8."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_pdf(pdf_path: str) -> dict[str, Any]:
    if has_text_layer(pdf_path):
        return _parse_with_docling(pdf_path)
    return _parse_with_qwen_vlm(pdf_path)

def export_text(parsed: dict) -> str:
    source = parsed.get("source")

    if source == "docling_native":
        return parsed.get("text", "")

    text = parsed.get("text")
    if source == "qwen_vlm" or text is not None:
        text = text or {}
        pages_error = parsed.get("pages_error") or {}
        parts = []

        for key in sorted(text, key=lambda k: int(k)):
            page_num = int(key)
            body = (text[key] or "").strip()
            header = f"===== PAGE {page_num} ====="

            err = (
                pages_error.get(key)
                or pages_error.get(page_num)
                or pages_error.get(str(page_num))
            )
            if err:
                body = f"[LỖI OCR ở trang này: {err}]\n\n" + body

            parts.append(f"{header}\n{body}")

        return "\n\n".join(parts)

    return parsed.get("text", "")


def save_text(parsed: dict, output_path: str) -> str:
    """Write export_text() result to disk; return output_path."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(export_text(parsed))
    return output_path