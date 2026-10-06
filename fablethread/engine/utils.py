"""Shared utility helpers for engine and state modules."""

from __future__ import annotations

import re
from typing import Any

_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]")
_CONDITION_PUNCT = ("*", "_", "`", ".", ",", ";", ":", "!", "?")


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


def coerce_condition_str(v: Any) -> Any:
    if isinstance(v, str):
        cid = v.lower().strip().replace(" ", "_")
        for ch in _CONDITION_PUNCT:
            cid = cid.replace(ch, "")
        cid = "_".join(cid.split()) or "condition"
        return {"id": cid, "label": v.strip()}
    return v
