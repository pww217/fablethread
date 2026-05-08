# Compactor Overhaul — Stable Recent Window, Batched Prior History, Sanitization Validation

## Status
`open`

## Part of
standalone

## Dependencies
- none
- Coordinate with `docs/plans/narrator-driven-scope.md` if that plan begins modifying narrator context assembly before this one executes — conceptual overlap on narrator inputs, no confirmed direct file conflict currently.

## Objective
Fix the compactor so narrator context is stable, non-redundant, and predictable. The narrator always receives the most recent `window_turns` completed turns (default 3), never more. Compaction runs every `compact_every` turns (default 6), converting the oldest eligible turns into append-only `prior_history` bullets in `meta`. The current bug — `last_compacted_turn` being set to `current_turn` instead of the actual end of the compacted band — causes already-compacted turns to keep appearing as recent context and be re-submitted to the LLM on every subsequent compaction. This plan also adds Pydantic-validated state sanitization output to the compaction call so the compactor can repair structural drift (duplicate NPCs, duplicate inventory, orphaned quests, stale pressures, resolved conditions) while it already holds the full game state.

## Non-goals
- Do not redesign the full NPC compendium system.
- Do not rewrite extractor prompts.
- Do not retroactively rewrite narrative prose already stored in `chronicle.md`.
- Do not make `world_state` mutable or compact it.
- Do not add a second LLM call — sanitization is appended to the single compaction call output.
- Do not merge `compact_every` into `window_turns`; they are separate controls.
- Do not add compendium field-level corrections (e.g. `last_seen_state`) until those fields are verified in source — executor must check before including.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `config.yaml` | modify | Set `window_turns: 3`, `compact_every: 6`, add `recent_turns_min: 2` |
| `ccya/engine/config.py` | modify | Add `recent_turns_min: int = 2`; keep `compact_every`; add `_validate_compactor_config` |
| `ccya/engine/turn.py` | modify | Compute narrator recent-turn count from `last_compacted_turn`, `window_turns`, `recent_turns_min`; pass `min_turn_exclusive` to loader |
| `ccya/engine/compactor.py` | modify | Fix compaction band math; append bullets to `meta.prior_history`; parse and validate sanitization JSON; apply deterministic state fixes; set `last_compacted_turn` to `compact_end` not `current_turn`; remove `recent_events` mutation path |
| `ccya/state/io.py` | modify | Add `meta.prior_history: []` to `_default_state`; migrate missing field in `_migrate_state`; fix missing/invalid `last_compacted_turn` |
| `ccya/state/chronicle.py` | modify | Add `min_turn_exclusive: int = 0` parameter to `load_recent_chronicle_turns` |
| `ccya/models.py` | modify | Add `CompactorNpcMerge`, `CompactorSanitizationResult` Pydantic models |
| `ccya/prompts/compact_system.j2` | modify | Remove recent-events compaction instructions; add bullet-history + sanitization output contract |
| `ccya/prompts/compact_user.j2` | modify | Remove events section; add structured mechanical state reference with exact IDs |
| `docs/REPOMAP/config.md` | update | Document `recent_turns_min`, defaults, invariant relationships |
| `docs/REPOMAP/engine.md` | update | Document fixed recent-turn calc, corrected compactor trigger math, sanitization validation flow |
| `docs/REPOMAP/state.md` | update | Document `meta.prior_history`, updated `load_recent_chronicle_turns` signature |
| `docs/REPOMAP/models.md` | update | Document compactor sanitization models |
| `docs/REPOMAP/prompts.md` | update | Document updated compactor prompt contract |
| `docs/plans/TODO.md` | update | Replace existing compactor TODO entry with updated line |
| `tests/test_compactor.py` | create/modify | Unit coverage for window math, parsing, Pydantic validation, sanitization application |
| `tests/test_engine_pipeline.py` | modify | Pipeline-level coverage: narrator recent turns stop duplicating compacted turns |

## Firm decisions

1. `window_turns`, `compact_every`, and `recent_turns_min` are three separate knobs. Defaults: `window_turns: 3`, `compact_every: 6`, `recent_turns_min: 2`. They must not be merged.

2. The narrator receives exactly `min(window_turns, turns_since_last_compaction)` recent turns, with a floor of `min(recent_turns_min, turns_available)`. On turns 1 and 2 the floor applies naturally because fewer than 2 completed turns exist.

3. Compaction fires when `current_turn % compact_every == 0`. It converts all turns from `last_compacted_turn + 1` up through `retain_from - 1`, where `retain_from = max(1, current_turn - window_turns + 1)`. With defaults at turn 6: `retain_from = 4`, so compacted band = turns 1–3, turns 4–6 remain as recent pool.

4. `meta.last_compacted_turn` records the highest turn number actually written to `prior_history` — i.e. `compact_end`, not `current_turn`. This is the root bug fix. Setting it to `current_turn` was wrong and caused redundant re-compaction.

