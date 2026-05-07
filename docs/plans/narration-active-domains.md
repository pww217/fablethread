# Plan: Active Domains from Narration

## Problem

`active_domains` is determined by the rules LLM (Call 0) from raw player input alone.
The rules LLM has minimal context — just the player's action and one recent turn.
It frequently guesses wrong about which state domains will change, causing:

- Extraction prompts to skip domains that actually changed (missed updates)
- Extraction prompts to run domains that didn't change (wasted tokens, noise)
- The extraction pipeline to produce stale or incomplete deltas

The narration LLM (Call 1) has far richer context: full state, chronicle, inventory,
quests, conditions, rules outcome, scene pressure, momentum, combat fatigue, location
age, recently-left NPCs, known characters, world factions. It's already reasoning
about what changed to write the narrative. Asking it to also output which domains
changed is just asking it to be explicit about what it's already analyzing.

## Solution

Add a structured JSON header to the narration prompt. The narration LLM determines
active domains as part of its reasoning, outputs them as a JSON block at the top of
its response (after any thinking tags), then writes the narrative prose. The server
parses the JSON after the stream completes, strips the header from the narrative, and
passes the domains to the extraction pipeline.

The user never sees the header — it's stripped before the narrative is saved to the
chronicle or sent in `turn_complete`.

---

## Design

### Output format

The narration LLM outputs a JSON block at the very top of its response (after any
`<thinking>` tags if thinking mode is enabled):

```
{"active_domains": ["scene", "inventory", "recent_events"]}

The guard falls...
```

JSON is used because:
- Python can parse it reliably with `json.loads()`
- No ambiguity about delimiters or format
- Easy to validate against the known domain set
- The LLM is good at JSON output when prompted

### Valid domains

```python
ALL_DOMAINS = frozenset({
    "scene",
    "inventory",
    "quest_updates",
    "location_change",
    "recent_events",
    "pc_condition",
    "compendium_npc",
})
```

The parser validates each domain against this set, silently dropping unknown values.
If the LLM returns an empty list, invalid JSON, or no header at all, fall back to
the default set.

### Default fallback

```python
_DEFAULT_DOMAINS = [
    "scene",
    "inventory",
    "quest_updates",
    "location_change",
    "recent_events",
    "pc_condition",
    "compendium_npc",
]
```

All 7 domains included — `compendium_npc` is in the default because NPC introductions
and compendium updates happen frequently enough that skipping extraction by default
risks losing NPC identity data.

### Parsing location

In `turn.py`, after `strip_thinking()` is called on the assembled narrative:

```python
narrative = strip_thinking("".join(narrative_chunks))
narrative, active_domains = _parse_narration_header(narrative)
```

`_parse_narration_header` returns `(cleaned_narrative, active_domains_list)`.

### Passing to extraction

The extraction pipeline decides **which streams run** based on `scope.skip_domains`
(lines 398-399, 440-441 in `extraction.py`), not `active_domains`. The `active_domains`
parameter only influences what gets passed to the prompt templates.

When narration-derived domains are available, we must **override both** `active_domains`
and `skip_domains` in the intent's scope. The `skip_domains` is computed as the
complement: `ALL_DOMAINS - set(active_domains)`. This ensures the extraction streams
actually run for the domains the narration identified.

The cleanest approach: use `IntentEnvelope.model_copy()` to create a modified intent
with the new scope, preserving all other fields. This avoids manual field copying and
is forward-compatible with model changes.

---

## Implementation

### 1. `ccya/engine/turn.py` — add `_parse_narration_header`

Add at module level (after imports, before `run_turn`):

```python
import json
import re

_ALL_DOMAINS = frozenset({
    "scene",
    "inventory",
    "quest_updates",
    "location_change",
    "recent_events",
    "pc_condition",
    "compendium_npc",
})

_DEFAULT_DOMAINS = [
    "scene",
    "inventory",
    "quest_updates",
    "location_change",
    "recent_events",
    "pc_condition",
    "compendium_npc",
]


def _parse_narration_header(text: str) -> tuple[str, list[str]]:
    """Parse active_domains JSON header from narration output.

    Looks for a JSON object at the start of the text (after optional whitespace).
    The header must contain an "active_domains" key with a list of domain names.
    Valid domains are filtered against _ALL_DOMAINS; unknown values are dropped.

    Returns (cleaned_text, active_domains).
    If no valid header found, returns (text, default_domains).
    """
    # Match JSON object at start, optionally followed by whitespace/newline
    # Non-greedy .*? stops at the first }, which is correct for the flat structure
    match = re.match(r'\s*(\{.*?\})\s*\n?', text, re.DOTALL)
    if not match:
        return text, list(_DEFAULT_DOMAINS)

    json_str = match.group(1)
    try:
        parsed = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return text, list(_DEFAULT_DOMAINS)

    if not isinstance(parsed, dict) or "active_domains" not in parsed:
        return text, list(_DEFAULT_DOMAINS)

    domains = parsed["active_domains"]
    if not isinstance(domains, list):
        return text, list(_DEFAULT_DOMAINS)

    valid = [d for d in domains if isinstance(d, str) and d in _ALL_DOMAINS]
    if not valid:
        return text, list(_DEFAULT_DOMAINS)

    cleaned = text[match.end():].lstrip("\n")
    return cleaned, valid
```

