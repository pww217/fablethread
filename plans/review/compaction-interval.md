# Compaction Interval and Sanitization Fidelity

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective
The current compactor runs a full 6-turn play-by-play compaction every 6 turns, producing a verbose chronicle that duplicates information already captured by `recent_events` (a ring buffer of key facts) and the last 2–3 full narrations retained in context. The play-by-play adds token cost without proportional signal value. Separately, `pressure_remove` and `condition_remove` deltas are not logged during compaction, making it impossible to audit what was dropped — the sanitization fidelity score is 0.25 as a result. This plan changes the compaction interval to every 12 turns, switches the compaction target from full play-by-play to a `recent_events`-anchored summary, and adds explicit remove-delta logging.

## Non-goals
- Does not change `recent_events` ring buffer size or structure.
- Does not change the Pydantic `CompactResult` schema.
- Does not change how full narrations are retained in context.
- Does not change the compaction prompt's narrative synthesis logic — only what it summarizes and when it runs.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/engine/compactor.py` | modify | Change interval from 6 to 12; change input to `recent_events` summary + current state snapshot instead of full turn narrations |
| `ccya/prompts/compact_system.j2` | modify | Update to summarize from `recent_events` + state snapshot, not turn-by-turn prose |
| `ccya/prompts/compact_user.j2` | modify | Pass `recent_events` list and current state snapshot instead of narration history |
| `ccya/engine/turn.py` | modify | Log `pressure_remove` and `condition_remove` events during compaction delta application |
| `docs/REPOMAP/engine.md` | update | Document new compaction interval and input format |

## Firm decisions

1. Compaction interval: every 12 turns, not 6. Rationale: `recent_events` already provides a compact fact ring; full compaction is redundant at 6 turns when 2–3 full narrations are still in context.
2. Compaction input: `recent_events` list (last 12) + current state snapshot (quests, pressures, conditions, inventory summary, NPC compendium). Not full narration prose. The model summarizes facts it was given, not events it must re-interpret from prose.
3. Remove-delta logging: any `pressure_remove` or `condition_remove` applied during compaction must emit a `compaction_remove` event to `events.jsonl` with `entity_type`, `entity_id`, and `reason: "compaction"`.
4. The compaction prompt's output format does not change — only its input changes. This minimizes risk.
5. The `recent_events` ring buffer is the source of truth for what the compactor summarizes. If an event isn't in `recent_events`, it is not summarized.

## Implementation — Phase 1: Change Interval and Input

### Context files to load
- `ccya/engine/compactor.py`
- `ccya/prompts/compact_system.j2`
- `ccya/prompts/compact_user.j2`
- `docs/REPOMAP/engine.md`

### Overview
Change the compaction trigger in `compactor.py` from every 6 turns to every 12. Update `compact_user.j2` to receive `recent_events` and a state snapshot instead of narration history. Update `compact_system.j2` to instruct the model to synthesize from structured facts, not prose.

### Detailed steps

#### Step 1.1 — Change compaction interval in compactor.py

**File:** `ccya/engine/compactor.py`

**What:** Find the constant or condition that triggers compaction (likely `if turn_number % 6 == 0`) and change it to `% 12`.

**Why:** Halving the compaction frequency reduces token cost by ~50% on long runs while retaining state integrity via `recent_events`.

**Code Snippet:**
```python
# Find: if turn_number % 6 == 0:
# Replace with:
COMPACTION_INTERVAL = 12
# ...
if turn_number % COMPACTION_INTERVAL == 0:
```

**Validation:** Confirm compaction does not fire at turn 6 in a test run. Confirm it fires at turn 12.

***

#### Step 1.2 — Change compact_user.j2 input from narration history to recent_events + state snapshot

**File:** `ccya/prompts/compact_user.j2`

**What:** Replace the narration history block with two new blocks:
1. `## recent_events` — the last 12 `recent_events` entries rendered as a flat list.
2. `## current_state` — a compact snapshot: active quests (name + objectives status), active pressures (id + urgency), active conditions (id + duration), inventory summary (item names + quantities), NPC compendium entries (name + one-line bio).

Remove the narration turn-by-turn prose block entirely.

**Why:** The model summarizes better from structured facts than from prose it must re-parse. The `recent_events` ring already contains the key narrative beats in compact form. Removing prose narration from the compaction input cuts context length significantly.

