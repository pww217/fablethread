# Thread Sanitizer — periodic arc/thread hygiene

## Purpose

Design authority for the thread sanitizer: a batch process that reads narrative evidence and rewrites `arc.threads[]` to match what actually happened at the table. This document governs implementation under `/plans/`.

## Problem Statement

Threads accumulate without correction. The storyteller can add threads, update urgency, and push progress, but it never _removes_ or _consolidates_ threads that narrative outruns. Over time:

- Threads linger as `active: true` long after their narrative context is resolved
- Urgency levels drift — threads tagged `urgent` remain urgent 10 turns later with no narrative pressure
- Progress entries pile up with low-signal updates that don't reflect the actual arc of events
- `visible_goal` and `goal_context` ossify on whatever the storyteller set at scene start
- The LLM spends context tokens rendering irrelevant thread state in every prompt

The old compactor tried to fix this with pressure-level cleanup and bulletin dedup, but was removed in favor of per-turn `prior_history` bullets. Those bullets are factual summaries — they don't retroactively fix thread structure. The manual `thread_stale_threshold` (auto-latent after 3 untouched turns) helps but is too blunt: a thread may be narratively resolved without having received a `last_updated_turn` bump.

## Constraints

- Zero changes to extraction, storyteller, narrate, or ruling prompts
- Must not rewrite chronicle.md, touch prior_history, or modify state outside `arc`
- Total new code < 350 lines (module + prompt + trivial integrations)
- Must work with `prior_history` as it exists today — no schema migration
- Runs synchronously (blocking), matching old compactor behavior
- Must reuse existing CSS classes (`tv-compaction-*` in `app.src.css:2563-2611`)
- Must follow the old compactor's SSE phase event shape exactly (same `compact_start`/`compact_done` pattern, renamed to `sanitize`)
- Turn viewer row must mirror old compaction row structure (collapsible card, header metadata, detail body)

## Non-goals

- World state pruning
- NPC compendium cleanup
- Inventory or condition sanitization
- Chronicle rewriting (no `## COMPACTED` blocks, no prose removal)
- Per-turn incremental correctness — this is a batch fixer, not a guard

## Current State — What Exists

### Thread lifecycle

**Per turn:** storyteller emits `thread_update` (urgency/active/summary/progress), `thread_add` (new thread), `thread_resolve` (moves thread to `completed_threads[]`). Applied immediately by `_apply_thread_updates()` (`turn.py:144`) and `_apply_thread_resolutions()` (`turn.py:332`).

**Batch fixer:** none. `thread_stale_threshold` (default 3) sets `active: false` on threads untouched for N turns, applied in `_apply_thread_updates()`. Blind TTL — no narrative judgment.

### Data the sanitizer needs

| Data | Source | Availability |
|---|---|---|
| Current `arc` (visible_goal, goal_context, threads, completed_threads) | `state["arc"]` | In-memory after persist |
| Last 5 turns of full prose + user input | `load_last_narration(save_dir, 5)` — chronicle.md | At any time |
| Up to 20 prior_history bullets | `state["meta"]["prior_history"]` | In-memory after persist |

### Problems with Current State

- **No narrative grounding for thread state.** The storyteller sets urgency/summary per turn, but never consolidates threads retroactively. After 10+ turns, `summary` text can reference events the LLM no longer remembers.
- **Completed threads accumulate in `completed_threads[]`** indefinitely — no eviction mechanism. Prompt context pays the tax every turn.
- **`visible_goal` drifts implicitly** via `goal_update` (flat string replace), but nothing reconciles it against the accumulated thread list.
- **Auto-latent is purely mechanical.** A thread with `last_updated_turn=12` at turn 20 becomes latent, even if narrative evidence says it should still be active (or vice versa).
- **No feedback loop.** When storyteller hallucinates a thread that never appeared in narration, nothing detects and removes it.

## Proposed Solution

A new module `ccya/engine/thread_sanitizer.py`. Every N turns (`sanitize_every`, default 5), after state persist and prior_history append, run `sanitize_threads()`:

