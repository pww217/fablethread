# Ideas — Pipeline Improvements from Noir Save Analysis

**Source:** `saves/noir--1930s-2026-06-02/` (turns 1–17)  
**Full findings:** See `plans/findings/NOIR-EV.md`  

---

## GM Beat Generation

### Problem
Storytell generated repetitive pressure→event/npc_behavior beats across T12-T17, creating a "someone knocking on door" loop. The system prompt (`storytell_system.j2:135-184`) has 50 lines of beat diversity instructions but the user prompt provides zero visibility into previous GM beats — storytell cannot follow its own rules because it doesn't know what was emitted last turn or 2 turns ago.

Additionally, "Breathe" directives don't work: when storytell respects them and emits null (no GM beat), `pending_gm_beat` is never cleared. Old pressure beats persist in narrate for 2-3 extra turns after the directive should have taken effect — confirmed at T10, T13, and T16 where "Breathe" was issued but narrate still injected PRESSURE beats from earlier turns.

### Proposed Fixes

**Clear pending_gm_beat when storytell emits null (fixes "Breathe" broken)**
- At `turn.py:998-1005`, after storytell output is parsed, if no GM beat field exists in the JSON output, explicitly set `pending_gm_beat = None` and clear `beat_expires_turn`
- This makes "Breathe" directives actually work — narrate stops injecting old pressure beats 2-3 turns later
- Also fixes T10/T11 where storytell emitted null but narrate saw PRESSURE from earlier turns

**GM Beat History (`last_n_beats`)**
- At `turn.py:998-1005`, after storing the new beat, append `{type, surface_as}` to a `state.meta.last_n_beats` list capped at 5 entries
- Pass into `_storytell_messages()` and inject into `storytell_user.j2` before GM beat instructions
- Gives storytell visibility into what *it* generated last 2–3 turns so its own diversity instructions become actionable

**Tear out TTL=2 mechanism entirely**
- Current TTL (`beat_expires_turn = turn_no + 2`) creates race conditions between expiration checks, storytell timing, and narrate injection points
- Beats persist 2-3 extra turns after "Breathe" because no beat exists to expire — pending_gm_beat just sits there until overwritten or 3+ turns pass
- Replace with simpler model: beat auto-clears after 1 turn (or immediately when storytell emits null), and rely on Python-side enforcement for floor relief beats rather than TTL expiration

**GM Beat Expiration Countdown**
- At `narrate_user.j2:95-97`, add expiration countdown to current beat display
- Python already tracks `beat_expires_turn = turn_no + 2` at `turn.py:1004`; narrate sees type/surface_as but no TTL
- Add `[expires in N turns]` → narrator knows to use it before it expires vs. let it fade naturally

**Beat Resolution Tracking (future)**
- Track whether a GM beat from 2+ turns ago was resolved in the narrative or left hanging
- An unresolved pressure beat should naturally escalate rather than repeat at same intensity level
- Requires tracking beat resolution state, not just emission history

### Maybe (low priority, revisit later)

**GM Beat Structure Categorization by Scene Element**
- Track which scene element each GM beat targets and prevent repeating same-element beats within 2 turns even if types differ; would have caught "someone arrives at door" across T12-T17 where all 5 beats were arrival-type despite varying labels

**GM Beat Recency Penalty**
- Track `{beat_type, surface_as, last_used_turn}` per category so storytell can be encouraged to use a beat type that hasn't been used in 4+ turns rather than being forced into variety when scene genuinely supports it

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

## Implementation Priority

**High impact, low token cost (~5-10 tokens each):**
1. Clear pending_gm_beat when storytell emits null → fixes "Breathe" broken across 3+ turns
2. Tear out TTL=2 mechanism entirely → eliminates race conditions + timing mismatches
3. GM beat last_n_beats history → storytell prompt (enables diversity instructions to work)
4. GM beat expiration countdown → narrate prompt  
5. NPC last_seen with turn delta + location comparison
6. Resolved arcs for storytell (reuse existing `_arc.j2` logic)

**Medium impact, needs more thought:**
5. Condition age display + system guidance model shift

**Future/deferred:**
6. Thread progress as append list
7. Beat resolution tracking
8. Python-side beat diversity enforcement with corrective guidance or forced variety beats

**Maybe (low priority, revisit later):**
- GM beat structure categorization by scene element
- GM beat recency penalty
