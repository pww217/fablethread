# Mechanics: Pressure Decay, Momentum Floor, and Scene Cap

## Status
`open`

## Part of
standalone

## Dependencies
- none (can run in parallel with other plans)

## Objective
Three mechanical failures compound into the death spiral observed across every eval run: (1) pressure entries only escalate (background → simmering → immediate) but never decay on avoidance or time — once immediate, a pressure stays immediate indefinitely unless explicitly resolved, giving the player no mechanical path out; (2) the momentum floor is enforced in prompts only (narration-pacing-fixes.md fixes the prompt side) but has no engine-level consequence — momentum can stay at -3 for an unlimited number of turns; (3) immediate threats in combat are uncapped, allowing up to 7 simultaneous immediate pressures which overwhelm the narrator and break pacing. This plan adds a pressure age/decay pass, a momentum floor escalation, and a hard immediate-pressure cap to `pressure.py`.

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
| `ccya/engine/turn.py` | modify | Call `age_pressures()` after extractor delta application, before narrator render |
| `docs/REPOMAP/engine.md` | update | Document `age_pressures()` function signature and decay rules |

## Firm decisions

1. Pressure age is tracked in the existing `turns_active` field (already on the model per REPOMAP). No new fields.
2. Decay rule: a pressure that is `immediate` and has not been targeted by the player's `intent_verb` for 2 consecutive turns decays to `simmering`. A `simmering` pressure not targeted for 3 consecutive turns decays to `background`. A `background` pressure not targeted for 4 consecutive turns expires and is removed.
3. Targeting is defined as: the pressure's `entity_id` appears in the narration's `present_npcs`, OR the player's `intent_verb` is `fight`, `flee`, `negotiate`, `hide`, or `distract` (i.e., any engagement verb).
4. Immediate-pressure cap: maximum 3 simultaneous `immediate` pressures. When a 4th would be added by the extractor, it is queued as `simmering` instead. The engine logs a `pressure_cap_downgrade` event.
5. Momentum floor: if momentum == -3 for 2 consecutive turns without improvement, the engine forces a `breathing_room` gm_beat override on the next turn regardless of what the progress extractor emitted. This is the engine safety valve — the prompt directive (narration-pacing-fixes.md) is the first line, this is the fallback.

## Implementation — Phase 1: pressure.py Decay Pass

### Context files to load
- `ccya/engine/pressure.py`
- `ccya/engine/turn.py`
- `docs/REPOMAP/engine.md`

### Overview
Add `age_pressures(state, player_intent_verb, narration_present_npcs)` to `pressure.py`. It increments `turns_active` on every active pressure, applies decay rules, removes expired pressures, and enforces the immediate cap. Returns a list of `PressureEvent` log entries for telemetry.

### Detailed steps

#### Step 1.1 — Add age_pressures() to pressure.py

**File:** `ccya/engine/pressure.py`

**What:** Add a new top-level function `age_pressures()`. It must not modify state in place — it returns a tuple of `(updated_pressures: list[Pressure], events: list[dict])`.

**Why:** Separating the aging pass from the extractor delta application ensures that decay is deterministic and auditable, not dependent on model output.

