# Fix ruling check resolution and arc narration mechanical issues

## Status
`completed`

## Phases

2 phases: Phase 1 — arc narration prompt data + merge safety; Phase 2 — ruling silent no-roll fallback logging + validation.

## Issue

Two independent classes of bugs producing dead-silent failures:

**Arc narration.** (1) `narrate.py` builds thread context dicts without `last_seen_turn`, so `_arc.j2` renders `(last seen T?)` every turn. (2) `_merge_arc_update()` silently wipes engine-managed threads and completed_threads on ANY narrator arc_update because Pydantic defaults all CampaignArc fields to non-None values (`[]` for lists), and the merge function checks `is not None` — which always passes, triggering wholesale replacement with empty lists at delta.py:56-64. (3) Narrator ARC_UPDATE blocks that emit thread fields bypass the prompt's "do not include threads" instruction and silently overwrite engine state via the same wholesale replacement path. (4) `_upsert_threads()` in `delta.py:28-41` is defined but never called — dead code.

**Ruling check resolution.** `_call_ruling()` falls back to `check=RulesCheck(required=False)` on parse failure (no usable log). The LLM may emit `check.required=true` but omit `skill` (encouraged by the "omit null/empty fields" prompt instruction); the validator at `models.py:118` coerces empty skill to `None`, and the gate at `turn.py:768` (`intent.check.required and intent.check.skill`) silently skips resolution. No log distinguishes "no check needed" from "check was requested but skill was empty" — the operator sees `rolled=False` in events.jsonl either way.

## Solution

**Phase 1 — Arc narration:** Fix `_merge_arc_update()` to skip Pydantic-defaulted empty lists (prevents silent wiping of engine threads). Filter narrator arc_update keys before validation (prevents thread-field contamination when narrator emits malformed data). Add `last_seen_turn` to the thread context dict in `narrate.py`. Remove dead `_upsert_threads()` from `delta.py`.

**Phase 2 — Ruling checks:** Validate inside `_call_ruling()` that `check.required=True` implies `skill` is non-None (treat as parse error, triggering retry). Add a log line at `turn.py:791` when the `else` branch fires but `intent.check.required` was True, so operators see exactly why no roll happened.

## Firm decisions

1. `_merge_arc_update()` continues to do wholesale thread replacement — that is correct for engine callers (`_apply_thread_signals`, `_apply_thread_resolutions`) which return the complete thread state.
2. Thread safety for narrator arc_update is enforced at the call site (`turn.py:1277-1293`), not inside `_merge_arc_update()`. Filter on the dict before it reaches merge.
3. `_upsert_threads()` in `delta.py` is dead code — remove it.
4. No new Pydantic models or config keys.
5. No Prompt modifications for arc narration other than the `_arc.j2` template (which already works correctly for the data it receives — the fix is in the data).

## Non-goals

- No changes to the arc threading model, pipeline architecture, or CampaignArc schema.
- No changes to the LLM ruling engine's prompt intent or classification logic — only the Python-side validation and logging are fixed.
- No adding `phase` field to CampaignArc model. `narrate.py:58` reads `.get("phase", "setup")` from the raw state dict — this is unused in prompts and not part of the narrator arc_update flow. Leave it as-is; it is inert.

## Risks, Ambiguities, and Blockers

- `_merge_arc_update()` silently wipes `threads` and `completed_threads` when Pydantic defaults CampaignArc lists to `[]`. Step 1.1 fixes this by changing the merge function's checks from `is not None` to truthiness (`if au.threads:`), which skips merging for empty lists while still allowing non-empty updates from engine callers (who return full computed thread lists). Thread management is engine-only by design, so silently ignoring narrator-emitted threads is correct behavior but worth noting.
- `CampaignArc.model_validate()` does NOT silently drop unrecognized keys like `threads` — it validates the full nested structure (`list[ArcThread]`). If the narrator emits malformed thread data with all required ArcThread fields populated (e.g., id + summary + scope), validation succeeds and `_merge_arc_update()` overwrites engine state. Step 1.2 prevents this by removing those keys before validation.
- The `_call_ruling()` validation of `required=True` → `skill` presence adds a new retryable failure. If the LLM reliably omits `skill` on `required=true`, this could increase ruling retries. Mitigation: update the ruling prompt to explicitly instruct the LLM to always include `skill`/`difficulty` when `required=true`.
## Implementation — Phase 1: Arc narration data + merge safety

### Context files to load

