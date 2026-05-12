# System Cohesion Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Compactor sanitization completeness | Ensure `_apply_sanitization` closes stale quests, removes zero-amount inventory, removes expired conditions, and removes stale pressures reliably |
| 02 | Scope-gate correctness | Fix silent domain fallback hiding extract skips; ensure `_DEFAULT_DOMAINS` only fires on provably missing scope tag |
| 03 | Pressure TTL write-back | Confirm `_expire_scene_pressures` mutations are written back before state persist; fix avoidance decay triggering on wrong path |
| 04 | Momentum-band coherence | Ensure `apply_momentum` and `check_momentum_band_delta` in universal asserts agree on clamp semantics; add `momentum_before/after/delta` to events.jsonl |

## Objective
Several failures in the eval run pointed not to individual LLM calls but to the engine-level systems that bind them: the compactor silently skipped sanitization when completed quests and stale pressures were present; scope-gate domain fallback masked extraction skips in telemetry; `_expire_scene_pressures` mutations did not survive to the persisted state on all paths; and momentum telemetry was too thin to diagnose band-delta mismatches. This plan addresses each of those integration-seam failures.

## Non-goals
- Prompt-level changes to extractor few-shots or narrator directives — covered in prompt-quality and narrative plans.
- State-level `apply_delta` logic for inventory and quests — covered in state-fidelity plan.
- Eval auto-checker assertion additions — covered in eval-harness plan.
- Pack schema or scenario fixture changes.

---

## Implementation — Phase 01: Compactor sanitization completeness

### Files to pull for context
- `ccya/engine/compactor.py` (`_apply_sanitization`, `_parse_compact_response`, `maybe_compact`)
- `ccya/state/delta.py` (to understand `apply_delta` quest/condition/pressure/inventory APIs — do not duplicate logic here, reuse helpers)
- `docs/REPOMAP/engine.md` (compactor section)
- `tests/test_compactor.py`

### Detailed steps

#### Step 1.1 — Assert `_apply_sanitization` is gated correctly on non-empty content

**File:** `ccya/engine/compactor.py`

**What:** Read `_apply_sanitization` and `_parse_compact_response`. Confirm that `CompactorSanitizationResult` is only considered a no-op when all four lists (`npc_merge`, `inventory_remove`, `quest_close`, `pressure_remove`, `condition_remove`) are empty or absent. If the current check treats a result with only some populated fields as a no-op, fix it.

**Why:** The `_assert_compactor_sanitization_nonzero` universal assert FAILs when `compaction_ran` is True but `sanitization` fields are empty despite completed quests in state — this indicates either the LLM is not emitting sanitization or `_parse_compact_response` is dropping it.

**Code Snippet**
```python
def _sanitization_nonempty(san: CompactorSanitizationResult | None) -> bool:
    if san is None:
        return False
    return bool(
        san.npc_merge
        or san.inventory_remove
        or san.quest_close
        or san.pressure_remove
        or san.condition_remove
    )
```
Use `_sanitization_nonempty(san)` to decide whether `compaction_ran` should be set to True in `maybe_compact`.

**Validation:** Existing `test_compactor.py` sanitization tests should pass. Add a test: compact with a state containing one completed quest and one stale pressure; assert `compaction_ran=True` and the state no longer contains the completed quest.

---

#### Step 1.2 — Make `_apply_sanitization` quest-close robust

**File:** `ccya/engine/compactor.py`

**What:** Verify that `_apply_sanitization`'s quest-close path uses `status == "completed"` (not a string literal that differs from what `apply_delta` writes). If there is any normalization mismatch, align them.

**Why:** If `apply_delta` writes `"completed"` but `_apply_sanitization` compares against `"done"` or `"closed"`, sanitization will silently no-op on completed quests.

**Validation:** Test: call `_apply_sanitization` directly with a state containing `status: "completed"` quests; assert they are removed.

---

#### Step 1.3 — Log sanitization actions with structured keys

**File:** `ccya/engine/compactor.py`

**What:** After `_apply_sanitization`, emit a `logger.info` call with keys: `turn`, `trace_id`, `quests_closed`, `inventory_removed`, `npcs_merged`, `pressures_removed`, `conditions_removed`. Use `logging.getLogger(__name__)`.

**Why:** Sanitization is currently a silent in-place mutation. Without logging, it is impossible to tell from logs whether it ran or was skipped.

**Code Snippet**
```python
log = logging.getLogger(__name__)
# After _apply_sanitization(state, san):
log.info(
    "compactor sanitization applied",
    extra={
        "turn": state.get("meta", {}).get("turn"),
        "quests_closed": len(san.quest_close or []),
        "inventory_removed": len(san.inventory_remove or []),
        "npcs_merged": len(san.npc_merge or []),
        "pressures_removed": len(san.pressure_remove or []),
        "conditions_removed": len(san.condition_remove or []),
    },
)
```

**Validation:** Run compaction in smoke test; check logs contain `compactor sanitization applied`.

---

