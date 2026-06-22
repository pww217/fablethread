# Plan: Feed Resolved Pressures Into Narration Context (Finding #3)

## Status
completed

**Date:** 2026-05-17  
**Related Finding:** FINDINGS.md Section 3 — "De-escalate sections empty"

---

## Architecture Overview

### Current Flow (Broken)

```mermaid
flowchart LR
    subgraph Turn N
        A[Narration runs] --> B[Progress extraction]
        B --> C[Purge/expire pressures]
        C --> D[delta.scene_pressure_remove = [id1, id2]]
        D --> E[apply_delta — IDs removed from state]
    end

    subgraph Turn N+1
        F[Narration runs — NO resolved pressure data available]
        G[Breathe directive fires — 'A pressure has resolved']
        H[De-escalate section: (empty)]
    end

    A -. "sees pre-removal state" .-> B
    E -. "IDs lost, urgency/text gone" .-> F
```

**Problems:**
1. Narration runs BEFORE purge/expire — zero data about what will be removed
2. `delta.scene_pressure_remove` stores only string IDs (no text, no urgency)
3. After `apply_delta`, resolved pressure data is permanently lost from state
4. Breathe directive fires in narration with no context on WHAT to de-escalate
5. Progress extraction's "deescalation" section just says velocity = -0.60 — direction without causality

### Desired Flow (Fixed)

```mermaid
flowchart LR
    subgraph Turn N
        A[Narration runs] --> B[Progress extraction]
        B --> C[Purge/expire pressures]
        C --> D[Capture resolved = {id, text, urgency} objects]
        D --> E[state.meta.resolved_pressures_last_turn = resolved list]
        E --> F[apply_delta — IDs removed from state.scene_pressure]
    end

    subgraph Turn N+1 Narration Context
        G[Read meta.resolved_pressures_last_turn]
        H[Pass into narrate_user.j2 context]
        I["Resolved Pressures (from last turn) section"]
        J[Breathe directive — specific pressures named]
    end

    subgraph Turn N+1 Progress Context  
        K[Read meta.resolved_pressures_last_turn for extractor too]
        L["De-escalation: {id} resolved at {urgency} urgency"]
    end

    F -. persists in state.meta .-> G
```

**Key changes:**
- After purge/expire, capture full pressure objects (not just IDs) into `state.meta.resolved_pressures_last_turn`
- Read this field at start of next turn's narration and pass into both narrate and extract prompts
- Templates display resolved pressures with urgency tags so narrator knows what to de-escalate

---

## Implementation Details

### 1. Capture full pressure data in purge/expire (pressure.py)

**File:** `ccya/engine/pressure.py`  
**Change:** Modify `_purge_scene_pressures()` and `_expire_scene_pressures()` to also populate a new field on StateDelta that captures resolved pressures with their full data.

The cleanest approach: add a temporary list in turn.py that gets populated alongside `delta.scene_pressure_remove`. We already have the pressure objects available — we just need to record them before filtering.

**Option A (minimal):** In `turn.py` after purge/expire calls, diff old vs new scene_pressure lists and build resolved data. No changes to pressure.py or models.

```python
# After _purge_scene_pressures + _expire_scene_pressures:
pressures_before = {p.get("id"): p for p in (state.get("scene") or {}).get("scene_pressure") or []}
for rid in delta.scene_pressure_remove:
    if rid in pressures_before and not any(p.get("id") == rid for p in state.get("scene", {}).get("scene_pressure") or []):
        # This pressure was removed — capture its pre-removal data
        resolved.append({
            "id": pressures_before[rid]["id"],
            "urgency": pressures_before[rid].get("urgency", "background"),
            "text": pressures_before[rid].get("text", ""),
        })
```

This is the minimal approach — zero changes to pressure.py or models. Just a diff in turn.py.

**Decision:** Use Option A. No new StateDelta field needed, no model changes. The resolved data only needs to persist for one turn (in state.meta).

### 2. Store resolved pressures in state.meta (turn.py)

**File:** `ccya/engine/turn.py`  
**Location:** After purge/expire runs (~line 863), before momentum/floor relief checks.

```python
# Capture resolved pressure data for next turn's narration context
_resolved = []
pressures_before_purge = {p.get("id"): p for p in (state.get("scene") or {}).get("scene_pressure") or []}
for rid in delta.scene_pressure_remove:
    if rid not in pressures_before_purge:
        continue  # already removed by extractor's scene stream changes, skip
    pre_data = pressures_before_purge[rid]
    _resolved.append({
        "id": pre_data.get("id", ""),
        "urgency": pre_data.get("urgency", "background"),
        "text": pre_data.get("text", ""),
    })

if _resolved:
    state.setdefault("meta", {})["resolved_pressures_last_turn"] = _resolved
else:
    # Clear if nothing resolved — prevents stale data from old turns
    (state.get("meta") or {}).pop("resolved_pressures_last_turn", None)
```

**Why store in `state.meta` (not a new state field):** Mirrors the existing `pending_gm_beat` pattern. Runtime-only, not part of default state structure. Gets saved/loaded automatically with full state.

### 3. Read resolved pressures at start of narration (turn.py)

**File:** `ccya/engine/turn.py`  
**Location:** Around line 617-622 where `_pending_gm_beat` is read. Add similar read for resolved pressures.

```python
_resolved_pressures = (state.get("meta") or {}).get("resolved_pressures_last_turn")
```

Pass into `_narrate_messages()` call around line 705:

```python
narr_messages = _narrate_messages(
    ...
    resolved_pressures=_resolved_pressures,  # NEW
)
```

### 4. Pass resolved pressures into narrate context (narrate.py)

