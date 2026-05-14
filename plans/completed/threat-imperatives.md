# Threat Imperatives

## Status
`open`

## Phases

3 phases: Add a computed "threat imperative" system — like location imperatives but for scene pressures — so old threats get narratively resolved instead of persisting for 15+ turns.

## Objective

Scene pressures (threats) currently persist far too long because the LLM extractor rarely emits `scene_pressure_remove` and the engine's auto-removal only kicks in at 15 turns. Location imperatives solve the analogous problem for locations: a computed directive tells the narrator to advance the story when a location is too old. This plan adds the same pattern for threats — when a threat reaches a certain age, the narrator receives a "Resolve a Threat" directive, which causes the narrator to weave a resolution into the story, which the extractor then picks up and emits as `scene_pressure_remove`.

## Non-goals

- Do not change how scene pressures are created (still LLM-driven via extractor).
- Do not add a separate "threat" model — threats ARE scene pressures.
- Do not change the urgency escalation system (background → building → immediate).
- Do not add UI changes or new panels.
- Do not change compactor pressure handling.

## Firm decisions

1. Threat imperatives are computed directives (like location imperatives), not stored state. They fire based on threat age thresholds.
2. The narrator resolves threats narratively; the extractor removes them from state. The engine never forcibly removes a threat — it only instructs the narrator to resolve one.
3. Three age thresholds: background pressure at 3 turns, background imperative at 5 turns, building imperative at 4 turns. Immediate threats are excluded (they already have an 8-turn TTL from becoming immediate).
4. When multiple threats qualify, the oldest one is named in the directive context so the narrator resolves the right one.
5. The extraction prompt is updated so the extractor recognizes "threat resolved" narration and emits `scene_pressure_remove`.

## Conflicts and overlap

None. No open plans touch scene pressure lifecycle or narration directives.

## Implementation — Phase 1: Config + computation

### Context files to load
- `ccya/engine/config.py` — add config fields
- `ccya/engine/turn.py` — add `_compute_threat_ages()` call

### Detailed steps

#### Step 1.1 — Add threat imperative config fields

**File:** `ccya/engine/config.py`

**What:** Add three new config fields for threat imperative age thresholds.

**Why:** These control when the narrator is instructed to resolve a threat. Mirrors the location imperative thresholds (location_pressure_at=3, location_imperative_at=5).

**Code Snippet**
```python
# In EngineConfig dataclass, after scene_pressure_deescalate_on_success (line 82):
    # Threat imperative thresholds (turns since turn_added)
    # Background threat → narration directive "Threat Pressure" at this age
    threat_pressure_at: int = 3
    # Background threat → narration directive "Resolve a Threat" at this age
    threat_imperative_at: int = 5
    # Building threat → narration directive "Resolve a Threat" at this age
    building_threat_imperative_at: int = 4
```

**In `build_engine_config()`, after `scene_pressure_deescalate_on_success` mapping (lines 145-147):**
```python
        threat_pressure_at=int(game.get("threat_pressure_at", 3)),
        threat_imperative_at=int(game.get("threat_imperative_at", 5)),
        building_threat_imperative_at=int(game.get("building_threat_imperative_at", 4)),
```

**Validation:** `make check` passes. Config fields are wired through `build_engine_config()`.

### Tests to write or update

None for this phase (config defaults are trivially verified by the existing config tests if any exist; otherwise the defaults are self-evident).

### REPOMAP updates required

- `docs/REPOMAP/config.md` — add `threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at` to the EngineConfig table

### Risks

None. Pure config addition.

## Implementation — Phase 2: Turn pipeline + templates

### Context files to load
- `ccya/engine/turn.py` — add `_compute_threat_ages()`, wire into pipeline
- `ccya/engine/narrate.py` — add `threat_ages` parameter + config values to context
- `ccya/prompts/narrate_user.j2` — display threat ages, fire directives
- `ccya/prompts/narrate_system.j2` — add "Resolve a Threat" directive definition

### Detailed steps

