# State Fidelity Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Inventory and key lifecycle | Fix brass_key phantom, inventory_update vs re-add, and vague payments vs zero-balance removes |
| 02 | Quest identity and auto-close | Ensure single quest per concept, enforce dedup across all quests. **Step 02.2 (terminal-state guard) is superseded by mechanical plan Phase 03** — skip that step. |
| 03 | NPC presence consistency | Prevent ghost NPCs from remove-then-readd cycles and clarify "absence ≠ departure" in state handling |
| 04 | Conditions and pressures | Bring `bruised_ribs`-style conditions and long-lived pressures under explicit TTL and resolution rules. **Step 04.1 (pressure TTL) defers to system-cohesion plan Phase 03** — skip that step. |

## Objective
The eval run exposed multiple state fidelity issues: phantom inventory items (brass_key persisted after confirmed use), incorrect inventory operations (re-adding instead of updating, or removing items that never existed), duplicate quests for the same concept, completed quests that remained active, ghost NPCs that disappeared then reappeared as new, and a wound condition (`bruised_ribs`) and ambient pressures that persisted for nearly the entire run without resolution. This plan tightens `apply_delta`, the extraction pipeline, and related state helpers so that the serialized state always matches the narrated fiction and internal lifecycle rules.

## Non-goals
- Prompt changes for key-use, duplicate quests, or ghost NPCs — those live in the prompt-quality plan.
- Changes to compactor sanitization or prior_history compaction — covered in the system-cohesion plan.
- Auto-checker and eval harness changes — separate eval plan.
- Broad redesign of the pressure system; here we only enforce consistency with existing design.

---

## Implementation — Phase 01: Inventory and key lifecycle

### Files to pull for context
- `ccya/state/delta.py` (`apply_delta`, especially inventory section at lines 89-177)
- `ccya/state/inventory.py` (`normalize_inventory_id`, `resolve_inventory_canonical_id`, `resolve_inventory_remove_target`, `_fuzzy_match_inventory`)
- `ccya/engine/extraction.py` (to see how `inventory_add/remove/update` map into StateDelta)

### Detailed steps

#### Step 1.1 — Treat duplicate add of existing item as update, not new entry

**File:** `ccya/state/delta.py`

**What:** This behavior **already exists** in `apply_delta` at lines 99-139. When `inventory_add` refers to an ID that already exists in `state["inventory"]`, the code adds the new amount to the existing entry (line 107: `ex["amount"] = int(ex.get("amount", 1)) + amt`). A fuzzy-match safety net also exists at lines 117-134.

**Why:** T8 appears to re-add the brass key as a new item rather than updating the existing entry. Since the merge logic exists, the root cause is likely in the extraction pipeline sending a new ID instead of the canonical ID, or the `reconcile_delta` function not catching add+remove conflicts for the same item.

**Action:** Verify `reconcile_delta` at `delta.py:54-81` handles the case where the same item appears in both `inventory_add` and `inventory_remove` on the same turn. The existing code (lines 63-68) drops from add when `add_ids & remove_ids` conflicts exist — this should already prevent the brass_key phantom if the extractor sends both add and remove. If the extractor only sends add (missing the remove), the issue is in extraction, not `apply_delta`.

**Validation:** Test: start with a state containing one `brass_key` with `amount: 1`. Apply a delta with `inventory_add[id="brass_key", amount=1]`. Assert there is still one entry with `amount: 2`.

---

#### Step 1.2 — Ensure successful key use removes the key from inventory

**File:** `ccya/state/delta.py`

**What:** This behavior **already exists** in `apply_delta` at lines 141-164. When `inventory_remove` reduces an item's amount to 0 or below, the item is removed from the inventory list (line 161: `inv = [x for x in inv if x.get("id") != canonical]`).

**Why:** The brass key remained in inventory across T8–T13. Since the removal logic exists, the root cause is likely that the extractor never sent `inventory_remove` for the brass key, or `reconcile_delta` blocked the remove due to a conflict.

**Action:** Verify the extraction pipeline sends `inventory_remove` when a key is consumed. Check that `reconcile_delta` (line 63-68) doesn't drop the remove due to a false add+remove conflict.

**Validation:** Test: apply a delta that removes the only `brass_key`. Assert no entry with `id == "brass_key"` remains in `state["inventory"]`.