- `ccya/engine/turn.py` (lines 1277-1293, 1486-1500)
- `ccya/state/delta.py` (lines 25-64)
- `ccya/engine/narrate.py` (lines 50-72)
- `ccya/prompts/sections/_arc.j2` (line 24)
- `ccya/models.py` (lines 43-55 ArcThread)

### Detailed steps

#### Step 1.1 — Fix `_merge_arc_update()` to skip Pydantic-defaulted empty lists

**File:** `ccya/state/delta.py`, lines 56 and 60

**What:** Change the `is not None` checks at delta.py:56 (`if au.threads is not None:`) and line 60 (`if au.completed_threads is not None:`) to truthiness checks (`if au.threads:` and `if au.completed_threads:`). This prevents silently wiping engine-managed threads/completed_threads when Pydantic defaults CampaignArc lists to `[]`.

```python
# Before (line ~56):
    if au.threads is not None:
        arc["threads"] = [t.model_dump(exclude_none=True) for t in au.threads]
# After:
    if au.threads:
        arc["threads"] = [t.model_dump(exclude_none=True) for t in au.threads]

# Before (line ~60):  
    if au.completed_threads is not None:
        arc["completed_threads"] = [t.model_dump(exclude_none=True) for t in au.completed_threads]
# After:
    if au.completed_threads:
        arc["completed_threads"] = [t.model_dump(exclude_none=True) for t in au.completed_threads]
```

