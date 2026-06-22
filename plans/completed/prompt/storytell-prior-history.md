# Storytell prior_history context

## Purpose

Give the storytell extractor the last 10 summarized outcome bullets (its own prior `outcome_summary` values) to improve arc/thread awareness across turns.

## Problem Statement

The storyteller is responsible for thread and arc lifecycle decisions (resolve, add, update urgency, eventually resolve arcs), but has no multi-turn summarized context. It only sees the last turn's full prose narrative. This makes it blind to narrative trajectory — it can't tell whether a thread has been building for 5 turns or 2, or whether the current arc's goal is approaching resolution. The narrator already gets both full prose (1 turn) and summary bullets (up to 20); the storyteller should too.

## Constraints

- Cap at 10 bullets (tighter than narrator's 20) — enough for an arc's attention span, not so many it adds noise.
- Keep turn-number prefixes (`[T{n}]`) in LLM prompts — both storyteller and narrator need to see *when* each outcome occurred.
- `strip_turn_prefix` filter stays in config.py — still needed for player-facing UI, just removed from LLM prompts.
- No test changes — tests are removed during refactor per AGENTS.md.

## Non-goals

- Changing the narrator's cap of 20 — out of scope.
- Adding any new model fields or config keys — hardcoded slice of 10 is sufficient.
- Rewriting outcome_summary guidance or prompt structure.
- Changing the storyteller's existing `recent_turns` (full prose) behavior — this is additive, not replacing.

## Solution

Add `prior_history` (last 10 bullets from state) to the storytell user prompt context, rendered as a new "## Recent Outcomes" block before the existing "## last turn's context" block. Keep turn-number prefixes. Also remove `strip_turn_prefix` from the narrator's prompt so it too preserves turn numbers for the LLM.

## Firm decisions

1. **Python-side slice to 10.** `_storytell_messages` slices `state["meta"]["prior_history"][-10:]` before passing to template.
2. **Keep turn numbers in LLM prompts.** Both storytell and narrate templates render bullets with `- [T{n}]` prefix intact. `strip_turn_prefix` filter is kept for future UI use only.
3. **Place "## Recent Outcomes" right before "## last turn's context".** Bullets (summary) then full prose — natural information-dense-to-sparse ordering.
4. **Section header: "## Recent Outcomes".** Distinct from narrator's "## Prior History", shorter window (10 vs 20).

## Risks, Ambiguities, and Blockers

None. The change is purely additive (new template variable in one prompt, filter removal in another). No model changes, no pipeline changes, no config changes.

## Status
`completed`

## Phases

1 phase: add prior_history to storytell context, add template section, fix narrator template to keep turn numbers, update StorytellerBoundary.

## Implementation — Phase 1: Add prior_history to storytell context

### Context files to load

- `ccya/engine/extraction.py` — `_storytell_messages` function (lines 226-273)
- `ccya/prompts/storytell_user.j2` — template insertion point (lines 37-39)
- `ccya/prompts/narrate_user.j2` — template line 51 (prior_history rendering with filter)
- `ccya/prompts/context.py` — `StorytellerBoundary` class (lines 265-285)

### Detailed steps

#### Step 1.1 — Add prior_history to storytell template context

**File:** `ccya/engine/extraction.py`, function `_storytell_messages` (line 226), template context dict (lines 248-267)

**What:** Add a `prior_history` key to the `user_ctx` dict, sourced from `state["meta"]["prior_history"]`, sliced to the last 10 entries. Gracefully handle missing `meta` key or missing `prior_history` key.

```python
"prior_history": list((state.get("meta") or {}).get("prior_history", [])[-10:]),
```

Insert after `"recent_turns"` (line 264) and before `"turn_no"` (line 265), keeping the roughly grouped order (arc/thread context → world state → history → intent → narration).

**Why:** The slice ensures the storyteller only sees the most recent 10 outcome bullets. The `get` chain handles missing state gracefully.

**Validation:** `make check` passes. Observe a rendered storytell prompt contains the `prior_history` key with at most 10 entries.

#### Step 1.2 — Add "## Recent Outcomes" section to storytell_user.j2

**File:** `ccya/prompts/storytell_user.j2`, between lines 37-38 (before "## last turn's context")

**What:** Insert a new section block that renders `prior_history` bullets with turn-number prefixes intact (no `strip_turn_prefix` filter):

```
{% if prior_history %}
## Recent Outcomes
{% for b in prior_history %}{{ b }}
{% endfor -%}
{% endif %}
```

Place it immediately before `{% if recent_turns %}` (line 37) so the layout is:

1. ... existing sections ...
2. ## Recent Outcomes (new — summary bullets, most recent 10)
3. ## last turn's context (existing — full prose, most recent 1 turn)
4. ... remaining sections ...

**Why:** Bullets (summary) before full prose creates natural information density ordering. The storyteller sees the trajectory first, then reads the most recent turn in detail.

**Validation:** For a game with 3+ turns, inspect rendered storytell prompt and verify the "## Recent Outcomes" block appears with turn-prefixed bullets. For a fresh game with no prior_history, verify the block does not render (empty/absent).

#### Step 1.3 — Remove `strip_turn_prefix` filter from narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2`, line 51

**What:** Change `{{ b | strip_turn_prefix }}` to `{{ b }}` so turn-number prefixes are preserved in the narrator's "## Prior History" section.

**Before:**
```jinja2
{% for b in prior_history %}{{ b | strip_turn_prefix }}
```

**After:**
```jinja2
{% for b in prior_history %}{{ b }}
```

The `strip_turn_prefix` filter function in `ccya/engine/config.py` stays — it may be used in the future for player-facing UI rendering.

**Why:** Per design decision: "In user prompts, it should always, always, always have the turn number prepending it." The narrator and storyteller prompts are both user prompts (LLM-facing), so both should show turn numbers.

**Validation:** Inspect a rendered narrator prompt. Prior history bullets should include the `[T{n}]` prefix (e.g., `- [T3] Curtis searched the captain's cabin` not just `Curtis searched the captain's cabin`).

#### Step 1.4 — Add `prior_history` field to StorytellerBoundary

**File:** `ccya/prompts/context.py`, class `StorytellerBoundary` (lines 265-285)

**What:** Add `prior_history: list[str]` field to match the new template variable. Place it after `recent_turns` (line 283) for logical grouping with other history-related fields.

**Before:**
```python
    recent_turns: list[ChronicleEntryBlock]
    turn_no: int
    band: str
```

**After:**
```python
    recent_turns: list[ChronicleEntryBlock]
    prior_history: list[str]
    turn_no: int
    band: str
```

**Why:** The alignment check (`tests/test_alignment.py`) validates that all root template variables exist on `StorytellerBoundary`. Without this field, `make check` fails on the Pydantic model validation.

**Validation:** `make check` passes, including the alignment test that checks `StorytellerBoundary` covers all root variables in `storytell_user.j2`.

### Tests to write or update

No test changes — tests are removed during refactor per AGENTS.md. Run `make check` at end of phase.

### REPOMAP updates required

- `ccya/prompts/context.py` — `StorytellerBoundary` gains `prior_history: list[str]`
