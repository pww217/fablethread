# Ev Tooling Improvements

## Purpose

Fix critical bugs in ev checkers, add compact output modes, create new diagnostic commands, and update documentation to make future game sessions faster and more accurate.

## Problem Statement

The ev.py tooling requires significant manual effort to analyze game sessions. Commands are verbose, critical fields are missing from output, some checkers fail due to bugs, and documentation doesn't reflect actual event shapes. This makes analyzing 27-turn sessions painful and error-prone, requiring manual event parsing, template reading, and cross-referencing across multiple commands.

## Constraints

- Must use `.venv/bin/python scripts/debug/ev.py` for all testing
- No breaking changes to existing command interfaces
- All new commands must follow existing patterns in `ccya/ev/`
- Documentation must be updated alongside code changes
- Python 3.13+ required

## Non-goals

- Adding LLM-based checkers (requires API access, out of scope)
- Changing the engine's event emission format
- Adding new game packs or scenarios
- Modifying the core engine pipeline

## Firm decisions

1. Add `--compact` flag to `ev.py deltas` — show only thread/inventory/condition/gm_beat changes in summary format
2. Add `ev.py threads <save-dir>` command — show thread lifecycle across all turns in compact table
3. Add `ev.py beats <save-dir>` command — show turn-by-turn beat type + surface_as + beat_locked status
4. Add `ev.py momentum-check <save-dir>` command — show momentum + band + expected delta in one table
5. Add `ev.py goals <save-dir>` command — show goal changes over time
6. Add `ev.py effective-age <save-dir>` command — show effective_scene_age over time
7. Add `ev.py beat-ttl <save-dir>` command — show beat TTL expiration over time
8. Fix `sanitizer_lifecycle` checker — remove `threads_removed` from `requires_fields`
9. Add `beat_locked`, `consecutive_pressure`, `momentum_floor` to `ev.py mechanics --pacing` output
10. Save `narrate` extraction to events for verification

## Risks, Ambiguities, and Blockers

- **Ambiguity:** What format should `--compact` use? Table vs. key-value? Decision: use table format matching existing `ev.py mechanics --dice` style
- **Risk:** Adding `narrate` extraction to events increases file size. Mitigation: only save if extraction has meaningful content (not empty)
- **Risk:** New commands may conflict with existing `ev.py trace` command. Mitigation: new commands are save-dir based, `trace` is turn-based
- **Blocker:** None identified

## Status

`completed` — All 3 phases complete, plus CLI fix for save-dir handling

## Phase 1 Completed

- Fixed `sanitizer_lifecycle` checker: removed `threads_removed` from requires_fields and logic (engine never emits this field)
- Fixed `cmd_check` in `ccya/ev/check.py`: passes all events (not just turn events) to `run_checkers`, enabling sanitizer checker to find its events
- Rewrote `sanitizer_lifecycle` checker to use state snapshots from turn events instead of END state (fixes false positives for resolved threads)
- Added `consecutive_pressure` to `_show_pacing()` output in `ccya/ev/deltas.py`
- Fixed `_strip_flags` in `ccya/ev/__init__.py`: boolean flags (`--pacing`, `--dice`, etc.) no longer consume next positional arg as their value

## Phase 2 Completed

- Added `cmd_threads()` — shows thread lifecycle across all turns in compact table
- Added `cmd_beats()` — shows turn-by-turn beat type + surface_as + beat_locked status
- Added `cmd_momentum_check()` — shows momentum + band + expected delta in one table
- Added `cmd_goals()` — shows goal changes over time from sanitizer events
- Added `cmd_effective_age()` — shows effective_scene_age over time (currently no data in events)
- Added `cmd_beat_ttl()` — shows beat TTL expiration over time
- Added `--compact` flag to `deltas` command — shows only thread/inventory/condition/gm_beat changes in summary format
- Added routing for all new commands in `ccya/ev/__init__.py`
- Fixed `_strip_flags` to include `compact` in `_BOOL_FLAGS`

## Phase 3 Completed

- Updated `scripts/debug/README.md` with new command documentation
- Updated `docs/ev/RUBRIC.md` with narrate extraction note and sanitizer checker limitation
- Updated `docs/repomap.md` with new command signatures
- Updated `docs/architecture/persist.md` with event field notes

## Bug Fix: CLI save-dir handling

- Fixed `ccya/ev/__init__.py` line 91-93: when last arg starts with "saves/" and is a directory, load events from `events.jsonl` in that directory instead of failing with IsADirectoryError

## Phases

3 phases covering: (1) critical bug fixes, (2) new diagnostic commands, (3) documentation updates

---

## Implementation — Phase 1: Critical Bug Fixes

### Context files to load
- `ccya/ev/checkers/sanitizer.py` — sanitizer_lifecycle checker
- `ccya/ev/deltas.py` — deltas and mechanics commands
- `ccya/engine/thread_sanitizer.py` — engine's sanitizer event emission

