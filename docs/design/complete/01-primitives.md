# Primitives Document

> **Status:** scoping
> **Related designs:**
> - [02-Arc System Redesign](./02-arc-system-redesign.md)
> - [03-Seed Worldbuilding Redesign](./03-seed-worldbuilding-redesign.md)
>
> **Discovery/evidence:** [Arc System — Discovery](../discovery/arc-system-problems.md)

This document captures all shared building blocks that both the arc system redesign
and the seed worldbuilding redesign depend on. It is the canonical reference for:
- Field renames and deletions
- TTL strategy
- Pressure score system
- Age tracking
- `pc.situation` primitive definition
- Execution order

Both other design docs reference this document, not each other, for shared concepts.
This eliminates circular dependencies and ensures a single source of truth.

## Execution Order

**Primitives → Arc System → Seed Worldbuilding.**

The primitives document defines shared building blocks. The arc system redesign defines
`arc_origin`, `long_term_objective`, and thread→world state promotion. The seed
worldbuilding redesign depends on those definitions.

This order ensures that when the arc system plan is written, all shared primitives are
already defined. When the seed worldbuilding plan is written, both primitives and arc
system are already defined.

## Field Renames and Deletions

### Renames

| Old Field | New Field | Scope | Rationale |
|-----------|-----------|-------|-----------|
| `progress` | `major_updates` | ArcThread model, prompts, packs | "Major" signals "only when something worth noting happens." Not a running play-by-play. |
| `visible_goal` | `long_term_objective` | CampaignArc model, ArcResolution, StorytellerResult, prompts, packs | "Long-term" signals update frequency and duration. "Objective" avoids immediate-completion trigger. |
| `arc` (state key) | `long_term_objective` (state key) | `state/io.py _default_state()`, all engine code reading `state["arc"]`, all prompt context builders, all Jinja2 templates referencing `current_arc` | Consistent with LLM-naming principle; the state key should match the model name and signal duration to the LLM. |
| `CampaignArc` (model name) | `LongTermObjective` (model name) | `state.py:79-85`, all imports, `turn_state.py`, `thread_sanitizer.py`, `seed.py`, `extraction.py`, `narrate.py`, `ruling.py` | Same rationale as state key rename. UI displays as "Objective." |
| `goal_context` | `arc_origin` | Seed state model, prompts, UI | "How did the PC end up here?" Past tense, 2–3 sentences. Seed-time field only, never regenerated. |
| `progress_kind` | `major_update_signal` | ProgressEntry in ArcThread | "Signal" is more descriptive. Values: `advancement` / `setback` only. |

### Deletions

| Field | Scope | Reason |
|-------|-------|--------|
| `chapter_end` | CampaignArc, prompts, packs, engine | No behavioral effect. Added as patch for arc_resolve misuse. Adds cognitive load. |
| `promote_to_world_state` | ThreadResolution model | Replaced by two-step candidate system. Currently active in turn_state.py:341-349 (applies to `state["scene"]["world_state"]`), to be removed. |
| `goal_context` (all references) | CampaignArc, _default_state(), StorytellerResult, sanitizer schema, turn_state.py, audit.py, eval checkers, Jinja2 templates, PC UI panel | Replaced by `arc_origin`. No backward compatibility. |
| `ArcResolution.drop_threads` | `state.py:185`, `turn_state.py:235-243`, `storytell_system.j2:14` | Threads carry forward automatically on arc resolution. Arc and thread lifecycles are fully decoupled. Explicit dropping removed. |
| `ArcResolution.new_threads` | `state.py:186`, `turn_state.py:264-270`, `storytell_system.j2:14` | Thread creation is decoupled from arc resolution. Storyteller emits `thread_add` independently on any turn. No special thread-creation moment tied to arc resolution. |
| `turns_since` warning guard | `turn_state.py:225-233` | Soft warning block deleted entirely. No replacement. Consistent with no-hard-floors principle; hint tiers handle arc resolution frequency. |

### Kept (previously proposed for deletion)

