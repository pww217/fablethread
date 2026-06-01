# Reduce thread proliferation — prompt-only fixes

## Purpose

Reduce the number of active threads in play by improving how the storyteller LLM is prompted to consolidate, update, and resolve threads — with no Python-side enforcement changes.

## Problem Statement

The system produces ~1 thread per turn on average, with many overlapping (e.g., `naval_coordination_failure` + `electronic_jamming_interference` — same problem, different wording). Completed threads are never resolved because the LLM (a) doesn't know `thread_resolve` exists as a first-class operation, (b) treats thread summaries as immutable once created, creating new threads when situations evolve instead of updating existing ones, and (c) has no guidance that "superseded by events" is a valid resolution path.

## Constraints

- Prompt-only changes. No Python enforcement, no JS-side logic, no new model fields.
- Must not change the JSON output schema that Python validates against.
- Must preserve or improve existing behavior for well-behaved games.

## Non-goals

- No Python-side fuzzy dedup or overlap detection (deferred for now)
- No active thread cap enforcement (soft prompt limit only)
- No arc-level resolution changes (already covered by prior plans)
- No changes to narrate prompts or scene/state extract prompts

## Solution

Three targeted additions to `storytell_system.j2`:

1. **Expose `thread_resolve`** as a first-class operation with clear guidance on when to resolve (completed, superseded, merged, no longer relevant).
2. **Teach the LLM that threads can be fully reshaped** via `thread_update` — the summary, progress, and urgency are all mutable at any turn. A thread's identity is its `id`; its wording can evolve.
3. **Strengthen the overlap/consolidation check** with concrete examples of "update existing, don't create new" and a directive to prefer broader threads.

## Firm decisions

1. Only `ccya/prompts/storytell_system.j2` and `ccya/prompts/storytell_user.j2` will be modified.
2. No JSON schema changes — `thread_resolve` already exists in StorytellerResult.
3. The existing CRITICAL overlap-checking instruction is retained and expanded, not replaced.
4. All three changes go in one phase (same file, same concern, same context block).

## Risks, Ambiguities, and Blockers

- The LLM might over-resolve threads prematurely. Mitigation: guidance says "only resolve when genuinely concluded or superseded."
- Adding more instructions increases system prompt length. The thread operations section grows by ~40 lines (~300 tokens). Well within budget.
- `ThreadResolution.resolution_state` accepts only `Literal["resolved", "failed", "abandoned"]` (ccya/models.py:346). The plan's examples must stay within these values — no `"superseded"`.

## Status

`completed`

## Phases

1. Prompt edits to storytell_system.j2 + storytell_user.j2

## Implementation — Phase 1: Prompt edits

### Context files to load
- `ccya/prompts/storytell_system.j2` (full file, already loaded)
- `ccya/prompts/storytell_user.j2` (full file, already loaded)

### Detailed steps

#### Step 1.1 — Add `thread_resolve` section to system prompt

**File:** `ccya/prompts/storytell_system.j2`

**What:** Insert a new section between "Thread operations — scope decides lifecycle" (ends at line 53 with the existing CRITICAL overlap-checking block) and "## Arc resolution" (line 55), documenting `thread_resolve` as a standalone operation. Also add `thread_resolve` to the JSON schema example at lines 10-15: insert after the `thread_update` line and before the `arc_resolve` line. Use the form `"thread_resolve": [{"id": "thread_id", "resolution_state": "resolved|failed|abandoned", "outcome": "One sentence outcome."}],`.

**Why:** `thread_resolve` is a valid StorytellerResult field (ccya/models.py:416) with engine support in `_apply_thread_resolutions()` (turn.py:296-370), but is absent from the system prompt — the LLM doesn't know it can resolve individual threads directly. No schema changes needed; the Pydantic model already accepts it.

**Content to add:**
```
`thread_resolve`: A list of objects to mark individual threads as resolved, failed, or abandoned — independent of arc resolution. Use this when a thread has run its course, was superseded by events, or merged into a broader concern. THIS IS VALID — not every thread needs a dramatic completion. Example: `[{"id": "enemy_presence_in_ruins", "resolution_state": "abandoned", "outcome": "Threats absorbed into broader encirclement situation."}]`

Valid `resolution_state` values: `"resolved"` (thread reached its conclusion), `"failed"` (thread's goal was thwarted), `"abandoned"` (thread superseded, merged, or no longer relevant — use for consolidation).

When to resolve:
- Thread reached its natural conclusion → `"resolved"` or `"failed"`.
- Thread's concern was absorbed into a different, broader thread → `"abandoned"` (resolve the narrower one, keep the broader one; outcome explains why).
- Thread no longer relevant to the current story direction → `"abandoned"`.
- Thread existed long enough that its urgency decayed to background without renewal → `"abandoned"`.

CRITICAL: Do NOT resolve threads that are still meaningfully active. `thread_resolve` removes the thread from the active list — use it decisively but sparingly. Prefer `thread_update {active: false}` to dormant-demote threads that might resurface.
```

