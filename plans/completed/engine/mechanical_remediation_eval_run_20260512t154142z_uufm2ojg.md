# Mechanical Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`completed`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Delta validation hardening | Clamp overdraw and zero-balance removes; strip fallback message before narrative delivery |
| 02 | Ghost NPC prevention | Enforce absence ≠ departure rule in engine dedup; add npc_remove guard in extraction post-processing |
| 03 | Quest lifecycle correctness | Prevent completed-quest re-emission from colliding with engine auto-close; fix auto-close vs dedup contradiction in apply_delta |
| 04 | Condition TTL enforcement | Wire turns_remaining into Condition at seed/add time; engine already processes age pass — ensure it fires on all code paths |
| 05 | Momentum observability | Surface momentum delta in per-turn diff output and events.jsonl scope key |

## Objective
Five confirmed mechanical failures were identified across a 13-turn eval run. Delta validation allowed a zero-balance inventory remove through at T9 and an invented-item remove at T13, both causing engine rejections that leaked fallback messages into the narrative stream. The scene extractor falsely removed NPCs at T7 (they never left), then re-added them as fresh entries at T10, creating ghost NPCs. The progress extractor re-emitted completed quests (`settle_the_debt`, `deliver_the_ledger`) as active after close, causing ID collisions that blocked auto-close. `bruised_ribs` persisted all 13 turns with no TTL mechanism. Momentum values were updating correctly per-turn but were never surfaced in the structured diff output or events, making them invisible to the eval checker and to operators debugging a run.

## Non-goals
- Prompt text changes for rules, narrate, extract_state, extract_progress, extract_scene, or compactor prompts — those are covered in the prompt-quality remediation plan.
- Auto-checker fixes (NPC name tokenizer false positives, pressure directive timing) — covered in the eval remediation plan.
- Design-level changes to pressure TTL, beat variety, or pacing — covered in the system-cohesion remediation plan.
- Any change to `llm_client.py`, `server/`, or `pack.py`.

---

## Implementation — Phase 01: Delta validation hardening

### Files to pull for context
- `ccya/state/delta.py`
- `ccya/engine/turn.py`
- `ccya/state/inventory.py`
- `ccya/engine/narrate.py` (for fallback message origin — confirm the fallback string)

### Detailed steps

#### Step 1.1 — Clamp zero-balance inventory_remove in `_validate`

**File:** `ccya/engine/turn.py`

**What:** In `_validate(state, delta)` (line 875), when an `inventory_remove` entry's resolved item has `amount == 0`, emit a rejection entry and drop the op from `delta.inventory_remove` before returning. The existing code already catches missing IDs and overdraws; extend it to also catch zero-amount items.

**Why:** A zero-balance remove will always fail `apply_delta`'s guard and produce a delta rejection event, which triggers the engine's fallback routing. Catching it in `_validate` before `apply_delta` runs prevents the rejection event and stops fallback message leakage.

**Code Snippet**
```python
def _validate(state: dict[str, Any], delta: StateDelta) -> list[dict[str, Any]]:
    rejections: list[dict[str, Any]] = []

    inv_list: list[dict[str, Any]] = state.get("inventory", [])
    inv_by_id: dict[str, dict[str, Any]] = {
        str(it.get("id", "")): it for it in inv_list if isinstance(it, dict)
    }
    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_list, rem.id)
        if canonical is None:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "value": rem.id,
                    "reason": f"Inventory item '{rem.id}' does not exist",
                }
            )
            continue
        item = inv_by_id.get(canonical)
        if item and int(item.get("amount") or 0) == 0:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "zero_balance",
                    "value": canonical,
                    "reason": f"Item '{canonical}' has zero balance",
                }
            )
            continue
        if rem.amount is None:
            continue
        try:
            requested = int(rem.amount)
        except (TypeError, ValueError):
            continue
        if requested <= 0:
            continue
        current = int(inv_by_id.get(canonical, {}).get("amount") or 1)
        if requested > current:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "warn_overdraw",
                    "value": canonical,
                    "requested": requested,
                    "current": current,
                    "reason": (
                        f"Over-draw on '{canonical}': requested {requested} but stack is {current}. "
                        "apply_delta will clamp to a full-stack remove."
                    ),
                }
            )

    # quest_updates is create-or-update: new quest IDs are allowed (apply_delta creates them).
    # No quest ID validation here.

    return rejections
```