| Field | Scope | Reason |
|-------|-------|--------|
| `urgency_set_turn` | ArcThread model | Actively read and written in turn_state.py:140,153,595 and seed.py:371-384. Used for urgency decay (stepwise demotion: urgent → normal → background). Deleting it breaks urgency decay. |

### `goal_context` Deletion Cascade

`goal_context` exists in 28+ locations. All callsites must be deleted simultaneously. Partial deletion breaks the engine.

**Models (state.py):**
- `state.py:81` — CampaignArc field
- `state.py:186` — ArcResolution field

**Engine (turn_state.py):**
- `turn_state.py:249` — stored in resolved_arcs entry (must be removed)
- `turn_state.py:266` — new successor arc construction (must be removed)
- `turn_state.py:534-541` — goal_update path (must be updated to use `long_term_objective`)

**Engine (thread_sanitizer.py):**
- `thread_sanitizer.py:143,150` — pass `goal_context` to template (must be removed)
- `thread_sanitizer.py:219-222` — `_apply_goal_update` validates dict with `goal_context` (must be removed)
- `thread_sanitizer.py:340-345` — `_apply_goal_update` applies `goal_context` to `arc.goal_context` (must be removed)
- `thread_sanitizer.py:238-240` — coerces unknown `progress_kind` to "advancement" including "shift" (must remove "shift" from valid set)

**State init (state/io.py):**
- `state/io.py:93` — `_default_state()` initialization (must be removed)

**Prompts (Jinja2):**
- `storytell_system.j2:14` — arc_resolve example (must be removed)
- `sanitize_thread.j2:15,86` — sanitizer prompt (must be removed)
- `generate_seed_system.j2:37,64` — seed prompt (must be updated to `arc_origin`)

**Templates (Jinja2):**
- `_state_left.html:64,109` — PC UI panel (must be updated to `arc_origin`)

**Checkers (ev/checkers/):**
- `ev/checkers/arc_resolution_validity.py:64-69` — validates goal_context present (must be removed)
- `ev/checkers/goal_update_validity.py:56,58` — validates visible_goal (must be updated to long_term_objective)
- `ev/checkers/arc_goals.py:38,40` — validates visible_goal (must be updated to long_term_objective)

**Ev tools:**
- `ev/audit.py:312,321,325` — audit references (must be removed/updated)
- `ev/state_tools.py:472,1029,1111` — state tools (must be updated to long_term_objective)
- `ev/prompt_context.py:217` — prompt context (must be updated to long_term_objective)

**Changes/delta/narrate/extraction:**
- `engine/changes.py:285-286` — change detection (must be updated to long_term_objective)
- `state/delta_builder.py:53-55` — delta builder (must be updated to long_term_objective)
- `engine/narrate.py:65` — narrate context (must be updated to long_term_objective)
- `engine/extraction/pipeline.py:227` — extraction pipeline (must be updated to long_term_objective)

**Other callsites:**
- `ev/play.py:503,525` — turn context (must be updated to long_term_objective)
- `server/tv.py:408` — server TV (must be updated to long_term_objective)
- `_save_picker.html:29` — save picker UI (must be updated to arc_origin)
- `_state_left.html:63,109` — PC UI panel (must be updated to arc_origin)

### `major_update_signal` Values

Two values only: `advancement` and `setback`. `shift` is removed entirely.

Rationale: the only information the engine needs is whether the thread moved forward or
backward. `shift` described dimensional change, not directional progress, and had no
distinguishing value from a low-signal `advancement`. If nothing significant happened,
no `major_updates` entry should be emitted — the field name already enforces this.

**Model locations to update:**
- `state.py:22` — `ProgressEntry.kind: Literal["advancement", "setback", "shift"]` → `Literal["advancement", "setback"]`
- `state.py:170` — `ThreadUpdate.progress_kind` → renamed to `major_update_signal` with `Literal["advancement", "setback"]`

## Age Tracking

### `LongTermObjective`: `started_turn`

One field is added to `LongTermObjective`: `started_turn: int | None = None`.

