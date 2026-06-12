# Eval Rubric — How to Check a Game

Use this rubric when inspecting a game session with `ev.py`. Check one area at a time, not all at once. Focused checks produce more accurate findings.

## Priority Order

### 1. Momentum Lifecycle

**What it validates:** Momentum tracking, floor streaks, band correctness

**What to look for:**
- Roll band maps correctly to momentum delta (crit_success +2, success +1, fail -1, crit_fail -2)
- Values stay within [-3, +3] bounds
- At momentum -2 or below, success gives +2, crit_success gives +3 (floor relief scaling)
- Floor streak: momentum at -3 for 3+ consecutive turns without relief is a failure
- Momentum delta in events matches the computed delta from band mapping

**Commands:**
```bash
ev.py check 5 momentum_lifecycle --save-dir saves/my-game
ev.py trace pc.momentum saves/my-game/events.jsonl          # trajectory
ev.py mechanics 12 --dice saves/my-game/events.jsonl        # ruling + band context
```

**Red flags:**
- Delta doesn't match band mapping (e.g., success giving +1 at floor when it should be +2)
- Momentum drops below -3 or exceeds +3
- 3+ consecutive turns at -3 with no `breathing_room` beat injected

---

### 2. GM Beat Lifecycle

**What it validates:** GM beat type transitions, pressure compliance, floor relief

**What to look for:**
- `pending_gm_beat` from one turn is consumed or updated in the next
- When storyteller emits a GM beat, state's `pending_gm_beat` matches its type
- `beat_locked` prevents pressure stacking after fail bands
- Floor relief: when `beat_locked` is true AND pending beat is None or pressure-type AND beat_locked was NOT triggered by momentum floor, `breathing_room` must be injected (intentional: momentum crisis requires escalation, not breathing room — MB-3)
- Beat TTL: storyteller-emitted beats expire after 2 turns (`beat_expires_turn = turn_no + 2`), floor relief beats also get 2 turns (architecture docs claim 3, but code uses 2)
- Beat type variety: no more than 2 consecutive same-type beats; at least 1 in 3 beats should be non-pressure

**Commands:**
```bash
ev.py check 5 gm_beat_lifecycle --save-dir saves/my-game
ev.py trace compendium.meta.pending_gm_beat saves/my-game/events.jsonl
ev.py mechanics 8 --pacing saves/my-game/events.jsonl       # beat + pacing context
```

**Red flags:**
- Pending beat persists across 3+ turns without consumption
- `beat_locked` at momentum floor without `breathing_room` injection (TICK-7)
- 3+ consecutive pressure/escalation/complication beats

---

### 3. Thread Lifecycle & Arc Goals

**What it validates:** Thread add/update correctness, goal alignment

**What to look for:**
- `thread_add` entries appear in next turn's `state_snapshot.arc.threads`
- `thread_update` IDs reference existing threads in `state.arc.threads`
- `goal_update` string from storyteller matches `arc.visible_goal` in state
- Thread progression is meaningful (not tiny increments like 0.50, 0.53, 0.56)
- No orphan threads in state that no sanitizer event ever touches

**Commands:**
```bash
ev.py check 5 thread_lifecycle arc_goal_updates --save-dir saves/my-game
ev.py trace arc.threads saves/my-game/events.jsonl          # thread state over time
ev.py deltas 7 saves/my-game/events.jsonl                   # find thread mutations
```

**Red flags:**
- `thread_add` emitted but not in next turn's state
- `thread_update` references non-existent thread ID
- Goal updates don't match visible_goal in state
- Thread progress stuck at tiny increments (LLM dedup rejection pattern)

---

### 4. Pacing Directives

**What it validates:** Consecutive pressure tracking, outcome hints, beat variety, directive rendering

**What to look for:**
- Consecutive pressure counter increments on pressure/escalation/complication beats, resets on others
- `outcome_hint` rendered in narrator prompt
- Pacing directive rendered in storyteller prompt
- Removed directives ("location pressure", "location imperative", "combat fatigue") not lingering
- Scene Imperative fires at 4 effective turns (3 actual scene turns, 0 if combat tags present)
- Beat type variety: no single type exceeds 60% of all beats (requires 3+ beats)
- `surface_as` consistency: consecutive same-type beats don't flip between "ambient" and "environmental" without directive change

**Commands:**
```bash
ev.py check 5 pacing_directives --save-dir saves/my-game
ev.py trace pacing_context saves/my-game/events.jsonl       # directive state over time
ev.py mechanics 10 --pacing saves/my-game/events.jsonl      # beat + directive context
ev.py beats saves/my-game/events.jsonl                      # beat type + surface + locked
ev.py momentum-check saves/my-game/events.jsonl             # momentum + band + delta
```

> **Note:** `outcome_hint` is rendered in both `narrate_prompt.rendered_user` and `storytell.rendered_user` (in extraction). The `narrate_prompt` is saved at the event level, not in the `extraction` dict. To verify `pacing_context` rendering, check `storytell.rendered_user` in extraction events or `narrate_prompt.rendered_user` at the event level.

**Red flags:**
- Consecutive pressure counter doesn't match actual beat types
- `outcome_hint` missing from narrator prompt
- Single beat type exceeds 60% of total beats
- Removed directives still rendered in prompts

---

### 5. Inventory & Conditions

**What it validates:** Inventory balance, condition lifecycle, cap enforcement

**What to look for:**
- No negative inventory amounts in `state_snapshot.inventory`
- No overdraw: removing items that don't exist or have zero quantity
- Condition IDs appear in ruling's `reason` text (lowercase comparison)
- No duplicate condition IDs in a single turn
- Condition count respects cap (`PC_CONDITIONS_MAX` = 5)
- Condition removals reference conditions that existed in previous turn's state

