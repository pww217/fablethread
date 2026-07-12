# Plan: Add Per-Call Sampling Parameters (top_p, frequency_penalty) and Full Config Nesting

## Purpose

Add top_p, frequency_penalty, seed, and stub fields for top_k/min_p/rep_penalty to the LLM client layer with a nested config structure (`llm.ruling.temperature`, `llm.narrate.top_p`), enabling stage-specific sampling profiles across all pipeline callers.

## Problem Statement

The ccya codebase currently passes only `temperature` per-call from flat YAML keys (e.g., `narrate_temperature: 0.9`). Different pipeline stages need different sampling profiles — ruling needs near-deterministic output, narrate needs creative variety with repetition suppression — but the client layer has no support for additional sampling parameters. The config structure is also unwieldy with long flat key names that double as nested keys (`ruling_temperature`, `extract_frequency_penalty`).

## Constraints

- No backward compatibility: direct migration from flat to nested config only
- All fields added to EngineConfig now, even if some are null stubs for later wiring (top_k, min_p, rep_penalty)
- llm_client.py must accept all new params as optional keyword-only arguments with conditional pass-through (only included in request dict when not None)
- generate_pack_from_brief() receives full EngineConfig like other callers — no individual host/model args pattern
- Warmup call stays hardcoded at temperature=0.0 (cold-start optimization, not a user-facing stage)
- llama-swap.yaml already updated with `--rep-penalty 1.15 --rep-penalty-window 64`

## Non-goals

- Does NOT implement per-request top_k/min_p/rep_penalty wiring — those fields exist in EngineConfig but llm_client.py will not pass them to the API (blocker: mlx-lm SDK support)
- Does NOT change warmup call behavior
- Does NOT add presence_penalty or seed values from config (seed always null, presence_penalty skipped per design decision)

## Solution

Add top_p and frequency_penalty as new EngineConfig fields with nested YAML keys. Extend llm_client.py's `chat()` and `chat_stream()` to accept these plus stub fields for later SDK support. Update all callers (ruling, extract, narrate, seed gen, pack gen) to pass the new params from config. Migrate config.yaml from flat keys (`narrate_temperature: 0.9`) to nested structure (`llm.narrate.temperature`).

## Firm decisions

1. **Nested config format**: `config.llm.ruling.top_p`, not `config.ruling_top_p`
2. **No backward compatibility**: direct migration, no flat-key fallback
3. **All fields in EngineConfig now**: even null stubs for top_k/min_p/rep_penalty to avoid the pacing-beat-system-design.md burn pattern of unlisted dataclass defaults silently swallowing YAML values
4. **generate_pack_from_brief gets full config**: consistent with ruling/extraction/turn/seed — no individual host/model args
5. **Warmup stays hardcoded at 0.0**: cold-start optimization, not a user-facing stage
6. **llm_client.py conditional pass-through only**: new params included in request dict iff not None
7. **rep_penalty/top_k/min_p accepted but never passed to API**: llm_client.py accepts them as kwargs for future wiring; they are excluded from the OpenAI-compatible request dict since mlx-lm doesn't support per-request these yet

## Risks, Ambiguities, and Blockers

- **Risk**: Changing generate_pack_from_brief() signature (config instead of host/model) touches routes.py which calls it — must verify no other callers exist
- **Blocker**: top_k/min_p/rep_penalty cannot be passed to the API until mlx-lm adds per-request support for these parameters. Fields in EngineConfig are stubs only.

## Status
`completed`

## Phases

3 phases: migrate config structure, extend client layer with new params, wire all callers to pass new params from nested config.

---

## Implementation — Phase 1: Migrate config.yaml and update EngineConfig dataclass + build_engine_config()

### Context files to load
- `config.yaml` (repo root)
- `ccya/engine/config.py` lines 92–216 (EngineConfig dataclass + build_engine_config function)

### Detailed steps

#### Step 1.1 — Migrate config.yaml from flat keys to nested structure

**File:** `config.yaml`