`created_turn` is not added. In practice arcs are constructed and immediately surfaced — the seed arc is built and rendered on turn 1; successor arcs are built and rendered on the same turn `arc_resolve` fires. The two fields would always have the same value. `started_turn` is the single source of truth for arc age.

**Set points:**
- Seed pipeline: set when the seed arc object is written to state
- Successor arc: set in `_apply_arc_resolve()` at `turn_state.py:264-270` when `LongTermObjective` is constructed

The pressure score system uses `started_turn` for duration weight calculation.

## TTL Strategy

### Completed/Abandoned Threads

- **Data retention:** Kept in `state.yaml` forever for auditability. No TTL on data.
- **Prompt rendering:** Surfaces in prompts for 3 turns after resolution (as "Recently
  Resolved Threads"), then removed from all prompt rendering.
- **Hard cap:** Removed. The `[:15]` hard cap in `_arc.j2` is deleted. TTL filtering
  ensures bounded prompt load, so unbounded growth in data is acceptable.
- **Abandoned threads:** Included in the 3-turn TTL alongside resolved threads. If they
  turn out to distract the narrator by forcing recall of forgotten threads, they can be
  filtered to resolved-only in a future pass.
- **"Past Resolutions" in narrate_user.j2:** Removed. It renders unfiltered completed
  threads, causing context bloat. The TTL-filtered "Recently Resolved Threads" section
  in `_arc.j2` replaces it.

### Dormant Threads

- **Auto-dormant threshold:** 8 turns (configurable). Moved from 4 turns.
- **Archival TTL:** 13 turns (8 dormant + 5 more). When a thread has been dormant for
  5 more turns, the sanitizer marks it for archival.
- **Archival resurfacing:** No. Dormant threads approaching archival do NOT get a
  resurfacing hint. LLMs are bad at ignoring things. The TTL system handles cleanup
  without requiring proactive resurfacing.

### Resolved Arcs

- **Prompt rendering:** TTL-filtered in prompts (3 turns). Already implemented in
  `_get_resolved_arcs()` in narrate.py. No change needed.

### NPC Archival

Existing pattern, no change:
- **Nearby decay:** 2 turns before nearby → known auto-decay.
- **Departed archive:** 3 turns as "departed" before → archived.
- **Archived NPCs:** Excluded from roster, kept in compendium. No TTL on data.

## Pressure Score System

The engine computes a `pressure_score` per thread and per arc at render time. It is never
persisted to state and never visible in any LLM prompt until it crosses a hint threshold.
When it crosses a threshold, only the resulting hint tag is injected — not the score
itself.

### Two Inputs

**Duration weight** (same structure for threads and arcs):

| Age (turns active) | Cumulative duration weight added |
|---|---|
| 1–4 | 0 |
| 5–7 | +1 |
| 8–10 | +3 (cumulative: 4) |
| 11–13 | +6 (cumulative: 10) |
| 14+ | +10 (cumulative: 20) |

**Progress signal:**
- Threads: each `advancement` entry in `major_updates` → +1; each `setback` → −1
  (floor: 0). Turns with no update are neutral.
- Arcs: each thread resolved under this arc → +2. Threads abandoned or archived → +0.
  Turn count is covered by duration weight; resolved thread count is the only progress
  signal.

*Pressure score = duration weight + progress signal.*

### Hint Tiers

| Tier | Thread threshold | Arc threshold | Signal injected |
|---|---|---|---|
| None | < 4 | < 5 | Nothing |
| Soft hint | 4–6 | 5–8 | "Consider resolving" |
| Strong hint | 7–9 | 9–12 | "This should be reaching conclusion" |
| Imperative | ≥ 10 | ≥ 13 | "Wrap up — failure is a valid resolution" |

Thresholds are initial tuning values. They will be validated against eval data and may be
made configurable at the pack level in a future pass.

### Hint Delivery

When a thread crosses a tier threshold, the hint is injected into both the narrator
prompt and the storyteller prompt on the same turn. The narrator acts first (writes
toward the signaled conclusion); the storyteller receives the narrator's output plus
the same hint and is told to respond to what the narrator played out. This is a
coordinated nudge, not a hard resolve — the LLM retains narrative judgment about how
closure happens.

For arcs, the same tiers apply with the arc thresholds above. Hint language for arcs
should refer to the arc's `long_term_objective` and explicitly note that both success
and failure are valid resolutions.

### Implementation

The hint computation should live in a shared preprocessing helper (e.g.,
`engine/hints.py`) — pure functions, state in, hint context out, no side effects.
Both the narrator path (`narrate.py`) and the storyteller path (`extraction/storytell.py`)
currently build their arc context independently with no shared builder. The hints helper
is the right shared injection point for both thread and arc hints without adding a new
dependency between those two paths.

## `pc.situation` Primitive

### What It Is

`pc.situation` is a `dict[str, Any]` keyed by the pack's `pc_situation_schema`. It is a
peer of `bio`, `tagline`, and `stats` in `_default_state()`.

The schema is defined in `scenario.yaml` by the pack author. It declares which
situational axes matter for this genre. The LLM receives these as structured slots to
populate — not open-ended prose. The schema describes *what to ask*, not *what to answer*.

### Authoring Constraint

**3–5 keys maximum.** Each key should answer a question the player would reasonably ask
before the game begins — not plot hooks, not obligations, not backstory. Situational
facts only: what do they have, where is it, what condition is it in, who are they to
the people around them.

All keys are `required: false` — the LLM may determine the PC has no vessel, no home
port, no crew. It must state that explicitly rather than invent something false.

### Updatable During Gameplay

pc.situation should be updatable when circumstances change:
- Vessel destroyed or stolen → update vessel field
- Home port burned down → update home_port field
- Crew lost or gained → update crew field

This is important for continuity at turn 15 and turn 25. The narrator needs to know
where the PC's home is, whether they have a vehicle, what their situation looks like
now — not just what it was at turn 0.

### Tiered Surfacing in Prompts

- **Seed prompt + first 2–3 turns:** Full pc.situation is fed to the seed prompt and
  early narration. This establishes the PC's baseline canon (home settlement, family,
  vehicle, crew, etc.) and may generate NPCs, inventory items, or other persistent
  state.
