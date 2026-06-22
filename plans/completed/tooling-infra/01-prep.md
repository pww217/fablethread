# Pacing/Beat System — Plan 1/3: Investigation and Prerequisite Verification

## Purpose

Read all target source at the line ranges specified in the design doc, confirm every empirical claim, identify dead code that can be removed as a standalone step, and document the precise wiring required for Plans 2 and 3.

## Problem Statement

The design doc makes claims about current code state (Finding 1.8: GM Beat section absent from storytell user prompt; counter logic at turn.py:1183-1192; floor relief block at turn.py:1089-1096). These must be verified against live source before Plans 2 and 3 can execute confidently. Missing or stale assumptions would cause Plans 2/3 to operate on incorrect baselines.

## Constraints

- No behavioral changes in this plan.
- All changes deferred to Plans 2 and 3.
- Source reads are the primary deliverable.

## Non-goals

- Not implementing any design changes.
- Not restoring the GM Beat section (that happens in Plan 3, first step).

## Solution

Read all five target zones in turn.py and the storytell prompt templates, cross-reference against the design doc's claims, produce a verified inventory of what exists, what's dead/replaceable, and what wiring is needed for the subsequent plans.

## Firm decisions

1. Every design doc claim about code state must be verified by reading source before Plan 2 begins.
2. Any dead code found is inventoried for deferred cleanup, not removed — removal happens in Plans 2/3 as part of replacement edits.
3. If the GM Beat section is absent (claimed in Finding 1.8), document the exact wiring needed to restore it — do not implement.

## Risks, Ambiguities, and Blockers

- None. This is a read-only plan.

## Status

`completed`

## Phases

3 phases: (1) source reconnaissance, (2) prerequisite verification (GM Beat section), (3) dead code inventory.

---

## Implementation — Phase 1: Source Reconnaissance

### Context files to load

- `ccya/engine/turn.py` lines 420-550 (`_compute_narration_directive` + `_compute_pacing_context`)
- `ccya/engine/turn.py` lines 994-1006 (gm_beat apply block)
- `ccya/engine/turn.py` lines 1089-1096 (floor relief injection)
- `ccya/engine/turn.py` lines 1183-1192 (consecutive_pressure counter update)
- `ccya/engine/turn.py` lines 750-758 (narrate pending_gm_beat read — pattern for storytell)
- `ccya/prompts/storytell_system.j2` lines 126-187 (PacingContext + GM Beat guidance sections)
- `ccya/prompts/storytell_user.j2` (entire file — check for beat rendering)
- `ccya/prompts/narrate_user.j2` lines 95-98 (beat rendering pattern to replicate)
- `ccya/engine/extraction.py` lines 226-274 (`_storytell_messages` — verify context variables passed to template)
- `plans/findings/CONSOLIDATED-EV-FINDINGS.md` lines 85-89 (Finding 1.8)

### Detailed steps

#### Step 1.1 — Read `_compute_narration_directive` (turn.py:420-473)

**File:** `ccya/engine/turn.py`

**What:** Verify the priority stack, Breathe trigger (`narrative_velocity < -0.3`), and that `scope_scene_threads` is in function scope for Change 6's urgent-thread guard.

**Why:** Design doc Change 6 adds an urgent-thread guard before the `return "Breathe"` at line 441. Must confirm `scope_scene_threads` is a parameter (it is — line 479 shows it passed from `_compute_pacing_context`).

**Validation:** Document that `scope_scene_threads` is available as a parameter and contains `ArcThread` objects with `.urgency` attributes.

#### Step 1.2 — Read `_compute_pacing_context` (turn.py:476-546)

**File:** `ccya/engine/turn.py`

**What:** Verify beat_locked trigger at lines 502-508, outcome_hint computation at lines 511-528, and that `consecutive_pressure_turns` is a parameter with default 0.

**Why:** Change 1 (counter re-key) feeds into this function. Must confirm the parameter signature and beat_locked conditional.

**Validation:** Document the exact line: `consecutive_pressure_turns >= config.consecutive_pressure_threshold or momentum <= config.momentum_floor`.

#### Step 1.3 — Read gm_beat apply block (turn.py:994-1006)

**File:** `ccya/engine/turn.py`

**What:** Verify the exact `if _new_beat and _new_beat.type:` block that sets `pending_gm_beat`. Confirm scope of `_new_beat`, `_beat_dict`, `turn_no`, and `state` at this location.

**Why:** Change 3 adds an else branch here. Must know the exact variable names and types.

**Validation:** Document: `_new_beat = storyteller_result.gm_beat if storyteller_result else None` at line 998; the existing `if _new_beat and _new_beat.type:` at line 1000 sets `pending_gm_beat` via `state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict`.

#### Step 1.4 — Read floor relief block (turn.py:1089-1096)

**File:** `ccya/engine/turn.py`

**What:** Verify the exact `if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):` guard and breathing_room injection.

**Why:** Change 2 replaces the guard. Must confirm `_pc` is in scope, `pending_gm_beat` is read from state, and the injection format.

**Validation:** Document exact injection format: `{"type": "breathing_room", "surface_as": "ambient", "beat_expires_turn": turn + 3}`.

#### Step 1.5 — Read consecutive_pressure counter (turn.py:1183-1192)

**File:** `ccya/engine/turn.py`

**What:** Verify the `if (directive in ("Pressure", "Overwhelm")) and not thread_updates:` logic and that `storyteller_result` is in scope.

