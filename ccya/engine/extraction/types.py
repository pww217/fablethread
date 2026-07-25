"""Typed data structures for the extraction pipeline.

Replaces `dict[str, Any]` containers with proper TypedDicts to eliminate
defensive `.get()` chaining (F4) and improve type safety.
"""

from __future__ import annotations

from typing import Any, TypedDict


class ContextMeta(TypedDict, total=False):
    """Context metadata written by all extraction streams."""
    system_text: str
    user_text: str
    system_chars: int
    user_chars: int
    total_chars: int
    est_tokens: int
    trimmed: bool
    trimmed_chars: int


class StreamResult(TypedDict, total=False):
    """Result shape for a single extraction stream (scene, state, record)."""
    output: Any
    skipped: bool
    attempts: int
    retry_errors: list[str]
    tokens_in: int
    tokens_out: int
    ms: float
    context_meta: ContextMeta
    error: str


class NarrateResultDict(TypedDict):
    """Result shape for the narration stream."""
    output: str
    tokens_in: int
    tokens_out: int
    ms: float


class SanitizeResultDict(TypedDict):
    """Result shape for the sanitize step."""
    ms: float
    skipped: bool


class WorldResultDict(TypedDict):
    """Result shape for the world step."""
    output: list[dict[str, Any]]
    skipped: bool
    tokens_in: int
    tokens_out: int
    ms: float


class CompDedupRedirect(TypedDict):
    """Shape of a compendium dedup redirect entry."""
    original_id: str
    redirected_to: str
    name: str
