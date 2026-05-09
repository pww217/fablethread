# Plan: Compactor Recent Events Compaction

**Problem:** The compactor does not compact `recent_events`. The ring buffer in `apply_delta()` caps at 20 entries but does not consolidate — events accumulate verbatim, losing narrative cohesion. The compactor was previously designed to handle this but it was removed during the compactor-overhaul refactor.

**Goal:** Restore recent_events compaction to the compactor. The LLM should consolidate similar/related events, aim to halve the count, keep key facts narratively, and phase them in-universe (player-facing UI).

---

## 1. Model Changes — `ccya/models.py`

### 1.1 Add `CompactorRecentEventCompact` model

Add before `CompactorSanitizationResult` (around line 364):

```python
class CompactorRecentEventCompact(BaseModel):
    """A consolidated recent event produced by the compactor."""
    id: str
    """New snake_case ID for the consolidated event."""
    text: str
    """Consolidated narrative text, in-universe phrasing."""
    turn: int = 0
    """Turn this event originated from (for ordering)."""
```

### 1.2 Add field to `CompactorSanitizationResult`

Add to `CompactorSanitizationResult` (line 364-369):

```python
class CompactorSanitizationResult(BaseModel):
    npc_merge: list[CompactorNpcMerge] = Field(default_factory=list)
    inventory_remove: list[str] = Field(default_factory=list)
    quest_close: list[str] = Field(default_factory=list)
    pressure_remove: list[str] = Field(default_factory=list)
    condition_remove: list[str] = Field(default_factory=list)
    recent_events_compact: list[CompactorRecentEventCompact] = Field(default_factory=list)
```

---

## 2. Prompt Changes

### 2.1 `ccya/prompts/compact_system.j2` — Add Part 3

Insert after Part 2 (after line 70, before "Hard rules"):

```
## PART 3: Recent events compaction

The game maintains a list of `recent_events` — narratively significant facts surfaced
to the player in the UI. This list has grown across turns and needs consolidation.

### What to do

- **Consolidate:** Merge similar or related events into single entries. If two events
  describe the same NPC, the same location change, or the same quest thread, combine
  them into one coherent narrative sentence.
- **Trim:** Aim to reduce the total count by about half. Keep the most narratively
  significant events. Drop events that are now stale, irrelevant, or fully superseded
  by later events.
- **Preserve:** Keep key facts about:
  - PC status changes (conditions, injuries, morale)
  - NPC introductions and their roles
  - Quest-relevant developments and leads
  - Major world/state changes (location shifts, new alliances, conflicts)
  - Durable facts that will matter for future turns
- **Phase narratively:** Write each consolidated event as an in-universe narrative
  fact, not a mechanical summary. The player reads these directly. Use the same
  prose style as the narration. Examples:
  - Bad: "Player met Caron and learned he's waiting for payment."
  - Good: "Caron has been waiting for you — he knows about the debt."
- **New IDs:** Generate fresh snake_case IDs for consolidated events. Do NOT reuse
  old IDs — the compactor replaces the entire list.

### Output format

Include `recent_events_compact` in the JSON object. Each entry:
```json
{
  "recent_events_compact": [
    {"id": "caron_waiting", "text": "Caron has been waiting for you — he knows about the debt.", "turn": 2},
    {"id": "road_toughs", "text": "Road-toughs are extorting travelers near the Crossed Keys Inn.", "turn": 3}
  ]
}
```

Omit the key if the list would be empty (no consolidation needed).
```

### 2.2 `ccya/prompts/compact_user.j2` — Add Recent Events Section

Add after the PC Conditions section (after line 64):

```jinja2

## RECENT EVENTS
*(These are player-facing narrative facts. Consolidate and trim.)*
{% if recent_events -%}
{% for event in recent_events %}- [{{ event.get("id", "?") }}] (turn {{ event.get("turn", "?") }}) {{ event.text if event is mapping else event }}
{% endfor -%}
{% else -%}
(empty)
{% endif -%}
```

### 2.3 Update `CompactorSanitizationResult` output format in system prompt

Update the JSON output format example in Part 2 (line 60-68) to include the new field:

```json
{
  "npc_merge": [{"keep_id": "...", "remove_ids": ["..."]}],
  "inventory_remove": ["item_id"],
  "quest_close": ["quest_id"],
  "pressure_remove": ["pressure_id"],
  "condition_remove": ["condition_id"],
  "recent_events_compact": [{"id": "...", "text": "...", "turn": 0}]
}
```

---

## 3. Compactor Changes — `ccya/engine/compactor.py`

### 3.1 Pass recent_events to prompt builder

In `_build_compact_messages()` (line 144), extract recent_events and pass to template:

```python
def _build_compact_messages(
    env: Any,
    state: dict[str, Any],
    turns: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build system + user messages for the compaction LLM call."""
    system_prompt = env.get_template("compact_system.j2").render()

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    present_npcs = state.get("scene", {}).get("present_npcs") or []
    pressures = state.get("scene", {}).get("scene_pressure") or []
    inventory = list(state.get("inventory") or [])
    _npcs_raw = (state.get("compendium") or {}).get("npcs") or {}
    compendium_npcs: list[tuple[str, Any]] = list(_npcs_raw.items())
    all_quests = list(state.get("quests") or [])
    conditions = list((state.get("pc") or {}).get("conditions") or [])
    recent_events = list((state.get("scene") or {}).get("recent_events") or [])

    user_prompt = env.get_template("compact_user.j2").render(
        turns=turns,
        active_quests=active_quests,
        npc_names=[n.get("name", n) if isinstance(n, dict) else n for n in present_npcs],
        pressures=pressures,
        inventory=inventory,
        compendium_npcs=compendium_npcs,
        all_quests=all_quests,
        conditions=conditions,
        recent_events=recent_events,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content", user_prompt},
    ]
```

### 3.2 Apply recent_events_compact in `maybe_compact()`

In `maybe_compact()` (line 105-108), after `_apply_sanitization()`, add recent_events replacement:

```python
    if sanitization is not None:
        _apply_sanitization(state, sanitization)

        # Replace recent_events with compactor's consolidated version
        if sanitization.recent_events_compact:
            scene = state.setdefault("scene", {})
            scene["recent_events"] = [
                {
                    "id": e.id,
                    "text": e.text,
                    "turn": e.turn or current_turn,
                }
                for e in sanitization.recent_events_compact
            ]
            _log.info(
                "compactor: compacted %d → %d recent_events",
                len(recent_events) if recent_events else 0,
                len(sanitization.recent_events_compact),
                extra=log_ctx,
            )

    state.setdefault("meta", {})["last_compacted_turn"] = compact_end
```

Need to capture `recent_events` count before the sanitization block. Add near line 100:

```python
    recent_events_count = len(state.get("scene", {}).get("recent_events") or [])
```

### 3.3 Add log context variable

Add `log_ctx` near line 100 in `maybe_compact()`:

```python
    log_ctx = {"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"}
```

---

## 4. Test Changes — `tests/test_compactor.py`

### 4.1 Update existing test

The test `test_does_not_touch_recent_events` (line 389) must be **removed** — the compactor now DOES touch recent_events.

### 4.2 Update `test_no_recent_events_instruction`

The test at line 603 that asserts "recent_events" is NOT in the system prompt must be **removed** — recent_events is now a core part of the compactor prompt.

### 4.3 Add new test: `test_recent_events_compaction`

