# Fix run_turn_retry missing narrator arguments

## Status
`completed`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Pass threat_ages and turn_no to _narrate_messages in run_turn_retry | Match the argument set that run_turn uses |
| 02 | Fix deescalate type from bool to float in run_turn_retry | Replace False with 0.0 |

## Objective
`run_turn_retry` in `engine/turn.py` calls `_narrate_messages` with a subset of the keyword arguments that `run_turn` provides. Specifically it omits `threat_ages`, `turn_no`, `threat_pressure_at`, `threat_imperative_at`, and `building_threat_imperative_at`. These five arguments control the Threat Pressure and Resolve a Threat narrator directives — without them, retried turns never fire these directives regardless of how old or urgent the scene pressures are. Additionally, `deescalate=False` is passed where the type annotation requires `float`, which is a mypy error.

## Non-goals
- No changes to `_narrate_messages` signature.
- No changes to what `run_turn` passes.
- No changes to threat threshold constants in `EngineConfig`.
- No prompt changes.

---

## Implementation — Phase 01: Pass threat_ages and turn_no to _narrate_messages in run_turn_retry

### Files to pull for context
- `ccya/engine/turn.py` — full `run_turn_retry` function, focusing on the `_narrate_messages` call
- `ccya/engine/narrate.py` — `_narrate_messages` signature

### Detailed steps

#### Step 1.1 — Compute threat_ages before the _narrate_messages call in run_turn_retry

**File:** `ccya/engine/turn.py`

**What:** In `run_turn_retry`, `ages = _compute_ages(state)` is already called before the `_narrate_messages` call. Add a `threat_ages` computation directly below it:

```python
ages = _compute_ages(state)
threat_ages = _compute_threat_ages(state)
```

**Why:** `_compute_threat_ages` is already imported and used in `run_turn`. Retry paths load the same state and need the same threat context for narrator directives.

**Validation:** Verify that `_compute_threat_ages` is already defined above `run_turn_retry` in the file — it is, at module level.

#### Step 1.2 — Add the five missing keyword arguments to the _narrate_messages call in run_turn_retry

**File:** `ccya/engine/turn.py`

**What:** Locate the `_narrate_messages(...)` call inside `run_turn_retry`. It currently ends with:
```python
            world_factions=_world_factions,
            world_locations=_world_locations,
        )
```
Add the five missing arguments:
```python
            world_factions=_world_factions,
            world_locations=_world_locations,
            threat_ages=threat_ages,
            turn_no=turn_no,
            threat_pressure_at=config.threat_pressure_at,
            threat_imperative_at=config.threat_imperative_at,
            building_threat_imperative_at=config.building_threat_imperative_at,
        )
```

**Why:** `run_turn` passes all five. Without them, `_narrate_messages` uses its defaults: `threat_ages=None` (renders as empty list), `turn_no=0`, and the threshold defaults (3, 5, 4). `turn_no=0` causes every age comparison to produce negative ages, so no directives fire.

**Validation:** After this change, a retry of a turn with a 4-turn-old `immediate` pressure should produce a narrate prompt that contains "Resolve a Threat" or the pressure text in its directive block. Verify by logging `rendered_narr_system` for a retry with an aged pressure in state.

---

## Implementation — Phase 02: Fix deescalate type from bool to float in run_turn_retry

### Files to pull for context
- `ccya/engine/turn.py` — `run_turn_retry` function

### Detailed steps

#### Step 2.1 — Replace deescalate=False with deescalate=0.0

**File:** `ccya/engine/turn.py`

**What:** In `run_turn_retry`, the `_narrate_messages` call passes `deescalate=False`. Also, the `_run_extraction_pipeline` call passes `deescalate=False`. Change both to `deescalate=0.0`.

**Why:** `_narrate_messages` declares `deescalate: float = 0.0`. `_run_extraction_pipeline` declares `deescalate: float = 0.0`. `False` is a `bool`, which is a subclass of `int`, not `float`. Mypy flags this as a type error. The runtime behavior is identical (bool 0 == float 0.0 in arithmetic contexts) but the intent is wrong and it will block `make check`.

**Code Snippet**

In the `_narrate_messages` call inside `run_turn_retry`:
```python
            # Retry: skip deescalation/quest-age awareness since the rules
            # outcome is already fixed — re-rolling narration shouldn't
            # change the pacing directive.
            deescalate=0.0,
```

In the `_run_extraction_pipeline` call inside `run_turn_retry`:
```python
            deescalate=0.0,
```

**Validation:** `make check` (mypy) must pass with no errors on `engine/turn.py` after this change.

### Tests to write or update
No new tests needed for the type fix — mypy is the validator. For Phase 01, the behavior change is in prompt construction which is tested via integration. Add a focused unit test:

**File:** `tests/test_narrate.py` (create if it does not exist)

```python
def test_narrate_messages_threat_ages_wired() -> None:
    """threat_ages passed to _narrate_messages must appear in rendered user prompt."""
    from pathlib import Path
    from ccya.engine.config import _build_jinja_env
    from ccya.engine.narrate import _narrate_messages

    template_dir = str(Path("ccya/prompts"))
    env = _build_jinja_env(template_dir)
    state: dict = {
        "meta": {"turn": 5, "prior_history": []},
        "pc": {"name": "Test", "tagline": "", "bio": "", "stats": {}, "conditions": [], "momentum": 0},
        "location": {"id": "loc1", "name": "The Market", "description": ""},
        "inventory": [],
        "scene": {"tags": [], "tagline": "", "present_npcs": [], "world_state": [], "recent_events": [], "scene_pressure": []},
        "compendium": {"npcs": {}},
        "world": {"factions": [], "locations": []},
    }
    threat_ages = [{"id": "p1", "text": "Guards closing in", "urgency": "immediate", "age": 4}]
    msgs = _narrate_messages(
        env, state, "I wait",
        threat_ages=threat_ages,
        turn_no=5,
        threat_imperative_at=3,
    )
    combined = " ".join(m["content"] for m in msgs)
    assert "Guards closing in" in combined
```

### REPOMAP and architecture updates
`docs/REPOMAP/engine.md` — update `run_turn_retry` description: note that it now computes `threat_ages` and passes all narrator threat-directive arguments, matching `run_turn`.

### Risks
1. If any existing test snapshot-tests the narrate prompt for a retry turn, it will now include threat directives that were previously absent. Update the snapshot — the new output is correct.

## Ambiguities requiring resolution before execution
None.
