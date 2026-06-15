# EV Tool Meta-Analysis

**Date:** 2026-06-15
**Scope:** `scripts/debug/ev.py` — all subcommands, data shapes, UX, and limitations

---

## What EV Does Well

### 1. Turn-level inspection is excellent
`ev.py turn N` with `--json` gives a complete, structured dump of every pipeline stage for a single turn. The `--json` flag is the single most useful command for deep debugging — it surfaces every field, every prompt, every extraction output in one place.

### 2. Summary is fast and informative
`ev.py summary` gives a one-line-per-turn overview with stream counts, token usage, ruling intent, and delta counts. It's the right first step for any investigation.

### 3. Checkers are comprehensive and well-organized
The 25 deterministic checkers cover the full pipeline: phase transitions, beat validity, thread lifecycle, inventory integrity, NPC presence, tension monotonicity, crisis counting, sanitizer lifecycle, roll consistency, and more. The `--all` flag runs them all at once with a clear PASS/FAIL table.

### 4. Beats table is the best high-level mechanic view
`ev.py beats` produces a clean phase/beat-type/surface/directive table with consecutive streak detection and the `recent_beats` sliding window from state. This is the single best command for understanding narrative pacing.

### 5. Threads table shows arc progression clearly
`ev.py threads` renders a turn-by-turn matrix of thread urgency changes (latent/urgent/active) with progress kind annotations (advancement/shift/resolve). It makes it easy to see which threads are driving the story.

### 6. Momentum-check is useful for ruling analysis
`ev.py momentum-check` shows roll bands, tension_delta, raw/final totals per turn. It reveals whether the ruling engine is producing the expected tension trajectory.

### 7. State command with format options is practical
`ev.py state --format compact|pc|inventory|location|scene|arc|npcs|compidx` gives targeted views of the active game state without parsing raw YAML.

### 8. Deltas and diff are precise
`ev.py deltas N` shows exactly what changed on a turn. `ev.py diff A B --section npcs|inventory|conditions|location` shows before/after comparisons. Both are essential for tracing state mutations.

### 9. Prompt inspection is thorough
`ev.py prompt N stream user/system/field` isolates individual prompt components. Combined with `--json`, it's possible to see exactly what the LLM saw and returned for any stream.

### 10. Timing reveals performance issues
`ev.py timing` breaks down per-turn latency by pipeline stage (ruling/narrate/scene/state/storytell) and shows token counts. It caught the severe slowdown in Run 3 (turns 17-20: 70-109s each).

---

## What EV Does Poorly

### 1. `check --all` with `--save-dir` doesn't auto-detect events path
**Bug:** `ev.py check --all --save-dir saves/ev/XXX` fails with `saves/default/events.jsonl not found`. You must explicitly pass the events.jsonl path as the last positional arg: `ev.py check --all saves/ev/XXX/events.jsonl --save-dir saves/ev/XXX`.

The README says "The events file path is auto-detected from `--save-dir`" but this only works for `play`, not for `check`. This is a UX inconsistency that costs time.

### 2. `search` doesn't support dot-notation for nested fields
**Gap:** `ev.py search pacing_context.scene_phase:CRISIS` fails with `invalid expression 'pacing_context.scene_phase'`. The search command only supports flat `field:value` or `input~regex` patterns. There's no way to search nested JSON fields like `pacing_context.scene_phase` or `extraction.storytell.output.gm_beat.type`.

The README shows `ev.py search pacing_context.scene_phase:CRISIS` as an example, but it doesn't work. This is a documentation bug.

### 3. `trace` doesn't work for `pacing_context.scene_phase`
**Gap:** `ev.py trace pacing_context.scene_phase` returns `Field not tracked per-turn`. The trace command can't follow nested fields across turns. This is a significant limitation since phase trajectory is one of the most important things to track.

### 4. `goals` returns nothing even when goals change
**Gap:** `ev.py goals` returned `(no goal changes found)` for all three runs, even though `arc_resolve.visible_goal` clearly changed in the storytell output (e.g., Run 1 turn 10: `"visible_goal": "Secure the primary medical transport route through the South Charles pass."`).

The `goals` command appears to look at `extraction.storytell.output.goal_update` specifically, not `arc_resolve.visible_goal`. When the storyteller emits an arc_resolve with a new visible_goal but no separate goal_update string, the goals command misses it entirely.

### 5. Narrate prose is stored in `narrate_prompt.output`, not `narrate.output`
**Data shape issue:** `ev.py turn N --json` shows `narrate.output` as empty, but the actual narrated prose is in `narrate_prompt.output`. This means:
- `ev.py prompt N narrate output` works (reads from narrate_prompt.output)
- But any checker or command that reads from `narrate.output` gets nothing
- The `state_fidelity` LLM checker reads from `narrate` field, which is empty — it's checking against nothing

### 6. Extraction format is inconsistent: `changes` vs `extraction_context`
**Critical gap:** All three test saves use `.extraction.changes` only, not `.extraction_context`. The `compat` command shows "Uses neither: 26/28/27" — meaning the `changes` field is not recognized as a valid extraction format by the compat checker.

Checkers that read `extraction_context` (like `inventory_integrity`, `conditions_lifecycle`, `npc_presence`, `location_change`) will find no data in these saves. Yet these checkers reported PASS — which means they're reading from `.applied` and `.state_snapshot` instead, not from `extraction_context`. This is a silent fallback that masks the format mismatch.

