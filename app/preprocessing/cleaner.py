from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_TABLE_SPAN_RE = re.compile(r"<table\b.*?</table>", re.DOTALL | re.IGNORECASE)
_REPEATED_PUNCT_RE = re.compile(r"([^\w\s])\1{2,}")
_OCR_ARTIFACT_CHARS_RE = re.compile("[\x0b\x0c\ufeff\u200b\u200c\u200d\ufffd]")
_MULTI_BLANK_LINE_RE = re.compile(r"\n{3,}")
_INLINE_WHITESPACE_RE = re.compile(r"[ \t]+")

_CJK_RE = re.compile(
    "["
    "\u4e00-\u9fff"
    "\u3400-\u4dbf"
    "\uf900-\ufaff"
    "\u3040-\u30ff"
    "\u3000-\u303f"
    "\uff00-\uffef"
    "]"
)

_LATEX_ARTIFACT_RE = re.compile(r"\\\(|\\\)|\\[a-zA-Z]{2,}")

_EMPTY_IMAGE_RE = re.compile(
    r"(?i)\b("
    r"the image contains no text|"
    r"the image contains no text or content|"
    r"the image contains no text or characters|"
    r"blank rectangular box|"
    r"no visible content|"
    r"it is a blank rectangular box"
    r").*"
)

_DIGITAL_SIGNATURE_RE = re.compile(
    r"(?i)("
    r"digitally signed by|"
    r"foxit pdf reader|"
    r"oid\.0\.9\.2342|"
    r"reason:\s*i am the author|"
    r"dn:\s*c=vn|"
    r"\bMST\s*:\s*\d{8,15}\b|"
    r"\bE\s*=\s*[\w.\-+]+@[\w.\-]+|"
    r"\bDate\s*:\s*\d{4}[./-]\d{1,2}[./-]\d{1,2}|"
    r"\bCN\s*=\s*|"
    r"\bOID\.\d|"
    r"\bS\s*=\s*TP\b|"
    r"\bL\s*=\s*\"|"
    r"Location\s*:\s*$"
    r").*"
)

_SEQUENTIAL_NUMBERS_RE = re.compile(r"^\s*(?:\d{1,3}\s+){8,}\d{1,3}\s*$")

_STAMP_SOUP_RE = re.compile(
    r"^(?:"
    r"[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]{1,4}"
    r"(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ0-9\-]{1,6}){0,4}"
    r")$"
)
_VIET_LATIN_LETTER_RE = re.compile(
    r"[A-Za-zÀ-Ỹà-ỹĂăÂâÊêÔôƠơƯưĐđ]"
)
_MATH_OCR_CHAR_RE = re.compile(
    "[\u0370-\u03FF\u1F00-\u1FFF∂∑∏√∞≈≠≤≥±×÷·∙∆∇∥]"
)
_PAGE_NUMBER_RE = re.compile(r"^\s*\d{1,3}\s*$")
_MIN_CONTENT_LINE_LEN = 7


@dataclass(slots=True)
class CleaningConfig:
    normalize_whitespace: bool = True
    normalize_unicode: bool = True
    remove_duplicate_blank_lines: bool = True
    remove_ocr_artifact_chars: bool = True
    collapse_repeated_punctuation: bool = True
    remove_watermark_lines: bool = True
    remove_garbage_lines: bool = True
    remove_repeated_consecutive_lines: bool = True
    remove_symbol_only_lines: bool = True
    remove_cjk_chars: bool = True
    remove_gibberish_lines: bool = True
    remove_ocr_noise_phrases: bool = True
    remove_trailing_short_lines: bool = True
    unicode_form: str = "NFC"
    garbage_char_dominance_ratio: float = 0.85
    garbage_min_line_length: int = 6
    watermark_min_repeats: int = 3
    gibberish_min_tokens: int = 4
    gibberish_single_char_token_ratio: float = 0.6
    gibberish_min_line_length: int = 6
    trailing_min_content_len: int = _MIN_CONTENT_LINE_LEN


