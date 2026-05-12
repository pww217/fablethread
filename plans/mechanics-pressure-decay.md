# Mechanics: Pressure Decay, Momentum Floor, and Scene Cap

## Status
`open`

## Part of
standalone

## Dependencies
- none (can run in parallel with other plans)

## Objective
Three mechanical failures compound into the death spiral observed across every eval run: (1) pressure entries only escalate (background → building → immediate) but never decay on avoidance or time — once immediate, a pressure stays immediate indefinitely unless explicitly resolved, giving the player no mechanical path out; (2) the momentum floor is enforced in prompts only (narration-pacing-fixes.md fixes the prompt side) but has no engine-level consequence — momentum can stay at -3 for an unlimited number of turns; (3) immediate threats in combat are uncapped, allowing up to 7 simultaneous immediate pressures which overwhelm the narrator and break pacing. This plan adds a pressure age/decay pass, a momentum floor escalation, and a hard immediate-pressure cap to `pressure.py`.

## Non-goals
- Does not change pressure schema fields (no new Pydantic model changes).
- Does not change how pressures are added — only how they age and expire.
- Does not touch the narrator or extractor prompts (those are handled in prompt plans).
- Does not change dice resolution or band logic.
- Does not address quest-over-completion (separate prompting concern).

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/engine/pressure.py` | modify | Add `age_pressures()` pass: increment `turns_active`, decay urgency on non-engagement, cap immediate count at 3 |
| `ccya/engine/turn.py` | modify | Call `age_pressures()` after extractor delta application, before compaction |
| `docs/REPOMAP/engine.md` | update | Document `age_pressures()` function signature and decay rules |

## Firm decisions

1. Pressure age is tracked by computing `current_turn - turn_added` from the existing `turn_added` field on `ScenePressure`. No new model fields. The `turn_added` field already exists on `ScenePressure` per `ccya/models.py:382`.
2. Decay rule: a pressure that is `immediate` and has not been targeted by the player's `intent_verb` for 2 consecutive turns decays to `building`. A `building` pressure not targeted for 3 consecutive turns decays to `background`. A `background` pressure not targeted for 4 consecutive turns expires and is removed. Urgency values are `Literal["immediate", "building", "background"]` per `ccya/models.py:381`.
3. Targeting is defined as: the pressure's `entity_id` appears in the narration's `present_npcs`, OR the player's `intent_verb` is `fight`, `flee`, `negotiate`, `hide`, or `distract` (i.e., any engagement verb).
4. Immediate-pressure cap: maximum 3 simultaneous `immediate` pressures. When a 4th would be added by the extractor, it is queued as `building` instead. The engine logs a `pressure_cap_downgrade` event via `append_event`.
5. Momentum floor: if momentum == -3 for 2 consecutive turns without improvement, the engine forces a `breathing_room` gm_beat override on the next turn regardless of what the progress extractor emitted. This is the engine safety valve — the prompt directive (narration-pacing-fixes.md) is the first line, this is the fallback.

## Implementation — Phase 1: pressure.py Decay Pass

### Context files to load
- `ccya/engine/pressure.py`
- `ccya/engine/turn.py`
- `ccya/models.py` (for `ScenePressure` model)
- `docs/REPOMAP/engine.md`

### Overview
Add `age_pressures(state, pressures, intent_verb, present_npc_ids)` to `pressure.py`. It computes age from `turn_added`, applies decay rules, removes expired pressures, and enforces the immediate cap. Returns a list of updated `ScenePressure` dicts and a list of event dicts for logging.

### Detailed steps

#### Step 1.1 — Add age_pressures() to pressure.py

**File:** `ccya/engine/pressure.py`

**What:** Add a new top-level function `age_pressures()`. It must not mutate state in place — it returns a tuple of `(updated_pressures: list[dict], events: list[dict])`.

**Why:** Separating the aging pass from the extractor delta application ensures that decay is deterministic and auditable, not dependent on model output.

**Code Snippet:**
```python
ENGAGEMENT_VERBS = frozenset({
    "fight", "flee", "negotiate", "hide", "distract", "attack", "defend",
})

