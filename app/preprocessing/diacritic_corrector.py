from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
import json
from pathlib import Path

def load_corrections_config(path: str | Path | None = None) -> dict:
    """Load word_fixes / token_fixes / whitelist từ JSON (nếu có)."""
    if path is None:
        path = Path(__file__).with_name("corrections_config.json")
    else:
        path = Path(path)
    if not path.exists():
        return {"word_fixes": {}, "token_fixes": {}, "whitelist": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "word_fixes": dict(data.get("word_fixes") or {}),
        "token_fixes": dict(data.get("token_fixes") or {}),
        "whitelist": list(data.get("whitelist") or []),
    }
_TABLE_SPAN_RE = re.compile(r"<table\b.*?</table>", re.DOTALL | re.IGNORECASE)

# Vietnamese financial-number shape used in the EDA notebook (§6):
#   -1.234.567,89   1.234   0,5   -12,34
_NUM_RE = re.compile(
    r"(?<![\w.])"  # not mid-token
    r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|"
    r"-?\d+,\d+"
    r"(?![\w.])"
)

# Placeholder that cannot collide with real OCR text (no digits/letters that
# a dictionary entry would match).
_NUM_PLACEHOLDER = "⟦NUM_{}⟧"
_NUM_PLACEHOLDER_RE = re.compile(r"⟦NUM_(\d+)⟧")


# ---------------------------------------------------------------------------
# High-confidence word-level OCR confusions observed in Vietnamese audited
# financial statements. Keys are the *erroneous* surface form (as OCR emits
# it); values are the corrected form. Keep this list precision-first: only
# add pairs that are essentially never legitimate words on their own in
# this domain. Case is matched case-insensitively; the replacement preserves
# the original token's capitalisation pattern when possible.
# ---------------------------------------------------------------------------
_DEFAULT_WORD_FIXES: dict[str, str] = {
    # d / đ stroke (extremely common OCR swap)
    "tai san": "tài sản",
    "tai sán": "tài sản",
    "tài san": "tài sản",
    "dong tien": "dòng tiền",
    "doanh thu": "doanh thu",  # identity kept as anchor; real errors below
    "doanh thu thuan": "doanh thu thuần",
    "loi nhuan": "lợi nhuận",
    "lợi nhuan": "lợi nhuận",
    "von chu so huu": "vốn chủ sở hữu",
    "von chu sở hữu": "vốn chủ sở hữu",
    "no phai tra": "nợ phải trả",
    "phai thu": "phải thu",
    "phai tra": "phải trả",
    "bang can doi ke toan": "bảng cân đối kế toán",
    "bao cao tai chinh": "báo cáo tài chính",
    "bao cao luu chuyen tien te": "báo cáo lưu chuyển tiền tệ",
    "thuyet minh": "thuyết minh",
    "thuyết minh bao cao tai chinh": "thuyết minh báo cáo tài chính",
    "kiem toan": "kiểm toán",
    "kiem toán": "kiểm toán",
    "ke toan": "kế toán",
    "kế toan": "kế toán",
    "tong giam doc": "tổng giám đốc",
    "giam doc": "giám đốc",
    "ke toan truong": "kế toán trưởng",
    "nguoi lap bieu": "người lập biểu",
    "co phan": "cổ phần",
    "co dong": "cổ đông",
    "dai hoi": "đại hội",
    "dai dien": "đại diện",
    "phap luat": "pháp luật",
    "trich lap": "trích lập",
    "du phong": "dự phòng",
    "khau hao": "khấu hao",
    "nguyen te": "nguyên tệ",
    "chenh lech": "chênh lệch",
    "ty gia": "tỷ giá",
    "lai suat": "lãi suất",
    "chi phi": "chi phí",
    "gia von": "giá vốn",
    "hang ton kho": "hàng tồn kho",
    "tai san co dinh": "tài sản cố định",
    "tai san dai han": "tài sản dài hạn",
    "tai san ngan han": "tài sản ngắn hạn",
    "no ngan han": "nợ ngắn hạn",
    "no dai han": "nợ dài hạn",
    "von dieu le": "vốn điều lệ",
    "thue thu nhap": "thuế thu nhập",
    "thue gia tri gia tang": "thuế giá trị gia tăng",
    "bao lanh": "bảo lãnh",
    "cam ket": "cam kết",
    "nghiep vu": "nghiệp vụ",
    "phat sinh": "phát sinh",
    "so du": "số dư",
    "so cai": "sổ cái",
    "but toan": "bút toán",
    "ket chuyen": "kết chuyển",
    "phan bo": "phân bổ",
    "danh gia": "đánh giá",
    "ghi nhan": "ghi nhận",
    "trinh bay": "trình bày",
    "ap dung": "áp dụng",
    "thong tu": "thông tư",
    "chuan muc": "chuẩn mực",
    "chuan mực ke toan": "chuẩn mực kế toán",
    "don vi": "đơn vị",
    "dong viet nam": "đồng Việt Nam",
    "trieu dong": "triệu đồng",
    "ty dong": "tỷ đồng",
}

