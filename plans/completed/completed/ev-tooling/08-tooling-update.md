# EV Tooling Update — Convergence-Complete CLI

## Status: completed

## Purpose

Update the EV tooling (`ev.py`), its documentation, and the ev skill to reflect the convergence scoring redesign. Fix data shape issues identified in the tooling meta-analysis. Add commands for the new primitives (convergence score, CLIMAX, Curtain Call) and remove dead code (momentum-check reading a dead field, stale `.pyc` orphans).

## Scope

Four workstreams, executed in order:

| Phase | Workstream | Depends on |
|---|---|---|
| 0 | Cleanup — stale `.pyc` orphans, dead checker refs in docs | — |
| 1 | Data access layer fixes — nested field support, narrate shape, compat, check auto-detect | — |
| 2 | New commands — convergence, rolls, phase-transitions, curtain-call, warnings, prompt-sizes | Phase 1 (trace/search fixes) |
| 3 | Documentation — ev skill, README, CHECKERS.md | All prior phases |

## Files to Modify

### Phase 0 — Cleanup

```
ccya/ev/checkers/__pycache__/
  crisis_turn_counting.cpython-313.pyc   ← delete (stale rename orphan)
  momentum.cpython-313.pyc               ← delete (deleted checker)
  tension_delta.cpython-313.pyc           ← delete (deleted checker)
  tension_monotonicity.cpython-313.pyc    ← delete (deleted checker)
```

### Phase 1 — Data Access Layer Fixes

| File | Change |
|---|---|
| `ccya/ev/events.py` | `extract_field_from_event()`: add generic fallback path after hardcoded field lookups. Currently returns `None` for unknown fields (line 319). Fallback should do dot-notation traversal on the event dict using `ev.get(part)` chaining. This enables `trace pacing_context.convergence_score`, `trace pacing_context.climax_turn_count`, etc. |
| `ccya/ev/state_tools.py` | `cmd_search` / `parse_search_expression()`: add dot-notation support for nested field queries. `cmd_goals`: add fallback to read `arc_resolve.visible_goal` when `goal_update` is absent. |
| `ccya/ev/check.py` | `cmd_check`: auto-detect `events.jsonl` from `--save-dir` path, matching `play` behavior. |
| `ccya/ev/inspect.py` or event model | Narrate output: populate `narrate.output` from `narrate_prompt.output` at event-write time, or update all consumers to read from `narrate_prompt.output`. |
| `ccya/ev/compat.py` | `cmd_compat`: recognize `extraction.changes` as a valid extraction format in addition to `extraction_context`. |
| `ccya/engine/turn.py` | Store 5 convergence component booleans in `pacing_context` alongside `convergence_score`. Fix `event["extract"]["retries"]` from hardcoded 0 to actual count. Add `reconcile_warnings` to event dict. |

### Phase 1f — Event schema: convergence components + warning signals

Three write-site changes in `turn.py`:

**Convergence 5 components:** After `_pc.convergence_score = convergence_score` (line 793), populate the component booleans on the PacingContext:

```python
# PacingContext class (line 98): add field
convergence_components: dict = field(default_factory=dict)

# After line 793 in the turn pipeline:
components = {}
# Component 1-2: thread signals
components["thread_weight"] = 1 if thread_urgency_count >= 1 else 0
components["urgency_depth"] = 1 if thread_urgency_count >= 2 else 0
# Component 3: scene age
scene_age = ctx._ages.get("scene_age", 0)
components["scene_age"] = 1 if scene_age >= config.scene_pressure_threshold else 0
# Component 4: beat streak
recent_beats = state.get("meta", {}).get("recent_beats", [])
if recent_beats:
    pressure_types = {"pressure", "complication", "escalation", "setback"}
    n = len(recent_beats)
    window = recent_beats[: min(n, 5)]
    pressure_count = sum(1 for b in window if b.get("type") in pressure_types)
    threshold = ceil(n * 0.6) if n < 5 else 3
    components["beat_streak"] = 1 if pressure_count >= threshold else 0
else:
    components["beat_streak"] = 0
# Component 5: dice weight
components["dice_weight"] = 1 if (
    ctx.outcome is not None
    and ctx.outcome.rolled
    and ctx.outcome.band in ("crit_fail", "fail")
    and thread_urgency_count >= 1
) else 0

_pc.convergence_components = components
```

