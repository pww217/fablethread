---
title: Beat Generation Split — Eval Review Findings
status: draft
created: 2026-06-27
labels:
  - eval
  - engine
  - pacing
  - narrative
---

# Beat Generation Split — Eval Review Findings

## Scope

Eval group: `evals/runs/2026-06-26_0.30.0-2-g7a309d9_7a309d9/`
Branch: `beat-generation-split` (SHA `7a309d9`)
Runs analyzed: `0341` (15t), `0352` (15t), `0406` (15t), `0300` (10t custom), `0323` (10t space-western)
Prior eval group for diff: `2026-06-25_0.28.0-120-gbde47c3_bde47c3`

## What Changed on This Branch

The branch splits the old single "Storytell" stream into two separate phases:

1. **Record** (renamed from Storytell) — runs *during* the extraction pipeline, just like scene/state. Handles thread operations, actions generation, outcome_summary. No longer produces `gm_beat`.
2. **World** (new) — runs *after* the turn completes (end-of-turn async window), generates 2-3 candidate GM beats for the *next* turn.

Key architectural changes:
- `storytell.py` → `record.py` (renamed, stripped of beat logic)
- `storytell_system.j2` → `record_system.j2` (renamed, removed GM Beat section)
- `storytell_user.j2` → `record_user.j2` (renamed, removed scene input, pending beat, curtain call, allowed beat types)
- New `world_system.j2` + `world_user.j2` — prompt for beat candidate generation
- New `ccya/engine/world.py` — async world step function
- Ruling phase now reads `beat_candidates` from `state.meta` and asks LLM to pick ONE via `selected_beat`
- Beat lifecycle moved from extraction pipeline to ruling phase: validate `selected_beat` → set `pending_gm_beat` → append to `recent_beats` → discard `beat_candidates`
- `GMBeat.beat_expires_turn` removed — no longer tracked
- `StorytellerResult.gm_beat` removed
- `TurnResult.gm_beat` removed
- Sanitize and World moved to end-of-turn async window (after `yield("complete")`)
- Server UI references updated: `storytell` → `record`, GM beat display removed from turn viewer

## Pipeline Flow (Current)

```
Turn N:
  1. Ruling — picks selected_beat from beat_candidates (set by World on Turn N-1)
  2. Narrate — integrates pending_gm_beat into narration
  3. Scene — extracts candidate_npcs
  4. State — extracts inventory/condition deltas
  5. Record — extracts threads, actions, outcome_summary
  6. [yield("complete")]
  7. Sanitize — async
  8. World — generates beat_candidates for Turn N+1
  9. Save event/state with beat_candidates in meta
```

## Findings

### 1. World Step IS Running — beat_candidates in last_turn_state Fixed on HEAD

**Evidence:** The final `state.yaml` for run `0341` shows `beat_candidates` with 2 entries at T15. The `events.jsonl` `last_turn_state` meta shows `beat_candidates: MISSING` for all turns.

**Root cause:** Eval runs were done at SHA `7a309d9` where `event["last_turn_state"] = state` and `append_event()` were called **before** the world step. The code at `b52c7800` (HEAD) moved these to **after** the world step, so beat_candidates are now included in last_turn_state.

**Status:** **Resolved on HEAD.** The diff between `7a309d9` and `b52c7800` shows:
- `7a309d9`: `event["last_turn_state"] = state` → `append_event()` → `save_state()` → world step
- `b52c7800`: world step → `save_state()` → `event["last_turn_state"] = state` → `append_event()` → `save_state()`

**Note:** Eval tooling reading `events.jsonl` from `7a309d9` runs will still show MISSING. Need to re-run evals on HEAD to verify.

### 2. Beat Selection IS Working — Ruling Picks from Candidates

**Evidence:** In `events.jsonl`, `ruling_prompt.output` contains `selected_beat` on most turns (T2, T3, T5, T6, T7, T8, T9, T10, T12, T14, T15). The `post_turn_pending_beat` field matches the selected beat.

