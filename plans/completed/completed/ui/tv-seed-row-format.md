# Turn viewer: render seed as a turn 0 row

## Status
`completed`

## Phases

2 phases: inject seed row into turns data, then add template + JS rendering.

## Issue

Seed state (initial game state at turn 0) is currently rendered as a static seed card in the `{% else %}` template branch — the branch that only shows when `turns` is empty. This means:
1. It disappears entirely after the first turn is taken
2. Its visual format (custom `<details>` sections) doesn't match the turn viewer's existing visual language
3. No JSON syntax highlighting or consistent header layout

## Solution

Instead of returning `seed_info` as a separate value from `_turn_viewer_data`, inject a synthetic row with `row_kind: "seed"` into the `turns` list at index 0. Render this row in the Alpine.js `x-for` loop with a template section modeled after the compaction bar — a header with badge + title, and an expandable body showing the full seed state as highlighted JSON.

## Firm decisions

1. Seed row uses `row_kind: "seed"` — distinct from `"compaction"` and regular turn rows
2. The seed row collapse key is the literal string `"seed"` to avoid collision with turn 0 or compaction rows
3. `_turn_viewer_data` returns to a 2-tuple `(turns, no_events)` — seed_info is no longer a separate return value
4. Both endpoints (SSR `/turn_viewer`, JSON `/turn_viewer/data`) simplify to just `turns + no_events`
5. Seed row body shows the entire seed state as formatted JSON with syntax highlighting
6. Seed row always visible through all filters
7. Seed row default-collapsed if there are any real turns, default-open otherwise (matching compaction behavior: collapsed if `i > 0`)

## Non-goals

- No seed generation prompts — user explicitly said "I just need a seed row but just outputs"
- No pills or per-stage breakdowns — user said "don't need pills necessary"
- No state diff coloring (seed is initial state, nothing to diff against)

## Risks, Ambiguities, and Blockers

- The `_collapseTurns` JS function and `visibleTurns` filter function need updates to handle the new `row_kind: "seed"`
- JSON serialization: ensure the seed state is serializable through the existing `turns | tojson` pipeline (it is — `load_state` returns dicts, `json.dumps` handles those)

## Implementation — Phase 1: Inject seed row in tv.py + endpoints

### Context files to load

- `ccya/server/tv.py` — `_turn_viewer_data()` function
- `ccya/server/routes.py` — both turn_viewer endpoints (SSR and JSON API)

### Detailed steps

#### Step 1.1 — Inject seed row into turns list

**File:** `ccya/server/tv.py`

**What:** In `_turn_viewer_data()`, remove the `seed_info` return value. Instead, after computing seed state (same logic as before), inject a synthetic row into the `turns` list at index 0 (most recent, before reverse).

The seed row dict:
```python
{
    "row_kind": "seed",
    "turn": 0,
    "pack_type": seed_type,
    "pack_source": pack_source,
    "seed_json": json.dumps(seed_state, indent=2),
}
```

Where `seed_state` is a cleaned dict containing: `pc`, `location`, `inventory`, `scene`, `compendium`, `arc`, `__seed_meta__` (if dynamic). This gets pretty-printed into `seed_json` for syntax highlighting.

**Why:** The seed row becomes part of the regular turns list, visible at index 0 alongside all other turns. It never disappears.

**Validation:** `uv run python -c "from pathlib import Path; from ccya.server.tv import _turn_viewer_data; t, n = _turn_viewer_data(Path('/tmp/test-turn-viewer')); assert len(t) > 0; assert t[0]['row_kind'] == 'seed'"`

#### Step 1.2 — Restore return type and update endpoints

**File:** `ccya/server/tv.py` and `ccya/server/routes.py`

**What:** Change `_turn_viewer_data` return type back to `tuple[list[dict[str, Any]], bool]`. Remove `seed_info` from the 3-tuple. Update both endpoints in routes.py:
- SSR endpoint: remove `seed_info` unpacking and context passing
- JSON endpoint: remove `seed_info` from response dict

**Why:** The seed data is now embedded in the turns list — no separate channel needed.

**Validation:** `uv run python -c "import inspect; from ccya.server import tv; sig = inspect.signature(tv._turn_viewer_data); assert sig.return_annotation.__args__[1] is bool"` (check return type has 2 elements)

### Tests to write or update

Tests are deferred during refactor per AGENTS.md.

### REPOMAP updates required

- `docs/repomap.md` line ~35: Update tv.py entry — change `_turn_viewer_data()` returns `(rows, no_events, seed_info)` back to `(rows, no_events)` and note seed row injection

## Implementation — Phase 2: Template + JS + CSS cleanup

### Context files to load

- `ccya/templates/_turn_viewer.html` — Alpine.js loop, collapse/visible functions
- `ccya/static/app.src.css` — seed card CSS classes to replace