5. `meta.prior_history` is the canonical append-only long-term summary store. Each entry is formatted `- [T{n}] ...`. The `## COMPACTED` block in `chronicle.md` remains for human inspection only and is not the authoritative source for prompt assembly.

6. The compactor no longer touches `scene.recent_events`. That field is owned by `apply_delta` exclusively.

7. Sanitization proposals from the LLM are validated through Pydantic before any state mutation. Validation failure logs a warning and skips sanitization entirely — state is never partially applied.

8. All proposed IDs from sanitization output are checked against an allowlist built from current state before any mutation. Unknown IDs are silently skipped per-operation.

9. `world_state` is immutable. The compactor must not read from or write to it.

10. No second LLM call for validation. One call per compaction event.

11. Compendium field corrections (`last_seen_state`, `last_location`-style) are NOT included in this plan. They require source verification first. If the executor finds those fields in source, they may file a follow-on plan — not extend this one.

12. Final validation step: `make check && make test`.

---

## Implementation — Phase 1: Config, state schema, and Pydantic models

### Context files to load
- `AGENTS.md`
- `docs/REPOMAP/config.md`
- `docs/REPOMAP/state.md`
- `docs/REPOMAP/models.md`
- `ccya/engine/config.py`
- `ccya/state/io.py`
- `ccya/models.py`
- `config.yaml`

### Overview
Add the three config fields required by the new design, add `meta.prior_history` to state with migration, and add Pydantic models for sanitization output validation. No compactor logic changes yet.

### Detailed steps

#### Step 1.1 — Add `recent_turns_min` to `EngineConfig` and add config validation

**File:** `ccya/engine/config.py`

**What:** Add `recent_turns_min: int = 2` to `EngineConfig`. Keep `compact_every` and `window_turns` unchanged. Add `_validate_compactor_config(config: EngineConfig) -> None` that enforces:
- `window_turns >= 1`
- `compact_every > window_turns`
- `0 <= recent_turns_min <= window_turns`

Call `_validate_compactor_config` wherever `EngineConfig` is constructed or loaded from file (check `load_config()` and any server bootstrap path).

**Why:** Input validation at the module boundary prevents silent misconfiguration. The `compact_every > window_turns` invariant is load-bearing — if they are equal, the compactor would compact the entire recent window on every firing.

**Code Snippet**
```python
# In EngineConfig dataclass, add after compact_temperature:
recent_turns_min: int = 2

# New function in config.py:
def _validate_compactor_config(config: "EngineConfig") -> None:
    if config.window_turns < 1:
        raise ValueError(f"window_turns must be >= 1, got {config.window_turns}")
    if config.compact_every <= config.window_turns:
        raise ValueError(
            f"compact_every ({config.compact_every}) must be > window_turns ({config.window_turns})"
        )
    if config.recent_turns_min < 0:
        raise ValueError(f"recent_turns_min must be >= 0, got {config.recent_turns_min}")
    if config.recent_turns_min > config.window_turns:
        raise ValueError(
            f"recent_turns_min ({config.recent_turns_min}) must be <= window_turns ({config.window_turns})"
        )
```

**Validation:** Constructing `EngineConfig(window_turns=3, compact_every=3)` raises `ValueError`. Constructing `EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)` succeeds.

---

#### Step 1.2 — Update `config.yaml`

**File:** `config.yaml`

**What:** Set `window_turns: 3`, `compact_every: 6`, add `recent_turns_min: 2`. Keep `compact_temperature: 0.1`.

**Why:** These are the agreed defaults.

**Code Snippet**
```yaml
# Under [game] or equivalent section:
window_turns: 3
compact_every: 6
recent_turns_min: 2
compact_temperature: 0.1
```

**Validation:** `python -c "from ccya.engine.config import load_config, _validate_compactor_config; c = load_config(); _validate_compactor_config(c); print('ok')"` prints `ok`.

---

#### Step 1.3 — Add `meta.prior_history` to state and migration

**File:** `ccya/state/io.py`

**What:** Add `"prior_history": []` under `meta` in `_default_state()`. In `_migrate_state(state)`, add guards to initialize `prior_history` to `[]` if absent or not a list, and to set `last_compacted_turn` to `0` if absent, not an int, or negative.

**Why:** `prior_history` is the new canonical compacted-history store. Migration must be safe for all existing saves.

**Code Snippet**
```python
# In _default_state(), meta block:
"meta": {
    "game_name": "",
    "turn": 0,
    "setting_pack": "",
    "model": "",
    "compendium_touch_order": [],
    "pending_gm_beat": None,
    "last_compacted_turn": 0,
    "prior_history": [],   # NEW
},

# In _migrate_state(state):
meta = state.setdefault("meta", {})
if not isinstance(meta.get("prior_history"), list):
    meta["prior_history"] = []
if not isinstance(meta.get("last_compacted_turn"), int) or meta["last_compacted_turn"] < 0:
    meta["last_compacted_turn"] = 0
```

