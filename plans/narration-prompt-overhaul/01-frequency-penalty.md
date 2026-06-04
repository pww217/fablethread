# Narration Prompt Overhaul — Phase 1: Frequency Penalty

## Purpose

Add `frequency_penalty` to the narrate LLM call to reduce modifier and structural repetition in turn narration, with a blocking pre-condition to verify server support.

## Problem Statement

The narrate call passes only `temperature` to the LLM. No frequency, presence, or repetition penalty is set. After 34 turns, modifiers like "rhythmic" (20×), "sudden" (22×), and "like a" (13×) are overused. The model falls back on the same trained patterns because there is no penalty for reusing tokens proportional to their frequency.

## Constraints

- `mlx_lm.server` may not support `frequency_penalty` — this is a blocking pre-condition.
- Default 0.3 must be safe for Qwen3 27B. If sentence fluency degrades, reduce.
- No new config format or migration path.
- Only the narrate streaming call gets frequency_penalty. Extract/storytell/seed calls pass None (no change).

## Non-goals

- Not changing extract, storytell, or seed LLM calls.
- Not adding a config UI knob or runtime-mutable field.
- Not adding `presence_penalty` or `repeat_penalty`.
- Not changing the prompt templates.

## Solution

Add `narrate_frequency_penalty` config field (default 0.3), thread it through `EngineConfig` → `chat_stream()` → narrate call site. Other callers pass None (default). If server verification fails, the entire phase is abandoned and the prompt-only phases (2, 3) are the full intervention.

## Firm decisions

1. Default 0.3 — safe starting value. Monitor and adjust (failure modes document 0.5 if repetition persists, 0.15 if fluency degrades).
2. Narrate-only. Seed is single-shot (modifier repetition less visible); extract/storytell use `chat()` not `chat_stream()`.
3. Blocking pre-condition: if `frequency_penalty` is silently ignored by the server, drop this phase entirely.

## Risks, Ambiguities, and Blockers

- **BLOCKING PRE-CONDITION:** `mlx_lm.server` support for `frequency_penalty` is unverified. A curl-based test must pass before implementation begins.
- Frequency penalty penalizes all repeated tokens proportionally, including common words ("the", "a", "was") that appear more often. At 0.3 the effect should be mild, but monitor for unnatural article/auxiliary patterns.
- Qwen3 27B may respond differently to frequency_penalty than other models. If modifier repetition persists, increase to 0.5. If fluency degrades, reduce to 0.15.

## Status
`open`

## Blocking pre-condition — verify frequency_penalty server support

Before any implementation, run a curl-based verification against the running server.

**Verification script:**

```bash
# 1. Send a prompt with frequency_penalty=0.0 (baseline)
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen3.6-27B-4bit",
    "messages": [
      {"role": "system", "content": "Repeat the word 'rhythmic' as many times as you can in a sentence. Keep going until I stop you."},
      {"role": "user", "content": "Write a sentence using the word 'rhythmic'."}
    ],
    "frequency_penalty": 0.0,
    "max_tokens": 100
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"

# 2. Same prompt with frequency_penalty=1.0
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen3.6-27B-4bit",
    "messages": [
      {"role": "system", "content": "Repeat the word 'rhythmic' as many times as you can in a sentence. Keep going until I stop you."},
      {"role": "user", "content": "Write a sentence using the word 'rhythmic'."}
    ],
    "frequency_penalty": 1.0,
    "max_tokens": 100
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"
```

**Pass condition:** The `frequency_penalty=1.0` output uses "rhythmic" significantly fewer times than the `0.0` baseline. If outputs are identical or the server returns an error without dropping frequency_penalty (common silent-ignore pattern), abandon Phase 1.

## Implementation — Phase 1

### Context files to load

- `ccya/engine/config.py` — `EngineConfig` dataclass + `build_engine_config()` function
- `ccya/config.yaml` — LLM config section
- `ccya/llm_client.py` — `chat_stream()` function
- `ccya/engine/turn.py` — narrate call site at lines 944–951

### Detailed steps

#### Step 1.1 — Add `narrate_frequency_penalty` to EngineConfig

**File:** `ccya/engine/config.py`

**What:** Add `narrate_frequency_penalty: float = 0.3` field to the `EngineConfig` dataclass (after `narrate_temperature`).

**Why:** Central config dataclass consumed by the turn pipeline. New field follows the same pattern as existing temperature fields.

**Validation:** `make check` passes. No other code changes needed — default 0.3 is a valid default with or without the turn.py change.

#### Step 1.2 — Parse in `build_engine_config()`

**File:** `ccya/engine/config.py`

**What:** Add `narrate_freq = float(llm.get("narrate_frequency_penalty", 0.3))` after the temperature parsing block (after line 173), and pass it as `narrate_frequency_penalty=narrate_freq` to the `EngineConfig(...)` constructor.

**Why:** Bridge between config.yaml dict and the typed dataclass.

**Validation:** `make check` passes.

#### Step 1.3 — Add `frequency_penalty` to config.yaml

**File:** `config.yaml`

**What:** Add `narrate_frequency_penalty: 0.3` under the `llm:` section (after `narrate_temperature: 0.9`).

**Why:** User-visible default. Follows the existing `narrate_temperature` naming pattern.

**Validation:** Manual inspection. The `build_engine_config()` fallback to 0.3 means this is not load-bearing.

#### Step 1.4 — Add `frequency_penalty` parameter to `chat_stream()`

**File:** `ccya/llm_client.py`

**What:** Add `frequency_penalty: float | None = None` as a keyword-only parameter to `chat_stream()` (after `temperature`). Add it to the `kwargs` dict when not None:

```python
kwargs["frequency_penalty"] = frequency_penalty
```

**Why:** The OpenAI-compatible API accepts `frequency_penalty` as a chat completions parameter. Default None ensures backward compatibility — callers that don't pass it get no penalty.

**Validation:** `make check` passes.

#### Step 1.5 — Pass `frequency_penalty` from narrate call site

**File:** `ccya/engine/turn.py`

**What:** Add `frequency_penalty=config.narrate_frequency_penalty` to the `llm_chat_stream()` call at line 944:

```python
async for chunk in llm_chat_stream(
    config.host,
    config.model,
    narr_messages,
    temperature=config.narrate_temperature,
    frequency_penalty=config.narrate_frequency_penalty,
    timeout=float(config.request_timeout_s),
    stream_stats=narr_stream_stats,
):
```

**Why:** This is the only streaming call that benefits from frequency-based repetition reduction.

**Validation:** `make check` passes.

### Tests to write or update

No tests exist during refactor phase. Validation is by `make check` after all steps, plus a manual sanity check: run a turn and verify the LLM call includes `frequency_penalty` in the request (visible in application logs if `log_llm_io` is enabled).