**Why:** Change 1 replaces this with beat-type tracking. Must confirm `storyteller_result` is accessible at this location (it's unpacked at line 996 from `_extract_result`).

**Validation:** Document: `_extract_result is not None` guard at line 1184; `storyteller_result` and `_pc.directive` both in scope.

#### Step 1.6 — Read narrate pending_gm_beat pattern (turn.py:750-758)

**File:** `ccya/engine/turn.py`

**What:** Verify how the narrate pipeline reads `pending_gm_beat` from state, checks TTL, and stores it in context for template rendering.

**Why:** The storytell pipeline needs to do the same thing (pass `pending_gm_beat` to `storytell_user.j2`). This is the pattern to replicate.

**Validation:** Document exactly: `_pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")` at line 750, TTL check at lines 752-755, stored in `ctx._pending_gm_beat` at line 758.

#### Step 1.7 — Read storytell_user.j2 template

**File:** `ccya/prompts/storytell_user.j2`

**What:** Read entire file (47 lines). Confirm no `## GM Beat` section, no `pending_beat` or `gm_beat` rendering.

**Why:** Design doc Finding 1.8 claims the GM Beat section is absent. Must confirm by reading the file.

**Validation:** Document that the template has sections for: inventory, conditions, NPC roster, location, arc/threads, world_state, pacing_context, rules_outcome, recent outcomes, prior turn context, player_intent, and turn narration — but NO beat section.

#### Step 1.8 — Read _storytell_messages context wiring (extraction.py:226-274)

**File:** `ccya/engine/extraction.py`

**What:** Verify which context variables are passed to `storytell_user.j2` at lines 251-268.

**Why:** Plan 3 needs to add `pending_gm_beat` to this context dict. Must know the exact structure.

**Validation:** Document the current context keys: `narration`, `npc_roster`, `location`, `inventory`, `conditions`, `current_arc`, `all_threads`, `world_state`, `intent`, `pacing_context`, `recent_turns`, `prior_history`, `turn_no`, `band`.

---

## Implementation — Phase 2: Prerequisite Verification (GM Beat Section)

### Context files to load

Same as Phase 1 (already read).

### Detailed steps

#### Step 2.1 — Confirm Finding 1.8

**File:** `ccya/prompts/storytell_user.j2`

**What:** Cross-reference the file read in Step 1.7 against Finding 1.8's claim that "the `## GM Beat` section with beat type, `## Current Pressures`, and `pending_beat` are completely missing from the storytell user prompt."

**Why:** This is the critical prerequisite for Change 4b (beat history rendering). If the beat context section doesn't exist, beat history cannot be added until it does.

**Validation:** CONFIRMED — storytell_user.j2 has no `## GM Beat` section, no `pending_beat` rendering, no beat type display. The narrator_user.j2 lines 95-98 (`**Beat:** ... rendering) is the pattern that must be replicated in storytell_user.j2.

#### Step 2.2 — Document exact restoration requirements

**File:** `ccya/engine/extraction.py` (context wiring) + `ccya/prompts/storytell_user.j2` (template rendering)

**What:** Specify the minimum changes needed to restore the GM Beat section:

1. In `_storytell_messages` (extraction.py:248-268), add `"pending_beat": (state.get("meta") or {}).get("pending_gm_beat")` to the template context dict.
2. In `storytell_user.j2`, add a `## GM Beat` section (after pacing_context or before CURRENT TURN) that renders the pending_beat type, surface_as, and expiry — following the narrate_user.j2 pattern but adapted for the storyteller's role.

Exact rendering text to be determined in Plan 3 (this is interface spec, not implementation).

**Why:** Plan 3 will implement these changes as its first task, before adding beat history.

**Validation:** Documented. No code written.

---

## Implementation — Phase 3: Dead Code Inventory

### Context files to load

- `ccya/engine/turn.py` lines 750-758, 994-1006, 1089-1096, 1183-1192 (already read)
- `ccya/engine/turn.py` lines 476-483 (function signature of `_compute_pacing_context`)

### Detailed steps

#### Step 3.1 — Evaluate directive-based counter (turn.py:1183-1192) for standalone removal

**File:** `ccya/engine/turn.py`

**What:** The counter logic at lines 1183-1192 is:
- Increments when `directive in ("Pressure", "Overwhelm")` — but these directives never fire (0/51 turns).
- Resets to 0 on every other turn.
- This means the counter is always 0 at `_compute_pacing_context` (line 504), making the first branch of beat_locked unreachable.

**Why:** Is this safe to remove as a standalone step (before Plan 2)? No — because Plan 2 Change 1 replaces this exact block. Removing it now and rewriting it in Plan 2 is unnecessary churn. The block is dead-but-harmless — it consumes ~1 CPU cycle per turn. Leave it in place for Plan 2 to replace in one edit.

**Validation:** VERDICT — retain. Plan 2 replaces it entirely.

#### Step 3.2 — Evaluate floor relief guard (turn.py:1090) for standalone removal

**File:** `ccya/engine/turn.py`

**What:** The guard at line 1090 (`if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat")`) is structurally unreachable because beat_locked never fires. It's dead-but-harmless.

**Why:** Same reasoning as Step 3.1 — Plan 2 Change 2 replaces this guard. Standalone removal creates unnecessary diff.

**Validation:** VERDICT — retain. Plan 2 replaces it.

#### Step 3.3 — Search for other dead code in turn.py unrelated to this design

**File:** `ccya/engine/turn.py`

**What:** Quick search for any imports, variables, or functions that are truly unreferenced and unrelated to the beat/pacing changes. Use grep for `# type: ignore[unused-import]` or similar markers.

**Why:** Inventory for deferred cleanup. Do not remove — all code changes belong in Plans 2 and 3.

**Validation:** Document findings. No files modified.

---

## Tests to write or update

None. This plan produces no code changes. All test-related work is deferred until after Plans 2 and 3 complete.
