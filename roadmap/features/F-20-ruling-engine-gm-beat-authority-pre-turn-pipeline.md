---
title: "Ruling Engine GM Beat Authority & Pre-Turn Pipeline"
status: done
urgency: 3
size: medium
created: 2026-06-24
ticket_id: F-20
design: docs/design/beat-generation-split-design.md
labels:
  - architecture
  - engine
  - pacing
  - design-question
---
## Problem

Current Storytell (Step 2c) is overloaded: it handles backward-looking tasks (thread lifecycle, arc resolution, state extraction) AND forward-looking tasks (GM beat generation). Beat generation creates a cognitive disconnect — it decides what happens next *before* knowing player intent for the upcoming turn, forcing the narrator to reconcile a beat with player input even when they don't fit together.

Ruling engine currently does its job well (intent classification, impossibility check, difficulty adjustment, dice resolution). Adding beat generation to it would overload ruling with the same forward-looking creative work.

## Vision

Split the monolithic Storytell into three focused, evenly-loaded steps:

1. **Record** (refactored Storytell) — Post-narration scribe. Backward-looking only. Records what changed narratively: thread updates, arc resolutions. Lightweight, fast. Low temperature.

2. **World** (async, new) — Post-persist world simulation. Forward-looking only. Generates 2-3 candidate GM beats from scene signals. Runs while player reads (~5s). Stores candidates in `state.meta`. Medium temperature (0.5-0.6).

3. **Ruling** (refactored) — Pre-narration selector. Reads beat candidates prepared by World. Picks the best beat for the player's actual intent. Does not generate beats; selects from prepared options. Temperature unchanged.

## Architecture

```
Turn N completes → Record (sync) → Persist → World (async, ~5s) → candidates in state.meta
Turn N+1 starts → Ruling reads candidates → selects beat → Narrate consumes selected beat
```

## Why This Over Alternatives

**vs. ruling generates beats:** Same problem — ruling still guesses forward-looking content before knowing intent. Just shifted to a different phase.

**vs. ruling selects beats:** This is the chosen approach. Selection is a constrained choice problem, not open-ended creative generation. Ruling has player intent, which generation lacks.

**vs. keeping beats in Storytell:** Storytell is already overloaded. Forward-looking beat generation is its heaviest responsibility and creates the intent disconnect.

## Step Inventory

### 1. Record (refactored Storytell)

**Direction:** Backward-looking (documents what just happened)

**Tasks:**
- Thread lifecycle: `thread_update`, `thread_resolve`, `thread_add`
- Arc operations: `goal_update`, `arc_resolve`
- Actions: 4 suggested player choices
- Outcome summary: 1-2 sentence recap

**Removed:** GM beat generation (moved to World)

**Inputs (trimmed):**
- `narration` (from Step 1) — still needed for thread analysis
- `arc.threads[]` (unified scope=scene + scope=arc) — still needed
- `rules_outcome.band` — still needed for thread advancement guidance
- `recent_turns[-10:]` — still needed for context
- `prior_history[:-1]` — still needed for context

**Inputs (removed or reduced):**
- ~~`pacing_context`~~ — not needed for backward-looking documentation
- ~~`candidate_npcs`~~ — moved to World
- ~~`npc_roster`~~ — slimmed or removed (no beat generation needed)
- ~~`inventory`~~ — not needed for thread/arc operations
- ~~`conditions`~~ — not needed for thread/arc operations
- ~~`intent`~~ — not needed for backward-looking analysis
- ~~`recent_beats`~~ — moved to World

**Outputs:**
- `thread_update: list[ThreadUpdate]`
- `goal_update: dict | None`
- `arc_resolve: ArcResolution | None`
- `thread_resolve: list[ThreadResolution]`
- `thread_add: ArcThread | None`
- `actions: list[str]`
- `outcome_summary: str`
- ~~`gm_beat`~~ — removed

**Temperature:** Low (0.1-0.3) — deterministic scribe work

**Cognitive load:** Low. Documentation role. Backward-looking analysis of what changed. Should be faster and more reliable than current Storytell.

### 2. World (async, new)

**Direction:** Forward-looking (simulates what the world wants to do next)

**Tasks:**
- Generate 2-3 candidate GM beats for the next turn
- Each candidate has: `type`, `effect`, `npc_id`, `driver`, TTL

**Inputs:**
- `candidate_npcs` (from Scene Extract — per-NPC beat signals with driver assignment)
- `arc.threads[]` (urgency counts, active threads)
- `narration` (from Step 1) — or narration summary (needs decision)
- `pacing_context` (directive, outcome_hint, scene_phase)
- `recent_beats` (beat history for diversity)
- `allowed_beat_types` (phase-derived constraints)

**Outputs:**
- `beat_candidates: list[GMBeat]` (2-3 candidates)
- Stored in `state.meta.beat_candidates` for ruling to read

**Temperature:** Medium (0.5-0.6) — constrained creative generation

**Cognitive load:** Moderate. Creative generation constrained by beat schema, phase constraints, and candidate_npcs signals. Runs async (~5s) while player reads, so doesn't add to turn latency.

