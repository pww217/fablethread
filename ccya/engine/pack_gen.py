"""World pack generation from player concept (WorldBrief -> ScenarioBrief -> Pack on disk)."""

from __future__ import annotations

import logging
import random
import re
import uuid
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.names import generate_name_pool
from ccya.llm_client import chat as llm_chat, strip_thinking, trim_messages
from ccya.pack import Pack, PackManifest, ScenarioBrief, WorldBrief, GeneratedPackMeta, load_pack

_log = logging.getLogger("ccya.engine")


def _slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s[:40] or "custom-world"


def _convert_tuples_to_lists(obj: Any) -> Any:
    """Recursively convert tuples to lists for YAML compatibility.

    yaml.dump serializes Python tuples with !!python/tuple which
    yaml.safe_load cannot reconstruct. Convert to lists before writing.
    """
    if isinstance(obj, dict):
        return {k: _convert_tuples_to_lists(v) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return [_convert_tuples_to_lists(item) for item in obj]
    if isinstance(obj, list):
        return [_convert_tuples_to_lists(item) for item in obj]
    return obj


def _build_generate_pack_messages(
    env: Environment,
    brief: WorldBrief,
    name_pool: dict[str, list[str]],
    name_seed: int,
) -> list[dict[str, str]]:
    ctx = {
        "brief": brief,
        "name_pool": name_pool,
        "name_seed": name_seed,
    }
    system_text = _render(env, "generate_pack_system.j2", ctx)
    user_text = _render(env, "generate_pack_user.j2", ctx)
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


async def generate_pack(
    brief: WorldBrief,
    config: EngineConfig,
    packs_dir: Path,
    *,
    template_dir: str | None = None,
    max_retries: int = 2,
) -> Pack:
    """Generate a complete world pack from a WorldBrief and write it to packs/custom/.

    Returns the loaded Pack ready for generate_seed().
    """
    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    # Bootstrap name pool using default locales until scenario provides them
    default_locales = [{"locale": "en_US", "weight": 1.0}]
    name_seed = random.randint(10_000_000, 99_999_999)
    name_pool = generate_name_pool(default_locales)

    messages = _build_generate_pack_messages(env, brief, name_pool, name_seed)
    messages, _, _ = trim_messages(messages, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(0, "generate_pack", messages)

    parse_error = ""
    for attempt in range(1 + max_retries):
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"generate_pack_request_attempt_{attempt}",
                messages=messages,
                max_chars=config.log_llm_io_max_chars,
            )
        try:
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                temperature=config.generate_seed_temperature,
                timeout=float(config.request_timeout_s),
            )
        except Exception as exc:
            _log.error("generate_pack: LLM error: %s", exc, extra={"trace_id": trace_id})
            raise

        raw = result.get("response", "") if isinstance(result, dict) else ""
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"generate_pack_response_attempt_{attempt}",
                response=raw,
                max_chars=config.log_llm_io_max_chars,
            )

        cleaned = strip_thinking(raw)
        j = _find_json(cleaned)
        if j is None:
            parse_error = "No JSON found in generate_pack response"
            _log.warning("generate_pack failed (attempt %d): %s", attempt + 1, parse_error, extra={"trace_id": trace_id})
            if attempt < max_retries:
                messages.append({"role": "user", "content": f"Output failed to parse: {parse_error}. Re-emit valid ScenarioBrief JSON only."})
            continue

        try:
            # Inject name_seed if LLM omitted it
            if "name_seed" not in j:
                j["name_seed"] = name_seed
            scenario = ScenarioBrief(**j)
        except Exception as exc:
            parse_error = str(exc)
            _log.warning("generate_pack validation failed (attempt %d): %s", attempt + 1, parse_error, extra={"trace_id": trace_id})
            if attempt < max_retries:
                messages.append({"role": "user", "content": f"ScenarioBrief validation failed: {parse_error[:300]}. Re-emit corrected JSON."})
            continue

        # Write pack to disk
        slug = _slugify(brief.concept) + "-" + uuid.uuid4().hex[:6]
        pack_dir = packs_dir / "custom" / slug
        pack_dir.mkdir(parents=True, exist_ok=True)

        manifest = PackManifest(
            id=slug,
            name=brief.concept.title(),
            description=brief.concept,
            genre=brief.tone or "",
            tone_tags=[],
        )
        generated_meta = GeneratedPackMeta(
            generated=True,
            world_brief_concept=brief.concept,
        )
        pack_yaml_data = {
            **manifest.model_dump(exclude_none=True),
            **generated_meta.model_dump(exclude_none=True),
        }
        with open(pack_dir / "pack.yaml", "w") as f:
            yaml.dump(pack_yaml_data, f, allow_unicode=True, sort_keys=False)

        scenario_dict = _convert_tuples_to_lists(scenario.model_dump(exclude_none=True))
        with open(pack_dir / "scenario.yaml", "w") as f:
            yaml.dump(scenario_dict, f, allow_unicode=True, sort_keys=False)

        _log.info(
            "generate_pack: wrote pack %s",
            slug,
            extra={"trace_id": trace_id, "pack": slug},
        )

        return load_pack(slug, packs_dir)

    raise RuntimeError(f"generate_pack failed after {1 + max_retries} attempts — trace {trace_id}")
