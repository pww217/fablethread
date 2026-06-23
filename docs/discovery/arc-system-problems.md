# Arc System — Discovery

> **Related:**
> - [01-Primitives](../design/01-primitives.md) — Shared building blocks
> - [02-Arc System Redesign](../design/02-arc-system-redesign.md)
> - [03-Seed Worldbuilding Redesign](../design/03-seed-worldbuilding-redesign.md)
>
> **Status:** Evidence collected, decisions recorded, awaiting design phase

Problems identified through eval analysis (outer-rim saves, noir/ww2/piracy runs), prompt inspection, code review, and prompt evolution tracing across 7 eval cycles (June 17–22, 2026).

---

## Eval Data Trace

### Eval Cycle Timeline

| Date | Commits | Packs | Turns | Score | Arc/Thread Notes |
|------|---------|-------|-------|-------|------------------|
| Jun 17 | `07266252` | 5 | 25 | 95.7% avg | Thread resolution: Piracy 71.4%, WW2 37.5%, Noir 30%, Space 30%, Zombie 25%. Thread ID hallucination (Space T25). Goal churn (WW2 4 changes in 4 turns). |
| Jun 18 | `255992b` | 5 | 30 | 99.2% | Goal update no-op (piracy T12). Sanitizer timing fix for thread/arc resolution checkers. Added `chapter_end` field. |
| Jun 20 (1) | `e399818` | 5 | 30 | 98.5% | `arc_resolve: {}` empty object (piracy T8). `goal_update_validity` fail (noir T30). Thread dormant/active swap. Arc resolution frequency target set to 8-15 turns. |
| Jun 20 (2) | `69faea9` | 5 | 30 | 100% | arc_resolve prompt fix reduced piracy retries 80% (5→1). All deterministic checkers pass. |
| Jun 21 | `47ff6261` | 3 | 20 | 92-96% | Arc resolve too fast (WW2 T4, T6) — same visible_goal. ArcThread.type no coercion validator. |
| Jun 21 | outer-rim | 1 | 34 | N/A | Arc resolution far too common: T4, T6, T15, T31 — all same visible_goal. chapter_end has no behavioral effect. Thread proliferation: 14 created, 13 pending. |
| Jun 22 | `dabe3b81` | 5 | 25 | 92-96% | **Zero arc resolutions across all 5 packs** (105 threads, 0 arc_resolves). Thread resolution rates collapsed: Noir 5.9%, Space 26.7%, Piracy 12.5%, Zombie 18.8%, WW2 16.7%. |
| Jun 22 | `2b62d1d` | 2 | 25 | 100% | **Eval Cycle 2 (zombie aggressive, noir opportunist).** Confirms all prior findings. New: thread resolution events ≠ unique threads, NPC roster limit, convergence starvation, ruling system "routine" path too generous. |

### Thread Resolution Rate Regression

| Pack | Jun 17 | Jun 22 | Change |
|------|--------|--------|--------|
| Golden Piracy | 71.4% (5/7) | 12.5% (3/24) | -58.9pp |
| Space Western | 30% (3/10) | 26.7% (4/15) | -3.3pp |
| Noir | 30% (3/10) | 5.9% (1/17) | -24.1pp |
| Zombie | 25% (3/12) | 18.8% (3/16) | -6.2pp |
| WW2 | 37.5% (3/8) | 16.7% (3/18) | -20.8pp |

### Eval Cycle 1 (Jun 22) — Full Arc/Thread Findings

**Issue #10: No Arc Resolutions**
Zero arc resolutions across all 5 packs. Despite 105 total threads created, none are ever resolved via `arc_resolution`. Threads are only updated or left pending. This means the game never closes its narrative arcs.

**Issue #5: Thread Resolution Rate**
Threads accumulate but rarely get resolved:

| Pack | Created | Resolved | Rate |
|------|---------|----------|------|
| noir | 17 | 1 | 5.9% |
| space-western | 15 | 4 | 26.7% |
| golden-piracy | 24 | 3 | 12.5% |
| zombie | 16 | 3 | 18.8% |
| ww2 | 18 | 3 | 16.7% |

### Eval Cycle 2 (Jun 22, later) — Additional Findings

Eval Cycle 2 ran 2 packs (zombie aggressive, noir opportunist) × 25 turns. Both runs passed all 25 deterministic checkers at 100%. LLM-based checkers were skipped.

This eval **confirmed all prior findings** and added new ones:

**Storyteller NPC roster missing presence tags.** The storyteller's user prompt rendered empty `[]` brackets instead of `[PRESENT]`, `[KNOWN]`, etc. because `build_npc_roster(slim=True)` omitted the `presence` field while `_npc_roster.j2` unconditionally renders `[{{ n.presence | upper }}]`. This means the storyteller cannot see NPC presence context in its prompt. **Fixed in commit `b36940d`** — added `presence` to the slim-mode dict in `npc_roster.py:77`.

**Thread resolution events ≠ unique threads.** The storyteller generates `thread_resolve` events for threads that no longer exist in the active thread list. The raw numbers show ~50% resolved, but these are events, not unique threads. The same thread ID appears in multiple resolve entries because the storyteller keeps trying to resolve threads that were already moved to `completed_threads` by a prior arc_resolve. The sanitizer's dedup catches them, but the LLM keeps trying.