- **Ongoing turns:** A stripped-down version surfaces in narrate prompts (and possibly
  storytell/ruling). Only fields marked with `persist: true` (or equivalent) are
  included. Items that generated their own persistent entities (NPCs, inventory)
  don't need ongoing surfacing — those entities carry their own context.

Example: "home settlement" persists (the PC still has a home). "Crew member X" doesn't
need surfacing — if that crew member matters, they exist as an NPC in the compendium.
But "vessel condition: damaged" might persist if the vessel itself is a persistent entity.

**`persist` flag — IMPLEMENTED.** Each `pc_situation_schema` entry has a `persist: bool` field (default `false`). The engine filters `pc.situation` to only include keys where `persist: true` when building ruling and narrate prompts. Seed prompt always receives the full situation. Pack authors mark durable situation keys (vessel, home, unit, etc.) with `persist: true`. Backstory-only keys (family, reputation) leave it as `false`.

### Relationship to External Inventory

pc.situation is related to the idea of "external inventory" — things that belong to the
PC but aren't on their person (ship, home, base of operations). This needs more
fleshing out and may warrant a separate field or extension of pc.situation. Deferred.

### Prompt Surfacing Across the Engine

`pc.situation` (persistent fields only) surfaces in the narrator, storyteller, and ruling
prompts throughout gameplay. The ruling prompt in particular needs it to avoid ruling
impossible actions that depend on established situational facts — if the PC owns a
vehicle, ruling must know this or it will incorrectly deny movement actions.

Full `pc.situation` feeds the seed prompt and opening narration only. Ongoing prompts
receive only fields marked `persist: true`.

## Resolved Design Decisions

### D1. `goal_update` format mismatch — RESOLVED