# Single-token fixes applied only when the whole token matches (no spaces).
# Safer than multi-word phrase matching for short function words that OCR
# frequently strips diacritics from.
_DEFAULT_TOKEN_FIXES: dict[str, str] = {
    "tai": "tại",
    "cua": "của",
    "va": "và",
    "cac": "các",
    "cho": "cho",
    "voi": "với",
    "theo": "theo",
    "tu": "từ",
    "den": "đến",
    "tren": "trên",
    "duoi": "dưới",
    "trong": "trong",
    "ngoai": "ngoài",
    "nay": "này",
    "do": "đó",
    "khi": "khi",
    "neu": "nếu",
    "de": "để",
    "duoc": "được",
    "se": "sẽ",
    "da": "đã",
    "dang": "đang",
    "bi": "bị",
    "boi": "bởi",
    "ve": "về",
    "nhu": "như",
    "nhung": "những",
    "mot": "một",
    "hai": "hai",
    "nam": "năm",
    "ky": "kỳ",
    "quy": "quý",
    "thang": "tháng",
    "ngay": "ngày",
}


@dataclass(slots=True)
class DiacriticCorrectorConfig:
    """Toggles for :class:`DiacriticCorrector`."""

    enabled: bool = True
    config_path: str | None = None
    protect_numbers: bool = True
    apply_word_fixes: bool = True
    apply_token_fixes: bool = False  # off by default: higher false-positive risk
    # Extra user-supplied phrase fixes merged on top of the built-in list.
    extra_word_fixes: dict[str, str] = field(default_factory=dict)
    extra_token_fixes: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class DiacriticStats:
    """How many corrections were applied (for the quality scorecard)."""

    phrases_corrected: int = 0
    tokens_corrected: int = 0
    numbers_protected: int = 0

    def __iadd__(self, other: "DiacriticStats") -> "DiacriticStats":
        self.phrases_corrected += other.phrases_corrected
        self.tokens_corrected += other.tokens_corrected
        self.numbers_protected += other.numbers_protected
        return self