#### Step 2.1 — Add `_compute_threat_ages()` function

**File:** `ccya/engine/turn.py`

**What:** Add a function that computes the age of each scene pressure. Returns a list of dicts with `id`, `text`, `urgency`, and `age` (turns since `turn_added`).

**Why:** The narrator template needs to know which threats are old so it can resolve the right one. Mirrors `_compute_ages()` pattern.

**Code Snippet**
```python
def _compute_threat_ages(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute age of each scene pressure for threat imperative directives.

    Returns a list of dicts with keys: id, text, urgency, age.
    Only includes pressures with a valid turn_added (> 0).
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    result: list[dict[str, Any]] = []
    for p in pressures:
        if not isinstance(p, dict):
            continue
        turn_added = p.get("turn_added")
        if not turn_added or turn_added == 0:
            continue
        result.append({
            "id": p.get("id", ""),
            "text": p.get("text", ""),
            "urgency": p.get("urgency", "background"),
            "age": current_turn - turn_added,
        })
    # Sort by age descending so the oldest threat is first
    result.sort(key=lambda x: x["age"], reverse=True)
    return result
```

**Validation:** Function returns correct ages for pressures with valid turn_added. Pressures with turn_added=0 or None are excluded.

### Tests to write or update

**File:** `tests/test_pressure.py` (add new class)

```python
class TestComputeThreatAges:
    def test_basic_ages(self) -> None:
        from ccya.engine.turn import _compute_threat_ages

        state: dict[str, Any] = {
            "meta": {"turn": 10},
            "scene": {"scene_pressure": [
                {"id": "old", "text": "Old threat", "urgency": "background", "turn_added": 3},
                {"id": "new", "text": "New threat", "urgency": "building", "turn_added": 8},
            ]},
        }
        ages = _compute_threat_ages(state)
        assert len(ages) == 2
        assert ages[0]["id"] == "old"  # oldest first
        assert ages[0]["age"] == 7
        assert ages[1]["id"] == "new"
        assert ages[1]["age"] == 2

    def test_excludes_invalid_turn_added(self) -> None:
        from ccya.engine.turn import _compute_threat_ages

        state: dict[str, Any] = {
            "meta": {"turn": 10},
            "scene": {"scene_pressure": [
                {"id": "valid", "text": "V", "urgency": "background", "turn_added": 5},
                {"id": "invalid", "text": "I", "urgency": "background", "turn_added": 0},
            ]},
        }
        ages = _compute_threat_ages(state)
        assert len(ages) == 1
        assert ages[0]["id"] == "valid"

    def test_empty_pressures(self) -> None:
        from ccya.engine.turn import _compute_threat_ages

        state: dict[str, Any] = {"meta": {"turn": 5}, "scene": {"scene_pressure": []}}
        ages = _compute_threat_ages(state)
        assert ages == []
```

### REPOMAP updates required

- `docs/REPOMAP/engine.md` — add `_compute_threat_ages()` to the turn.py function table

#### Step 2.2 — Wire `_compute_threat_ages()` into the turn pipeline

**File:** `ccya/engine/turn.py`

**What:** Call `_compute_threat_ages()` after `_compute_ages()` and pass the result to `_narrate_messages()`.

**Why:** The narrator needs threat age data to fire directives.

**Code Snippet** (in `run_turn()`, after the `_compute_ages(state)` call at line 379):
```python
        # Age counters for narration directives
        ages = _compute_ages(state)
        threat_ages = _compute_threat_ages(state)
        quest_ages = _compute_quest_ages(state, turn_no)
```

Then in the `_narrate_messages()` call (around line 476), add `threat_ages=threat_ages` plus the three config threshold values to the kwargs.

**Validation:** `_narrate_messages()` receives `threat_ages` as a kwarg. The template can access it.

### Tests to write or update

