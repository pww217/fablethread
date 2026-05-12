# Compaction Interval and Sanitization Fidelity

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Affected Files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/engine/compactor.py` | modify | Change compaction trigger from `config.compact_every` (default 6) to 12; change `_extract_turns_for_compact` to use `recent_events` instead of chronicle prose; add remove-delta logging in `_apply_sanitization` |
| `ccya/prompts/compact_system.j2` | modify | Update system instruction to synthesize from structured facts, not prose |
| `ccya/prompts/compact_user.j2` | modify | Remove narration turns block; pass `recent_events` and state snapshot |
| `ccya/engine/config.py` | modify | Change `compact_every` default from `6` to `12` (or update `config.yaml`) |
| `docs/REPOMAP/engine.md` | update | Document new compaction interval and input format |
| `docs/REPOMAP/prompts.md` | update | Note removal of narration prose block, addition of structured state sections |

## Overview
Change compaction from every 6 turns (reading full narration prose) to every 12 turns (reading `recent_events` + state snapshot), and add logging for removed pressures/conditions during sanitization.

## Phases

### Phase 1: Change Interval and Input

#### Step 1.1 — Change compaction interval

**File:** `ccya/engine/config.py:74` and `config.yaml:28`

**What:** The compaction interval is controlled by `config.compact_every`, which defaults to `0` (disabled) in `EngineConfig` and is set to `6` in `config.yaml`. Change the value in `config.yaml` from `6` to `12`. The trigger in `compactor.py:41` already reads `config.compact_every`, so no code change is needed there.

**Current (config.yaml:28):**
```yaml
  compact_every: 6
```

**New:**
```yaml
  compact_every: 12
```

**Why:** The compaction trigger in `compactor.py:41` is `if current_turn % config.compact_every != 0: return state, False`. Changing the config value changes the interval. The plan's original code snippet (`COMPACTION_INTERVAL = 12`) was wrong — there is no such constant; the interval is a config value.

**Validation:** Confirm compaction does not fire at turn 6 in a test run. Confirm it fires at turn 12.

***

#### Step 1.2 — Change compact_user.j2 input from narration history to recent_events + state snapshot

**File:** `ccya/prompts/compact_user.j2`

**What:** The current template (68 lines) has two sections: (1) `## TURNS TO COMPACT` iterating over `turns` (each with `turn`, `input`, `narrative`), and (2) `## ACTIVE CONTEXT` + `## MECHANICAL STATE` + `## RECENT EVENTS` with state sections. The plan wants to **remove** the turns section and **keep/modify** the state sections.

The call site in `compactor.py:184-193` already passes `turns`, `active_quests`, `pressures`, `inventory`, `compendium_npcs`, `all_quests`, `conditions`, and `recent_events`. The plan wants to stop passing `turns` and instead pass a simplified state snapshot.

**Text — new compact_user.j2 structure:**
```
## recent_events (last 12, most recent last)
{% for evt in recent_events %}
- [T{{ evt.turn }}] {{ evt.text if evt is mapping else evt }}
{% endfor %}

## current_state

### quests
{% for q in active_quests %}
- {{ q.get("id", "?") }}: {{ q.get("title", "?") }}
{% for obj in (q.get("objectives") or []) %}[{{ 'x' if obj.get("done") else ' ' }}] {{ obj.get("description", "?") }}{% endfor %}
{% endfor %}

### pressures
{% for p in pressures %}
- {{ p.get("id", "?") }} ({{ p.get("urgency", "").upper() }}): {{ p.get("text", p) }}
{% endfor %}

### conditions
{% for c in conditions %}
- {{ c.get("id", "?") }}: {{ c.get("label", "?") }} ({{ c.get("description", "") }})
{% endfor %}

### inventory
{% for item in inventory %}
- {{ item.get("id", "?") }}: {{ item.get("name", "?") }}{% if item.get("amount", 1) != 1 %} ×{{ item.get("amount") }}{% endif %}
{% endfor %}

### npcs
{% for npc_id, npc in compendium_npcs %}
- {{ npc_id }}: {{ npc.get("name", "?") }}{% if npc.get("title") %} ({{ npc.get("title") }}){% endif %}
{% endfor %}
```

**In `compactor.py:63-65`, change `_extract_turns_for_compact` call to return `recent_events` instead of turns. The `maybe_compact` function already has `recent_events` available from `state["scene"]["recent_events"]`. The `_build_compact_messages` call at line 74 already receives `state` and extracts `recent_events` at line 182. The `turns` parameter passed to the template at line 184 should be removed or replaced with `None`.**

**Corrected call site in `compactor.py:184`:**
```python
# Remove `turns=turns,` from the render call.
# The turns variable from _extract_turns_for_compact is no longer needed.
user_prompt = env.get_template("compact_user.j2").render(
    active_quests=active_quests,
    pressures=pressures,
    inventory=inventory,
    compendium_npcs=compendium_npcs,
    all_quests=all_quests,
    conditions=conditions,
    recent_events=recent_events,
)
```

