# Post-Convergence Cleanup — Phase 2: EV Deltas + State Tools

## Purpose

Update `ev/deltas.py` and `ev/state_tools.py` to reflect renamed fields and removed machinery: `crisis_turn_count`→`climax_turn_count`, `tension_delta` removal, `consecutive_pressure_beats` removal. Plan 1 engine changes must be merged.

## Firm decisions

- `ev/deltas.py`: `crisis_turn_count`→`climax_turn_count` in display. `tension_delta` display removed. `consecutive_pressure_beats` display removed.
- `ev/state_tools.py`: `tension_delta` field removed from display. `crisis_turn_count`→`climax_turn_count`.

## Status

`open`

## Dependencies

- Plan 1 complete (event dict no longer emits removed fields).

## Implementation — Phase 2: EV Deltas + State Tools

### Context files to load

- `ccya/ev/deltas.py` — around lines 340-360
- `ccya/ev/state_tools.py` — around lines 500-645

### Detailed steps

#### Step 2.1 — Update deltas.py compact display

**File:** `ccya/ev/deltas.py`

**What:**
- Line 342: Change `crisis_count = pacing_ctx.get("crisis_turn_count", 0)` to `climax_count = pacing_ctx.get("climax_turn_count", 0)`.
- Line 344: Update display string to use `climax_turn_count`.
- Lines 354-356: Remove the `tension_delta` extraction and display block (checks `result.get("tension_delta")`).
- Lines 358-360: Remove the `consecutive_pressure_beats` extraction and display block (checks `ev.get("post_extraction_consecutive_pressure_beats")`).

**Why:** Event dict fields renamed or removed.

**Validation:** `grep -n 'tension_delta\|crisis_turn\|consecutive_pressure' ccya/ev/deltas.py` should return 0 (after changes).

#### Step 2.2 — Update state_tools.py display

**File:** `ccya/ev/state_tools.py`

**What:**
- Line 501: Remove `"tension_delta": ruling.get("tension_delta", "")` from the display dict.
- Line 514: Remove the `delta = r['tension_delta']` line and its display.
- Line 642: Change `crisis_count = scene.get("crisis_turn_count", 0)` to `climax_count = scene.get("climax_turn_count", 0)`.
- Line 644: Update display string to use `climax_turn_count`.

**Why:** Event dict fields renamed or removed.

**Validation:** `grep -n 'tension_delta\|crisis_turn' ccya/ev/state_tools.py` should return 0 (after changes).

### Tests to write or update

No tests. Run `make check` after all Plan 3 phases complete.
