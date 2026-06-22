# Arc System — Discovery

Problems identified through eval analysis (outer-rim saves, noir/ww2/piracy runs), prompt inspection, and code review.

## 1. Arc Resolution Misuse — "Chapter Reset" Pattern

**Symptom:** Storyteller fires `arc_resolve` every 4–16 turns, but keeps the same `visible_goal` every time.

**Evidence (outer-rim, 34 turns, 4 arc_resolves):**

| Turn | visible_goal | drop_threads | new_threads |
|------|-------------|--------------|-------------|
| 4 | "Establish a reliable smuggling route..." | distress_signal_discovery | saloon_intelligence_gathering |
| 6 | Same | saloon_intelligence_gathering | guild_confrontation |
| 15 | Same | distress_signal_mystery, chemical_hazard_obstruction, immediate_combat_threat | guild_arrest_escalation |
| 31 | Same | docking_bay_chaos, security_response_escalation | sublevel_pursuit |

**Root cause:** Storyteller treats `arc_resolve` as a "new chapter/scene" marker, not an arc-ending event. The prompt (line 72 of `storytell_system.j2`) says:
> WRONG: `arc_resolve` with unchanged `visible_goal` (no-op). RIGHT: `arc_resolve` introduces a new goal or `chapter_end: true` keeps the current one.

But the storyteller does the opposite — unchanged goal + thread drops + new threads.

**Consequence:**
- `completed_threads` reset to `[]` on every arc_resolve (turn_state.py:268) — loses all completed thread history
- New arc entry created each time, stored in `resolved_arcs` (TTL-filtered, 3 turns)
- Successor arc has less context than parent arc
- Arc frequency warning fires (turn_state.py:226-233) but only logs, doesn't prevent
- Outer-rim: 4 arc_resolves in 34 turns (avg 8.5 turns), but all are no-op goals — effectively zero real arc progress

## 2. `arc_resolve` vs `chapter_end: true` — Indistinguishable Semantics

**Problem:** The prompt gives two mechanisms for "chapter ends but goal stays the same":
- `arc_resolve` with unchanged visible_goal (explicitly marked WRONG in prompt)
- `chapter_end: true` (explicitly marked RIGHT in prompt)

The storyteller consistently picks the WRONG one. The schema shows both fields in the same JSON object, making them feel like options rather than mutually exclusive signals.

**Schema (storytell_system.j2:14):**
```json
"arc_resolve": {"resolution": "...", "visible_goal": "...", "goal_context": "...", "drop_threads": ["..."], "new_threads": [...]},
"goal_update": "...",
"chapter_end": true,
```

All three are top-level keys in the same object. The storyteller interprets `arc_resolve` as "something happened, here's the result" and `chapter_end` as "but the arc continues." This is the opposite of the intended semantics.

## 3. `goal_context` — Dead Code for LLM, Required Noise

**Problem:** `goal_context` is:
- UI-only (sidebar tooltip, resolved arc context in `_state_left.html`)
- Never rendered in narrator or storyteller prompts
- Required by `ArcResolution` schema (Pydantic validation)
- Validated by `arc_resolution_validity` checker (non-empty string)
- Set by seed (initial), updated by storyteller `arc_resolve` (on chapter end), updated by sanitizer `goal_update` (if dict format)

**Consequence:** Storyteller must generate `goal_context` every time it emits `arc_resolve` — even though it has no mechanical purpose. This wastes LLM context/tokens and creates "emotional whiplash" — the storyteller generates a brand new context string with no connection to the previous arc's context (it never sees the old context).

**Design doc confirms:** `arc-system-design.md:147` — "goal_context in prompts is noise — it's a UI tooltip, not a narrative signal." `arc-resolution-redesign-design.md` — "goal_context is UI-only; not rendered in prompts."

## 4. Thread `progress` — Misleading Naming

**Problem:** The field is called `progress` but it's really a journal entry / log. The name implies "this needs to be updated every turn" — which is exactly what the storyteller does.

**Prompt (storytell_system.j2):**
> `thread_update`: Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation.

**Consequence:** Storyteller adds progress entries every turn, even when instructed "Default: emit nothing." The progress deduplication (70% text-similarity check) catches obvious rephrasings but not semantic ones.

**Current progress kinds:** `advancement`, `setback`, `shift` — these are vague and don't help the storyteller decide when to update. They're more like metadata tags than meaningful classifications.

**Better naming:** `notes`, `journal_entry`, or `log` — something that denotes "only update for important changes, not every turn."

## 5. Thread Urgency — Binary, Not Graduated

**Problem:** Urgency is `background | normal | urgent` — a 3-state system that's too coarse. The prompt says:
- `background` → "Faded but recoverable. Set `dormant: true`."
- `normal` → "Active and relevant but not pressing right now."
- `urgent` → "Immediate. Something happening now or about to escalate."

**Consequence:** The storyteller oscillates between `normal` and `urgent` with little nuance. There's no "cooling down" or "building up" — just snap transitions. This creates artificial urgency inflation where everything becomes `urgent` quickly.

**Outer-rim evidence:** 21 threads created, 19 still pending after 34 turns. Only 2 resolved (9.5%). Threads accumulate and never decay naturally.

## 6. Thread Add — No Conceptual Overlap Detection

