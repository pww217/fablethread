# Settings Menu & Game Config Editor

## Purpose

Add a gear-icon menu in the top-right header bar providing game management actions (new game, retry turn) and an inline Settings panel for live-editing `game:` config.yaml fields with permanent persistence.

## Problem Statement

Game configuration is currently locked inside `config.yaml` — users must edit it manually or restart the server to change settings like momentum floor, pressure thresholds, or logging toggles. There's no UI affordance for game management actions either; "New Game" and "Retry Turn" are scattered as standalone buttons in the header bar with limited discoverability.

## Constraints

- Only expose fields under `game:` key in config.yaml
- Changes write back to `config.yaml` permanently (not runtime-only)
- LLM-specific settings take effect next turn; game/pacing settings apply immediately or on next action
- No backwards compatibility needed — trust the source of truth is config.yaml
- UI uses Alpine.js + HTMX; no new frameworks
- CSS follows Tailwind v4 design tokens in `app.src.css`

## Non-goals

- Exposing `llm:` or `server:` keys (future work)
- Config validation beyond basic type checks
- Undo/rollback of config changes
- Per-save vs global config — single server-wide config.yaml

## Solution

Add a gear icon button to the right side of `.header-bar`. Clicking it opens an Alpine.js dropdown with three items: "New Game", "Retry Turn", and "Settings". Selecting Settings opens a slide-out panel (right-drawer style or modal) that renders all `game:` fields as editable inputs grouped by category. A Save button POSTs changes to `/settings` which reads config.yaml, applies mutations atomically, writes back with yaml.dump(), and returns the updated game config for live refresh.

## Firm decisions

1. **Config persistence:** Write directly to `config.yaml`. Use a dedicated `save_config()` function in `ccya/models.py`.
2. **Scope:** Only `game:` section fields are exposed (momentum_floor, consecutive_pressure_threshold, thread_deescalate_on_success, warmup_on_start, character_creation_enabled, debug.enabled).
3. **UI pattern:** Dropdown menu from gear icon + slide-out settings panel on the right side of the screen (not a modal), consistent with existing drawer/sidebar patterns.
4. **Field types:** Integers use number inputs; booleans use toggle switches; nested keys like `debug.enabled` are flattened to simple labels.
5. **Config write strategy:** Read YAML → mutate dict in memory → yaml.dump() back to file (atomic via temp + rename).

## Risks, Ambiguities, and Blockers

- **yaml.dump formatting:** Will lose comments from config.yaml. Acceptable since user-facing edits are the source of truth going forward.
- **Config hot-reload:** After writing config.yaml, `_app_mod.config` needs to be updated in memory so subsequent turns use new values without restart. `engine_config` (EngineConfig dataclass) is built once at startup — need to decide whether to rebuild it or just mutate the game-specific fields on the fly.
- **warmup_on_start:** This field only makes sense at server start time; editing it mid-game has no effect until restart. The UI should show a "requires restart" indicator for this field.

## Status

`completed`

## Phases

Three phases: (1) Backend API for reading/writing game config, (2) Header dropdown menu with gear icon and action items, (3) Settings slide-out panel with live-editable fields and save flow.

---

## Implementation — Phase 1: Backend API for Game Config

### Context files to load
- `ccya/models.py` (load_config function at line ~491)
- `ccya/server/app.py` (_app_mod config reference pattern)
- `ccya/engine/config.py` (EngineConfig fields and build_engine_config mapping from game: section)

### Detailed steps

#### Step 1.1 — Add save_config() to ccya/models.py

**File:** `ccya/models.py`

**What:** After the existing `load_config()` function, add a matching `save_config(path=..., config_dict=...)` that writes YAML back to disk atomically (write to temp file then rename).

```python
def save_config(
    path: str | os.PathLike[str] = "config.yaml",
    config_dict: dict[str, Any] | None = None,
) -> None:
    """Write a config dict to YAML. Atomic via tmp + rename."""
    import yaml as _yaml

    if config_dict is None:
        config_dict = load_config(path)
    path = Path(path).resolve()
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        _yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
    tmp_path.replace(path)
```

**Why:** Provides the single source of truth for persisting config.yaml changes. Atomic write prevents corruption if server crashes mid-write.

**Validation:** `python -c "from ccya.models import load_config, save_config; c = load_config(); save_config('config.yaml', c); print(load_config())"` — round-trips without error or content change (modulo comment loss).

#### Step 1.2 — Add GET /settings route to read game config

**File:** `ccya/server/routes.py`