**File:** `ccya/engine/narrate.py`  
**Location:** In `_narrate_messages()`, add parameter and include in user_ctx dict.

Add to function signature (~line 13-50):
```python
resolved_pressures: list[dict[str, Any]] | None = None,
```

Include in `user_ctx` dict (around line 67-101):
```python
"resolved_pressures": resolved_pressures or [],
```

### 5. Render resolved pressures in narrate_user.j2 template

**File:** `ccya/prompts/narrate_user.j2`  
**Location:** Before the Breathe directive section (around line 90). Add a new section that shows what was resolved last turn.

```jinja2
{% if resolved_pressures %}
### Resolved Pressures (from last turn)
{% for p in resolved_pressures -%}
- [{{ p.urgency | upper }}] {{ p.text }} (`{{ p.id }}`)
{% endfor -%}
{% endif %}

{% if narrative_velocity < -0.3 %}

**Narration Directive:** Breathe
... (existing Breathe content stays as-is) ...
```

This gives the narrator concrete data: which specific pressures resolved, at what urgency level. The system prompt already says "A pressure has resolved. Pull back. Describe quiet or relief." — now it knows exactly WHICH pressure(s).

### 6. Render resolved pressures in extract_progress_user.j2 template (for progress extraction too)

**File:** `ccya/prompts/extract_progress_user.j2`  
**Location:** In the de-escalation section (around line 58), add resolved pressure data.

```jinja2
{% if narrative_velocity < -0.3 -%}
## deescalation
Narrative velocity indicates de-escalation ({{ "%.2f"|format(narrative_velocity) }}).
{% if resolved_pressures %}
The following pressures were resolved last turn:
{% for p in resolved_pressures -%}
- [{{ p.urgency | upper }}] {{ p.text }} (`{{ p.id }}`)
{% endfor -%}
Prefer `breathing_room` beat type or no beat. Do not add new immediate pressures.
Allow existing pressures to persist without escalation.
{% else %}
Strong deescalation. Prefer `breathing_room` beat type or no beat. Do not add new immediate pressures.
... (existing content) ...
```

This gives the progress extractor context about what wound down, so it can write appropriate beat instructions.

### 7. Pass resolved_pressures into extraction context (turn.py + extraction.py)

**File:** `ccya/engine/turn.py`  
**Location:** In `_extract_progress_messages()` call (~line 380 area). Add:

```python
"resolved_pressures": _resolved_pressures,  # same data used for narration
```

The progress extractor already receives `narrative_velocity` and `deescalate` — resolved pressures are additional context. No changes needed to extraction.py since the data flows through the template rendering.

---

## Files Changed (Summary)

| File | Changes | Lines affected (est.) |
|------|---------|----------------------|
| `ccya/engine/turn.py` | Capture resolved data after purge/expire; read at start of narration; pass to both narrate and extract calls | ~20 lines added |
| `ccya/engine/narrate.py` | Add `resolved_pressures` parameter to `_narrate_messages()`; include in user_ctx | ~3 lines changed |
| `ccya/prompts/narrate_user.j2` | Render resolved pressures section before Breathe directive | ~6 lines added |
| `ccya/prompts/extract_progress_user.j2` | Include resolved pressure data in de-escalation section | ~5 lines added |

**Zero changes to:** models.py, delta.py, pressure.py (Option A diff approach). No new StateDelta fields. No breaking changes.

---

## Edge Cases & Considerations

1. **Nothing resolved last turn:** `resolved_pressures` is empty list — templates skip the section. Breathe directive still fires if velocity < -0.3 (based on deescalate from dice results). Narrator just has less specific context.

2. **Multiple pressures resolved at once:** All are listed in the resolved section. Breathe directive applies to all of them. Narrator should describe what wound down.

3. **Stale data risk:** We clear `resolved_pressures_last_turn` when empty (line 860 area). This prevents old turn's resolved pressures from persisting if a turn had no removals.

4. **Events.jsonl logging:** The resolved pressure data is NOT stored in events — only IDs are logged via `applied.scene_pressure_remove`. If needed for future analysis, we could add it to the event record under a new key like `resolved_pressures` (list of {id, urgency, text}). Not part of this change.

5. **Token budget:** Adding resolved pressures section adds ~30-60 tokens per turn when something resolves. Negligible compared to 1280 token average narration output. The Breathe directive already exists in the template.

---

## Testing Strategy

**Unit tests (in `tests/test_*.py`):**
- Test that resolved pressures are captured after purge/expire with correct {id, urgency, text} data
- Test that resolved_pressures_last_turn is stored in state.meta and cleared when empty  
- Test that narrate_user.j2 renders the resolved section correctly
- Test Breathe directive still fires without resolved data (backward compat)

**Integration test:** Run a save through 3+ turns including at least one pressure resolution. Verify:
- Turn N where pressures resolve → `resolved_pressures_last_turn` populated in state after turn completes
- Turn N+1 narration includes resolved section with correct IDs and urgency levels  
- Turn N+1 de-escalate section is NOT empty (was always empty before this change)

**Manual verification:** Run FINDINGS.md save scenario. Verify T8's `tomas_death_imminent` removal appears in T9's narrate context under "Resolved Pressures" with `[IMMEDIATE] urgency`. Verify de-escalate section populates instead of being `(empty)`.

---

## Implementation Order (Sequential Dependencies)

1. **turn.py** — Capture resolved data after purge/expire, read at start of narration
2. **narrate.py** — Add parameter and context passing  
3. **narrate_user.j2** — Render resolved section in template
4. **extract_progress_user.j2** — Render resolved data in de-escalation section

Steps 1 must complete before 2-4 (data flow). Steps 2-4 are independent of each other. Can do 2+3+4 in parallel after step 1.