**Commands:**
```bash
ev.py check 5 inventory_integrity conditions_lifecycle --save-dir saves/my-game
ev.py state --save-dir saves/my-game --format inventory     # current inventory
ev.py state --save-dir saves/my-game --format conditions    # current conditions
ev.py deltas 11 saves/my-game/events.jsonl                  # find inventory/condition changes
```

**Red flags:**
- Negative inventory amounts
- Removing items not in previous turn's inventory
- More than 5 conditions active simultaneously
- Condition ID in extraction not found in ruling reason text

---

### 6. NPC Presence & Compendium

**What it validates:** NPC lifecycle, compendium consistency, no ghosting

**What to look for:**
- NPCs introduced in scene stay present (no sudden disappearance)
- `recently_left` scene tags don't appear in current state
- `JUST_LEFT` tag doesn't appear in narrator prompt for active NPCs
- Compendium updates (`applied.compendium_npc_update`) track NPC state changes correctly
- NPC notes evolve logically across turns

**Commands:**
```bash
ev.py check 5 npc_presence --save-dir saves/my-game
ev.py diff 3 10 --section npcs saves/my-game/events.jsonl   # NPC changes between turns
ev.py deltas 8 saves/my-game/events.jsonl                   # find NPC mutations
ev.py trace compendium.npcs.<name>.notes --show-unchanged saves/my-game/events.jsonl
```

**Red flags:**
- NPC present in turn N, absent in turn N+1 without `recently_left` or `JUST_LEFT`
- Compendium updates not reflected in next turn's state
- NPC notes regressing or contradicting previous turns

---

### 7. Location & Scene Transitions

**What it validates:** Location continuity, scene tag evolution, no teleporting

**What to look for:**
- When `applied.location_change` is emitted, post-turn location ID differs from previous turn
- Scene tags evolve logically (no sudden scene jumps without transition)
- Environmental shifts tracked in scene state
- Location descriptions match scene context

**Commands:**
```bash
ev.py check 5 location_change --save-dir saves/my-game
ev.py state --save-dir saves/my-game --format location      # current location
ev.py state --save-dir saves/my-game --format scene         # current scene tags
ev.py diff 5 10 --section location saves/my-game/events.jsonl
```

**Red flags:**
- Location changes without transition narration
- Scene tags jumping between unrelated locations
- `applied.location_change` present but location ID unchanged from previous turn

**Known bug (TICK-26):** `applied.location_change` doesn't exist in events — field is `applied.location_description`. Checker returns "required field not found" for every turn.

---

### 8. Sanitizer Lifecycle

**What it validates:** Thread sanitization correctness, no orphan threads, no goal noops

**What to look for:**
- `threads_updated`/`resolved` IDs exist in `state.arc.threads` at the sanitizer's turn (NOT END state — use state snapshots from turn events)
- `threads_added` IDs don't conflict with existing threads at the sanitizer's turn
- No `goal_changed` noops (goal set to same value)
- Orphan threads: threads in state never referenced by any sanitizer event
- Sanitizer events exist in events.jsonl (`kind: "sanitizer"`)

> **Note:** The engine never emits `threads_removed` — it moves threads to `completed_threads[]` instead. The `sanitizer_lifecycle` checker was fixed to not require this field. When checking thread existence, use the state at the sanitizer's turn (from `state_snapshot` in turn events), not the END state, to avoid false positives for resolved threads.

**Commands:**
```bash
ev.py check 5 sanitizer_lifecycle --save-dir saves/my-game
ev.py turn 12 saves/my-game/events.jsonl                    # full dump, look for sanitizer events
ev.py goals saves/my-game/events.jsonl                      # goal changes over time
```

**Red flags:**
- Sanitizer references thread ID not in state
- Goal changed to same value (noop)
- Threads in state with no sanitizer event ever touching them
- No sanitizer events at all (sanitizer not running)

---

### 9. LLM-Based Quality Checks (optional, slower)

**What they validate:** Narrative alignment, beat consequences, extraction fidelity

**What to look for:**
- **directive_tone_match:** Narration tone aligns with roll band (success→positive, fail→tense, crit_fail→severe)
- **beat_narrative_chain:** GM beat produces observable narrative consequence in current and next turn narration (pressure→urgency, complication→obstacle, escalation→raised stakes)
- **state_fidelity:** State extraction matches what narration describes — no missing or unsupported changes

**Commands:**
```bash
ev.py check 5 directive_tone_match --llm --save-dir saves/my-game
ev.py check 5 beat_narrative_chain --llm --save-dir saves/my-game
ev.py check 5 state_fidelity --llm --save-dir saves/my-game
```

**Red flags:**
- Success narration reads like a failure (tone mismatch)
- GM beat emitted but no narrative trace of it in subsequent turns
- Narration describes state changes not captured in extraction (or vice versa)

---

## Quick Reference — Commands by Goal

| If you want... | Command |
|---|---|
| Momentum trajectory | `ev.py trace pc.momentum saves/my-game/events.jsonl` |
| Beat type over time | `ev.py trace compendium.meta.pending_gm_beat saves/my-game/events.jsonl` |
| Thread mutations | `ev.py deltas <N> saves/my-game/events.jsonl` |
| NPC changes between turns | `ev.py diff 3 10 --section npcs saves/my-game/events.jsonl` |
| Inventory snapshot | `ev.py state --save-dir saves/my-game --format inventory` |
| Full mechanics breakdown | `ev.py mechanics 12 --pacing --dice saves/my-game/events.jsonl` |
| All checkers on all turns | `ev.py check --all --save-dir saves/my-game` |
| Single checker on single turn | `ev.py check 5 momentum_lifecycle --save-dir saves/my-game` |
