# Compactor: eliminate narrative gap

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Fix retain boundary | Change `retain_from` to use `recent_turns_min` so compaction always covers up to the recent window edge |
| 02 | Fix config validator | Relax the `compact_every > window_turns` constraint to `compact_every >= recent_turns_min` |
| 03 | Update config defaults | Set `compact_every: 3` in the default config shipped with the repo |

## Objective
The compactor fires every `compact_every` turns and retains the last `window_turns` turns as uncompacted prose. However, the narrator only needs `recent_turns_min` turns as full prose — everything between `recent_turns_min` and `window_turns` falls into a dead zone: not in `recent_turns` (window too small) and not yet in `prior_history` bullets (not yet compacted). On a long game this produces a visible gap in the narrator's context window.

## Non-goals
- Does not change how `chronicle.md` is written or structured.
- Does not change the LLM prompt templates for compaction (`compact_system.j2`, `compact_user.j2`).
- Does not change `window_turns` semantics for the narrator — the narrator still loads up to `window_turns` of prose via `chronicle_tail`. The change only affects the compactor's retention boundary.
- Does not add new tests beyond those specified below.

---

## Implementation — Phase 01: Fix retain boundary

### Files to pull for context
- `ccya/engine/compactor.py`
- `ccya/engine/config.py`

### Detailed steps

#### Step 1.1 — Change `retain_from` in `maybe_compact`

**File:** `ccya/engine/compactor.py`

**What:** Replace the line that computes `retain_from` to use `config.recent_turns_min` instead of `config.window_turns`. This means the compactor compacts everything older than the minimum narrator window, not everything older than the full window.

**Why:** The invariant is: after compaction, every turn older than `recent_turns_min` is either a bullet in `prior_history` or covered by `chronicle_tail`. Right now turns in the range `[current_turn - window_turns + 1, current_turn - recent_turns_min]` are neither — the gap. Using `recent_turns_min` closes it completely.

**Before (line 45 in `maybe_compact`):**
```python
    retain_from = max(1, current_turn - config.window_turns + 1)
```

**After:**
```python
    retain_from = max(1, current_turn - config.recent_turns_min + 1)
```

No other lines in `maybe_compact` reference `retain_from` in a way that needs updating — `compact_end = retain_from - 1` and `compact_start = last_compacted_turn + 1` are both derived from it correctly.

**Validation:** Trace through manually with `compact_every=3`, `recent_turns_min=2`, `window_turns=3`:
- T3 fires: `retain_from = max(1, 3-2+1) = 2`, compacts T1. T2–T3 stay as prose. ✓
- T6 fires: `retain_from = max(1, 6-2+1) = 5`, compacts T2–T4 (compact_start=2, compact_end=4). T5–T6 stay. ✓
- T9 fires: compacts T5–T7. T8–T9 stay.
- T12 (pre-compaction): `recent_turns` loads T10–T12. T1–T9 are all in bullets. No gap. ✓

---

## Implementation — Phase 02: Fix config validator

### Files to pull for context
- `ccya/engine/config.py`

### Detailed steps

#### Step 2.1 — Replace the `compact_every <= window_turns` guard

**File:** `ccya/engine/config.py`

**What:** In `_validate_compactor_config`, replace the existing constraint that `compact_every > window_turns` with a constraint that `compact_every >= recent_turns_min`. Also change `recent_turns_min < 0` to `recent_turns_min < 1`.

**Why:** After Phase 01, the correct invariant is that each compaction run must compact at least one turn. With `retain_from = current_turn - recent_turns_min + 1`, the compacted range spans `recent_turns_min - 1` turns at minimum (on the first fire, more on subsequent). The compactor already guards `compact_start > compact_end` and returns early — but the config validator should reflect the correct contract. The old `compact_every > window_turns` guard is now wrong and would reject valid configs like `compact_every=3, window_turns=3`.