**Validation:** Load a pre-existing save fixture that lacks `prior_history`. Assert `state["meta"]["prior_history"] == []`. Load a new save. Assert same. Load a save with a negative `last_compacted_turn`. Assert it becomes `0`.

---

#### Step 1.4 — Add compactor sanitization Pydantic models

**File:** `ccya/models.py`

**What:** Add two models. Do not add field-update models (not in scope until field names are verified in source).

**Why:** Pydantic validation is the primary guard against malformed LLM sanitization output touching state.

**Code Snippet**
```python
from pydantic import BaseModel, Field

class CompactorNpcMerge(BaseModel):
    keep_id: str
    remove_ids: list[str] = Field(default_factory=list)


class CompactorSanitizationResult(BaseModel):
    npc_merge: list[CompactorNpcMerge] = Field(default_factory=list)
    inventory_remove: list[str] = Field(default_factory=list)
    quest_close: list[str] = Field(default_factory=list)
    pressure_remove: list[str] = Field(default_factory=list)
    condition_remove: list[str] = Field(default_factory=list)

    model_config = {"extra": "ignore"}  # drop unknown keys silently
```

**Validation:** `CompactorSanitizationResult.model_validate({"npc_merge": [{"keep_id": "a", "remove_ids": ["b"]}], "unknown_key": 99})` succeeds without error. `CompactorSanitizationResult.model_validate({"npc_merge": "wrong_type"})` raises `ValidationError`.

---

### Tests to write or update
- `tests/test_compactor.py::test_validate_compactor_config_rejects_compact_every_lte_window_turns`
- `tests/test_compactor.py::test_validate_compactor_config_rejects_recent_turns_min_gt_window_turns`
- `tests/test_compactor.py::test_migrate_state_adds_prior_history`
- `tests/test_compactor.py::test_migrate_state_fixes_invalid_last_compacted_turn`
- `tests/test_compactor.py::test_sanitization_model_ignores_unknown_keys`
- `tests/test_compactor.py::test_sanitization_model_rejects_wrong_npc_merge_shape`

### REPOMAP updates required
- `docs/REPOMAP/config.md`: add `recent_turns_min` row; clarify that `compact_every > window_turns` is required; update defaults.
- `docs/REPOMAP/state.md`: add `prior_history: list[str]` under `meta`.
- `docs/REPOMAP/models.md`: add `CompactorNpcMerge` and `CompactorSanitizationResult`.

### Risks
1. Server bootstrap may pass config kwargs directly to `EngineConfig`. If `recent_turns_min` is absent from an old `config.yaml` in a deployed save, it defaults to `2` (acceptable). If the bootstrap path does `**cfg_dict` with unexpected keys it will blow up; executor must check `server/app.py`.
2. If `models.py` already imports from `pydantic` for other models, no new import is needed. If not, add the import.

---

## Implementation — Phase 2: Recent-turn selection and compaction math

### Context files to load
- `AGENTS.md`
- `docs/REPOMAP/engine.md`
- `docs/REPOMAP/state.md`
- `ccya/engine/turn.py`
- `ccya/engine/compactor.py`
- `ccya/state/chronicle.py`
- `ccya/state/io.py`
- Phase 1 output files

### Overview
Fix the two coupled bugs: (1) `load_recent_chronicle_turns` has no way to exclude already-compacted turns, and (2) `last_compacted_turn` is set to `current_turn` instead of the actual compacted band end. Fix both. Update `turn.py` to compute desired recent-turn count correctly.

### Detailed steps

#### Step 2.1 — Add `min_turn_exclusive` to `load_recent_chronicle_turns`

**File:** `ccya/state/chronicle.py`

**What:** Add `min_turn_exclusive: int = 0` keyword argument. Filter out any parsed turn where `turn_num <= min_turn_exclusive` before taking the last `n`. All existing callers pass no value and get the same behavior as before (default `0` filters nothing).

**Why:** Without this, turns 1–3 keep showing up as recent context even after they've been compacted into `prior_history`.

**Code Snippet**
```python
def load_recent_chronicle_turns(
    save_dir: Path,
    n: int,
    *,
    min_turn_exclusive: int = 0,
) -> list[dict[str, Any]]:
    """Return up to the last n turns from chronicle.md with turn > min_turn_exclusive."""
    path = save_dir / "chronicle.md"
    if not path.exists() or n <= 0:
        return []
    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))
    if not matches:
        return []
    turns: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        turn_num = int(m.group(1))
        if turn_num <= min_turn_exclusive:
            continue
        turn_input = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        narrative = text[body_start:body_end].strip()
        turns.append({"turn": turn_num, "input": turn_input, "narrative": narrative})
    return turns[-n:]
```