**Why:** `_merge_arc_update()` checks `is not None` at lines 56 and 60, which always passes when Pydantic defaults CampaignArc lists to `[]`. Even a minimal narrator arc_update like `{"visible_goal": "new goal"}` silently wipes engine state because the empty-thread default triggers wholesale replacement with an empty list. Changing to truthiness checks (`if au.threads:`) skips merging for empty lists while still allowing non-empty updates from either engine callers (who return full computed thread lists) or narrator arc_updates that explicitly set threads (which shouldn't happen but would now be silently ignored — correct behavior since thread management is engine-only).

**Validation:** Run the test command: `python3 -c "from ccya.models import CampaignArc; from ccya.state.delta import _merge_arc_update; state = {'threads': [{'id': 't1'}]}; au = CampaignArc.model_validate({'visible_goal': 'new goal'}); _merge_arc_update(state, au); print('threads preserved:', len(state.get(\\\"threads\\\", [])) > 0)"` — should output `True`.

#### Step 1.2 — Filter narrator arc_update to allowed keys only (thread-field contamination)

**File:** `ccya/engine/turn.py`, lines 1277-1293

**What:** After `_extract_narrator_arc_update()` returns `narrator_arc_dict` and before calling `CampaignArc.model_validate()`, filter out thread-related keys (`threads`, `completed_threads`) that the narrator should not manage. Allowed fields: `visible_goal`, `thematic_question`, `pc_drive`, `discovered_truths`, `hidden_truths`. Strip all others including unrecognized keys like `goal_context`.

Insert a filter block between line 1277 and 1278 (after `_extract_narrator_arc_update()` returns):

```python
_ALLOWED_NARRATOR_ARC_KEYS = {
    "visible_goal", "thematic_question", "pc_drive",
    "discovered_truths", "hidden_truths",
}
narrator_arc_dict = {k: v for k, v in narrator_arc_dict.items() if k in _ALLOWED_NARRATOR_ARC_KEYS}
```

**Why:** `CampaignArc.model_validate()` does NOT silently drop unrecognized keys like `threads` — it validates the full nested structure (`list[ArcThread]`). If the narrator emits malformed thread data with all required ArcThread fields populated (id + summary + scope), validation succeeds and `_merge_arc_update()` overwrites engine state. The filter prevents this by removing those keys before validation.

Note: Step 1.1 already fixes the Pydantic-default empty-list wiping issue, so even if a minimal narrator arc_update passes through without thread fields, it won't silently wipe engine threads anymore (Step 1.2 + Step 1.1 together provide defense in depth).

#### Step 1.3 — Remove dead `_upsert_threads()` from delta.py

**File:** `ccya/state/delta.py`, lines 28-41

**What:** Delete the `_upsert_threads` inner function defined at line 28. It is called by no code path (zero grep hits beyond its definition). The function signature suggests it was intended for per-thread-ID merging, but `_merge_arc_update()` uses wholesale replacement which is correct for all callers after Step 1.1's truthiness-check fix.

**Why:** Dead code violates AGENTS.md clean code rules.

**Validation:** After deletion, `grep -r _upsert_threads ccya/` returns zero results.

#### Step 1.4 — Add `last_seen_turn` to narrate thread context

**File:** `ccya/engine/narrate.py`, lines 59-67

**What:** Add `"last_seen_turn": t.get("last_seen_turn") if isinstance(t, dict) else getattr(t, "last_seen_turn", None)` to the thread dict builder (in `_narrate_messages()`), after the `"active"` key. The exact pattern follows the existing coercion for other fields in lines 61-67. Include `None` as default so the template sees null rather than an error.

**Why:** `_arc.j2:24` renders `t.last_seen_turn or '?'`. Without the field in the context dict, Jinja treats missing keys as empty string — producing `(last seen T)` with no value.

**Validation:** Without server: `python3 -c "from jinja2 import Environment; from pathlib import Path; tpl = Environment().from_string(Path('ccya/prompts/sections/_arc.j2').read_text()); print(tpl.render(current_arc={'visible_goal': 'test', 'threads': [{'summary': 'test', 'urgency': 'urgent', 'scope': 'arc', 'id': 't1', 'active': True, 'last_seen_turn': 3}]}))"` — the output should contain `(last seen T3)`.

### Tests to write or update

No tests (refactor phase — tests removed per AGENTS.md).

### REPOMAP updates required

None.

---

## Implementation — Phase 2: Ruling check resolution logging and validation

### Context files to load

- `ccya/engine/ruling.py` (lines 50-117)
- `ccya/engine/turn.py` (lines 765-794)
- `ccya/engine/config.py` (skip — no config change needed)

### Detailed steps

#### Step 2.1 — Verify existing `_call_ruling()` parse-failure log is adequate

**File:** `ccya/engine/ruling.py`, lines 113-117

**What:** Read the existing WARNING at line 113: `"ruling call failed after all attempts — defaulting to no-roll"`. Confirm it includes enough context (trace_id, attempt count) for operators to identify parse failures in logs. No change needed if adequate; proceed to Step 2.2.

**Why:** The plan originally assumed a new log was needed here, but the existing WARNING already fires when `_call_ruling()` exhausts retries and falls back to no-intent. Verify it's sufficient before adding redundant logging.

#### Step 2.2 — Validate `check.required=true` implies `skill` is present

**File:** `ccya/engine/ruling.py`, in `_call_ruling()`, after line 92 (after `IntentEnvelope(**j)` succeeds).

**What:** After successfully parsing the IntentEnvelope, add a validation step:

```python
intent = IntentEnvelope(**j)
if intent.check.required and not intent.check.skill:
    raise ValueError(f"check.required=true but check.skill is missing/empty (got {j.get('check', {}).get('skill', None)})")
return intent, usage, raw, ""
```

Place this between lines 92 and 93. The existing `except Exception` at line 97 catches the `ValueError`, logs it, and retries (or falls back to no-intent after all retries). This ensures the LLM receives feedback about the missing skill field and can correct it.

**Why:** When the LLM emits `check.required=true` without a `skill` field, the Pydantic default of `None` bypasses `coerce_skill` and passes through, then silently fails the gate at `turn.py:768`. Raising during parse gives the LLM a chance to retry with the correct output.

**Validation:** No shell command — trace through the retry logic. On a ruling response with `{"intent": "test", "intent_verb": "act", "target": "", "check": {"required": true}}`, the function should hit the new `ValueError`, log the retry message, and append the feedback message to messages. After `max_ruling_retries` failures, it returns the default no-intent.

#### Step 2.3 — Log when check requested but roll skipped

**File:** `ccya/engine/turn.py`, before line 791

**What:** Before the `else` branch (line 791) that creates `RulesOutcome(rolled=False)`, add a log statement at WARNING level that fires only when `intent.check.required` is True but the condition `intent.check.skill` is falsy:

```python
if intent.check.required and not intent.check.skill:
    _log.warning(
        "rules: check required on T%d but skill=%s — no roll will occur",
        state.get("meta", {}).get("turn", 0) + 1,
        intent.check.skill,
        extra={"trace_id": trace_id, "turn": state.get("meta", {}).get("turn", 0) + 1},
    )
```

Also add a DEBUG log when `not intent.check.required`, so operators can distinguish "no check needed" from "check was requested but silently skipped". For the non-required case, use `_log.debug` level to avoid noise.

**Why:** Without this, the events.jsonl shows `rolled: False` with no way to tell if the ruling engine decided "no check" or if a requested check was silently dropped. This is the single most confusing gap in the pipeline's observability.

**Validation:** After the change, run `grep` to confirm the two new log statements exist. No runtime test available without a server.

### Tests to write or update

No tests (refactor phase — tests removed per AGENTS.md).

### REPOMAP updates required

None.