**Decision:** `goal_update` becomes a dict with `long_term_objective` key only. `arc_origin` is a seed-time field set once and never changes — the storyteller should not be generating it mid-game.

**Mechanical corrections:**
- `StorytellerResult.goal_update` in `extraction.py:231` — change from `str | None` to `dict | None`
- `thread_sanitizer.py:219-222` — `_apply_goal_update` already expects a dict; update to use `long_term_objective` key only (remove `goal_context`)
- `thread_sanitizer.py:340-345` — `_apply_goal_update` applies `goal_context` to `arc.goal_context`; remove this line (field deleted)
- `turn_state.py:534-536` — update to apply dict to `long_term_objective` field only

### D2. TTL filtering in `_arc.j2` — RESOLVED

**Decision:** TTL filtering in the context builder, not the template. Pass pre-filtered `completed_threads` to the template, following the same pattern as `_get_resolved_arcs()` in narrate.py:139.

**Mechanical corrections:**
- `_arc.j2:21` — replace `current_arc.completed_threads[:15]` with TTL-filtered `completed_threads` from context builder
- Context builder in `prompts/context.py` — add TTL filtering for completed_threads (3-turn TTL)
- `_arc.j2:18-24` — remove `[:15]` hard cap, render all TTL-filtered threads

### D3. `started_turn` initialization point — RESOLVED

**Decision:** `started_turn` only. `created_turn` is not added — arcs are constructed and immediately surfaced in practice, so the two fields would always have the same value. `started_turn` is the single source of truth for arc age. Set at arc construction time: in the seed pipeline when the seed arc object is written to state, and in `_apply_arc_resolve()` at `turn_state.py:264-270` when a successor `LongTermObjective` is constructed.

**Mechanical corrections:**
- `state.py:80-81` — add `started_turn: int | None = None` to LongTermObjective (no `created_turn`)
- `state/io.py:93` — add initialization in `_default_state()`
- Seed pipeline — set `started_turn` when arc is created
- `_apply_arc_resolve()` in `turn_state.py:264-270` — set `started_turn` when successor arc is constructed

### D4. Thread type change `reason` field — RESOLVED

**Decision:** Add `reason: str | None` to `ThreadUpdate` model.

**Mechanical corrections:**
- `state.py:170` — add `reason: str | None` to ThreadUpdate model
- Storyteller prompt — instruct storyteller to provide reason when changing thread type
- Sanitizer prompt — instruct sanitizer to provide reason when changing thread type

### D5. `drop_threads` and `new_threads` removed from `ArcResolution` — RESOLVED

**Decision:** `ArcResolution` no longer contains `drop_threads` or `new_threads`. Arc and thread lifecycles are fully decoupled. All threads carry forward to the successor arc automatically on `arc_resolve`. The storyteller emits `thread_add` independently — there is no special thread-creation moment tied to arc resolution. Threads that predate the arc age out naturally via the pressure score / hint tier system.

**Mechanical corrections:**
- `state.py:185-186` — remove `drop_threads` and `new_threads` from `ArcResolution`
- `turn_state.py:235-243` — remove `drop_threads` filtering logic; all threads carry forward
- `turn_state.py:264-270` — remove `new_threads` from successor arc construction
- `storytell_system.j2:14` — update `arc_resolve` schema example to remove `drop_threads` and `new_threads`

### D6. `arc_origin` placement — RESOLVED

**Decision:** `arc_origin` is a field on the seed state model only. It is generated once by the seed LLM at turn 0 and never again. It is not a field on `LongTermObjective` and not a field on `ArcResolution`.

Successor arcs do not receive an `arc_origin`. The preceding narration serves as the origin for any arc that begins after turn 0 — the player lived through it and it is already in context. A dedicated field is only meaningful at turn 0 when the player has no prior context.

`arc_origin` surfaces in the opening narration and the UI sidebar for the initial arc only. It is never injected into narrate, storytell, or ruling prompts during gameplay.