**Validation:** In tests, construct a delta with `inventory_remove=[InventoryRemove(id="credits")]` against a state where `credits.amount == 0`. Assert `_validate` returns one rejection with `kind: "zero_balance"` and that `delta.inventory_remove` is empty.

---

#### Step 1.2 — Strip fallback message before appending to chronicle

**File:** `ccya/engine/turn.py`

**What:** After the fallback is appended to `narrative` (line 700 in `run_turn`, line 1306 in `run_turn_retry`), scan `narrative` for the fallback sentinel string before passing it to `append_chronicle` and to the extraction pipeline. If found, strip the fallback line from the narration and emit a `warn`-level log with `trace_id` and `turn` context keys.

**Why:** The fallback message `*That action didn't resolve as expected. Trace `...` — try rephrasing.*` appears in the narration stream when the engine's routing layer injects it after a delta rejection. It is not narrative prose and must not persist in `chronicle.md` or be fed to extractors, which would extract fictional state changes from it.

**Code Snippet**
```python
_FALLBACK_SENTINEL = "*That action didn't resolve as expected"

def _strip_fallback(narration: str, *, trace_id: str, turn: int) -> str:
    log = logging.getLogger(__name__)
    lines = narration.splitlines()
    clean = [ln for ln in lines if not ln.strip().startswith(_FALLBACK_SENTINEL)]
    if len(clean) < len(lines):
        log.warning(
            "Fallback message stripped from narration",
            extra={"trace_id": trace_id, "turn": turn},
        )
    return "\n".join(clean)
```

Call `_strip_fallback(narrative, trace_id=trace_id, turn=turn_no)` immediately after the fallback is appended (line 700 in `run_turn`, line 1306 in `run_turn_retry`), before `append_chronicle` and before the event payload is assembled.

**Validation:** Unit test: pass a narration string containing the sentinel on its own line. Assert the returned string does not contain the sentinel and that a WARNING was logged.

---

### Tests to write or update
- `tests/test_turn_validate.py` (new or extend existing) — test `_validate` with zero-balance remove: assert rejection + delta mutation.
- `tests/test_strip_fallback.py` (new) — test `_strip_fallback` with sentinel present, absent, mid-line (should NOT strip mid-line occurrences — full-line only).

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — add `_strip_fallback(narration, *, trace_id, turn) -> str` to turn.py internal functions section. Update `_validate` entry to note zero-balance rejection.

### Risks
1. `_FALLBACK_SENTINEL` string may change across server versions. Mitigation: define it as a module-level constant and add a comment linking to the routing layer that generates it.
2. Stripping mid-narration (not line-start) would silently delete legitimate prose. Mitigation: only match lines where the stripped line *starts with* the sentinel, not contains it.

---

## Implementation — Phase 02: Ghost NPC prevention

### Files to pull for context
- `ccya/engine/extraction.py` (focus: `_run_extraction_pipeline`, `_dedup_compendium_add`, post-processing block)
- `ccya/state/delta.py` (`apply_delta` — present_npcs delta section)
- `ccya/models.py` (`SceneExtractResult` — fields `npc_add`, `npc_remove`, `npc_update`)

### Detailed steps

#### Step 2.1 — Add post-extraction npc_remove guard in extraction pipeline

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, after the scene extractor returns `scene_result` (around line 458), call `_check_npc_ghost_cycle(scene_result, state, trace_id=trace_id, turn_no=turn_no)` to scan `scene_result.npc_remove` and `scene_result.npc_add` for same-turn remove+add cycles. For each ID in both lists, log a `GHOST_NPC_CYCLE` warning and drop both ops. If the ID is being removed but also appears in `state["scene"]["recently_left"]` from the prior turn, allow the remove.

**Why:** The primary ghost NPC failure mode was: extractor removes NPC at T7 without narrative justification → narration at T10 re-introduces them → state adds them back as new. The guard does not fully prevent an unjustified remove (that requires a prompt fix), but it does prevent the re-add from creating a phantom when the original NPC ID is already in the compendium.

