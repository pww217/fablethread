"""Turn engine: two-call pipeline (narrate + extract) with reliability measures."""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from ccya.models import ExtractResult, StateDelta, TurnResult
from ccya.ollama import chat as ollama_chat, chat_stream as ollama_chat_stream
from ccya.state import (
    append_chronicle,
    append_event,
    apply_delta,
    load_state,
    save_state,
)

# ---------------------------------------------------------------------------
# Per-save turn in-flight guard (async-safe via EventLock)
# ---------------------------------------------------------------------------

class _EventLock:
    """Per-key async lock dict for turn-in-flight guard."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    async def acquire(self, key: str) -> None:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        await self._locks[key].acquire()

    async def release(self, key: str) -> None:
        lock = self._locks.get(key)
        if lock and lock.locked():
            lock.release()


_inflight: _EventLock = _EventLock()


def is_turn_in_progress(save_dir: str) -> bool:
    """Check if a turn is currently running for the given save."""
    lock = _inflight._locks.get(save_dir)
    return lock is not None and lock.locked()


@dataclass
class EngineConfig:
    ollama_host: str = "http://localhost:11434"
    model: str = "gemma3:27b"
    keep_alive: str = "60m"
    num_ctx: int = 32768
    request_timeout_s: int = 180
    narrate_temperature: float = 0.8
    extract_temperature: float = 0.0
    max_extract_retries: int = 1
    window_turns: int = 6
    chronicle_prefix_budget_tokens: int = 1500
    established_facts_max: int = 10


def _build_jinja_env(template_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _narrate_system_prompt(env: Environment, state: dict, user_input: str) -> str:
    t = env.get_template("narrate.j2")
    return t.render(state=state, user_input=user_input)


def _extract_system_prompt(env: Environment, narrative: str) -> str:
    schema = ExtractResult.model_json_schema()
    t = env.get_template("extract.j2")
    return t.render(schema_json=json.dumps(schema, indent=2), narrative=narrative)


# ---------------------------------------------------------------------------
# JSON extraction helpers
# ---------------------------------------------------------------------------

def _strip_thinking(text: str) -> str:
    """Remove <thinking>...</thinking> block, return rest."""
    m = re.search(r"<thinking>\s*.*?\s*</thinking>", text, re.DOTALL)
    if m:
        return (text[:m.start()] + text[m.end():]).strip()
    return text.strip()


def _find_json(text: str) -> dict | None:
    """Try to find and parse a JSON object in text. Unwraps ExtractResult if present."""
    text = text.strip()

    def _try_parse(t: str) -> dict | None:
        try:
            return json.loads(t)
        except (json.JSONDecodeError, ValueError):
            return None

    # Direct parse
    j = _try_parse(text)
    if j is not None:
        return _maybe_unwrap(j)

    # Fenced code block
    if "```" in text:
        for part in text.split("```"):
            p = part.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            result = _try_parse(p)
            if result is not None:
                return _maybe_unwrap(result)

    # Brace search
    b = text.find("{")
    if b >= 0:
        r = text.rfind("}")
        if r > b:
            result = _try_parse(text[b:r + 1])
            if result is not None:
                return _maybe_unwrap(result)
    return None


def _maybe_unwrap(j: dict) -> dict:
    """If JSON is an ExtractResult, extract state_delta. Pass through StateDelta as-is."""
    if "state_delta" in j and "actions" in j:
        return j["state_delta"]
    return j


async def _collect_narrate(stream: Any) -> tuple[str, float, float]:
    """Collect streaming tokens, return (text, first_token_ms, total_ms)."""
    # Handle both real async generators (has __aiter__) and mocked async functions (coroutines)
    if asyncio.iscoroutine(stream):
        stream = await stream
    chunks: list[str] = []
    first_ms = 0.0
    start = asyncio.get_event_loop().time()
    try:
        async for chunk in stream:
            if not chunks:
                first_ms = (asyncio.get_event_loop().time() - start) * 1000
            chunks.append(chunk)
    except Exception:
        pass
    elapsed = (asyncio.get_event_loop().time() - start) * 1000
    return "".join(chunks), first_ms, elapsed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_turn(
    save_dir: Path,
    user_input: str,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
) -> TurnResult:
    """Execute one turn: narrate (stream) + extract (structured JSON)."""
    if config is None:
        config = EngineConfig()

    template_dir = template_dir or str(Path(__file__).parent / "prompts")
    env = _build_jinja_env(template_dir)

    trace_id = uuid.uuid4().hex[:8]
    errors: list[dict] = []
    metrics: dict = {}
    state = load_state(save_dir)
    narrative = ""
    delta: StateDelta | None = None
    actions: list[str] = []
    scene_tags: list[str] = []
    established_facts: list[str] = []

    try:
        await _inflight.acquire(str(save_dir))

        # === Call 1: Narrate ===
        narr_prompt = _narrate_system_prompt(env, state, user_input)
        narr_stream = ollama_chat_stream(
            config.ollama_host, config.model,
            [{"role": "system", "content": narr_prompt}],
            temperature=config.narrate_temperature,
            keep_alive=config.keep_alive,
            num_ctx=config.num_ctx,
            timeout=float(config.request_timeout_s),
        )
        narrative, first_ms, narr_ms = await _collect_narrate(narr_stream)

        narr_metrics = {"first_token_ms": round(first_ms, 1), "total_ms": round(narr_ms, 1)}

        # === Call 2: Extract ===
        ext_prompt = _extract_system_prompt(env, narrative)
        ext_messages: list[dict] = [{"role": "system", "content": ext_prompt}]

        t2 = asyncio.get_event_loop().time()
        retries = 0
        parse_error: str = ""

        for attempt in range(1 + config.max_extract_retries):
            try:
                result = await ollama_chat(
                    config.ollama_host, config.model,
                    ext_messages,
                    stream=False,
                    format=ExtractResult.model_json_schema(),
                    temperature=config.extract_temperature,
                    keep_alive=config.keep_alive,
                    num_ctx=config.num_ctx,
                    timeout=float(config.request_timeout_s),
                )
                raw = result.get("response", "") if isinstance(result, dict) else ""
                ext_usage = result.get("usage", {}) if isinstance(result, dict) else {}
                cleaned = _strip_thinking(raw)
                j = _find_json(cleaned)
                if j is not None:
                    delta = StateDelta(**j)
                    retries = attempt
                    break
                raise ValueError("No JSON found in response")
            except Exception as exc:
                parse_error = str(exc)
                if attempt < config.max_extract_retries:
                    fb = (
                        f"Your previous output failed to parse: {parse_error[:200]}."
                        f" Re-emit JSON matching the schema. No prose outside <thinking>."
                    )
                    ext_messages.append({"role": "user", "content": fb})
                    retries = attempt + 1
                else:
                    errors.append({"trace_id": trace_id, "message": parse_error})

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        ext_metrics = {"retries": retries, "total_ms": round(ext_ms, 1), "tokens_in": ext_usage.get("prompt_tokens", 0), "tokens_out": ext_usage.get("total_tokens", 0)}
        metrics = {"narrate": {**narr_metrics, "tokens_in": ext_metrics["tokens_in"], "tokens_out": ext_metrics["tokens_out"]}, "extract": ext_metrics}

        # === Validate & apply delta ===
        applied: dict = {}
        rejected: list[dict] = []

        if delta is not None:
            rejected = _validate(state, delta)
            if rejected:
                errors.append({"trace_id": trace_id, "message": f"Delta validation failed ({len(rejected)} rejection(s))."})
                narrative += "\n\n*That action didn't resolve as expected.*"
            else:
                state = apply_delta(state, delta, established_facts_max=config.established_facts_max)
                actions = getattr(delta, "actions", [])
                scene_tags = getattr(delta, "scene_tags", [])
                established_facts = list(getattr(delta, "established_facts", []))
                applied = delta.model_dump(exclude_none=True)

        # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        event = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": user_input,
            "narrative": narrative,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": scene_tags,
            "established_facts": established_facts,
            "narrate": narr_metrics,
            "extract": metrics["extract"],
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(save_dir, narrative.strip())

        return TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=scene_tags,
            established_facts=established_facts,
            metrics=metrics,
            errors=errors,
        )

    except Exception as exc:
        errors.append({"trace_id": trace_id, "message": str(exc)})
        if not narrative:
            narrative = f"*An error occurred. Trace `{trace_id}` — try rephrasing.*"
        return TurnResult(
            turn=state.get("meta", {}).get("turn", 0),
            trace_id=trace_id,
            narrative=narrative,
            state_delta={},
            errors=errors,
            metrics=metrics,
        )
    finally:
        await _inflight.release(str(save_dir))


def _validate(state: dict, delta: StateDelta) -> list[dict]:
    """Strict delta validator. Returns list of rejection dicts."""
    rejections: list[dict] = []

    existing_inv = {item.get("id") for item in state.get("inventory", [])}
    for rid in delta.inventory_remove:
        if rid not in existing_inv:
            rejections.append({"field": "inventory_remove", "value": rid,
                               "reason": f"Inventory item '{rid}' does not exist"})

    existing_quests = {q.get("id") for q in state.get("quests", [])}
    for qu in delta.quest_updates:
        if qu.id not in existing_quests:
            rejections.append({"field": "quest_updates", "value": qu.id,
                               "reason": f"Quest '{qu.id}' does not exist in state"})

    return rejections


async def warmup(config: EngineConfig) -> None:
    """Silent 1-token chat call to pre-load the model."""
    try:
        await ollama_chat(
            config.ollama_host, config.model,
            [{"role": "user", "content": "ok"}],
            temperature=0.0,
            keep_alive=config.keep_alive, num_ctx=config.num_ctx,
            timeout=30.0,
        )
    except Exception:
        pass
