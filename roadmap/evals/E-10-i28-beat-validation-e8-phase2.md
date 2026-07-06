---
title: "Eval — I-28 beat recipe + complete E-8 Phase 2 (3x15 persona runs)"
status: scoping
urgency: 2
size: medium
created: 2026-07-05
ticket_id: E-10
labels:
  - eval
  - beats
  - pacing
---

## Purpose

Complete the 3x15 persona eval runs that were started for I-28 beat recipe validation and E-8 Phase 2. This single eval batch validates both tickets simultaneously.

## Status: I-28 FAILING — `npcs` always empty

All 3 runs show 100% of beats with empty `npcs` field:
- `1717_space-western_15t`: 45/45 beats empty `npcs`
- `1723_golden-piracy_15t`: 45/45 beats empty `npcs`
- `1655_noir-1930s_15t`: 3/3 beats empty `npcs` (incomplete run — only 3 turns before investigation)

### Root cause discovered

**Bug: `state.compendium.npcs` is a `FrozenDict[str, NPCEntry]` (Pydantic models). `build_npc_roster()` calls `entry.get("presence")` on Pydantic models → returns `None` → defaults to `KNOWN` at `npc_roster.py:91` → filters everyone out.**

The scene extractor (`scene.py:20`) already does `.model_dump()` correctly, which is why it works. The world step (`world.py:43`), narrate step (`narrate.py:51`, `narrate.py:242`), and ruling step (`ruling.py:162`) all pass raw `state.compendium.npcs` without `.model_dump()`.

**Fix applied:** Added `.model_dump()` dict comprehension in:
- `world.py:43` — world step NPC roster
- `narrate.py:51` — `_narrate_messages()` default npc_roster
- `narrate.py:242` — `_build_narrate_context()` present-only roster
- `ruling.py:162` — ruling step NPC roster

**Template fix:** `narrate_user.j2` — added `## Characters` header before `{% include "sections/_npc_roster.j2" %}` to match the system prompt's reference to "## Characters list."

## Prompt rendering verification (turn 4, golden-piracy)

All user prompts render correctly after I-28 fixes:

| Stream | Status | NPC roster |
|--------|--------|------------|
| world | FIXED | 4 NPCs with full details |
| narrate | FIXED | "## Characters" header + full roster |
| ruling | FIXED | "## Present NPCs" simplified roster |
| scene | FIXED | All 4 NPCs in compendium |
| state | OK | No NPC roster needed |
| record | OK | Works via --from-events |
| storytell | BROKEN (pre-existing) | No Jinja templates exist |

### E-8 (I-13, I-25, I-26 testing validation)
- **Phase 1:** noir-1930s:driven 5 turns — critical check passed
- **Phase 2 (partial):** noir-1930s:driven 9 turns post-fix — phase persistence fix confirmed (SETUP→RISING at turn 3)
- **Phase 3:** zombie-survival:cautious 25t + allied-ww2:aggressive 25t — I-25 bug confirmed (phase stays SETUP), convergence oscillating
- **Phase 2 (post-fix):** 3 runs × 9 turns each — phase persistence confirmed across all 3
- **E-8 findings:**
  - I-25 band outcomes + phase transitions: **confirmed working** (phase persistence fix in `narrate.py`)
  - I-26 pc.situation keys: **no issue** (keys stable across turns)
  - I-13 skill distribution: **insufficient data** (too few rolls in short runs)
  - **OPEN ISSUE:** Opening prose leak CONFIRMED across all runs — `pc.situation.opening` contains full prose text
  - Thread lifecycle false positive fixed (B-30)
  - Sanitizer lifecycle checker fixed (`.get()` on Pydantic model → `getattr`)
  - Turn metrics: extract dominates (54% of time, ~20s/turn)

### I-28 (Beat recipe format with NPC personality priority)
- Beat recipe format changes committed in `641e06fa`
- Changes: recipe-format beats with bracket tags, NPC priority order, `npcs` field on GMBeat model, ruling.py passes `npcs` through, narrator prompt updated
- **Partial progress:** noir-1930s:driven 15-turn run completed (save: `1655_noir-1930s_15t`)
- **Missing:** space-western:speedrunner 15t, golden-piracy:completionist 15t

## Eval Plan

### Phase 1: Complete 3x15 persona runs

Run the two missing persona pairs for 15 turns each:

1. **space-western:speedrunner** 15 turns
2. **golden-piracy:completionist** 15 turns

(noir-1930s:driven already completed as `1655_noir-1930s_15t`)

### Phase 2: Validation checks per ticket

#### I-28 checks (beat recipe format)
- Beat `npcs` field populated in most beats (not empty `[]`)
- Beat `effect` uses recipe format with bracket tags (`[npcs: name]`, `[highlight: fear]`, `[thread: id]`)
- No thread-only beats when NPCs exist in scene
- No thread repetition (same thread ID in 5-turn window)
- World model follows NPC-first priority order
- Narrator can interpret recipe beats naturally (no confusion in narration)
- Beat types use 8 types (hazard dropped)

#### E-8 checks (continue validation)
- **Opening prose leak:** Does `pc.situation.opening` still contain full prose in these runs? (confirmed in prior runs)
- **I-25 band outcomes:** Do success/crit_success rolls produce narrative relief and scene motion? Check outcome_hint alignment with band.
- **Phase transitions:** Verify phase machine continues working across longer runs
- **I-13 skill distribution:** Still insufficient data in 15-turn runs — need 25+ turn runs with more dice rolls

### Phase 3: I-13 skill distribution (conditional)

Only if Phase 1+2 pass with no critical bugs:

Run 25-turn evals with more dice rolls expected:
- zombie-survival:cautious 25 turns
- allied-ww2:aggressive 25 turns

Track skill distribution across all rolls. Target ~25% each (strength, dexterity, constitution, charisma, wits, intelligence). Check intent_verb → skill mapping is working correctly.

### Phase 4: Opening prose leak (conditional)

If the opening prose leak is confirmed in Phase 1 runs (likely given prior evidence):

File as a new bug ticket. The `opening` field in `pc.situation` contains full prose text instead of just the schema-defined keys. This is separate from the I-25 band outcomes fix.

## Deep Dive Commands (after runs)

```bash
# Beat inspection
ev.py beats --save-dir <save-dir>
ev.py turn <N> --format json | jq '.beat'  # per-turn beat details
ev.py mechanism <N> --beats  # beat selection per turn

# Beat recipe format validation
ev.py turn <N> --format json | jq '.beat.candidates[].npcs'  # check npcs populated
ev.py turn <N> --format json | jq '.beat.candidates[].effect'  # check recipe format

# I-25 band outcomes
ev.py rolls --save-dir <save-dir>
ev.py turns --save-dir <save-dir>
ev.py mechanics <N> --pacing --dice

# I-26 opening prose
ev.py state --save-dir <save-dir> --format pc  # check pc.situation keys
ev.py state --save-dir <save-dir> --format pc | grep -A5 "opening:"

# I-13 skill distribution
ev.py rolls --save-dir <save-dir>  # track skill per roll

# Convergence + phase
ev.py convergence --save-dir <save-dir>
ev.py phase-transitions --save-dir <save-dir>
```

## Output

Phase reports at: `evals/runs/<group>/PHASE-1.md`, `PHASE-2.md`
Consolidated report: `evals/runs/<group>/REPORT.md`