DECAY_THRESHOLDS = {
    "immediate": 2,   # turns unengaged before dropping to building
    "building": 3,    # turns unengaged before dropping to background
    "background": 4,  # turns unengaged before expiry
}

URGENCY_ORDER = ["immediate", "building", "background"]


def _is_engaged(pressure: dict, intent_verb: str, present_npc_ids: set[str]) -> bool:
    if intent_verb in ENGAGEMENT_VERBS:
        return True
    entity_id = pressure.get("entity_id")
    if entity_id and entity_id in present_npc_ids:
        return True
    return False


def age_pressures(
    pressures: list[dict],
    intent_verb: str,
    present_npc_ids: set[str],
) -> tuple[list[dict], list[dict]]:
    """Age pressures, decay urgency on non-engagement, remove expired.

    Args:
        pressures: list of pressure dicts (from state["scene"]["scene_pressure"]).
        intent_verb: the player's intent verb from rules output.
        present_npc_ids: set of NPC ids present in the scene this turn.

    Returns:
        (updated_pressures, events) where events contains log entries for
        pressure_decayed, pressure_expired, and pressure_cap_downgrade.
    """
    updated: list[dict] = []
    events: list[dict] = []
    present_set = set(present_npc_ids)

    for p in pressures:
        if not isinstance(p, dict):
            continue
        engaged = _is_engaged(p, intent_verb, present_set)
        if engaged:
            # Reset age counter on engagement
            p = dict(p)
            p["turns_active"] = 0
            updated.append(p)
            continue

        turn_added = p.get("turn_added", 0)
        if turn_added == 0:
            # Predate this tracking — skip aging
            updated.append(p)
            continue

        current_turn = p.get("_current_turn", 0)
        new_turns = current_turn - turn_added

        threshold = DECAY_THRESHOLDS.get(p.get("urgency", "background"), 99)

        if new_turns >= threshold:
            current_idx = URGENCY_ORDER.index(p.get("urgency", "background"))
            if current_idx == len(URGENCY_ORDER) - 1:
                # background expired
                events.append({
                    "kind": "pressure_expired",
                    "pressure_id": p.get("id", ""),
                    "reason": "unengaged",
                })
                continue  # drop from updated list
            else:
                new_urgency = URGENCY_ORDER[current_idx + 1]
                events.append({
                    "kind": "pressure_decayed",
                    "pressure_id": p.get("id", ""),
                    "from": p.get("urgency", "background"),
                    "to": new_urgency,
                })
                p = dict(p)
                p["urgency"] = new_urgency
                p["turns_active"] = 0
        else:
            p = dict(p)
            p["turns_active"] = new_turns

        updated.append(p)

    return updated, events
```

**Validation:** Write a unit test with a pressure at `immediate`, `turn_added=5`, `_current_turn=7` (age=2), no engagement. After one call, urgency should be `building` and `turns_active` should be 0.

***

#### Step 1.2 — Enforce immediate cap in age_pressures

**File:** `ccya/engine/pressure.py`

**What:** After the aging/decay pass, add a post-pass that enforces the cap: if more than 3 pressures remain at `immediate`, downgrade the excess (oldest by computed age) to `building`.

**Why:** The cap prevents the narrator from being overwhelmed with 7 simultaneous immediate threats, which produces incoherent narration and forces the model to pick arbitrary ones to honor.

**Code Snippet (append to age_pressures, before return):**
```python
    # --- Immediate pressure cap ---
    IMMEDIATE_CAP = 3
    immediate_list = [p for p in updated if p.get("urgency") == "immediate"]
    if len(immediate_list) > IMMEDIATE_CAP:
        # Sort by turns_active descending — oldest first to downgrade
        sorted_immediate = sorted(
            immediate_list,
            key=lambda x: x.get("turns_active", 0),
            reverse=True,
        )
        to_downgrade = sorted_immediate[IMMEDIATE_CAP:]
        downgrade_ids = {p.get("id") for p in to_downgrade}
        capped = []
        for p in updated:
            if p.get("id") in downgrade_ids:
                events.append({
                    "kind": "pressure_cap_downgrade",
                    "pressure_id": p.get("id", ""),
                    "from": "immediate",
                    "to": "building",
                })
                p = dict(p)
                p["urgency"] = "building"
                p["turns_active"] = 0
            capped.append(p)
        updated = capped