### Tests to write or update
- `tests/test_compactor.py`: add tests for `_sanitization_nonempty`, quest-close status string alignment, and structured logging output.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` compactor section: document `_sanitization_nonempty` helper and the structured logging contract.

### Risks
1. If `_apply_sanitization` ID allowlist validation silently skips unknown IDs, a compactor response with off-ID quests will appear to succeed but not close anything. The existing allowlist behavior should be verified before assuming sanitization ran.

---

## Implementation — Phase 02: Scope-gate correctness

### Files to pull for context
- `ccya/engine/turn.py` (`_split_scope_tail`, `_DEFAULT_DOMAINS`, `_ALL_DOMAINS`)
- `ccya/engine/extraction.py` (`_run_extraction_pipeline` — how `active_domains` is consumed)
- `ccya/eval/universal_asserts.py` (no assert currently covers false domain fallback; this phase will surface the need)

### Detailed steps

#### Step 2.1 — Distinguish "missing scope tag" from "malformed scope tag" in fallback logging

**File:** `ccya/engine/turn.py`

**What:** When `_split_scope_tail` returns `None` for `active_domains`, log a `WARNING` that distinguishes the two causes: (a) scope tag was truly absent (narrator did not emit one), (b) scope tag was present but malformed JSON. Currently both fall back to `_DEFAULT_DOMAINS` silently.

**Why:** The eval judge noted that scope fall-through was masking extraction skips. Without distinguishing the cause, the rate of narrator scope tag failures is invisible.

**Code Snippet**
```python
# In the fallback block of _split_scope_tail or its call site:
if active_domains is None:
    if "<scope>" in narration_raw:
        log.warning(
            "scope tag present but malformed; falling back to all domains",
            extra={"turn": turn_no, "trace_id": trace_id},
        )
    else:
        log.warning(
            "narrator emitted no scope tag; falling back to all domains",
            extra={"turn": turn_no, "trace_id": trace_id},
        )
    active_domains = list(_DEFAULT_DOMAINS)
```

**Validation:** Test `_split_scope_tail` with: (a) clean prose without `<scope>` — verify warning A is logged; (b) prose with `<scope>{bad json}</scope>` — verify warning B is logged.

---

#### Step 2.2 — Record `decided_by` accurately in events.jsonl scope key

**File:** `ccya/engine/turn.py`

**What:** The `scope` key in `events.jsonl` has a `decided_by` field. Ensure it uses at least three values: `"narrator"` (scope tag present and valid), `"fallback_no_tag"` (no tag emitted), `"fallback_malformed"` (tag present but invalid). Currently it may only distinguish `"narrator"` vs `"fallback"`.

**Why:** The eval trace needs this to attribute false-domain-fallback failures correctly.

**Validation:** Run a smoke test and inspect the `scope.decided_by` field in the emitted event.

---

### Tests to write or update
- Add unit tests for `_split_scope_tail` covering all three paths and confirming `decided_by` values.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md`: expand the scope-parsing section to document the three `decided_by` values.

### Risks
1. If `_split_scope_tail` currently returns a namedtuple or something beyond a bare `list | None`, the call site refactor must match the existing return type.

---

## Implementation — Phase 03: Pressure TTL write-back

### Files to pull for context
- `ccya/engine/pressure.py` (`_expire_scene_pressures`, `_purge_scene_pressures`)
- `ccya/engine/turn.py` — find the exact call sites for both pressure functions and confirm ordering relative to `save_state`
- `ccya/engine/config.py` (`EngineConfig`) — pressure TTL config fields

### Detailed steps

#### Step 3.1 — Audit write-back path for `_expire_scene_pressures`

**File:** `ccya/engine/pressure.py`

**What:** Confirm that `_expire_scene_pressures` mutates `state["scene"]["scene_pressure"]` directly (not a local copy). If the function operates on a local list, reassign it back:

**Code Snippet**
```python
def _expire_scene_pressures(
    state: dict, delta: StateDelta, config: EngineConfig | None = None, avoidance: bool = False
) -> None:
    pressures: list[dict] = state["scene"].get("scene_pressure", [])
    # ... mutation logic ...
    state["scene"]["scene_pressure"] = pressures  # ensure write-back
```

**Validation:** Unit test: create a state with a pressure at `max_turns` exceeded; call `_expire_scene_pressures`; assert the pressure is removed from `state["scene"]["scene_pressure"]`.

---

#### Step 3.2 — Confirm `_expire_scene_pressures` runs on `run_turn_retry` path

**File:** `ccya/engine/turn.py`

**What:** Grep `run_turn_retry` for calls to `_expire_scene_pressures`. If it is missing, add the same call that exists in `run_turn`, in the same relative position (after delta application, before `save_state`).

**Why:** The mechanical plan flagged that the condition age pass may be missing from `run_turn_retry`; the same gap likely exists for pressure expiry.

**Validation:** Add a `run_turn_retry` smoke test that starts with an expired pressure; assert it is absent from state after the retry turn.

---

#### Step 3.3 — Confirm avoidance decay only fires when player input triggers avoidance detection

**File:** `ccya/engine/turn.py`