**Example T2:**
- Beat candidates in ruling prompt: `pressure` (tough_a), `complication` (matthew_estrada)
- Selected: `complication` — "Matthew Estrada signals a warning about the thugs at the door."
- `post_turn_pending_beat`: `type=complication, npc_id=matthew_estrada`

**Example T5:**
- Beat candidates: `escalation` (tough_a), `pressure` (tough_b)
- Selected: `escalation` — "The Bald Tough slams a heavy fist onto the table..."
- `post_turn_pending_beat`: `type=escalation, npc_id=tough_a`

**Verdict:** Beat selection pipeline works correctly. Ruling reads candidates from prompt, picks one, and it flows into `pending_gm_beat`.

### 3. Scene Produces candidate_npcs — World Receives Them

**Evidence:** `events.jsonl` `extraction.scene.output.candidate_npcs` shows 2-3 candidates per turn with valid `id`, `type` (motivation/fear/leverage/bond), and `effect` fields.

**Example T5:**
```
candidate_npcs:
  - id: tough_a, type: motivation, effect: "Bald Tough wants to intimidate Aren Voss..."
  - id: halden, type: fear, effect: "Halden fears the escalating violence..."
  - id: tough_b, type: leverage, effect: "Scarred Tough considers exercising leverage..."
```

**Verdict:** Scene extraction pipeline produces valid candidates. World step should receive these as `scene_result.candidate_npcs`.

### 4. Beat Diversity — LLM Repeats Types Too Often

**Evidence:** `recent_beats` across T2-T15 in run `0341`:
```
T2: complication
T3: complication, pressure
T5: complication, pressure, escalation
T6: complication, pressure, escalation, escalation
T7: complication, pressure, escalation, escalation, setback
T8: pressure, escalation, escalation, setback, revelation
T9: escalation, escalation, setback, revelation, opportunity
T10: escalation, setback, revelation, opportunity, opportunity
T12: setback, revelation, opportunity, opportunity, revelation
T14: revelation, opportunity, opportunity, revelation, revelation
T15: opportunity, opportunity, revelation, revelation, opportunity
```

**Pattern:** `escalation` appears 4 times consecutively (T5-T6, windowed). `opportunity` and `revelation` cluster heavily in T12-T15. The diversity guidance in `world_system.j2` ("Don't repeat the same beat type more than twice consecutively") is not being followed by the LLM.

**Verdict:** LLM diversity compliance is weak. The prompt instructs it but the model doesn't consistently follow. This is a prompt quality issue, not a code bug.

### 5. Phase Transitions — Working Correctly

**Evidence across all runs:**

Run `0341` (15t):
```
T1-T2: SETUP → T3: RISING → T4-T6: CLIMAX → T7: RESOLUTION → T8: BREATHER → T9: RISING → T10: CLIMAX → T13: RESOLUTION → T14-T15: BREATHER
```

Run `0406` (15t):
```
T1-T3: SETUP → T4-T6: CLIMAX → T7: RESOLUTION → T8: BREATHER → T9: RISING → T10-T12: CLIMAX → T13: RESOLUTION → T14-T15: BREATHER
```

Run `0300` (10t custom):
```
T1-T2: SETUP → T3: RISING → T4-T6: CLIMAX → T7: RESOLUTION → T8: BREATHER → T9: RISING → T10: CLIMAX
```

**Pattern:** SETUP → RISING → CLIMAX → RESOLUTION → BREATHER → [repeat] cycle is consistent across all runs. CLIMAX typically lasts 2-3 turns before RESOLUTION. Convergence score drives transitions correctly.

**Verdict:** Phase engine works as designed. No regressions.

### 6. Allowed Beat Types — Phase-Aligned Correctly

**Evidence:** `events.jsonl` `allowed_beat_types` per phase:
- SETUP: all 9 types
- RISING: pressure, complication, escalation, revelation, twist (5 types)
- CLIMAX: pressure, escalation, complication (3 types)
- RESOLUTION: revelation, hazard, callback, opportunity, setback, breathing_room (6 types)
- BREATHER: revelation, hazard, callback, opportunity, setback, breathing_room (6 types)

