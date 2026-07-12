# Supporting Changes — Phase 1: Dice Roll Frequency Reduction

## Purpose

Tighten the ruling LLM's roll criteria to reduce roll rate from ~69% to ~35-45%, breaking the fail→condition→harder→fail spiral.

## Firm decisions

- Ruling system prompt roll criteria tightened from three permissive conditions to three restrictive conditions.
- Expanded no-roll list added.
- Thread context added to ruling user prompt so LLM can assess thread relevance.
- Ruling schema updated: `tension_delta` field removed from `IntentEnvelope` in the schema (since Phase 1 of the core plan removed it from the model). The LLM should no longer emit `tension_delta`.

## Status

`completed`

## Implementation — Phase 1: Dice Roll Frequency Reduction

### Context files to load

- `ccya/prompts/ruling_system.j2` — full file (97 lines)
- `ccya/prompts/ruling_user.j2` — full file (36 lines)

### Detailed steps

#### Step 1.1 — Tighten roll criteria in ruling_system.j2

**File:** `ccya/prompts/ruling_system.j2`

**What:** Replace the "Decision rule — default NO" section (lines 18-25):

Old:
```
## Decision rule — default NO

Set `check.required=true` only when ALL THREE hold:
- (a) The player initiates an action with clear intent — including speech acts directed at a character who has reason to resist
- (b) Failure has a real, meaningful consequence
- (c) The outcome is genuinely uncertain

Set `required=false` for: idle observation, unimpeded movement, item inspection, casual conversation, passing time, routine commerce with a willing counterparty (buying at market price, paying a stated fee, settling a known debt).
```

New:
```
## Decision rule — default NO

Set `check.required=true` only when ALL THREE hold:
- (a) Occurs at a major narrative pivot — scene transition, decisive confrontation, gamble that alters the story. Actions in scenes with urgent threads are more likely to qualify.
- (b) Failure has a real, irreversible consequence
- (c) The outcome is genuinely uncertain

Set `required=false` for: idle observation, unimpeded movement, item inspection, casual conversation, passing time, routine commerce, information gathering, actions already attempted in this scene without new stakes, taking cover, reloading, healing, using a prepared item as intended.
```

**Why:** Criterion (a) narrowed from "clear intent + meaningful action" to "major narrative pivot" with thread context qualifier. No-roll list expanded with common LLM over-roll patterns.

**Validation:** After deployment with Plan 1 core, run `ev play --llm --turns 20` and check roll rate via `ev check --checker roll_band_consistency` or manual summary.

#### Step 1.2 — Add thread context to ruling_user.j2

**File:** `ccya/prompts/ruling_user.j2`

**What:** Add an "Urgent Threads" section between the "scene" section (line 14) and the inventory section. Only show when urgent threads exist:

```
{% if urgent_threads %}
## Urgent Threads
{% for t in urgent_threads %}
- {{ t.id }} — {{ t.summary }}
{% for p in t.progress[-3:] %}
    {{ p.kind }} — "{{ p.text }}"
{% endfor %}
{% endfor %}
{% endif %}
```

Note: `ProgressEntry` has no `turn` field (only `kind` and `text`). Turn numbers omitted — recency is conveyed by the `-3:` slice (last 3 entries).

The `urgent_threads` variable must be passed from the Python caller. In `ccya/engine/ruling.py`'s `_ruling_messages()` function, add `urgent_threads` to the user prompt context — filter `arc.threads` to those with `urgency == "urgent"`, include last 3 progress entries with turn numbers.

**Why:** The ruling LLM needs thread context to apply criterion (a) — whether the action relates to a major narrative pivot.

**Validation:** Check rendered ruling user prompt contains "## Urgent Threads" when threads are urgent.

#### Step 1.3 — Remove `tension_delta` from ruling schema and field rules

**File:** `ccya/prompts/ruling_system.j2`

**What:**
- Remove the "## Tension delta" section (lines 54-64) entirely.
- Remove `tension_delta` from the Schema JSON (line 76).
- Remove `tension_delta` from the Field rules (line 92).

**Why:** `tension_delta` removed from `IntentEnvelope` in Plan 1 Phase 1. The ruling LLM should not emit a field that is no longer consumed.

**Validation:** `grep -n 'tension_delta' ccya/prompts/ruling_system.j2` should return 0 matches.

#### Step 1.4 — Wire urgent_threads context in ruling.py

**File:** `ccya/engine/ruling.py`

**What:** In the function that builds ruling user messages, add `urgent_threads` to the Jinja context. Filter active threads with `urgency == "urgent"`, include id, summary, and last 3 progress entries.

**Why:** The ruling user template references `urgent_threads` — the Python side must pass it.

**Validation:** After a turn with urgent threads, check rendered ruling user prompt includes the urgent threads section.

### Tests to write or update

No tests exist. Run `make check` after all phases of Plan 2 are complete.