@dataclass(slots=True)
class CleaningStats:
    artifact_chars_removed: int = 0
    punctuation_runs_collapsed: int = 0
    watermark_lines_removed: int = 0
    garbage_lines_removed: int = 0
    duplicate_consecutive_lines_removed: int = 0
    symbol_noise_lines_removed: int = 0
    cjk_chars_removed: int = 0
    gibberish_lines_removed: int = 0
    ocr_noise_phrases_removed: int = 0
    trailing_short_lines_removed: int = 0

    def __iadd__(self, other: "CleaningStats") -> "CleaningStats":
        self.artifact_chars_removed += other.artifact_chars_removed
        self.punctuation_runs_collapsed += other.punctuation_runs_collapsed
        self.watermark_lines_removed += other.watermark_lines_removed
        self.garbage_lines_removed += other.garbage_lines_removed
        self.duplicate_consecutive_lines_removed += (
            other.duplicate_consecutive_lines_removed
        )
        self.symbol_noise_lines_removed += other.symbol_noise_lines_removed
        self.cjk_chars_removed += other.cjk_chars_removed
        self.gibberish_lines_removed += other.gibberish_lines_removed
        self.ocr_noise_phrases_removed += other.ocr_noise_phrases_removed
        self.trailing_short_lines_removed += other.trailing_short_lines_removed
        return self


def _is_ocr_noise_phrase_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _EMPTY_IMAGE_RE.search(stripped):
        return True
    if _DIGITAL_SIGNATURE_RE.search(stripped):
        return True
    if _SEQUENTIAL_NUMBERS_RE.match(stripped):
        return True
    if len(stripped) <= 24 and _STAMP_SOUP_RE.match(stripped):
        lower = stripped.lower()
        if any(w in lower for w in ("công ty", "báo cáo", "bảng", "mục", "năm")):
            return False
        letters = [ch for ch in stripped if ch.isalpha()]
        if letters and sum(1 for ch in letters if ch.isupper()) / len(letters) >= 0.85:
            return True
    return False


def _is_garbage_line(line: str, config: CleaningConfig) -> bool:
    stripped = line.strip()
    if len(stripped) < config.garbage_min_line_length:
        return False
    compact = stripped.replace(" ", "")
    if not compact:
        return False
    counts: dict[str, int] = {}
    for ch in compact:
        counts[ch] = counts.get(ch, 0) + 1
    dominant_char = max(counts, key=counts.get)
    if dominant_char.isalpha():
        return False
    return max(counts.values()) / len(compact) >= config.garbage_char_dominance_ratio


def _is_watermark_line(line: str, config: CleaningConfig) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    tokens = stripped.split()
    if len(tokens) < config.watermark_min_repeats:
        return False
    first = tokens[0].lower()
    run = 1
    for tok in tokens[1:]:
        if tok.lower() != first:
            break
        run += 1
    return run >= config.watermark_min_repeats and run == len(tokens)


def _is_gibberish_line(line: str, config: CleaningConfig) -> bool:
    stripped = line.strip()
    if len(stripped) < config.gibberish_min_line_length:
        return False
    if _LATEX_ARTIFACT_RE.search(stripped):
        return True
    tokens = stripped.split()
    if len(tokens) < config.gibberish_min_tokens:
        return False
    single = sum(1 for tok in tokens if len(tok.strip(".,()-–")) <= 1)
    return single / len(tokens) >= config.gibberish_single_char_token_ratio

def _letter_count(s: str) -> int:
    return len(_VIET_LATIN_LETTER_RE.findall(s))


def _is_natural_number_line(stripped: str) -> bool:
    return bool(re.fullmatch(r"\d+", stripped))


def _is_low_alpha_garbage(stripped: str, max_letters: int = 4) -> bool:
    if not stripped:
        return False
    if _is_natural_number_line(stripped):
        return False
    return _letter_count(stripped) <= max_letters and len(stripped) >= 4

def _is_stamp_or_footer_garbage(stripped: str) -> bool:
    if re.match(r"^\d{4,}\.?$", stripped):
        return True
    if re.match(r"^\d{4,}\.?\s+\S", stripped) and len(stripped) <= 24:
        return True
    if len(stripped) <= 20 and _STAMP_SOUP_RE.match(stripped):
        return True
    return False


def _is_symbol_only_line(stripped: str) -> bool:
    return bool(stripped) and all(
        not ch.isalnum() and not ch.isspace() for ch in stripped
    )

def _is_math_ocr_garbage(stripped: str) -> bool:
    if not stripped:
        return False
    if _MATH_OCR_CHAR_RE.search(stripped):
        return True
    if stripped.count("|") >= 2 and len(stripped) <= 48:
        if _letter_count(stripped) <= 3:
            return True
    return False

