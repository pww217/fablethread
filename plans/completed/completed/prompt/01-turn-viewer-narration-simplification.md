# Turn Viewer — Narration Simplification Alignment

## Status
`completed`

## Phases

2 phases: Update turn viewer (tv.py + template) to reflect unified threads, PacingContext struct, and removed fields from narration simplification design. Also fix `_arc.j2` prompt template for unified threads display in Narrator inputs.

## Issue

The turn viewer still references old data models that have been replaced by the narration simplification: `stakes` on IntentEnvelope is gone but still displayed; `scene_pressure[]` + active/latent thread split are merged into unified `arc.threads[]`; PacingContext consolidates 6 independent pacing signals into one struct but isn't persisted as structured event data so it can only be seen indirectly through rendered prompts; _ExtractionContext (the post-delta view of state that Progress Extract used) is also not persisted, making eval pipeline debugging require replay logic. The compaction sanitization badge references removed `pressure_remove`. `_arc.j2` still uses the old `active_threads` split that no longer exists on this branch.

## Solution

1. Add PacingContext to events.jsonl event dict in turn.py so tv.py can display it as structured data (directive, gate, beat_hint, beat_locked) — primarily in the diff panel per user request for storytelling elements visibility and eval pipeline access.
2. Add _ExtractionContext to events.jsonl event dict — gives evals direct access to post-delta view of state that Progress Extract used (NPC roster, inventory snapshot, conditions) without reconstruction logic. Key `"extraction_context"` is distinct from existing keys so it won't interfere with inter-turn reads.
3. Update `_tv_state_diff()` with special handling for thread operations (`thread_advance`, `thread_resolve`) to show them more clearly than generic list-of-strings formatting.
4. Remove stale references: stakes template block from _turn_viewer.html, pressure_remove from compaction sanitization tracking in tv.py and template.
5. Fix `_arc.j2` prompt template to use unified `threads[]` with scope/active filtering instead of old `active_threads`.

## Firm decisions

1. PacingContext is added as a structured `"pacing_context"` key in the event dict written to events.jsonl (turn.py line ~1370). Displayed primarily in diff panel, secondarily visible via rendered prompts already contain directive/gate text.
2. Thread operations get enhanced display in diff panel — thread IDs shown with scope/urgency context from full thread objects when available (via inputs snapshot), otherwise just clean ID listing. Since `_tv_state_diff()` reads dynamically from parsed JSON blobs, new field names are picked up automatically; we add formatting polish only.
3. `pressure_remove` is dropped entirely from compaction sanitization tracking — unified threads don't have a direct "remove" operation (they get resolved and moved to completed_threads).
4. All stakes references removed without replacement — it had no meaningful substitute per user decision.
5. `_arc.j2` uses unified `threads[]` with scope/active filtering matching what narrate_user.j2 already does at lines 40-43 (filter by `t.scope == "scene"`).

## Non-goals

- Do not modify Step 2a (Scene Extract) or Step 2b (State Extract) — they are unchanged per design doc.
- Do not modify Jinja prompt templates beyond `_arc.j2` — the user said most everything is updated; remaining template changes belong to a separate plan.
- Do not add tests — AGENTS.md says tests are temporarily removed during refactor.

## Risks, Ambiguities, and Blockers

- **PacingContext serialization**: Adding `"pacing_context"` key to event dict requires serializing the PacingContext dataclass (directive, beat_hint, beat_locked, gate, summary). Need to ensure it's a plain dict compatible with JSON encoding. The `summary` field is human-readable log text that should NOT be sent to LLMs but IS safe for events.jsonl display.
- **_ExtractionContext serialization**: Adding `"extraction_context"` key serializes dicts/lists from `_build_extraction_context()` (NPC roster, location dict, inventory list, conditions list). These are already JSON-compatible since they come from state.yaml parsing — no special handling needed. The key is distinct from existing keys (`"rules"`, `"narrate"`, `"extract"`, `"extraction"`) so it won't interfere with inter-turn reads that look at those established paths.
- **Thread scope/urgency in diff panel**: `_tv_state_diff()` only has access to parsed ProgressExtractResult output (which contains thread IDs as strings, not full objects). To show scope/urgency we'd need threads from state — this is already available via inputs snapshot. The diff panel enhancement should be lightweight: just format list-of-strings cleanly without false claims about showing metadata that isn't in the extraction output.
- **Compaction sanitization**: If existing compactor code still emits `pressure_remove` keys, dropping them from tv.py display logic means they'll silently not show — which is correct since we're ripping out old references.