**Also in `compactor.py:63-65`, the `_extract_turns_for_compact` call and its result can be removed or kept for backward compatibility (the function still exists and is tested).**

**Validation:** Render `compact_user.j2` with a test state fixture. Confirm no narration prose appears. Confirm all five state sections render correctly.

***

#### Step 1.3 — Update compact_system.j2 summarization instruction

**File:** `ccya/prompts/compact_system.j2`

**What:** The plan's original system prompt snippet was approximate. The actual file (155 lines) has three parts: PART 1 (prior-history bullets), PART 2 (state sanitization), PART 3 (recent_events compaction). The plan wants to update PART 1's instruction from summarizing prose turns to synthesizing from structured facts.

**Current (lines 1-9):**
```
You are a game historian and consistency editor for a TTRPG session.

Your output has two parts:
1. One bullet per compacted turn.
2. One JSON object with state sanitization actions (or {}).
```

**New:**
```
You are a game historian and consistency editor for a TTRPG session.

Your output has two parts:
1. One bullet per recent event (synthesized from structured facts, not turn prose).
2. One JSON object with state sanitization actions (or {}).
```

**The plan's new system prompt text (for PART 1) should replace the current PART 1 instructions (lines 11-39) with guidance to synthesize from the structured `recent_events` and `current_state` sections provided in the user message, rather than from turn-by-turn narration prose.**

**Validation:** Run compaction with the new prompt. Confirm output is coherent, does not reference specific turn numbers, and accurately reflects the provided state facts.

***

### Phase 2: Remove-Delta Logging

#### Step 2.1 — Log remove deltas during sanitization application

**File:** `ccya/engine/compactor.py` (NOT `turn.py`)

**What:** The plan's original code snippet referenced `CompactResult` and `compact_result.deltas`, which **do not exist**. The compaction output is `CompactorSanitizationResult` (defined in `ccya/models.py:367`). The sanitization is applied in `_apply_sanitization()` (compactor.py:247-327), which already has logging for each removal type. The plan wants to add explicit `compaction_remove` events.

The `_apply_sanitization` function already logs removals at lines 315-316 (pressure) and 326-327 (condition) using `_log.info`. The plan wants these logged as structured events that can be audited. The logging already exists — the plan's "sanitization fidelity score is 0.25" metric likely comes from the eval harness, not from event logging. The existing `_log.info` calls already serve this purpose.

**If explicit event logging is required**, add `append_event` calls in `_apply_sanitization`. However, `_apply_sanitization` currently has no access to `save_dir` or event logging. The caller `maybe_compact` (line 109) calls `_apply_sanitization(state, sanitization)`. The `save_dir` is available in `maybe_compact`. The logging should be added in `maybe_compact` after `_apply_sanitization` returns, or `_apply_sanitization` should be extended to accept a logging callback.

**Corrected approach — add logging in `maybe_compact` after sanitization:**
```python
# In maybe_compact, after _apply_sanitization(state, sanitization) at line 109:
if sanitization is not None:
    _apply_sanitization(state, sanitization)
    current_turn = int((state.get("meta") or {}).get("turn", 0) or 0)
    for item in sanitization.pressure_remove:
        _log.info(
            "compactor: compaction_remove pressure %r", item.id,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compaction_remove"},
        )
    for item in sanitization.condition_remove:
        _log.info(
            "compactor: compaction_remove condition %r", item.id,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compaction_remove"},
        )
```

**The plan's original code snippet was wrong because:**
1. `CompactResult` does not exist — the model is `CompactorSanitizationResult`
2. There is no `deltas` field on compaction output — sanitization fields are `pressure_remove`, `condition_remove`, etc.
3. The logging should be in `compactor.py`, not `turn.py` — compaction is entirely contained in compactor.py
4. The logging already exists as `_log.info` in `_apply_sanitization` — the plan just needs to add the `compaction_remove` kind tag for auditability

**Validation:** Run a compaction that removes a pressure. Confirm `compaction_remove` log entry appears. The sanitization logging already exists in `_apply_sanitization` at lines 315-316 and 326-327.

***

### Tests to write or update
- `tests/test_compactor.py`: trigger test — confirm compaction fires at turn 12, not turn 6 (update existing tests that use `compact_every=6`).
- `tests/test_compactor.py`: input test — render `compact_user.j2` with fixture, confirm no narration prose, confirm all 5 state sections present.
- `tests/test_compactor.py`: remove-delta log test — run compaction that removes a condition, confirm `compaction_remove` in log output.

### Risks
1. **`recent_events` ring may not contain 12 entries before first compaction** — at turn 12, the ring may have fewer entries if events were sparse. Mitigation: render however many exist; the template uses `{% for %}` which handles empty lists gracefully.
2. **Compaction at turn 12 means a longer gap without summarization for very long runs** — if the ring buffer is small (< 12 entries), some early-game facts may be lost between turns 0–12. Mitigation: the 2–3 full narrations retained in context cover this gap.
3. **`_extract_turns_for_compact` is still called but its result is no longer used** — the function and its tests should be updated or deprecated. The function is also referenced in `docs/REPOMAP/engine.md:133`.
