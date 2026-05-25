# Latent Seeds & Beat Expansion — Unified Design

## Purpose

This document is the design authority for plans implementing latent narrative potential (replacing `hidden_truths`) and expanding the GM beat into a richer creative handoff between stateless LLM turns. It consolidates two related problems into one design: (1) hidden_truths and latent threads are dead/broken, and (2) the beat carries too little signal to meaningfully shape next turn's narration.

## Current State — What Exists

### Three Broken Mechanisms

1. **`hidden_truths: list[str]`** — generated at seed time (2–4 strings), stored on `CampaignArc` (`ccya/models.py:64`), passed to template context in `ArcThreadBlock.hidden_truths` (`ccya/prompts/context.py:99`), but **never rendered by `_arc.j2`**. The narrator is told about them conceptually (`narrate_system.j2:62,81`) but cannot see the actual text. The data exists in state, consumes prompt context bandwidth through `context.py`, and is invisible to both LLMs. Dead data.

2. **Latent threads** — the seed prompt says "include 2–3 threads that should start as active and any latent threads", but `seed.py:346–349` **force-activates every thread** (`object.__setattr__(t, "active", True)`), defeating the entire concept. Any thread the LLM marks as latent at seed time is instantly promoted to active by force. Combined with automatic cooldown-based promotion in `_apply_thread_signals` (`turn.py:325–360`), the system has two redundant and contradictory latent→active paths.

3. **GMBeat is too thin** — current schema (`ccya/models.py:428–448`) carries only `{type: str, surface_as: str, beat_expires_turn: int}`. This is emitted by the storyteller (Step 2c) after analyzing the narrative, stored in `state.meta.pending_gm_beat`, and consumed by the next turn's narrator as a single prompt line: "Beat: PRESSURE — surface as npc_behavior." The narrator already receives a pacing directive with similar information. The beat adds no unique signal beyond a type label the narrator already knows.

### The Beat Handoff Gap

The narrator is stateless per turn. The beat is the only creative bridge between turns:

```
Turn N: Narrator writes prose → Storyteller reads prose, produces beat → state.pending_gm_beat → Turn N+1: Narrator reads beat
```

Currently the beat carries no information about:
- What **emotional register** the prose established (mood)
- Which **thread or element** advanced most (focus)
- Whether the PC ended the turn **better or worse** (valence)
- A **1-sentence synthesis** of what happened (continuity)
- Whether the pacing system has detected a **punishment loop** (relief flag)

Without valence, the narrator doesn't know if the player needs consequences or advancement. Without focus, the narrator can drift. Without mood, prose stays generic. Without relief, the default LLM mode ("escalate") runs unchecked.

### Punishment Loop — The Root Cause

The system prompt (`narrate_system.j2:117-133`) trains the LLM to escalate on success ("the world reacts to PC momentum") and stonewall on fail ("NPC does NOT engage constructively"). Both feel bad. Python's only relief mechanism is momentum floor (-3) injection of `breathing_room` with TTL +3, which is reactive — the player endures many punishing turns before Python acts. There is no proactive relief detection based on narrative success signals.

The pacing system (`_compute_pacing_context`) watches momentum, velocity, combat age, and thread urgency counts. It never watches for **thread resolution, good rolls, or player progress** — it only detects misery, and even then only at extremes.

### Thread Creation During Play

The storyteller can emit `thread_add: ArcThread` to create threads from scratch, but has no feedstock of narrative potential — it invents threads from nothing, which produces generic or disconnected story tensions. The `ArcThread.promotes` field exists (`ccya/models.py:58`) but is never read on resolution.

Automatic latent→active promotion (`_apply_thread_signals`, 3-turn cooldown, oldest-first) promotes the oldest latent thread regardless of narrative fit. This produces directionless thread activation — the wrong thread gets promoted because the system has no concept of narrative relevance.

### ARC_UPDATE Dual Path

The narrator emits `<<<ARC_UPDATE_START>>>` blocks for `discovered_truths`, `visible_goal`, etc. (`narrate_system.j2:64-78`), creating a dual-path arc mutation where both narrator and storyteller mutate arc state. This is confusing and unnecessary — all arc mutations belong to one LLM. The narrator should be pure prose.

