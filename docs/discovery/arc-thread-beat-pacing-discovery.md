# Discovery: Arcs, Threads, Beats, and Pacing

> **Purpose:** Fact-finding spec sheet of how arcs, threads, beats, urgency, and pacing currently work, combined with the goals and requirements stated for the next design phase. No solutions — just the current state and the problems to solve.

---

## 1. Current State: Arcs and Threads

### 1.1 Data Models

**`ArcThread`** (`ccya/models.py:35-61`)
- `id`: str — 2–4 word conceptual bucket, no proper nouns
- `summary`: str — situation description, not an objective
- `active`: bool — True = active, False = latent/dormant
- `urgency`: `background` | `normal` | `urgent`
- `progress`: list[ProgressEntry] — append-only, kind: `advancement` | `setback` | `shift`
- `resolution_state`: str | None — `resolved` | `failed` | `abandoned`
- `outcome`: str | None — past-tense sentence at resolution
- `resolved_turn`: int | None
- `last_updated_turn`: int | None — drives auto-latent demotion
- `added_turn`: int | None
- `urgency_set_turn`: int | None — drives urgency decay

**`CampaignArc`** (`ccya/models.py:64-71`)
- `visible_goal`: str — chapter-level goal
- `goal_context`: str — UI-only tooltip, never sent to LLM
- `threads`: list[ArcThread] — active threads
- `completed_threads`: list[ArcThread] — resolved/failed/abandoned
- `resolution`: str | None
- `last_thread_created_turn`: int

**`ThreadUpdate`** (`ccya/models.py:411-416`) — Storyteller output
- `id`, `active`, `urgency`, `progress`, `progress_kind`

**`ThreadResolution`** (`ccya/models.py:403-408`)
- `id`, `resolution_state`, `outcome`, `promote_to_world_state`

**`ArcResolution`** (`ccya/models.py:419-424`)
- `resolution`, `visible_goal`, `goal_context`, `drop_threads`, `new_threads`

### 1.2 Thread Lifecycle

1. **CREATE** (`thread_add`) — Storyteller emits with id, summary, urgency. Engine sets `added_turn` and `urgency_set_turn`. Hard limit: 2 active at game start. Runtime max: 5 active (`thread_max_active`).

2. **UPDATE** (`thread_update`) — Storyteller emits with id + optional fields. Progress is always appended (70% SequenceMatcher dedup). Auto-latent demotion: untouched for `thread_stale_threshold=3` turns → `active=False`. Urgency decay: `urgent→normal→background` after `thread_urgency_max_age=8` turns at same level.

3. **RESOLVE** (`thread_resolve`) — Storyteller emits with id, resolution_state, outcome. Thread moves from `threads[]` to `completed_threads[]`. Resolution states: `resolved`, `failed`, `abandoned`.

4. **PURGE** — No standalone purge mechanism. Completed threads pruned from prompt context after `thread_memory_ttl=3` turns. **There is no way to drop a thread from the active list except via `thread_resolve` or `arc_resolve` (which resets the entire arc).**

### 1.3 Arc Lifecycle

1. **CREATE (seed)** — Created via pack's `arc_categories` pool selection or LLM-generated in `generate_seed()`. Contains initial `visible_goal` and pre-seeded threads (1–2 active, up to 3 latent, total 4–5).

2. **UPDATE (mid-arc)** — `goal_update`: direct `visible_goal` change without ending arc. Applied directly to state dict, NOT through `_merge_arc_update`.

3. **RESOLVE** (`arc_resolve`) — Current arc stored in `resolved_arcs[]` with TTL. Successor arc created with new `visible_goal` and empty threads (minus dropped threads). No automatic arc-scoped thread resolution in current code.

4. **TTL Cleanup** — Resolved arcs appear in prompts for `arc_memory_ttl=3` turns.

### 1.4 Engine Processing (Arc Director) — `turn.py:1192-1291`