**Before (in `_validate_compactor_config`, lines 169–185):**
```python
def _validate_compactor_config(config: EngineConfig) -> None:
    if config.window_turns < 1:
        raise ValueError(f"window_turns must be >= 1, got {config.window_turns}")
    if config.compact_every < 0:
        raise ValueError(
            f"compact_every must be >= 0, got {config.compact_every}"
        )
    if 0 < config.compact_every <= config.window_turns:
        raise ValueError(
            f"compact_every ({config.compact_every}) must be > window_turns ({config.window_turns})"
        )
    if config.recent_turns_min < 0:
        raise ValueError(f"recent_turns_min must be >= 0, got {config.recent_turns_min}")
    if config.recent_turns_min > config.window_turns:
        raise ValueError(
            f"recent_turns_min ({config.recent_turns_min}) must be <= window_turns ({config.window_turns})"
        )
```

**After:**
```python
def _validate_compactor_config(config: EngineConfig) -> None:
    if config.window_turns < 1:
        raise ValueError(f"window_turns must be >= 1, got {config.window_turns}")
    if config.compact_every < 0:
        raise ValueError(
            f"compact_every must be >= 0, got {config.compact_every}"
        )
    if config.recent_turns_min < 1:
        raise ValueError(f"recent_turns_min must be >= 1, got {config.recent_turns_min}")
    if config.recent_turns_min > config.window_turns:
        raise ValueError(
            f"recent_turns_min ({config.recent_turns_min}) must be <= window_turns ({config.window_turns})"
        )
    if 0 < config.compact_every < config.recent_turns_min:
        raise ValueError(
            f"compact_every ({config.compact_every}) must be >= recent_turns_min ({config.recent_turns_min})"
            f" (or 0 to disable)"
        )
```

**Validation:** Confirm all of the following pass:
- `compact_every=0` (disabled) → no error
- `compact_every=3, recent_turns_min=2, window_turns=3` → no error (was previously rejected)
- `compact_every=1, recent_turns_min=2` → raises ValueError
- `recent_turns_min=0` → raises ValueError
- `recent_turns_min=4, window_turns=3` → raises ValueError

---

## Implementation — Phase 03: Update config defaults

### Files to pull for context
- `config.yaml` (root of repo)

### Detailed steps

#### Step 3.1 — Set compact_every to 3

**File:** `config.yaml`

**What:** Update the `game` section to set `compact_every: 3`. `recent_turns_min: 2` is already present in the config.

**Why:** With the fix in Phase 01, `compact_every=3` with `recent_turns_min=2` produces the desired behavior: compaction runs every 3 turns, always covers everything older than the 2-turn narrator window, and never creates a gap.

**What to change:**
```yaml
game:
  compact_every: 3        # was 6
  recent_turns_min: 2     # narrator always sees 2 full turns as prose
```

Leave `window_turns` at its current value (3). Do not change other `game` keys.

**Validation:** Start a new game and play to turn 9. Check that:
1. Compaction fires at T3, T6, T9.
2. At T9, `state.meta.prior_history` contains bullets covering T1–T7.
3. The narrator prompt at T9 shows T8–T9 as full prose in Recent History, and T1–T7 as bullets in Prior History.
4. No gap between the bullet coverage and the prose window.

---

### Tests to write or update

**File:** `tests/test_compactor.py`

The existing test file already contains tests for config validation and compactor logic. The following tests need updating to reflect the new behavior:

#### Tests to update

- `TestValidateCompactorConfig.test_rejects_compact_every_lte_window_turns` (line 57): Currently asserts that `compact_every=3, window_turns=3` raises `ValueError`. After Phase 02, this should NOT raise. Update to assert it passes.

- `TestValidateCompactorConfig.test_rejects_compact_every_less_than_window_turns` (line 62): Currently asserts that `compact_every=3, window_turns=5` raises. After Phase 02, `compact_every=3` with `recent_turns_min=2` is valid (3 >= 2). Update to use `compact_every=1` to test rejection.

- `TestValidateCompactorConfig.test_rejects_negative_recent_turns_min` (line 72): Currently checks `recent_turns_min=-1` against `>= 0`. After Phase 02, the check is `>= 1`. Update the match string.

