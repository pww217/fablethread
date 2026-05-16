# Integration Test Plan

**Location:** `tests/integration/test_turn_pipeline.py`  
**Runner:** `pytest` with `pytest-asyncio`  
**LLM calls:** Zero — all five pipeline steps are mocked at the `llm_client` boundary  
**Status:** Planned

---

## Goals

1. Verify that `run_turn()` executes all five steps in order and produces a valid `StateDelta` for each.
2. Verify that state mutations accumulate correctly across multiple turns — specifically that the outputs of one turn's extractors become the inputs of the next turn's pipeline.
3. Verify that the Python-side systems (dice resolution, pressure lifecycle, condition TTL, inventory delta validation, quest health computation, NPC roster assembly) behave correctly without LLM involvement.
4. Provide a regression surface for consolidation plan implementations — plans 1–4 and the `band_examples` move should all be testable here with no changes to the test fixture.

---

## Architecture of the Test Suite

### Mock boundary

All mocking happens at `ccya.llm_client.LLMClient`. The five pipeline steps call this client at five distinct call sites in `turn.py`. Each call site is identified by the prompt template name passed to the client (e.g., `"rules_system"`, `"narrate_system"`, `"extract_scene_system"`, etc.). The mock dispatcher reads the template name and returns a pre-baked response fixture.

This means:
- `run_turn()` executes real Python code end-to-end
- Jinja templates are rendered (real behavior)
- `apply_delta()` mutates real state objects (real behavior)
- Dice resolution runs (real behavior)
- Pressure, arc, quest health, NPC roster all run (real behavior)
- No actual HTTP/socket call is made

### Fixture structure

```
tests/
  integration/
    test_turn_pipeline.py       # Test cases
    conftest.py                 # Fixtures: mock state, mock LLM, mock responses
    fixtures/
      state_base.yaml           # Minimal valid starting state
      llm_responses/
        rules_turn1.json        # IntentEnvelope for turn 1
        rules_turn2.json        # IntentEnvelope for turn 2
        rules_turn3.json        # IntentEnvelope for turn 3
        narrate_turn1.txt       # Narrative prose (plain text)
        narrate_turn2.txt
        narrate_turn3.txt
        scene_turn1.json        # SceneExtractResult
        scene_turn2.json
        scene_turn3.json
        state_turn1.json        # StateExtractResult
        state_turn2.json
        state_turn3.json
        progress_turn1.json     # ProgressExtractResult
        progress_turn2.json
        progress_turn3.json
```

---

## Base State Fixture (`fixtures/state_base.yaml`)

Minimal but complete. Includes at least:

- **PC:** Name, stats (brawn 1, finesse 2, wit 3, nerve 2, heart 1), no conditions, 3 inventory items (one with TTL=1 condition pre-attached for condition-expiry testing)
- **Location:** id `loc_tavern`, name `The Rusty Flagon`, tags `[indoor, social]`
- **Scene:** 1 present NPC (`npc_barkeep`), 1 known NPC (`npc_contact`), no recently_left
- **Quests:** 2 active quests — one recently advanced (turn 1), one stalled at turn -5 (to exercise HIGH aggression immediately)
- **Compendium:** Both NPCs with bio, motivation, fear, leverage
- **Meta:** turn=1, no pending_gm_beat, no scene_pressure
- **Arc threads:** 1 active thread with engagement tags matching `gather_information` (so turn 1 exercises engagement scoring)
- **World:** 2 factions, 3 nearby locations, cultural name pool

---

## LLM Response Fixtures

Each turn has five response fixtures. They are intentionally designed to exercise state mutation, not just pass validation.

### Turn 1 — Social interaction, no dice

**User input:** `"I ask the barkeep about the missing merchant."`

**`rules_turn1.json`** — `IntentEnvelope`
```json
{
  "intent": "gather_information",
  "intent_verb": "ask",
  "target": "barkeep",
  "stakes": "low",
  "check": {"required": false, "skill": null, "difficulty": null}
}
```
*(No dice roll. `rules_outcome.rolled = False`.)*

