# Plan: Recent Events Overhaul

## Problem

`recent_events` in scene state is a flat list of strings. The current deduplication logic in `engine.py` (`_fact_in_list`) compares events by normalizing them to lowercase and checking word equality:

```python
def _norm_fact(s: Any) -> str:
    return " ".join(str(s or "").lower().split())

def _fact_in_list(needle: str, haystack: list[Any]) -> bool:
    hn = _norm_fact(needle)
    for h in haystack:
        if _norm_fact(h) == hn:
            return True
    return False
```

This is doing semantic comparison at the string level, which is the wrong tool for the job. The result:

- **False positives**: two distinct events that happen to share most words get silently merged (e.g. "The guard left the room" and "The guard left the building" normalize to different strings, but slight rephrasing — "The guard has left" vs. "The guard left" — can collide).
- **False negatives**: the same event rephrased by the LLM on a retry or re-extraction doesn't match its original and gets added as a duplicate.
- **No edit path**: because events are matched by content, there's no reliable way to update an existing event without the risk of creating a duplicate.

### Why PbtA-style event tracking is cleaner

In tabletop PbtA, the GM's move list is a *discrete set of named outcomes*, not a prose log. Each move has an identity independent of how it's worded. The equivalent here is: every `recent_event` should have a stable ID that the extractor assigns, so "event X was updated" is a clean operation rather than a string-match gamble.

---

## Proposed Design

### Structured event objects

Replace the string list with a list of small objects:

```python
# models.py
class RecentEvent(BaseModel):
    id: str           # stable snake_case identifier, e.g. "guard_left_room"
    text: str         # human-readable prose
    turn: int         # turn added (for age-based eviction ordering)
```

The state schema becomes:

```yaml
scene:
  recent_events:
    - id: guard_left_room
      text: "The guard left the room and locked the door behind him."
      turn: 4
    - id: player_found_key
      text: "You found a brass key under the floorboards."
      turn: 5
```

### Extractor changes

**`StateDelta` / `ProgressExtractResult`** — update the event fields:

- `recent_events_add: list[RecentEvent]` — new events with fresh IDs
- `recent_events_update: list[RecentEvent]` — revised text for an existing ID
- `recent_events_remove: list[str]` — IDs to remove (not content strings)

The extractor prompt instructs:
> Assign a stable `snake_case` ID to each new event. To update an existing event's text, emit it under `recent_events_update` using its existing ID. To remove an event, emit its ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

### `apply_delta` changes

**`ccya/state.py`** — update `apply_delta()` to:

1. On `recent_events_add`: append new event objects, reject if ID already exists.
2. On `recent_events_update`: find by ID, replace `text` field only.
3. On `recent_events_remove`: filter out by ID.
4. Eviction (max events): sort by `turn` ascending, drop oldest.

### Deduplication

`_fact_in_list` and `_norm_fact` are deleted entirely. The `summarize_changes()` diff in `engine.py` compares by event ID, not content:

```python
pre_event_ids = {e["id"] for e in pre_events if isinstance(e, dict)}
post_event_ids = {e["id"] for e in post_events if isinstance(e, dict)}
# added = post - pre
# removed = pre - post
```

### Template changes

Narrate and extract templates that render `recent_events` currently iterate over strings. Update to iterate over objects and render `event.text`. The `id` and `turn` fields are metadata — don't render them to the LLM in prose contexts, only use them for diff/dedup logic.

---

## Migration

- Existing saves with string `recent_events` lists need a one-time migration: read each string, generate a deterministic ID from it (slugify first 6 words), set `turn: 0`.
- Add a migration helper in `ccya/state.py`:

```python
def migrate_recent_events(state: dict) -> dict:
    """Upgrade string recent_events to object form in-place."""
    events = (state.get("scene") or {}).get("recent_events") or []
    if events and isinstance(events[0], str):
        import re
        def _slugify(s: str) -> str:
            words = re.sub(r"[^a-z0-9 ]", "", s.lower()).split()[:6]
            return "_".join(words) or "event"
        state["scene"]["recent_events"] = [
            {"id": _slugify(e), "text": e, "turn": 0}
            for e in events
        ]
    return state
```

Call this at `load_state()` time as a transparent upgrade.