## Implementation — Phase 1: Engine + tv.py changes

### Context files to load
- `ccya/engine/turn.py` (lines ~555-620 for PacingContext, lines ~574-585 for _build_extraction_context call site, lines ~1345-1400 for event building)
- `ccya/server/tv.py` (full file — _tv_state_diff at line 133, compaction sanitization at line 309)
- `ccya/engine/extraction.py` (lines ~39-58 for _ExtractionContext dataclass definition and field names)

### Detailed steps

#### Step 1.1 — Add PacingContext to events.jsonl event dict

**File:** `ccya/engine/turn.py`, around line ~1370-1400 (event building section)

**What:** After the existing `"rules": rules_event,` entry in the event dict, add a new key that serializes PacingContext into a plain dict. The variable `_pc` is already computed at this point via `_compute_pacing_context()` and passed to both Narrator and Progress Extract. Add:

```python
"pacing_context": {
    "directive": _pc.directive if _pc else "",
    "beat_hint": _pc.beat_hint if _pc else None,
    "beat_locked": bool(_pc.beat_locked) if _pc else False,
    "gate": _pc.gate if _pc else "allow",
    "summary": _pc.summary if _pc else "",
},
```

**Why:** PacingContext is the primary in-turn-only data flow that replaces 6 independent pacing signals. Without it in events.jsonl, tv.py cannot display structured pacing decisions — users can only see directive/gate text indirectly through rendered prompt strings. Adding it as a top-level event key gives both tv.py clean access for diff panel display and eval pipelines direct access to Python's storytelling decisions without reconstruction logic.

**Validation:** `grep -n "pacing_context" ccya/engine/turn.py | grep '"pacing_context"'` should show the new dict entry in the event building section.

#### Step 1.2 — Add _ExtractionContext to events.jsonl event dict

**File:** `ccya/engine/turn.py`, around line ~1370-1400 (event building section), after PacingContext key added in Step 1.1

**What:** After the `"pacing_context": {...}` entry, add a new key that serializes `_ExtractionContext` into a plain dict. The variable `extraction_ctx` is already built at this point via `_build_extraction_context()` and passed to `_extract_progress_messages()`. Add:

```python
"extraction_context": {
    "present_npcs_this_turn": list(extraction_ctx.present_npcs_this_turn) if extraction_ctx else [],
    "location_this_turn": dict(extraction_ctx.location_this_turn) if extraction_ctx else {},
    "scene_tags_this_turn": list(extraction_ctx.scene_tags_this_turn) if extraction_ctx else [],
    "inventory_this_turn": list(extraction_ctx.inventory_this_turn) if extraction_ctx else [],
    "conditions_this_turn": list(extraction_ctx.conditions_this_turn) if extraction_ctx else [],
},
```

**Why:** _ExtractionContext is the post-delta view of state that Progress Extract used to make its thread/beat/event decisions. Without it in events.jsonl, debugging why Progress made specific choices requires replaying scene+state deltas against base state — error-prone and slow for eval pipelines. Having this structured data gives evals direct access to exactly what Progress saw (NPC roster, inventory snapshot, conditions) without reconstruction logic. The key `"extraction_context"` is distinct from existing keys (`"rules"`, `"narrate"`, `"extract"`, `"extraction"`) so it won't interfere with inter-turn reads that look at those established paths.