Key design decisions:
- `\n?` makes the trailing newline optional — handles both cases (with/without blank line)
- `.lstrip("\n")` on the cleaned text removes any residual blank lines after the header
- `re.DOTALL` ensures `.*?` matches across newlines (in case the LLM wraps the JSON)
- Returns defaults for any failure mode: no match, invalid JSON, missing key, wrong type, empty result

### 2. `ccya/engine/turn.py` — wire into `run_turn()`

After line 338 (`narrative = strip_thinking(...)`), add parsing:

```python
narrative = strip_thinking("".join(narrative_chunks))
narrative, active_domains = _parse_narration_header(narrative)
```

Then at line 371, before `_run_extraction_pipeline`, build the modified intent:

```python
from ccya.models import IntentEnvelope, Scope

# Override intent scope with narration-derived domains
if intent is not None:
    skip = list(_ALL_DOMAINS - set(active_domains))
    modified_intent = intent.model_copy(
        update={"scope": Scope(
            active_domains=active_domains,
            skip_domains=skip,
            implicit_preconditions=intent.scope.implicit_preconditions,
            ambiguities=intent.scope.ambiguities,
        )}
    )
else:
    modified_intent = None
```

Pass `modified_intent` to `_run_extraction_pipeline` instead of `intent`:

```python
delta, actions, outcome_summary, failed, extraction_event, progress_result = (
    await _run_extraction_pipeline(
        env, state, narrative,
        rules_outcome=outcome,
        intent=modified_intent,  # was: intent
        config=config,
        ...
    )
)
```

### 3. `ccya/engine/turn.py` — wire into `run_turn_retry()`

Same pattern as `run_turn()`. After line 818 (`narrative = strip_thinking(...)`):

```python
narrative = strip_thinking("".join(narrative_chunks))
narrative, active_domains = _parse_narration_header(narrative)
```

Then build `modified_intent` and pass it to `_run_extraction_pipeline` at line 852.

### 4. `ccya/prompts/narrate_system.j2` — add instruction

Add a new section after the "Markdown (light)" section (after line 45), before the
conditional world/genre sections:

```
## Active domains header
Before writing your narrative, determine which state domains changed this turn.
Output them as a JSON block at the very top of your response, then write your prose.

Format: {"active_domains": ["domain1", "domain2"]}

Valid domains: scene, inventory, quest_updates, location_change, recent_events,
               pc_condition, compendium_npc

Only list domains that actually changed or need attention this turn.
`scene` is always active — include it in every response.
If nothing else changed, output: {"active_domains": ["scene"]}

IMPORTANT: If you are using thinking tags, output the JSON header AFTER the closing
</thinking> tag, not inside it. The header must be the first thing in your visible output.
```

The thinking mode instruction is critical — `strip_thinking()` removes content inside
`<thinking>` tags, so the header must be outside.

### 5. `ccya/engine/extraction.py` — no changes needed

The extraction pipeline reads `intent.scope.active_domains` and `intent.scope.skip_domains`
via `_active_domains(intent)` and `scope.skip_domains`. By passing the modified intent
from `turn.py`, both values are already correct. No changes to `extraction.py` are needed.

This is the key insight from the review: the existing pipeline checks `skip_domains` to
decide which streams run (lines 398-399, 440-441). By computing `skip` as the complement
of `active_domains` in `turn.py`, we ensure the right streams execute.

---

## Edge Cases

### LLM forgets the header

Fallback to defaults. The regex won't match, `json.loads` will fail, or the array
will be empty — all paths return `_DEFAULT_DOMAINS` (all 7 domains). Safe.

### LLM outputs header in wrong format

Same — validation catches it, returns defaults.

### LLM outputs header mid-response

The regex uses `re.match` which anchors at the start of the string. Mid-response headers
are ignored.

### Thinking mode enabled

`strip_thinking()` removes `<thinking>` content before `_parse_narration_header` runs.
The prompt instructs the LLM to output the header **after** the closing `</thinking>` tag.
The header will be at the start of the cleaned text.

### Retry path

