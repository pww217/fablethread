# Narration Persistence Fix

## Purpose

Fix the narration window losing content on page refresh: seed narration (turn 0) disappears, deltas vanish, and the scroll container appears truncated. Also fix choice buttons sometimes disappearing on refresh.

## Problem Statement

When the user refreshes the browser page during an active game:

1. **Seed narration disappears:** The opening narrative (turn 0) is stored in server in-memory state (`_dynamic_opening`) and in `state.yaml["__seed_meta__"]`, but **never written to chronicle.md**. On refresh, `_dynamic_opening` is empty and chronicle.md is empty, so the opening block is never rendered. If the game has 0 history turns, the "no content" check triggers the pack picker modal.

2. **Deltas disappear:** `_load_recent_history()` loads the last 8 turns from chronicle.md. Since the seed narration isn't in chronicle.md, the earliest turns are missing. Deltas (inventory added/removed, threads added) in those missing turns don't appear.

3. **Truncation (can't scroll to turn 1):** UI symptom of #2. The narrative panel only has 8 turns instead of the full chronicle.

4. **Choice buttons sometimes disappear:** When `events.jsonl` doesn't exist or the last event has no `actions` field, `_load_last_actions()` returns `[]`. The template condition `{% if last_actions %}` is falsy for empty list, falling through to "Continue your adventure." instead of rendering action pills.

**Root cause:** The seed narration is not persisted to chronicle.md during game initialization. All other content (turns 1+) IS in chronicle.md, but the 8-turn limit means older content is missing. The in-memory `_dynamic_opening` is the only place the seed narration survives across turns — and it's wiped on server restart or page refresh.

## Constraints

- Writing `## Turn 0 — Seed` to chronicle.md must not break any existing consumers (ev.py reads events.jsonl only, turn_viewer reads events.jsonl + state.yaml only, thread sanitizer uses last 5 turns from chronicle).
- The chronicle format uses `## Turn N — user_input` headers parsed by regex `^## Turn (\d+) — (.+)$`. Turn 0 must follow this exact format.
- `_load_recent_history()` uses turn number as a join key to merge ruling data from events.jsonl. Turn 0 has no ruling in events.jsonl, so `ruling_map.get(0)` returns None (correct behavior).
- No test writing during refactor phase.
- Blast radius should be minimal — only touch chronicle initialization and page-load loading logic.

## Non-goals

- Loading ALL chronicle turns into the narrative panel (would be expensive with thousands of turns).
- Changing the 8-turn history limit for the narrative panel (performance).
- Modifying ev.py, turn_viewer, or other UI elements.
- Changing the events.jsonl format or structure.

## Solution

### Step 1: Write seed narration to chronicle.md during init

Modify `init_save_dir()` in `ccya/state/io.py` to write the seed narration as `## Turn 0 — Seed` in chronicle.md when the seed contains `__seed_meta__.opening_narrative`.

**Format:** `\n## Turn 0 — Seed\n\n{opening_narrative}`

This ensures the seed narration is in the same format as all other turns, parseable by `load_last_narration()`.

### Step 2: Load opening from chronicle on page refresh

Modify `_load_recent_history()` in `ccya/server/panels.py` to return turn 0 separately from the rest of the history. Add a new function `_load_opening_from_chronicle()` that extracts the opening narrative from turn 0 in chronicle.md.

Modify the `GET /` route in `ccya/server/routes.py` to:
- Always load the opening from chronicle.md (not from in-memory `_dynamic_opening`)
- Pass the opening to the template context
- History starts from turn 1 (not turn 0)

### Step 3: Fix template empty-state logic

Modify the empty-state condition in `index.html` to show the empty prompt only when there's truly no narrative (no opening AND no history). Currently it checks `not history and not state.location.id`, but should also consider the opening.

### Step 4: Verify choice buttons loading

Verify that `_load_last_actions()` correctly loads actions from the last event in events.jsonl. The existing logic should work — the buttons disappear when there are genuinely no actions in the last event (which is correct behavior). No code change needed unless a bug is found.

## Firm decisions

1. Turn 0 in chronicle.md uses the format `## Turn 0 — Seed` (em dash, space, "Seed" as input placeholder).
2. The opening is loaded from chronicle.md on every page refresh, regardless of whether history exists.
3. History in the narrative panel starts from turn 1 (turn 0 is rendered in the separate opening block).
4. The 8-turn history limit remains unchanged for the narrative panel (performance).
5. Writing to chronicle.md during init uses the same format as `append_chronicle()` (leading `\n` before the header).
6. If chronicle.md has no turn 0 (legacy saves or static packs), the opening falls back to in-memory `_dynamic_opening`.

## Risks, Ambiguities, and Blockers

- **Legacy saves:** Existing save directories have empty chronicle.md with no turn 0. The opening will fall back to in-memory `_dynamic_opening` (empty on refresh). This is acceptable — the user would need to start a new game for the fix to apply.
- **Static packs:** Static packs have hardcoded opening narratives in their pack files. These are loaded from the pack manifest, not from the seed. The chronicle-based loading only applies to dynamic packs (generated via LLM).
- **Blast radius:** Writing to chronicle.md during init touches `ccya/state/io.py`. Loading from chronicle touches `ccya/server/panels.py` and `ccya/server/routes.py`. No changes to template rendering logic (opening block already exists).
- **Thread sanitizer:** Uses `load_last_narration(save_dir, 5)`. If turn 0 is in chronicle, it would be included in the last 5 turns for early games. The sanitizer skips when `current_turn == 0` (checks state.yaml, not chronicle), so no impact.
- **Ruling join:** `_load_recent_history()` merges chronicle turns with ruling data from events.jsonl using turn number as key. Turn 0 has no ruling in events.jsonl, so `ruling_map.get(0)` returns None. This is correct — the seed has no ruling.

## Status
`completed`

## Additional fixes discovered during review

### Change lines/diffs persistence (cc2360c)

**Problem:** After a turn completes, the change lines (inventory added/removed, threads added, etc.) are rendered by JS in `_buildTurnChanges()` during `turn_complete`. On page refresh, these are lost because the server-rendered history only includes `turn/input/narrative/ruling` — not `change_lines`.

**Fix:** 
- `panels.py`: `_load_changes_map()` builds turn→change_lines from events.jsonl using `format_change_lines()` (same as turn_complete).
- `panels.py`: `_group_change_lines()` replicates JS `_groupChangeLines()` logic for Jinja template rendering.
- `panels.py`: `_load_recent_history()` now includes `change_lines` and `change_groups` in each history entry.
- `index.html`: Template renders `change_groups` as `turn-changes` div after roll badge in each history block.

**Files changed:** `ccya/server/panels.py`, `ccya/templates/index.html`

## Phases

2 phases: (1) Backend: write seed to chronicle + load opening from chronicle, (2) Frontend: fix empty-state logic.

---

## Implementation — Phase 1: Backend

### Context files to load
- `ccya/state/io.py` — `init_save_dir()` function
- `ccya/state/chronicle.py` — `load_last_narration()`, chronicle format
- `ccya/server/panels.py` — `_load_recent_history()`, `_get_opening()`, `_load_last_actions()`
- `ccya/server/routes.py` — `GET /` route handler, `_apply_seed_to_save_dir()`
- `ccya/server/app.py` — `_dynamic_opening`, `_dynamic_opening_actions`, `_dynamic_opening_outcome`

### Detailed steps

#### Step 1.1 — Write seed narration to chronicle.md in `init_save_dir()`

**File:** `ccya/state/io.py`

**What:** Modify `init_save_dir()` to write the seed narration to chronicle.md when the seed contains `__seed_meta__.opening_narrative`.

**Current code (line 129-135):**
```python
def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")
    (save_dir / "state_snapshot.yaml").unlink(missing_ok=True)
```

**New code:**
```python
def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    chronicle_path = save_dir / "chronicle.md"
    seed_meta = seed.get("__seed_meta__") or {}
    opening = seed_meta.get("opening_narrative")
    if opening:
        chronicle_path.write_text(f"\n## Turn 0 — Seed\n\n{opening.strip()}")
    else:
        chronicle_path.write_text("")
    (save_dir / "events.jsonl").write_text("")
    (save_dir / "state_snapshot.yaml").unlink(missing_ok=True)
```

**Why:** Ensures the seed narration is in chronicle.md in the same format as other turns, parseable by `load_last_narration()`.

**Validation:** After a new game, `saves/default/chronicle.md` should start with `\n## Turn 0 — Seed\n\n{opening narrative text}`.

#### Step 1.2 — Add `_load_opening_from_chronicle()` function

**File:** `ccya/server/panels.py`

**What:** Add a function that extracts the opening narrative from turn 0 in chronicle.md. Uses the same parsing logic as `load_last_narration()` but specifically targets turn 0.

**New function (after `_load_last_actions`, before `_debug_context`):**
```python
def _load_opening_from_chronicle(save_dir: Path) -> str | None:
    """Extract the opening narrative from turn 0 in chronicle.md. Returns None if not found."""
    from ccya.state.chronicle import _TURN_HEADER
    
    path = save_dir / "chronicle.md"
    if not path.exists():
        return None
    
    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))
    for m in matches:
        if int(m.group(1)) == 0:
            narrative = text[m.end():].strip()
            return narrative if narrative else None
    return None
```

**Why:** Provides a clean way to load the opening from chronicle.md on page refresh. Reuses the existing regex pattern.

**Validation:** `python -c "from ccya.server.panels import _load_opening_from_chronicle; print(_load_opening_from_chronicle(Path('saves/default')))"` — returns the opening narrative string or None.

#### Step 1.3 — Modify `_load_recent_history()` to exclude turn 0

**File:** `ccya/server/panels.py`

**What:** Modify `_load_recent_history()` to exclude turn 0 from the history list (turn 0 is rendered in the separate opening block).

**Current code (lines 54-67):**
```python
def _load_recent_history(save_dir: Path, n: int = 8) -> list[dict[str, Any]]:
    """Return the last n turns from chronicle.md for page-reload continuity (full narrative)."""
    turns = load_last_narration(save_dir, n)
    ruling_map = _load_ruling_map(save_dir)
    _log.debug("_load_recent_history n=%d turns=%d ruling_entries=%d", n, len(turns), len(ruling_map))
    return [
        {
            "turn": t["turn"],
            "input": t["input"],
            "narrative": t["narrative"],
            "ruling": ruling_map.get(t["turn"]),
        }
        for t in turns
    ]
```

**New code:**
```python
def _load_recent_history(save_dir: Path, n: int = 8) -> list[dict[str, Any]]:
    """Return the last n turns from chronicle.md (excluding turn 0 seed)."""
    all_turns = load_last_narration(save_dir, n + 1)  # +1 to account for turn 0 exclusion
    turns = [t for t in all_turns if t["turn"] != 0]
    # If we excluded turn 0 and now have fewer than n, load one more
    if len(turns) < n:
        more = load_last_narration(save_dir, n + 2)
        turns = [t for t in more if t["turn"] != 0]
    ruling_map = _load_ruling_map(save_dir)
    _log.debug("_load_recent_history n=%d turns=%d ruling_entries=%d", n, len(turns), len(ruling_map))
    return [
        {
            "turn": t["turn"],
            "input": t["input"],
            "narrative": t["narrative"],
            "ruling": ruling_map.get(t["turn"]),
        }
        for t in turns
    ]
```

Actually, let me simplify this. The logic is getting complex. Let me use a cleaner approach:

**Simpler new code:**
```python
def _load_recent_history(save_dir: Path, n: int = 8) -> list[dict[str, Any]]:
    """Return the last n turns from chronicle.md (excluding turn 0 seed)."""
    all_turns = load_last_narration(save_dir, n + 1)
    turns = [t for t in all_turns if t["turn"] != 0]
    ruling_map = _load_ruling_map(save_dir)
    _log.debug("_load_recent_history n=%d turns=%d ruling_entries=%d", n, len(turns), len(ruling_map))
    return [
        {
            "turn": t["turn"],
            "input": t["input"],
            "narrative": t["narrative"],
            "ruling": ruling_map.get(t["turn"]),
        }
        for t in turns[-n:]
    ]
```

**Why:** Excludes turn 0 from the history list. The `n + 1` ensures we get n turns after excluding turn 0. The `[-n:]` slice handles the case where there are fewer than n turns.

**Validation:** For a game with 10 turns (0-9), `_load_recent_history()` should return turns 2-9 (8 turns, excluding 0 and 1... wait, that's wrong).

Let me reconsider. If there are 10 turns (0-9) and we want the last 8 from history (excluding turn 0), we want turns 2-9. `load_last_narration(save_dir, 9)` returns turns 1-9 (9 turns). Filtering out turn 0 gives turns 1-9 (9 turns). Taking `[-8:]` gives turns 2-9. That's correct.

But if there are 2 turns (0-1), `load_last_narration(save_dir, 3)` returns turns 0-1. Filtering out turn 0 gives turn 1. Taking `[-8:]` gives turn 1. Correct.

If there are 0 turns (empty chronicle), `load_last_narration(save_dir, 9)` returns []. Filtering gives []. Correct.

#### Step 1.4 — Modify `GET /` route to load opening from chronicle

**File:** `ccya/server/routes.py`

**What:** Modify the `GET /` route to always load the opening from chronicle.md (not from in-memory `_dynamic_opening`). Fall back to in-memory if chronicle has no turn 0.

**Current code (lines 178-194):**
```python
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = _load_recent_history(_app_mod.SAVE_DIR)
    last_actions = _load_last_actions(_app_mod.SAVE_DIR) if history else []
    state = _load_current_state()
    opening = (
        _get_opening() if not history and state.get("location", {}).get("id") else ""
    )
    opening_actions = _get_opening_actions() if not history and opening else []
    ctx = _debug_context()
    ctx["state"] = state
    ctx["history"] = history
    ctx["last_actions"] = last_actions
    ctx["opening"] = opening
    ctx["opening_actions"] = opening_actions
    ctx["opening_outcome_summary"] = _get_opening_outcome_summary() if opening else ""
    ctx["has_narrative"] = bool(opening or history)
    ...
```

**New code:**
```python
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = _load_recent_history(_app_mod.SAVE_DIR)
    last_actions = _load_last_actions(_app_mod.SAVE_DIR) if history else []
    state = _load_current_state()
    # Always try chronicle first, fall back to in-memory (for live turns during a session)
    opening = _load_opening_from_chronicle(_app_mod.SAVE_DIR) or _get_opening()
    opening_actions = _get_opening_actions() if not history and not last_actions else []
    ctx = _debug_context()
    ctx["state"] = state
    ctx["history"] = history
    ctx["last_actions"] = last_actions
    ctx["opening"] = opening
    ctx["opening_actions"] = opening_actions
    ctx["opening_outcome_summary"] = _get_opening_outcome_summary() if opening else ""
    ctx["has_narrative"] = bool(opening or history)
    ...
```

**Why:** 
- Opens from chronicle first (survives refresh), falls back to in-memory (for live turns during a session where chronicle hasn't been updated yet).
- `last_actions` is loaded regardless of whether history exists (fixes the case where events.jsonl has actions but chronicle is empty during a live turn).
- `opening_actions` only shown when there's no history AND no last_actions (prevents showing opening actions after the first turn).

**Import addition:** Add `_load_opening_from_chronicle` to the imports from `.panels`.

**Validation:** After a new game and page refresh, the opening narrative should be visible in the narrative panel. The pack picker should NOT auto-open.

#### Step 1.5 — Update imports in routes.py

**File:** `ccya/server/routes.py`

**What:** Add `_load_opening_from_chronicle` to the imports from `.panels`.

**Current import (lines 38-46):**
```python
from .panels import (
    _debug_context,
    _get_opening,
    _get_opening_actions,
    _get_opening_outcome_summary,
    _load_current_state,
    _load_last_actions,
    _load_recent_history,
)
```

**New import:**
```python
from .panels import (
    _debug_context,
    _get_opening,
    _get_opening_actions,
    _get_opening_outcome_summary,
    _load_current_state,
    _load_last_actions,
    _load_opening_from_chronicle,
    _load_recent_history,
)
```

### Verification for Phase 1

1. Start a new game. Verify chronicle.md contains `\n## Turn 0 — Seed\n\n{opening narrative}`.
2. Refresh the page. Verify the opening narrative is visible in the narrative panel.
3. Play several turns. Verify the narrative panel shows the opening + last 8 turns.
4. Refresh the page. Verify the opening + last 8 turns are visible.
5. Verify ev.py still works (reads events.jsonl, not chronicle).
6. Verify turn_viewer still works (reads events.jsonl + state.yaml).

---

## Implementation — Phase 2: Frontend

### Context files to load
- `ccya/templates/index.html` — narrative panel template, empty-state logic, actions zone

### Detailed steps

#### Step 2.1 — Fix empty-state condition in template

**File:** `ccya/templates/index.html`

**What:** Modify the empty-state condition to show the empty prompt only when there's truly no narrative (no opening AND no history). Currently it checks `not history and not state.location.id`, but should also consider the opening.

**Current code (lines 138-142):**
```html
{% if not history and not state.location.id %}
<p class="empty-state" id="empty-prompt" style="padding: 8px 0;">
    No game loaded yet. Click <strong style="color: var(--text-primary)">New Game</strong> to begin.
</p>
{% endif %}
```

**New code:**
```html
{% if not history and not opening and not state.location.id %}
<p class="empty-state" id="empty-prompt" style="padding: 8px 0;">
    No game loaded yet. Click <strong style="color: var(--text-primary)">New Game</strong> to begin.
</p>
{% endif %}
```

**Why:** The empty prompt should only show when there's truly no game content. If the opening exists (seed narration loaded from chronicle), there IS narrative content even if history is empty.

**Validation:** After a new game and page refresh, the empty prompt should NOT appear. The opening narrative should be visible instead.

#### Step 2.2 — Verify Alpine `hasNarrative` consistency

**File:** `ccya/templates/index.html`

**What:** Verify that the Alpine `hasNarrative` property matches the server-side `has_narrative` context. Both should be `true` when opening or history exists.

**Current code (line 1031):**
```javascript
hasNarrative: {{ 'true' if has_narrative else 'false' }},
```

**Current route context (line 194):**
```python
ctx["has_narrative"] = bool(opening or history)
```

**Status:** Already consistent. No change needed. The fix in Phase 1 ensures `opening` is populated from chronicle, so `has_narrative` will be `true` when the opening exists.

### Verification for Phase 2

1. Start a new game. Refresh the page. Verify the empty prompt does NOT appear.
2. Verify the opening narrative is visible in the narrative panel.
3. Verify the pack picker does NOT auto-open on refresh.
4. Verify the choice buttons are visible after the first turn completes.
5. Refresh the page. Verify the choice buttons are still visible.

---

## Documentation Updates

- **`docs/repomap.md`:** Update the `_load_recent_history` section to note that it excludes turn 0 (seed narration).
- **`docs/architecture/OVERVIEW.md`:** Update the data persistence section to note that the seed narration is stored in chronicle.md as turn 0.