**Validation:** After edit, grep for `"extraction_context"` in turn.py should show the new dict entry alongside PacingContext and other event keys. Verify no existing code references `event["extraction_context"]` (it shouldn't — this is a new key).

#### Step 1.3 — Drop pressure_remove from compaction sanitization tracking

**File:** `ccya/server/tv.py`, line ~309-314

**What:** In `_turn_viewer_data()`, remove `"pressure_remove"` from the tuple of keys checked for `has_sanitization`. The current code checks:
```python
"npc_merge", "inventory_remove",
"pressure_remove", "condition_remove"
```
Remove `"pressure_remove"` so it becomes just:
```python
"npc_merge", "inventory_remove",
"condition_remove"
```

**Why:** `scene_pressure[]` is merged into unified `arc.threads[]`. The compactor no longer emits pressure-related sanitization actions — tracking a field that doesn't exist creates dead code and confusion. Per user decision #3, drop entirely without replacement.

**Validation:** After edit, grep for `"pressure_remove"` in tv.py should return zero matches.

#### Step 1.4 — Add special thread display handling to `_tv_state_diff()`

**File:** `ccya/server/tv.py`, function `_tv_state_diff()`, around line ~180-224

**What:** In the field processing loop (after parsing extraction output), add a check for unified thread operation fields before the generic suffix-based op detection. When encountering `thread_advance` or `thread_resolve`:
- For `thread_advance`: display as comma-separated IDs with a `[N threads]` prefix, dimmed if empty list
- For `thread_resolve`: display each resolution entry showing id + resolution_state inline (e.g., `"missing_ore: resolved"`)

The existing code at lines 190-223 handles `_add`, `_update`, `_remove` suffixes and generic lists. Thread operations use different naming (`thread_advance`, `thread_resolve`, `thread_add`) that won't match the suffix patterns — they'll fall through to the generic dict/list handling which is acceptable but not ideal for readability. Add a targeted check before the suffix detection:

```python
# Special display for unified thread operations (not covered by _add/_update/_remove suffixes)
if field_key == "thread_advance":
    value_str = ", ".join(str(x) for x in val[:6]) + ("\u2026" if len(val) > 6 else "")
elif field_key == "thread_resolve" and isinstance(val, list):
    parts = []
    for entry in (val or [])[:4]:
        if isinstance(entry, dict):
            rid = entry.get("id", "?")
            rstate = entry.get("resolution_state", "")
            parts.append(f"{rid}: {rstate}")
    value_str = "; ".join(parts) if parts else "\u2014"
elif field_key == "thread_add":
    # thread_add is a single ArcThread object or null — show summary
    if isinstance(val, dict):
        tid = val.get("id", "?")
        tsummary = val.get("summary", "")[:80]
        scope_tag = f"[{val.get('scope', '?')}]"
        value_str = f"{tid} {scope_tag}: {tsummary}"
    else:
        value_str = "null (gate blocked)"
```

**Why:** Thread operations are the primary storytelling signal from Progress Extract. The generic list-of-strings formatting doesn't convey that `thread_advance` is a list of IDs while `thread_resolve` carries resolution state metadata. Special handling makes these critical fields immediately readable in the diff panel without requiring users to expand prompt output tabs.

**Validation:** After edit, verify `_tv_state_diff()` still returns valid change dicts for all existing field types (npc_add/remove/update, inventory_add/remove, pc_condition_add/remove, recent_events_*). The new thread handling is additive — it checks specific field names before the generic suffix logic.

### Tests to write or update
None per AGENTS.md — tests temporarily removed during refactor.

### REPOMAP updates required
- `docs/repomap.md` — if there's a section documenting turn viewer data flow, note that PacingContext is now persisted as structured event data and thread operations have enhanced diff display. Otherwise no changes needed since the repomap documents engine modules not UI components.

## Implementation — Phase 2: Template updates

### Context files to load
- `ccya/templates/_turn_viewer.html` (full file)
- `ccya/prompts/sections/_arc.j2` (lines 13-20 — active_threads section)

### Detailed steps

#### Step 2.1 — Remove stakes template block from rules stage display

**File:** `ccya/templates/_turn_viewer.html`, lines ~175-185

**What:** Delete the entire `<template x-if="t.rules_intent.stakes">...</template>` block that renders a "stakes" definition list term inside the rules stage output. The full block is:
```html
<template x-if="t.rules_intent.stakes"><dt>stakes</dt><dd x-text="t.rules_intent.stakes"></dd></template>
```

**Why:** `IntentEnvelope.stakes` was removed from models.py per narration simplification design. Displaying a field that no longer exists is dead UI code that will never render anything meaningful on new events. Per user decision #4, rip out without replacement — stakes had no real substitute in the simplified model.

**Validation:** After edit, grep for `"stakes"` or `t.rules_intent.stakes` in _turn_viewer.html should return zero matches (other than any unrelated occurrences).

#### Step 2.2 — Remove pressure_remove from compaction sanitization display section

**File:** `ccya/templates/_turn_viewer.html`, lines ~75-76

**What:** Delete the entire `<template x-if="t.sanitization.pressure_remove && t.sanitization.pressure_remove.length">...</template>` block that displays "Pressures removed" count in the compaction card body. The full block is:
```html
<template x-if="t.sanitization.pressure_remove && t.sanitization.pressure_remove.length">
    <div class="tv-compaction-san-row">Pressures removed: <span x-text="t.sanitization.pressure_remove.length"></span></div>
</template>
```

**Why:** `scene_pressure[]` is merged into unified `arc.threads[]`. The compactor no longer emits pressure-related sanitization actions, and we already dropped the tracking from tv.py in Phase 1 Step 1.2. This template block is dead UI code that will never render on new events.

**Validation:** After edit, grep for `"pressure_remove"` or `t.sanitization.pressure` in _turn_viewer.html should return zero matches.

#### Step 2.3 — Display PacingContext structured data in diff panel

**File:** `ccya/templates/_turn_viewer.html`, inside the diff section (after failures template block, before state_diff template)

**What:** Add a new `<template x-if="t.pacing_context">...</template>` block that renders PacingContext fields as labeled rows in the diff panel. Place it between the failures section and the state_changes section:

```html
<template x-if="t.pacing_context && (t.pacing_context.directive || t.pacing_context.gate !== 'allow' || t.pacing_context.beat_hint)">
    <div class="tv-diff-section">
        <div class="tv-diff-section-label">Pacing Context</div>
        <template x-if="t.pacing_context.directive">
            <div class="tv-diff-row">
                <span class="tv-diff-field">directive</span>
                <span class="tv-diff-value" x-text="t.pacing_context.directive"></span>
            </div>
        </template>
        <template x-if="t.pacing_context.gate && t.pacing_context.gate !== 'allow'">
            <div class="tv-diff-row">
                <span class="tv-diff-field">gate</span>
                <span class="tv-diff-value" :class="'tv-sts-' + (t.pacing_context.gate === 'block_add' ? 'rejected' : 'retried')" x-text="t.pacing_context.gate"></span>
            </div>
        </template>
        <template x-if="t.pacing_context.beat_hint">
            <div class="tv-diff-row">
                <span class="tv-diff-field">beat_hint</span>
                <span class="tv-diff-value" x-text="t.pacing_context.beat_hint"></span>
            </div>
        </template>
        <template x-if="t.pacing_context.beat_locked">
            <div class="tv-diff-row">
                <span class="tv-diff-field">beat_locked</span>
                <span class="tv-diff-value" style="color: var(--status-error)">true — floor relief fired</span>
            </div>
        </template>
    </div>
</template>
```

**Why:** PacingContext is now persisted as structured event data (Phase 1 Step 1.1). Displaying it in the diff panel gives users immediate visibility into Python's pacing decisions without needing to expand prompt output tabs. The conditional display only shows non-default values: directive when non-empty, gate when not "allow", beat_hint when present, and beat_locked as a prominent error-colored indicator since floor relief is significant.

**Validation:** After edit, verify the Alpine.js template syntax is valid — all `x-if` conditions use proper JavaScript expression syntax compatible with x-show/x-for patterns already used in this file. The section label "Pacing Context" follows existing naming convention (same style as "Failures", "State changes").

#### Step 2.4 — Fix `_arc.j2` for unified threads display

**File:** `ccya/prompts/sections/_arc.j2`, lines ~13-20

**What:** Replace the old active_threads section with a unified threads filter that matches what narrate_user.j2 already does at lines 40-43. The current code:
```jinja2
{% if current_arc.active_threads -%}


**Active threads:**
{% for t in current_arc.active_threads -%}
- [{{ t.urgency | upper }}] {{ t.summary }}
{% endfor -%}
{% endif -%}
```

Should become:
```jinja2
{%- set scene_threads = (current_arc.threads | selectattr('scope', 'equalto', 'scene') | list) %}
{% if scene_threads -%}


**Active threads:**
{% for t in scene_threads -%}{% if t.active %}- [{{ t.urgency | upper }}] {{ t.summary }} (last seen T{{ t.last_seen_turn or '?' }}){% endif %}
{% endfor -%}
{% endif -%}
```

**Why:** `CampaignArc` on this branch uses unified `threads[]` with scope/active properties — there is no longer an `active_threads` attribute. The Narrator prompt template (narrate_user.j2 lines 40-43) already filters by `t.scope == 'scene'`. This change brings `_arc.j2` into alignment: iterate over unified threads, filter to scene-scope + active-only threads for display as "Active threads", and show last_seen_turn for context.

**Validation:** After edit, verify the Jinja template syntax is valid — particularly that `selectattr('scope', 'equalto', 'scene')` works correctly with the list of thread dicts from state.yaml. The `{% if t.active %}` filter inside the loop ensures only active threads display (Python sets this flag based on age rules).

### Tests to write or update
None per AGENTS.md — tests temporarily removed during refactor.

### REPOMAP updates required
- `docs/repomap.md` — no changes needed; repomap documents engine modules not UI components. The `_arc.j2` change is a prompt template fix that doesn't affect module boundaries.