**Convergence starvation in noir.** T20-T22 in noir have convergence score = 0 across all 5 components: no urgent threads, no threat threads, scene age = 0, no beat streak (null beats), no dice weight (no rolls). The opportunist persona's stealth-heavy play style starves convergence. There's no mechanism to recover from a zero-convergence state. The convergence threshold was lowered from 3 to 2 in commit `eed5878`, but this alone isn't sufficient when all 5 components are 0.

**Ruling system "routine" path too generous.** The opportunist persona exploits the ruling system's "routine" path by choosing stealth actions that the ruling system classifies as "no check required: routine movement." This creates a gameplay loop where the opportunist avoids rolls entirely, which starves convergence (no dice_weight component) and creates dead spots.

**Thread TTL disconnect.** Narrator filters `completed_threads` by TTL (3 turns in `narrate.py:128-136`), meaning completed threads disappear from the narrator's context after 3 turns. But the storyteller in the next turn still has access to them via `all_threads` in the prompt context. This creates a disconnect: the narrator "forgets" completed threads but the storyteller doesn't.

**Thread lifecycle in arc_resolve.** When `arc_resolve` fires, it drops threads via `drop_threads[]` and optionally adds `new_threads[]`. But the storyteller often resolves arcs without explicitly dropping threads, leaving them in limbo — neither in `threads` nor `completed_threads`. The sanitizer's dedup catches some, but orphaned threads accumulate.

**Thread dedup/rejection.** Both runs show thread progress dedup rejections (0.72-0.75 overlap ratio), meaning the storyteller generates thread updates that are nearly identical to previous entries. The sanitizer rejects them, but the LLM keeps trying.

**Null beat rate 34-57%.** Both runs show significant null beat rates: zombie ~40%, noir ~52%. The storyteller's prompt doesn't enforce beat generation. The `_nullify_invalid_gm_beat` validator sets `gm_beat = None` when the LLM emits an invalid type or omits the beat entirely. No checker enforces a null-beat threshold.

**Arc resolution too frequent.** Both runs show arc resolves every 1-5 turns (target: 8-15). The storyteller resolves arcs on almost every CLIMAX turn, creating "goal churn" where the player's visible goal changes constantly.

**Goal update rate near-zero.** Both runs show 93-96% null `goal_update` in storyteller output. The arc's `visible_goal` changes via `arc_resolve` (not `goal_update`), meaning the storyteller uses the arc_resolve path but not providing incremental goal updates between arc resolutions.

**Thread urgency distribution skewed.** Both runs show very few urgent threads relative to total threads. The convergence score depends on `urgent_thread` component (+1), but most threads are "normal" urgency.

**Thread type distribution skewed.** Both runs show a heavy skew toward "threat" type threads. The storyteller generates threats but rarely opportunities, complications, or revelations.

**Thread add rate low.** Both runs show 59-64% null `thread_add` in storyteller output. The storyteller generates thread updates more often than new threads.

**Curtain call turn-count based, not narrative-based.** T25 in noir is in CLIMAX with curtain_call="" (not forced, not active), meaning the storyteller wasn't prompted to resolve threads. Curtain call fires when `climax_turn_count >= climax_turn_limit - 1` (forced) or `climax_turn_count == 1` (active) — purely mechanical, doesn't check whether the narrative has reached a natural conclusion point.

**Phase machine too rigid.** The phase machine enforces a strict state machine (SETUP→RISING→CLIMAX→RESOLUTION→BREATHER→RISING), creating a "conveyor belt" pattern where the game moves through phases mechanically rather than narratively.

**Spiral detection not used in convergence.** `detect_spiral()` detects death spirals (consecutive hard rolls or high ratio of hard rolls). This feeds into `spiral_detected` in PacingContext, which modifies allowed beat types (removes pressure beats), but it doesn't directly affect convergence. A player in a death spiral gets fewer pressure beats, which reduces beat_streak, which reduces convergence — creating a feedback loop where bad rolls make it harder to reach CLIMAX.

**Beat driver always "motivation".** Both runs show that the vast majority of beats use `driver="motivation"`. This creates a narrow narrative palette where all beats feel the same.

**Beat streak component fragile.** The `beat_streak` component requires ≥60% of last 5 beats to be pressure types. With null beats at 34-57%, the window is often too small to establish a streak. When the storyteller generates a null beat, the streak resets, which reduces convergence.

**Beat expiration turn-based, not narrative-based.** `beat_expires_turn` in GMBeat sets a turn number after which the beat expires. This is mechanical — the beat disappears regardless of whether the narrative has resolved it.

**NPC presence enum incomplete.** `NpcPresence` enum has PRESENT, NEARBY, KNOWN, DEPARTED. But the engine also uses "archived" as a terminal state (turn_state.py:670, prompt_context.py:30). The "archived" state is not in the enum, which is a design inconsistency.

**NPC roster limited to 10.** `_build_npc_roster()` in prompt_context.py:25-53 returns `entries[:10]`. If there are more than 10 NPCs in the compendium, only the first 10 (by presence priority) are shown to the LLM. This can cause NPCs to be silently dropped from the storyteller's context.

**NPC dialogue not tracked.** The NPC model has no `dialogue` or `speech_history` field. NPCs are described in the roster but don't have memorable dialogue patterns. The storyteller generates NPC dialogue in narration, but it's not tracked in state.

