# Pacing Directive & Beat Constraint Overhaul

## Purpose

Rewire how pacing directives (Scene Imperative, Scene Pressure, Breathe) and the death spiral signal interact with beat-type constraints, fixing the stuck-in-scene loop where a player gets compounding pressure beats despite the system trying to break the scene.

## Problem Statement

Scene Imperative fires correctly when a scene is stale (age >= 4), but its directive only appears as text in the LLM prompt — the hard beat-type constraints are gated exclusively by scene phase (RISING/CRISIS/etc.). When Scene Imperative fires while phase is RISING, the allowed beats still include `pressure`, `complication`, `escalation` — the exact beats that keep the player stuck. Separately, the system has no detection for when a player is losing repeatedly (death spiral), so a player can fail 5 rolls in a row and get zero system-level relief.

## Constraints

- No changes to threads, arcs, NPCs, inventory, or scene phase transitions
- No new directives or beat types — only rewire how existing directives constrain beats
- Beat constraint function signature changes are additive (new optional params with defaults) — all existing callers unchanged
- Must not regress existing behavior for normal (non-spiral, no-directive) turns

## Non-goals

- Thread forcing or thread resolution changes
- Condition counting
- Config UI or save-state migration
- Arc-level pacing changes
- Narrate pipeline changes beyond one soft nudge in the user prompt
- Changes to storytell output schema or action generation

## Solution

Three mechanical changes: (1) `derive_allowed_beat_types()` gains optional `directive` and `spiral_detected` params that override the phase-based defaults when Scene Imperative, Breathe, or spiral-detected are active; (2) a spiral detection function tracks roll-difficulty history and flags when 3 consecutive or 3/5 recent rolls are "hard" or worse; (3) the turn pipeline appends roll bands to a `recent_rolls` rolling window after the ruling phase, computes the spiral flag before narrate, and passes it to both narrate and storytell so the beat constraint can enforce it.

## Firm decisions

1. Beat constraints are filtered by directive: Scene Imperative → situation-changers + opportunity; Breathe → relief + revelation + callback; Scene Pressure → phase defaults unchanged.
2. Spiral detection uses roll difficulty bands ("hard" or worse), window of 5, threshold of 3 consecutive or 3/5.
3. Spiral flag removes all pressure bucket types (pressure, complication, escalation) from the phase defaults. Does not restrict situation-changers or relief.
4. outcome_hint is text-only, never a hard constraint.
5. Current turn's roll counts same-turn for spiral detection.
6. Spiral decays after 2 non-hard rolls.
7. No thread forcing, no condition counting.

## Risks, Ambiguities, and Blockers

- The beat constraint is enforced via prompt instruction + the `allowed_beat_types` line in the user prompt. If the LLM routinely ignores it, the fix must move to structured output schema enforcement. The existing `enforce_relief` mechanism works the same way and is effective, so this is low risk.
- `recent_rolls` state will be appended to `state["meta"]` which is already a mutable dict used for rolling state. No persistence format change needed.

## Status

`completed`

## Phases

5 phases: (1) models and beat constraint logic, (2) pipeline wiring, (3) prompt template updates, (4) documentation, (5) close plan.

---

## Implementation — Phase 1: Models and Beat Constraint Logic

### Context files to load

- `ccya/engine/_pacing.py` (full file, 34 lines)
- `ccya/engine/turn.py:97-102` — `PacingContext` dataclass
- `ccya/engine/config.py:140-174` — existing pacing config fields
- Design doc: Beat Taxonomy section, New Model Shapes section

### Detailed steps

#### Step 1.1 — Add config fields for spiral detection

**File:** `ccya/engine/config.py` (~line 168, after `thread_max_active`)

**What:** Add three new fields to `EngineConfig`:
```python
# Death spiral detection
spiral_consecutive_hard: int = 3        # N consecutive hard+ rolls triggers spiral flag
spiral_hard_ratio: tuple[int, int] = (3, 5)  # M of last N hard+ triggers spiral flag
spiral_decay_turns: int = 2             # non-hard rolls to clear spiral flag
```