```

**Validation:** Test with 4 immediate pressures. After `age_pressures()`, exactly 3 remain immediate and 1 is building. Events list contains one `pressure_cap_downgrade`.

***

#### Step 1.3 — Call age_pressures in turn.py

**File:** `ccya/engine/turn.py`

**What:** After delta application and after `_purge_scene_pressures` / `_expire_scene_pressures`, invoke `age_pressures()` with the current state, the intent verb from rules output, and the present NPC ids from state.

**Why:** The aging pass must happen after extractors have added new pressures for this turn, and after purge/expire have run, but before compaction and persist. This ensures the narrator always sees the post-decay, capped pressure list.

**Code Snippet (add import at top of turn.py, after existing pressure import):**
```python
from ccya.engine.pressure import _expire_scene_pressures, _purge_scene_pressures, age_pressures
```

**Code Snippet (insert after line 617 in run_turn, after `_expire_scene_pressures` call):**
```python
            _expire_scene_pressures(state, delta, config)

            # --- Pressure aging pass ---
            _intent_verb = intent.intent_verb
            _present_ids = {npc.get("id", "") for npc in _present_npcs if isinstance(npc, dict)}
            _pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
            _current_turn = state.get("meta", {}).get("turn", 0) + 1
            _updated_pressures, _pressure_events = age_pressures(
                pressures=_pressures,
                intent_verb=_intent_verb,
                present_npc_ids=_present_ids,
            )
            # Stamp _current_turn on each pressure for next turn's computation
            for _p in _updated_pressures:
                _p["_current_turn"] = _current_turn
            state.setdefault("scene", {})["scene_pressure"] = _updated_pressures
            for _evt in _pressure_events:
                _log.info(
                    "pressure: %s", _evt.get("kind", ""),
                    extra={"turn": _current_turn, "trace_id": trace_id, "pack": "", "kind": "pressure"},
                )
```

**Validation:** Run a full turn where a pressure was added last turn and player did not engage it. Confirm `turns_active` / age is computed in state. Run 2 consecutive non-engagement turns on an immediate pressure. Confirm it decays to building.

***

## Implementation — Phase 2: Momentum Floor Engine Fallback

### Context files to load
- `ccya/engine/turn.py`
- `ccya/state/momentum.py`
- `docs/REPOMAP/engine.md`

### Overview
Add a momentum floor tracker that counts consecutive turns at -3. On the second consecutive floor turn, override the GM beat to `breathing_room` regardless of extractor output. Reset the counter when momentum rises above -3.

### Detailed steps

#### Step 2.1 — Add momentum floor override in run_turn

**File:** `ccya/engine/turn.py`

**What:** Track `consecutive_floor_turns` as a local variable derived from recent events. Check `state["pc"]["momentum"]` after delta application. If momentum == -3 and the previous turn also had momentum == -3, override `progress_result.gm_beat` to `breathing_room`.

**Why:** The prompt directive (narration-pacing-fixes.md) tells the narrator to give relief, but a stubborn model may still stack failures. The engine override is the hard fallback.

**Code Snippet (add after line 675 in run_turn, after `apply_delta`):**
```python
        # --- Momentum floor override ---
        MOMENTUM_FLOOR = -3
        _prev_events = load_recent_events(save_dir, 1)
        _prev_momentum = None
        if _prev_events:
            _prev_momentum = _prev_events[0].get("pc_momentum")
        _current_momentum = int((state.get("pc") or {}).get("momentum", 0))
        _consecutive_floor = 0
        if _current_momentum == MOMENTUM_FLOOR:
            _consecutive_floor = 1
            if _prev_momentum is not None and _prev_momentum == MOMENTUM_FLOOR:
                _consecutive_floor = 2
        if _consecutive_floor >= 2 and progress_result and progress_result.gm_beat:
            if progress_result.gm_beat.type != "breathing_room":
                _log.info(
                    "momentum: floor override to breathing_room (consecutive=%d)",
                    _consecutive_floor,
                    extra={"turn": _current_turn, "trace_id": trace_id, "pack": "", "kind": "momentum"},
                )
                _new_beat = progress_result.gm_beat.model_copy(update={"type": "breathing_room"})
                progress_result = progress_result.model_copy(update={"gm_beat": _new_beat})
