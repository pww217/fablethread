# Eval Full-Context Trace

**Status:** Draft · May 2026  
**Scope:** Replace the compact `build_trace()` with a full-context trace that includes all inputs and outputs the turn engine processes — system prompts (per-turn), user prompts (per turn), world pack content, and state snapshots.

---

## Vision

The judge must evaluate the engine using the **same data the engine itself uses**. No summaries, no abstractions, no parallel data collection. The trace is a faithful reconstruction of every input and output the turn pipeline processes.

**Two non-negotiable principles:**

1. **Engine-agnostic.** The trace builder reads only from `events.jsonl` — the canonical output of the core engine pipeline. It does not import engine modules, does not know about new mechanics, and does not need updating when features change. If the engine produces it in events.jsonl, the judge sees it. If a new mechanic changes how the engine works, the trace automatically reflects it because it reads rendered prompts and state snapshots, not hardcoded field names.

2. **Complete observability.** The judge sees every input and output: all 5 rendered prompts per turn (rules system/user, narrate system/user, 3 extraction system/user), all engine outputs (rules outcome, narration text, 3 extraction outputs, applied/rejected deltas, suggested actions), per-turn state snapshots, and the world pack style text. No data is summarized or truncated unless the trace exceeds the judge's budget — and even then, the truncation strategy preserves the beginning and end of the run.

**What this means in practice:** When a new mechanic is added (e.g., a new extraction stream, a new state field, a new prompt section), the trace automatically includes it. The judge rubric may need updating to evaluate the new criterion, but the trace builder does not need any code changes. The engine is the single source of truth.

---

## Problem

The current `build_trace()` in `ccya/eval/judge.py` produces a compact summary (~30000 chars) that omits critical information the rubric asks the judge to evaluate:

- **context_fidelity (#6):** Judge can't see rendered prompts — only token estimates. Can't verify the rules call actually knew stats/conditions, or that extractors actually saw the narration.
- **state_drift (#10):** Judge only sees per-turn applied summaries, not actual state values. Can't verify inventory totals match, or that recent_events has stale duplicates.
- **mechanical_consistency (#11):** Judge can't verify momentum changes (no `meta.momentum` visible), can't verify conditions don't duplicate.
- **npc_development (#13):** Judge can't see NPC bios or compendium — only `present_npcs` in extraction output.
- **player_agency (#14):** Judge can't see `actions` (suggested actions).
- **pacing_and_pressure (#15):** Judge can't see pressure expiry (no state history), only `scene_pressure_add` in extraction output.
- **genre_and_universe_fit (#4):** Judge can't see `style.md` or world state to verify lore consistency.

The events.jsonl already stores all rendered prompts (`rendered_system`, `rendered_user`) for every stream. The judge just doesn't see them.

---

## Design

### Data Sourcing: Metadata Event in events.jsonl

**Decision:** The runner writes a single metadata event as the first line of `events.jsonl`. The judge reads it from there. No external file loading, no path guessing, no new function parameters.

**Why:** The plan's original approach of loading `state.yaml` from the run directory and passing `pack_style` as a parameter is fragile:
- The runner writes `{scenario_id}.state.yaml`, not `state.yaml` — path resolution would break
- `pack_style` isn't stored in any file accessible to `run_judge()`
- This creates a divergence path: eval needs to know about pack loading just for the judge
- `run_judge()` would need new parameters, breaking the contract

**How:** The runner (`ccya/eval/runner.py`) writes a metadata event as the first line of `events.jsonl` before the turn events:

```python
# In runner.py, after loading events, prepend metadata:
metadata_event = {
    "__metadata__": True,
    "pack_id": pack.manifest.id,
    "pack_style": pack.style_text,
    "seed_state": seed,  # pack.seed.model_dump()
}
# Prepend to events list, then write back
events.insert(0, metadata_event)
```

The judge's `build_trace()` reads `events[0]` to check for metadata, then processes turn events starting from `events[1]`.

**What the metadata event contains:**
| Field | Source | Purpose |
|---|---|---|
| `__metadata__` | Hardcoded `True` | Marker to distinguish from turn events |
| `pack_id` | `pack.manifest.id` | Identifies which pack was used |
| `pack_style` | `pack.style_text` | World pack style.md content for genre/lore evaluation |
| `seed_state` | `pack.seed.model_dump()` | Initial state: meta, pc, inventory, quests, compendium, world |

**Why seed_state is the full model dump (not key fields):** The judge needs the complete initial state to verify state drift. Key-field extraction is a trace-builder optimization that loses information. The seed state is bounded (one-time, not per-turn) and fits within the budget.

### Trace Structure

The trace has two sections, in order:

```
═══════════════════════════════════════════════════════════
SECTION 1: STATIC CONTEXT (one-time, shared by all turns)
═══════════════════════════════════════════════════════════

## World Pack Style
[pack.style_text content]

## Seed State
[full seed_state JSON — meta, pc, inventory, quests, compendium, world]

## Engine Constants
[constants_block() output — already exists]

## System Prompts (per-turn, from turn 1)

### Rules System Prompt
[rendered_system from turn 1 rules_prompt]

### Narrate System Prompt
[rendered_system from turn 1 narrate_prompt]

### Extract Scene System Prompt
[rendered_system from turn 1 extraction.scene.rendered_system]

### Extract State System Prompt
[rendered_system from turn 1 extraction.state.rendered_system]

### Extract Progress System Prompt
[rendered_system from turn 1 extraction.progress.rendered_system]

═══════════════════════════════════════════════════════════
SECTION 2: PER-TURN CONTEXT
═══════════════════════════════════════════════════════════

TURN 1 — [input]

### System Prompts

#### Rules System Prompt
[rendered_system from turn 1 rules_prompt]

#### Narrate System Prompt
[rendered_system from turn 1 narrate_prompt]

#### Extract Scene System Prompt
[rendered_system from turn 1 extraction.scene.rendered_system]

#### Extract State System Prompt
[rendered_system from turn 1 extraction.state.rendered_system]

#### Extract Progress System Prompt
[rendered_system from turn 1 extraction.progress.rendered_system]

### User Prompts

#### Rules User Prompt
[rendered_user from turn 1 rules_prompt]

#### Narrate User Prompt
[rendered_user from turn 1 narrate_prompt]

#### Extract Scene User Prompt
[rendered_user from turn 1 extraction.scene.rendered_user]

#### Extract State User Prompt
[rendered_user from turn 1 extraction.state.rendered_user]

#### Extract Progress User Prompt
[rendered_user from turn 1 extraction.progress.rendered_user]

### Engine Outputs

#### Rules
[full rules event: band, skill, difficulty, dice, stat_mod, diff_mod, cond_mod, final_total, outcome_summary, intent_verb, intent]

#### Narration
[full narration text — no truncation]

#### Extraction: Scene
[full extraction.scene output: scene_tags, present_npcs, location_change, summary, etc.]

#### Extraction: State
[full extraction.state output: inventory_add/remove/update, pc_condition_add/remove, etc.]

#### Extraction: Progress
[full extraction.progress output: quest_updates, recent_events_add, compendium_npc_update, scene_pressure_add, pending_gm_beat, etc.]

#### Applied Deltas
[full applied dict — no summary]

#### Rejected Deltas
[full rejected list]

#### Suggested Actions
[full actions list]

#### Context Telemetry
[per-stream est_tokens, trimmed flag, trimmed_chars — from context_meta]

### State After Turn
[full state snapshot: meta.momentum, scene.scene_pressure, pc.conditions, inventory, quests, compendium.npcs, scene.present_npcs, scene.recent_events, scene.pending_gm_beat]

---

TURN 2 — [input]
...
```

### Key Design Decisions

#### 1. Per-turn system prompts (not turn-1 only)

**Decision:** Include system prompts per-turn for every stream.

**Rationale:** The original plan's "render once from turn 1" assumption is fragile:
- Rules system prompt is static, but the user prompt changes every turn (recent_turns, chronicle)
- Extraction system prompts are static Jinja templates, but extraction user prompts change
- The `run_turn_retry` path sets `rules_prompt` to empty strings — turn-1 assumption would silently skip rules prompts for retry turns
- If a future change makes system prompts dynamic, the trace would silently lie by showing stale turn-1 data
- Including per-turn system prompts costs nothing — they're already captured in events.jsonl

**Tradeoff:** Slightly larger trace. Mitigated by the truncation strategy (static context is included once, per-turn system prompts are bounded).

#### 2. No new parameters to `build_trace()` or `run_judge()`

**Decision:** `build_trace(events, *, max_chars)` reads everything from events.jsonl. `run_judge()` signature is unchanged.

**Rationale:** New parameters create divergence paths. The runner already has `pack.style_text` and `pack.seed` — it writes them into the metadata event. The judge reads them from events.jsonl. Zero new dependencies, zero new file I/O paths.

#### 3. Greedy truncation with guaranteed first+last turns

**Decision:** If the trace exceeds `max_chars`, include static context + first turn + last turn + as many middle turns as fit greedily. Never truncate static context. Never truncate user prompts within a turn.

**Rationale:** The original plan's "first N/2 + last N/2" approach creates a gap in the middle where the judge can't see cause-and-effect chains. A 10-turn run with middle truncated loses the critical development phase. The judge needs to see the beginning (initial state, first decisions) and the end (final state, outcomes) plus as much middle as possible.

**Truncation order:**
1. Never truncate static context (world pack, seed state, constants, system prompts)
2. Always include turn 1 and the last turn
3. Greedily fill middle turns
4. If a single turn's user prompts exceed remaining budget, include the turn but truncate narration/extraction outputs within it
5. Add truncation marker

#### 4. Don't change `JudgeConfig.max_input_chars` default

**Decision:** Keep `JudgeConfig.max_input_chars` default at 30000. The `evals/config.yaml` already has `max_input_chars: 100000`.

**Rationale:** Changing the Python default affects all consumers. The eval harness already overrides it via config. The default of 30000 is appropriate for the compact trace fallback.

#### 5. State snapshots include full state (not key fields)

**Decision:** Per-turn state snapshots include the full state dict, not a filtered subset.

**Rationale:** The judge needs to verify state drift across turns. Filtering state fields risks hiding drift in fields the trace builder author didn't anticipate. The state snapshot is bounded per-turn and the judge can focus on relevant fields.

**Caveat:** The snapshot is captured after `run_turn()` completes and after compaction (if enabled). This means `recent_events` may be pruned in the snapshot. This is correct — the judge should see the state as the engine leaves it, not the intermediate state before compaction.

#### 6. Compact trace as fallback

**Decision:** If static context alone exceeds 30% of `max_chars`, fall back to the compact trace. This protects against regressions where a pack's style text or system prompts grow unexpectedly large.

**Rationale:** A 100KB+ style.md or a system prompt that grew to 50KB would make the full-context trace unusable. The fallback ensures the judge still gets useful output.

---

## Implementation

### Files Changed

| File | Change |
|---|---|
| `ccya/eval/runner.py` | Write metadata event as first line of events.jsonl |
| `ccya/eval/judge.py` | Rewrite `build_trace()` — new structure with static context + per-turn context |
| `ccya/eval/judge.py` | Rename current `build_trace()` to `_compact_trace()` for fallback |
| `ccya/eval/judge.py` | New `_render_static_context()` function |
| `ccya/eval/judge.py` | New `_render_turn_context()` function |
| `ccya/eval/judge.py` | New `_extract_state_keys()` function for state snapshots |
| `ccya/eval/judge.py` | New `_truncate_trace()` function for truncation strategy |
| `evals/rubrics/default.md` | Add trace format instructions at top |
| `docs/REPOMAP/eval.md` | Update `build_trace()` description |
| `docs/plans/TODO.md` | Mark as complete |
| `tests/test_eval.py` | Add unit tests for `build_trace()` |

### `build_trace()` Signature (unchanged)

```python
def build_trace(events: list[dict[str, Any]], *, max_chars: int) -> str:
```

Reads `pack_style` and `seed_state` from the metadata event at `events[0]`. Processes turn events from `events[1:]`.

### Runner Changes: Metadata Event

In `ccya/eval/runner.py`, after collecting events from `events.jsonl` and before writing to `dst_events`:

```python
# After loading events from src_events:
events_lines = src_events.read_text().splitlines()
events = [json.loads(ln) for ln in events_lines if ln.strip()]

# Prepend metadata event
metadata_event = {
    "__metadata__": True,
    "pack_id": pack.manifest.id,
    "pack_style": pack.style_text,
    "seed_state": seed,  # pack.seed.model_dump()
}
events.insert(0, metadata_event)

# Merge state snapshots into events for state_yaml assertions
for i, snap in enumerate(state_snapshots):
    if i < len(events):
        events[i]["state_snapshot"] = snap

# Run structured asserts
for i, turn in enumerate(scenario.turns):
    if i >= len(turn_records):
        break
    record = turn_records[i]
    if i < len(events) and turn.asserts:
        record.assert_results = _check_asserts(turn.asserts, events[i])

# Write back with metadata prepended
dst_events.write_text("\n".join(json.dumps(ev) for ev in events) + "\n")
```

**Caveat:** The metadata event is a JSON object with `__metadata__: True`. It is not a turn event. The judge's `build_trace()` must skip it when iterating turns.

**Caveat:** The metadata event is written to the output events file (`{scenario_id}.events.jsonl`) but NOT to the save-dir events file (`save_dir/events.jsonl`). The save-dir events file is written by the engine during `run_turn()` and is not modified by the runner.

### `build_trace()` Implementation

```python
def build_trace(events: list[dict[str, Any]], *, max_chars: int) -> str:
    """Build the full-context trace string sent to the judge as the user message.
    
    The first event may be a metadata event (__metadata__: True) written by the
    runner. Turn events follow. Each turn event contains rendered prompts, engine
    outputs, applied/rejected deltas, and a state snapshot.
    """
    # Separate metadata from turn events
    metadata: dict[str, Any] = {}
    turn_events: list[dict[str, Any]] = []
    for ev in events:
        if isinstance(ev, dict) and ev.get("__metadata__"):
            metadata = ev
        else:
            turn_events.append(ev)
    
    pack_style = metadata.get("pack_style", "")
    seed_state = metadata.get("seed_state")
    
    # Render static context
    static = _render_static_context(pack_style, seed_state, turn_events)
    
    # Safety: if static context alone is too large, fall back to compact trace
    if len(static) > max_chars * 0.3:
        return _compact_trace(events, max_chars=max_chars)
    
    remaining = max_chars - len(static)
    
    # Render all turn blocks
    turn_blocks = []
    for ev in turn_events:
        block = _render_turn_context(ev)
        turn_blocks.append(block)
    
    # Truncation: always include first and last turn, greedily fill middle
    if len(turn_blocks) <= 2:
        turns_to_include = turn_blocks
    else:
        first_block = turn_blocks[0]
        last_block = turn_blocks[-1]
        middle_blocks = turn_blocks[1:-1]
        
        # Check if first + last fit
        if len(first_block) + len(last_block) > remaining:
            # Even first+last don't fit — fall back to compact
            return _compact_trace(events, max_chars=max_chars)
        
        # Greedily fill middle
        middle_included = []
        chars_used = len(first_block) + len(last_block)
        for block in middle_blocks:
            if chars_used + len(block) <= remaining:
                middle_included.append(block)
                chars_used += len(block)
            else:
                # Try to partially include this turn (truncate narration/extraction)
                # For now, stop — the compact fallback is safer
                break
        
        turns_to_include = [first_block] + middle_included + [last_block]
    
    trace = static + "\n".join(turns_to_include)
    
    # Add truncation marker if we dropped turns
    if len(trace) < len(static) + sum(len(b) for b in turn_blocks):
        trace += "\n\n[... trace truncated — not all turns included ...]\n\n"
    
    return trace
```

### `_render_static_context()`

```python
def _render_static_context(
    pack_style: str,
    seed_state: dict[str, Any] | None,
    turn_events: list[dict[str, Any]],
) -> str:
    """Render the one-time context section of the trace.
    
    Includes: world pack style, seed state, engine constants,
    and the 5 system prompts from turn 1.
    """
    lines = []
    
    # World pack style
    if pack_style:
        lines.append("## World Pack Style\n")
        lines.append("```\n" + pack_style + "\n```\n")
    
    # Seed state
    if seed_state:
        lines.append("## Seed State\n")
        lines.append("```json\n" + json.dumps(seed_state, indent=2, default=str) + "\n```\n")
    
    # Engine constants (existing)
    lines.append("## Engine Constants\n")
    lines.append(constants_block())
    
    # System prompts from turn 1
    if turn_events:
        first = turn_events[0]
        lines.append("## System Prompts (from turn 1)\n")
        
        rules_sys = (first.get("rules_prompt") or {}).get("rendered_system", "")
        if rules_sys:
            lines.append("### Rules System Prompt\n")
            lines.append("```\n" + rules_sys + "\n```\n")
        
        narr_sys = (first.get("narrate_prompt") or {}).get("rendered_system", "")
        if narr_sys:
            lines.append("### Narrate System Prompt\n")
            lines.append("```\n" + narr_sys + "\n```\n")
        
        extraction = first.get("extraction") or {}
        for stream_name, label in [("scene", "Extract Scene"), ("state", "Extract State"), ("progress", "Extract Progress")]:
            ex = extraction.get(stream_name) or {}
            sys_prompt = ex.get("rendered_system", "")
            if sys_prompt:
                lines.append(f"### {label} System Prompt\n")
                lines.append("```\n" + sys_prompt + "\n```\n")
    
    return "\n".join(lines)
```

### `_render_turn_context()`

```python
def _render_turn_context(event: dict[str, Any]) -> str:
    """Render the per-turn context section of the trace."""
    turn = event.get("turn", "?")
    inp = event.get("input", "")
    lines = [f"\nTURN {turn} — {inp}\n"]
    
    # System prompts (per-turn)
    lines.append("### System Prompts\n")
    
    rules_sys = (event.get("rules_prompt") or {}).get("rendered_system", "")
    if rules_sys:
        lines.append("#### Rules System Prompt\n")
        lines.append("```\n" + rules_sys + "\n```\n")
    
    narr_sys = (event.get("narrate_prompt") or {}).get("rendered_system", "")
    if narr_sys:
        lines.append("#### Narrate System Prompt\n")
        lines.append("```\n" + narr_sys + "\n```\n")
    
    extraction = event.get("extraction") or {}
    for stream_name, label in [("scene", "Extract Scene"), ("state", "Extract State"), ("progress", "Extract Progress")]:
        ex = extraction.get(stream_name) or {}
        sys_prompt = ex.get("rendered_system", "")
        if sys_prompt:
            lines.append(f"#### {label} System Prompt\n")
            lines.append("```\n" + sys_prompt + "\n```\n")
    
    # User prompts
    lines.append("### User Prompts\n")
    
    rules_user = (event.get("rules_prompt") or {}).get("rendered_user", "")
    if rules_user:
        lines.append("#### Rules User Prompt\n")
        lines.append("```\n" + rules_user + "\n```\n")
    
    narr_user = (event.get("narrate_prompt") or {}).get("rendered_user", "")
    if narr_user:
        lines.append("#### Narrate User Prompt\n")
        lines.append("```\n" + narr_user + "\n```\n")
    
    for stream_name, label in [("scene", "Extract Scene"), ("state", "Extract State"), ("progress", "Extract Progress")]:
        ex = extraction.get(stream_name) or {}
        user_prompt = ex.get("rendered_user", "")
        if user_prompt:
            lines.append(f"#### {label} User Prompt\n")
            lines.append("```\n" + user_prompt + "\n```\n")
    
    # Engine outputs
    lines.append("### Engine Outputs\n")
    
    # Rules
    rules = event.get("rules") or {}
    if rules:
        lines.append("#### Rules\n")
        lines.append(json.dumps(rules, indent=2))
        lines.append("")
    
    # Narration (full, no truncation)
    narration = (event.get("narrate_prompt") or {}).get("output", "")
    if narration:
        lines.append("#### Narration\n")
        lines.append(narration)
        lines.append("")
    
    # Extraction outputs (full)
    for stream_name, label in [("scene", "Extract Scene"), ("state", "Extract State"), ("progress", "Extract Progress")]:
        ex = extraction.get(stream_name) or {}
        output = ex.get("output")
        if output:
            lines.append(f"#### {label}\n")
            lines.append(json.dumps(output, indent=2, default=str))
            lines.append("")
    
    # Applied / Rejected / Actions
    applied = event.get("applied") or {}
    if applied:
        lines.append("#### Applied Deltas\n")
        lines.append(json.dumps(applied, indent=2, default=str))
        lines.append("")
    
    rejected = event.get("rejected") or []
    if rejected:
        lines.append("#### Rejected Deltas\n")
        lines.append(json.dumps(rejected, indent=2, default=str))
        lines.append("")
    
    actions = event.get("actions") or []
    if actions:
        lines.append("#### Suggested Actions\n")
        lines.append(json.dumps(actions, indent=2))
        lines.append("")
    
    # Context telemetry
    lines.append("#### Context Telemetry\n")
    lines.append(_context_line(event))
    lines.append("")
    
    # State snapshot
    state_snap = event.get("state_snapshot") or {}
    if state_snap:
        lines.append("### State After Turn\n")
        lines.append(json.dumps(state_snap, indent=2, default=str))
        lines.append("")
    
    lines.append("---")
    return "\n".join(lines)
```

### `_compact_trace()` (renamed from current `build_trace()`)

```python
def _compact_trace(events: list[dict[str, Any]], *, max_chars: int) -> str:
    """Compact trace fallback — used when full-context trace exceeds budget.
    
    This is the original build_trace() logic, preserved for fallback.
    """
    # ... current build_trace() implementation, unchanged ...
    lines: list[str] = [constants_block()]
    blocks: list[str] = []
    for ev in events:
        # ... current logic ...
    # ... current truncation logic ...
```

### Rubric Update

Update the rubric's instruction at the top to tell the judge how to read the new trace format:

```markdown
# ccya Eval Judge — Default Rubric

You are evaluating one run of an interactive narrative game. The game's engine
makes 5 LLM calls per turn:

1. **rules** — classify intent, decide if a skill check is needed, choose scope.
2. **narrate** — write the prose for this turn given the rules outcome.
3. **extract.scene** — extract scene-level changes (location, present_npcs, tags, summary).
4. **extract.state** — extract pc-level changes (inventory deltas, conditions).
5. **extract.progress** — extract longer-arc changes (quest progress, recent_events, compendium NPC bios).

## Trace format

The user message contains:

1. **Static Context** — World pack style (style.md), seed state (initial game state),
   engine constants (live thresholds), and the 5 system prompts from turn 1.
   These define the rules and constraints the engine operates under.

2. **Per-Turn Context** — For each turn: the 5 system prompts (rendered for that turn),
   the 5 user prompts (rendered for that turn), all engine outputs (rules, narration,
   3 extraction outputs, applied/rejected deltas, actions), context telemetry, and
   the full state snapshot after the turn.

**How to evaluate:**
- Compare each turn's user prompts against its outputs to verify context fidelity.
- Compare consecutive state snapshots to verify state drift and mechanical consistency.
- Use the system prompts as the ground truth for what the engine was instructed to do.
- Use the seed state and engine constants as the ground truth for thresholds and initial conditions.
- The trace includes ALL data the engine processed — do not assume information is missing
  because it is not in the compact summary format you may have seen before.
```

---

## Estimated Trace Size

For a 10-turn eval with the eval-pack:

| Section | Approx chars |
|---|---|
| Static context (style + seed state + constants + 5 system prompts) | ~20,000 |
| Per turn (5 system prompts + 5 user prompts + rules + narration + 3 extraction outputs + applied + state snapshot) | ~12,000 |
| 10 turns | ~120,000 |
| **Total** | **~140,000** |

This exceeds the 100,000 char budget. Truncation will include turn 1, turn 10, and as many middle turns as fit. For the eval-pack specifically (short narration, small state), the per-turn size may be closer to 8,000 chars, bringing the total to ~100,000.

**Mitigation:** The truncation strategy guarantees the judge sees the beginning and end of the run. For longer runs (20+ turns), the judge will see turn 1, turn N, and a subset of middle turns.

**Note:** The per-turn estimate includes per-turn system prompts (the original plan's "render once" optimization would save ~2,000 chars for system prompts). This is intentional — per-turn system prompts are more accurate and the budget increase is acceptable.

---

## Risks and Mitigations

### Risk 1: Trace size exceeds budget for large packs

**Severity:** High  
**Impact:** Truncation kicks in, judge sees incomplete run  
**Mitigation:** 
- Truncation strategy guarantees first+last turns
- Compact trace fallback if static context exceeds 30% of budget
- `max_input_chars: 100000` in eval config is already generous
- If a pack's style.md is extremely large, the static context check catches it

### Risk 2: `run_turn_retry` events have empty rules prompts

**Severity:** Medium  
**Impact:** Rules system/user prompts missing for retry turns  
**Mitigation:** `_render_turn_context()` checks for empty prompts and skips them gracefully. The rules output and narration are still present.

### Risk 3: State snapshot captures post-compaction state

**Severity:** Low  
**Impact:** `recent_events` in snapshot may be pruned vs. intermediate state  
**Mitigation:** This is correct behavior — the judge should see the state as the engine leaves it. The compaction is part of the engine pipeline.

### Risk 4: Metadata event format changes in future

**Severity:** Low  
**Impact:** Judge misinterprets metadata as turn event  
**Mitigation:** The `__metadata__: True` marker is checked explicitly. If the runner stops writing metadata, `build_trace()` falls back to compact trace (no metadata = no seed_state = static context is smaller).

### Risk 5: New extraction streams or prompt types

**Severity:** None (by design)  
**Impact:** Trace builder would need updating  
**Mitigation:** The trace builder iterates over the known stream names (`scene`, `state`, `progress`). If a new stream is added, it won't appear in the trace. However, the rules/narrate prompts are always captured. The trace builder should be updated when new streams are added, but this is a low-effort change (add one stream name to the iteration list).

**Alternative:** Make the iteration dynamic by inspecting the event structure. This adds complexity and fragility. The current approach (explicit stream names) is simpler and the streams are stable.

### Risk 6: JSON serialization of state snapshots

**Severity:** Low  
**Impact:** State snapshots with non-serializable types (datetime, Path) cause errors  
**Mitigation:** `json.dumps(..., default=str)` handles non-serializable types by converting to string. This is already used in the runner.

### Risk 7: Regressions in existing eval behavior

**Severity:** Medium  
**Impact:** Compact trace fallback path has bugs  
**Mitigation:** 
- `_compact_trace()` is the original `build_trace()` implementation, unchanged
- Unit tests verify both full-context and compact trace paths
- Integration test (`make eval`) validates end-to-end

---

## Testing

### Unit Tests (`tests/test_eval.py`)

1. **`test_build_trace_full_context_structure()`** — Verify trace has static context section followed by per-turn sections. Verify metadata event is parsed correctly.

2. **`test_build_trace_no_metadata()`** — Verify fallback to compact trace when no metadata event present.

3. **`test_build_trace_truncation_first_last()`** — Verify that when truncation is needed, turn 1 and the last turn are always included.

4. **`test_build_trace_retry_turns()`** — Verify that events with empty rules prompts (from `run_turn_retry`) are handled gracefully.

5. **`test_build_trace_static_context_too_large()`** — Verify fallback to compact trace when static context exceeds 30% of budget.

6. **`test_build_trace_no_truncation_small_run()`** — Verify that a small run (3 turns) produces a complete trace without truncation.

7. **`test_metadata_event_format()`** — Verify the metadata event written by the runner has the correct structure.

### Integration Test

Run `make eval` with the full-context trace and verify the judge produces valid output. Compare scores with the compact trace to ensure no regressions.

---

## Migration

1. **Add metadata event to runner.** In `runner.py`, prepend metadata event to events list before writing to output file.

2. **Rename current `build_trace()` to `_compact_trace()`.** Preserve original implementation unchanged.

3. **Implement new `build_trace()`** with full-context logic, reading metadata from events[0].

4. **Implement `_render_static_context()`** — world pack, seed state, constants, turn-1 system prompts.

5. **Implement `_render_turn_context()`** — per-turn system prompts, user prompts, engine outputs, state snapshots.

6. **Update rubric** with trace format instructions.

7. **Add unit tests** for all edge cases.

8. **Run `make eval`** to verify end-to-end.

9. **Update `docs/REPOMAP/eval.md`** with new `build_trace()` description.

10. **Mark TODO complete.**

---

## What This Does NOT Do

- **Does not add new engine instrumentation.** The trace reads only from events.jsonl, which the engine already writes. No new logging, no new state fields, no new API calls.
- **Does not change the engine pipeline.** `run_turn()`, `run_turn_retry()`, and all submodules are unchanged.
- **Does not add new eval infrastructure.** No new config keys, no new CLI flags, no new files.
- **Does not change the judge model or rubric criteria.** The rubric is updated only with trace format instructions. The 15 criteria remain the same.
- **Does not handle new mechanics automatically.** If a new mechanic adds a new extraction stream or new state field, the trace builder needs a one-line update to include the new stream name. The judge rubric needs a new criterion. But the trace builder does not need to know about the mechanic's logic — it just reads whatever the engine produces.
