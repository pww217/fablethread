# Plan 2: Inventory Hardening (Gate + UI)

## Status
`completed`

## Phases

2 phases: (1) enforce durability gate on inventory operations and pass inventory to ruling phase; (2) make all inventory delta changes display yellow in turn viewer.

## Issue

Two independent but related problems with inventory handling:

**Problem A — Narrator ignores inventory state:** The ruling LLM call (`ruling.py`) never receives inventory data, so it cannot validate whether actions like "reload pistol" are physically possible given current stock. If the player has 0 ammo and says "I reload," nothing stops the narrator from narrating a successful reload.

**Problem B — No durability gate on inventory operations:** `delta_builder.py` applies all three inventory ops (`inventory_add`, `inventory_remove`, `inventory_update`) identically with no concept of durable vs ephemeral changes. Any LLM can arbitrarily add new items every turn, remove them the next, and update names/notes without restriction. Only damage (amount reduction) and upgrades on existing items should persist; arbitrary additions are rejected unless they reference an item already in inventory or a loot gain from narration context.

**Problem C — UI inconsistency:** `inventory_update` displays yellow but `inventory_add` shows green and `inventory_remove` shows red, making it hard to distinguish "this is all inventory-related" at a glance.

## Solution

Phase 1: Pass inventory list to ruling phase via `_ruling_messages()` parameter; add durability gate in `delta_builder.py` that only allows `inventory_add` for items already present (amount increase) or explicitly referenced as loot gains from narration context. Phase 2: Update tv.py and CSS so all three inventory op types display yellow (`--accent`).

## Firm decisions

