# Plan: I-34 — Auto-adjust difficulty based on matching stat

## Design Reference

- Roadmap: `roadmap/improvements/I-34-auto-adjust-difficulty-based-on-matching-stat.md`
- I-34 proposes post-hoc difficulty adjustment based on PC's matching stat value

## Problem Statement

The ruling LLM defaults to "hard" for almost all tense situations — combat, social confrontation, anything with stakes. Even when the PC's matching stat is 4, they get no advantage on difficulty assessment. This creates frustrating loops where high-stats feel no different from mid-stats on rolls.

## Stat-based adjustment

| Stat | Feel | Effect |
|------|------|--------|
| 4 | Expert | Downgrade one tier (always) |
| 3 | Competent | ~33% chance to downgrade one tier |
| 2 | Mediocre | No adjustment |
| 1 | Terrible | Upgrade one tier (always) |

Difficulty ladder: `trivial (+2) → easy (+1) → normal (0) → hard (-1) → extreme (-2)`

## Scope

- **Phase 1:** Add `_adjust_difficulty()` to `ccya/rules.py`, integrate into `resolve_check()`
- **Phase 2:** Add `original_difficulty` and `difficulty_adjustment` fields to `RulesOutcome`
- **Phase 3:** Show `difficulty_adjustment` in UI tooltips across all roll badge templates
- **Phase 4:** Update docs (repomap, architecture)

## Status

`completed`

---

## Phase 1: `_adjust_difficulty()` in rules.py

### Context files to load

- `ccya/rules.py` — `resolve_check()` at line 140, diff_mod computation at line 164
- `ccya/models/config.py` — `Difficulty` literal, `DIFFICULTY_MOD` dict

### What changes

Add `_DIFFICULTY_ORDER` list and `_adjust_difficulty()` function to `ccya/rules.py`:

```python
_DIFFICULTY_ORDER = ["trivial", "easy", "normal", "hard", "extreme"]

def _adjust_difficulty(difficulty: str, stat_value: int, rng: random.Random | None = None) -> tuple[str, str]:
    """Adjust difficulty down one tier based on stat value.
    
    Returns (adjusted_difficulty, adjustment_reason).
    
    Stat 4 (Expert): down one tier always
    Stat 3 (Competent): ~33% chance down one tier
    Stat 2 (Mediocre): no adjustment
    Stat 1 (Terrible): up one tier always
    """
    idx = _DIFFICULTY_ORDER.index(difficulty)
    original = difficulty
    rng = rng or random
    
    if stat_value == 4:
        idx = max(0, idx - 1)
        reason = f"difficulty downgraded from {original} to {_DIFFICULTY_ORDER[idx]} — skill level 4"
    elif stat_value == 3:
        if rng.random() < 0.33:
            idx = max(0, idx - 1)
            reason = f"difficulty downgraded from {original} to {_DIFFICULTY_ORDER[idx]} — skill level 3"
        else:
            reason = ""
    elif stat_value == 1:
        idx = min(4, idx + 1)
        reason = f"difficulty upgraded from {original} to {_DIFFICULTY_ORDER[idx]} — skill level 1"
    else:
        reason = ""
    
    return _DIFFICULTY_ORDER[idx], reason
```

### Where to call

In `resolve_check()` at line 164, before `diff_mod = mods[difficulty]`:

```python
difficulty, _ = _adjust_difficulty(difficulty, stat_value, rng)
diff_mod = mods[difficulty]
```

### Why

- `_adjust_difficulty` is pure Python, deterministic given rng — easy to test
- Stat 3 uses `rng.random() < 0.33` — close enough to 1/3 for gameplay purposes
- Passing `rng` through allows testability with seeded RNG

---

## Phase 2: Add fields to RulesOutcome

### Context files to load

- `ccya/models/rules.py` — `RulesOutcome` model at line 38

### What changes

Add two fields to `RulesOutcome`:

```python
original_difficulty: str = ""
difficulty_adjustment: str = ""
```

- `original_difficulty` — what the LLM assigned (preserved for display)
- `difficulty_adjustment` — reason text for UI tooltip (e.g., "difficulty downgraded from hard to normal — skill level 4")

### Where to set

In `ccya/engine/ruling.py` after `resolve_check()` returns (line ~249):

```python
outcome = resolve_check(...)
# Capture LLM's difficulty before any internal adjustment
outcome.original_difficulty = intent.check.difficulty
# _adjust_difficulty already sets outcome.difficulty_adjustment internally
```

Actually, `_adjust_difficulty` returns the reason string — we need to pass it back to the outcome. The cleanest approach: have `_adjust_difficulty` return the reason, then set `outcome.difficulty_adjustment` in ruling.py.

---

## Phase 3: Show `difficulty_adjustment` in UI tooltips

### Context files to load

- `ccya/templates/index.html:202` — roll header with difficulty tooltip
- `ccya/templates/_turn_log.html:12` — roll header with difficulty tooltip
- `ccya/static/game-utils.js:296-297` — JS roll badge builder

### What changes

Add a second line to the difficulty tooltip showing `difficulty_adjustment` when present.

**index.html (line 202):**
```jinja2
{% if r.reason %}
<span class="has-tooltip">
    {{ r.difficulty | default('') | lower }}
    <span class="tooltip-body">
        {{ r.reason }}
        {% if r.difficulty_adjustment %}
        <br>{{ r.difficulty_adjustment }}
        {% endif %}
    </span>
</span>
{% else %}
{{ r.difficulty | default('') | lower }}
{% endif %}
```

**_turn_log.html (line 12):** Same pattern as index.html.

**game-utils.js (line 296-297):**
```javascript
if (payload.reason) {
    hdr.innerHTML = '🎲 <strong>' + skillLabel + '</strong> &nbsp;·&nbsp; <span class="has-tooltip">' + diffLabel + '<span class="tooltip-body">' + payload.reason;
    if (payload.difficulty_adjustment) {
        hdr.innerHTML += '<br>' + payload.difficulty_adjustment;
    }
    hdr.innerHTML += '</span></span>';
}
```

### Why

- Shows player why difficulty changed — transparency builds trust
- Second line in tooltip keeps it compact — doesn't clutter the main display
- `original_difficulty` not shown separately — `difficulty_adjustment` already contains both original and adjusted values

---

## Phase 4: Documentation updates

- `docs/architecture/state-models.md` — add `original_difficulty` and `difficulty_adjustment` to `RulesOutcome` field list
- `docs/repomap.md` — update `rules.py` description to mention `_adjust_difficulty()`
- `AGENTS.md` — no changes needed (no build/lint/command changes)

---

## Validation

- `make check` passes (lint + typecheck)
- Manual inspection: roll badges show `difficulty_adjustment` when present
- Stat 4 on "hard" → shows "difficulty downgraded from hard to normal — skill level 4"
- Stat 1 on "normal" → shows "difficulty upgraded from normal to hard — skill level 1"
- Stat 3 on "hard" → ~33% shows downgraded message, ~67% shows nothing
- Stat 2 → never shows adjustment message
- `ev.py dice` command shows adjusted difficulty correctly
