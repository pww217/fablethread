# Mechanical Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`open`

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

**What:** In `_validate(state, delta)`, when an `inventory_remove` entry's resolved item has `amount == 0` (or the ID does not exist), instead of emitting a warning-and-proceed, emit a rejection entry and drop the op from `delta.inventory_remove` before returning. The existing code already catches missing IDs; extend it to also catch zero-amount items.

**Why:** A zero-balance remove will always fail `apply_delta`'s guard and produce a delta rejection event, which triggers the engine's fallback routing. Catching it in `_validate` before `apply_delta` runs prevents the rejection event and stops fallback message leakage.

**Code Snippet**
```python
def _validate(state: dict, delta: StateDelta) -> list[dict]:
    rejections: list[dict] = []
    inventory = state.get("inventory", [])
    id_to_item = {item["id"]: item for item in inventory}

    kept_removes: list = []
    for op in delta.inventory_remove:
        raw_id = op.id if hasattr(op, "id") else op.get("id", "")
        resolved = resolve_inventory_remove_target(inventory, raw_id)
        if resolved is None:
            rejections.append({
                "op": "inventory_remove",
                "id": raw_id,
                "reason": "item_not_found",
            })
            continue
        item = id_to_item.get(resolved)
        if item is not None and item.get("amount", 0) == 0:
            rejections.append({
                "op": "inventory_remove",
                "id": raw_id,
                "reason": "zero_balance",
            })
            continue
        kept_removes.append(op)

    delta.inventory_remove = kept_removes
    return rejections
```

**Validation:** In tests, construct a delta with `inventory_remove=[{id: "credits"}]` against a state where `credits.amount == 0`. Assert `_validate` returns one rejection with `reason: "zero_balance"` and that `delta.inventory_remove` is empty.

---

#### Step 1.2 — Strip fallback message before appending to chronicle

**File:** `ccya/engine/turn.py`

**What:** After the narrate streaming call completes and the full narration string is assembled, scan it for the fallback sentinel string before passing it to `append_chronicle` and to the extraction pipeline. If found, strip the fallback line from the narration and emit a `warn`-level log with `trace_id` and `turn` context keys.

**Why:** The fallback message `*That action didn't resolve as expected...*` appears in the narration stream when the engine's routing layer injects it after a delta rejection. It is not narrative prose and must not persist in `chronicle.md` or be fed to extractors, which would extract fictional state changes from it.

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

Call `_strip_fallback(narration, trace_id=trace_id, turn=turn_no)` immediately after the narrate stream is assembled, before `append_chronicle` and before `_run_extraction_pipeline`.

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
- `ccya/engine/extraction.py` (`_scene_npc_roster`)

### Detailed steps

#### Step 2.1 — Add post-extraction npc_remove guard in extraction pipeline

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, after the scene extractor returns `scene_result`, scan `scene_result.npc_remove` (or equivalent field) for IDs. For each ID in `npc_remove`, verify that the NPC's ID does NOT appear in `state["scene"]["present_npcs"]` without explicit narrative evidence. Since we cannot re-read the narration at this point without cost, apply a looser guard: if an `npc_add` for the same ID also appears in the same delta (i.e., remove + add in the same turn), log a `GHOST_NPC_CYCLE` warning and drop both ops. If the ID is being removed but also appears in `recently_left` from the prior turn, allow it. Otherwise allow the remove — but log it so the eval checker can surface it.

**Why:** The primary ghost NPC failure mode was: extractor removes NPC at T7 without narrative justification → narration at T10 re-introduces them → state adds them back as new. The guard does not fully prevent an unjustified remove (that requires a prompt fix), but it does prevent the re-add from creating a phantom when the original NPC ID is already in the compendium.

