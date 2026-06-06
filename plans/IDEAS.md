# Ideas — Pipeline Improvements from Save Analysis

**Source:** `saves/noir--1930s-2026-06-02/` (turns 1–17)  
**Full findings:** See `plans/findings/NOIR-EV.md`, `CONSOLIDATED-EV-FINDINGS.md`

---

## GM Beat Generation

### Problem (Corrected)
Storytell generated repetitive pressure beats across T12-T17, creating a "someone knocking on door" loop. The system prompt (`storytell_system.j2:135-184`) has 50 lines of beat diversity instructions. The user prompt DOES render beat history via `## Recent Beats` at `storytell_system.j2:195-203` (confirmed in v3 turn_viewer). The LLM has beat data available but **ignores diversity instructions** — consecutive pressure/complication beats still appear even when last_n_beats shows them.

Three distinct bugs (all still confirmed in pirate save):
1. **"Breathe" directives don't clear pending_gm_beat** — Storytell respects them (emits null), but pending_gm_beat is never cleared when storytell outputs null. Old pressure beats persist in narrate for 2-3 extra turns. Root fix: clear pending_gm_beat when storytell returns null.
2. **Floor relief beats structurally unreachable** — `if _pc.beat_locked and not pending_gm_beat` at turn.py line ~1090. Since pending_gm_beat is almost never None, the condition is nearly always false. Root fix: remove the second condition.
3. **beat_locked never triggers** — `consecutive_pressure_turns` tracks `directive in ("Pressure", "Overwhelm")` but no turn had those directives across 77+ turns combined. The counter was 0 everywhere despite pressure-type GM beats from storytell. Root fix: track actual beat types, not directives.

### Proposed Fixes (Ordered)

**Phase 1 — No-cost code fixes (0 tokens, <10 lines Python)**
These fix structural bugs that prevent existing safety nets from working:

- [ ] **Remove `not pending_gm_beat` guard (~line 1090)** — Change to just `if _pc.beat_locked`. Enables floor relief beats to override stale beats whenever beat_locked triggers.
- [ ] **Clear pending_gm_beat when storytell emits null** — After `_new_beat = ...`, add else branch: if null, set `pending_gm_beat = None` and clear `beat_expires_turn`. Makes "Breathe" actually work.
- [ ] **Track actual beat types for consecutive_pressure** — Add counter keyed to `_new_beat.type in ("pressure", "escalation")` instead of directive-based tracking. Makes beat_locked functional.

**Phase 2 — Low-token metadata plumbing (~10 tokens)**

- [ ] **Pass `pending_gm_beat` to storytell** — Add `"current_gm_beat": pending_gm_beat` to `_storytell_messages()` context, inject into `storytell_user.j2`. Closes feedback loop at ~5 tokens.
- [ ] **Beat origin tag + directive hint in narrate** — Tag beat as `[generated]` or `[carryover]`, append `[dir: {directive}]` from pacing context. ~4 tokens total.

### Beat Fallback (Pressure/Overwhelm null handling)

Storytell should not need to emit a beat every turn — Breathe directives and Scene Imperative pushes naturally create turns without beats. But when directive is Pressure or Overwhelm and storytell emits null, the scene stalls with no GM pressure injected at all. Pirate save confirmed: 3/7 turns had beats (T2 opportunity, T5 pressure, T7 complication), but during turn 7's Scene Imperative + PARTIAL band result, LLM still failed to advance story because beat was just a complication without teeth.

- [ ] **Pressure directive null → auto-generate beat fallback.** When `_compute_pacing_context` returns Pressure/Overwhelm and storytell_result.gm_beat is None/null, derive a beat from ruling phase's outcome_summary and current scene state:
```python
if _pc.directive in ("Pressure", "Overwhelm") and (_new_beat is None):
    # Derive beat from active urgent threads + NPC presence data
    _new_beat = {"type": "complication" if urgent_count >= 2 else "pressure", 
                 "surface_as": derive_surface_from_urgent_threads()}
```
This doesn't require LLM self-governance — it's a safety net for when the directive says "escalate" and storytell fails to deliver. Surface_as can be derived from NPC presence data (npc_behavior if present NPCs exist, environmental otherwise).

### Deferred / Low Priority

- [ ] GM beat expiration countdown in narrate — cosmetic only
- [ ] Beat resolution tracking — complex, marginal gain once beat_locked works
- [ ] Python-side diversity enforcement — only needed if storytell continues to repeat after Phase 2 fixes

### Correction Since Original Document

- [x] **last_n_beats history** — Already renders in storytell prompt via `storytell_system.j2:195-203`. The LLM HAS beat history available but ignores diversity instructions. Retracted as a missing feature.
- [x] **GM Beat section absent from storytell** — Retracted. The `## Recent Beats` section renders correctly in v3. Beat data reaches the storyteller. The problem is LLM noncompliance, not missing prompt plumbing.