Processing order:
1. `chapter_end` signal (records turn, no state mutation)
2. `_apply_thread_updates` — merge `thread_update[]` into active threads
3. `goal_update` — direct dict assignment
4. Same-turn conflict detection: `thread_update` + `thread_resolve` for same ID → warning
5. `_apply_arc_resolve` — resolve arc, create successor
6. `_apply_thread_resolutions` — move resolved threads to `completed_threads[]`
7. `thread_add` — add new thread if under `thread_max_active`

### 1.5 Thread Sanitizer — `thread_sanitizer.py`

Runs every `sanitize_every=5` turns (configurable, 0=disabled). Independent LLM call that reviews threads against recent narration evidence. Returns structured JSON with `goal_update`, `thread_updates`, `resolved_threads`, `new_threads`. Validates against Pydantic models, applies changes to state.

Sanitizer prompt (`sanitize_thread.j2`) instructs:
- Per-thread checks: resolved? urgency wrong? latent/activated? progress noisy?
- Temporal decay: inactive threads with no progress for 3+ turns → resolve or remove
- Progress consolidation: 3+ entries on same subject → fold into one
- Thread count: target 3–4, merge overlapping, demote on-hold
- Arc goal: do NOT pivot visible_goal when thread resolved/failed/changed urgency; DO when main objective impossible, revelation invalidates goal, situation changed drastically, or 8+ turns without progress

### 1.6 Prompt Rendering

**`_thread_list.j2`** (7 lines) — Shared include:
- Shows: ID, `(latent)` marker, urgency in brackets, summary, turns-since-update, progress entries
- Stale filter: threads not updated for > 2 turns are hidden
- Target: "3-4, ~5 total"

**`_arc.j2`** (22 lines):
- Campaign arc goal, resolution, previously resolved arcs (TTL, truncated to 120 chars), completed threads (capped at 15, shows urgency and resolved turn)

### 1.7 How Threads/Arcs Are Surfaced

| Agent | What they see | How |
|-------|--------------|-----|
| **Ruling** | Only **urgent** threads (id, summary, last 3 progress entries) | `ruling_user.j2` — "Urgent Threads" section |
| **Narrator** | Active threads (latent filtered out), arc goal, completed threads (TTL) | `narrate_user.j2` — `_thread_list.j2` include, `_arc.j2` include, "Past Resolutions" section |
| **Storyteller** | **All threads** (active + latent), arc goal, completed threads (TTL), pacing context, scene phase, allowed beat types, pending beat, recent beats, curtain call | `storytell_user.j2` — `_arc.j2` include, `_thread_list.j2` include, pacing/phase/beat sections |
| **Sanitizer** | All threads, completed threads, recent narration (5 turns), prior history | `sanitize_thread.j2` — `_thread_list.j2` include, narration context |
| **UI (sidebar)** | Active threads (urgency-based CSS, progress tooltip), completed threads (last 20, outcome tooltip), resolved arcs (last 5) | `_state_left.html` |
| **UI (turn review)** | Thread changes (added/updated/resolved/failed/abandoned/removed), arc resolution | `tv.py` |

### 1.8 UI Display

**Left sidebar** (`_state_left.html`):
- Active threads: only `active == true`, sorted reverse (newest first), urgency-based CSS classes (`arc-thread-urgent`, `arc-thread-building`), progress in tooltip
- Completed threads: last 20, reverse order, outcome in tooltip
- Resolved arcs: last 5, resolution text truncated to 120 chars

**Turn review** (`tv.py`):
- Thread changes: `thread_update` (id:urgency), `arc_resolve` (resolved: text), `thread_resolve` (id: state), `thread_add` (id: summary)
- Sanitizer diffs: update/add operations with field-level before/after

### 1.9 Configuration

| Field | Default | Purpose |
|-------|---------|---------|
| `thread_stale_threshold` | 3 | Turns before auto-latent demotion |
| `thread_max_active` | 5 | Max active threads before oldest evicted |
| `thread_urgency_max_age` | 8 | Turns before urgency demotion (urgent→normal→background) |
| `thread_memory_ttl` | 3 | TTL for completed threads in prompts |
| `arc_memory_ttl` | 3 | TTL for resolved arcs in prompts |
| `sanitize_every` | 5 | Turns between sanitizer runs (0=disabled) |
| `sanitize_temperature` | 0.3 | LLM temperature for sanitization |
| `scene_pressure_threshold` | 3 | Scene Pressure directive threshold |
| `scene_imperative_threshold` | 4 | Scene Imperative directive threshold |

