# Phase 5 — LLM judge + rubric

**Goal:** Build a single-call LLM judge that reads `events.jsonl` and a markdown
rubric, scores the run, and returns a `JudgeResult` consumable by the phase-4
report. Hand-author the default rubric.

**Prerequisites:** Phase 1, 2, 3, 4 complete.

**Estimated context:** ~25K tokens.

---

## Files to read first

- `ccya/plans/p3-inference/eval-harness.md` — overview
- `ccya/plans/p3-inference/eval-harness/04-report.md` — handoff state, including the duck-typed shape `generate_report` expects on `judge_result`
- `ccya/ccya/llm_client.py` lines 121-128, 231-258 — `_get_client` and `chat()` signature; you'll call it directly.
- `ccya/eval/runner.py` lines 1-80 — `RunResult` shape (already in your context after phase 3 if you wrote it; otherwise read just to confirm)

That's it.

---

## Design

The judge does ONE LLM call:

1. Read the events.jsonl produced by the runner.
2. Build a compact trace string (truncate to `eval_cfg.judge.max_input_chars`).
3. Send `[system=rubric.md, user=trace + structured-output schema instruction]` to the configured judge model (defaults to engine model from `config.yaml`).
4. Parse the JSON response into `JudgeResult`.
5. If a previous run exists for the same scenario AND its REPORT.md has a parseable judge score, set `previous_overall` so the report can flag a drop.

**Compact trace format** (the user message body sent to the judge):

```
TURN <n> — <input>
[scope] active=[...] skip=[...]
[rules] band=<band> skill=<skill> outcome=<one-line summary>
[narrate] <first 800 chars of narrative + ellipsis if longer>
[extract.scene] <first 300 chars of raw output>
[extract.state] <first 300 chars of raw output>
[extract.progress] <first 300 chars of raw output>
[applied] <one-line summary of applied delta>
[rejected] <list of rejected entries, if any>
---
```

