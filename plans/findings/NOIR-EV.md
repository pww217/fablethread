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

## 6. GM Beat Expiration Mechanism — Broken in Three Ways

**Current behavior:** At `turn.py:998-1005`, TTL is set to `beat_expires_turn = turn_no + 2`. At lines 750-758, expiration checks `turn_no > beat_expires_turn` and clears pending_gm_beat. Both use the same formula (`state.turn + 1`), so a beat generated at Tn expires at Tn+3 narrate setup (`(n+2) + 1 > n+2` is false, `n+3 > n+2` is true). In practice: beat lives for 2 narration turns.

**Problem A — Storytell always replaces before expiry:** Since storytell emits a GM beat on most turns, expiration never fires in practice. The beat is always replaced by a new one before it expires. This creates a state where `pending_gm_beat` always exists, so floor relief beats at lines 1090-1096 (`beat_locked=True AND no existing beat`) never trigger even after 5+ consecutive pressure turns.

**Problem B — "Breathe" directives don't clear pending_gm_beat:** When storytell receives a "Breathe" directive, it respects the intent and emits null (no GM beat field in output). However, `pending_gm_beat` is **never cleared** when storytell outputs null (line 1000 only writes if `_new_beat and _new_beat.type` are both truthy). Old pressure beats persist in narrate for 2-3 extra turns after the "Breathe" directive should have taken effect.

The actual directive + beat chain (corrected, verified from state_snapshot + event data):

| Turn | Pacing Directive | Storytell GM | Narrate Beat Injection | Actual Behavior |
|------|-----------------|-------------|----------------------|-----------------|
| T4   | "" (empty)      | *null*      | REVELATION/npc_behavior | Valid 1-in-4 null cadence. T3's revelation persists as carryover. **Not** a "Breathe" turn. |
| T5   | ""              | pressure/event | REVELATION/npc_behavior | Architectural 1-turn lag. Narrate reads T3's revelation (persisted through T4 null). |
| T6   | ""              | pressure/npc_behavior | PRESSURE/event | Clean — narrate sees T5's pressure/event. |
| T7   | **Breathe**     | opportunity/npc_behavior | PRESSURE/npc_behavior | Architectural 1-turn lag. Narrate reads T6's pressure. T7's opportunity is for T8 narrate. |
| T8   | ""              | revelation/player_discovery | OPPORTUNITY/npc_behavior | Clean — narrate sees T7's opportunity. |
| T9   | ""              | pressure/npc_behavior | REVELATION/player_discovery | Clean — narrate sees T8's revelation. |
| T10  | **Breathe**     | *null*      | PRESSURE/npc_behavior | **[BUG REVEALED]** Storytell respects Breathe (null). T9's pressure persists (expires_turn=11, 10>11? No). Narrate sees stale T9 beat. |
| T11  | ""              | *null*      | PRESSURE/npc_behavior | Same T9 beat persists (11>11? No). **Not** a Breathe turn — storytell chose null independently. |
| T12  | ""              | pressure/event | *(no Beat line)* | T9's beat finally expires (12>11? Yes). **Narrate had zero beat guidance this turn.** |
| T13  | **Breathe**     | *null*      | PRESSURE/event | T12's beat persists (13>14? No). gate=block_escalate blocks thread_add (not beat generation). |
| T14  | Scene Pressure  | pressure/event(?) | PRESSURE/event | T12's beat still persists through T13 null (14>14? No). |
| T15  | Scene Imperative | pressure/npc_behavior | PRESSURE/event | Clean — narrate sees T14's pressure/event. |
| T16  | **Breathe**     | *null*      | PRESSURE/npc_behavior | T15's beat persists (16>17? No). Breathe respected but stale beat continues. |
| T17  | Scene Imperative | pressure/npc_behavior | PRESSURE/npc_behavior | T15's beat persists (17>17? No). T17's new beat will reach T18. |

**Core problem — architectural 1-turn lag, not expiration race:** Narrate runs BEFORE extraction (storytell). At `turn.py:891`, narrate setup reads pending_gm_beat. At lines 965-1005, extraction runs and storytell may replace it. So narrate ALWAYS reads the beat generated by the **previous** turn's storytell, never the current turn's. This is by design (line 744-747 comment), but it means:

- **T7**: Mismatch is NOT about beat 4 expiring. Beat 4 was already overwritten by T5 and T6. The real cause: narrate reads T6's pressure, T7's opportunity is for T8.
- **T10/T13/T16**: "Breathe" is respected by storytell (emits null), but the previous turn's pressure beat is still in pending_gm_beat. Since nothing clears it, narrate sees stale data.

