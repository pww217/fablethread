"""Inventory normalization and resolution helpers.

ID convention:
  Inventory items have canonical IDs defined at seed time (e.g., "iron_coins",
  "brass_key"). The LLM extracts items by natural-language names from narration
  (e.g., "credits", "Iron Coins", "brass key"). The normalization pipeline
  bridges this gap:

    1. normalize_inventory_id(raw) — Lowercase, strip, replace hyphens/spaces
       with underscores, remove non-alphanumeric. Maps "Iron Coins" -> "iron_coins".
    2. resolve_inventory_canonical_id(raw, inventory) — Normalize raw, then
       match against canonical IDs and alias lists.
    3. resolve_inventory_remove_target(raw, inventory) — Same as above but also
       matches against item names (fallback for items without aliases).
    4. _fuzzy_match_inventory(name, inventory) — Token-overlap scoring for
       detecting duplicates during inventory_add (threshold 0.6).

  Conditions do NOT currently have equivalent normalization — Phase 04 of
  eval-engine-fixes-02.md plans to add normalize_condition_id() mirroring
  this pattern. See plans/eval-engine-fixes-02.md.
"""

from __future__ import annotations

import logging
import re
from typing import Any

_log = logging.getLogger(__name__)


def normalize_inventory_id(raw: str) -> str:
    if not isinstance(raw, str):
        raw = str(raw)
    s = raw.lower().strip()
    s = re.sub(r"[\-\s]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s or "_"


def resolve_inventory_canonical_id(
    inventory: list[dict[str, Any]], raw_id: str
) -> str | None:
    want = normalize_inventory_id(raw_id)
    for it in inventory:
        if normalize_inventory_id(it.get("id", "")) == want:
            _log.debug("resolve_inventory_canonical_id raw=%s -> %s", raw_id, it["id"])
            return str(it["id"])
        for alias in (it.get("aliases") or []):
            if isinstance(alias, str) and normalize_inventory_id(alias) == want:
                _log.debug("resolve_inventory_canonical_id raw=%s -> %s (via alias %s)", raw_id, it["id"], alias)
                return str(it["id"])
    _log.debug("resolve_inventory_canonical_id raw=%s normalized=%s no match", raw_id, want)
    return None


def resolve_inventory_remove_target(
    inventory: list[dict[str, Any]], raw_id: str
) -> str | None:
    c = resolve_inventory_canonical_id(inventory, raw_id)
    if c:
        return c
    want = normalize_inventory_id(raw_id)
    for it in inventory:
        nm = it.get("name")
        if isinstance(nm, str) and normalize_inventory_id(nm) == want:
            return str(it["id"])
    return None


def _fuzzy_match_inventory(name: str, inventory: list[dict[str, Any]]) -> str | None:
    """Returns canonical ID if `name` is a likely duplicate of an existing item.

    Uses token overlap — no external dependencies. Threshold 0.6.
    If all incoming tokens are contained in the candidate, uses containment score.
    """
    name_tokens = set(name.lower().split())
    if not name_tokens:
        return None
    best_id, best_score = None, 0.0
    for item in inventory:
        if not isinstance(item, dict):
            continue
        candidate_tokens: set[str] = set()
        item_name = item.get("name", "")
        if isinstance(item_name, str):
            candidate_tokens |= set(item_name.lower().split())
        for alias in (item.get("aliases") or []):
            if isinstance(alias, str):
                candidate_tokens |= set(alias.lower().split())
        if not candidate_tokens:
            continue
        overlap = len(name_tokens & candidate_tokens)
        if name_tokens.issubset(candidate_tokens):
            # Full containment: incoming is a subset of existing (e.g. "dagger" in "worn dagger")
            score = overlap / len(name_tokens)
        else:
            score = overlap / max(len(name_tokens), len(candidate_tokens))
        if score > best_score:
            best_score = score
            best_id = item["id"]
    return best_id if best_score >= 0.6 else None