This is intentionally NOT the full prompts (those are in the rubric's "what to
check" guidance, not the per-turn data) — token budget matters.

---

## Files to create

### 1. `evals/rubrics/default.md`

Hand-authored, human-readable, editable. Used as the system prompt for the judge.

```markdown
# ccya Eval Judge — Default Rubric

You are evaluating one run of an interactive narrative game. The game's engine
makes 5 LLM calls per turn:

1. **rules** — classify intent, decide if a skill check is needed, choose scope.
2. **narrate** — write the prose for this turn given the rules outcome.
3. **extract.scene** — extract scene-level changes (location, present_npcs, tags, summary).
4. **extract.state** — extract pc-level changes (inventory deltas, conditions).
5. **extract.progress** — extract longer-arc changes (quest progress, recent_events, compendium NPC bios).

You will see one TURN block per turn in the user message. Each block contains
the player input, the scope decision, the rules outcome, the narration, the
extractor outputs, and what was applied/rejected.

## What to evaluate

Score the run on each criterion below from 1 (worst) to 5 (best). Be a harsh
critic. Most well-functioning runs land at 3 or 4. A 5 means truly excellent
and a 1 means broken or absent.

### 1. extraction_consistency
Do the extractors emit deltas that match the narration? Examples of low scores:
- Narration says "you pay 50 credits" but extract.state has no inventory_remove.
- Narration introduces a new NPC but extract.scene.present_npcs doesn't include them.
- extract.progress invents a quest objective the narration didn't actually advance.

### 2. context_fidelity
Did each call have enough context, with no obviously missing fields?
- The rules call should know the player's stats, conditions, and current scene.
- The narrate call should know the rules band and recent turns.
- The extract calls should know the active scope and the narration to extract from.
Penalize when context is clearly missing (e.g. an extractor invents an NPC the
narration doesn't mention — likely missing the rendered narration).

### 3. context_economy
Was each call given only what it needed, or is there obvious bloat?
- Penalize repeating the entire chronicle in every system prompt.
- Penalize listing all 50 known NPCs when only 3 are in scene and the touch order
  list is short.
- Penalize unbounded recent_events growth across turns.

### 4. narrative_quality
Is the prose in service of the game?
- Specific, concrete sensory detail.
- Honors the dice — failed actions don't sneak through as successes.
- Honors the present NPCs — they act, react, or are visibly present.
- Plain language, no archaic or trope-heavy phrasing.
- Length appropriate to the action.

### 5. scope_correctness
Were the right domains active for each turn?
- A pure dialogue turn should NOT have inventory in active_domains.
- A combat turn SHOULD have pc_condition in active_domains.
- Skipped streams (skipped=true) should be skipped only when the narration truly
  contains no changes for that domain.

### 6. state_drift
Across the whole run, does the state evolve coherently?
- Inventory totals match what was used / acquired.
- Quest objectives complete in a sensible order.
- Recent_events doesn't accumulate stale duplicates.
- NPCs aren't created with conflicting bios on different turns.

## Output format

Return ONLY a JSON object matching exactly this schema. No prose before or after.
No markdown fences.

```json
{
  "overall_score": 3,
  "findings": [
    {"criterion": "extraction_consistency", "score": 4, "note": "One short sentence."},
    {"criterion": "context_fidelity",        "score": 3, "note": "One short sentence."},
    {"criterion": "context_economy",         "score": 3, "note": "One short sentence."},
    {"criterion": "narrative_quality",       "score": 4, "note": "One short sentence."},
    {"criterion": "scope_correctness",       "score": 3, "note": "One short sentence."},
    {"criterion": "state_drift",             "score": 3, "note": "One short sentence."}
  ],
  "comments": "Two to four sentences. Concrete, specific, actionable. Reference turn numbers."
}
```

`overall_score` is a 1-5 integer that is your overall verdict — NOT an average.
You may weight criteria as you see fit. Briefly justify the weighting in `comments`
when the overall score diverges from the criterion scores.
```

### 2. `ccya/eval/judge.py`

```python
"""Single LLM judge over events.jsonl.

One call, one rubric, structured JSON output. Truncates input to fit the
configured judge model's window. Parses tolerantly — one bad turn shouldn't kill
the eval.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ccya.eval.config import EvalConfig
from ccya.llm_client import chat, strip_thinking
from ccya.models import load_config


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class JudgeResult:
    overall_score: int
    findings: list[dict[str, Any]] = field(default_factory=list)
    comments: str = ""
    raw_response: str = ""
    rubric_path: str = ""
    model: str = ""
    previous_overall: int | None = None


# ---------------------------------------------------------------------------
# Trace builder
# ---------------------------------------------------------------------------


_NARRATE_TRUNC = 800
_EXTRACT_TRUNC = 300


def _summarize_applied(applied: dict[str, Any]) -> str:
    parts: list[str] = []
    for k in ("inventory_add", "inventory_remove", "inventory_update"):
        v = applied.get(k) or []
        if v:
            parts.append(f"{k}={len(v)}")
    for k in ("pc_condition_add", "pc_condition_remove"):
        v = applied.get(k) or []
        if v:
            parts.append(f"{k}={len(v)}")
    for k in ("quest_updates", "recent_events_add", "compendium_npc_update"):
        v = applied.get(k) or []
        if v:
            parts.append(f"{k}={len(v)}")
    if applied.get("location_change"):
        parts.append("location_change")
    if applied.get("scene_tags"):
        parts.append(f"scene_tags={applied['scene_tags']}")
    return ", ".join(parts) or "(no changes)"


def _summarize_rejected(rejected: list[Any]) -> str:
    if not rejected:
        return "(none)"
    return f"{len(rejected)} rejected: " + json.dumps(rejected[:3], default=str)[:200]


def _trim(s: str, n: int) -> str:
    s = s or ""
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def _scope_summary(rules_event: dict[str, Any] | None, rules_prompt: dict[str, Any]) -> str:
    """Scope is in the rules prompt's raw output — try to extract from there."""
    raw = rules_prompt.get("output", "")
    raw = strip_thinking(raw or "")
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            scope = data.get("scope") or {}
            active = scope.get("active_domains") or []
            skip = scope.get("skip_domains") or []
            return f"active={active} skip={skip}"
    except (json.JSONDecodeError, AttributeError):
        pass
    return "active=? skip=?"


def build_trace(events: list[dict[str, Any]], *, max_chars: int) -> str:
    """Build the compact trace string sent to the judge as the user message."""
    blocks: list[str] = []
    for ev in events:
        turn = ev.get("turn", "?")
        inp = ev.get("input", "")
        rules = ev.get("rules") or {}
        rules_prompt = ev.get("rules_prompt") or {}
        narrate_prompt = ev.get("narrate_prompt") or {}
        extraction = ev.get("extraction") or {}
        applied = ev.get("applied") or {}
        rejected = ev.get("rejected") or []

        scene = (extraction.get("scene") or {}).get("output", "")
        state = (extraction.get("state") or {}).get("output", "")
        progress = (extraction.get("progress") or {}).get("output", "")
        narration = narrate_prompt.get("output", "")

        scope_line = _scope_summary(rules, rules_prompt)
        rules_line = (
            f"band={rules.get('band', '—')} skill={rules.get('skill', '—')} "
            f"summary={(rules.get('outcome_summary') or '')[:140]}"
            if rules and rules.get("rolled")
            else f"intent_only verb={rules.get('intent_verb', '—') if rules else '—'}"
        )

        block = (
            f"TURN {turn} — {inp}\n"
            f"[scope] {scope_line}\n"
            f"[rules] {rules_line}\n"
            f"[narrate] {_trim(narration, _NARRATE_TRUNC)}\n"
            f"[extract.scene] {_trim(scene, _EXTRACT_TRUNC)}\n"
            f"[extract.state] {_trim(state, _EXTRACT_TRUNC)}\n"
            f"[extract.progress] {_trim(progress, _EXTRACT_TRUNC)}\n"
            f"[applied] {_summarize_applied(applied)}\n"
            f"[rejected] {_summarize_rejected(rejected)}\n"
            f"---\n"
        )
        blocks.append(block)

    full = "\n".join(blocks)
    if len(full) <= max_chars:
        return full
    head_keep = int(max_chars * 0.6)
    tail_keep = max_chars - head_keep - 80
    return (
        full[:head_keep]
        + "\n\n[... trace truncated to fit judge window ...]\n\n"
        + full[-tail_keep:]
    )


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_judge_response(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction from a judge response.

    Strips think tags, finds the outermost JSON object, returns the parsed dict.
    Raises ValueError on unrecoverable output.
    """
    s = strip_thinking(raw or "")
    s = s.strip()
    if s.startswith("```"):
        # markdown fence; strip first and last line
        s = "\n".join(s.splitlines()[1:-1])
    m = _JSON_OBJ_RE.search(s)
    if m is None:
        raise ValueError("no JSON object found in judge response")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"judge JSON parse failed: {exc}") from exc