**NPC personality assignment automatic but inconsistent.** `apply_npc_scene_management()` automatically assigns personality to named NPCs that lack one, using `assign_personality()` from personality.py. This means NPCs get personalities based on their motivation/fear, but the assignment is automatic and not guided by the storyteller.

**Group NPC resolution complex but fragile.** The engine has extensive logic for group NPC resolution (quantity stripping, alias mapping, deduplication). If the LLM generates inconsistent IDs (e.g., "militia_guards" on one turn, "two_militia_guards" on another), the deduplication may not work correctly.

**Dice distribution reflects persona but lacks variety in noir.** Both runs show heavy stat skew: zombie = 78.9% strength rolls, noir = 100% dexterity rolls. This is correct behavior but suggests the opportunist persona's "use whatever works" approach converges on a single skill.

**Storyteller prompt too information-dense.** Both runs show high token usage in storyteller extraction (4552 tokens in, 178 tokens out for T25 noir). The storyteller prompt is complex, with thread context, NPC roster, beat context, and pacing directives. The low output token count suggests the LLM is generating concise but sparse storyteller output, which contributes to null beats and null thread_adds.

**Convergence threshold change has mixed results.** Lowering from 3 to 2 helped the aggressive persona (convergence consistently ≥3 in RISING, natural CLIMAX transitions) but didn't solve the opportunist's dead-spot problem. The threshold change alone isn't sufficient when all 5 components are 0.

### Prompt Evolution Trace

Changes to arc/thread-related prompts between eval periods:

**Jun 17 → Jun 18 (07266252 → 185d118)**
- `_arc.j2`: Added thread IDs to completed threads list (fixes thread ID hallucination)
- `storytell_system.j2`: Added `chapter_end` field, clarified `thread_resolve` is the ONLY way to drop threads, added CRITICAL warning against using `arc_resolve` to drop threads, simplified beat types
- `storytell_user.j2`: Added `⚠️ REMINDER` for allowed beat types
- **Result:** Checker bugs fixed, thread ID hallucination fixed, 100% pass on some packs

**Jun 18 → Jun 20 (185d118 → e399818)**
- `generate_seed_system.j2`: **Major arc changes** — replaced `active` with `dormant`, added thread type requirements (at least one threat, at least one non-threat), added dormant thread guidance
- `narrate_system.j2`: Added `BACKGROUND` urgency label, thread type display
- `narrate_user.j2`: **Massive rewrite** — removed location/conditions/inventory from user prompt
- `sanitize_thread.j2`: Replaced `active` with `dormant`, added type/dormant update guidance, added abandonment criteria
- **Result:** 100% pass across all 5 packs (130/130)

**Jun 20 → Jun 21 (e399818 → 47ff6261)**
- `storytell_system.j2`: **Major beat overhaul** — replaced `surface_as` with `effect`+`npc_id`+`driver`, added scene-driven beat generation (candidate_npcs mapping), added beat flavor by type, tightened arc_resolve (no empty objects, no-op visible_goal), tightened goal_update
- `extract_scene_system.j2`: Added `candidate_npcs` extraction (motivation/fear/leverage/bond with effect)
- **Result:** 92-96% pass — arc issues resurface (zero arc resolutions, thread accumulation)

**Jun 21 → HEAD (47ff6261 → 2b62d1d)**
- `ruling_system.j2`: Minor wording tweaks
- **Result:** Same issues persist

**Key prompt changes correlating with arc/thread regression:**
1. **June 18 dormant/active swap + type requirements** — Added thread type enforcement in seed prompt, replaced active→dormant across all prompts. Thread resolution rates still dropped.
2. **June 21 beat overhaul (surface_as → effect)** — Removed `surface_as` from beat system, replaced with `effect`+`npc_id`+`driver`. Storytell prompt became much more complex with candidate_npcs mapping, beat flavor tables, and NPC-driven beats.
3. **June 21 tightened arc_resolve guidance** — Added "no empty objects", "no no-op visible_goal", "compare against current visible_goal". LLM still doesn't resolve arcs — it just omits arc_resolve entirely.
4. **Narrate user prompt massive simplification** (June 18) — Removed location/conditions/inventory from user prompt. May have reduced LLM's awareness of arc state when making decisions.

**Key insight:** Prompt patches between Jun 17 and Jun 22 made thread resolution worse, not better. More guidance + more fields + more complexity = worse LLM performance. The fix is fewer fields, clearer separation, and engine-driven lifecycle management.

---

## Structural Problems

### 1. Arc Resolution Misuse — "Chapter Reset" Pattern

**Symptom:** Storyteller fires `arc_resolve` every 4–16 turns, but keeps the same `visible_goal` every time.

**Evidence (outer-rim, 34 turns, 4 arc_resolves):**

| Turn | visible_goal | drop_threads | new_threads |
|------|-------------|--------------|-------------|
| 4 | "Establish a reliable smuggling route..." | distress_signal_discovery | saloon_intelligence_gathering |
| 6 | Same | saloon_intelligence_gathering | guild_confrontation |
| 15 | Same | distress_signal_mystery, chemical_hazard_obstruction, immediate_combat_threat | guild_arrest_escalation |
| 31 | Same | docking_bay_chaos, security_response_escalation | sublevel_pursuit |