**Code Snippet**
```python
def _check_npc_ghost_cycle(
    scene_result: SceneExtractResult,
    *,
    trace_id: str,
    turn_no: int,
) -> SceneExtractResult:
    log = logging.getLogger(__name__)
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

Call `_check_npc_ghost_cycle(scene_result, trace_id=trace_id, turn_no=turn_no)` immediately after the scene extractor call returns, before merging into `StateDelta`.

**Validation:** Unit test: construct a `SceneExtractResult` with `npc_remove=[{id: "tough_a"}]` and `npc_add=[{id: "tough_a", ...}]`. Assert both are dropped from the result and a WARNING is logged.

---

#### Step 2.2 — Log unjustified npc_remove for observability

**File:** `ccya/engine/extraction.py`

**What:** For any `npc_remove` op that survives the cycle check, log at DEBUG level with `trace_id`, `turn`, and `npc_id`. This does not prevent the remove — that requires the prompt fix — but makes the event visible in structured logs so it appears in eval traces.

**Code Snippet**
```python
log = logging.getLogger(__name__)
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
- `docs/REPOMAP/engine.md` — add `_check_npc_ghost_cycle(scene_result, *, trace_id, turn_no) -> SceneExtractResult` to extraction.py internal functions.

### Risks
1. Cycle detection only catches same-turn remove+add. A remove at T7 followed by add at T10 is not caught here — that requires the prompt fix (absence ≠ departure rule). Mitigation: log is sufficient for engine-side observability; the prompt fix is the correct long-term solution.
2. `scene_result` may use a different field name for the remove list depending on model version. Mitigation: read the actual `SceneExtractResult` model fields from `ccya/models.py` before implementing — do not assume the field name.

**Ambiguities requiring resolution before execution:**
1. What is the exact field name on `SceneExtractResult` for NPC removes? The REPOMAP says `npc_remove` but the model definition must be confirmed in `ccya/models.py`. Options: A) `npc_remove` (list of NpcRemoveOp), B) another name. **Read `ccya/models.py` before implementing.**

---

## Implementation — Phase 03: Quest lifecycle correctness

### Files to pull for context
- `ccya/state/delta.py` (`apply_delta` — quest upsert section, auto-complete logic)
- `ccya/engine/extraction.py` (`_run_extraction_pipeline` post-processing)
- `ccya/models.py` (`ProgressExtractResult`, `QuestUpdate` fields)

### Detailed steps

#### Step 3.1 — Guard against re-emitting completed quests in `apply_delta`

**File:** `ccya/state/delta.py`

**What:** In `apply_delta`, in the quest upsert loop, before upserting a `QuestUpdate`, check whether the quest already exists in `state["quests"]` with `status == "completed"` or `status == "failed"`. If so, skip the upsert entirely and emit a structured log warning. Do not raise — a completed quest being re-emitted as active is a prompt defect, not an engine error.

**Why:** The progress extractor re-emits `settle_the_debt` at T2 and `deliver_the_ledger` at T7 with `status: active` after they completed. `apply_delta`'s upsert logic currently processes these as legitimate updates, reverting the quest to active and blocking the auto-close signal the engine already fired.

**Code Snippet**
```python
log = logging.getLogger(__name__)

for quest_update in (delta.quest_updates or []):
    existing = next(
        (q for q in state.get("quests", []) if q["id"] == quest_update.id),
        None,
    )
    if existing and existing.get("status") in ("completed", "failed"):
        log.warning(
            "Skipping quest update: quest already in terminal state",
            extra={
                "quest_id": quest_update.id,
                "existing_status": existing["status"],
                "proposed_status": quest_update.status,
            },
        )
        continue
    # ... existing upsert logic ...
```

**Validation:** Unit test: apply a delta with `quest_updates=[{id: "settle_the_debt", status: "active", ...}]` against a state where `settle_the_debt.status == "completed"`. Assert the quest remains `completed` and a WARNING was logged.

---

#### Step 3.2 — Clarify auto-close trigger path in `apply_delta`

**File:** `ccya/state/delta.py`

**What:** Confirm and document the exact condition under which `apply_delta` auto-closes a quest. The auto-close rule says "emit quest with all objectives done" to trigger closure; the dedup rule says "don't re-emit completed quests." These are intended to operate on different turns: the *completion turn* emits the quest with all objectives done → `apply_delta` closes it → on subsequent turns the quest is already `completed` so the guard in Step 3.1 blocks any re-emission. Add a comment block in `apply_delta` documenting this two-turn contract explicitly.

**Why:** The confusion in the model arises from the rules appearing contradictory. Making the engine's contract explicit in code comments prevents future changes from breaking the two-turn flow.