class OCRCleaner:
    """Làm sạch text OCR từng page; giữ nguyên HTML <table>."""

    def __init__(self, config: CleaningConfig | None = None) -> None:
        self.config = config or CleaningConfig()

    def clean(self, text: str) -> tuple[str, CleaningStats]:
        stats = CleaningStats()
        segments = self._split_preserving_tables(text)

        out: list[str] = []
        for segment, is_table in segments:
            if is_table:
                out.append(segment)
                continue
            cleaned, seg_stats = self._clean_segment(segment)
            stats += seg_stats
            out.append(cleaned)

        result = "".join(out)

        if self.config.remove_duplicate_blank_lines:
            result = _MULTI_BLANK_LINE_RE.sub("\n\n", result)

        if self.config.remove_trailing_short_lines:
            result, n = self._clean_trailing_short_lines(
                result, min_len=self.config.trailing_min_content_len
            )
            stats.trailing_short_lines_removed += n
            stats.garbage_lines_removed += n

        return result, stats

    @staticmethod
    def _split_preserving_tables(text: str) -> list[tuple[str, bool]]:
        segments: list[tuple[str, bool]] = []
        last_end = 0
        for match in _TABLE_SPAN_RE.finditer(text):
            if match.start() > last_end:
                segments.append((text[last_end : match.start()], False))
            segments.append((match.group(0), True))
            last_end = match.end()
        if last_end < len(text):
            segments.append((text[last_end:], False))
        return segments

    def _clean_segment(self, text: str) -> tuple[str, CleaningStats]:
        cfg = self.config
        stats = CleaningStats()

        if cfg.normalize_unicode:
            text = unicodedata.normalize(cfg.unicode_form, text)

        if cfg.remove_ocr_artifact_chars:
            text, n = _OCR_ARTIFACT_CHARS_RE.subn("", text)
            stats.artifact_chars_removed += n

        if cfg.remove_cjk_chars:
            text, n = _CJK_RE.subn("", text)
            stats.cjk_chars_removed += n

        if cfg.collapse_repeated_punctuation:
            text, n = _REPEATED_PUNCT_RE.subn(r"\1", text)
            stats.punctuation_runs_collapsed += n

        if cfg.normalize_whitespace:
            text = "\n".join(
                _INLINE_WHITESPACE_RE.sub(" ", line).rstrip()
                for line in text.split("\n")
            )

        kept: list[str] = []
        prev_normalized: str | None = None

        for line in text.split("\n"):
            stripped = line.strip()

            if cfg.remove_symbol_only_lines and _is_symbol_only_line(stripped):
                stats.symbol_noise_lines_removed += 1
                continue

            if cfg.remove_ocr_noise_phrases and _is_ocr_noise_phrase_line(line):
                stats.ocr_noise_phrases_removed += 1
                continue

            if cfg.remove_garbage_lines and _is_garbage_line(line, cfg):
                stats.garbage_lines_removed += 1
                continue

            if cfg.remove_watermark_lines and _is_watermark_line(line, cfg):
                stats.watermark_lines_removed += 1
                continue

            if cfg.remove_gibberish_lines and _is_gibberish_line(line, cfg):
                stats.gibberish_lines_removed += 1
                continue

            if _PAGE_NUMBER_RE.match(stripped):
                stats.garbage_lines_removed += 1
                continue

            if _is_stamp_or_footer_garbage(stripped):
                stats.garbage_lines_removed += 1
                continue

            if _is_math_ocr_garbage(stripped):
                stats.garbage_lines_removed += 1
                continue

            if _is_low_alpha_garbage(stripped):
                stats.garbage_lines_removed += 1
                continue

            if cfg.remove_repeated_consecutive_lines:
                normalized = stripped.lower()
                if normalized and normalized == prev_normalized:
                    stats.duplicate_consecutive_lines_removed += 1
                    continue
                if normalized:
                    prev_normalized = normalized

            kept.append(line)

        return "\n".join(kept), stats

    @staticmethod
    def _clean_trailing_short_lines(
        text: str, min_len: int = _MIN_CONTENT_LINE_LEN
    ) -> tuple[str, int]:
        """Từ cuối page dò ngược: xóa dòng trống / dòng < min_len
        đến khi gặp dòng dài >= min_len.
        """
        if not text or not text.strip():
            return text, 0

        lines = text.split("\n")
        idx = len(lines) - 1
        removed = 0

        def _is_trailing_stamp_caps(stripped: str) -> bool:
            """Rác stamp cuối page: ngắn + gần như toàn hoa."""
            if not stripped or len(stripped) > 20:
                return False
            letters = [ch for ch in stripped if ch.isalpha()]
            if len(letters) < 2:
                return False
            upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
            return upper_ratio >= 0.85

        while idx >= 0:
            stripped = lines[idx].strip()
            if not stripped or len(stripped) < min_len:
                removed += 1
                idx -= 1
                continue
            break

        if removed == 0:
            return text, 0

        return "\n".join(lines[: idx + 1]).rstrip("\n"), removed