**Root cause:** Storyteller treats `arc_resolve` as a "new chapter/scene" marker, not an arc-ending event. The prompt (line 72 of `storytell_system.j2`) says:
> WRONG: `arc_resolve` with unchanged `visible_goal` (no-op). RIGHT: `arc_resolve` introduces a new goal or `chapter_end: true` keeps the current one.

But the storyteller does the opposite — unchanged goal + thread drops + new threads.

**Consequence:**
- `completed_threads` reset to `[]` on every arc_resolve (turn_state.py:268) — loses all completed thread history
- New arc entry created each time, stored in `resolved_arcs` (TTL-filtered, 3 turns)
- Successor arc has less context than parent arc
- Arc frequency warning fires (turn_state.py:226-233) but only logs, doesn't prevent
- Outer-rim: 4 arc_resolves in 34 turns (avg 8.5 turns), but all are no-op goals — effectively zero real arc progress

**Design decision:** `arc_resolve` should only do arc-ending. Thread operations should be independent fields (`thread_resolve`, `thread_add`) that the engine applies regardless of arc state. The prompt patch (chapter_end) is removed — see [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

### 2. `arc_resolve` vs `chapter_end: true` — Indistinguishable Semantics

**Problem:** The prompt gives two mechanisms for "chapter ends but goal stays the same":
- `arc_resolve` with unchanged visible_goal (explicitly marked WRONG in prompt)
- `chapter_end: true` (explicitly marked RIGHT in prompt)

The storyteller consistently picks the WRONG one. The schema shows both fields in the same JSON object, making them feel like options rather than mutually exclusive signals.

**Schema (storytell_system.j2:14):**
```json
"arc_resolve": {"resolution": "...", "visible_goal": "...", "goal_context": "...", "drop_threads": ["..."], "new_threads": [...]},
"goal_update": "...",
"chapter_end": true,
```

All three are top-level keys in the same object. The storyteller interprets `arc_resolve` as "something happened, here's the result" and `chapter_end` as "but the arc continues." This is the opposite of the intended semantics.

**Design decision:** `chapter_end` is removed entirely. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#chapter_end).

### 7. Arc Model Schema — Confusing Structure

**Problem:** The `ArcResolution` schema mixes concerns:
- `resolution` — prose summary of what happened
- `visible_goal` — the new arc goal (required, even if unchanged)
- `goal_context` — UI-only context (required, even though LLM never sees it)
- `drop_threads` — thread cleanup (should use `thread_resolve`)
- `new_threads` — thread creation (should use `thread_add`)

**Consequence:** The storyteller sees one big JSON object with everything in it and treats it as "here's everything that happened this turn." This is the opposite of the intended design — each field should be independent.

**Schema (state.py:173-178):**
```python
class ArcResolution(BaseModel):
    resolution: str
    visible_goal: str
    goal_context: str
    drop_threads: list[str]
    new_threads: list[ArcThread]
```

**Design decision:** Decouple `arc_resolve` from thread operations. `arc_resolve` should only contain arc-ending fields. Thread operations become independent top-level fields. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

### 11. Goal Update — Mid-Arc Pivot vs Arc Resolve Confusion

**Problem:** Two mechanisms for changing the arc goal:
- `goal_update` (mid-arc pivot) — direct string assignment to `state["arc"]["visible_goal"]`
- `arc_resolve.visible_goal` (chapter ending) — replaces entire arc

The storyteller conflates these. It uses `arc_resolve` with unchanged visible_goal (which should use `goal_update` or nothing), and it uses `goal_update` for no-ops (which the prompt explicitly forbids).

**Prompt (storytell_system.j2:76):**
> **CRITICAL: Compare your proposed `goal_update` against the current `visible_goal`. If they are identical or nearly identical (same meaning, different wording), do NOT emit `goal_update`.**

But the goals checker (outer-rim) shows goal_update firing on turns 4, 6, 15, 31 — all with the same goal. These are arc_resolves, not goal_updates.

**Design decision:** Rename `visible_goal` to something that signals "medium-to-long-term objective" (not a one-turn thing). See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

---

## Naming and Semantics Problems

### 4. Thread `progress` → `major_updates` (Renamed)

**Problem:** The field is called `progress` but it's really a journal entry / log. The name implies "this needs to be updated every turn" — which is exactly what the storyteller does.

**Prompt (storytell_system.j2):**
> `thread_update`: Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation.

**Consequence:** Storyteller adds progress entries every turn, even when instructed "Default: emit nothing." The progress deduplication (70% text-similarity check) catches obvious rephrasings but not semantic ones.

**Current progress kinds:** `advancement`, `setback`, `shift` — these are vague and don't help the storyteller decide when to update. They're more like metadata tags than meaningful classifications.

**Design decision:** Renamed to `major_updates`. Signals "only when something worth noting happens." The word "major" does the heavy lifting.

### 5. Thread Urgency — Binary, Not Graduated

**Problem:** Urgency is `background | normal | urgent` — a 3-state system that's too coarse. The prompt says:
- `background` → "Faded but recoverable. Set `dormant: true`."
- `normal` → "Active and relevant but not pressing right now."
- `urgent` → "Immediate. Something happening now or about to escalate."

**Consequence:** The storyteller oscillates between `normal` and `urgent` with little nuance. There's no "cooling down" or "building up" — just snap transitions. This creates artificial urgency inflation where everything becomes `urgent` quickly.

**Outer-rim evidence:** 21 threads created, 19 still pending after 34 turns. Only 2 resolved (9.5%). Threads accumulate and never decay naturally.

**Design decision:** Auto-dormant threshold moves from 4 to 8 turns. Urgency decay (stepwise demotion) at 8 turns means threads can develop before decaying. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

### 12. Thread Progress Kinds — Vague Classifications (Undecided)

**Problem:** `progress_kind` is `advancement | setback | shift` — vague categories that don't help the storyteller decide when to update.

**Consequence:** Everything gets marked as `advancement` because the storyteller interprets "something happened" as "progress." The categories are too broad to be useful.

**Design decisions considered:**
- (a) Drop entirely — simplest path
- (b) Tie to mechanics — numeric ticker (advancement ticks up, setback ticks down, threshold triggers hints to narrator)
- (c) Replace with signal categories — e.g., "near_resolution", "stalled", "escalating"

**Status:** Undecided. Needs more thought. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#open-questions).

---

## Dead State and Required Noise

### 3. `goal_context` → `arc_origin` (Renamed)

**Problem:** `goal_context` is:
- UI-only (sidebar tooltip, resolved arc context in `_state_left.html`)
- Never rendered in narrator or storyteller prompts
- Required by `ArcResolution` schema (Pydantic validation)
- Validated by `arc_resolution_validity` checker (non-empty string) — **this checker must be removed or updated when goal_context is removed**
- Set by seed (initial), updated by storyteller `arc_resolve` (on chapter end), updated by sanitizer `goal_update` (if dict format)

**Consequence:** Storyteller must generate `goal_context` every time it emits `arc_resolve` — even though it has no mechanical purpose. This wastes LLM context/tokens and creates "emotional whiplash" — the storyteller generates a brand new context string with no connection to the previous arc's context (it never sees the old context).

**Design decision:** `goal_context` is removed entirely. Replaced by `arc_origin` (2–3 sentences, past tense, "how did the PC end up here?"). Placement: UI (sidebar tooltip) and seed opening narration only. NOT in narrate/storytell prompts. See [03-Seed Worldbuilding Redesign](./03-seed-worldbuilding-redesign.md#new-field-arcarc_origin) and [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

### 13. Arc Thread Urgency Set Turn — Deprecated

**Problem:** `ArcThread.urgency_set_turn` (state.py:38) exists but is never read or written by the engine. It's dead state.

**Design decision:** Deprecated. Delete.

### 15. Thread Resolution — `promote_to_world_state` — Replaced

**Problem:** `thread_resolve.promote_to_world_state` (bool) exists in the schema but is never read by the engine. It's dead state.

**Design decision:** Replaced by two-step candidate system: storyteller flags `world_state_candidate`, sanitizer confirms every 5 turns. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

### 14. Sanitizer and Storyteller — Different `goal_update` Formats

**Problem:**
- Storyteller: `goal_update: "string"` (direct string assignment)
- Sanitizer: `goal_update: {visible_goal: str, goal_context: str}` (dict format)

**Consequence:** Format mismatch. The `arc_goal_updates` checker compares storyteller's string `goal_update` against `state.visible_goal` — this works for storyteller but the sanitizer's dict format is a separate code path. Previously filed (roadmap/archive/goal-update-format-mismatch-storyteller-emits.md).

**Design decision:** When `goal_context` is removed and replaced with `arc_origin` (UI-only), the sanitizer's dict format for `goal_update` becomes unnecessary. Both should use string format.

---

## Engine Behavior Problems

### 6. Thread Add — No Conceptual Overlap Detection

**Problem:** The prompt says "scan all active AND latent threads for conceptual overlap" before emitting `thread_add`. But the storyteller consistently creates new threads for tensions that are already tracked under different IDs.

**Consequence:** Thread proliferation. Outer-rim has 21 threads created in 34 turns, with 19 still pending. The hard cap of 5 forces the storyteller to either drop threads (via `arc_resolve` with `drop_threads`) or create new ones, both of which are destructive.

### 9. Arc Resolution Frequency — Warning Only, No Enforcement

**Problem:** `turn_state.py:226-233` warns if arc_resolve fires < 5 turns since last resolution (target: 8-15), but doesn't prevent it.

**Consequence:** The storyteller fires arc_resolve whenever it wants. The warning is a log message only — no mechanical enforcement.

### 10. Completed Threads History — Lost on Every Arc Resolve

**Problem:** `completed_threads` is reset to `[]` on every arc_resolve (turn_state.py:268).

**Consequence:** Successor arc has zero context about what was previously resolved. The storyteller has to re-learn from `resolved_arcs` (TTL-filtered, 3 turns) and `completed_threads` (which is now empty). This means the storyteller has less context in the successor arc than in the parent arc.

### 6 (cont.) Thread Culling — Abandonment Without Narrative

When >= 3 dormant threads exist, the oldest (by `last_updated_turn`) is culled: moved to `completed_threads` with `resolution_state="abandoned"` (turn_state.py:623-649). This is mechanical, not narrative — no justification for why the thread was abandoned.

### Auto-Dormant — 4 Turns → 8 Turns (Changed)

Threads untouched for >= 4 turns get `dormant=True` (turn_state.py:112-133). This is too aggressive for a game running 25-34 turns — threads get dormant before they've had a chance to develop.

**Design decision:** Auto-dormant threshold moves from 4 to 8 turns (configurable). See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

### Urgency Decay — Stepwise Demotion

Urgency steps down (urgent→normal→background) after `thread_urgency_max_age` turns (default 8, turn_state.py:135-159). Combined with auto-dormant at 4 turns, threads go dormant before urgency decays naturally.

With auto-dormant at 8 turns, urgency decay and auto-dormant are aligned — threads can develop for 8 turns before either mechanism fires.

### Auto-Thread Completion — Remove If Present (Changed)

The engine auto-resolves threads when progress entries >= threshold (default 3, `thread_completion_threshold`). This is a hard TTL on active threads.

**Design decision:** Remove auto-thread completion. Hard TTL on active threads is a terrible idea. Threads should be resolved by the storyteller via `thread_resolve`. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

---

## Validation and Coercion Problems

### 8. Arc Thread — `type` Field Has No Coercion (Fixed)

**Problem:** `ArcThread.type` (`Literal["threat", "opportunity", "complication", "revelation"] | None`) had no coercion validator. Uppercase from LLM caused Pydantic validation error → entire `thread_add` rejected → full storytell retry. (Fixed in this session with `@field_validator`.)

**Related:** `GMBeat.type` has coercion (returns `None` for invalid → silently nullifies beat). `GMBeat.driver` has no coercion — invalid value `"environment"` fails validation → beat nullified.

**Design decision:** Type is stable by default. Can change via storyteller or sanitizer, but requires a `reason` field. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions).

### 5 (cont.) Empty `arc_resolve` Crashes Validation

LLM emits `arc_resolve: {}` (empty dict). Pydantic `ArcResolution` requires `resolution`, `visible_goal`, `goal_context` so `{}` fails validation. Fix was to nullify before Pydantic sees it in `_coerce_scene_json()` (extraction/utils.py), but this masks the underlying prompt problem.

---

## State Model Problems

### CampaignArc Model (state.py:79-86)

```python
class CampaignArc(BaseModel):
    visible_goal: str = ""
    goal_context: str = ""
    threads: list[ArcThread] = Field(default_factory=list)
    completed_threads: list[ArcThread] = Field(default_factory=list)
    resolution: str | None = None
    last_thread_created_turn: int = 0
```

**Issues:**
- `resolution` field exists but is never set by the engine (only by storyteller via `arc_resolve`)
- `last_thread_created_turn` tracks thread_add cooldown but is never reset on arc_resolve
- No `created_turn` or `started_turn` — no way to measure arc age
- No TTL on `completed_threads` — they accumulate forever
- `goal_context` → to be replaced by `arc_origin`

**Design decisions:**
- Add `created_turn` or `started_turn` for arc age tracking
- `goal_context` → `arc_origin` (UI-only + opening narration)
- Consider TTL on `completed_threads`

### ArcThread Model (state.py:26-76)

```python
class ArcThread(BaseModel):
    id: str
    summary: str
    dormant: bool = False
    urgency: Literal["background", "normal", "urgent"] = "normal"
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    progress: list[ProgressEntry] = Field(default_factory=list)
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None
    last_updated_turn: int | None = None
    added_turn: int | None = None
    urgency_set_turn: int | None = None  # DEAD STATE
```

**Issues:**
- `urgency_set_turn` is dead state (never read or written)
- `added_turn` exists but is unused for thread age calculation
- `last_updated_turn` exists but auto-dormant uses 4 turns (not based on this)
- No `resolved_by` field (engine vs storyteller vs auto)
- `resolution_state` is set by storyteller (`thread_resolve`) or engine (auto-complete), but no distinction
- `progress` → to be renamed to `major_updates`
- `promote_to_world_state` in ThreadResolution → replaced by two-step candidate system

**Design decisions:**
- `progress` → `major_updates`
- `urgency_set_turn` → delete
- `promote_to_world_state` → delete (replaced by two-step candidate system)
- `resolved_turn` already exists — no addition needed
- Auto-dormant threshold: 4 → 8 turns
- Archival TTL: 13 turns (8 dormant + 5 more)

### State Shape (state/io.py:91-99)

```python
"arc": {
    "visible_goal": "",
    "goal_context": "",
    "threads": [],
    "completed_threads": [],
    "resolution": None,
    "last_thread_created_turn": 0,
},
"resolved_arcs": [],
```

**Issues:**
- `resolved_arcs` is a list, not a dict — no TTL tracking built in, TTL is applied at render time in `narrate.py`
- No `arc_age` or `turns_since_resolve` — frequency warning uses meta tracking instead
- `last_thread_created_turn` in both arc and meta — duplicated state
- `goal_context` → to be replaced by `arc_origin`
- `visible_goal` → to be renamed

---

## Prompt Integration Problems

### `_arc.j2` Template (prompts/sections/_arc.j2)

Renders `### Campaign Arc` with visible_goal, resolution, completed threads (TTL-limited to 15), and previously resolved arcs (TTL-limited).

**Issues:**
- Completed threads shown without thread IDs until June 18 fix (caused hallucination)
- TTL of 3 turns on completed_threads and resolved_arcs is very short — storyteller loses context quickly
- No thread age display — storyteller can't tell if a thread is fresh or stale
- Thread summaries are truncated to 80 chars — loses context

### Storyteller Prompt Integration (storytell_system.j2)

**Issues:**
- `thread_resolve` and `thread_update` in same JSON object as `arc_resolve` — storyteller treats them as "everything that happened"
- `goal_update` and `arc_resolve.visible_goal` in same object — conflated semantics
- `chapter_end` as boolean in same object — feels like an option, not a signal (REMOVED)
- Thread type guidance says "set type to match semantic role" but LLM treats it as optional (fixed in June 21 with "REQUIRED" language)

**Design decisions:**
- Decouple `arc_resolve` from thread operations
- Remove `chapter_end`
- Rename fields for clarity

### Narrator Prompt Integration (narrate_system.j2, narrate_user.j2)

**Issues:**
- Thread display shows `[TYPE]` or `[TYPE - URGENCY]` but doesn't show thread age or progress count
- Removed location/conditions/inventory from user prompt (June 18) — may reduce arc awareness
- No thread lifecycle guidance for narrator — doesn't tell narrator to reference resolved threads

---

## Sanitizer Integration Problems

### thread_sanitizer.py (engine/thread_sanitizer.py)

Runs every 5 turns (configurable) as independent arc management path.

**Issues:**
- Sanitizer uses dict format for `goal_update` (`{visible_goal, goal_context}`) while storyteller uses string — format mismatch
- Sanitizer thread abandonment criteria (5 turns no mention + 3 turns no activity) conflicts with auto-dormant (4 turns)
- Sanitizer has its own prompt (`sanitize_thread.j2`) with different thread lifecycle guidance than storyteller prompt
- Sanitizer can set `dormant: True` but auto-dormant already did this — redundant

**Design decisions:**
- Auto-dormant at 8 turns aligns with sanitizer criteria
- Sanitizer extended to world state authority (see Seed Worldbuilding Redesign, Workstream 2)
- Sanitizer confirms world state candidates from storyteller (two-step system)

---

## Checkers — Gaps and False Positives

### Existing Arc/Thread Checkers

| Checker | What it checks | Known issues |
|---------|---------------|--------------|
| `arc_resolution_validity` | drop_threads reference existing threads | Fixed: compares against previous turn's snapshot |
| `thread_resolution_validity` | thread_resolve IDs exist in state | Fixed: compares against previous turn's snapshot |
| `thread_lifecycle` | thread_add appears in state, thread_update IDs valid | Fixed: checks current + previous turn state, changes events |
| `goal_update_validity` | goal_update differs from previous visible_goal | Fixed: compares against previous turn's snapshot |
| `arc_goals` | goal_update applied correctly | Fixed: compares against current turn's snapshot |

### Missing Checkers

- **No arc_resolve frequency checker** — warns in engine but no checker tracks it
- **No thread accumulation checker** — no checker tracks thread count over time
- **No thread resolution rate checker** — no checker tracks resolution rates
- **No completed_threads TTL checker** — no checker verifies TTL behavior
- **No arc_resolve no-op checker** — no checker verifies visible_goal changes across resolutions

---

## Summary

The arc system has three fundamental problems:

1. **Schema confusion** — `arc_resolve` mixes arc-ending, thread cleanup, and thread creation into one JSON object. The storyteller interprets it as "everything that happened" rather than "the arc is ending."

2. **Naming confusion** — `progress` implies "update every turn." `urgency` is too coarse (3 states). `progress_kind` is too vague (3 categories).

3. **Dead/required noise** — `goal_context` is required by schema but UI-only. `urgency_set_turn` and `promote_to_world_state` are dead state.

The system needs a ground-up redesign, not patches.

### Prompt Plumbing Audit

A separate prompt plumbing audit is planned to verify that every variable meant to be plumbed into user prompts is correctly rendered. This should be done before and after implementation to catch "bugs" that turn out to be missing prompt plumbing rather than structural issues.

### Decisions Recorded

See [01-Primitives](../design/01-primitives.md) for canonical definitions of field renames, TTL strategy, pressure score system, and age tracking. See [02-Arc System Redesign](../design/02-arc-system-redesign.md#decisions) for arc-specific decisions. Key decisions:
- `progress` → `major_updates`
- `goal_context` → `arc_origin` (UI-only + opening narration)
- `visible_goal` → `long_term_objective` (settled)
- `chapter_end` → firm removal
- Auto-dormant: 4 → 8 turns
- Archival TTL: 13 turns
- Thread type: stable by default, changes require `reason` field
- Thread → world state: two-step (storyteller flags, sanitizer confirms)
- Multiple arcs: deferred
- Auto-thread completion: remove if present
- `urgency_set_turn`: delete
- `promote_to_world_state`: delete (replaced by two-step candidate system)
- Progress kind categories → `major_update_signal`: settled, `advancement` and `setback` only; `shift` removed
- Hard floor on `arc_resolve` removed; replaced by tiered pressure score hint system
- Pressure score system — threads (advancement +1, setback −1, duration weight) and arcs (resolved threads +2, duration weight); hint tiers drive LLM nudges, not hard resolves; thresholds are tunable
- Completed/abandoned threads: keep in data forever, TTL-filter in prompts (3 turns), no hard cap
- "Past Resolutions" in narrate_user.j2: removed (unfiltered, causes bloat)
- Thread archival resurfacing: no (LLMs are bad at ignoring things)
- Arc → world state: out of scope for this redesign
- Thread urgency graduated states: deferred
- Execution order: primitives → arc system → seed worldbuilding

### Skeptical Items (Question These)

These findings may not actually be problems. They need to be questioned before committing to design changes.

**Thread TTL disconnect.** The narrator's 3-turn TTL on completed threads and the storyteller's access to them via `all_threads` may be by design, not a bug. The narrator's context window is limited, and completed threads are low-priority context. The storyteller has a wider context. If the storyteller has access to completed threads via `all_threads` in the prompt, then the narrator forgetting them isn't a bug — it's a feature. The real problem is orphaned threads (not explicitly dropped by arc_resolve), not that completed threads expire. **Settled:** Completed/abandoned threads are kept in data forever, TTL-filtered in prompts (3 turns), no hard cap. "Past Resolutions" in narrate_user.j2 is removed (unfiltered, causes bloat).

**NPC roster limited to 10.** This is a context management decision, not a bug. Bumping to 12 (user preference) or 15 adds cognitive load to the storyteller prompt. Whether the value of seeing 11-20 NPCs outweighs the cost of a larger prompt is an open question.

**Beat driver always "motivation".** "Motivation" is the most narratively relevant driver — NPCs act based on what they want. "Fear," "leverage," "bond," and "personality" are valid but less frequently the primary driver in a given turn. This might be a prompt design issue (the storyteller isn't being prompted to use other drivers) rather than a fundamental flaw. User preference: motivation = primary, leverage/bond = secondary, fear = third, personality = removed (valid option).

**Null beat rate 34-57%.** All beats have a two-turn TTL, and a 30-50% null rate gives the narration room to breathe. Less than 50% null is acceptable. No checker needed to enforce a threshold.

**NPC dialogue not tracked.** The NPC model has no dialogue or speech_history field. User preference: not needed. Personality fields (including speech) and previous turn outcomes should be sufficient to drive consistent NPC behavior.

### Items Needing Deeper Investigation

**Convergence starvation mechanism.** [RESOLVED — bug ticket created: `roadmap/bugs/convergence-starvation.md`]. This is the biggest gap in the current designs. The arc redesign and seed redesign don't address pacing engine convergence. The ruling system's "routine" path lets the opportunist avoid rolls, which starves dice_weight, which starves convergence. Questions:
- Should the ruling system be less generous with "routine" skips?
- Should convergence have a proactive injection mechanism (e.g., "if convergence has been <2 for N turns, inject a pressure beat")?
- Should the phase machine allow narrative-based transitions (e.g., "if the player has been in stealth for 5 turns, transition to a new phase based on narrative context, not just convergence score")?
- The convergence threshold was lowered from 3 to 2 in commit `eed5878` to help with starvation, but it hasn't helped much. Previously, the problem may have been overly passive NPCs (which are apparently doing better now) and NPCs not getting their personalities correctly due to a misconfiguration.

**Thread resolution events ≠ unique threads.** [RESOLVED — bug ticket created: `roadmap/bugs/thread-resolution-events-not-unique.md`]. The storyteller generates `thread_resolve` events for threads that no longer exist in the active thread list. Root cause: the storyteller's user prompt shows both active threads AND completed threads. The storyteller sees completed thread IDs in the prompt and tries to resolve them. Recommended fix: remove completed threads from the storyteller's prompt.

**NPC dialogue tracking.** User preference: not needed. But this should be confirmed by examining whether personality fields (including speech) and previous turn outcomes actually produce consistent NPC dialogue in practice.

**Prompt plumbing audit.** User is running a separate prompt audit to verify that every variable meant to be plumbed into user prompts is correctly rendered. This should be done before and after implementation to catch "bugs" that turn out to be missing prompt plumbing.

### Evidence Sources

- [Eval Cycle 1 Report (2026-06-22)](../../evals/runs/2026-06-22_0.28.0-72-gdabe3b81_dabe3b8/REPORT.md)
- [Outer Rim Full Eval (2026-06-21)](../../evals/findings/outer-rim-eval-2026-06-21.md)
- [2026-06-21 Report](../../evals/runs/2026-06-21_0.28.0-56-g47ff6261_47ff626/REPORT.md)
- [2026-06-20 Consolidated (Post-Fix)](../../evals/runs/2026-06-20_0.28.0-29-g69faea92_69faea9/CONSOLIDATED-REPORT.md)
- [2026-06-20 Consolidated (Pre-Fix)](../../evals/runs/2026-06-20_0.28.0-28-ge3998180_e399818/CONSOLIDATED-REPORT.md)
- [2026-06-18 Report](../../evals/runs/2026-06-18_0.27.0-61-g255992b6_255992b/REPORT.md)
- [2026-06-17 Consolidated](../../evals/runs/2026-06-17_0.27.0-31-g07266252_0726625/consolidated-narrative-eval-2026-06-17.md)
- Source code: `ccya/models/state.py`, `ccya/engine/turn_state.py`, `ccya/engine/thread_sanitizer.py`, `ccya/engine/_pacing.py`, `ccya/engine/narrate.py`, `ccya/engine/changes.py`, `ccya/state/delta_builder.py`, `ccya/state/io.py`, `ccya/prompts/sections/_arc.j2`, `ccya/prompts/storytell_system.j2`, `ccya/prompts/storytell_user.j2`, `ccya/prompts/sanitize_thread.j2`, `ccya/prompts/generate_seed_system.j2`, `ccya/prompts/narrate_system.j2`, `ccya/prompts/narrate_user.j2`, `ccya/prompts/context.py`, `ccya/engine/extraction/utils.py`
