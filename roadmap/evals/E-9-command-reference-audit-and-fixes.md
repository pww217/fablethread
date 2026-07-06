---
title: "COMMANDS.md audit and fixes"
status: done
urgency: 2
size: medium
created: 2026-07-05
ticket_id: E-9
labels:
  - eval
  - docs
---

## Context

`docs/ev/COMMANDS.md` is the canonical command reference for `ev.py`. It was audited against `ccya/ev/__init__.py`, `ccya/ev/state_tools.py`, `ccya/ev/audit.py`, `ccya/ev/warnings.py`, and 19 architecture docs.

## Findings

### Outdated / Vacuous Commands

| Command | Issue | Fix |
|---------|-------|-----|
| `beat-ttl` | Reads `beat_expires_turn` which was **removed** — beats are single-turn commitments with no TTL. Command produces vacuous output. | Remove from COMMANDS.md, or note as deprecated/vacuous |
| `effective-age` | Reads `extraction.scene.output.effective_scene_age` which doesn't exist in `SceneExtractResult` (only `compendium_npc_update` + `candidate_npcs`). Command produces vacuous output. | Remove from COMMANDS.md, or note as deprecated/vacuous |
| `storyteller-audit` | Description says "Checks record output" but uses "storytell" language. Code actually reads `extraction.record.output` correctly, but description is inconsistent. | Update description to "Record" terminology |
| `beats` | Code comment references "storytell extraction" (outdated). `recent_beats` is never persisted in `state.meta` — it's a local `turn.py` variable, so that display section never works. | Update comment, note `recent_beats` display doesn't work |

### Missing Commands

| Command | Where | What it does |
|---------|-------|-------------|
| `personas` | `__init__.py:296` | Shows user persona registry from `PERSONA_REGISTRY_FILE` |

### Missing Flags

| Command | Flag | What it does |
|---------|------|-------------|
| `convergence` | `--by-scene` | Groups convergence output by scene |
| `phase-transitions` | `--by-scene` | Groups transitions by scene |
| `curtain-call` | `--by-scene` | Groups curtain call data by scene |
| `trace` | `--show-unchanged` | Shows turns where value didn't change |

### Incomplete Documentation

| Command | What's missing | What's valid |
|---------|---------------|--------------|
| `state --format` | Listed as `compact\|pc\|inventory\|...` | `full, compact, pc, inventory, location, scene, arc, npcs, compidx` |
| `diff --section` | Listed as `npcs\|...` | `npcs, inventory, conditions, location, tags, applied` |
| `warnings` signals | Listed as `extract.retries, retry_errors, rejected, reconcile_warnings` | Also includes `thread_dedup_rejections` and `compendium_dup_redirects` |

### Stream Aliases

| Alias | Maps to | Note |
|-------|---------|------|
| `storytell` | `record` | Listed in COMMANDS.md but should be flagged as **deprecated/legacy** |
| `progress` | `record` | Listed correctly |
| `rules` | `ruling` | Listed correctly |

### Rubric Quick Reference — Verify These

Rubric items 7, 10, 13 reference `sanitizer_lifecycle`, `arc_goal_updates`, `thread-audit` — these checkers exist in code. But verify that `arc_goal_updates` maps to `arc_goals` checker ID (COMMANDS.md uses checker names, code uses `arc_goals`).

## Ideal Command Set — Coverage Analysis

Target: cover all key mechanics and objects in `state.yaml`, `events.jsonl`, and `prompts.jsonl` with focused, robust commands. No massive output, no irrelevant output.

### Turn-by-turn inspection
| Command | What it covers | Source |
|---------|---------------|--------|
| `summary` | Overview of entire run | `events.jsonl` |
| `turn <N>` | Full dump of one turn | `events.jsonl` |
| `prompt <N> <stream>` | Render a specific prompt/output | `events.jsonl` |
| `deltas <N>` | What mutated on a turn | `events.jsonl` (applied/rejected) |
| `mechanics <N>` | Dice, ruling, pacing, beats for one turn | `events.jsonl` |

### State snapshots
| Command | What it covers | Source |
|---------|---------------|--------|
| `state --format` | Current state, filtered by section | `state.yaml` |
| `diff` | Compare two turns' state | `state.yaml` |
| `trace` | Track a field across turns | `events.jsonl` |
| `search` | Find turns matching patterns | `events.jsonl` |

### Mechanics & objects
| Command | What it covers | Source |
|---------|---------------|--------|
| `threads` | Thread lifecycle, dormancy, urgency decay, caps | `events.jsonl` + `state.yaml` |
| `goals` | Arc goal changes over time | `events.jsonl` + `state.yaml` |
| `beats` | Beat candidates, pending beats, recent beats | `state.yaml` |
| `rolls` | Dice resolution bands | `events.jsonl` |
| `convergence` | Convergence score over turns | `events.jsonl` |
| `phase-transitions` | Scene phase transitions | `events.jsonl` |
| `curtain-call` | Scene phase compliance | `events.jsonl` |

### Extraction pipeline
| Command | What it covers | Source |
|---------|---------------|--------|
| `warnings` | Retry errors, rejections, dedup signals | `events.jsonl` |
| `prompt-sizes` | Token counts per pipeline stage | `events.jsonl` |

### Audit
| Command | What it covers | Source |
|---------|---------------|--------|
| `storyteller-audit` | Record output format compliance | `events.jsonl` |
| `ruling-audit` | Band distribution, reason non-empty | `events.jsonl` |
| `thread-audit` | Thread lifecycle, orphans, resolution rate | `events.jsonl` |
| `npc-ghosting` | NPC disappearance detection | `state.yaml` |
| `state-history` | Conditions/inventory over time | `events.jsonl` |
| `active-conditions` | Current conditions, max concurrent | `state.yaml` |
| `compat` | Format compatibility | `events.jsonl` |

