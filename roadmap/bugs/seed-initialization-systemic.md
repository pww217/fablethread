---
title: "Seed Initialization Systemic Failures — Dynamic Packs"
status: done
urgency: 1
size: large
created: 2026-06-24
labels:
  - engine
  - seed
  - arc
  - sanitizer
  - generation
---

## Investigation Summary

All 4 original issues have been investigated. Root causes identified and fixes applied for issues 1, 3, 4, and 5.

---

All 5 user-facing packs (noir-1930s, allied-ww2, golden-piracy, space-western, zombie-survival) use **dynamic seeds** via `scenario.yaml`. Static packs have been removed entirely — the eval harness no longer uses a static pack. This ticket documents findings specific to the dynamic seed pipeline.

---

## 1. Static Seed Path Removed

The static seed path in `routes.py` has been removed entirely. All new games now go through the dynamic seed pipeline (`generate_seed()`). The `_generate_seed_actions()` helper, `pack_type` parameter in `_apply_seed_to_save_dir()`, and `_seed_type` metadata have all been removed. The `packs/eval/` directory has been deleted.

**Path:** `routes.py:532-543` — when hints are provided, `pack.seed` is used.

**Bug:** `SeedState` model (`pack.py:60-76`) had no `actions` field. `_apply_seed_to_save_dir()` was called with `actions=None`, so `_dynamic_opening_actions = []`. The UI rendered no action pills.

**Evidence:** `SeedState` fields: `meta, pc, location, inventory, scene, compendium, arc, arc_origin, world`. No `actions`. `SeedEnvelope` (dynamic path) has `actions: list[str]` with `min_length=4, max_length=4`.

**Impact:** Static seed packs (eval harness + hints fallback) produced no opening choices.

**Fix applied:**
- Added `actions: list[str] = Field(default_factory=list)` to `SeedState` (`pack.py:75`)
- Added `_generate_seed_actions()` helper (`routes.py:72-116`) that generates 4 fallback actions from seed context (quests, NPCs, inventory, arc goal)
- Updated static seed path to call `_generate_seed_actions(seed)` and pass actions to `_apply_seed_to_save_dir()` (`routes.py:542-543`)
- Updated `_apply_seed_to_save_dir()` condition to allow actions without opening_narrative (`routes.py:139`)

---

## 2. Dynamic Seed Actions — Works in Eval, May Fail in Practice

**Path:** `routes.py:545-556` → `generate_seed()` → `SeedEnvelope` with `actions`.

**Finding:** All 12 eval runs (2026-06-24) show 4 actions in `state.yaml['__seed_meta__']['actions']`. The SeedEnvelope validation enforces `min_length=4, max_length=4`.

**Risk:** If LLM fails to produce valid JSON with exactly 4 actions, SeedEnvelope validation fails and retries. If all retries fail, `generate_seed()` raises `RuntimeError` → user sees "Game creation failed". This is not a silent failure — but it's a hard failure with no fallback.

**Prompt constraints** (`generate_seed_system.j2:214-224`):
- Exactly 4 choices, 7–10 words each, active voice
- At least 2 advance arc goal or active thread
- One involves named NPC present in scene
- One is environmental
- One is freeform rooted in PC background or motivation
- Span different postures: confront, deflect, investigate, protect, exploit, withdraw
- No generic verbs fitting any protagonist in any setting
- At least 2 should reveal character priorities or relationships

**Assessment:** These constraints are very specific. The LLM may struggle to produce 4 distinct, non-generic actions that all fit simultaneously. Consider relaxing or providing fallback generation.

---

## 3. Arc Origin Overlaps PC Bio (FIXED)

**Prompt analysis** (`generate_seed_system.j2:129-130`):

```
## Arc origin
- `arc_origin`: 2–3 sentences in past tense answering "how did the PC end up here?" This is a seed-time field only — never regenerated. It should connect the PC's backstory to the current situation in a way that feels inevitable in hindsight.
```

**Bug:** The prompt asked arc_origin to answer "how did the PC end up here?" — this inherently required knowledge of the PC's backstory. The generation order (step 5) placed arc_origin **after** PC bio generation (step 4), so the LLM had the bio context and would naturally conflate them.

**Expected behavior:** `arc_origin` should be independently invented lore (world history, faction events, ancient conflicts) that **later** gets tied to the PC through gameplay or arc threads. It should not be a restatement of the PC's backstory.

**Evidence:** Generation order in prompt:
1. World facts (global)
2. World facts (local)
3. Key locations
4. PC situation ← PC bio generated here
5. **Arc origin** ← has PC bio context, will overlap
6. Campaign arc

