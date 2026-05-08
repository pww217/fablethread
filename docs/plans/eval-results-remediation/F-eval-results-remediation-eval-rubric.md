# Eval Rubric and Auto-Checker Overhaul

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective
The current rubric has two aggregate scores (`mechanical_score`, `narrative_score`) and five
pipeline sub-scores (1–5 each). The normalization code in `judge.py` only accepts those exact
keys. The rubric itself conflates issues that should be separately tracked — it doesn't produce
scores the report can act on granularly, the auto-checker assertions are too narrow to catch
the bugs the two eval runs surfaced, and the judge output format has no anchors (what does a
3/5 mean vs a 4/5?). This plan hardens all three layers: rubric (the judge's system prompt),
auto-checker assertions (`universal_asserts.py`), and the score normalization/reporting path
in `judge.py` + `report.py`.

## Non-goals
- Does not change how the trace is built (`build_trace`, `TraceOptions`).
- Does not change `EvalConfig`, `JudgeConfig`, or `evals/config.yaml` structure.
- Does not change the runner, scenario format, or how events are collected.
- Does not rename the existing pipeline extractor calls (scene/state/progress rename is in a
  separate plan).
- Does not add new auto-checker assertions that require reading source files not yet inspected
  (e.g., dice band computation); those are follow-on.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `evals/rubrics/default.md` | modify | Rewrite rubric: anchor score definitions, add gm_beat auto-fail, add cross-turn consistency criterion, tighten issues taxonomy, update output YAML keys |
| `ccya/eval/judge.py` | modify | `_normalize_scores`: accept new YAML keys; add `gm_beat_empty_autofail` flag; validate score ranges; update `_render_static_context` pipeline label for future rename-compatibility |
| `ccya/eval/universal_asserts.py` | modify | Add 5 new assertions: gm_beat instruction non-empty, pressure lifecycle validity, inventory transfer matched, quest objective done-on-success-only, no-roll binding not injected |
| `ccya/eval/report.py` | modify | Render new score keys in judge summary block; render `gm_beat_empty_autofail` flag; add per-dimension score table in judge summary |
| `docs/REPOMAP/eval.md` | update | Reflect new assertion names, new score keys, updated rubric path note |
| `docs/plans/TODO.md` | update | Add this plan under P2 |

## Firm decisions

1. **Score scale stays 1–5.** The existing `_normalize_scores` clamp logic is correct; we expand
   which keys it accepts, not the range. `report.py` renders `pipeline_scores` already by key
   name — we add new keys alongside the existing ones so old runs still render without error.

2. **New YAML front-matter keys are additive.** The judge output gains `dimension_scores` (a new
   sub-dict) and an optional `gm_beat_empty_autofail: true/false` bool. Old keys
   (`mechanical_score`, `narrative_score`, `pipeline_scores`) are kept unchanged so any
   already-run judge.md is still parseable by the old report.

3. **Auto-checker failures are fail-only, never warn.** Assertions either pass or fail. No
   severity tiers in `universal_asserts.py` — that complexity belongs in `report.py` flag
   categorization, which already has `flag_at_top`.

4. **Rubric rewrite preserves all existing evaluation criteria.** The new rubric adds anchors
   and a new `cross_turn_consistency` narrative criterion; it does not remove any existing
   criterion. All existing `pipeline_scores` sub-keys remain valid.

5. **`gm_beat_empty_autofail` in the judge front matter is a boolean flag, not a score
   reduction.** `report.py` will surface it as a flag rather than mechanically penalizing the
   `mechanical_score`. The score is still the judge's subjective call.

6. **Rubric instruction tense: present tense, imperative.** Every rubric instruction is phrased
   as "You must..." or "For each turn, check..." — not "Ideally..." or "Consider...".
   Permissive language in the rubric correlates with permissive scores.

7. **Conditional Jinja is not applicable here** — the rubric is a static markdown file, not a
   Jinja template. All rubric content is always included.

---

## Implementation — Phase 1: Auto-Checker New Assertions

### Context files to load
- `ccya/eval/universal_asserts.py` (full — already read)
- `ccya/eval/judge.py` (full — already read, needed for how failures are consumed)

### Overview
Add five new assertion functions to `universal_asserts.py` and register them in
`run_all_universal_asserts`. Each function has the same signature as existing ones:
`(event, prev_event) -> dict` with keys `assertion`, `passed`, `detail`, `scope`.

### Detailed steps

#### Step 1.1 — `check_gm_beat_instruction_nonempty`

**File:** `ccya/eval/universal_asserts.py`

**What:** Assert that if a `gm_beat` was applied this turn, its `instruction` field is a
non-empty string (not `""`, not `null`, not a whitespace-only string).

**Why:** The two eval runs showed `gm_beat` entries with blank `instruction` fields being
applied, producing beats with no actionable guidance for the narrator. This is a direct output
quality failure.

**Code Snippet**
```python
def check_gm_beat_instruction_nonempty(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """gm_beat applied this turn must have a non-empty instruction string."""
    applied = event.get("applied") or {}
    beat = applied.get("gm_beat")
    if beat is None:
        return {
            "assertion": "universal.gm_beat.instruction_nonempty",
            "passed": True,
            "detail": "(no beat applied)",
            "scope": "universal",
        }
    if not isinstance(beat, dict):
        return {
            "assertion": "universal.gm_beat.instruction_nonempty",
            "passed": True,
            "detail": "(beat not a dict — skipping)",
            "scope": "universal",
        }
    instruction = beat.get("instruction") or ""
    if not instruction.strip():
        return {
            "assertion": "universal.gm_beat.instruction_nonempty",
            "passed": False,
            "detail": f"gm_beat applied with empty/null instruction: {beat}",
            "scope": "universal",
        }
    return {
        "assertion": "universal.gm_beat.instruction_nonempty",
        "passed": True,
        "detail": f"instruction present ({len(instruction)} chars)",
        "scope": "universal",
    }
```

**Validation:** Run `make test`. Verify assertion name matches `universal.gm_beat.instruction_nonempty` string exactly.

---

#### Step 1.2 — `check_pressure_lifecycle_valid`

**File:** `ccya/eval/universal_asserts.py`

**What:** For each `scene_pressure_add` in `applied` this turn, assert the pressure either
(a) didn't exist in the prior state, OR (b) existed but is being re-added with a higher
severity (background → building → immediate). Also: for each `scene_pressure_remove` in
`applied`, verify the removed pressure ID exists in the prior state snapshot.

**Why:** Eval runs showed pressure being removed when not resolved (location change as false
trigger) and pressure being added redundantly without escalating severity.

**Code Snippet**
```python
_PRESSURE_SEVERITY_RANK = {"background": 0, "building": 1, "immediate": 2}


def check_pressure_lifecycle_valid(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """scene_pressure adds must not re-add same-severity entries; removes must exist."""
    applied = event.get("applied") or {}
    prev_snap = (prev_event.get("state_snapshot") or {}) if prev_event else {}
    prev_pressures: dict[str, Any] = {}
    for p in (prev_snap.get("scene") or {}).get("scene_pressures") or []:
        if isinstance(p, dict) and p.get("id"):
            prev_pressures[p["id"]] = p

    issues: list[str] = []

    for p in applied.get("scene_pressure_add") or []:
        if not isinstance(p, dict):
            continue
        pid = p.get("id")
        sev = p.get("severity", "background")
        if pid and pid in prev_pressures:
            old_sev = prev_pressures[pid].get("severity", "background")
            old_rank = _PRESSURE_SEVERITY_RANK.get(old_sev, 0)
            new_rank = _PRESSURE_SEVERITY_RANK.get(sev, 0)
            if new_rank <= old_rank:
                issues.append(
                    f"pressure '{pid}' re-added at same/lower severity "
                    f"({old_sev} → {sev})"
                )

    for p in applied.get("scene_pressure_remove") or []:
        pid = p if isinstance(p, str) else (p.get("id") if isinstance(p, dict) else None)
        if pid and pid not in prev_pressures:
            issues.append(f"pressure '{pid}' removed but did not exist in prior state")

    if issues:
        return {
            "assertion": "universal.pressure_lifecycle.valid",
            "passed": False,
            "detail": "; ".join(issues),
            "scope": "universal",
        }
    return {
        "assertion": "universal.pressure_lifecycle.valid",
        "passed": True,
        "detail": f"ok ({len(applied.get('scene_pressure_add') or [])} adds, "
                  f"{len(applied.get('scene_pressure_remove') or [])} removes)",
        "scope": "universal",
    }
```

**Validation:** `make test`. Confirm assertion fires on a fixture event where a background pressure is re-added as background.

---

#### Step 1.3 — `check_quest_objective_done_on_success_only`

**File:** `ccya/eval/universal_asserts.py`

**What:** If `rules.band` is `fail`, `crit_fail`, or `setback`, assert no quest objective in
`applied.quest_updates` has `done: true` set this turn.

**Why:** Eval runs showed objectives marked `done: true` on partial/setback bands. Objectives
should only complete on success or crit_success bands.

**Code Snippet**
```python
_FAIL_BANDS = frozenset({"fail", "crit_fail", "setback"})


def check_quest_objective_done_on_success_only(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """Quest objectives must not be marked done=true on fail/crit_fail/setback bands."""
    rules = event.get("rules") or {}
    band = (rules.get("band") or "").lower()
    if band not in _FAIL_BANDS:
        return {
            "assertion": "universal.quest_objective.done_on_success_only",
            "passed": True,
            "detail": f"(band={band or 'none'} — not a fail band)",
            "scope": "universal",
        }
    applied = event.get("applied") or {}
    bad_objectives: list[str] = []
    for qu in applied.get("quest_updates") or []:
        if not isinstance(qu, dict):
            continue
        for obj in qu.get("objectives") or []:
            if isinstance(obj, dict) and obj.get("done") is True:
                bad_objectives.append(
                    f"quest={qu.get('id','?')} obj={obj.get('id','?')}"
                )
    if bad_objectives:
        return {
            "assertion": "universal.quest_objective.done_on_success_only",
            "passed": False,
            "detail": f"band={band}, done objectives: {bad_objectives}",
            "scope": "universal",
        }
    return {
        "assertion": "universal.quest_objective.done_on_success_only",
        "passed": True,
        "detail": f"band={band}, no objectives completed",
        "scope": "universal",
    }
```

**Validation:** `make test`. Confirm fires when a fixture event has `band: fail` and `done: true`.

---

#### Step 1.4 — `check_no_roll_no_binding`

**File:** `ccya/eval/universal_asserts.py`

**What:** If `rules.rolled` is `false` (or absent), assert the narrate user prompt does NOT
contain the `rules_outcome (BINDING` string. Complement to the existing
`check_rolled_implies_binding`.

**Why:** The inverse failure — injecting a BINDING block on a no-roll turn — causes the
narrator to behave as if a roll occurred when none did. Eval runs showed this sporadically on
turns classified as social/descriptive with no check.

**Code Snippet**
```python
def check_no_roll_no_binding(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """If rules.rolled=false, narrate user prompt must NOT contain BINDING block."""
    rules = event.get("rules") or {}
    if rules.get("rolled"):
        return {
            "assertion": "universal.narrate.no_binding_on_no_roll",
            "passed": True,
            "detail": "(roll occurred — skip)",
            "scope": "universal",
        }
    nu = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    if "rules_outcome (BINDING" in nu:
        return {
            "assertion": "universal.narrate.no_binding_on_no_roll",
            "passed": False,
            "detail": "rolled=false but BINDING block present in narrate user prompt",
            "scope": "universal",
        }
    return {
        "assertion": "universal.narrate.no_binding_on_no_roll",
        "passed": True,
        "detail": "no roll, no binding block",
        "scope": "universal",
    }
```

**Validation:** `make test`.

---

#### Step 1.5 — `check_pending_gm_beat_nonempty`

**File:** `ccya/eval/universal_asserts.py`

**What:** If `state_snapshot.scene.pending_gm_beat` is set, assert its `instruction` field is
non-empty. This catches the case where a beat is stored to state but is hollow — it will still
be consumed by the narrator next turn but provide no guidance.

**Why:** Different from Step 1.1 (which checks `applied.gm_beat`). This assertion catches
hollow beats *in state* — they were applied in a prior turn with bad content and are now
sitting as the pending beat for the next narrator call.

**Code Snippet**
```python
def check_pending_gm_beat_nonempty(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """state_snapshot.scene.pending_gm_beat.instruction must not be empty if beat is set."""
    snap = event.get("state_snapshot") or {}
    beat = (snap.get("scene") or {}).get("pending_gm_beat")
    if beat is None:
        return {
            "assertion": "universal.pending_gm_beat.instruction_nonempty",
            "passed": True,
            "detail": "(no pending beat)",
            "scope": "universal",
        }
    if not isinstance(beat, dict):
        return {
            "assertion": "universal.pending_gm_beat.instruction_nonempty",
            "passed": True,
            "detail": "(pending beat not a dict — skipping)",
            "scope": "universal",
        }
    instruction = beat.get("instruction") or ""
    if not instruction.strip():
        return {
            "assertion": "universal.pending_gm_beat.instruction_nonempty",
            "passed": False,
            "detail": f"pending_gm_beat in state has empty instruction: {beat}",
            "scope": "universal",
        }
    return {
        "assertion": "universal.pending_gm_beat.instruction_nonempty",
        "passed": True,
        "detail": f"instruction present ({len(instruction)} chars)",
        "scope": "universal",
    }
```

**Validation:** `make test`.

---

#### Step 1.6 — Register all new assertions in `run_all_universal_asserts`

**File:** `ccya/eval/universal_asserts.py`

**What:** Add all five new functions to the `run_all_universal_asserts` return list.

**Code Snippet**
```python
def run_all_universal_asserts(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> list[dict[str, Any]]:
    return [
        check_recent_events_turn_stamped(event),
        check_pending_gm_beat_consumed(event, prev_event),
        check_location_change_applied(event, prev_event),
        check_rolled_implies_binding(event),
        check_npc_mention_extracted(event),
        # New assertions:
        check_gm_beat_instruction_nonempty(event, prev_event),
        check_pressure_lifecycle_valid(event, prev_event),
        check_quest_objective_done_on_success_only(event, prev_event),
        check_no_roll_no_binding(event, prev_event),
        check_pending_gm_beat_nonempty(event, prev_event),
    ]
```

**Validation:** `make check && make test`. All existing tests pass. New assertions appear in REPORT.md auto-checker table.

---

### Tests to write or update

**File:** `tests/eval/test_universal_asserts.py` (create if absent, add to if exists)

For each new assertion, write at minimum:
- `test_check_gm_beat_instruction_nonempty_passes_no_beat` — event with no `applied.gm_beat`
- `test_check_gm_beat_instruction_nonempty_passes_with_instruction` — beat with non-empty instruction
- `test_check_gm_beat_instruction_nonempty_fails_empty_instruction` — beat with `instruction: ""`
- `test_check_pressure_lifecycle_valid_passes_new_pressure` — pressure_add where ID is not in prev state
- `test_check_pressure_lifecycle_valid_fails_same_severity_readd` — pressure_add at same severity as existing
- `test_check_pressure_lifecycle_valid_fails_remove_nonexistent` — pressure_remove for ID not in prev state
- `test_check_quest_objective_done_on_success_only_passes_success` — band=success, done=true (allowed)
- `test_check_quest_objective_done_on_success_only_fails_fail_band` — band=fail, done=true
- `test_check_no_roll_no_binding_passes_no_roll_no_binding` — rolled=false, no BINDING in prompt
- `test_check_no_roll_no_binding_fails_no_roll_with_binding` — rolled=false but BINDING present
- `test_check_pending_gm_beat_nonempty_passes_no_beat` — no pending beat in state
- `test_check_pending_gm_beat_nonempty_fails_empty_instruction` — pending beat with `instruction: ""`

Each test constructs a minimal `event` dict with only the required keys. No FakeLLM needed — these are pure dict assertions.

### REPOMAP updates required
`docs/REPOMAP/eval.md` — add new assertion names to the `universal_asserts.py` entry.

### Risks
1. `check_pressure_lifecycle_valid` path for `scene_pressure_remove` — the applied delta
   format for removes may be a list of strings (pressure IDs) or a list of dicts. The
   implementation handles both; verify against actual events.jsonl from a run before
   committing.
2. `check_quest_objective_done_on_success_only` — the `band` field lives at `event.rules.band`
   per the engine REPOMAP. Confirm this key path is correct at test time; the assertion
   silently passes if band is absent rather than falsely failing.

---

## Implementation — Phase 2: `judge.py` Score Normalization + Flag

### Context files to load
- `ccya/eval/judge.py` (full — already read)
- `ccya/eval/config.py` (full — already read)

### Overview
Extend `_normalize_scores` in `judge.py` to accept a new `dimension_scores` sub-dict (added
in Phase 3's rubric) and a `gm_beat_empty_autofail` boolean. Add the autofail check. Update
`report.py` to render the new dimension scores table.

### Detailed steps

#### Step 2.1 — Extend `_normalize_scores`

**File:** `ccya/eval/judge.py`

**What:** Accept `dimension_scores` dict (7 keys, 1–5 each) and `gm_beat_empty_autofail` bool
from the YAML front matter. Existing keys (`mechanical_score`, `narrative_score`,
`pipeline_scores`) are unchanged.

**Why:** The new rubric emits `dimension_scores` as a separate block. The normalization must
pass it through to `JudgeResult.scores` so `report.py` can render it.

**Code Snippet**
```python
_DIMENSION_SCORE_KEYS = frozenset({
    "narration_fidelity",
    "prose_quality",
    "rules_classification",
    "extraction_accuracy",
    "quest_pressure_tracking",
    "gm_beat_quality",
    "cross_turn_consistency",
})

_PIPELINE_SCORE_KEYS = frozenset({
    "rules", "narrate", "extract_scene", "extract_state", "extract_progress"
})


def _normalize_scores(fm: dict[str, Any]) -> dict[str, Any]:
    """Coerce score values to ints clamped 1-5. Pass through other fields untouched."""
    def _coerce(v: Any) -> int | None:
        try:
            n = int(round(float(v)))
        except (TypeError, ValueError):
            return None
        return max(1, min(5, n))

    out: dict[str, Any] = {}
    for k in ("mechanical_score", "narrative_score"):
        if k in fm:
            out[k] = _coerce(fm[k])

    ps = fm.get("pipeline_scores") or {}
    if isinstance(ps, dict):
        out["pipeline_scores"] = {
            k: _coerce(v) for k, v in ps.items() if k in _PIPELINE_SCORE_KEYS
        }

    ds = fm.get("dimension_scores") or {}
    if isinstance(ds, dict):
        out["dimension_scores"] = {
            k: _coerce(v) for k, v in ds.items() if k in _DIMENSION_SCORE_KEYS
        }

    autofail = fm.get("gm_beat_empty_autofail")
    if autofail is not None:
        out["gm_beat_empty_autofail"] = bool(autofail)

    return out
```

**Validation:** Unit test: feed a dict with both old and new keys; assert all are present in output, all scores clamped 1–5, `gm_beat_empty_autofail` is bool.

---

#### Step 2.2 — `report.py`: render dimension scores and autofail flag

**File:** `ccya/eval/report.py`

**What:** In `_render_judge_summary`, after the existing `pipeline_scores` block, render a
`dimension_scores` table if present. In `_collect_flags`, add a `gm_beat_autofail` flag if
`judge.scores.get("gm_beat_empty_autofail") is True`.

**Why:** These are the two visible surfaces where the new data reaches the user.

**Code Snippet**
```python
# In _render_judge_summary, after the pipeline_scores block:
ds = scores.get("dimension_scores") or {}
if ds:
    parts.append("")
    parts.append("**Dimension scores:**")
    for k in (
        "narration_fidelity", "prose_quality", "rules_classification",
        "extraction_accuracy", "quest_pressure_tracking",
        "gm_beat_quality", "cross_turn_consistency",
    ):
        v = ds.get(k, "?")
        parts.append(f"- {k}: {v}/5")

# In _collect_flags, before the judge_score_drop block:
if judge is not None and (judge.scores or {}).get("gm_beat_empty_autofail"):
    flags.append(
        Flag(
            kind="gm_beat_autofail",
            summary="judge flagged gm_beat with empty instruction this run",
            detail="See judge.md for which turns. Root cause: progress extractor "
                   "emitted a gm_beat with blank instruction field.",
        )
    )
```

**Validation:** Run eval on an existing events.jsonl with a patched judge.md containing the new front matter keys; confirm REPORT.md renders the new sections.

---

### Tests to write or update

**File:** `tests/eval/test_judge.py` (add to existing)

- `test_normalize_scores_new_keys` — feed dict with `dimension_scores` and `gm_beat_empty_autofail`; assert both present in output
- `test_normalize_scores_clamps_dimension` — feed dimension score of 7; assert clamped to 5
- `test_normalize_scores_old_keys_unchanged` — feed only old keys; assert no `dimension_scores` key in output

### REPOMAP updates required
`docs/REPOMAP/eval.md` — note new `_DIMENSION_SCORE_KEYS` set, `gm_beat_empty_autofail` flag, updated `_normalize_scores` signature.

### Risks
1. `report.py` currently reads `pipeline_scores` keys by name in a hardcoded tuple. If a run's
   judge.md predates this change and has no `dimension_scores`, the table simply doesn't render
   — no crash. Backward-compatible.

---

## Implementation — Phase 3: Rubric Rewrite

### Context files to load
- `evals/rubrics/default.md` (full — already read)
- `ccya/eval/judge.py` — specifically `_normalize_scores` and `parse_judge_response` (already read)

### Overview
Replace the content of `evals/rubrics/default.md` with a rewritten rubric. The rewrite:
1. Adds anchored score definitions (1/5 and 5/5 described concretely for each criterion).
2. Adds `dimension_scores` YAML block (7 keys) in the output format alongside existing keys.
3. Adds `gm_beat_empty_autofail: true/false` to the YAML block.
4. Adds a new `cross_turn_consistency` narrative criterion.
5. Strengthens the `gm_beat` hidden-issue bullet with explicit empty-instruction wording.
6. Strengthens the pressure lifecycle section with explicit "location change is not resolution" wording.
7. Updates pipeline labels to use future-compatible names (adds note that `extract_progress` may
   be renamed `extract_storyteller` in a future run — judge should score under either name).
8. Makes all instruction language imperative, not permissive.

### Detailed steps

#### Step 3.1 — Write `evals/rubrics/default.md`

**File:** `evals/rubrics/default.md`

**What:** Full replacement. The complete new rubric text follows.

**Why:** Score anchors prevent score inflation. The new YAML keys enable granular regression
tracking. The `cross_turn_consistency` criterion catches cross-turn state bugs the existing
narrative criteria miss. Imperative language prevents the judge from applying soft scoring.

**Code Snippet**
```markdown
# ccya Eval Judge — Default Rubric v2

You are evaluating one run of an interactive narrative game. The game's engine
makes 5 LLM calls per turn, executed sequentially:

1. **rules** — classify intent, decide if a skill check is needed, choose scope (active_domains / skip_domains).
2. **narrate** — write the prose for this turn given the rules outcome.
3. **extract.scene** — extract scene-level changes (location, present_npcs, tags, summary).
4. **extract.state** — extract pc-level changes (inventory deltas, conditions).
5. **extract.progress** — extract longer-arc changes (quest progress, recent_events, compendium NPC bios, scene_pressure, gm_beat).

Note: `extract.progress` may appear as `extract.storyteller` in newer runs. Score it identically.

## Trace format

You will receive the trace as a single markdown document with two top-level sections:

### 1. Static Context (immutable across all turns — appears once at the top)

- **World Pack Style** — the game's `style.md` content
- **Seed State** — the initial game state before any turns (full JSON)
- **Engine Constants** — live thresholds (pressure escalation turns, momentum range, momentum delta per band)
- **System Prompts** — the 5 system prompts pulled from turn 1. They are identical every turn.

### 2. Per-Turn blocks

Each `# TURN N` block contains:
- **Input** — the player command
- **User Prompts** — the rendered user prompt for each of the 5 streams (some may say "(skipped)")
- **Engine Outputs** — Rules (parsed JSON + raw LLM output), Narration (full prose), Extract Scene/State/Progress (full JSON)
- **Applied Deltas** — what the engine actually applied
- **Rejected Deltas** — what was rejected
- **Context Telemetry** — token estimates per stream, trim status
- **State After Turn** — full game state JSON (diff vs previous on interior turns)

`# Deterministic Signals` at the end lists auto-checker failures and per-turn metrics.

***

## How to evaluate

The system prompts are the ground truth. The trace contains everything the engine sent and
received in full. Do not assume information is missing.

You must be harsh. Score inflation is a calibration failure. A functional but mediocre run
scores 3/5. A run with a single category-A mechanical failure (scope miss, dice contradiction,
wrong state mutation) scores no higher than 2/5 for that pipeline.

***

## Score anchors (apply to every criterion)

| Score | Meaning |
|---|---|
| 5 | Correct or excellent in every observable turn. No issues found. |
| 4 | One minor issue that did not affect game state or narrative outcome. |
| 3 | Two or three issues, or one issue that affected one turn's state. Functional overall. |
| 2 | Multiple issues, or one issue that affected multiple turns. Noticeably impaired. |
| 1 | Broken. The pipeline did not fulfill its primary function for most of the run. |

These anchors apply to ALL scored criteria — mechanical and narrative.

***

## Section 1: Mechanical Correctness (PRIMARY — weighted 2x)

Your most important job is to judge whether the engine's mechanics are functioning correctly.
A run with a compelling story but broken state tracking is a broken run.

### How to evaluate each pipeline

For each of the 5 pipelines, produce a **full trace** that shows the end-to-end flow:

1. **System prompt key instructions** — What did the system prompt tell the LLM to do?
2. **User prompt key inputs** — What context was provided? What was the LLM supposed to do with it?
3. **LLM output** — What did the LLM actually produce? Quote specific fields/values.
4. **State mutation** — What did the engine do with that output?

Then answer these questions:

- **What went well** — At least two paragraphs. Specific turns and fields.
- **What went poorly** — At least two paragraphs. Specific turns and fields.
- **Prompt analysis** — What was not needed (bloat, redundancy)? What was missing? Cite turns.
- **Issues** — Bulleted list. Each: description, turn numbers, failure mode (see taxonomy), remediation.

Failure mode taxonomy — use exactly one per issue:
- **bad prompt** — ambiguous, contradictory, missing constraints, or bloated instructions
- **failed to output key information** — LLM omitted a required field or used wrong values
- **failed to input key information** — user prompt omitted context the LLM needed
- **messy logic** — post-processing (delta application, reconciliation) is buggy
- **scope/domain mismatch** — active/skip domain decision caused downstream miss or over-production
- **schema drift** — LLM output doesn't match expected schema

### Scope and domain mapping

For each turn, check:
- Did rules correctly identify which domains could change?
- Did narration produce changes that extractors missed because the domain was skipped?
- Did extractors produce changes for correctly-skipped domains?
- When a stream was skipped, was narration truly free of changes in that domain?

**Scope failures are mechanical failures.** If narration says "you hand over the brass key"
but `inventory` was in `skip_domains`, that is a `scope/domain mismatch` failure.

### gm_beat enforcement

You must check every turn for gm_beat quality. For each turn where `gm_beat` was applied:

1. Is `instruction` non-empty? An empty or null `instruction` is an **automatic failure** for
   the `extract_progress` pipeline on that turn. Set `gm_beat_empty_autofail: true` in your
   front matter.
2. Is the instruction specific and story-grounded (references actual NPCs, locations, or
   plot elements from this run)? Generic instructions ("raise the stakes") score poorly.
3. Was the beat consumed by the narrator next turn? If `pending_gm_beat` persisted unchanged
   across two turns, that is a failure.

### Pressure lifecycle enforcement

For each scene pressure in the trace, you must verify:
- Escalation path: background → building → immediate. Skipping a stage is a failure.
- **A location change alone is not a valid reason to remove a pressure.** A pressure is only
  removed when the narration shows the underlying threat resolved (threat neutralized, escaped,
  defused). If a pressure is removed solely because the PC moved locations, that is a `messy
  logic` failure.
- Expiration: pressures with `max_turns` set must expire when that turn count is reached.
- New pressures seeded at appropriate story moments (not on every turn, not never).

### Hidden issues to look for

The following are known failure classes. This list is **not exhaustive** — search for issues
beyond it.

- `recent_events_add` with `turn: 0` instead of the current turn number
- `npc_update` used for NPCs not in `present_npcs` (should be `npc_add`)
- Tense conflicts between style pack and narrate prompt
- Quest objectives marked `done: true` on fail/setback/partial bands
- `pending_gm_beat` persisting beyond 1 turn
- `trim_messages` truncating narration from extractor user prompts
- Duplicate conditions for the same injury
- `inventory_remove` IDs not matching existing inventory IDs
- Momentum not updating per band deltas (crit_success +2, success +1, partial 0, setback −1, fail −1, crit_fail −2)
- Dice band not matching narration outcome
- `scene_tags` incorrect (missing "combat" when combat occurred, or added when not)
- Quest auto-complete not firing when all objectives are `done: true`
- NPC scene cap (8 named NPCs) exceeded without eviction
- `actions` field with fewer than 4 choices or choices not grounded in current narration
- `deescalate=true` but new `scene_pressure_add` entries emitted
- Condition guidance violated: negative conditions added on clean success/crit_success
- Compound actions: roll on a trivial sub-action instead of the gating action
- Anti-declare-outcome: player asserted success, difficulty was not hardened
- **gm_beat with empty `instruction` field** — automatic failure flag (see above)
- **Pressure removed on location change without narrative resolution** — messy logic failure

### Pipeline scoring criteria

Score each pipeline 1–5 using the anchors above.

**rules** — intent classification, skill/difficulty selection, scope/domain mapping, compound
action handling, anti-declare-outcome enforcement

**narrate** — dice outcome adherence (BINDING), GM beat consumption, de-escalation directives,
age-based directives, style adherence

**extract.scene** — NPC add/update/remove accuracy, location change fidelity, scene tag
correctness, actions quality, scene cap enforcement

**extract.state** — inventory delta accuracy, condition delta accuracy, hard cap adherence,
reconciliation correctness, ID normalization

**extract.progress** — quest update accuracy, recent events management, compendium NPC updates,
scene pressure lifecycle, GM beat generation (instruction quality and specificity)

### Compaction evaluation

When compaction is present in the trace:

1. **Bullet quality** — Do bullets preserve named NPCs, key items, quest outcomes, and
   irreversible choices? Do they cull atmospheric repetition and uneventful content?
2. **State sanitization** — Were real structural problems caught? Were false positives avoided?
3. **Narration awareness** — Does post-compaction narration reflect the compacted state?
4. **Deduplication** — Did NPC merges resolve identity confusion?

***

## Section 2: Narrative Quality (SECONDARY)

Score each narrative criterion 1–5 using the anchors above. Be a harsh critic. Most
well-functioning runs land at 3 or 4. A 5 means genuinely excellent. A 1 means absent or
broken.

### quest_arc_quality
Did quests form a compelling long-arc narrative? Did objectives feel like real goals with
meaningful stakes? Did completing a quest feel earned? Did failure create interesting new
problems? Did quest rewards fit the effort required? Did quests support the genre?

### rewards_and_consequences
Did the game give real rewards for success and real consequences for failure? Did failures
create interesting problems rather than dead-ends? Did the player feel the weight of their
choices? Were there meaningful trade-offs?

### narrative_compellingness
Was the story compelling enough that a player would want to keep playing? Did it have a
satisfying arc — rising tension, meaningful choices, a payoff? Did choices feel like they
mattered?

### genre_and_universe_fit
Did the story feel appropriate to the genre and universe? Was tone consistent — gritty,
grounded, morally gray? Did NPCs feel like real people? Did the setting feel tangible?

### npc_development
Do NPCs change meaningfully throughout the narrative? Do bios evolve based on interactions?
Do NPCs react to the player's actions? Do NPCs have consistent personalities?

### player_agency
Does the game respect player choice? Do failures create new options? Are there multiple valid
approaches? Are suggested actions contextually appropriate?

### pacing_and_pressure

Score this criterion once. Internally weigh two signals:

**pressure_mechanics (objective — weight 60%):**
- Did scene_pressure entries escalate background → building → immediate?
- Did pressures expire when `max_turns` was reached?
- Did narration reflect urgency changes?
- Were new pressures seeded at appropriate moments?

**narrative_pacing (subjective — weight 40%):**
- Are there breathing-room turns between high-tension beats?
- Does momentum visibly affect narration tone?
- Does the arc feel satisfying across the full run?

Your single `score` is the weighted composite. Call out pressure_mechanics failures explicitly.

### cross_turn_consistency
Did state persist correctly across turns? Check for:
- NPCs referenced in narration that disappeared from state without being removed
- Quest objectives re-opened after being completed
- Inventory items referenced in narration but absent from state
- Conditions applied and then silently dropped without narrative explanation
- Location referenced in narration that contradicts state.location
- Compendium NPC bios that contradict narration from the same or adjacent turns

Score 5 if state is fully consistent with narration across all turns. Score lower for each
observable inconsistency.

***

## Auto-checker integration

The trace's `# Deterministic Signals` section lists every assertion that failed. For every
failure, you must:

1. Explain **why** the assertion failed.
2. Provide a **remediation**. Use the failure mode taxonomy.

These are deterministic — do not re-derive whether they passed.

New assertions you may see (in addition to prior ones):
- `universal.gm_beat.instruction_nonempty` — gm_beat applied with empty/null instruction
- `universal.pressure_lifecycle.valid` — pressure re-added at same/lower severity, or removed when nonexistent
- `universal.quest_objective.done_on_success_only` — objective marked done on fail/setback band
- `universal.narrate.no_binding_on_no_roll` — BINDING block injected on a no-roll turn
- `universal.pending_gm_beat.instruction_nonempty` — pending beat in state has empty instruction

***

## Output format

Return a YAML front matter block followed by a structured markdown body.

```
---
mechanical_score: <int 1-5>
narrative_score: <int 1-5>
pipeline_scores:
  rules: <int 1-5>
  narrate: <int 1-5>
  extract_scene: <int 1-5>
  extract_state: <int 1-5>
  extract_progress: <int 1-5>
dimension_scores:
  narration_fidelity: <int 1-5>
  prose_quality: <int 1-5>
  rules_classification: <int 1-5>
  extraction_accuracy: <int 1-5>
  quest_pressure_tracking: <int 1-5>
  gm_beat_quality: <int 1-5>
  cross_turn_consistency: <int 1-5>
gm_beat_empty_autofail: <true | false>
---

# Mechanical Analysis

## Pipeline: rules

### Trace
<End-to-end trace of one or two representative turns.>

### Scope Analysis
<Track active_domains / skip_domains. Call out scope failures with turn numbers.>

### What Went Well
<At least two paragraphs. Specific turns and fields.>

### What Went Poorly
<At least two paragraphs. Specific turns and fields.>

### Prompt Analysis
<Bloat, redundancy, missing context. Cite turns.>

### Issues
- **<short description>** (turns: <list>) — Failure mode: <taxonomy value>. Remediation: <what should change>.

## Pipeline: narrate
<Same subsections.>

## Pipeline: extract_scene
<Same subsections.>

## Pipeline: extract_state
<Same subsections.>

## Pipeline: extract_progress
<Same subsections.>

# Narrative Analysis

## Criterion: quest_arc_quality
**Score:** <1-5>
<Two or more sentences. Cite turns.>

### Issues
- ...

## Criterion: rewards_and_consequences
**Score:** <1-5>

## Criterion: narrative_compellingness
**Score:** <1-5>

## Criterion: genre_and_universe_fit
**Score:** <1-5>

## Criterion: npc_development
**Score:** <1-5>

## Criterion: player_agency
**Score:** <1-5>

## Criterion: pacing_and_pressure
**Score:** <1-5>
<Internally weight pressure_mechanics (60%) + narrative_pacing (40%).>

## Criterion: cross_turn_consistency
**Score:** <1-5>
<List any observable state-narration inconsistencies with turn numbers.>

# Auto-Checker Failures

<For every failure in Deterministic Signals, explain WHY and propose a remediation.>

# Additional Observations

<Patterns or bugs not covered above.>

# Verdict

<2-4 sentences. Concrete, specific, actionable. Reference turn numbers.>

# Narrative Recap

<3-5 sentences summarizing the player's arc.>


**Validation:** After writing the file, run `python -m ccya.eval --scenario <any> --turns 1`
(or equivalent) and confirm the judge returns parseable YAML front matter with all new keys.
Confirm `_normalize_scores` accepts the new block without error.

---

### Tests to write or update

No new unit tests for the rubric file itself (it's a text prompt). The Phase 2 tests for
`_normalize_scores` cover the YAML key parsing. Manual validation via a judge call.

### REPOMAP updates required
`docs/REPOMAP/eval.md` — note `rubric_path` default value, document `dimension_scores` and
`gm_beat_empty_autofail` keys, update the "Output format" description.

### Risks
1. The judge model may not reliably emit the new `dimension_scores` block on first runs.
   The `_normalize_scores` code handles absent keys gracefully (no crash, no rendering).
   Score drift from the new anchors may make first post-upgrade runs look like regressions
   vs pre-upgrade runs — this is expected and acceptable.
2. `cross_turn_consistency` is a subjective criterion. The judge may score it inconsistently
   across runs. Consider flagging in `flag_at_top` config if this becomes noisy.
3. The `gm_beat_empty_autofail` bool requires the judge to set it accurately. The
   `universal.gm_beat.instruction_nonempty` assertion provides a deterministic backstop.

---

## Ambiguities requiring resolution before execution

None. All code paths verified against the actual source. Score keys and dict access patterns
confirmed against `judge.py`, `report.py`, and `universal_asserts.py`.

## TODO.md update

Add under **P2 — Eval / Observability**:
