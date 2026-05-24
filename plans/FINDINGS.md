# Eval Run Findings — `20260524T045455Z_9_w4mtd1`

**Pack:** `full_cycle` · **Model:** `gemma-4-26b-A4B-it-mxfp8` · **Judge model:** `Qwen3.6-35B-A3B-OptiQ-4bit`  
**Turns:** 18 (13 input turns) · **Duration:** 464s · **Retries:** 0 · **Parse failures:** 0  
**Compared against:** `20260524T024358Z_tk_6sfrm` (previous run)

---

## What Phase 01–03 Fixed

### Score parsing: all four domain judges now produce real data

| Domain | Previous run | New run | Change |
|--------|-------------|---------|--------|
| `state_correctness` | avg(3, 3) → meta estimated | avg(3, 3) → **parsed directly** | ✅ Same value, now parsed |
| `narrative_interplay` | `{}` (empty front matter) → meta synthesized from stale data | **3, 3** → **parsed directly** | ✅ Was broken, now works |
| `prompt_pipeline` | `{}` (bold formatting broke YAML) → meta guessed | **5,4,4,4,4 avg 4** → **parsed directly** | ✅ Was broken, now works |
| `compaction` | `{}` (type-hint whitespace broke int coercion) → meta guessed | **3** → **parsed directly** | ✅ Was broken, now works |

### Meta judge no longer synthesizes from empty dicts

The previous run's meta verdict was constructed entirely from estimated/guessed values because three of four domain judges returned `{}`. The new run's meta judge reads real domain scores and only estimates when a specific field is absent (e.g., `state_fidelity_rate` and `prompt_adherence_rate` are not emitted by judges with those field names).

### Auto-checker false positives (Phase 02) deployed but untested in this run

The events.jsonl this run consumed was generated BEFORE Phase 02 changes were applied. The false positives listed below ("Marrow", "Leather", "Though") will require a new eval run with the fixes active to verify improvement.

### Trace quality (Phase 03) deployed: narrate_summary captured

`narrate_summary` field is now present in events.jsonl, providing meta-eval with quick visibility into rules_outcome presence without parsing full rendered_user content. Thread signal logs upgraded from DEBUG to INFO for before/after progress tracking.

---

## Scores

| Score | Value | Meta Adjustment | Source |
|-------|-------|-----------------|--------|
| `mechanical_score` | **3/5** | None | state_correctness: avg(extraction_accuracy=3, mechanic_lifecycle=3) |
| `narrative_score` | **2/5** | Downgrade -1 | narrative_interplay domain value 3 (meta downgrades due to interplay analysis) |
| `system_cohesion_score` | **2/5** | Downgrade -1 | narrative_interplay domain value 3 (same pattern) |
| `prompt_quality_score` | **4/5** | None | prompt_pipeline: avg(rules=5, narrate=4, scene=4, state=4, storytell=4) |
| `compaction_score` | **4/5** (judge score 3; meta adjusted up) | None | compaction value 3 → meta considers partial pass vs generic bullet |
| `state_fidelity_rate` | **0.65** | Estimated | Not emitted by any domain judge. Meta estimates from extraction/lifecycle scores. |
| `prompt_adherence_rate` | **0.85** | Estimated | Not emitted by any domain judge. Meta estimates from prompt_pipeline data. |

---

## CRITICAL — Engine-level bugs surfaced by eval

### C1. Narrator prompt wiring failure: `rules_outcome` never reaches Narrator

**Auto-checker:** `narrate.binding_present` failed on **5 turns** (T6, T7, T10, T11, T13) — every turn where `rolled=true`.

**Root cause:** `_compute_pacing_context()` is skipped or its output is never injected into `narrate_user.j2`. The Narrator generates prose without knowledge of dice outcomes, band results, or mechanical consequences. The engine has mechanics (momentum, conditions, threads) that run correctly, but narrative has no awareness of them.

**Evidence from meta judge:**
- "Anti-declare-outcome enforcement failed" (T11) — player declared "bodyguard draws knife" and engine accepted as fact rather than ruling
- Phantom thread `clear_the_road_toughs` persists T6–13 because Progress Extract has no narrative context to resolve it
- GM beats are "silent state drivers" with no narrative reflection

**Fix:** Inject `_compute_pacing_context()` output and `rules_outcome` into Narrator prompt on every turn where dice were rolled. Requires modifying `_narrate_messages()` or its caller to pass `rules_outcome` parameter.

**Severity:** BREAKS EVERY MECHANICAL TURN. Everything else depends on this.

---

### C2. Progress Extractor fails to emit 4 actions consistently

**Auto-checker:** `storytell.actions_quality` failed on **3 turns** (T4, T8, T12).

**Root cause:** Storyteller LLM returns 0 actions instead of the required 4. The fallback logic in `_run_extraction_pipeline()` generates synthetic actions from narration sentences — this covers the runtime but produces weak actions that don't advance threads.

**Evidence:**
- T3, T6, T9, T12: consistently fails
- State_correctness notes: "Fails to emit exactly 4 actions consistently due to strict JSON schema constraints or model ignoring instructions under certain pacing contexts"
- The fallback actions are generated from `narr_sentences` which may be empty or generic when narration is sparse

**Fix:** Two paths needed: (1) debug the Storyteller prompt's `actions` field schema to improve LLM compliance, (2) improve fallback action generation to produce more substantive actions when LLM fails.

---

### C3. Inventory/Condition ID Schema Drift

