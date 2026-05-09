# Fix: Thinking Suppression + Actions Date Display

## Table of Contents

1. [Status](#status)
2. [Part of](#part-of)
3. [Dependencies](#dependencies)
4. [Objective](#objective)
5. [Non-goals](#non-goals)
6. [Affected files](#affected-files)
7. [Firm decisions](#firm-decisions)
8. [Implementation — Phase 1: Suppress Thinking on All LLM Calls](#implementation--phase-1-suppress-thinking-on-all-llm-calls)
9. [Implementation — Phase 2: Fix Actions Date Display](#implementation--phase-2-fix-actions-date-display)
10. [Ambiguities requiring resolution before execution](#ambiguities-requiring-resolution-before-execution)
11. [TODO.md update](#todomd-update)

---

## Status
`open`

## Part of
`standalone`

## Dependencies
- none

## Objective

Two bugs were surfaced by evaluations. First, every LLM call in the pipeline
(rules, narrate, and all three extraction streams) is potentially thinking at
inference time because `apply_thinking` is only injected when the
`enable_*_thinking` flags are `True`; when they are `False`, no `/no_think`
tag is appended, and Qwen3 models think by default unless explicitly
suppressed. The latency cost is significant and the thought tokens are hidden
from the user by `strip_thinking`, meaning the work is wasted. The fix is to
always call `apply_thinking`, passing the flag value through (True → `/think`,
False → `/no_think`), so thinking is opt-in and suppressed by default. Second,
the `actions` list surface in the UI renders the raw ISO-8601 `ts` timestamp
from `events.jsonl` as a visible string rather than a human-readable label.
The `ts` field is produced by `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`
in `turn.py` and is meant for machine use only; the UI must format it (or the
field written to the event must be both machine and human friendly).

## Non-goals

- This plan does NOT change model routing, temperature, or any other inference
  parameter.
- This plan does NOT refactor the extraction pipeline structure.
- This plan does NOT touch compactor.py, state.py, or chronicle logic.
- This plan does NOT add a new config field — `enable_narrate_thinking` and
  `enable_extract_thinking` already exist; we are changing how their `False`
  value is handled.
- This plan does NOT change the `ts` field's stored value — the ISO string
  stays in `events.jsonl` for machine consumers. Only the display path changes.
- This plan does NOT investigate or fix the rules temperature, retry logic, or
  any eval scoring beyond the two surfaced issues.

---

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/llm_client.py` | modify | `apply_thinking` always appends a tag; `/no_think` when `enable=False` |
| `ccya/engine/narrate.py` | modify | Always call `apply_thinking(msgs, enable_narrate_thinking)` unconditionally |
| `ccya/engine/rules.py` | modify | Call `apply_thinking(msgs, False)` before passing to `llm_chat` (rules never think) |
| `ccya/engine/extraction.py` | modify | All three `_extract_*_messages` builders: remove the `if enable_thinking:` guard, always call `apply_thinking` |
| `ccya/engine/compactor.py` | inspect + modify if needed | Check whether compactor calls `apply_thinking`; suppress if not already done |
| `ccya/api/routes.py` (or equivalent UI/SSE handler) | inspect + modify | Format `ts` into a human-readable string before sending to UI, OR instruct frontend to format it |
| `docs/REPOMAP/engine.md` | update | Note that thinking is now always explicitly set per call |
| `docs/plans/TODO.md` | update | Add this plan |

> **Note on routes.py path:** The exact file serving the actions SSE/JSON to
> the UI was not read. It is likely `ccya/api/routes.py` or a template in
> `ccya/templates/`. This must be verified before Phase 2 execution — see
> Ambiguities section.

---

## Firm decisions

1. **`apply_thinking` must always be called, not conditionally.** Qwen3 thinks
   by default. The `if enable:` guard in `narrate.py` and `extraction.py` is
   the root cause. Removing the guard and always passing the flag value (True
   or False) is the minimal correct fix.

2. **Rules LLM calls never think.** `_call_rules` does not currently call
   `apply_thinking` at all. It must call `apply_thinking(messages, False)`
   before every call attempt, including retry attempts. There is no config flag
   for rules thinking — it is unconditionally off.

3. **`apply_thinking` in `llm_client.py` already handles both branches**
   (`/think` and `/no_think`) based on the `enable` argument. No new function
   is needed; only the call sites need to remove their guards.

4. **The ISO timestamp `ts` stays as-is in `events.jsonl`.** Machine consumers
   (judge, metrics) depend on it. Only the display path changes. The human
   label is derived at render time, not at write time.

5. **Retry loops in `_call_rules` append feedback messages.** `apply_thinking`
   must be applied to the initial message list before the loop, not inside it,
   because the tag is appended to the last message and retry feedback is
   appended after that. Applying it inside the loop would double-tag on
   retries.

---

## Implementation — Phase 1: Suppress Thinking on All LLM Calls

### Context files to load
ccya/llm_client.py
ccya/engine/config.py
ccya/engine/rules.py
ccya/engine/narrate.py
ccya/engine/extraction.py
ccya/engine/compactor.py ← read to check whether it calls apply_thinking


### Overview

`apply_thinking` in `llm_client.py` already correctly appends `/think` or
`/no_think` based on a boolean. The bug is that four call sites only call it
when the flag is `True`, leaving Qwen3 free to think when it is `False`. This
phase removes every `if enable_thinking:` guard and calls `apply_thinking`
unconditionally. Rules is a special case: it has no flag at all and must have
`apply_thinking(msgs, False)` added explicitly.

### Detailed steps

#### Step 1.1 — Verify `apply_thinking` handles `enable=False`

**File:** `ccya/llm_client.py`

**What:** Confirm (no change required if already correct) that `apply_thinking`
appends `/no_think` when `enable=False`. The current implementation reads:

```python
def apply_thinking(
    messages: list[dict[str, str]], enable: bool
) -> list[dict[str, str]]:
    tag = "/think" if enable else "/no_think"
    msgs = [dict(m) for m in messages]
    msgs[-1]["content"] = f"{msgs[-1]['content']} {tag}"
    return msgs
```

This is already correct. No change needed here. Confirm during execution that
the function signature and body match exactly before proceeding.

**Validation:** Read the file; confirm `tag = "/think" if enable else "/no_think"`.
If the function body differs from the above, stop and surface the discrepancy
before continuing.

---

#### Step 1.2 — Remove the guard in `narrate.py`

**File:** `ccya/engine/narrate.py`

**What:** In `_narrate_messages`, the current code is:

```python
    if enable_narrate_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs
```

Replace with:

```python
    msgs = apply_thinking(msgs, enable_narrate_thinking)
    return msgs
```

**Why:** When `enable_narrate_thinking=False` (the default), the model
currently receives no tag and thinks freely. With this change it receives
`/no_think` unconditionally, suppressing inference-time thinking.

**Code Snippet**

```python
# In _narrate_messages, replace the conditional block at the end of the function:
    msgs = apply_thinking(msgs, enable_narrate_thinking)
    return msgs
```

**Validation:** After edit, confirm the file no longer contains
`if enable_narrate_thinking:`. Run `make check`.

---

#### Step 1.3 — Remove the guard in `extraction.py` (three builders)

**File:** `ccya/engine/extraction.py`

**What:** Three message-builder functions each have the pattern:

```python
    if enable_thinking:
        msgs = apply_thinking(msgs, True)
    return msgs
```

In `_extract_scene_messages`, `_extract_state_messages`, and
`_extract_progress_messages`, replace each guard with an unconditional call.

**Why:** Same root cause as narrate. `enable_extract_thinking` defaults to
`False` in `EngineConfig`, so all three streams currently run without any
thinking tag and Qwen3 is free to think on all of them.

**Code Snippet**

```python
# Replace in _extract_scene_messages (end of function):
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs

# Replace in _extract_state_messages (end of function):
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs

# Replace in _extract_progress_messages (end of function):
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs
```

**Validation:** After edit, confirm `extraction.py` no longer contains
`if enable_thinking:`. Run `make check`.

---

#### Step 1.4 — Add thinking suppression to `_call_rules`

**File:** `ccya/engine/rules.py`

**What:** `_call_rules` calls `llm_chat` without ever calling `apply_thinking`.
Add an import (already available at module level via `from ccya.llm_client
import ... strip_thinking`) and apply `/no_think` to the messages before the
retry loop begins.

**Why:** Rules LLM calls have no thinking flag in config. They must always run
with `/no_think`. The tag must be applied once, before the `for attempt in
range(...)` loop, because retry feedback is appended inside the loop and
`apply_thinking` only touches the final message.

**Code Snippet**

```python
# Add apply_thinking to the import at the top of rules.py:
from ccya.llm_client import apply_thinking, chat as llm_chat, strip_thinking

# In _call_rules, immediately before the retry loop:
async def _call_rules(
    messages: list[dict[str, Any]],
    config: EngineConfig,
    trace_id: str,
) -> tuple[IntentEnvelope, dict[str, int], str]:
    _no_intent = IntentEnvelope(
        intent="",
        intent_verb="act",
        check=RulesCheck(required=False),
    )
    _no_usage: dict[str, int] = {"prompt_tokens": 0, "total_tokens": 0}
    parse_error = ""
    # Rules never think — suppress unconditionally before retry loop.
    messages = apply_thinking(messages, False)
    for attempt in range(1 + config.max_rules_retries):
        # ... rest of loop unchanged
```

**Validation:** Confirm `apply_thinking` is called once, before the loop.
Confirm the import line is updated. Run `make check`.

---

#### Step 1.5 — Inspect `compactor.py` for LLM calls

**File:** `ccya/engine/compactor.py`

**What:** Read the file. Identify every call to `llm_chat` or `llm_chat_stream`.
For each, check whether `apply_thinking` is called before it.

**Why:** The compactor runs as a background phase. If it makes LLM calls
without `/no_think`, it is also silently thinking.

**Code Snippet**

This is an inspection step. If LLM calls are found without `apply_thinking`:

```python
# Before each llm_chat / llm_chat_stream call in compactor.py,
# add (adjust variable name to match actual local variable):
    compact_msgs = apply_thinking(compact_msgs, False)
```

If no LLM calls are found, no change is needed. Document the finding.

**Validation:** Confirm every `llm_chat`/`llm_chat_stream` call in
`compactor.py` is preceded by `apply_thinking`. Run `make check`.

---

### Tests to write or update

**File:** `tests/test_llm_client.py` (or create if absent)

- `test_apply_thinking_no_think`: call `apply_thinking(msgs, False)`, assert
  last message content ends with ` /no_think`.
- `test_apply_thinking_think`: call `apply_thinking(msgs, True)`, assert last
  message content ends with ` /think`.
- `test_apply_thinking_does_not_mutate_input`: confirm original list is
  unchanged (function makes copies).

**File:** `tests/test_rules.py` (or create if absent)

- `test_call_rules_sends_no_think`: use `FakeLLM` (see `docs/REPOMAP/testing.md`
  for the pattern). Capture the messages sent to the fake. Assert the last
  user message content ends with ` /no_think`.

**File:** `tests/test_extraction.py` (or create if absent)

- `test_extract_scene_messages_no_think_by_default`: call
  `_extract_scene_messages(..., enable_thinking=False)`, assert last message
  ends with ` /no_think`.
- `test_extract_scene_messages_think_when_enabled`: call with
  `enable_thinking=True`, assert last message ends with ` /think`.
- Same pair for `_extract_state_messages` and `_extract_progress_messages`.

**File:** `tests/test_narrate.py` (or create if absent)

- `test_narrate_messages_no_think_by_default`: call
  `_narrate_messages(..., enable_narrate_thinking=False)`, assert last message
  ends with ` /no_think`.
- `test_narrate_messages_think_when_enabled`: call with `True`, assert `/think`.

> **Note:** The exact FakeLLM pattern and test fixture structure is documented
> in `docs/REPOMAP/testing.md`. The executor must read that file before writing
> tests.

### REPOMAP updates required

**File:** `docs/REPOMAP/engine.md`

Add a note under the `llm_client` or `engine` section:

> `apply_thinking(messages, enable)` is now called unconditionally before
> every LLM call. `enable=False` → `/no_think` appended; `enable=True` →
> `/think` appended. Rules calls always use `False`. Narrate and extract
> calls use their respective `EngineConfig` flags.

### Risks

1. **Qwen3 model does not support `/no_think`.** If the model in use is not a
   Qwen3-instruct variant, the tag may appear literally in the output or be
   ignored. Mitigation: `strip_thinking` already handles `<think>` blocks;
   the tag itself is appended to user content, not a system directive. In the
   worst case the model ignores it — which is the current behavior — so there
   is no regression risk.
2. **`apply_thinking` mutates the last message only.** If the message list is
   empty, `msgs[-1]` will raise `IndexError`. Mitigation: all builders always
   produce at least `[system, user]` messages; this is already assumed
   elsewhere. Document the precondition.
3. **Retry messages in `_call_rules` are appended after the tag.** The feedback
   line `"Re-emit the IntentEnvelope JSON only."` becomes the new last message
   after retry. This is fine — the original tag is baked into the first user
   message, not a system message, so it carries through. Qwen3 tags are
   per-generation, not per-message; the first user message sets the mode for
   the entire completion.

---

## Implementation — Phase 2: Fix Actions Date Display

### Context files to load
ccya/engine/turn.py
ccya/api/routes.py ← verify path; may be ccya/routes.py or ccya/server.py
ccya/templates/ ← list directory; find templates rendering actions


### Overview

The `actions` list in `events.jsonl` contains plain strings (player-facing
suggestions produced by the progress extractor). These have no date. The
`ts` field is a separate top-level key on the event object. The evaluation
found a date string visible in the UI where it should not be — likely the `ts`
field is being rendered as a label in the actions component, or the raw ISO
string is passed through as a display value somewhere. This phase traces the
data path from `events.jsonl` → route → template/SSE → UI component and fixes
the formatting at the presentation layer.

> **Pre-execution requirement:** The executor must read `ccya/api/routes.py`
> (or equivalent) and the relevant template before making any changes. The
> exact rendering path is not confirmed from the files already read. See
> Ambiguities section.

### Detailed steps

#### Step 2.1 — Trace the actions display path

**File:** `ccya/api/routes.py` (verify actual path)

**What:** Find the route or SSE handler that sends `actions` to the frontend.
Confirm whether `ts` is being bundled into the actions payload, or whether a
timestamp is being used as a label elsewhere in the same component.

**Why:** Without tracing the path, the fix might be applied to the wrong layer.

**Validation:** Identify the exact line where `actions` and/or `ts` are
serialized and sent to the UI. Document the finding before proceeding to 2.2.

---

#### Step 2.2 — Fix the display

This step has two sub-cases depending on findings in 2.1.

**Sub-case A — `ts` is being injected into the actions payload:**

If the route or template is passing `event["ts"]` into the same data structure
as `actions`, remove it. `actions` is a `list[str]` of player suggestions.
The `ts` has no place there.

**Code Snippet (route example — adapt to actual code):**

```python
# BEFORE (hypothetical — adapt to actual):
payload = {
    "actions": event["actions"],
    "ts": event["ts"],
}

# AFTER:
payload = {
    "actions": event["actions"],
    # ts is not a display field — omit from UI payload
}
```

**Sub-case B — `ts` is rendered as a label in the actions component:**

If a template or JavaScript component renders `event.ts` as a human-readable
timestamp label, format it properly using Python's `datetime.fromisoformat`
at the route layer, or format it in the frontend template.

**Code Snippet (route format approach — adapt to actual code):**

```python
from datetime import datetime, timezone

def _fmt_ts(iso: str) -> str:
    """Format ISO UTC timestamp as 'May 9, 2026 at 10:33 AM' for display."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%-d %b %Y at %-I:%M %p UTC")
    except (ValueError, AttributeError):
        return iso

# In the route handler, before serializing to the UI:
display_ts = _fmt_ts(event["ts"])
```

**Why:** The ISO string `2026-05-09T15:33:00Z` is machine-readable, not
human-readable. The UI should display something like `9 May 2026 at 3:33 PM
UTC` if a timestamp is shown at all.

**Sub-case C — The issue is in a Jinja2 template:**

If `ts` appears in a `.j2` or `.html` template directly (not in Python), add
a Jinja2 filter:

```jinja2
{# BEFORE: #}
{{ event.ts }}

{# AFTER: #}
{{ event.ts | replace("T", " ") | replace("Z", " UTC") }}
```

Or register a proper `datetime_fmt` filter in the Jinja environment
(`_build_jinja_env` in `config.py`) and use it in the template.

**Validation:** Run the app locally and trigger a turn. Confirm the actions
display does not show a raw ISO timestamp. Confirm the human-readable label
(if shown) is correctly formatted.

---

### Tests to write or update

**File:** `tests/test_routes.py` (or equivalent API test)

- `test_actions_payload_contains_no_raw_ts`: fire a mock turn through the
  route; assert the `actions` array in the SSE/JSON response contains only
  strings that do not match `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z`.

**File:** `tests/test_turn.py` (or equivalent)

- `test_event_ts_is_iso`: assert `event["ts"]` matches `%Y-%m-%dT%H:%M:%SZ`
  format — confirming the stored value is machine-readable and unchanged.

### REPOMAP updates required

**File:** `docs/REPOMAP/engine.md` or `docs/REPOMAP/routes.md` (whichever covers the API layer)

Add a note:

> `event["ts"]` (ISO-8601 UTC string) is for machine use only. The UI
> presentation layer must format it before display. Do not pass raw `ts` into
> the actions component.

### Risks

1. **The rendering path is in a JavaScript frontend, not Python templates.**
   If the UI is a separate SPA, the fix must be in the JS layer. Mitigation:
   the executor must inspect the `ccya/templates/` directory and any
   `static/` or `frontend/` directory to determine the rendering layer before
   making changes.
2. **Strftime format strings are platform-dependent.** `%-d` and `%-I` (no
   leading zero) work on Linux/macOS but not Windows. Mitigation: this runs
   on macOS (local dev); use `%-d` and `%-I` but note the caveat.
3. **Changing the display format may break snapshot tests.** If any test
   asserts on rendered HTML or JSON output containing the raw ISO string,
   those tests will need updating. Mitigation: run `make test` and update
   any failing snapshot assertions.

---

## Ambiguities requiring resolution before execution

1. **Route/template file path for the actions display.** The files
   `ccya/api/routes.py`, `ccya/routes.py`, `ccya/server.py`, and
   `ccya/templates/` were not read. The executor must determine which file
   renders or serializes `actions` and `ts` to the UI before beginning Phase 2.
   Options: A) It is a Python route in `ccya/api/routes.py`. B) It is a
   Jinja2 template. C) It is a JavaScript frontend file. The executor must
   NOT proceed with Phase 2 step 2.2 until this is confirmed.

2. **Whether `ts` is being shown as an actions label or as a separate UI
   element.** The evaluation surfaced that a date is visible in the actions
   UI, but it is not clear from the event structure whether: A) `ts` is
   directly rendered in the actions list component, or B) a timestamp is
   rendered as a separate label above/below the actions list and the issue
   is that it uses the raw ISO format. The executor must visually confirm
   which case applies before choosing sub-case A, B, or C in Step 2.2.

3. **Compactor LLM call pattern.** `compactor.py` was not read. The executor
   must read it at the start of Phase 1 and confirm whether it calls
   `apply_thinking`. Options: A) It calls `llm_chat` without `apply_thinking`
   — add suppression. B) It already calls `apply_thinking`. C) It does not
   call the LLM at all. Report which case applies.

4. **FakeLLM pattern location.** Tests reference `docs/REPOMAP/testing.md`
   for the FakeLLM fixture. If that file does not exist or does not describe
   a FakeLLM, the executor must surface this and ask before writing tests that
   depend on it.

---

## TODO.md update

Add under the appropriate priority section (suggest P1 — latency is a player-
facing regression):

```markdown
- [ ] Fix thinking suppression + actions date display — [docs/plans/fix-thinking-suppression-actions-date.md]
```