1. Read current arc/thread state + last 5 full turns from chronicle + up to 20 prior_history bullets
2. Call LLM prompt (`sanitize_thread.j2`) asking it to review and output thread changes
3. Parse response, validate, apply changes to `state["arc"]`
4. Re-save state if changes were made
5. Write `kind: "sanitizer"` event to events.jsonl
6. Yield SSE phase events matching old compactor pattern

### Pipeline hook — exact position

Hook goes between prior_history append and `yield ("complete", ...)` in `turn.py:1415-1417`:

```python
# turn.py:1406-1434 (current)
# Append outcome_summary as prior_history bullet (after persist, before yield complete)
if outcome_summary and outcome_summary.strip():
    ...
    save_state(save_dir, state)

# NEW: Thread sanitizer (after prior_history, before yield complete)
if config.sanitize_every > 0:
    t_sanitize = asyncio.get_running_loop().time()
    state, sanitize_ran = await sanitize_threads(save_dir, state, config, trace_id=trace_id)
    if sanitize_ran:
        yield ("phase", {"phase": "sanitize_start", "expected_ms": 0})
        yield ("phase", {"phase": "sanitize_done", "ms": round(
            (asyncio.get_running_loop().time() - t_sanitize) * 1000, 1
        )})
    save_state(save_dir, state)  # re-save regardless (harmless no-op if no changes)

# yield complete unchanged
result_obj = TurnResult(
```

This exactly mirrors the old compactor's hook in `turn.py:1596-1602` (old commit), just renamed and moved to after prior_history instead of after chronicle append.

### Events.jsonl record shape

Follows the old compactor's record shape (`compactor.py:130-145`) with differences for thread-only focus:

```python
{
    "kind": "sanitizer",
    "turn": int,               # current turn number
    "trace_id": str,
    "ms": float,               # wall-clock ms for this LLM call
    "tokens_in": int,
    "tokens_out": int,
    "threads_updated": [str],  # thread IDs with field changes
    "threads_removed": [str],  # thread IDs removed entirely
    "threads_resolved": [str], # thread IDs moved to completed_threads
    "threads_added": [str],    # new thread IDs created
    "goal_changed": bool,      # whether visible_goal was modified
    "changes_detail": {        # per-thread detail for turn viewer
        "updated": {id: {changed_fields...}},
        "removed": [id...],
        "resolved": [{id, resolution_state, outcome}],
        "added": [{id, summary, urgency, scope}],
        "goal": {"before": str|None, "after": str|None},
    }
}
```

### Prompt design

**System** (`sanitize_thread.j2` — single file, system + user sections):

