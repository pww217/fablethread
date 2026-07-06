---
title: "Fresh eval cycle — comprehensive post-I-28 validation"
status: scoping
urgency: 2
size: large
created: 2026-07-06
ticket_id: E-11
labels:
  - eval
  - comprehensive
---

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