**Evidence:**
- Extractors emit `"credits"` but seed/state uses `"Iron Coins"` → rejected deltas on T6, T9
- Extractor emits `"bruisedribs"` (no underscore) but existing condition is `"bruised_ribs"` → phantom condition
- Auto-checker `inventory_remove` fails on T6 (credits), T8 (brass_key)

**Root cause:** No canonical ID mapping layer between extraction output and state persistence. Extractors emit human-readable names from narration; state expects specific IDs.

**Fix:** Implement alias resolution in state delta merger, or standardize extraction prompts to reference canonical IDs from existing state.

**Severity:** Causes validator rejections, phantom conditions, and cascading extraction errors.

---

### C4. Location change delta drop / logging gap

**Auto-checker:** `location_change.applied` failed on **2 turns** (T5, T9) — "location_change emitted but state.location.id unchanged".

**Evidence from meta judge:** "Location deltas are applied to final state but not logged in 'Applied Deltas', suggesting a race condition or separate code path."

**Root cause:** Either (a) the delta is dropped before application but state mutates via a separate path, or (b) the checker reads state at the wrong time (before persist). The meta judge flags this as "engine_bug" — intermediate drop where final state is actually correct.

**Fix:** Investigate `apply_delta()` for location changes and ensure the audit log captures all applied deltas, not just successful ones.

---

## MEDIUM — Eval infrastructure gaps

### M1. `state_fidelity_rate` and `prompt_adherence_rate` not parsed

**Evidence:** Both fields show `null → 0.65 / 0.85` in meta verdict with "Estimation" as the source. The domain judges (state_correctness, prompt_pipeline) do not emit these specific field names in their YAML front matter.

**Root cause:** The domain judge output format uses `extraction_accuracy_score` and `mechanic_lifecycle_score` (state_correctness) and `pipeline_scores` with sub-keys (prompt_pipeline). Neither emits a top-level `state_fidelity_rate` or `prompt_adherence_rate`. The meta judge estimates these from available data instead of reading them directly.

**Fix:** Either (a) make domain judges emit these rate fields in their front matter, or (b) add a post-processing step in `_build_meta_judge_input()` that computes these rates from available scores.

### M2. Auto-checker false positives — "Marrow", "Leather", "Though" still flagged

**Evidence:** `npc_mention.extracted` failed on **5 turns** (T5, T7, T9, T10, T13). Specific false positives:
- "Marrow" (T5): location name fragment from "Marrow's Crossing"
- "Leather" (T7, T9, T10): item descriptor/material
- "Though" (T13): transition word

**Phase 02 status:** These runs used old events.jsonl generated before Phase 02. The fixes (descriptor_stop additions, word-boundary matching, transition word stop list) should address "Though" and "Leather". "Marrow" requires snake_case-aware matching since the location ID is `marrows_crossing` but the natural language form is "Marrow's Crossing".

### M3. `ruling.rolled` assertion: 6 turns failed (false positive)

**Auto-checker:** `ruling.rolled` fails on 6 turns (T2, T3, T5, T8, T9, T13) with detail `"rolled=False"`. This assertion appears to fail whenever `rolled=False` — which is the correct engine behavior for non-dice turns. This is a **false positive** in the assertion logic: it should pass (not flag) when the engine correctly decides not to roll.

**Fix:** The assertion should only fail if rolled=True was expected but not produced, or if the ruling pipeline errored. A turn where no roll is needed should be a pass, not a fail.

### M4. Meta judge lacks raw trace access (structural limitation, unchanged from previous)

The meta judge receives only domain judge scores and body summaries. It cannot independently verify domain judge claims against source data (events.jsonl, state snapshots, prompts). This is by design for token budget but means meta analysis quality depends entirely on domain judge thoroughness.

---

## LOW — Cosmetic / future drift risks

### L1. Compaction judge scored 3 but meta reports 4

The compaction judge self-scores 3/5 (one "PARTIAL" pass, T4 generic bullet). The meta judge reports compaction_score as 4 with a note that the adjustment is based on considering the partial pass as minor. This is a transparency issue — the meta should explain the adjustment or the domain judge should score higher.

### L2. `generate_actions_quality_failure` emits duplicate action types

The fallback action generation in `_run_extraction_pipeline()` (extraction.py) can emit the same action type multiple times (e.g., two "take a careful look" actions) when `present_npc_names` is empty and no narr_sentences exist. This technically satisfies the "4 actions" count but produces meaningless duplicates.

### L3. Momentum band_delta always reported as 0

The engine's momentum delta field in `RulesOutcome` is consistently reported as `0` even on successful rolls. The state_correctness judge flags this: "T5 shows a drop from -1 to -3 despite reporting delta=0. The momentum logic appears broken or disconnected from the dice resolution output." This may be a logging bug rather than a momentum calculation bug (state shows correct values).

---

## Summary

| Priority | What | Who | Estimated effort |
|----------|------|-----|-----------------|
| **C1** | Inject `rules_outcome` + `PacingContext` into Narrator prompt | `turn.py`/`narrate.py` | 1-2 days |
| **C2** | Fix Progress Extractor 4-action failure (prompt + fallback) | `extraction.py` prompts | 1-2 days |
| **C3** | ID normalization layer for inventory/conditions | `state.py` delta merger | 1 day |
| **C4** | Location change delta logging/timing | `turn.py` apply_delta path | 0.5 day |
| **M1** | Emit `state_fidelity_rate` from domain judges | `judge.py` per-domain | 0.5 day |
| **M2** | Fix remaining auto-checker false positives | `universal_asserts.py` | 0.5 day |
| **M3** | Fix `ruling.rolled` false positive assertion | `universal_asserts.py` | 0.5 day |
