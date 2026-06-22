# Fluid UI Sizing

## Purpose

Make the CCYA web UI automatically scale to fit any browser window size so players never need to manually zoom (Ctrl/Cmd +/-).

## Problem Statement

The entire UI uses fixed `px` font sizes and rigid 320px sidebars. On smaller screens or high-DPI displays, content is too small; on large monitors it's cramped. Users must manually zoom the browser to make the UI usable. There are no intermediate breakpoints between desktop (>768px) and mobile (≤768px), leaving laptops and tablets with a one-size-fits-all layout that doesn't adapt to available space.

## Constraints

- Must not change the visual design at the default 14px base — current appearance is correct
- Must preserve all existing responsive behavior on ≤768px (mobile drawer system)
- Must work without JS for basic sizing (CSS-only scaling); JS only handles sidebar width persistence
- Must be a single-file change where possible to minimize risk

## Non-goals

- No new breakpoints or layout restructuring beyond what's needed for proportional sizing
- No changes to mobile-specific behavior at ≤768px
- No JavaScript-based font scaling (keep it CSS-only)
- No support for dynamic runtime resizing after page load (window resize handled by browser reflow of fluid units)

## Solution

Set a fluid base on the `html` element using CSS `clamp()`, then convert all 195 font-size declarations from fixed `px` to relative `rem`. Make sidebar widths proportional (`min(320px, 28vw)` instead of rigidly 320px). Everything scales proportionally with viewport width.

## Firm decisions

1. **Base font size uses clamp:** `html { font-size: clamp(12px, 1.5vw, 17px); }` — minimum 12px (readable), default ~14px on typical screens, maximum 17px for large monitors
2. **All fonts use rem units** relative to the html base — no individual element clamp values needed
3. **Sidebars proportional:** `min(320px, 28vw)` with a JS-enforced minimum of 180px on drag-resize
4. **Only one file changed:** `ccya/static/app.src.css` (the compiled output will be regenerated via the build step)

## Risks, Ambiguities, and Blockers

- **Risk:** Some very small UI text (9px → ~0.64rem at minimum base) may become hard to read on smallest screens. Mitigation: clamp minimum of 12px keeps even 9px elements at readable sizes
- **Risk:** Drag-resize JS enforces a hardcoded 180px sidebar minimum — this is fine since proportional widths will naturally stay above that on most screens
- **Ambiguity:** The compiled CSS (`app.css`) needs to be regenerated after editing `app.src.css`. Verify the build command.

## Status

`completed`

## Phases

N/A — single phase, single file change.

---

## Implementation — Phase 1: Convert all sizing to fluid units

### Context files to load
- `/Users/pwilson/Repos/ccya/ccya/static/app.src.css` (primary target)

### Detailed steps

#### Step 1.1 — Set fluid base font size on html element

**File:** `ccya/static/app.src.css`, line ~61

**What:** Replace the existing `html, body { height: 100%; margin: 0; }` block with a new rule that sets a fluid base font size via clamp():

```css
*, *::before, *::after { box-sizing: border-box; }
html, body { height: 100%; margin: 0; }
html { font-size: clamp(12px, 1.5vw, 17px); }
```

**Why:** Establishes a responsive base that scales from 12px (small screens) to ~14px (typical desktops) to 17px (large monitors). Everything using `rem` will scale proportionally.

**Validation:** At viewport widths of:
- 320px → html ≈ 12px
- 960px → html ≈ 14px  
- 1440px → html ≈ 15.7px
- 1920px+ → html caps at 17px

#### Step 1.2 — Convert body font-size from px to rem

**File:** `ccya/static/app.src.css`, line ~67

**What:** Change `font-size: 14px;` on the `body` selector to `font-size: 1rem;`.

**Why:** The base body text should inherit directly from the html clamp. This is the reference point for all rem values throughout the file.

**Validation:** Body text renders at ~14px on typical desktops, scales up/down with viewport.

#### Step 1.3 — Convert ALL remaining font-size declarations from px to rem

**File:** `ccya/static/app.src.css` (all occurrences of `font-size: Npx`)

**What:** Systematically convert every remaining `font-size: <N>px;` declaration to use the equivalent in rem, calculated against a 14px base. Use this conversion table for reference:

| px | rem (rounded) |
|----|---------------|
| 9  | 0.64rem       |
| 10 | 0.71rem       |
| 10.5 | 0.75rem     |
| 11 | 0.79rem       |
| 11.5 | 0.82rem     |
| 12 | 0.86rem       |
| 13 | 0.93rem       |
| 14 | 1rem          |
| 15 | 1.07rem       |
| 16 | 1.14rem       |
| 17 | 1.21rem       |
| 18 | 1.29rem       |
| 24 | 1.71rem       |
| 28 | 2rem          |
| 48 | 3.43rem       |

**Exceptions:**
- `font-size: inherit;` — leave as-is (line 3045)
- `font-size: 0;` — leave as-is (mobile turn-log-toggle, line 1789)
- `font-size: 0.65rem;` and `font-size: 0.8rem;` — already relative, leave as-is (lines 2583, 1745)
- Mobile media query values (`@media (max-width: 768px)`): convert to rem using the same table

**Why:** Every font in the UI must be relative to the html base for proportional scaling. This is a bulk find-and-replace across all 195 declarations, minus the exceptions above.

**Validation:** Run `make check` after completion. Visually verify that:
- Desktop layout at default viewport looks identical (base ~14px)
- Narrative text remains readable
- Sidebar labels and small UI elements are legible
- Mobile drawer system still works correctly

#### Step 1.4 — Make sidebar widths proportional

**File:** `ccya/static/app.src.css`, line ~47 (`--sidebar-w`) and line ~493 (`.sidebar`)

**What:** Change the CSS variable from a fixed value to a proportional one:
```css
--sidebar-w: min(320px, 28vw);
```

This automatically updates both the `var(--sidebar-w)` reference on `.sidebar` and any other selectors that use it.

**Why:** Sidebars currently lock at 320px regardless of screen width, causing horizontal overflow or cramped narrative columns on smaller screens. Proportional widths let sidebars shrink with available space while maintaining a reasonable maximum.

**Validation:** At various viewport widths:
- ~1024px → sidebar ≈ 286px (slightly narrower than default)
- 769px → sidebar ≈ 215px (narrative gets more room, sidebars still functional)
- >1143px → sidebar caps at 320px

#### Step 1.5 — Update drag-resize minimum to match proportional behavior

**File:** `ccya/static/app.src.css` or JS in index.html where the 180px minimum is enforced

**What:** Verify that the drag-resize JS still uses a 180px minimum floor for sidebars. This should remain unchanged since it's a hard lower bound regardless of proportional sizing.

**Why:** Users may manually shrink sidebars below what vw would naturally produce; the 180px floor prevents unusably narrow panels.

**Validation:** Drag-resize still works, sidebar doesn't go below 180px on any screen size.

### Tests to write or update

None — tests are temporarily removed during refactor per AGENTS.md. Verify via `make check` (lint + typecheck) and manual visual inspection across viewport widths:
- 375px (mobile, should trigger drawer system unchanged)
- 768px (boundary between mobile/desktop layouts)
- 1024px tablet portrait
- 1280px laptop
- 1920px desktop