**Code Snippet:**
```python
ENGAGEMENT_VERBS = {"fight", "flee", "negotiate", "hide", "distract", "attack", "defend"}

DECAY_THRESHOLDS = {
    "immediate": 2,   # turns unengaged before dropping to simmering
    "simmering": 3,   # turns unengaged before dropping to background
    "background": 4,  # turns unengaged before expiry
}

URGENCY_ORDER = ["immediate", "simmering", "background"]

def _is_engaged(pressure: "Pressure", intent_verb: str, present_npc_ids: set[str]) -> bool:
    if intent_verb in ENGAGEMENT_VERBS:
        return True
    if pressure.entity_id and pressure.entity_id in present_npc_ids:
        return True
    return False

def age_pressures(
    pressures: list["Pressure"],
    intent_verb: str,
    present_npc_ids: set[str],
) -> tuple[list["Pressure"], list[dict]]:
    updated: list["Pressure"] = []
    events: list[dict] = []
    present_set = set(present_npc_ids)

    for p in pressures:
        engaged = _is_engaged(p, intent_verb, present_set)
        if engaged:
            # Reset age counter on engagement
            p = p.model_copy(update={"turns_active": 0})
            updated.append(p)
            continue

        new_turns = p.turns_active + 1
        threshold = DECAY_THRESHOLDS.get(p.urgency, 99)

        if new_turns >= threshold:
            current_idx = URGENCY_ORDER.index(p.urgency)
            if current_idx == len(URGENCY_ORDER) - 1:
                # background expired
                events.append({"kind": "pressure_expired", "pressure_id": p.id, "reason": "unengaged"})
                continue  # drop from updated list
            else:
                new_urgency = URGENCY_ORDER[current_idx + 1]
                events.append({
                    "kind": "pressure_decayed",
                    "pressure_id": p.id,
                    "from": p.urgency,
                    "to": new_urgency,
                })
                p = p.model_copy(update={"urgency": new_urgency, "turns_active": 0})
        else:
            p = p.model_copy(update={"turns_active": new_turns})

        updated.append(p)

    return updated, events
```

**Validation:** Write a unit test with a pressure at `immediate`, `turns_active=1`, no engagement. After one call, `turns_active` should be 2. After a second call, urgency should be `simmering` and `turns_active` should be 0.

***

#### Step 1.2 — Enforce immediate cap in age_pressures

**File:** `ccya/engine/pressure.py`

**What:** After the aging/decay pass, add a post-pass that enforces the cap: if more than 3 pressures remain at `immediate`, downgrade the excess (oldest by `turns_active`) to `simmering`.

**Why:** The cap prevents the narrator from being overwhelmed with 7 simultaneous immediate threats, which produces incoherent narration and forces the model to pick arbitrary ones to honor.

**Code Snippet:**
```python
# After the main loop in age_pressures(), before return:
immediate_list = [p for p in updated if p.urgency == "immediate"]
if len(immediate_list) > 3:
    # Sort by turns_active descending — oldest first to downgrade
    to_downgrade = sorted(immediate_list, key=lambda x: x.turns_active, reverse=True)[3:]
    downgrade_ids = {p.id for p in to_downgrade}
    capped = []
    for p in updated:
        if p.id in downgrade_ids:
            events.append({
                "kind": "pressure_cap_downgrade",
                "pressure_id": p.id,
                "from": "immediate",
                "to": "simmering",
            })
            p = p.model_copy(update={"urgency": "simmering", "turns_active": 0})
        capped.append(p)
    updated = capped
```

**Validation:** Test with 4 immediate pressures. After `age_pressures()`, exactly 3 remain immediate and 1 is simmering. Events list contains one `pressure_cap_downgrade`.

***

#### Step 1.3 — Call age_pressures in turn.py

**File:** `ccya/engine/turn.py`

**What:** After extractor delta application and before `_narrate_messages()` is called, invoke `age_pressures()` with the current state, the intent verb from rules output, and the present NPC ids from state.

**Why:** The aging pass must happen after extractors have added new pressures for this turn, but before the narrator receives the updated pressure list. This ensures the narrator always sees the post-decay, capped pressure list.

**Code Snippet:**
```python
from ccya.engine.pressure import age_pressures

# After apply_deltas() / after extractor results applied:
updated_pressures, pressure_events = age_pressures(
    pressures=state.scene.scene_pressure,
    intent_verb=rules_result.intent_verb,
    present_npc_ids={npc.id for npc in state.scene.present_npcs},
)
state = state.model_copy(
    update={"scene": state.scene.model_copy(update={"scene_pressure": updated_pressures})}
)
for evt in pressure_events:
    log_event(evt)  # use existing log_event pattern
```

**Validation:** Run a full turn where a pressure was added last turn and player did not engage it. Confirm `turns_active` incremented in state. Run 2 consecutive non-engagement turns on an immediate pressure. Confirm it decays to simmering.

***

## Implementation — Phase 2: Momentum Floor Engine Fallback

### Context files to load
- `ccya/engine/turn.py`
- `docs/REPOMAP/engine.md`

