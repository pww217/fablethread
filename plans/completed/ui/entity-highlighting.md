# Entity Highlighting in Narration

## Purpose

Replace LLM-driven `**bold**` formatting of NPC names, inventory items, and other stateful entities with programmatic client-side coloring — making entity references visually distinct without burdening the LLM.

## Problem Statement

The `narrate_system.j2` prompt instructed the LLM to emit `**bold**` for NPC names (first introduction) and inventory items (when used). This consumed LLM output tokens, added formatting noise to the prompt, and resulted in inconsistent application. The LLM is not a reliable formatter — bold was sometimes applied late, missed items, or appeared on partial names.

## Constraints

- Zero server-side pipeline changes. No new endpoints, no state plumbing, no prompt rework beyond what's already done.
- Must work within the existing markdown rendering path (marked.js → HTML).
- Must not double-wrap or interfere with existing `<strong>`/`<em>`/`<a>` tags.
- Entity data must come from `result.state` already present in the `turn_complete` event — no new data fetching.

## Non-goals

- Highlighting during streaming text reveal (entity data not available until turn_complete).
- Highlighting in CLI/ev play output (debugging tool, not player-facing).
- Server-side entity matching or HTML injection.
- Custom markdown syntax or marked.js extensions.

## Solution

A client-side JS function `_highlightEntities(container, state)` that walks text nodes inside rendered narrative blocks and wraps known entity names in colored `<span>` tags with CSS classes. Applied on `turn_complete` after `_renderMarkdown()` and before `_applyMarkdown().` Also applied on `DOMContentLoaded` for initial page-load history, using the server-rendered state passed via a JSON script tag.

## Firm decisions

1. Entity type → CSS class mapping: NPCs → `entity-npc`, items → `entity-item`, PC → `entity-pc`, location → `entity-location`.
2. Full-name matching only (e.g. `Mira Sovak`, not `Mira`). Prevents false positives on common given names.
3. Case-insensitive matching against lowercased name lookup.
4. Sort entity names by length descending so `Kestrel M4 Sniper Rifle` matches before `Kestrel M4`.
5. Skip text nodes already inside `<strong>`, `<em>`, `<a>`, or any existing `entity-*` span — no double-wrapping.
6. The initial page-load state is embedded as a `<script id="initial-state" type="application/json">` tag so `_highlightEntities` can run on server-rendered history blocks.

## Risks, Ambiguities, and Blockers

- NPC name collision with common English words: full-name matching mitigates, but a name like "Rose Carter" will match prose mentioning "Rose" + "Carter" separately. Acceptable risk — the full name "Rose Carter" must appear contiguously in text for a match.
- Entity names with regex special characters: names like "D'Artagnan" or "MC-5" need `RegExp` escaping. Must use a `String.prototype.replace` with a function-based matcher on lowercased text, not `new RegExp(name, 'gi')`.
- Location names like "the Rust Bucket" — the determiner "the" before it won't be highlighted. Only the canonical name itself gets wrapped. Acceptable — the color still draws attention.

## Status

`completed`

## Phases

1. Client-side JS + CSS: highlighting function, entity collection, DOM wiring, styling.

## Implementation — Phase 1: Client-side entity highlighting

### Context files to load

- `ccya/templates/index.html` (JS `game()` Alpine component, `_renderMarkdown`, `_applyMarkdown`, DOMContentLoaded handler)
- `ccya/templates/_state_left.html` (NPC name display format)
- `ccya/static/app.css` (existing CSS patterns for coloring reference)

### Detailed steps

#### Step 1.1 — Add CSS classes for entity highlighting

**File:** `ccya/static/app.css`

**What:** Add four CSS class sets targeting entity span styling:

```css
.entity-npc    { color: var(--accent-npc, #e06c75); }
.entity-item   { color: var(--accent-item, #61afef); }
.entity-pc     { color: var(--accent-pc, #98c379); }
.entity-location { color: var(--accent-location, #d19a66); }
```

Base fallback colors use a warm-red for NPCs (distinct, signals a person), blue for items (neutral/inventory), green for PC (self-reference), orange for locations (place marker).

**Why:** CSS classes keep styling out of JS and make future theme changes trivial.

**Validation:** grep confirms the file exists and is referenced in `index.html` at line 11.

#### Step 1.2 — Add `_highlightEntities()` JS function

**File:** `ccya/templates/index.html` (insert after `_applyMarkdown()` definition, around line 2281)

**What:** A pure function that:
1. Accepts a container element and the state dict.
2. Collects entity names from state:
   - NPC names: `Object.values(state.compendium.npcs).map(e => e.name).filter(Boolean)`
   - Inventory item names: `state.inventory.map(i => i.name).filter(Boolean)`
   - PC name: `state.pc.name`
   - Location name: `state.location.name`
3. Sorts collected names by descending length.
4. Walks all text nodes in the container (using a TreeWalker with `NodeFilter.SHOW_TEXT`).
5. For each text node, checks if its lowercased content contains any entity name. If so, splits the text node around the match and inserts a `<span class="entity-{type}">` containing the matched text (preserving original case from the text node).
6. Skips text nodes whose parent is already `<strong>`, `<em>`, `<a>`, or a span whose class starts with `entity-`.

```javascript
function _highlightEntities(container, state) {
    if (!state || !container) return;
    const names = [];

    // Collect NPC names
    const npcs = (state.compendium && state.compendium.npcs) || {};
    for (const id in npcs) {
        const entry = npcs[id];
        if (entry && entry.name) names.push({ name: entry.name, cls: 'entity-npc' });
    }

    // Collect inventory item names
    const inv = state.inventory || [];
    for (const item of inv) {
        if (item && item.name) names.push({ name: item.name, cls: 'entity-item' });
    }

    // Collect PC name
    if (state.pc && state.pc.name) names.push({ name: state.pc.name, cls: 'entity-pc' });

    // Collect location name
    if (state.location && state.location.name) names.push({ name: state.location.name, cls: 'entity-location' });

    if (!names.length) return;

    // Sort descending by length to match longest first
    names.sort((a, b) => b.name.length - a.name.length);

    // Walk text nodes
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);

    for (const textNode of textNodes) {
        // Skip if parent is already an entity or formatting tag
        const p = textNode.parentNode;
        if (p && (p.tagName === 'STRONG' || p.tagName === 'EM' || p.tagName === 'A'
            || (p.tagName === 'SPAN' && p.className && p.className.startsWith('entity-')))) {
            continue;
        }

        const text = textNode.textContent;
        const lower = text.toLowerCase();
        let replaced = false;

        for (const { name, cls } of names) {
            const idx = lower.indexOf(name.toLowerCase());
            if (idx === -1) continue;

            replaced = true;
            const before = text.slice(0, idx);
            const match = text.slice(idx, idx + name.length);
            const after = text.slice(idx + name.length);

            const frag = document.createDocumentFragment();
            if (before) frag.appendChild(document.createTextNode(before));
            const span = document.createElement('span');
            span.className = cls;
            span.textContent = match;
            frag.appendChild(span);
            if (after) frag.appendChild(document.createTextNode(after));

            textNode.parentNode.replaceChild(frag, textNode);
            break; // one entity match per text node — avoids nesting
        }
    }
}
```

**Signature:**

```javascript
function _highlightEntities(container: HTMLElement, state: object): void
```

**Why:** Text-node walking is the only reliable way to insert inline HTML without breaking existing markup. The `skip-if-parent-is-entity` guard prevents double-wrapping when the function runs on already-highlighted content (e.g. after HTMX swaps).

**Validation:** Manual: open narrative, verify known NPC names appear in accent color.

#### Step 1.3 — Embed initial state on page load

**File:** `ccya/templates/index.html` (inside `<body>`, before the closing `</body>` or in the head)

**What:** Add a JSON script tag containing the serialized game state so `_highlightEntities` can run on server-rendered history blocks at DOMContentLoaded.

```html
<script id="initial-state" type="application/json">{{ state | tojson }}</script>
```

**Why:** Without serialized state, page-load history blocks cannot be highlighted (JS has no access to entity names until a turn_complete event fires and provides `result.state`).

**Validation:** Page source shows `<script id="initial-state">` with valid JSON. No syntax errors.

#### Step 1.4 — Wire `_highlightEntities` into `turn_complete` handler

**File:** `ccya/templates/index.html` (inside the `turn_complete` event listener, after line 1853's `_applyMarkdown(block)`)

**What:** Add a single call after `_applyMarkdown(block)`:

```javascript
_highlightEntities(block, result.state);
```

**Why:** At this point the narrative block has been fully rendered via `_renderMarkdown()` and any `[data-md]` elements processed. Entity highlighting is the final visual pass.

**Validation:** After a turn completes, NPC names and item names in the new narrative block are colored.

#### Step 1.5 — Wire `_highlightEntities` into `DOMContentLoaded`

**File:** `ccya/templates/index.html` (inside the `DOMContentLoaded` listener, after line 2461's `_applyMarkdown()`)

**What:** After `_applyMarkdown()`, read the initial state script tag and highlight history blocks:

```javascript
const stateScript = document.getElementById('initial-state');
if (stateScript) {
    try {
        const initState = JSON.parse(stateScript.textContent);
        document.querySelectorAll('.narrative-block .narrative-text').forEach(el => {
            _highlightEntities(el, initState);
        });
    } catch (e) { /* state JSON parse failure — skip highlighting */ }
}
```

**Why:** Server-rendered history blocks exist in the DOM at page load. Without this call, they remain unhighlighted until the next turn.

**Validation:** On page load with existing history, NPC names in previous turns' narratives are colored.

### Tests to write or update

No automated tests. This is purely a front-end presentation change. Manual verification:
1. Start a new game, play 1-2 turns.
2. Verify NPC names (e.g. "Mira Sovak") appear in red/warm accent.
3. Verify inventory item names (e.g. "Kestrel M4") appear in blue.
4. Verify PC name appears in green.
5. Verify bold from old turns (pre-change) still renders as `<strong>` via marked.js — no double-processing.
6. Load an existing save with history — verify highlighting on page load.