def _coerce_score(v: Any) -> int:
    try:
        n = int(round(float(v)))
    except (TypeError, ValueError):
        return 0
    return max(1, min(5, n))


# ---------------------------------------------------------------------------
# Previous-run lookup (for previous_overall)
# ---------------------------------------------------------------------------


_OVERALL_RE = re.compile(r"\*\*Overall:\*\*\s*(\d+)\s*/\s*5", re.MULTILINE)


def _lookup_previous_overall(prev_report_path: Path) -> int | None:
    if not prev_report_path.exists():
        return None
    txt = prev_report_path.read_text()
    m = _OVERALL_RE.search(txt)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def run_judge(
    events_path: Path,
    *,
    eval_cfg: EvalConfig,
    previous_report_path: Path | None = None,
    game_config_path: Path | None = None,
) -> JudgeResult:
    """Read events.jsonl, send to judge, return JudgeResult.

    Honors MOCK_MODE via llm_client (returns canned response — score will be
    parsed from the mock and JudgeResult will have overall_score=0).
    """
    rubric_path = Path(eval_cfg.judge.rubric_path)
    if not rubric_path.is_absolute():
        rubric_path = REPO_ROOT / rubric_path
    if not rubric_path.exists():
        raise FileNotFoundError(f"rubric not found: {rubric_path}")
    rubric_text = rubric_path.read_text()

    cfg_path = game_config_path or (REPO_ROOT / "config.yaml")
    game_cfg = load_config(cfg_path)
    llm = game_cfg.get("llm", {})
    host = str(llm.get("host", "http://localhost:8080/v1"))
    judge_model = eval_cfg.judge.model or str(llm.get("model", ""))
    if not judge_model:
        raise ValueError("judge model not set (eval_cfg.judge.model is null AND game config llm.model is empty)")

    events_lines = events_path.read_text().splitlines() if events_path.exists() else []
    events = [json.loads(line) for line in events_lines if line.strip()]
    trace = build_trace(events, max_chars=eval_cfg.judge.max_input_chars)

    messages = [
        {"role": "system", "content": rubric_text},
        {"role": "user", "content": trace},
    ]

    resp = await chat(
        host=host,
        model=judge_model,
        messages=messages,
        temperature=eval_cfg.judge.temperature,
    )
    raw = resp.get("response", "") or ""

    overall = 0
    findings: list[dict[str, Any]] = []
    comments = ""
    try:
        parsed = parse_judge_response(raw)
        overall = _coerce_score(parsed.get("overall_score", 0))
        for f in parsed.get("findings") or []:
            if not isinstance(f, dict):
                continue
            findings.append(
                {
                    "criterion": str(f.get("criterion", "")),
                    "score": _coerce_score(f.get("score", 0)),
                    "note": str(f.get("note", "")),
                }
            )
        comments = str(parsed.get("comments", ""))
    except ValueError as exc:
        comments = f"(judge response could not be parsed: {exc})"

    previous_overall = (
        _lookup_previous_overall(previous_report_path) if previous_report_path else None
    )

    return JudgeResult(
        overall_score=overall,
        findings=findings,
        comments=comments,
        raw_response=raw,
        rubric_path=str(rubric_path),
        model=judge_model,
        previous_overall=previous_overall,
    )