```
[SYSTEM]
You are a thread manager for a TTRPG. Your job is to review the current arc
and thread state against the narrative evidence, then output corrections.

Rules:
- Never invent thread IDs. Only use IDs present in the Current Arc section.
- Output exactly one valid JSON object within <sanitize>...</sanitize> tags.
- If no changes are needed, output <sanitize>{}</sanitize>.
- Do not output anything outside the <sanitize> tags.

[USER]
## Current Arc

**Goal:** {{ visible_goal }}
{% if goal_context %}**Context:** {{ goal_context }}{% endif %}
{% if resolution %}**Resolution:** {{ resolution }}{% endif %}

### Active Threads
{% include "sections/_thread_list.j2" %}
{# _thread_list.j2 renders id, scope, active/latent, urgency, summary,
   turns-since-update, and progress entries — exactly what the sanitizer
   needs to see for each thread. The `gate` variable won't be set so the
   "Gate: blocked" text won't render. No issues. #}

### Completed Threads{% if completed_threads %}
{% for ct in completed_threads %}- `{{ ct.id }}` [{{ ct.scope }}] {{ ct.summary }} — {{ ct.resolution_state }} at turn {{ ct.resolved_turn }}{% endfor %}
{% else %}
(none){% endif %}

## Recent Narration (last 5 turns)
{% for t in recent_turns %}
### Turn {{ t.turn }} — {{ t.input }}
{{ t.narrative }}
{% endfor %}

## Prior History (bullets from earlier turns)
{% for b in prior_history %}{{ b }}
{% endfor %}

## Instructions

Review each active thread against the narrative evidence and output a JSON
object inside <sanitize> tags. For each thread consider:

1. Is it narratively resolved? → add to resolved_threads[] with resolution_state + outcome.
2. Is urgency wrong for what happened? → update urgency field.
3. Should it be latent or active again? → set active field.
4. Is summary stale? → rewrite summary field.
5. Are progress entries noisy or dedup-worthy? → provide updated progress list.

Also consider the arc goal and context — should visible_goal or goal_context be
updated to reflect current narrative direction?

### Output JSON schema

{
  "goal_update": {               // omit if unchanged
    "visible_goal": "...",
    "goal_context": "..."
  },
  "thread_updates": [            // only threads needing changes
    {
      "id": "existing_id",
      "active": true/false,      // omit if unchanged
      "urgency": "...",          // omit if unchanged
      "summary": "...",          // omit if unchanged
      "progress": [str, ...],    // full replacement list, omit if unchanged
      "progress_kind": "advancement"/"setback"/"shift"
    }
  ],
  "resolved_threads": [          // threads to move to completed_threads
    {
      "id": "existing_id",
      "resolution_state": "resolved"/"failed"/"abandoned",
      "outcome": "One sentence describing what happened."
    }
  ],
  "removed_threads": [           // threads to delete entirely
    {"id": "existing_id", "reason": "Why this thread is removed"}
  ],
  "new_threads": [               // new threads from narrative evidence
    {
      "id": "new_unique_id",
      "summary": "Thread summary",
      "urgency": "normal",
      "scope": "arc",
      "active": true
    }
  ],
  "_checklist": {                // MANDATORY — forces model to check each category
    "thread_count": "Reviewed N active threads",
    "resolved": "N threads narratively resolved",
    "removed": "N threads removed (reason)",
    "new": "N new threads added from narrative evidence",
    "goal": "Goal unchanged or updated (why)"
  }
}
```

The `_checklist` pattern is borrowed from the old compactor's prompt (`compact_system.j2`). It forces the LLM to explicitly acknowledge each category rather than silently omitting it. Without this, models tend to skip categories for which they have no changes.

### Shared prompt sections

- **`sections/_thread_list.j2`** — reused directly in the user prompt (renders `id`, `scope`, `active/latent`, `urgency`, `summary`, `turns-since-update`, `progress` entries). No modifications needed; its template variables (`threads`, `turn_no`, `gate`) are a superset of what the sanitizer has.
- **`sections/_arc.j2`** — NOT reused because it renders `resolved_arcs` (TTL-pruned arc history) and truncates `completed_threads` to 15 with an "…and N more" line. The sanitizer needs full thread visibility for decision-making. Instead, the sanitizer prompt renders arc info inline.
- **`sections/_inventory.j2`**, **`_npc_roster.j2`**, **`_location.j2`**, **`_world_state.j2`** — NOT reused. The sanitizer is prose-only; no inventory, NPCs, location, or world state in the prompt.

### Output model and validation

No new Pydantic models. The LLM output is parsed as a plain dict. Validation uses existing `ArcThread`, `CampaignArc`, `ThreadUpdate`, `ThreadResolution` from `models.py` for sub-objects:

```python
# Internal contract — not persisted as a model
# Parsed from <sanitize>...</sanitize> block in LLM response
{
    "goal_update": dict | None,           # {"visible_goal": str, "goal_context": str}
    "thread_updates": list[dict],          # each dict validated against ThreadUpdate model
    "resolved_threads": list[dict],        # each dict validated against ThreadResolution model
    "removed_threads": list[dict],         # [{"id": str, "reason": str}]
    "new_threads": list[dict],            # each dict validated against ArcThread model
    "_checklist": dict[str, str],          # freeform, validated as dict[str, str]
}
```

**ID validation rule:** Every `id` in `thread_updates[]`, `resolved_threads[]`, and `removed_threads[]` must match an existing thread ID in either `state.arc.threads[]` or `state.arc.completed_threads[]`. Unknown IDs are logged and skipped. This prevents hallucinated deletions.

**New thread ID collision rule:** If a new thread's `id` already exists in either `threads[]` or `completed_threads[]`, log a warning and skip (don't create duplicate).

### Apply logic (`_apply_sanitization(state, output)`)