1. Durability gate on `inventory_add`: if the item ID does not exist in current inventory, reject the addition unless it matches a loot gain detected in recent_events or actions from this turn's narration. This prevents "LLM hallucinates new sword every turn" while still allowing legitimate loot gains tracked via narration context.
2. Inventory is passed to ruling as `inventory: list[dict]` with only `{id, name, amount}` per item — minimal context sufficient for validation without bloating the ruling prompt.
3. UI yellow uses existing CSS variable `--accent` (#f0a030 amber) already applied to `.tv-diff-op--update`.

## Non-goals

- Does not implement scene-boundary clearing of ephemeral items (separate feature).
- Does not add a "durable" flag or TTL field to InventoryItem model.
- Does not modify the narrate phase or extraction pipeline for inventory detection.
- Does not change loot gain mechanics — only gates how additions are applied post-extraction.

## Risks, Ambiguities, and Blockers

**Ambiguity:** How does Python detect "loot gains from narration context"? The simplest heuristic: if an `inventory_add` references a new item AND that same item name appears in the recent_events or actions list for this turn, allow it. Otherwise reject with warning log. This is imperfect but prevents arbitrary additions while allowing legitimate loot.

**Risk:** Existing saves may have items added via un-gated LLM calls. The gate only applies forward — no migration needed since rejected ops are silently dropped (same as current behavior for invalid removes).

**Blocker:** None. Both phases touch independent code paths: ruling.py + delta_builder.py for Phase 1, tv.py + CSS for Phase 2.

---

## Implementation — Phase 1: Inventory durability gate and ruling context

### Context files to load
- `ccya/engine/ruling.py` — add inventory parameter to `_ruling_messages()` call chain
- `ccya/prompts/ruling_user.j2` — include inventory section in rendered template
- `ccya/state/delta_builder.py` — add durability gate logic around `inventory_add` processing (lines 132-171)
- `ccya/engine/turn.py` — pass inventory to `_ruling_messages()` call site

### Detailed steps

#### Step 2.1.1 — Pass inventory list to ruling phase

**File:** `ccya/engine/ruling.py`

**What:** Add `inventory: list[dict[str, Any]] | None = None` parameter to `_ruling_messages()`. Render it into the user prompt template under key `"inventory"`. Update all callers in turn.py that invoke `_call_ruling()` / `_ruling_messages()` to pass `state.get("inventory") or []`.

**Why:** The ruling LLM needs visibility into current inventory to validate actions like "reload pistol" against actual stock levels. Without this, the narrator can narrate physically impossible outcomes.

**Validation:** Run `make check` — verify no missing import or type errors from adding parameter. All existing callers must be updated.

#### Step 2.1.2 — Include inventory in ruling_user.j2 template

**File:** `ccya/prompts/ruling_user.j2`

**What:** Add an `{% if inventory %}## Inventory{% for item in inventory %}- {{ item.name }} ({{ item.amount }}){% endfor %}{% endif %}` section to the user prompt, placed after the "scene" / present_npcs block and before the "Last Turn Outcome" block. Note: `recent_turns` is passed as a render context variable but not rendered in this template — place inventory between lines 14 (present_npcs end) and line 16 (last_outcome conditional). Only show `name`, `amount` per item — minimal context sufficient for validation.

**Why:** Provides ruling LLM with current inventory snapshot so it can validate player actions against actual stock levels. Minimal format keeps token budget tight.

**Validation:** Render the template manually or via test to confirm valid Jinja output. No structural changes to existing sections.

#### Step 2.1.3 — Add durability gate on inventory_add in delta_builder.py

**File:** `ccya/state/delta_builder.py`

**What:** In the `inventory_add` processing loop (lines 132-171), add a check before adding new items: if the item ID is not already present AND does not appear as a loot gain detected in recent_events or actions for this turn, log at WARNING level and skip the addition. The gate only blocks brand-new items; amount increases on existing items proceed normally (lines 138-148).

Specifically:
- After line 170 (`inv.append(d)`), move that append inside a conditional block
- Before appending, check if `target_id` already exists in `by_id`. If not, verify the item name appears in recent_events text or actions list for this turn. If neither matches, log warning and skip (do NOT append).
- Existing items found via canonical/fuzzy match still get amount increased — no gate applies to them.

**Why:** Prevents LLM from hallucinating new inventory items every turn while allowing legitimate loot gains detected in narration context. The heuristic is: if Python can't find evidence of this item being gained through the narrative flow, don't add it. This enforces "durable changes only" — damage and upgrades on existing items persist; arbitrary additions are rejected.

**Validation:** Run `make check`. Verify that inventory_add for existing items still works (amount increase path). New-item additions without narration context should be silently dropped with warning log.

#### Step 2.1.4 — Add inventory_add validation to `_validate()` in turn.py for rejection tracking

**File:** `ccya/engine/turn.py`

**What:** In the existing `_validate()` function (lines 1597-1644), add a check for `inventory_add` entries that mirrors the durability gate logic from Step 2.1.3. Currently `_validate()` only handles `inventory_remove` rejections; adding inventory_add validation ensures blocked additions appear in the event's `rejected` list and get the rejected badge in the turn viewer.

Specifically:
- After line 1603 (`inv_by_id = {...}`), add a loop over `delta.inventory_add`:
```python
for add_item in delta.inventory_add:
    canonical = resolve_inventory_canonical_id(inv_list, add_item.id)
    if canonical is not None:
        continue  # existing item — gate already enforced in apply_delta()
    # New item check: verify loot gain context via recent_events or actions
    has_loot_context = False
    for evt in (delta.recent_events_add or []):
        text = getattr(evt, 'text', str(evt)) if hasattr(evt, 'text') else str(evt)
        if add_item.id.lower() in text.lower() or add_item.name.lower() in text.lower():
            has_loot_context = True; break
    for action_text in (delta.actions or []):
        if add_item.id.lower() in action_text.lower() or add_item.name.lower() in action_text.lower():
            has_loot_context = True; break
    if not has_loot_context:
        rejections.append({
            "field": f"inventory_add:{add_item.id}",
            "kind": "durability_gate",
            "value": add_item.id,
            "reason": f"New item '{add_item.name}' — no loot gain context detected in recent_events or actions; rejected by durability gate",
        })
```

**Why:** `_validate()` runs BEFORE `apply_delta()` (turn.py:1243 vs 1257). The existing rejection tracking system populates the event's `rejected` list from `_validate()`, which feeds into tv.py's `rejected_set` and the turn viewer's rejected badge. Without adding inventory_add validation here, blocked additions would be silently dropped with only a WARNING log — users won't see in the UI that their item was rejected. This matches how existing `inventory_remove` rejections work (lines 1604-1644).

**Validation:** Run `make check`. Verify that durability-gate-blocked inventory_add entries appear in the event's `rejected` list and display with the "rejected" badge in the turn viewer.

### Tests to write or update

- **Test: inventory_add gate rejects new item not in recent_events/actions**
  - Setup: State with empty inventory, delta with `inventory_add` containing a brand-new item ID/name that does NOT appear in any recent_event text or actions list
  - Run `apply_delta()`
  - Assert: inventory remains empty; WARNING log emitted

- **Test: inventory_add gate allows new item referenced in recent_events**
  - Setup: State with empty inventory, delta with `inventory_add` for "rusty key", and a recent_event containing text mentioning "key" or the exact item name
  - Run `apply_delta()`
  - Assert: item added to inventory

- **Test: inventory_add on existing item still increases amount (gate bypass)**
  - Setup: State with one item in inventory, delta with matching `inventory_add` for same ID
  - Run `apply_delta()`
  - Assert: amount increased; no gate check triggered

### REPOMAP updates required

- `ccya/engine/ruling.py`: `_ruling_messages()` signature gains `inventory` parameter — update repomap entry at line 17 if present, or add note about new parameter.
- `ccya/state/delta_builder.py`: `apply_delta()` now enforces durability gate on inventory_add entries — no interface change but behavior documented in comment near function docstring.

---

## Implementation — Phase 2: Inventory UI delta yellow styling

### Context files to load
- `ccya/static/app.src.css` — CSS variable definitions for diff op colors
- `ccya/server/tv.py` — `_tv_state_diff()` or equivalent function that determines display class per field suffix

### Detailed steps

#### Step 2.2.1 — Make all inventory ops yellow in tv.py and template

**File:** `ccya/server/tv.py` + `ccya/templates/_turn_viewer.html`

**What:** Add an optional `op_css_class` field to each diff entry dict in `_tv_state_diff()`. For fields prefixed with `inventory_`, set `"op_css_class": "update"` which overrides the default CSS class derivation. The template already uses `ch.op` for both the CSS class and display symbol; add a conditional override so that when `op_css_class` is present, it's used instead of deriving from `ch.op`.

In tv.py `_tv_state_diff()`, inside the per-field rendering loop (after line 245 where `"rejected"` is set), add:
```python
if field_key.startswith("inventory_"):
    entry["op_css_class"] = "update"
```
where `entry` is the diff dict being built.

In `_turn_viewer.html` at line 277, update the class binding from:
```html
:class="'tv-diff-op--' + ch.op"
```
to:
```html
:class="ch.op_css_class ? 'tv-diff-op--' + ch.op_css_class : 'tv-diff-op--' + ch.op"
```

This makes all three inventory op types display yellow via `.tv-diff-op--update` while preserving their original `+`/`-`/~ symbols. The only template change is one conditional class binding at line 277; no other HTML changes needed.

**Why:** All inventory changes are semantically related — they represent the same game subsystem. Grouping them under one color helps players quickly identify what changed without parsing field names. Currently only `inventory_update` is yellow; additions and removals use green/red which implies "good/bad" rather than "same category." The `op_css_class` override approach preserves display symbols (`+`/`-`/~) while changing colors, avoiding confusion from all inventory ops showing as "~".

**Validation:** Run `make check`. Verify that in the turn viewer: `inventory_add` shows yellow "+" (was green), `inventory_remove` shows yellow "-" (was red), `inventory_update` still shows yellow "~" (unchanged).

#### Step 2.2.2 — Verify CSS already supports the styling

**File:** `ccya/static/app.src.css`

**What:** Confirm that `.tv-diff-op--update { color: var(--accent); }` exists and uses amber/yellow (`#f0a030`). No changes needed if present; otherwise add it.

**Why:** Phase 2 only needs the CSS class to exist — implementation already applies `inventory_update` → yellow via existing rule at line 2541. Verifying this prevents duplicate or conflicting rules.

**Validation:** Confirm one matching selector exists in app.src.css. No edits required if present.

### Tests to write or update

No automated tests needed for CSS-only changes. Manual visual verification sufficient per AGENTS.md (tests temporarily removed during refactor).

### REPOMAP updates required

None. This is a display-layer change only; no model, API, or pipeline contract modifications.
