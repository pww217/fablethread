# Plan: Active Domains from Narration

## Problem

`active_domains` is determined by the rules LLM (Call 0) from raw player input alone.
The rules LLM has minimal context — just the player's action and one recent turn.
It frequently guesses wrong about which state domains will change, causing:

- Extraction prompts to skip domains that actually changed (missed updates)
- Extraction prompts to run domains that didn't change (wasted tokens, noise)
- `build_state_slice()` in `narrate.py` to hide/show state sections incorrectly
- The extraction pipeline to produce stale or incomplete deltas

The narration LLM (Call 1) has far richer context: full state, chronicle, inventory,
quests, conditions, rules outcome, scene pressure, momentum, combat fatigue, location
age, recently-left NPCs, known characters, world factions. It's already reasoning
about what changed to write the narrative. Asking it to also output which domains
changed is just asking it to be explicit about what it's already analyzing.

## Solution

Add a structured JSON header to the narration prompt. The narration LLM determines
active domains as part of its reasoning, outputs them as a JSON block at the top of
its response, then writes the narrative prose. The server parses the JSON after the
stream completes, strips the header from the narrative, and passes the domains to
the extraction pipeline.

The user never sees the header — it's stripped before the narrative is saved to the
chronicle or sent in `turn_complete`.

---

## Design

### Output format

The narration LLM outputs a JSON block at the very top of its response:

```json
{"active_domains": ["scene", "inventory", "recent_events"]}
```

Followed by a newline, then the narrative prose:

```json
{"active_domains": ["scene", "inventory", "recent_events"]}

The guard falls...
```

JSON is used because:
- Python can parse it reliably with `json.loads()`
- No ambiguity about delimiters or format
- Easy to validate against the known domain set
- The LLM is good at JSON output when prompted

### Valid domains

The domain set is fixed and known:

```python
ALL_DOMAINS = {
    "scene",
    "inventory",
    "quest_updates",
    "location_change",
    "recent_events",
    "pc_condition",
    "compendium_npc",
}
```

The parser validates each domain against this set, silently dropping unknown values.
If the LLM returns an empty list or invalid JSON, fall back to the default set.

### Parsing location

In `turn.py`, after the narration stream completes:

```python
# turn.py line ~338
narrative = strip_thinking("".join(narrative_chunks))
narrative, active_domains = _parse_narration_header(narrative)
```

The `_parse_narration_header` function:
1. Strips any `<thinking>` content (already done by `strip_thinking`)
2. Looks for a JSON block at the start of the response
3. Parses and validates the `active_domains` array
4. Returns `(cleaned_narrative, active_domains_list)`

### Passing to extraction

Two options:

**Option A: Modify `intent.scope.active_domains`** (simpler, less invasive)

```python
# After parsing, before extraction
if active_domains:
    intent.scope.active_domains = active_domains
```

This works because `_run_extraction_pipeline` reads `intent.scope.active_domains`
via `_active_domains(intent)` at `extraction.py:34,84,126,210`.

**Option B: Add `active_domains` parameter to `_run_extraction_pipeline`** (cleaner,
more explicit)

```python
async def _run_extraction_pipeline(
    ...
    active_domains: list[str] | None = None,
) -> tuple[...]:
    if active_domains is not None:
        scope = Scope(active_domains=active_domains)
    else:
        scope = intent.scope if intent else Scope()
```

This is cleaner because it doesn't mutate `intent` (which was produced by the rules
LLM and may be logged/stored). Option B is preferred.

---

## Changes

### 1. `ccya/prompts/narrate_system.j2`

Add a new section to the system prompt:

```
## Active domains header
Before writing your narrative, determine which state domains changed this turn.
Output them as a JSON block at the very top of your response, then write your prose.

Format: {"active_domains": ["domain1", "domain2"]}

Valid domains: scene, inventory, quest_updates, location_change, recent_events,
               pc_condition, compendium_npc

Only list domains that actually changed or need attention this turn.
If nothing changed, output: {"active_domains": ["scene"]}
```

Placement: After the "Markdown (light)" section, before the conditional world/genre sections.

### 2. `ccya/engine/turn.py`

**Add `_parse_narration_header()` function:**

```python
import json
import re

_VALID_DOMAINS = frozenset({
    "scene", "inventory", "quest_updates",
    "location_change", "recent_events",
    "pc_condition", "compendium_npc",
})

_DEFAULT_DOMAINS = [
    "scene", "inventory", "quest_updates",
    "location_change", "recent_events", "pc_condition",
]


def _parse_narration_header(text: str) -> tuple[str, list[str]]:
    """Parse active_domains JSON header from narration output.

    Returns (cleaned_text, active_domains).
    If no valid header found, returns (text, default_domains).
    """
    # Look for JSON block at the start (after any whitespace)
    match = re.match(r'\s*(\{.*?\})\s*\n', text, re.DOTALL)
    if not match:
        return text, list(_DEFAULT_DOMAINS)

    json_str = match.group(1)
    try:
        parsed = json.loads(json_str)
        if not isinstance(parsed, dict) or "active_domains" not in parsed:
            return text, list(_DEFAULT_DOMAINS)
        domains = parsed["active_domains"]
        if not isinstance(domains, list):
            return text, list(_DEFAULT_DOMAINS)
        valid = [d for d in domains if isinstance(d, str) and d in _VALID_DOMAINS]
        if not valid:
            return text, list(_DEFAULT_DOMAINS)
        # Strip the header from the text
        cleaned = text[match.end():]
        return cleaned, valid
    except (json.JSONDecodeError, ValueError):
        return text, list(_DEFAULT_DOMAINS)
```

