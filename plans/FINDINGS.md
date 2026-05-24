# Eval Harness Audit — Findings

Audited across two deep-passes against current engine state (post-commit `0f4af40`). Covers: `ccya/eval/{config,scenario,runner,judge,universal_asserts,report,engine_mirror,redundancy,compaction_signals}`, `ccya/eval/architecture_context.py`, rubrics in `evals/rubrics/`, scenarios in `evals/scenarios/`.

---

## HIGH — Evaluation results will be wrong or incomplete

### H1. Stale field reference: `PacingContext.beat_hint` (scenario)

**File:** `evals/scenarios/full_cycle.py`, line 98
```python
"PacingContext.beat_hint should suggest 'complication' when beat is pending",
```

`beat_hint` was removed in commit `71cffcb`. PacingContext now has only: `directive`, `beat_locked`, `gate`, `summary`. This expects line references a field that no longer exists — the scenario's assertion will never be satisfied by current engine behavior. It is either silently passing (if missing fields are treated as None) or failing in an unobservable way, but it is not testing what it claims to test.

**Fix:** Replace with reference to `PacingContext.directive` or `PacingContext.gate`, depending on the original intent of the assertion.

---

### H2. Hardcoded momentum delta mapping (universal_asserts.py) vs imported constant

**File:** `ccya/eval/universal_asserts.py`, lines 541-548
```python
expected = {
    "crit_success": 2,
    "success": 1,
    "partial": 0,
    "setback": -1,
    "fail": -1,
    "crit_fail": -2,
}.get(band)
```

This dict is duplicated inline rather than importing `engine_mirror.MOMENTUM_DELTA` (which itself imports from `ccya.rules.MOMENTUM_DELTA`). Currently matches rules.py exactly, but if bands or deltas ever change in production code this assertion silently drifts — it would validate against stale expectations and either produce false positives (accepting wrong behavior) or false negatives (flagging correct behavior).

**Fix:** Import the mapping from `engine_mirror.MOMENTUM_DELTA` so assertions always reflect current engine defaults.

---

### H3. NaN propagation in rate normalization (judge.py)

**File:** `ccya/eval/judge.py`, lines 980-981
```python
def _coerce_rate(v: Any) -> float | None:
    f = float(v)               # float('nan') → succeeds, returns NaN!
    return max(0.0, min(1.0, f))  # NaN comparisons are always False — clamp is a no-op
```

`float('nan')` does not raise ValueError; it returns NaN successfully. The clamp `max(0.0, min(1.0, float('nan')))` also returns NaN (NaN comparisons are always False in Python). If an LLM outputs `"state_fidelity_rate: nan"` or YAML parsing produces NaN from a corrupted value, the rate field in scores will be NaN — which could cause downstream report rendering failures (`f"{rate}"` renders as `nan`) or regression detection comparison errors.

**Fix:** Add explicit NaN check before clamping:
```python
def _coerce_rate(v: Any) -> float | None:
    f = float(v)
    if math.isnan(f): return 0.0  # or raise ValueError / return None
    return max(0.0, min(1.0, f))
```

---

## MEDIUM — Evaluation quality is degraded or misleading

### M1. Stale GMBeat `.instruction` references in rubric (default.md)

**File:** `evals/rubrics/default.md`, lines 316-317
```markdown
| Beat created | extraction.progress.gm_beat present in turn N | Beat has type + instruction |
| Beat narrated | Narration contains content matching beat's instruction | Beat instruction reflected in prose |
```

GMBeat model (ccya/models.py) now only has `type`, `surface_as`, `beat_expires_turn`. The `.instruction` field was removed in commit `71cffcb`. These rubric lines tell judges to look for a field that no longer exists, which would cause them to incorrectly score beats as malformed or miss the actual surface_as semantics.

**Fix:**
- Line 316: "Beat has type + surface_as" (instead of "type + instruction")
- Line 317: "Narration contains content matching beat's surface_as/type semantics" (instruction is gone)

---

### M2. Stale save/restore description in rubric (default.md line 305)

**File:** `evals/rubrics/default.md`, line 305
```markdown
After narration, beat is temporarily cleared then restored for extraction.
```