Integration test in `tests/test_turn.py` (if it exists) or `tests/test_pressure.py`:
```python
def test_threat_ages_passed_to_narrator(self) -> None:
    """Verify threat_ages flows from _compute_threat_ages through to _narrate_messages."""
    # This is implicitly tested by the template rendering test if one exists.
    # Otherwise, the unit tests for _compute_threat_ages above are sufficient.
    pass
```

#### Step 2.2b — Add threat_ages parameter to _narrate_messages()

**File:** `ccya/engine/narrate.py`

**What:** Add `threat_ages` parameter to `_narrate_messages()` function signature and pass config threshold values through the template context.

**Why:** `_narrate_messages()` currently has no `threat_ages` parameter (lines 12-38). The template at `narrate_user.j2` references `building_threat_imperative_at`, `threat_imperative_at`, `threat_pressure_at` — these values are not in the current template context. Without this step, the template cannot access threat data or config values.

**Code Snippet** (add to `_narrate_messages()` parameters after `scene_pressure` at line 34):
```python
    threat_ages: list[dict[str, Any]] | None = None,
    threat_pressure_at: int = 3,
    threat_imperative_at: int = 5,
    building_threat_imperative_at: int = 4,
```

Add to `user_ctx` dict (after `scene_pressure` at line 58):
```python
        "threat_ages": threat_ages or [],
        "threat_pressure_at": threat_pressure_at,
        "threat_imperative_at": threat_imperative_at,
        "building_threat_imperative_at": building_threat_imperative_at,
```

**In `run_turn()` caller** (around line 476, in the `_narrate_messages()` call), add:
```python
            threat_ages=threat_ages,
            threat_pressure_at=config.threat_pressure_at,
            threat_imperative_at=config.threat_imperative_at,
            building_threat_imperative_at=config.building_threat_imperative_at,
```

**In `run_turn_retry()` caller** (around line 1130): Do NOT pass threat_ages — consistent with the existing pattern of skipping deescalation/quest-age awareness on retry (see comment at lines 1145-1147). The retry path already skips `ages=ages` as well.

**Validation:** `_narrate_messages()` accepts the new parameters. Template context includes threat data and config values.

#### Step 2.3 — Update narrate_user.j2: display threat ages + fire directives

**File:** `ccya/prompts/narrate_user.j2`

**What:** Add a "Threats" section that shows each threat's age. Add narration directives for threat pressure and threat imperative.

**Why:** The narrator needs to know which threats are old and which one to resolve. The directives fire at the configured thresholds.

**Code Snippet** (add after the "Active Threats" section at lines 42-46):
```jinja2
{% if threat_ages -%}
### Threats
{% for t in threat_ages %}- [{{ t.urgency | upper }}] {{ t.text }} ({{ t.age }} turns old)
{% endfor -%}
{% endif -%}
```

Add directives after the existing location imperative/pressure directives (after line 129, before `=== PLAYER INPUT ===`):
```jinja2
{% if threat_ages %}
{% set old_building = threat_ages | selectattr("urgency", "equalto", "building") | selectattr("age", "ge", building_threat_imperative_at) | list %}
{% set old_background = threat_ages | selectattr("urgency", "equalto", "background") | selectattr("age", "ge", threat_imperative_at) | list %}
{% set background_pressure = threat_ages | selectattr("urgency", "equalto", "background") | selectattr("age", "ge", threat_pressure_at) | selectattr("age", "lt", threat_imperative_at) | list %}
{% if old_building or old_background %}

**Narration Directive:** Resolve a Threat
Resolve the oldest threat listed above. It has been active too long. Weave its resolution naturally into the narration — the threat is dealt with, neutralized, or escapes. Do NOT introduce a new threat in this narration.
{% elif background_pressure %}

**Narration Directive:** Threat Pressure
A background threat has been lingering. Acknowledge it in the scene — show its presence affecting the environment or NPCs. No need to resolve it yet, but don't ignore it.
{% endif %}
{% endif %}
```

**Validation:** Template renders correctly with threat_ages. Directives fire at the right thresholds.

### Tests to write or update

No new template tests needed if existing narrate tests cover directive rendering. Otherwise, add a template rendering test.

