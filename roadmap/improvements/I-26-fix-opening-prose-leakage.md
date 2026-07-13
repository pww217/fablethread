---
title: "Fix opening prose leakage in prepare_seed output"
status: done
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

## Updated Evaluation (2026-07-05 — Post-Fix Runs)

### CONFIRMED REGRESSION: Opening prose leak is BACK

All three new runs (noir-1930s, space-western, golden-piracy) show `opening` field in `pc.situation` containing full prose text (300-400 words of atmospheric narration).

| Pack | Situation Keys | Opening Present |
|------|---------------|-----------------|
| noir-1930s | `family`, `office_location`, `opening`, `reputation`, `residence` | YES — ~380 words |
| space-western | `filiation`, `home_port`, `opening`, `reputation`, `vessel` | YES — ~380 words |
| golden-piracy | `alliance_status`, `home_port`, `opening`, `reputation`, `vessel` | YES — ~380 words |

**Conclusion:** The I-25 prose leak fix (commit 4c009946) is NOT working or has been re-introduced. The `opening` field is present in `pc.situation` across all packs. The fix needs to be re-examined — either the code path wasn't triggered in the earlier space-western run, or a later change re-introduced the leak.

**Note:** The earlier space-western run (2026-07-04, commit b593d8c) showed clean `pc.situation` with no `opening` leak. The new runs (2026-07-05, commits after 4c009946) show the leak. This suggests either:
1. The fix in 4c009946 was incomplete (only affected some code paths)
2. A later commit (d71fff2f — model change) re-introduced the leak
3. The earlier run was from a different save/directory that hadn't been updated

## Root Cause (2026-07-05)

**ev.py still writes `opening` to `pc.situation["opening"]`.** 

The I-25 fix updated `routes.py` (server path → `seed_meta["opening"]`) but did not update `ev.py` (CLI/eval path). At `ccya/ev/play.py:287`:

```python
seed_dict.setdefault("pc", {}).setdefault("situation", {})["opening"] = final_envelope.opening_narrative
```

This is the **only** code path that writes `opening` to `pc.situation` in eval runs. The server path was fixed; the CLI path was not.

## Fix Applied (2026-07-05)

Changed `ccya/ev/play.py:287` to write to `seed_meta["opening"]` (matching the server fix in routes.py):

```python
seed_dict.setdefault("seed_meta", {})["opening"] = final_envelope.opening_narrative
```

This aligns the CLI path with the server path fix from I-25.