**Code Snippet**
```python
def _check_npc_ghost_cycle(
    scene_result: SceneExtractResult,
    state: dict[str, Any],
    *,
    trace_id: str,
    turn_no: int,
) -> SceneExtractResult:
    log = logging.getLogger("ccya.engine")
    remove_ids = {op.id for op in (scene_result.npc_remove or [])}
    add_ids = {op.id for op in (scene_result.npc_add or [])}
    cycle_ids = remove_ids & add_ids
    if cycle_ids:
        log.warning(
            "npc_remove/npc_add cycle detected — dropping both ops for IDs",
            extra={"trace_id": trace_id, "turn": turn_no, "ids": list(cycle_ids)},
        )
        scene_result = scene_result.model_copy(
            update={
                "npc_remove": [op for op in (scene_result.npc_remove or []) if op.id not in cycle_ids],
                "npc_add": [op for op in (scene_result.npc_add or []) if op.id not in cycle_ids],
            }
        )
    return scene_result
```

Call `_check_npc_ghost_cycle(scene_result, state, trace_id=trace_id, turn_no=turn_no)` immediately after the scene extractor call returns (line 458 in `extraction.py`), before the dedup blocks and before merging into `StateDelta`.

**Validation:** Unit test: construct a `SceneExtractResult` with `npc_remove=[NpcRemove(id="tough_a")]` and `npc_add=[NpcAdd(id="tough_a", notes="")]`. Assert both are dropped from the result and a WARNING is logged.

---

#### Step 2.2 — Log unjustified npc_remove for observability

**File:** `ccya/engine/extraction.py`

**What:** For any `npc_remove` op that survives the cycle check, log at DEBUG level with `trace_id`, `turn`, and `npc_id`. This does not prevent the remove — that requires the prompt fix — but makes the event visible in structured logs so it appears in eval traces.

**Code Snippet**
```python
log = logging.getLogger("ccya.engine")
for op in (scene_result.npc_remove or []):
    log.debug(
        "npc_remove emitted",
        extra={"trace_id": trace_id, "turn": turn_no, "npc_id": op.id},
    )
```

**Validation:** Check that `npc_remove` events appear in the JSONL log during eval replay with the correct `trace_id` and `turn` values.

---

### Tests to write or update
- `tests/test_extraction_npc.py` (new) — test `_check_npc_ghost_cycle` with remove+add cycle, remove-only, add-only.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — add `_check_npc_ghost_cycle(scene_result, state, *, trace_id, turn_no) -> SceneExtractResult` to extraction.py internal functions.

### Risks
1. Cycle detection only catches same-turn remove+add. A remove at T7 followed by add at T10 is not caught here — that requires the prompt fix (absence ≠ departure rule). Mitigation: log is sufficient for engine-side observability; the prompt fix is the correct long-term solution.
2. `scene_result` fields are confirmed: `npc_remove: list[NpcRemove]`, `npc_add: list[NpcAdd]`, `npc_update: list[NpcUpdate]` — all have `.id` attribute.

---

## Implementation — Phase 03: Quest lifecycle correctness

### Files to pull for context
- `ccya/state/delta.py` (`apply_delta` — quest upsert section, auto-complete logic via `_auto_complete_quest`)
- `ccya/engine/extraction.py` (`_run_extraction_pipeline` post-processing)
- `ccya/models.py` (`ProgressExtractResult`, `QuestUpdate` fields)

### Detailed steps

#### Step 3.1 — Guard against re-emitting completed quests in `apply_delta`

**File:** `ccya/state/delta.py`

**What:** In `apply_delta`, in the quest upsert loop (line 225), before upserting a `QuestUpdate`, check whether the quest already exists in `state["quests"]` with `status == "completed"` or `status == "failed"`. If so, skip the upsert entirely and emit a structured log warning. Do not raise — a completed quest being re-emitted as active is a prompt defect, not an engine error.

**Why:** The progress extractor re-emits `settle_the_debt` at T2 and `deliver_the_ledger` at T7 with `status: active` after they completed. `apply_delta`'s upsert logic currently processes these as legitimate updates, reverting the quest to active and blocking the auto-close signal the engine already fired.

