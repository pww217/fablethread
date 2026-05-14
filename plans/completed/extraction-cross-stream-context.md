# Extraction cross-stream context: stale-state bug

## Status
`completed`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Cross-stream context struct | Define `ExtractionContext` dataclass; thread scene/state results forward to progress |
| 02 | Progress prompt wiring | Update `_extract_progress_messages` + `extract_progress_user.j2` to consume current-turn context |
| 03 | Tests | Unit tests asserting progress sees this-turn data, not last-turn data |

## Objective
All three extraction streams — scene, state, progress — receive the same unmodified `state` dict, which is the **pre-turn, pre-delta** game state. The streams run sequentially, but their outputs are never fed forward as input to the next stream. As a result, the progress extractor evaluates quests, facts, NPC notes, and outcome_summary against last turn's `present_npcs`, `inventory`, `scene_pressure`, and `active_quests`, not the ones that were just established by the narration and the upstream extractors this turn. This causes the LLM to contradict itself, track stale NPCs, and miss inventory/condition changes that just happened.

## Non-goals
- Does **not** change the sequential execution order of the three streams (scene → state → progress).
- Does **not** change the narration pipeline, rules pipeline, or `apply_delta` call sites.
- Does **not** restructure the `StateDelta` model.
- Does **not** alter the scene or state extractor prompts — their inputs are already correct (they only need `state` + narration).
- Does **not** add parallelism to the extraction pipeline.
- Does **not** touch `extract_scene_user.j2` or `extract_state_user.j2`.

---

## Implementation — Phase 01: Cross-stream context struct

### Files to pull for context
- `ccya/engine/extraction.py`
- `ccya/models.py` (scan `SceneExtractResult`, `StateExtractResult` field names)

### Detailed steps

#### Step 1.1 — Define `ExtractionContext` datatype

**File:** `ccya/engine/extraction.py`

**What:** Add a private dataclass at module level (after imports, before `_check_npc_ghost_cycle`) that captures the this-turn deltas from stream 1 and stream 2 in a structured, typed form that stream 3 can consume. This is not a Pydantic model — it never leaves this module and never touches the LLM I/O boundary.

**Why:** Avoids mutating `state` in-place mid-pipeline (which would be confusing and hard to test), avoids passing a growing kwargs blob through `_extract_progress_messages`, and gives the executor a clear named type to audit.

**Code Snippet**
```python
from dataclasses import dataclass, field

@dataclass
class _ExtractionContext:
    """Carries this-turn deltas from scene + state streams into the progress stream.

    All fields are derived from extract results, NOT from `state`.  They
    represent what happened *this turn* as determined by the prior two streams.
    """
    # Scene stream outputs (stream 1)
    present_npcs_this_turn: list[dict] = field(default_factory=list)
    """present_npcs list after applying npc_add/npc_remove from scene result."""
    location_this_turn: dict = field(default_factory=dict)
    """Location dict after applying location_change from scene result (or state's if no change)."""
    scene_tags_this_turn: list[str] = field(default_factory=list)
    """scene.tags after scene stream."""
    scene_pressure_this_turn: list[dict] = field(default_factory=list)
    """scene_pressure after applying scene stream's pressure add/remove."""

    # State stream outputs (stream 2)
    inventory_this_turn: list[dict] = field(default_factory=list)
    """inventory list after applying inventory_add/remove/update from state result."""
    conditions_this_turn: list[dict] = field(default_factory=list)
    """pc.conditions after applying pc_condition_add/remove from state result."""
```

**Validation:** `python -c "from ccya.engine.extraction import _ExtractionContext; print('ok')"` exits 0.

---

#### Step 1.2 — Add `_build_extraction_context` helper

**File:** `ccya/engine/extraction.py`

**What:** A pure function that takes the pre-turn `state`, the `scene_result`, and the `state_result` and returns a populated `_ExtractionContext`. All logic is straightforward list-diff — no LLM calls, no I/O.

