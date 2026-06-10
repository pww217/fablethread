# Ideas — Pipeline Improvements from Noir Save Analysis

**Source:** `saves/noir--1930s-2026-06-02/` (turns 1–17)  
**Full findings:** See `plans/findings/NOIR-EV.md`  

---

## GM Beat Generation

### Problem (Corrected)
Storytell generated repetitive pressure beats across T12-T17, creating a "someone knocking on door" loop. The system prompt (`storytell_system.j2:135-184`) has 50 lines of beat diversity instructions but the user prompt provides zero visibility into previous GM beats — storytell cannot follow its own rules because it doesn't know what was emitted last turn or 2 turns ago.

Three distinct bugs:
1. **"Breathe" directives don't clear pending_gm_beat** — Storytell respects them (emits null), but pending_gm_beat is never cleared when storytell outputs null. Old pressure beats persist in narrate for 2-3 extra turns (T10, T13, T16 confirmed). Root fix: clear pending_gm_beat when storytell returns null.

2. **Floor relief beats structurally unreachable** — Line 1090 has `if _pc.beat_locked and not pending_gm_beat`. Since pending_gm_beat is almost never None (storytell replaces it every turn OR old beats persist through null), the condition is nearly always false. The `not pending_gm_beat` guard effectively disables the entire floor relief system. Root fix: remove the second condition.

3. **beat_locked never triggers** — `consecutive_pressure_turns` tracks `directive in ("Pressure", "Overwhelm")` but no turn in this save had those directives. Directives were empty, "Breathe", "Scene Pressure", or "Scene Imperative". The counter was 0 across all 17 turns despite 9+ pressure-type GM beats from storytell. The counter tracks the wrong signal (ruling directive instead of actual beat type). Root fix: track actual GM beat types, not directives.

### Proposed Fixes (Ordered: Minimum Viable Fix First)

**Phase 1 — No-cost code fixes (0 tokens, <10 lines Python)**
These fix the "Breathe" broken issue and enable existing safety net mechanisms that are structurally blocked:

1. **Remove `not pending_gm_beat` from line 1090** — Change `if _pc.beat_locked and not pending_gm_beat` to `if _pc.beat_locked`. This single-line deletion enables floor relief beats to override stale beats whenever beat_locked triggers. The guard was meant to prevent overwriting a valid beat with a generic relief, but in practice it blocks every relief injection because pending_gm_beat is never None.

2. **Clear pending_gm_beat when storytell emits null** — At `turn.py:998-1005`, after `_new_beat = storyteller_result.gm_beat if storyteller_result else None`, add an else branch: if `storyteller_result is not None and (_new_beat is None or not _new_beat.type)`, set `pending_gm_beat = None` and clear `beat_expires_turn`. This makes "Breathe" actually work.

3. **Track actual beat types for consecutive_pressure** — At `turn.py:1000-1005`, add: `if _new_beat and _new_beat.type in ("pressure", "escalation"): meta["consecutive_pressure_beats"] += 1 else: meta["consecutive_pressure_beats"] = 0`. Then change beat_locked in `rules.py` to use this counter instead of the directive-based `consecutive_pressure_turns`. Fixes beat_locked never triggering.

**Phase 2 — Low-token metadata plumbing (~10 tokens)**

4. **Pass `pending_gm_beat` to storytell** — Add `"current_gm_beat": pending_gm_beat` to `_storytell_messages()` context. Inject into `storytell_user.j2` as `## Current GM Beat: {type, surface_as}`. Currently storytell receives zero beat information. This closes the feedback loop at ~5 tokens.

5. **Beat origin tag + directive hint in narrate** — At `narrate_user.j2:95-97`, tag beat as `[generated]` or `[carryover]` based on turn_generated distance. Append `[dir: {directive}]` from pacing context. ~4 tokens total. Tells narrate whether the beat is fresh or stale, and why it was chosen.

6. **Tear out TTL=2 mechanism** — Replace with simpler model: beat auto-clears after 1 narration turn. Since narrate always reads the previous turn's beat (architectural 1-turn lag), a beat generated at Tn is read by Tn+1 narrate. After that, it's stale — auto-clear. This eliminates the 2-3 turn persistence entirely. Combine with Fix 2 (clear on storytell null) for complete control.

