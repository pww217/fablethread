# Turn Viewer Seed Display at Game Start

## Status
`completed`

## Phases

2 phases: Load seed metadata, persist dynamic pack data, and render full initial game state in turn_viewer when no turns exist yet.

## Issue

Turn viewer shows "No turns recorded yet" at game start because events.jsonl is empty after `init_save_dir()`. Users cannot see what initial game state was set up or why it was generated that way — especially for dynamic packs where the LLM produced everything from scratch, including PC details, location, inventory, world state, and opening narrative.

## Solution

When turn_viewer detects zero turns/events, load `state.yaml` to display the full seed data as an initial game state card at the top of the timeline. For static packs this shows the hand-authored YAML content; for dynamic packs it additionally persists and displays the LLM-generated metadata (opening_narrative, actions) that currently lives only in memory. The existing turn cards remain unchanged below.

## Firm decisions

1. Seed data displayed via `state.yaml` — no separate file needed. Add two new fields to state meta: `_seed_type` ("static"|"dynamic") and `_pack_source` (path or pack name).
2. Opening_narrative and actions are persisted in a new top-level key `__seed_meta__` on the root of state.yaml, alongside existing keys like `meta`, `pc`, etc. This keeps them accessible without module-local variables.
3. Turn viewer loads seed data independently from event parsing — `_turn_viewer_data()` returns `(rows, no_events, seed_info)` tuple where `seed_info` is a dict ready for template rendering.
4. Seed display uses existing turn-viewer CSS classes and styling patterns (cards, collapsible sections) to maintain visual consistency.
5. Static packs: show full state.yaml content organized by section (PC, Location, Inventory, Scene, Arc, Compendium). Dynamic packs: additionally show opening_narrative and actions in a dedicated "Seed Generation" card.

## Non-goals

- Do NOT persist LLM prompts or raw responses used to generate seeds — only the final output metadata.
- Do NOT modify existing turn event rendering below the seed display area.
- Do NOT add SSE updates for seed data changes (seed is set once at game start, never changes).
- Do NOT show seed generation details for static packs (no LLM was involved).

## Risks, Ambiguities, and Blockers

1. **state.yaml schema compatibility**: Adding `__seed_meta__` to root of state.yaml — existing code that loads/saves state must not clobber this field on subsequent writes. Need to verify `_default_state()` doesn't overwrite it and `save_state()` preserves it.
2. **State size for display**: Full seed state can be large (compendium NPCs, inventory items). Should we show everything or summarize? Decision: show all sections but make them collapsible in the UI, matching existing turn viewer pattern of collapsible stage rows.
3. **Static pack source path tracking**: For static packs, `_pack_source` should record which pack directory was used (e.g., `packs/my-pack/seed_state.yaml`) so users know provenance. Need to pass this through from the new_game handler where `load_pack()` already knows the pack path.
4. **Existing module-level variables**: `_dynamic_opening` and `_dynamic_opening_actions` are currently used by panels.py for game display. After persisting, we should transition panels.py to read from state.yaml instead of memory — but that's out of scope for this plan (non-goals).

## Implementation — Phase 1: Persist seed metadata in state.yaml

### Context files to load
- `/Users/pwilson/repos/ccya/ccya/server/routes.py` — new_game handler, _apply_seed_to_save_dir()
- `/Users/pwilson/repos/ccya/ccya/state/io.py` — init_save_dir(), save_state(), _default_state()
- `/Users/pwilson/repos/ccya/ccya/models.py` — existing state shape definitions

### Detailed steps

#### Step 1.0 — Add __seed_meta__ to root of state.yaml and persist dynamic pack data

**File:** `ccya/server/routes.py`

**What:** Modify `_apply_seed_to_save_dir()` (line 49-64) signature to accept two new optional parameters: `pack_type: str | None = None` ("static" or "dynamic") and `pack_source: str | None = None`. Inside the function, after line 55 (`seed_dict.setdefault("meta", {})["model"] = ...`), add:

```python
if pack_type is not None:
    seed_dict.setdefault("meta", {})["_seed_type"] = pack_type
if pack_source is not None:
    seed_dict.setdefault("meta", {})["_pack_source"] = pack_source
if opening_narrative is not None and actions is not None:
    seed_dict["__seed_meta__"] = {
        "opening_narrative": opening_narrative,
        "actions": actions,
    }
```