At event-write time (line 1338 area), serialize alongside convergence_score:

```python
"convergence_score": _pc.convergence_score if _pc else 0,
"convergence_components": _pc.convergence_components if _pc else {},
```

The `convergence` command then reads `pacing_context.convergence_components` directly — no recomputation. This duplicates the component logic from `compute_convergence_score()` but keeps the function's return type unchanged and avoids coupling the pacing module to the event schema.

**Fix `extract.retries`** — change hardcoded `0` to actual count from stream retry_errors:

```python
# turn.py:1076 — change from:
"retries": 0,
# to:
"retries": sum(
    len((stream or {}).get("retry_errors", []))
    for stream in [scene_event, state_event, storytell_event]
),
```

**Add `reconcile_warnings`** — `reconcile_delta()` returns a warnings list that's currently logged and discarded. Store it in the event:

```python
# turn.py ~1104 — after reconcile_delta call:
delta, reconcile_warnings = reconcile_delta(state, delta)
# add:
event["reconcile_warnings"] = reconcile_warnings
```

### Phase 2 — New Commands

| File | Change |
|---|---|
| `ccya/ev/__init__.py` | Add `rolls`, `convergence`, `phase-transitions`, `curtain-call`, `warnings`, `prompt-sizes` to help text and match/case dispatch. Remove `momentum-check`. |
| `ccya/ev/state_tools.py` | `cmd_momentum_check` → rename to `cmd_rolls`. Update docstring and help text. New: `cmd_convergence` — reads `pacing_context.convergence_components`, prints table with threshold highlighting. New: `cmd_phase_transitions` — walks events, detects phase changes, prints transition log with triggers (convergence_score, climax_turn_count, scene_phase, outcome_hint). |
| `ccya/ev/state_tools.py` (new funcs) | New: `cmd_curtain_call` — scans CLIMAX turns for `thread_resolve` in storytell output and `curtain_call` field in user prompt context; flags violations. |
| `ccya/ev/` new module `warnings.py` | New: `cmd_warnings` — scans events for `extract.retries`, `extraction.*.retry_errors`, `event["rejected"]`, `event["reconcile_warnings"]`. Seeds, dedup, and other non-event warnings listed as gaps. |
| `ccya/ev/` new module `prompt_sizes.py` | New: `cmd_prompt_sizes` — reads `tokens_in`/`tokens_out` per pipeline stage across turns, prints table + growth trend. |

### Phase 3 — Documentation

| File | Change |
|---|---|
| `.opencode/skills/ev/SKILL.md` | Remove dead `docs/architecture/ev-tooling.md` reference. Add new commands to capabilities list. Replace "momentum" reference with "convergence". Make lighter (signpost-only). |
| `scripts/debug/README.md` | Add `rolls`, `convergence`, `phase-transitions`, `curtain-call`, `warnings`, `prompt-sizes` to command reference. Remove `momentum-check`. Update any stale convergence references. |
| `docs/ev/CHECKERS.md` | Remove `tension_delta` entry (deleted checker). Remove `tension_monotonicity` entry (deleted checker). Rename `crisis_turn_counting` heading + content to `climax_turn_counting`. Verify all 27 remaining checkers match source. |
| `docs/design/ev/` | Already updated in prior session. No further changes needed. |
| `docs/architecture/ev-tooling.md` | Does not exist. Either create or remove the reference from the skill. **(Decision needed: create minimal doc or just remove ref from skill)** |

## Phase Details

### Phase 0 — Cleanup

Trivial. Delete 4 stale `.pyc` files. Update CHECKERS.md entries for the 3 removed/renamed checkers. No code changes to checkers themselves (they were already removed from `.py` source).

### Phase 1 — Data Access Layer Fixes

#### 1a. Nested field support for `trace` and `search`

`extract_field_from_event()` in `ccya/ev/events.py` has a hardcoded lookup table (inventory, conditions, npcs, location, scene.tagline) and returns `None` for everything else (line 319). `cmd_trace` in `state_tools.py` calls it and bails with "Field not tracked per-turn" when it returns `None`.