**`narrate_turn1.txt`** — Narrative prose referencing the barkeep giving partial information and mentioning a contact in the market district. Must reference the active scene pressure (from `state_base.yaml` if pre-seeded) so `test_narration_directive_injected` has something to assert on; alternatively the pressure is added this turn and asserted in turn 2.

**`scene_turn1.json`** — `SceneExtractResult`
- No location change
- `npc_update`: barkeep attitude updated to `helpful`
- No compendium update

**`state_turn1.json`** — `StateExtractResult`
- No inventory changes
- No condition changes
- *(TTL condition not yet expired — it was set to 1, and the engine pre-removes at TTL=0. Turn 1 marks it for removal; turn 2 confirms it gone.)*

**`progress_turn1.json`** — `ProgressExtractResult`
- `quest_updates`: advance objective on stalled quest (quest staleness clock resets)
- `recent_events_add`: 1 new event
- `gm_beat`: type `opportunity`, target `npc_contact`, instruction `"Contact approaches at the market next turn"`
- `scene_pressure_add`: 1 new pressure `"Rival agents watching the tavern"`, urgency `medium`
- `actions`: exactly 4 entries (hard requirement — see `test_progress_actions_count`)

---

### Turn 2 — Skill check, mixed success

**User input:** `"I slip out the back to lose any tails."`

**`rules_turn2.json`** — `IntentEnvelope`
```json
{
  "intent": "evade",
  "intent_verb": "slip out",
  "target": "rivals",
  "stakes": "moderate",
  "check": {"required": true, "skill": "finesse", "difficulty": "standard"}
}
```
*(Dice roll fires. Python dice resolution runs. Fixture does not control the roll — the test asserts on band boundaries, not exact outcomes. See "Dice assertions" below.)*

**`narrate_turn2.txt`** — Narrative prose set in the alley behind the tavern. References the pending GM beat being consumed (contact spotted across the square). Must also reference the active scene pressure from turn 1 — this is what `test_narration_directive_injected` verifies: that the rendered narrate_user.j2 prompt contained `scene_pressure` and `narration_directive` before the mock was called.

**`scene_turn2.json`** — `SceneExtractResult`
- `location_change`: `loc_market_district`
- `npc_remove`: `npc_barkeep` (no longer present)
- `npc_add`: `npc_contact` (now present)
- `compendium_npc_update`: `npc_contact` last_seen updated

**`state_turn2.json`** — `StateExtractResult`
- `pc_condition_add`: `winded` with `ttl=2` (from the exertion)
- No inventory changes

**`progress_turn2.json`** — `ProgressExtractResult`
- `scene_pressure_remove`: the tavern pressure from turn 1 (resolved by leaving)
- `scene_pressure_add`: new pressure `"Contact is nervous, won't speak freely here"`, urgency `high`
- `quest_updates`: partial advance on information quest
- `gm_beat`: None (beat consumed this turn)
- `beat_disposition`: `consumed`
- `actions`: exactly 4 entries

---

### Turn 3 — Confrontation, partial failure

**User input:** `"I press the contact for the full story, now."`

**`rules_turn3.json`** — `IntentEnvelope`
```json
{
  "intent": "pressure",
  "intent_verb": "press",
  "target": "npc_contact",
  "stakes": "high",
  "check": {"required": true, "skill": "nerve", "difficulty": "hard"}
}
```

**`narrate_turn3.txt`** — Prose where the contact gives partial information but clams up on the most sensitive detail. Mentions the PC receives a folded note.

**`scene_turn3.json`** — `SceneExtractResult`
- No location change
- `npc_update`: `npc_contact` attitude `frightened`

**`state_turn3.json`** — `StateExtractResult`
- `inventory_add`: `{name: "Folded Note", description: "Unsigned, in a merchant's hand", tags: ["document", "clue"]}`
- No condition changes
- **No `inventory_remove` for items not in inventory** — fixture must be clean; this is the zero-balance guard (see `test_inventory_remove_validation`)

