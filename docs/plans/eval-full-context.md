# Eval Full-Context Trace

**Status:** Draft · May 2026  
**Scope:** Replace the compact `build_trace()` with a full-context trace that includes all inputs and outputs the turn engine processes — system prompts (rendered once), user prompts (per turn), world pack content, and state snapshots.

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

### Trace Structure

The new trace has three sections, in order:

```
═══════════════════════════════════════════════════════════
SECTION 1: STATIC CONTEXT (rendered once, shared by all turns)
═══════════════════════════════════════════════════════════

## World Pack
[style.md content]

## Seed State (key fields)
[meta.momentum, pc.stats, pc.conditions, inventory summary, quests summary, compendium.npcs summary]

## Engine Constants
[constants_block() output — already exists]

## System Prompts (rendered once from turn 1)

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

### User Prompts (rendered for this turn)

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
[per-stream est_tokens, trimmed flag, trimmed_chars — same as current _context_line]

### State After Turn
[full state snapshot: meta.momentum, scene.scene_pressure, pc.conditions, inventory, quests, compendium.npcs, scene.present_npcs, scene.recent_events, scene.pending_gm_beat]

---

TURN 2 — [input]
...
```

### Key Design Decisions

1. **System prompts rendered once from turn 1.** The system prompts are Jinja templates rendered against the initial state. They are nearly identical across turns (only `recent_turns` and `chronicle` sections change, and those are in the *user* prompt, not system). We take the turn 1 rendered system prompt for each of the 5 calls.

2. **User prompts per turn.** These contain the turn-specific context (recent turns, chronicle, narration, scope). Each turn's user prompts are included in full.

3. **No truncation on narration or extraction outputs.** The compact trace trims narration to 800 chars and extraction outputs to 300 chars. The full-context trace includes them in full.

4. **State snapshots per turn.** After each turn, the full state is included so the judge can verify state drift, momentum changes, pressure expiry, and NPC bio evolution.

5. **World pack content included once.** `style.md` and key fields from `seed_state.yaml` (momentum, stats, conditions, inventory, quests, NPC compendium) are included at the top.

6. **`max_input_chars` raised to 100000.** Already set in `evals/config.yaml`. The default in `JudgeConfig` is 30000 — this needs to be raised to 100000 to match.

---

## Implementation

### Files Changed

| File | Change |
|---|---|
| `ccya/eval/judge.py` | Rewrite `build_trace()` — new structure with static context + per-turn context |
| `ccya/eval/judge.py` | New `_render_static_context()` function |
| `ccya/eval/judge.py` | New `_render_turn_context()` function |
| `ccya/eval/judge.py` | New `_state_summary()` function for state snapshots |
| `ccya/eval/config.py` | Raise `JudgeConfig.max_input_chars` default from 30000 to 100000 |
| `evals/config.yaml` | Verify `max_input_chars: 100000` (already set) |
| `docs/REPOMAP/eval.md` | Update `build_trace()` description |
| `docs/plans/TODO.md` | Mark as complete |

### `build_trace()` Signature

```python
def build_trace(
    events: list[dict[str, Any]],
    *,
    max_chars: int,
    pack_style: str = "",
    seed_state: dict[str, Any] | None = None,
) -> str:
```

The new signature accepts optional `pack_style` and `seed_state` parameters. These are passed from `run_judge()` which already has access to the pack and state.

### `run_judge()` Changes

In `run_judge()`, after loading events:

```python
# Load pack style and seed state for full-context trace
pack_style = ""
seed_state = None
if game_config_path:
    game_cfg = load_config(game_config_path)
    # ... load pack style from pack.style_text if available
    # ... load seed state from save_dir if available
```

Actually, `run_judge()` receives `events_path` and `game_config_path`. The events are from a run directory which has the state snapshot. We can load the state from the run's state.yaml.

