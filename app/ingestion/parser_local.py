"""
Parse one financial PDF into a normalized dict for chunker.py.

Strategy (document-level, not per-page hybrid):
  - Text layer present  -> Docling  (source="docling_native")
  - Scanned pages only  -> Qwen3-VL local inference (source="qwen_vlm")

The OCR branch returns per-page text so citation can be page-accurate.
"""

from __future__ import annotations

import locale
import os
import sys
import traceback
from functools import lru_cache
from typing import Any

import pypdfium2 as pdfium
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

TEXT_LAYER_SAMPLE_PAGES = int(os.getenv("PARSER_TEXT_LAYER_SAMPLE_PAGES", "3"))
TEXT_LAYER_MIN_CHARS = int(os.getenv("PARSER_TEXT_LAYER_MIN_CHARS", "20"))

QWEN_MODEL_ID = os.getenv("QWEN_OCR_MODEL_ID", "Qwen/Qwen3-VL-2B-Instruct")
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
    "6. Dùng '#', '##', '###' cho tiêu đề/đề mục nếu nhận ra cấp bậc, để giữ cấu trúc tài liệu."
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

    if hasattr(doc, "export_to_text"):
        content = doc.export_to_text()
    else:
        content = doc.export_to_markdown()

    return {
        "source": "docling_native",
        "text": content,
        "pages": doc.num_pages(),
        "pages_error": {},
    }


# ---------------------------------------------------------------------------
# Qwen3-VL branch (scanned PDFs, local inference)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_qwen_model():
    """Load model + processor once per process."""
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    kwargs: dict[str, Any] = {"dtype": "auto", "device_map": "auto"}

    if QWEN_OCR_LOAD_4BIT:
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
    processor = AutoProcessor.from_pretrained(
        QWEN_MODEL_ID,
        min_pixels=QWEN_OCR_MIN_PIXELS,
        max_pixels=QWEN_OCR_MAX_PIXELS,
    )
    return model, processor


def _render_page_to_pil(pdf_path: str, page_index: int, dpi: int):
    """Render a single page to an in-memory RGB PIL image."""
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        bitmap = pdf[page_index].render(scale=dpi / 72)
        return bitmap.to_pil().convert("RGB")
    finally:
        pdf.close()


def _ocr_page_with_qwen(pil_image, max_new_tokens: int = QWEN_OCR_MAX_NEW_TOKENS) -> str:
    """Run Qwen3-VL on one page image; return text."""
    import torch
    from qwen_vl_utils import process_vision_info

    model, processor = _load_qwen_model()

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": pil_image},
                {"type": "text", "text": OCR_PROMPT},
            ],
        }
    ]
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)

    trimmed = [
        out_ids[len(in_ids) :]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    return processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]


def _parse_with_qwen_vlm(pdf_path: str, dpi: int = QWEN_OCR_DPI) -> dict[str, Any]:
    pdf = pdfium.PdfDocument(pdf_path)
    num_pages = len(pdf)
    pdf.close()

    pages_text: dict[int, str] = {}
    pages_error: dict[int, str] = {}

    for i in range(num_pages):
        page_num = i + 1
        try:
            image = _render_page_to_pil(pdf_path, i, dpi)
            pages_text[page_num] = _ocr_page_with_qwen(image)
            print(f"[parser] OCR page {page_num}/{num_pages}")
        except Exception as e:
            tb = traceback.format_exc()
            pages_text[page_num] = ""
            pages_error[page_num] = f"{type(e).__name__}: {e}\n{tb}"
            _safe_print(f"[parser] OCR failed on page {page_num}/{num_pages}: {e}")
            _safe_print(tb)

    return {
        "source": "qwen_vlm",
        "pages_text": pages_text,
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

    pages_text = parsed.get("pages_text")
    if source == "qwen_vlm" or pages_text is not None:
        pages_text = pages_text or {}
        pages_error = parsed.get("pages_error") or {}
        parts = []

        for key in sorted(pages_text, key=lambda k: int(k)):
            page_num = int(key)
            body = (pages_text[key] or "").strip()
            header = f"===== PAGE {page_num} ====="

            err = (
                pages_error.get(key)
                or pages_error.get(page_num)
                or pages_error.get(str(page_num))
            )
            if err:
                body = f"[LỖI OCR ở trang này: {err}]\n\n" + body

            if not body:
                body = "(trang rỗng / OCR không trả về nội dung)"
            parts.append(f"{header}\n{body}")

        return "\n\n".join(parts)

    return parsed.get("text", "")


def save_text(parsed: dict, output_path: str) -> str:
    """Write export_text() result to disk; return output_path."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(export_text(parsed))
    return output_path