**Why:** Thresholds must be configurable for tuning and test scenarios. Defaults match the design doc consensus (3 consecutive, 3/5, 2 decay).

**Validation:** `make check` passes.

#### Step 1.2 — Add beat bucket constants and spiral detection function to `_pacing.py`

**File:** `ccya/engine/_pacing.py`

**What:** Add three pieces to the module:
1. Beat bucket constants mapping bucket names to their beat type lists:
```python
BEAT_BUCKETS: dict[str, list[str]] = {
    "pressure":    ["pressure", "complication", "escalation"],
    "situation":   ["revelation", "twist", "hazard", "callback"],
    "relief":      ["opportunity", "breathing_room"],
}
```
2. A `RollRecord` dataclass (or reuse a dict shape via Python code — see design doc model shape, but implement as a typed dict or dataclass at module level).
3. A `detect_spiral()` function with the signature from the design doc:
```python
def detect_spiral(
    recent_rolls: list[dict[str, Any]],
    consecutive_hard_threshold: int = 3,
    hard_ratio_threshold: tuple[int, int] = (3, 5),
) -> bool
```
Logic: if any X consecutive rolls (where `band in ("hard", "extreme")`) >= `consecutive_hard_threshold`, OR if Y of last Z rolls are "hard" or worse (where Y/Z from `hard_ratio_threshold`), return True. The list is ordered most-recent-first — iterate from the front.

**Why:** Bucket constants allow `derive_allowed_beat_types` to remove/add buckets by name rather than hardcoding individual beat types in the logic. `detect_spiral` encapsulates the threshold logic in one testable function.

**Note:** The `detect_spiral` signature uses `dict[str, Any]` — the module currently only imports `EngineConfig`. Add `from typing import Any` to the imports at the top of the file. With `from __future__ import annotations` already present, the import is needed for type checkers, not runtime.

**Validation:** `make check` passes.

#### Step 1.3 — Update `derive_allowed_beat_types()` signature and logic

**File:** `ccya/engine/_pacing.py`

**What:** Change signature to add `directive: str = ""` and `spiral_detected: bool = False` keyword-only parameters. Replace the body with the priority-ordered logic from the design doc:

Priority order:
1. `directive == "Scene Imperative"` → return `BEAT_BUCKETS["situation"] + BEAT_BUCKETS["relief"]` (situation-changers + opportunity)
2. `directive == "Breathe"` → return `BEAT_BUCKETS["relief"] + ["revelation", "callback"]`
3. `spiral_detected` (and no directive matched above) → start from phase defaults, then remove `BEAT_BUCKETS["pressure"]` entries from the list
4. `enforce_relief` and `scene_phase == "CRISIS"` → return `["breathing_room"]` (existing)
5. Otherwise → return `BEAT_PHASE_MAP.get(scene_phase, list(BEAT_PHASE_MAP["SETUP"]))` (existing)

**Why:** Directives must override phase-based defaults to prevent the contradiction where Scene Imperative says "break loop" but the phase allows compounding beats.

**Validation:** Unit test: call with various directive/spiral combinations and assert the returned list matches the design doc's directive-to-bucket mapping table.

#### Step 1.4 — Add `spiral_detected` field to `PacingContext`

**File:** `ccya/engine/turn.py:97-102`

**What:** Add `spiral_detected: bool = False` field after `outcome_hint`. The `PacingContext` dataclass has no factory method — just add the field with a default value; all existing construction sites (e.g., `_compute_pacing_context()` at line 480) will continue to work since the new field has a default.

**Why:** The flag needs to flow through the pipeline from the detection point to the storytell call site. Adding it to `PacingContext` is the cleanest path — it's already passed to both narrate and storytell as a single object.

**Validation:** `make check` passes.

### Tests to write or update