```

### 3. Update `ccya/eval/__init__.py`

Add judge exports:

```python
"""ccya eval harness.

Tier 2 of the eval system: live-LLM in-process driver, single judge, single scenario.
See ccya/plans/p3-inference/eval-harness.md.
"""

from ccya.eval.config import EvalConfig, load_eval_config
from ccya.eval.judge import JudgeResult, build_trace, parse_judge_response, run_judge
from ccya.eval.report import generate_report
from ccya.eval.runner import (
    RunResult,
    TurnRecord,
    find_previous_run,
    load_run_result,
    run_scenario,
)
from ccya.eval.scenario import Scenario, Turn, discover_scenarios, load_scenario

__all__ = [
    "EvalConfig",
    "JudgeResult",
    "RunResult",
    "Scenario",
    "Turn",
    "TurnRecord",
    "build_trace",
    "discover_scenarios",
    "find_previous_run",
    "generate_report",
    "load_eval_config",
    "load_run_result",
    "load_scenario",
    "parse_judge_response",
    "run_judge",
    "run_scenario",
]
```

---

## Verification

```bash
# 1. Imports clean
uv run python -c "
from ccya.eval import run_judge, JudgeResult, build_trace, parse_judge_response
print('judge imports OK')
"

# 2. Rubric file exists and is parseable
test -f evals/rubrics/default.md
wc -l evals/rubrics/default.md

