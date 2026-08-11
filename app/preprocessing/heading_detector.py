from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_ROMAN_RE = re.compile(
    r"^\s*(M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))\s*[\.\)]\s+\S"
)
_ROMAN_TOKEN_RE = re.compile(r"^\s*([IVXLCDM]+)\s*[\.\)]")

_DECIMAL_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*[\.\)]?\s+\S")
_DECIMAL_TOKEN_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)")

_MIN_TITLE_LEN = 8
_MAX_TITLE_LEN = 90
_MIN_CAPS_WORDS = 2

_HEADING_BLACKLIST = frozenset(
    {
        "có",
        "không",
        "v",
        "x",
        "yes",
        "no",
        "ok",
        "chủ tịch",
        "chủ tịch hđqt",
        "chủ tịch hội đồng quản trị",
        "tổng giám đốc",
        "phó tổng giám đốc",
        "kế toán trưởng",
        "kế toán trường",
        "người lập biểu",
        "giám đốc",
        "thành viên",
        "phó chủ tịch",
    }
)

_HEADING_DENY_SUBSTR = (
    "digitally signed",
    "foxit pdf",
    "the image contains",
    "blank rectangular",
    "oid.0.9",
    "mst:",
    "@gmail",
    "http://",
    "https://",
)


def _roman_to_int(token: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(token.upper()):
        val = values.get(ch, 0)
        total += -val if val < prev else val
        prev = max(prev, val)
    return total


@dataclass(slots=True)
class HeadingCandidate:
    text: str
    level: int
    numbering: str | None
    line_index: int


class HeadingDetector:
    def __init__(self, caps_title_max_words: int = 10) -> None:
        self.caps_title_max_words = caps_title_max_words
        self._stack: list[tuple[int, str]] = []

    def reset_hierarchy(self) -> None:
        self._stack = []

    def current_path(self) -> tuple[str, ...]:
        """Path hiện tại — dùng để gắn section cho paragraph/list/table."""
        return tuple(text for _, text in self._stack)

    def recognize_line(self, line: str, line_index: int) -> HeadingCandidate | None:
        stripped = line.strip()
        if not stripped:
            return None

        lower = stripped.lower()
        if lower in _HEADING_BLACKLIST:
            return None
        if any(deny in lower for deny in _HEADING_DENY_SUBSTR):
            return None
        if re.fullmatch(r"[vVxX×✓✔☐☑]\s*", stripped):
            return None

        if _ROMAN_RE.match(stripped):
            token_match = _ROMAN_TOKEN_RE.match(stripped)
            token = token_match.group(1) if token_match else ""
            value = _roman_to_int(token)
            if 0 < value <= 50:
                return HeadingCandidate(
                    text=stripped, level=1, numbering=token, line_index=line_index
                )

        if _DECIMAL_RE.match(stripped):
            token_match = _DECIMAL_TOKEN_RE.match(stripped)
            token = token_match.group(1) if token_match else ""
            body = re.sub(r"^\s*\d+(?:\.\d+)*\s*[\.\)]?\s*", "", stripped)
            if len(re.sub(r"\s+", "", body)) < 3:
                return None
            depth = token.count(".") + 1
            return HeadingCandidate(
                text=stripped, level=depth + 1, numbering=token, line_index=line_index
            )

        if self._looks_like_caps_title(stripped):
            return HeadingCandidate(
                text=stripped, level=1, numbering=None, line_index=line_index
            )

        return None

    def _looks_like_caps_title(self, line: str) -> bool:
        if not (_MIN_TITLE_LEN <= len(line) <= _MAX_TITLE_LEN):
            return False
        words = line.split()
        if len(words) < _MIN_CAPS_WORDS or len(words) > self.caps_title_max_words:
            return False
        letters = [ch for ch in line if ch.isalpha()]
        if len(letters) < _MIN_TITLE_LEN:
            return False
        uppercase_letters = sum(1 for ch in letters if ch.isupper())
        if (uppercase_letters / len(letters)) < 0.95:
            return False
        if line.strip().lower() in _HEADING_BLACKLIST:
            return False
        return True

    def resolve_path(self, candidate: HeadingCandidate) -> tuple[str, ...]:
        while self._stack and self._stack[-1][0] >= candidate.level:
            self._stack.pop()
        self._stack.append((candidate.level, candidate.text))
        return tuple(text for _, text in self._stack)