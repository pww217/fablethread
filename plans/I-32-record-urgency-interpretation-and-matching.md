# Plan: I-32 — Record Prompt Urgency Interpretation & Beat Candidates Fix

## Design Reference

- Design: `roadmap/improvements/I-32-record-urgency-interpretation-and-matching.md`
- I-32 identifies two issues: (1) Record prompt missing urgency interpretation guidance, (2) beat_candidates event capture ordering bug

## Problem Statement

After commit a1d05285, Record's prompt was stripped of urgency escalation guidance. Result: all 3 Phase 2 eval runs stayed in SETUP for 15 turns — no phase transitions occurred because no urgent threads were created.

Additionally, `beat_candidates` is empty on every turn in events because the event dict is built at `turn.py:619` before the async world step writes candidates at `turn.py:792`.

## Firm decisions (from I-32)

1. Don't fully revert a1d05285 — premature closure rules were legitimately removed
2. Rewrite as interpretation rules, not corrective rules
3. Record CAN promote urgency (schema allows bidirectional control)
4. Use concrete event-mappable summaries (not keywords) — no template change needed
5. `last_updated_turn` already rendered in `_thread_list.j2:9` — done
6. Beat candidates fix: capture from `extraction.world.output` after async world step

## Scope

- **Phase 1:** Add urgency interpretation rules + CLIMAX awareness + matching instruction to `record_system.j2`
- **Phase 2:** Fix beat_candidates event capture ordering in `turn.py` + re-run eval

## Status

`completed`

---

## Phase 1: Urgency interpretation rules in record_system.j2

### Context files to load

- `ccya/prompts/record_system.j2` — current prompt (~86 lines)
- `ccya/prompts/sections/_thread_list.j2` — thread rendering (already has `last_updated_turn`)
- `roadmap/improvements/I-32-record-urgency-interpretation-and-matching.md:34-69` — exact rules to add

### What changes

Add three new sections to `record_system.j2`:

1. **Thread urgency interpretation rules** — translate narrator portrayal → urgency labels
2. **CLIMAX phase awareness** — at least one thread MUST be urgent in CLIMAX
3. **How to match** — instruction for connecting narration events to thread summaries

### Where to add

After the existing "Threads" section (after line 56), before "Arc resolution" (line 57).

### Exact additions

```markdown
## Thread urgency interpretation

The Narrator controls thread portrayal. Your job is to translate that portrayal into urgency labels.

**Escalate to urgent when:**
- The narrator describes a threat as immediate/imminent (armed, approaching, time-sensitive)
- A background thread's NPC appears or the thread resurfaces in narration
- Scene phase is CLIMAX — at least one thread MUST be urgent

**Demote to background when:**
- The narrator describes a thread as faded/distant/past
- An NPC associated with the thread departed
- A thread has been dormant for 6+ turns

**Set dormant: true when:**
- The associated NPC departed
- The thread is fading and unlikely to resurface soon
- You're resolving the thread (thread_resolve)

**Set dormant: false when:**
- The associated NPC is present again
- The thread resurfaces in narration

## CLIMAX phase

If `scene_phase` is CLIMAX:
- At least one thread MUST be urgent. If none are, set the most relevant to urgent.
- Prefer `thread_resolve` for the main pressure thread.

## Matching threads to narration

For each event in the narration, find the matching thread by comparing the event to the thread summary. If the event involves the same people, places, or actions, it relates to that thread.

Thread summaries describe concrete events, not implications. Match by:
- **People:** character names, roles (guard, merchant, captain)
- **Places:** locations, districts, landmarks
- **Actions:** pursuits, discoveries, confrontations, damages

If a thread's `last_updated_turn` is ≥ 6 turns ago and urgency is still `normal`, consider escalating to `urgent` — it may have been ignored by the player.
```

### Why

- Gives Record concrete criteria for urgency escalation (was stripped in a1d05285)
- CLIMAX awareness ensures the pacing engine's trigger (`thread_urgency_count > 0`) fires during climax
- Matching instruction bridges the gap between narration prose and thread context
- `last_updated_turn` is already rendered in `_thread_list.j2` — Record just needs to know how to use it

### Validation

- Prompt renders without Jinja errors
- Phase 2 eval run shows phase transitions (SETUP → RISING → CLIMAX)
- `thread_urgency_decay` checker passes (urgency changes tracked correctly)

---

## Phase 2: Beat candidates capture fix + eval re-run

### Context files to load

- `ccya/engine/turn.py:619` — event dict built here, reads `beat_candidates` too early
- `ccya/engine/turn.py:780-792` — async world step, writes candidates to state
- `ccya/engine/turn.py:644` — `beat_candidates` field in event dict

### What changes

Capture `beat_candidates` from `extraction.world.output` instead of `state.meta.beat_candidates`.

### Where to change

`turn.py` — move `beat_candidates = state.meta.beat_candidates or []` from line 619 to after the async world step completes (~line 792+).

### Before (current):

```python
# Line 619 — BEFORE async world step
beat_candidates = state.meta.beat_candidates or []
# ...
event = {
    # ...
    "beat_candidates": beat_candidates,  # Always empty on even turns
    # ...
}
```

### After:

Move the entire event dict construction (turn.py line 622-659) to after the async world step completes (~line 792+).

```python
# After async world step (~line 792+)
beat_candidates = (extraction_event.get("world") or {}).get("output") or []

_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
event = {
    "ts": _ts,
    "trace_id": trace_id,
    "turn": state.meta.turn,
    "type": "turn",
    "input": user_input,
    "applied": applied,
    "rejected": rejected,
    "thread_dedup_rejections": thread_dedup_rejections,
    "actions": actions,
    "ruling": ruling_event,
    "pacing_context": {
        "directive": pc.directive if pc else "",
        "outcome_hint": pc.outcome_hint if pc else None,
        "summary": pc.summary if pc else "",
        "scene_phase": state.scene.scene_phase,
        "climax_turn_count": state.scene.climax_turn_count,
        "breather_turn_count": state.scene.breather_turn_count,
        "convergence_score": pc.convergence_score if pc else 0,
        "convergence_components": pc.convergence_components if pc else {},
        "convergence_threads": pc.convergence_threads if pc else [],
    },
    "beat_candidates": beat_candidates,  # Now captures world step output
    "npc_updates": npc_updates,
    "post_turn_pending_beat": state.meta.pending_gm_beat,
    "allowed_beat_types": derive_allowed_beat_types(
        state.scene.scene_phase,
        directive=pc.directive if pc else "",
    ),
    "post_turn_location_id": state.location.id,
    "scene_phase": state.scene.scene_phase,
    "curtain_call": state.scene.curtain_call,
    "narrate": {**narr_metrics, "prose": narrative},
    "extract": ext_metrics,
    "extraction": extraction_event,
    "changes": changes,
    "reconcile_warnings": reconcile_warnings,
    # ... rest of event dict (prompt logging continues)
}
```

### Why

`beat_candidates` is populated by the async world step (`_run_world_step()` → `_log.debug("turn.world_complete"...)` at line 791). The event dict is built at line 619 — before the async step completes. On even turns, `state.meta.beat_candidates` is stale/empty from the previous turn. Capturing from `extraction.world.output` after the async step completes gives the correct data.

### Validation

- `beat_candidates` field in events contains valid candidates on even turns
- No regression on odd turns (candidates captured from previous turn's world step)
- `make check` passes

---

## Documentation updates

- `docs/architecture/` — update record prompt contract (urgency interpretation section)
- `docs/repomap.md` — update record_system.j2 description to mention urgency interpretation rules
- `AGENTS.md` — no changes needed (no build/lint/command changes)