**Validation:** Chronicle with turns 1–7, called with `min_turn_exclusive=3, n=3` → returns turns 5, 6, 7. Called with `min_turn_exclusive=0, n=3` → returns turns 5, 6, 7 (same — existing behavior unchanged).

---

#### Step 2.2 — Fix narrator recent-turn count in `run_turn`

**File:** `ccya/engine/turn.py`

**What:** Replace the current `load_recent_chronicle_turns(save_dir, config.window_turns)` call (wherever it appears before narrator prompt assembly) with the corrected computation below.

**Why:** This is the user-visible fix — compacted turns stop appearing in narrator context.

**Computation rule (implement exactly as written):**
```
last_compacted_turn = state["meta"].get("last_compacted_turn", 0)  # 0 if missing
current_turn_completed = state["meta"].get("turn", 0)              # turns written to chronicle so far
turns_since_compaction = max(0, current_turn_completed - last_compacted_turn)
desired_recent = min(config.window_turns, turns_since_compaction)
if current_turn_completed > 0:
    desired_recent = max(desired_recent, min(config.recent_turns_min, turns_since_compaction))
```

Then call:
```python
recent_turns = load_recent_chronicle_turns(
    save_dir,
    desired_recent,
    min_turn_exclusive=last_compacted_turn,
)
```

**Why the floor check:** On turn 1 (`current_turn_completed=0` before narration runs), `desired_recent=0` which is correct — no turns are written yet. The `current_turn_completed > 0` guard prevents the floor from firing before the game starts. On turn 2 (1 completed turn, 0 compacted), `turns_since_compaction=1`, `desired_recent = max(min(3,1), min(2,1)) = max(1,1) = 1`. Correct.

**Validation table (verify all rows in tests):**

| current_turn_completed | last_compacted_turn | desired_recent | min_turn_exclusive |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 1 | 0 | 1 | 0 |
| 2 | 0 | 2 | 0 |
| 3 | 0 | 3 | 0 |
| 4 | 0 | 3 | 0 |
| 5 | 0 | 3 | 0 |
| 6 | 0 | 3 | 0 |
| 6 | 3 | 3 | 3 |
| 7 | 3 | 3 | 3 |
| 8 | 3 | 3 | 3 |
| 9 | 3 | 3 | 3 |

After turn 6 compaction fires and sets `last_compacted_turn=3`: turn 7 narrator loads turns 4, 5, 6. Turn 8 loads 5, 6, 7. Turn 9 loads 6, 7, 8. Never loads 1, 2, or 3 again.

---

#### Step 2.3 — Rewrite compaction band math in `maybe_compact`

**File:** `ccya/engine/compactor.py`

**What:** Rewrite the trigger and band calculation. Critical fix: set `last_compacted_turn = compact_end` not `current_turn`.

**Why:** The current code sets `last_compacted_turn = current_turn` which causes the next compaction cycle to compute `compact_start = current_turn + 1` — skipping all the turns between the old compact_end and the current trigger. This is the root redundancy bug.

**Code Snippet**
```python
async def maybe_compact(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
) -> dict[str, Any]:
    """Run compaction if current turn triggers it.

    Trigger: current_turn % compact_every == 0.
    Compacts turns [last_compacted_turn+1 .. retain_from-1].
    retain_from = max(1, current_turn - window_turns + 1).
    Sets last_compacted_turn = compact_end (NOT current_turn).
    """
    if config.compact_every <= 0:
        return state

    current_turn = int((state.get("meta") or {}).get("turn", 0) or 0)
    if current_turn == 0:
        return state

    if current_turn % config.compact_every != 0:
        return state

    last_compacted_turn = int((state.get("meta") or {}).get("last_compacted_turn", 0) or 0)
    retain_from = max(1, current_turn - config.window_turns + 1)
    compact_end = retain_from - 1
    compact_start = last_compacted_turn + 1

    if compact_start > compact_end:
        _log.info(
            "compactor: nothing to compact at turn %d (compact_start=%d > compact_end=%d)",
            current_turn, compact_start, compact_end,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
        return state

    _log.info(
        "compactor: compacting turns %d–%d at turn %d (window=%d, compact_every=%d)",
        compact_start, compact_end, current_turn, config.window_turns, config.compact_every,
        extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
    )

    turns = _extract_turns_for_compact(save_dir, compact_start, compact_end)
    if not turns:
        return state

    # ... env setup, LLM call (unchanged) ...

    bullets_text, sanitization = _parse_compact_response(response_text)

    if not bullets_text.strip():
        _log.warning(
            "compactor: LLM returned empty bullets at turn %d, skipping",
            current_turn,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
        return state

    # Append to prior_history
    new_bullets = [b.strip() for b in bullets_text.splitlines() if b.strip()]
    state.setdefault("meta", {}).setdefault("prior_history", []).extend(new_bullets)

    # Mirror to chronicle.md for human readability
    _write_compacted_block(save_dir, bullets_text)

    # Apply sanitization (Pydantic-validated, allowlist-checked)
    if sanitization is not None:
        _apply_sanitization(state, sanitization)

    # THE FIX: set to compact_end, not current_turn
    state.setdefault("meta", {})["last_compacted_turn"] = compact_end

    return state
```

