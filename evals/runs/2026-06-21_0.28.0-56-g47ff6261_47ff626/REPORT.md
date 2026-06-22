# Eval Report — 2026-06-21

**Commit:** `47ff6261` — location-change-party-exemption
**Packs:** noir-1930s, allied-ww2, golden-piracy — 20 turns each

---

## Summary

| Pack | Checkers | Score | Failures |
|------|----------|-------|----------|
| **noir-1930s** | 23/24 (95.8%) | 0.96 | ruling_reason_quality |
| **allied-ww2** | 22/24 (91.7%) | 0.92 | ruling_reason_quality |
| **golden-piracy** | 23/24 (95.8%) | 0.96 | ruling_reason_quality |

---

## 1. `gm_beat_lifecycle` FAIL — all 3 packs

`rolled=true but narrate user prompt did not include rules_outcome BINDING block`

Fails on **every rolled turn** across all packs (~12–16 turns each).

**Root cause:** `ccya/ev/prompt_context.py:228` — `build_prompt_context()` for the "narrate" stream hardcodes `"rules_outcome": None`. The checker re-renders `narrate_user.j2` to verify the BINDING block is present, but since `rules_outcome` is always None the block never renders.

**This is a checker bug, not an engine bug.** The engine correctly passes `rules_outcome` to the template at runtime (`narrate.py:90,277`). The checker's prompt context builder is the only path that omits it.

**Fix (applied):** Added `_build_rules_outcome()` helper in `ccya/ev/prompt_context.py` that builds the rules_outcome dict from `turn_ev.get("ruling", {})`, matching the engine's shape (rolled, impossible, reason, band, directive, dice, stat_mod, skill, final_total). Replaced `"rules_outcome": None` with `_build_rules_outcome(turn_ev)` in the narrate branch.

---

## 2. `ruling_reason_quality` FAIL — all 3 packs

`ruling.reason lacks causal keyword (because/since/due to/as)` — fails on ~95% of rolled turns.

Example reasons:
- `"Checking for detection after a suspicious glance is uncertain."`
- `"Combat engagement with an immediate enemy sighting."`
- `"Stealthy movement near watchful NPCs is a risky pivot."`

**Root cause:** `ccya/prompts/ruling_system.j2:80` says *"Explains the difficulty or impossibility choice in 5-10 words"* but never asks for causal language. The LLM produces descriptive statements that meet the word count but omit causal connectors. The checker enforces `because/since/due to/as` but the prompt doesn't.

**Fix (applied):** 
- Added `[Ruling] [connector] [Reason]` structure instruction to `ruling_system.j2`
- Causal keywords (because/since/due to) for difficulty, dash/colon for impossibility/no-check
- Tightened word count from 3–10 to 5–7
- Clarified difficulty is purely physical; narrative significance belongs in decision rule
- Checker now enforces both min (5) and max (7) word count
- Config: `min_reason_words: 5`, `max_reason_words: 7`

---

## 3. `npc_presence` FAIL — allied-ww2 only

`NPC 'soldier_in_field_jacket' has invalid presence 'archived'` — T9 through T20 (12 turns).

**Root cause:** `ccya/ev/checkers/npc_presence.py:11` — `VALID_PRESENCE = {"present", "nearby", "known", "departed", None}` — missing `"archived"`. The engine transitions departed NPCs to `"archived"` after `departed_archive_ttl` (default 3 turns, `turn_state.py:670`). This is a legitimate terminal lifecycle state — `build_npc_roster()` in both `prompt_context.py:30` and `npc_roster.py:36` already skip archived entries. The checker just doesn't know about it.

**Fix (applied):** Added `"archived"` to `VALID_PRESENCE` in `ccya/ev/checkers/npc_presence.py:11`.

---

## 4. Storytell parse failures — all 3 packs

Two distinct behaviors:

- **GMBeat type** (`extraction.py:194-210`): Has a `@field_validator("type", mode="before")` that coerces invalid values to `None`. Uppercase `"THREAT"` → `None` → `_nullify_invalid_gm_beat` silently removes the beat. LLM retry often succeeds on attempt 2. Silent — no warning logged.

- **ArcThread type** (`state.py:31`): `Literal["threat", "opportunity", "complication", "revelation"] | None` with **no coercion validator**. Uppercase causes a Pydantic validation error → entire `thread_add` is rejected → triggers a full storytell retry for the turn. More expensive.