**Why:** Centralizes the "apply-deltas-in-memory" logic in one testable place instead of scattering it through the pipeline.

**Code Snippet**
```python
def _build_extraction_context(
    state: dict,
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
) -> _ExtractionContext:
    """Compute this-turn derived context from the two upstream extraction results.

    Does NOT mutate `state`.
    """
    scene = state.get("scene") or {}
    compendium_npcs = (state.get("compendium") or {}).get("npcs") or {}

    # --- present_npcs: start from state, apply add/remove ---
    current_npcs: dict[str, dict] = {
        npc["id"]: dict(npc)
        for npc in (scene.get("present_npcs") or [])
        if isinstance(npc, dict) and npc.get("id")
    }
    for op in (scene_result.npc_remove or []):
        current_npcs.pop(op.id, None)
    for op in (scene_result.npc_add or []):
        nid = op.id if hasattr(op, "id") else op.get("id", "")
        if not nid:
            continue
        # Enrich from compendium
        entry = compendium_npcs.get(nid, {})
        row: dict = {"id": nid}
        if hasattr(op, "name"):
            row["name"] = op.name or entry.get("name", "")
        if hasattr(op, "notes"):
            row["notes"] = op.notes or ""
        if not row.get("name") and entry.get("name"):
            row["name"] = entry["name"]
        current_npcs[nid] = row

    # --- location: apply location_change if present ---
    if scene_result.location_change:
        lc = scene_result.location_change
        location_this_turn = {
            "name": getattr(lc, "name", "") or (state.get("location") or {}).get("name", ""),
            "description": getattr(lc, "description", "") or scene_result.location_description or "",
        }
    else:
        location_this_turn = dict(state.get("location") or {})

    # --- scene_tags: apply scene_tags from scene result ---
    tags_this_turn = list(scene_result.scene_tags or scene.get("tags") or [])

    # --- scene_pressure: apply add/remove from progress (not yet run) so we
    #     use state's current pressures only — progress hasn't run yet ---
    pressure_this_turn = list(scene.get("scene_pressure") or [])

    # --- inventory: start from state, apply add/remove/update ---
    inv_by_id: dict[str, dict] = {}
    for item in (state.get("inventory") or []):
        if isinstance(item, dict) and item.get("id"):
            inv_by_id[item["id"]] = dict(item)
    for op in (state_result.inventory_remove or []):
        inv_by_id.pop(op.id, None)
    for op in (state_result.inventory_add or []):
        nid = op.id if hasattr(op, "id") else op.get("id", "")
        if not nid:
            continue
        inv_by_id[nid] = {
            "id": nid,
            "name": getattr(op, "name", nid),
            "notes": getattr(op, "notes", ""),
        }
    for op in (state_result.inventory_update or []):
        nid = op.id if hasattr(op, "id") else op.get("id", "")
        if nid in inv_by_id:
            if hasattr(op, "name") and op.name:
                inv_by_id[nid]["name"] = op.name
            if hasattr(op, "notes") and op.notes:
                inv_by_id[nid]["notes"] = op.notes

    # --- conditions: apply add/remove ---
    pc = state.get("pc") or {}
    cond_by_id: dict[str, dict] = {}
    for c in (pc.get("conditions") or []):
        if isinstance(c, dict) and c.get("id"):
            cond_by_id[c["id"]] = dict(c)
    for op in (state_result.pc_condition_remove or []):
        cond_by_id.pop(op.id if hasattr(op, "id") else op.get("id", ""), None)
    for op in (state_result.pc_condition_add or []):
        nid = op.id if hasattr(op, "id") else op.get("id", "")
        if not nid:
            continue
        cond_by_id[nid] = {
            "id": nid,
            "label": getattr(op, "label", nid),
            "description": getattr(op, "description", ""),
        }

    return _ExtractionContext(
        present_npcs_this_turn=list(current_npcs.values()),
        location_this_turn=location_this_turn,
        scene_tags_this_turn=tags_this_turn,
        scene_pressure_this_turn=pressure_this_turn,
        inventory_this_turn=list(inv_by_id.values()),
        conditions_this_turn=list(cond_by_id.values()),
    )
```