### What to drop (vacuous or overlaps)
- `beat-ttl` — field removed, no TTL concept, `extraction.world` already outputs beat candidates
- `effective-age` — field doesn't exist in `SceneExtractResult`

### What to add
- `personas` — user persona registry (exists in code, undocumented)

### Coverage gaps
| Gap | What's missing | Notes |
|-----|---------------|-------|
| `prompts.jsonl` inspection | No command reads `prompts.jsonl` directly | `prompt` command renders from `events.jsonl` only, not from `prompts.jsonl` |
| Sanitizer `changes` display | No dedicated command for `event["changes"]` / `event["changes_detail"]` | `storyteller-audit` and `thread-audit` touch this indirectly, but no human-readable "show what sanitizer did" command |
| `turn` output size | `turn` dumps everything — inherently large | Could be split into `turn ruling`, `turn narrate`, `turn scene`, `turn state`, `turn record`, `turn world` for focused inspection, but that's a bigger change |

### Stream aliases
| Alias | Maps to | Note |
|-------|---------|------|
| `storytell` | `record` | Listed in COMMANDS.md but should be flagged as **deprecated/legacy** |
| `progress` | `record` | Listed correctly |
| `rules` | `ruling` | Listed correctly |

### Rubric Quick Reference — Verify These

Rubric items 7, 10, 13 reference `sanitizer_lifecycle`, `arc_goal_updates`, `thread-audit` — these checkers exist in code. But verify that `arc_goal_updates` maps to `arc_goals` checker ID (COMMANDS.md uses checker names, code uses `arc_goals`).

## Priority Fixes

1. Remove or deprecate `beat-ttl` and `effective-age` (vacuous commands referencing removed fields)
2. Add `personas` command
3. Add `--by-scene` flags to `convergence`, `phase-transitions`, `curtain-call`
4. Complete `state` formats and `diff` sections
5. Add missing `warnings` signals
6. Flag `storytell` stream alias as deprecated
7. Update `storyteller-audit` description to "Record" terminology
8. Add `prompts.jsonl` inspection capability (new command or flag on `prompt`)
9. Add sanitizer `changes` display command or integrate into existing audit

## Implemented

### COMMANDS.md updates
- Removed `beat-ttl` and `effective-age` from table (vacuous commands)
- Added `--by-scene` flag to `convergence`, `phase-transitions`, `curtain-call`
- Added `--show-unchanged` flag to `trace`
- Completed `state --format` values: `full, compact, pc, inventory, location, scene, arc, npcs, compidx`
- Completed `diff --section` values: `npcs, inventory, conditions, location, tags, applied`
- Added `thread_dedup_rejections` and `compendium_dedup_redirects` to `warnings` signals
- Flagged `storytell` stream alias as deprecated/legacy
- Updated `storyteller-audit` description to "Record" terminology
- Added `sanitizer` command to audit table
- Added `sanitizer` command to turn data inspection table

### Code changes
- Added `sanitizer` command: `ccya/ev/audit.py` — `cmd_sanitizer()` function, shows sanitizer events for a specific turn
- Added `--from-events` flag to `prompt` command: reads from `prompts.jsonl` when available, falls back to `events.jsonl`
- Added `from-events` to `_BOOL_FLAGS` in `ccya/ev/__init__.py`
- Added `sanitizer` routing in `ccya/ev/__init__.py`
- Added `sanitizer` to help text in `ccya/ev/__init__.py`
- Added `Path` import to `ccya/ev/inspect.py`
- Added `from_events` and `save_dir` parameters to `cmd_prompt()` in `ccya/ev/inspect.py`

## Testing Results — Round 2

All commands tested against `saves/cordyceps-year-twenty-2026-07-05/`.

### Working correctly (no issues)
- `summary` — clean, focused
- `timing` — clean per-turn breakdown
- `turn <N>` — full dump (inherently large by design)
- `prompt <N> <stream>` — clean, focused
- `deltas <N>` — clean, shows key changes
- `mechanics <N>` — clean, shows ruling/beat/outcome/pacing/connectors
- `state --format` (all 9 formats) — clean
- `diff <A> <B>` — clean, shows intermediate changes
- `search` — works with `field~regex` syntax
- `rolls` — clean table
- `convergence` / `convergence --by-scene` — works
- `phase-transitions` — works (no transitions in save, correctly reports)
- `curtain-call` — works (no CLIMAX turns, correctly reports)
- `sanitizer <N>` — works (shows thread changes, goal changes, changes_detail)
- `storyteller-audit` — works
- `ruling-audit` — works
- `thread-audit` — works
- `npc-ghosting` — works
- `state-history` — works
- `active-conditions` — works
- `beats` — works, shows pipeline candidates
- `goals` — works (no goal changes in save, correctly reports)
- `prompt-sizes` — clean table with growth trends

### Bugs found and fixed
| Bug | Cause | Fix |
|-----|-------|-----|
| `state --format arc` shows "?" for threads | Code reads `t.get("text")` but state stores `t.get("summary")` | Changed to `t.get("summary") or t.get("text")` |
| `state --format arc` shows "?" for completed threads | Same issue — reads `t.get("text")` | Changed to `t.get("summary") or t.get("text")` |
| `warnings` shows duplicate rows per turn | Iterates every event (multiple events per turn) | Aggregates by turn, sums/extends lists |

### Not bugs (by design / documentation)
- `trace` can't find `player_intent` — `player_intent` doesn't exist as a top-level event field, it lives inside `ruling` dict. Correct path is `ruling.intent` (already works via generic fallback). No fix needed.