**Text — new compact_user.j2 structure:**
```
## recent_events (last 12, most recent last)
{% for evt in recent_events %}
- [T{{ evt.turn }}] {{ evt.summary }}
{% endfor %}

## current_state

### quests
{% for q in active_quests %}
- {{ q.name }}: {% for obj in q.objectives %}[{{ 'x' if obj.done else ' ' }}] {{ obj.text }}{% endfor %}
{% endfor %}

### pressures
{% for p in scene_pressure %}
- {{ p.id }} ({{ p.urgency }}): {{ p.description }}
{% endfor %}

### conditions
{% for c in active_conditions %}
- {{ c.id }}: {{ c.description }} ({{ c.turns_remaining }} turns remaining)
{% endfor %}

### inventory
{% for item in inventory %}
- {{ item.name }}: {{ item.quantity if item.quantity is not none else 'unique' }}
{% endfor %}

### npcs
{% for npc in compendium %}
- {{ npc.name }}: {{ npc.bio_summary }}
{% endfor %}
```

**Validation:** Render `compact_user.j2` with a test state fixture. Confirm no narration prose appears. Confirm all five state sections render correctly.

***

#### Step 1.3 — Update compact_system.j2 summarization instruction

**File:** `ccya/prompts/compact_system.j2`

**What:** Replace the instruction to "summarize the events of the last N turns" with an instruction to "synthesize the current state of the story from the structured facts provided."

**Current (approximate):**
```
You are a story archivist. Summarize the last 6 turns of gameplay into a compact chronicle that preserves key events, character arcs, and world changes.
```

**New:**
```
You are a story archivist. You receive structured facts about the current story state: recent events, active quests, pressures, conditions, inventory, and NPC records. Synthesize these into a compact chronicle paragraph (150–250 words) that captures: (1) what the player has accomplished, (2) what threats and complications remain active, (3) the current emotional and narrative stakes. Do not invent facts not present in the structured input. Do not describe turn-by-turn actions — write a coherent narrative summary of the current situation.
```

**Validation:** Run compaction with the new prompt. Confirm output is 150–250 words, does not reference specific turn numbers, and accurately reflects the provided state facts.

***

## Implementation — Phase 2: Remove-Delta Logging

### Context files to load
- `ccya/engine/turn.py` or `ccya/engine/compactor.py` (wherever compaction deltas are applied)

### Overview
When compaction applies `pressure_remove` or `condition_remove` deltas, emit a `compaction_remove` event to `events.jsonl`.

### Detailed steps

#### Step 2.1 — Log remove deltas during compaction application

**File:** `ccya/engine/turn.py` or `ccya/engine/compactor.py`

**What:** In the section that applies compaction deltas to state, after each `pressure_remove` or `condition_remove` delta is successfully applied, emit a log event.

**Code Snippet:**
```python
# In the delta application loop for compaction results:
for delta in compact_result.deltas:
    if delta.op in ("pressure_remove", "condition_remove"):
        log_event({
            "kind": "compaction_remove",
            "entity_type": delta.op.replace("_remove", ""),
            "entity_id": delta.id,
            "reason": "compaction",
            "turn": current_turn,
        })
    apply_delta(state, delta)  # existing apply function
```

**Validation:** Run a compaction that removes a pressure. Confirm `compaction_remove` event appears in `events.jsonl`. Confirm `sanitization_fidelity` in the eval report is > 0.25.

***

### Tests to write or update
- `tests/test_compactor.py`: trigger test — confirm compaction fires at turn 12, not turn 6.
- `tests/test_compactor.py`: input test — render `compact_user.j2` with fixture, confirm no narration prose, confirm all 5 state sections present.
- `tests/test_compactor.py`: remove-delta log test — run compaction that removes a condition, confirm `compaction_remove` in events.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: update `compactor.py` entry — interval now 12, input format is `recent_events` + state snapshot.
- `docs/REPOMAP/prompts.md`: update `compact_user.j2` entry — note removal of narration prose block, addition of structured state sections.

### Risks
1. **`recent_events` ring may not contain 12 entries before first compaction** — at turn 12, the ring may have fewer entries if events were sparse. Mitigation: render however many exist; the template uses `{% for %}` which handles empty lists gracefully.
2. **Compaction at turn 12 means a longer gap without summarization for very long runs** — if the ring buffer is small (< 12 entries), some early-game facts may be lost between turns 0–12. Mitigation: the 2–3 full narrations retained in context cover this gap.
3. **`compact_result.deltas` field name** — executor must verify the actual field name for compaction output deltas in `CompactResult`. Do not invent field names.

## Ambiguities requiring resolution before execution
1. Does `compact_user.j2` currently receive narration history as a variable called `narration_history` or `turns`? Executor must read the template and the call site in `compactor.py` to confirm before replacing the block.
2. Does `CompactResult` have a `deltas` field, or does it apply removes directly? Executor must confirm the compaction output schema before adding the logging hook.

## TODO.md update
Add under **P2 — Stability / Fidelity**:
```
- [ ] [Compaction Interval and Sanitization Fidelity](plans/compaction-interval.md)
```