### Detailed steps

#### Step 1.1 — Fix sanitizer_lifecycle checker requires_fields

**File:** `ccya/ev/checkers/sanitizer.py`

**What:** Remove `threads_removed` from `requires_fields` list at line 13-14. The engine never emits this field, causing the checker to fail on all games.

**Why:** The checker requires a field that doesn't exist in any game's events, making it unusable.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py check 27 sanitizer_lifecycle saves/cordyceps-year-twenty-2026-06-11/events.jsonl
# Should pass instead of failing with "required field 'threads_removed' not found"
```

#### Step 1.2 — Add beat_locked, consecutive_pressure, momentum_floor to mechanics --pacing output

**File:** `ccya/ev/deltas.py`

**What:** In `_show_pacing()` function (line 261-297), add output for `beat_locked`, `consecutive_pressure`, and `momentum_floor` fields from `pacing_context` and `state_snapshot`.

**Why:** These fields are critical for momentum/beat analysis but require reading events directly.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py mechanics 13 --pacing saves/cordyceps-year-twenty-2026-06-11/events.jsonl
# Should show beat_locked, consecutive_pressure, momentum_floor in output
```

#### Step 1.3 — Save narrate extraction to events

**File:** `ccya/engine/turn.py`

**What:** In the event recording logic, save `narrate` extraction to events alongside `scene`, `state`, `storytell`. Check if narrate extraction has meaningful content before saving.

**Why:** Currently events only contain `['scene', 'state', 'storytell']` in extraction, making it impossible to verify if `pacing_context` is rendered in narrate prompts without reading templates directly.

**Validation:**
```bash
.venv/bin/python3 -c "
import json
with open('saves/cordyceps-year-twenty-2026-06-11/events.jsonl') as f:
    for line in f:
        event = json.loads(line)
        if event.get('turn') == 1 and event.get('kind') is None:
            print('extraction keys:', list(event.get('extraction', {}).keys()))
            break
"
# Should include 'narrate' in extraction keys
```

### Tests to write or update

- Run `ev.py check 27 sanitizer_lifecycle saves/cordyceps-year-twenty-2026-06-11/events.jsonl` — should pass
- Run `ev.py mechanics 13 --pacing saves/cordyceps-year-twenty-2026-06-11/events.jsonl` — should show new fields
- Verify narrate extraction is saved to events for a new game turn

---

## Implementation — Phase 2: New Diagnostic Commands

### Context files to load
- `ccya/ev/__init__.py` — CLI entry point, command routing
- `ccya/ev/state_tools.py` — existing state tools, trace/diff commands
- `ccya/ev/events.py` — event loading, field extraction helpers
- `ccya/ev/deltas.py` — existing deltas/mechanics commands for reference

### Detailed steps

#### Step 2.1 — Add compact mode to deltas command

**File:** `ccya/ev/deltas.py`

**What:** Add `--compact` flag to `cmd_deltas()` function. When enabled, show only thread/inventory/condition/gm_beat changes in a compact table format instead of full JSON dumps.

**Why:** Full JSON dumps make scanning 27 turns painful. Compact mode saves significant time.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py deltas 15 --compact saves/cordyceps-year-twenty-2026-06-11/events.jsonl
# Should show compact table with thread/inventory/condition/gm_beat changes
```

#### Step 2.2 — Add threads command

**File:** `ccya/ev/state_tools.py` (add new function), `ccya/ev/__init__.py` (add routing)

**What:** Add `cmd_threads()` function that shows thread lifecycle across all turns in a compact table. Show thread ID, status (active/latent/resolved), urgency, and progress at each turn.

**Why:** `ev.py deltas` is the only way to find thread mutations, but requires scanning 27 verbose outputs manually.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py threads saves/cordyceps-year-twenty-2026-06-11
# Should show compact table of thread lifecycle across all turns
```

#### Step 2.3 — Add beats command

**File:** `ccya/ev/state_tools.py` (add new function), `ccya/ev/__init__.py` (add routing)

**What:** Add `cmd_beats()` function that shows turn-by-turn beat type + surface_as + beat_locked status in a compact table.

**Why:** `ev.py deltas` shows `storytell.gm_beat` in stderr, not structured output. Dedicated command saves time.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py beats saves/cordyceps-year-twenty-2026-06-11
# Should show compact table of beat emissions across all turns
```

#### Step 2.4 — Add momentum-check command

**File:** `ccya/ev/state_tools.py` (add new function), `ccya/ev/__init__.py` (add routing)

**What:** Add `cmd_momentum_check()` function that shows momentum + band + expected delta in one table. Cross-reference momentum trajectory with roll bands to verify delta correctness.

**Why:** `ev.py trace pc.momentum` requires manual cross-referencing with band data from `--dice` to verify delta correctness.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py momentum-check saves/cordyceps-year-twenty-2026-06-11
# Should show compact table with momentum, band, expected delta, actual delta, match status
```

#### Step 2.5 — Add goals command

