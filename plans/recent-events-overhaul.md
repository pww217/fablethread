# Plan: Recent Events Overhaul

## Problem

`recent_events` in scene state is a flat list of strings. The current deduplication logic
in `engine.py` (`_fact_in_list`) compares events by normalizing them to lowercase and
checking word equality:

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

This is the wrong tool: near-identical strings don't match, slightly rephrased strings do.
The result is false merges and duplicate events living side by side.

### Root cause

The extractor has no stable reference to compare against when writing events. It sees
narration text and tries to emit strings, with no IDs to anchor identity across turns.
The `summarize_changes()` diff in `engine.py` suffers from the same problem — it compares
previous and current event lists by string content, making the diff unreliable.

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

State schema:

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

**`StateDelta`** — update event fields:

- `recent_events_add: list[RecentEvent]` — new events with fresh IDs
- `recent_events_update: list[RecentEvent]` — revised text for an existing ID
- `recent_events_remove: list[str]` — IDs to remove (not content strings)

Extractor prompt instruction:
> Assign a stable `snake_case` ID to each new event. To update an existing event's text,
> emit it under `recent_events_update` using its existing ID. To remove an event, emit its
> ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

### `apply_delta` changes

**`ccya/state.py`** — update `apply_delta()`:

1. `recent_events_add`: append new objects; reject if ID already exists
2. `recent_events_update`: find by ID, replace `text` only
3. `recent_events_remove`: filter out by ID
4. Eviction (max events): sort by `turn` ascending, drop oldest

### `summarize_changes()` deduplication fix

**`ccya/engine.py`** — replace fuzzy norm comparison with exact ID comparison:

```python
pre_event_ids = {e["id"] for e in pre_events if isinstance(e, dict)}
post_event_ids = {e["id"] for e in post_events if isinstance(e, dict)}
# added = post_event_ids - pre_event_ids
# removed = pre_event_ids - post_event_ids
```

`_fact_in_list` and `_norm_fact` in `engine.py` are deleted entirely once this lands.
The `_fact_in_list` / `_norm_fact` functions in `state.py` are **untouched** — they
serve a different purpose there.

### Template changes

Narrate and extract templates that render `recent_events` currently iterate over strings.
Update to iterate over objects and render `event.text`. The `id` and `turn` fields are
metadata — do not render them to the LLM in prose contexts, use them for diff/dedup only.

---

## Migration

Existing saves with string `recent_events` lists get a one-time upgrade at `load_state()`:

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

---

## Relationship to other plans

- **`reconciliation-system.md`** handles cross-domain state contradictions (item in both
  add and remove lists, etc.). Event-specific ID conflicts (duplicate `recent_events_add`
  IDs) are handled here in `apply_delta`, not in reconciliation.
- **`entity-dedup.md`** covers the same ID + alias pattern for inventory and NPCs.
  `recent_events` uses the same ID discipline but simpler — events are never aliased,
  only added, updated, or removed by ID.