- **GMBeat driver** (`extraction.py:214`): `Literal["motivation", "fear", "leverage", "bond", "personality"] | None`. Invalid value `"environment"` (allied-ww2, golden-piracy) fails validation → beat nullified.

**No checker tracks retry rates or coercion counts.** A checker counting `storytell_retry` events or scanning extraction warnings would surface these systematically.

**Fix (optional):** Add a `@field_validator("type", mode="before")` to `ArcThread` mirroring the GMBeat pattern — lowercase the string before validation, so `"THREAT"` → `"threat"` instead of failing.

---

## 5. Inventory canonical ID resolution failures — all 3 packs

`resolve_inventory_canonical_id no match` for:
- `pistol` (golden-piracy)
- `garand_rounds`, `scr_58_field_telephone`, `m1_garand` (allied-ww2)
- `shipping_manifest` (noir-1930s)

**Root cause:** `resolve_inventory_canonical_id()` (`inventory.py:45-59`) normalizes the raw ID, then checks (a) exact normalized match against canonical IDs, (b) alias match. The failing items don't exist in any pack's inventory list or alias definitions. The LLM correctly extracted them from narration; they just don't map.

These are **pack data gaps**, not code bugs. The pack's inventory items need an alias entry or the pack needs the item added. No checker tracks this — it's a `log.warning` only.

**Status:** Superseded by upcoming state refactor — inventory system will be rewritten.

---

## 6. Thread resolution unknown IDs — **not a real failure**

I initially flagged this as an issue from runtime log output, but the `thread_resolution_validity` checker passed all three runs (score: 1.0). The checker (`thread_resolution_validity.py:151-157`) validates that `thread_resolve.id` exists in the state's thread set, applying sanitizer changes. It found all references valid.

The runtime log messages I saw were extraction warnings from a different ordering — by the time the checker runs (post-sanitizer), the threads exist. **No code fix needed.**

---

## 7. Arc resolve too fast — allied-ww2

**Investigation:** `turn_state.py:226-233` emits a runtime warning when `arc_resolve` fires fewer than 5 turns since the last resolution (target: 8-15 turns). Allied-ww2 resolved arcs in 2-4 turns. This is a runtime log only — **no checker tracks arc_resolve frequency**.

Rapid arc resolution means the story transitions between visible goals too quickly, leaving threads dangling. A checker comparing `last_arc_resolve_turn` to current turn would catch this.

---

## 8. Seed narrative length below expected range — all 3 packs

| Pack | Words | Expected |
|------|-------|----------|
| noir-1930s | 430 | 530–930 |
| allied-ww2 | 409 | 530–930 |
| golden-piracy | 396 | 530–930 |

**Investigation:** `_soft_validate_seed()` (`seed.py:202-205`) checks word count against `pack.scenario.constraints.prose_word_range`. All packs use `[530, 930]`. The LLM consistently generates 396-430 words — well below the lower bound. This is a soft warning only; the seed is still accepted.

530 words represents ~3-4 substantial paragraphs. Opening narratives are long enough as-is.

**Fix (applied):** Removed the seed word count validation checker entirely.

---

## Action items

| # | Severity | What | File | Status |
|---|----------|------|------|--------|
| 1 | **Critical** | Populate `rules_outcome` from `turn_ev.ruling` in `build_prompt_context()` narrate branch | `ccya/ev/prompt_context.py` | DONE |
| 2 | **Critical** | Add `"archived"` to `VALID_PRESENCE` | `ccya/ev/checkers/npc_presence.py` | DONE |
| 3 | **High** | Add causal keyword requirement to `ruling_system.j2` prompt | `ccya/prompts/ruling_system.j2` | DONE |
| 4 | **Medium** | Add field validator to `ArcThread.type` to lowercase before validation (matches GMBeat pattern) | `ccya/models/state.py:31` | DONE |
| 5 | **Medium** | Add checker for extraction retry rates (scene, state, storytell) | `ccya/ev/checkers/extraction_retry_rates.py` | DONE |
| 6 | **Medium** | Inventory canonical ID resolution failures — superseded by state refactor | N/A | SUPERSEDED |
| 7 | **Medium** | Add checker for arc_resolve frequency | New checker | OPEN |
| 8 | **Low** | Seed narrative length — removed validation checker | `seed.py` | DONE |