**Problem C — Floor relief beats blocked by `not pending_gm_beat` condition:** At `turn.py:1090`:
```python
if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
```
The `not pending_gm_beat` condition means the floor relief beat is ONLY injected if pending_gm_beat is already None. But since storytell generates a beat every turn (Problem A) OR old beats persist through null turns (Problem B), pending_gm_beat is almost never None. Result: the breathing_room relief path at line 1090-1096 is **structurally unreachable** in the noir save.

**The beat_locked threshold also never triggered** — `consecutive_pressure_turns` was 0 across all 17 turns (see Section 7). Even if it did trigger, the relief beat would still be blocked by the `not pending_gm_beat` condition.

**Likely fix:** Three independent changes:
1. Clear pending_gm_beat when storytell emits null (fixes "Breathe" broken)
2. Remove `not pending_gm_beat` from line 1090 (enables floor relief beats to override stale beats)
3. Tear out the TTL=2 mechanism entirely. Replace with simpler model: beat persists for exactly 1 narration turn, then auto-clears. The 1-turn lag is architectural (narrate runs before extraction) so this gives each beat exactly 1 narration impact.

---

## 7. Consecutive Pressure Tracking — Never Triggered

At `turn.py:1184-1192`, `consecutive_pressure_turns` increments when directive is "Pressure"/"Overwhelm" AND no thread_update was emitted, resetting otherwise. When it reaches `config.consecutive_pressure_threshold` (default 3), it triggers `beat_locked=True`.

**Problem — not just thread updates, but wrong directive basis:** The eval shows `consecutive_pressure_turns=0` across all 17 turns in events.jsonl. This isn't just because thread updates reset it — the bigger issue is that **directives were never "Pressure" or "Overwhelm"** in this save. Directives across all 17 turns were:

| Directive Type | Turns |
|---------------|-------|
| "" (empty) | T1-T6, T8-T9, T11-T12 |
| "Breathe" | T7, T10, T13, T16 |
| "Scene Pressure" | T14 |
| "Scene Imperative" | T15, T17 |

Zero turns with "Pressure" or "Overwhelm" directive. The counter is keyed to RULING directives, not actual BEAT types. Storytell generated 9 pressure-type GM beats (T5, T6, T9, T12, T14, T15, T17 + T8?/T10?) without a single counter increment — because none of those turns had a "Pressure"/"Overwhelm" directive.

**The fundamental design flaw:** `consecutive_pressure_turns` tracks `directive in ("Pressure", "Overwhelm")` — the ruling phase's assessment of scene velocity. But the actual repetitive beats come from storytell's independent generation, not from the directive. The ruling phase never output "Pressure" in this save because the narrative velocity didn't trigger that threshold (momentum stayed moderate, scene age was low, thread urgency varied). Meanwhile storytell generated pressure beats anyway due to the door-knocking scene state.

**Tentative fix:** Change `consecutive_pressure_turns` to track actual beat types emitted by storytell, not ruling directives. Store `gm_beat.type` into `state.meta.consecutive_pressure_beats` at turn.py:1000-1005 when the beat is stored. Use this new counter for beat_locked threshold: `consecutive_pressure_beats >= 3` triggers locked regardless of directive or thread updates.

**Compounding issue:** Even if beat_locked triggers, the floor relief beat at turn.py:1090-1096 is blocked by the `not pending_gm_beat` condition (Section 6, Problem C). Fix both: (1) separate beat type tracking from directive-based tracking, (2) remove `not pending_gm_beat` condition so relief beats can override stale beats.

---

## 8. Solution Effectiveness Analysis

### Proposed Solutions (from NOIR-EV T1-T7 and IDEAS.md)

