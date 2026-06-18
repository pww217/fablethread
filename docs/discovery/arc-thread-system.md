# Arc and Thread System

## Overview

**Arcs** and **threads** are a narrative tracking system that allows the game to track long-term goals (arcs) and specific narrative tensions (threads) across turns. The system is entirely LLM-driven with minimal Python-side enforcement.

---

## Core Concepts

### What is an Arc?

An **arc** (`CampaignArc`) represents a narrative chapter — the overarching goal the player is working toward. It contains:

- `visible_goal`: The current chapter goal (a string)
- `goal_context`: UI-only tooltip text (never rendered to LLM)
- `threads`: Active narrative threads under this arc
- `completed_threads`: Resolved threads for TTL context
- `resolution`: Set when arc is resolved
- `last_thread_created_turn`: Tracks pacing

**Key relationship**: An arc can be resolved (ended) and replaced by a new arc, but threads do NOT drive arc lifecycle — they're independent.

### What is a Thread?

A **thread** (`ArcThread`) represents a specific narrative tension or concern. Threads are contained within an arc and have their own lifecycle independent of the arc.

**Note on scope**: The original design had `scope: "scene" | "arc"` but this field has been **removed from the current `ArcThread` model**. The design docs reference it but the current code does not implement it. Threads are now a unified list without scope classification.

---

## Data Models

### `ArcThread` (`ccya/models.py:35-61`)

```python
class ArcThread(BaseModel):
    id: str                          # Unique identifier
    summary: str                    # Brief description (3-7 words)
    active: bool = True             # False = latent/dormant
    urgency: Literal["background", "normal", "urgent"] = "normal"
    progress: list[ProgressEntry]    # Append-only progress log
    resolution_state: str | None    # Set on completion: "resolved", "failed", "abandoned"
    outcome: str | None             # Past-tense sentence at resolution
    resolved_turn: int | None       # Turn when resolved
    last_updated_turn: int | None   # Turn of last update (drives auto-latent)
    added_turn: int | None          # Turn when created
    urgency_set_turn: int | None   # Turn when urgency last set (drives decay)
```

### `ProgressEntry` (`ccya/models.py:30-33`)

```python
class ProgressEntry(BaseModel):
    kind: Literal["advancement", "setback", "shift"] = "advancement"
    text: str
```

### `CampaignArc` (`ccya/models.py:64-71`)

```python
class CampaignArc(BaseModel):
    visible_goal: str = ""
    goal_context: str = ""
    threads: list[ArcThread] = []
    completed_threads: list[ArcThread] = []
    resolution: str | None = None
    last_thread_created_turn: int = 0
```

### `ThreadUpdate` (`ccya/models.py:411-416`) — Storyteller Output

```python
class ThreadUpdate(BaseModel):
    id: str
    active: bool | None = None
    urgency: Literal["background", "normal", "urgent"] | None = None
    progress: str | None = None
    progress_kind: Literal["advancement", "setback", "shift"] | None = None
```

### `ThreadResolution` (`ccya/models.py:403-408`)

```python
class ThreadResolution(BaseModel):
    id: str
    resolution_state: Literal["resolved", "failed", "abandoned"]
    outcome: str = ""
    promote_to_world_state: bool = False
```

### `ArcResolution` (`ccya/models.py:419-424`)

```python
class ArcResolution(BaseModel):
    resolution: str
    visible_goal: str
    goal_context: str
    drop_threads: list[str] = []
    new_threads: list[ArcThread] = []
```

### `StorytellerResult` (`ccya/models.py:468-479`) — Full Storyteller Output

```python
class StorytellerResult(BaseModel):
    actions: list[str] = []
    outcome_summary: str = ""
    goal_update: str | None = None        # Mid-arc visible_goal change
    gm_beat: GMBeat | None = None
    thread_resolve: list[ThreadResolution] = []
    thread_add: ArcThread | None = None
    thread_update: list[ThreadUpdate] = []
    arc_resolve: ArcResolution | None = None
    chapter_end: bool = False
```

