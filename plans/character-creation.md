# Character Creation Screen — Technical Implementation Plan

## Overview

This plan covers the design and implementation of a character creation screen for ccya, as noted in `TODO.md` under **Characters & NPCs → Character creation**: "character creation screen on top of world/genre selection." The screen sits at New Game time, between pack selection and the first turn. It uses the existing `PlayerOverrides` model already built and wired in `pack.py`, the six-stat canonical system defined in `AGENTS.md`, and the existing Alpine.js + HTMX + Tailwind frontend stack.

---

## Scope

The character creation screen must:

1. Collect a **PC name** and **tagline** (role + defining trait, per existing `pc.tagline` field)
2. Allow **stat point allocation** — 12–18 points across 6 stats (1–4 per stat)
3. Accept optional **free-form hints** that populate `PlayerOverrides` (influences NPC generation, inventory, opening quest)
4. Feed output into the existing `generate_seed()` / `init_save_dir()` flow without changing engine internals

Everything that already works — pack selection, `generate_seed`, `apply_delta`, `init_save_dir` — is left untouched. Character creation is purely additive.

---

## Architecture

### Where It Fits in the Flow

```
/panels/pack-picker  (existing, HTMX fragment)
        ↓
[New Game modal: Pack selected]
        ↓
[Character creation step]  ← NEW
        ↓
POST /new-game  (existing endpoint, extended)
        ↓
generate_seed() or init_save_dir()  (existing, unchanged)
```

The New Game modal currently proceeds directly from pack selection to `POST /new-game`. The character creation step is inserted as a second panel within that same modal, navigated with an in-modal `Next` / `Back` flow — no new routes required at minimum viable scope.

### Data Path

1. User fills in the form → Alpine.js collects `{name, tagline, stats, pc_hints, free_form}` in-memory.
2. On confirm, the form submits `POST /new-game` with the new fields alongside `pack_id`.
3. `server.py` reads the new fields from `request.form()`, constructs a `PlayerOverrides` object, and passes it to `generate_seed()`.
4. For **static packs**, the PC name/tagline/stats directly overwrite the seed's `pc` fields before `init_save_dir()`.
5. For **dynamic packs**, `PlayerOverrides.pc_hints` is injected into the `generate_seed` prompt as soft guidance. The LLM still owns the final seed, but the player's inputs bias the result.

---

## Backend Changes

### `pack.py` — No changes needed

`PlayerOverrides` is already defined and documented:

```python
class PlayerOverrides(BaseModel):
    pc_hints: str = ""
    npc_hints: str = ""
    location_hints: str = ""
    quest_hints: str = ""
    free_form: str = ""
```

The `is_empty()` method and the full wiring stub exist. Nothing to add here.

### `engine.py` — Wire `PlayerOverrides` into `generate_seed`

`generate_seed()` currently has no `overrides` parameter. Add:

```python
async def generate_seed(
    pack: Pack,
    config: EngineConfig,
    template_dir: str,
    overrides: PlayerOverrides | None = None,
) -> SeedEnvelope:
    ...
```

Inside `generate_seed`, serialize `overrides` to a short YAML block and inject it into the `generate_seed_user.j2` template context under a `player_overrides` key. The template should render it only when non-empty:

```jinja
{% if player_overrides %}
## Player Preferences
{{ player_overrides }}
{% endif %}
```

This follows the existing conditional pattern used for `enable_thinking`.

### `server.py` — Read new form fields and apply overrides

In `POST /new-game`, after the pack-switching block, add:

```python
overrides = PlayerOverrides(
    pc_hints=str(form.get("pc_hints", "")).strip(),
    free_form=str(form.get("free_form", "")).strip(),
    npc_hints=str(form.get("npc_hints", "")).strip(),
    quest_hints=str(form.get("quest_hints", "")).strip(),
)

# Hard overrides for explicit name/tagline/stats (static packs only)
pc_name = str(form.get("pc_name", "")).strip()
pc_tagline = str(form.get("pc_tagline", "")).strip()
pc_stats_raw = str(form.get("pc_stats", "")).strip()  # JSON string from frontend
```

For **static packs**, after building the seed dict, patch the PC fields before `init_save_dir`:

```python
if _active_pack.manifest.mode == "static":
    seed = _active_pack.seed.model_dump()
    if pc_name:
        seed["pc"]["name"] = pc_name
    if pc_tagline:
        seed["pc"]["tagline"] = pc_tagline
    if pc_stats_raw:
        import json
        stats = json.loads(pc_stats_raw)
        if _validate_stats(stats):  # see below
            seed["pc"]["stats"] = stats
    seed.setdefault("meta", {})["model"] = config["llm"]["model"]
    init_save_dir(SAVE_DIR, seed)
```

For **dynamic packs**, pass `overrides` into `generate_seed()`. Build `pc_hints` from the hard inputs if provided:

```python
if pc_name or pc_tagline:
    hint_parts = []
    if pc_name:
        hint_parts.append(f"Name the PC '{pc_name}'.")
    if pc_tagline:
        hint_parts.append(f"Tagline: '{pc_tagline}'.")
    if pc_stats_raw:
        hint_parts.append(f"Use these exact stats: {pc_stats_raw}.")
    overrides = overrides.model_copy(update={"pc_hints": " ".join(hint_parts) + " " + overrides.pc_hints})
```

Add a `_validate_stats` helper in `server.py`:

```python
def _validate_stats(stats: dict) -> bool:
    SKILLS = {"strength", "dexterity", "wits", "lore", "charisma", "resolve"}
    if set(stats.keys()) != SKILLS:
        return False
    if not all(isinstance(v, int) and 1 <= v <= 4 for v in stats.values()):
        return False
    total = sum(stats.values())
    return 12 <= total <= 18
```

All validation is pure Python — no new dependencies.

### `config.yaml` — Optional flag

Add a feature flag under `game:` to allow disabling the screen for pack authors who ship static packs with fixed PCs:

```yaml
game:
  character_creation_enabled: true
```

Wire into `EngineConfig` per the AGENTS.md adding-a-config-flag checklist: `config.yaml` → `EngineConfig` → `server.py` wiring → conditional in template.

---

## Frontend Changes

### Template: `_char_creation.html` (new Jinja2 partial)

A new HTMX fragment rendered inside the New Game modal as a second step. Requires Alpine.js `x-data` for the stat allocator — no new libraries.

**Alpine.js component state:**

```javascript
{
  pc_name: '',
  pc_tagline: '',
  pc_hints: '',
  free_form: '',
  stats: {
    strength: 2, dexterity: 2, wits: 2,
    lore: 2, charisma: 2, resolve: 2
  },
  get total() { return Object.values(this.stats).reduce((a,b)=>a+b,0) },
  get isValid() {
    return this.pc_name.trim().length > 0
      && this.total >= 12 && this.total <= 18
      && Object.values(this.stats).every(v => v >= 1 && v <= 4)
  },
  increment(stat) {
    if (this.stats[stat] < 4 && this.total < 18) this.stats[stat]++
  },
  decrement(stat) {
    if (this.stats[stat] > 1) this.stats[stat]--
  },
  serializedStats() {
    return JSON.stringify(this.stats)
  }
}
```

**Stat display** uses the six-stat table from `AGENTS.md` for inline descriptions — shown as tooltips on hover using the existing `#tooltip-portal` pattern. Each stat row shows: stat name, +/− buttons, current value pip display (1–4 dots), and a brief descriptor.

**Points budget display:** A prominent counter showing `Total: X / 18 (min 12)` updates reactively. The Confirm button is disabled (`x-bind:disabled="!isValid"`) until the state is valid.

**Hidden fields** submitted with the form:

```html
<input type="hidden" name="pc_stats" x-bind:value="serializedStats()">
<input type="hidden" name="pack_id" x-bind:value="selectedPackId">
```

### Modal Navigation (`index.html`)

The New Game modal currently fires `POST /new-game` directly from the pack picker. Change the flow to:

1. Pack picker → user clicks **Select Pack** → Alpine.js advances `modalStep` from `'pack'` to `'character'`
2. Character creation step renders inline via `x-show`
3. **Confirm** submits the full form to `POST /new-game`
4. **Back** returns to `'pack'` step, preserving pack selection

Use `x-show` with Alpine.js step tracking rather than an HTMX navigation — keeps the modal self-contained with no extra round trips:

```html
<div x-data="newGameModal()">
  <!-- Step 1: Pack picker -->
  <div x-show="step === 'pack'">
    <!-- existing _pack_picker.html content -->
  </div>

  <!-- Step 2: Character creation -->
  <div x-show="step === 'character'">
    <!-- _char_creation.html content -->
  </div>
</div>
```

If `character_creation_enabled: false` in config, skip the character step and submit directly after pack selection — pass the flag from `server.py` into the template context.

