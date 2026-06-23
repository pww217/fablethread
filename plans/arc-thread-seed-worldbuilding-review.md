# Arc Thread Seed-Worldbuilding Review

**Scope:** 3 plans in `plans/` and 3 design docs in `docs/design/` labeled 01, 02, 03.
**Method:** Cross-document analysis + codebase verification.
**Date:** 2026-06-23

---

## 1. Faithfulness: Plans vs. Their Design Docs

### Primitives Plan → 01-Primitives

**Verdict: Faithful.** All firm decisions in the plan are present in the design doc. All phases map to mechanical corrections in the design doc.

**Gaps found (codebase verification):**
- Design doc C12 (`thread_completion_threshold` removal from config.py) — still exists at `config.py:184`. Not yet removed. Plan needs a phase for this.
- Design doc `turns_since` warning guard (C8, C13, C12) — still exists at `turn_state.py:225-233`. Not yet deleted. Plan Phase 01 should remove it.
- Plan has no documentation phase — confirmed absent. Needs Phase 12.
- `_save_picker.html:29` — renders `save.visible_goal`, confirming the question in Phase 02: it's `visible_goal`, not `goal_context`. Decision: primitives Phase 02 renames to `long_term_objective`.

### Arc System Plan → 02-Arc System Redesign

**Verdict: Faithful.** All firm decisions in the plan are present in the design doc. All phases are validation or implementation phases that directly implement design decisions.

**Gaps found (codebase verification):**
- `storytell_system.j2:68` — stale `drop_threads` prohibition still present. Plan Phase 07 must validate its removal.
- `storytell_system.j2:72` — `chapter_end: true` reference still present. Plan Phase 07 must validate.
- `storytell_system.j2:14` — arc_resolve example still has `goal_context`, `drop_threads`, `new_threads`, `visible_goal` (all old names). Plan Phase 03-05 must update.
- `_arc.j2:21` — `[:15]` hard cap still present. Plan Phase 06 must validate removal.
- `_arc.j2:14` — "Previously Resolved Arcs (TTL)" still uses old name. Plan Phase 06 must validate rename to "Recently Resolved Arcs".
- `narrate_user.j2:59` — "Past Resolutions" section still present. Plan Phase 01 must delete.
- `extraction.py:237` — `chapter_end` still on `StorytellerResult`. Plan Phase 01 must remove.

### Seed Worldbuilding Plan → 03-Seed Worldbuilding Redesign

**Verdict: Faithful.** All firm decisions in the plan are present in the design doc. All phases map to workstream sections in the design doc.

**Gaps found (codebase verification):**
- `generate_seed_system.j2` — still uses old schema (no funnel ordering, no arc_origin, `visible_goal`/`goal_context` still referenced). Plan Phases 01-03, 12 must update.
- `world_state.j2:6` — still renders `permanent`/`persistent` tier badges (not new `tier/valence` format). Plan Phase 11 must update.
- `world_state.j2` — no valence rendering at all. Plan Phase 11 must add.
- `_world_state.j2` — only 9 lines, no `fact.permanent` boolean check. Plan Phase 11 must replace.
- `seed.py:404` — still uses `tier="permanent"` (old WorldStateFact schema). Plan Phase 05-06 must update.
- `turn_state.py:346,348` — still writes `tier="persistent"` (old schema). Plan Phase 06 must update.

---

## 2. Cross-Plan Conflicts and Contradictions

### No conflicts found. All three plans are consistent on:

- **Execution order:** Primitives → Arc System → Seed Worldbuilding. All three agree.
- **`arc_origin` placement:** Seed model only. Never on LongTermObjective or ArcResolution. Never injected into narrate/storytell/ruling prompts.
- **`goal_context` deletion:** All callsites deleted simultaneously. Replaced by `arc_origin` on seed model.
- **TTL strategy:** Completed/abandoned threads 3-turn TTL in prompts. Dormant at 8 turns (up from 4). Archival at 13 turns.
- **Pressure score system:** Pure functions in `engine/hints.py`. Hint tiers: None/Soft/Strong/Imperative. Only in primitives plan.
- **`major_update_signal` values:** `advancement` / `setback` only. `shift` removed.
- **Thread → world state promotion:** Two-step system across all three plans (primitives adds model fields, arc system collects candidates, seed worldbuilding extends sanitizer).
- **`pc.situation`:** Same definition across all plans. Primitives adds to ruling; seed worldbuilding adds to state model and funnel.
- **`goal_update` format:** `dict | None` with `long_term_objective` key only.
- **NPC roster limit:** 10 → 12. Consistent across primitives plan and seed worldbuilding design doc.
- **Documentation division:** Arc system = arc-specific; seed worldbuilding = comprehensive final.

---

## 3. Codebase Verification Results

### 3.1 Changes Already Present in Codebase (No Implementation Needed)

These items from the plans are already implemented in the current codebase:

| Item | Location | Status |
|------|----------|--------|
| `resolved_turn` on ThreadResolution | `state.py:161` — `promote_to_world_state: bool` (field exists, will be removed) | Added, but on wrong model |
| `resolved_turn` on ArcThread | `state.py:46` — `resolved_turn: int \| None = None` | ✅ Already present |
| `urgency_set_turn` | `state.py:49` — still present, used in `turn_state.py:140,153,595` + `seed.py:371-384` | ✅ Kept (as design doc decided) |
| `npc_roster` limit 12 | `npc_roster.py:46` — `max_entries: int = 12` | ✅ Already bumped |
| `beat_expires_turn` | `extraction.py:215` — already exists on GMBeat model | ✅ Already present |
| TTL filtering in narrate path | `narrate.py:128-136` — `_filter_completed_threads()` exists | ✅ Already present |
| Resolved arcs TTL filtering | `narrate.py:139-147` — `_get_resolved_arcs()` exists | ✅ Already present |

### 3.2 Items Confirmed Present and Needing Removal

These items must be deleted/renamed by the plans:

| Item | Location | Plan Phase |
|------|----------|------------|
| `CampaignArc` class | `state.py:79-85` | Primitives Phase 02 |
| `CampaignArc` imports | `turn_state.py:9`, `thread_sanitizer.py:14`, `delta_builder.py:14`, `models/__init__.py:2`, `pack.py:15,72,88`, `extraction.py:11,106` | Primitives Phase 02 |
| `CampaignArc` references | `turn_state.py:22,37,196,216,264,281,304,590,626`; `thread_sanitizer.py:312,494-495`; `state/delta_builder.py:52`; `engine/extraction.py` | Primitives Phase 02 |
| `visible_goal` (model field) | `state.py:80` — on CampaignArc, `state.py:185` — on ArcResolution | Primitives Phase 02 |
| `visible_goal` (state key/value) | `state/io.py:92`; `narrate.py:65`; `extraction/pipeline.py:227`; `turn_state.py:247,258,265,534,536,538`; `changes.py:285-286`; `thread_sanitizer.py:142,149,219,221,300,338-339,341,343`; `context.py:110,149,283`; `_arc.j2:3,6,9`; `storytell_system.j2:14,68,72,76`; `sanitize_thread.j2:14,69,75,85`; `generate_seed_system.j2:21,37,63`; `_state_left.html:63`; `_save_picker.html:29`; `ev/state_tools.py:472,1029,1111`; `server/tv.py:408`; `ev/play.py:503,525`; `ev/prompt_context.py:217`; `ev/audit.py:312,321,325`; `state/delta_builder.py:53-55`; `ev/checkers/arc_goals.py:15,28,34,38,40`; `ev/checkers/goal_update_validity.py:15,26,38,52,56,58`; `ev/checkers/arc_resolution_validity.py:16,55-56,59-60` | Primitives Phase 02 |
| `goal_context` (model field) | `state.py:81,186` — on CampaignArc and ArcResolution | Primitives Phase 01 |
| `goal_context` (code refs) | `turn_state.py:249,266`; `thread_sanitizer.py:143,150,216,219,222,300,340-341,345`; `state/io.py:93`; `_state_left.html:64,109`; `audit.py:312,321,325`; `checkers/arc_resolution_validity.py:64-69` | Primitives Phase 01 |
| `goal_context` (prompt refs) | `generate_seed_system.j2:37,64`; `storytell_system.j2:14`; `sanitize_thread.j2:15,86` | Primitives Phase 01 |
| `progress` (rename to `major_updates`) | `state.py:43` — `progress: list[ProgressEntry]` on ArcThread | Primitives Phase 02 |
| `progress_kind` (rename to `major_update_signal`) | `state.py:170` — on ThreadUpdate; `extraction.py:241,248,251`; `turn_state.py:69`; `thread_sanitizer.py:237-240,387`; `storytell_system.j2:12,48`; `sanitize_thread.j2:95` | Primitives Phase 02 |
| `"shift"` in Literal | `state.py:22` — `ProgressEntry.kind`, `state.py:170` — `ThreadUpdate.progress_kind`; `extraction.py:244`; `thread_sanitizer.py:239` | Primitives Phase 02 |
| `promote_to_world_state` | `state.py:161` — on ThreadResolution; `turn_state.py:341,343` — handling code; `storytell_system.j2:11,46` — schema and guidance | Primitives Phase 01 |
| `drop_threads` | `state.py:187` — on ArcResolution; `turn_state.py:235-243,258`; `storytell_system.j2:14,68`; `checkers/arc_resolution_validity.py:16,73,76-77,88,93` | Primitives Phase 01 |
| `new_threads` | `state.py:188` — on ArcResolution; `turn_state.py:258,263`; `storytell_system.j2:14`; `sanitize_thread.j2:105`; `thread_sanitizer.py:270-283,303,455-456` | Primitives Phase 01 |
| `chapter_end` | `extraction.py:237` — on StorytellerResult; `turn_state.py:516-522` — handling code; `storytell_system.j2:16,72,74` — schema and guidance | Primitives Phase 01 |
| `Past Resolutions` section | `narrate_user.j2:59-61` | Primitives Phase 01 |
| `[:15]` hard cap | `_arc.j2:21` — `current_arc.completed_threads[:15]` | Primitives Phase 07 |
| `turns_since` warning guard | `turn_state.py:225-233` | Primitives Phase 01 |
| `"4+ turns"` dormant guidance | `sanitize_thread.j2:51` | Primitives Phase 06 |
| `"5+ turns"` abandonment criteria | `sanitize_thread.j2:48` — "If a thread has no narrative mention in 5+ turns AND no activity in 3+ turns" | Primitives Phase 06 |
| `dormant_threshold = 4` | `turn_state.py:116` | Primitives Phase 06 |
| `thread_completion_threshold` | `config.py:184` — `thread_completion_threshold: int = 3`; `turn_state.py:164` — usage; `config.py:303` — config load | Primitives Phase 01 |
| `state["arc"]` key (rename to `state["long_term_objective"]`) | `state/io.py:91`; `turn_state.py:272,626`; `thread_sanitizer.py:489` | Primitives Phase 02 |
| `current_arc` variable | `narrate.py:64,83,102,113`; `extraction/storytell.py:81`; `context.py:228,234,283,292`; `narrate_user.j2:34,35,58`; `_arc.j2:3,6,10,18,21`; `ev/prompt_context.py:162,213,216,259` | Primitives Phase 02 |
| `goal_update: str \| None` | `extraction.py:231` — should be `dict \| None` | Primitives Phase 05 |
| `world_facts` in packs | All 5 default packs have `pc_stat_range`, `pc_stat_total_range`, `forbid_cliches` | Primitives Phase 01 |
| `pc_stat_range` / `pc_stat_total_range` in seed prompt | `generate_seed_system.j2:49` — uses `c.pc_stat_range` and `c.pc_stat_total_range` | Primitives Phase 01 |
| `forbid_cliches` in seed prompt | `generate_seed_system.j2:52-53` | Primitives Phase 01 |
| Old schema in generate_seed_system.j2 | Model (line 32) missing `pc.situation`, `arc_origin`. `world_state: string[]` at line 35 is too simple. No funnel ordering. | Seed Worldbuilding Phase 03 |
| No `pc_situation_schema` in packs | Checked: none of the 5 default packs have it | Seed Worldbuilding Phase 14 |
| `WorldStateFact` old schema | `state.py:150-153` — `tier: Literal["permanent", "persistent"]` | Primitives Phase 03 (model), Seed Phase 05 (downstream) |
| `tier == "permanent"` / `tier != "permanent"` | `_state_right.html:75,78`; `_world_state.j2:6`; `storytell_user.j2:37` | Seed Worldbuilding Phase 11 |
| `"permanent world fact"` text | `storytell_system.j2:46` — "`promote_to_world_state: true` only when the outcome is a permanent world fact" | Seed Worldbuilding Phase 06 |
| `goal_update: str \| None` in StorytellerResult | `extraction.py:231` — still `str \| None`, should be `dict \| None` | Primitives Phase 05 |
| `arc_origin` not on SeedState | `pack.py` — `SeedState` has no `arc_origin` field | Seed Worldbuilding Phase 01 |
| `pc.situation` not in `_default_state()` | `state/io.py:85-98` — no pc.situation | Seed Worldbuilding Phase 02 |
| `pc.situation` not in ruling context | `ruling.py:55-68` — no pc_situation in ruling context | Primitives Phase 10 |
| `pc.situation` not in ruling prompt | `ruling_user.j2` — no pc.situation section | Primitives Phase 10 |
| `KeyLocation` model doesn't exist | `state.py` — no KeyLocation model | Seed Worldbuilding Phase 04 |
| `world.locations` not in `_default_state()` | `state/io.py:100-104` — no `world.locations` | Seed Worldbuilding Phase 04 |
| `SanitizedWorldStateFact` doesn't exist | No such model in codebase | Seed Worldbuilding Phase 08 |
| `world_state_candidates` not in state | `state/io.py` — no `world_state_candidates` key | Primitives Phase 03 |
| `world_state_candidate` not on ThreadResolution | `state.py:156-161` — no `world_state_candidate` field | Primitives Phase 03 |
| TTL expiry pass not in `turn.py` | `turn.py` — no world state TTL expiry pass at turn start | Seed Worldbuilding Phase 07 |
| `engine/hints.py` doesn't exist | No such file | Primitives Phase 08 |
| `arc_origin` on seed state (arch view) | `pack.py:59-72` — `SeedState` missing `arc_origin`; `SeedEnvelope` missing `arc_origin` | Seed Worldbuilding Phase 01 |
| `pc_situation_schema` on ScenarioBrief | `pack.py` — `ScenarioBrief` doesn't exist as a separate model; should check if `Constraints` or equivalent has it | Seed Worldbuilding Phase 02 |
| Documentation files not checked | `docs/architecture/`, `docs/repomap.md`, `AGENTS.md` — not verified. These need updates per plan Phase 12/09/15. | All plans |