**Code Snippet**
```python
_log = logging.getLogger("ccya.state")

for qu in delta.quest_updates:
    existing = next(
        (q for q in state.get("quests", []) if q["id"] == qu.id),
        None,
    )
    if existing and existing.get("status") in ("completed", "failed"):
        _log.warning(
            "Skipping quest update: quest already in terminal state",
            extra={
                "quest_id": qu.id,
                "existing_status": existing["status"],
                "proposed_status": qu.status,
            },
        )
        continue
    # ... existing upsert logic ...
```

**Validation:** Unit test: apply a delta with `quest_updates=[QuestUpdate(id="settle_the_debt", status="active")]` against a state where `settle_the_debt.status == "completed"`. Assert the quest remains `completed` and a WARNING was logged.

---

#### Step 3.2 — Clarify auto-close trigger path in `apply_delta`

**File:** `ccya/state/delta.py`

**What:** Confirm and document the exact condition under which `apply_delta` auto-closes a quest. The auto-close is implemented via `_auto_complete_quest()` (line 210) which checks `q.get("status") == "active"` and `all(o.get("done") for o in q.get("objectives", []))`, then sets `q["status"] = "completed"`. This runs at line 298 after all quest updates are processed. The dedup guard in Step 3.1 blocks re-emission on subsequent turns. Add a comment block in `apply_delta` documenting this two-turn contract explicitly.

**Why:** The confusion in the model arises from the rules appearing contradictory. Making the engine's contract explicit in code comments prevents future changes from breaking the two-turn flow.

**Code Snippet**
```python
# Quest auto-close contract (two-turn flow):
# Turn N (completion turn): progress extractor emits quest with all objectives done,
#   status="active". apply_delta's upsert loop applies the update, then
#   _auto_complete_quest() (line 298) sees all objectives done → sets status="completed".
# Turn N+1 onward: quest.status == "completed" in state. apply_delta's terminal-state
#   guard (Step 3.1 above) will skip any further updates. The progress extractor prompt must
#   not re-emit completed quests; this guard is the engine-side safety net.
```

**Validation:** Read the existing auto-close logic in `apply_delta` and confirm the comment accurately describes the current code path. The auto-close exists at line 298 via `_auto_complete_quest(q)`.

---

### Tests to write or update
- `tests/test_delta_quest.py` (new or extend) — test that a delta with a `completed`-status quest update is skipped and warning is logged. Test that a delta with all objectives done auto-closes the quest on the same apply.

### REPOMAP and architecture updates
- `docs/REPOMAP/state.md` — update `apply_delta` entry to note terminal-state guard for quest upserts.

### Risks
1. `apply_delta` does implement auto-close via `_auto_complete_quest()` at line 298 — confirmed in code.
2. The terminal-state guard could block legitimate quest reopen flows. **No quest reopen flow exists in the codebase** — `status` is only set to `"active"`, `"completed"`, or `"failed"`; there is no reopen mechanism. The guard is safe as-is.

---

## Implementation — Phase 04: Condition TTL enforcement

### Files to pull for context
- `ccya/engine/turn.py` (condition age pass block — lines 631-649 in `run_turn`, lines 1241-1257 in `run_turn_retry`)
- `ccya/state/delta.py` (`apply_delta` — condition add section, lines 311-321)
- `ccya/models.py` (`Condition`, `ConditionAdd` — `turns_remaining: int | None = None`, no `permanent` field)

### Detailed steps

#### Step 4.1 — Confirm condition age pass fires on `run_turn_retry` path

**File:** `ccya/engine/turn.py`

**What:** The condition age pass exists in both `run_turn` (lines 631-649) and `run_turn_retry` (lines 1241-1257). **This step is a no-op** — both functions already have the identical age pass block that decrements `turns_remaining`, removes expired conditions, and logs `condition_expired` events.

**Why:** `bruised_ribs` persisted 13 turns. If it was set with `turns_remaining=None` (permanent), no TTL is possible without a prompt fix. But the age pass is confirmed present on both code paths.

**Validation:** Confirmed: `run_turn` age pass at lines 631-649, `run_turn_retry` age pass at lines 1241-1257. Both are functionally identical.

---

#### Step 4.2 — Set default `turns_remaining` on condition add

**File:** `ccya/state/delta.py`