**Code Snippet**
```python
# Quest auto-close contract (two-turn flow):
# Turn N (completion turn): progress extractor emits quest with all objectives done,
#   status="active". apply_delta sees all objectives done → sets status="completed".
# Turn N+1 onward: quest.status == "completed" in state. apply_delta's terminal-state
#   guard (see above) will skip any further updates. The progress extractor prompt must
#   not re-emit completed quests; this guard is the engine-side safety net.
```

**Validation:** Read the existing auto-close logic in `apply_delta` and confirm the comment accurately describes the current code path. If the auto-close logic is missing or uses a different trigger condition, surface as an ambiguity before proceeding.

---

### Tests to write or update
- `tests/test_delta_quest.py` (new or extend) — test that a delta with a `completed`-status quest update is skipped and warning is logged. Test that a delta with all objectives done auto-closes the quest on the same apply.

### REPOMAP and architecture updates
- `docs/REPOMAP/state.md` — update `apply_delta` entry to note terminal-state guard for quest upserts.

### Risks
1. If `apply_delta` does not currently implement auto-close (the eval suggests it may be prompt-only), the auto-close guard in Step 3.2 will reference nonexistent logic. Mitigation: read `ccya/state/delta.py` fully before implementing — confirm auto-close exists and its exact trigger.
2. The terminal-state guard could block legitimate quest reopen flows (e.g., a quest failing then being reactivated). If the codebase has such flows, the guard needs a `reopen` allowlist. Options: A) never allow reopen from terminal state, B) allow reopen only if the delta explicitly sets `status == "active"` and the update includes a non-empty `reopen_reason` field. **Confirm with the user before implementing if reopen flows exist.**

**Ambiguities requiring resolution before execution:**
1. Does `apply_delta` currently implement quest auto-close, or is auto-close solely a side effect of the progress extractor emitting all-done objectives? Options: A) `apply_delta` has auto-close logic, B) auto-close is handled engine-side in `turn.py` after delta application, C) it is not implemented and only expected via prompt. **Read `ccya/state/delta.py` before implementing.**
2. Is there a legitimate quest reopen flow anywhere in the codebase? Options: A) no, B) yes. **Search `ccya/` for `status.*active` or `reopen` patterns if unclear.**

---

## Implementation — Phase 04: Condition TTL enforcement

### Files to pull for context
- `ccya/engine/turn.py` (condition age pass block — already referenced in REPOMAP)
- `ccya/state/delta.py` (`apply_delta` — condition add section, `Condition` model stamping)
- `ccya/models.py` (`Condition` model — confirm `turns_remaining` field exists)

### Detailed steps

#### Step 4.1 — Confirm condition age pass fires on `run_turn_retry` path

**File:** `ccya/engine/turn.py`

**What:** The REPOMAP documents a condition age pass that runs after delta application in `run_turn`. Verify it also runs in `run_turn_retry`. If `run_turn_retry` skips the age pass, add the same block (decrement `turns_remaining`, remove expired conditions, log `condition_expired` event).

**Why:** `bruised_ribs` persisted 13 turns. If it was set with `turns_remaining=None` (permanent), no TTL is possible without a prompt fix. But if the age pass is being skipped on retry paths, a condition with a finite `turns_remaining` would also persist indefinitely.

**Code Snippet**
```python
# In run_turn_retry, after apply_delta, add the same age pass as run_turn:
conditions = state.get("pc", {}).get("conditions", [])
surviving = []
for cond in conditions:
    tr = cond.get("turns_remaining")
    if tr is None:
        surviving.append(cond)
        continue
    tr -= 1
    if tr <= 0:
        log.info(
            "Condition expired",
            extra={"condition_id": cond["id"], "turn": turn_no},
        )
        append_event(save_dir, {"type": "condition_expired", "id": cond["id"], "turn": turn_no})
    else:
        cond["turns_remaining"] = tr
        surviving.append(cond)
state["pc"]["conditions"] = surviving
```

**Validation:** Confirm the age pass block is identical in `run_turn` and `run_turn_retry`. If it is already present in both, this step is a no-op — document that fact and proceed.

---

#### Step 4.2 — Set default `turns_remaining` on condition add

**File:** `ccya/state/delta.py`

