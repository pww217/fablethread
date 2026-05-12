# System Cohesion Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Compactor sanitization completeness | Ensure `_apply_sanitization` closes stale quests, removes zero-amount inventory, removes expired conditions, and removes stale pressures reliably |
| 02 | Scope-gate correctness | Fix silent domain fallback hiding extract skips; ensure `_DEFAULT_DOMAINS` only fires on provably missing scope tag |
| 03 | Pressure TTL write-back | Confirm `_expire_scene_pressures` mutations are written back before state persist; fix avoidance decay triggering on wrong path |
| 04 | Momentum-band coherence | **SUPERSEDED by mechanical plan Phase 05** — mechanical plan already adds `momentum_before/after/delta` to events.jsonl and `summarize_changes`. Skip this phase entirely. |

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

**What:** Read `_apply_sanitization` and `_parse_compact_response`. Confirm that `CompactorSanitizationResult` is only considered a no-op when all five lists (`npc_merge`, `inventory_remove`, `quest_close`, `pressure_remove`, `condition_remove`) are empty or absent. If the current check treats a result with only some populated fields as a no-op, fix it.

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

**What:** After `_apply_sanitization`, emit a `log.info` call with keys: `turn`, `quests_closed`, `inventory_removed`, `npcs_merged`, `pressures_removed`, `conditions_removed`. Use the existing `_log` instance (`logging.getLogger("ccya.engine")`).

**Why:** Sanitization is currently a silent in-place mutation. Without logging, it is impossible to tell from logs whether it ran or was skipped.

**Code Snippet**
```python
# Inside _apply_sanitization, after all mutation loops:
log_ctx = {"turn": state.get("meta", {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "compactor"}
_log.info(
    "compactor sanitization applied",
    extra={
        **log_ctx,
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

**What:** Modify `_split_scope_tail` to return a 3-tuple `(prose, active_domains | None, decided_by: str)` where `decided_by` is one of: `"narrator"` (scope tag present and valid), `"fallback_no_tag"` (no `<scope>` tag found), `"fallback_malformed"` (tag present but invalid JSON/wrong shape). Update both call sites in `run_turn` and `run_turn_retry` to unpack the 3-tuple.

**Why:** The eval judge noted that scope fall-through was masking extraction skips. Without distinguishing the cause, the rate of narrator scope tag failures is invisible. `_DEFAULT_DOMAINS` has 5 domains (not 7 — `_ALL_DOMAINS` has 7).

**Code Snippet**
```python
def _split_scope_tail(text: str) -> tuple[str, list[str] | None, str]:
    """Extract <scope>...</scope> tail, return (prose, active_domains | None, decided_by).

    decided_by: "narrator" | "fallback_no_tag" | "fallback_malformed"
    """
    m = _SCOPE_TAIL_RE.search(text)
    if not m:
        return text, None, "fallback_no_tag"

    prose = (text[:m.start()] + text[m.end():]).rstrip()
    json_str = m.group(1).strip()

    try:
        parsed = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return prose, None, "fallback_malformed"

    if not isinstance(parsed, dict):
        return prose, None, "fallback_malformed"

    raw = parsed.get("active_domains")
    if not isinstance(raw, list):
        return prose, None, "fallback_malformed"

    domains = [d for d in raw if isinstance(d, str) and d in _ALL_DOMAINS]
    return prose, domains, "narrator"
```

Update call sites to unpack 3 values:
```python
# In run_turn (around line 540):
narrative, parsed_domains, scope_decided_by = _split_scope_tail(full_with_tail)
_active_domains = (
    list(parsed_domains) if parsed_domains is not None else list(_DEFAULT_DOMAINS)
)
```

**Validation:** Test `_split_scope_tail` with: (a) clean prose without `<scope>` — verify `decided_by == "fallback_no_tag"`; (b) prose with `<scope>{bad json}</scope>` — verify `decided_by == "fallback_malformed"`; (c) valid scope tag — verify `decided_by == "narrator"`.

---

#### Step 2.2 — Record `decided_by` accurately in events.jsonl scope key

**File:** `ccya/engine/turn.py`

**What:** Add `decided_by` to the `scope` key in the event dict. Currently the scope key is `{"active_domains": _active_domains}`. Update to:

**Code Snippet**
```python
# In run_turn event dict (around line 794):
"scope": {
    "active_domains": _active_domains,
    "decided_by": scope_decided_by,
},
```

Apply the same change in `run_turn_retry` event dict (around line 1394).

**Why:** The eval trace needs this to attribute false-domain-fallback failures correctly. The REPOMAP documents that `events.jsonl` gains a `scope` key with `{active_domains, decided_by, skipped_streams}` — this phase implements the `decided_by` portion.

**Validation:** Run a smoke test and inspect the `scope.decided_by` field in the emitted event.

---

### Tests to write or update
- Add unit tests for `_split_scope_tail` covering all three paths and confirming `decided_by` values.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md`: expand the scope-parsing section to document the three `decided_by` values and the updated `_split_scope_tail` return type.

### Risks
1. `_split_scope_tail` currently returns a 2-tuple. Changing to a 3-tuple requires updating both call sites in `run_turn` and `run_turn_retry`.

---

## Implementation — Phase 03: Pressure TTL write-back