### 1.10 Known Problems (from `arc-thread-conflation.md`)

- **Arcs resolve every 1–6 turns** when thread IDs change, ignoring the prompt's "target cadence: 8–15 turns" guidance
- **Arc resolution fires on thread lifecycle events** rather than genuine chapter-ending moments
- **Root cause:** `drop_threads` only exists inside `arc_resolve`. The LLM has no way to drop stale threads without resolving an arc. It's forced to conflate thread management with chapter ending.
- **Arcs vs threads are related but distinct:** threads are specific tensions, arcs are chapter-level goals. Thread lifecycle doesn't drive arc lifecycle, but mechanics force conflation.
- **Thread resolution rate drops to 0%** because arcs keep resetting, losing thread history
- **Game feels like it's constantly restarting its chapter** without actually ending

### 1.11 Pack-Level: `arc_categories`

Packs define `arc_categories` as pool entries (id + tags). During seed generation, one is selected via `_select_from_pool()` and used to inform the `visible_goal` and thread generation. Currently, `arc_categories` are just thematic buckets (e.g., `power_struggle`, `resource_scarcity`, `collapse_conspiracy`) — they have no semantic type distinction (threat/opportunity/revelation).

---

## 2. Current State: Threats (Urgency System)

### 2.1 No Standalone Threat Model

There is **no** `Threat` model. The concept of "threat" has been **fully absorbed into the thread urgency system** via `ArcThread.urgency` (values: `background`, `normal`, `urgent`).

### 2.2 How Urgency Functions as Threat Signal

- `urgent` threads count toward `thread_urgency_count`
- `thread_urgency_count` drives:
  - Phase transitions (SETUP→RISING when count > 0)
  - Convergence score components (≥1 urgent = +1, ≥2 urgent = +1)
  - Ruling prompt (urgent threads listed separately)
  - Directive computation (Scene Imperative/Scene Pressure thresholds)
- Urgency decay: Python-enforced stepwise demotion `urgent→normal→background` after 8 turns at same level
- Seed enforcement: at most 2 active threads at game start, non-active threads never `urgent`

### 2.3 Old Threat System (Removed)

The historical system (`threat_ages`, `threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at`, `_compute_threat_ages()`) has been **completely removed**. Only referenced in dead code comments and plan docs.

### 2.4 Where "Threat" Appears in Code Today

- Dead code comment in `context.py:224` (references removed fields)
- NPC leverage descriptions: "what they can offer, threaten, or withhold"
- Intent verb mappings: "intimidate/threaten → intimidate"
- Personality definitions (speech hints)
- Scenario thread IDs/tags in packs (e.g., `infection_threat`, `outside_threat_escalation`)
- Eval state.yaml narrative text

---

## 3. Current State: Beat Types

### 3.1 Beat Types and Categories

**`GMBeat.type`**: `complication` | `revelation` | `opportunity` | `breathing_room` | `pressure` | `twist` | `setback` | `escalation` | `callback`

**`BEAT_BUCKETS`** (`_pacing.py:17-21`):
- `pressure`: pressure, complication, escalation, setback
- `situation`: revelation, twist, hazard, callback
- `relief`: opportunity, breathing_room

### 3.2 Phase-to-Beat Mapping (`BEAT_PHASE_MAP`)

| Phase | Allowed Beat Types |
|-------|-------------------|
| SETUP | All 9 (open world) |
| RISING | pressure, complication, escalation, revelation, twist |
| CLIMAX | pressure, escalation, complication |
| RESOLUTION | breathing_room, callback, revelation |
| BREATHER | opportunity, revelation, callback, breathing_room, hazard |

### 3.3 Beat Lifecycle