Save/restore was removed in commit `71cffcb`. Current behavior (turn.py lines 1120-1121):
```python
# Clear pending_gm_beat after narration consumed it — not restored since Storytell no longer receives beat context
state.setdefault("meta", {})["pending_gm_beat"] = None
```

Beat is now permanently cleared after narration, NOT restored for extraction. This description would mislead a judge evaluating whether beats are properly visible to progress extraction (they're not anymore).

**Fix:** Update to reflect permanent clearing: "After narration, pending_gm_beat is permanently set to None — it is no longer restored before extraction."

---

### M3. Hardcoded momentum floor `-3` in universal_asserts.py vs imported constant

**File:** `ccya/eval/universal_asserts.py`, line 631
```python
if m is not None and m <= -3:
```

Report.py was fixed (commit `0f4af40`) to import `MOMENTUM_MIN` from engine_mirror, but the assertion still hardcodes `-3`. If MOMENTUM_MIN ever changes in ccya/state/momentum.py, this assertion silently drifts — same risk as H2 above.

**Fix:** Import `from ccya.eval.engine_mirror import MOMENTUM_MIN` and use `MOMENTUM_MIN` instead of the literal `-3`.

---

### M4. Meta judge is isolated from all trace data (structural limitation)

The meta judge receives **only** domain judge scores and summaries (`body_md` extractions). It does NOT receive:
- Architecture docs (`arch_context=""`)
- Engine constants / seed state / system prompts
- Auto-checker failures (only sent to state_correctness judge)
- Redundancy signals, compaction signals, metrics rows
- Any raw event data

This is by design per the meta rubric ("Your job is synthesis, not new analysis"), but it means the meta score is entirely dependent on domain judge quality and completeness of their summaries. The meta judge cannot independently verify claims against source data — if a domain judge hallucinates or misses something, the meta judge has no way to catch it.

**Assessment:** Acceptable design tradeoff (token budget), but worth documenting as a known limitation in any evaluation documentation.

---

### M5. Narrative interplay judge missing extraction metadata

**File:** `ccya/eval/judge.py`, lines 159-164
```python
filtered_ext[stream] = {
    "output": s.get("output"),
    "skipped": s.get("skipped", False),
    "attempts": s.get("attempts", 1),
}
```

`retry_errors` and `context_meta` are stripped from extraction outputs for non-prompt_pipeline judges. The rubric's NPC Entry/Exit checks (Section 2A) require comparing timestamps or turn numbers that might be in the full extraction output but are lost here. This is a tradeoff for token reduction, but it limits diagnostic capability when judging NPC lifecycle correctness.

**Assessment:** Low risk currently — most NPC assertions work with just `output`. Medium risk if future rubric sections need retry/error diagnostics.

---

## LOW — Cosmetic issues / drift risks (currently harmless)

### L1. Local `_VALID_STREAMS` in runner.py vs engine_mirror.EXTRACT_STREAMS

**File:** `ccya/eval/runner.py`, line 194
```python
_VALID_STREAMS = frozenset(("ruling", "extract.state", "extract.scene", ...))
```

Currently identical to `engine_mirror.EXTRACT_STREAMS` (lines 46-53), but decoupled. If one is updated and the other isn't, scenario assertions could validate against stale stream names silently with no warning.

**Assessment:** Cosmetic currently — both sets match. Consider importing from engine_mirror for single source of truth.

---

### L2. Field name terminology mismatch in rubric (default.md line 310)

**File:** `evals/rubrics/default.md`, line 310
```markdown
If beat's expires_at turn has passed → engine discards it
```

Current model uses `beat_expires_turn` (ccya/models.py), not `expires_at`. Conceptually correct but inconsistent with actual code field name. Could confuse a judge reading the rubric against source code.

**Fix:** Change to "If beat's beat_expires_turn has passed → engine discards it."

---

### L3. Pipeline scores key filtering is strict on old names (judge.py)

**File:** `ccya/eval/judge.py`, lines 996-997
```python
pipeline_scores = {k: v for k, v in pipeline_scores.items() if k in ("ruling", "narrate", "extract_scene", "extract_state", "storytell")}
```

Only accepts the current set of keys. If a rubric or LLM outputs under an old name like `"extract_progress"` (the previous stream name before commit `71cffcb`), it is silently dropped — no warning, just zero score for that pipeline dimension. This is correct behavior for preventing stale data from polluting results, but could mask scoring errors if rubrics reference outdated names.

**Assessment:** Correct behavior currently. Worth noting in case old rubric files are still referenced somewhere.

---

### L4. State correctness judge has no narrate_prompt text (judge.py)

**File:** `ccya/eval/judge.py`, line 90
```python
# no narrate_prompt, no ruling_prompt text, no user prompts
```

By design — state_correctness only gets parsed outputs and deltas. But this limits diagnostic capability when drift involves narrative-state mismatches (e.g., narration says one thing but extraction produces a different delta). The judge must infer from extraction outputs alone without the actual prose to compare against.

**Assessment:** Acceptable tradeoff for token budget. State_correctness is primarily about mechanical correctness, not semantic alignment with prose.

---

### L5. Three thread lifecycle constants have no source of truth in engine code (engine_mirror.py)

**File:** `ccya/eval/engine_mirror.py`, lines 22-24
```python
_ACTIVE_THREAD_CAP: int = 3        # maximum number of active threads simultaneously
_EXPIRE_SILENT_TURNS: int = 5      # consecutive turns without being advanced before demoted to latent
_PROMOTION_COOLDOWN_TURNS: int = 3  # minimum turns between latent-to-active promotions
```

These are defined only in engine_mirror.py — they are NOT imported from any production module. If these become configurable or change in the engine, the mirror is the single point of failure for their correctness. The comments say "engine-internal" but there's no actual import to verify against source.

**Assessment:** Acceptable if these are truly design constants (not runtime-configurable). Should be documented as such and reviewed periodically when thread lifecycle behavior changes.

---

### L6. Momentum assertion accepts clamp tolerance too broadly (universal_asserts.py line 580)

```python
if actual == expected or (expected > 0 and 0 <= actual <= expected) or ...:
    passed = True
```

For a `+2` delta at the edge (momentum near +3), it accepts any actual value from 0..2. This can't distinguish between "clamped correctly" vs "momentum wasn't applied at all." A stricter check would be: actual should equal expected OR actual should be within 1 of expected when near boundaries.

**Assessment:** Intentional design (engine clamping is valid), but means the assertion has lower signal-to-noise ratio for edge cases. Acceptable given that momentum application bugs are rare and the clamp behavior is documented.

---

## Summary Table

| ID | Severity | File | Issue |
|----|----------|------|-------|
| H1 | HIGH | `evals/scenarios/full_cycle.py:98` | Stale `PacingContext.beat_hint` field reference |
| H2 | HIGH | `ccya/eval/universal_asserts.py:541-548` | Hardcoded momentum delta mapping (drift risk) |
| H3 | HIGH | `ccya/eval/judge.py:980-981` | NaN propagation in rate normalization |
| M1 | MEDIUM | `evals/rubrics/default.md:316-317` | Stale GMBeat `.instruction` references |
| M2 | MEDIUM | `evals/rubrics/default.md:305` | Stale save/restore description for beats |
| M3 | MEDIUM | `ccya/eval/universal_asserts.py:631` | Hardcoded momentum floor `-3` (drift risk) |
| M4 | MEDIUM | `ccya/eval/judge.py:run_judges()` | Meta judge isolated from all trace data |
| M5 | MEDIUM | `ccya/eval/judge.py:159-164` | Narrative interplay missing extraction metadata |
| L1 | LOW | `ccya/eval/runner.py:194` vs engine_mirror | Local `_VALID_STREAMS` decoupled from mirror |
| L2 | LOW | `evals/rubrics/default.md:310` | Terminology mismatch (`expires_at` vs `beat_expires_turn`) |
| L3 | LOW | `ccya/eval/judge.py:996-997` | Strict pipeline scores key filtering (old names silently dropped) |
| L4 | LOW | `ccya/eval/judge.py:82-90` | State correctness judge has no narrate_prompt text |
| L5 | LOW | `ccya/eval/engine_mirror.py:22-24` | Thread lifecycle constants have no source of truth in engine |
| L6 | LOW | `ccya/eval/universal_asserts.py:580` | Momentum assertion clamp tolerance too broad |