### Overview
Add a momentum floor tracker that counts consecutive turns at -3. On the second consecutive floor turn, override the GM beat to `breathing_room` regardless of extractor output. Reset the counter when momentum rises above -3.

### Detailed steps

#### Step 2.1 — Add consecutive_floor_turns to run_turn state tracking

**File:** `ccya/engine/turn.py`

**What:** Track `consecutive_floor_turns` as a local variable across turns. This does not need to be persisted in `GameState` — it can be derived from `recent_events` or tracked in a turn-scoped counter. The simplest approach: check `state.momentum` before and after application. If momentum == -3 after application and was == -3 before application, increment a counter stored in `state.metadata` or derived from the last 2 events in `events.jsonl`.

**Why:** The prompt directive (narration-pacing-fixes.md) tells the narrator to give relief, but a stubborn model may still stack failures. The engine override is the hard fallback.

**Code Snippet:**
```python
# After extractor application, before narrator call:
MOMENTUM_FLOOR = -3
FLOOR_OVERRIDE_THRESHOLD = 2

# Derive consecutive floor turns from recent events (last 2 turns)
recent_momentum_values = [
    e.get("momentum_after")
    for e in get_recent_events(limit=2)  # use existing event log reader
    if "momentum_after" in e
]
consecutive_at_floor = sum(1 for m in recent_momentum_values if m == MOMENTUM_FLOOR)

if state.momentum == MOMENTUM_FLOOR and consecutive_at_floor >= FLOOR_OVERRIDE_THRESHOLD:
    # Override gm_beat to breathing_room
    if progress_result.gm_beat != "breathing_room":
        log_event({"kind": "momentum_floor_override", "original_beat": progress_result.gm_beat})
        progress_result = progress_result.model_copy(update={"gm_beat": "breathing_room"})
```

**Validation:** Run a test scenario with 3 consecutive -3 momentum turns. Confirm that on turn 3, `gm_beat` is forced to `breathing_room` in the event log, and the `momentum_floor_override` event is emitted.

***

### Tests to write or update
- `tests/test_pressure.py`: decay threshold tests for each urgency level.
- `tests/test_pressure.py`: immediate cap test (4 immediate in → 3 immediate out, 1 event emitted).
- `tests/test_pressure.py`: engagement reset test (immediate pressure at turns_active=1, engaged → turns_active=0).
- `tests/test_turn.py`: momentum floor override test (3 consecutive -3 momentum → gm_beat overridden).

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: add `age_pressures(pressures, intent_verb, present_npc_ids) -> (list[Pressure], list[dict])` under `pressure.py` functions; document `ENGAGEMENT_VERBS`, `DECAY_THRESHOLDS`, immediate cap rule.
- `docs/REPOMAP/engine.md`: document `momentum_floor_override` logic in `turn.py`.

### Risks
1. **Engagement verb list too narrow** — if player uses a synonym not in `ENGAGEMENT_VERBS`, pressure won't reset. Mitigation: the list is conservative by design; prefer false positives (treating engagement as non-engagement) over false negatives.
2. **Pressure decay too aggressive** — if a simmering pressure decays before the player can address it, quests may silently lose their threat context. Mitigation: the thresholds (2/3/4 turns) are deliberately conservative. Tune in eval after first run.
3. **`get_recent_events(limit=2)`** — executor must use the actual event log reader function name from `turn.py` or `events.py`. Do not invent a function call.

## Ambiguities requiring resolution before execution
1. What is the actual function/method for reading recent events from `events.jsonl` in `turn.py`? Options: A) A dedicated reader function in `ccya/engine/events.py`. B) Direct file read in `turn.py`. Executor must grep for the pattern before implementing the floor counter.
2. Does `Pressure` have a `turns_active` field already? The REPOMAP mentions it but executor must confirm it exists in the Pydantic model before using it. If absent, add it as `turns_active: int = 0`.

## TODO.md update
Add under **P1 — Critical Bugs**:
```
- [ ] [Mechanics: Pressure Decay, Momentum Floor, Scene Cap](plans/mechanics-pressure-decay.md)
```