**In `run_turn()`:** After line 338 (`narrative = strip_thinking(...)`):

```python
narrative = strip_thinking("".join(narrative_chunks))
narrative, active_domains = _parse_narration_header(narrative)
```

Then pass `active_domains` to `_run_extraction_pipeline()` at line 371:

```python
delta, actions, outcome_summary, failed, extraction_event, progress_result = (
    await _run_extraction_pipeline(
        env, state, narrative,
        rules_outcome=outcome,
        intent=intent,
        active_domains=active_domains,  # NEW
        config=config,
        ...
    )
)
```

**In `run_turn_retry()`:** Same change after line 818 (`narrative = strip_thinking(...)`):

```python
narrative = strip_thinking("".join(narrative_chunks))
narrative, active_domains = _parse_narration_header(narrative)
```

And pass to `_run_extraction_pipeline()` at line 852.

### 3. `ccya/engine/extraction.py`

**Update `_run_extraction_pipeline()` signature:**

```python
async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    pack_examples: list["ExtractExample"] | None = None,
    deescalate: bool = False,
    quest_ages: list[dict[str, Any]] | None = None,
    active_domains: list[str] | None = None,  # NEW
) -> tuple["StateDelta", list[str], str, list[str], dict[str, Any], "ProgressExtractResult"]:
```

**Update the scope resolution at line 346:**

```python
if active_domains is not None:
    scope = Scope(active_domains=active_domains)
else:
    scope = intent.scope if intent else Scope()
```

This is the only place `_active_domains(intent)` is called for scope resolution.
The three extraction message builders (`_extract_scene_messages`, `_extract_state_messages`,
`_extract_progress_messages`) still call `_active_domains(intent)` internally, but they
receive `intent` which may have the old domains. We need to also pass `active_domains`
to those functions, or better: pass the resolved `scope` to them.

Actually, looking more carefully: `_active_domains(intent)` is called inside each
message builder. If we pass `active_domains` to `_run_extraction_pipeline`, we need
to also pass it down to the three builders. Or we can create a modified `intent`
with the new domains and pass that.

**Simpler approach:** Create a modified intent with the parsed domains:

```python
# In _run_extraction_pipeline, at line 346:
if active_domains is not None:
    # Override intent's scope with parsed domains
    intent = IntentEnvelope(
        intent=intent.intent if intent else "",
        intent_verb=intent.intent_verb if intent else "act",
        check=intent.check if intent else RulesCheck(required=False),
        scope=Scope(active_domains=active_domains),
    )
# Now _active_domains(intent) will return the parsed domains
```

This is the cleanest approach — no changes needed to the three message builders.

### 4. `ccya/prompts/narrate_user.j2` (optional)

No changes needed. The user prompt already provides all the context the narration LLM
needs to determine which domains changed. The instruction goes in the system prompt.

---

## Edge Cases

### LLM forgets the header

Fallback to defaults. The regex won't match, `json.loads` will fail, or the array
will be empty — all paths return the default domain set.

### LLM outputs header in wrong format

Same — validation catches it, returns defaults.

### LLM outputs header mid-response

The regex only matches at the start of the text (`\A` or `^`), so mid-response headers
are ignored.

### Thinking mode enabled

`strip_thinking()` removes `<thinking>` content before `_parse_narration_header` runs,
so the header will be at the start of the cleaned text. The LLM should output the
header after the thinking block, not inside it. The prompt should clarify this.

### Retry path

`run_turn_retry()` also calls narration and needs the same parsing. Both paths must
be updated.

### Empty narration

If the stream produces no content, `strip_thinking("")` returns `""`, the regex
won't match, and defaults are used. Safe.

### Token budget impact

The JSON header is ~30-50 tokens. The prompt instruction is ~80 tokens. Total overhead
is minimal compared to the full narration prompt (~2000-4000 tokens).

---

## Testing

### Unit tests for `_parse_narration_header`

- Valid JSON header → returns (cleaned_text, domains)
- Valid JSON with unknown domains → filters to valid set
- Invalid JSON → returns (original_text, defaults)
- No header → returns (original_text, defaults)
- Empty array → returns (original_text, defaults)
- Header mid-response → returns (original_text, defaults)
- Header with extra whitespace → still parses correctly

### Integration test

Add a test that verifies the extraction pipeline uses parsed domains when the
narration includes a valid header. This would require a FakeLLM that returns
a narration with a header.

---

## Rollback

If the narration LLM consistently fails to output the header, or if the parsed
domains are worse than the rules LLM's guesses, the feature can be disabled by
removing the prompt instruction and the parsing call. The fallback to defaults
ensures nothing breaks.

---

## Implementation Order

1. Add `_parse_narration_header()` to `turn.py` with unit tests
2. Add prompt instruction to `narrate_system.j2`
3. Wire parsing into `run_turn()` and `run_turn_retry()`
4. Wire `active_domains` parameter into `_run_extraction_pipeline()`
5. Integration test with FakeLLM
6. Manual testing with real LLM