1. **goal_update**: If present and non-empty, replace `state.arc.visible_goal` and `state.arc.goal_context` with new values.
2. **thread_updates**: For each update, find thread by ID in `state.arc.threads[]`. Apply non-null fields (active, urgency, summary, progress). Same pattern as `_apply_thread_updates()` in `turn.py:144`.
3. **resolved_threads**: For each resolution, find thread by ID in `state.arc.threads[]`. Set `resolution_state`, `outcome`, `resolved_turn` (current turn), `active: false`. Move from `state.arc.threads[]` to `state.arc.completed_threads[]`. Same pattern as `_apply_thread_resolutions()` in `turn.py:332`.
4. **removed_threads**: Remove thread by ID from both `state.arc.threads[]` and `state.arc.completed_threads[]`.
5. **new_threads**: Validate each as `ArcThread`. Append to `state.arc.threads[]`. Set `last_thread_created_turn` to current turn.
6. If any changes were made, return `True` (so caller can re-save state).

## Config

```python
@dataclass
class EngineConfig:                  # ccya/engine/config.py:92
    # ...existing fields...
    sanitize_every: int = 5          # 0 = disabled; runs every N turns
    sanitize_temperature: float = 0.3

# In build_engine_config() (config.py:265):
sanitize_cfg = llm.get("sanitize", {})
sanitize_every = int(game.get("sanitize_every", 5))
sanitize_temperature = float(sanitize_cfg.get("temperature", 0.3))

# config.yaml additions:
# llm:
#   sanitize:
#     temperature: 0.3
# game:
#   sanitize_every: 5        # 0 = disabled entirely
```

## UI — phase labels (exact old compactor shape)

In `ccya/templates/index.html`, add after the `persist` handler (current line ~779):

```javascript
} else if (p === 'sanitize_start') {
    label.textContent = 'Sanitizing state…';
    if (eta) eta.textContent = '';
} else if (p === 'sanitize_done') {
    label.textContent = 'Saving…';
    if (eta) eta.textContent = '';
}
```

The `sanitize_done` label uses "Saving…" (matching `extract_done`/`persist`) rather than the old compactor's "Cleaning up…" because the sanitizer is a state mutation, not a chronicle rewrite. This is the one deliberate UI departure from the old compactor.

## Turn viewer — sanitizer row

**`tv.py`** — add handler for `ev.get("kind") == "sanitizer"` right after the JSON-decode try/except (current `tv.py:371` area):

```python
if ev.get("kind") == "sanitizer":
    chg = ev.get("changes_detail") or {}
    rows.append({
        "row_kind": "sanitizer",
        "turn": int(ev.get("turn") or 0),
        "ms": round(float(ev.get("ms", 0)), 1),
        "tokens_in": int(ev.get("tokens_in", 0)),
        "tokens_out": int(ev.get("tokens_out", 0)),
        "threads_updated": list(ev.get("threads_updated", [])),
        "threads_removed": list(ev.get("threads_removed", [])),
        "threads_resolved": list(ev.get("threads_resolved", [])),
        "threads_added": list(ev.get("threads_added", [])),
        "goal_changed": bool(ev.get("goal_changed")),
        "changes_detail": chg,
        "has_changes": bool(
            chg.get("updated")
            or chg.get("removed")
            or chg.get("resolved")
            or chg.get("added")
            or chg.get("goal")
        ),
    })
    continue
```

**`_turn_viewer.html`** — add sanitizer block between seed block and catch-all (between lines 69 and 71):