## Problems with Current State

- `hidden_truths` is dead data: stored, transported, never rendered. Wastes prompt context and model complexity.
- Seed-time latent threads are force-activated, making latent labels meaningless.
- Automatic cooldown promotion activates threads by age, not narrative relevance.
- GMBeat carries no mood, focus, valence, continuity, or relief — too thin to shape next turn's narrator.
- No proactive punishment loop detection. Relief only fires at momentum floor.
- ARC_UPDATE creates unnecessary dual-path arc mutation.
- The `promotes` field on ArcThread exists but is never used on resolution.
- The storyteller creates threads from nothing (no feedstock), producing generic tensions.

## Target State — What It Becomes

### Core Changes

**Replacement 1 — hidden_truths → latent_seeds**

`hidden_truths: list[str]` → `latent_seeds: list[LatentSeed]` on `CampaignArc` and `ArcThreadBlock`. Each `LatentSeed` has `{id: str, summary: str}` — no tags, no urgency, no scope. These are narrative potential, not mechanical tokens. Both LLMs see them rendered in `_arc.j2`.

The narrator uses latent seeds as material to foreshadow. The storyteller uses them as feedstock for thread activation and/or truth revelation.

**Replacement 2 — force-activate removed**

The force-active override at `seed.py:346-349` is removed. At seed time, the prompt generates 1–2 active threads + 2–4 latent seeds. Any thread the LLM creates with `active: false` stays false.

**Replacement 3 — auto-promotion → hybrid activation**

The cooldown-based automatic promotion block (`turn.py:325-360`) is removed. Only two paths activate latent threads:

1. **Storyteller explicit** — listing a latent ID in `thread_advance` immediately promotes it (already works, preserved).
2. **Hybrid auto-promotion** — when a thread resolves via `_apply_thread_resolutions`, if the resolved thread has entries in its `promotes` list, the first eligible latent matching that ID is promoted. The storyteller can suppress this by emitting `suppress_auto_promote: True` on its result. If the resolved thread has no `promotes`, no auto-promotion occurs (the slot stays open for the storyteller to fill later).

This gives the arc designer control over chain progression (via `promotes`) while letting the storyteller override when the player needs air.

**Replacement 4 — GMBeat expansion**

The GMBeat schema gains:

- `mood: str` — 1-2 word emotional register set by the storyteller from prose analysis (e.g. "claustrophobic", "bittersweet", "wary"). This is the primary fix for prose genericness.
- `focus: str` — thread_id, NPC_id, or element the next narrator should foreground. Set by storyteller. Prevents pivot drift.
- `valence: Literal["better", "worse", "mixed"] | None` — how the PC ended this turn. Set by storyteller from outcome_summary + band. Tells next narrator whether consequences should lean relief or pressure.
- `continuity: str` — 1-sentence synthesis of what just happened. Set by storyteller. Saves narrator from re-parsing prose.
- `relief: bool = False` — Python-set override flag. When True, the narrator receives a constraint: "do not escalate this turn." Set by Python when punishment loop is detected (see Decision Table for trigger).

New GMBeat shape:
```
GMBeat
  type: complication | revelation | opportunity | breathing_room | pressure | twist | setback | escalation | callback
  surface_as: ambient | event | npc_behavior | environmental | player_discovery | item
  mood: str
  focus: str
  valence: Literal["better", "worse", "mixed"] | None
  continuity: str
  relief: bool = False
  beat_expires_turn: int | None
```

