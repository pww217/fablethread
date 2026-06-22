# Plan 05 — LLM-based checkers

## Purpose

Implement LLM-based narrative checkers (`directive_tone_match`, `beat_narrative_chain`, `state_fidelity`) and the model loading/orchestration for the `--checker-model` flag.

## Problem Statement

Deterministic checkers catch mechanical failures (wrong momentum delta, inventory overdraw) but cannot evaluate narrative quality: does the narration tone match the rules directive? Does the GM beat produce observable narrative consequence? Does extraction match what narration describes? These require semantic understanding that only an LLM can provide.

## Constraints

- Checker model is configurable via `--checker-model` flag (default: engine model Gemma 4-26B)
- Engine model and checker model are never in memory simultaneously
- LLM checkers use the same `@register_checker` interface as deterministic checkers
- Each LLM checker has a focused 20–30 line prompt, not a monolithic rubric
- Model is loaded on demand for `check --all --llm` or `check <turn> <llm_checker>`

## Non-goals

- Replacing the old rubric-based judges — those are being deleted in phase 6
- Multi-run trend tracking
- Agentic evaluation (multi-step reasoning across many turns)

## Solution

Implement LLM checker base infrastructure: model loading, context formatting, structured output parsing. Implement three LLM checkers, each with a focused prompt. Wire into the checker framework via the existing `@register_checker` interface.

## Firm decisions

- Checker model defaults to engine model (Gemma). Override with `--checker-model`.
- Only one model loaded at a time. Engine model unloaded before checker model loads.
- LLM checkers return the same `CheckerResult` type as deterministic checkers.
- Prompts are focused (20–30 lines each), not multi-concern rubrics.

## Risks, Ambiguities, and Blockers

- Model loading/unloading is slow (10–30s). UX impact: `check --all --llm` has a noticeable delay before producing output. Mitigation: print "Loading checker model..." to stderr before loading.
- LLM output parsing: the checker model must emit structured output. If it emits malformed JSON, the checker must degrade gracefully (return inconclusive, not crash).
- Prompt quality: each checker prompt needs iteration to produce reliable results. The prompts in this plan are starting points, not final. Expect to iterate.
- What model is used for loading/unloading? mlx-lm's `load_model` and model lifecycle. Check the actual `ccya/llm_client.py` for the loading API.

## Status

`completed`

## Implementation

### Context files to load

- `ccya/llm_client.py` — `chat()` function signature, model loading, tokenization
- `ccya/engine/config.py` line 86 (`EngineConfig` — model name, temperature, generation config)
- `ccya/ev/checkers/__init__.py` — `register_checker`, `CheckerResult`, `CheckerMeta`
- `ccya/ev/events.py` — event field extraction utilities
- `ccya/models.py` — relevant data types for formatting checker context

### Detailed steps

#### Step 5.1 — LLM checker infrastructure

**File:** `ccya/ev/checkers/_llm.py`

**What:** Shared utilities for LLM-based checkers.

```python
import hashlib
from ccya.llm_client import chat as llm_chat

_checker_model: tuple[Any, Any] | None = None  # (model, tokenizer)

def _load_checker_model(config: EngineConfig) -> tuple[Any, Any]:
    """Load the checker model. Uses config.model if --checker-model not set,
    otherwise loads the specified model. Caches the loaded model.
    Logs a message to stderr: "Loading checker model: {model_name}..."
    """

def _unload_checker_model():
    """Unload the checker model to free memory."""

def _call_llm_checker(
    system_prompt: str,
    user_prompt: str,
    config: EngineConfig,
) -> dict:
    """Call the checker LLM and parse its structured output.
    
    1. Ensure checker model is loaded (_load_checker_model)
    2. Call llm_chat with system + user prompt
    3. Try to parse response as JSON
    4. If parsing fails, return {"error": "parse_failed", "raw": response}
    5. Return parsed dict
    
    The LLM is instructed to return a JSON object with keys:
    {"passed": bool, "score": float, "reasoning": str, "findings": list[dict]}
    """

def _build_checker_prompt(checker_id: str, events: list[dict]) -> tuple[str, str]:
    """Build system and user prompts for a checker.
    Uses a template registry: {checker_id: (system_template, user_template)}.
    Renders templates with event data.
    """
```

**Why:** All LLM checkers share model loading, prompt rendering, and output parsing. Factoring this out keeps each checker focused on its specific evaluation logic.

**Validation:** `python -c "from ccya.ev.checkers._llm import _build_checker_prompt; print(_build_checker_prompt('directive_tone_match', [ev]))"` — produces a rendered prompt.

#### Step 5.2 — `directive_tone_match` checker

**File:** `ccya/ev/checkers/llm_checkers.py`

**What:**

```python
@register_checker(
    "directive_tone_match", "llm",
    requires_fields=["ruling.band", "ruling.intent", "narrate", "extraction_context.scene_tags_this_turn"],
    description="Does narration tone match the rules directive? (per-turn LLM call)",
)
def directive_tone_match(events: list[dict]) -> CheckerResult:
```

Prompt (system):
```
You are evaluating a narration's tone alignment with the game rules directive.
Given the ruling (band, intent) and the narration text, determine if the
narration's tone appropriately reflects the roll outcome.

A SUCCESS band should have confident, positive narration.
A FAIL band should have tense, setback-oriented narration.
A CRIT_FAIL should have severe consequence narration.
Scene tags may modify the expected tone (e.g., "tense_confrontation" raises stakes).

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "finding": str}
```

**Why:** The most straightforward LLM checker — compares two pieces of text (directive context and narration) for tonal consistency.

**Validation:** Create a test event where a success band has narration describing failure. Verify checker FAILs.

#### Step 5.3 — `beat_narrative_chain` checker

**File:** `ccya/ev/checkers/llm_checkers.py`

**What:**

```python
@register_checker(
    "beat_narrative_chain", "llm",
    requires_fields=["state_snapshot.meta.pending_gm_beat",
                    "narrate", "extraction.storytell"],
    description="Does the GM beat produce observable narrative consequence?",
)
def beat_narrative_chain(events: list[dict]) -> CheckerResult:
```

This checker looks at two consecutive turns (or one turn where a beat is set and the next where it's consumed). It evaluates whether the narrative consequence matches the declared GM beat type.

Prompt (system):
```
You are evaluating whether a GM beat's narrative consequence matches its
declared type. Given:
1. The GM beat type (pressure, escalation, complication, etc.)
2. The beat's surface_as (ambient, environmental, etc.)
3. The narration text where the beat was generated
4. The narration text of the following turn

Determine if the narrative consequence plausibly follows from the beat type.
A "pressure" beat should create urgency. A "complication" should introduce
an obstacle. An "escalation" should raise existing stakes. An "ambient"
beat need not produce specific consequences.

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "finding": str}
```

**Why:** This checks a core narrative mechanic — beats should produce observable effects in the story.

**Validation:** Run against a turn where a "pressure" beat was set. Verify the checker gives a reasoned evaluation.

#### Step 5.4 — `state_fidelity` checker

**File:** `ccya/ev/checkers/llm_checkers.py`

**What:**

```python
@register_checker(
    "state_fidelity", "llm",
    requires_fields=["narrate", "extraction_context",
                    "applied.inventory_add", "applied.inventory_remove",
                    "applied.pc_condition_add", "applied.pc_condition_remove"],
    description="Does extraction match what narration describes?",
)
def state_fidelity(events: list[dict]) -> CheckerResult:
```

This checker compares the narration text against the extraction results. If the narration says "you pick up the rusty key" but there's no inventory_add for a key, that's a fidelity failure.

Prompt (system):
```
You are evaluating whether the extraction (state changes) correctly reflects
the narration. Given:
1. The narration text
2. The inventory changes (add/remove)
3. The condition changes (add/remove)

Determine if the state changes are supported by the narration. The narration
must explicitly mention or strongly imply each state change. Missing changes
that the narration describes are failures. Extra changes not supported by
narration are also failures.

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "findings": [{"field": str, "issue": str}]}
```

**Validation:** Create a test event where narration mentions picking up an item but no inventory_add is recorded. Verify FAIL.

#### Step 5.5 — Wire `--llm` flag into check command

**File:** `ccya/ev/__init__.py` and `ccya/ev/check.py`

**What:** Update the check command dispatch to:
1. Accept `--llm` flag (already in interface from phase 4)
2. When `--llm` is present, include LLM-based checkers in the checker list
3. Before running LLM checkers, load the checker model (via `_llm._load_checker_model`)
4. After LLM checkers complete, unload checker model (via `_llm._unload_checker_model`)
5. If `--checker-model` is set, use that model name; otherwise use the engine model

Add `--checker-model` flag to `check` and `play --check` commands.

### Tests to write or update

1. `ev.py check 5 directive_tone_match --llm` — runs LLM checker, produces CheckerResult
2. `ev.py check 5 --all --llm` — runs all deterministic + all LLM checkers
3. `ev.py check 5 --all --llm --checker-model qwen3-35b` — uses Qwen for evaluation
4. Verify that malformed LLM output produces `inconclusive` CheckerResult, not a crash
5. Manual: inspect the rendered prompt to verify it contains the expected context