**Problem:** The prompt says "scan all active AND latent threads for conceptual overlap" before emitting `thread_add`. But the storyteller consistently creates new threads for tensions that are already tracked under different IDs.

**Consequence:** Thread proliferation. Outer-rim has 21 threads created in 34 turns, with 19 still pending. The hard cap of 5 forces the storyteller to either drop threads (via `arc_resolve` with `drop_threads`) or create new ones, both of which are destructive.

## 7. Arc Model Schema — Confusing Structure

**Problem:** The `ArcResolution` schema mixes concerns:
- `resolution` — prose summary of what happened
- `visible_goal` — the new arc goal (required, even if unchanged)
- `goal_context` — UI-only context (required, even though LLM never sees it)
- `drop_threads` — thread cleanup (should use `thread_resolve`)
- `new_threads` — thread creation (should use `thread_add`)

**Consequence:** The storyteller sees one big JSON object with everything in it and treats it as "here's everything that happened this turn." This is the opposite of the intended design — each field should be independent.

**Schema (state.py:173-178):**
```python
class ArcResolution(BaseModel):
    resolution: str
    visible_goal: str
    goal_context: str
    drop_threads: list[str]
    new_threads: list[ArcThread]
```

## 8. Arc Thread — `type` Field Has No Coercion (Fixed in This Session)

**Problem:** `ArcThread.type` (`Literal["threat", "opportunity", "complication", "revelation"] | None`) had no coercion validator. Uppercase from LLM caused Pydantic validation error → entire `thread_add` rejected → full storytell retry. (Fixed in this session with `@field_validator`.)

**Related:** `GMBeat.type` has coercion (returns `None` for invalid → silently nullifies beat). `GMBeat.driver` has no coercion — invalid value `"environment"` fails validation → beat nullified.

## 9. Arc Resolution Frequency — Warning Only, No Enforcement

**Problem:** `turn_state.py:226-233` warns if arc_resolve fires < 5 turns since last resolution (target: 8-15), but doesn't prevent it.

**Consequence:** The storyteller fires arc_resolve whenever it wants. The warning is a log message only — no mechanical enforcement.

## 10. Completed Threads History — Lost on Every Arc Resolve

**Problem:** `completed_threads` is reset to `[]` on every arc_resolve (turn_state.py:268).

**Consequence:** Successor arc has zero context about what was previously resolved. The storyteller has to re-learn from `resolved_arcs` (TTL-filtered, 3 turns) and `completed_threads` (which is now empty). This means the storyteller has less context in the successor arc than in the parent arc.

## 11. Goal Update — Mid-Arc Pivot vs Arc Resolve Confusion

**Problem:** Two mechanisms for changing the arc goal:
- `goal_update` (mid-arc pivot) — direct string assignment to `state["arc"]["visible_goal"]`
- `arc_resolve.visible_goal` (chapter ending) — replaces entire arc

The storyteller conflates these. It uses `arc_resolve` with unchanged visible_goal (which should use `goal_update` or nothing), and it uses `goal_update` for no-ops (which the prompt explicitly forbids).

**Prompt (storytell_system.j2:76):**
> **CRITICAL: Compare your proposed `goal_update` against the current `visible_goal`. If they are identical or nearly identical (same meaning, different wording), do NOT emit `goal_update`.**

But the goals checker (outer-rim) shows goal_update firing on turns 4, 6, 15, 31 — all with the same goal. These are arc_resolves, not goal_updates.

## 12. Thread Progress Kinds — Vague Classifications

**Problem:** `progress_kind` is `advancement | setback | shift` — vague categories that don't help the storyteller decide when to update.

**Consequence:** Everything gets marked as `advancement` because the storyteller interprets "something happened" as "progress." The categories are too broad to be useful.

**Better approach:** Tie progress kinds to mechanical consequences (e.g., "thread moved closer to resolution," "thread introduced new obstacle," "thread context changed") rather than vague narrative categories.

## 13. Arc Thread Urgency Set Turn — Unused

**Problem:** `ArcThread.urgency_set_turn` (state.py:38) exists but is never read or written by the engine. It's dead state.

## 14. Sanitizer and Storyteller — Different `goal_update` Formats

**Problem:** 
- Storyteller: `goal_update: "string"` (direct string assignment)
- Sanitizer: `goal_update: {visible_goal: str, goal_context: str}` (dict format)

**Consequence:** Format mismatch. The `arc_goal_updates` checker compares storyteller's string `goal_update` against `state.visible_goal` — this works for storyteller but the sanitizer's dict format is a separate code path. Previously filed (roadmap/archive/goal-update-format-mismatch-storyteller-emits.md).

## 15. Thread Resolution — `promote_to_world_state` — Unused

**Problem:** `thread_resolve.promote_to_world_state` (bool) exists in the schema but is never read by the engine. It's dead state.

## Summary

The arc system has three fundamental problems:

1. **Schema confusion** — `arc_resolve` mixes arc-ending, thread cleanup, and thread creation into one JSON object. The storyteller interprets it as "everything that happened" rather than "the arc is ending."

2. **Naming confusion** — `progress` implies "update every turn." `urgency` is too coarse (3 states). `progress_kind` is too vague (3 categories).

3. **Dead/required noise** — `goal_context` is required by schema but UI-only. `urgency_set_turn` and `promote_to_world_state` are dead state.

The system needs a ground-up redesign, not patches.