1. **Emit**: Storyteller outputs `gm_beat: {"type": "...", "surface_as": "..."}` constrained to `allowed_beat_types`
2. **Store**: `pending_gm_beat` set with `beat_expires_turn = turn_no + 2`
3. **Consume**: Narrator receives `pending_gm_beat` next turn, integrates into prose
4. **Expire**: If `turn_no > beat_expires_turn`, `pending_gm_beat` cleared
5. **Replace**: New storytell beat replaces old; null storytell pops `pending_gm_beat`
6. **Record**: `recent_beats.append()` (capped at 5, most-recent-first)

### 3.4 How Beats Are Surfaced

| Agent | What they see | How |
|-------|--------------|-----|
| **Narrator** | `pending_gm_beat` (type, surface_as), `outcome_hint`, `spiral_detected` | `narrate_user.j2` — "Beat" section, "Outcome" section, "Spiral" section |
| **Storyteller** | `pending_beat` (from previous turn), `recent_beats` (history), `allowed_beat_types`, `scene_phase`, `pacing_context` | `storytell_user.j2` — "GM Beat" section, "Recent Beats" section, "allowed_beat_types" reminder |
| **UI (turn viewer)** | `gm_beat_type`, `gm_beat_surface_as`, `gm_beat_allowed_beat_types` | `_turn_viewer.html` |
| **UI (debug)** | Beat type/surface_as inline | `index.html` debug metadata row |

### 3.5 Beat Diversity and Constraints

- System prompt: "Don't repeat the same beat type more than twice consecutively. Vary surface_as turn to turn."
- `derive_allowed_beat_types()`: Scene Imperative directive overrides phase defaults to `["revelation", "hazard", "callback", "opportunity", "setback", "breathing_room"]` (situation-changers + relief)
- Death spiral: removes pressure bucket from phase defaults
- Roll band guidance: success → reward/reveal, partial → tension/obstacle, fail → recovery, no roll → neutral/discovery

---

## 4. Current State: Pacing System

### 4.1 Phase Engine

**5-state machine**: SETUP → RISING → CLIMAX → RESOLUTION → BREATHER → RISING

| Transition | Condition |
|------------|-----------|
| SETUP → RISING | Urgent thread appears |
| RISING → CLIMAX | convergence_score ≥ threshold (default 3) |
| CLIMAX → RESOLUTION | climax_turn_count ≥ limit (default 4) |
| RESOLUTION → BREATHER | Always (1-turn transition) |
| BREATHER → RISING | Urgent thread appears OR breather_max_turns (3) elapsed |

### 4.2 Convergence Score (5-component, 0–5)

| Component | Condition | Lines |
|-----------|-----------|-------|
| Thread weight | `thread_urgency_count >= 1` | +1 |
| Urgency depth | `thread_urgency_count >= 2` | +1 |
| Scene age | `scene_age >= scene_pressure_threshold (3)` | +1 |
| Beat streak | 60%+ of last 5 beats are pressure types | +1 |
| Dice weight | Failed/crit_fail roll + `thread_urgency_count >= 1` | +1 |

Threshold: `config.convergence_threshold` (default 3). Score cannot reach threshold without at least one urgent thread.

### 4.3 PacingContext

```
PacingContext:
  directive: str           # "Scene Imperative" | "Scene Pressure" | ""
  outcome_hint: str | None # "hold" | "transition" (from ruling, overridden by scene age)
  summary: str             # Human-readable log, never sent to LLM
  spiral_detected: bool    # Death spiral flag from recent rolls
  convergence_score: int   # 0-5 score for RISING→CLIMAX transition
  convergence_components: dict[str, int]
```

### 4.4 Curtain Call (CLIMAX Phase Soft Close)

| Tier | Trigger | Signal |
|------|---------|--------|
| Active | Turn 1 of CLIMAX | `curtain_call: "active"` — "MUST resolve the active thread this scene" |
| Forced | Turn ≥ climax_turn_limit - 1 | `curtain_call: "forced"` — "This thread MUST resolve now" |

### 4.5 How Pacing Is Computed (Per Turn)

1. Ruling phase: intent + outcome (roll band), appends to `recent_rolls`
2. Narrate setup:
   - Expire stale beats
   - Compute `thread_urgency_count` from `arc.threads[]`
   - Compute `scene_age` via `_compute_ages()`
   - Compute `convergence_score` via `compute_convergence_score()`
   - Compute `scene_phase` via `_compute_scene_phase()` (5-state machine)
   - Compute `directive` via `_compute_narration_directive()` (scene age-based priority stack)
   - Compute `pacing_context` (directive, outcome_hint, spiral, convergence)