**What:** Replace the four flat temperature keys with a nested structure under each stage key:
```yaml
llm:
  host: http://127.0.0.1:8080/v1
  model: mlx-community/gemma-4-26b-a4b-it-mxfp8
  request_timeout_s: 180

  ruling:
    temperature: 0.2
    top_p: 0.80

  extract:
    temperature: 0.4
    top_p: 0.85
    frequency_penalty: 0.15

  narrate:
    temperature: 0.9
    top_p: 0.95
    frequency_penalty: 0.5

  generate_seed:
    temperature: 0.9
    top_p: 0.95

  pack_generation:
    temperature: 0.8
    top_p: 0.95

  max_llm_retries: 1
  context_window: 32768
```

Remove the old flat keys (`ruling_temperature`, `extract_temperature`, `narrate_temperature`, `generate_seed_temperature`). Add new key `pack_generation` with temperature and top_p (currently not in config at all). Keep existing non-LLM keys unchanged.

**Why:** Nested structure is shorter, groups related params naturally, eliminates the long flat key naming pattern that doubled as nested keys.

**Validation:** Run `python3 -c "import yaml; print(yaml.safe_load(open('config.yaml'))['llm'])"` — verify output has nested dict under ruling/extract/narrate/generate_seed/pack_generation with correct values, and old flat keys are gone.

#### Step 1.2 — Add new fields to EngineConfig dataclass

**File:** `ccya/engine/config.py` (EngineConfig class)

**What:** Add the following fields after existing temperature fields:
```python
# ruling
ruling_top_p: float = 0.8

# extract  
extract_top_p: float = 0.85
extract_frequency_penalty: float = 0.15

# narrate
narrate_top_p: float = 0.95
narrate_frequency_penalty: float = 0.5

# generate_seed
generate_seed_top_p: float = 0.95

# pack_generation (stub)
pack_generation_temperature: float = 0.8
pack_generation_top_p: float = 0.95

# SDK-supported but not yet wired from config
seed: None = None

# Stub fields for later mlx-lm per-request support — always null until SDK adds these params
top_k: None = None
min_p: None = None
rep_penalty: None = None
rep_penalty_window: None = None
```

**Why:** All fields must exist in the dataclass now to prevent the silent-default-burn pattern. Stub fields with `None` defaults make it explicit that these are not yet wired from config, while still being available when mlx-lm adds SDK support.

**Validation:** Run `python3 -c "from ccya.engine.config import EngineConfig; e = EngineConfig(); print(e.ruling_top_p)"` — should output 0.8 without error. Verify all new fields are accessible with correct defaults.

#### Step 1.3 — Update build_engine_config() to read nested config format

**File:** `ccya/engine/config.py` (build_engine_config function)

**What:** Replace the flat-key reading pattern:
```python
# OLD
narrate_t = float(llm.get("narrate_temperature", 0.9))
extract_t = float(llm.get("extract_temperature", 0.4))
ruling_t = float(llm.get("ruling_temperature", 0.2))
seed_t = float(llm.get("generate_seed_temperature", 0.9))
```

With nested reading:
```python
# NEW — ruling
ruling_cfg = llm.get("ruling", {})
ruling_t = float(ruling_cfg.get("temperature", 0.2))
ruling_top_p = float(ruling_cfg.get("top_p", 0.8))

# extract
extract_cfg = llm.get("extract", {})
extract_t = float(extract_cfg.get("temperature", 0.4))
extract_top_p = float(extract_cfg.get("top_p", 0.85))
extract_freq_penalty = float(extract_cfg.get("frequency_penalty") or 0)

# narrate
narrate_cfg = llm.get("narrate", {})
narrate_t = float(narrate_cfg.get("temperature", 0.9))
narrate_top_p = float(narrate_cfg.get("top_p", 0.95))
narrate_freq_penalty = float(narrate_cfg.get("frequency_penalty") or 0)

# generate_seed
seed_cfg = llm.get("generate_seed", {})
seed_t = float(seed_cfg.get("temperature", 0.9))
seed_top_p = float(seed_cfg.get("top_p", 0.95))

# pack_generation (stub — not yet used by callers, but read for completeness)
pack_cfg = llm.get("pack_generation", {})
pack_temp = float(pack_cfg.get("temperature") or 0.8)
pack_top_p = float(pack_cfg.get("top_p") or 0.95)
```

