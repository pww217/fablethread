# Review: Entity Highlighting (commit 8d95174)

## Scope
- Prompt: removed bold instruction from `narrate_system.j2` and `SYSTEM_PROMPTING.md`
- CSS: `.entity-npc`, `.entity-item`, `.entity-pc`, `.entity-location` in `app.src.css`
- JS: `_highlightEntities()` function + wiring in `turn_complete` and `DOMContentLoaded` in `index.html`

## Contract validation (all pass)
- `_highlightEntities(container, state)` signature matches both call sites
- State shape: `compendium.npcs`, `inventory`, `pc`, `location` all present in `result.state`
- `tojson` filter is registered in Jinja env
- `app.css` is rebuilt from `app.src.css` (verified Tailwind build step)

## Correctness (all pass)
- Safe against empty/null state (optional chaining everywhere)
- Safe against XSS (`textContent`, not `innerHTML`)
- Double-wrapping guard: skips text nodes inside `<strong>`, `<em>`, `<a>`, existing `entity-*` spans
- No regex escaping issues (uses `String.indexOf`, not `RegExp`)
- Sorted by length descending for longest-first matching
- Initial-state fails silently on parse failure

## Design tradeoff (accepted)
- **One entity match per original text node** — the `break` after the first match means only the first entity name per text node gets highlighted. In practice, entity references separated by punctuation/paragraphs land in different text nodes, so this fires once per entity in most sentences. Acceptable per the plan.

## Documentation
- Updated `SYSTEM_PROMPTING.md` (removed "bolding rules" from description)
- FEATURE-IDEAS.md entry added as F-I13 (FIXED)
- No `docs/architecture/`, `docs/repomap.md`, or `AGENTS.md` changes needed

## Out of scope (unchanged per user)
- `charCreation()` stat budget 10→11 and archetype value changes — pre-existing in worktree, not part of this feature