**Fix applied:**
- Moved arc_origin to step 4 (before PC situation) in generation order (`generate_seed_system.j2:64-66`)
- Rewrote arc_origin prompt to ask for independent world-level lore, not PC-specific backstory (`generate_seed_system.j2:129-130`)
- Updated generation order numbering accordingly

---

## 4. Seed Turn Summary Broken (FIXED)

**Finding:** `SeedEnvelope` has an `outcome_summary` field (`pack.py:92`). The prompt asks for "One sentence (~10–20 words) summarizing the opening situation as a quest-log or journal entry."

**Path:** `routes.py:507` passes `outcome_summary=envelope.outcome_summary` to `_apply_seed_to_save_dir()`. This is stored in `state.yaml['__seed_meta__']['outcome_summary']`.

**Root cause** (`routes.py:274`): `ctx["opening_outcome_summary"] = _get_opening_outcome_summary() if opening else ""`. The `opening_outcome_summary` was only set if `opening` (the opening narrative) was truthy. `_get_opening_outcome_summary()` returns `_app._dynamic_opening_outcome`, which is a module-level variable set during dynamic seed creation. This variable is ephemeral — if the server restarts or a new game starts, it's reset. The seed's `outcome_summary` was written to `state.yaml` but **never read back** for display.

**Assessment:** This IS a bug. The seed's `outcome_summary` was generated and stored but not displayed in the UI.

**Fix applied:** Updated `routes.py:274` to read `outcome_summary` from `state.yaml['__seed_meta__']['outcome_summary']` first, falling back to `_get_opening_outcome_summary()` if not found:
```python
ctx["opening_outcome_summary"] = (state.get("__seed_meta__") or {}).get("outcome_summary", "") or (_get_opening_outcome_summary() if opening else "")
```

---

## 5. Sanitizer Not Running (FIXED)

**Finding:** `turn.py:495-505` — sanitizer runs if `config.sanitize_every > 0`. The sanitizer is called **after** turn persistence, not during seed initialization.

**Root cause** (`thread_sanitizer.py:233-260`): The `_validate_parsed()` function validates LLM JSON output against Pydantic models (`ThreadUpdate`, `ThreadResolution`, `SanitizedWorldStateFact`). However, `urgency` and `type` fields in `ThreadUpdate` had **no coercion** for non-standard values. If the LLM returned values like `"urgency": "high"` or `"type": "danger"`, validation failed and ALL thread updates were skipped. The `major_update_signal` field had coercion to "advancement", but `urgency` and `type` did not.

Similarly, `resolution_state` in `ThreadResolution` and `valence`/`tier` in `SanitizedWorldStateFact` had no coercion.

**Impact:** If the LLM consistently returned non-standard enum values, the sanitizer would consistently return `sanitize_ran=False`, making it appear as if it "didn't run."

**Fix applied:** Added coercion for non-standard enum values in `_validate_parsed()`:
- `urgency`: coerce to "normal" if not in `["background", "normal", "urgent"]`
- `type`: coerce to `None` if not in `["threat", "opportunity", "complication", "revelation"]`
- `resolution_state`: coerce to "resolved" if not in `["resolved", "failed", "abandoned"]`
- `tier`: coerce to "global" if not in `["global", "local"]`
- `valence`: coerce to "neutral" if not in `["threat", "complication", "neutral", "boon"]`

---

## 6. Arc Origin Prompt — Additional Issues

**Generation order problem:** The prompt says "Build in this order, using everything already established before generating what comes next." But arc_origin (step 5) was asked to "connect the PC's backstory to the current situation" — this required the PC bio (step 4) to be complete. The LLM would naturally use the bio context, causing overlap.

**Prompt contradiction:** The prompt said arc_origin should be "seed-time field only, never regenerated" but also said it should "connect the PC's backstory to the current situation." This created a tension: if it's truly independent lore, it shouldn't reference the PC's backstory. If it connects to the PC's backstory, it's not independent.

**Fix applied:** Rewrote arc_origin prompt to explicitly ask for independent world-level lore with no PC references. The PC tie-in happens in step 6 (campaign arc threads).

---

## Files Changed

- `ccya/pack.py` — Added `actions: list[str]` field to `SeedState`
- `ccya/server/routes.py` — Added `_generate_seed_actions()` helper, updated static seed path, fixed outcome_summary display
- `ccya/prompts/generate_seed_system.j2` — Fixed arc_origin generation order and prompt
- `ccya/engine/thread_sanitizer.py` — Added coercion for non-standard enum values in `_validate_parsed()`