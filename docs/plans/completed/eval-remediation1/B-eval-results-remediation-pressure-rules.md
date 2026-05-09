# Scene Pressure Lifecycle Rules Remediation

## Status
`open`

## Part of
`eval-results-remediation`

## Dependencies
- Plan A (`eval-results-remediation-pipeline-field-routing.md`) must be complete. After Plan A, `scene_pressure_*` lives in `SceneExtractResult` and is governed by `extract_scene_system.j2`. This plan's prompt changes target that file.

## Objective
The eval runs identified two pressure lifecycle failures: (1) pressure was removed on location change even when the underlying threat was unresolved, and (2) a fixed-price transaction with a willing NPC triggered a dice check, causing a pressure entry to be added/retained for a routine social exchange. This plan adds a "survival check" requirement for pressure removal, a location-change guard in the engine, and a no-check transaction carve-out in the rules prompt.

## Non-goals
- Does NOT change the `scene_pressure` data model (`ScenePressure`).
- Does NOT change pressure expiry/escalation logic (`_expire_scene_pressures`).
- Does NOT change the pressure purge-on-combat-end logic.
- Does NOT touch quest logic, NPC logic, or any other field in any extractor.
- Does NOT change `EngineConfig` fields.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/extract_scene_system.j2` | modify | Add "survival check" rule for `scene_pressure_remove`; add location-change guard |
| `ccya/engine/pressure.py` | modify | Add location-change guard in `_purge_scene_pressures`: never auto-purge pressures on location change alone when `urgency == "immediate"` |
| `ccya/prompts/rules_system.j2` | modify | Add carve-out: fixed-price transactions with a willing/neutral NPC do not require a check |
| `docs/REPOMAP/engine.md` | update | Document urgency-based location-change guard in `_purge_scene_pressures` |
| `docs/plans/TODO.md` | update | Add this plan |

## Firm decisions

1. **Pressure removal requires narrative evidence that the threat itself is gone**, not just that the player succeeded on a roll or changed location. The scene extractor prompt must say this explicitly.
2. **Location change does not auto-remove `immediate` or `building` pressures** unless the narration shows the threat cannot follow (e.g., "the guards are locked behind the sealed gate"). A `background` pressure may lapse on location change.
3. **The engine-side `_purge_scene_pressures`** currently purges all pressures on location change. This is too aggressive. After this plan, it only auto-purges `background` pressures on location change; `immediate` and `building` pressures survive location change and must be explicitly removed by the scene extractor.
4. **Fixed-price payment to a willing NPC** (e.g., paying the dock fee, buying an item from a shopkeeper at stated price) is not a charisma/persuasion check. The rules prompt must enumerate this explicitly.
5. `target` and `stakes` are kept as outputs — they are useful for the `_log_rules_outcome` trace and for future judge evaluation. No change.

## Implementation — Phase 1: Pressure prompt rule

### Context files to load
- `ccya/prompts/extract_scene_system.j2` (post Plan A)

### Overview
Add two explicit sub-rules to the `scene_pressure_remove` field rule in the scene extractor system prompt: (1) the survival check requirement, (2) the location-change guard.

### Detailed steps

#### Step 1.1 — Extend `scene_pressure_remove` rule in `extract_scene_system.j2`

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the current one-line `scene_pressure_remove` description with the expanded version below. Insert immediately after the existing `scene_pressure_remove` line.

**Why:** The LLM was removing pressures because the player left the scene, even when the pressure (e.g., "guards are hunting you") was still active. It needs an explicit "did the threat itself resolve?" check before emitting a removal.

**Code Snippet** (replace the `scene_pressure_remove` line with):

scene_pressure_remove: IDs of pressures now resolved. Before emitting a removal, ask: did the narration show the underlying threat itself was eliminated? Examples of valid removal evidence: "the fire was extinguished", "the guards were evaded and the gates sealed behind you", "the bomb was defused". Examples of invalid removal evidence: "the player moved to a new location", "the player succeeded on a roll", "the threat is no longer mentioned". A location change alone NEVER justifies removing an immediate or building pressure — those can follow the player. A background pressure may be removed on location change only if the narration explicitly implies the source of the threat is in the now-left location.

**Validation:** Template renders without error. Run a test narration through the scene extractor with an active `immediate` pressure and a location change in the narration — assert `scene_pressure_remove` is empty.

---

## Implementation — Phase 2: Engine guard in `_purge_scene_pressures`

### Context files to load
- `ccya/engine/pressure.py`

### Overview
Read the existing `_purge_scene_pressures` function. Add a guard: on location change, only auto-purge pressures with `urgency == "background"`. Leave `immediate` and `building` pressures for the LLM extractor to decide.

### Detailed steps

#### Step 2.1 — Add urgency guard in `_purge_scene_pressures`

**File:** `ccya/engine/pressure.py`

**What:** In the `location_changed` branch of `_purge_scene_pressures`, add a filter so only `background` pressures are auto-removed. Read the current implementation first — the exact variable names may differ.

**Why:** The engine should not override the LLM extractor's pressure removal decision for active threats. It may still auto-purge stale background texture.

**Code Snippet** (replace the location_changed branch at lines 69-73):
```python
    if location_changed:
        for p in pressures:
            if isinstance(p, dict):
                urgency = p.get("urgency", "background")
                if urgency == "background":
                    delta.scene_pressure_remove.append(p.get("id", ""))
        return