**Validation:**
- Turn 6, defaults: `retain_from=4`, `compact_end=3`, `compact_start=1`. Compacts 1–3. `last_compacted_turn=3`.
- Turn 12, defaults (after turn 6 set `last_compacted_turn=3`): `retain_from=10`, `compact_end=9`, `compact_start=4`. Compacts 4–9. `last_compacted_turn=9`.
- Turn 18: compacts 10–15. `last_compacted_turn=15`.

---

#### Step 2.4 — Update `_parse_compact_response` to return `CompactorSanitizationResult | None`

**File:** `ccya/engine/compactor.py`

**What:** Change return type to `tuple[str, CompactorSanitizationResult | None]`. Parse the last JSON object from the response, validate through `CompactorSanitizationResult.model_validate`. Return `None` on any parse/validation failure.

**Why:** Pydantic validation is the gate before state mutation. A `None` return means skip sanitization entirely.

**Code Snippet**
```python
from ccya.models import CompactorSanitizationResult
from pydantic import ValidationError

def _parse_compact_response(
    response_text: str,
) -> tuple[str, CompactorSanitizationResult | None]:
    """Parse LLM output into (bullet_lines_text, sanitization | None).

    Bullets: lines matching ^- \\[T\\d+\\]
    Sanitization: last JSON object in response, validated through CompactorSanitizationResult.
    """
    bullets = [
        line.strip()
        for line in response_text.splitlines()
        if _BULLET_RE.match(line.strip())
    ]
    bullets_text = "\n".join(bullets)

    # Find last JSON object (not array) in response
    last_open = response_text.rfind("{")
    sanitization: CompactorSanitizationResult | None = None
    if last_open >= 0:
        last_close = response_text.rfind("}", last_open)
        if last_close > last_open:
            candidate = response_text[last_open : last_close + 1]
            try:
                payload = json.loads(candidate)
                if isinstance(payload, dict):
                    sanitization = CompactorSanitizationResult.model_validate(payload)
            except (json.JSONDecodeError, ValueError, ValidationError) as exc:
                _log.warning("compactor: invalid sanitization payload, skipping: %s", exc)

    return bullets_text, sanitization
```

**Validation:** Response with valid bullets and `{}` → returns bullets text and `CompactorSanitizationResult()` (empty). Response with invalid JSON → returns bullets and `None`. Response with `{"npc_merge": "wrong"}` → Pydantic raises, returns `None`.

---

#### Step 2.5 — Add `_apply_sanitization` with allowlist validation

**File:** `ccya/engine/compactor.py`

**What:** New function. Before any mutation, build allowlists of all known IDs from current state. Skip any proposed ID not in the relevant allowlist. Log all applied operations. Apply: `npc_merge`, `inventory_remove`, `quest_close`, `pressure_remove`, `condition_remove`.

**Why:** Allowlist validation is the second defense layer after Pydantic. LLMs can hallucinate plausible-looking IDs that don't exist.