**Mechanical corrections:**
- Seed state model — add `arc_origin: str` field
- `generate_seed_system.j2` — instruct seed LLM to generate `arc_origin` (2–3 sentences, past tense, "how did the PC end up here?")
- `_save_picker.html` and `_state_left.html` — render `arc_origin` in UI sidebar for initial arc display
- `ArcResolution` — no `arc_origin` field; do not add one

### D7. Ruling context extended — RESOLVED

**Decision:** The ruling prompt context is extended to include `pc.situation` (persistent fields only). No arc fields are added to ruling. Ruling does not need narrative goal context — it needs situational facts about what the PC owns and can access.

**Mechanical corrections:**
- `engine/ruling.py` — add `pc_situation` (persistent fields only) to ruling context
- `ruling_user.j2` — add `pc.situation` section to ruling prompt

### D8. `LongTermObjective` / `long_term_objective` rename — RESOLVED

**Decision:** `CampaignArc` is renamed to `LongTermObjective` throughout. The state key `state["arc"]` is renamed to `state["long_term_objective"]`. The UI displays this as "Objective." This rename follows the same principle as `progress → major_updates` and `visible_goal → long_term_objective`: field names are prompts, and the name must signal duration and scope to the LLM.

**Mechanical corrections:**
- `state.py:79-85` — rename class `CampaignArc` to `LongTermObjective`; update all imports
- `state/io.py` — rename `state["arc"]` key to `state["long_term_objective"]` in `_default_state()`
- All engine files reading `state["arc"]` — update key reference
- All prompt context builders — update variable name passed to templates
- All Jinja2 templates using `current_arc` — rename variable to `current_objective` (or equivalent consistent name)

### D9. No auto-arc-resolve — RESOLVED

**Decision:** Arc resolution is entirely storyteller-driven. No auto-resolve logic is implemented and none will be. Confirmed via codebase search — no such logic exists. The hint tier system handles arc completion pressure. No mechanical corrections needed.

## Mechanical Corrections (from design review 2026-06-23)

This section lists all CRITICAL findings from the design review that require mechanical
code/prompt/model changes. Each finding maps to specific files that must be updated.

### Field Renames

| CRITICAL | Old → New | Files to Update |
|----------|-----------|-----------------|
| C18, C35, C36, C37, C39, C40, C41, C42, C43, C47, C48, C49, C50 | `visible_goal` → `long_term_objective` | state.py:80, turn_state.py:247,265,534, thread_sanitizer.py:142,149, prompts/context.py:110,149, engine/narrate.py:65, engine/extraction/pipeline.py:227, ev/prompt_context.py:217, ev/state_tools.py:472,1029,1111, ev/play.py:503,525, server/tv.py:408, engine/changes.py:285-286, state/delta_builder.py:53-55, _arc.j2:3,6,9, storytell_system.j2:72,76, generate_seed_system.j2:63-64 |
| — | `goal_update` format | `str | None` → `dict | None` with `long_term_objective` key (extraction.py:231, thread_sanitizer.py:219-222,340-345, turn_state.py:534-536) |
| C19 | `progress` → `major_updates` | state.py:43, all code references (100+ matches in grep) |
| C20 | `progress_kind` → `major_update_signal` | state.py:170, all code references |
| C30 | `goal_context` → `arc_origin` in prompts | generate_seed_system.j2:37,64 |
| — | `arc` (state key) → `long_term_objective` | state/io.py _default_state(), all engine code reading state["arc"] |
| — | `CampaignArc` → `LongTermObjective` | state.py:79-85 and all imports throughout codebase |

### Field Deletions

| CRITICAL | Field | Files to Update |
|----------|-------|-----------------|
| C15 | `ThreadResolution.promote_to_world_state` | state.py:161, storytell_system.j2:11, turn_state.py:341,343 |
| C16 | `ArcResolution.goal_context` | state.py:186 |
| C17 | `CampaignArc.goal_context` | state.py:81, turn_state.py:249,266, state/io.py:93 |
| C27 | `chapter_end` in prompts | storytell_system.j2:16,72,74 |
| C7 | "Past Resolutions" in narrate_user.j2 | narrate_user.j2:59-61 |
| C8 | `[:15]` hard cap in _arc.j2 | _arc.j2:21 |
| — | `ArcResolution.drop_threads` | state.py:185, turn_state.py:235-243, storytell_system.j2:14 |
| — | `ArcResolution.new_threads` | state.py:186, turn_state.py:264-270, storytell_system.j2:14 |
| — | `turns_since` warning guard | turn_state.py:225-233 |