### Detailed steps

#### Step 2.1 — Add seed row template section

**File:** `ccya/templates/_turn_viewer.html`

**What:** Add a new `<template x-if="t.row_kind === 'seed'">` block in the Alpine `x-for` loop, ordered before the compaction check (seed is turn 0, shown first). Modeled after compaction:

```html
<template x-if="t.row_kind === 'seed'">
    <div class="tv-turn-card">
        <div class="tv-compaction-header" @click="toggleTurnCollapsed('seed')">
            <span class="tv-compaction-icon">✦</span>
            <span class="tv-compaction-title">Seed</span>
            <span class="tv-stage-badge" x-text="t.pack_type"></span>
            <span class="tv-compaction-range" x-text="t.pack_source"></span>
            <span class="tv-stage-chevron" :class="{ open: !isTurnCollapsed('seed') }">▶</span>
        </div>
        <div class="tv-compaction-body" x-show="!isTurnCollapsed('seed')">
            <pre class="tv-pre"><code class="language-json" x-effect="tvInitJsonBlock($el, t.seed_json)"></code></pre>
        </div>
    </div>
</template>
```

Reuse existing CSS classes: `tv-turn-card`, `tv-compaction-header`, `tv-compaction-title`, `tv-stage-badge`, `tv-compaction-range`, `tv-stage-chevron`, `tv-compaction-body`, `tv-pre`. These are already defined and styled.

**Why:** Matches existing visual language. The seed row gets the same header/body structure as compaction and turn rows.

**Validation:** `uv run python ...` (render template with seed row in data, verify `tv-seed-*` not present in output, verify `✦ Seed` header present)

#### Step 2.2 — Update JavaScript functions

**File:** `ccya/templates/_turn_viewer.html`

**What:** Update three JS functions:

1. `_collapseTurns()` — handle seed key:
```javascript
var key = t.row_kind === 'compaction' ? 'c-' + t.turn : 
          t.row_kind === 'seed' ? 'seed' : t.turn;
```

2. `visibleTurns()` — seed always visible:
```javascript
if (t.row_kind === 'seed') return true;
```
Add this above the compaction check in the filter.

3. `navToIdx()` — handle seed key in scroll:
```javascript
var key = t.row_kind === 'compaction' ? 'c-' + t.turn : 
          t.row_kind === 'seed' ? 'seed' : t.turn;
```
Replace the existing key computation line.

**Why:** Without these, the seed row would be filtered out or use the wrong collapse key.

**Validation:** Visual test in browser.

#### Step 2.3 — Clean up old seed card

**File:** `ccya/templates/_turn_viewer.html`

**What:** Remove the `{% if seed_info %}...{% elif no_events %}...{% else %}...{% endif %}` block from the `{% else %}` branch (lines 308-373). Replace with something simple. The `{% else %}` branch only renders when `turns` is falsy, which happens when:
- events.jsonl doesn't exist at all → no_events=True → show "No events found"
- events.jsonl exists but game never started → seed has no data → show "No turns recorded"

But now seed is a row in turns. When does turns remain empty?
- events.jsonl doesn't exist → early return `[], True`
- events.jsonl exists but empty + no seed data → no seed row injected → `[][], False` → empty

So the `{% else %}` branch still needs:
```html
{% if no_events %}
<div class="turn-viewer-no-events">No events found. Start a game to generate turn data.</div>
{% else %}
<div class="turn-viewer-empty">No turns recorded yet.</div>
{% endif %}
```

**Why:** Removes dead code that rendered the old seed card.

**Validation:** Visual test — fresh game page shows seed row, no old seed card.

#### Step 2.4 — Clean up seed CSS

**File:** `ccya/static/app.src.css`

**What:** Remove the entire `.tv-seed-card` through `.tv-seed-conditions` block (lines ~2357-2434). These CSS classes are no longer used.

But wait — I should keep them in case the user wants to reference them later. Actually, per AGENTS.md: "Remove dead code immediately." So remove them.

Actually, there might still be CSS needed. Let me check what CSS classes the new template uses:
- `tv-turn-card` — already defined
- `tv-compaction-header` — already defined
- `tv-compaction-icon` — already defined
- `tv-compaction-title` — already defined
- `tv-stage-badge` — already defined
- `tv-compaction-range` — already defined
- `tv-stage-chevron` — already defined
- `tv-compaction-body` — already defined
- `tv-pre` — already defined (part of turn card rendering)

No new CSS needed! All classes already exist.

**Why:** Removes unused CSS per clean code rules.

### Tests to write or update

Deferred per AGENTS.md.

### REPOMAP updates required

- `docs/repomap.md` line ~35: Update tv.py entry to remove seed_info from return type mention