### Files to pull for context
- `ccya/engine/pressure.py` (`_expire_scene_pressures`, `_purge_scene_pressures`)
- `ccya/engine/turn.py` — find the exact call sites for both pressure functions and confirm ordering relative to `save_state`
- `ccya/engine/config.py` (`EngineConfig`) — pressure TTL config fields

### Detailed steps

#### Step 3.1 — Audit write-back path for `_expire_scene_pressures`

**File:** `ccya/engine/pressure.py`

**What:** Confirm that `_expire_scene_pressures` mutates `state["scene"]["scene_pressure"]` directly (not a local copy). The function operates on a local list copy but mutates dict items in-place (urgency, turn_became_immediate, max_turns), and extends `delta.scene_pressure_remove` with removed IDs. `apply_delta` then uses `delta.scene_pressure_remove` to filter the state. This write-back path is correct — no changes needed to `_expire_scene_pressures` itself.

**Why:** The mechanical plan flagged that the condition age pass may be missing from `run_turn_retry`; the same gap likely exists for pressure expiry.

**Validation:** Unit test: create a state with a pressure at `max_turns` exceeded; call `_expire_scene_pressures`; assert `delta.scene_pressure_remove` contains the pressure ID.

---

#### Step 3.2 — Confirm `_expire_scene_pressures` runs on `run_turn_retry` path

**File:** `ccya/engine/turn.py`

**What:** In `run_turn_retry`, `_expire_scene_pressures` is called at line 1238 WITHOUT the `avoidance` parameter (defaults to `False`). In `run_turn`, it is called at line 628 WITH `avoidance=avoidance`. The `run_turn_retry` path does not detect avoidance (it skips Call 0 where avoidance detection lives). This is acceptable — avoidance detection requires player input analysis which `run_turn_retry` doesn't have (it receives `intent.intent` as the input, not the original `user_input`).

**Why:** The mechanical plan flagged that the condition age pass may be missing from `run_turn_retry`; the same gap likely exists for pressure expiry.

**Validation:** Add a test for `run_turn_retry` that starts with an expired pressure; assert it is absent from state after the retry turn.

---

#### Step 3.3 — Confirm avoidance decay only fires when player input triggers avoidance detection

**File:** `ccya/engine/turn.py`

**What:** Avoidance detection currently happens inline in `run_turn` (lines 270-277). The `avoidance` boolean is computed by checking `config.avoidance_keywords` against `user_input.lower()`. This is correct — it only fires when keywords are detected. No `_detect_avoidance` function exists; the detection is inline.

**Code Snippet** (current code, verify it's correct):
```python
# Lines 270-277 in run_turn:
_avoidance_kw = config.avoidance_keywords
_input_lower = (user_input or "").lower()
avoidance = any(kw in _input_lower for kw in _avoidance_kw)
if avoidance:
    _log.debug(
        "pacing: avoidance detected in input",
        extra={"turn": state.get("meta", {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "pacing"},
    )
```

**Validation:** Test with a keyword in `avoidance_keywords` and confirm `_log.debug` fires; test without and confirm it does not.

---

### Tests to write or update
- `tests/test_pressure.py`: add tests confirming `_expire_scene_pressures` populates `delta.scene_pressure_remove` and that pressure mutations survive to state dict after `apply_delta`.
- Add a `run_turn_retry` smoke test that starts with an expired pressure; assert it is absent from state after the retry turn.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` pressure section: document write-back guarantee (mutations via delta) and avoidance flag semantics.

### Risks
1. If pressure mutation was already correct but `save_state` was called before the pressure pass in some code paths, changing order could affect other side effects. Read `run_turn` call ordering carefully before changing anything.

---

## Implementation — Phase 04: Momentum-band coherence

**ABANDONED — superseded by mechanical plan Phase 05.**

The mechanical plan (`mechanical_remediation_eval_run_20260512t154142z_uufm2ojg.md`) already implements:
- Step 5.1: momentum diff in `summarize_changes` / `format_change_lines`
- Step 5.2: `momentum_before`/`momentum_after`/`momentum_delta` in events.jsonl rules event

This phase would duplicate that work with slightly different event shapes (mechanical puts it in `rules_event`, this plan puts it as a top-level `event["momentum"]`). Execute the mechanical plan's momentum phases instead. If additional momentum-band coherence checks are needed (e.g., `check_momentum_band_delta` in universal asserts), add them as a follow-up after mechanical is complete.

---

## Ambiguities requiring resolution before execution

1. Does `_apply_sanitization` currently use `status == "completed"` or another string when closing quests? Read source before Step 1.2. (Confirmed: it uses `status == "completed"` at compactor.py:303.)
2. What is the exact return type of `_split_scope_tail`? Tuple, named tuple, dataclass? Confirm before adding the `decided_by` field in Step 2.2. (Confirmed: returns `tuple[str, list[str] | None]` — a 2-tuple. Must be changed to 3-tuple.)
3. ~~Is `apply_momentum` called inside `apply_delta` or separately in `run_turn`?~~ **Resolved by mechanical plan Phase 05.** Momentum telemetry is handled by the mechanical plan; this phase is abandoned.
4. Does `run_turn_retry` already call `_expire_scene_pressures`? Search before adding a second call. (Confirmed: `run_turn_retry` calls `_expire_scene_pressures` at line 1238 WITHOUT the `avoidance` parameter. This is correct since retry doesn't have original user_input for avoidance detection.)
