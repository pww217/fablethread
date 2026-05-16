# Fix: extract_progress_user.j2 Orphan Header and Missing Action Grounding

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Fix orphan gm_beat header and add fallback text for empty NPC/thread sections | Single-phase template edit |

## Objective
Two concrete issues exist in `extract_progress_user.j2`:

1. **Orphan `## gm_beat` header** (line ~52): The `## gm_beat` section header renders unconditionally even when `pending_beat` is falsy and `deescalate` is 0. This produces an empty `## gm_beat` section in every prompt where no beat is pending, wasting tokens and potentially confusing the model.

2. **No fallback for empty `present_npcs` and `active_threads`**: Both sections are guarded by `{% if %}` with no `{% else %}`. The `actions` schema in `extract_progress_system.j2` requires: one action involving a present NPC, one advancing an active thread. When both sections are missing from the rendered prompt (e.g., early turns before threads activate or before NPCs are tracked), the model cannot satisfy 3 of 4 structural requirements and consistently omits the `actions` field entirely. This is the likely root cause of the 13-turn `actions: []` failure observed in eval.

## Non-goals
- Do not change the schema instructions in `extract_progress_system.j2`.
- Do not change the Python code in `extraction.py` or `turn.py`.
- Do not alter any other section in `extract_progress_user.j2`.
- Do not add new context variables or change what Python passes to the template.

## Implementation — Phase 01: Fix orphan header and add fallback text

### Files to pull for context
- `ccya/prompts/extract_progress_user.j2` (already read — reproduced below for reference)
- `ccya/prompts/extract_progress_system.j2` (already read — actions rule is the constraint)

### Current template structure (relevant sections)

```jinja2
{% if present_npcs -%}
## present_npcs (in scene right now)
...
{% endif -%}

{% if active_threads -%}
## active_threads
...
{% endif -%}

...

## gm_beat                           ← ORPHAN: renders unconditionally
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
...
{% endif -%}
{% if deescalate > 0 -%}
## deescalate
...
{% endif -%}
```

### Detailed steps

#### Step 1.1 — Fix orphan `## gm_beat` header

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Remove the unconditional `## gm_beat` line. The subsections `pending_beat` and `deescalate` are already individually gated by `{% if %}`. They do not need a parent header at all — each subsection carries its own `##` heading.

Before:
```jinja2
## gm_beat
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires at turn: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif -%}
{% if deescalate > 0 -%}
## deescalate
...
{% endif -%}
```

After (remove the standalone `## gm_beat` line entirely):
```jinja2
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires at turn: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif -%}
{% if deescalate > 0 -%}
## deescalate
A pressure resolved this turn (magnitude: {{ "%.1f"|format(deescalate) }}).
{% if deescalate >= 0.8 -%}
Strong deescalation. Prefer `breathing_room` beat type or no beat. Do not add new immediate pressures.
{% else -%}
Partial deescalation. Prefer low-urgency beat or no beat.
{% endif -%}

{% endif -%}
```

**Why:** An empty section header with no content following it is pure token waste and a formatting signal that tells the model to expect content that never comes.

**Validation:** Render the template with `pending_beat=None` and `deescalate=0`. Confirm `## gm_beat` does not appear in output. Render with `pending_beat` populated. Confirm `## pending_beat` appears correctly.

#### Step 1.2 — Add fallback text for empty `present_npcs` section

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Add an `{% else %}` branch to the `present_npcs` block:

Before:
```jinja2
{% if present_npcs -%}
## present_npcs (in scene right now)
{% for n in present_npcs %}- `{{ n.id }}` | **{{ n.name or n.id }}**...
{% endfor %}
{% endif -%}
```

After:
```jinja2
{% if present_npcs -%}
## present_npcs (in scene right now)
{% for n in present_npcs %}- `{{ n.id }}` | **{{ n.name or n.id }}**{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor %}
{%- else %}
## present_npcs
None tracked. For the NPC-based action, use any character mentioned in the narration this turn.
{% endif -%}
```

**Why:** The `actions` schema requires one NPC-involving action. When `present_npcs` is empty and no `## present_npcs` section appears at all, models treat the constraint as unanswerable and omit `actions` entirely. A fallback instruction unlocks the NPC constraint without adding context weight.

**Validation:** Render the template with `present_npcs=[]`. Confirm the fallback line appears. Render with a populated list. Confirm normal NPC roster renders and fallback does NOT appear.

#### Step 1.3 — Add fallback text for empty `active_threads` section

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Add an `{% else %}` branch to the `active_threads` block:

Before:
```jinja2
{% if active_threads -%}
## active_threads
{% for t in active_threads %}- `{{ t.id }}` [{{ t.urgency | upper }}] {{ t.summary | truncate(120) }}...
{% endfor %}
{% endif -%}
```

After:
```jinja2
{% if active_threads -%}
## active_threads
{% for t in active_threads %}- `{{ t.id }}` [{{ t.urgency | upper }}] {{ t.summary | truncate(120) }}{% if t.tags %} tags: {{ t.tags | join(', ') }}{% endif %}
{% endfor %}
{%- else %}
## active_threads
None active yet. For the thread-advancing action, use any goal or objective the player has pursued in the narration.
{% endif -%}
```

**Why:** Same reasoning as Step 1.2. The model cannot satisfy the thread-advancing constraint when no threads exist. A fallback instruction redirects it to use narrative context instead of silently failing.

**Validation:** Render with `active_threads=[]`. Confirm fallback appears. Render with threads populated. Confirm normal list renders.

### Tests to write or update
- `tests/test_prompt_audit.py`:
  - `test_progress_user_no_orphan_gm_beat_header`: render `extract_progress_user.j2` with `pending_beat=None, deescalate=0`. Assert `"## gm_beat\n"` (the bare header with no content) is NOT in output.
  - `test_progress_user_present_npcs_fallback`: render with `present_npcs=[]`. Assert `"None tracked"` is in output.
  - `test_progress_user_active_threads_fallback`: render with `active_threads=[]`. Assert `"None active yet"` is in output.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: note that `extract_progress_user.j2` provides fallback text for empty `present_npcs` and `active_threads` to satisfy the `actions` schema constraint.

### Risks
1. The fallback text may cause the model to generate generic actions ("pursue your goal") rather than specific ones on turn 1 — acceptable; this is better than `actions: []`.
2. Removing `## gm_beat` header may cause the pending_beat and deescalate sections to feel disconnected in the rendered output — mitigation: each subsection has its own `##` header, so no loss of structure.

## Ambiguities requiring resolution before execution
1. Is the `## gm_beat` orphan header in `extract_progress_user.j2` at the exact position described above? Options: A) Yes — remove it as described. B) No — re-read the file and locate it before editing.
2. Does the current `present_npcs` block use the exact same Jinja syntax shown above? Options: A) Yes. B) No — re-read the file and adapt the after-block to match the exact current syntax without altering any rendered content for the non-empty case.
