# LLM Server Findings — `mlx_lm.server` Sampling Parameter Behavior

## Original Finding (2026-04): All OpenAI-compatible sampling parameters silently ignored

**Status: SUPERSEDED.** Per-request params now confirmed working with proper startup flags. See current findings below.

### Resolution Applied (2026-04)

Added `--temp 0.9 --top-p 0.95 --top-k 40 --min-p 0.05` to the `mlx-community/gemma-4-26b-a4b-it-mxfp8` entry in `~/.llm/llama-swap.yaml`.

---

## Current Findings (2026-06)

### Status: CONFIRMED WORKING — per-request temperature and seed forward to mlx

Per-request parameters **do forward** to the mlx server. Llama-swap does not reload the model when per-request parameters change — mlx handles them in-memory. The model stays "already ready" regardless of parameter changes.

### Confirmed Working (via API)

| Parameter | Status |
|---|---|
| `temperature` | ✅ Per-request override works, overrides startup `--temp` |
| `seed` | ✅ Same seed + params = identical cached output |
| `top_p` | ✅ Accepted without error; effect unproven but recommended |
| `frequency_penalty` | ✅ Accepted without error; targeted at narrate repetition (see table) |
| `presence_penalty` | ✅ Accepted without error; not used — freq_penalty covers the goal when stacked |

### Not Available via SDK

| Parameter | Status |
|---|---|
| `repetition_penalty`, `rep_penalty_window` | ❌ NOT in OpenAI SDK `Completions.create` signature — cannot be sent from Python client. Only available as server startup flags (`--rep-penalty`, `--rep-penalty-window`) or via `filters.setParams` in llama-swap.yaml. Static per-model, not per-request. |
| `top_k`, `min_p` | ❌ NOT in OpenAI SDK — only available as server startup flags (`--top-k`, `--min-p`). Static per-model. |

### No Model Reload on Per-Request Parameter Change

Changing params per-request does **not** trigger a model reload in llama-swap. Log shows `"already ready"` even when temperature varies across requests. The mlx server handles parameter changes in-memory.

---

## Gemma 4 26B — Recommended Sampling Parameters (Gemma-specific)

### Server startup flags (`llama-swap.yaml`)

Single server slot means one value per param. Anchor to narrate/seed since that's the highest-value creative work:

```
--temp 0.9
--top-p 0.95
--top-k 40
--min-p 0.05
--rep-penalty 1.08
--rep-penalty-window 64
```