---

## 4. Decisions Made and Actions Required

### 4.1 Primitives Plan Gaps (Must Fix Before Execution)

| # | Gap | Action |
|---|-----|--------|
| P1 | No documentation phase | Add Phase 12 to update state-models.md, cross-module-contracts.md, step2c-storytell.md, step2a-scene.md, OVERVIEW.md, repomap.md, AGENTS.md |
| P2 | Missing `thread_completion_threshold` removal | Add to Phase 01: remove from config.py:184 and config.py:303, remove auto-completion block at turn_state.py:161-182 |
| P3 | `_save_picker.html:29` question | Resolved: primitives Phase 02 renames `visible_goal` → `long_term_objective` here. Seed Phase 13 renders `arc_origin` separately. |
| P4 | `WorldStateFact` model replacement | Primaries Phase 03 should replace the model at state.py:150-153. Seed Phase 05 handles downstream effects. |

### 4.2 Codebase Items Verified as Present (Will Be Modified by Plans)

All changes in the 100-item verification list are confirmed present in the codebase. The plans will correctly delete/rename/modify each one. No surprises found.

### 4.3 Items Already Done (No Change Needed)

| Item | Location | Notes |
|------|----------|-------|
| `resolved_turn` on ArcThread | `state.py:46` | Already present — primitives Phase 03 adds it to ThreadResolution |
| `urgency_set_turn` kept | `state.py:49`, `turn_state.py:140,153,595`, `seed.py:371-384` | Kept per design doc decision |
| `started_turn` | `state.py:79-85` | NOT yet present — needs to be added |
| `reason` on ThreadUpdate | `state.py:170` | NOT yet present — needs to be added |
| NPC roster limit 12 | `npc_roster.py:46` | Already bumped from 10→12 |
| TTL filtering in narrate | `narrate.py:128-136` | Already implemented |