| Solution | Effectiveness | Why |
|----------|--------------|-----|
| Clear pending_gm_beat when storytell emits null | **HIGH — directly fixes root cause** | Solves Problem B + C. Stale beats stop persisting. Requires 2 lines of code at turn.py:998-1005. Token cost: 0. |
| Remove `not pending_gm_beat` from line 1090 | **HIGH — enables existing mechanism** | Score relief beats can now override stale beats regardless of pending_gm_beat state. 0 tokens, 1 line deletion. |
| Tear out TTL=2 mechanism entirely | **HIGH — eliminates dead code** | Currently serves no purpose (beat always replaced before expiry or persists through null). Replace with "1 narration turn then clear." |
| GM beat last_n_beats history | **MEDIUM — necessary but insufficient alone** | Gives storytell visibility into its own output. But without Fix A+B+C (clear on null, remove block, TTL fix), stale beats still reach narrate even with better storytell output. |
| Track beat type, not directive, for consecutive_pressure | **MEDIUM — fixes wrong basis** | Changes counter from ruling directive to actual GM beat type. Without the `not pending_gm_beat` fix, relief beats still blocked. |
| GM beat expiration countdown in narrate | **LOW — cosmetic, doesn't change beat quality** | Narrate sees TTL remaining but can't act on it differently than current "use it or lose it" behavior. ~5 tokens for no structural improvement. |
| NPC last_seen with turn delta + context | **MEDIUM — improves narrator quality** | Helps but doesn't address root cause. The beat loop is structural, not NPC-continuity-driven. |
| Resolved arcs for storytell | **LOW-MEDIUM — correct asymmetry but low recurrence** | Asymmetry exists but resolved arcs were rare in this save (only 1 at T10). |
| Thread progress as append list | **LOW PRIORITY** | Thread progress wasn't the driver of the beat loop. Separating thread_add from threads. |
| Python-side diversity enforcement | **HIGH but complex** | Hard override for storytell beats. Risk of hallucinogenic override if Python doesn't understand scene state. Better approach: inject corrective guidance first, escalate to override. |
| Narrator feedback loop (reorder narrate/storytell) | **HIGH impact, HIGH complexity** | Fixes the 1-turn lag fundamentally. But requires significant pipeline restructuring. Worth considering for Phase 2 after the simpler fixes prove insufficient. |

### New Low-Cost, High-Impact Solutions

**Gap identified:** None of the proposed solutions (T1-T7, A-H, IDEAS items) address the structural 1-turn lag or the `not pending_gm_beat` blocker. Below are fixes that cost near-zero tokens and require small code changes.

#### Fix 1: Remove `not pending_gm_beat` condition (0 tokens, 1 line)
At `turn.py:1090`, change:
```python
if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
```
To:
```python
if _pc.beat_locked:
```
This makes floor relief beats fire whenever beat_locked triggers, regardless of whether pending_gm_beat already exists. The relief beat overwrites the stale beat entirely. Risk: if beat_locked triggers incorrectly, it could suppress a valid storytell beat — but beat_locked is conservative (only triggers at consecutive_pressure >= 3 or momentum <= floor), so this is safe.

#### Fix 2: Track actual beat types for consecutive_pressure (2 lines, 0 tokens)
At `turn.py:1000-1005`, after storing the beat, add:
```python
if _new_beat and _new_beat.type in ("pressure", "escalation"):
    meta["consecutive_pressure_beats"] = meta.get("consecutive_pressure_beats", 0) + 1
else:
    meta["consecutive_pressure_beats"] = 0
```
Then change beat_locked at rules.py to use `consecutive_pressure_beats` instead of `consecutive_pressure_turns`. This tracks actual GM beat repetition, not ruling directives. Works regardless of thread updates.

#### Fix 3: Pass `pending_gm_beat` to storytell (~5 tokens)
Currently storytell receives ZERO beat information — not even the beat it generated last turn. Add to extraction.py `_storytell_messages()` context: `"current_gm_beat": pending_gm_beat` (the beat pending from last turn). Inject into storytell_user.j2 as a single line: `## Current GM Beat: {type: pressure, surface_as: npc_behavior}`. This gives storytell minimal awareness of what beat is currently shaping narration. Without this, storytell is blind to the beat system entirely.

Cost: ~5 tokens. High leverage because it closes the feedback loop: storytell can now see "the current beat is pressure/npc_behavior" and adjust.

