# Eval System Findings

Bugs, issues, and improvement opportunities discovered during verification of the 2026-06-05 eval run.

---

## CRITICAL BUGS

### 1. Auto-checker reads momentum from `meta` instead of `pc` (False-positive cascade)

**Files:**
- `ccya/eval/universal_asserts.py:768` — `check_beat_locked_dual_trigger()`
- `ccya/eval/universal_asserts.py:544` — `check_floor_no_relief()`
- `ccya/eval/report.py:724` — report generation

**Bug:** All three functions read momentum via `(state_snapshot or {}).get("meta") or {}`, but momentum lives under `pc.momentum`, not `meta`. This produces `momentum=0` (the default) for every turn, causing false-positive failures across the entire pacing assertion suite.

**Evidence from event data:**
```
T6:  pc.momentum=-2 → beat_locked should be False ✓ (auto-checker sees momentum=0, expects False — passes by luck)
T7:  pc.momentum=-3 → beat_locked should be True  ✗ (auto-checker sees momentum=0, expects False — FAILS)
T10: pc.momentum=-2→-3 → beat_locked should be True  ✗ (same false failure)
```

The engine code is correct everywhere it matters (`turn.py:790,816,828,886,893` all read from `pc`). The eval report's #1 critical finding ("momentum desync in `_compute_pacing_context()`") is entirely fabricated by this auto-checker bug.

**Fix:** Replace `.get("meta").get("momentum", 0)` with `(state_snapshot.get("pc") or {}).get("momentum", 0)` in all three locations.

---

### 2. Location change failure misidentified (T12 vs T13)

**Report claim:** "Location change at Turn 12 was emitted but `state.location.id` remained `crossed_keys_entrance`."

**Reality:** Event data shows the transition was correctly applied:
- `applied.location_change.id = "river_docks"` ✓
- `state_snapshot.location.id = "river_docks"` ✓

The actual auto-checker failure occurred at **T13**, where it reported `"location_change emitted but state.location.id unchanged"`. However, T13's event data shows no `applied.location_change` (only `location_description`). This is likely an auto-checker bug caused by event interleaving — the checker's `prev_event` tracking got confused.

**Fix:** Investigate the `check_location_change_applied()` assertion's prev_event logic for race conditions with split turns or metadata events.

---

## MAJOR ISSUES

### 3. Condition orphan check is too strict (False positives on narrative-only conditions)

**File:** `ccya/eval/universal_asserts.py:927-959` — `check_orphan_conditions()`

**Bug:** The assertion requires every condition ID to have an entry in `CONDITION_MODS`. But the engine's `conditions_modifier()` function (`rules.py:134-145`) already handles missing keys gracefully with `.get(key, {})`, defaulting to zero modifier. Conditions like `cornered`, `winded`, and `scraped_and_bruised` are intentionally narrative-only — they have no mechanical effect but shouldn't be flagged as errors.

**Event data:** These conditions appear in T6-T13 with valid lifecycle (add/remove) but lack entries in:
```python
CONDITION_MODS = {
    "wounded": {"strength": -1, "dexterity": -1},
    "exhausted": {"strength": -1, "dexterity": -1, "resolve": -1},
    "drugged": {"wits": -1, "resolve": -1},
    "frightened": {"resolve": -1, "charisma": -1},
    "shaken": {"resolve": -1},
    "bleeding": {"strength": -1},
}
```

**Fix options:**
- (A) Add narrative-only conditions to `CONDITION_MODS` with zero-value modifiers — keeps the assertion simple but pollutes the config.
- (B) Update `check_orphan_conditions()` to accept a list of "narrative-only" condition IDs that are exempt from the check.
- (C) Remove the assertion entirely if narrative conditions without modifiers are an intentional design choice.

---

### 4. T10 actions quality failure is spurious (caught intermediate pass)

**Report claim:** "Storyteller emitted empty actions list in the first T10 pass."

**Reality:** Event data shows two T10 blocks:
- First block: `actions: []`, ruling with no roll data (empty input pass)
- Second block: 4 valid actions, full ruling output (`band=partial`)

The auto-checker flagged the intermediate state. The final output is correct. This suggests either split-turn handling in the eval pipeline or an empty first-pass that was superseded — but the assertion doesn't account for this.

**Fix:** Either deduplicate events by turn before running assertions, or add a `final_pass_only` flag to skip non-final passes.

---

## MINOR ISSUES

### 5. Eval report misdiagnosed T7 intent redirection root cause

The eval correctly identified that the player's negotiate-with-Halden intent was redirected (T7 ruling: `impossible`, outcome: "physically pinned"). However, it blamed momentum desync as the root cause — which is false (see finding #1). The real issue is in the **ruling LLM's decision logic**: when a player attempts to interact with an absent NPC, the ruling phase should narrate that absence rather than inventing a physical obstruction. This is a prompt/engine design issue, not a data flow bug.

### 6. `check_floor_no_relief()` has same momentum readbug as #1

**File:** `ccya/eval/universal_asserts.py:544`

Same pattern as finding #1 — reads from `meta.momentum`. This assertion checks that floor relief doesn't fire when it shouldn't, but with `momentum=0`, the expected behavior is always "no floor relief" regardless of actual game state. All results for this assertion are unreliable.

