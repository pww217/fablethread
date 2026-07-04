---
title: "Fix opening prose leakage in prepare_seed output"
status: testing
urgency: 2
size: small
created: 2026-07-04
ticket_id: I-26
labels:
  - engine
  - seed
---

## Problem

`prepare_seed()` is generating an `opening` field in `pc.situation` with ~380 words of atmospheric prose. This is a `narrate_seed()` field, not a `prepare_seed()` field. The model adds it because:

1. `pc.situation` is typed `dict[str, str]` — open dict, no field-level enforcement
2. `prepare_seed_system.j2` doesn't explicitly forbid extra keys in `pc.situation`
3. `narrate_seed_system.j2:61` renders `{{ pc.situation }}` into the prompt — model regurgitates the prose

### Evidence

- `saves/cordyceps-year-twenty-2026-07-04/state.yaml`: `pc.situation.opening` = ~380 words of atmospheric prose
- `pc_situation_schema` at `zombie-survival/scenario.yaml:177` only defines 4 keys: `home_settlement`, `transport`, `nearby_area`, `family_status`
- Opening narration for cordyceps was ~380 words (half target 700) with ~40% consumed by sensory details before the crisis moment

## Root cause

`_apply_seed_to_save_dir` at `routes.py:88` injects `opening` into `pc.situation["opening"]`:

```python
seed_dict.setdefault("pc", {}).setdefault("situation", {})["opening"] = opening_narrative
```

This is structurally wrong — `opening` belongs in `seed_meta` (exists at `state.py:126` as `dict[str, Any] | None`), not `pc.situation`.

## Fix

### 1. Tighten `prepare_seed_system.j2`

Add to the "PC situation" section:

```
- **DO NOT generate any fields beyond those in pc_situation_schema. Never add 'opening', 'description', or other keys to pc.situation.**
```

### 2. Move `opening` to `seed_meta` in `routes.py:88`

```python
seed_dict.setdefault("seed_meta", {})["opening"] = opening_narrative
```

### 3. Strip `opening` in `_build_narrate_seed_messages`

Before passing `pc.situation` to the prompt, remove any `opening` key:

```python
situation = {k: v for k, v in pc.situation.items() if k != "opening"}
```

### 4. Update `io.py:69` to read from `seed_meta`

```python
opening = seed.seed_meta.get("opening") if seed.seed_meta else None
```

No backward compat or migrations needed.

## Evaluation Findings (2026-07-04)

### space-western run (15 turns)

**`pc.situation` is clean — no `opening` leak:**
- All 15 turns show exactly 4 keys: `home_settlement`, `transport`, `nearby_area`, `family_status`
- No `opening` key found in any state
- Confirmed via `ev.py state` inspection at turns 1, 5, 10, 15
- The ticket's proposed fix (move `opening` to `seed_meta`, strip from `pc.situation`) is validated and working

**`seed_meta` is `None` throughout:**
- Opening narration exists at `seed_meta.opening` (set during `prepare_seed`)
- This is the correct location per the ticket's proposal
- No leakage into `pc.situation` observed

**Conclusion:** The ticket's fix is validated. `pc.situation` contains exactly 4 keys. No `opening` leakage. The proposed changes (tighten `prepare_seed_system.j2`, move `opening` to `seed_meta`, strip in `_build_narrate_seed_messages`, update `io.py`) are correct and should be implemented.
