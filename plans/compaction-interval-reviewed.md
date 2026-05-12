Now let me check the models and config for the compaction-related types and settings.
Let me check for `CompactResult` and also look at the existing compactor tests.
Now I have all the information needed. Let me compile the review.

# Plan Review: Compaction Interval and Sanitization Fidelity

## Summary
The plan has significant accuracy issues: template variable/field names don't match the actual codebase, several referenced symbols don't exist, and the compaction interval change is mischaracterized. The plan acknowledges some ambiguities but doesn't resolve them. **5 warnings, 0 blockers** — the plan can be fixed without changing intent.

## Findings

### Phase 1: Change Interval and Input

#### Step 1.1 — Change compaction interval in compactor.py

**Finding:** The plan suggests adding `COMPACTION_INTERVAL = 12` and changing `if turn_number % COMPACTION_INTERVAL == 0:`. The actual code at `compactor.py:41` uses `if current_turn % config.compact_every != 0:`. The compaction interval is controlled by `EngineConfig.compact_every` (default `0` = disabled), not a hardcoded constant. The plan should instruct changing the config value, not adding a module-level constant.
**Category:** WARNING
**Plan says:** `COMPACTION_INTERVAL = 12` / `if turn_number % COMPACTION_INTERVAL == 0:`
**Code shows:** `if current_turn % config.compact_every != 0:` at `compactor.py:41`. `config.compact_every` is an `EngineConfig` field (default `0`, from `config.yaml` `game.compact_every`).

#### Step 1.2 — Change compact_user.j2 input from narration history to recent_events + state snapshot

**Finding (variable name mismatch):** The plan template uses `scene_pressure`, `active_conditions`, and `compendium` as variable names. The actual compactor.py passes `pressures`, `conditions`, and `compendium_npcs` (lines 176, 181, 179/189). The template would fail to render these sections.
**Category:** WARNING
**Plan says:** `{% for p in scene_pressure %}`, `{% for c in active_conditions %}`, `{% for npc in compendium %}`
**Code shows:** `pressures=pressures,` (line 187), `conditions=conditions,` (line 191), `compendium_npcs=compendium_npcs,` (line 189)

**Finding (field name mismatch — event.summary):** The plan template uses `evt.summary` for recent events. The actual `recent_events` entries have `id`, `text`, and `turn` fields (compactor.py lines 114-120, compact_user.j2 line 64). The plan should use `evt.text`.
**Category:** WARNING
**Plan says:** `{{ evt.summary }}`
**Code shows:** `event.text` in compact_user.j2:64 and compactor.py:117

**Finding (field name mismatch — obj.text):** The plan template uses `obj.text` for quest objectives. The actual objectives have `description` and `done` fields (compact_user.j2:16). The plan should use `obj.description`.
**Category:** WARNING
**Plan says:** `{{ obj.text }}`
**Code shows:** `obj.get("description", "?")` in compact_user.j2:16

**Finding (field name mismatch — p.description):** The plan template uses `p.description` for pressures. The actual pressures have `id`, `text`, `urgency`, `turn_added`, `max_turns` fields (compactor.py:176, compact_user.j2:24). The plan should use `p.text`.
**Category:** WARNING
**Plan says:** `{{ p.description }}`
**Code shows:** `p.get("text", p)` in compact_user.j2:24

**Finding (field name mismatch — c.turns_remaining):** The plan template uses `c.turns_remaining` for conditions. The actual conditions have `id`, `label`, `description`, `added_turn` fields (compactor.py:181, compact_user.j2:55). There is no `turns_remaining` field. The plan would need to compute `current_turn - c.added_turn` or use `c.added_turn`.
**Category:** WARNING
**Plan says:** `{{ c.turns_remaining }} turns remaining`
**Code shows:** `c.get("id")`, `c.get("label")`, `c.get("description")` in compact_user.j2:55-56. No `turns_remaining` field exists.

**Finding (field name mismatch — item.quantity):** The plan template uses `item.quantity` for inventory. The actual inventory items have `id`, `name`, `amount`, `notes` fields (compactor.py:177, compact_user.j2:33). The plan should use `item.amount`.
**Category:** WARNING
**Plan says:** `{{ item.quantity if item.quantity is not none else 'unique' }}`
**Code shows:** `item.get("amount")` in compact_user.j2:33