**What:** In `apply_delta`'s condition add section, if a new `Condition` is added without a `turns_remaining` value (i.e., `None`), apply a configurable default TTL for non-permanent conditions. Conditions that the prompt explicitly marks as permanent (e.g., `turns_remaining: null` or the Pydantic model sentinel) are left as `None`. Conditions added without any `turns_remaining` field get a default of `config.default_condition_ttl_turns` (new config key, default 10).

**Why:** `bruised_ribs` was seeded with no TTL and persisted the entire run. The prompt fix will add a TTL instruction; the engine-side default ensures that even if the prompt omits `turns_remaining`, the condition does not persist indefinitely by default.

**Note:** This step requires a new `EngineConfig` field. Coordinate with whoever makes config changes.

**Code Snippet**
```python
# In apply_delta, condition add section:
DEFAULT_CONDITION_TTL = getattr(config, "default_condition_ttl_turns", 10) if config else 10

for cond_add in (delta.pc_condition_add or []):
    cond_dict = cond_add if isinstance(cond_add, dict) else cond_add.model_dump()
    if cond_dict.get("turns_remaining") is None and not cond_dict.get("permanent", False):
        cond_dict["turns_remaining"] = DEFAULT_CONDITION_TTL
    # ... existing dedup + append logic ...
```

**Validation:** Unit test: add a condition with no `turns_remaining`. Assert it is stamped with `DEFAULT_CONDITION_TTL`. Add a condition with `turns_remaining: null, permanent: true`. Assert it remains `None`.

---

### Tests to write or update
- `tests/test_condition_ttl.py` (new) — test default TTL stamping on add, test age pass expiry, test `turns_remaining=None` permanent condition is not decremented.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — update `run_turn_retry` entry to confirm condition age pass coverage.
- `docs/REPOMAP/state.md` — update `apply_delta` entry to note default TTL stamping.
- `docs/REPOMAP/config.md` — add `default_condition_ttl_turns: int` (default 10) to EngineConfig table.

### Risks
1. Seeds that explicitly set conditions without `turns_remaining` (treating them as permanent) will now get a 10-turn TTL unless `permanent: true` is set. This is a behavior change for existing saves. Mitigation: run `_migrate_state` to add `turns_remaining: null` to any existing condition that has no `turns_remaining` field AND is older than 5 turns (heuristic for "was intended as permanent").
2. The `permanent` field may not exist on the `Condition` Pydantic model. Options: A) use `turns_remaining is None` as the permanent sentinel (current behavior — do not add a `permanent` field), B) add a `permanent` bool to `Condition`. If A, the default TTL stamping must only apply when the value was literally absent from the LLM output (not present as `null`). **Confirm field presence in `ccya/models.py`.**

**Ambiguities requiring resolution before execution:**
1. Does the `Condition` Pydantic model have a `permanent` field, or is `turns_remaining: None` the permanent sentinel? Options: A) `permanent` field exists, B) `None` is the sentinel. **Read `ccya/models.py` before implementing.**

---

## Implementation — Phase 05: Momentum observability

### Files to pull for context
- `ccya/state/momentum.py`
- `ccya/engine/turn.py` (where `apply_momentum` is called and `summarize_changes` runs)
- `ccya/engine/changes.py` (`summarize_changes`, `format_change_lines`)
- `ccya/state/chronicle.py` (`append_event`)

### Detailed steps

#### Step 5.1 — Include momentum in `summarize_changes` diff

**File:** `ccya/engine/changes.py`

**What:** In `summarize_changes(pre, post, applied, rejected)`, add a momentum diff. If `pre["pc"]["momentum"] != post["pc"]["momentum"]`, include a `momentum` key in the returned dict: `{"before": int, "after": int, "delta": int}`. `format_change_lines` should render this as a line: `⚡ Momentum {before:+d} → {after:+d}` when delta is nonzero.

**Why:** `summarize_changes` is the source of the per-turn diff surfaced in the UI and in eval telemetry. Momentum was updating correctly (confirmed by the Qwen judge table) but was invisible in diffs. The eval auto-checker flagged momentum observability as a gap because no `momentum` field appeared in any turn's diff output.

