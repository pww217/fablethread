---
title: "Consolidate duplicate condition coercion and shared utility functions"
status: idea
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

| Function | Locations |
|----------|-----------|
| `_coerce_condition_str()` | `ccya/models/state.py:337`, `ccya/models/extraction.py:55` |
| `_strip_non_ascii()` | `ccya/state/npcs.py:38`, `ccya/engine/npc_roster.py:189`, `ccya/state/delta_builder.py:27` |
| `_is_named()` | `ccya/state/npcs.py:16`, `ccya/engine/npc_roster.py:75` |

### Dead code

- `_coerce_condition_str()` in `ccya/models/state.py:337` is never called — dead code.
- `_expire_conditions()` in `ccya/engine/turn_state.py:429-483` handles both `Condition` model objects and raw dict format. The dict branch is dead code since state is always typed `list[Condition]`.

## Plan

1. Create `ccya/engine/utils.py` with shared `is_named()`, `strip_non_ascii()`, `coerce_condition_str()`.
2. Remove `_coerce_condition_str()` from `ccya/models/state.py` (dead code).
3. Import `coerce_condition_str` from `engine/utils` in `ccya/models/extraction.py`.
4. Import `is_named`, `strip_non_ascii` from `engine/utils` in `ccya/state/npcs.py`.
5. Import `is_named`, `strip_non_ascii` from `engine/utils` in `ccya/engine/npc_roster.py`.
6. Import `strip_non_ascii` from `engine/utils` in `ccya/state/delta_builder.py`.
7. Remove dict-format handling from `_expire_conditions()` in `ccya/engine/turn_state.py`.

## Risk

Low. All changes are refactoring — no behavioral changes. Functions are pure with identical implementations. Dict branch removal is safe (typed state guarantees `list[Condition]`).

## Not Simplified

- Condition reason field requirement (prevents silent changes)
- TTL system (default 10 turns, permanent flag)
- Cap of 5 active conditions (game balance)
- Duration guidance bands (useful LLM guidance)

This is cleanup-only. The conditions mechanics are already lean.
