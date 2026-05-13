Good — I now understand the plan format and the exact current state of the codebase. Here's the plan:

***

# Replace Quest System with Campaign Arc + NPC Motivation

## Status
`open`

## Part of
Standalone

## Dependencies
- None. This plan does not depend on any open plan.
- `remove-faction-pool-system.md` should be completed first — it cleans up faction wiring that overlaps with new faction fields introduced here, though it is not a hard blocker.

## Conflicts and overlap
- Removes `active_quests`, `QuestUpdate`, `QuestObjective`, `Quest`, and quest-related fields from `models.py`, `state.yaml`, and all prompt templates.
- Removes `quest_ages`, `quest_threshold_directive`, `pending_beat` (quest-scoped), and `quest_updates` from Step 2c.
- Adds new fields to `CompendiumNpcUpdate` — no conflict with any open plan.
- Modifies `seed_system.j2` / `seed_user.j2` and `SeedEnvelope` / `GameState` — coordinate if any other plan touches seed generation.

## Objective

The current quest system (`Quest`, `QuestObjective`, `QuestUpdate`) is structurally mismatched to a freeform LLM-driven RPG. Quests are short-lived, prone to extraction errors, reliant on fragile objective indexing, and generate excessive deduplication overhead in Step 2c. They provide no durable high-level narrative structure.

This plan replaces the quest system with three complementary mechanics:

1. **Campaign Arc** — a high-level narrative scaffold generated at seed time, stored in Python state, and surfaced to the narrator turn by turn. Provides a visible player goal, a campaign phase, and a small number of active threads. Latent threads are promoted by Python rules as the game progresses.

2. **NPC Motivation & Fear** — durable NPC personality fields (`motivation`, `fear`, `leverage`) added to `CompendiumNpcUpdate`, flowing to the narrator via the existing `known_characters` path. Flavor-only for now; no mechanical wiring to Step 0.

3. **PC Drive + Expressed Stances** — lightweight player identity fields (`pc.drive`, `pc.expressed_stances`) added at seed time. PC drive is player-authored or generated from seed. Expressed stances are a simple counter updated by Python, not extracted by LLM.

Together, these give the game a durable spine that:
- persists across 20+ turns without extraction fragility
- naturally incorporates momentum as a salience bias
- keeps NPC motivation flowing to the narrator without extra extraction complexity
- makes the PC less faceless without requiring per-turn personality extraction