### Model Updates

| CRITICAL | Model | Old → New |
|----------|-------|-----------|
| C14 | `ProgressEntry.kind` | `Literal["advancement", "setback", "shift"]` → `Literal["advancement", "setback"]` (state.py:22) |
| C14 | `ThreadUpdate.progress_kind` | Renamed to `major_update_signal` with `Literal["advancement", "setback"]` (state.py:170) |
| C83 | `WorldStateFact` | Full replacement: old `tier: Literal["permanent", "persistent"]` → new `tier: Literal["global", "local"]` + `permanent: bool` + `valence: Literal["threat", "complication", "neutral", "boon"]` + `expires_turn: int | None` (state.py:150-154) |
| C6 | `ThreadUpdate` | Add `reason: str | None` (state.py:170) |
| C58, C59 | ThreadResolution | Add `world_state_candidate` field or add `world_state_candidates` list to state |
| C55, C56, C57 | ThreadResolution | Add `resolved_turn` marker |
| C17 | CampaignArc | Add `created_turn: int | None` and `started_turn: int | None` (state.py:80-81) |
| — | `StorytellerResult.goal_update` | `str | None` → `dict | None` with `long_term_objective` key (extraction.py:231) |
| — | `LongTermObjective` (renamed from CampaignArc) | Add `started_turn: int | None = None` (state.py:79-85); set in seed pipeline and turn_state.py:264-270 |
| — | Seed state model | Add `arc_origin: str` field |

### Threshold Updates

| CRITICAL | Location | Old → New |
|----------|----------|-----------|
| C9 | turn_state.py:116 | `dormant_threshold = 4` → `dormant_threshold = 8` |
| C13 | turn_state.py:229 | `if turns_since < 5` → `if turns_since < 8` |
| C12 | config.py:184 | Remove `thread_completion_threshold: int = 3` |

### Template/Prompt Updates

| CRITICAL | Location | Change |
|----------|----------|--------|
| C10 | sanitize_thread.j2:51 | "4+ turns" → "8+ turns" (dormant guidance) |
| C11 | sanitize_thread.j2:48 | Align abandonment criteria with TTL strategy (5+ turns no mention, 3+ turns no activity → review and align) |
| C24 | sanitize_thread.j2:15 | Remove `{% if goal_context %}**Context:** {{ goal_context }}{% endif %}` |
| C25 | sanitize_thread.j2:86 | Remove `goal_context` from JSON schema example |
| C26 | storytell_system.j2:14 | Remove `goal_context` from arc_resolve example |
| C27 | storytell_system.j2:16,72,74 | Remove `chapter_end` references |
| C28 | storytell_system.j2:72 | `visible_goal` → `long_term_objective` |
| C29 | storytell_system.j2:76 | `visible_goal` → `long_term_objective` |
| C30 | generate_seed_system.j2:37,63-64 | `goal_context` → `arc_origin`, `visible_goal` → `long_term_objective` |
| C31 | _arc.j2:3,6,9 | `visible_goal` → `long_term_objective` |
| C32 | _arc.j2:18-24 | Remove `[:15]` hard cap, add TTL filtering |
| C33 | _arc.j2:12-16 | Rename "Previously Resolved Arcs" to "Recently Resolved Arcs" |
| C34 | _arc.j2:18-24 | Add TTL filtering to completed_threads |
| C7 | narrate_user.j2:59-61 | Remove "Past Resolutions" section |
| C82 | _world_state.j2, storytell_user.j2 | Render tier and valence as paired badges: `[global/threat]`, `[local/boon]` |
| — | _world_state.j2:6 | Replace `fact.tier == "permanent"` check with `fact.permanent` boolean field (new schema) |
| — | thread_sanitizer.py:238-240 | Remove "shift" from progress_kind coercion check: `if pk not in ("advancement", "setback", "shift")` → `if pk not in ("advancement", "setback")` |
| — | ruling_user.j2 | Add `pc.situation` section to ruling prompt |
| — | Add `world_state_candidates: []` to `_default_state()` | `state/io.py` |
| — | Bump NPC roster limit 10 → 12 | `prompt_context.py:25-53` (`_build_npc_roster()`) |