---

## Stat Allocation UI — Detailed Spec

### Layout

Two-column grid at 768px+, single column below. Each row:

```
[Stat Name]  [Description]       [−] [●●○○] [+]  [value]
Strength     Force, melee, soak  [−] [●●○○] [+]    2
```

Dot pip display: filled dot per point (●), empty per remaining capacity (○), always 4 total. Tailwind implementation using `w-3 h-3 rounded-full` with conditional `bg-[var(--color-primary)]` / `bg-[var(--color-surface-offset)]`.

### Constraints Feedback

- `+` button: `x-bind:disabled="stats[s] >= 4 || total >= 18"` — grayed, cursor-not-allowed
- `−` button: `x-bind:disabled="stats[s] <= 1"` — grayed
- Point budget bar: `<progress>` element showing `total` of 18 max with `min` annotation at 12
- Label: "Points spent: X (12 min · 18 max)"

### Presets (Optional, Recommended)

Three quick-pick preset buttons populate the stat object. Purely cosmetic convenience — the player can modify after applying:

| Preset | STR | DEX | WIT | LOR | CHA | RES | Total |
|--------|-----|-----|-----|-----|-----|-----|-------|
| Brawler | 4 | 2 | 2 | 1 | 1 | 2 | 12 |
| Smooth Talker | 1 | 2 | 2 | 2 | 4 | 1 | 12 |
| Balanced | 2 | 2 | 2 | 2 | 2 | 2 | 12 |

Presets start at the minimum (12) so the player can spend the remaining 6 points freely.

---

## CSS Changes (`app.src.css`)

Never edit `app.css` directly — edit `app.src.css` then run `make css`. New classes needed:

```css
/* Stat pip dots */
.stat-pip        { @apply w-3 h-3 rounded-full transition-colors duration-150; }
.stat-pip-filled { @apply bg-[var(--color-primary)]; }
.stat-pip-empty  { @apply bg-[var(--color-surface-dynamic)]; }

/* Stat row */
.stat-row { @apply flex items-center gap-3 py-2 border-b border-[var(--color-divider)] last:border-0; }
.stat-btn { @apply w-7 h-7 rounded flex items-center justify-center text-sm font-mono
            bg-[var(--color-surface-offset)] hover:bg-[var(--color-surface-dynamic)]
            disabled:opacity-30 disabled:cursor-not-allowed transition-colors; }

/* Point budget bar */
.point-budget { @apply text-sm tabular-nums text-[var(--color-text-muted)]; }
```

---

## Testing

Add to `tests/test_char_creation.py`:

- **`test_validate_stats_valid`** — returns True for valid allocation (total 12–18, all values 1–4)
- **`test_validate_stats_invalid_total`** — returns False for total < 12 or > 18
- **`test_validate_stats_invalid_range`** — returns False when any stat is 0 or 5
- **`test_validate_stats_wrong_keys`** — returns False for unexpected stat keys
- **`test_new_game_static_pc_override`** — mock `init_save_dir`, POST `/new-game` with `pc_name`, `pc_tagline`, valid `pc_stats`; assert `init_save_dir` called with patched `seed["pc"]` values
- **`test_new_game_static_invalid_stats_ignored`** — POST with malformed `pc_stats` JSON; assert original stats preserved, no crash
- **`test_player_overrides_injected_into_generate_seed`** — mock `generate_seed`, POST `/new-game` with a dynamic pack and `pc_hints`; assert `overrides.pc_hints` was non-empty in the call

---

## Implementation Order

1. `_validate_stats` helper + `server.py` form field reading — pure Python, no UI, write tests first
2. `generate_seed()` signature extension in `engine.py` + template conditional in `generate_seed_user.j2`
3. `_char_creation.html` template — stat allocator Alpine.js component, tooltip integration
4. Modal step navigation in `index.html` — `x-show` step switching, Back/Next wiring
5. CSS additions in `app.src.css` + `make css`
6. `character_creation_enabled` config flag — add last once the feature is working

---

## Out of Scope

- **Character avatars** (`TODO.md`: "generate images/avatars for characters") — separate feature; depends on image generation tooling not yet in the codebase
- **Character traits** (`TODO.md`: "assign each character a set of traits") — separate feature; requires new state fields and extraction prompt changes
- **NPC context injection** (`TODO.md`: "NPC inventories, motivations, and inter-character relations") — separate feature in the Context & Performance section