```

The existing function uses `delta.scene_pressure_remove.append()` in a loop (not `pressures[:]` mutation) and has a `return` early-exit after the location_changed branch. The guard filters by `urgency == "background"` before appending to the delta, so only background pressures are auto-removed on location change. `immediate` and `building` pressures are left for the LLM extractor to decide.

**Validation:** Write a unit test: create a state with one `immediate` and one `background` pressure, call `_purge_scene_pressures` with `location_changed=True`, assert `immediate` pressure survives and `background` pressure is removed.

---

## Implementation — Phase 3: Rules prompt carve-out

### Context files to load
- `ccya/prompts/rules_system.j2`

### Overview
The rules system prompt already has a "Decision rule — default NO" section. Add a fourth carve-out condition for fixed-price commercial transactions with willing participants.

### Detailed steps

#### Step 3.1 — Add carve-out to `rules_system.j2`

**File:** `ccya/prompts/rules_system.j2`

**What:** After the existing "If the input is: idle observation, unimpeded movement..." sentence, add a new explicit exemption for fixed-price transactions.

**Why:** The rules engine was triggering charisma checks for "pay the dock fee" or "buy the item at the listed price." These are not contested social actions — the NPC has no reason to resist and the price is fixed. No check should be required.

**Code Snippet** (insert after the existing no-roll sentence):

If the player is paying a stated or clearly implied fixed price to a willing or commercially neutral NPC (buying goods at market price, paying a fee, tipping, settling a stated debt) — set check.required=false. No charisma roll is needed for routine commerce with a willing counterparty.


**Validation:** Construct a test where `user_input = "I pay the 50 credit dock fee to the harbormaster"` — the rules extractor must return `check.required: false`. Run it through `_call_rules` with a FakeLLM that returns compliant JSON.

---

### Tests to write or update

**File:** `tests/test_pressure.py` (create or extend)
```python
from typing import Any

from ccya.engine.pressure import _purge_scene_pressures
from ccya.models import StateDelta


def test_purge_preserves_immediate_on_location_change() -> None:
    state: dict[str, Any] = {"scene": {"scene_pressure": [
        {"id": "guards_hunting", "urgency": "immediate", "text": "Guards on alert", "turn_added": 1},
        {"id": "fog_ahead", "urgency": "background", "text": "Dense fog", "turn_added": 1},
    ]}}
    delta = StateDelta()
    _purge_scene_pressures(state, delta, location_changed=True)
    # immediate pressure survives (not in delta.remove list)
    assert "guards_hunting" not in delta.scene_pressure_remove
    # background pressure is auto-removed
    assert "fog_ahead" in delta.scene_pressure_remove


def test_purge_preserves_building_on_location_change() -> None:
    state: dict[str, Any] = {"scene": {"scene_pressure": [
        {"id": "wall_guard", "urgency": "building", "text": "Sentry at gate", "turn_added": 1},
        {"id": "distant_thunder", "urgency": "background", "text": "Thunder rumbling", "turn_added": 1},
    ]}}
    delta = StateDelta()
    _purge_scene_pressures(state, delta, location_changed=True)
    assert "wall_guard" not in delta.scene_pressure_remove
    assert "distant_thunder" in delta.scene_pressure_remove
```

**File:** `tests/test_engine_smoke.py` (extend — reuse existing `_FakeLLM` class)
```python
def test_rules_no_check_for_fixed_price_transaction() -> None:
    from ccya.models import StateDelta
    # _FakeLLM is defined at module level in test_engine_smoke.py
    fake = _FakeLLM(
        rules_response='{"intent": "commerce", "check": {"required": false}}'
    )
    # ... run through _call_rules with the rendered prompt ...
    # Assert intent.check.required is False
```

### REPOMAP updates required
`docs/REPOMAP/engine.md` — add a note about the urgency-based location-change guard in `_purge_scene_pressures` (only `background` pressures auto-purged on location change).

### Risks
1. **`_purge_scene_pressures` signature** — must read the actual function before implementing the guard; the current purge logic may not have the same variable structure as assumed.
2. **Rules prompt carve-out too broad** — the "willing/commercially neutral" qualifier must be narrow. Negotiating a price, haggling, or dealing with a hostile/suspicious NPC still requires a check. The word "stated or clearly implied fixed price" is the limiting clause.

## Ambiguities requiring resolution before execution
None.

## TODO.md update
Under `## P1 — Active`:
Scene pressure lifecycle rules — see [`eval-results-remediation/B-eval-results-remediation-pressure-rules.md`](eval-results-remediation/B-eval-results-remediation-pressure-rules.md)