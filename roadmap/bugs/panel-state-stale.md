---
title: "Left panel (scene/NPCs) not updating correctly after turn ends"
status: done
urgency: 2
size: medium
created: 2026-07-11
ticket_id: B-43
labels: [ui, state-sync, present-nearby]
design:
plan: plans/B-43-panel-state-stale.md
pr:
  url:
  branch:
validation: 2026-07-11
---

## Description

The left state panel (scene panel with NPCs — present vs. nearby, location, arcs) does not reflect the actual end-of-turn state. NPCs appear with stale presence values (e.g., "nearby" instead of "known" after decay), or lose updates made by the extraction pipeline.

## Validation

All three root causes **CONFIRMED** by hand-reading source files. No false positives. No additional issues found.

- Iss 1: `game.js:903` re-fetches only `/panels/state-right` — confirmed via grep on all HTMX panel calls
- Issue 2: `game.js:982` arc handler re-fetches `/panels/state-left` during extraction — confirmed that `state.yaml` on disk is pre-turn at that point (save at `turn.py:832` happens after `yield ("complete")`)
- Issue 3: `pipeline.py:116` panel_update fires at pre-apply state — confirmed decay logic is in `_apply_state_updates()` at `turn_state.py:661-676`, executed from `_apply_phase()` at `turn.py:219-224` after extraction completes

**Regression risk: NONE.** Purely UI-side fixes. Zero engine changes needed. The SSE pipeline, extraction, delta application, and persistence are all correct — only rendering/refresh sequencing is broken.

## Root Cause — Three Issues in Turn/End-of-Turn Flow

### Issue 1: `world_done` only re-fetches right panel (HIGH)

**File:** `ccya/static/game.js:903`

After the async window completes (sanitize + world step), the `world_done` handler only re-fetches `/panels/state-right`:

```js
htmx.ajax('GET', '/panels/state-right', { target: '#state-panel-right' });
```

The left scene panel is never updated. Any async mutations from `_run_world_step()` or `sanitize_threads()` leave the left panel stale indefinitely.

### Issue 2: Arc `panel_update` triggers premature HTMX re-fetch (MEDIUM-HIGH)

**File:** `ccya/static/game.js:982`

During extraction, the `arc` panel_update handler fires:

```js
htmx.ajax('GET', '/panels/state-left', { target: '#state-panel-left' });
```

At this point `state.yaml` has NOT been saved yet — `save_state()` doesn't happen until `_persist_and_async_cleanup()` (turn.py:832). The HTMX request reads **pre-turn** state from disk via `_load_current_state()` (routes.py:602), replacing the JS-rendered scene panel updates with stale data.

This causes a visible flash: scene briefly updates via JS `innerHTML` (panel_update), then gets overwritten by HTMX with pre-turn NPC presence.

### Issue 3: Scene `panel_update` misses post-delta NPC lifecycle decay (MEDIUM)

**File:** `ccya/engine/pipeline.py:116-119` vs `ccya/engine/turn_state.py:661-676`

The extraction pipeline sends `panel_update` events with pre-apply state (compendium from extraction, before delta application). NPC lifecycle decay (`nearby→known`, `departed→archived`) runs in `_apply_state_updates()` after extraction. So the scene panel shows NPCs that should have already decayed.

## Data Flow Diagram

```
Extraction (pipeline.py)
  ├─ panel_update:scene  → JS innerHTML (pre-delta state)  ← [issue 3]
  ├─ panel_update:state  → JS innerHTML
  └─ panel_update:arc    → HTMX re-fetch /panels/state-left → stale state.yaml [issue 2]

Apply Phase (turn_state.py)
  └─ _apply_state_updates() → NPC lifecycle decay

Persist (turn.py:832)
  └─ save_state() → state.yaml finally updated

Async Window
  └─ sanitize + world step (mutates state on disk)

world_done (game.js:903)
  └─ HTMX re-fetch /panels/state-right only  ← [issue 1]
  └─ left panel never re-fetched
```

## Components Involved

| Component | File:Line |
|-----------|-----------|
| SSE turn endpoint | `ccya/server/routes.py:251-341` |
| Turn pipeline (`run_turn`) | `ccya/engine/turn.py:62-291` |
| Extraction panel updates | `ccya/engine/pipeline.py:116-119` |
| NPC lifecycle decay | `ccya/engine/turn_state.py:661-676` |
| State save | `ccya/engine/turn.py:832` |
| Left panel template | `ccya/templates/_state_left.html:1-80` |
| Right panel template | `ccya/templates/_state_right.html:1-147` |
| Panel routes (HTMX) | `ccya/server/routes.py:557-612` |
| SSE panel_update JS handler | `ccya/static/game.js:924-983` |
| SSE world_done JS handler | `ccya/static/game.js:899-916` |
| SSE turn_complete JS handler | `ccya/static/game.js:986-1090` |

## Proposed Fix Direction

1. **Remove** the HTMX re-fetch in the arc `panel_update` handler (`game.js:982`). Let the HTMX re-render happen only from server-triggered events, not from JS during extraction.
2. **Add** a `/panels/state-left` re-fetch in the `world_done` handler (`game.js:903`) to ensure the left panel reflects post-async-window state.
3. Optionally: Re-count NPC presence in the scene panel after `turn_complete` using the `state_snapshot` from `result.state` (which already has the correct post-apply state) instead of relying on panel_update events.