Then pass all new values to the EngineConfig constructor:
```python
return EngineConfig(
    host=..., model=..., context_window=..., request_timeout_s=...,
    ruling_temperature=ruling_t, extract_temperature=extract_t, narrate_temperature=narrate_t, generate_seed_temperature=seed_t,
    ruling_top_p=ruling_top_p,
    extract_top_p=extract_top_p, extract_frequency_penalty=extract_freq_penalty,
    narrate_top_p=narrate_top_p, narrate_frequency_penalty=narrate_freq_penalty,
    generate_seed_top_p=seed_top_p,
    pack_generation_temperature=pack_temp, pack_generation_top_p=pack_top_p,
    max_llm_retries=..., log_llm_io=..., log_llm_io_max_chars=..., log_prompts=...,
    # ... rest unchanged (game fields)
)
```

**Why:** Reads from the new nested YAML structure. Uses `or 0` for frequency_penalty since it's optional in config but defaults to 0 when not specified. Stub values read with `or default` pattern so missing pack_generation section doesn't crash.

**Validation:** Run `python3 -c "from ccya.engine.config import build_engine_config; from ccya.models import load_config; cfg = load_config(); ec = build_engine_config(cfg); print(ec.narrate_top_p, ec.extract_frequency_penalty)"` — should output 0.95 and 0.15 respectively.

---

## Implementation — Phase 2: Extend llm_client.py with new sampling parameters

### Context files to load
- `ccya/llm_client.py` (full file)

### Detailed steps

#### Step 2.1 — Add optional kwargs to chat() function signature and conditional pass-through

**File:** `ccya/llm_client.py`, `chat()` function (around line 145)

**What:** Extend the existing parameters:
```python
# ADD these after temperature in the signature:
top_p: float | None = None,
frequency_penalty: float | None = None,
seed: int | None = None,
# Stub fields for later mlx-lm SDK support — accepted but never passed to API yet:
top_k: int | None = None,  # not in OpenAI SDK signature
min_p: float | None = None,  # not in OpenAI SDK signature  
rep_penalty: float | None = None,  # not in OpenAI SDK signature
rep_penalty_window: int | None = None,  # not in OpenAI SDK signature
```

Add conditional pass-through for the three SDK-supported params (top_p, frequency_penalty, seed) — same pattern as temperature:
```python
# After existing kwargs dict construction, add:
if top_p is not None:
    kwargs["top_p"] = float(top_p)
if frequency_penalty is not None:
    kwargs["frequency_penalty"] = float(frequency_penalty)
if seed is not None:
    kwargs["seed"] = int(seed)

# Do NOT pass top_k/min_p/rep_penalty to the API — stubs only, for future wiring when mlx-lm adds SDK support.
```

**Why:** Conditional pass-through means callers can always pass these params without checking if they're set. The three SDK-supported ones get forwarded; the stub fields are accepted as kwargs but never included in the request dict (blocker: not in OpenAI SDK signature).

**Validation:** Run `python3 -c "import inspect; from ccya.llm_client import chat; sig = inspect.signature(chat); print([p for p in sig.parameters])"` — verify new params appear. Check that top_k/min_p/rep_penalty are NOT passed to the API by reviewing the kwargs dict construction logic.

#### Step 2.2 — Add optional kwargs to chat_stream() function signature and conditional pass-through

**File:** `ccya/llm_client.py`, `chat_stream()` function (around line 105)

**What:** Same pattern as chat(): add top_p, frequency_penalty, seed, plus stub fields (top_k, min_p, rep_penalty, rep_penalty_window) to the signature. Add conditional pass-through for SDK-supported params in the kwargs dict before passing to `client.chat.completions.create()`.

**Why:** Consistency — both streaming and non-streaming paths must support all new parameters identically.