`run_turn_retry()` also calls narration and needs the same parsing. Both paths are
updated identically.

### Empty narration

If the stream produces no content, `strip_thinking("")` returns `""`, the regex
won't match, and defaults are used. Safe.

### `build_state_slice()` in `narrate.py`

The state slice is built for the narration prompt, which happens **before** the narration
LLM runs. The narration LLM can't retroactively fix the state slice it was given.
This is acceptable — the state slice is already built with the rules LLM's domains,
and the narration LLM has full context regardless. The narration-derived domains only
affect the extraction pipeline, which runs after narration.

### Token budget impact

The JSON header is ~30-50 tokens. The prompt instruction is ~120 tokens. Total overhead
is minimal compared to the full narration prompt (~2000-4000 tokens).

---

## Testing

### Unit tests for `_parse_narration_header`

Create `tests/test_parse_narration_header.py`:

```python
from ccya.engine.turn import _parse_narration_header

def test_valid_header():
    text = '{"active_domains": ["scene", "inventory"]}\n\nThe guard falls...'
    cleaned, domains = _parse_narration_header(text)
    assert domains == ["scene", "inventory"]
    assert cleaned == "The guard falls..."

def test_valid_header_no_trailing_newline():
    text = '{"active_domains": ["scene"]}'
    cleaned, domains = _parse_narration_header(text)
    assert domains == ["scene"]
    assert cleaned == ""

def test_valid_header_with_whitespace():
    text = '  \n  {"active_domains": ["scene", "inventory"]}  \n\nProse here.'
    cleaned, domains = _parse_narration_header(text)
    assert domains == ["scene", "inventory"]
    assert cleaned == "Prose here."

def test_filters_unknown_domains():
    text = '{"active_domains": ["scene", "unknown_domain", "inventory"]}\n\nProse.'
    cleaned, domains = _parse_narration_header(text)
    assert domains == ["scene", "inventory"]
    assert cleaned == "Prose."

def test_invalid_json_fallback():
    text = '{"active_domains": ["scene",}\n\nProse.'
    cleaned, domains = _parse_narration_header(text)
    assert cleaned == text  # original text preserved
    assert "scene" in domains  # defaults include scene

def test_no_header_fallback():
    text = "Just prose, no header at all."
    cleaned, domains = _parse_narration_header(text)
    assert cleaned == text
    assert len(domains) == 7  # all defaults

def test_empty_array_fallback():
    text = '{"active_domains": []}\n\nProse.'
    cleaned, domains = _parse_narration_header(text)
    assert cleaned == text  # fallback, original preserved
    assert len(domains) == 7

def test_header_mid_response_ignored():
    text = "Some prose first.\n{"active_domains": ["scene"]}\nMore prose."
    cleaned, domains = _parse_narration_header(text)
    assert cleaned == text  # no match at start, returns original
    assert len(domains) == 7

def test_missing_active_domains_key():
    text = '{"other_key": "value"}\n\nProse.'
    cleaned, domains = _parse_narration_header(text)
    assert cleaned == text
    assert len(domains) == 7

def test_active_domains_not_list():
    text = '{"active_domains": "scene"}\n\nProse.'
    cleaned, domains = _parse_narration_header(text)
    assert cleaned == text
    assert len(domains) == 7

def test_empty_string():
    cleaned, domains = _parse_narration_header("")
    assert cleaned == ""
    assert len(domains) == 7

def test_header_followed_by_prose_with_braces():
    text = '{"active_domains": ["scene"]}\n\nThe guard said "}'
    cleaned, domains = _parse_narration_header(text)
    assert domains == ["scene"]
    assert cleaned == 'The guard said "}'
```

### Integration test

Add a test that mocks the LLM to return a narration with a valid header, then verifies
the extraction pipeline receives the correct domains. This requires `FakeLLM` configuration
in the test harness.

---

## Rollback

If the narration LLM consistently fails to output the header, or if the parsed
domains are worse than the rules LLM's guesses, the feature can be disabled by:

1. Removing the prompt instruction from `narrate_system.j2`
2. Removing the `_parse_narration_header` call from `turn.py` (both paths)

The fallback to defaults ensures nothing breaks even if the parsing function is present
but the LLM doesn't cooperate.

---

## Implementation Order

1. Add `_parse_narration_header()` to `turn.py` with unit tests
2. Add prompt instruction to `narrate_system.j2`
3. Wire parsing into `run_turn()` — parse header, build modified intent, pass to extraction
4. Wire parsing into `run_turn_retry()` — same pattern
5. Run `make test` to verify all tests pass
6. Manual testing with real LLM — verify headers are parsed correctly
7. Move plan to `docs/plans/completed/`
