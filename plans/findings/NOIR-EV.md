# Noir Save Analysis — Arc & World State Systems

**Save:** `saves/noir--1930s-2026-06-02/`  
**Turns examined:** 1–17 (all turns)  
**Date:** June 2, 2026  

---

## 1. GM Beat Loop — Circular Storytelling (T7–T17)

### Symptoms
From T12 through T17, the GM beat generator produced a repetitive cycle:
- **T12:** `pressure/event` → dock_runner arrives at door with paper
- **T14:** `pressure/event` → unknown visitor pounding + frantic arrival framing
- **T15:** `pressure/npc_behavior` → Leo appears at doorway, detained by officers
- **T16:** `pressure/npc_behavior` → officers drag Leo away (escalation of same structure)
- **T17:** `pressure/event` → dock_runner arrives inside collapsing

The player experienced this as "several random people knocking on my door" and "officers leaving, coming, leaving, coming again." The GM beat generation was stuck in a pressure→event/npc_behavior loop with no variety enforcement.

### Root Cause: Storytell Has No Beat History Visibility

**How beats are generated:** At `turn.py:998-1005`, every storytell output unconditionally replaces `pending_gm_beat` (TTL=2). Since the storyteller emits a beat 100% of turns in this sequence, expiration never fires and floor relief beats at lines 1090–1096 never trigger.

**How beats reach narrate:** At `narrate_user.j2:95-97`, only the *current* `pending_gm_beat` (type + surface_as) is injected into the narrator's prompt. There is no history of previous beat types or surface values anywhere in any stream's prompt.

**How storytell decides what to emit:** The system prompt (`storytell_system.j2:135-184`) contains 50 lines of beat diversity instructions:
> "Crisis-aware beat diversity: During extended sequences (3+ consecutive pressure-type beats), vary beat types — do not repeat pressure/escalation every turn."  
> "At least one in three beats must use a non-pressure type"

But the user prompt (`storytell_user.j2`) provides **zero information about previous GM beats**. There is no `last_n_beats` structure in state.meta and nothing injected into `_storytell_messages`. The LLM instructions are advisory-only with no enforcement layer. Storytell literally cannot follow its own diversity rules because it has no data to work with — it sees 10 recent narrations (prose only) but not structured beat metadata like `type=pressure surface_as=event` from previous turns.

**The feedback loop:**
1. Storytell generates `pressure/event` independently each turn
2. Narrator interprets "surface as event" + pressure directive as another arrival-type scene
3. Next turn, storytell sees similar unresolved scene state (door knocking still active) and makes the same independent choice again

### What Storytell Actually Saw at T17

**NPC roster:** `dock_runner` [PRESENT], `unknown_visitor` [PRESENT] pounding/screaming, `uniformed_officers` [PRESENT] returning toward door. Compendium state was correct — dock_runner had proper presence tracking and last_seen data.

**Prior history (Recent Outcomes):**
- [T12] "Aaron opened the door to find a panicked dock runner clutching a mysterious paper"
- [T14] "Aaron is caught between approaching uniformed officers and a frantic, unidentified visitor demanding entry"
- [T15] "Aaron confronted Leo at the doorway, only to have the uniformed officers arrive and violently detain Leo against the wall"

This *should* tell storytell door arrivals happened 3 times recently. But without beat history visibility, storytell cannot cross-reference prior_history bullets against its own previous GM beats. The instructions say "recent twist/callback beats should not repeat within 2 turns" but provide no mechanism for storytell to count how many arrival-type events occurred in recent history or track what *it* generated last turn.

### Tentative Solutions (NOT COMMITTED TO)

**T1: Add `last_n_beats` to state.meta + inject into storytell prompt**
- At `turn.py:998-1005`, after storing the new beat, also append `{type, surface_as}` to a `state.meta.last_n_beats` list capped at 5 entries
- Pass this into `_storytell_messages()` as a new parameter and inject it into `storytell_user.j2` before GM beat instructions
- This gives storytell visibility into what *it* generated last 2–3 turns so its own diversity instructions become actionable

**T2: Python-side beat diversity enforcement (hard constraint)**
- At `turn.py:998-1005`, after storytell emits a beat, check against `last_n_beats` for variety violations
- If the last 2 beats were both `pressure` type or same `surface_as`, inject corrective guidance into the prompt (e.g., "Previous 2 turns used pressure/event and pressure/npc_behavior — prefer non-pressure this turn")
- Or: reject/override the beat entirely with a forced null/breathing_room

**T3: Track GM beats by scene element category, not just type/surface_as**
- Instead of raw `{type, surface_as}`, categorize each beat by which *scene element* it targets (NPC behavior vs environmental event vs player discovery vs location change)
- Prevent repeating the same scene-element target within 2 turns even if types differ
- This would have prevented "someone arrives at door" structure from repeating across T12, T14-T17

