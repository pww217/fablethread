***

# Pack Deletion — Delete Custom/Generated Worlds from Pack Picker

## Status
`completed`

## Part of
standalone

## Objective
Players have no way to remove generated or custom worlds from the pack picker. This plan adds a delete button on each custom/generated pack card in the pack picker modal, with a confirmation dialog and server-side deletion.

## Non-goals
- No deletion of built-in (default) packs.
- No deletion of the currently active pack (blocked with error).
- No bulk delete or "delete all" functionality.
- No undo or trash/recycle bin.

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/server/routes.py` | modify | Add `DELETE /packs/{pack_id:path}` route, `_resolve_pack_dir()` helper |
| `ccya/templates/_pack_picker.html` | modify | Wrap custom pack cards in `.pack-card-wrapper`, add delete button |
| `ccya/templates/index.html` | modify | Add `handleDelete()` and `_wirePackCards()` helpers, wire delete handlers |
| `ccya/static/app.src.css` | modify | Add `.pack-card-wrapper`, `.pack-card-delete` styles |
| `docs/REPOMAP/server.md` | update | Add DELETE route to routes table |
| `docs/REPOMAP/frontend.md` | update | Update pack picker description |

## Implementation

### Step 1 — Server route

**File:** `ccya/server/routes.py`

Add `DELETE /packs/{pack_id:path}` route:
- Only allow deleting `custom/` or `generated/` packs (403 for built-in)
- Block deletion of currently active pack (409)
- Use `shutil.rmtree()` to remove the pack directory
- Return `{"ok": true}` on success, `{"error": "..."}` on failure

Add `_resolve_pack_dir()` helper (mirrors `pack._resolve_pack_dir` for server-side use).

### Step 2 — Template: delete button on pack cards

**File:** `ccya/templates/_pack_picker.html`

Wrap each custom pack card in a `.pack-card-wrapper` div. Add a delete button (`pack-card-delete`) with `data-delete-pack="{{ p.id }}"` inside the wrapper. The button shows a `×` character.

### Step 3 — CSS: delete button styling

**File:** `ccya/static/app.src.css`

Add:
- `.pack-card-wrapper` — relative positioning container
- `.pack-card-delete` — absolute positioned, hidden by default, revealed on wrapper hover, red accent on hover
- `z-index: 2` on delete button so it sits above the card button

### Step 4 — JS: delete handler + re-wiring

**File:** `ccya/templates/index.html`

In `openPackPicker()`:
- Add `handleDelete(deleteBtn, originalHtml)` — confirms, fetches DELETE, re-renders pack list
- Extract `_wirePackCards(originalHtml)` — attaches delete handlers to each button (capture phase, `stopImmediatePropagation`) and the body-level card click handler
- Call `_wirePackCards(html)` after initial pack list load
- Re-call `_wirePackCards(newHtml)` after successful deletion re-render

### Step 5 — Update docs

- `docs/REPOMAP/server.md` — add DELETE route to routes table
- `docs/REPOMAP/frontend.md` — update pack picker description

## Verification

1. Open pack picker modal
2. Hover over a custom/generated pack card — delete `×` appears in top-right
3. Click `×` — confirmation dialog appears
4. Confirm — pack is deleted, pack list re-renders without that pack
5. Built-in packs have no delete button
6. Currently active pack cannot be deleted (error shown)