### World State Model Replacement (C83)

The entire `WorldStateFact` model in `state.py:150-154` is replaced:

**Old schema:**
```python
class WorldStateFact(BaseModel):
    id: str
    text: str
    tier: Literal["permanent", "persistent"]
```

**New schema:**
```python
class WorldStateFact(BaseModel):
    id: str
    text: str
    tier: Literal["global", "local"]
    permanent: bool = False
    valence: Literal["threat", "complication", "neutral", "boon"] = "neutral"
    expires_turn: int | None = None
```

**Files to update for tier values:**
- `turn_state.py:346,348` — `tier: "persistent"` → `tier: "local"` (or `"global"`)
- All code that branches on `"permanent"` or `"persistent"` in world state context
- `pack.py:56` — `SeedScene.world_state: list[WorldStateFact | str]`

### Two-Step World State Candidate System (C52-C82)

The current code in `turn_state.py:341-349` does direct one-step promotion. This must be replaced with a two-step system:

1. **Storyteller flags** — `ThreadResolution` gets a `world_state_candidate` field
2. **Sanitizer confirms** — Every 5 turns, sanitizer evaluates candidates within 0–5 turns of resolution
3. **Sanitizer has full authority** — promote, reject, consolidate, modify, or replace the entire world state array

**State changes needed:**
- Add `world_state_candidates` list to state (populated by storyteller, consumed by sanitizer)
- Add `resolved_turn` marker to ThreadResolution (for TTL evaluation)
- Add TTL to candidate evaluation (0–5 turns after resolution)
- Engine swaps old world state array for new one atomically (sanitizer returns complete replacement)
- TTL expiry pass at start of each turn: hard-delete facts where `current_turn >= expires_turn`
- All removals are hard deletes. No archive list in state. `events.jsonl` is the record.

### Sanitizer World State Output Model

The sanitizer is extended to maintain world state. It receives the full `world_state` list as context and returns a complete replacement array:

```json
{
  "world_state": [
    {
      "id": "fact_id",
      "text": "current or revised text",
      "tier": "global | local",
      "permanent": false,
      "valence": "threat | complication | neutral | boon",
      "expires_turn": null
    }
  ]
}
```

**Files to update:**
- `thread_sanitizer.py` — add world state to input context and output schema
- `sanitize_thread.j2` — add world state to prompt context
- `config.py` — ensure `sanitize_every` applies to world state sanitization

### Seed-Time Valence Requirement

The seed prompt must produce at least one `neutral` or `boon` fact across the combined global + local world state.

**File to update:**
- `generate_seed_system.j2` — add valence requirement to seed prompt instructions

## Out of Scope

These items are explicitly scoped to other designs or deferred to future passes. They
are not addressed in this primitives document.

- **Arc → world state** — When an arc resolves, its narrative weight does not directly
  feed into world state. Deferred to a future pass.
- **Multiple arcs** — Whether threads cleanly fit into multiple concurrent arcs (1–3)
  is deferred.
- **Thread urgency graduated states** — Currently background/normal/urgent is too coarse.
  Deferred to a future design pass.
- **External inventory** — Related to pc.situation, needs separate design. Deferred.
- **Convergence starvation** — Pacing engine problem, not arc system problem. Out of
  scope. See bug ticket: `roadmap/bugs/convergence-starvation.md`.
- **Pack-level threshold tuning** — Pressure score thresholds may be configurable at
  the pack level in a future pass. Deferred.
