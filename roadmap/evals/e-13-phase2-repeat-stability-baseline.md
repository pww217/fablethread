---
title: "Phase 2 repeat eval: stability baseline across 5 pack/persona combos"
status: testing
urgency: 2
size: large
created: 2026-07-11
ticket_id: E-13
labels:
  - thread-urgency
  - beat-generation
  - ruling-quality
design:
plan:
pr:
  url:
  branch:
---

## Description

Phase 2 repeat eval against SHA `db5eff16` (tag `0.31.0-83`). Eval 5 pack/persona runs: noir→driven (5t), space-western→speedrunner (15t), golden-piracy→completionist (15t), zombie-survival→cautious (15t), allied-ww2→aggressive (15t). Direct checker execution found failures NOT in the agent's solo report: `thread_urgency_decay` on space-western and zombie (not in report), `beat_candidates_present` on golden-piracy and allied-ww2 (not in report). Agent report only showed `ruling_reason_quality` FAIL on zombie.

## Runs

| # | Pack → Persona | Turns | Pass Rate | Failing Checkers |
|---|----------------|-------|-----------|-----------------|
| 1 | noir-1930s → driven | 5 | 100% (43/43) | None |
| 2 | space-western → speedrunner | 15 | 97% (40/41) | `thread_urgency_decay` (2) |
| 3 | golden-piracy → completionist | 15 | 97% (40/41) | `beat_candidates_present` (1) |
| 4 | zombie-survival → cautious | 15 | 95% (39/41) | `thread_urgency_decay` (3), `ruling_reason_quality` (2) |
| 5 | allied-ww2 → aggressive | 15 | 97% (40/41) | `beat_candidates_present` (2) |

**Aggregate: 198/207 checks pass (95.7%). SKIP: `beat_narrative_chain` (missing `pending_gm_beat`) + `sanitizer_lifecycle` (requires state dir).**

### Note on agent report vs direct runner
The agent-generated report showed `ruling_reason_quality` FAIL on zombie. Direct checker execution confirmed this AND found additional failures not in the report: `thread_urgency_decay` on space-western and zombie, and `beat_candidates_present` on golden-piracy and allied-ww2.

## Root Cause Analysis

### 1. `beat_candidates_present` FAIL → ENGINE BUG (ban looseness)

**Data:** golden-piracy T5 (`beat_candidates=[]`), allied-ww2 T11/T15 (`beat_candidates=[]`). Space-western passes every turn.

**Root cause: Diversity bans threshold too low (2+ in 5). Combined with phase restriction, bans permute into a 0-beat pool.**

Decision: loosen ban thresholds from 2→3, change "MUST NOT" → "avoid if possible".

**Validation: LEGITIMATE ENGINE BUG + PROMPT ISSUE.** The engine lacks a last-resort fallback when bans + phase eliminate all valid beats. Prompt has hard numerical bans (2+) which are too aggressive.

**Decided ACTION:** Loose ban thresholds in `ccya/prompts/world_system.j2` from "appears 2+" to "appears 3+" and "MUST NOT" → "avoid if possible".

**Further actions:** Add explicit warning-level logger in `_run_world_step` (currently silent when beats=[]).

### 2. `thread_urgency_decay` FAIL → ENGINE BUG

**Data:** 
- space-western: `black_market_expansion`, `supply_chain_sabotage` (seeded dormant at T1, stay at `normal` through T10, decay at T11)
- zombie: `unreliable_intelligence`, `scavenger_alliance`, `plague_mutation` (seeded dormant, stay at `normal` through T15)

**Root cause: two interacting bugs.**

Bug A — Seeded threads have `urgency_set_turn=None`, making decay skip entirely.
- Seed prompt JSON example (prepare_seed_system.j2:162-169) lacks `urgency_set_turn` field
- LLM follows example, outputs only `urgency`, `dormant`, `type`, `id`, `summary`
- `_apply_thread_automatics` (turn_state.py:179): `if _set_turn is None: continue` — decay skips seeded threads
- Auto-dormant skips dormant threads (line 159: `not t.dormant` → false) — can't run on already-dormant
**Result: A dormant `background` thread with `urgency_set_turn=None` sits forever unmanaged — it can't auto-dormant (already dormant), decay is skipped (`None`), and it can only be modified if the LLM explicitly updates it via extraction.**