# 3. parse_judge_response handles a typical response
uv run python -c "
from ccya.eval.judge import parse_judge_response
sample = '''
Some preamble.

\`\`\`json
{\"overall_score\": 3, \"findings\": [{\"criterion\": \"x\", \"score\": 4, \"note\": \"ok\"}], \"comments\": \"fine\"}
\`\`\`
'''
out = parse_judge_response(sample)
assert out['overall_score'] == 3
assert out['findings'][0]['note'] == 'ok'
print('parse OK:', out)
"

# 4. parse_judge_response handles raw JSON without fences
uv run python -c "
from ccya.eval.judge import parse_judge_response
out = parse_judge_response('{\"overall_score\": 5, \"findings\": [], \"comments\": \"\"}')
assert out['overall_score'] == 5
print('raw parse OK')
"

# 5. parse_judge_response strips <think> tags
uv run python -c "
from ccya.eval.judge import parse_judge_response
s = '<think>internal chatter</think>{\"overall_score\": 4, \"findings\": [], \"comments\": \"\"}'
out = parse_judge_response(s)
assert out['overall_score'] == 4
print('think-strip OK')
"

# 6. End-to-end smoke (MOCK_MODE) — runner + judge + report
mkdir -p evals/scenarios
cat > evals/scenarios/_smoke.py <<'PY'
from ccya.eval.scenario import Scenario, Turn

scenario = Scenario(
    id="_smoke",
    pack="eval-pack",
    description="judge smoke",
    turns=[
        Turn(input="Look around the inn.", phase="dialogue"),
        Turn(input="Ask Halden about the contract.", phase="dialogue"),
    ],
)
PY

MOCK_MODE=1 uv run python -c "
import asyncio
from pathlib import Path
from ccya.eval.config import load_eval_config
from ccya.eval.scenario import load_scenario
from ccya.eval.runner import run_scenario, REPO_ROOT
from ccya.eval.judge import run_judge
from ccya.eval.report import generate_report

async def main():
    sc = load_scenario('evals/scenarios/_smoke.py')
    cfg = load_eval_config()
    rr = await run_scenario(sc, eval_cfg=cfg, packs_dir=REPO_ROOT / 'evals' / 'packs')
    judge = await run_judge(Path(rr.events_jsonl_path), eval_cfg=cfg)
    print('judge.overall_score =', judge.overall_score)
    print('judge.raw_response[:300] =', judge.raw_response[:300])
    report_path = generate_report(rr, eval_cfg=cfg, judge_result=judge)
    print('report written:', report_path)
    print('--- REPORT.md head ---')
    print(report_path.read_text()[:1800])

asyncio.run(main())
"

# 7. Cleanup
rm evals/scenarios/_smoke.py

# 8. Existing tests still pass
uv run pytest -q tests/test_engine_smoke.py
```

In step 6 the judge call goes through MOCK_MODE — the mock returns a non-JSON
narrative string, so `parse_judge_response` will fail and `judge.overall_score`
will be 0 with `comments` containing the parse error. That's expected for the
mock. The point of step 6 is to verify the wiring (no exceptions, report
includes a Judge block).

For real-LLM verification you'll have to wait for phase 6 (CLI + Makefile) and
running `make eval` against the live mlx_lm server.

---

## STOP HERE

Phase 5 is complete. Verify all checks pass, then stop and start a new chat with
`eval-harness/06-cli-and-makefile.md`.

### Handoff to phase 6

State after this phase:

- `ccya/eval/judge.py` exists; `run_judge(events_path, eval_cfg=..., previous_report_path=...)` returns a `JudgeResult`.
- `evals/rubrics/default.md` is the editable system prompt.
- `parse_judge_response` tolerates `<think>` tags, markdown fences, leading prose.
- The judge consumes ~30K chars max of trace by default (set in `evals/config.yaml`); `build_trace` truncates with a head/tail split when over budget.
- The end-to-end pipeline (runner → judge → report) works in MOCK_MODE.
- Real-LLM judge calls are blocked on phase 6 wiring (Makefile + CLI).

Phase 6 wires the CLI (`python -m ccya.eval`) and Makefile targets. It also creates the actual `full_cycle.py` scenario.
