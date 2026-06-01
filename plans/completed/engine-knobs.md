# Settings Panel — Additional Engine Knobs

## Purpose

Add 7 new configurable engine settings to the game settings modal, giving players control over difficulty curves, scene pacing, and failure tone without exposing engine internals.

## Problem Statement

The CCYA engine has numerous hardcoded constants that directly affect gameplay balance and player experience—difficulty modifier tables, scene age thresholds for Pressure/Imperative directives, momentum velocity scaling factors, near-miss narration softening, and thread memory TTLs—but none are exposed or configurable. Players have no way to adjust how challenging rolls feel or how fast scenes escalate without modifying source code or restarting the server with manual config edits.

## Constraints

- All changes span 4 files: `engine/config.py`, `server/routes.py`, `models.py` (already has save_config), and `templates/index.html`.
- Existing settings modal fields must remain unchanged; new fields are additions only.
- Defaults must match current hardcoded behavior so existing configs don't break or change gameplay.
- No new dependencies or frameworks.
- Tooltip system already exists via `_bindTooltips()` using `.has-tooltip` class anchors with nested `.tooltip-body`.

## Non-goals

- No changes to LLM temperature settings (they're startup-only and require server restart).
- No redesign of the modal layout or CSS — new fields follow existing field patterns.
- No difficulty preset system beyond simple string values ("forgiving", "balanced", "demanding").
- No per-difficulty granularity in UI; presets are pre-computed modifier tuples stored as strings.

## Solution

Add 7 config.yaml keys and corresponding EngineConfig fields, expose them via GET/POST `/api/settings`, wire them through the ruling/pacing pipeline to replace hardcoded constants, and add form controls with tooltips to the settings modal HTML. All defaults match current behavior exactly.

## Firm decisions

1. **difficulty_curve**: Stored as string preset ("forgiving"/"balanced"/"demanding") in config.yaml; EngineConfig resolves it to a modifier dict at startup via `_resolve_difficulty_modifiers()`. No per-difficulty fields exposed — presets are pre-computed tuples.
2. **Scene thresholds**: Two integer fields (`scene_pressure_threshold`, `scene_imperative_threshold`) passed into `_compute_narration_directive()` instead of hardcoded 3/5 values.
3. **Momentum pacing factor**: Float field (0.3/0.5/1.0) replacing the hardcoded `normalized * 0.5` and cap at ±0.5 in velocity calculation.
4. **Near-miss softening**: Boolean field controlling whether near-fails (final_total=4 or 5) get softer narration directive text. Passed through resolve_check() from ruling step config.
5. **Thread/Arc memory TTLs**: Integer fields replacing hardcoded `ttl = 3` in `_filter_completed_threads()` and `_get_resolved_arc()` in narrate.py.

## Risks, Ambiguities, and Blockers

- **Ambiguous: near_miss_softening wiring.** resolve_check() is called from the ruling step where config IS available (line 561 of turn.py). Need to pass `config.near_miss_softening` into resolve_check() or have it read from EngineConfig directly.
- **Scope creep risk:** These are 7 new fields across multiple modules. Each requires threading through existing call chains. Keep defaults conservative and match current behavior exactly.

## Status

`completed`

## Phases

3 phases: (1) Backend config model + API wiring, (2) Engine pipeline integration for pacing/difficulty/failure tone, (3) UI form controls with tooltips in settings modal.

---

## Implementation — Phase 1: Backend config model and API wiring

### Context files to load
- `ccya/engine/config.py` (EngineConfig dataclass lines 42–76; build_engine_config() lines 79–134)
- `ccya/server/routes.py` (GET/POST /api/settings routes lines 570–622)

### Detailed steps

#### Step 1.1 — Add fields to EngineConfig dataclass

**File:** `ccya/engine/config.py`, after line 75 (`thread_deescalate_on_success`)

**What:** Add 7 new fields with defaults matching current hardcoded behavior:

```python
# Difficulty curve preset (forgiving/balanced/demanding)
difficulty_curve: str = "balanced"
# Scene pacing thresholds (turns before directive triggers)
scene_pressure_threshold: int = 3
scene_imperative_threshold: int = 5
# Momentum influence on narrative direction (scaling factor, capped at ±factor)
momentum_pacing_factor: float = 0.5
# Near-miss softening: whether near-fails get softer narration directive text
near_miss_softening: bool = True
# TTL for completed threads and resolved arcs in narration context (turns)
thread_memory_ttl: int = 3
arc_memory_ttl: int = 3
```

**Why:** These are the new config fields that will be read from config.yaml at startup. Defaults match current hardcoded behavior so existing gameplay is unchanged.

**Validation:** `python -c "from ccya.engine.config import EngineConfig; c=EngineConfig(); assert c.difficulty_curve=='balanced'; assert c.scene_pressure_threshold==3"`

#### Step 1.2 — Add difficulty resolver method to EngineConfig

**File:** `ccya/engine/config.py`, inside the EngineConfig class (after line 76)

**What:** Add a private method `_resolve_difficulty_modifiers()` that returns the actual modifier dict based on the preset:

```python
def _resolve_difficulty_modifiers(self) -> dict[str, int]:
    curves = {
        "forgiving": {"trivial": 3, "easy": 1, "normal": 0, "hard": -1, "extreme": -2},
        "balanced": {"trivial": 2, "easy": 1, "normal": 0, "hard": -1, "extreme": -2},
        "demanding": {"trivial": 1, "easy": 0, "normal": 0, "hard": -1, "extreme": -3},
    }
    return curves.get(self.difficulty_curve or "balanced", curves["balanced"])
```

**Why:** Players select a preset string; the engine resolves it to actual modifier values at startup. No need to pass per-difficulty fields through the pipeline — one resolver call gives the full dict.

**Validation:** `python -c "from ccya.engine.config import EngineConfig; c=EngineConfig(); assert c._resolve_difficulty_modifiers()['hard']==-1"`

#### Step 1.3 — Wire new fields in build_engine_config()

**File:** `ccya/engine/config.py`, inside `build_engine_config()` after line 134 (after existing game config reads)

**What:** Add reading of the 7 new keys from config.yaml's `game:` section:

```python
        difficulty_curve=game.get("difficulty_curve", "balanced"),
        scene_pressure_threshold=int(game.get("scene_pressure_threshold", 3)),
        scene_imperative_threshold=int(game.get("scene_imperative_threshold", 5)),
        momentum_pacing_factor=float(game.get("momentum_pacing_factor", 0.5)),
        near_miss_softening=bool(game.get("near_miss_softening", True)),
        thread_memory_ttl=int(game.get("thread_memory_ttl", 3)),
        arc_memory_ttl=int(game.get("arc_memory_ttl", 3)),
```

**Why:** These map config.yaml keys to EngineConfig fields at startup. Defaults match current hardcoded behavior.

**Validation:** `python -c "from ccya.engine.config import build_engine_config; c=build_engine_config({'game': {}}); assert c.difficulty_curve=='balanced'"`

#### Step 1.4 — Expose new fields in GET /api/settings route

**File:** `ccya/server/routes.py`, inside get_settings() function (after line 582)

**What:** Add the 7 new keys to the JSONResponse dict:

```python
        "difficulty_curve": game_config.get("difficulty_curve", "balanced"),
        "scene_pressure_threshold": game_config.get("scene_pressure_threshold", 3),
        "scene_imperative_threshold": game_config.get("scene_imperative_threshold", 5),
        "momentum_pacing_factor": game_config.get("momentum_pacing_factor", 0.5),
        "near_miss_softening": game_config.get("near_miss_softening", True),
        "thread_memory_ttl": game_config.get("thread_memory_ttl", 3),
        "arc_memory_ttl": game_config.get("arc_memory_ttl", 3),
```

**Why:** The frontend needs to read these values from the API when opening the settings modal. GET route is what loadSettings() calls.

**Validation:** `curl http://localhost:8765/api/settings | python -m json.tool` should include all 7 new keys with default or current config.yaml values.

#### Step 1.5 — Accept new fields in POST /api/settings route

**File:** `ccya/server/routes.py`, inside post_settings() function (after line 604, before the debug section handling)

**What:** Add acceptance of integer and float fields:

```python
    for key in ("scene_pressure_threshold", "scene_imperative_threshold", "thread_memory_ttl", "arc_memory_ttl"):
        if key in data:
            game_config[key] = int(data[key])

    if "momentum_pacing_factor" in data:
        val = float(data["momentum_pacing_factor"])
        # Clamp to reasonable range [0.1, 2.0]
        game_config["momentum_pacing_factor"] = max(0.1, min(2.0, val))

    if "difficulty_curve" in data:
        valid_curves = ("forgiving", "balanced", "demanding")
        curve_val = str(data["difficulty_curve"])
        if curve_val not in valid_curves:
            return JSONResponse({"error": f"Invalid difficulty_curve. Must be one of {valid_curves}"}, status_code=400)
        game_config["difficulty_curve"] = curve_val

    for key in ("near_miss_softening",):
        if key in data:
            game_config[key] = bool(data[key])
```

**Why:** POST route needs to accept and validate the new fields before persisting. Momentum pacing factor is clamped to [0.1, 2.0] to prevent extreme values; difficulty_curve validates against allowed presets.

**Validation:** Test with curl POST requests for each field type (int, float, bool, string preset). Verify validation rejects invalid curves and out-of-range momentum factors.

---

## Implementation — Phase 2: Engine pipeline integration

### Context files to load
- `ccya/engine/turn.py` (_compute_pacing_context lines 468–507; _compute_narration_directive lines 408–465; velocity calc line 399–405; resolve_check call site line 635)
- `ccya/rules.py` (resolve_check function lines 172–221; near_miss logic line 203; build_directive near_miss handling line 161–164)
- `ccya/engine/narrate.py` (_filter_completed_threads line 109; _get_resolved_arc line 122)

### Detailed steps

#### Step 2.1 — Pass difficulty_modifiers into resolve_check()

**File:** `ccya/rules.py`, modify `resolve_check()` signature and body (lines 172–221)

**What:** Add an optional `difficulty_mods: dict[str, int] | None = None` parameter to resolve_check(). When provided, use it instead of the module constant DIFFICULTY_MOD. Update line 194 from `diff_mod = DIFFICULTY_MOD[difficulty]` to `diff_mod = (difficulty_mods or DIFFICULTY_MOD)[difficulty]`.

**Why:** EngineConfig.difficulty_curve resolves to a modifier dict at startup; we need to pass that into resolve_check() instead of reading the hardcoded module constant. This is the cleanest approach — one parameter, no global state changes.

Also update line 187 validation from `if difficulty not in DIFFICULTY_MOD` to use `(difficulty_mods or DIFFICULTY_MOD)`.

**Validation:** `python -c "from ccya.rules import resolve_check; r=resolve_check(skill='strength', difficulty='hard', pc_stats={'strength': 2}, pc_conditions=[], difficulty_mods={'trivial':3,'easy':1,'normal':0,'hard':-1,'extreme':-2}); assert r.diff_mod==-1"`

#### Step 2.2 — Pass near_miss_softening into resolve_check() and build_directive()

**File:** `ccya/rules.py`, modify resolve_check() (lines 172–221)

**What:** Add optional parameter `near_miss_softening: bool = True` to resolve_check(). Update line 203 from `near_miss = band == "fail" and final_total >= 5` to `near_miss = near_miss_softening and band == "fail" and final_total >= 5`. Pass it through to build_directive() at line 204 (already accepted as keyword arg).

**Why:** When near_miss_softening is False, near-fails should get harsh narration regardless of how close the roll was. This controls whether soft directive text appears on borderline failures.

#### Step 2.3 — Pass difficulty_modifiers and near_miss into resolve_check call site

**File:** `ccya/engine/turn.py`, line 635–642 (resolve_check call in ruling step)

**What:** Update the resolve_check() call to pass config fields:

```python
            outcome = resolve_check(
                skill=intent.check.skill,
                difficulty=intent.check.difficulty,
                pc_stats=(state.get("pc") or {}).get("stats") or {},
                pc_conditions=[cid for cid in _pc_cond_ids if cid],
                intent_verb=intent.intent_verb,
                intent=intent.intent,
                difficulty_mods=config._resolve_difficulty_modifiers(),
                near_miss_softening=config.near_miss_softening,
            )
```

**Why:** Config is available at line 561 as `ctx.config`. Pass the resolved modifier dict and softening flag into resolve_check().

#### Step 2.4 — Thread scene thresholds through _compute_narration_directive()

**File:** `ccya/engine/turn.py`, modify `_compute_narration_directive()` signature (line 408) and body

**What:** Add optional parameters to the function:
```python
def _compute_narration_directive(
    narrative_velocity: float,
    scope_scene_threads: list["ArcThread"],
    ages: dict[str, int],
    scene_pressure_threshold: int = 3,
    scene_imperative_threshold: int = 5,
) -> str:
```

Replace hardcoded thresholds in the function body:
- Line 425 comment and line 437 (`effective_age >= 5`) → `effective_age >= scene_imperative_threshold`
- Line 460 (`3 <= effective_age < 5`) → `scene_pressure_threshold <= effective_age < scene_imperative_threshold`

**Why:** These are the configurable scene age thresholds. Default values match current hardcoded behavior (Pressure at 3, Imperative at 5).

#### Step 2.5 — Pass scene thresholds into _compute_narration_directive() call site

**File:** `ccya/engine/turn.py`, line 486–490 (_compute_pacing_context calling _compute_narration_directive)

**What:** Update the call to pass config fields:
```python
    directive = _compute_narration_directive(
        narrative_velocity=narrative_velocity,
        scope_scene_threads=scope_scene_threads,
        ages=ages,
        scene_pressure_threshold=config.scene_pressure_threshold,
        scene_imperative_threshold=config.scene_imperative_threshold,
    )
```

**Why:** _compute_pacing_context already receives config at line 474. Pass the threshold fields through to directive computation.

#### Step 2.6 — Make momentum_pacing_factor configurable in velocity calculation

**File:** `ccya/engine/turn.py`, lines 398–405 (_narrative_velocity function)

**What:** Add optional parameter and use it instead of hardcoded values:
```python
def _narrative_velocity(
    momentum: int,
    momentum_floor: int = -3,
    momentum_ceiling: int = 3,
    pacing_factor: float = 0.5,
) -> float:
    ...
    # Scale down -- momentum alone shouldn't dominate; caps at +/-pacing_factor
    return max(-pacing_factor, min(pacing_factor, normalized * pacing_factor))
```

**Why:** The hardcoded `normalized * 0.5` and cap at ±0.5 need to be configurable. Default value of 0.5 matches current behavior exactly.

#### Step 2.7 — Pass momentum_pacing_factor into _narrative_velocity call site

**File:** `ccya/engine/turn.py`, find where _narrative_velocity is called and pass config field (search for `_narrative_velocity(` or the velocity calc logic around line 403).

**What:** Pass `pacing_factor=config.momentum_pacing_factor` into the call.

#### Step 2.8 — Thread thread_memory_ttl and arc_memory_ttl through narrate.py functions

**File:** `ccya/engine/narrate.py`, modify `_filter_completed_threads()` (line 109) and `_get_resolved_arc()` (line 122)

**What:** Add optional TTL parameters with defaults:
```python
def _filter_completed_threads(arc: dict[str, Any], turn_no: int, ttl: int = 3) -> list[dict[str, Any]]:
    ...
    # Use configurable TTL; default to 3 turns for backward compatibility

def _get_resolved_arc(state: dict[str, Any], turn_no: int, ttl: int = 3) -> list[dict[str, Any]]:
    ...
```

Replace `ttl = 3` at line 112 and line 124 with the parameter.

**Why:** These are configurable memory depth settings for how long past resolutions stay visible in narration context. Default of 3 matches current behavior.

#### Step 2.9 — Pass TTL fields into narrate.py functions from _narrate_messages() call site

**File:** `ccya/engine/narrate.py`, within `_narrate_messages()` at lines 54 and 66 where the TTL functions are called:
```python
            "resolved_arc": _get_resolved_arc(state, turn_no, ttl=arc_ttl),
...
            "completed_threads": _filter_completed_threads(arc, turn_no, ttl=thread_ttl),
```

**What:** Add `arc_ttl` and `thread_ttl` parameters to `_narrate_messages()` signature (around line 19) and pass them through from the call site in turn.py.

---

## Implementation — Phase 3: UI form controls with tooltips

### Context files to load
- `ccya/templates/index.html` (settings modal HTML lines ~254–340; Alpine.js settings state/methods around line 1750)

### Detailed steps

#### Step 3.1 — Add new fields to settings modal HTML

**File:** `ccya/templates/index.html`, within the `.settings-body` div (after existing fieldset for "Game Options", before status message at ~line 324)

**What:** Add three new fieldsets with emoji labels and tooltips:

```html
<!-- Difficulty -->
<fieldset class="settings-fieldset">
    <legend>⚔️ Difficulty</legend>
    
    <label class="setting-row has-tooltip">
        <span class="setting-label">Curve</span>
        <div class="tooltip-body">How challenging are rolls overall. "Forgiving" gives generous bonuses to easy actions; "Demanding" makes hard and extreme checks punishing.</div>
        <select x-model="settings.difficulty_curve">
            <option value="forgiving">🤝 Forgiving</option>
            <option value="balanced">⚖️ Balanced</option>
            <option value="demanding">💀 Demanding</option>
        </select>
    </label>
</fieldset>

<!-- Pacing -->
<fieldset class="settings-fieldset">
    <legend>🎬 Pacing</legend>
    
    <div class="setting-row has-tooltip">
        <span class="setting-label">Scene turnover speed</span>
        <div class="tooltip-body">How quickly stale scenes trigger Pressure or Imperative directives. "Slow burn" gives scenes more time; "Fast forward" pushes action sooner.</div>
        <select x-model.number="settings.scene_pressure_threshold">
            <option :value="2">⚡ Fast</option>
            <option :value="3">🎬 Normal</option>
            <option :value="5">🐌 Slow burn</option>
        </select>
    </div>

    <div class="setting-row has-tooltip">
        <span class="setting-label">Momentum influence on pacing</span>
        <div class="tooltip-body">How much good or bad rolls steer the narrative direction. "Subtle" means momentum barely nudges pacing; "Strong" means roll outcomes directly shape scene motion.</div>
        <select x-model.number="settings.momentum_pacing_factor">
            <option :value="0.3">🌊 Subtle</option>
            <option :value="0.5">⚖️ Normal</option>
            <option :value="1.0">💨 Strong</option>
        </select>
    </div>
</fieldset>

<!-- Failure tone -->
<fieldset class="settings-fieldset">
    <legend>🎭 Failure tone</legend>
    
    <div class="setting-row setting-toggle has-tooltip">
        <span class="setting-label">Near-miss softening</span>
        <div class="tooltip-body">When a roll barely fails (just 1 or 2 points away from success), should the narration soften the blow with "the roll was close" instead of harsh failure text?</div>
        <button type="button" 
                @click="settings.near_miss_softening = !settings.near_miss_softening"
                :class="{ 'toggle-on': settings.near_miss_softening }"
                class="setting-toggle-btn">
            <div class="toggle-knob"></div>
        </button>
    </div>

    <div class="setting-row has-tooltip">
        <span class="setting-label">Thread memory depth</span>
        <div class="tooltip-body">How long resolved threads and arcs stay visible in narration context. "Shallow" means fresh context each turn; "Deep" keeps past resolutions visible longer for continuity.</div>
        <select x-model.number="settings.thread_memory_ttl">
            <option :value="1">📄 Shallow</option>
            <option :value="3">🎭 Normal</option>
            <option :value="6">📚 Deep</option>
        </select>
    </div>
</fieldset>
```

**Why:** These are the 7 new form controls matching the agreed-upon menu structure. Each has emoji labels for visual flair, tooltips explaining what each setting does in player-friendly terms (not engine jargon), and sensible preset options or toggle states.

The difficulty_curve uses a `<select>` with string values since it's a preset selector rather than a numeric field. Scene turnover speed and momentum influence use select presets matching the agreed-upon option sets. Near-miss softening is an on/off toggle (boolean). Thread memory TTL uses select presets for shallow/normal/deep.

**Validation:** Open settings modal — verify all 7 new fields render correctly with emoji labels, tooltips appear on hover via existing _bindTooltips() system, and values match current config.yaml or defaults.

---

### Tests to write or update

None per AGENTS.md directive: "Tests are temporarily removed during refactor." Manual verification only:
1. Open settings modal → verify all 7 new fields render with emoji labels and tooltips
2. Change each field → save → reload page → verify values persist from config.yaml
3. Test difficulty_curve presets affect roll outcomes (forgiving gives +1 to trivial vs balanced's +2)
4. Test scene turnover speed changes directive triggers at different scene ages