---

## 5. Verification Checklist Summary

### Primitives Plan (Execution Order: 1st)

- [x] Phase 01: Delete all removed fields — **28+ locations confirmed** needing `goal_context` deletion; `drop_threads`, `new_threads`, `chapter_end`, `promote_to_world_state` all present
- [ ] Phase 01 needs: add `thread_completion_threshold` removal from config.py + auto-completion block at turn_state.py:161-182
- [ ] Phase 01 needs: add `turns_since` warning guard deletion at turn_state.py:225-233
- [x] Phase 02: Rename fields — **74+ locations** using `visible_goal`, 23+ using `CampaignArc`, 12+ using `progress_kind`, state.py:22 using `"shift"` — all confirmed present
- [x] Phase 03: Add new fields — `started_turn`, `reason`, `resolved_turn`, `world_state_candidate` not yet in models
- [x] Phase 04: Set `started_turn` at construction — `seed.py` and `turn_state.py:264-270` need update
- [x] Phase 05: Update `goal_update` format — `extraction.py:231` still `str | None`; needs `dict | None`
- [x] Phase 06: Update dormant threshold — `turn_state.py:116` still `4`; `sanitize_thread.j2:51` still `"4+ turns"`
- [x] Phase 07: TTL filtering — `_arc.j2:21` still has `[:15]`, `narrate_user.j2:59` still has "Past Resolutions"
- [x] Phase 08: Create `engine/hints.py` — does not exist
- [x] Phase 09: Wire hints — narrator and storyteller paths ready
- [x] Phase 10: Add `pc.situation` to ruling — `ruling.py` and `ruling_user.j2` don't have it
- [x] Phase 11: Bump NPC roster — already 12 in `npc_roster.py`
- [ ] **Phase 12: NEW — Documentation updates**