**File:** `ccya/ev/state_tools.py` (add new function), `ccya/ev/__init__.py` (add routing)

**What:** Add `cmd_goals()` function that shows goal changes over time by scanning sanitizer events for `goal_update` or `arc_resolve`.

**Why:** Need to grep events manually for `goal_update` or `arc_resolve`. Dedicated command saves time.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py goals saves/cordyceps-year-twenty-2026-06-11
# Should show compact table of goal changes across all turns
```

#### Step 2.6 — Add effective-age command

**File:** `ccya/ev/state_tools.py` (add new function), `ccya/ev/__init__.py` (add routing)

**What:** Add `cmd_effective_age()` function that shows `effective_scene_age` over time for Scene Imperative verification.

**Why:** No command shows `effective_scene_age` over time, which is needed to verify Scene Imperative firing at the right moment.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py effective-age saves/cordyceps-year-twenty-2026-06-11
# Should show compact table of effective_scene_age across all turns
```

#### Step 2.7 — Add beat-ttl command

**File:** `ccya/ev/state_tools.py` (add new function), `ccya/ev/__init__.py` (add routing)

**What:** Add `cmd_beat_ttl()` function that shows beat TTL expiration over time by tracking `beat_expires_turn` values.

**Why:** No command shows `beat_expires_turn` over time, making it impossible to verify TTL expiration without reading events directly.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py beat-ttl saves/cordyceps-year-twenty-2026-06-11
# Should show compact table of beat TTL expiration across all turns
```

### Tests to write or update

- Run each new command against cordyceps save directory — should produce compact, readable output
- Verify commands work with other save directories (no hardcoded paths)
- Test edge cases: empty events, no sanitizer events, no beat emissions

---

## Implementation — Phase 3: Documentation Updates

### Context files to load
- `docs/ev/RUBRIC.md` — eval rubric
- `scripts/debug/README.md` — ev.py command reference
- `docs/repomap.md` — module boundaries, public APIs
- `docs/architecture/OVERVIEW.md` — pipeline flow, data shapes

### Detailed steps

#### Step 3.1 — Update RUBRIC.md with narrate extraction note

**File:** `docs/ev/RUBRIC.md`

**What:** Add note to Phase 4 (Pacing Directives) that `narrate` extraction may not be saved to events, requiring template reading for verification. Add note about condition cap verification step. Add note about NPC departure verification.

**Why:** Rubric should reflect actual event shapes and verification limitations.

**Validation:**
```bash
grep -n "narrate extraction" docs/ev/RUBRIC.md
# Should find note about narrate extraction not being saved to events
```

#### Step 3.2 — Update RUBRIC.md with sanitizer checker limitation

**File:** `docs/ev/RUBRIC.md`

**What:** Add note to Phase 8 (Sanitizer Lifecycle) that `sanitizer_lifecycle` checker requires `threads_removed` which doesn't exist in any game's events (fixed in Phase 1).

**Why:** Rubric should document known checker limitations and fixes.

**Validation:**
```bash
grep -n "sanitizer" docs/ev/RUBRIC.md
# Should find note about threads_removed limitation
```

#### Step 3.3 — Update README.md with new commands

**File:** `scripts/debug/README.md`

**What:** Add documentation for all new commands: `threads`, `beats`, `momentum-check`, `goals`, `effective-age`, `beat-ttl`. Add `--compact` flag documentation for `deltas` command.

**Why:** README is the primary command reference, must document all available commands.

**Validation:**
```bash
grep -n "ev.py threads\|ev.py beats\|ev.py momentum-check" scripts/debug/README.md
# Should find documentation for new commands
```

#### Step 3.4 — Update repomap.md with new module boundaries

**File:** `docs/repomap.md`

**What:** Add new commands to module boundaries section. Update public APIs for `ccya/ev/state_tools.py` and `ccya/ev/deltas.py`.

**Why:** Repomap documents module boundaries and public APIs, must reflect new commands.

**Validation:**
```bash
grep -n "cmd_threads\|cmd_beats\|cmd_momentum_check" docs/repomap.md
# Should find new command signatures in module boundaries
```

#### Step 3.5 — Update OVERVIEW.md with event shape changes

**File:** `docs/architecture/OVERVIEW.md`

**What:** Add note about `narrate` extraction being saved to events. Update data shapes section to reflect new event fields.

**Why:** Architecture docs must reflect actual event shapes and pipeline mechanics.

**Validation:**
```bash
grep -n "narrate extraction" docs/architecture/OVERVIEW.md
# Should find note about narrate extraction in events
```

### Tests to write or update

- Verify all documentation updates are accurate and complete
- Run `grep` commands above to confirm documentation exists
- Test that new commands are discoverable from README

---

## Done when

- All 3 phases complete
- All checkers pass on cordyceps save directory
- All new commands produce compact, readable output
- All documentation updated
- No breaking changes to existing commands
- Python 3.13+ compatibility maintained
