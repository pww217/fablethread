# Compactor: eliminate narrative gap + preserve recent_events causality

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Fix retain boundary | Change `retain_from` to use `recent_turns_min` so compaction always covers up to the recent window edge |
| 02 | Fix config validator | Relax the `compact_every > window_turns` constraint to `compact_every >= recent_turns_min` |
| 03 | Remove recent_events clobber | Stop the compactor from replacing `recent_events` wholesale; let the extraction pipeline own it |
| 04 | Update config defaults | Set `compact_every: 3` in the default config shipped with the repo |

## Objective
The compactor fires every `compact_every` turns and retains the last `window_turns` turns as uncompacted prose. However, the narrator only needs `recent_turns_min` turns as full prose — everything between `recent_turns_min` and `window_turns` falls into a dead zone: not in `recent_turns` (window too small) and not yet in `prior_history` bullets (not yet compacted). On a long game this produces a visible gap in the narrator's context window. The second bug is that when compaction fires, it replaces `state.scene.recent_events` with a consolidated LLM summary, losing first-person causal facts (e.g. "I shot Jon" becomes "Jon is dead").

## Non-goals
- Does not change how `chronicle.md` is written or structured.
- Does not change the LLM prompt templates for compaction (`compact_system.j2`, `compact_user.j2`).
- Does not change `window_turns` semantics for the narrator — the narrator still loads up to `window_turns` of prose via `chronicle_tail`. The change only affects the compactor's retention boundary.
- Does not remove the `recent_events_compact` field from `CompactorSanitizationResult` or the LLM prompt — the LLM may still emit it; we just stop applying it to state.
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

**Before (line ~40 in `maybe_compact`):**
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

**What:** In `_validate_compactor_config`, replace the existing constraint that `compact_every > window_turns` with a constraint that `compact_every >= recent_turns_min`. Also add a guard that `recent_turns_min >= 1`.

**Why:** After Phase 01, the correct invariant is that each compaction run must compact at least one turn. With `retain_from = current_turn - recent_turns_min + 1`, the compacted range spans `recent_turns_min - 1` turns at minimum (on the first fire, more on subsequent). The compactor already guards `compact_start > compact_end` and returns early — but the config validator should reflect the correct contract. The old `compact_every > window_turns` guard is now wrong and would reject valid configs like `compact_every=3, window_turns=3`.

**Before (in `_validate_compactor_config`):**
```python
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

## Implementation — Phase 03: Remove recent_events clobber

### Files to pull for context
- `ccya/engine/compactor.py`

### Detailed steps

#### Step 3.1 — Remove the `recent_events_compact` application block

**File:** `ccya/engine/compactor.py`

**What:** In `maybe_compact`, remove the block that replaces `state["scene"]["recent_events"]` with the compactor's consolidated version. Keep the `_apply_sanitization` call (it handles NPC merges, inventory, quests, pressures, conditions — all correct). Only remove the `recent_events_compact` replacement.

**Why:** `recent_events` is owned by the extraction pipeline and is populated with precise, first-person causal facts each turn. The compactor's LLM consolidation loses causal attribution ("Jon Mendoza is dead" vs "I shot Jon Mendoza"). The cap at `recent_events_max` (default 20) already prevents unbounded growth. Removing this block means `recent_events` always reflects the extraction pipeline's real output without lossy rewriting.

**Before (block starting at ~line 112 in `maybe_compact`):**
```python
    if sanitization is not None:
        _apply_sanitization(state, sanitization)

        # Replace recent_events with compactor's consolidated version
        if sanitization.recent_events_compact:
            scene = state.setdefault("scene", {})
            scene["recent_events"] = [
                {
                    "id": e.id,
                    "text": e.text,
                    "turn": e.turn or current_turn,
                }
                for e in sanitization.recent_events_compact
            ]
            _log.info(
                "compactor: compacted %d → %d recent_events",
                recent_events_count,
                len(sanitization.recent_events_compact),
                extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
            )
```

**After:**
```python
    if sanitization is not None:
        _apply_sanitization(state, sanitization)
        # recent_events is intentionally NOT replaced here.
        # The extraction pipeline owns recent_events and preserves causal
        # attribution (who did what to whom). The compactor's consolidated
        # version loses first-person facts. recent_events_max caps growth.
```

Also remove the now-unused `recent_events_count` variable that was only used in the removed log line:

**Before (line ~line 90):**
```python
    recent_events_count = len(state.get("scene", {}).get("recent_events") or [])