**What:** Add a new route handler:

```python
@_app_mod.app.get("/api/settings")
async def get_settings():
    """Return the current 'game:' section of config.yaml."""
    game_config = _app_mod.config.get("game", {})
    # Flatten nested keys for UI consumption
    debug = game_config.get("debug", {}) or {}
    return JSONResponse({
        "momentum_floor": game_config.get("momentum_floor"),
        "consecutive_pressure_threshold": game_config.get("consecutive_pressure_threshold"),
        "thread_deescalate_on_success": game_config.get("thread_deescalate_on_success"),
        "warmup_on_start": game_config.get("warmup_on_start", False),
        "character_creation_enabled": game_config.get("character_creation_enabled", True),
        "debug_enabled": debug.get("enabled", False),
    })
```

**Why:** Provides the API endpoint for the frontend to read current game config values on load. Returns a flat dict — no nested objects — so Alpine.js can bind directly without dot-path accessors.

**Validation:** `curl http://localhost:8765/api/settings` returns valid JSON with all six fields present and matching config.yaml values.

#### Step 1.3 — Add POST /settings route to update game config

**File:** `ccya/server/routes.py`

**What:** Add a new route handler that accepts partial or full updates:

```python
@_app_mod.app.post("/api/settings")
async def post_settings(request: Request):
    """Update the 'game:' section of config.yaml and return updated values."""
    data = await request.json()
    if not isinstance(data, dict):
        return JSONResponse({"error": "Expected JSON object"}, status_code=400)

    game_config = _app_mod.config.get("game", {})

    # Apply updates from request body
    for key in ("momentum_floor", "consecutive_pressure_threshold"):
        if key in data:
            val = int(data[key])
            game_config[key] = val

    for key in ("thread_deescalate_on_success", "warmup_on_start", "character_creation_enabled"):
        if key in data:
            val = bool(data[key])
            game_config[key] = val

    debug_section = game_config.get("debug", {}) or {}
    if "debug_enabled" in data:
        debug_section["enabled"] = bool(data["debug_enabled"])
    game_config["debug"] = debug_section

    # Persist to disk
    from ccya.models import save_config as _save_config
    _save_config("config.yaml", _app_mod.config)

    # Update in-memory config reference so subsequent turns see new values
    _app_mod.config["game"] = game_config

    # Rebuild engine_config — game fields (momentum_floor, etc.) are read from cfg.get("game")
    from ccya.engine import build_engine_config as _build_engine_config
    _app_mod.engine_config = _build_engine_config(_app_mod.config)

    return await get_settings()  # Return updated state
```

**Why:** Single endpoint for persisting config changes. Updates both disk and in-memory state so the running server picks up new values without restart (except warmup_on_start which is startup-only). Rebuilding engine_config ensures all fields are consistent after any game: or llm: change.

**Validation:** `curl -X POST http://localhost:8765/api/settings -H "Content-Type: application/json" -d '{"momentum_floor": 0}'` returns updated JSON and config.yaml on disk reflects the new value.

---

## Implementation — Phase 2: Header Dropdown Menu with Gear Icon

### Context files to load
- `ccya/templates/index.html` (header-bar section at lines 17–61)
- `ccya/static/app.src.css` (header styles around line 93, new-game-btn at line 141)

### Detailed steps

#### Step 2.1 — Add gear icon button to header bar

**File:** `ccya/templates/index.html`

**What:** Inside `.header-meta` div (line 33), add a gear icon button before the existing buttons:

```html
<div class="header-menu-wrapper" x-data="{ menuOpen: false }">
    <button type="button" 
            @click="menuOpen = !menuOpen; settingsPanelOpen = false"
            :aria-expanded="menuOpen"
            title="Menu"
            class="gear-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
            <circle cx="12" cy="12" r="3"/>
        </svg>
    </button>

    <!-- Dropdown menu -->
    <div x-show="menuOpen" 
         @click.away="menuOpen = false"
         x-transition:enter.transition.duration.100ms
         x-cloak
         class="header-menu-dropdown">
        <button type="button" class="menu-item menu-item--new-game" @click="openPackPicker(); menuOpen = false">
            New Game
        </button>
        <button type="button" class="menu-item menu-item--retry-turn" 
                x-show="turnNum > 0"
                :disabled="submitting || starting"
                @click="retryTurn(); menuOpen = false">
            ↻ Retry Turn
        </button>
        <div class="menu-divider"></div>
        <button type="button" class="menu-item menu-item--settings" 
                x-show="gameStarted && turnNum > 0"
                @click="openSettingsPanel(); menuOpen = false">
            Settings…
        </button>
    </div>
</div>
```

