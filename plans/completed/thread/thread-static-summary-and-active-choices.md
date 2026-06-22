# Thread Static Summary and Active Choices

## Purpose

Refine the thread update and choice systems so threads are statically summarized after creation, progress entries are short and factual, and all storyteller choices are proactive actions.

## Problem Statement

Despite prior design work establishing that thread summaries should be static, the `ThreadUpdate` model still carries a `summary` field that the storyteller (and sanitizer) can change, undermining the static-contract intent. Progress entries are verbose and speculative — they restate or forecast beyond what this turn's events factually support. Storyteller choices still sometimes land on reactive or passive phrasing despite existing anti-passive guidance, and the rigid choice-allocation rules (X choices must be about Y) constrain creativity without reliable compliance.

## Constraints

- Pipeline order is fixed (narrate → extract → arc director)
- Prompt templates are the primary interface; code changes enforce model-level constraints
- Backwards compatibility not required — old saves with `summary` in thread_update JSON will be silently ignored (Pydantic extra field handling)

## Non-goals

- Changing the progress rendering format in `_thread_list.j2` (ProgressEntry repr is a separate concern)
- Thread sanitizer algorithm changes beyond removing summary update support
- Adding code enforcement for summary length or choice structure
- Changes to the seeding prompt or scene extraction prompts

## Solution

Remove `summary` from `ThreadUpdate` so the model itself prevents summary updates. Tighten prompt guidance so progress entries are 5–7 words, factual, current-turn-only. Rewrite the Actions section so every choice starts with an active verb and the rigid allocation rules are removed. Update the sanitizer prompt so it no longer suggests or accepts summary rewrites. Add prompt guidance about resolving vs. replacing threads that are no longer relevant.

## Firm decisions

1. `ThreadUpdate.summary` is removed from the model. Thread summaries are set once at creation (`thread_add`) and never changed.
2. Progress entries are 5–7 words max, factual, and describe only what this turn's events confirm.
3. Every storyteller choice must begin with an active verb (binding rule, not suggestion).
4. Removed: structured choice allocation rules (X choices about highest-urgency thread, X about NPC, X environmental, X freeform, at least 2 must advance arc goal/active thread).
5. Kept: no passive options (wait, observe), no meandering, escalate/force decision/change irreversibly.
6. Thread replacement guidance: if a thread is no longer relevant, resolve it (if fully concluded) or set latent (if might resurface), then optionally create a new thread. Do not repurpose by updating summary.

## Risks, Ambiguities, and Blockers

- The sanitizer prompt still lists summary rewrite as step 4; the output schema still includes `summary` in thread_updates. After `summary` is removed from ThreadUpdate, sanitizer-emitted summaries will be silently ignored by model validation. Prompt must be updated to prevent useless emissions.
- Progress length (5–7 words) is prompt guidance, not code-enforced. The LLM may still exceed it. Monitoring is the only recourse.

## Status
`open`

## Phases

2 phases: model+engine changes, then prompt changes.

---

## Implementation — Phase 1: Model and Engine Changes

### Context files to load

- `ccya/models.py` (ThreadUpdate class)
- `ccya/engine/turn.py` (`_apply_thread_updates` function)
- `ccya/prompts/sanitize_thread.j2` (remove summary from output schema)

### Detailed steps

#### Step 1.1 — Remove `summary` from `ThreadUpdate`

**File:** `ccya/models.py:395-401`

**What:** Remove the `summary` field from `ThreadUpdate`:
```python
class ThreadUpdate(BaseModel):
    id: str
    active: bool | None = None
    urgency: Literal["background", "normal", "urgent"] | None = None
    progress: str | None = None
    progress_kind: Literal["advancement", "setback", "shift"] | None = None
```

**Why:** Enforce static-summary contract at the model level. Any story teller or sanitizer output containing a `summary` key in a thread_update dict is silently ignored by Pydantic's extra-field handling.

**Validation:** `make check`

#### Step 1.2 — Remove summary-update logic from `_apply_thread_updates`

**File:** `ccya/engine/turn.py:192-193`

**What:** Delete the two lines that apply `update.summary` to a thread:
```python
if update.summary is not None:
    updates["summary"] = update.summary
```

**Why:** The field no longer exists on ThreadUpdate; these lines would cause a compile/type error.

**Validation:** `make check`

#### Step 1.3 — Remove `summary` from sanitizer output schema

**File:** `ccya/prompts/sanitize_thread.j2:62`

**What:** Remove `"summary": "..."` from the `thread_updates` output JSON schema in the sanitizer prompt. Also remove line 44 ("Is summary stale? → rewrite summary field").

After:
```
### Output JSON schema

{
  "goal_update": {               // omit if unchanged
    "visible_goal": "...",
    "goal_context": "..."
  },
  "thread_updates": [            // only threads needing changes
    {
      "id": "existing_id",
      "active": true/false,      // omit if unchanged
      "urgency": "...",          // omit if unchanged
      "progress": [str, ...],    // full replacement list, omit if unchanged
      "progress_kind": "advancement"/"setback"/"shift"
    }
  ],
```