**Code Snippet**
```python
def _apply_sanitization(
    state: dict[str, Any],
    san: CompactorSanitizationResult,
) -> None:
    """Apply compactor sanitization to state in-place.

    Validates all IDs against allowlists built from current state.
    Unknown IDs are silently skipped. Never raises.
    """
    log_ctx = {"turn": state.get("meta", {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "compactor"}

    compendium_npcs: dict[str, Any] = (state.get("compendium") or {}).get("npcs") or {}
    inventory: list[dict[str, Any]] = list(state.get("inventory") or [])
    quests: list[dict[str, Any]] = list(state.get("quests") or [])
    pressures: list[dict[str, Any]] = list((state.get("scene") or {}).get("scene_pressure") or [])
    conditions: list[dict[str, Any]] = list((state.get("pc") or {}).get("conditions") or [])

    known_npc_ids = set(compendium_npcs.keys())
    known_inventory_ids = {it.get("id") for it in inventory if it.get("id")}
    known_quest_ids = {q.get("id") for q in quests if q.get("id")}
    known_pressure_ids = {p.get("id") for p in pressures if p.get("id")}
    known_condition_ids = {c.get("id") for c in conditions if c.get("id")}

    # npc_merge
    for merge in san.npc_merge:
        if merge.keep_id not in known_npc_ids:
            _log.warning("compactor: npc_merge keep_id %r unknown, skipping", merge.keep_id, extra=log_ctx)
            continue
        valid_remove = [rid for rid in merge.remove_ids if rid in known_npc_ids and rid != merge.keep_id]
        for rid in valid_remove:
            compendium_npcs.pop(rid, None)
            _log.info("compactor: merged duplicate NPC %r into %r", rid, merge.keep_id, extra=log_ctx)
        # Remove from present_npcs
        scene = state.setdefault("scene", {})
        remove_set = set(valid_remove)
        scene["present_npcs"] = [
            n for n in (scene.get("present_npcs") or [])
            if (n.get("id") if isinstance(n, dict) else n) not in remove_set
        ]

    # inventory_remove
    valid_inv_remove = {iid for iid in san.inventory_remove if iid in known_inventory_ids}
    if valid_inv_remove:
        state["inventory"] = [it for it in inventory if it.get("id") not in valid_inv_remove]
        for iid in valid_inv_remove:
            _log.info("compactor: removed duplicate inventory item %r", iid, extra=log_ctx)

    # quest_close (only active quests)
    valid_quest_close = {qid for qid in san.quest_close if qid in known_quest_ids}
    for q in quests:
        if q.get("id") in valid_quest_close and q.get("status") == "active":
            q["status"] = "completed"
            _log.info("compactor: closed orphaned quest %r", q.get("id"), extra=log_ctx)

    # pressure_remove
    valid_pressure_remove = {pid for pid in san.pressure_remove if pid in known_pressure_ids}
    if valid_pressure_remove:
        scene = state.setdefault("scene", {})
        scene["scene_pressure"] = [p for p in pressures if p.get("id") not in valid_pressure_remove]
        for pid in valid_pressure_remove:
            _log.info("compactor: removed stale pressure %r", pid, extra=log_ctx)

    # condition_remove
    valid_cond_remove = {cid for cid in san.condition_remove if cid in known_condition_ids}
    if valid_cond_remove:
        pc = state.setdefault("pc", {})
        pc["conditions"] = [c for c in conditions if c.get("id") not in valid_cond_remove]
        for cid in valid_cond_remove:
            _log.info("compactor: removed resolved condition %r", cid, extra=log_ctx)
```

**Validation:** State with `compendium.npcs = {"a": {...}, "b": {...}}`. Call with `npc_merge=[{keep_id:"a", remove_ids:["b","c"]}]`. Assert `"b"` removed (known), `"c"` skipped (unknown). Assert `"a"` untouched.

---

### Tests to write or update
- `tests/test_compactor.py::test_chronicle_loader_min_turn_exclusive_filter`
- `tests/test_compactor.py::test_narrator_desired_recent_computation` (parametrize with the full validation table from Step 2.2)
- `tests/test_compactor.py::test_maybe_compact_turn6_compacts_1_to_3_sets_last_compacted_3`
- `tests/test_compactor.py::test_maybe_compact_turn12_compacts_4_to_9_sets_last_compacted_9`
- `tests/test_compactor.py::test_parse_response_returns_none_on_bad_json`
- `tests/test_compactor.py::test_parse_response_returns_none_on_validation_error`
- `tests/test_compactor.py::test_apply_sanitization_skips_unknown_npc_ids`
- `tests/test_compactor.py::test_apply_sanitization_merges_known_duplicate_npc`
- `tests/test_compactor.py::test_apply_sanitization_removes_known_inventory_item`
- `tests/test_compactor.py::test_apply_sanitization_closes_only_active_quests`
- `tests/test_compactor.py::test_apply_sanitization_skips_unknown_pressure_id`
- `tests/test_compactor.py::test_maybe_compact_does_not_touch_recent_events`
- `tests/test_engine_pipeline.py::test_narrator_context_excludes_compacted_turns_after_turn6`

### REPOMAP updates required
- `docs/REPOMAP/state.md`: update `load_recent_chronicle_turns` signature with `min_turn_exclusive`.
- `docs/REPOMAP/engine.md`: document corrected `maybe_compact` trigger/band math; document `_parse_compact_response` new return type; add `_apply_sanitization`.

### Risks
1. `turn.py` may call `load_recent_chronicle_turns` in more than one place. Executor must grep for all call sites and update each one.
2. With `compact_every=6`, the first compaction at turn 6 compacts a 3-turn band (turns 1–3). The second at turn 12 compacts a 6-turn band (turns 4–9). This asymmetry is intentional and correct. Tests must document this explicitly so it is not accidentally "fixed" to equal-size batches.
3. The `current_turn` value in `turn.py` during narrator prompt assembly may reflect the turn currently being generated, not yet written to chronicle. The `last_compacted_turn` should be read from state which reflects completed turns. Executor must verify the exact moment `state["meta"]["turn"]` is incremented in the turn pipeline.

---

## Implementation — Phase 3: Prompt contract