**Finding (field name mismatch — npc.bio_summary):** The plan template uses `npc.bio_summary` for NPC compendium. The actual compendium NPCs have `name`, `title`, `bio`, `aliases` fields (compactor.py:178-179, compact_user.j2:40-41). The plan should use `npc.bio`.
**Category:** WARNING
**Plan says:** `{{ npc.bio_summary }}`
**Code shows:** `npc.get("name")`, `npc.get("title")`, `npc.get("bio")`, `npc.get("aliases")` in compact_user.j2:41

#### Step 1.3 — Update compact_system.j2 summarization instruction

**Finding:** The plan's proposed system prompt text is reasonable and fits the existing template structure. The current `compact_system.j2` has three parts (prior-history bullets, state sanitization, recent_events compaction) and the plan's new instruction replaces the PART 1 guidance. The plan says "only its input changes" for the output format, which is consistent.
**Category:** SUGGESTION
**Plan says:** Replace system prompt instruction
**Code shows:** `compact_system.j2:1-155` has three parts. The plan's new instruction for PART 1 is compatible. The plan should clarify that PART 2 (sanitization) and PART 3 (recent_events) instructions remain unchanged.

### Phase 2: Remove-Delta Logging

#### Step 2.1 — Log remove deltas during compaction application

**Finding (symbol doesn't exist — CompactResult):** The plan references `CompactResult` in non-goals and Phase 2.1. This model does not exist. The actual model is `CompactorSanitizationResult` (models.py:367). The plan has an ambiguity section that acknowledges this question.
**Category:** WARNING
**Plan says:** `CompactResult` (non-goals), `compact_result.deltas` (Phase 2.1)
**Code shows:** `CompactorSanitizationResult` at `ccya/models.py:367`. No `CompactResult` exists.

**Finding (symbol doesn't exist — deltas field):** The plan references `compact_result.deltas` (or `san.deltas`). `CompactorSanitizationResult` has no `deltas` field. It has separate lists: `npc_merge`, `inventory_remove`, `quest_close`, `pressure_remove`, `condition_remove`, `recent_events_compact`. The plan has an ambiguity section that acknowledges this question.
**Category:** WARNING
**Plan says:** `for delta in compact_result.deltas:` / `delta.op in ("pressure_remove", "condition_remove")` / `delta.id`
**Code shows:** `CompactorSanitizationResult` has `pressure_remove: list[CompactorSanitizationAction]` and `condition_remove: list[CompactorSanitizationAction]`. No `deltas` or `op` field exists. The logging should iterate over `san.pressure_remove` and `san.condition_remove` separately.

**Finding (symbol doesn't exist — log_event):** The plan references `log_event()` which doesn't exist. The correct function is `append_event()` from `ccya.state.chronicle` (chronicle.py:15), which is already imported in `ccya/engine/turn.py:47`. The logging should be added in `_apply_sanitization()` in compactor.py, which already has logging via `_log.info()`. The plan should use `_log.info()` or `append_event()` instead.
**Category:** WARNING
**Plan says:** `log_event({...})`
**Code shows:** No `log_event` function exists. `append_event()` exists at `ccya/state/chronicle.py:15`. `_apply_sanitization()` already uses `_log.info()` for logging (compactor.py:278, 295, 305, 316, 327).

**Finding (symbol doesn't exist — sanitization_fidelity):** The plan references `sanitization_fidelity` in the validation step. This metric does not exist anywhere in the codebase. The plan would need to define this metric or use an existing one.
**Category:** WARNING
**Plan says:** `Confirm sanitization_fidelity in the eval report is > 0.25`
**Code shows:** No `sanitization_fidelity` found anywhere in the codebase.

## Unchanged
- **File existence:** All 5 files referenced in the plan exist: `ccya/engine/compactor.py`, `ccya/prompts/compact_system.j2`, `ccya/prompts/compact_user.j2`, `ccya/engine/turn.py`, `docs/REPOMAP/engine.md`.
- **`_apply_sanitization` exists:** The function exists at `compactor.py:247` and already handles `pressure_remove` (line 307-316) and `condition_remove` (line 319-327) with logging. The logging hook from Phase 2 should be added here.
- **`append_event` exists and is importable:** Already imported in `turn.py:47`. The compactor.py would need to import it from `ccya.state.chronicle`.
- **`recent_events` already passed to template:** compactor.py:182-192 already extracts and passes `recent_events` to the template. The plan's intent to use `recent_events` is already partially supported.
- **`compactor.py:63` — `_extract_turns_for_compact` already extracts turns from chronicle.md:** The plan's intent to switch from narration history to `recent_events` + state snapshot would require changing this function or adding a new one. The plan doesn't explicitly address this.