**What:** Locate `avoidance` detection (keyword check against `config.avoidance_keywords`). Confirm the `avoidance=True` flag is only passed to `_expire_scene_pressures` when that detection fires, not on every turn. Add a log line when avoidance is detected.

**Code Snippet**
```python
avoidance_detected = _detect_avoidance(user_input, config)
if avoidance_detected:
    log.info("avoidance detected", extra={"turn": turn_no, "trace_id": trace_id})
_expire_scene_pressures(state, delta, config=config, avoidance=avoidance_detected)
```

**Validation:** Test with a keyword in `avoidance_keywords` and confirm `log.info` fires; test without and confirm it does not.

---

### Tests to write or update
- `tests/test_pressure_writeback.py`: confirm `_expire_scene_pressures` mutation survives to state dict after call.
- `tests/test_pressure_retry_path.py`: confirm pressure expiry runs on `run_turn_retry`.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` pressure section: document write-back guarantee and avoidance flag semantics.

### Risks
1. If pressure mutation was already correct but `save_state` was called before the pressure pass in some code paths, changing order could affect other side effects. Read `run_turn` call ordering carefully before changing anything.

---

## Implementation — Phase 04: Momentum-band coherence

### Files to pull for context
- `ccya/state/momentum.py` (`apply_momentum`, `MOMENTUM_MIN`, `MOMENTUM_MAX`)
- `ccya/eval/universal_asserts.py` (`check_momentum_band_delta`)
- `ccya/engine/changes.py` (`summarize_changes`, `format_change_lines`)
- `ccya/engine/turn.py` (where `apply_momentum` is called and where events are appended)

### Detailed steps

#### Step 4.1 — Add `momentum_before`, `momentum_after`, `momentum_delta` to events.jsonl

**File:** `ccya/engine/turn.py`

**What:** Before calling `apply_momentum`, capture `momentum_before = state["pc"]["momentum"]`. After `apply_delta` (which calls `apply_momentum`), capture `momentum_after`. Emit both plus `momentum_delta = momentum_after - momentum_before` into the turn event.

**Why:** The eval REPORT currently shows no per-turn momentum telemetry. The `check_momentum_band_delta` universal assert can only flag mismatches it can see; without explicit before/after in the event, debugging requires replaying the trace manually.

**Code Snippet**
```python
momentum_before = state["pc"].get("momentum", 0)
# ... apply_delta ...
momentum_after = state["pc"].get("momentum", 0)
event["momentum"] = {
    "before": momentum_before,
    "after": momentum_after,
    "delta": momentum_after - momentum_before,
    "band": outcome.band,
}
```

**Validation:** Run a smoke test and inspect the emitted event; confirm `momentum.before`, `momentum.after`, `momentum.delta`, `momentum.band` are present.

---

#### Step 4.2 — Add momentum diff to `summarize_changes` and `format_change_lines`

**File:** `ccya/engine/changes.py`

**What:** `summarize_changes(pre, post, applied, rejected)` currently diffs inventory, player facts, quests. Add a `momentum` key to the returned dict that includes `before`, `after`, and `delta`.

**Code Snippet**
```python
def summarize_changes(pre: dict, post: dict, applied: list, rejected: list) -> dict:
    changes = _summarize_applied(applied)
    momentum_before = pre.get("pc", {}).get("momentum", 0)
    momentum_after = post.get("pc", {}).get("momentum", 0)
    changes["momentum"] = {
        "before": momentum_before,
        "after": momentum_after,
        "delta": momentum_after - momentum_before,
    }
    return changes
```

In `format_change_lines`, emit a momentum line only when delta is nonzero:
```python
if changes.get("momentum", {}).get("delta", 0) != 0:
    m = changes["momentum"]
    lines.append(f"📊 Momentum: {m['before']:+d} → {m['after']:+d}")
```

**Validation:** Unit test `summarize_changes` with two states differing by momentum; assert `changes["momentum"]` is correct. Test `format_change_lines` produces the momentum line only on non-zero delta.

---

### Tests to write or update
- `tests/test_changes_momentum.py` — test `summarize_changes` and `format_change_lines` for momentum key.
- Update `test_engine_smoke.py` to assert the emitted event contains a `momentum` block.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` changes.py section: document `momentum` key in `summarize_changes` output.
- `docs/REPOMAP/engine.md` turn.py section: document `momentum` key in emitted events.

### Risks
1. Adding `momentum` to `summarize_changes` output changes the return type shape; any downstream consumers that do `changes["inventory"]` etc. are unaffected, but tests asserting on the exact dict keys will need updating.

---

## Ambiguities requiring resolution before execution

1. Does `_apply_sanitization` currently use `status == "completed"` or another string when closing quests? Read source before Step 1.2.
2. What is the exact return type of `_split_scope_tail`? Tuple, named tuple, dataclass? Confirm before adding the `decided_by` field in Step 2.2.
3. Is `apply_momentum` called inside `apply_delta` or separately in `run_turn`? This determines where `momentum_before` must be captured. Read `ccya/engine/turn.py` before Step 4.1.
4. Does `run_turn_retry` already call `_expire_scene_pressures`? Search before adding a second call.
