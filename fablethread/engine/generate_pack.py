"""generate_pack.py — LLM-driven pack generation from player-supplied world brief."""
from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

import yaml

from fablethread.engine.config import EngineConfig, _build_jinja_env, _render
from fablethread.llm_client import chat_with_config as llm_chat
from fablethread.pack import Pack, PackFiles, PackManifest, ScenarioBrief, validate_pack

_log = logging.getLogger(__name__)

_NAME_RE = re.compile(r"[^\x00-\x7F]")


def _strip_non_ascii(text: str) -> str:
    if not text:
        return text
    result = _NAME_RE.sub("", text).strip()
    return result


def _sanitize_brief(brief: ScenarioBrief) -> ScenarioBrief:
    """Strip non-ASCII from all name fields as a safety net."""
    brief.world_name = _strip_non_ascii(brief.world_name)
    for f in brief.factions:
        f.name = _strip_non_ascii(f.name)
    return brief


async def generate_pack_from_brief(
    inputs: dict[str, Any],
    packs_root: Path,
    config: EngineConfig,
    template_dir: str,
    trace_id: str,
    max_retries: int = 1,
) -> AsyncIterator[dict[str, Any]]:
    """
    Generate an ephemeral pack from a player-supplied world brief.

    Yields server-sent event dicts: phase, pack_ready, or generation_error.
    Writes the result to packs_root / 'generated' / <uuid>/.
    """
    pack_id = f"generated/{uuid.uuid4().hex[:12]}"
    out_dir = packs_root / "generated" / pack_id.split("/")[1]
    out_dir.mkdir(parents=True, exist_ok=True)

    concept = inputs.get("concept", "")
    world_name = inputs.get("world_name", "")
    tone_tags = inputs.get("tone_tags", [])
    _log.info(
        "generate_pack_from_brief start concept_len=%d tone_tags=%d world_name=%s",
        len(concept), len(tone_tags), world_name or "(none)",
        extra={"trace_id": trace_id, "pack": pack_id},
    )

    parse_error = ""
    for attempt in range(1 + max_retries):
        try:
            yield {"type": "phase", "label": "Generating scenario…"}

            env = _build_jinja_env(template_dir)

            concept = inputs.get("concept", "")
            world_name = inputs.get("world_name", "")
            tone_tags = inputs.get("tone_tags", [])
            mood_note = inputs.get("mood_note", "")
            world_rules = inputs.get("world_rules", [])

            system_prompt = _render(
                env,
                "generate_pack_system_wb.j2",
                {},
            )
            user_prompt = _render(
                env,
                "generate_pack_user_wb.j2",
                {
                    "concept": concept,
                    "world_name": world_name,
                    "tone_tags": tone_tags,
                    "mood_note": mood_note,
                    "world_rules": world_rules,
                },
            )

            _log.debug(
                "generate_pack_from_brief LLM call",
                extra={"trace_id": trace_id, "pack": pack_id},
            )

            response_text = await llm_chat(
                config,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.pack_generation_temperature,
                top_p=config.pack_generation_top_p,
                timeout=300.0,
                num_ctx=config.num_ctx,
                enable_thinking=False,
                reasoning_effort="none",
                thinking_budget=0,
            )

            raw = response_text.content

            yield {"type": "phase", "label": "Parsing world…"}

            # Parse YAML from LLM response — the pack-gen prompt instructs YAML output.
            # Strip markdown fences if present.
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[1:])
            if cleaned.endswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[:-1])

            scenario_data = yaml.safe_load(cleaned)
            if not isinstance(scenario_data, dict):
                raise ValueError(f"Expected YAML dict, got {type(scenario_data).__name__}")

            brief = ScenarioBrief(**scenario_data)
            brief = _sanitize_brief(brief)

            # Validate before writing to disk
            temp_pack = Pack(manifest=PackManifest(id=pack_id, name=brief.world_name or "Generated World"), scenario=brief)
            validate_pack(temp_pack, pack_id=pack_id)

            # Write scenario.yaml
            (out_dir / "scenario.yaml").write_text(
                yaml.dump(brief.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            # Derive pack name: LLM world_name > user input > concept-derived > fallback
            pack_name = brief.world_name or world_name
            if not pack_name and concept:
                words = concept.split()
                candidate = " ".join(words[:5]).title()
                # Strip leading articles/prepositions
                while candidate.split() and candidate.split()[0].lower() in ("a", "an", "the", "of", "and", "in", "on", "to"):
                    candidate = " ".join(candidate.split()[1:]) if len(candidate.split()) > 1 else candidate
                # Strip trailing articles/prepositions
                trailing = {"the", "a", "an", "of", "and", "or", "for", "in", "on", "at", "to", "by"}
                while candidate.split() and candidate.split()[-1].lower() in trailing:
                    candidate = " ".join(candidate.rsplit(None, 1)[0]) if len(candidate.split()) > 1 else candidate
                pack_name = candidate
            pack_name = pack_name or "Custom World"
            manifest = PackManifest(
                id=pack_id,
                name=pack_name,
                description=brief.description or "",
                tone_tags=tone_tags,
                files=PackFiles(world="world.md", scenario="scenario.yaml"),
                name_locales=brief.name_locales,
                use_male_only_names=False,
            )
            (out_dir / "pack.yaml").write_text(
                yaml.dump(manifest.model_dump(), allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            _log.info(
                "generate_pack_from_brief complete factions=%d world_name=%s",
                len(brief.factions), brief.world_name or "(none)",
                extra={"trace_id": trace_id, "pack": pack_id},
            )

            yield {"type": "pack_ready", "pack_id": pack_id}
            return

        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "generate_pack_from_brief failed (attempt %d/%d): %s",
                attempt + 1,
                1 + max_retries,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < max_retries:
                _log.info(
                    "generate_pack_from_brief retrying",
                    extra={"trace_id": trace_id, "attempt": attempt + 2},
                )

    _log.warning(
        "generate_pack_from_brief failed after all attempts",
        extra={"trace_id": trace_id},
    )
    yield {"type": "generation_error", "error": parse_error}