#### Fix 4: Beat origin tag in narrate (~1 token)
At `narrate_user.j2:95-97`, append whether the beat is `[generated]` (fresh from last turn's storytell) or `[carryover]` (persisted from 2+ turns ago, meaning storytell has emitted null since). Python can compute this: if `pending_gm_beat.turn_generated == turn_no - 1`, it's generated; otherwise carryover.

This tells narrate: "the beat you're receiving is stale — don't prioritize it as a fresh creative signal." Narrate can then weight it lower.

Cost: ~1 token (the tag word). Implementation: store `turn_generated` alongside `beat_expires_turn` at line 1003-1004.

#### Fix 5: Directive hint in narrate beat line (~3 tokens)
At `narrate_user.j2:95-97`, change from:
```
**Beat:** PRESSURE — surface as `npc_behavior`
```
To:
```
**Beat:** PRESSURE — surface as `npc_behavior` [dir: Tension]
```
Tells narrate *why* this beat type was chosen — was it from a ruling directive, or from storytell's independent judgment? Narrate can then interpret "this is a Soft Pressure directive beat — escalate but leave room" vs. "this is a storytell-chosen pressure beat — scene state caused this."

Cost: ~3 tokens. Requires passing directive into the template context.

#### Fix 6: Track scene element target per beat (cheaper than categorization)
Instead of the complex categorization proposed in Section 4A, simply add a `scene_context` field to the GM beat struct: e.g., `"scene_context": "door_arrival"` or `"scene_context": "interior_search"`. This is a single string generated by storytell alongside type/surface_as. Python stores it, passes it back in last_n_beats. Storytell can then see `last_n_beats: [{type: pressure, surface_as: event, scene_context: door_arrival}, ...]`.

This replaces the 4-category scene element system with a simpler free-text tag. Storytell generates the tag; Python just passes it through. Zero token cost at generation time (storytell outputs it for free as part of the beat dict). ~3-5 tokens at injection time for the last 5 beats.

### Implementation Order (revised)

1. **Remove `not pending_gm_beat` from line 1090** — 0 tokens, 1 line, enables existing safety net
2. **Clear pending_gm_beat when storytell emits null** — 2 lines, 0 tokens, fixes "Breathe" broken
3. **Track actual beat types for consecutive_pressure** — 2 lines, 0 tokens, makes beat_locked functional
4. **Pass pending_gm_beat to storytell** — ~5 tokens, closes storytell's blindness
5. **Tear out TTL=2 mechanism** — replace with 1-narration auto-clear
6. **Beat origin tag + directive hint in narrate** — ~4 tokens total, improves narrate beat interpretation
7. **last_n_beats history** — ~5-10 tokens, enables storytell diversity instructions
8. **Scene context tag in beats** — ~3-5 tokens, replaces scene element categorization

All of steps 1-6 cost under 10 tokens total and require fewer than 20 lines of Python changes. They fix the "Breathe" broken issue, enable beat_locked, close storytell's beat blindness, and improve narrate's beat interpretation — without any LLM prompt restructuring or pipeline reordering.

---

## Appendix: Key Code References

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Beat storage/replacement | `turn.py` | 998-1005 | Stores storytell gm_beat into state.meta.pending_gm_beat, TTL=2; never cleared when storytell emits null (only writes if `_new_beat and _new_beat.type` are truthy) |
| Beat expiration check | `turn.py` | 750-758 | Clears pending_gm_beat if turn_no > beat_expires_turn. 1-turn architectural lag (narrate runs before extraction) means beats always serve 1 turn late |
| Floor relief beats | `turn.py` | 1090-1096 | Generates breathing_room when `beat_locked AND not pending_gm_beat`. **Both conditions structurally blocked**: (1) beat_locked never triggers — counter tracks directives, not actual beats (Section 7). (2) pending_gm_beat never None — stale beats persist through null turns. |
| Consecutive pressure counter | `turn.py` | 1184-1192 | Tracks when directive in ("Pressure", "Overwhelm") AND no thread_update. Counter was 0 across all 17 turns because directives were never "Pressure"/"Overwhelm" — they were empty, Breathe, Scene Pressure, or Scene Imperative. |
| Narrate/storytell pipeline order | `turn.py` | 891, 965 | Narrate setup (line 891) runs BEFORE extraction pipeline (line 965). This creates the 1-turn architectural lag: narrate always reads the previous turn's storytell beat. |
| Storytell messages build | `extraction.py` | 226-274 | Builds storytell [system, user] — no beat history injected |
| Narrate GM beat injection | `narrate_user.j2` | 95-97 | Injects current pending_gm_beat (type + surface_as only) — no origin tag, no directive hint, no TTL countdown |
| Storytell diversity instructions | `storytell_system.j2` | 135-184 | 50 lines of GM beat guidance — advisory only, no enforcement, no beat history provided |
| NPC roster template | `_npc_roster.j2` | 1-16 | Renders NPCs with last_seen as location name only; no turn delta or context |
| last_seen stamping | `turn.py` | 1106-1117 | Stamps {turn, location_id, location_name} on compendium update |
| Thread updates application | `turn.py` | 1119-1125 | Applies storytell thread_update (single-string replacement) |
| Prior history accumulation | `turn.py` | 1295-1304 | Appends outcome_summary bullets, capped at 20 entries |

(Showing lines 332-364. Use offset=365 to continue.)
| NPC roster template | `_npc_roster.j2` | 1-16 | Renders NPCs with last_seen as location name only |
| last_seen stamping | `turn.py` | 1106-1117 | Stamps {turn, location_id, location_name} on compendium update |
| Thread updates application | `turn.py` | 1119-1125 | Applies storytell thread_update (single-string replacement) |
| Prior history accumulation | `turn.py` | 1295-1304 | Appends outcome_summary bullets, capped at 20 entries |
