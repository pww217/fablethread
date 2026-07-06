---
title: "Fresh eval cycle — comprehensive post-I-28 validation"
status: done
completed: 2026-07-06
urgency: 2
size: large
created: 2026-07-06
ticket_id: E-11
labels:
  - eval
  - comprehensive
---

## Status: Complete — all phases done, REPORT.md written

## LLM Backend

- **Primary:** `10.75.100.51:1234` (LMStudio, `google/gemma-4-26b-a4b-it`)
- **Fallback:** `localhost:8080` (llama-swap, Gemma 4-26B)

## Purpose

Run a fresh eval cycle with fresh eyes after I-28 beat recipe changes and E-8 phase persistence fix. Validate all open bugs and eval findings across multiple personas and turn lengths. Use ev-review for deep subjective analysis of the most complex systems.

## Pre-Eval Checklist (Before Running Evals)

### Fix B-33: Engine thread culling abandons seed threads on turn 1
- **Urgency:** 2 | **Size:** small
- **Root cause:** Culling threshold `>= 3` dormant threads fires immediately when seed generates 3 dormant threads
- **Fix:** Change threshold from `>= 3` to `>= 4` in `ccya/engine/turn_state.py:593`
- **Files:** `turn_state.py`, optionally `pacing-systems.md` if threshold changes

### Fix B-29: NPCEntry.id missing in state-left template
- **Urgency:** 2 | **Size:** small | **Status:** validated
- **Root cause:** Template uses `npc.id` but NPCEntry has no `id` field — ID is dict key
- **Fix:** Use dict key instead of `.id` on NPCEntry in `_state_left.html`
- **Files:** `_state_left.html` lines 12-20, 44-52

### Fix I-17: Per-NPC deterministic sidebar colors
- **Urgency:** scoping | **Size:** scoping
- **Current state:** Color generation exists in `npc_roster.py` and `server/app.py` as separate implementations
- **Issue:** Two different palettes (npc_roster has 12 colors, server has 12 colors but different values), potential inconsistency
- **Fix:** Consolidate color generation into single source, ensure templates use it consistently

## Eval Plan

### Phase 1: Run 3×15 persona evals (I-28 + E-8 continuation)

Complete the eval runs started in E-10:

1. **noir-1930s:driven** 15 turns
2. **space-western:speedrunner** 15 turns
3. **golden-piracy:completionist** 15 turns

### Phase 2: Run 2×25 persona evals (I-13 skill distribution)

Only if Phase 1 passes:

4. **zombie-survival:cautious** 25 turns
5. **allied-ww2:aggressive** 25 turns

### Phase 3: Ev-Review deep dives (subjective analysis)

After eval runs complete, use ev-review for focused deep dives on:

1. **Pacing/Phase Engine** — Does the 5-state machine feel right? Are transitions justified? Check convergence score computation vs narrative feel.
2. **Thread Lifecycle** — Are seed threads surfacing? Are dormant threads handled well? Check thread urgency escalation.
3. **Beat System** — Are mechanism-tag beats producing good narration? Any repetition? Diversity ban working?
4. **NPC System** — Are NPCs feeling alive? Presence transitions natural? Compendium management working?
5. **Sanitizer** — Is thread sanitization reasonable? Any edge cases? Unknown thread ID warnings?

### Phase 4: New Bug Discovery

Track any new bugs found during eval runs as new B- tickets. Priority areas:

- Opening prose leak (confirmed in E-8, verify if fixed)
- Thread lifecycle edge cases
- Extraction failures
- Template rendering issues
- Convergence score anomalies

## Open Issues to Verify

### From E-8 / E-10:
- [ ] **Opening prose leak:** Does `pc.situation.opening` still contain full prose? (confirmed in prior runs)
- [ ] **I-25 band outcomes:** Do success/crit_success rolls produce narrative relief? (phase persistence fix confirmed, need more data)
- [ ] **I-13 skill distribution:** Need 25+ turn runs for sufficient dice rolls
- [ ] **Thread lifecycle:** Any thread_update/thread_resolve referencing unknown IDs?

### From B-33:
- [ ] **Seed thread abandonment:** No threads should abandon on turn 1 after threshold fix

### From B-26:
- [ ] **Sanitizer edge cases:** Unknown thread ID warnings — should be tolerable, not blocking

### From I-19:
- [ ] **Seed threads surfacing:** Do seed threads ever go dormant for entire run? Need to verify if this is still happening.

### From I-4:
- [ ] **Difficulty balancing:** Are too many hard rolls happening? Player momentum stuck at -2/-3?

## Ev-Review Commands

### Pacing/Phase Engine
```bash
ev.py mechanics <N> --dice --pacing --save-dir <path>
ev.py convergence --save-dir <path>
ev.py phase-transitions --save-dir <path>
```

### Thread Lifecycle
```bash
ev.py threads --summary --save-dir <path>
ev.py turn <N> --format json | jq '.arc.threads[] | {id, urgency, dormant}'
```

### Beat System
```bash
ev.py beats --save-dir <path>
ev.py turn <N> --format json | jq '.beat'
ev.py mechanism <N> --beats
```

### NPC System
```bash
ev.py turn <N> --format json | jq '.compendium.npcs | to_entries[] | {id: .key, presence: .value.presence}'
ev.py state --save-dir <path> --format pc
```

### Sanitizer
```bash
ev.py warnings --save-dir <path>
ev.py turn <N> --format json | jq '.changes[] | select(.kind == "sanitizer")'
```

### State Inspection
```bash
ev.py state --save-dir <path> --format pc | grep -A5 "opening:"
ev.py turns --save-dir <path>
ev.py rolls --save-dir <path>
```