```

**After:** Delete this line entirely.

**Validation:** After this change, run a game to turn 9 with `compact_every=3`. Verify:
1. `recent_events` in state after compaction still contains first-person entries from turns 1–N (not a consolidated summary).
2. The compactor log does NOT emit "compactor: compacted N → M recent_events".
3. NPC merges, quest closes, and other sanitization still apply correctly.

---

## Implementation — Phase 04: Update config defaults

### Files to pull for context
- `config.yaml` (root of repo — confirm exact path before executing)

### Detailed steps

#### Step 4.1 — Set compact_every to 3

**File:** `config.yaml`

**What:** Update the `game` section to set `compact_every: 3`. If `recent_turns_min` is not already present, add `recent_turns_min: 2`.

**Why:** With the fix in Phase 01, `compact_every=3` with `recent_turns_min=2` produces the desired behavior: compaction runs every 3 turns, always covers everything older than the 2-turn narrator window, and never creates a gap.

**What to change:**
```yaml
game:
  compact_every: 3        # was 0 (disabled) or 6
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

Add or update the following test functions:

- `test_retain_boundary_uses_recent_turns_min`: construct a mock state at turn 6 with `compact_every=3`, `recent_turns_min=2`, `window_turns=3`. Verify `compact_end = 4` (i.e., turns 1–4 are compacted, turns 5–6 kept). Previously this would have computed `compact_end = 2` (retaining 3 turns), leaving a gap.

- `test_no_gap_invariant`: simulate 12 turns of compaction by calling `maybe_compact` at T3, T6, T9, T12 with mock chronicle data. Assert that at every turn, the union of `prior_history` bullet coverage and `recent_turns` prose covers all turns 1 through `current_turn - 1` with no gaps.

- `test_validator_accepts_compact_every_equal_window_turns`: assert `_validate_compactor_config` does NOT raise for `compact_every=3, window_turns=3, recent_turns_min=2`.

- `test_validator_rejects_compact_every_below_recent_turns_min`: assert `_validate_compactor_config` raises `ValueError` for `compact_every=1, recent_turns_min=2`.

- `test_recent_events_not_clobbered`: after `maybe_compact` with a sanitization payload that includes `recent_events_compact`, assert `state["scene"]["recent_events"]` is unchanged from before the call.

Use the existing `FakeLLM` pattern from `docs/REPOMAP/testing.md` for the LLM call in `maybe_compact`.

### REPOMAP and architecture updates

- `docs/REPOMAP/compactor.md` (if it exists): update the description of `retain_from` to reference `recent_turns_min` instead of `window_turns`. Update the invariant description to state: "After compaction, all turns older than `recent_turns_min` are either in `prior_history` bullets or covered by `chronicle_tail`."

### Risks

1. **Existing saves with `last_compacted_turn` set**: on upgrade, the first compaction after the fix will compact a larger range than before (from `last_compacted_turn + 1` through `current_turn - recent_turns_min`). This is correct behavior but produces more bullets in one shot. Mitigation: acceptable — the compactor already handles variable-sized ranges, and the LLM is given only the prose for the turns being compacted.

2. **compact_every=3 doubles LLM call frequency**: compaction now runs twice as often. Each compaction covers fewer turns (2 instead of 5+), so the prompt is smaller. Net LLM cost per 6 turns is approximately equal. Mitigation: monitor latency; if needed, raise `compact_every` to 4 or 5 without reintroducing the gap (the fix works at any value >= `recent_turns_min`).

3. **recent_events unbounded growth if extraction pipeline emits duplicates**: removing the compactor's consolidation means `recent_events` grows until the `recent_events_max` cap prunes it by eviction. If extraction emits redundant events, they now persist longer. Mitigation: `recent_events_max: 20` is already enforced in the extraction pipeline. The eviction note is shown in the UI when this triggers.

## Ambiguities requiring resolution before execution

1. **Config file path**: The plan assumes `config.yaml` at the repo root. Confirm the actual path before executing Phase 04. Options: A) `config.yaml` at root, B) `config/default.yaml` or similar, C) config is only set per-user and there is no shipped default to update.

2. **`compact_user.j2` references `recent_events_compact`**: the LLM prompt may instruct the model to return a `recent_events_compact` field. After Phase 03, the compactor ignores it but still sends it to the LLM and parses it (the `CompactorSanitizationResult` model still accepts it). This is harmless but wastes tokens. Options: A) leave the prompt and model unchanged (safest, no prompt churn), B) remove the `recent_events_compact` section from `compact_user.j2` and `CompactorSanitizationResult` in a follow-on plan. Recommendation: A for this plan, follow-on plan for B.