---

## 2. NPC Continuity — Compendium Tracking Works, Narrator Doesn't Use It Well

### What the Data Shows

**Compendium state was correct throughout.** At `turn.py:1106-1117`, last_seen gets stamped as `{turn, location_id, location_name}` when an NPC receives a compendium update. Presence values (present/known) flow correctly through scene → extraction → storytell pipeline via `_npc_roster.j2`.

**Example — dock_runner:**
- T12: `presence: "present"`, notes "clutching crumpled paper and wheezing in panic"
- T14: `presence: "known"` (left scene), last_seen Sullivan's Apartment
- T17: `presence: "present"` again, notes "collapsing against doorframe with cylinder"

The compendium correctly tracked dock_runner as the same NPC across 5 turns. The narrator saw them in the roster at T17 with full bio and presence state.

### Why Narrator Still Repeated the Pattern

**last_seen is just a location name.** At `_npc_roster.j2:13`, last_seen renders as "last seen: Sullivan's Apartment" — no narrative context about what was happening 5 turns ago (dock_runner was seized by police and dragged down the hall). The narrator sees `presence: known` → `present` transition but has no structured memory of *why* this NPC left or *what* they were doing last time present.

**Narrator only gets 1 recent turn.** At `narrate.py:89`, narrate receives `recent_turns[-1:]` — just the previous turn's prose. This is insufficient for establishing continuity when an NPC goes absent (known) and returns (present) across multiple turns. The narrator must infer all continuity from narrative prose alone, which doesn't explicitly state "this is the same dock_runner from 5 turns ago."

**The repetition was structural, not identity-based.** Storytell generated another arrival-type GM beat because it lacked beat history visibility (see Section 1). The narrator then interpreted this as a fresh door encounter. This was primarily a GM beat generation failure, not an NPC tracking failure — but the weak last_seen context made it harder for the narrator to recognize "this structure just happened."

### Tentative Solutions (NOT COMMITTED TO)

**T4: Expand last_seen to include outcome_summary snippet**
- At `turn.py:1106-1117`, when stamping last_seen, also attach a brief narrative context from the turn's outcome_summary or recent narration
- Example: instead of just `{location_name: "Sullivan's Apartment"}`, store `{location_name: "Sullivan's Apartment", context: "seized by officers and dragged down hallway"}`
- This is cheap — outcome_summary already exists per-turn, no new LLM work needed

**T5: Pass 2 recent turns to narrator instead of 1**
- At `narrate.py` / `turn.py`, change from `recent_turns[-1:]` to `recent_turns[-2:]` for narrate
- This gives the narrator more context for establishing NPC continuity across absent/present transitions

---

## 3. Thread Progress Overwrites — Investigative Findings Get Buried

### What Happened

At T4, Aaron searches for a murder weapon and finds no blade among debris. At T5, storytell updates `clerk_murder_coverup` thread progress from "Confirmed the absence of a weapon suggests professional cleanup by council assets" to "Transcribed details of the professional wound and council stationery into notebook."

The old finding survives in `prior_history` as `- [T4] Aaron searched the room for the murder weapon but found no blade among the debris.` But it gets buried — by T17, prior_history has 20 entries (capped at turn.py:1302-1303), and early investigative findings are pushed out or become invisible in the bulleted list.

### Root Cause

At `turn.py:1119-1125`, `_apply_thread_updates` processes thread updates from storytell output. The storytell JSON contains a single `progress` string per updated thread, which **replaces** the previous value entirely. There is no accumulation mechanism — each update overwrites.

### Tentative Solutions (NOT COMMITTED TO)

**T6: Change thread progress to append-only list**
- Replace single-string `thread.progress` with a structure like `{progress_log: [str, str, ...], current_summary: str}` where updates append rather than replace
- Cap the log at N entries per thread (e.g., 10) or unlimited — player can hover over a thread to see full bulleted history
- Keep `current_summary` as the last entry for display purposes in prompts

**T7: Show progress_log in storytell prompt alongside threads**
- At `_arc.j2`, render each thread's update log (last 3 entries) so storytell has visibility into what was previously recorded about this thread
- This helps storytell avoid duplicating information already captured and makes more intelligent update decisions

---

## 4. GM Beat Accuracy & Diversity — Beyond 5-Turn History

Beyond passing last 5 beats to the prompt, here are additional levers for improving beat generation quality:

### A. Pass Scene Element Usage Tracking
Track which *scene elements* each GM beat targeted (NPC behavior, environmental event, player discovery, location shift). Storytell could then avoid repeating "someone arrives at door" structure even if it doesn't remember the exact previous beat type. This categorization would need to be added as metadata alongside `type`/`surface_as`.