**Validation:** Write one quick smoke test (see Phase 03) that calls this with a synthetic state + empty results and asserts lengths are correct.

---

#### Step 1.3 — Call `_build_extraction_context` in `_run_extraction_pipeline` and thread it to progress

**File:** `ccya/engine/extraction.py`

**What:** After stream 2 completes (after the `except` block for `extract_state`), call `_build_extraction_context` and pass the resulting `_ExtractionContext` into `_extract_progress_messages`. Add `extraction_ctx` as a required parameter to `_extract_progress_messages`.

**Why:** This is the minimum viable wire-up. The context struct is built exactly once, from the two completed results, before progress is called.

**Code Snippet**

In `_run_extraction_pipeline`, immediately after the state stream's `except` block ends and before `t_progress = ...`:

```python
    # Build this-turn context from scene + state results for the progress stream
    extraction_ctx = _build_extraction_context(state, scene_result, state_result)
```

Then in the progress call:
```python
    progress_msgs = _extract_progress_messages(
        env, narration, state,
        state_result=state_result,
        extraction_ctx=extraction_ctx,          # ← add this
        enable_thinking=config.enable_extract_thinking,
        intent=intent,
        deescalate=deescalate,
        quest_ages=quest_ages or [],
        recent_turns=(recent_turns or [])[-2:],
        turn_no=turn_no,
        stakes=_stakes,
        band=_band,
    )
```

**Validation:** `make check` passes (mypy/ruff). No runtime error on import.

---

## Implementation — Phase 02: Progress prompt wiring

### Files to pull for context
- `ccya/engine/extraction.py` (as modified in Phase 01)
- `ccya/prompts/extract_progress_user.j2`
- `docs/REPOMAP/prompts.md` (section on extract_progress_user.j2 variable contract)

### Detailed steps

#### Step 2.1 — Update `_extract_progress_messages` signature and rendering

**File:** `ccya/engine/extraction.py`

**What:** Add `extraction_ctx: _ExtractionContext` as a required parameter. Replace the three stale `state`-derived variables (`present_npcs`, `location`, `scene_pressure`) with the `_ExtractionContext` equivalents. Keep the old `state_ctx` cross-stream surface (items_gained/items_lost) — it's harmless and consistent — but it is now redundant with `extraction_ctx.inventory_this_turn`. Leave it in place for now to avoid a large diff; mark it with a `# TODO: remove` comment.

**Why:** The Jinja template is the LLM's view of the world. Every variable passed here becomes part of the prompt. Replacing stale sources here is sufficient to fix the bug — no changes needed to system prompts.

**Code Snippet**
```python
def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    state_result: "StateExtractResult",
    extraction_ctx: "_ExtractionContext",          # ← new required param
    enable_thinking: bool = False,
    intent: "IntentEnvelope | None" = None,
    deescalate: float = 0.0,
    quest_ages: list[dict[str, Any]] = [],
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    stakes: str = "",
    band: str = "",
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (quests + facts + actions + outcome_summary)."""
    pc = state.get("pc") or {}
    scene = state.get("scene") or {}

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    recent_events = list(scene.get("recent_events") or [])
    world_state = list(scene.get("world_state") or [])

    # Cross-stream: minimal surfaces (legacy; superseded by extraction_ctx)
    # TODO: remove state_ctx once templates are fully migrated to extraction_ctx
    state_ctx = {
        "items_gained": [it.name for it in state_result.inventory_add],
        "items_lost": [it.id for it in state_result.inventory_remove],
    }

    system_text = _render(env, "extract_progress_system.j2", {})
    pending_beat = (state.get("meta") or {}).get("pending_gm_beat") or None
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "pc_stats": pc.get("stats") or {},
            # This-turn derived values (from extraction_ctx) — NOT state
            "present_npcs": extraction_ctx.present_npcs_this_turn,
            "location": extraction_ctx.location_this_turn,
            "scene_pressure": extraction_ctx.scene_pressure_this_turn,
            "inventory": extraction_ctx.inventory_this_turn,
            "conditions": extraction_ctx.conditions_this_turn,
            # State-sourced (these don't change within a turn)
            "known_npcs": _known_characters_for_extract(state, compact=True),
            "active_quests": active_quests,
            "recent_events": recent_events,
            "world_state": world_state,
            "state_result": state_ctx,
            "quest_threshold_directive": _quest_threshold_directive(active_quests),
            "intent": intent,
            "deescalate": deescalate,
            "quest_ages": quest_ages,
            "recent_turns": recent_turns or [],
            "turn_no": turn_no,
            "stakes": stakes,
            "band": band,
            "pending_beat": pending_beat,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs
```