**What:** In `apply_delta`'s condition add section (lines 311-321), if a new `Condition` is added without a `turns_remaining` value (i.e., `None`), apply a default TTL. The `Condition` Pydantic model has `turns_remaining: int | None = None` — there is no `permanent` field. `turns_remaining: None` is the permanent sentinel. For new conditions where `turns_remaining` is `None`, stamp a default TTL of 10 turns.

**Why:** `bruised_ribs` was seeded with no TTL and persisted the entire run. The prompt fix will add a TTL instruction; the engine-side default ensures that even if the prompt omits `turns_remaining`, the condition does not persist indefinitely by default.

**Code Snippet**
```python
DEFAULT_CONDITION_TTL = 10

for ca in delta.pc_condition_add:
    cid = ca.id
    if not cid or cid in existing_ids:
        continue
    cond_dict = {
        "id": cid,
        "label": ca.label,
        "description": ca.description,
        "added_turn": current_turn,
    }
    if ca.turns_remaining is not None:
        cond_dict["turns_remaining"] = ca.turns_remaining
    else:
        cond_dict["turns_remaining"] = DEFAULT_CONDITION_TTL
    existing_conds.append(cond_dict)
    existing_ids.add(cid)
```

**Validation:** Unit test: add a condition with `turns_remaining=None`. Assert it is stamped with `DEFAULT_CONDITION_TTL` (10). Add a condition with `turns_remaining=5`. Assert it retains the explicit value.

---

### Tests to write or update
- `tests/test_condition_ttl.py` (new) — test default TTL stamping on add, test age pass expiry, test `turns_remaining=None` permanent condition is not decremented.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — note that `run_turn_retry` already includes condition age pass (no change needed).
- `docs/REPOMAP/state.md` — update `apply_delta` entry to note default TTL stamping for conditions.

### Risks
1. Seeds that explicitly set conditions without `turns_remaining` (treating them as permanent) will now get a 10-turn TTL. This is a behavior change for existing saves. Mitigation: run `_migrate_state` to add `turns_remaining: null` to any existing condition that has no `turns_remaining` field AND is older than 5 turns (heuristic for "was intended as permanent").
2. The `Condition` model does NOT have a `permanent` field — `turns_remaining: None` is the sole permanent sentinel. Default TTL stamping applies when `turns_remaining` is `None` on new adds.

---

## Implementation — Phase 05: Momentum observability

### Files to pull for context
- `ccya/state/momentum.py` (`apply_momentum(state, band)`)
- `ccya/engine/turn.py` (where `apply_momentum` is called at line 357, and `summarize_changes` at line 750)
- `ccya/engine/changes.py` (`summarize_changes`, `format_change_lines`)
- `ccya/state/chronicle.py` (`append_event`)

### Detailed steps

#### Step 5.1 — Include momentum in `summarize_changes` diff

**File:** `ccya/engine/changes.py`

**What:** In `summarize_changes(pre, post, _applied, rejected)` (line 108), add a momentum diff. If `pre["pc"]["momentum"] != post["pc"]["momentum"]`, include a `momentum` key in the returned dict: `{"before": int, "after": int, "delta": int}`. `format_change_lines` should render this as a line: `⚡ Momentum {before:+d} → {after:+d}` when delta is nonzero.

**Why:** `summarize_changes` is the source of the per-turn diff surfaced in the UI and in eval telemetry. Momentum was updating correctly (confirmed by the Qwen judge table) but was invisible in diffs. The eval auto-checker flagged momentum observability as a gap because no `momentum` field appeared in any turn's diff output.

**Code Snippet**
```python
def summarize_changes(
    pre: dict[str, Any],
    post: dict[str, Any],
    _applied: dict[str, Any],
    rejected: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    inventory: list[dict[str, Any]] = []
    player: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []
    quests: list[dict[str, Any]] = []
    momentum: list[dict[str, Any]] = []

    # ... existing inventory, player, facts, quests diffs ...

    pre_momentum = pre.get("pc", {}).get("momentum", 0)
    post_momentum = post.get("pc", {}).get("momentum", 0)
    if pre_momentum != post_momentum:
        momentum.append({
            "kind": "momentum_changed",
            "before": pre_momentum,
            "after": post_momentum,
            "delta": post_momentum - pre_momentum,
        })

    return {"inventory": inventory, "player": player, "facts": facts, "quests": quests, "momentum": momentum}
```