### 7. Report generation shows wrong momentum values to humans

**File:** `ccya/eval/report.py:724` and `ccya/eval/judge.py:698`

The report output tables show `momentum=0` in auto-checker failure details (e.g., "beat_locked=False but expected True (momentum=0, floor=-3...)"). This misleads human reviewers into debugging the engine when the bug is in the checker. The momentum values shown should be read from `pc.momentum`.

### 8. No deduplication of split/retried turns in assertion pipeline

Event data shows T10 has two blocks (empty pass + valid pass). If other turns have similar splits, assertions may fire on intermediate states rather than final outcomes. The eval system should either:
- Deduplicate by turn number before running checks, or
- Only evaluate the last event per turn.

### 9. `check_orphan_conditions` severity is mislabeled as "red" for pass case

**File:** `ccya/eval/universal_asserts.py:958`

The pass case returns `"severity": "red"` instead of a lower severity (e.g., "yellow"). This inflates red counts in reports.

### 10. Auto-checker has no visibility into whether momentum desync is real vs checker bug

When `beat_locked_dual_trigger` fires, the failure detail shows `momentum=0`. A reviewer cannot distinguish between:
- Engine reads stale data (real bug)
- Checker reads from wrong location (eval bug)

**Fix:** Add a diagnostic field to assertion output showing both `meta.momentum` and `pc.momentum`, or always read from the canonical location (`pc`) so mismatches are obvious.

---

## META-IMPROVEMENT OPPORTUNITIES FOR EVALS

### 11. Auto-checker assertions should be independently verifiable with minimal context

Current failure output: `"beat_locked=False but expected True (momentum=0, floor=-3...)"` — the reviewer must open event data separately to verify whether momentum is actually in `pc` or `meta`. A better assertion would include a self-diagnostic:
```python
"detail": "beat_locked mismatch (reported_momentum=0 from meta vs actual_pc.momentum=-3)",
```

### 12. Eval reports should flag known-checker-bugs before presenting findings

The report's #1 critical finding ("momentum desync") is entirely caused by the auto-checker bug in finding #1 above. A pre-flight check that validates assertion logic (e.g., "verify momentum location matches engine code") would catch this class of error before generating misleading reports.

### 13. Condition system needs explicit design doc for eval visibility

The `CONDITION_MODS` dict has only 6 entries (`wounded`, `exhausted`, `drugged`, `frightened`, `shaken`, `bleeding`) but the engine accepts arbitrary condition IDs from narration with zero runtime errors (via `.get(key, {})`). The eval system treats this as an error without any documentation explaining whether narrative-only conditions are intentional. Either:
- Document which conditions are "mechanical" vs "narrative-only", or
- Make `CONDITION_MODS` exhaustive at runtime (warn on unknown condition IDs).

### 14. Split-turn handling should be explicit in eval pipeline

The presence of two T10 blocks suggests the scenario runner can emit multiple events per turn (e.g., empty pass + retry, or split extraction phases). The assertion suite has no concept of "final output" vs "intermediate state." This leads to spurious failures on intermediate data.

### 15. Auto-checker should validate its own assumptions at runtime

Before running assertions, the checker could emit a validation step:
```python
# Sanity check: does momentum exist under pc?
pc_mom = (state_snapshot.get("pc") or {}).get("momentum")
meta_mom = ((state_snapshot.get("meta")) or {}).get("momentum")
if meta_mom is not None and pc_mom != meta_mom:
    warn(f"momentum differs between pc ({pc_mom}) and meta ({meta_mom}) — some checks may be unreliable")
```

### 16. Report should include assertion coverage matrix

The report lists pass/fail per turn but doesn't show which assertions are known to have false-positive rates or read from incorrect data locations. A metadata section listing each assertion's reliability status would prevent misinterpretation:
- `beat_locked_dual_trigger` — **UNRELIABLE** (reads momentum from wrong location)
- `floor_no_relief` — **UNRELIABLE** (same issue)
- `conditions.orphan` — **PARTIALLY RELIABLE** (flags narrative-only conditions as errors)

### 17. Pacing metrics table in report is misleading with broken data

The Momentum Table (Section 4, lines ~103-112 of the eval report) shows "WRONG_DIR" and "FLAT" flags derived from auto-checker analysis that reads `momentum=0`. The entire momentum lifecycle assessment is unreliable until finding #1 is fixed.

### 18. No automated regression detection for assertion logic itself

If an assertion's data source changes (e.g., momentum moves from `meta` to `pc`), there's no mechanism to detect that the assertion now reads stale/wrong data. Assertions should include a "last verified" timestamp or be paired with golden-event tests.

### 19. Universal assert results table severity counts are inflated by false positives

The summary table shows red-severity failures for assertions like `beat_locked_dual_trigger` (4 turns), `conditions.orphan` (5 turns), and `location_change.applied` (1 turn, misidentified). After fixing findings #1-3, the red count would drop significantly. The report's "Critical" section is therefore inflated by eval-system bugs rather than engine bugs.

### 20. Event data structure should be documented for assertion authors

The event dict has `state_snapshot.pc.momentum` but also a `meta` key (whose purpose and contents are unclear). Assertion authors need to know the canonical location for each piece of state. A docstring or separate schema file mapping event fields to their authoritative locations would prevent bugs like finding #1.
