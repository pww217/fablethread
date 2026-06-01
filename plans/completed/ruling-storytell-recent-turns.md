# Wire recent turn narration into ruling + adjust cutoffs for narrator/storytell

## Purpose

Give ruling T-1's full narration (it currently only gets a brief outcome summary). Increase the narrator's recent turn window to 20 bullets and storytell's to 10, both starting from T-2 (since T-1 is already covered as the "last turn" in narrator and as `narration` in storytell).

## Problem Statement

Ruling (Call 0) only receives `last_outcome` — a brief summary string. It has no access to the prior turn's full narrative, which limits its ability to classify intent with story continuity. Additionally, the narrator only loads 1 prior turn and storytell loads 2, but both should carry deeper history: narrator up to 20 turns and storytell up to 10 turns, both starting from T-2 since T-1 is already fully included elsewhere.

## Constraints

- No backwards compatibility required — rip and replace.
- Context budget: 8k tokens effective. 20 turns of full narrative is substantial — the existing `trim_messages()` truncation will handle overflow.
- One source of truth: `recent_turns` is loaded once at turn start from `chronicle.md`.
- On turn X, available turns from chronicle are T-1 through T-(X-1).

## Non-goals

- Changing scene extraction's recent_turns handling (it needs T-1 for delta context).
- Changing `load_last_narration()` or chronicle format.
- Modifying `trim_messages()` behavior.

## Solution

Increase `_recent_turn_count()` to load enough turns for all consumers. Each phase slices the shared `recent_turns` list appropriately:
- **Ruling**: `[-1:]` → T-1 only (full narration, replaces `last_outcome`)
- **Narrator**: `[:-1][-20:]` → T-2 through ~T-21, capped at 20 bullets
- **Storytell**: `[:-1][-10:]` → T-2 through ~T-11, capped at 10 bullets
- **Scene extraction**: unchanged at `[-1:]` → T-1

## Firm decisions

1. `_recent_turn_count()` returns 21 — enough for narrator's 20 bullets + T-1 for ruling.
2. Ruling gets `recent_turns[-1:]` = [T-1] — the full prior narration, not just `last_outcome`.
3. The `last_outcome` field stays in the template for backward compat but ruling's primary context is now the full narrative.
4. Narrator receives up to 20 turns starting from T-2. Template renders all as `## Recent Turns` bullets.
5. Storytell receives up to 10 turns starting from T-2. Template renders them as prior context.
6. Scene extraction stays at `[-1:]` — it needs T-1 for NPC/location delta tracking.

## Risks, Ambiguities, and Blockers