Update the three call sites in routes.py to pass these new args:
- Line 272 (static pack): `_apply_seed_to_save_dir(seed, pack_type="static", pack_source=_app_mod._pack_id)` — no `opening_narrative`/`actions` since static packs don't have them.
- Line 283 (dynamic pack in new_game): `_apply_seed_to_save_dir(seed, envelope.opening_narrative, envelope.actions, pack_type="dynamic", pack_source=_app_mod._pack_id)`
- Line 307 (reroll): Same as line 283 — `_apply_seed_to_save_dir(seed, envelope.opening_narrative, envelope.actions, pack_type="dynamic", pack_source=_app_mod._pack_id)`

**Why:** Opening_narrative and actions currently exist only as module-level variables (`_dynamic_opening`, `_dynamic_opening_actions`) that are lost on server restart. Persisting them in state.yaml makes them available for turn_viewer display and survives restarts.

**Validation:** After `new_game` completes, verify `state.yaml` contains a top-level `__seed_meta__` key with `opening_narrative`, `actions`, `_pack_source`. For static packs this should be absent or empty.

#### Step 1.1 — Verify save_state preserves root-level keys through YAML round-trip

**File:** `ccya/state/io.py`, function `save_state()` at line 117-123, and `_default_state()` at line 45-96

**What:** No code changes needed to io.py. Confirm that:
- `save_state()` (line 117) calls `yaml.dump(state, f, ...)` which serializes ALL keys in the dict — any root-level key like `__seed_meta__` will be preserved through yaml round-trip since it just dumps whatever dict is passed to it.
- `_default_state()` does NOT include a `__seed_meta__` key in its return value (line 45-96) — this ensures only explicitly set seeds have this field, and fresh saves without seed metadata won't create an empty one.

**Why:** init_save_dir() always overwrites state.yaml completely via save_state(save_dir, seed) — there is no merging behavior to worry about. New seeds replace old ones entirely on rerolls, so __seed_meta__ will be overwritten with new values automatically. No preservation logic needed in io.py.

**Validation:** Run `reroll` flow and verify __seed_meta__ gets replaced with new opening_narrative/actions (not preserved from previous game).

### Tests to write or update
N/A (tests temporarily removed during refactor per AGENTS.md)

### REPOMAP updates required
- `/Users/pwilson/Repos/ccya/docs/repomap.md` — Update "State I/O" section to note __seed_meta__ root-level key in state.yaml. Note that save_state preserves all root-level keys through yaml.dump round-trip. Update "Seed metadata persistence" entry.

## Implementation — Phase 2: Render seed data in turn_viewer when no turns exist

### Context files to load
- `/Users/pwilson/repos/ccya/ccya/server/tv.py` — _turn_viewer_data() function, return value structure
- `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html` — Alpine.js template, existing rendering logic
- `/Users/pwilson/repos/ccya/ccya/static/app.src.css` — Existing turn-viewer CSS classes for styling reference

### Detailed steps

#### Step 2.0 — Modify _turn_viewer_data to return seed_info alongside rows and no_events

**File:** `ccya/server/tv.py`, function `_turn_viewer_data(save_dir: Path)` at line 337-570, imports section (line 1-10)

**What:** Add import at top of tv.py after existing imports:
```python
from ..state.io import load_state
```

Change the return type from `tuple[list[dict[str, Any]], bool]` to `tuple[list[dict[str, Any]], bool, dict | None]`. Restructure the function to compute `seed_info` once at the end before a single return point. Move the three existing returns (lines 360, 568, 570) into an intermediate variable pattern:

- Initialize `rows` at the top and only early-return when `path` doesn't exist (line 340).
- At line 359-360, instead of `return server_rows or [], bool(server_rows)`, assign to `rows` and fall through to function end.
- At line 565-568, instead of `return all_rows, False`, compute `rows = all_rows` and fall through.
- At line 570, fall through instead of returning.

At the bottom of the function, after all row-building logic, add seed_info computation then a single return:

```python
seed_info = None
if len(rows) == 0 and not no_events:
    # Zero turns AND events.jsonl exists — fresh game with valid state.yaml
    try:
        st = load_state(save_dir)
        meta = st.get("meta", {}) or {}
        seed_type = meta.get("_seed_type")
        if seed_type in ("static", "dynamic"):
            seed_info = {
                "pack_type": seed_type,
                "pack_source": meta.get("_pack_source", ""),
                "pc_name": st.get("pc", {}).get("name", ""),
                "pc_tagline": st.get("pc", {}).get("tagline", ""),
                "pc_stats": st.get("pc", {}).get("stats", {}),
                "pc_conditions": list(st.get("pc", {}).get("conditions") or []),
                "pc_momentum": st.get("pc", {}).get("momentum", 0),
                "location_name": st.get("location", {}).get("name", ""),
                "inventory_count": len(st.get("inventory", []) or []),
                "world_state_lines": list(st.get("scene", {}).get("world_state") or []),
                "recent_events_lines": [e if isinstance(e, str) else e.get("text", "") for e in st.get("scene", {}).get("recent_events") or []],
                "npcs_in_compendium": {k: {"name": v.get("name"), "title": v.get("title")} for k, v in (st.get("compendium", {}).get("npcs") or {}).items()},
                "arc_info": st.get("arc") if st.get("arc") else None,
            }
            __seed_meta = st.get("__seed_meta__") or {}
            if seed_type == "dynamic" and __seed_meta:
                seed_info["opening_narrative"] = __seed_meta.get("opening_narrative")
                seed_info["actions"] = __seed_meta.get("actions")
    except Exception as exc:
        _log.warning("Failed to load state for turn_viewer seed display", extra={"error": str(exc)})

return rows, no_events, seed_info  # replace existing return statements with this pattern
```

