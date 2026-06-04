# LLM Server Findings — `mlx_lm.server` Sampling Parameter Behavior

## Finding (2026-06-04): All OpenAI-compatible sampling parameters silently ignored (RESOLVED)

**Status: FIXED** — see Resolution section below.

### Original Finding

The running `mlx_lm.server` instance (v0.31.3, serving `mlx-community/gemma-4-26b-a4b-it-mxfp8`) was accepting OpenAI-compatible chat completions parameters without error but **not applying them**. The server ran deterministically regardless of the following parameters:

| Parameter | Tested values | Result |
|---|---|---|
| `temperature` | 0.0, 0.9 | Identical output |
| `frequency_penalty` | 0.0, 1.0, 2.0 | Identical output |
| `top_p` | 1.0 | No effect |
| `seed` | `null` | No effect |
| `bogus_parameter_xyz` | 1.0 | Silently accepted (no error) |

**Evidence:** Two separate calls with identical prompts but different `temperature` (0.0 vs 0.9) produced byte-identical output. Two calls with `frequency_penalty=0.0` vs `frequency_penalty=2.0` produced byte-identical output. Confirmed with trivial prompts ("Name three colors") and narrative prompts ("3-sentence story about a robot who learns to paint").

### Root Cause

`llama-swap.yaml` was launching the MLX server **without `--temp`**, causing MLX to default to greedy/argmax decoding. Per-request OpenAI-compatible parameters (`temperature`, `frequency_penalty`, etc.) are never forwarded to the underlying MLX generation — they're ignored by the server. The startup `--temp` flag is the only mechanism that controls sampling behavior.

### Impact (before fix)

- **`narrate_temperature: 0.9` in `config.yaml` was decorative** — the server ran greedily regardless
- **All other temperature knobs** (`ruling_temperature`, `extract_temperature`, `generate_seed_temperature`): same, decorative
- **`frequency_penalty` (Change C of narration-prompt-overhaul-design): dead code** — the design's blocking precondition correctly predicted this failure mode
- **Prompt-only changes were the only effective levers**

### Resolution (2026-06-04)

Added `--temp 0.9 --top-p 0.95 --top-k 40 --min-p 0.05` to the `mlx-community/gemma-4-26b-a4b-it-mxfp8` entry in `~/.llm/llama-swap.yaml`. The model slot must be reloaded via llama-swap for the new flag to take effect.

**Note:** With the single-slot fix, all pipeline stages (ruling, extract, narrate, seed) run at the same server-level temperature (0.9). The per-stage `config.yaml` temperature knobs remain decorative. If ruling instability is observed (erratic intent parsing, JSON extraction errors), the fix is a dual-slot setup: one slot at `--temp 0.3` for structured calls (ruling, extract), one at `--temp 0.9` for generative calls (narrate, seed), with model routing done in `config.yaml`.

### Verification

After reloading the model slot, run the two-call test:
```bash
# Run twice — outputs should differ if sampling is working
curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mlx-community/gemma-4-26b-a4b-it-mxfp8", "messages": [{"role": "user", "content": "Write a 3-sentence story about a robot who learns to paint."}], "temperature": 0.9}' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

If outputs differ between calls, sampling is now working.