- On turn 1: no prior turns exist. All consumers get empty lists. Correct behavior.
- On turn 2: only T-1 exists. Ruling gets [T-1]. Narrator/storytell get [] (T-2 doesn't exist yet). Correct.
- On turn 3: T-1 and T-2 exist. Ruling gets [T-1]. Narrator gets [T-2] (1 bullet). Storytell gets [T-2] (1 bullet).
- 20 turns of full narrative could be large. `trim_messages()` handles token overflow — no extra work needed.
- The `RulingBoundary` docstring previously noted `recent_turns` as a dead field — needs updating.

## Status

`completed` — committed 166e56f

## Phases

1. Single phase: increase turn load count, wire different slices to ruling/narrator/storytell, update templates and boundary models.

## Implementation — Phase 1: Wire recent turns with per-phase slicing

### Context files to load
- `ccya/engine/turn.py` (lines 584-586: `_recent_turn_count`, lines 589-623: `_ruling_phase`, lines 869-878: turn setup)
- `ccya/engine/ruling.py` (lines 16-45: `_ruling_messages`)
- `ccya/prompts/ruling_user.j2`
- `ccya/engine/extraction.py` (lines 226-274: `_storytell_messages`, line 419: scene slice, line 522: storytell slice)
- `ccya/prompts/storytell_user.j2` (lines 36-38: recent_turns block)
- `ccya/prompts/narrate_user.j2` (lines 56-62: Recent Turns section)
- `ccya/prompts/context.py` (lines 187-199: `RulingBoundary`)

### Detailed steps

#### Step 1.1 — Increase `_recent_turn_count()` to 21

**File:** `ccya/engine/turn.py:584-586`

**What:** Change `_recent_turn_count()` to return 21 instead of 1. Update its docstring.

**Why:** 21 turns = 20 narrator bullets (T-2 to T-21) + 1 turn for ruling (T-1). This is the max any consumer needs from chronicle.

**Validation:** `_recent_turn_count({})` returns 21.

#### Step 1.2 — Pass T-1's full narration to ruling

**File:** `ccya/engine/ruling.py:16-45`

**What:** Add `recent_turns: list[dict[str, Any]] | None = None` parameter to `_ruling_messages()`. Add it to the template context dict.

**Why:** Ruling needs access to T-1's full narrative for intent classification continuity.

**Validation:** `grep -n "recent_turns" ccya/engine/ruling.py` shows the new parameter.

#### Step 1.3 — Wire recent_turns in `_ruling_phase()`

**File:** `ccya/engine/turn.py:608-623`

**What:** After the existing `_prev_events` loading block, pass `ctx.recent_turns[-1:]` as the `recent_turns` kwarg to `_ruling_messages()`. Keep the existing `last_outcome` parameter as well.

**Why:** Ruling gets T-1's full narrative. The `last_outcome` stays for now — the template can use either or both.

**Validation:** Rendered ruling prompt includes the full T-1 narrative when available.

#### Step 1.4 — Update ruling template for recent turns

**File:** `ccya/prompts/ruling_user.j2`

**What:** Add a block after the existing `last_outcome` section:

```jinja2
{%- if recent_turns %}
## Last Turn Narrative (T{{ recent_turns[-1].turn }})
{{ recent_turns[-1].narrative }}
{%- endif %}
```

**Why:** Gives the ruling LLM the full prior turn narrative for context, replacing the thin outcome summary as the primary context source.

**Validation:** Rendered ruling prompt includes full T-1 narrative when available.

#### Step 1.5 — Update `RulingBoundary`

**File:** `ccya/prompts/context.py:187-199`

**What:** Add `recent_turns: list[ChronicleEntryBlock] = Field(default_factory=list)` to `RulingBoundary`. Update docstring to remove the "dead field" note and document the new field.

**Why:** Boundary model must match what the template renders.

**Validation:** `python -c "from ccya.prompts.context import RulingBoundary; print('recent_turns' in RulingBoundary.model_fields)"` prints `True`.

#### Step 1.6 — Cap narrator's recent_turns to 20 bullets

**File:** `ccya/engine/turn.py:826-828` (in `_narrate_setup()`)

**What:** In `_narrate_setup()`, change line 828 from `recent_turns=ctx.recent_turns` to `recent_turns=ctx.recent_turns[:-1][-20:]`. This slices the full 21-turn list to exclude T-1 and cap at 20 before passing to the template.

**Why:** Narrator gets T-2 through T-21, max 20 bullets. T-1 is excluded because it's already the "last turn" rendered separately in the narrate template's existing flow. `ctx.recent_turns` itself stays as the full 21-turn list so that ruling (step 1.3) can access T-1 via `ctx.recent_turns[-1:]`.

**Do NOT modify `ctx.recent_turns` at TurnContext creation (line 878).** That would break ruling's access to T-1.

**Validation:** With 25 turns in chronicle, the slice passed to `_narrate_messages` has 20 entries (T-2 to T-21). `ctx.recent_turns` still has 21 entries.

#### Step 1.7 — Adjust storytell slice to 10 turns from T-2

**File:** `ccya/engine/extraction.py:522`

**What:** Change `recent_turns=(recent_turns or [])[-2:]` to `recent_turns=(recent_turns or [])[:-1][-10:]`.

**Why:** Storytell gets T-2 through T-11, max 10 bullets. T-1 is excluded (already in `narration`). The `[:-1]` excludes T-1, `[-10:]` caps at 10.

**Validation:** With 15 turns in chronicle, storytell receives 10 entries.

#### Step 1.8 — Update storytell template to render all recent turns

**File:** `ccya/prompts/storytell_user.j2:36-38`

**What:** Replace the single-turn rendering block:

```jinja2
{% if recent_turns %}
## prior turn context
{% for t in recent_turns %}
**T{{ t.turn }}:** {{ t.narrative }}
{% endfor %}
{% endif %}
```

**Why:** Currently only renders `recent_turns[-1]` (one turn). After the slice change, recent_turns contains up to 10 turns — the template should render all of them as bullets, matching the narrator's pattern.

**Validation:** Rendered storytell prompt shows all available prior turns as labeled bullets.

### Tests to write or update

Tests are temporarily removed during refactor. Validate by running `make check` after all changes.