**Do not add** `--dry-multiplier` — community testing shows it degrades Gemma 4 output quality. [reddit](https://www.reddit.com/r/Oobabooga/comments/1soekcx/optimal_sampling_parameters_for_gemma_4_models/)

### Per-call params (config.yaml)

These become live the moment mlx-lm ships per-request sampling param support. At that point `build_engine_config()` needs additional fields alongside existing temperature wiring:

| Stage | temp | top_p | top_k | min_p | freq_penalty | rep_penalty | presence_penalty |
|---|---|---|---|---|---|---|---|
| Ruling | 0.2 | 0.80 | 30 | null | null | 1.15 | null |
| Extract | 0.4 | 0.85 | 35 | 0.05 | 0.15 | null | null |
| Narrate | 0.9 | 0.95 | 40 | 0.05 | 0.5 | 1.08* | null |
| Seed gen | 0.9 | 0.95 | 40 | 0.05 | null | 1.08* | null |
| Pack gen | 0.8 | 0.95 | 40 | 0.05 | null | null | null |

### Rationale notes for the plan

- **Ruling top_p lowered to 0.80, top_k to 30**: tightest nucleus of any stage — near-deterministic rule resolution
- **Extract freq_penalty 0.15 fixed**: beats and state summaries benefit from light repetition suppression; anything higher risks mangling field names
- **Narrate freq_penalty 0.5 + rep_penalty 1.08**: freq_penalty handles word-level overuse, rep_penalty handles structural cadence problem (sentence opener repetition, beat shape repetition) that Gemma 4 specifically exhibits. Server-level value lowered from 1.15 to 1.08 as experiment — concerns about JSON/YAML syntax characters being penalized by extraction stage.
- **Seed gen skips freq_penalty**: want diverse archetype selection, not token suppression — rep_penalty alone keeps it from looping phrases mid-generation
- **Pack gen skips both penalties**: fully creative, no recurrence risk, long single-shot generation
- **min_p 0.05 everywhere except ruling**: at temp=0.2 the distribution is already so peaked that min_p's dynamic threshold scales to near-zero — effectively a no-op for ruling; skip it there to keep config clean and avoid edge cases where an unlikely-but-correct ruling interpretation gets clipped
- **rep_penalty window 64**: ~2–3 sentences of context, enough to break rhythmic patterns without penalizing legitimate reuse of proper nouns and game terms across longer output. Server-level value is 1.08 (experiment) — lowered from 1.15 due to concerns about JSON/YAML syntax characters being suppressed by extraction stage
- **presence_penalty null everywhere**: freq_penalty=0.5 at narrate already covers the goal; stacking both risks over-constraining vocabulary

### Server-level vs per-call rep_penalty asymmetry

The server startup flag sets `--rep-penalty 1.08` globally, which benefits narrate and seed gen (highest-value calls) without meaningfully harming ruling or extract — at temp=0.2 with a peaked distribution, a 1.08 multiplicative penalty on recently-seen tokens in a 64-token window has minimal practical effect since those tokens weren't likely candidates anyway. The asymmetry works in favor: the stages that need it benefit, the stages that don't are largely unaffected. Lowered from 1.15 to 1.08 as an experiment — 1.15 was feared to penalize JSON/YAML syntax characters (brackets, braces) used heavily by extraction.

---

## How to Replicate the Experiment

### Setup

```bash
# Ensure llama-swap is running on localhost:8080 with updated startup flags
MODEL="mlx-community/gemma-4-26b-a4b-it-mxfp8"
BASE="http://127.0.0.1:8080/v1"
```

### Test 1: Temperature forwarding (verifies per-request params work)

```bash
echo "=== temp=0.0 x2 (deterministic) ==="
for i in 1 2; do
  curl -s -X POST "$BASE/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"'"$MODEL"'","messages":[{"role":"user","content":"Starting with Twisted, describe a forest in 10 words."}],"max_tokens":100,"temperature":0.0}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
done

echo ""
echo "=== temp=1.8 x2 (random) ==="
for i in 1 2; do
  curl -s -X POST "$BASE/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"'"$MODEL"'","messages":[{"role":"user","content":"Starting with Twisted, describe a forest in 10 words."}],"max_tokens":100,"temperature":1.8}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
done

# Expected: temp=0.0 outputs identical to each other; temp=1.8 differs from temp=0.0
```

### Test 2: Seed determinism (verifies seed forwards)

```bash
echo "=== seed=42 x2 (should be identical) ==="
for i in 1 2; do
  curl -s -X POST "$BASE/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"'"$MODEL"'","messages":[{"role":"user","content":"Write a short sentence about a river."}],"max_tokens":80,"temperature":0.5,"seed":42}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
done

# Expected: both outputs byte-identical
```

### Test 3: Check llama-swap logs for model reload on param change

```bash
LOG_BEFORE=$(wc -l < ~/.llm/logs/llama-swap.log)

curl -s -X POST "$BASE/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"'"$MODEL"'","messages":[{"role":"user","content":"Test."}],"max_tokens":20,"temperature":0.0}' > /dev/null

curl -s -X POST "$BASE/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model":"'"$MODEL"'","messages":[{"role":"user","content":"Test."}],"max_tokens":20,"temperature":1.8}' > /dev/null

LOG_AFTER=$(wc -l < ~/.llm/logs/llama-swap.log)
tail -$((LOG_AFTER - LOG_BEFORE)) ~/.llm/logs/llama-swap.log | grep -E "loading|unload|reload|fast-path|dispatch"

# Expected: all entries show fast-path/"already ready", no model reload on temp change
```

### Test 4: Python client mirror test (verify new params before implementing)

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://127.0.0.1:8080/v1", api_key="local")
MODEL = "mlx-community/gemma-4-26b-a4b-it-mxfp8"

async def test_param(**kwargs):
    kwargs["model"] = MODEL
    kwargs["messages"] = [{"role": "user", "content": "Starting with Twisted, write a short sentence."}]
    kwargs["max_tokens"] = 100
    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content

async def main():
    r = await test_param(temperature=0.9, top_p=0.85)
    print(r)
    r = await test_param(temperature=0.9, frequency_penalty=0.5)
    print(r)
    # Compare outputs for visible difference

asyncio.run(main())
```

### Check supported params in OpenAI SDK

```python
from openai.resources.chat.completions import Completions
import inspect

sig = inspect.signature(Completions.create)
for name in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'repetition_penalty', 'seed']:
    print(f"{name}: {'supported' if name in sig.parameters else 'NOT supported'}")

# Expected: all except repetition_penalty are supported by the SDK
```

---

## Historical Context

- **2026-04 original finding**: mlx server ran without `--temp`, did greedy decoding, all params ignored
- **2026-04 resolution**: Added startup flags to llama-swap.yaml (`--temp 0.9 --top-p 0.95 --top-k 40 --min-p 0.05`)
- **2026-06 updated finding**: Per-request `temperature` and `seed` now work; additional params accepted but effect unproven; `repetition_penalty`, `top_k`, `min_p` only via server startup flags

## Future: build_engine_config changes when mlx-lm supports per-request sampling

When mlx-lm ships per-request support for these parameters, the following will need to change in addition to `llm_client.py`:

1. **EngineConfig dataclass** (`ccya/engine/config.py`): Add fields alongside existing temperatures — e.g., `ruling_top_p: float = 0.8`, `narrate_frequency_penalty: float = 0.5`, plus `rep_penalty` and `rep_penalty_window` if the SDK ever supports them (currently not in OpenAI SDK signature).

2. **build_engine_config()** (`ccya/engine/config.py:152-216`): Read new config keys from nested structure — e.g., `llm.get("ruling", {}).get("top_p")`, mapping to the corresponding EngineConfig field. Currently reads flat keys like `llm.get("narrate_temperature", 0.9)`.

3. **Caller sites**: Update ruling.py, extraction.py, turn.py, seed.py, generate_pack.py to pass new params from config to their respective llm calls — same pattern as existing temperature wiring.