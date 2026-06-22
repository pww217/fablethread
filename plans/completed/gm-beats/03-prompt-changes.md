# Pacing/Beat System — Plan 3/3: Prompt Changes (GM Beat Section + Beat History + Scene Imperative)

## Purpose

Restore the missing `## GM Beat` section in the storytell user prompt, add beat history rendering to the storytell system prompt, and add Scene Imperative behavioral guidance — the frontend half of the pacing overhaul.

## Problem Statement

The storyteller prompt has two gaps: (1) the `## GM Beat` section with pending_beat data is entirely absent from the user prompt (Finding 1.8), meaning the storyteller generates beats blind to what was in effect; (2) the ~50 lines of beat diversity guidance in the system prompt are structurally untestable because no beat history is passed to the LLM. Separately, Scene Imperative fires correctly when scenes stall but carries no behavioral weight in the storytell prompt.

## Constraints

- Pipeline order unchanged. The narrator consumes beat data from state; the storyteller receives beat data via prompt context. The 1-turn lag persists.
- The system prompt's `## GM Beat guidance` section (lines 135-187) is unchanged — only new sections are prepended before it.
- No backwards compatibility. Prompts are rendered fresh each turn; pre-feature saves simply lack `recent_beats` in meta.

## Non-goals

- No changes to narrate prompts (narrate_user.j2 already renders `**Beat:**` at lines 95-98; narrate_system.j2 is not touched).
- No changes to beat type vocabulary.
- No changes to the existing GM Beat guidance content.
- No turn.py changes (all backend state mutations are in Plan 2). The one-line extraction.py wiring in Step 1 is an exception — it's tightly coupled to the prompt changes (must pass `pending_beat` to the template).

## Solution

Three prompt modifications plus one extraction.py wiring change: (1) pass `pending_beat` from state to `storytell_user.j2` and render it as a `## GM Beat` section; (2) prepend beat history rendering in `storytell_system.j2` before the existing GM Beat guidance; (3) add Scene Imperative guidance to the existing PacingContext guidance section in `storytell_system.j2`.

## Firm decisions

1. The `## GM Beat` section in storytell_user.j2 shows the currently pending beat (type, surface_as, expiry) — the same data the narrator receives. This gives the storyteller awareness of what beat context is active.
2. Beat history rendering in storytell_system.j2 is a Jinja `{% if recent_beats %}` block before the `## GM Beat guidance` section header. Format: 3-5 most recent beats listed oldest-first.
3. Scene Imperative guidance is appended to the existing PacingContext guidance bullet list in storytell_system.j2 (lines 126-133).
4. The beat history is read from `meta.recent_beats` (populated by Plan 2 Step 4) and passed to the storytell system prompt via the `_storytell_messages` context.

## Risks, Ambiguities, and Blockers

- The beat history data (`recent_beats`) is populated by Plan 2, which also adds `pending_gm_beat` null-clear and floor relief overrides. Plan 3 must be executed after Plan 2's state mutations are in place.
- Pre-feature saves without `recent_beats` in meta: the Jinja `{% if recent_beats %}` guard handles this gracefully — empty list or missing key → no rendering.

## Status

`open`

---

## Phases

1 phase: all prompt changes in dependency order (wiring → section restoration → beat history → SI guidance).

---

## Implementation

### Context files to load

- `ccya/prompts/storytell_user.j2` (entire file — 47 lines)
- `ccya/prompts/storytell_system.j2` lines 118-187 (PacingContext guidance + GM Beat guidance)
- `ccya/prompts/narrate_user.j2` lines 95-98 (existing beat rendering pattern)
- `ccya/engine/extraction.py` lines 226-274 (`_storytell_messages` — context dict)
- `ccya/prompts/sections/` (directory listing — check if `_beat_history.j2` should be a subtemplate)

### Detailed steps

#### Step 1 — Wire pending_beat into storytell user context

**File:** `ccya/engine/extraction.py` lines 248-268

**What:** Add `pending_beat` to the context dict passed to `storytell_user.j2`. Read from `state["meta"]["pending_gm_beat"]` (same pattern as the narrate pipeline at turn.py:750).

Insert at line ~265 (alongside `turn_no` and `band`):

```python
            "pending_beat": (state.get("meta") or {}).get("pending_gm_beat"),
```

The existing context keys are: `narration`, `npc_roster`, `location`, `inventory`, `conditions`, `current_arc`, `all_threads`, `world_state`, `intent`, `pacing_context`, `recent_turns`, `prior_history`, `turn_no`, `band`.

**Why:** The storytell_user.j2 template currently has no beat data. Step 2 adds the rendering block — without the data, the template renders nothing.

**Validation:** After the change, the storytell user prompt template has access to `pending_beat` as a dict with keys `type`, `surface_as`, `beat_expires_turn` (or None when no beat exists).

---

#### Step 2 — Add `## GM Beat` section to storytell_user.j2

**File:** `ccya/prompts/storytell_user.j2`

**What:** Add a `## GM Beat` section between the `pacing_context` block (line 29) and the `rules_outcome` block (line 30). In the current template, the `pacing_context` block ends at line 29 with `{% endif %}`, and `rules_outcome` starts at line 30. Insert:

```
{% if pending_beat and pending_beat.type %}
## GM Beat
Type: **{{ pending_beat.type | replace('_', ' ') | upper }}**
Surface: `{{ pending_beat.surface_as | default('ambient') }}`
Expires: Turn {{ pending_beat.beat_expires_turn }}

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.
{% endif %}
```

**Jinja placement detail:** The current template flow:
```
{% endif %}{% if band %}
## rules_outcome
```

The new block goes between these two existing blocks:
```
{% endif %}{% if pending_beat and pending_beat.type %}
## GM Beat
...
{% endif %}{% if band %}
## rules_outcome
```

**Why:** Restores the missing GM Beat section that Finding 1.8 identified. The storyteller needs structural knowledge of what beat the narrator just used to make informed diversity decisions.

**Pattern reference:** `narrate_user.j2` lines 95-98 renders `**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — surface as {{ pending_beat.surface_as | default('ambient') }}`. The storyteller version is more detailed (adds expiry) because the storyteller generates the next beat.

**Validation:** Render a mock storytell user prompt with a pending_beat: should see `## GM Beat` section with type, surface, expiry. Render without pending_beat: section is absent (Jinja guard handles it).

---

#### Step 3 — Add beat history rendering to storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** Add a beat history block immediately before the `## GM Beat guidance` section header (line 135). Render `recent_beats` as a formatted list.

The existing structure around line 133-135:
```
When multiple directives are joined (e.g. "Pressure; Resolve a Threat"), prioritize the primary directive and layer the secondary as thematic guidance for beat type selection.

## GM Beat guidance
```

Insert between lines 133 and 135:
```
{% if recent_beats %}
## Recent Beats (last {{ recent_beats | length }})

{% for b in recent_beats %}
T{{ b.turn }}: {% if b.type %}{{ b.type | replace('_', ' ') | upper }}{% else %}null{% endif %}{% if b.type and b.surface_as %} ({{ b.surface_as }}){% endif %}
{% endfor %}

Use this history to vary your beat types — avoid repeating the same type more than twice in a sequence. At least one in three beats should be a non-pressure type.
{% endif %}

## GM Beat guidance
```

**Why:** Gives the LLM the data it needs to follow the ~50 lines of diversity guidance. The beat history is the input the guidance has always assumed exists.

**Pre-condition:** The `recent_beats` data must be passed to the `storytell_system.j2` rendering context. In `extraction.py` line 246, the system prompt is rendered with an empty context: `system_text = _render(env, "storytell_system.j2", {})`. Add `recent_beats` to this dict:

```python
system_text = _render(
    env,
    "storytell_system.j2",
    {
        "recent_beats": list((state.get("meta") or {}).get("recent_beats", [])),
    },
)
```

This requires `state` to be in scope in `_storytell_messages` — it already is (line 229).

**Validation:** After Plan 2 populates `meta.recent_beats`, the storytell system prompt should render a "## Recent Beats" section with the last 5 turns. Pre-feature saves without `recent_beats` render nothing (Jinja `{% if %}` guard).

---

#### Step 4 — Add Scene Imperative guidance to storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** Add one bullet to the `## PacingContext guidance` section (lines 126-133). Insert between the existing `**Tension**` bullet (line 131) and the closing paragraph (line 133):

```
- **Scene Imperative** — this scene has been active too long without meaningful progression. Your primary directive is to **advance the story** — generate choices that move the narrative forward, introduce new information, or force a decision point.
```

The existing section ends at line 133:
```
- **Tension** → do NOT add pressures unless concrete threat emerges; prefer updating existing threads

When multiple directives are joined...
```

Insert after the Tension bullet, before the "When multiple directives are joined" line.

**Why:** Scene Imperative fires correctly (at effective_scene_age >= 5) but has no behavioral weight — the storyteller doesn't change its output during SI turns. This gives the storyteller specific guidance on what to do during SI turns without touching narrate (which already has `outcome_hint="advance"` guidance).

**Validation:** When `pacing_context.directive` contains "Scene Imperative", the storyteller system prompt now includes an actionable instruction to advance the story. No behavioral change for other directives.

---

### Template rendering order

After all Plan 3 changes, the storytell prompt will render in this order:

**storytell_user.j2 (user prompt):**
1. Inventory, conditions, NPC roster, location
2. Arc, threads, world_state
3. `pacing_context`
4. `## GM Beat` (new — Step 2)
5. `rules_outcome`
6. Recent Outcomes, Prior Turn Context, Player Intent
7. CURRENT TURN NARRATION

**storytell_system.j2 (system prompt):**
1. Output schema + discipline rules
2. Actions, Outcome Summary, Thread Ops, Arc Resolution
3. Rules-outcome guidance, World State rules
4. Choice momentum
5. `## PacingContext guidance` (includes new SI bullet — Step 4)
6. `## Recent Beats` (new — Step 3)
7. `## GM Beat guidance` (existing)

### Tests to write or update

No tests (suspended during refactor). Run `make check` after all Plan 2 + Plan 3 changes are complete.
