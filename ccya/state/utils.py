"""State package shared utility helpers."""

from __future__ import annotations

import re

_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]")


def is_named(name: str) -> bool:
    """Heuristic: a proper name has 2+ words with first and last capitalized."""
    if not name:
        return False
    words = name.strip().split()
    if len(words) < 2:
        return False
    first_word = words[0]
    last_word = words[-1]
    return bool(first_word and first_word[0].isupper() and last_word and last_word[0].isupper())


def strip_non_ascii(text: str) -> str:
    """Strip non-ASCII characters from text."""
    if not text:
        return text
    return _NON_ASCII_RE.sub("", text).strip()