**Validation:** Confirm `present_npcs`, `location`, `scene_pressure`, `inventory`, `conditions` are no longer sourced from `state` directly inside this function. Grep: `grep -n "state.get" ccya/engine/extraction.py` — none of those keys should appear in the new `_extract_progress_messages` body.

---

#### Step 2.2 — Update `extract_progress_user.j2` to use `inventory` and `conditions`

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** The template currently renders `present_npcs`, `location`, and `scene_pressure` from variables that now carry this-turn data. Verify it also renders inventory and conditions correctly. If the template currently does not render `inventory` or `conditions` at all, add a concise section. If it already references them, no change is needed — the fix is purely in what Python passes.

**Why:** The prompt must surface current inventory and conditions so the progress LLM can correctly assess item-dependent quest progress, condition-triggered outcomes, etc.

**Code Snippet**

Read the current template first (`ccya/prompts/extract_progress_user.j2`). Then add, at a logical position (after NPC section, before quests):

```jinja2
{%- if inventory %}
## Current inventory (this turn)
{% for item in inventory -%}
- {{ item.id }}: {{ item.name }}{% if item.notes %} — {{ item.notes }}{% endif %}
{% endfor %}
{%- endif %}

{%- if conditions %}
## PC conditions (this turn)
{% for c in conditions -%}
- {{ c.id }}: {{ c.label }}{% if c.description %} — {{ c.description }}{% endif %}
{% endfor %}
{%- endif %}
```

Only add these blocks if they don't already exist in the template. If inventory/conditions are already rendered, confirm they are fed from the `inventory` and `conditions` template variables (which now carry this-turn data).

**Validation:** Render the template with a synthetic context (see Phase 03 tests) and assert the rendered string contains the item name from the added inventory op, not the old state item.

---

## Implementation — Phase 03: Tests

### Files to pull for context
- `tests/` (list directory to find existing extraction tests)
- `docs/REPOMAP/testing.md`
- `ccya/engine/extraction.py` (as modified in Phases 01–02)

### Detailed steps

#### Step 3.1 — Unit test: `_build_extraction_context`

**File:** `tests/test_extraction_context.py` (new file)

**What:** Four test functions covering the core logic of `_build_extraction_context`.

**Why:** This function contains the only non-trivial logic in the patch (list-diff on npcs and inventory). If it regresses, the pipeline silently falls back to stale state.