- `TestValidateCompactorConfig.test_boundary_recent_turns_min_zero` (line 91): Currently asserts `recent_turns_min=0` does NOT raise. After Phase 02, `recent_turns_min=0` should raise `ValueError`. Update to expect the error.

- `TestMaybeCompactBandMath.test_turn6_compacts_1_to_3_sets_last_compacted_3` (line 363): Currently asserts `last_compacted_turn == 3`. After Phase 01, `compact_end = 4` so `last_compacted_turn == 4`. Update assertion.

- `TestMaybeCompactBandMath.test_turn12_compacts_4_to_9_sets_last_compacted_9` (line 380): Currently asserts `last_compacted_turn == 9` with `last_compacted_turn=3` initial state. After Phase 01, `compact_end = 10` so `last_compacted_turn == 10`. Update initial state and assertion.

- `TestMaybeCompactBandMath.test_compacted_turns_removed_from_chronicle` (line 484): Currently asserts `last_compacted_turn == 3` and that Turn 4 remains in chronicle. After Phase 01, `last_compacted_turn == 4` and Turn 4 is removed. Update assertions.

- `TestMaybeCompactBandMath.test_incremental_compaction_removes_new_range` (line 508): Currently asserts `last_compacted_turn == 9` with `last_compacted_turn=3` initial state. After Phase 01, `last_compacted_turn == 10` and turns 1–10 are removed. Update initial state and assertions.

- `TestCompactionEventEmission.test_compaction_event_written_when_compaction_runs` (line 928): Currently asserts `compact_end == 3`. After Phase 01, `compact_end == 4`. Update assertion.

#### Tests to add

- `test_retain_boundary_uses_recent_turns_min`: construct a mock state at turn 6 with `compact_every=3`, `recent_turns_min=2`, `window_turns=3`. Verify `compact_end = 4` (i.e., turns 1–4 are compacted, turns 5–6 kept). Previously this would have computed `compact_end = 2` (retaining 3 turns), leaving a gap.

- `test_no_gap_invariant`: simulate 12 turns of compaction by calling `maybe_compact` at T3, T6, T9, T12 with mock chronicle data. Assert that at every turn, the union of `prior_history` bullet coverage and `recent_turns` prose covers all turns 1 through `current_turn - 1` with no gaps.

- `test_validator_accepts_compact_every_equal_window_turns`: assert `_validate_compactor_config` does NOT raise for `compact_every=3, window_turns=3, recent_turns_min=2`.

- `test_validator_rejects_compact_every_below_recent_turns_min`: assert `_validate_compactor_config` raises `ValueError` for `compact_every=1, recent_turns_min=2`.

Use the existing `FakeLLM` pattern from `tests/test_compactor.py` for the LLM call in `maybe_compact`.

### REPOMAP and architecture updates

- `docs/REPOMAP/config.md`: update the description of `_validate_compactor_config` to state the new constraint: `compact_every >= recent_turns_min` (or 0 to disable), `recent_turns_min >= 1`.

### Risks

1. **Existing saves with `last_compacted_turn` set**: on upgrade, the first compaction after the fix will compact a larger range than before (from `last_compacted_turn + 1` through `current_turn - recent_turns_min`). This is correct behavior but produces more bullets in one shot. Mitigation: acceptable — the compactor already handles variable-sized ranges, and the LLM is given only the prose for the turns being compacted.

2. **compact_every=3 doubles LLM call frequency**: compaction now runs twice as often. Each compaction covers fewer turns (2 instead of 5+), so the prompt is smaller. Net LLM cost per 6 turns is approximately equal. Mitigation: monitor latency; if needed, raise `compact_every` to 4 or 5 without reintroducing the gap (the fix works at any value >= `recent_turns_min`).

## Ambiguities resolved

1. **Config file path**: Confirmed `config.yaml` is at the repo root. `recent_turns_min: 2` is already present in the config; only `compact_every` needs updating from 6 to 3.