- `detect_spiral()`: test with empty list, clean rolls (all success), threshold-exact consecutive hards, threshold-exact ratio, mixed bands, list shorter than window, edge of threshold (2 consecutive = not triggered, 3 = triggered, 4 = still triggered).
- `derive_allowed_beat_types()`: test each priority level — Scene Imperative returns situation + relief regardless of phase, Breathe returns relief + revelation + callback regardless of phase, spiral removes pressure types from any phase default, enforce_relief + CRISIS returns breathing_room (unchanged), plain call returns phase defaults (unchanged).

---

## Implementation — Phase 2: Pipeline Wiring

### Context files to load

- `ccya/engine/turn.py:630-730` — `_ruling_phase()` end where `ctx.outcome` is set
- `ccya/engine/turn.py:733-821` — `_narrate_setup()` full function
- `ccya/engine/turn.py:824-1030` — `run_turn()` pipeline from ruling call through extraction
- `ccya/engine/extraction.py:250-289` — `_storytell_messages()` template rendering
- `ccya/engine/narrate.py:20-109` — `_narrate_messages()` function (verify it passes `pacing_context` — already does)

### Detailed steps

#### Step 2.1 — Append roll band to `recent_rolls` after ruling phase

**File:** `ccya/engine/turn.py` — in `run_turn()`, after line 882 (after `ruling_raw_response` is captured, at the point where `turn_no` is known)

**What:** After the ruling phase completes and `ctx.outcome` is set, append a record to `state["meta"]["recent_rolls"]`. Only when `ctx.outcome.rolled` is True. Record format: `{"turn": turn_no, "band": ctx.outcome.band}`. Cap the list to 5 entries (oldest discarded).

```python
# After _ruling_phase() returns and turn_no is set (around line 885)
if ctx.outcome and ctx.outcome.rolled:
    recent_rolls = state.setdefault("meta", {}).setdefault("recent_rolls", [])
    recent_rolls.insert(0, {"turn": turn_no, "band": ctx.outcome.band})
    if len(recent_rolls) > 5:
        recent_rolls.pop()
```

**Why:** The roll must be recorded before spiral detection runs later in the same turn. The recent_rolls list is the rolling window for `detect_spiral()`.

**Validation:** Turn on debug logging. Run a turn with a roll. Check `state["meta"]["recent_rolls"]` contains one entry with the correct turn and band. Run a non-roll turn — no entry added.

#### Step 2.2 — Compute spiral flag in `_narrate_setup()` after pacing context

**File:** `ccya/engine/turn.py` — in `_narrate_setup()`, after `_pc = _compute_pacing_context(...)` (after line 806)

**What:** Call `detect_spiral()` using the spiral config from `config` and the `recent_rolls` from state meta. Store the result on `TurnContext` and on `PacingContext`:

1. Add a field to `TurnContext`:
   ```python
   # In TurnContext dataclass
   _spiral_detected: bool = False
   ```
2. After `_pc = _compute_pacing_context(...)`:
   ```python
   recent_rolls = state.get("meta", {}).get("recent_rolls", [])
   ctx._spiral_detected = detect_spiral(
       recent_rolls,
       consecutive_hard_threshold=config.spiral_consecutive_hard,
       hard_ratio_threshold=config.spiral_hard_ratio,
   )
   _pc.spiral_detected = ctx._spiral_detected
   ```

**Why:** Spiral flag needs to be available to both narrate (via `pacing_context`) and storytell (via `pacing_context`). Computing it once in `_narrate_setup()` avoids recomputing.

**Validation:** Set up a scenario with 3+ consecutive hard rolls in recent_rolls. Call `_narrate_setup`. Assert `_pc.spiral_detected` is True. Run with all-success rolls — assert False.

#### Step 2.3 — Wire directive and spiral into both `derive_allowed_beat_types` call sites

**Files:** `ccya/engine/extraction.py:275-282` and `ccya/engine/turn.py:1349-1356`

**What:** Update both call sites that pass `directive` and `spiral_detected`:

**Site A** — `extraction.py:275-282` (storytell prompt constraint — authoritative):
```python
"allowed_beat_types": derive_allowed_beat_types(
    scene.get("scene_phase", "SETUP"),
    directive=pacing_context.directive if pacing_context else "",
    spiral_detected=pacing_context.spiral_detected if pacing_context else False,
    enforce_relief=derive_enforce_relief(
        scene.get("scene_phase", "SETUP"),
        state.get("meta", {}).get("consecutive_pressure_beats", 0),
        config or EngineConfig(),
    ),
),
```

**Site B** — `turn.py:1349-1356` (event logging — must match for correct debug output):
```python
"allowed_beat_types": derive_allowed_beat_types(
    state.get("scene", {}).get("scene_phase", "SETUP"),
    directive=_pc.directive if _pc else "",
    spiral_detected=_pc.spiral_detected if _pc else False,
    enforce_relief=derive_enforce_relief(
        state.get("scene", {}).get("scene_phase", "SETUP"),
        state.get("meta", {}).get("consecutive_pressure_beats", 0),
        config,
    ),
),
```

Also add `spiral_detected` to the event log's `pacing_context` dict at line 1339-1342 so the checker and ev tools can read it:
```python
"pacing_context": {
    "directive": _pc.directive if _pc else "",
    "outcome_hint": _pc.outcome_hint if _pc else None,
    "spiral_detected": _pc.spiral_detected if _pc else False,
    "summary": _pc.summary if _pc else "",
    "scene_phase": ...,
    ...
},
```

**Why:** Site A constrains the LLM prompt — this is the correctness-critical one. Site B ensures the event log matches what the LLM actually saw, preventing debug confusion. The event `pacing_context` dict must carry `spiral_detected` so checkers and ev tools can validate directive/spiral constraint compliance.

**Validation:** Add a debug log line showing the computed `allowed_beat_types` from both sites. Run a Scene Imperative turn — assert the list excludes pressure bucket types. Run a spiral turn — assert the same.

#### Step 2.4 — No changes needed to `_narrate_messages()`

**File:** `ccya/engine/narrate.py:20-109`

**What:** Verify no change is needed. `_narrate_messages()` already accepts `pacing_context: PacingContext | None` and renders it via `narrate_user.j2`. Since `PacingContext` now carries `spiral_detected`, the flag is automatically available in the template. No signature change needed.

**Why:** Passing `pacing_context` through to the narrate template is already working. The new field flows through for free.

**Validation:** (None needed — confirmed by code read.)

### Tests to write or update

- Integration test: run a turn pipeline end-to-end with a forced spiral scenario. Assert that `state["meta"]["recent_rolls"]` is populated and `pacing_context.spiral_detected` equals expected value.
- Integration test: run a turn with Scene Imperative directive. Assert that the `allowed_beat_types` rendered in the storytell prompt contains only situation-changers + opportunity.

---

## Implementation — Phase 3: Prompt Template Updates

### Context files to load

- `ccya/prompts/storytell_system.j2` (full file, 95 lines)
- `ccya/prompts/narrate_user.j2` (full file, 104 lines)
- Design doc: Beat Taxonomy section (definitions, buckets, directive mapping table)

### Detailed steps

#### Step 3.1 — Update `storytell_system.j2` with beat taxonomy and directive/spiral guidance

**File:** `ccya/prompts/storytell_system.j2`

**What:** Replace the existing phase-beat constraint table (lines 49-58) with an expanded version that documents:
1. The beat taxonomy definitions (each type's purpose, from the design doc's "Revised definitions" table)
2. The three functional buckets (pressure, situation, relief) with their types
3. The directive/spiral override mechanism: "Directives and the spiral flag can override the phase-based defaults. When Scene Imperative is active, only situation-changing and relief beats are allowed. When Breathe is active, only relief, revelation, and callback are allowed. When a spiral is detected (repeated hard rolls), pressure-type beats are removed from the allowed list — the system provides an exit vector instead of compounding the situation."
4. Keep the existing `enforce_relief` note for CRISIS

**Format:** Clear markdown tables. The LLM must be able to understand which beats are available and why. Keep it to 40-50 lines total added.