[OPEN: The storyteller currently infers its beat from the narrative alone. Adding mood/focus/valence/continuity means the storyteller must also extract these as part of its output. This makes the storyteller's job larger and may increase token usage. Is the storyteller reliable enough to produce consistent mood labels across turns, or will mood drift produce incoherent tone shifts?]

[OPEN: `continuity` overlaps with `outcome_summary` which the storyteller already emits. Are they redundant, or does continuity serve a different purpose (next-turn narrator guidance vs. this-turn conclusion)? Decision: continuity is *forward-facing* (where we are now, what's next), while outcome_summary is *backward-facing* (what just happened). They share source data but serve different consumers.]

**Replacement 5 — ARC_UPDATE removed**

The entire `<<<ARC_UPDATE_START>>>` sentinel system is removed from `narrate_system.j2`. The narrator is pure narration prose. Remove `_extract_narrator_arc_update` call site in `turn.py:1392-1419`, `_ALLOWED_NARRATOR_ARC_KEYS`, and associated merge logic.

The storyteller gains ability to update `visible_goal` and `thematic_question` via new fields on `StorytellerResult`.

**Addition — reveal_latent_seeds**

`StorytellerResult` gains `reveal_latent_seeds: list[str]` — the storyteller emits seed IDs to promote their summaries to `discovered_truths` without creating a thread. Python handles the dedup merge.

**Addition — thread_add_latent_seed_id**

`StorytellerResult` gains `thread_add_latent_seed_id: str | None` — if set alongside `thread_add`, the new thread's summary is pre-populated from the matching latent seed. The storyteller can override the summary if desired.

**Addition — suppression field for auto-promotion**

`StorytellerResult` gains `suppress_auto_promote: bool = False` — when True, the hybrid auto-promotion path on resolution is skipped for this turn.

### Data Flow (Turn)

```
Turn N:
  PacingContext (Python): directive, gate, beat_locked ← from momentum, thread counts, combat age
                         relief: True if 4+ consecutive pressure turns + no thread advanced
    
  → Narrator receives: PacingContext + pending_beat from Turn N-1
    
  → Narrator writes prose (pure — no ARC_UPDATE sentinel)
    
  → Storyteller receives: prose + state + PacingContext + arc (including latent_seeds)
    
  → Storyteller emits:
      - thread_advance / resolve / add (as today)
      - reveal_latent_seeds: ["seed_id"]  (new)
      - thread_add_latent_seed_id: "seed_id"  (new)
      - suppress_auto_promote: bool  (new)
      - visible_goal / thematic_question (new — replaces ARC_UPDATE)
      - beat with expanded schema:
          {type, surface_as, mood, focus, valence, continuity, relief, beat_expires_turn}
    
  → Python:
      - Processes thread_advance/resolve as today
      - On resolve: if resolves thread with `promotes` and storyteller didn't suppress
        → auto-promote first eligible latent matching promotes[0]
      - Processes reveal_latent_seeds → append to discovered_truths
      - Stores expanded beat in state.meta.pending_gm_beat
      - If no beat emitted AND relief=True: inject breathing_room

Turn N+1:
  → Narrator reads: PacingContext + expanded beat (mood, focus, valence, continuity, relief, type, surface_as)
  → Narrator writes with richer guidance
```

### Cadence Diagram

```
Latent seeds at seed:
  2-4 seeds (narrative potential, no type/urgency/scope)

During play:
  Thread resolves →
    If promoted from a thread with `promotes`:
      storyteller CAN suppress
      if not suppressed → first eligible latent seed matching promotes[0] → thread_add
    If no `promotes`:
      no auto-promotion → slot stays open
  
  Storyteller CAN also:
    - activate latent seed directly: thread_add + thread_add_latent_seed_id
    - reveal seed without thread: reveal_latent_seeds
    - update visible_goal / thematic_question
    - emit expanded beat with mood/focus/valence/continuity

  Python CAN also:
    - set beat.relief=True when punishment loop detected
    - set beat.relief triggers N consecutive pressure + thread stall
```

## Decision Table

| Decision | What | Why |
|---|---|---|
| hidden_truths → latent_seeds | Replace `list[str]` with `list[{id, summary}]`. | Dead data becomes usable narrative feedstock. Both LLMs see it rendered. |
| Force-activate removed | Delete `seed.py:346-349`. | Latent threads at seed time stay latent if the LLM marks them. |
| Auto-promotion → hybrid | Remove cooldown-gated promotion. Add resolution-triggered promotion from `promotes` field with storyteller override (`suppress_auto_promote`). | Removes age-based wrong-thread promotion. Uses designed thread chains. Storyteller can suppress when player needs air. |
| ARC_UPDATE removed | Delete sentinel system from narrator. | Narrator becomes pure prose. Single mutation path via storyteller. |
| Storyteller gains arc mutation fields | Add `visible_goal`, `thematic_question` to `StorytellerResult`. | Replaces what ARC_UPDATE provided. Single authority. |
| GMBeat expanded | Add `mood`, `focus`, `valence`, `continuity`, `relief`. | Richer creative handoff. Fixes genericness (mood), drift (focus), punishment (relief, valence). |
| Python sets beat.relief | Relief trigger: 4+ consecutive turns where directive != Breathe/empty AND no thread advanced. | Proactive punishment loop detection using signals Python already has. |
| Storyteller sets mood, focus, valence, continuity | These are narrative inferences from the prose the storyteller just analyzed. | Clean mechanical/narrative split. Storyteller already has the data. |
| reveal_latent_seeds as separate field | `StorytellerResult.reveal_latent_seeds: list[str]`. Python merges into discovered_truths. | Explicit pipeline. Cleaner than inferring reveal from the beat. |
| Land latent seeds first, beat expansion second | Two implementations. | Latent seeds are structural (model/prompt changes). Beat expansion is additive. Avoids touching same code twice. |
| Punishment loop threshold | `relief=True` when 4 consecutive pressure-type turns AND no `thread_advance` in those turns. | Player is being pounded with no progress signal. Configurable threshold. |

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `CampaignArc.hidden_truths` | `ccya/models.py:64` | Replaced by `latent_seeds: list[LatentSeed]` |
| `ArcThreadBlock.hidden_truths` | `ccya/prompts/context.py:99` | Replaced by `latent_seeds: list[LatentSeed]` |
| Force-active override (lines 346-349) | `ccya/engine/seed.py` | Deleted. Latent threads keep LLM-assigned active value. |
| Auto-promotion block (lines 325-360) | `ccya/engine/turn.py` | Deleted. Replaced by hybrid resolution-triggered path. |
| `_PROMOTION_COOLDOWN_TURNS` constant | `ccya/engine/turn.py:158` | No longer used. |
| `_ALLOWED_NARRATOR_ARC_KEYS` | `ccya/engine/turn.py:1395` | Deleted with ARC_UPDATE removal. |
| `_extract_narrator_arc_update` call site | `ccya/engine/turn.py:1392-1419` | Function kept for potential debugging use. |
| `## ARC UPDATE` section | `narrate_system.j2:64-78` | Deleted. No sentinel output. |
| Hidden truths guidance lines | `narrate_system.j2:62,80-81` | Deleted. No hidden truths to reference. |
| `hidden_truths` merge logic | `ccya/engine/delta_builder.py:_merge_arc_update` | Deleted. Field no longer exists. |
| `ArcThread` field: (none removed) | — | `promotes` preserved, now actively used. |

## What Is Unchanged

- Step 0 (ruling LLM call) — no change. Intent classification remains separate.
- Step 1 (narrate) — unchanged except removal of ARC_UPDATE output. Still streams prose.
- Step 2a (scene extract) — completely unchanged.
- Step 2b (state extract) — completely unchanged.
- Step 2c (storytell) — gains new fields but retains all existing output fields (`thread_advance`, `thread_resolve`, `recent_events_add/update/remove`, `actions`, `outcome_summary`).
- `thread_advance` and `thread_resolve` mechanics — progress counting, completion threshold, resolution_state, 5-turn silent demotion. Unchanged.
- Thread caps (`_ACTIVE_THREAD_CAP=3`, `_LATENT_THREAD_CAP=4`). Unchanged.
- PacingContext struct (`directive`, `gate`, `beat_locked`, `summary`). Unchanged except `relief` moves onto the beat, not PacingContext.
- `_compute_pacing_context()` — unchanged. Still produces directive/gate/beat_locked from same inputs.
- `_apply_thread_signals()` — unchanged except removing auto-promotion block.
- `_apply_thread_resolutions()` — unchanged except adding optional resolution-triggered promotion after its normal work.
- `resolve_check()` dice engine — completely unchanged.
- Dice band mapping, momentum tracking, condition lifecycle — unchanged.
- Chronicle/events persistence — unchanged.
- Server routes, UI panels, turn viewer — no changes.
- Compact/chronicle truncation — unchanged.
- `goal_context` — seed-only, unchanged.

## Migration Notes

No state migration needed. `hidden_truths` is currently dead data (never rendered), so existing saved games with `hidden_truths` on the arc will simply have empty `latent_seeds`. The latent seeds are generated at seed time only — existing games' seed data doesn't have them.

If running with an existing static pack, the old pack's `hidden_truths` in `pack_seed_state.yaml` will be ignored after the schema change. The `CampaignArc` model will drop the unknown field during Pydantic validation.

## New Model Shapes

```python
class LatentSeed(BaseModel):
    id: str
    summary: str

class CampaignArc(BaseModel):
    visible_goal: str = ""
    thematic_question: str = ""
    goal_context: str = ""
    latent_seeds: list[LatentSeed] = Field(default_factory=list)  # replaces hidden_truths
    discovered_truths: list[str] = Field(default_factory=list)
    threads: list[ArcThread] = Field(default_factory=list)
    completed_threads: list[ArcThread] = Field(default_factory=list)
    pc_drive: str = ""
```

```python
class GMBeat(BaseModel):
    type: Literal[str, None]  # same set as today
    surface_as: Literal[str] = "ambient"  # same set as today
    mood: str = ""  # NEW: "claustrophobic", "bittersweet", "wary", etc.
    focus: str = ""  # NEW: thread_id or NPC_id
    valence: Literal["better", "worse", "mixed"] | None = None  # NEW
    continuity: str = ""  # NEW: 1-sentence synthesis
    relief: bool = False  # NEW: Python-set anti-punishment flag
    beat_expires_turn: int | None = None
```

```python
class StorytellerResult(BaseModel):
    # Existing fields (unchanged):
    recent_events_add: list[RecentEvent] = Field(default_factory=list)
    recent_events_update: list[RecentEventUpdate] = Field(default_factory=list)
    recent_events_remove: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    gm_beat: GMBeat | None = None
    thread_advance: list[str] = Field(default_factory=list)
    thread_resolve: list[ThreadResolution] = Field(default_factory=list)
    thread_add: ArcThread | None = None
    # New fields:
    reveal_latent_seeds: list[str] = Field(default_factory=list)  # NEW: promote seed summaries to discovered_truths
    thread_add_latent_seed_id: str | None = None  # NEW: pre-populate thread from latent seed
    suppress_auto_promote: bool = False  # NEW: suppress resolution-triggered promotion this turn
    visible_goal: str | None = None  # NEW: replaces narrator's ARC_UPDATE visible_goal
    thematic_question: str | None = None  # NEW: replaces narrator's ARC_UPDATE thematic_question
```

```python
class ArcThreadBlock(BaseModel):
    visible_goal: str
    thematic_question: str
    pc_drive: str
    threads: list[ArcThreadSummary]
    discovered_truths: list[str]
    latent_seeds: list[LatentSeed]  # replaces hidden_truths
```

## Prompt Token Impact

| Template | Tokens removed | Tokens added | Net |
|---|---|---|---|
| `narrate_system.j2` | ~60 (ARC_UPDATE section + hidden_truths refs) | 0 | -60 |
| `narrate_user.j2` | 0 | ~10 (latent seeds rendering via `_arc.j2`) | +10 |
| `_arc.j2` | 0 | ~30 (latent seeds block) | +30 |
| `storytell_system.j2` | 0 | ~60 (output schema + guidance for new fields) | +60 |
| `storytell_user.j2` | 0 | ~10 (continuation of existing beat/pacing sections) | +10 |
| `generate_seed_system.j2` | ~20 (hidden_truths guidance) | ~40 (latent_seeds guidance) | +20 |

Total net increase: ~70 tokens across all prompts per turn.

The expanded GMBeat is ~50 tokens of JSON serialized into the beat field of `narrate_user.j2` — negligible.

## Ambiguities and Risks

**[OPEN: Storyteller mood reliability]** The storyteller (LLM) must extract a consistent mood label from prose it just read. Mood is subjective — two different storyteller runs on the same narrative might produce different mood labels ("claustrophobic" vs "tense"). If mood fluctuates wildly between turns, the narrator gets whiplash. Mitigation: mood is advisory, not authoritative — the narrator still has the full narrative + PacingContext. But if the mood signal is unreliable, it becomes noise. Could we constrain mood to a small enum set (5-7 values) rather than free-text?

**[OPEN: relief vs. PacingContext overlap]** `relief: True` on the beat duplicates the function of `directive: "Breathe"` on PacingContext in one direction. The current system already has a `Breathe` directive that blocks escalation. The difference is that `Breathe` triggers on velocity < -0.3 (momentum already dropping), while relief triggers on proactive signals (N consecutive pressure + stall). These are different conditions, but a narrator seeing both `directive: "Tension"` and `relief: True` might be confused about which takes priority. Decision: `relief` is a secondary modifier on the beat, same as `; Combat Fatigue` is a secondary on directives. The narrator gets: `Directive: Pressure. Beat: {type, mood, valence, relief: true}` — relief overrides the directive's default escalation behavior.

**[OPEN: continuity hallucination risk]** The storyteller generating a 1-sentence synthesis from its own narrative is at risk of hallucinating details that weren't in the prose. The continuity sentence is consumed by a different LLM (next turn's narrator) and can't be validated against ground truth at generation time. The narrator might internalize a fake continuity and write next turn's prose against a hallucinated state. Mitigation: continuity is strictly "what just happened in the prose that I just analyzed" — the storyteller's hallucination rate should be low since it's summarizing its input, not inventing. But we should monitor.

**[OPEN: promotion chain deadlock]** If a resolved thread's `promotes` points to a seed that's already completed or has unfilled `unlock_if`, the auto-promotion silently fails. The slot stays open. Should Python fall through to "next eligible latent" when the promotes target is blocked? Or should it stay open for the storyteller? Decision: stay open — the arc designer chose that chain, and the storyteller can suppress if it's wrong. A fallthrough to arbitrary promotion re-introduces the age-based randomness we're removing.

**[OPEN: existing packs with hidden_truths]** Static packs have `hidden_truths` in their `pack_seed_state.yaml`. After the schema change, Pydantic drops the unknown field. The player loses whatever narrative secrets were in there. Mitigation: `hidden_truths` was never rendered, so players have never seen these values — the loss is invisible. For dynamic packs, the seed generator will produce `latent_seeds` instead.

## Context for Implementing LLMs

- `ccya/models.py` — `CampaignArc` (line 61), `GMBeat` (line 428), `StorytellerResult` (line 451), `ArcThread` (line 43), `LatentSeed` (new). Schema changes and base model work.
- `ccya/engine/turn.py` — `_apply_thread_signals` (line 162), `_apply_thread_resolutions` (line 363), inline thread_add logic (line 1343), narrator ARC_UPDATE extraction (line 1392). All mutation sites for the thread lifecycle changes, beat storage, and ARC_UPDATE removal.
- `ccya/engine/seed.py` — force-active override at lines 346-349. Remove it.
- `ccya/prompts/narrate_system.j2` — ARC_UPDATE section (lines 64-78) to delete. hidden_truths references (lines 62, 80-81) to delete.
- `ccya/prompts/narrate_user.j2` — pending_beat rendering (line 84-86) — update to display new beat fields.
- `ccya/prompts/storytell_system.j2` — output schema (lines 5-17) to extend. Thread_add guidance (line 38) to mention latent_seed_id. Add guidance for new fields.
- `ccya/prompts/storytell_user.j2` — add latent seeds to template context alongside existing threads.
- `ccya/prompts/sections/_arc.j2` — add latent seeds rendering block.
- `ccya/prompts/context.py` — `ArcThreadBlock` (line 91), `from_state` (line 102). Replace hidden_truths with latent_seeds.
- `ccya/engine/delta_builder.py` — `_merge_arc_update`. Remove hidden_truths merge logic.
- `ccya/engine/extraction.py` — storyteller result processing path. New fields need merge logic (reveal_latent_seeds, thread_add_latent_seed_id, visible_goal, thematic_question, suppress_auto_promote).
- `docs/repomap.md` — update field references after schema changes.
- `docs/architecture/thread-lifecycle.md` — update promotion rules and constants.