### Context files to load
- `AGENTS.md`
- `docs/REPOMAP/prompts.md`
- `ccya/prompts/compact_system.j2`
- `ccya/prompts/compact_user.j2`
- `ccya/engine/compactor.py` (post Phase 2)
- `ccya/models.py` (post Phase 1)

### Overview
Replace the prompt contract to match the new two-part output (bullets + sanitization JSON). Remove the previous `PART 2: recent events` section entirely. Update the user template to include all mechanical state with exact IDs so the LLM can ground sanitization proposals.

### Detailed steps

#### Step 3.1 — Rewrite `compact_system.j2`

**File:** `ccya/prompts/compact_system.j2`

**What:** Replace entire file content with the spec below. Remove any instruction about outputting a recent-events JSON array. Require the sanitization object to be the last thing in the response.

**Why:** The old prompt drove the `recent_events` mutation path which is being removed. The new prompt drives the bullet + sanitization contract.

**Code Snippet**
```jinja2
You are a game historian and consistency editor for a TTRPG session.

Your output has two parts:
1. One bullet per compacted turn.
2. One JSON object with state sanitization actions (or {}).

The JSON object must be the last thing in your response, after a blank line.

---

## PART 1: Prior-history bullets

Compress each full-turn narrative into one bullet. These are internal session notes — the player never reads them directly.

### Preserve
- Named NPCs: first mention, role, and any title
- Location the turn took place in
- Quest outcomes: resolved, failed, new leads uncovered
- Key items: gained, lost, consumed
- Condition changes: gained or cleared
- Irreversible player choices
- Death or departure of named characters
- Any mechanical consequence that affects future play (alliances, enmities, oaths)

### Cull
- Atmospheric setting description that repeats across turns
- Dialogue without durable consequence
- Combat blow-by-blow (keep opponent and outcome, not round-by-round)
- Uneventful rest/travel that produced no outcome

### Format
`- [T{n}] {1–2 sentence summary}`

One bullet per turn. If a turn was uneventful, write `- [T{n}] Uneventful — no mechanical changes.`

---

## PART 2: State sanitization

You have the full mechanical state. Identify structural problems that should be fixed.
Only flag problems you are **highly confident** about — false positives cause data loss.
When uncertain, omit.

### What to flag

**npc_merge** — Two compendium NPC entries that are clearly the same person under different IDs (same name, same role, consistent bios). Provide `keep_id` (canonical) and `remove_ids` (duplicates).

**inventory_remove** — An inventory item that appears twice with different IDs but identical name and purpose. Provide the ID of the copy to remove (keep the one with higher amount or richer notes).

**quest_close** — An active quest whose objectives are all `done: true` but the quest was never closed, OR a quest whose narrative conclusively ended multiple turns ago per the bulletin.

**pressure_remove** — A `scene_pressure` entry whose triggering situation has been fully resolved per the bulletin (e.g. the chase is over, the deadline passed).

**condition_remove** — A `pc.condition` that the bulletin clearly shows was cured or resolved. Do NOT remove conditions that might still plausibly apply.

### Output format

After the bullet lines and a blank line, output exactly one JSON object:

```json
{
  "npc_merge": [{"keep_id": "...", "remove_ids": ["..."]}],
  "inventory_remove": ["item_id"],
  "quest_close": ["quest_id"],
  "pressure_remove": ["pressure_id"],
  "condition_remove": ["condition_id"]
}
```

Omit any key whose list would be empty. If nothing needs fixing, output `{}`.

---

## Hard rules

- Never invent IDs. Every ID you write must appear verbatim in the MECHANICAL STATE section of the user message.
- Never propose a key not listed above.
- The JSON object must be the last thing you output.
- Output bullet lines first, then a blank line, then the JSON object. No other sections.
```

**Validation:** Render the template. Assert it contains `PART 1` and `PART 2` headings, no mention of `recent_events`, and the words `The JSON object must be the last thing`.

---

#### Step 3.2 — Rewrite `compact_user.j2`

**File:** `ccya/prompts/compact_user.j2`

**What:** Replace entire file. Remove `RECENT EVENTS TO COMPACT`. Add `TURNS TO COMPACT` and `MECHANICAL STATE` sections. All IDs must be rendered exactly as they appear in state so the LLM can reference them in sanitization output.

**Why:** The LLM needs exact IDs to produce usable sanitization output. Without them it guesses, and guessed IDs are caught by the allowlist check in Phase 2 — but the action is wasted.