**Validation:** Same inspection approach as Step 2.1 but against chat_stream(). Verify signature matches chat() for sampling param names (excluding timeout/stream_stats which are stream-specific).

---

## Implementation — Phase 3: Wire callers to pass new params from config

### Context files to load
- `ccya/engine/ruling.py` lines 70–85 (llm_chat call)
- `ccya/engine/extraction.py` lines 345–351 (llm_chat call)
- `ccya/engine/turn.py` lines 936–942 (llm_chat_stream call for narrate)
- `ccya/engine/seed.py` lines 244–250 (llm_chat call)
- `ccya/server/routes.py` lines 485–510 (generate_pack_from_brief call site)
- `ccya/engine/generate_pack.py` lines 36–107 (function signature and llm_chat call)

### Detailed steps

#### Step 3.1 — Update ruling.py to pass top_p from config

**File:** `ccya/engine/ruling.py`, the `llm_chat()` call at line 77

**What:** Add `top_p=config.ruling_top_p` to the existing llm_chat() arguments:
```python
result = await llm_chat(
    config.host,
    config.model,
    messages,
    temperature=config.ruling_temperature,
    top_p=config.ruling_top_p,  # NEW
    timeout=float(config.request_timeout_s),
)
```

**Why:** Ruling needs tight nucleus (top_p=0.80) for near-deterministic rule resolution per Gemma 4 recommendations.

**Validation:** Verify the call site has top_p passed as keyword argument after temperature, before timeout. No other callers of ruling.py's main function need changes — config is already passed in.

#### Step 3.2 — Update extraction.py to pass top_p and frequency_penalty from config

**File:** `ccya/engine/extraction.py`, the `_call_stream()` llm_chat() call at line 345

**What:** Add both new params:
```python
result = await llm_chat(
    config.host,
    config.model,
    messages,
    temperature=config.extract_temperature,
    top_p=config.extract_top_p,              # NEW
    frequency_penalty=config.extract_frequency_penalty,  # NEW
    timeout=float(config.request_timeout_s),
)
```

**Why:** Extract benefits from light repetition suppression (freq_penalty=0.15) and moderate nucleus (top_p=0.85) for beat/state diversity while preserving field names.

**Validation:** Verify both new params passed as keyword arguments after temperature, before timeout. Check that `_call_stream` is the only llm_chat call in extraction.py — if there are additional calls elsewhere, update those too.

#### Step 3.3 — Update turn.py narrate call to pass top_p and frequency_penalty from config

**File:** `ccya/engine/turn.py`, the `llm_chat_stream()` call at line 936 (narration phase)

**What:** Add both new params:
```python
async for chunk in llm_chat_stream(
    config.host,
    config.model,
    narr_messages,
    temperature=config.narrate_temperature,
    top_p=config.narrate_top_p,              # NEW
    frequency_penalty=config.narrate_frequency_penalty,  # NEW
    timeout=float(config.request_timeout_s),
    stream_stats=narr_stream_stats,
):
```

**Why:** Narration needs creative variety with repetition suppression (temp=0.9, top_p=0.95, freq_penalty=0.5) to prevent word/phrase drift across turns per Gemma 4 recommendations.

**Validation:** Verify new params passed after temperature, before timeout and stream_stats. Check that the warmup call at line ~1498 stays unchanged (hardcoded temp=0.0). Also check if turn.py has any other llm_chat calls besides narrate/warmup — update those too if present.

#### Step 3.4 — Update seed.py to pass top_p from config

**File:** `ccya/engine/seed.py`, the `llm_chat()` call at line 244

**What:** Add top_p:
```python
result = await llm_chat(
    config.host,
    config.model,
    messages,
    temperature=config.generate_seed_temperature,
    top_p=config.generate_seed_top_p,  # NEW
    timeout=float(config.request_timeout_s),
)
```

**Why:** Seed generation benefits from high creativity (temp=0.9) with moderate nucleus control (top_p=0.95). Skips frequency_penalty per design decision to allow diverse archetype selection.