```python
async def test_recent_events_compaction(self, tmp_path: Path, mock_llm: FakeLLM):
    """Compactor consolidates recent_events and writes back to state."""
    config = make_config(compact_every=6, window_turns=3)
    state = {
        "meta": {"turn": 6, "last_compacted_turn": 0},
        "scene": {
            "recent_events": [
                {"id": "arrived", "text": "You arrived in Marrow's Crossing after three days on the road.", "turn": 1},
                {"id": "rumors", "text": "You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.", "turn": 2},
                {"id": "caron_found", "text": "You found Caron in the tavern — he's been waiting for you.", "turn": 3},
            ]
        },
        "quests": [],
        "inventory": [],
        "compendium": {"npcs": {}},
        "pc": {"conditions": []},
        "scene_pressure": [],
    }
    # Chronicle with turns 1-6
    _write_chronicle(tmp_path, state)

    # Mock LLM returns consolidated events
    mock_llm.set_response(
        "- [T1] You arrived in Marrow's Crossing after three days on the road.\n"
        "- [T2] Uneventful — no mechanical changes.\n"
        "- [T3] Uneventful — no mechanical changes.\n"
        "\n"
        '```json\n'
        '{"recent_events_compact": ['
        '{"id": "arrival_and_rumors", "text": "You arrived in Marrow\'s Crossing to hear that road-toughs are extorting travelers near the inn.", "turn": 1},'
        '{"id": "caron_waiting", "text": "Caron has been waiting for you in the tavern — he knows about the debt.", "turn": 3}'
        ']}\n'
        '```'
    )

    result = await maybe_compact(tmp_path, state, config)

    assert len(result["scene"]["recent_events"]) == 2
    assert result["scene"]["recent_events"][0]["id"] == "arrival_and_rumors"
    assert result["scene"]["recent_events"][1]["id"] == "caron_waiting"
```

### 4.4 Add new test: `test_recent_events_empty_input`

```python
async def test_recent_events_empty_input(self, tmp_path: Path, mock_llm: FakeLLM):
    """Compactor with no recent_events produces no recent_events_compact."""
    config = make_config(compact_every=6, window_turns=3)
    state = {
        "meta": {"turn": 6, "last_compacted_turn": 0},
        "scene": {"recent_events": []},
        "quests": [],
        "inventory": [],
        "compendium": {"npcs": {}},
        "pc": {"conditions": []},
        "scene_pressure": [],
    }
    _write_chronicle(tmp_path, state)

    mock_llm.set_response(
        "- [T1] You arrived in Marrow's Crossing.\n"
        "\n"
        "{}"
    )

    result = await maybe_compact(tmp_path, state, config)
    assert result["scene"]["recent_events"] == []
```

### 4.5 Add new test: `test_recent_events_compact_replaces_all`

```python
async def test_recent_events_compact_replaces_all(self, tmp_path: Path, mock_llm: FakeLLM):
    """Compactor replaces ALL existing recent_events, not just updates."""
    config = make_config(compact_every=6, window_turns=3)
    state = {
        "meta": {"turn": 6, "last_compacted_turn": 0},
        "scene": {
            "recent_events": [
                {"id": "old_1", "text": "Old event 1", "turn": 1},
                {"id": "old_2", "text": "Old event 2", "turn": 2},
                {"id": "old_3", "text": "Old event 3", "turn": 3},
                {"id": "old_4", "text": "Old event 4", "turn": 4},
            ]
        },
        "quests": [],
        "inventory": [],
        "compendium": {"npcs": {}},
        "pc": {"conditions": []},
        "scene_pressure": [],
    }
    _write_chronicle(tmp_path, state)

    mock_llm.set_response(
        "- [T1] You arrived in Marrow's Crossing.\n"
        "- [T2] Uneventful.\n"
        "- [T3] Uneventful.\n"
        "- [T4] Uneventful.\n"
        "\n"
        '```json\n'
        '{"recent_events_compact": ['
        '{"id": "consolidated", "text": "You arrived in Marrow\'s Crossing, heard about road-toughs, and found Caron waiting.", "turn": 1}'
        ']}\n'
        '```'
    )

    result = await maybe_compact(tmp_path, state, config)
    assert len(result["scene"]["recent_events"]) == 1
    assert result["scene"]["recent_events"][0]["id"] == "consolidated"
```

---

## 5. Summary of Changes

| File | Change |
|---|---|
| `ccya/models.py` | Add `CompactorRecentEventCompact` model; add `recent_events_compact` field to `CompactorSanitizationResult` |
| `ccya/prompts/compact_system.j2` | Add Part 3: recent_events compaction instructions |
| `ccya/prompts/compact_user.j2` | Add `## RECENT EVENTS` section |
| `ccya/engine/compactor.py` | Pass recent_events to prompt; apply `recent_events_compact` in `maybe_compact()` |
| `tests/test_compactor.py` | Remove `test_does_not_touch_recent_events`; remove `test_no_recent_events_instruction`; add 3 new tests |