```html
<template x-if="t.row_kind === 'sanitizer'">
    <div class="tv-compaction-card">
        <div class="tv-compaction-header" @click="toggleTurnCollapsed('s-' + t.turn)">
            <span class="tv-compaction-icon">⟳</span>
            <span class="tv-compaction-title">Thread Sanitizer</span>
            <span class="tv-compaction-range" x-text="'Turn ' + t.turn"></span>
            <span class="tv-compaction-bullets" x-text="(t.threads_updated.length + t.threads_resolved.length + t.threads_removed.length + t.threads_added.length) + ' changes'"></span>
            <span x-show="t.has_changes" class="tv-compaction-san-badge">sanitized</span>
            <span class="tv-stage-chevron" :class="{ open: !isTurnCollapsed('s-' + t.turn) }">▶</span>
        </div>
        <div class="tv-compaction-body" x-show="!isTurnCollapsed('s-' + t.turn)">
            <div class="tv-compaction-label">Latency</div>
            <div class="tv-compaction-more" x-text="t.ms + 's / ' + (t.tokens_in + t.tokens_out) + ' tokens'"></div>
            <template x-if="t.has_changes && t.changes_detail">
                <div class="tv-compaction-san">
                    <template x-if="t.changes_detail.removed && t.changes_detail.removed.length">
                        <div class="tv-compaction-san-row">
                            Threads removed:
                            <template x-for="r in t.changes_detail.removed" :key="r">
                                <div class="tv-compaction-san-item" x-text="r.id + ': ' + r.reason"></div>
                            </template>
                        </div>
                    </template>
                    <template x-if="t.changes_detail.resolved && t.changes_detail.resolved.length">
                        <div class="tv-compaction-san-row">
                            Threads resolved:
                            <template x-for="r in t.changes_detail.resolved" :key="r.id">
                                <div class="tv-compaction-san-item" x-text="r.id + ' [' + r.resolution_state + '] ' + r.outcome"></div>
                            </template>
                        </div>
                    </template>
                    <template x-if="t.changes_detail.updated && Object.keys(t.changes_detail.updated).length">
                        <div class="tv-compaction-san-row">
                            Threads updated:
                            <template x-for="(fields, tid) in t.changes_detail.updated" :key="tid">
                                <div class="tv-compaction-san-item" x-text="tid + ': ' + Object.keys(fields).join(', ')"></div>
                            </template>
                        </div>
                    </template>
                    <template x-if="t.changes_detail.added && t.changes_detail.added.length">
                        <div class="tv-compaction-san-row">
                            Threads added:
                            <template x-for="a in t.changes_detail.added" :key="a.id">
                                <div class="tv-compaction-san-item" x-text="a.id + ' [' + a.urgency + '] ' + a.summary"></div>
                            </template>
                        </div>
                    </template>
                    <template x-if="t.changes_detail.goal && (t.changes_detail.goal.before !== t.changes_detail.goal.after)">
                        <div class="tv-compaction-san-row">
                            Arc goal updated:
                            <div class="tv-compaction-san-item" x-text="t.changes_detail.goal.before + ' → ' + t.changes_detail.goal.after"></div>
                        </div>
                    </template>
                </div>
            </template>
            <template x-if="!t.has_changes">
                <div class="tv-compaction-no-san">No thread changes needed.</div>
            </template>
        </div>
    </div>
</template>
```

**TV filter** — change the catch-all from `<template x-if="t.row_kind !== 'seed'">` to `<template x-if="t.row_kind !== 'seed' && t.row_kind !== 'sanitizer'">` and update `visibleTurns()` to always show sanitizer rows (like seed rows):

```javascript
// in visibleTurns():
if (t.row_kind === 'seed' || t.row_kind === 'sanitizer') return true;
```

## Alternatives Considered and Rejected

1. **Full rewrite of arc.threads[]** — LLM outputs complete replacement thread list. Rejected: any thread not mentioned by LLM gets silently dropped. Cost of accidental thread loss exceeds cost of delta complexity.

2. **Rule-based thread cleanup** — TTL-evict stale threads deterministically. Rejected: the whole point is narrative grounding, not mechanical TTL.

3. **Integrate into storyteller** — Fix threads every turn without extra LLM call. Rejected: adds surface area to the extraction prompt (already large and fragile).