---

## Thread Lifecycle

### 1. CREATE (`thread_add`)

- Storyteller emits `thread_add` with `id`, `summary`, `urgency`
- Engine sets `added_turn` and `urgency_set_turn` at creation time
- Hard limit: at most 2 threads active at game start (`seed.py:367-368`)
- Runtime max active: `thread_max_active=5` (`config.py:167`)

### 2. UPDATE (`thread_update`)

- Storyteller emits `thread_update` with `id` + optional fields
- Progress is **always appended** (not replaced) — `turn.py:160-184`
- Auto-latent demotion: threads untouched for `thread_stale_threshold=3` turns go `active=False` (`turn.py:199-215`)
- Urgency decay: `urgent→normal→background` after `thread_urgency_max_age=8` turns at same level (`turn.py:217-241`)

### 3. RESOLVE (`thread_resolve`)

- Storyteller emits `thread_resolve` with `id`, `resolution_state`, `outcome`
- Thread moves from `threads[]` to `completed_threads[]` (`turn.py:1253`)
- Resolution states: `"resolved"`, `"failed"`, `"abandoned"`

### 4. PURGE

- Scene-scoped threads were purged on location change (now removed from design)
- TTL-based: completed threads pruned from prompt context after `thread_memory_ttl=3` turns

---

## Arc Lifecycle

### 1. CREATE (seed time)

- Created via pack's `CampaignArc` or LLM-generated in `generate_seed()`
- Contains initial `visible_goal` and potentially pre-seeded threads

### 2. UPDATE (mid-arc)

- `goal_update`: Direct `visible_goal` change without ending arc (`turn.py:1222-1229`)
- Applied directly to `state["arc"]["visible_goal"]`, NOT through `_merge_arc_update`
- `arc_resolve`: Full arc resolution — creates successor arc, auto-resolves arc-scoped threads

### 3. RESOLVE (`arc_resolve`)

- Current arc stored in `resolved_arcs[]` with TTL
- Successor arc created with new `visible_goal` and empty `threads[]`
- **No automatic arc-scoped thread resolution** in current code (scope field removed)

### 4. TTL Cleanup

- Resolved arcs appear in prompts for `arc_memory_ttl=3` turns

---

## Engine Processing (Arc Director) — `turn.py:1202-1300`

Processing order:

1. `_apply_thread_updates` — merge `thread_update[]` into active threads
2. `goal_update` — direct dict assignment if `storyteller_result.goal_update`
3. `_apply_arc_resolve` — resolve arc if `arc_resolve` present
4. `_apply_thread_resolutions` — move resolved threads to `completed_threads[]`
5. `thread_add` — add new thread if under `thread_max_active`

**Same-turn conflict detection**: If same `id` appears in both `thread_update` and `thread_resolve`, a warning is logged — resolution takes precedence (`turn.py:1231-1239`).

---

## Thread Sanitizer — `thread_sanitizer.py`

Runs every `sanitize_every=5` turns (configurable, 0=disabled).

### Purpose

Batch LLM-driven cleanup of stale threads, goal updates, and thread resolutions.

### Process

1. Loads last 5 narrations + prior history
2. Calls LLM with arc state + evidence
3. LLM returns structured JSON with `goal_update`, `thread_updates`, `resolved_threads`, `new_threads`
4. Validates against Pydantic models
5. Applies changes to state

### Key validation (`thread_sanitizer.py:225-253`)

- `thread_updates`: Validated against `ThreadUpdate`, progress coerced to string
- `resolved_threads`: Validated against `ThreadResolution`
- Unknown thread IDs are skipped with warning

---

## Prompt Templates

### `_arc.j2` (`ccya/prompts/sections/_arc.j2`)

Renders current arc's `visible_goal`, resolution, completed threads (TTL), and previously resolved arcs.

### `_thread_list.j2` (`ccya/prompts/sections/_thread_list.j2`)

