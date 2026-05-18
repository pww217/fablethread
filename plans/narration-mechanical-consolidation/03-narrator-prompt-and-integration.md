# Narrator Prompt and Integration Changes

## Status
`open`

## Phases

1 phase: update Narrate step to remove deescalate/narrative_velocity kwargs from `_narrate_messages()`, pass `PacingContext.directive` (tone/direction for prose) and `beat_hint` instead, clean up turn.py callers that pass the old pacing signals to Narrate.

## Issue

Narrate receives 3+ independent pacing inputs (`directive`, `deescalate`, `narrative_velocity`) when only directive matters for prose tone/direction. The raw float values of velocity and deescalate boolean are noise — they don't help write better text when the LLM already has the authoritative directive from Python's consolidated computation in phase 02. Lines 97-134 of `narrate_user.j2` contain Jinja2 logic that duplicates Python's pacing decision tree (velocity < -0.3 → Breathe, immediate_count ≥ 3 → Overwhelm, etc.) — the LLM sees both Python-computed directive AND raw velocity floats it cannot reconcile with each other. This creates conflicting signals where narrative_velocity might say "Breathe" while deescalate says something different, forcing the LLM to guess which signal is authoritative for prose tone.

## Solution

Narrator gets exactly what prose needs: `PacingContext.directive` for tone/direction, plus `beat_hint` when a beat is pending. No velocity floats, no deescalate booleans — just the authoritative pacing decision Python already made in phase 02's `_compute_pacing_context()`. Lines 97-134 of `narrate_user.j2` (the Jinja2 directive computation logic) are replaced with direct field access to `pacing_context.directive`, `pacing_context.beat_hint`, and `pacing_context.gate`. The LLM writes appropriate prose based on directive alone (e.g., "Breathe" → calm scene-setting; "Overwhelm" → tension-building urgency). Beat_hint guides narration of pending GM beats woven into prose without a separate beat instruction block.

## Firm decisions
1. Narrator receives only 2 inputs: `directive` (tone/direction for prose) and `beat_hint` when pending — no other pacing signals are sent regardless of what Python computes internally. This is the minimum sufficient interface for prose generation; anything more would be noise that wastes tokens without improving output quality.
2. Lines 97-134 of `narrate_user.j2` (Jinja2 directive computation logic) are fully replaced with direct field access to PacingContext fields — NO Jinja2 conditional logic for computing directives in templates anymore. The template becomes a passive consumer, not a decision-maker.
3. `_narrate_messages()` function signature is updated: remove `deescalate`, `narrative_velocity` parameters; add `pacing_context=PacingContext | None = None`. All callers in turn.py updated to pass PacingContext struct instead of individual variables.

## Non-goals
- Changes to Scene Extract or State Extract prompts/templates (explicitly unchanged per design doc decision table)
- Progress Extract prompt changes (handled in 04)
- Pacing computation logic itself (handled in 02 — only template/consumption changes here)
- Removing `momentum`, `ages`, `threat_ages` from Narrate context variables — these are still used elsewhere in the template for location_age checks, combat_fatigue display, and threat aging display

## Risks, Ambiguities, and Blockers

**Risk: Jinja2 template logic duplication.** Lines 97-134 of `narrate_user.j2` contain a complete directive computation tree using Jinja2 filters (`selectattr`, comparison operators). Removing this means the LLM no longer sees velocity/deescalate values to "verify" Python's decision. The template will only show `pacing_context.directive` as text — if PacingContext is None (shouldn't happen after 02), there should be NO fallback Jinja2 computation, just an empty directive field that the LLM interprets neutrally.

**Risk: Existing tests for `_narrate_messages()` kwargs.** Tests in `test_narrate.py` and integration tests may pass deescalate/narrative_velocity as keyword arguments to `_narrate_messages()`. These must be deleted rather than retrofitted — the function signature changes, so passing old args would cause TypeError.

**Risk: Momentum display logic still uses raw momentum value.** Lines 79-89 of `narrate_user.j2` show momentum-based text ("HIGH (+{{ m }})", "FLOOR ({{ m }})"). This is separate from pacing directive computation and should remain — it gives the LLM context about where momentum sits without being a decision signal. No change needed to these lines.

**Ambiguity resolved: beat_hint behavior.** `beat_hint` is sent only when PacingContext.beat_locked=True or when there's an explicit pending_gm_beat in meta. The template uses `{% if pacing_context and pacing_context.beat_hint %}` — no Jinja2 computation, just field access. If None/empty string, the block doesn't render.

**Blockers:** Phase 02 must complete first so PacingContext struct exists with directive/beat_hint/gate fields that this phase consumes. The `_narrate_messages()` call site in turn.py (around line 782) currently passes deescalate/narrative_velocity — these are the variables being replaced.

