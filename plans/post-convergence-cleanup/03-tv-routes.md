# Post-Convergence Cleanup — Phase 3: Turn Viewer + Routes

## Purpose

Update the turn viewer (`server/tv.py`) and settings API (`server/routes.py`) to reflect removed and renamed fields. Plan 1 engine changes must be merged.

## Firm decisions

- `tv.py`: `crisis_turn_count`→`climax_turn_count`. `consecutive_pressure_beats` removed. `enforce_relief` removed.
- `routes.py`: `consecutive_pressure_threshold` removed from settings endpoint.

## Status

`open`

## Dependencies

- Plan 1 complete (event dict no longer emits removed fields).

## Implementation — Phase 3: Turn Viewer + Routes

### Context files to load

- `ccya/server/tv.py` — lines 600-625
- `ccya/server/routes.py` — lines 735-770

### Detailed steps

#### Step 3.1 — Update turn viewer pacing context

**File:** `ccya/server/tv.py`

**What:** At lines 606-614:
- Change `"crisis_turn_count": pacing_ctx.get("crisis_turn_count")` to `"climax_turn_count": pacing_ctx.get("climax_turn_count")`.
- Remove `"consecutive_pressure_beats": ev.get("post_extraction_consecutive_pressure_beats")`.
- Remove `"gm_beat_enforce_relief": enforce_relief` (line 619) and the variable setting it.

**Why:** Fields renamed or removed from event dict.

**Validation:** `grep -n 'crisis_turn\|consecutive_pressure\|enforce_relief' ccya/server/tv.py` should return 0 (after changes).

#### Step 3.2 — Update settings API

**File:** `ccya/server/routes.py`

**What:**
- Remove `"consecutive_pressure_threshold": game_config.get("consecutive_pressure_threshold")` from the GET `/api/settings` response (line 742).
- Remove `"consecutive_pressure_threshold"` from the writable keys tuple in POST `/api/settings` (line 765).

**Why:** Config field removed from EngineConfig in Plan 1 Phase 1.

**Validation:** `grep -n 'consecutive_pressure' ccya/server/routes.py` should return 0 (after changes).

### Tests to write or update

No tests. Run `make check` after all Plan 3 phases complete.