**Code Snippet**
```python
def summarize_changes(pre: dict, post: dict, applied: list, rejected: list) -> dict:
    changes = {}
    # ... existing inventory, player, facts, quests diffs ...

    pre_momentum = pre.get("pc", {}).get("momentum", 0)
    post_momentum = post.get("pc", {}).get("momentum", 0)
    if pre_momentum != post_momentum:
        changes["momentum"] = {
            "before": pre_momentum,
            "after": post_momentum,
            "delta": post_momentum - pre_momentum,
        }

    return changes
```

```python
# In format_change_lines, add:
if "momentum" in changes:
    m = changes["momentum"]
    lines.append(f"⚡ Momentum {m['before']:+d} → {m['after']:+d}")
```

**Validation:** Unit test: call `summarize_changes` with `pre.pc.momentum = -1` and `post.pc.momentum = 1`. Assert `changes["momentum"] == {"before": -1, "after": 1, "delta": 2}`. Assert `format_change_lines` includes the momentum line.

---

#### Step 5.2 — Emit momentum in events.jsonl per turn

**File:** `ccya/engine/turn.py`

**What:** After `apply_momentum(state, band)` is called, append a momentum field to the turn's event payload in `events.jsonl`. The existing event already captures the turn's `band` and `dice` results — add `momentum_before` and `momentum_after` alongside them.

**Why:** The eval checker reads `events.jsonl` to populate the momentum table. If momentum is not in the event, the checker cannot validate the momentum arc. This was the root cause of the `(no momentum field)` readout in the eval checker.

**Code Snippet**
```python
# In run_turn, after apply_momentum call:
momentum_before = pre_state.get("pc", {}).get("momentum", 0)
# apply_momentum mutates state in place
apply_momentum(state, band)
momentum_after = state.get("pc", {}).get("momentum", 0)

# When appending the turn event:
event_payload["momentum_before"] = momentum_before
event_payload["momentum_after"] = momentum_after
event_payload["momentum_delta"] = momentum_after - momentum_before
```

**Validation:** Run a single eval turn with a `fail` band. Assert `events.jsonl` last event contains `momentum_before`, `momentum_after`, and `momentum_delta` keys with correct values.

---

### Tests to write or update
- `tests/test_changes.py` (new or extend) — test `summarize_changes` with momentum change; test no momentum key when unchanged; test `format_change_lines` momentum rendering.
- `tests/test_momentum_event.py` (new) — use FakeLLM to run a single turn with a known band; assert the emitted event contains the three momentum fields.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — update `summarize_changes` and `format_change_lines` entries to note momentum diff. Update `run_turn` entry to note momentum event fields.
- `docs/REPOMAP/state.md` — update `apply_momentum` entry to note that callers are expected to capture before/after for event logging.

### Risks
1. `pre_state` must be captured before `apply_momentum` mutates state. If `apply_momentum` is called in a context where `pre_state` is already a reference (not a copy), `momentum_before` will read the post-mutation value. Mitigation: capture `momentum_before = state["pc"]["momentum"]` as a scalar before the call — scalars are not mutated in place.
2. The `changes` dict structure is consumed downstream (UI panel, SSE events). Adding a new `momentum` key is additive and should not break consumers, but verify no code does `for k in ("inventory", "player", "facts", "quests"):` exhaustive iteration.

---

## Ambiguities requiring resolution before execution

1. **Phase 02:** What is the exact field name on `SceneExtractResult` for NPC removes and adds? Options: A) `npc_remove` / `npc_add`, B) different names. Read `ccya/models.py` before implementing.

2. **Phase 03, Q1:** Does `apply_delta` contain auto-close logic, or is auto-close implemented elsewhere (or not at all)? Options: A) `apply_delta` has it, B) `turn.py` post-delta, C) absent. Read `ccya/state/delta.py` before implementing.

3. **Phase 03, Q2:** Does a legitimate quest reopen flow exist (completed → active)? Options: A) no, B) yes. If yes, the terminal-state guard needs a reopen allowlist.

4. **Phase 04:** Does the `Condition` Pydantic model have a `permanent` field, or is `turns_remaining: None` the sole permanent sentinel? Read `ccya/models.py` before implementing.

5. **Phase 04:** Does `run_turn_retry` already include the condition age pass? Options: A) yes (no-op), B) no (add it). Read `ccya/engine/turn.py` before implementing — if already present, skip Step 4.1.
