# Phase 2 Review Findings

## Observation: Sentinel markers in Jinja templates are visible to production LLM

**Files:** `ccya/prompts/narrate_user.j2`, `ccya/prompts/extract_scene_user.j2`, `ccya/prompts/extract_progress_user.j2`

The sentinel markers (`<<<TRACE_IMMUTABLE_START>>>` / `<<<TRACE_IMMUTABLE_END>>>`) are injected into the Jinja templates. The rendered user prompts stored in `events.jsonl` contain these markers. The engine strips them via `strip_trace_markers_in_messages()` BEFORE sending to the LLM.

**Verification:** All 5 chat call sites (rules, narrate x2, extract_scene, extract_state, extract_progress) now call `strip_trace_markers_in_messages()` after capturing the rendered content but before trimming and sending to the LLM. The `rendered_user` stored in events retains the markers for the eval trace.

**Status:** ✅ Implemented — `ccya/engine/markers.py` + `turn.py` (3 sites) + `extraction.py` (3 sites)

---

## Observation: `npc_roster` in extract_scene_user.j2 may not be truly immutable

**File:** `ccya/prompts/extract_scene_user.j2:25-29`

The compendium NPC roster (`npc_roster`) is marked as immutable. However, the compendium can grow over time as new NPCs are added via `compendium_npc_update`. If the roster grows, the judge would not see new entries in the deduped trace.

**Mitigation:** New compendium entries appear in the per-turn `applied.compendium_npc_update` and in the `state_snapshot` at end of turn. The judge can reconstruct from those signals. If this becomes a problem, the markers can be removed from this section.

**Status:** ⚠️ Documented — acceptable for Phase 2; monitor in practice.

---

## Observation: State diff uses `id` as identity for all list-of-dict items

**File:** `ccya/eval/judge.py:_diff_list`

The diff helper assumes list items have an `id` field. If a list has dicts without `id`, it falls back to set-diff via `_hashable`. This may be lossy for complex nested objects.

**Status:** ✅ Acceptable — fallback is documented in code; no known lists without `id` in the state schema.

---

## Summary

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | Design | Sentinel markers visible to production LLM if not stripped | ✅ Fixed — all 5 call sites strip |
| 2 | Minor | `npc_roster` may not be truly immutable | ⚠️ Documented — judge can reconstruct from applied deltas |
| 3 | Minor | State diff fallback for lists without `id` may be lossy | ✅ Acceptable — no known cases in state schema |

---

## Bug: Runner writes raw disk events (no `state_snapshot`) to output

**File:** `ccya/eval/runner.py:584-592`

The runner injects `state_snapshot` into `turn_events` (line 570) for use by structured asserts, but then writes `all_events` (raw disk events) to the output directory. The judge never sees `state_snapshot` in the output events.

**Fix:** Write enriched events built from `turn_events` (with injected snapshots) + metadata event.

**Status:** ✅ Fixed — `ccya/eval/runner.py:584-590`

---

## Minor: Variable shadowing in `report.py:_collect_flags`

**File:** `ccya/eval/report.py:296-306`

`cur` shadows the function parameter `cur: list[TurnMetrics]`. The outer `cur` is not used after this block, so it's latent, not active.

**Fix:** Renamed to `cur_score`.

**Status:** ✅ Fixed — `ccya/eval/report.py:296-306`

---

## Summary

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | Design | Sentinel markers visible to production LLM if not stripped | ✅ Fixed — all 5 call sites strip |
| 2 | Minor | `npc_roster` may not be truly immutable | ⚠️ Documented — judge can reconstruct from applied deltas |
| 3 | Minor | State diff fallback for lists without `id` may be lossy | ✅ Acceptable — no known cases in state schema |
| 4 | **Bug** | Runner writes raw disk events (no `state_snapshot`) to output | ✅ Fixed |
| 5 | Minor | Variable shadowing: `cur` in `_collect_flags` | ✅ Fixed — renamed to `cur_score` |

---

## Phase 3 Implementation Notes

### New file: `ccya/eval/universal_asserts.py`

5 universal assertion functions covering:
- `check_recent_events_turn_stamped` — verifies `recent_events_add[].turn` is stamped with current turn
- `check_pending_gm_beat_consumed` — verifies `pending_gm_beat` doesn't persist unchanged across turns
- `check_location_change_applied` — verifies `location_change` applied delta matches state location.id
- `check_rolled_implies_binding` — verifies `rules.rolled=true` implies narrate prompt has BINDING block
- `check_npc_mention_extracted` — heuristic: flags narration names not in npc_add/update/known (conservative, >3 missing suppressed)

### Changes to `ccya/eval/judge.py`

- `build_trace()` now accepts `auto_checker_failures` and `metrics_rows` kwargs
- `_render_deterministic_signals()` renders Auto-Checker Failures + Metrics tables
- `_build_metrics_rows()` extracts token counts from `rules_prompt.context_meta.est_tokens` and `narrate_prompt.context_meta.est_tokens` (not from old `rules["tokens_in"]` path)
- `run_judge()` computes universal assert failures from events and passes them to `build_trace()`

### Changes to `ccya/eval/runner.py`

- Universal asserts run after scenario-specific asserts for every turn
- Results appended to `record.assert_results` (same format as scenario asserts)

### Changes to `ccya/eval/engine_mirror.py`

- Added `BANDS`, `SKILLS`, `DIFFICULTIES`, `INTENT_VERBS_HINT`, `PC_CONDITION_CAP`, `SCENE_NAMED_NPC_CAP` constants
- `constants_block()` now includes all schema constants for judge trace

### Changes to `evals/rubrics/default.md`

- Auto-checker integration section updated to reference `# Deterministic Signals` section
- Output format already had `# Auto-Checker Failures` section referencing Deterministic Signals