Bug B — LLM elevates dormant background threads to `normal` via extraction.
- The record LLM prompt shows dormant threads in the "Dormant Threads" footer (sections/_thread_list.j2:17)
- The prompt says "Default: emit nothing" for `thread_update`, but the boundary between "should not update" vs "should escalate" is ambiguous
- `_apply_thread_updates`, line 63-65: `if update.urgency is not None: updates["urgency"] = update.urgency; updates["urgency_set_turn"] = turn_no` — resetting the decay counter
**Result: Seed thread stays at `normal` for ~8 turns from the moment it's elevated.**

**Validation: LEGIT ENGINE BUG.** Confirmed by source:
- `ccya/models/state.py:293` — `urgency_set_turn: int | None = None` (no default)
- `ccya/engine/turn_state.py:179` — `if _set_turn is None: continue` (decay skips)
- `ccya/prompts/prepare_seed_system.j2:162-169` — No urgency_set_turn in JSON example

**ACTION (proposed fixes):**
1. **Add `urgency_set_turn: 0` to seed prompt JSON example** (prepare_seed_system.j2:162-169) — this makes decay trackable from T1 for all seeded threads.
2. **Fix auto-dormant for dormant+background threads.** Current code skips `dormant=True` threads. Change: if `dormant=True` AND `urgency == "background"` AND `last_updated_turn` older than threshold, set `urgency_set_turn = turn_no` to seed the decay counter.
3. **Clarify record prompt boundaries.** Explicit instruction: "Do NOT update dormant threads in `thread_update` unless the thread's situation has materially changed."

### 3. `ruling_reason_quality` FAIL → LLM PROMPT ISSUE

**Data:** zombie T3: "Check required: social confrontation with high stakes." — no causal keyword. T10: "forceful announcement creates narrative tension." — no causal keyword. 7 other rolls used causal phrasing with "since" or "because".

**Root cause: Prompt says "Use because/since/due to" — permissive language. LLM interprets as option.**

Prompt wording (ruling_system.j2:3): `"Use because/since/due to"` — LLM reads as "you can use these" not "you must use one of these". The LLM defaults to "Check required: <noun-phrase>" when pushed for conciseness.

**Validation: LEGITIMATE PROMPT ISSUE.** Confirmed by source: ruling.py:30 checker accepts (`reason_keywords = ("because", "since", "due to", "as")`), ruling_system.j2:3 says "Use because/since/due to". The prompt lacks explicit prohibition of noun-phrase style.

**ACTION (proposed fix):**
Replace line 3 in ruling_system.j2 with:
```
Every output MUST include a non-empty `reason` field. Structure: [Ruling] [connector] [Reason]. For difficulty rulings, use ONLY "because", "since", or "due to" as the connector. NEVER use colons, dashes, or standalone noun-phrase fragments ("Check required: uncertain outcome") — these are narrative statements, not causal reasoning. HARD CAP: 10 words max.
```

## Assessment & Actions Completed

### Completed
- All three root causes validated against source code — confirmed legitimate bugs/issues.
- **`beat_candidates_present`**: 
  - Ban thresholds loosened in `ccya/prompts/world_system.j2` (2+ → 3+, "MUST NOT" → "avoid if possible")
  - Warning logger added in `_run_world_step` when beats=[] (world.py:201)
- **`thread_urgency_decay`**:
  - Added `urgency_set_turn: 0` to seed prompt JSON examples (prepare_seed_system.j2:41, 168)
  - Fixed decay logic in `_apply_thread_automatics` (turn_state.py:179) — seeded threads with `urgency_set_turn=None` now default to `last_updated_turn` instead of being skipped
  - Record prompt clarified with dormant thread boundary instructions (record_system.j2:52)
- **`ruling_reason_quality`**: 
  - Replaced ruling_system.j2:3 with prescriptive causal phrasing enforcement — "NEVER use colons, dashes, or standalone noun-phrases"

## Resolution

### Changes Since Last Eval (SHA `d1c91365`)

- `I-37`: Fix recent_beats persistence bug
- `B-42`: NPC presence demotion fix (add `last_seen_location`, prevent location stamp override)
- `I-34`: Difficulty adjustment improvements
- `F-34`: Pack parity: manifest fields, pool min count, pre-write validation
- `F-15`: Pack validation gate
- Design reorg
