# Settings Panel Bug Fixes

## Purpose

Fix three critical issues in the settings modal: broken close button, missing config pre-population, and absent field tooltips.

## Problem Statement

The settings panel has three bugs that make it unusable as designed: (1) the escape key, backdrop click, and × close button all silently fail because JS references `window.appInstance` instead of `window._gameInstance`; (2) fields show defaults or blank values instead of actual config.yaml data because `loadSettings()` is never invoked before opening; (3) no field has any explanatory tooltip or hint text.

## Constraints

- All changes are in `ccya/templates/index.html`.
- No new dependencies or frameworks.
- Existing Alpine.js bindings (`x-model`, `:class`) must remain unchanged — only wiring and content added.
- Tooltip system already exists via `_bindTooltips()` using `.has-tooltip` class anchors with nested `.tooltip-body`.
- GET `/api/settings` returns correct flattened config; POST route is working (proven by save functionality).

## Non-goals

- No changes to backend routes or models.py.
- No redesign of settings panel layout or CSS.
- No new fields added or removed from the form.
- No tooltip content for "Save" button or status messages.

## Solution

Three targeted fixes in `index.html`: (1) rename all three `window.appInstance` references to `window._gameInstance`; (2) call `loadSettings()` within `openSettingsPanel()` before showing the modal; (3) add `.has-tooltip` elements with nested tooltip content to every field that needs explanation.

## Firm decisions

1. Close button fix: change `appInstance` → `_gameInstance`. No alternative variable name exists or is needed.
2. Config pre-population: call `loadSettings()` at the start of `openSettingsPanel()`, not wrapped around init — simpler and avoids stale state issues since modal can be reopened after config changes elsewhere.
3. Tooltips use existing `.has-tooltip` / `.tooltip-body` pattern already used in narrative column (see `_bindTooltips()` at line ~1874).

## Risks, Ambiguities, Blockers

- **Ambiguous: tooltip content for each field.** I'll write concise descriptions based on the plan doc's field definitions. If any description is inaccurate or unclear, it needs user review before merging.
- `loadSettings()` has no loading indicator during fetch — fields briefly flash defaults then update. Low risk since response is near-instant; acceptable tradeoff vs adding a spinner to this minimal plan scope.

## Status

`completed`

## Phases

1 phase: all three fixes in `index.html`.

---

## Implementation — Phase 1: Fix close button, pre-populate config, add tooltips

### Context files to load
- `ccya/templates/index.html` (lines ~1802–1819 for close button; lines ~1754–1762 and ~1787–1793 for settings logic; lines ~264–340 for field HTML)

### Detailed steps

#### Step 1.1 — Fix close button references

**File:** `ccya/templates/index.html`

**What:** In the DOMContentLoaded block (lines 1802–1819), change all three occurrences of `window.appInstance?.closeSettingsPanel()` to `window._gameInstance?.closeSettingsPanel()`. Specifically:
- Line 1807: backdrop click handler
- Line 1810: close button click handler  
- Line 1815: escape key handler

**Why:** Alpine's game component stores itself at `window._gameInstance` (line ~1021). There is no `window.appInstance`. All three handlers silently fail because `undefined?.closeSettingsPanel()` returns undefined.

**Validation:**
```bash
grep -n 'appInstance' ccya/templates/index.html
# Should return 0 results for appInstance; _gameInstance should appear in close handler context
grep -c '_gameInstance.*closeSettingsPanel' ccya/templates/index.html
# Expected: 3
```

#### Step 1.2 — Pre-populate config on modal open

**File:** `ccya/templates/index.html`

**What:** Add a call to `this.loadSettings()` at the start of `openSettingsPanel()` (line ~1787), before removing `.hidden`. The method should become:
```js
async openSettingsPanel() {
    await this.loadSettings();
    document.getElementById('settings-backdrop').classList.remove('hidden');
    const modal = document.getElementById('settings-modal');
    modal.classList.remove('hidden');
    modal.focus();
},
```

**Why:** `loadSettings()` is defined (line ~1754) but never invoked. Fields bind to an empty object `{}`, so number inputs are blank and toggles default to false/off regardless of actual config.yaml values.

**Validation:** After fix, open settings modal — fields should show: momentum_floor=-3, consecutive_pressure_threshold=3, thread_deescalate_on_success=on (toggle), character_creation_enabled=on (toggle), warmup_on_start=off (checkbox), debug_enabled=on (toggle).

#### Step 1.3 — Add tooltips to all settings fields

**File:** `ccya/templates/index.html`

**What:** Wrap or add `.has-tooltip` elements with nested `.tooltip-body` content for each field in the settings modal HTML (~lines 264–340). The tooltip system is already wired via `_bindTooltips()` — just need to add markup.

Add tooltips to these fields:

| Field | Tooltip text (concise) |
|---|---|
| Momentum Floor | Minimum momentum gain per turn, regardless of player success or failure. Keeps the game from stalling at zero. |
| Consecutive Pressure Threshold | Number of consecutive turns below momentum floor before pressure events trigger automatically. |
| De-escalate threads on success | When enabled, successful actions clear related thread state instead of accumulating it. Reduces narrative clutter over time. |
| Character Creation | Allow the engine to generate new characters during play based on player choices and story context. |
| Warmup on Server Start | Run a lightweight model warmup request when the server starts. Prevents first-request latency but adds ~5 seconds to startup. |

For "Warmup on Server Start", replace or augment the existing static hint `<span class="setting-hint">Requires server restart to take effect</span>` with a `.has-tooltip` element instead (the tooltip text covers this).

**How:** Each field's label should be wrapped in or adjacent to a `.has-tooltip` anchor. Example pattern for number fields:
```html
<label class="setting-row has-tooltip" data-tooltip-pos="top">
    <span class="setting-label">Momentum Floor</span>
    <div class="tooltip-body">Minimum momentum gain per turn, regardless of player success or failure.</div>
    <input type="number" x-model.number="settings.momentum_floor" min="-10" max="10"/>
</label>
```

For toggle fields:
```html
<label class="setting-row setting-toggle has-tooltip" data-tooltip-pos="top">
    <span class="setting-label">De-escalate threads on success</span>
    <div class="tooltip-body">When enabled, successful actions clear related thread state instead of accumulating it.</div>
    <button type="button" @click="settings.thread_deescalate_on_success = !settings.thread_deescalate_on_success" :class="{ 'toggle-on': settings.thread_deescalate_on_success }" class="setting-toggle-btn">
        <div class="toggle-knob"></div>
    </button>
</label>
```

For the warmup field, replace `<span class="setting-hint">Requires server restart to take effect</span>` with:
```html
<div class="tooltip-body">Run a lightweight model warmup request when the server starts. Prevents first-request latency but adds ~5 seconds to startup.</div>
```

**Why:** Users need context for what each setting does before changing it. The existing tooltip system is already functional and styled — just unused in this panel.

**Validation:** Open settings modal, hover over any field label or toggle — a `.tooltip-body` should appear near the element with descriptive text. All 6 fields (including warmup hint replacement) have tooltips.

### Tests to write or update

None per AGENTS.md directive: "Tests are temporarily removed during refactor." Manual verification only:
1. Open settings modal → verify all fields show actual config.yaml values
2. Click × close button, click backdrop outside panel, press Escape key → verify modal closes each time  
3. Hover over field labels/toggles → verify tooltip content appears