---

## NPC Compendium & Continuity

### Problem (Corrected)
NPC last_seen shows only location name ("last seen: Sullivan's Apartment") with no temporal distance or narrative context. When an NPC goes present→known→present across multiple turns, the narrator cannot distinguish "just here" from "absent 5 turns ago." Additionally, unknown_visitor was marked [PRESENT] despite never entering the scene — they were knocking/screaming *outside* the door.

**[STILL BROKEN]** Scene extractor NPC presence tracking failure: Returning known NPCs appearing in narration consistently fail to emit `presence: "present"` when transitioning from KNOWN→PRESENT status. In pirate save (7 turns), Nicholas Vane appeared every turn without presence field — Silas Thorne and Elias Vance (new characters) correctly got it set. LLM can follow instruction #79 for new NPCs but fails for returning ones, likely because it sees the NPC in narration and defaults to "just update notes" without checking current status from compendium roster.

### Proposed Fixes

- [ ] **NPC last_seen with location comparison + turn delta** — At `_npc_roster.j2:13`, change from showing just `location_name` to including turn count and current-location comparison. Python already stamps `{turn, location_id, location_name}` at `turn.py:1107-1117`; just needs to be surfaced differently.
- [ ] **Presence state granularity (NEARBY/AUDIBLE tier)** — Add NEARBY or AUDIBLE tier between PRESENT and KNOWN for NPCs who are audible/near but not physically in the room. Prevents storytell from treating them as active scene participants when they're just environmental pressure.
- [x] **NPC presence mechanism at code level** — `compendium.npcs` dict with presence field implemented via compendium consolidation (`ab111691`, `4a531e63`). Template renders `[PRESENT]/[KNOWN]` badges in `_npc_roster.j2:7`. LLM instruction-following gap remains (see above).
- [ ] **NPC Alias Resolution** — Add instruction to `extract_scene_system.j2` that placeholder names like "Unknown Visitor" should go into `aliases`, not `name`. Enhance `_dedup_compendium_update()` at `extraction.py:142-161` to match new proper names against existing NPCs where placeholders are stored as aliases.
- [ ] **Scene Extraction Identity Deduplication** — Fuzzy-match bio keywords against existing NPCs when scene extractor creates an NPC from narration text, before they hit the compendium. Make dedup more robust beyond current `_dedup_compendium_update()` which only checks exact name/alias matches.

### Scene Extractor Presence Tracking (New)

- [ ] **Structured context — presence check list** — Add a pre-computed list of NPCs who should be checked for presence transitions, injected into `extract_scene_user.j2` before narration:
```
## Presence check required
- nicholas_vane [was KNOWN last turn — set presence="present" if narration places him back in scene]
- robert_lowe [was PRESENT last turn — keep unless narration shows departure (set presence="known")]
```
This gives LLM explicit decision points rather than expecting it to cross-reference prose `[KNOWN]`/`[PRESENT]` badges against narration text. Low token cost (~5 tokens per NPC).

- [ ] **Fuzzy matching rejection** — Add validation in `_apply_scene_extraction()` that compares named NPCs appearing in narration text against extracted `compendium_npc_update`. If an NPC name appears in narration but has no corresponding update entry, reject the extraction and log warning. This is brute-force: it catches LLM failures to emit presence changes without requiring prompt instruction fixes. Can be combined with structured context — tells LLM what to check, rejects when it forgets.

---

## Arc & Thread Management

### Problem
Thread progress updates replace previous values entirely (single-string replacement), burying investigative findings in prior_history. Storytell does not receive resolved arcs — only narrate gets them via TTL-filtered list at `narrate.py:56`. All saves confirm zero arc_resolves across 77+ turns combined; visible goals become obsolete but never update or resolve.

### Proposed Fixes

- [ ] **Resolved Arcs for Storytell** — Narrate already receives resolved_arcs with TTL filtering (default 3 turns), showing resolution text AND goal_context via `_arc.j2` lines 14-15. Add it to `_storytell_messages()` params at `extraction.py:248-269`. Helps storytell understand why arcs ended the way they did for better successor generation.
- [ ] **Thread Progress as Append List** — Replace single-string `thread.progress` with `{progress_log: [str, ...], current_summary: str}` where updates append rather than replace. Cap log at N entries per thread or unlimited. Keep `current_summary` as last entry for display in prompts.

### Thread Update Frequency (New)