## Dependencies
01: needs `stakes` removed from IntentEnvelope (so Narrate doesn't receive it) + unified ArcThread shape for state.arc.threads[] reference in narration context. 02: needs PacingContext struct to exist so turn.py can pass directive and beat_hint instead of the old separate signals.

---

## Implementation Steps — Phase 03: Narrator Prompt and Integration Changes

### Context files to load
The executor MUST read these files before making changes:

1. **`ccya/prompts/narrate_user.j2`** (lines 97-134) — Jinja2 directive computation logic that must be fully replaced with PacingContext field access. Lines 79-89 show momentum display which remains unchanged.
2. **`ccya/engine/turn.py`** (around line 750-809, `_narrate_messages()` call site) — where deescalate/narrative_velocity are passed to Narrate template context. Also the `_narrate_messages()` function definition around line 400+ that needs signature update.
3. **`tests/test_narrate.py`** (if exists) or integration tests — find and delete any test passing deescalate/narrative_velocity kwargs to `_narrate_messages()`.

### Detailed steps

#### Step 03.01 — Replace Jinja2 directive computation in narrate_user.j2 with PacingContext field access

**File:** `ccya/prompts/narrate_user.j2` (lines 97-134)

**What:** Delete the entire block from line 97 to line 134 inclusive — this is all Jinja2 conditional logic that computes directives based on narrative_velocity, scene_pressure counts, ages, and threat_ages. Replace it with a single PacingContext field access block:
- `pacing_context.directive` → rendered as "Narration Directive" section (if not empty)
- `pacing_context.beat_hint` → rendered as beat suggestion when pending_gm_beat exists AND pacing_context has beat_locked=True

**Why:** Lines 97-134 duplicate Python's pacing computation in Jinja2 — the LLM sees both raw velocity floats and computed directives, creating conflicting signals. Phase 02 computes PacingContext once with authoritative decision logic; phase 03 makes the template a passive consumer of that decision via direct field access only. No Jinja2 conditional directive computation should remain after this change.

**Code Snippet (replacement for lines 97-134):**
```jinja2
{% if pacing_context and pacing_context.directive %}

**Narration Directive:** {{ pacing_context.directive }}
{% endif %}
{% if pending_beat and pending_beat.type %}

**GM Beat:** {{ pending_beat.instruction }}
Surface as {{ pending_beat.surface_as }}. This is backstage direction — integrate it naturally, not as player-visible narration.
{% elif pacing_context and pacing_context.beat_hint %}

**Beat Hint:** The narrator should surface a `{{ pacing_context.beat_hint }}` beat this turn if narrative context supports it.
{% endif %}
```

**Validation:** Read the resulting template to confirm NO Jinja2 conditional logic for computing directives remains — only direct field access to `pacing_context.directive`, `pacing_context.beat_hint`. Lines 79-89 (momentum display) must remain untouched. The template should render cleanly with `{% if pacing_context and pacing_context.directive %}` blocks that produce NO output when PacingContext is None or directive is empty string.

#### Step 03.02 — Update `_narrate_messages()` function signature in turn.py

**File:** `ccya/engine/turn.py` (around line 400+)

**What:** Find the `_narrate_messages()` function definition and update its parameter list:
- **Remove:** `deescalate`, `narrative_velocity` parameters
- **Add:** `pacing_context=PacingContext | None = None` keyword argument with default None for backward compatibility during transition (though after 02 completes, it will always be provided)

**Why:** The function signature change is the core integration point — removing old pacing variables and adding PacingContext struct as the single authoritative input. Default None allows gradual rollout if needed, though phase 03 should complete fully so all callers pass PacingContext.

**Code Snippet (signature update):**
```python
def _narrate_messages(
    env: Environment,
    state: dict[str, Any],
    user_input: str,
    *,
    chronicle_tail: list[dict],
    recent_turns: list[dict],
    enable_narrate_thinking: bool = False,
    pack_style: str | None = None,
    narrator_rules: str | None = None,
    world_rules: str | None = None,
    rules_outcome: Any = None,  # RulesOutcome dataclass or None
    npc_name_pool: Any = None,
    recently_left: list[str],
    momentum: int = 0,
    pending_beat: dict[str, Any] | None = None,
    pacing_context: PacingContext | None = None,  # NEW — replaces deescalate + narrative_velocity
    ages: dict[str, int],  # kept for location_age/combat_fatigue display in template
    known_npcs: list[dict],
    present_npcs: list[dict],
    compendium_bios: str | None = None,
    pc_allegiance: str | None = None,
    scene_pressure: list[dict],  # kept for "Active Threats" display in template (lines 39-42)
    turn_no: int,
    world_factions: list[dict] | None = None,
    world_locations: list[dict] | None = None,
    threat_ages: list[dict],  # kept for "Resolve a Threat" display in template (lines 120-134)
    ...
) -> tuple[list[dict], dict]:
```

**Validation:** Run `make check` after editing to confirm syntax correctness. The function signature should have NO deescalate or narrative_velocity parameters — only pacing_context as the new PacingContext input field. Any internal template rendering that previously used these variables must now use `pacing_context.directive`, `pacing_context.beat_hint`, etc.

#### Step 03.03 — Update `_narrate_messages()` call site in run_turn() to pass PacingContext

**File:** `ccya/engine/turn.py` (around line 782-809)

**What:** Replace the deescalate and narrative_velocity keyword arguments passed to `_narrate_messages()` with pacing_context. The current code passes these variables individually — replace them with a single PacingContext struct reference:
```python
# OLD (to delete):
deescalate=deescalate,
narrative_velocity=narrative_velocity,

# NEW (replacement):
pacing_context=pacing_context,  # replaces deescalate + narrative_velocity
```

**Why:** This is the call site where PacingContext computed in step 02.02 flows into Narrate template context. The orchestrator already has `pacing_context` from `_compute_pacing_context()` — it just needs to pass it through instead of passing individual variables that are now redundant.

**Important note:** Keep these variables for compatibility until prompts fully migrate:
- `ages=ages`, `threat_ages=threat_ages`, `scene_pressure=effective_pressure` — still used elsewhere in template for display purposes (location_age check, combat_fatigue display, Active Threats section)
- `momentum=momentum`, `pending_beat=pending_gm_beat` — still needed for momentum display and beat instruction rendering

**Validation:** Run `make check && make test` after editing. The `_narrate_messages()` call should pass `pacing_context=pacing_context` as a keyword argument with NO deescalate or narrative_velocity arguments remaining in the call site. No functional change until template variables are fully migrated — for now, PacingContext is computed and passed but template may not yet use it (that's covered by step 03.01).

#### Step 03.04 — Delete tests for removed `_narrate_messages()` kwargs

**File:** `tests/test_narrate.py` or relevant test files

**What:** Find and delete any test functions that:
- Call `_narrate_messages(deescalate=..., narrative_velocity=...)` with the old parameters
- Assert on template rendering behavior based on deescalate/narrative_velocity values (e.g., "verify Breathe directive appears when velocity < -0.3")

**Why:** AGENTS.md says "remove dead code immediately." Tests for removed function parameters are themselves dead code — they test behavior that no longer exists after the signature change. The PacingContext computation behavior is covered by phase 02's tests in `test_pacing.py`.

**Validation:** Run `grep -rn 'deescalate.*_narrate_messages\|narrative_velocity.*_narrate_messages' tests/` — should return zero matches after deletion. Also run `make check && make test` to confirm no broken imports or missing function parameters in test harnesses.

### Tests to write or update

#### Delete: Any test passing deescalate/narrative_velocity to `_narrate_messages()`
**What:** Find all tests that call `_narrate_messages(deescalate=..., narrative_velocity=...)` and delete them entirely — these test behavior that no longer exists after the signature change. The PacingContext computation behavior is covered by phase 02's `test_pacing.py` tests for directive/beat_hint/gate computation.

#### New: `test_narrate_messages_receives_pacing_context_directive`
**File:** `tests/test_narrate.py` (or create if doesn't exist)  
**What:** Call `_narrate_messages()` with a PacingContext containing `directive="Breathe"` and verify the rendered template output contains "Narration Directive: Breathe" in the Jinja2 context variables passed to template rendering. Assert NO deescalate or narrative_velocity variables are present in template context dict.

#### New: `test_narrate_messages_pacing_context_none_no_directive_rendered`
**File:** `tests/test_narrate.py`  
**What:** Call `_narrate_messages()` with `pacing_context=None`. Assert that NO "Narration Directive" section appears in template output — the `{% if pacing_context and pacing_context.directive %}` block should produce no output when PacingContext is None.

#### New: `test_narrate_messages_beat_hint_rendered_when_locked`
**File:** `tests/test_narrate.py`  
**What:** Call `_narrate_messages()` with PacingContext containing `beat_hint="breathing_room"` and pending_gm_beat=None (no explicit beat in meta). Assert template output contains "Beat Hint: The narrator should surface a breathing_room beat this turn if narrative context supports it."

### REPOMAP updates required

Update `docs/repomap.md`:
- **Module index (~line 12):** Update `ccya/engine/turn.py` description to note "_narrate_messages() receives PacingContext struct (directive + beat_hint) instead of separate deescalate/narrative_velocity variables — template consumes these via direct field access."
- **5-call turn pipeline section:** Add a line after step 2 noting "Narrate prompt uses pacing_context.directive for tone/direction; NO Jinja2 directive computation remains in templates — all directives computed by Python's _compute_pacing_context() in phase 02."