### B. Pass Recent Narration Themes
Instead of raw narration prose (which is token-heavy), extract 2-3 high-level themes from recent narrations and pass them as structured tags: e.g., `[door_confrontation, police_presence, isolation]`. Storytell could then see "you've had 3 door confrontations recently" without needing full prose.

### C. Python-Side Beat Budget
Maintain a per-turn budget in state.meta tracking how many beats of each type have been used across the last N turns: `{pressure: 4, opportunity: 1, complication: 2}`. When storytell emits its beat, check if it would push any category over-budget and inject corrective guidance or force variety.

### D. Beat-Scene-State Alignment Check
Before accepting a GM beat from storytell, Python could verify alignment with current scene state at `turn.py:998`. Example checks:
- If beat targets "NPC behavior" but no named NPCs are PRESENT → flag as misaligned
- If beat is "player_discovery" but player just searched this area 2 turns ago → suggest alternative
- This would be advisory guidance injected into the prompt, not hard enforcement

### E. Directive-to-Beat Mapping Refinement
Currently at `storytell_system.j2:126-131`, directives loosely map to beat types (Pressure→complication/pressure). Could tighten this mapping with explicit constraints: "After 2+ consecutive pressure beats from Pressure directive, prefer complication over escalation." This is prompt-level guidance but more specific than current instructions.

### F. Beat Recency Penalty
Track not just *what* beat was emitted last turn, but *how long ago* each beat type was last used. If `pressure/event` hasn't been used in 4 turns and the scene supports it (door knocking unresolved), storytell could be encouraged to use it rather than being forced into variety for its own sake. This requires more granular tracking: `{beat_type, surface_as, last_used_turn}` per category.

### G. Narrator Feedback Loop
Currently GM beat generation happens *before* narration completes — storytell generates a beat, then narrate receives it and writes prose. What if the beat generation saw what was just narrated? This would require restructuring: have narrate run first (without GM beat), then storytell sees both prior history AND current turn's partial narration to generate its beat more contextually aware of what just happened.

### H. Beat "Resolution" Tracking
Track whether a GM beat from 2+ turns ago was *resolved* in the narrative or left hanging. An unresolved pressure beat should naturally escalate rather than repeat at same intensity level. This requires tracking beat resolution state, not just emission history.

---

## 5. World State — Working Correctly (But Growing)

World state accumulation is clean across all 17 turns:
- T10: `ross_hostility_aaron` added
- T13: `council_dock_purge` added
- T16: `leo_detained` added
- T17: `council_seal_in_aaron_possession` added

No duplicates or overwrites. 5 persistent facts are non-redundant and accurately reflect game state changes. However, by T17 these immutable world_state lines consume noticeable prompt space (~20% of storytell user prompt). This is acceptable growth but worth monitoring as the campaign continues — if world_state grows beyond ~8-10 entries, it may warrant summarization or tiered visibility (show only "persistent" items in full, compress "temporary" ones).

---

## 6. GM Beat Expiration Mechanism — Broken in Two Ways

**Current behavior:** At `turn.py:998-1005`, TTL is set to `beat_expires_turn = turn_no + 2`. At lines 750-758, expiration checks `turn_no > beat_expires_turn` and clears pending_gm_beat.

**Problem A — Storytell always replaces before expiry:** Since storytell emits a GM beat 100% of turns in this save (except when "Breathe" directive is active), TTL=2 means expiration never fires in practice. The beat is always replaced by a new one before it expires. This creates a state where `pending_gm_beat` always exists, so floor relief beats at lines 1090-1096 (`beat_locked=True AND no existing beat`) never trigger even after 5+ consecutive pressure turns.

**Problem B — "Breathe" directives don't clear pending_gm_beat:** When storytell receives a "Breathe" directive, it respects the intent and emits null (no GM beat field in output). However, `pending_gm_beat` is **never cleared** when storytell outputs null. Old pressure beats persist in narrate for 2-3 extra turns after the "Breathe" directive should have taken effect:

| Turn | Directive | Storytell Output | Narrate Sees | What Happened |
|------|-----------|-----------------|--------------|---------------|
| T10  | Breathe   | *(none)*        | PRESSURE/npc_behavior | Old beat from T8/T9 persists; storytell emitted null but pending_gm_beat was never cleared |
| T11  | -         | *(none)*        | pressure/event | Same old beat, now 3-turn persistence — expiration should have fired at turn_no > expires_turn but no new beat overwrote it either (storytell still had nothing to emit) |
| T12  | Breathe   | pressure/event  | PRESSURE/npc_behavior | "Breathe" ignored by storytell; old beats from earlier turns injected into narrate before storytell's own output took effect |
| T13  | Breathe + block_escalate | *(none)* | PRESSURE/event | Both directives ignored — no beat generated but old pressure beat persisted in pending_gm_beat for 2+ extra turns |
| T16  | Breathe   | *(none)*        | PRESSURE/npc_behavior | Same pattern: storytell respected "Breathe" (null output), narrate saw old beat from 2-3 turns ago |