#### Step 2.4 — Update narrate_system.j2: add "Resolve a Threat" directive definition

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add the "Resolve a Threat" and "Threat Pressure" directives to the narration directives section.

**Why:** The system prompt tells the narrator HOW to follow the directive. Without this definition, the narrator may not know what to do.

**Code Snippet** (add after the Location Pressure directive at line 88, before "Fail-band outcomes" at line 90):
```
- **Threat Pressure** — A background threat has been lingering in the scene. Acknowledge it — show its presence affecting the environment, NPCs, or the player's options. No need to resolve it yet, but don't ignore it.
- **Resolve a Threat** — One of the active threats has been around too long. Resolve it narratively: the threat is dealt with, neutralized, escapes, or is otherwise no longer a danger. Weave this resolution naturally into the story. Do NOT introduce a new threat in this narration. The player should feel relief that a persistent danger is gone.
```

**Validation:** The new directives appear in the system prompt alongside existing ones.

### REPOMAP updates required

- `docs/REPOMAP/prompts.md` — add "Resolve a Threat" and "Threat Pressure" to the narration directives table

### Risks

- The template Jinja filters (`selectattr`, `ge`) need to work correctly. Test with the template renderer.
- If `threat_ages` is empty, the `{% if threat_ages %}` block should not fire.

## Implementation — Phase 3: Extraction prompt update

### Context files to load
- `ccya/prompts/extract_progress_system.j2` — update scene_pressure_remove guidance
- `ccya/prompts/extract_progress_user.j2` — add directive context

### Detailed steps

#### Step 3.1 — Update extraction system prompt: guide extractor on threat resolution

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Update the `scene_pressure_remove` field rules to explicitly mention that the extractor should remove threats the narrator resolved in response to a "Resolve a Threat" directive.

**Why:** The extractor currently removes pressures based on narrative cues, but doesn't have explicit guidance for the threat imperative case. The narrator may resolve a threat narratively, but if the extractor doesn't recognize this as a resolution signal, the pressure persists.

**Code Snippet** (update the `scene_pressure_remove` section at lines 91-92):
```
`scene_pressure_remove`: IDs of pressures now resolved. Emit the id string in the list.
**IMPORTANT: If the narration shows a threat being resolved (e.g., the swarm scatters, the pursuers give up, the danger passes), you MUST emit its ID here. This includes threats resolved in response to a "Resolve a Threat" narration directive — the narrator resolved it, you remove it from state.**
```

**Validation:** The updated guidance is present in the system prompt. The extractor should now recognize threat resolution narration.

### Tests to write or update

No new unit tests needed — this is a prompt change. The existing extraction tests should still pass. Integration testing via eval runs will verify the extractor picks up threat resolutions.

### REPOMAP updates required

- `docs/REPOMAP/prompts.md` — note the updated `scene_pressure_remove` guidance for threat resolution

### Risks

- The extractor might over-remove threats (removing threats that aren't actually resolved). The prompt guidance should be clear enough to prevent this.

## Ambiguities requiring resolution before execution

1. **Should immediate threats also get a threat imperative?** Currently excluded because they already have an 8-turn TTL from becoming immediate. But if an immediate threat has been around for 10+ turns total (before becoming immediate), the player might still feel stuck. Decision: exclude immediate threats from threat imperatives — the existing TTL system handles them. If this proves insufficient, add `immediate_threat_imperative_at` as a config field in a follow-up.

2. **Should the directive name the specific threat to resolve?** The current design shows all threats with ages in the template, sorted oldest-first. The narrator resolves the oldest. Alternative: pass the single oldest threat ID to the directive. Decision: show all threats with ages — the narrator can choose which to resolve if multiple qualify, but the oldest is the most natural choice.

3. **What about the compactor?** When the compactor runs, should it also check for old pressures and remove them? Decision: no — the compactor already has `pressure_remove` guidance. The threat imperative system handles runtime resolution; the compactor handles historical cleanup. No change needed.