Fix: add a generic fallback path after the hardcoded checks:

```python
def extract_field_from_event(ev: dict, field: str):
    # ... existing hardcoded lookups for inventory, conditions, npcs, location, scene.tagline ...

    # Generic fallback: dot-notation traversal on event dict
    parts = field.split(".")
    current = ev
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current
```

This makes `ev.py trace pacing_context.convergence_score`, `ev.py trace pacing_context.climax_turn_count`, and `ev.py trace pacing_context.scene_phase` all work.

**Important:** The generic fallback runs only when the field doesn't match a hardcoded key — existing lookups (inventory, conditions, etc.) are unaffected.

`_trace_display_name()` and `format_trace_value()` need no changes — they already work on the resolved value.

`parse_search_expression()` in `state_tools.py` currently splits on `:` and uses the left side as a flat key. Change to accept dotted keys and pass them through `extract_field_from_event()` for matching — same dot-notation traversal.

#### 1b. `cmd_goals` — visible_goal fallback

Current: reads `extraction.storytell.output.goal_update`. Add: if absent, read `extraction.storytell.output.arc_resolve.visible_goal`.

```python
storytell = (ev.get("extraction") or {}).get("storytell") or {}
output = storytell.get("output") or {}
goal = output.get("goal_update")  # existing
if not goal:
    arc_resolve = output.get("arc_resolve") or {}
    goal = arc_resolve.get("visible_goal")
```

#### 1c. `check --save-dir` auto-detect

Current: events path resolution in `__init__.py:87-95` checks if the last positional arg starts with `saves/` — but if the user passes `--save-dir saves/ev/XXX` without a positional events path, it falls back to `saves/default/events.jsonl`.

Fix: before the positional arg check, if `--save-dir` is in flags and no explicit events path is given, derive events path as `Path(flags["save-dir"]) / "events.jsonl"`:

```python
# Before line 87 in __init__.py:
if "save-dir" in flags and not (len(args) > 1 and args[-1].startswith("saves/")):
    turn_file = Path(flags["save-dir"]) / "events.jsonl"
    # Don't strip args — save-dir came from flags, not positional
```

This matches the `play` command's behavior where `--save-dir` is the primary way to specify a session.

#### 1d. Narrate output shape

Current: `event["narrate"]` is `narr_metrics` — a timing-only dict (`first_token_ms`, `total_ms`, `tokens_in`, `tokens_out`). The actual narrate prose lives in `event["narrate_prompt"]["output"]`.  

Fix: add `"output": narrative` to the `narr_metrics` dict at `turn.py:943-948`, so `event["narrate"]["output"]` carries the prose alongside the existing timing fields. One write-site change:

```python
narr_metrics = {
    "first_token_ms": round(first_ms, 1),
    "total_ms": round(narr_ms, 1),
    "tokens_in": int(narr_stream_stats.get("prompt_eval_count", 0)),
    "tokens_out": int(narr_stream_stats.get("eval_count", 0)),
    "output": narrative,  # NEW
}
```

Existing consumers reading `narrate.first_token_ms`, `narrate.total_ms`, etc. are unaffected. New consumers can read `narrate.output`. Historical events before this fix have `narrate.output` absent — documented in README.

#### 1e. Compat checker

Current: `cmd_compat` checks for `extraction_context` field. Many saves use `extraction.changes` instead.

Fix: also check for `extraction.changes` as a non-empty dict. Mark saves using it as `"changes format"` rather than `"neither"`.

### Phase 2 — New Commands

#### 2a. `rolls` (rename of `momentum-check`)

- Rename the match/case key in `__init__.py` from `"momentum-check"` to `"rolls"`
- Rename function in `state_tools.py` from `cmd_momentum_check` to `cmd_rolls`
- Update docstring: `"""Show roll bands + raw/final totals per turn."""`
- Code stays the same (already removed tension_delta, already shows rolls only)
- The `--pacing` and `--dice` flags on `mechanics` already cover convergence — no need to add it here

#### 2b. `convergence`

New command. Reads `pacing_context.convergence_components` (5 booleans, stored at write time in Phase 1f) and `pacing_context.convergence_score` from each turn event. Renders a table:

```
Turn | Phase    | Thread | Depth | Age | Beat | Dice | Score | ≥3?
─────┼──────────┼────────┼───────┼─────┼──────┼──────┼───────┼─────
  3  | RISING   |   1    |  0    |  1  |  0   |  1   |   3   | YES →
  4  | CLIMAX   |   1    |  1    |  1  |  1   |  0   |   4   | YES
  5  | CLIMAX   |   1    |  1    |  1  |  1   |  1   |   5   | YES
```

Each component column is 0 or 1. "→" on CLIMAX entry turn. Score column highlighted red when <3 in RISING, green when ≥3 at entry.

Components read directly from stored fields — no recomputation. The `convergence_components` dict is written by `turn.py` at the same point `convergence_score` is written.

#### 2c. `phase-transitions`

Walk events in order. Detect when `pacing_context.scene_phase` changes. For each transition, print:

```
Turn 3: RISING → CLIMAX   (convergence_score=4, climax_turn_count=1)
Turn 7: CLIMAX → RESOLUTION (climax_turn_count=4, outcome_hint=transition)
Turn 8: RESOLUTION → BREATHER (breather_turn_count=1, no location change)
```

Special cases:
- BREATHER → RISING (urgency > 0 or breather_max_turns)
- RESOLUTION → SETUP (location change)
- CLIMAX entry always sets `climax_turn_count=1`

#### 2d. `curtain-call`

For each turn where `pacing_context.scene_phase == "CLIMAX"`:
1. Check if `extraction.storytell.output.thread_resolve` exists and is non-empty
2. Check if `climax_turn_count == 1` (turn 1 threshold: "active")
3. Check if `climax_turn_count >= climax_turn_limit - 1` (second-to-last: "forced")
4. Report: pass/fail per turn with details

CLIMAX turn counting already verified by `climax_turn_counting` checker — this command focuses on the LLM's compliance, not the phase machine.

#### 2e. `warnings`

Scan events for warning signals using existing event fields:

| Warning type | Event source | Availability |
|---|---|---|
| LLM extraction retries | `event["extract"]["retries"]` (now real, fixed in Phase 1f) | Available |
| Per-stream retry errors | `event["extraction"][stream]["retry_errors"]` | Available today |
| Inventory validation rejections | `event["rejected"]` | Available today |
| Reconcile warnings | `event["reconcile_warnings"]` (added in Phase 1f) | Available |
| generate_seed soft-check | Not stored in any event field (logged only in `seed.py:421-424`) | **Gap** — requires schema change in `seed.py` |
| Thread update dedup | Not stored in any event field (logged only in `turn.py:161-168`) | **Gap** — requires schema change |
| Compendium NPC dedup | Not stored in any event field (modified delta silently in `extraction.py:720-743`) | **Gap** — requires schema change |

The `warnings` command reads the 4 available sources and prints a summary table per turn:

```
Turn | Extract.Retries | Retry Errors    | Rejected         | Reconcile Warnings
─────┼────────────────┼─────────────────┼──────────────────┼────────────────────
  1  |       0        | scene: 1, state: 0, storytell: 0 | —  | —
  5  |       2        | scene: 2, state: 0, storytell: 0 | overdraw: knives x1 | —
```

A separate **Gaps** section at the bottom lists warning types not capturable from events, with the file/line where they're produced.

#### 2f. `prompt-sizes`

Reads `tokens_in` and `tokens_out` from each pipeline stage's prompt event:

```
Turn | Ruling_in | Ruling_out | Narr_in | Narr_out | Scene_in | ... | Total
─────┼───────────┼────────────┼─────────┼──────────┼──────────┼─────┼──────
  1  |   1200    |    150     |  4500   |   800    |  3800    | ... | 12000
  5  |   1300    |    180     |  4800   |   920    |  4200    | ... | 13500
 10  |   1400    |    200     |  5200   |   1100   |  4800    | ... | 14800
```

Growth trend line at the bottom (linear regression slope) for each stage.

### Phase 3 — Documentation

#### 3a. ev skill

Replace current content with minimal signpost:

```markdown
---
name: ev
description: ev.py — CLI for turn data, checkers, play, and eval
---

Read these before using:
- `scripts/debug/README.md` — full command reference
- `docs/ev/CHECKERS.md` — checker library

Invocation:
```
.venv/bin/python scripts/debug/ev.py <command> [args...]
```

Key modules:
- `ccya/ev/` — command implementations
- `ccya/ev/checkers/` — checker plugins (27 registered)
```