3. Extraction: storytell receives `pacing_context`, `scene_phase`, `allowed_beat_types`, `pending_beat`, `recent_beats`
4. Beat lifecycle: new beat stored, `recent_beats.append()`

### 4.6 How Pacing Is Surfaced

| Agent | What they see | How |
|-------|--------------|-----|
| **Narrator** | `outcome_hint` (advance/transition/hold), `pending_gm_beat`, `spiral_detected` | `narrate_user.j2` — "Outcome" section, "Beat" section, "Spiral" section |
| **Storyteller** | `directive`, `outcome_hint`, `scene_phase`, `allowed_beat_types`, `pending_beat`, `recent_beats`, `curtain_call` | `storytell_user.j2` — "pacing_context", "Scene phase", "GM Beat", "Recent Beats", "Curtain Call" sections |
| **UI (turn viewer)** | `scene_phase`, `climax/breather turn counts`, `summary`, `outcome_hint`, `convergence_score`, `convergence_components` | `_turn_viewer.html` |
| **UI (debug)** | `scene_phase`, `gm_beat` (type/surface_as), `outcome_hint`, `summary` | `index.html` debug metadata row |

### 4.7 Configuration

| Field | Default | System |
|-------|---------|--------|
| `convergence_threshold` | 3 | Phase Engine (RISING→CLIMAX) |
| `climax_turn_limit` | 4 | Phase Engine (CLIMAX→RESOLUTION) |
| `breather_max_turns` | 3 | Phase Engine (BREATHER→RISING) |
| `scene_pressure_threshold` | 3 | Pacing Context (Scene Pressure directive) |
| `scene_imperative_threshold` | 4 | Pacing Context (Scene Imperative directive) |
| `recent_beats_max` | 5 | GM Beats (recent_beats history cap) |
| `spiral_consecutive_hard` | 3 | Death spiral (consecutive threshold) |
| `spiral_hard_ratio` | (3, 5) | Death spiral (ratio threshold) |

---

## 5. How Everything Flows Through the Turn Pipeline

### 5.1 Full Pipeline (5 Calls + Arc Director)

```
Player input
  ↓
Step 0: Ruling — intent + outcome (roll band, directive)
  ↓
Narrate Setup (turn.py:723-853):
  - Expire stale beats
  - Compute thread_urgency_count
  - Compute scene_age
  - Compute convergence_score (5 components)
  - Compute scene_phase (5-state machine)
  - Compute directive (scene age-based)
  - Compute pacing_context (directive, outcome_hint, spiral, convergence)
  ↓
Step 1: Narrate — prose generation (receives pending_gm_beat, pacing_context)
  ↓
Step 2a: Scene Extract — scene_tagline, location_change, compendium_npc_update
  ↓
Step 2b: State Extract — inventory deltas, condition add/remove
  ↓
Step 2c: Storytell Extract — thread ops, arc_resolve, goal_update, gm_beat, actions
  (receives: pacing_context, scene_phase, allowed_beat_types, pending_beat, recent_beats, threads, arc)
  ↓
Arc Director (turn.py:1192-1291):
  1. chapter_end signal
  2. _apply_thread_updates (progress, urgency decay, auto-latent)
  3. goal_update (direct dict assignment)
  4. _apply_arc_resolve (resolve arc, create successor, carry threads)
  5. _apply_thread_resolutions (move to completed_threads)
  6. thread_add (dedup, cap eviction)
  ↓
Beat lifecycle: store pending_gm_beat, recent_beats.append()
  ↓
Thread sanitizer (if turn % sanitize_every == 0): independent LLM call
  ↓
State delta → change summarization → UI display → persist
```

### 5.2 Cross-Module Data Flow

```
arc.threads[].urgency
  → thread_urgency_count
    → convergence_score (components 1, 2)
      → RISING→CLIMAX transition
        → scene_phase
          → allowed_beat_types (BEAT_PHASE_MAP)
            → storytell gm_beat selection
              → pending_gm_beat
                → narrator prose integration

scene_age
  → directive (Scene Imperative/Scene Pressure)
    → pacing_context
      → storytell thread/beat guidance
      → narrator outcome_hint override

recent_beats
  → convergence_score (component 4: beat streak)
    → RISING→CLIMAX transition
  → storytell diversity awareness
    → beat type selection
```

### 5.3 What Each Agent Controls

| Agent | Controls | Cannot Control |
|-------|----------|----------------|
| **Ruling** | Dice outcome, band, intent classification | Thread state, arcs, beats, pacing |
| **Narrator** | Prose, beat integration, outcome narration | Thread ops, arc resolution, beat emission |
| **Storyteller** | thread_add, thread_update, thread_resolve, arc_resolve, goal_update, chapter_end, gm_beat, actions | Dice outcome, prose, ruling |
| **Sanitizer** | Batch thread cleanup, goal updates, new threads (every N turns) | Dice, prose, ruling, beat emission |
| **Engine (Python)** | Urgency decay, auto-latent demotion, thread cap, progress dedup, phase transitions, convergence score, beat expiry | Thread creation, arc resolution, beat type selection |

### 5.4 What the LLM Sees (Prompt Context by Agent)

**Narrator sees:**
- Player Character, Inventory, Location, Characters, World State, Immutable Reference, Scene Context, Scene phase, Prior History, Recent Turns, Campaign Arc (goal, threads, completed threads, resolved arcs), This Turn's Result, Player Input, Directives (outcome_hint, spiral)

**Storyteller sees:**
- Inventory, Conditions, NPCs, Location, Campaign Arc (goal, threads, completed threads, resolved arcs), World State, Pacing Context (directive, outcome_hint), Scene Phase + allowed beat types, Curtain Call, GM Beat (pending), Recent Beats, Rules Outcome (band), Prior History, Recent Turns, Player Intent, Current Turn Narration

**Ruling sees:**
- Player Input, Urgent Threads (only), NPCs, Inventory, Recent Turns, Scene Phase

---

## 6. Goals and Requirements for Next Design Phase

### 6.1 Semantic Thread Types (Replacing Urgency)

**Goal:** Move away from urgency-based models (background/normal/urgent) toward semantic models like threat, opportunity, revelation, or similar categories.

**Considerations:**
- Should semantic types go hand-in-hand with beat types and be tied to beats somehow?
- Should they combine existing threats (urgency) with recent beats given by the storyteller?
- How do semantic types differ from or relate to `arc_categories` (which are already thematic buckets)?
- Should threads have a semantic type field, or should the type be derived from context (beats + recent activity)?

### 6.2 Pacing Signals from Semantic Types and Recent Beats

**Goal:** Use thread semantic types and recent beat history as pacing signals.

**Examples stated:**
- A "threat" is naturally considered urgent
- An "opportunity" is not urgent
- Out of a five-turn window, three pressure or comp-action beats assigned to progress the phase could signal pacing
- Still may have version CS9 (active vs background), but that's TBD

**Considerations:**
- How do semantic types map to urgency-like signals?
- Should recent beat composition (pressure ratio, relief ratio, situation ratio) drive pacing differently than current convergence score?
- Should the 5-component convergence score be replaced, augmented, or kept alongside new signals?
- Should pacing be computed from thread semantics + beat history rather than (or in addition to) urgency counts?

### 6.3 Clarify Purpose of Arcs, Arc Summaries, Threads, and Thread Progress Updates

**Goal:** Define what arcs, arc summaries, threads, and thread progress updates actually are/represent.

**Questions:**
- Are they objectives? Notes? Facts?
- Right now there's a lot of overlap — they're all of those things simultaneously
- Should arcs be purely chapter-level objectives with clear resolution criteria?
- Should threads be tracking specific tensions with independent lifecycle?
- Should arc summaries be separate from arc goals (like `resolution` vs `visible_goal`)?
- Should thread progress be factual records, narrative summaries, or both?

### 6.4 Organic Thread Drop/Abandonment

