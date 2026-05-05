# Plan: Momentum Track

## Concept

Momentum is a simple integer on the PC (-3 to +3) that tracks narrative pressure over time.
Think of it as the engine's equivalent of a human GM reading the room: after several bad
turns, the GM eases up; after a run of clean wins, they raise the stakes. Momentum automates
that signal without adding any player-facing complexity.

It answers the question: *"Has this player been punished enough?"*

## Mechanics

| Event | Momentum change |
|---|---|
| `crit_success` | +2 |
| `success` | +1 |
| `partial` (new band) | 0 |
| `setback` | -1 |
| `fail` | -1 |
| `crit_fail` | -2 |
| No roll (narrative turn) | 0 |

Clamped to [-3, +3] at all times.

## How It Affects the Game

Momentum is **not a stat that gets rolled** — it's a context signal passed to the narrator.
The narrator prompt gets one line:

- `momentum: +2` → "The player is on a winning streak; raise the stakes or introduce a new
  complication."
- `momentum: 0` → Neutral. No special instruction.
- `momentum: -2` → "The player has been struggling; give them a small break — a moment of
  respite, a lucky detail, or a friendly NPC beat."
- `momentum: -3` → "The player has been punished hard. Unless narrative logic demands
  otherwise, soften the next beat."

## Implementation

### State

**`ccya/state.py`**
- Add `momentum: int = 0` to `_default_state()` PC section
- Add migration guard in `_migrate_state()`: `pc.setdefault("momentum", 0)`
- Clamp on write: `max(-3, min(3, value))`

**`ccya/models.py`**
- Add `momentum_delta: int` with `ge=-1, le=1` to `StateExtractResult`
  — this is an engine-internal field; the extractor never sets it. It is computed
  deterministically from `band` in Python and stored here for pipeline clarity.

Delta table (engine-side, not LLM-driven):

```python
MOMENTUM_MIN = -3
MOMENTUM_MAX = 3

MOMENTUM_DELTA: dict[str, int] = {
    "crit_success": +2,
    "success":      +1,
    "partial":       0,
    "setback":      -1,
    "fail":         -1,
    "crit_fail":    -2,
}

def apply_momentum(state: dict, band: str | None) -> int:
    """Update pc.momentum based on the roll band. Returns new value."""
    pc = state.setdefault("pc", {})
    current = int(pc.get("momentum", 0))
    delta = MOMENTUM_DELTA.get(band or "", 0)
    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + delta))
    pc["momentum"] = new_val
    return new_val
```

### Engine Integration

**`ccya/engine.py`** — in `run_turn()`, after `outcome` resolves and before
`_narrate_messages()` is called:

```python
if outcome.rolled:
    apply_momentum(state, outcome.band)
```

The updated `state` dict (with new momentum) flows into `_narrate_messages()` naturally.

### Narrator Prompt

**`ccya/prompts/narrate_user.j2`** — expose `pc.momentum`:

```jinja
{% set m = state.pc.momentum | default(0) %}
{% if m >= 2 %}
MOMENTUM: HIGH (+{{ m }}). The player is on a strong run. Consider raising the stakes,
introducing a complication, or making the world react to their success.
{% elif m <= -2 %}
MOMENTUM: LOW ({{ m }}). The player has been struggling. Unless the fiction demands
punishment, offer a small break — a useful detail, a moment of respite, or a friendly beat.
{% endif %}
```

Only emit the directive at |momentum| >= 2 to avoid injecting noise on neutral turns.

### Extraction

Momentum is engine-managed, not LLM-managed. The extractor must never be asked to set or
change momentum. It is calculated deterministically from `band` in Python only.

### UI

Optional: display momentum as a small indicator in the PC stats panel. A simple [-3..+3]
bar or pip row. Label it "Momentum" or leave it as an internal debug field initially.

## Notes

- Depends on `band-collapse.md` — use the 5-band system for the delta table.
- Momentum resets to 0 on new game (seed generation).
- The narrator treats momentum as *advisory*, not binding — it should never override clear
  narrative logic (e.g., momentum +3 doesn't mean NPCs love a player who just burned down
  a village).