**Phase 3 — Prompt-level improvements (~10-15 tokens)**

7. **GM Beat History (`last_n_beats`)** — At `turn.py:998-1005`, after storing the new beat, append `{type, surface_as}` to a `state.meta.last_n_beats` list capped at 5 entries. Pass into `_storytell_messages()` and inject into `storytell_user.j2`. Gives storytell visibility into what *it* generated last 2–3 turns so its own diversity instructions become actionable. Requires Phase 2 Fix 4 to also be in place (current beat + historical beats = complete picture).

8. **Scene context tag in beats** — Add `scene_context` field to the GM beat dict (free-text tag like "door_arrival", "interior_search"). Storytell generates it alongside type/surface_as. Python stores it, passes it back in last_n_beats. Replaces the complex 4-category scene element system with a simpler pass-through tag. ~3-5 tokens for last 5 beats.

**Deferred (may not be needed after Phase 1+2):**

- GM beat expiration countdown in narrate — cosmetic only, doesn't fix structural issues
- Beat resolution tracking — complex, marginal gain once beat_locked works
- GM beat structure categorization by scene element — superseded by scene_context tag
- GM beat recency penalty — superseded by last_n_beats visibility
- Python-side diversity enforcement — only needed if storytell continues to repeat after Phase 2+3 fixes

---

## NPC Compendium & Continuity

### Problem
NPC last_seen shows only location name ("last seen: Sullivan's Apartment") with no temporal distance or narrative context. When an NPC goes present→known→present across multiple turns (dock_runner at T12-T17), the narrator cannot distinguish "just here" from "absent 5 turns ago." Additionally, unknown_visitor was marked [PRESENT] despite never entering the scene — they were knocking/screaming *outside* the door.

### Proposed Fixes

**NPC last_seen with location comparison + turn delta**
- At `_npc_roster.j2:13`, change from showing just `location_name` to including turn count and current-location comparison
- Example output: "last seen: T14, 3 turns ago" or "last seen: this location (T14), 3 turns ago"
- Requires passing current location ID into the roster context for comparison at `_npc_roster.j2`
- Python already stamps `{turn, location_id, location_name}` at `turn.py:1107-1117`; just needs to be surfaced differently

**Presence state granularity (NEARBY/AUDIBLE tier)**
- Problem: Presence is binary — present/known. unknown_visitor was marked [PRESENT] despite never entering the scene; they were knocking/screaming *outside* the door, not inside Sullivan's Apartment. "Present" should mean in-scene.
- Add NEARBY or AUDIBLE tier between PRESENT and KNOWN for NPCs who are audible/near but not physically in the room (e.g., someone knocking on a closed door). Prevents storytell from treating them as an active scene participant when they're just environmental pressure.

**NPC Alias Resolution (Unknown Visitor → Leo)**
- Problem: "Unknown Visitor" was created with `name="Unknown Visitor"` instead of being stored as an alias. When "Leo" appeared 2 turns later, scene extractor saw a new proper name and created a separate entry — no dedup link existed.
- Fix 1 (scene extraction): Add instruction to `extract_scene_system.j2` that placeholder names like "Unknown Visitor," "Frantic Stranger," "Mysterious Figure" should go into `aliases`, not `name`. Only proper names (given + family name) belong in `name`.
- Fix 2 (dedup logic): Enhance `_dedup_compendium_update()` at `extraction.py:142-161` to match new proper names against existing NPCs where those placeholders are stored as aliases, with matching location and timing within 1-2 turns. Update the existing entry with the real name instead of creating a duplicate.
- Fix 3 (storytell instructions): Once a proper name is known in storytell's GM beat guidance, reference NPCs by their real names rather than descriptions like "someone knocking at door." This guides narrate toward using proper names naturally and prevents arrival-type beats for resolved identities.
- UI display: Proper name first, fall back to alias if no proper name set (template change in `_npc_roster.j2`).