And the numbered instructions list loses item 4 entirely, renumbering 5 → 4.

**Why:** The sanitizer outputs raw dicts validated against ThreadUpdate. If the schema still shows `summary`, the LLM will emit it and waste tokens on silently-ignored fields.

**Validation:** Visual inspection of updated prompt.

---

## Implementation — Phase 2: Prompt Guidance Changes

### Context files to load

- `ccya/prompts/storytell_system.j2` (full file)
- `ccya/prompts/sanitize_thread.j2` (already partially updated in Phase 1)

### Detailed steps

#### Step 2.1 — Update `thread_update` guidance in storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2:28`

**What:** Replace the existing `thread_update` guidance block with content that:
- Removes the `summary` option entirely
- States progress is 5–7 words max, factual, current-turn only
- States threads are static — if no longer relevant, resolve/set-latent + create new

Current (line 28):
```
**`thread_update`:** `summary` OR `progress` — not both. `summary` (4–7 words) when the thread's nature or direction changed, describing a broad SITUATION — not an objective or action. `progress` (one sentence) explaining HOW the thread's trajectory evolved beyond what the narration shows, with an optional `progress_kind` classifying the change. Do NOT emit `progress` that restates what happened — if a reader would learn nothing new about the thread's trajectory, omit it. Urgency decays one step per turn unaddressed. If inactive 2+ turns without new progress, set `active: false`. DO NOT change a thread's `summary` after its initial creation unless the thread's fundamental nature has shifted. The summary represents a single plot point — it is static, not evolving. Progress entries are how we see things changing. Only update `progress`, never `summary`.
```

Replacement:
```
**`thread_update`:** Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation or forecast. `progress_kind` classifies the change. Do NOT restate what narration already showed. If the thread is no longer relevant, resolve it (thread_resolve) or set active: false, then create a new thread via thread_add — do not repurpose with progress that contradicts the summary.
```

Also update the schema example on line 10 to remove `summary`:
```
"thread_update": [{"id": "...", "progress": "...", "progress_kind": "advancement|setback|shift", "urgency": "background|normal|urgent", "active": true}],
```

**Why:** Enforces all four user requirements: static summaries, 5–7 word progress, factual/turn-only, thread replacement instead of repurposing.

**Validation:** Visual inspection.

#### Step 2.2 — Update `Actions` guidance in storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2:78-82`

**What:** Replace current Actions section with:
```
## Actions

Emit exactly 4 choices, ~10 words each. Every choice must begin with an active verb. Each choice must escalate, force a decision, or change things irreversibly. No meandering ("look at that", "talk to them"), no passive options (wait, observe), nothing generic enough for any protagonist in any setting. Span different postures — not variations of the same approach.
```

Key changes from current:
- "Every choice must begin with an active verb" — new binding rule
- Removed: "active voice as if spoken by the PC" (redundant with active verb rule)
- Removed: entire "Structure: one pursues the highest-urgency thread..." paragraph
- Removed: "At least 2 of 4 must directly advance an arc goal or active thread"
- Kept: "Span different postures — not variations of the same approach" (diversity guidance)
- Kept: "Emit exactly 4 choices, ~10 words each"
- Kept: "Never emit an empty array"
- Kept: "Each choice must escalate, force a decision, or change things irreversibly"
- Kept: no meandering, no passive options

**Why:** Every choice is now structurally proactive (verb-first). The rigid allocation rules constrained creativity without reliable compliance.

**Validation:** Visual inspection.

#### Step 2.3 — Update sanitizer progress guidance

**File:** `ccya/prompts/sanitize_thread.j2`

**What:** In the numbered instructions section (lines 38-45), replace item 5 (now 4 after step 1.3):
```
4. Are progress entries noisy, dedup-worthy, or too long? → provide updated progress list (5–7 words per entry, factual).
```

Also add a brief instruction to the top-level rules: "Progress entries must be 5–7 words max, factual, and describe only what the narrative evidence confirms."

**Why:** Align sanitizer with the same length/factuality rules as storyteller progress entries.

**Validation:** Visual inspection.

#### Step 2.4 — Update `thread_add` guidance for summary length

**File:** `ccya/prompts/storytell_system.j2` (around line 30)

**What:** In the `thread_add` guidance, add: "Thread summaries: 5–7 words, a very broad conceptual bucket for the tension — not a detailed description. A good summary fits 3–4+ progress updates over the thread's lifetime."

**Why:** User explicitly said summary should be 5-7 words, very broad bucket.

**Validation:** Visual inspection.

### Tests to write or update

No tests currently exist (refactor phase). Verification is via `make check` (lint + typecheck) and visual prompt review.

---

## Documentation updates

### docs/design/complete/arc-thread-system-design.md

- `ThreadUpdate` model shape: remove `summary` from field list
- Add row to decision table: "ThreadUpdate.summary removed — threads are static after creation. Replace via resolve+add, not update."
- Update "What Is Changed" section to note `ThreadUpdate.summary` removed
- Update the ThreadUpdate model snippet to match

### docs/repomap.md

- Update any reference to ThreadUpdate fields if present