The conditional `if len(rows) == 0 and not no_events` ensures we only show seed_info when: (a) there are zero turns/events in events.jsonl, AND (b) events.jsonl exists (`no_events=False`). This excludes the case where no_events=True (events.jsonl doesn't exist at all — fresh server without any game started).

**Why:** This separates seed display data preparation from event parsing. The template receives a clean dict ready for rendering without needing to parse raw state.yaml structures. Seed loading is wrapped in try/except so failures don't break turn viewer if state.yaml becomes corrupted or unreadable.

**Validation:** Run server and open turn_viewer on empty save dir — verify `no_events` is False, `seed_info` dict is populated with all fields (pc_name, location_name, etc.), and the SSR template renders the seed card with correct data.

#### Step 2.1 — Update API endpoints to pass seed_info to template

**File:** `ccya/server/routes.py`, lines ~458-507 (turn_viewer and turn_viewer_data handlers)

**What:** Unpack the third return value from `_turn_viewer_data()` at both call sites:
- Line 462 (`/turn_viewer` SSR endpoint): Change `turns, no_events = _turn_viewer_data(_app_mod.SAVE_DIR)` to `turns, no_events, seed_info = _turn_viewer_data(_app_mod.SAVE_DIR)`. Add `"seed_info": seed_info` to the context dict passed to `_render()` (line 465-470).
- Line 476 (`/turn_viewer/data` JSON endpoint): Same unpacking change. Add `"seed_info": seed_info` to the `JSONResponse({ ... })` dict returned at line 478-485.

**Why:** Both endpoints need access to seed data for template rendering and API consumers. The SSE stream (`/turn_viewer/stream`) doesn't need updates since seed info never changes after game start — it only emits "updated" events on events.jsonl mtime changes, not state.yaml changes.

**Validation:** Check that `/turn_viewer/data` returns `seed_info` field when turn_count is 0, and null otherwise. Verify SSR template receives it correctly via Jinja serialization.

#### Step 2.2 — Render initial game state card in turn viewer template

**File:** `ccya/templates/_turn_viewer.html`, lines ~309-314 (the `{% else %}` branch at line 297, which renders when turns is empty)

**What:** The template has two branches controlled by the Jinja condition on line 15 (`{% if turns and turns | length > 0 %}`). Seed display goes in the **else branch** starting at line 297 — this is where "No events found" (line 309) or "No turns recorded yet" (line 311) currently render. Replace lines 308-312 with conditional seed rendering:

```html
        {% if seed_info %}
        <div class="tv-seed-card">
            <div class="tv-seed-header">
                <span class="tv-seed-badge" x-text="seed_info.pack_type | capitalize"></span>
                <span class="tv-seed-pack-source">{{ seed_info.pack_source }}</span>
                <span class="tv-seed-turn-count">0 turns</span>
            </div>

            {% if seed_info.pack_type == "dynamic" and seed_info.opening_narrative %}
            <details open>
                <summary class="tv-seed-section-header">Seed Generation</summary>
                <div class="tv-seed-narrative">{{ seed_info.opening_narrative }}</div>
                {% if seed_info.actions %}
                <ol class="tv-seed-actions">{% for a in seed_info.actions %}<li>{{ a }}</li>{% endfor %}</ol>
                {% endif %}
            </details>
            {% endif %}

            <details open>
                <summary class="tv-seed-section-header">Player Character</summary>
                <div><strong>{{ seed_info.pc_name }}</strong> — {{ seed_info.pc_tagline }}</div>
                <div class="tv-seed-stats">{% for s, v in seed_info.pc_stats.items() %}<span class="tv-seed-stat">{{ s }}: {{ v }}</span>{% endfor %}</div>
                <div class="tv-seed-momentum">Momentum: {{ seed_info.pc_momentum }}</div>
                {% if seed_info.pc_conditions %}<div class="tv-seed-conditions">Conditions: {{ seed_info.pc_conditions | join(", ") }}</div>{% endif %}
            </details>

            <details open>
                <summary class="tv-seed-section-header">Location</summary>
                <div>{{ seed_info.location_name }}</div>
            </details>

            {% if seed_info.inventory_count %}
            <details open>
                <summary class="tv-seed-section-header">Inventory ({{ seed_info.inventory_count }})</summary>
                <!-- Render inventory items from state.yaml — full detail in template -->
            </details>
            {% endif %}

            {% if seed_info.world_state_lines or seed_info.recent_events_lines %}
            <details open>
                <summary class="tv-seed-section-header">Scene</summary>
                <!-- Render world_state and recent_event lines -->
            </details>
            {% endif %}

            {% if seed_info.arc_info %}
            <details open>
                <summary class="tv-seed-section-header">Arc</summary>
                <!-- Render arc.visible_goal, thematic_question, threads -->
            </details>
            {% endif %}

            {% if seed_info.npcs_in_compendium %}
            <details open>
                <summary class="tv-seed-section-header">Compendium NPCs ({{ seed_info.npcs_in_compendium | length }})</summary>
                <!-- Render NPC names and titles -->
            </details>
            {% endif %}
        </div>
        {% elif no_events %}
        <div class="turn-viewer-no-events">No events found. Start a game to generate turn data.</div>
        {% else %}
        <div class="turn-viewer-empty">No turns recorded yet.</div>
        {% endif %}
```

Use existing CSS classes where possible (`.tv-turn-card`, `.tv-pipeline-stage` for collapsible sections, matching the existing compaction card styling at line 2320+ in app.src.css). Add new minimal CSS only for seed-specific elements:
- `.tv-seed-badge` — small badge showing "static" or "dynamic" pack type (similar to existing status badges)
- `.tv-seed-header` — header row matching turn card headers styling
- `.tv-seed-section-header` — collapsible section summary matching stage row headers
- `.tv-seed-narrative` — prose text container for opening_narrative

**Why:** This gives users immediate visibility into what initial state was set up and why, directly in the turn viewer they're already using to debug turns. The collapsible pattern matches existing UI conventions so it feels native. Placing this in the `{% else %}` branch (line 297) ensures it only renders when there are zero turns — existing turn card rendering below is unaffected since that lives in the `{% if turns and turns | length > 0 %}` branch starting at line 15.

**Validation:** Open turn_viewer on a fresh game (both static and dynamic packs). Verify:
- Seed card renders at top of timeline with correct data from state.yaml
- All sections are collapsible via native `<details>` elements and expand/collapse correctly
- Opening narrative and actions appear only for dynamic packs
- Existing turn cards below render unchanged when turns exist
- No visual regressions in existing turn viewer styling

### Tests to write or update
N/A (tests temporarily removed during refactor per AGENTS.md)

### REPOMAP updates required
- `/Users/pwilson/Repos/ccya/docs/repomap.md` — Update "Turn Viewer" section to note seed_info return value from `_turn_viewer_data()`. Note new `__seed_meta__` root-level key in state.yaml. Add entry for initial game state card rendering in turn viewer template.