**Code Snippet**
```python
"""Tests for _build_extraction_context in extraction.py."""
import pytest
from unittest.mock import MagicMock
from ccya.engine.extraction import _build_extraction_context
from ccya.models import SceneExtractResult, StateExtractResult


def _make_npc_add(npc_id: str, name: str):
    m = MagicMock()
    m.id = npc_id
    m.name = name
    m.notes = ""
    return m


def _make_npc_remove(npc_id: str):
    m = MagicMock()
    m.id = npc_id
    return m


def _make_inv_add(item_id: str, item_name: str):
    m = MagicMock()
    m.id = item_id
    m.name = item_name
    m.notes = ""
    return m


def _make_inv_remove(item_id: str):
    m = MagicMock()
    m.id = item_id
    return m


def test_npc_add_appears_in_context():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult(
        npc_add=[_make_npc_add("guard_01", "Town Guard")],
        npc_remove=[],
    )
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert any(n["id"] == "guard_01" for n in ctx.present_npcs_this_turn)


def test_npc_remove_absent_from_context():
    state = {
        "scene": {
            "present_npcs": [{"id": "guard_01", "name": "Town Guard"}],
            "tags": [],
            "scene_pressure": [],
        },
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult(
        npc_remove=[_make_npc_remove("guard_01")],
    )
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert not any(n["id"] == "guard_01" for n in ctx.present_npcs_this_turn)


def test_inventory_add_appears_in_context():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [{"id": "sword_01", "name": "Iron Sword"}],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult()
    state_result = StateExtractResult(
        inventory_add=[_make_inv_add("potion_01", "Health Potion")],
        inventory_remove=[_make_inv_remove("sword_01")],
    )
    ctx = _build_extraction_context(state, scene_result, state_result)
    ids = [i["id"] for i in ctx.inventory_this_turn]
    assert "potion_01" in ids
    assert "sword_01" not in ids


def test_location_change_applied():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    lc = MagicMock()
    lc.name = "Forest"
    lc.description = "A dense wood."
    scene_result = SceneExtractResult(location_change=lc)
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert ctx.location_this_turn["name"] == "Forest"
```

**Validation:** `make test` passes with these four tests green.

---

#### Step 3.2 — Integration smoke test: progress sees this-turn NPC

**File:** `tests/test_extraction_integration.py` (new file)

**What:** A test that constructs a minimal `state` with NPC X absent, builds a `scene_result` that adds NPC X, then calls `_extract_progress_messages` and asserts NPC X's name appears in the rendered user prompt.

**Why:** Closes the loop — even if `_build_extraction_context` works correctly, a bug in how the context is passed to the template would be invisible to the unit tests above.

**Code Snippet**
```python
"""Integration test: progress prompt contains this-turn NPC."""
from unittest.mock import MagicMock, patch
from ccya.engine.extraction import (
    _build_extraction_context,
    _extract_progress_messages,
)
from ccya.models import SceneExtractResult, StateExtractResult


def _fake_render(env, template, ctx):
    """Stub renderer: returns the context vars as a string."""
    npcs = ctx.get("present_npcs", [])
    return " ".join(n.get("name", "") for n in npcs)


def test_progress_prompt_contains_this_turn_npc():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": [], "recent_events": [], "world_state": []},
        "inventory": [],
        "pc": {"conditions": [], "stats": {}},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
        "quests": [],
        "meta": {},
    }
    npc_add = MagicMock()
    npc_add.id = "captain_01"
    npc_add.name = "Captain Aldric"
    npc_add.notes = ""
    scene_result = SceneExtractResult(npc_add=[npc_add])
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)

    with patch("ccya.engine.extraction._render", side_effect=_fake_render):
        msgs = _extract_progress_messages(
            env=MagicMock(),
            narration="Captain Aldric enters.",
            state=state,
            state_result=state_result,
            extraction_ctx=ctx,
            turn_no=5,
        )

    user_msg = next((m["content"] for m in msgs if m["role"] == "user"), "")
    assert "Captain Aldric" in user_msg
```

**Validation:** `make test` passes.

---

### REPOMAP and architecture updates

**`docs/REPOMAP/engine.md`** — Update the `_run_extraction_pipeline` entry:
- Add `_ExtractionContext` dataclass and `_build_extraction_context` to the function inventory under `extraction.py`.
- Update the description of `_extract_progress_messages` to note it now requires `extraction_ctx: _ExtractionContext`.
- Update the pipeline flow diagram / description to show that scene + state results are combined into `_ExtractionContext` before progress runs.

**`docs/REPOMAP/prompts.md`** — Update the `extract_progress_user.j2` variable contract to add `inventory` (list[dict], this-turn) and `conditions` (list[dict], this-turn) if they are newly added in Step 2.2.