- [ ] **Band-aligned gating** — In `_apply_thread_updates`, check ruling band before merging LLM-emitted updates. If band is fail/setback/partial/no_roll AND the update isn't a genuinely new thread_add, discard it. Enforces instruction at `storytell_system.j2:138-140` ("do NOT mark threads as affected for failed checks").
- [ ] **Minimum interval enforcement** — Track last-update turn per-thread-id in state. If LLM tries to update a thread within 2 turns of its previous update without adding new progress content, reject it. Prevents the T1→T2 `the_imperial_leak` overwrite pattern seen across all saves.
- [ ] **Pre-emission validation** — Before merging any `thread_update`, compare old vs new progress text similarity (simple string diff). If LLM emits a thread update with identical or near-identical content to previous turn, reject it and log warning.

---

## Condition Lifecycle

### Current Behavior
Python auto-expires conditions at `turn.py:1011-1030`: when `turns_remaining` hits 0, condition is removed from state entirely and an event logged. Permanent conditions (no turns_remaining field) persist indefinitely forever. Zombie save had 5 conditions added across 34 turns with zero present in final state — effectively dead code.

### Proposed Change

- [ ] **Condition age + system guidance instead of hard expiration** — Give LLM visibility into condition age in prompts alongside existing TTL countdown. Add system prompt guidance: "Consider conditions > 4 turns as requiring pruning soon unless narration demands they remain." Shifts lifecycle management partially to the LLM rather than Python silently deleting them.

---

## What Was Considered But Rejected

| Idea | Reason for Rejecting |
|------|---------------------|
| Momentum trend direction | Narrator probably doesn't need it; storytell could use but token cost vs benefit unclear at this stage |
| De-escalation magnitude / narrative velocity raw floats | Already consolidated into directive string ("Pressure"/"Breathe"); adding raw values adds system prompt weight without clear payoff |
| Scene age + combat urgency display | 15-25 tokens is more than others; Python already uses it for directives — if narrator can't self-correct from those, may not help enough to justify cost |
| Inventory/condition delta signals (this-turn changes) | Current handling works fine per assessment |

---

## Resolved / Addressed Since Analysis

These items were identified in earlier analysis but have been addressed by subsequent commits:

- [x] **NPC presence mechanism** — `compendium.npcs` dict with presence field implemented via compendium consolidation (`ab111691`, `4a531e63`). Template renders `[PRESENT]/[KNOWN]` badges in `_npc_roster.j2:7`. LLM instruction-following gap remains (see NPC section above).
- [x] **UI scene card reads present NPCs** — Scene card now reads from compendium.npcs with presence='present' (`bba35d96`). NPC tooltips show bio/bond/motivation/fear/leverage + presence badge (`c2ff7110`).
- [x] **NPC mention heuristic removed** — `check_npc_mention_extracted()` and `_extract_candidate_names()` removed in commit `b7954761`. The NPC mention heuristic was failing since inception, flagging "Slowly", "Marrow" (location), "Ahead" as unknown NPCs. 182 lines of dead validation code removed from universal_asserts.py.
- [x] **Thread hard limits at seed time** — Commit `1ddf22bf` fixed backwards thread loop in seed.py, enforcing max 2 active threads at game start with all non-active forced to background urgency. Prompt tightened world_state count and relevance guidance (`59c39e9`).
- [x] **Beat last_n_beats rendering** — Template at `storytell_system.j2:195-203` renders `{% if recent_beats %}## Recent Beats...{% endif %}`. Storytell DOES receive beat history via this mechanism (confirmed in turn_viewer). LLM ignores diversity instructions despite having the data available.

---

## Implementation Priority

### Phase 1 — Code-only fixes (structural bugs)
- [ ] Remove `not pending_gm_beat` guard from line ~1090
- [ ] Clear pending_gm_beat when storytell emits null
- [ ] Track actual beat types for consecutive_pressure counter
- [x] NPC mention heuristic removal — done in b7954761

### Phase 2 — Low-token metadata plumbing (~10 tokens)
- [ ] Pass `pending_gm_beat` to storytell
- [ ] Beat origin tag + directive hint in narrate
- [ ] NPC last_seen with turn delta + location comparison
- [ ] Resolved arcs for storytell

### Phase 3 — Prompt-level improvements (~10-15 tokens)
- [x] Restraint examples added to thread_update/world_state (59c39e9) — LLM still not following, needs code enforcement
- [ ] GM beat last_n_beats history — template exists but LLM ignores diversity instructions

### High impact, needs implementation:
- [ ] Thread update frequency controls (band gating + interval enforcement)
- [ ] Scene extractor presence tracking (structured context or fuzzy rejection)
- [ ] Beat fallback for Pressure/Overwhelm null handling

### Deferred / Low Priority:
- Condition age display + system guidance model shift
- Thread progress as append list
- NPC alias resolution
- Python-side beat diversity enforcement with corrective guidance