### 7. `generate_seed soft-check` warning is not surfaced by any EV command
**Gap:** The narrate prompt enforces a 530-930 word range for opening narratives, but all three first-turn narrations were far below (194, 167, 172 words). The `generate_seed soft-check: Opening narrative <450> words` warning appears in the raw output but is not captured in any structured field that EV commands can query.

There's no `ev.py` command to surface soft-check warnings. They're lost in the noise of the play command's stdout.

### 8. `thread_updates.dedup` warnings are not queryable
**Gap:** When the LLM produces tiny progress increments (0.50, 0.53, 0.56) that trigger dedup rejections, these warnings appear in stdout but are not stored in any event field. There's no way to count or analyze dedup rejection patterns across a session.

### 9. `extraction.state.empty` warnings are not queryable
**Gap:** When the state extractor fails to find inventory or condition changes after retries, the warning appears in stdout but is not stored in the event. There's no way to count these failures or correlate them with turn outcomes.

### 10. Context bloat in storytell prompts
**Observation:** Token counts grow steadily from ~15,000 to ~16,800 input tokens across 20 turns. The storytell user prompt embeds the full state snapshot, recent beats, active threads, and pacing context. As threads accumulate and scene descriptions grow, the prompt becomes increasingly bloated.

Run 3 shows the impact dramatically: turns 17-20 took 70-109 seconds each (vs. ~27s earlier), with scene extraction taking 20-30 seconds per turn. The context growth is causing real performance degradation.

---

## Information EV Doesn't Ask For (But Should)

### 1. No soft-check warning summary
A command like `ev.py warnings` or `ev.py soft-checks` that surfaces all `generate_seed soft-check` and `extraction.state.empty` warnings across a session would be valuable. Currently these are lost in stdout.

### 2. No dedup rejection summary
A command showing how many thread_update dedup rejections occurred, with the rejected progress values, would help diagnose LLM thread-update quality issues.

### 3. No phase transition summary
While `beats` shows the phase per turn, there's no command that explicitly lists phase transitions with the triggering conditions (crisis_turn_count reached, breather max, location change, etc.).

### 4. No doom spiral detection
The `spiral_detected` field exists in `pacing_context` but is always `false` in all three runs. There's no command that analyzes whether the game *should* have entered a spiral state based on consecutive pressure beats, tension trajectory, and beat patterns. The `spiral_detected` field is a binary flag that the engine sets internally, but EV doesn't have a command to analyze spiral risk independently.

### 5. No directive-to-narrative alignment score
The `directive_tone_match` LLM checker exists but requires `--llm` flag and is slow. There's no quick deterministic proxy for checking whether directives (Scene Pressure, Scene Imperative, etc.) align with the actual narrative tone.

### 6. No extraction retry summary
The `extract.retries` field exists per turn but there's no command that summarizes retry patterns across a session. High retry counts on state extraction indicate extraction prompt issues.

### 7. No scene stability analysis
There's no command that shows how many times the scene changed vs. how many turns were spent in each scene. This would help evaluate whether scenes are too short or too long.

---

## Context Bloat Issues

### 1. Storytell prompt grows with every turn
The storytell user prompt embeds the full state snapshot including all active threads, NPC notes, inventory, conditions, and recent beats. As the session progresses:
- Threads accumulate (6 threads in Run 3 by turn 20)
- NPC notes grow verbose (multi-sentence descriptions)
- Recent beats history fills the sliding window
- Pacing context adds phase/directive/crisis metadata

This causes the storytell prompt to grow from ~15,000 to ~16,800 tokens, with scene extraction being the biggest contributor (20-30s per turn in Run 3).

### 2. State snapshot is duplicated across turns
Every turn's `state_snapshot` contains the full game state at the start of that turn. When you run `ev.py turn N --json`, you get the full state snapshot embedded in the event. Inspecting multiple turns means loading multiple copies of nearly-identical state.

### 3. Narrate prompts include full context
The narrate user prompt includes `context_meta` which contains the full state, scene description, and pacing context. This is separate from the storytell prompt, meaning the same context is embedded in multiple prompts per turn.

### 4. No truncation or summarization strategy
There's no EV command or flag to analyze prompt sizes or suggest truncation points. The tooling assumes prompts fit within context limits, but doesn't help diagnose when they're getting too large.

---

## Recommendations

1. **Fix `check --all` auto-detection** — Make `--save-dir` work without explicit events path, matching `play` behavior.
2. **Add dot-notation support to `search`** — Allow `pacing_context.scene_phase:CRISIS` syntax.
3. **Fix `trace` for nested fields** — Support `trace pacing_context.scene_phase`.
4. **Fix `goals` to read `arc_resolve.visible_goal`** — Currently only reads `goal_update` string.
5. **Fix narrate data shape** — Either populate `narrate.output` from `narrate_prompt.output`, or update all consumers to read from `narrate_prompt.output`.
6. **Add `ev.py warnings` command** — Surface soft-check, dedup, and extraction warnings.
7. **Add `ev.py phase-transitions` command** — Explicit phase transition log with triggers.
8. **Add `ev.py spiral-risk` command** — Analyze spiral risk independently of the `spiral_detected` flag.
9. **Add prompt size analysis** — `ev.py prompt-sizes` to show token growth per stage across turns.
10. **Fix compat checker** — Recognize `changes` as a valid extraction format, or migrate all saves to `extraction_context`.