**Validation:** Verify top_p passed as keyword argument after temperature, before timeout. Check that the retry loop structure is preserved — no changes to attempt counting or error handling logic.

#### Step 3.5 — Update generate_pack_from_brief() and its call site in routes.py

**File A:** `ccya/engine/generate_pack.py`, function signature at line 36
**File B:** `ccya/server/routes.py`, lines 491–507 (call site)

**What A — Change generate_pack_from_brief() signature:** Replace individual host/model args with full EngineConfig:
```python
# OLD signature:
async def generate_pack_from_brief(
    inputs, packs_root, llm_host, llm_model, template_dir, trace_id, max_retries=1,
):

# NEW signature:
async def generate_pack_from_brief(
    inputs, packs_root, config, template_dir, trace_id, max_retries=1,
):
```

Update the internal llm_chat call at line 99 to use config fields and pass new params:
```python
response_text = await llm_chat(
    host=config.host,
    model=config.model,
    messages=[...],
    temperature=config.pack_generation_temperature,   # NEW
    top_p=config.pack_generation_top_p,               # NEW
    timeout=300.0,
)
```

**What B — Update routes.py call site:** Replace individual host/model args with config:
```python
# OLD (around line 491):
llm_host = str(_app_mod.engine_config.host).rstrip("/")
llm_model = str(_app_mod.engine_config.model)
max_retries = _app_mod.engine_config.max_llm_retries

async def _stream():
    async for event in generate_pack_from_brief(
        inputs=inputs, packs_root=packs_root, llm_host=llm_host, 
        llm_model=llm_model, template_dir=template_dir, trace_id=trace_id, max_retries=max_retries,
    ):

# NEW:
async def _stream():
    async for event in generate_pack_from_brief(
        inputs=inputs, packs_root=packs_root, config=_app_mod.engine_config, 
        template_dir=template_dir, trace_id=trace_id, max_retries=max_retries,
    ):
```

**Why:** Makes generate_pack consistent with all other callers (ruling/extraction/turn/seed) which receive full EngineConfig. Eliminates the inconsistent pattern of passing host/model individually while also accessing config elsewhere in routes.py. Adds temperature and top_p for pack gen stage per Gemma 4 recommendations (temp=0.8, top_p=0.95).

**Validation:** Verify generate_pack_from_brief() signature changed from individual args to config object. Verify internal llm_chat call uses `config.host`, `config.model`, etc. Verify routes.py no longer extracts host/model individually before the call — passes `_app_mod.engine_config` directly instead. Run a quick syntax check: `python3 -c "from ccya.server.routes import *"` and `python3 -c "from ccya.engine.generate_pack import generate_pack_from_brief"`.

#### Step 3.6 — Update docs/repomap.md to reflect new fields and signatures

**File:** `docs/repomap.md`

**What:** Update the following sections:
- Lines 78–80 (llm_client.py section): Change from `chat(host, model, messages) → response dict` to include optional params. New signature: `chat(host, model, messages, *, temperature=None, max_tokens=None, timeout=180, top_p=None, frequency_penalty=None, seed=None, ...)`. Update chat_stream similarly with new sampling params.
- Line 167+ (EngineConfig field naming): Add new fields to the list: ruling_top_p, extract_top_p, narrate_top_p, generate_seed_top_p, pack_generation_temperature, pack_generation_top_p, extract_frequency_penalty, narrate_frequency_penalty, seed, top_k, min_p, rep_penalty, rep_penalty_window.
- Line 12 (config.py description): Update to mention sampling parameter fields alongside existing EngineConfig dataclass description.

**Why:** The plan skill requires documentation updates as mandatory — `docs/repomap.md` must reflect new files, functions, signatures, module boundaries, cross-module contracts, or public APIs. These are all API changes that affect the repomap.

**Validation:** Run `grep -n "EngineConfig\|chat_stream\|llm_client" docs/repomap.md | head -20` — verify new fields and updated signatures appear in the output.

---

### Tests to write or update

Tests are temporarily removed during refactor — skip test updates per AGENTS.md. Run `make check` (lint + typecheck) as final validation step after all phases complete.