```python
# In run_judge():
events = [json.loads(line) for line in events_lines if line.strip()]

# Load state snapshot from the run for static context
state_snap = {}
state_yaml_path = events_path.parent / "state.yaml"
if state_yaml_path.exists():
    try:
        import yaml
        state_snap = yaml.safe_load(state_yaml_path.read_text()) or {}
    except Exception:
        pass

trace = build_trace(events, max_chars=eval_cfg.judge.max_input_chars, seed_state=state_snap)
```

### `_render_static_context()`

```python
def _render_static_context(seed_state: dict[str, Any] | None, first_event: dict[str, Any]) -> str:
    """Render the one-time context section of the trace.
    
    Includes: world pack style, seed state key fields, engine constants,
    and the 5 system prompts rendered from turn 1.
    """
    lines = []
    
    # World pack style
    if seed_state:
        lines.append("## World Pack Style\n")
        # style.md is not in state — need to pass it separately
        # For now, skip or pass as param
    
    # Seed state key fields
    if seed_state:
        lines.append("## Seed State (key fields)\n")
        lines.append(f"- **Momentum:** {seed_state.get('meta', {}).get('momentum', 0)}")
        lines.append(f"- **PC:** {seed_state.get('pc', {}).get('name', '?')}")
        lines.append(f"- **Stats:** {json.dumps(seed_state.get('pc', {}).get('stats', {}))}")
        lines.append(f"- **Conditions:** {len(seed_state.get('pc', {}).get('conditions', []))}")
        inv = seed_state.get('inventory', [])
        lines.append(f"- **Inventory:** {len(inv)} items")
        quests = seed_state.get('quests', [])
        lines.append(f"- **Quests:** {len(quests)} active")
        comp = seed_state.get('compendium', {}).get('npcs', {})
        lines.append(f"- **NPC Compendium:** {len(comp)} NPCs")
        lines.append("")
    
    # Engine constants (existing)
    lines.append("## Engine Constants\n")
    lines.append(constants_block())
    
    # System prompts from turn 1
    if first_event:
        lines.append("## System Prompts (rendered once from turn 1)\n")
        
        rules_sys = (first_event.get("rules_prompt") or {}).get("rendered_system", "")
        if rules_sys:
            lines.append("### Rules System Prompt\n")
            lines.append("```\n" + rules_sys + "\n```\n")
        
        narr_sys = (first_event.get("narrate_prompt") or {}).get("rendered_system", "")
        if narr_sys:
            lines.append("### Narrate System Prompt\n")
            lines.append("```\n" + narr_sys + "\n```\n")
        
        extraction = first_event.get("extraction") or {}
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
    
    extraction = event.get("extraction") or {}
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
        lines.append(json.dumps(_extract_state_keys(state_snap), indent=2, default=str))
        lines.append("")
    
    lines.append("---")
    return "\n".join(lines)
```

### `_extract_state_keys()`

```python
def _extract_state_keys(state: dict[str, Any]) -> dict[str, Any]:
    """Extract the key state fields the judge needs to evaluate criteria.
    
    Returns a dict with: meta.momentum, scene.scene_pressure, pc.conditions,
    pc.momentum, inventory, quests, compendium.npcs (bios), scene.present_npcs,
    scene.recent_events, scene.pending_gm_beat.
    """
    result = {}
    
    meta = state.get("meta", {})
    result["momentum"] = meta.get("momentum", 0)
    
    pc = state.get("pc", {})
    result["pc_conditions"] = pc.get("conditions", [])
    
    scene = state.get("scene", {})
    result["scene_pressure"] = scene.get("scene_pressure", [])
    result["pending_gm_beat"] = scene.get("pending_gm_beat")
    result["present_npcs"] = scene.get("present_npcs", [])
    result["recent_events"] = scene.get("recent_events", [])
    
    result["inventory"] = state.get("inventory", [])
    result["quests"] = state.get("quests", [])
    
    comp = state.get("compendium", {}).get("npcs", {})
    # Only include name, title, bio per NPC (not last_seen, etc.)
    result["npc_bios"] = {
        nid: {"name": n.get("name", ""), "title": n.get("title", ""), "bio": n.get("bio", "")}
        for nid, n in comp.items()
    }
    
    return result
```

