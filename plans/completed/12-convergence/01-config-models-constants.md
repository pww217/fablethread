# Convergence Scoring — Phase 1: Config, Models, Constants

## Purpose

Prepare EngineConfig, IntentEnvelope, beat constants, and type aliases for the convergence scoring engine. No behavioral changes — this phase only reshapes data structures and constants.

## Firm decisions

- `tension_delta` removed from `IntentEnvelope`. Field deleted from model, not merely unused.
- `TensionDelta` type alias kept for Phase 1 (still imported by `turn.py`). Will be deleted in Phase 2 alongside its last consumer.
- `BEAT_BUCKETS["pressure"]` gains `setback`. `PRESSURE_BEAT_TYPES` gains `setback`.
- `consecutive_pressure_threshold` removed from EngineConfig.
- `crisis_urgency_threshold` removed from EngineConfig.
- `convergence_threshold` added to EngineConfig (default 3).
- `crisis_turn_limit` → `climax_turn_limit` renamed in EngineConfig (field def + `build_engine_config`). Consumers renamed in Phase 2.
- `spiral_decay_turns` — confirmed already absent from source (present only in docs/old plans). No code change needed.
- Breathe directive removed (resolved gap: tension_delta was its only trigger; 0% de-escalates across 80 turns).

## Status

`completed`

## Implementation — Phase 1: Config, Models, Constants

### Context files to load

- `ccya/engine/config.py` — EngineConfig class (lines 97-184), `build_engine_config` (lines 196-298)
- `ccya/models.py` — `TensionDelta` type alias (line 18), `IntentEnvelope` (lines 168-177)
- `ccya/engine/_pacing.py` — `BEAT_BUCKETS` (lines 15-19)
- `ccya/engine/turn.py` — `PRESSURE_BEAT_TYPES` (line 69)

### Detailed steps

#### Step 1.1 — EngineConfig: add convergence_threshold, rename crisis_turn_limit

**File:** `ccya/engine/config.py`

**What:**
- Add `convergence_threshold: int = 3` to EngineConfig, after `breather_max_turns` (line 159).
- Rename `crisis_turn_limit: int = 4` → `climax_turn_limit: int = 4` at line 158.
- Remove `crisis_urgency_threshold: int = 2` at line 157.
- Remove `consecutive_pressure_threshold: int = 3` at line 144.
- In `build_engine_config()`: add `convergence_threshold=int(game.get("convergence_threshold", 3))`, rename `crisis_turn_limit` → `climax_turn_limit` at line 281, remove `crisis_urgency_threshold` at line 280, remove `consecutive_pressure_threshold` at line 274.

**Why:** New convergence score needs a config threshold. `crisis_turn_limit` is renamed to `climax_turn_limit` (CRISIS→CLIMAX rename). Removed fields are dead or replaced.

**Validation:** `.venv/bin/python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.convergence_threshold == 3; assert hasattr(c, 'climax_turn_limit'); assert not hasattr(c, 'crisis_urgency_threshold'); assert not hasattr(c, 'consecutive_pressure_threshold')"`

#### Step 1.2 — IntentEnvelope: remove tension_delta field

**File:** `ccya/models.py`

**What:**
- Remove `tension_delta: TensionDelta = "maintains"` at line 176.
- Keep `TensionDelta` type alias at line 18 — still used by `turn.py` type hints. It will be deleted in Phase 2 Step 2.6 when all consumers are removed.

**Why:** `tension_delta` is architecturally wrong (0% de-escalates across 80 turns). Removing the field from IntentEnvelope eliminates the surface that ruling LLM writes to. The type alias is deferred to Phase 2 to avoid import breakage in `turn.py`.

**Validation:** `.venv/bin/python -c "from ccya.models import IntentEnvelope; i = IntentEnvelope(intent='test'); assert not hasattr(i, 'tension_delta')"`
Note: `from ccya.models import TensionDelta` should still work (type alias kept).

#### Step 1.3 — Update BEAT_BUCKETS pressure list

**File:** `ccya/engine/_pacing.py`

**What:** Add `"setback"` to the pressure bucket list at line 16:
```python
"pressure":  ["pressure", "complication", "escalation", "setback"],
```

**Why:** Design decision: setback applies negative pressure to the player — belongs with escalation, complication, pressure.

**Validation:** `.venv/bin/python -c "from ccya.engine._pacing import BEAT_BUCKETS; assert 'setback' in BEAT_BUCKETS['pressure']"`

#### Step 1.4 — Update PRESSURE_BEAT_TYPES tuple

**File:** `ccya/engine/turn.py`

**What:** Add `"setback"` to `PRESSURE_BEAT_TYPES` at line 69:
```python
PRESSURE_BEAT_TYPES = ("pressure", "escalation", "complication", "setback")
```

**Why:** Must match BEAT_BUCKETS pressure list. Used in consecutive pressure counter and relief injection checks.

**Validation:** `.venv/bin/python -c "from ccya.engine.turn import PRESSURE_BEAT_TYPES; assert 'setback' in PRESSURE_BEAT_TYPES"`

### Tests to write or update

No tests exist for this phase (tests temporarily removed per AGENTS.md). Run `make check` at end of Phase 4.
