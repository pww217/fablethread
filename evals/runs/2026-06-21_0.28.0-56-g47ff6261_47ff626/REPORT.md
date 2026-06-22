# Eval Report — 2026-06-21

**Commit:** `47ff6261` — location-change-party-exemption
**Packs:** noir-1930s, allied-ww2, golden-piracy — 20 turns each

---

## Summary

| Pack | Checkers | Score | Failures |
|------|----------|-------|----------|
| **noir-1930s** | 22/24 (91.7%) | 0.92 | gm_beat_lifecycle, ruling_reason_quality |
| **allied-ww2** | 21/24 (87.5%) | 0.88 | gm_beat_lifecycle, npc_presence, ruling_reason_quality |
| **golden-piracy** | 22/24 (91.7%) | 0.92 | gm_beat_lifecycle, ruling_reason_quality |

---

## 1. `gm_beat_lifecycle` FAIL — all 3 packs

`rolled=true but narrate user prompt did not include rules_outcome BINDING block`

Fails on **every rolled turn** across all packs (~12–16 turns each).

**Root cause:** `ccya/ev/prompt_context.py:228` — `build_prompt_context()` for the "narrate" stream hardcodes `"rules_outcome": None`. The checker re-renders `narrate_user.j2` to verify the BINDING block is present, but since `rules_outcome` is always None the block never renders.

**This is a checker bug, not an engine bug.** The engine correctly passes `rules_outcome` to the template at runtime (`narrate.py:90,277`). The checker just can't reproduce it.

**Fix:** Populate `rules_outcome` from `turn_ev.ruling` in the narrate branch of `build_prompt_context()`.

---

## 2. `ruling_reason_quality` FAIL — all 3 packs

`ruling.reason lacks causal keyword (because/since/due to/as)` — fails on ~95% of rolled turns.

Example reasons:
- "Checking for detection after a suspicious glance is uncertain."
- "Combat engagement with an immediate enemy sighting."
- "Stealthy movement near watchful NPCs is a risky pivot."

**Root cause:** `ccya/prompts/ruling_system.j2:80` says _"Explains the difficulty or impossibility choice in 5-10 words"_ but never asks for causal language. The LLM produces descriptive statements. The checker enforces `because/since/due to/as` but the prompt doesn't.

**Fix:** Add causal keyword requirement to `ruling_system.j2`, or relax the checker.

---

## 3. `npc_presence` FAIL — allied-ww2 only

`NPC 'soldier_in_field_jacket' has invalid presence 'archived'` — T9 through T20 (12 turns).

**Root cause:** `ccya/ev/checkers/npc_presence.py:11` — `VALID_PRESENCE = {"present", "nearby", "known", "departed", None}` — missing `"archived"`. The engine transitions departed NPCs to `archived` after `departed_archive_ttl` (default 3 turns, `turn_state.py:670`). This is a legitimate state; the checker just doesn't know about it.

**Fix:** Add `"archived"` to `VALID_PRESENCE`.

---

## 4. Storytell parse failures — all 3 packs

LLM returns uppercase thread types (`THREAT`, `REVELATION`, `COMPLICATION`, `OPPORTUNITY`) instead of lowercase. Invalid `gm_beat.driver` value `"environment"` appeared in allied-ww2 and golden-piracy. Allied-ww2 turn 2 had complete storytell failure (no actions after retries).

No checker tracks retry rates or extraction coercion failures.

---

## 5. Inventory canonical ID resolution — all 3 packs

`resolve_inventory_canonical_id no match` for:
- `pistol` (golden-piracy)
- `garand_rounds`, `scr_58_field_telephone`, `m1_garand` (allied-ww2)
- `shipping_manifest` (noir-1930s)

Items exist in inventory but don't match any canonical ID. No checker tracks this.

---

## 6. Thread resolution unknown IDs — all 3 packs

`thread_resolve` references IDs not found in state:
- noir-1930s: `dockside_extortion`, `alleyway_combat`
- allied-ww2: `enemy_sighting_immediate`, `ridge_skirmish_escalation`
- golden-piracy: `naval_blockade`

No checker validates `thread_resolve.target_thread_id` exists in `state.arc.threads` (separate from `thread_resolution_validity` which checks the resolution itself).

---

## 7. Arc resolve too fast — allied-ww2

Arcs resolved in 2–4 turns (target 8–15). No checker tracks `arc_resolve.frequency`.

---

## 8. Seed narrative length — all 3 packs

Opening narrative below expected range:

| Pack | Words | Expected |
|------|-------|----------|
| noir-1930s | 430 | 530–930 |
| allied-ww2 | 409 | 530–930 |
| golden-piracy | 396 | 530–930 |

No checker validates seed output quality.

---

## Action items

| # | Severity | What | File |
|---|----------|------|------|
| 1 | Critical | Populate `rules_outcome` in `build_prompt_context()` narrate branch | `ccya/ev/prompt_context.py:228` |
| 2 | Critical | Add `"archived"` to `VALID_PRESENCE` | `ccya/ev/checkers/npc_presence.py:11` |
| 3 | High | Add causal keyword requirement to ruling prompt or relax checker | `ccya/prompts/ruling_system.j2` |
| 4 | Medium | Add checker for storytell parse failure rates | New checker |
| 5 | Medium | Add checker for inventory canonical ID resolution failures | New checker |
| 6 | Medium | Add checker for thread resolve target ID validity against state | New checker |
