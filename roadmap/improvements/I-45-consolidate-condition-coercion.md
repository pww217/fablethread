---
title: "Consolidate duplicate condition coercion and shared utility functions"
status: done
urgency: 3
size: small
created: 2025-07-26
ticket_id: I-45
labels: [tech-debt]
design:
plan:
pr:
  url:
  branch:
---

## Description

The conditions system has three duplicated utility functions scattered across multiple files. All are pure functions with identical implementations. This adds maintenance burden and creates risk of divergence. Additionally, `_expire_conditions()` carries backward-compat dict handling that is dead code since `WorldState.pc.conditions` is typed as `list[Condition]`.

## Findings

### Duplicate functions (3 instances)

| Function | Locations | Status |
|----------|-----------|--------|
| `_coerce_condition_str()` | `ccya/models/state.py:344` (dead), `ccya/models/extraction.py:55` | Byte-identical bodies |
| `_strip_non_ascii()` | `ccya/state/npcs.py:38`, `ccya/engine/npc_roster.py:189` (inline regex) | Byte-identical bodies |
| `_strip_non_ascii()` | `ccya/state/delta_builder.py:27` | Same output, precompiled `_NAME_RE` regex (more efficient) |
| `_is_named()` | `ccya/state/npcs.py:16`, `ccya/engine/npc_roster.py:75` | Byte-identical bodies |

### Dead code

- `_coerce_condition_str()` in `ccya/models/state.py:344` is never called — dead code (confirmed via grep, no call sites).
- `_expire_conditions()` in `ccya/engine/turn_state.py:429-483` handles both `Condition` model objects and raw dict format. The dict branch is dead code since state is always typed `list[Condition]`.
- **Bonus finding:** The entire `updated_conds: list[Any]` accumulator in `_expire_conditions()` (lines 437-474) is built but never used. Only `expired_ids` flows to `state.expire_conditions(expired_ids)`. The `model_copy` / `model_dump` reconstruction work is wasted on every turn. Side effects (logging, expiring via the typed mutator) are the only live parts.

## Plan

1. Create `ccya/engine/utils.py` with shared `is_named()`, `strip_non_ascii()` (using precompiled regex), `coerce_condition_str()`.
2. Remove `_coerce_condition_str()` from `ccya/models/state.py` (dead code).
3. Import `coerce_condition_str` from `engine/utils` in `ccya/models/extraction.py`.
4. Import `is_named`, `strip_non_ascii` from `engine/utils` in `ccya/state/npcs.py`.
5. Import `is_named`, `strip_non_ascii` from `engine/utils` in `ccya/engine/npc_roster.py`.
6. Import `strip_non_ascii` from `engine/utils` in `ccya/state/delta_builder.py`; remove the now-unused `_NAME_RE` constant.
7. Simplify `_expire_conditions()` in `ccya/engine/turn_state.py`: remove the unused `updated_conds` accumulator and the dead dict-format branches. Function reduces to: extract `cond_id`/`tr`, skip `permanent`, decrement ints and record expired ids, warn on unknown types. Use `c.model_copy(update=...)` for any model mutations that are actually needed (likely none after simplification).

## Risk

Low. All changes are refactoring — no behavioral changes. Functions are pure with byte-identical or equivalent implementations. Dict branch removal is safe (typed state guarantees `list[Condition]`). Removing the unused accumulator changes nothing observable — the value was computed and discarded every turn.

## Not Simplified

- Condition reason field requirement (prevents silent changes)
- TTL system (default 10 turns, permanent flag)
- Cap of 5 active conditions (game balance)
- Duration guidance bands (useful LLM guidance)

This is cleanup-only. The conditions mechanics are already lean.