**Verdict:** `BEAT_PHASE_MAP` in `_pacing.py` is correct and applied properly by `derive_allowed_beat_types()`.

### 7. Record Stream — Working Correctly

**Evidence:** All turns show `record_skipped=False`, `record_actions=4`, valid `outcome_summary`, no retry errors. Stream renamed from `storytell` to `record` across all code paths (events, metrics, UI, prompts).

**Verdict:** Record stream works as a drop-in replacement for Storytell (minus beat generation).

### 8. "Duplicate" Turn Entries — Actually Sanitizer Events

**Evidence:** Runs `0341`, `0352`, `0406`, `0300`, `0323` all show entries for T5, T10, and T15 appearing twice. The second entry has `kind=sanitizer`, `threads_updated`, `changes_detail`, etc.

**Root cause:** The sanitizer runs every 5 turns by default (`sanitize_every=5` in `config.py:186`). It writes its own record to events.jsonl via `append_event(save_dir, record)` at `thread_sanitizer.py:123`. This is by design — the sanitizer record contains thread change details separate from the main turn record.

**Verdict:** **Not a bug.** These are distinct event types. Eval tooling just needs to filter by `kind` field (`kind=turn` vs `kind=sanitizer`). The second entry has no `last_turn_state` because it's a sanitizer record, not a turn record.

### 9. World Prompts Not in Eval Data — Fixed on HEAD

**Evidence:** `prompts.jsonl` contains 75 entries for 15 turns across 5 streams (ruling, narrate, scene, state, record = 5 × 15 = 75). No `world` stream entries.

**Root cause:** Eval runs were done at SHA `7a309d9` which did NOT have world prompt writing code. The code at `b52c7800` (HEAD) added world prompt rendering and `append_prompts()` call inside the async world step block.

**Status:** **Resolved on HEAD.** The diff between `7a309d9` and `b52c7800` shows world prompt code added at HEAD. Need to re-run evals on HEAD to verify world prompts appear in prompts.jsonl.

### 10. Driver Field — Inconsistent Quality

**Evidence:** `selected_beat.driver` values in ruling prompt output:
- T2: "The presence of the road thugs creates tension during the approach." (prose, not a valid driver)
- T3: "predatory intent" (not a valid driver)
- T5: "aggression" (not a valid driver)

Valid drivers per `GMBeat` model: `motivation`, `fear`, `leverage`, `bond`, `personality`. The LLM is generating free-text drivers instead of using the enum values.

**Verdict:** Prompt for ruling phase should explicitly restrict `driver` to the enum values. Currently the ruling prompt just shows the schema but doesn't enforce it.

## Summary

| Area | Status | Notes |
|------|--------|-------|
| Scene → candidate_npcs | Working | 2-3 candidates per turn, valid types |
| World → beat_candidates | Working | Persists to state.yaml, last_turn_state fixed on HEAD |
| Ruling → selected_beat | Working | Picks from candidates, flows to pending_gm_beat |
| Beat diversity | **Weak** | LLM repeats types 3-4x consecutively |
| Phase transitions | Working | SETUP→RISING→CLIMAX→RESOLUTION→BREATHER cycle consistent |
| Allowed beat types | Working | Phase-aligned correctly |
| Record stream | Working | Drop-in replacement for Storytell |
| "Duplicate" entries | **Not a bug** | Sanitizer events (kind=sanitizer), runs every 5 turns |
| World prompts in prompts.jsonl | **Fixed on HEAD** | Not in eval data (SHA 7a309d9 predates code) |
| Driver field validation | **Weak** | LLM generates prose instead of enum values |
| Event/state consistency | **Fixed on HEAD** | last_turn_state now written after world step |

## Action Items

1. **Re-run evals on HEAD** (`b52c7800`) to verify beat_candidates appear in events.jsonl last_turn_state and world prompts appear in prompts.jsonl
2. **Fix driver field prompt** — ruling prompt should explicitly restrict driver to enum values (`motivation`/`fear`/`leverage`/`bond`/`personality`)
3. **Fix beat diversity prompt** — world prompt diversity guidance not being followed by LLM