**Code Snippet**
```jinja2
## TURNS TO COMPACT

{% for t in turns -%}
### Turn {{ t.turn }} — {{ t.input }}
{{ t.narrative }}

{% endfor -%}

## ACTIVE CONTEXT

{% if active_quests -%}
### Active Quests
{% for q in active_quests -%}
- **[{{ q.get("id", "?") }}] {{ q.get("title", "?") }}**
{% for obj in (q.get("objectives") or []) -%}
  - [{{ "x" if obj.get("done") else " " }}] {{ obj.get("description", "?") }}
{% endfor -%}
{% endfor %}
{% endif -%}

{% if npc_names -%}
### Present NPCs
{{ npc_names | join(", ") }}
{% endif -%}

{% if pressures -%}
### Active Scene Pressures
{% for p in pressures -%}
- [{{ p.get("id", "?") }}] [{{ p.get("urgency", "").upper() }}] {{ p.get("text", p) }}
{% endfor %}
{% endif -%}

## MECHANICAL STATE
*(Read-only reference for sanitization. Use exact IDs shown.)*

### Inventory
{% for item in inventory -%}
- [{{ item.get("id", "?") }}] {{ item.get("name", "?") }}{% if item.get("amount", 1) != 1 %} ×{{ item.get("amount") }}{% endif %}{% if item.get("notes") %}: {{ item.get("notes") }}{% endif %}

{% else -%}
(empty)
{% endfor %}

### Compendium NPCs
{% for npc_id, npc in compendium_npcs -%}
- [{{ npc_id }}] {{ npc.get("name", "?") }}{% if npc.get("title") %} ({{ npc.get("title") }}){% endif %}{% if npc.get("aliases") %} aka {{ npc.get("aliases") | join(", ") }}{% endif %}

{% else -%}
(none)
{% endfor %}

### All Quests
{% for q in all_quests -%}
- [{{ q.get("id", "?") }}] {{ q.get("title", "?") }} — {{ q.get("status", "?") }}
{% else -%}
(none)
{% endfor %}

### PC Conditions
{% for c in conditions -%}
- [{{ c.get("id", "?") }}] {{ c.get("label", "?") }}: {{ c.get("description", "") }}
{% else -%}
(none)
{% endfor %}
```

**Note for executor:** The `_build_compact_messages` function in `compactor.py` (updated in Phase 2 Step 2.2) must pass `inventory`, `compendium_npcs`, `all_quests`, `conditions`, and `pressures` to the template. Verify all template variables are supplied by the Python render call.

**Validation:** Render with a sample state containing known IDs. Assert every inventory item ID appears in the rendered text. Assert no `RECENT EVENTS TO COMPACT` section appears.

---

### Tests to write or update
- `tests/test_compactor.py::test_system_prompt_contains_part1_and_part2_no_recent_events`
- `tests/test_compactor.py::test_user_prompt_renders_inventory_ids`
- `tests/test_compactor.py::test_user_prompt_renders_compendium_npc_ids`
- `tests/test_compactor.py::test_build_compact_messages_supplies_all_template_vars`

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: update `compact_system.j2` description (PART 1 bullets, PART 2 sanitization JSON); update `compact_user.j2` description (turns + mechanical state).

### Risks
1. Jinja2 tuple unpacking `{% for npc_id, npc in compendium_npcs %}` requires `compendium_npcs` to be a list of 2-tuples. The Phase 2 Python code passes `list((state.get("compendium") or {}).get("npcs", {}).items())` which produces this format. Executor must verify this is correct for the installed Jinja2 version.
2. A large compendium may push the prompt over token budget. The compactor call does not go through `trim_messages`. Acceptable for now — add a REPOMAP note that token trimming may be needed at scale.

---

## Ambiguities requiring resolution before execution

1. **Compendium field corrections.** The user mentioned `last_seen_state` and `last_location`-style NPC fields as targets for sanitization correction. These fields are NOT included in this plan because their exact names have not been verified in source. Executor must check `compendium.npcs` schema before execution. Options: A) keep scope as-is (dedup/cleanup only); B) add verified field correction to `CompactorSanitizationResult` and `_apply_sanitization` after confirming exact field names in source. Recommended: B, but only after source verification. Do not proceed to field corrections if the fields do not exist exactly as expected.

2. **`current_turn` timing in `turn.py`.** The `state["meta"]["turn"]` increment timing relative to the narrator prompt assembly call must be verified by the executor. If `turn` is already incremented before `load_recent_chronicle_turns` is called, then `current_turn_completed = state["meta"]["turn"] - 1` (since the current turn hasn't been written yet). If not yet incremented, use `state["meta"]["turn"]` directly. The validation table in Step 2.2 assumes completed-turn semantics. The executor must confirm the correct value before implementing.

---

## TODO.md update

Find the existing compactor-related TODO entry (if any) under `## P1` and replace it with:

```markdown
- [ ] **Compactor overhaul** — stable narrator window (`window_turns: 3`, `compact_every: 6`, `recent_turns_min: 2`), `meta.prior_history` canonical store, corrected `last_compacted_turn` math (root bug fix), Pydantic-validated sanitization (NPC dedup, inventory dedup, orphaned quest/pressure/condition cleanup), narrator no longer receives compacted turns — see [`compactor-overhaul.md`](compactor-overhaul.md)
```