```python
# In format_change_lines, add after the quests loop:
for row in ch.get("momentum") or []:
    if not isinstance(row, dict):
        continue
    k = row.get("kind")
    if k == "momentum_changed":
        b, a = row.get("before", 0), row.get("after", 0)
        lines.append(f"⚡ Momentum {b:+d} → {a:+d}")
```

**Validation:** Unit test: call `summarize_changes` with `pre.pc.momentum = -1` and `post.pc.momentum = 1`. Assert `changes["momentum"]` contains the momentum entry with `delta: 2`. Assert `format_change_lines` includes the momentum line.

---

#### Step 5.2 — Emit momentum in events.jsonl per turn

**File:** `ccya/engine/turn.py`

**What:** `apply_momentum(state, outcome.band)` is called at line 357 in `run_turn` (after rules resolution). Capture `momentum_before` and `momentum_after` around this call and add them to the event payload assembled at lines 781-812. In `run_turn_retry`, `apply_momentum` is NOT called (rules phase is skipped), so no momentum fields are needed there.

**Why:** The eval checker reads `events.jsonl` to populate the momentum table. If momentum is not in the event, the checker cannot validate the momentum arc. This was the root cause of the `(no momentum field)` readout in the eval checker.

**Code Snippet**
```python
# In run_turn, around line 357:
if outcome.rolled:
    momentum_before = state.get("pc", {}).get("momentum", 0)
    apply_momentum(state, outcome.band)
    momentum_after = state.get("pc", {}).get("momentum", 0)
    # ... existing outcome event fields ...
    rules_event["momentum_before"] = momentum_before
    rules_event["momentum_after"] = momentum_after
    rules_event["momentum_delta"] = momentum_after - momentum_before
```

**Validation:** Run a single eval turn with a `fail` band. Assert `events.jsonl` last event contains `momentum_before`, `momentum_after`, and `momentum_delta` keys with correct values in the `rules` sub-object.

---

### Tests to write or update
- `tests/test_changes.py` (new or extend) — test `summarize_changes` with momentum change; test no momentum key when unchanged; test `format_change_lines` momentum rendering.
- `tests/test_momentum_event.py` (new) — use FakeLLM to run a single turn with a known band; assert the emitted event contains the three momentum fields in `rules`.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — update `summarize_changes` and `format_change_lines` entries to note momentum diff. Update `run_turn` entry to note momentum event fields in `rules`.
- `docs/REPOMAP/state.md` — update `apply_momentum` entry to note that callers are expected to capture before/after for event logging.

### Risks
1. `apply_momentum` is called at line 357 in `run_turn`, which is BEFORE `state_pre_apply` is captured at line 686. This means `state_pre_apply` already includes the rules-phase momentum change. The momentum fields in `rules_event` capture the delta from the rules-phase `apply_momentum` call, which is the correct observable.
2. `run_turn_retry` does NOT call `apply_momentum` (rules phase is skipped), so no momentum fields are emitted in retry events. This is acceptable since the rules outcome is fixed.
3. The `changes` dict structure is consumed downstream (UI panel, SSE events). Adding a new `momentum` key is additive and should not break consumers.

---

## Ambiguities requiring resolution before execution

1. **Phase 02:** `SceneExtractResult` fields confirmed in `ccya/models.py`: `npc_add: list[NpcAdd]`, `npc_remove: list[NpcRemove]`, `npc_update: list[NpcUpdate]`. All have `.id` attribute.

2. **Phase 03, Q1:** `apply_delta` DOES contain auto-close logic via `_auto_complete_quest()` at line 298 in `ccya/state/delta.py`.

3. **Phase 03, Q2:** No quest reopen flow exists in the codebase. `status` is only set to `"active"`, `"completed"`, or `"failed"`; there is no reopen mechanism.

4. **Phase 04:** The `Condition` Pydantic model does NOT have a `permanent` field. `turns_remaining: None` is the sole permanent sentinel.

5. **Phase 04:** `run_turn_retry` already includes the condition age pass (lines 1241-1257). Step 4.1 is a no-op.