*(Note: this complements the mechanical plan's `_validate` zero-balance guard; together they prevent both engine rejections and phantom items.)*

---

#### Step 1.3 — Align vague payments and zero-balance rules

**File:** `ccya/state/delta.py`

**What:** `_validate` in `turn.py:875-920` already rejects overdraws as `kind: "warn_overdraw"` (non-blocking). `apply_delta` at lines 157-163 clamps overdraw to a full-stack remove. Adding duplicate overdraw detection in `apply_delta` would be redundant since `_validate` already handles this.

**Why:** T9 and T13 showed overdraw-like behavior; we want a single source of truth: `_validate` rejects, `apply_delta` assumes well-formed input.

**Action:** No code change needed in `apply_delta`. Instead, verify that `_validate`'s `warn_overdraw` classification (non-blocking) is appropriate — if overdraw should be a hard error, change `kind` from `"warn_overdraw"` to a blocking rejection in `turn.py:903-915`.

**Validation:** Unit test that attempts to remove more than available produces the expected rejection/warning behavior from `_validate`.

---

### Tests to write or update
- `tests/test_delta_inventory_merge.py` — add coverage for duplicate add → update, and zero-amount removal → item removal.
- `tests/test_delta_inventory_overdraw.py` — assert overdraw produces warning and no negative amounts.

### REPOMAP and architecture updates
- `docs/REPOMAP/state.md`: expand `apply_delta` inventory section to mention add-as-update and automatic removal of zero-amount items (already implemented; just verify docs are current).

### Risks
1. Existing code might already rely on zero-amount items as signals; search the repo for `amount == 0` on inventory before changing behavior.
2. If any scenario expects re-usable keys, ensure their items are modeled with non-removal semantics in prompts (i.e., not matching the "consumed key" examples from the prompt plan).

---

## Implementation — Phase 02: Quest identity and auto-close

### Files to pull for context
- `ccya/state/delta.py` (`apply_delta` — quest section at lines 195-298)
- `ccya/state/io.py` (`_default_state` for initial quest shape)
- `docs/REPOMAP/state.md`

### Detailed steps

#### Step 2.1 — Enforce quest ID uniqueness by semantic alias

**File:** `ccya/state/delta.py`

**What:** Introduce quest title normalization and dedup in `apply_delta`'s quest upsert section. Before appending a new quest (line 275-292), check if an existing quest has the same normalized title. If so, redirect the new quest's ID to the existing quest's ID and merge objectives.

**Why:** T8 created `deliver_halden_ledger` even though `deliver_the_ledger` already represented the same quest.

**Code Snippet**
```python
def _normalize_quest_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())

# In apply_delta, inside the quest loop, in the else branch (new quest) at line ~274:
# Before creating new_q:
new_title_norm = _normalize_quest_title(qu.title) if qu.title else ""
for existing_q in state.get("quests", []):
    existing_title_norm = _normalize_quest_title(existing_q.get("title", ""))
    if new_title_norm and existing_title_norm and new_title_norm == existing_title_norm:
        # Redirect new quest to existing — merge objectives
        log.warning(
            "Quest alias collision; redirecting new quest id to existing",
            extra={
                "existing_id": existing_q["id"],
                "proposed_id": qu.id,
            },
        )
        # Update existing quest with new data instead of creating new
        qu = QuestUpdate(
            id=existing_q["id"],
            title=qu.title,
            status=qu.status,
            objectives=qu.objectives,
        )
        # Fall through to the "existing quest" branch (if qu.id in existing_quests)
        break
else:
    # No collision found — proceed with new quest creation
    new_q: dict[str, Any] = {
        "id": qu.id,
        "title": _strip_non_ascii(qu.title) if qu.title else "",
        "status": qu.status or "active",
        "objectives": [
            {
                "description": _strip_non_ascii(o.description) if o.description else "",
                "done": o.done if o.done is not None else False,
                "failed": bool(o.failed) if o.failed is not None else False,
            }
            for o in qu.objectives
            if o.description
        ],
    }
    state.setdefault("quests", []).append(new_q)
    existing_quests[qu.id] = new_q
    _apply_quest_status_side_effects(new_q)
    touched_quest_ids.add(qu.id)
```

**Validation:** Test: state has `deliver_the_ledger` with title "Deliver the ledger to Halden." Delta contains quest update id `deliver_halden_ledger`, title "Deliver the ledger to Halden." Assert the update is redirected to the original ID and objectives are merged.

---

#### Step 2.2 — Make auto-close robust against re-activation

**ABANDONED — superseded by mechanical plan Phase 03, Step 3.1.**

The mechanical plan (`mechanical_remediation_eval_run_20260512t154142z_uufm2ojg.md`) already implements the terminal-state guard in `apply_delta`'s quest upsert loop: it checks whether a quest already has `status == "completed"` or `"failed"` and skips the upsert with a structured log warning. This state-fidelity plan's Step 3.1 would duplicate that logic with a slightly different implementation (this plan checks status at reassignment time; mechanical plan checks at upsert entry time). Execute the mechanical plan's Step 3.1 instead.

---

### Tests to write or update
- `tests/test_delta_quest_alias.py` — verify redirection of alias IDs.
- ~~`tests/test_delta_quest_terminal_state.py`~~ — **superseded by mechanical plan Phase 03 tests** (`tests/test_delta_quest.py`).

### REPOMAP and architecture updates
- `docs/REPOMAP/state.md`: document quest alias detection. Terminal-state behavior is documented by the mechanical plan.

### Risks
1. Over-aggressive title normalization might merge distinct quests with similar wording. Mitigation: keep normalization conservative (case and whitespace only) and rely on pack designers to avoid near-duplicate titles for different quests.

---

## Implementation — Phase 03: NPC presence consistency

### Files to pull for context
- `ccya/state/delta.py` (`apply_delta` — present_npcs, recently_left at lines 400-562)
- `ccya/state/npcs.py` (`build_npc_alias_map`, `touch_compendium_order`)
- `ccya/engine/extraction.py` (`_run_extraction_pipeline`, NPC post-processing)

### Detailed steps

#### Step 3.1 — Treat NPC removal as explicit-only

**File:** `ccya/state/delta.py`

**What:** This behavior **already exists** in `apply_delta`. At line 462, NPC presence is only updated when `has_npc_delta` is True (i.e., `delta.npc_add`, `delta.npc_remove`, or `delta.npc_update` is non-empty). Removals only happen via explicit `npc_remove` entries (lines 468-474). Absence from `npc_add` does not cause removal.

**Why:** T7 removed the toughs even though the narration didn't clearly state they left; this should never happen from implicit absence alone.

**Action:** No code change needed in `apply_delta`. The issue is likely in the extraction pipeline — verify that `SceneExtractResult.npc_remove` is being populated correctly when NPCs leave the scene. Check `_run_extraction_pipeline` in `extraction.py` lines 609-642 for the dedup logic that might be converting `npc_add` to `npc_update` instead of leaving NPCs in place.

**Validation:** Test: starting with two NPCs in `present_npcs`, apply a delta that has only narration about someone else with no `npc_remove`. Assert both NPCs remain.

---

#### Step 3.2 — Keep "recently_left" tracking consistent with removals

**File:** `ccya/state/delta.py`

**What:** This behavior **already exists** in `apply_delta` at lines 550-562. When NPCs are removed from `present_npcs`, `left_ids` is computed as `old_present_ids - new_present_ids`, and `recently_left` is populated with the removed NPCs' info from the compendium.

**Why:** T7 removed toughs; T10's re-add treated them as newly appearing rather than "still nearby".

**Action:** No code change needed in `apply_delta`. The `recently_left` tracking is working. The issue may be that `recently_left_turns` decays too quickly (default 2 turns at line 562), causing the ghost-detection window to close before T10. Consider increasing the default decay counter or verifying the decay logic in `turn.py` lines 739-747.

**Validation:** Test: remove an NPC and verify it shows up in `recently_left`. Test: verify `recently_left_turns` decay in `turn.py` works correctly.

---

### Tests to write or update
- `tests/test_delta_present_npcs_sticky.py` — ensure implicit absence doesn't delete NPCs.
- `tests/test_delta_recently_left.py` — ensure removed NPCs are tracked.

### REPOMAP and architecture updates
- `docs/REPOMAP/state.md`: clarify present_npcs and recently_left semantics and that absence ≠ removal.

### Risks
1. If any code currently infers cleanup based on absence, this change will increase the number of present NPCs; a quick grep for `present_npcs` updates is needed before implementation.

---

## Implementation — Phase 04: Conditions and pressures

### Files to pull for context
- `ccya/state/delta.py` (`apply_delta` — pc conditions and scene_pressure sections)
- `ccya/state/momentum.py` (for existing condition/pressure interactions)
- `ccya/engine/pressure.py` (`_expire_scene_pressures`, `_purge_scene_pressures`)
- `ccya/engine/turn.py` (condition age pass at lines 631-649, pressure calls at lines 622-628)

### Detailed steps

#### Step 4.1 — Ensure pressure TTL/escalation actually updates state

**ANALYSIS ONLY — implementation deferred to system-cohesion plan Phase 03.**

This step analyzed the pressure TTL logic in `pressure.py` and `turn.py`. The analysis found:
- The pressure pipeline in `turn.py` is correct: `_purge_scene_pressures` (line 622) and `_expire_scene_pressures` (line 628) are called before `apply_delta` (line 705), and `apply_delta` writes `delta.scene_pressure_remove` to `state["scene"]["scene_pressure"]` (lines 360-361).
- Root cause hypothesis: pressures with explicit `max_turns` set to a high value (or `None` with old `turn_added`) may not expire because `effective_age` never reaches `max_turns`.

The system-cohesion plan (`system-cohesion-remediation-20260512t154142z-uufm2ojg.md`) Phase 03 has the implementation steps to audit and fix the write-back path. Execute that plan's Phase 03 for the actual fix.

---

#### Step 4.2 — Align condition TTL with pressure TTL design

**File:** `ccya/engine/turn.py` and `ccya/state/delta.py`

**What:** Conditions already have TTL support via `turns_remaining` (decremented in `turn.py` lines 631-649 and 1241-1257). Pressures have TTL via `max_turns` and `turn_added` in `pressure.py`. The design is consistent: both are temporal and both are decremented/checked in `run_turn` and `run_turn_retry`.

**Why:** `bruised_ribs` persisted all 13 turns; pressures ran long. The design intends both to be temporal.

**Action:** Verify that `bruised_ribs` was added with a finite `turns_remaining` value. If it was added as permanent (`turns_remaining=None`), the issue is in the extraction pipeline, not `apply_delta`. If it had a finite TTL, verify the decrement logic in `turn.py` lines 631-649 is working correctly.

**Code Snippet** — Condition aging in `turn.py` (already correct):
```python
# Lines 631-649 in run_turn:
updated_conds = []
for c in (state.get("pc") or {}).get("conditions") or []:
    tr = c.get("turns_remaining")
    if tr is None:
        # Permanent condition — do not age
        updated_conds.append(c)
        continue
    new_remaining = tr - 1
    if new_remaining <= 0:
        append_event(save_dir, {
            "kind": "condition_expired",
            "condition_id": c.get("id"),
            "turn": turn_no,
        })
        # do not append — condition removed
    else:
        updated_conds.append({**c, "turns_remaining": new_remaining})

(state.setdefault("pc", {})["conditions"])[:] = updated_conds
```

**Validation:** Simulate 10 turns with a non-permanent condition and a `building` pressure; assert both are resolved or escalated/removed at or before the configured thresholds.

---

### Tests to write or update
- ~~`tests/test_pressure_ttl.py`~~ — **deferred to system-cohesion plan Phase 03 tests** (`tests/test_pressure.py`).
- `tests/test_condition_and_pressure_coexist.py` — create states with both and ensure they evolve as expected over multiple apply_delta + run_turn cycles.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` and `docs/REPOMAP/state.md`: clarify TTL behavior for conditions. Pressure TTL behavior is documented by the system-cohesion plan.

### Risks
1. Tightening TTL behavior may shorten some narrative arcs compared to existing packs; coordinate with design expectations before changing defaults.
2. If pressures are already tuned in `EngineConfig`, code changes should respect the configured thresholds and not hard-code any new values.

---

## Ambiguities requiring resolution before execution

1. Whether any code currently depends on zero-amount inventory items remaining in state. If so, that must be refactored before cleaning up zero-amount entries. (Already handled: `apply_delta` removes zero-amount items.)
2. ~~Whether quest reopen flows are intended (completed → active) for any pack.~~ **Resolved by mechanical plan Phase 03:** no quest reopen flow exists in the codebase. `status` is only set to `"active"`, `"completed"`, or `"failed"`.
3. Exact semantics of `recently_left` — is it just observability, or does any logic use it? Confirm in `ccya/engine/` and `ccya/server/`. (Used in `turn.py` for NPC bio loading and `recently_left_turns` decay.)
4. Current pressure TTL values and whether they've been tuned in production configs; ensure code matches config, not hard-coded defaults. (Pressure TTL implementation is handled by system-cohesion plan Phase 03.)