### Truncation Strategy

With full prompts and state, the trace will be much larger. The truncation strategy needs to change:

1. **Never truncate the static context section.** The system prompts, constants, and seed state are essential for the judge to understand the evaluation criteria.

2. **Truncate from the middle of the per-turn section.** If the trace exceeds `max_chars`, keep the static context + first N/2 turns + last N/2 turns, with a truncation marker in between. This preserves the beginning and end of the run.

3. **Within each turn, never truncate user prompts.** If a single turn's user prompts exceed the budget, that's a prompt bloat issue the judge should see. Truncate narration and extraction outputs only if absolutely necessary.

```python
def build_trace(events, *, max_chars, pack_style, seed_state):
    static = _render_static_context(seed_state, events[0] if events else None)
    
    if len(static) > max_chars * 0.3:
        # Static context alone is too large — something is wrong
        # Fall back to compact trace
        return _compact_trace(events, max_chars=max_chars)
    
    remaining = max_chars - len(static)
    turn_blocks = [_render_turn_context(ev) for ev in events]
    
    # Greedy: include as many full turns as fit
    turns_to_include = []
    chars_used = 0
    for block in turn_blocks:
        if chars_used + len(block) <= remaining:
            turns_to_include.append(block)
            chars_used += len(block)
        else:
            # Can't fit this turn fully — either truncate it or stop
            # For now, stop including turns (judge sees first N turns)
            break
    
    trace = static + "\n".join(turns_to_include)
    
    if len(trace) < len(static) + sum(len(b) for b in turn_blocks):
        # We truncated — add marker
        _TRUNC_MARKER = "\n\n[... trace truncated — not all turns included ...]\n\n"
        trace += _TRUNC_MARKER
    
    return trace
```

### Rubric Update

Update the rubric's instruction at the top to tell the judge how to read the new trace format:

```markdown
You are evaluating one run of an interactive narrative game.

The user message contains:

1. **Static Context** — World pack style, seed state key fields, engine constants,
   and the 5 system prompts (rendered once from turn 1). These define the rules
   and constraints the engine operates under.

2. **Per-Turn Context** — For each turn: the 5 user prompts (rendered for that turn),
   all engine outputs (rules, narration, extraction, applied/rejected deltas, actions),
   context telemetry, and the state snapshot after the turn.

**How to evaluate:**
- Compare each turn's user prompts against its outputs to verify context fidelity.
- Compare consecutive state snapshots to verify state drift and mechanical consistency.
- Use the system prompts as the ground truth for what the engine was instructed to do.
- Use the seed state and engine constants as the ground truth for thresholds and initial conditions.
```

---

## Estimated Trace Size

For a 10-turn eval with the eval-pack:

| Section | Approx chars |
|---|---|
| Static context (style + seed state + constants + 5 system prompts) | ~15,000 |
| Per turn (5 user prompts + rules + narration + 3 extraction outputs + applied + state snapshot) | ~8,000 |
| 10 turns | ~80,000 |
| **Total** | **~95,000** |

This fits within the 100,000 char budget. For longer runs (20+ turns), truncation will kick in.

---

## Testing

1. **Unit test:** `test_build_trace_full_context()` in `tests/test_eval_schema.py` — verify trace structure, verify static context appears once, verify per-turn sections are present, verify no truncation for small runs.

2. **Integration test:** Run `make eval` with the full-context trace and verify the judge produces valid output.

3. **Size test:** Verify trace size for 10-turn and 20-turn scenarios doesn't exceed `max_input_chars`.

---

## Migration

1. Rename current `build_trace()` to `_compact_trace()` for fallback.
2. Implement new `build_trace()` with full-context logic.
3. Add `pack_style` and `seed_state` parameters to `run_judge()`.
4. Load state from run directory in `run_judge()`.
5. Update rubric with new instructions.
6. Raise `JudgeConfig.max_input_chars` default to 100000.
7. Update `evals/config.yaml` if needed.
8. Add tests.
