# Eval Harness

Two-tier testing system. These are distinct pipelines with different goals, tooling, and when they run.

---

## Tier 1 — Structural Integration Tests (`make test`)

**Goal:** Fast, offline, deterministic pass/fail. Runs in CI on every change.

**Mechanism:** Uses the existing `_FakeLLM` in `test_engine_smoke.py`, which already handles the full 5-call turn structure (rules, narrate, scene extract, state extract, progress extract). Fixtures provide canned responses; the engine runs fully, touching all real code paths except the LLM client boundary.

**What is asserted:**
- Required fields present in `TurnResult` and emitted `StateDelta`
- No items in both inventory and removed list (reconciliation check)
- Index references in extractor output resolve to valid slugs
- Out-of-range indexes rejected as extraction failures, not silently ignored
- Retry logic triggered on malformed extraction response
- State before/after delta is internally consistent (no duplicate IDs, no orphaned references)
- `apply_delta` produces expected state shape for each fixture scenario

**Fixture format** (`tests/evals/fixtures/<name>.yaml`):
```yaml
description: "One-line human-readable scenario label"
input:
  player_command: "I reload my rifle and take cover"
  state: <inline snapshot of state.yaml — inventory, NPCs, scene, pc, meta.turn>
llm_responses:
  rules: <canned JSON string>
  narrative: <canned prose string>
  scene_extract: <canned JSON string>
  state_extract: <canned JSON string>
  progress_extract: <canned JSON string>
  # Optional: retry variants
  state_extract_retry: <malformed JSON to trigger retry path>
assertions:
  delta_contains:
    - path: "inventory"
      action: "remove"
      slug: "iron_rifle"
  state_after:
    - path: "pc.conditions"
      contains: "taking_cover"
  extraction_failures: 0
  retries: 0
```

**Fixture scenarios to build (start here):**
1. `golden_midgame.yaml` — realistic mid-game state, inventory + active NPCs, moderately complex command. Primary regression baseline.
2. `consumable_use.yaml` — player uses ammo; engine applies quantity math.
3. `item_remove.yaml` — item removed; index gap closed; next reference uses compacted indexes.
4. `npc_reference.yaml` — extractor references NPC by index; resolves to correct slug.
5. `extraction_retry.yaml` — first state_extract response is malformed; retry succeeds.
6. `extraction_total_failure.yaml` — all retries exhausted; TurnResult reflects failure correctly.

**Test runner:** Parametrized pytest — one test per fixture file in `tests/evals/fixtures/`. Runs as part of `make test`. Should complete in under 5 seconds total.

---

## Tier 2 — Qualitative Eval Pipeline (`make eval`)

**Goal:** Full live-server run against a real LLM. Local only, never CI. Run deliberately after significant changes to prompts, extraction logic, or state schema.

**Mechanism:** Assumes server is already running (`make dev` or `make run`). Uses the live HTTP API — same path a real game takes. No mocking.

**Flow:**

1. **Seed a known state** — `POST /new-game` with a fixture pack or direct state file injection (TBD: add a `/eval/load-state` route or write state.yaml directly before run).
2. **Submit a turn** — `GET /turn?input=<command>` (SSE stream). Drain the stream.
3. **Fetch results** — `GET /turn_viewer/data` returns full pipeline JSON.
4. **Write JSONL log** — append one record per pipeline phase with clear phase boundaries.
5. **Repeat** for N turns if running a multi-turn scenario.

**Output format** (`evals/outputs/<scenario>/<timestamp>.jsonl`, gitignored):
```jsonl
{"phase": "meta", "turn": 4, "player_command": "...", "timestamp": "..."}
{"phase": "rules", "intent": {...}, "outcome": {...}}
{"phase": "narration", "text": "..."}
{"phase": "scene_extract", "response_raw": "...", "delta": {...}, "retries": 0}
{"phase": "state_extract", "response_raw": "...", "delta": {...}, "retries": 0}
{"phase": "progress_extract", "response_raw": "...", "delta": {...}, "retries": 0}
{"phase": "state_after", "snapshot": {...}}
```

**Tooling for qualitative analysis:**

Inspect a run with `jq`:
```bash
# See all phases for a run
cat evals/outputs/golden_midgame/latest.jsonl | jq '.phase'

# Inspect state delta from state_extract
cat evals/outputs/golden_midgame/latest.jsonl | jq 'select(.phase == "state_extract") | .delta'

# Check retry counts across all extraction phases
cat evals/outputs/golden_midgame/latest.jsonl | jq 'select(.retries != null) | {phase, retries}'

# Diff state_before vs state_after
cat evals/outputs/golden_midgame/latest.jsonl | jq 'select(.phase == "state_after") | .snapshot'
```

Or use the Python helper (`scripts/eval_inspect.py`, TBD):
```bash
python scripts/eval_inspect.py evals/outputs/golden_midgame/latest.jsonl --phase state_extract
python scripts/eval_inspect.py evals/outputs/golden_midgame/latest.jsonl --diff  # state before vs after
```

**LLM-assisted qualitative review:**

After a `make eval` run, pass the JSONL to an LLM with:
> "Review this pipeline trace. Flag: (1) any extraction delta that looks narratively inconsistent with the narration phase, (2) any state_after that contradicts the player command, (3) retry counts above 0."

This is the primary qualitative signal. It is non-deterministic and should never gate CI.

---

## Makefile targets

```makefile
test:       ## Offline, mocked — runs Tier 1 fixtures as part of standard suite
    uv run pytest -q

eval:       ## Live server qualitative run — requires make dev to be running
    uv run python scripts/run_evals.py
```

---

## Files to create

| Path | Purpose |
|---|---|
| `tests/evals/fixtures/*.yaml` | Tier 1 fixture definitions |
| `tests/test_evals.py` | Parametrized pytest over fixtures dir |
| `scripts/run_evals.py` | Tier 2: curl live server, write JSONL output |
| `scripts/eval_inspect.py` | jq-style Python helper for JSONL inspection |
| `evals/outputs/` | Gitignored output dir for Tier 2 runs |

---

## Implementation order

1. Write `golden_midgame.yaml` — first fixture, most important.
2. Add `tests/test_evals.py` parametrized over `fixtures/` — should pass immediately with `_FakeLLM`.
3. Add remaining fixtures one scenario at a time.
4. Write `scripts/run_evals.py` — live server curl flow, JSONL output.
5. Write `scripts/eval_inspect.py` — optional convenience wrapper over jq.