**Scene Extraction Identity Deduplication**
- When scene extractor creates an NPC from narration text, fuzzy-match bio keywords against existing NPCs to detect potential duplicates before they hit the compendium. Relies on outcome_summary cross-referencing rather than just name matching. Make dedup more robust beyond current `_dedup_compendium_update()` which only checks exact name/alias matches.

---

## Arc & Thread Management

### Problem
Thread progress updates replace previous values entirely (single-string replacement), burying investigative findings in prior_history. Storytell does not receive resolved arcs — only narrate gets them via TTL-filtered list at `narrate.py:56`.

### Proposed Fixes

**Resolved Arcs for Storytell**
- Narrate already receives resolved_arcs with TTL filtering (default 3 turns), showing resolution text AND goal_context via `_arc.j2` lines 14-15
- Storytell does NOT receive this — add it to `_storytell_messages()` params at `extraction.py:248-269` and include in storytell prompt
- Helps storytell understand why arcs ended the way they did for better successor generation

**Thread Progress as Append List (future)**
- Replace single-string `thread.progress` with `{progress_log: [str, ...], current_summary: str}` where updates append rather than replace
- Cap log at N entries per thread or unlimited — player can hover over a thread to see full bulleted history
- Keep `current_summary` as last entry for display in prompts

---

## Condition Lifecycle

### Current Behavior
Python auto-expires conditions at `turn.py:1011-1030`: when `turns_remaining` hits 0, condition is removed from state entirely and an event logged. Permanent conditions (no turns_remaining field) persist indefinitely forever.

### Proposed Change

**Condition age + system guidance instead of hard expiration**
- Give LLM visibility into condition age in prompts alongside existing TTL countdown
- Add system prompt guidance: "Consider conditions > 4 turns as requiring pruning soon unless narration demands they remain"
- Shifts condition lifecycle management partially to the LLM rather than Python silently deleting them
- Needs more thought on interaction with existing auto-expiration mechanism

---

## What Was Considered But Rejected

| Idea | Reason for Rejecting |
|------|---------------------|
| Momentum trend direction | Narrator probably doesn't need it; storytell could use but token cost vs benefit unclear at this stage |
| De-escalation magnitude / narrative velocity raw floats | Already consolidated into directive string ("Pressure"/"Breathe"); adding raw values adds system prompt weight without clear payoff |
| Scene age + combat urgency display | 15-25 tokens is more than others; Python already uses it for directives — if narrator can't self-correct from those, this may not help enough to justify cost |
| Inventory/condition delta signals (this-turn changes) | Current handling works fine per assessment |

---

## Implementation Priority (Revised)

### Phase 1 — Code-only fixes (0 tokens, <10 lines, no prompt changes)
Do first — these fix structural bugs that prevent existing safety nets from working:
1. **Remove `not pending_gm_beat` from line 1090** — enables floor relief beats
2. **Clear pending_gm_beat when storytell emits null** — fixes "Breathe" broken
3. **Track actual beat types for consecutive_pressure** — makes beat_locked functional
4. **Tear out TTL=2 mechanism** — replace with 1-narration auto-clear (handled by new null-clearing)

### Phase 2 — Low-token metadata plumbing (~10 tokens total)
Do after Phase 1 is deployed and working:
5. **Pass pending_gm_beat to storytell** — ~5 tokens, closes storytell beat blindness
6. **Beat origin tag + directive hint in narrate** — ~4 tokens, improves beat interpretation
7. **NPC last_seen with turn delta + location comparison** — ~3 tokens, template-only change
8. **Resolved arcs for storytell** — ~5 tokens, reuses existing `_arc.j2` logic

### Phase 3 — Prompt-level improvements (~10-15 tokens)
9. **GM beat last_n_beats history** — ~5-10 tokens, enables diversity instructions
10. **Scene context tag** — ~3-5 tokens, replaces complex categorization

### Medium impact, needs more thought:
- Condition age display + system guidance model shift

### Deferred (may not be needed after Phases 1-3):
- Thread progress as append list
- Beat resolution tracking
- Python-side beat diversity enforcement with corrective guidance
- GM beat structure categorization by scene element
- GM beat recency penalty