## Non-goals
- No mechanical wiring of NPC motivation to Step 0 / dice resolution (flavor-only for now)
- No faction standing tracker or disposition scores
- No PC personality beyond `drive` and `expressed_stances`
- No arc abandonment / drift counter (deferred — expect players to follow the arc)
- No thread failure mutation logic (deferred — threads expire or stall but don't fork the arc)
- No `check.tags` wiring or tags-based difficulty modulation

## Affected files

| File | Change type | Summary |
|---|---|---|
| `ccya/engine/models.py` | modify | Remove Quest/QuestUpdate/QuestObjective models; add CampaignArc, ArcThread, ArcPhase, ThreadSignal, ThreadState; add NPC motivation/fear/leverage to CompendiumNpcUpdate; add pc.drive and pc.expressed_stances to PC model |
| `ccya/engine/seed.py` | modify | Generate campaign arc scaffold in `generate_seed()`; write arc to `GameState`; populate pc.drive from player override or seed generation |
| `ccya/engine/turn.py` | modify | Remove quest_ages, quest_threshold_directive from run_turn; pass arc fields to narrator and Step 2c; run Python arc director after delta apply |
| `ccya/engine/progress.py` | modify | Replace `quest_updates` with `thread_signals` + `player_drift_signals`; remove quest_ages/quest_threshold_directive inputs |
| `ccya/engine/narrate.py` | modify | Replace `active_quests` block with `current_arc` block (visible_goal, phase, active_threads summary) |
| `ccya/engine/arc.py` | create | New Python module — arc director: thread eligibility, salience scoring, promotion, turn-tick |
| `ccya/templates/seed_system.j2` | modify | Add arc scaffold generation instructions |
| `ccya/templates/seed_user.j2` | modify | Add player arc/drive override fields |
| `ccya/templates/narrate_system.j2` | modify | Replace quest rendering block with current_arc block; add NPC motivation/fear rendering in known_characters block |
| `ccya/templates/narrate_user.j2` | modify | Replace `active_quests` variable with `current_arc` |
| `ccya/templates/extract_progress_system.j2` | modify | Replace quest_updates instructions with thread_signals/player_drift_signals instructions; remove quest_ages/quest_threshold_directive |
| `ccya/templates/extract_progress_user.j2` | modify | Replace `active_quests` with arc summary; replace `quest_updates` output block with thread_signals output block |
| `ccya/templates/extract_scene_system.j2` | modify | Add motivation/fear/leverage rendering instructions for compendium_npc_update |
| `ccya/templates/extract_scene_user.j2` | modify | Add motivation/fear/leverage fields to compendium_npc_update output block |
| `saves/default/state.yaml` | data migration | Remove `quests` key; add `arc` key; add `pc.drive`; add `pc.expressed_stances` |
| `docs/ARCHITECTURE.md` | modify | Update Step 2c table, Step 1 inputs, SeedEnvelope output, and pipeline cross-reference to reflect arc system |
| `docs/REPOMAP/engine.md` | modify | Update models.py, progress.py, turn.py, narrate.py tables; document new arc.py |

***

## Schema reference

### New top-level models (models.py)

```python
class ArcPhase(str, Enum):
    SETUP = "setup"
    PURSUIT = "pursuit"
    REVERSAL = "reversal"
    CRISIS = "crisis"
    RESOLUTION = "resolution"

class ThreadState(str, Enum):
    LATENT = "latent"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"
    EXPIRED = "expired"

class ArcThread(BaseModel):
    id: str
    summary: str                     # 2–4 sentences, enough to build a scene from
    tags: list[str] = []             # e.g. ["lead", "cure", "records"] for tag-match salience
    state: ThreadState = ThreadState.LATENT
    urgency: str = "normal"          # normal | building | immediate
    progress: int = 0                # incremented by arc director on "advanced" signals
    unlock_if: str | None = None     # plain-language condition; Python evaluates heuristically
    promotes: list[str] = []         # thread IDs to promote when this one completes
    last_offered_turn: int | None = None

class CampaignArc(BaseModel):
    visible_goal: str                # always shown to narrator
    thematic_question: str           # shapes tone; shown to narrator
    phase: ArcPhase = ArcPhase.SETUP
    hidden_truths: list[str] = []    # never shown to narrator until promoted
    active_threads: list[ArcThread] = []
    latent_threads: list[ArcThread] = []
    completed_threads: list[ArcThread] = []
    arc_engagement: int = 0          # -3 to +3, biases salience
```

### Changes to existing models (models.py)

```python
# CompendiumNpcUpdate — add fields:
motivation: str | None = None
fear: str | None = None
leverage: str | None = None

# PC model — add fields:
drive: str | None = None             # player-authored or seed-generated
expressed_stances: dict[str, int] = {}  # e.g. {"compassionate": 2, "ruthless": 0}

# Remove entirely:
# Quest, QuestObjective, QuestUpdate, QuestObjectiveUpdate
# (and all references in GameState, StateDelta, ProgressExtractResult)
```

### ProgressExtractResult changes (models.py)

```python
# Remove:
# quest_updates: list[QuestUpdate]

# Add:
class ThreadSignalType(str, Enum):
    ADVANCED = "advanced"
    BLOCKED = "blocked"
    FAILED = "failed"
    IGNORED = "ignored"

class ThreadSignal(BaseModel):
    id: str
    signal: ThreadSignalType

thread_signals: list[ThreadSignal] = []
player_drift_signals: list[str] = []     # max 3 free-text strings, e.g. "interested_in_river_escape"
candidate_opportunity: str | None = None # single sentence; stored as latent stub if useful
```

***

## Implementation — Phase 1: Models and schema

### Context files to load
1. `ccya/engine/models.py`

### Overview
Remove all quest-related models. Add `CampaignArc`, `ArcThread`, `ArcPhase`, `ThreadState`, `ThreadSignal`, `ThreadSignalType` models. Add `motivation`, `fear`, `leverage` to `CompendiumNpcUpdate`. Add `drive` and `expressed_stances` to the PC model. Update `GameState` and `StateDelta` accordingly.

### Detailed steps

#### Step 1.1 — Remove quest models

**File:** `ccya/engine/models.py`

**What:** Delete `QuestObjectiveUpdate`, `QuestObjective`, `QuestUpdate`, and `Quest` class definitions. Remove `quests: list[Quest]` from `GameState`. Remove `quest_updates: list[QuestUpdate]` from `ProgressExtractResult`. Remove `quest_updates` from `StateDelta`.

**Validation:** No import of `Quest`, `QuestUpdate`, `QuestObjective`, `QuestObjectiveUpdate` should remain anywhere in the codebase. `grep -r "QuestUpdate\|QuestObjective\|class Quest" ccya/` should return nothing.

#### Step 1.2 — Add arc models

**File:** `ccya/engine/models.py`

**What:** Add `ArcPhase`, `ThreadState`, `ThreadSignalType`, `ArcThread`, `CampaignArc`, `ThreadSignal` as described in the schema reference above. Add `arc: CampaignArc | None = None` to `GameState`.

**Validation:** `from ccya.engine.models import CampaignArc, ArcThread, ArcPhase, ThreadState` should import cleanly.

#### Step 1.3 — Add NPC motivation fields

**File:** `ccya/engine/models.py`

**What:** Add `motivation: str | None = None`, `fear: str | None = None`, `leverage: str | None = None` to `CompendiumNpcUpdate`.

**Why:** These are durable NPC identity fields, not turn-volatile attitude. They belong on `CompendiumNpcUpdate`, which is already the identity store for NPCs in the scene extractor. [See NPC chat decisions above.]

**Validation:** `CompendiumNpcUpdate` should now have fields: `id, name, title, bio, aliases, allegiance, motivation, fear, leverage`.

#### Step 1.4 — Add PC drive and expressed stances

**File:** `ccya/engine/models.py`

**What:** Add `drive: str | None = None` and `expressed_stances: dict[str, int] = {}` to the PC model.

**Validation:** `GameState.pc.drive` and `GameState.pc.expressed_stances` should be accessible with correct types.

#### Step 1.5 — Update StateDelta

**File:** `ccya/engine/models.py`

**What:** Remove `quest_updates` from `StateDelta`. Add `arc_update: CampaignArc | None = None` — this is used by the arc director (Phase 4) to write a modified arc back to state after the Python tail runs.

***

## Implementation — Phase 2: Seed generation

### Context files to load
1. `ccya/engine/seed.py`
2. `ccya/templates/seed_system.j2`
3. `ccya/templates/seed_user.j2`

### Overview
Generate a campaign arc scaffold as part of `generate_seed()`. The arc is generated by the seed LLM call (same call that generates PC, NPCs, location, and opening narrative), not by a separate LLM call. Add `PlayerOverrides` field for arc/drive hints. Write arc to `GameState.arc`.

### Detailed steps

#### Step 2.1 — Add arc to SeedEnvelope

**File:** `ccya/engine/models.py` (or `ccya/engine/seed.py` if SeedEnvelope lives there)

**What:** Add `arc: CampaignArc` as a required field on `SeedEnvelope`. The seed LLM is responsible for generating a valid `CampaignArc` including `visible_goal`, `thematic_question`, `phase=setup`, `hidden_truths`, and initial threads (2–3 active, 4–8 latent).

#### Step 2.2 — Add pc.drive to SeedEnvelope

**What:** Add `pc_drive: str` to the seed output — the player's starting drive as a single sentence. If the player provided `arc_hints` in `PlayerOverrides`, incorporate them. Otherwise generate from pack context.

**Why:** Drive is the one sentence the player always knows. It is more persistent than the visible_goal but narrower — it is about the PC's personal reason, not the objective.

#### Step 2.3 — Update seed_system.j2

**What:** Add instructions telling the seed LLM to generate:
- `arc.visible_goal`: one sentence, affirmative, player-visible
- `arc.thematic_question`: one sentence, e.g. "How much of yourself do you spend to save one life?"
- `arc.hidden_truths`: list of 2–4 strings, never shown until promoted
- `arc.active_threads`: 2–3 threads with `id`, `summary` (2–4 sentences), `tags`, `urgency=normal`, `unlock_if=null`, `promotes=[]`
- `arc.latent_threads`: 4–8 threads with `id`, `summary`, `tags`, `unlock_if` (plain-language condition), `promotes` (thread IDs)

Instruct that thread summaries should be **seeds for the narrator, not dictated plot**. They should describe a situation, not specify exact events. The narrator should always have creative latitude in how a thread manifests.

Example thread summary (good):
> "A hospital records clerk may know where the convoy was rerouted before the quarantine collapse. The archive floor is accessible but the building has been increasingly dangerous. Time is working against this lead."

Example thread summary (bad):
> "Go to Saint Mercy Hospital. Find Mara. She will give you Ledger B-7. Return to the checkpoint."

#### Step 2.4 — Update seed_user.j2

**What:** Add `arc_hints` and `drive_hint` to the player override block so players can seed or influence the generated arc at game creation.

#### Step 2.5 — Write arc to GameState in seed.py

**What:** After the seed LLM call, copy `envelope.arc` to `seed_state.arc`. Copy `envelope.pc_drive` to `seed_state.pc.drive`. Initialize `seed_state.pc.expressed_stances = {}`.

**Validation:** After `/new-game`, `state.yaml` should contain a populated `arc` block with `visible_goal`, `phase: setup`, `active_threads`, `latent_threads`.

***

## Implementation — Phase 3: Narrator integration

### Context files to load
1. `ccya/engine/narrate.py`
2. `ccya/templates/narrate_system.j2`
3. `ccya/templates/narrate_user.j2`

### Overview
Replace the `active_quests` block in the narrator prompt with a `current_arc` block. Add motivation/fear/leverage rendering to the `known_characters` block.

### Detailed steps

#### Step 3.1 — Add arc to narrate.py inputs

**File:** `ccya/engine/narrate.py`

**What:** Add `arc: CampaignArc | None` parameter to `_narrate_messages()`. Remove `active_quests` parameter. Build a `current_arc_ctx` dict:
```python
current_arc_ctx = {
    "visible_goal": arc.visible_goal if arc else None,
    "thematic_question": arc.thematic_question if arc else None,
    "phase": arc.phase.value if arc else None,
    "active_threads": [
        {"summary": t.summary, "urgency": t.urgency}
        for t in (arc.active_threads if arc else [])
    ],
}
```

Pass `current_arc_ctx` to both `narrate_system.j2` and `narrate_user.j2`.

#### Step 3.2 — Update narrate_system.j2

**What:** Replace the `{% if active_quests %}...{% endif %}` block with:

```jinja
{% if current_arc and current_arc.visible_goal %}
## Campaign Arc
The player's overarching goal: **{{ current_arc.visible_goal }}**
Thematic question (shapes tone, do not state directly): *{{ current_arc.thematic_question }}*
Current phase: {{ current_arc.phase }}

{% if current_arc.active_threads %}
### Active threads (situations in play — present narratively, do not announce them directly)
{% for thread in current_arc.active_threads %}
- [{{ thread.urgency | upper }}] {{ thread.summary }}
{% endfor %}
{% endif %}
{% endif %}
```

**Key instruction to add:** The narrator should **never announce threads as objectives** ("Your mission is to..."). Threads are narrative situations that should emerge naturally from the scene. The narrator has full creative latitude in how a thread manifests — as an NPC comment, an environmental detail, an overheard conversation, a timed pressure. Urgency is a tone guide, not a directive.

#### Step 3.3 — Update known_characters block in narrate_system.j2

**What:** Add motivation/fear/leverage rendering inside the `{% for npc in known_characters %}` block:

```jinja
{% if npc.motivation %}Motivation: {{ npc.motivation }}{% endif %}
{% if npc.fear %}Fear: {{ npc.fear }}{% endif %}
{% if npc.leverage %}Leverage: {{ npc.leverage }}{% endif %}
```

These fields allow the narrator to write NPC behavior consistently with their established durable identity across turns, without over-dictating how they act in a specific scene.

#### Step 3.4 — Update narrate_user.j2

**What:** Replace `active_quests` variable reference with `current_arc`.

#### Step 3.5 — Update turn.py

**What:** Pass `arc=state.get_arc()` (or equivalent) to `_narrate_messages()`. Remove `active_quests` argument.

***

## Implementation — Phase 4: Progress extractor

### Context files to load
1. `ccya/engine/progress.py`
2. `ccya/templates/extract_progress_system.j2`
3. `ccya/templates/extract_progress_user.j2`

### Overview
Replace `quest_updates` with `thread_signals`, `player_drift_signals`, and `candidate_opportunity` in `ProgressExtractResult`. Remove quest-specific inputs (`quest_ages`, `quest_threshold_directive`). Update the extractor prompt accordingly.

### Detailed steps

#### Step 4.1 — Update extract_progress_system.j2

**What:** Replace the entire quest instructions block with:

```
## thread_signals
For each active thread that was meaningfully touched this turn, emit a signal:
- "advanced": the narrative clearly moved this thread forward
- "blocked": an obstacle arose that explicitly impedes this thread
- "failed": the thread was definitively closed with a negative outcome
- "ignored": the player's action had nothing to do with this thread

Only emit signals for threads that were clearly relevant to this turn's narrative.
Do not emit a signal for threads that were merely background or coincidentally present.
Emit at most one signal per thread per turn.

## player_drift_signals
If the player's action suggests a new interest, concern, or direction not covered by active threads,
emit up to 3 short phrases describing it. Examples:
  "interested in the river docks"
  "avoiding militia contact"
  "focused on finding shelter"
Leave empty if the player is engaging with active threads normally.

## candidate_opportunity
If the narrative introduced a new potential hook (a person, place, object, or situation that
could become a future thread), describe it in one sentence. Leave null if nothing new emerged.
```

Remove all quest-specific instructions: `quest_ages`, stalled-quest detection, objective deduplication rules, `quest_threshold_directive`, new-quest aggressiveness guidance.

#### Step 4.2 — Update extract_progress_user.j2

**What:**
- Replace `active_quests` input block with a short `active_threads` summary (just IDs and first sentence of summary — keep it small)
- Replace the `quest_updates` output block with `thread_signals`, `player_drift_signals`, `candidate_opportunity`
- Remove `quest_ages` and `quest_threshold_directive` blocks

#### Step 4.3 — Update progress.py / _extract_progress_messages

**File:** `ccya/engine/progress.py`

**What:** Remove `quest_ages`, `quest_threshold_directive`, `active_quests` parameters. Add `active_threads` (summary of current arc active threads). Update message builder accordingly.

***

## Implementation — Phase 5: Arc director (Python)

### Context files to load
1. `ccya/engine/turn.py`
2. (new file) `ccya/engine/arc.py`

### Overview
Create `ccya/engine/arc.py` as the Python campaign director. It runs in the post-extraction tail (after `apply_delta()`), consuming `thread_signals` and `player_drift_signals` from `ProgressExtractResult`, and mutating `state.arc` directly. This keeps all campaign progression logic in Python, off the LLM extraction hot path.

### Detailed steps

#### Step 5.1 — Create arc.py

**File:** `ccya/engine/arc.py`

**What:** Implement `tick_arc(arc: CampaignArc, signals: list[ThreadSignal], drift: list[str], momentum: float, turn_no: int) -> CampaignArc`.

Responsibilities:
- **Thread advancement:** If a thread receives `advanced` twice (across cumulative turns), mark it `complete` and promote threads in its `promotes` list from `latent` to `active`.
- **Thread failure:** If a thread receives `failed`, mark it `failed`. Do not auto-promote — let the game continue without that thread.
- **Thread expiry:** If a thread has been `active` for 8+ turns with only `ignored` signals, mark it `expired` and promote the next highest-salience latent thread.
- **Salience scoring:** When promoting a latent thread, score candidates by:
  - tag overlap with recent `player_drift_signals`
  - tag overlap with current active thread tags
  - momentum bias: low momentum → prefer tags `["aid", "breathing_room", "ally", "resource"]`; high momentum → prefer tags `["cost", "complication", "deadline", "betrayal_risk"]`
  - recency: prefer threads not recently offered
- **Active thread cap:** Keep at most 3 active threads at once. If fewer than 2 are active and latent threads exist, promote until the cap is reached.
- **Arc engagement:** Increment `arc_engagement` when the player's drift signals overlap with active thread tags. Decrement when all signals are unrelated.

Return the mutated arc.

**Why Python, not LLM:** Thread promotion rules are simple boolean logic on tag sets and counters. Asking the LLM to make these decisions would add latency and introduce hallucination risk for what is essentially a state machine. Emily Short's storylet systems work exactly because eligibility and promotion are deterministic — only content generation is LLM-authored.

#### Step 5.2 — Wire arc director into turn.py

**File:** `ccya/engine/turn.py`

**What:** After `apply_delta()` in the Python tail, call:
```python
if state.arc and progress_result:
    state.arc = tick_arc(
        arc=state.arc,
        signals=progress_result.thread_signals,
        drift=progress_result.player_drift_signals,
        momentum=state.meta.momentum,
        turn_no=state.meta.turn,
    )
```

Then persist `state` as normal. The arc update is written as part of the regular `state.yaml` save.

#### Step 5.3 — Expressed stances update

**File:** `ccya/engine/arc.py` (or `turn.py`)

**What:** After applying the delta, update `state.pc.expressed_stances` based on the player's input and outcome. This is a simple heuristic — not extracted by LLM:

```python
STANCE_KEYWORDS = {
    "compassionate": ["help", "heal", "save", "comfort", "protect", "trust"],
    "ruthless":      ["kill", "threaten", "abandon", "betray", "steal", "use"],
    "defiant":       ["refuse", "resist", "defy", "challenge", "reject", "ignore"],
    "cautious":      ["hide", "wait", "observe", "avoid", "sneak", "plan"],
}

def update_stances(stances: dict[str, int], user_input: str) -> dict[str, int]:
    lower = user_input.lower()
    for stance, keywords in STANCE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            stances[stance] = stances.get(stance, 0) + 1
    return stances
```

This is intentionally naive. It does not require extraction. It accumulates over time and gives the narrator a loose characterization signal without needing per-turn LLM inference.

***

## Implementation — Phase 6: Scene extractor NPC fields

### Context files to load
1. `ccya/templates/extract_scene_system.j2`
2. `ccya/templates/extract_scene_user.j2`

### Overview
Add `motivation`, `fear`, and `leverage` to the scene extractor's `compendium_npc_update` output block.

### Detailed steps

#### Step 6.1 — Update extract_scene_system.j2

**What:** Add to the `compendium_npc_update` instructions:

```
motivation (str | null): What this NPC fundamentally wants. Not what they want from the player right now — their persistent underlying drive. Set when first established or if clearly revealed this turn.
fear (str | null): What this NPC is most afraid of losing or having happen. Set when established or revealed.
leverage (str | null): What this NPC can offer, threaten, or withhold. Set when established or revealed.

These fields are durable and persistent — only update them if the narrative clearly establishes or revises them. Do not infer them from a single interaction unless they are strongly implied.
```

#### Step 6.2 — Update extract_scene_user.j2

**What:** Add `motivation`, `fear`, `leverage` to the `compendium_npc_update` JSON output example.

***

## Implementation — Phase 7: State migration and cleanup

### Context files to load
1. `ccya/engine/state.py` (if it handles migration)
2. `saves/default/state.yaml` (any active save)

### Overview
Existing save files will have a `quests` key and no `arc` key. The engine should handle missing `arc` gracefully (treat as `None`). A one-time migration note should be documented.

### Detailed steps

#### Step 7.1 — Handle missing arc in GameState

**What:** Ensure `arc: CampaignArc | None = None` in `GameState` so existing saves without an arc field load without error. The first turn played without an arc will simply not show arc context — the narrator renders a no-arc fallback (skip the `current_arc` block if `None`).

#### Step 7.2 — Remove quests key from active saves

**What:** For active development saves, manually remove the `quests:` key from `state.yaml`. No automated migration needed — this is dev-only state.

#### Step 7.3 — Remove quest scope domain

**File:** `ccya/templates/narrate_system.j2` (scope domain table), `docs/ARCHITECTURE.md`

**What:** Remove `quest_updates` from the scope domain table. It is no longer a valid active_domain. The narrator should not emit `quest_updates` in the `<scope>` tail.

***

## Scope domain table after this plan

| Domain | Extractor(s) triggered | Condition for emission |
|---|---|---|
| `scene` | 2a | NPC enters/leaves narration, NPC situation shifts |
| `location_change` | 2a | Player physically moves |
| `inventory` | 2b | Items received, used, dropped |
| `pc_condition` | 2b | Wounds, fatigue, mental conditions |
| `recent_events` | 2c | Narratively significant new world fact |
| `compendium_npc` | 2a | NPC named first time, identity change, death |

`quest_updates` is removed. Progress always runs; the thread_signals extraction replaces the quest domain gate entirely.

***

## Firm decisions
1. Quests (`Quest`, `QuestUpdate`, `QuestObjective`) are removed entirely. No backward compatibility.
2. Arc scaffold is generated once at seed time by the existing seed LLM call — not a separate LLM call.
3. Thread summaries are 2–4 sentences: enough narrative material for the narrator, not scripted plot.
4. Thread promotion is Python-only: tag matching + salience scoring, no LLM involvement.
5. NPC motivation/fear/leverage is flavor-only: flows to narrator via `known_characters`, not to Step 0.
6. PC expressed stances are keyword-heuristic, not extracted by LLM.
7. Arc abandonment, drift counters, and thread failure mutation are deferred.
8. `check.tags` dead schema is left alone by this plan (separate cleanup item).

## Ambiguities requiring resolution before execution
1. **Does `SeedEnvelope` live in `models.py` or `seed.py`?** Verify before writing Phase 2 changes.
2. **What is the exact Pydantic model for PC stats?** Verify `drive` and `expressed_stances` can be added without breaking stat validation (total 12–16, 6 stats).
3. **Does `_extract_progress_messages` in `progress.py` or `turn.py`?** Verify which file owns the message builder for Step 2c before Phase 4.
4. **Does the narrator prompt currently use `{% if active_quests %}` or is it always rendered?** Verify before writing the Phase 3 replacement block so the conditional structure matches.