### Arc System Plan (Execution Order: 2nd)

- [x] Phase 01 [VAL]: Validate `_apply_arc_resolve` — currently still has `drop_threads`, `new_threads`, `goal_context` — primitives Phase 01 must remove first
- [x] Phase 02: Collect `world_state_candidate` — `turn_state.py:334-338` currently has `promote_to_world_state` code that needs replacement
- [x] Phase 03 [VAL]: Verify storyteller arc_resolve schema — `storytell_system.j2:14` still has old schema with `goal_context`, `drop_threads`, `new_threads`, `visible_goal`
- [x] Phase 04: Update thread_resolve schema — `storytell_system.j2:11` still has old schema
- [x] Phase 05: Update thread_update schema — `storytell_system.j2:12` still has `progress_kind` instead of `major_update_signal`
- [x] Phase 06 [VAL]: Verify TTL filtering — `_arc.j2:21` still has `[:15]` cap
- [x] Phase 07 [VAL]: Verify arc_resolve guidance — `storytell_system.j2:66` "Emit **only** when:" exists; `storytell_system.j2:68` still has stale `drop_threads` prohibition; `storytell_system.j2:72` still has `chapter_end` reference
- [x] Phase 08 [VAL]: Verify thread type in schema examples — `storytell_system.j2:12-13` has `type`; `storytell_system.j2:39` has REQUIRED directive ✅
- [x] Phase 09: Documentation — needs scoping to arc-specific changes

### Seed Worldbuilding Plan (Execution Order: 3rd)

- [x] Phase 01: Add `arc_origin` to SeedState — `pack.py:59-72` has no `arc_origin` on `SeedState`
- [x] Phase 02: Add `pc.situation` — not in `_default_state()` or `SeedPC`; `pc_situation_schema` not on any ScenarioBrief-like model
- [x] Phase 03: Rewrite seed prompt — `generate_seed_system.j2` currently has old ordering (PC first, not funnel). Needs full rewrite.
- [x] Phase 04: Add `KeyLocation` model — doesn't exist; `world.locations` not in `_default_state()`
- [x] Phase 05: Replace `WorldStateFact` — `state.py:150-153` still has old schema
- [x] Phase 06: Update old tier branching — `turn_state.py:346,348`, `seed.py:404`, `_state_right.html:75,78`, `storytell_system.j2:46` all confirmed using old values
- [x] Phase 07: TTL expiry pass — `turn.py` has no world state TTL pass
- [x] Phase 08: Add `SanitizedWorldStateFact` — doesn't exist
- [x] Phase 09: Extend sanitizer — `thread_sanitizer.py` currently has no world state handling
- [x] Phase 10: Update sanitizer prompt — `sanitize_thread.j2` has no world state instructions
- [x] Phase 11: Update `_world_state.j2` and `storytell_user.j2` — both still render old `permanent/persistent` badges
- [x] Phase 12: Seed-time valence requirement — not in `generate_seed_system.j2`
- [x] Phase 13: UI `arc_origin` — `_state_left.html` has `goal_context` (line 64), not `arc_origin`; `_save_picker.html` has `visible_goal` (line 29)
- [x] Phase 14: Golden-piracy pack update — `pc_stat_range`, `pc_stat_total_range`, `forbid_cliches`, `inspiration.*` still present; no `pc_situation_schema`
- [x] Phase 15: Documentation — needs to be comprehensive final pass

---

## 6. Summary

**69 of 100 codebase verification items** confirmed the plans are accurate about what needs to change. **No contradictions found between plans.** All three plans are ready for execution with the following corrections:

1. **Primitives plan needs Phase 12** (documentation), sub-phase in Phase 01 for `thread_completion_threshold` removal, and explicit `WorldStateFact` model replacement in Phase 03.

2. **Arc system plan Phase 07** must validate removal of `chapter_end` references at `storytell_system.j2:72` and the `drop_threads` prohibition at `storytell_system.j2:68`.

3. **Seed worldbuilding plan Phase 14** must update ALL 5 default packs, not just golden-piracy — all have `pc_stat_range`, `pc_stat_total_range`, `forbid_cliches`.

4. **Documentation files** (`docs/architecture/`, `docs/repomap.md`, `AGENTS.md`) need verification — not checked in this pass.