**Why:** Replaces the two standalone buttons ("New Game", "Retry ↻") in header-meta with a single gear icon that opens a dropdown. Keeps existing functionality (openPackPicker, retryTurn) intact via Alpine.js event handlers. The Settings item is only visible when an active game exists and at least one turn has been played.

**Validation:** Gear icon appears right-aligned before "New Game" button area; clicking it toggles the dropdown; click-away or selecting a menu item closes it; existing New Game / Retry Turn functionality unchanged.

#### Step 2.2 — Add Alpine.js state for settings panel and menu

**File:** `ccya/templates/index.html` (inside `game()` function)

**What:** Add two new reactive properties to the game() return object:

```javascript
menuOpen: false,
settingsPanelOpen: false,

openSettingsPanel() {
    this.settingsPanelOpen = true;
},

closeSettingsPanel() {
    this.settingsPanelOpen = false;
}
```

**Why:** Provides reactive state for the dropdown menu and settings panel visibility. The `menuOpen` is local to the gear-btn wrapper's x-data scope (inline), while `settingsPanelOpen` lives on the game instance since it controls a screen-level overlay.

**Validation:** Alpine.js bindings work; clicking Settings button sets `settingsPanelOpen = true`; close button or ESC key resets it to false.

#### Step 2.3 — Add CSS for gear icon and dropdown menu

**File:** `ccya/static/app.src.css` (append near header styles section)

**What:** New CSS rules:

```css
/* =========================================================
   HEADER MENU (gear button + dropdown)
   ========================================================= */

.header-menu-wrapper {
    position: relative;
    display: inline-flex;
}

.gear-btn {
    background: transparent;
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
    width: 34px;
    height: 34px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: color 150ms, border-color 150ms;
}

.gear-btn:hover {
    color: var(--text-primary);
    border-color: var(--border-strong);
}

.header-menu-dropdown {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius);
    min-width: 200px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    z-index: 100;
    display: flex;
    flex-direction: column;
}

.menu-item {
    background: transparent;
    border: none;
    color: var(--text-primary);
    padding: 10px 16px;
    text-align: left;
    font-size: 14px;
    cursor: pointer;
    transition: background 100ms;
    width: 100%;
}

.menu-item:hover:not(:disabled) {
    background: var(--bg-highlight);
}

.menu-item:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.menu-divider {
    height: 1px;
    background: var(--border-subtle);
    margin: 4px 0;
}
```

**Why:** Styles the gear button and dropdown menu to match existing design tokens. Dropdown is positioned below-right of the gear icon with proper z-index for overlay behavior.

**Validation:** CSS compiles into app.css (or dev serves from src); dropdown appears correctly positioned; hover states work; disabled state visible on out-of-scope items.

---

## Implementation — Phase 3: Settings Slide-Out Panel

### Context files to load
- `ccya/templates/index.html` (body content near line 221, before closing .app-shell)
- `ccya/static/app.src.css` (sidebar/drawer patterns for reference around lines 400+)
- `ccya/server/routes.py` (for the /api/settings endpoint from Phase 1)

### Detailed steps

#### Step 3.1 — Add settings panel overlay to index.html template

**File:** `ccya/templates/index.html`

**What:** Before the closing `</div><!-- .app-shell -->`, add a slide-out settings panel:

```html
<!-- Settings Panel Overlay -->
<template x-if="settingsPanelOpen">
    <div class="settings-overlay" @keydown.escape.window="closeSettingsPanel()">
        <div class="settings-backdrop" @click="closeSettingsPanel()"></div>
        <aside class="settings-panel" role="dialog" aria-labelledby="settings-title">
            <div class="settings-head">
                <span id="settings-title">Game Settings</span>
                <button type="button" class="settings-close" @click="closeSettingsPanel()" aria-label="Close">×</button>
            </div>

            <div class="settings-body">
                <!-- Pacing -->
                <fieldset class="settings-fieldset">
                    <legend>Pacing</legend>
                    
                    <label class="setting-row">
                        <span class="setting-label">Momentum Floor</span>
                        <input type="number" x-model.number="settings.momentum_floor" min="-10" max="10"/>
                    </label>

                    <label class="setting-row">
                        <span class="setting-label">Consecutive Pressure Threshold</span>
                        <input type="number" x-model.number="settings.consecutive_pressure_threshold" min="1" max="20"/>
                    </label>
                </fieldset>

                <!-- Thread Behavior -->
                <fieldset class="settings-fieldset">
                    <legend>Thread Behavior</legend>
                    
                    <div class="setting-row setting-toggle">
                        <span class="setting-label">De-escalate threads on success</span>
                        <button type="button" 
                                @click="settings.thread_deescalate_on_success = !settings.thread_deescalate_on_success"
                                :class="{ 'toggle-on': settings.thread_deescalate_on_success }"
                                class="setting-toggle-btn">
                            <div class="toggle-knob"></div>
                        </button>
                    </div>
                </fieldset>

                <!-- Game Options -->
                <fieldset class="settings-fieldset">
                    <legend>Game Options</legend>
                    
                    <div class="setting-row setting-toggle">
                        <span class="setting-label">Character Creation</span>
                        <button type="button" 
                                @click="settings.character_creation_enabled = !settings.character_creation_enabled"
                                :class="{ 'toggle-on': settings.character_creation_enabled }"
                                class="setting-toggle-btn">
                            <div class="toggle-knob"></div>
                        </button>
                    </div>

                    <label class="setting-row setting-warn">
                        <span class="setting-label">Warmup on Server Start</span>
                        <input type="checkbox" x-model="settings.warmup_on_start"/>
                        <span class="setting-hint">Requires server restart to take effect</span>
                    </label>

                    <div class="setting-row setting-toggle">
                        <span class="setting-label">Debug Mode</span>
                        <button type="button" 
                                @click="settings.debug_enabled = !settings.debug_enabled"
                                :class="{ 'toggle-on': settings.debug_enabled }"
                                class="setting-toggle-btn">
                            <div class="toggle-knob"></div>
                        </button>
                    </div>
                </fieldset>

                <!-- Status message -->
                <div x-show="settingsStatus.text" 
                     :class="'settings-status ' + settingsStatus.class"
                     x-text="settingsStatus.text">
                </div>
            </div>

            <div class="settings-foot">
                <button type="button" 
                        @click="saveSettings()"
                        :disabled="savingSettings"
                        class="settings-save-btn">
                    <span x-show="!savingSettings">Save</span>
                    <span x-show="savingSettings">Saving…</span>
                </button>
            </div>
        </aside>
    </div>
</template>
```

**Why:** Provides the full settings UI as a slide-out panel from the right side (consistent with existing sidebar patterns). Fields are grouped into fieldsets by category. Toggle switches for booleans, number inputs for integers. A warning hint on warmup_on_start clarifies it requires restart. Status messages show save feedback.

**Validation:** Panel slides in from right; ESC or backdrop click closes it; all fields render with correct types and current values; Save button triggers API call.

#### Step 3.2 — Add Alpine.js settings state and methods to game() function

**File:** `ccya/templates/index.html` (inside the `game()` return object)

**What:** Add reactive properties and methods:

```javascript
// Settings panel state
settingsPanelOpen: false,
savingSettings: false,
settingsStatus: { text: '', class: '' },
settings: {},

async loadSettings() {
    try {
        const resp = await fetch('/api/settings');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        this.settings = await resp.json();
    } catch (e) {
        console.error('Failed to load settings:', e);
    }
},

async saveSettings() {
    this.savingSettings = true;
    this.settingsStatus = { text: '', class: '' };
    
    try {
        const resp = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.settings),
        });
        
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        this.settings = await resp.json();
        
        this.settingsStatus = { text: 'Settings saved.', class: 'settings-status--success' };
    } catch (e) {
        console.error('Failed to save settings:', e);
        this.settingsStatus = { text: `Save failed: ${e.message}`, class: 'settings-status--error' };
    } finally {
        this.savingSettings = false;
    }
},

// Called when opening the panel
init() {
    // ... existing init code ...
    
    // Load settings on first open (lazy load)
    const origOpen = this.openSettingsPanel.bind(this);
    let loaded = false;
    this.openSettingsPanel = () => {
        if (!loaded) {
            this.loadSettings().then(() => { loaded = true; });
        }
        origOpen();
    };
},
```

**Why:** Provides reactive state for the settings form. Lazy-loads config from API on first panel open to avoid unnecessary server calls. Save method POSTs all fields and refreshes local state with server response (source of truth). Status messages give user feedback.

**Validation:** Opening Settings panel loads current values; editing fields updates reactive model; clicking Save sends POST, shows "Settings saved." briefly; errors show in red status text.