**The timing mismatch:** Storytell generates its GM beat based on previous turn's narration and stores it into `pending_gm_beat`. Narrator reads the *current* `pending_gm_beat` at injection time. At T7, storytell generated opportunity/npc_behavior but narrate saw PRESSURE/npc_behavior — this is because beat 4 (expires_turn=6) expired when turn_no > 6 triggered, clearing pending_gm_beat before storytell stored its output for the *next* cycle. The result: old beats bleed into narration across multiple turns after they should have been cleared.

**Problem C — TTL mechanism doesn't help:** When storytell emits null ("Breathe"), expiration never fires because there's no beat to expire — pending_gm_beat just sits there until a *new* beat overwrites it 2-3 turns later (or 3+ turns pass and turn_no > expires_turn finally triggers). The TTL=2 mechanism was designed for beats that persist across turns, but in practice storytell either replaces them immediately or never generates anything to replace with.

**Likely fix:** Tear out the 2-turn TTL entirely. Replace with a simpler model where pending_gm_beat is cleared when storytell emits null (respecting "Breathe"/"block_escalate") and only persists for 1 turn after generation before auto-clearing. This eliminates the race condition between expiration checks, beat storage timing, and narrate injection points.

---

## 7. Consecutive Pressure Tracking — Not Working as Designed

At `turn.py:1184-1192`, `consecutive_pressure_turns` increments when directive is "Pressure"/"Overwhelm" AND no thread_update was emitted, resetting otherwise. When it reaches `config.consecutive_pressure_threshold` (default 3), it triggers `beat_locked=True`.

**Problem:** The eval shows `consecutive_pressure_turns=0` across all turns in events.jsonl despite T7-T11 having 5 consecutive pressure beats with no thread updates. This suggests either:
- Thread updates *were* emitted each turn (resetting the counter), or
- The directive wasn't consistently "Pressure"/"Overwhelm"

Looking at mechanics output, storytell was emitting `thread_update` on nearly every turn (updating `clerk_murder_coverup` progress), which resets the consecutive pressure counter. This means beat_locked never triggers and floor relief beats never fire — even though 5+ consecutive pressure turns occurred. The mechanism exists but is defeated by thread updates being emitted alongside pressure beats.

**Tentative fix:** Separate "pressure directive" tracking from "thread update presence." Track `consecutive_pressure_beats` (based on storytell's actual gm_beat output) independently of `consecutive_pressure_turns` (based on ruling directives). This way, 5 consecutive pressure GM beats would trigger beat_locked even if thread updates were also emitted.

**Compounding issue:** Even if beat_locked triggers and forces floor relief beats through the beat_locked path at turn.py:1090-1096, those relief beats still need to reach narrate correctly. The TTL=2 mechanism + timing mismatch (Section 6) means even forced null/relief beats may not clear pending_gm_beat in time for narration. Fix Section 6 first before relying on beat_locked as a safety net.

---

## Appendix: Key Code References

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Beat storage/replacement | `turn.py` | 998-1005 | Stores storytell gm_beat into state.meta.pending_gm_beat, TTL=2; never cleared when storytell emits null |
| Beat expiration check | `turn.py` | 750-758 | Clears pending_gm_beat if turn_no > beat_expires_turn — race condition with storytell timing |
| Floor relief beats | `turn.py` | 1090-1096 | Generates breathing_room when beat_locked AND no existing beat; defeated by TTL=2 + thread updates resetting counter |
| Consecutive pressure counter | `turn.py` | 1184-1192 | Tracks consecutive Pressure/Overwhelm directives (defeated by thread updates) |
| Storytell messages build | `extraction.py` | 226-274 | Builds storytell [system, user] — no beat history injected |
| Narrate GM beat injection | `narrate_user.j2` | 95-97 | Injects current pending_gm_beat (type + surface_as only) |
| Storytell diversity instructions | `storytell_system.j2` | 135-184 | 50 lines of GM beat guidance — advisory only, no enforcement |
| NPC roster template | `_npc_roster.j2` | 1-16 | Renders NPCs with last_seen as location name only |
| last_seen stamping | `turn.py` | 1106-1117 | Stamps {turn, location_id, location_name} on compendium update |
| Thread updates application | `turn.py` | 1119-1125 | Applies storytell thread_update (single-string replacement) |
| Prior history accumulation | `turn.py` | 1295-1304 | Appends outcome_summary bullets, capped at 20 entries |
