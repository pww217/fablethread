---
title: "Manual party management and inventory drop — plan"
ticket_id: F-29
---

## Design Reference

- Feature ticket: `roadmap/features/F-29-manual-party-and-inventory-drop.md`

## Phase summary

3 phases. Phase 1 removes unreliable LLM party prompting. Phase 2 adds two API endpoints (`POST /api/npc/{id}/toggle-party` and `POST /api/inventory/drop`). Phase 3 adds the party toggle icon and inventory drop buttons to the UI. Phases are ordered by dependency: engine changes first, then API, then UI.

---

## Phase 01: Remove LLM party prompting

**File:** `ccya/prompts/extract_scene_system.j2`
**What:** Remove the "Party assignment" section (lines 60-65). Remove `"party": true` from the JSON schema example (line 21). Remove the `party` field rule from the field rules list (line 40).
**Why:** Player-managed party replaces LLM-managed party.
**Validation:** Grep confirms no remaining references to `party` in the prompt file.

**File:** `ccya/models/extraction.py`
**What:** Remove `party: bool | None = None` from `CompendiumNpcUpdate` (line 32).
**Why:** No longer emitted by the scene extractor.
**Validation:** File compiles; no remaining `party` references in extraction models.

---

## Phase 02: Add API endpoints

**File:** `ccya/server/routes.py`
**What:** Add two route handlers:

1. `POST /api/npc/{npc_id}/toggle-party` — loads current state, toggles `party` on the named NPC in the compendium, saves state, returns updated NPC entry.
2. `POST /api/inventory/drop` — loads current state, removes item(s) from inventory, saves state, returns updated inventory list.

**Contract for toggle-party:**
```python
def toggle_npc_party(request: Request, npc_id: str):
    # 1. _require_save() check
    # 2. state = _load_current_state()
    # 3. if npc_id not in state.compendium.npcs → 404
    # 4. new_state = state.update_npc(npc_id, party=not state.compendium.npcs[npc_id].party)
    # 5. save_state(SAVE_DIR, new_state)
    # 6. return JSONResponse({"npc_id": npc_id, "party": new_state.compendium.npcs[npc_id].party})
```

**Contract for inventory drop:**
```python
def drop_inventory_item(request: Request):
    # 1. body = await request.json() → {item_id, amount?}
    # 2. _require_save() check
    # 3. state = _load_current_state()
    # 4. item_id = body["item_id"]; amount = body.get("amount")
    # 5. Find item in state.inventory by id
    # 6. If amount is None → remove entire item; else → reduce amount by amount (min 1)
    # 7. If amount > 0 after reduction → update amount; if amount == 0 → remove item
    # 8. save_state(SAVE_DIR, new_state)
    # 9. return JSONResponse({"inventory": [...]})
```

**Why:** Server-side state mutation is required — frontend state alone doesn't persist.
**Validation:** `curl` against `localhost:8765` confirms both endpoints return correct status codes and updated state.

---

## Phase 03: Add party toggle icon and inventory drop UI

**File:** `ccya/templates/_state_left.html`
**What:** Add a party toggle icon (right-aligned on each NPC card) for `present` and `nearby` NPCs. The icon is a small person silhouette SVG — hollow/grey when `party: false`, blue (`--accent-blue: #60a5fa`) when `party: true`. Uses `data-npc-id` attribute.
**Why:** Player needs to toggle party membership.

**File:** `ccya/static/game-utils.js`
**What:** 
1. Add `toggleNpcParty(npcId)` function — fire-and-forget `fetch('/api/npc/' + npcId + '/toggle-party', {method: 'POST'})` → on success, update the DOM icon color without page reload.
2. Add inventory drop UI — on inventory panel hover, show a right-aligned drop button (red X icon) next to each item. For single-quantity items, show a confirmation dialog. For multi-quantity items, show a popup with a number input. Call `fetch('/api/inventory/drop', {method: 'POST', body: JSON.stringify({item_id, amount})})`.
**Why:** Implements the interactive UI for both features.

**File:** `ccya/templates/_state_right.html`
**What:** Wrap inventory items in a hover-reveal container so drop buttons appear only when hovering the panel.
**Why:** Per the ticket spec, drop buttons are hover-only.

**File:** `ccya/static/app.src.css`
**What:** Add CSS for:
- Party toggle icon (`.npc-party-toggle`) — cursor pointer, right-aligned, grey→blue on active
- Inventory drop button (`.inv-drop-btn`) — right-aligned, appears on hover, red color
- Hover container for inventory panel (`.inventory-hover-container`) — reveals buttons on `:hover`
**Why:** Styling for new interactive elements.

**Validation:** UI renders correctly. Party toggle icon shows correct color. Inventory drop buttons appear on hover. Clicking both fires API calls and updates state.

---

## Documentation updates

**File:** `docs/architecture/step2a-scene.md`
**What:** Update section 3 (Party assignment) to note that party is now player-managed only. Remove references to LLM-assigned party.
**Why:** Pipeline docs must reflect current behavior.

**File:** `docs/repomap.md`
**What:** Update module boundaries for `CompendiumNpcUpdate` (remove party field) and add new API endpoints to the index.
**Why:** Module boundaries are stale without updates.

---

## Done when

- Phase 1: No `party` references in prompt or extraction models.
- Phase 2: Both API endpoints return correct responses and persist to state.
- Phase 3: UI renders correctly, interactions work, CSS matches spec.
- Docs updated to reflect removal of LLM party management and addition of API endpoints.