**`progress_turn3.json`** — `ProgressExtractResult`
- Quest objective marked `blocked` (contact won't fully cooperate)
- `scene_pressure_update`: nervousness pressure intensity upgraded to `critical`
- New `gm_beat`: `threat`, target `npc_contact`, instruction `"Contact bolts next turn unless PC reassures them"`
- `recent_events_add`: 2 events
- `actions`: exactly 4 entries

---

## Test Cases

### `test_single_turn_completes`

**What it tests:** The full pipeline runs without exception for turn 1, returns a valid `StateDelta`, and `apply_delta()` produces a state that passes model validation.

```python
async def test_single_turn_completes(mock_state, mock_llm):
    result = await run_turn(mock_state, "I ask the barkeep about the missing merchant.", mock_llm)
    assert result.narrative and len(result.narrative) > 50
    assert result.delta is not None
    new_state = apply_delta(mock_state, result.delta)
    # Basic validity
    assert new_state.meta.turn == 2
    assert new_state.scene.present_npcs  # barkeep still present
```

---

### `test_gm_beat_lifecycle`

**What it tests:** A GM beat generated at the end of turn 1 is present in `state.meta.pending_gm_beat` after `apply_delta()`. After turn 2 (which consumes it), `pending_gm_beat` is None and `beat_disposition` is `consumed`.

```python
async def test_gm_beat_lifecycle(mock_state, mock_llm):
    # Turn 1: beat generated
    r1 = await run_turn(mock_state, input_t1, mock_llm)
    s1 = apply_delta(mock_state, r1.delta)
    assert s1.meta.pending_gm_beat is not None
    assert s1.meta.pending_gm_beat.type == "opportunity"

    # Turn 2: beat consumed
    r2 = await run_turn(s1, input_t2, mock_llm)
    s2 = apply_delta(s1, r2.delta)
    assert s2.meta.pending_gm_beat is None
    assert r2.progress_result.beat_disposition == "consumed"
```

---

### `test_scene_pressure_lifecycle`

**What it tests:** Scene pressure added in turn 1 is present in state. Pressure removed in turn 2 is gone. Pressure updated in turn 3 has the correct new urgency. This test directly covers Plan 01 (urgency directive consolidation).

```python
async def test_scene_pressure_lifecycle(mock_state, mock_llm):
    r1 = await run_turn(mock_state, input_t1, mock_llm)
    s1 = apply_delta(mock_state, r1.delta)
    pressure_ids = [p.id for p in s1.scene.scene_pressure]
    assert len(pressure_ids) == 1  # one added
    assert s1.scene.scene_pressure[0].urgency == "medium"

    r2 = await run_turn(s1, input_t2, mock_llm)
    s2 = apply_delta(s1, r2.delta)
    assert len(s2.scene.scene_pressure) == 1  # old removed, new added
    assert s2.scene.scene_pressure[0].urgency == "high"

    r3 = await run_turn(s2, input_t3, mock_llm)
    s3 = apply_delta(s2, r3.delta)
    assert s3.scene.scene_pressure[0].urgency == "critical"
```

---

### `test_narration_directive_injected`

**What it tests:** When scene pressure is active, the narrate pipeline step receives a rendered `narrate_user.j2` context that includes non-empty `scene_pressure` and a non-empty `narration_directive`. This is the highest-priority gap identified by the eval run (20260516T202305Z): the narrator was generating prose without awareness of active pressure state.

The mock LLM must capture the rendered prompt it receives. The conftest `TurnAwareMockLLM` is extended with a `last_narrate_context` attribute that stores the kwargs passed to the narrate call site.

```python
async def test_narration_directive_injected(state_after_turn1, mock_llm):
    # state_after_turn1 has one active scene pressure (urgency=medium)
    assert state_after_turn1.scene.scene_pressure  # precondition

    await run_turn(state_after_turn1, input_t2, mock_llm)

    ctx = mock_llm.last_narrate_context
    assert ctx is not None, "Narrate call site never fired"
    assert "scene_pressure" in ctx and ctx["scene_pressure"], \
        "scene_pressure missing or empty in narrate context"
    assert "narration_directive" in ctx and ctx["narration_directive"], \
        "narration_directive missing or empty in narrate context — narrator is flying blind"
```

---

### `test_rolled_true_on_check`

**What it tests:** When `rules_result.check.required == True` (turn 2, skill check), `rules_outcome.rolled` is `True` after the rules pipeline step. Guards against the live bug where the rules pipeline underrolls — present turns show `rolled=False` when the intent called for a check.

```python
async def test_rolled_true_on_check(state_after_turn1, mock_llm):
    result = await run_turn(state_after_turn1, input_t2, mock_llm)
    assert result.rules_outcome.rolled is True
    assert result.rules_outcome.band is not None
```

---

### `test_npc_roster_assembly`

**What it tests:** Plan 04 — `build_npc_roster()` produces the correct presence tags for present, just_left, and known NPCs. Run after turn 2 (location change: barkeep left, contact arrived).

```python
def test_npc_roster_assembly(state_after_turn2):
    roster = build_npc_roster(
        present_npcs=state_after_turn2.scene.present_npcs,
        known_npcs=build_known_npcs(state_after_turn2, compendium_lru=10),
        recently_left=get_recently_left(state_after_turn2),
    )
    by_id = {e.id: e for e in roster}

    assert by_id["npc_contact"].presence == NpcPresence.PRESENT
    assert by_id["npc_barkeep"].presence == NpcPresence.JUST_LEFT
    # No NPC appears twice
    assert len(roster) == len(by_id)
    # PRESENT entries come first
    assert roster[0].presence == NpcPresence.PRESENT
```

---

### `test_quest_health_computation`

**What it tests:** Plan 03 — `compute_quest_health()` returns HIGH aggression at turn 1 (stalled quest at turn -5), NORMAL after turn 1 advances it, LOW after turn 2 also advances it.

```python
def test_quest_health_computation(mock_state, state_after_turn1, state_after_turn2):
    # Turn 0: stalled quest present → HIGH
    qh0 = compute_quest_health(mock_state.quests, current_turn=1)
    assert qh0.new_quest_aggression == QuestHealthAggression.HIGH
    assert any(q["id"] == "quest_stalled" for q in qh0.stalled)

    # After turn 1 advances stalled quest → clock resets → NORMAL or LOW
    qh1 = compute_quest_health(state_after_turn1.quests, current_turn=2)
    assert qh1.new_quest_aggression in (QuestHealthAggression.NORMAL, QuestHealthAggression.LOW)
    assert not any(q["id"] == "quest_stalled" for q in qh1.stalled)
```

---

### `test_condition_ttl_expiry`

**What it tests:** A condition with `ttl=1` added at turn 1 is pre-removed by the engine before turn 2's extraction payload is built. `engine_expired_conditions` contains the ID; the condition is absent from `state.pc.conditions` after `apply_delta()`.

```python
async def test_condition_ttl_expiry(mock_state, mock_llm):
    # mock_state has a condition with ttl=1 already on the PC
    initial_cond_ids = {c.id for c in mock_state.pc.conditions}

    r1 = await run_turn(mock_state, input_t1, mock_llm)
    s1 = apply_delta(mock_state, r1.delta)

    # Condition should be expired — not in new state
    remaining_cond_ids = {c.id for c in s1.pc.conditions}
    expired = initial_cond_ids - remaining_cond_ids
    assert len(expired) == 1  # exactly one TTL expiry
```

---

### `test_inventory_add_then_reference`

**What it tests:** An item added in turn 3 (`Folded Note`) is present in state and can be referenced by ID in a subsequent validation pass. Guards against ID normalization regressions.

```python
def test_inventory_add_then_reference(state_after_turn3):
    note = next(
        (i for i in state_after_turn3.inventory if "note" in i.name.lower()),
        None
    )
    assert note is not None
    assert note.id  # ID was assigned, not empty
    assert "document" in note.tags
```

---

### `test_inventory_remove_validation`

**What it tests:** The validator rejects `inventory_remove` deltas that target items with zero balance. Guards against the live bug in eval run 20260516T202305Z where credits were removed at T6 and T13 despite already being at 0. The fixture must attempt a removal of an item not in state; the validator must reject it and log to `rejected_deltas`; `apply_delta()` must not raise.

```python
async def test_inventory_remove_validation(mock_state, mock_llm):
    # Manually inject a state_extract result with an invalid removal
    from ccya.engine.changes import validate_delta, apply_delta
    from ccya.models import StateExtractResult

    bad_extract = StateExtractResult(
        inventory_remove=[{"id": "credits", "qty": 200}],  # not in state
        # ... other fields empty
    )
    result = validate_delta(mock_state, bad_extract)
    assert len(result.rejected) == 1
    assert "credits" in result.rejected[0]["item"]
    # apply_delta with the cleaned delta does not raise
    cleaned = apply_delta(mock_state, result.clean_delta)
    assert cleaned  # state returned intact
```

---

### `test_progress_actions_count`

**What it tests:** The progress extractor fixture returns exactly 4 `actions` entries. Guards against the live behavior where turns 4, 8, and 12 produced 0 actions. This is a hard assertion — 4 actions is the contract.

```python
async def test_progress_actions_count(mock_state, mock_llm):
    for turn_input in [input_t1, input_t2, input_t3]:
        result = await run_turn(mock_state, turn_input, mock_llm)
        mock_state = apply_delta(mock_state, result.delta)
        assert len(result.progress_result.actions) == 4, \
            f"Expected 4 actions, got {len(result.progress_result.actions)}"
```

---

### `test_dice_band_boundaries`

**What it tests:** Pure Python — `resolve_check()` maps raw totals to the correct Band. Does not use the mock LLM. Covers all five bands at their edges.

```python
@pytest.mark.parametrize("total,expected_band", [
    (2,  Band.CRITICAL_FAIL),
    (5,  Band.PARTIAL_FAIL),
    (6,  Band.PARTIAL_FAIL),
    (7,  Band.MIXED),
    (9,  Band.MIXED),
    (10, Band.SUCCESS),
    (12, Band.SUCCESS),
    (13, Band.CRITICAL_SUCCESS),
])
def test_dice_band_boundaries(total, expected_band, mock_pc):
    # Patch random.randint to return controlled values
    with patch("ccya.rules.random.randint", return_value=total // 2):
        outcome = resolve_check(
            pc=mock_pc,
            skill="finesse",
            difficulty="standard",
            forced_total=total,  # if resolve_check supports bypass; else mock dice
        )
    assert outcome.band == expected_band
```

---

### `test_location_change_propagates`

**What it tests:** When `scene_result.location_change` is non-null (turn 2), `state.location.id` actually changes after `apply_delta()`. This is a code-path test — the eval run confirmed that `_apply_delta` was emitting the location change but not applying it to state (`schema_drift` flag on T10 and T12). The assertion must be on `state.location.id`, not just on `scene_result.location_change`.

```python
async def test_location_change_propagates(state_after_turn1, mock_llm):
    assert state_after_turn1.location.id == "loc_tavern"  # precondition

    r2 = await run_turn(state_after_turn1, input_t2, mock_llm)
    assert r2.scene_result.location_change is not None  # fixture emitted the change
    s2 = apply_delta(state_after_turn1, r2.delta)

    # This is the assertion that was failing in the live system
    assert s2.location.id == "loc_market_district", \
        f"Location not applied: still {s2.location.id}"
    assert s2.location.id != state_after_turn1.location.id
```

---

### `test_arc_engagement_not_stuck`

**What it tests:** Arc engagement must change in response to player actions whose intent matches active thread tags. If the player performs matching actions across 3 turns, engagement must not remain at the same floor value. Guards against the live stagnation (T11–T13 stuck at -1) identified in eval run 20260516T202305Z.

The base state fixture includes an active arc thread tagged with `gather_information`. Turn 1's intent is `gather_information`. Engagement should increase.

```python
async def test_arc_engagement_not_stuck(mock_state, mock_llm):
    # Precondition: at least one active arc thread with matching engagement tags
    assert any(t.state == "active" for t in mock_state.arcs.threads)

    r1 = await run_turn(mock_state, input_t1, mock_llm)
    s1 = apply_delta(mock_state, r1.delta)

    # Engagement must have moved — it was 0 at start, intent matched tags
    assert s1.arcs.engagement != mock_state.arcs.engagement, \
        "Arc engagement did not change after a matching player action"

    # Run two more turns with different intents; engagement must not stagnate at floor
    r2 = await run_turn(s1, input_t2, mock_llm)
    s2 = apply_delta(s1, r2.delta)
    r3 = await run_turn(s2, input_t3, mock_llm)
    s3 = apply_delta(s2, r3.delta)

    # The invariant: engagement must not end at the same value for 3 consecutive turns
    # (exact value depends on dice and intent matching — we only assert non-stagnation)
    engagement_values = [s1.arcs.engagement, s2.arcs.engagement, s3.arcs.engagement]
    assert len(set(engagement_values)) > 1, \
        f"Arc engagement stagnant across all 3 turns: {engagement_values}"
```

---

### `test_compaction_no_future_bleed`

**What it tests:** After a compaction at turn N, no entry in `prior_history` contains a turn number greater than N. Guards against the confirmed data leakage bug in eval run 20260516T202305Z where T9 compaction output included T10 data.

```python
def test_compaction_no_future_bleed(state_after_turn3):
    from ccya.engine.compaction import compact_history

    compacted = compact_history(state_after_turn3, up_to_turn=3)
    # The compaction boundary is turn 3
    for entry in compacted.prior_history:
        turn_ref = entry.get("turn") or entry.get("t")
        if turn_ref is not None:
            assert int(turn_ref) <= 3, \
                f"Compaction leaked future turn {turn_ref} into prior_history"
```

---

### `test_three_turn_state_integrity`

**What it tests:** Run all three turns sequentially. Assert that the final state passes full model validation (Pydantic), that turn counter is 4, that chronicle has been appended three times, and that no key fields are None or empty that shouldn't be.

```python
async def test_three_turn_state_integrity(mock_state, mock_llm, tmp_path):
    state = mock_state
    for turn_input in [input_t1, input_t2, input_t3]:
        result = await run_turn(state, turn_input, mock_llm)
        state = apply_delta(state, result.delta)

    assert state.meta.turn == 4
    assert state.location.id == "loc_market_district"
    assert len(state.inventory) >= 4  # 3 original + 1 note
    assert any("note" in i.name.lower() for i in state.inventory)
    assert state.scene.scene_pressure  # at least one pressure
    assert state.meta.pending_gm_beat is not None  # beat from turn 3

    # Full model round-trip: serialize → deserialize → no exception
    from ccya.models import GameState
    rehydrated = GameState.model_validate(state.model_dump())
    assert rehydrated.meta.turn == 4
```

---

## `conftest.py` — Mock LLM Dispatcher

The dispatcher intercepts `LLMClient.complete()` and `LLMClient.stream()`. It routes by template name + current turn counter to return the correct fixture. The `last_narrate_context` attribute is added to support `test_narration_directive_injected`.

```python
# tests/integration/conftest.py
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

FIXTURES = Path(__file__).parent / "fixtures"

def _load(name: str) -> str:
    p = FIXTURES / "llm_responses" / name
    return p.read_text()

class TurnAwareMockLLM:
    """
    Stateful mock that tracks which turn it's on and returns the correct
    fixture for each pipeline step. Turn advances when rules_* is called
    (first call per turn).

    last_narrate_context: stores the full kwargs dict passed to the narrate
    call site so tests can assert on template context injection.
    """
    def __init__(self):
        self._turn = 1
        self._rules_called_this_turn = False
        self.last_narrate_context: dict | None = None

    async def complete(self, system_template: str, user_template: str, **kwargs) -> str:
        if "rules" in system_template:
            if not self._rules_called_this_turn:
                self._rules_called_this_turn = True
            return _load(f"rules_turn{self._turn}.json")

        if "narrate" in system_template:
            self.last_narrate_context = kwargs  # capture for assertion
            return _load(f"narrate_turn{self._turn}.txt")

        if "extract_scene" in system_template:
            return _load(f"scene_turn{self._turn}.json")

        if "extract_state" in system_template:
            return _load(f"state_turn{self._turn}.json")

        if "extract_progress" in system_template:
            result = _load(f"progress_turn{self._turn}.json")
            # Advance turn counter after the last step
            self._turn += 1
            self._rules_called_this_turn = False
            return result

        raise ValueError(f"Unexpected template: {system_template}")

    async def stream(self, system_template: str, user_template: str, **kwargs):
        # Narrate uses streaming — yield the fixture text token by token
        text = await self.complete(system_template, user_template, **kwargs)
        for chunk in text.split():
            yield chunk + " "


@pytest.fixture
def mock_llm():
    return TurnAwareMockLLM()


@pytest.fixture
def mock_state():
    from ccya.state import load_state
    return load_state(FIXTURES / "state_base.yaml")


@pytest.fixture
async def state_after_turn1(mock_state, mock_llm):
    from ccya.engine.turn import run_turn
    from ccya.engine.changes import apply_delta
    r = await run_turn(mock_state, "I ask the barkeep about the missing merchant.", mock_llm)
    return apply_delta(mock_state, r.delta)


@pytest.fixture
async def state_after_turn2(state_after_turn1, mock_llm):
    from ccya.engine.turn import run_turn
    from ccya.engine.changes import apply_delta
    r = await run_turn(state_after_turn1, "I slip out the back to lose any tails.", mock_llm)
    return apply_delta(state_after_turn1, r.delta)


@pytest.fixture
async def state_after_turn3(state_after_turn2, mock_llm):
    from ccya.engine.turn import run_turn
    from ccya.engine.changes import apply_delta
    r = await run_turn(state_after_turn2, "I press the contact for the full story, now.", mock_llm)
    return apply_delta(state_after_turn2, r.delta)
```

---

## Consolidation Plan Coverage

| Consolidation Plan | Test that covers it | What it verifies |
|---|---|---|
| Plan 01: Urgency Directive (scene_pressure + location_imperative) | `test_scene_pressure_lifecycle`, `test_narration_directive_injected` | Pressure add/update/remove round-trips correctly; directive reaches narrator template |
| Plan 02: narrative_velocity scalar | `test_three_turn_state_integrity` | No crash if field is missing or zero; pipeline still produces valid delta |
| Plan 03: `quest_health` block | `test_quest_health_computation` | Aggression level computed correctly; stalled list is accurate |
| Plan 04: Tiered NPC list | `test_npc_roster_assembly` | Presence tags correct; no duplicate entries; ordering is PRESENT-first |
| Plan 05: band_examples → template | `test_dice_band_boundaries` | Band mapping correct; no regression from removing runtime payload key |

---

## Known Checker Noise (Not Tested)

The eval auto-checker flags common nouns as missing NPCs (e.g., "Crossed", "Leather", "However"). This is a false-positive issue in the checker's NPC mention extraction, not a bug in the engine. The integration test does not assert on NPC mention extraction precision — that is an eval concern.

---

## What These Tests Do Not Cover

- **LLM output quality** — narrative coherence, prose quality, extraction accuracy. That is the eval system's job (`ccya/eval/`).
- **Streaming token delivery to client** — WebSocket / SSE transport layer. Integration test fakes the stream.
- **Character creation and seed generation pipelines** — separate pipelines, separate test files when written.
- **Concurrency** — multiple simultaneous turns. Out of scope here.
- **State persistence to disk** — `state.yaml` and `events.jsonl` write paths. Separate unit tests for `ccya/state/`.

---

## Running the Tests

```bash
# Install test deps (add to pyproject.toml if not present)
pip install pytest pytest-asyncio

# Run only integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=ccya.engine --cov-report=term-missing

# Run a single test
pytest tests/integration/test_turn_pipeline.py::test_three_turn_state_integrity -v
```

Expected runtime with mocked LLM: **< 2 seconds** for the full suite.

---

## Implementation Order

1. Write `fixtures/state_base.yaml` — start from a real save file, strip down, add arc thread with `gather_information` tag
2. Write `fixtures/llm_responses/*.json` and `*.txt` — use real LLM outputs from a test session as seeds, hand-edit to hit specific scenarios; ensure `progress_turnN.json` always has exactly 4 actions
3. Write `conftest.py` with `last_narrate_context` capture
4. Start with `test_dice_band_boundaries` (no fixture dependency) and `test_single_turn_completes`
5. Add `test_narration_directive_injected` — this test will fail until the narrate template injection bug is fixed; that's intentional, it's a regression gate
6. Add `test_location_change_propagates` — will fail until `_apply_delta` location bug is fixed
7. Add `test_inventory_remove_validation` — will fail until zero-balance guard is in place
8. Add remaining lifecycle tests
9. Add to CI: `pytest tests/integration/` as a required check