```

**Note:** The event logged by `append_event` in `run_turn` already includes `rules.band` but does NOT include `pc_momentum`. To track momentum across turns, we need to either:
A) Add `pc_momentum` to the event dict written by `append_event` (recommended — one line change near line 747), OR
B) Read `state["pc"]["momentum"]` from the saved `state.yaml` before the turn's delta was applied.

Option A is cleaner. Add this line near line 747 in `run_turn`, after the `rules_event` dict is built:
```python
        event["pc_momentum"] = int((state.get("pc") or {}).get("momentum", 0))
```

**Validation:** Run a test scenario with 3 consecutive -3 momentum turns. Confirm that on turn 3, `gm_beat` is forced to `breathing_room` in the event log, and the `momentum_floor_override` event is emitted.

***

### Tests to write or update
- `tests/test_pressure.py`: decay threshold tests for each urgency level (immediate→building at 2 turns, building→background at 3 turns, background expiry at 4 turns).
- `tests/test_pressure.py`: immediate cap test (4 immediate in → 3 immediate out, 1 event emitted).
- `tests/test_pressure.py`: engagement reset test (immediate pressure at age=1, engaged → age resets to 0).
- `tests/test_turn.py`: momentum floor override test (3 consecutive -3 momentum → gm_beat overridden).

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: add `age_pressures(pressures, intent_verb, present_npc_ids) -> (list[dict], list[dict])` under `pressure.py` functions; document `ENGAGEMENT_VERBS`, `DECAY_THRESHOLDS`, immediate cap rule.
- `docs/REPOMAP/engine.md`: document `momentum_floor_override` logic in `turn.py`.

### Risks
1. **Engagement verb list too narrow** — if player uses a synonym not in `ENGAGEMENT_VERBS`, pressure won't reset. Mitigation: the list is conservative by design; prefer false positives (treating engagement as non-engagement) over false negatives.
2. **Pressure decay too aggressive** — if a building pressure decays before the player can address it, quests may silently lose their threat context. Mitigation: the thresholds (2/3/4 turns) are deliberately conservative. Tune in eval after first run.
3. **`load_recent_events` function name** — confirmed as `ccya.state.load_recent_events(save_dir, n)` imported from `ccya/state/chronicle.py:59`. Use this exact function.
4. **`ScenePressure` model has no `turns_active` field** — confirmed absent from `ccya/models.py:378-383`. Age is computed as `current_turn - turn_added` at call time, stored as `_current_turn` on each pressure dict for next-turn computation. No model changes needed.
5. **`_expire_scene_pressures` already escalates background→building→immediate** — the new `age_pressures` decay runs in the opposite direction (immediate→building→background). Both coexist: `_expire_scene_pressures` handles TTL-based escalation, `age_pressures` handles engagement-based decay. The decay pass runs after expire, so decay can undo escalation if the player ignored the pressure.