## Output

Phase reports at: `evals/runs/<group>/PHASE-1.md`, `PHASE-2.md`, etc.
Consolidated report: `evals/runs/<group>/REPORT.md`

New bugs filed as B- tickets in `roadmap/bugs/`.
New eval findings filed as E- tickets if they warrant separate tracking.

## Eval Findings (Phase 1-3)

### Checker Fixes

1. **`convergence_recompute`** — 2 bugs fixed:
   - Removed `scene_age` component (removed from engine, checker still had it)
   - `recent_rolls` now reads from previous turn's state (convergence runs in narrate phase, before world step)

2. **`thread_lifecycle`** — 2 parts fixed:
   - Engine: cooldown rejections now logged to `thread_dedup_rejections`
   - Checker: skips thread_add when it's in `thread_dedup_rejections`

3. **`thread_cooldown`** — checker now skips thread_add that engine rejected for cooldown

### Engine Bugs Found

4. **SETUP→RISING transitions early** — Engine transitions SETUP→RISING on turn 2 in zombie-survival without valid trigger (no urgent thread, `turns_in_phase=1 < 3`). Likely in `_compute_scene_phase()`.

5. **World state TTL expiry not working** — Expired facts persist in `last_turn_state.scene.world_state` after `expires_turn`. Fact `edward_chaney_cornered` (expires_turn=5) still present on turns 6-9. TTL expiry in `turn.py:131-144` may not be persisting mutations.

6. **Beat candidates empty on some turns** — Investigated: world step legitimately returns 0 beats on turns 18, 24, 25 (zombie run) and turns 23-25 (allied-ww2 run). This is a late-game LLM issue — the world step LLM fails to generate beats in later turns. Not a checker bug.

### B-37 Status

- **Fixed** — `beat_candidates` now persisted at event top level (`turn.py:620`). Previously only in `extraction.world.output` (nested, hard to query). Added `beat_candidates` key to event dict in `_persist_and_async_cleanup()`.

### B-36 Status

- **Open** — `thread_add` extracted but silently dropped. `physical_bypass_retrieval` extracted as thread_add at turn 4 but never applied to `arc.threads`. No dedup/cooldown rejection logged. Suspected silent exception in arc validation block or early eviction by `thread_max_active` cap.

### Thread Lifecycle Deep Dive (zombie-survival 25t) — B-36 investigation

**6 threads total:** 3 seed (supply_stranglehold, sabotage_evidence, black_market_routes), 3 extraction thread_add (internal_corruption_discovery, physical_bypass_retrieval, locker_security_lockdown)

**4 resolved:** supply_stranglehold (turn 8), internal_corruption_discovery (turn 9), locker_security_lockdown (turn 7), sabotage_evidence (turn 10)
**2 active:** physical_bypass_retrieval (turn 4, never resolved), black_market_routes (turn 11, never resolved)

**Lifetimes:**
- locker_security_lockdown: 1-turn lifetime (extracted turn 6, resolved turn 7)
- internal_corruption_discovery: 6-turn lifetime (extracted turn 3, resolved turn 9)
- supply_stranglehold: 8-turn lifetime (seed turn 1, resolved turn 8)
- sabotage_evidence: 9-turn lifetime (seed turn 1, first update turn 8, resolved turn 10)

**Bugs found:**

1. **physical_bypass_retrieval thread lost** — extracted as thread_add at turn 4 but never applied to seed/thread pool (never appears in convergence_threads), no dedup rejection or cooldown rejection logged
2. **seed threads dedup-rejected** — supply_stranglehold dedup-rejected at turn 6, black_market_routes dedup-rejected at turns 14 and 15 (seed threads should bypass dedup)

### Beat System Deep Dive (zombie-survival 25t)

**Findings:**
- `selected_beat` always `0` across all 15 turns examined — ruling always selects first candidate
- `post_turn_pending_beat` null on 40% of turns (1, 7, 8, 11)
- When present, pending beats are predominantly `[npcs: Danny Gallegos] [highlight: leverage/motivation/fear]` — narrow NPC focus with repetitive effect patterns
- Allowed beat types shift correctly with phase: SETUP (8 types), RISING (5 types), CLIMAX (3 types)
- Beat diversity is low — effect patterns repeat, no novel beat types emerge beyond NPC pressure and thread revelation

### NPC Management Deep Dive (zombie-survival 25t, allied-ww2 25t, space-western 15t)

**NPC creation source:** Scene extractor only (via `extraction.scene.output.compendium_npc_update`). World step produces beat candidates only, not NPCs.

**NPC counts:**
- zombie-survival: 1 NPC created during gameplay (danny_gallegos), 2 in final state (1 seed)
- allied-ww2: 3 NPCs created (jose_gonzalez, unnamed_scout, armed_guards), 4 in final state (1 seed)
- space-western: 6 NPCs created during gameplay, 7 in final state (1 seed)

**Observability:** NPC data only in `extraction.scene.output.compendium_npc_update` (nested), not at event top level. Requires digging through extraction pipeline to see NPC changes.

**Presence None values:** Scene extractor sends `presence=None` when it doesn't want to change presence. Semantically correct (None = no change) but confusing for observability — cannot distinguish "no change" from "data missing" without schema knowledge.

**NPC dedup:** No dedup redirects found across all 3 runs. Scene extractor handles NPC identity correctly.

**NPC lifecycle:** jose_gonzalez departed at turn 18 (killed in action), properly tracked with `departed_reason` and `departed_turn`. armed_guards remains present through end of allied-ww2 run.

### B-29 Status

- **Fixed** — `_state_left.html` template bug resolved, `npc.id` → dict key usage confirmed working.