**Goal:** Allow threads to be dropped or abandoned over time in an organic way, without automatic removal.

**Considerations:**
- Current problem: no standalone way to drop threads except via `thread_resolve` or `arc_resolve` (which resets the entire arc)
- Should there be a `thread_drop` or `thread_archive` operation separate from `thread_resolve`?
- Should the sanitizer have more aggressive drop capabilities?
- Should threads naturally "fade" based on recency, narrative relevance, or both?
- How do we avoid automatic removal while still allowing organic decay?
- Should there be a concept of "abandoned" threads that are distinct from "failed" or "resolved" threads?

### 6.5 No Solutions Required

This discovery document is **not** asking for solutions. It is a fact-finding spec sheet of the current state and a statement of the goals/requirements. Design solutions come next, after this document is reviewed and any ambiguities are clarified.

---

## 7. Key Files Reference

| File | What it contains |
|------|------------------|
| `ccya/models.py:35-71, 403-424, 468-479` | ArcThread, CampaignArc, ThreadUpdate, ThreadResolution, ArcResolution, StorytellerResult |
| `ccya/engine/turn.py:112-331, 1192-1291` | _apply_thread_updates, _apply_arc_resolve, _apply_thread_resolutions, arc director |
| `ccya/engine/_pacing.py:1-131` | BEAT_BUCKETS, BEAT_PHASE_MAP, detect_spiral, derive_allowed_beat_types, compute_convergence_score |
| `ccya/engine/thread_sanitizer.py` | sanitize_threads() — batch LLM-driven cleanup |
| `ccya/prompts/sections/_arc.j2` | Arc rendering in prompts |
| `ccya/prompts/sections/_thread_list.j2` | Thread list rendering in prompts |
| `ccya/prompts/sanitize_thread.j2` | Sanitizer prompt template |
| `ccya/prompts/storytell_system.j2` | Storyteller system prompt (thread ops, arc resolution, beat guidance) |
| `ccya/prompts/storytell_user.j2` | Storyteller user prompt (threads, arc, pacing, beats, phase) |
| `ccya/prompts/narrate_user.j2` | Narrator user prompt (threads, arc, pacing, beats, outcome) |
| `ccya/prompts/ruling_user.j2` | Ruling user prompt (urgent threads) |
| `ccya/prompts/generate_seed_system.j2` | Seed generation prompt (arc categories, thread rules) |
| `ccya/prompts/context.py:77-150` | ArcThreadSummary, ArcThreadBlock for prompt rendering |
| `ccya/engine/config.py:160-178` | Thread/arc/pacing config fields |
| `ccya/state/delta_builder.py:52-67` | _merge_arc_update |
| `ccya/state/io.py:89-96` | State structure (arc, resolved_arcs) |
| `ccya/engine/seed.py:119-139, 359-389` | Arc category selection, thread urgency enforcement at seed |
| `ccya/pack.py:155` | ScenarioBrief.arc_categories field |
| `ccya/ev/checkers/threads.py` | thread_lifecycle checker |
| `ccya/ev/checkers/arc_goals.py` | arc_goal_updates checker |
| `ccya/ev/checkers/arc_resolution_validity.py` | arc_resolution_validity checker |
| `ccya/ev/checkers/thread_resolution_validity.py` | thread_resolution_validity checker |
| `ccya/ev/checkers/new_thread_validity.py` | new_thread_validity checker |
| `ccya/ev/checkers/pacing.py` | pacing_directives checker |
| `ccya/ev/checkers/beat_phase_validity.py` | beat_phase_validity checker |
| `ccya/ev/checkers/recent_beats.py` | recent_beats checker |
| `ccya/ev/checkers/sanitizer.py` | sanitizer_lifecycle checker |
| `ccya/templates/_state_left.html:75-130` | Thread/arc display in sidebar |
| `ccya/server/tv.py:235-265` | Thread display in turn review UI |
| `docs/discovery/arc-thread-conflation.md` | Eval findings on arc-thread conflation |
| `docs/discovery/arc-thread-system.md` | Arc and thread system documentation |
| `docs/architecture/pacing-systems.md` | Pacing systems documentation |
