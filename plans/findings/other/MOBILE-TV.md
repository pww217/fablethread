# Mobile Turn Viewer — Lessons Learned

## What was attempted

Add swipe-driven carousel navigation for the turn viewer on mobile (≤768px), replacing the two-column layout with single-panel swipe between pipeline and diff views.

## Why it failed

Tailwind's purge stripped **nearly all custom CSS** from `app.src.css` → `app.css`. Of ~50 `.tv-*` classes written, only 1 survived compilation. The mobile carousel styles (positioning, transforms, transitions) were completely absent from the compiled output, making both columns render in their default flexbox layout regardless of viewport width.

## Root cause

This project uses **Tailwind v4** as a utility-first framework that purges unused classes during build:

```
npx tailwindcss/cli -i ccya/static/app.src.css -o ccya/static/app.css --minify
```

Custom component-level CSS (`.tv-turn-columns`, `.tv-pipeline`, etc.) written in `app.src.css` gets stripped because Tailwind doesn't recognize these as utility classes or safelisted patterns. Only classes that appear in templates *and* match Tailwind's known utilities survive the purge — but even then, most custom selectors are dropped.

## What worked (briefly)

- **Alpine.js state management** (`turnColumns[turn]`, `carouselTransform()`) — pure JS, no CSS dependency
- **Swipe gesture detection** — standard touch events, works fine when paired with working CSS
- **Per-turn carousel logic** — extracted turn from event target via regex on element ID

## What didn't work

- Custom `.tv-*` class selectors in `app.src.css` → stripped by Tailwind purge
- Media queries inside the same file as utility classes → also purged
- Desktop styles for turn viewer survived (different mechanism), but mobile overrides were lost

## Key insight about this codebase

All custom UI styling must follow one of these patterns:

1. **Tailwind utility classes directly in templates** — e.g., `class="flex items-center gap-2"`
2. **Safelisted via Tailwind config** — explicit patterns that survive purge (requires modifying tailwind.config)
3. **Separate non-purged CSS file** — a static `.css` file served alongside the compiled one

The existing turn viewer uses pattern #1 for some elements but relies heavily on custom selectors in `app.src.css` which Tailwind strips. This is an architectural mismatch that wasn't apparent until implementation time.

## Alternative approaches for future work

### Option A: Rewrite with inline Tailwind utilities
Replace all `.tv-*` classes with utility class combinations directly in the template. Pros: works within existing build pipeline. Cons: verbose templates, loss of semantic naming, harder to maintain complex layouts like carousel transforms.

### Option B: Separate static CSS file
Create `ccya/static/tv-mobile.css` (or similar) that's served alongside `app.css` without Tailwind processing. Add a `<link>` tag in the turn viewer template for mobile-only styles via media query. Pros: full control over custom selectors, no purge issues. Cons: requires adding another asset pipeline entry point.

### Option C: Safelist patterns
Add regex safelists to Tailwind config matching `.tv-*` classes. Pros: keeps everything in one file. Cons: increases final CSS bundle size (all safelisted classes always included), requires modifying build config which may not be desired for this project.

## Recommendation

**Option B** — separate static CSS file — is the cleanest path forward because:
- Turn viewer already has its own template (`_turn_viewer.html`) and can include additional assets
- Keeps Tailwind's purge effective for the main game UI (where it works well)
- Preserves semantic class names and complex layout logic without bloat
- Minimal build pipeline changes

## Timeline

- Attempted: ~2 hours of implementation across 6 commits
- Reverted: all CSS/template/doc changes reverted to pre-mobile state
- Remaining work: choose one alternative approach above, write plan, implement
