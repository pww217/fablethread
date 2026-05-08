
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

**Code Snippet** (replace the location_changed purge block):
```python
if location_changed:
    _log.debug(
        "pressure.purge: location changed — removing background pressures only",
        extra={"turn": turn_no},
    )
    before = list(pressures)
    pressures[:] = [
        p for p in pressures
        if p.get("urgency") not in (None, "background")
    ]
    removed = [p["id"] for p in before if p not in pressures]
    if removed:
        _log.info(
            "pressure.purge: auto-removed background pressures on location change: %s",
            removed,
            extra={"turn": turn_no},
        )
```

Note: read the actual function signature and `state`/`delta` access pattern from `pressure.py` before writing the final code — the snippet above is the logic; adapt variable names to match the file.

**Validation:** Write a unit test: create a state with one `immediate` and one `background` pressure, call `_purge_scene_pressures` with `location_changed=True`, assert `immediate` pressure survives and `background` pressure is removed.

---

## Implementation — Phase 3: Rules prompt carve-out

### Context files to load
- `ccya/prompts/rules_system.j2`
- `ccya/prompts/rules_user.j2`

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
def test_purge_preserves_immediate_on_location_change():
    state = {"scene": {"scene_pressure": [
        {"id": "guards_hunting", "urgency": "immediate", "text": "Guards on alert", "turn_added": 1},
        {"id": "fog_ahead", "urgency": "background", "text": "Dense fog", "turn_added": 1},
    ]}}
    delta = ... # minimal delta with location_change set
    _purge_scene_pressures(state, delta, location_changed=True, ...)
    ids = [p["id"] for p in state["scene"]["scene_pressure"]]
    assert "guards_hunting" in ids
    assert "fog_ahead" not in ids

def test_purge_preserves_building_on_location_change():
    # same pattern, urgency="building"
    ...
```

**File:** `tests/test_rules_prompt.py` (create or extend — FakeLLM pattern)
```python
def test_rules_no_check_for_fixed_price_transaction():
    # Render rules_user.j2 with input "Pay the dock fee" and minimal state.
    # Use FakeLLM returning {"intent": "...", "check": {"required": false}}.
    # Assert intent.check.required is False.
    ...
```

### REPOMAP updates required
`docs/REPOMAP/pressure.md` — add a section documenting the urgency-based location-change guard behavior.

### Risks
1. **`_purge_scene_pressures` signature** — must read the actual function before implementing the guard; the current purge logic may not have the same variable structure as assumed.
2. **Rules prompt carve-out too broad** — the "willing/commercially neutral" qualifier must be narrow. Negotiating a price, haggling, or dealing with a hostile/suspicious NPC still requires a check. The word "stated or clearly implied fixed price" is the limiting clause.

## Ambiguities requiring resolution before execution
None.

## TODO.md update
Under `## P1 — Active`:
Scene pressure lifecycle rules — docs/plans/eval-results-remediation/eval-results-remediation-pressure-rules.md