Remove: `docs/architecture/ev-tooling.md` reference (doesn't exist), momentum reference, verbose per-file table, save path convention section (already in README).

#### 3b. `scripts/debug/README.md`

Add new commands to "Command reference" section under appropriate subsections:
- **Thread, beat, and phase analysis:** add `convergence`, `phase-transitions`, `curtain-call`
- **What happened — turn data inspection:** replace `momentum-check` with `rolls`
- **Validate — checker & eval infrastructure:** no change

Add a `### Prompt size analysis` subsection for `prompt-sizes`.

Add a `### Warnings` subsection for `warnings`.

#### 3c. `docs/ev/CHECKERS.md`

- Remove `### tension_delta` entry entirely (5 bullet fields)
- Remove `### tension_monotonicity` entry entirely
- Rename `### crisis_turn_counting` to `### climax_turn_counting`
- Update the crisis→climax entry's type, fields, what it checks, CLI example, and caveats to use CLIMAX naming
- Verify all 27 remaining checker IDs match `ccya/ev/checkers/__init__.py` line 124

## Risk Table

| Risk | Likelihood | Mitigation |
|---|---|---|
| Nested field trace breaks existing flat-field queries | Low | Add dot-notation check — if no dots, use original `ev.get()` path |
| Convergence components disagree with engine's live computation | Low | Components written at same point as convergence_score — same inputs, same logic |
| `narrate.output` fix only applies to new events | Low | Document in README: "historical events before this fix have empty narrate.output; use narrate_prompt.output instead" |
| Stale `.pyc` files resurrect on import | Low | Delete manually, verify with `find . -name '*.pyc' -not -path './.venv/*'` |
| `reconcile_warnings` absent from historical events | Low | `warnings` command handles missing field gracefully (shows "—") |

## Resolved Decisions

All decisions from design review resolved as follows:

1. **`docs/architecture/ev-tooling.md`** — remove the reference from the skill. The README is the single source of truth. No doc created.
2. **Convergence components** — store 5 booleans in `pacing_context.convergence_components` at write time in `turn.py` (Phase 1f).
3. **Warnings** — use current primitives: fix `extract.retries` hardcoded 0, add `reconcile_warnings` to event. `warnings` command reads these + `retry_errors` + `rejected`. Non-capturable warnings documented as gaps.

## Done When

- [ ] Phase 0: stale `.pyc` files deleted; CHECKERS.md no longer lists `tension_delta`, `tension_monotonicity`, `crisis_turn_counting`
- [ ] Phase 1a: `ev.py trace pacing_context.convergence_score` works; `ev.py trace pacing_context.climax_turn_count` works; `ev.py trace pacing_context.scene_phase` works
- [ ] Phase 1a: `ev.py search pacing_context.scene_phase:CLIMAX` works
- [ ] Phase 1b: `ev.py goals` shows goals from `arc_resolve.visible_goal` when `goal_update` absent
- [ ] Phase 1c: `ev.py check --all --save-dir saves/ev/XXX` works without explicit events path
- [ ] Phase 1d: New events have `narrate.output` populated; `ev.py turn N` shows narrate prose from `narrate.output`
- [ ] Phase 1e: `ev.py compat` recognizes `changes` format
- [ ] Phase 2a: `ev.py rolls` works; `ev.py momentum-check` returns error
- [ ] Phase 2b: `ev.py convergence` shows 5-component table with threshold highlighting
- [ ] Phase 2c: `ev.py phase-transitions` shows transition log with triggers
- [ ] Phase 2d: `ev.py curtain-call` verifies Curtain Call compliance
- [ ] Phase 2e: `ev.py warnings` shows extract retries and documented gaps
- [ ] Phase 2f: `ev.py prompt-sizes` shows token growth table
- [ ] Phase 3a: ev skill is minimal signpost with no dead refs
- [ ] Phase 3b: `scripts/debug/README.md` covers all new commands
- [ ] Phase 3c: `docs/ev/CHECKERS.md` has 27 checkers, no dead entries