**Validation:** Read the modified file and verify the new section is coherent between the thread operations section and the arc resolution section.

#### Step 1.2 — Add instruction that thread summaries are mutable

**File:** `ccya/prompts/storytell_system.j2`

**What:** Insert guidance inside the `thread_update` block (after line 43's example) telling the LLM it can and should rewrite a thread's summary/progress/urgency as the situation evolves — a thread's identity is its `id`, not its current wording.

**Why:** The `summary` field exists on ThreadUpdate (ccya/models.py:354) and is applied by `_apply_thread_updates()` (turn.py:188-189). The LLM can already mutate summaries but doesn't know it — it creates new threads instead of updating existing ones. This change closes the gap between capability and prompt guidance.

**Content to add** (as a new paragraph after the thread_update example, before the CRITICAL RULES at line 45):
```
IMPORTANT: A thread's identity is its `id` — not its current summary, progress, or urgency. When a situation evolves, update the existing thread via `thread_update` with new wording, rather than creating a new thread. Do not create a thread for every encounter variant — broaden it. Examples:
- Instead of creating `enemy_presence_in_ruins` + `alleyway_pursuit` + `encirclement_threat` as three threads, maintain one broader thread like `enemy_contact_advance` and update its summary/progress each turn.
- Instead of creating `naval_coordination_failure` and `electronic_jamming_interference` as separate threads, keep one thread and widen its summary to encompass both symptoms.
- When a threat escalates (e.g., sniper → pursuit → encirclement), update the existing thread to reflect the new reality. Do not spawn a new thread per escalation step.
```

**Validation:** Read the modified file and verify the new paragraph follows the thread_update example and precedes the CRITICAL RULES.

#### Step 1.3 — Strengthen overlap check with concrete examples

**File:** `ccya/prompts/storytell_system.j2`

**What:** Replace the current single-line consolidation instruction at line 53 with a more detailed version that includes concrete examples and a stronger directive.

**Why:** The existing "check for conceptual overlap" instruction is too abstract. The LLM needs concrete examples of what counts as overlap and a stronger directive to prefer updating over creating. Source data from actual games shows 9 threads created in 9 turns with significant overlap.

**Current text (line 53):**
```
CRITICAL: Before emitting `thread_add`, check all active and latent thread summaries for conceptual overlap. If an existing thread covers the same story tension (even with a different ID), do NOT emit `thread_add` — instead update that existing thread via `thread_update`. Only create new threads when the tension is genuinely distinct.
```

**Replacement text:**
```
CRITICAL — CONSOLIDATE BEFORE CREATING: Before emitting `thread_add`, scan every active and latent thread for conceptual overlap with the proposed new thread. Overlap means: same antagonist, same problem domain (e.g., both about enemy forces), same NPC, same location-based threat, or same thematic tension. If ANY existing thread covers related ground — even with a different ID, different wording, or a different specific instance — do NOT create a new thread. Instead, update the existing thread via `thread_update` with a broadened summary and new progress.

Only create a new thread when the tension is genuinely, fundamentally distinct from everything already tracked. Examples of when to UPDATE an existing thread instead:
- A sniper threat and a pursuer threat are both "enemy contact" — update one broader thread.
- A jammed radio and a weak signal are both "communication problems" — update one thread.
- A guard confrontation and a locked door are both "obstacles to the objective" — update one thread.
- An NPC's moral crisis and a faction's propaganda campaign are both "thematic pressure" — consider keeping one thread.

When in doubt about overlap, UPDATE an existing thread rather than creating a new one. You can always narrow later.
```

**Validation:** Read the modified file and verify the replacement is the final paragraph of the thread operations section, before the "## Arc resolution" header.

#### Step 1.4 — Show total thread count in storytell user prompt

**File:** `ccya/prompts/storytell_user.j2`

**What:** Add a `(N total)` count to the threads section header so the LLM has visibility into how many threads exist.

**Why:** The LLM gets no awareness of total thread count — it sees the list but doesn't have a quantitative sense. Showing `(N total)` makes the proliferation visible and gives the consolidation instructions concrete weight. `all_threads` is already a list in the template context (context.py:261, extraction.py:260).

**Current text (line 14):**
```
## threads (all — unified list; [SCENE] threads are auto-removed on location change)
```

**Replacement text:**
```
## threads ({{ all_threads|length }} total — unified list; [SCENE] threads are auto-removed on location change)
```

**Validation:** Read the modified file and verify the thread count is rendered. This depends on `all_threads` being a list (it is — the template iterates it on line 15).

### Tests to write or update

No tests to write — this is a prompt-only change. Validate by running a game turn and inspecting `ev.py turn <N>` to confirm the storyteller output uses `thread_resolve`, consolidates threads, and produces fewer net threads per turn.
