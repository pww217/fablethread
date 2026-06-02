# Mobile UI — Verification & Polish

## Purpose

Verify the mobile UI implementation is correct, rebuild the compiled CSS, run static checks, and fix any edge cases discovered during review.

## Problem Statement

The mobile UI design and implementation have evolved iteratively. The compiled CSS (`app.css`) may be stale, and no verification pass has been run against the final state. Lint + typecheck must pass, and the mobile layout should be visually confirmed at key breakpoints.

## Constraints

- No server-side changes (no Python, no routes, no templates other than `index.html`)
- Desktop experience (> 768px) must be identical — no regression

## Non-goals

- No new features or design changes
- No changes to sidebar card content or structure

## Solution

One-phase plan: rebuild CSS, run `make check`, and spot-check the mobile layout at 375px, 414px, and 768px viewport widths. Fix any issues found.

## Firm decisions

1. `app.css` is compiled from `app.src.css` via `make css` (Tailwind CLI)
2. `make check` = `make lint` (ruff) + `make typecheck` (mypy)
3. Desktop regression risk is zero — all mobile changes are inside `@media (max-width: 768px)`
4. Settings panel does not get fullscreen mobile override — `width: min(480px, 94vw)` is adequate

## Risks, Ambiguities, and Blockers

None. This is a verification pass on already-implemented code.

## Status
`open`

## Phases

1 phase: Verify rebuild, static checks, and visual state.

## Implementation — Phase 1: Build & Verify

### Context files to load

- `ccya/static/app.src.css` (mobile block at lines 1759–1932)
- `ccya/static/app.css` (compiled output)
- `Makefile` (build targets)
- `pyproject.toml` (lint/typecheck config)

### Detailed steps

#### Step 1.1 — Rebuild compiled CSS

**File:** `Makefile` (target: `css`)

**What:** Run `make css` to regenerate `app.css` from `app.src.css`.

**Why:** `app.css` is what the browser loads; it must be in sync with source.

**Validation:**
```
make css
# Verify: grep for mobile-specific rules in app.css
grep 'sidebar--open' ccya/static/app.css
```

#### Step 1.2 — Run lint + typecheck

**File:** `Makefile` (target: `check`)

**What:** Run `make check`.

**Why:** Static analysis must pass.

**Validation:**
```
make check
# Expected: zero errors
```

#### Step 1.3 — Verify mobile CSS rules in compiled output

**File:** `ccya/static/app.css`

**What:** Confirm key mobile rules survive the Tailwind compilation. Spot-check:
- `@media (max-width: 768px)` block exists
- `.sidebar { height: 100dvh; width: 100dvw !important; }` present
- `.sidebar-toggle--right::before` / `.sidebar-toggle--left::after` rules present
- `.header-logo { display: none }` present
- `.sidebar-backdrop` rules present
- `.pack-picker-modal { width: 100dvw; height: 100dvh; }` present
- `.turn-log-panel { border-radius: 0; }` present

**Why:** Tailwind may strip rules it considers unused; confirm the mobile block survives.

**Validation:**
```
# Manual checks, no test framework
echo "Checking for key mobile CSS rules..."
grep -q '100dvw' ccya/static/app.css && echo "OK: fullscreen width"
grep -q '100dvh' ccya/static/app.css && echo "OK: fullscreen height"
grep -q 'sidebar--open' ccya/static/app.css && echo "OK: drawer open class"
```

#### Step 1.4 — Manual visual check

**What:** Load the app in a browser at ≤ 768px viewport width. Verify:
1. Header shows: Player ← | 📖 Chronicle | → World
2. Scene tagline is absent from header
3. Tap Player → right drawer opens full-screen with ✕ close button
4. Tap World → left drawer opens full-screen
5. Tap backdrop → both drawers close
6. Swipe right on narrative → left drawer opens
7. Swipe left on narrative → right drawer opens
8. Turn log button → chronicle opens edge-to-edge
9. Modals (pack picker) → fullscreen
10. Rotate to landscape at 375px → drawers still work, body scroll restores when closed
11. Resize above 768px → drawers auto-close, desktop layout returns

**Why:** Functional verification of all implemented mobile features.

**Validation:** Manual pass. Report any issues as bugs.

### Tests to write or update

Tests are temporarily removed during refactor (per AGENTS.md). No test changes needed.