Renders active threads with:

- ID, urgency tag, summary
- Latent marker if `active=False`
- Staleness: "X turns ago" or "[new — never updated]"
- Progress log (all entries)
- Target: 3-4 active, ~5 total

---

## Configuration (`ccya/engine/config.py:160-178`)

| Field | Default | Purpose |
|-------|---------|---------|
| `thread_stale_threshold` | 3 | Turns before auto-latent demotion |
| `thread_max_active` | 5 | Max active threads before oldest evicted |
| `thread_urgency_max_age` | 8 | Turns before urgency demotion (urgent→normal→background) |
| `thread_memory_ttl` | 3 | TTL for completed threads in prompts |
| `arc_memory_ttl` | 3 | TTL for resolved arcs in prompts |
| `sanitize_every` | 5 | Turns between sanitizer runs (0=disabled) |
| `sanitize_temperature` | 0.3 | LLM temperature for sanitization |

---

## State Structure (`ccya/state/io.py:89-96`)

```python
"arc": {
    "visible_goal": "",
    "goal_context": "",
    "threads": [],           # list of ArcThread (active)
    "completed_threads": [], # list of ArcThread (resolved)
    "resolution": None,
    "last_thread_created_turn": 0,
},
"resolved_arcs": [],        # at state level, TTL-pruned
```

---

## Evaluation/Checking

| Checker | File | Purpose |
|---------|------|---------|
| `thread_lifecycle` | `ccya/ev/checkers/threads.py` | thread_add applied, thread_update IDs valid |
| `new_thread_validity` | `ccya/ev/checkers/new_thread_validity.py` | thread_add has id/summary, no duplicates |
| `thread_resolution_validity` | `ccya/ev/checkers/thread_resolution_validity.py` | thread_resolve entries valid |
| `arc_goal_updates` | `ccya/ev/checkers/arc_goals.py` | goal_update overwrites visible_goal |
| `arc_resolution_validity` | `ccya/ev/checkers/arc_resolution_validity.py` | arc_resolve has required fields |

---

## Key Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| `ccya/models.py` | 35-71, 403-424, 468-479 | ArcThread, CampaignArc, ThreadUpdate, ThreadResolution, ArcResolution, StorytellerResult |
| `ccya/engine/turn.py` | 112-245, 1202-1300 | `_apply_thread_updates`, `_apply_arc_resolve`, `_apply_thread_resolutions`, arc director |
| `ccya/engine/thread_sanitizer.py` | 1-490 | Periodic LLM-driven thread cleanup |
| `ccya/state/delta_builder.py` | 51-66 | `_merge_arc_update` |
| `ccya/prompts/context.py` | 77-150 | `ArcThreadSummary`, `ArcThreadBlock` for prompt rendering |
| `ccya/prompts/sections/_arc.j2` | 1-22 | Arc rendering in prompts |
| `ccya/prompts/sections/_thread_list.j2` | 1-7 | Thread list rendering in prompts |
| `ccya/engine/changes.py` | 209-289 | Thread change summarization for UI |
| `ccya/ev/state_tools.py` | 166-264 | `cmd_threads` for analyzing thread lifecycle |
| `ccya/server/tv.py` | 235-265 | Thread display in turn review UI |

---

## Design Evolution Notes

1. **Scope field removed**: The `scope: "scene" | "arc"` field existed in older designs but is NOT in the current `ArcThread` model. Tests reference it but the model doesn't have it.

2. **Progress is append-only**: Originally single-string overwrite, now `list[ProgressEntry]` with kind tags.

3. **Independent arc/thread lifecycle**: Threads resolve independently; arc resolution does NOT automatically resolve threads (unlike early designs).

4. **Urgency decay is Python-enforced**: Stepwise demotion happens in engine code, not just prompt guidance.

5. **Auto-latent demotion**: Engine automatically sets `active=False` after `thread_stale_threshold` turns without updates.