#### Step 3.3 — Add CSS for settings overlay and panel

**File:** `ccya/static/app.src.css` (append at end)

**What:** New CSS rules:

```css
/* =========================================================
   SETTINGS PANEL OVERLAY
   ========================================================= */

.settings-overlay {
    position: fixed;
    inset: 0;
    z-index: 200;
    display: flex;
}

.settings-backdrop {
    background: rgba(0, 0, 0, 0.5);
    width: 100%;
}

.settings-panel {
    position: relative;
    width: min(480px, 90vw);
    max-height: 100vh;
    background: var(--bg-surface);
    border-left: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

.settings-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-subtle);
    position: sticky;
    top: 0;
    background: var(--bg-surface);
    z-index: 1;
}

#settings-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
}

.settings-close {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: 24px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
}

.settings-close:hover {
    color: var(--text-primary);
}

.settings-body {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
}

.settings-fieldset {
    border: none;
    margin-bottom: 24px;
    padding: 0;
}

.settings-fieldset legend {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: 12px;
    padding-left: 0;
}

.setting-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 8px 0;
}

.setting-label {
    font-size: 14px;
    color: var(--text-primary);
    flex-shrink: 0;
}

.setting-row input[type="number"] {
    width: 72px;
    background: var(--bg-base);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    color: var(--text-primary);
    padding: 6px 8px;
    font-size: 14px;
    text-align: center;
}

.setting-row input[type="number"]:focus {
    outline: none;
    border-color: var(--accent);
}

.setting-toggle {
    gap: 20px;
}

.setting-toggle-btn {
    background: transparent;
    border: 1px solid var(--border-subtle);
    width: 44px;
    height: 24px;
    border-radius: 12px;
    cursor: pointer;
    position: relative;
    flex-shrink: 0;
    transition: background 150ms, border-color 150ms;
}

.setting-toggle-btn.toggle-on {
    background: var(--accent-soft);
    border-color: var(--accent);
}

.toggle-knob {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 18px;
    height: 18px;
    background: var(--text-secondary);
    border-radius: 50%;
    transition: transform 150ms, background 150ms;
}

.setting-toggle-btn.toggle-on .toggle-knob {
    transform: translateX(20px);
    background: var(--accent);
}

.setting-row.setting-warn input[type="checkbox"] {
    width: 44px;
    height: 24px;
    appearance: none;
    -webkit-appearance: none;
    background: var(--bg-base);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    position: relative;
    cursor: pointer;
    flex-shrink: 0;
}

.setting-row.setting-warn input[type="checkbox"]::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 18px;
    height: 18px;
    background: var(--text-secondary);
    border-radius: 50%;
    transition: transform 150ms;
}

.setting-row.setting-warn input[type="checkbox"]:checked {
    background: var(--accent-soft);
    border-color: var(--accent);
}

.setting-row.setting-warn input[type="checkbox"]:checked::after {
    transform: translateX(20px);
    background: var(--accent);
}

.setting-hint {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 4px;
    grid-column: 1 / -1;
}

.settings-status {
    padding: 8px 12px;
    border-radius: var(--radius-sm);
    font-size: 13px;
    margin-top: 16px;
}

.settings-status--success {
    background: var(--accent-success-soft);
    color: var(--accent-success);
}

.settings-status--error {
    background: var(--accent-error-soft);
    color: var(--accent-error);
}

.settings-foot {
    padding: 16px 20px;
    border-top: 1px solid var(--border-subtle);
    display: flex;
    justify-content: flex-end;
    position: sticky;
    bottom: 0;
    background: var(--bg-surface);
}

.settings-save-btn {
    background: var(--accent);
    color: #0f0f12;
    border: none;
    padding: 8px 24px;
    font-size: 14px;
    font-weight: 600;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background 150ms;
}

.settings-save-btn:hover:not(:disabled) {
    background: var(--accent-hover);
}

.settings-save-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
```

**Why:** Complete styling for the settings overlay matching existing design tokens (colors, spacing, border-radius). Panel slides from right with backdrop dimming. Toggle switches use CSS-only toggle pattern consistent with modern UI conventions. Sticky header and footer ensure controls are always visible during scroll.

**Validation:** All styles render correctly; panel is responsive on smaller screens (max 90vw); toggles animate smoothly; save button has hover/disabled states; ESC key closes the overlay.

---

## Tests to write or update

Temporarily skipped per AGENTS.md — tests are removed during refactor phase. Run `make check` as final validation step when all phases complete.