**Why:** The LLM needs to understand what each beat type means (not just its name) and that the constraints shown in `allowed_beat_types` can be narrower than the phase defaults. Without this documentation, the LLM won't respect the constraint.

**Validation:** Render the template with a test context. Assert the rendered output contains the beat taxonomy table, bucket descriptions, and the directive/spiral override note.

#### Step 3.2 — Add spiral nudge to `narrate_user.j2`

**File:** `ccya/prompts/narrate_user.j2` (around line 97-103, after the outcome_hint block)

**What:** Add a conditional block that renders when `spiral_detected` is True:
```jinja2
{%- if pacing_context and pacing_context.spiral_detected %}

**Spiral:** The player is in a downward spiral. Write an exit vector — a way through, a revelation, or a shift in circumstances.
{%- endif %}
```

**Why:** The narrator writes the scene description that establishes what's possible. A soft nudge to write an exit is low cost and helps the narrator align with the beat constraint's intent. The design doc specifies this should be a soft nudge, not a directive.

**Validation:** Render with `spiral_detected=True` — assert the nudge text appears. Render with `spiral_detected=False` — assert it does not.

### Tests to write or update

- Template rendering test: render `storytell_system.j2` with a test context. Assert the output contains key phrases from the beat taxonomy and directive/spiral override section.
- Template rendering test: render `narrate_user.j2` with `pacing_context.spiral_detected=True/False`. Assert nudge presence matches.

---

## Implementation — Phase 4: Documentation

### Context files to load

- `docs/repomap.md` (find the pacing/beat section)
- `docs/architecture/OVERVIEW.md` (find the pipeline section)
- `docs/architecture/` directory listing to find relevant subdocs

### Detailed steps

#### Step 4.1 — Update `docs/repomap.md`

**File:** `docs/repomap.md`

**What:** Find the section describing `_pacing.py` module boundaries and the beat constraint data flow. Add:
- `BEAT_BUCKETS` constant with its bucket structure
- `detect_spiral()` function signature and purpose
- Updated `derive_allowed_beat_types()` signature to note directive/spiral params
- `spiral_detected` field on `PacingContext`
- `recent_rolls` in state meta description

**Why:** Repomap is the primary signpost for navigators. Stale repomap = navigation bugs for future implementers.

**Validation:** `grep` for the existing `_pacing.py` entry in repomap. Confirm the update adds the new functions and fields.

#### Step 4.2 — Update pipeline architecture docs

**File:** `docs/architecture/OVERVIEW.md` (or the relevant pipeline subdoc)

**What:** Find the section describing the turn pipeline steps. Update the step list to include the `recent_rolls` append step (after ruling, before narrate setup) and the spiral detection step (in narrate setup, after pacing context computation). Also update the PacingContext data shape description to include `spiral_detected`.

**Why:** The timing section of the design doc specifies an exact pipeline order. This must be documented in the architecture doc for future debuggers.

**Validation:** Read the updated section. Confirm it matches the timing section from the design doc (steps 1-7 in order).

### Tests to write or update

(None — documentation only.)

---

## Implementation — Phase 5: Close plan

### Context files to load

(No code changes — repository-level integration check.)

### Detailed steps

#### Step 5.1 — Run `make check`

**File:** Repository root

**What:** Run `make check` (ruff + mypy) on the full codebase to confirm no lint or type errors.

**Why:** Required by AGENTS.md — final step when ALL work is complete.

**Validation:** `make check` exits 0.

#### Step 5.2 — Move plan to completed

**File:** `plans/pacing-directive-beat-constraint.md` → `plans/completed/04-pipeline/pacing-directive-beat-constraint.md`

**What:** Move the plan file to the completed plans directory under the pipeline category. All other existing plans follow this convention.

**Why:** The plan lifecycle policy in AGENTS.md specifies completed plans live in `plans/completed/` organized by category.

**Validation:** File exists at the new path, not at the old path. Update the Status line to `completed`.

### Tests to write or update

(None — repository-level integration check only.)