4. **Run in background task** — Non-blocking, fire-and-forget after `yield("complete")`. Rejected for now: requires lock/merge strategy against next turn, adds complexity. Blocking matches old compactor behavior.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Separate module | `ccya/engine/thread_sanitizer.py` | Single responsibility, testable in isolation |
| Delta-based output | LLM names threads to update/remove/resolve/add; unmentioned threads survive | Prevents accidental thread loss |
| Blocking (synchronous) | Runs before `yield("complete")`, matching old compactor `turn.py:1596-1602` | Predictable SSE ordering, no race conditions |
| Runs after prior_history | After `turn.py:1415` (prior_history append + save), before `yield("complete")` at line 1434 | Has full narrative evidence (this turn's prose in chronicle, fresh prior_history, latest state) |
| Re-saves state on changes | `save_state(save_dir, state)` after applying sanitization | Changes persist before yield complete |
| events.jsonl record | `kind: "sanitizer"` following old compactor's record shape (`compactor.py:130-145`) | Turn viewer needs structured data |
| Prose-only evidence | No inventory, NPC sheet, conditions, or world_state in prompt | Keeps prompt focused on thread hygiene |
| 5 full turns + up to 20 summary bullets | `load_last_narration(save_dir, 5)` + `state.meta.prior_history` (max 20) | Matches existing pipeline memory patterns |
| Thread-first ordering | Arc/thread state BEFORE narration in user prompt | Sanitizer's job is thread assessment; narration is evidence to validate against |
| Reuses `tv-compaction-*` CSS | No new CSS classes | Already in `app.src.css:2563-2611` from old compactor |
| SSE phase shape matches old compactor | `{"phase": "sanitize_start", "expected_ms": 0}` / `{"phase": "sanitize_done", "ms": ...}` | UI handler follows same pattern; minimal branch in `_setProgressFromPhase()` |
| _checklist rubric in prompt | Mandatory checklist output forces LLM to acknowledge every category | Borrowed from old `compact_system.j2` — prevents silent skipping |
| Reuses `_thread_list.j2` | Existing shared template renders threads with id/scope/urgency/active/summary/progress | No duplication of rendering logic; template vars are compatible |

## Failure Modes and Risks

| Risk | Mitigation |
|---|---|
| LLM hallucinates thread deletions | Only threads in `removed_threads[]` are deleted; ID validated against existing threads first |
| LLM repeats prior_history as thread summaries | Prompt instructs present-tense actionable summaries; _checklist rubric requires model to articulate why |
| LLM call fails (timeout/parse/validation) | `sanitize_threads()` catches all exceptions, logs warning, returns unchanged state. Turn proceeds without sanitization. Zero disruption. |
| Sanitizer delays `yield("complete")` | SSE has already streamed narrative tokens; only the `complete` event waits. If too slow, reduce `sanitize_every` or set to 0. |
| Same thread in `thread_updates[]` and `removed_threads[]` | Validate: `removed_threads` takes precedence. Thread deleted, update ignored. |
| New thread ID collides with existing | Validate: skip duplicate ID, log warning. |
| Goal update overwrites player-authored goal | Sanitizer only changes goal if LLM explicitly outputs `goal_update`. Current design's safeguard: the prompt doesn't encourage goal changes unless narrative strongly supports it. |
| No shared template `_thread_list.j2` | `_thread_list.j2` exists at `ccya/prompts/sections/_thread_list.j2` and renders all thread fields the sanitizer needs. Its `gate` variable dependency is optional (inline if block). |

## Open Questions

- `[OPEN]` Should the sanitizer prune `completed_threads[]` entries older than `thread_memory_ttl` (default 3 turns)? Currently they accumulate forever. The LLM could move them to `removed_threads[]`, but nothing forces it. A separate TTL eviction pass in `_apply_sanitization()` could silently drop completed threads older than TTL. Not doing this yet — let's see if it becomes a problem.

- `[OPEN]` completed_threads TTL — the `thread_memory_ttl` config (default 3) currently only affects which completed threads are included in narrate/extract prompts (`_filter_completed_threads()` in `turn.py`). The underlying state still grows unbounded. The sanitizer could enforce eviction: after applying all other changes, drop completed threads with `resolved_turn < (current_turn - thread_memory_ttl)`. Easy to add, trivially safe (they're already excluded from prompts).

## What Is Removed

Nothing. This module is additive. No existing code is deleted.

## What Is Unchanged

- `prior_history` bullet format, append logic (20-max capping) — `turn.py:1406-1415`
- `_apply_thread_updates()` — `turn.py:144-213`
- `_apply_thread_resolutions()` — `turn.py:332-390`
- `run_turn()` SSE event format, yield order, error handling — `turn.py:896-1474`
- `save_state()` / `load_state()` / `append_chronicle()` — `state/io.py`, `state/chronicle.py`
- Extraction pipeline (scene/state/storytell) — zero prompt changes
- Narrate pipeline — zero changes
- Ruling pipeline — zero changes
- All existing EngineConfig fields and defaults — `config.py:92-165`
- `build_engine_config()` mapping for existing fields — `config.py:175-266`
- All HTML templates except the two new phase label branches and new TV row block
- CSS — all compaction classes already exist
- `CompactorSanitizationResult` in `models.py:376` — stays dormant
- `TurnResult` dataclass — `models.py` (no new fields)
- `TurnContext` dataclass — `turn.py:70-99` (no new fields)
- `__init__.py` files — no new exports needed (sanitizer is called only from turn.py)

## New Model Shapes

No new Pydantic models. Internal contract only:

```python
# ccya/engine/thread_sanitizer.py — internal dict contract
# No new Pydantic models. Parsed LLM output validated against existing models.

# LLM output shape (inside <sanitize>...</sanitize>):
{
    "goal_update": dict | None,           # {"visible_goal": str, "goal_context": str}
    "thread_updates": list[dict],          # each validated against ThreadUpdate
    "resolved_threads": list[dict],        # each validated against ThreadResolution
    "removed_threads": list[dict],         # [{"id": str, "reason": str}]
    "new_threads": list[dict],            # each validated against ArcThread
    "_checklist": dict[str, str],
}
```

## Context for Implementing LLMs

| File | What it contains | Why read it |
|---|---|---|
| `ccya/engine/thread_sanitizer.py` (create) | New module: `sanitize_threads()`, `_build_messages()`, `_parse_response()`, `_apply_sanitization()` | This design doc is the spec |
| `ccya/prompts/sanitize_thread.j2` (create) | System + user prompt for the sanitizer LLM call | Reuse `sections/_thread_list.j2`, follow checklist rubric pattern from old `compact_system.j2` |
| `ccya/engine/turn.py:1395-1434` | Pipeline hook point (after prior_history → before yield complete) | Exact insertion point; mirror old compactor hook at `be8113f1^:turn.py:1596-1602` |
| `ccya/engine/config.py:92-165` | EngineConfig dataclass | Add `sanitize_every`, `sanitize_temperature` |
| `ccya/engine/config.py:175-266` | `build_engine_config()` | Add mapping for new fields from config.yaml |
| `ccya/models.py:34-69` | `ArcThread`, `CampaignArc` | Validate output thread objects |
| `ccya/models.py:397-403` | `ThreadUpdate` | Validate thread_updates output |
| `ccya/models.py:389-394` | `ThreadResolution` | Validate resolved_threads output |
| `ccya/state/chronicle.py:45-65` | `load_last_narration()` | Load 5 recent full turns from chronicle.md |
| `ccya/prompts/sections/_thread_list.j2` | Thread rendering template (id/scope/urgency/active/summary/progress) | Reuse in sanitizer user prompt |
| `ccya/server/tv.py:370-400` area | Turn viewer row building | Add sanitizer row_kind handler; mirror old compaction handler at `be8113f1^:tv.py:376-392` |
| `ccya/templates/_turn_viewer.html:47-71` | Turn viewer template — seed block + catch-all | Add sanitizer row block between them; mirror old compaction block at `be8113f1^:_turn_viewer.html:71-130` |
| `ccya/templates/index.html:745-779` | Phase label handler `_setProgressFromPhase()` | Add `sanitize_start`/`sanitize_done` branches; mirror old compact phase at `be8113f1^:index.html:546-550` |
| `git show be8113f1^:ccya/engine/compactor.py` | Old compactor | Reference: trigger check, event record shape, LLM call pattern, apply pattern |
| `git show be8113f1^:ccya/prompts/compact_system.j2` | Old compactor system prompt | Reference: _checklist rubric, output format, confidence guidelines |
| `git show be8113f1^:ccya/templates/_turn_viewer.html` (lines 40-130) | Old turn viewer with compaction row | Reference: row template structure, filter checkbox, card toggle |
| `git show be8113f1^:ccya/server/tv.py` (lines 370-400) | Old tv.py compaction handler | Reference: ev.get("kind") branching, row dict shape |