### 3. Ruling (refactored)

**Direction:** Forward-looking but intent-aware (selects from prepared options based on what player wants to do)

**Tasks:**
- Intent classification (existing)
- Impossibility check (existing)
- Difficulty adjustment (existing)
- Dice resolution (existing)
- Pacing context computation (existing)
- **Beat selection** ← new: pick best beat from `beat_candidates` based on player intent

**Inputs:**
- `state.pc`, `state.location` (existing)
- `user_input` (existing)
- `recent_turns[-1:]` (existing)
- `arc.threads[]` urgent only (existing)
- `npc_roster`, `inventory`, `conditions` (existing)
- `scene_phase` (existing)
- **`beat_candidates`** ← new: prepared by World, stored in state.meta

**Outputs:**
- `IntentEnvelope` (existing)
- `RulesOutcome` (existing)
- `PacingContext` (existing)
- **Selected `gm_beat`** ← new: passed to Narrate via `pending_gm_beat`

**Temperature:** Unchanged

**Cognitive load:** Heavy (existing) + very light (beat selection). Selection is a constrained choice problem — ruling doesn't generate beats, it picks from prepared options. The decision is guided by player intent + narration + candidates, which is much lighter than generating beats from scratch.

## Comparison

| Aspect | Record | World | Ruling |
|--------|--------|-------|--------|
| **Direction** | Backward-looking | Forward-looking | Forward-looking (intent-aware) |
| **Bucket** | Documentation | Creative generation | Decision + mechanics |
| **Cognitive load** | Low | Moderate | Heavy + very light |
| **Timing** | Sync (turn) | Async (~5s) | Sync (turn) |
| **Knowledge depth** | Medium (threads, arcs) | Medium (signals + context) | Shallow (candidates + intent) |
| **Error surface** | Reduced (no beat generation) | New (beat generation) | Minimal (selection only) |

## Token Estimates

### Current State (before split)

| Prompt | Lines | Est. Tokens |
|--------|-------|-------------|
| **Storytell system** | 142 | ~600-700 |
| **Storytell user** | 92 (template) | ~1500-4000 (highly variable) |
| **Ruling system** | 86 | ~400-450 |
| **Ruling user** | 34 (template) | ~800-1500 (variable) |

### After Split

| Step | System tokens | User tokens | Total |
|------|--------------|-------------|-------|
| **Record** | ~450-500 | ~1000-2500 | ~1450-3000 |
| **World** | ~200-250 | ~1000-2000 | ~1200-2250 |
| **Ruling** | ~450-475 | ~1000-1700 | ~1450-2175 |
| **Total** | **~1100-1225** | **~3000-6200** | **~4100-7425** |

**vs. current total:** ~1000-1150 system + ~2300-5500 user = ~3300-6650

The total token count increases modestly (~40-60% more system tokens due to duplication of instructions across Record and World system prompts). User prompt total stays roughly similar or decreases since Record's user prompt drops significantly (no narration, no inventory, no conditions, no NPC roster).

**Key difference:** Record's system prompt drops by ~30% (beat generation instructions removed). World's system prompt is very lightweight since beat generation is a constrained task. Ruling's system prompt barely changes (+~25 tokens for selection instructions).

## Benefits

1. **Lower turn latency** — Record is lighter without beat generation; World runs async (~5s while player reads)
2. **Fewer errors** — Record's focused scribe role reduces error surface; no more overloaded LLM call
3. **Intent-aware beats** — Ruling selects from candidates using actual player intent, solving the disconnect problem
4. **Evenly distributed load** — Three focused steps, each with clear responsibility
5. **Better temperatures** — Record at low temp for reliability, World at medium for creativity, Ruling unchanged

## Open Questions — Resolved

1. **Record inputs** — Record keeps narration (needed for actions/outcome_summary) and recent_turns (for context). Drops pacing_context, candidate_npcs, npc_roster, inventory, conditions, intent, recent_beats. Actions generated from narration text alone.

2. **World narration** — World gets full narration (not summary). Token cost acceptable for async step.

3. **Beat candidates lifecycle** — All candidates discarded after ruling selects one. World regenerates fresh candidates each turn.

4. **Actions + outcome_summary** — Record keeps both. Natural outputs of reviewing what happened. Actions generated from narration text alone.

5. **Beat selection mechanism** — Ruling's JSON output includes a `selected_beat` field alongside intent/ruling JSON. Parsed manually in `_call_ruling()` (no new Pydantic model).

6. **Async timing** — Not webhook-based. Extension of existing "no submit while turn is running" mechanism. Player can type input but cannot submit until World completes (~4-5s after turn ends).

7. **Recent beats ownership** — Ruling appends to `recent_beats` after selecting. History reflects what actually happened, not what was prepared.

8. **World template location** — `world_system.j2` and `world_user.j2` in `ccya/prompts/` (same level as all current templates).

9. **Ruling JSON parsing** — Manual dict check in `_call_ruling()` after parsing IntentEnvelope. Extends existing pattern without new Pydantic model.

## Suggested Next Step

Design review needed. Prototype async beat generation in isolation to assess complexity and timing.