def _preserve_case(src: str, replacement: str) -> str:
    """Best-effort capitalisation transfer from ``src`` onto ``replacement``."""
    if not src:
        return replacement
    if src.isupper():
        return replacement.upper()
    if src[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement

class DiacriticCorrector:
    """Conservative Vietnamese diacritic / OCR-spelling corrector.

    Parameters
    ----------
    config:
        Feature toggles and optional extra dictionaries. All steps that
        rewrite text can be disabled independently.
    """

    def __init__(self, config: DiacriticCorrectorConfig | None = None) -> None:
        self.config = config or DiacriticCorrectorConfig()

        # 1) Load corrections_config.json (cạnh file này, hoặc config.config_path)
        file_cfg = load_corrections_config(
            getattr(self.config, "config_path", None)
        )

        # 2) Merge: default < JSON file < extra_* trên Config (extra thắng)
        word_fixes = {
            **_DEFAULT_WORD_FIXES,
            **{k.lower(): v for k, v in file_cfg.get("word_fixes", {}).items()},
            **{k.lower(): v for k, v in self.config.extra_word_fixes.items()},
        }
        # Longest phrase first so "tai san co dinh" wins over "tai san".
        self._word_fixes_sorted = sorted(
            word_fixes.items(), key=lambda kv: len(kv[0]), reverse=True
        )

        self._token_fixes = {
            **_DEFAULT_TOKEN_FIXES,
            **{k.lower(): v for k, v in file_cfg.get("token_fixes", {}).items()},
            **{k.lower(): v for k, v in self.config.extra_token_fixes.items()},
        }

        # 3) Whitelist: viết tắt / tên DN — không bao giờ auto-correct
        self._whitelist: set[str] = {
            w.lower() for w in file_cfg.get("whitelist", [])
        } | {
            w.lower() for w in getattr(self.config, "extra_whitelist", ()) or ()
        }

    def correct(self, text: str) -> tuple[str, DiacriticStats]:
        """Correct ``text`` and return ``(corrected_text, stats)``.

        Table spans are passed through unchanged. Numeric tokens are
        placeholder-protected for the duration of the rewrite when
        ``config.protect_numbers`` is True.
        """
        stats = DiacriticStats()
        if not self.config.enabled or not text:
            return text, stats

        segments = self._split_preserving_tables(text)
        out: list[str] = []
        for segment, is_table in segments:
            if is_table:
                out.append(segment)
                continue
            fixed, seg_stats = self._correct_segment(segment)
            stats += seg_stats
            out.append(fixed)
        return "".join(out), stats

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

    def _correct_segment(self, text: str) -> tuple[str, DiacriticStats]:
        stats = DiacriticStats()
        protected = text
        num_vault: list[str] = []

        if self.config.protect_numbers:
            def _stash(m: re.Match[str]) -> str:
                num_vault.append(m.group(0))
                return _NUM_PLACEHOLDER.format(len(num_vault) - 1)

            protected = _NUM_RE.sub(_stash, text)
            stats.numbers_protected = len(num_vault)

        if self.config.apply_word_fixes:
            protected, n = self._apply_word_fixes(protected)
            stats.phrases_corrected += n

        if self.config.apply_token_fixes:
            protected, n = self._apply_token_fixes(protected)
            stats.tokens_corrected += n

        if num_vault:
            def _restore(m: re.Match[str]) -> str:
                idx = int(m.group(1))
                return num_vault[idx] if 0 <= idx < len(num_vault) else m.group(0)

            protected = _NUM_PLACEHOLDER_RE.sub(_restore, protected)

        return protected, stats

    def _apply_word_fixes(self, text: str) -> tuple[str, int]:
        """Replace known multi-word (and single-word) OCR error phrases.

        Matching is case-insensitive; replacement preserves the source
        token's capitalisation. Count = number of successful substitutions.
        Whitelisted tokens are never rewritten as a whole word match.
        """
        count = 0
        lines = text.split("\n")
        out_lines: list[str] = []
        for line in lines:
            lower = line.lower()
            result: list[str] = []
            i = 0
            while i < len(line):
                matched = False
                for err, fix in self._word_fixes_sorted:
                    end = i + len(err)
                    if end > len(line):
                        continue
                    # Boundary: phrase bounded by non-letters (or edges)
                    if i > 0 and (line[i - 1].isalpha() or line[i - 1].lower() == "đ"):
                        continue
                    if end < len(line) and (line[end].isalpha() or line[end].lower() == "đ"):
                        continue
                    if lower[i:end] != err:
                        continue
                    # Skip if the matched span is a whitelisted token
                    if err in self._whitelist:
                        continue
                    original_slice = line[i:end]
                    result.append(_preserve_case(original_slice, fix))
                    i = end
                    count += 1
                    matched = True
                    break
                if not matched:
                    result.append(line[i])
                    i += 1
            out_lines.append("".join(result))
        return "\n".join(out_lines), count

    def _apply_token_fixes(self, text: str) -> tuple[str, int]:
        """Whole-token (whitespace-delimited) dictionary pass.

        Whitelisted tokens (tctd, ctck, nhnn, ...) are left unchanged.
        """
        count = 0
        parts = re.split(r"(\s+)", text)
        out: list[str] = []
        for part in parts:
            if not part or part.isspace():
                out.append(part)
                continue
            # Strip trailing punctuation for lookup, then reattach.
            m = re.match(r"^([\wÀ-ỹĐđ]+)(.*)$", part)
            if not m:
                out.append(part)
                continue
            core, tail = m.group(1), m.group(2)
            key = core.lower()
            if key in self._whitelist:
                out.append(part)
                continue
            if key in self._token_fixes:
                out.append(_preserve_case(core, self._token_fixes[key]) + tail)
                count += 1
            else:
                out.append(part)
        return "".join(out), count