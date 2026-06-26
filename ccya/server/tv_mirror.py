"""Stream registry for turn viewer — single source of truth for pipeline topology.

All dot-paths are verified against live events.jsonl output.
Import _STREAMS and _get_nested in tv.py. Do not reference stream names directly there.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast


@dataclass(frozen=True)
class StreamDescriptor:
    key: str
    label: str
    stage_css: str
    # dot-path to the metrics blob (tokens_in, tokens_out, latency)
    metrics_path: str
    # dot-path to the prompt/output blob (rendered_system, rendered_user, output)
    # if None, same as metrics_path
    prompt_path: str | None = None
    # subkey within the prompt blob for the output value (None = use whole blob minus meta)
    output_subkey: str | None = "output"
    # True  → output is a prose string  → _tv_narration_lines
    # False → output is a dict (or JSON string to parse) → _tv_dict_to_lines
    is_text_output: bool = False
    # True  → output is a JSON string that must be json.loads'd before rendering
    output_is_json_string: bool = False
    # key within metrics blob for latency (rules uses total_ms; extraction streams use ms)
    ms_key: str = "ms"
    # upstream stream keys that feed this stream — drives connector generation
    inputs: list[str] = field(default_factory=list)
    # when True: show '—' for tokens when stream is skipped (extraction streams)
    skip_token_display: bool = False


_STREAMS: list[StreamDescriptor] = [
    StreamDescriptor(
        key="ruling",
        label="Ruling",
        stage_css="ruling",
        metrics_path="ruling",
        prompt_path="ruling_prompt",
        output_subkey="output",
        is_text_output=False,
        output_is_json_string=True,  # ruling_prompt.output is a serialized JSON string
        ms_key="total_ms",
        inputs=[],
    ),
    StreamDescriptor(
        key="narrate",
        label="narrate",
        stage_css="narrate",
        metrics_path="narrate",          # metrics only (total_ms, tokens_in, tokens_out)
        prompt_path="narrate_prompt",    # prompt + output live here
        output_subkey="output",
        is_text_output=True,             # narrate_prompt.output is prose
        ms_key="total_ms",
        inputs=["ruling"],
    ),
    StreamDescriptor(
        key="scene",
        label="scene",
        stage_css="scene",
        metrics_path="extraction.scene",
        prompt_path="extraction.scene",
        output_subkey="output",
        is_text_output=False,
        ms_key="ms",
        inputs=["ruling", "narrate"],
        skip_token_display=True,
    ),
    StreamDescriptor(
        key="state",
        label="state",
        stage_css="state",
        metrics_path="extraction.state",
        prompt_path="extraction.state",
        output_subkey="output",
        is_text_output=False,
        ms_key="ms",
        inputs=["ruling", "narrate", "scene"],
        skip_token_display=True,
    ),
    StreamDescriptor(
        key="record",
        label="Record",
        stage_css="record",
        metrics_path="extraction.record",
        prompt_path="extraction.record",
        output_subkey="output",
        is_text_output=False,
        ms_key="ms",
        inputs=["ruling", "narrate", "scene", "state"],
        skip_token_display=True,
    ),
]

# O(1) lookup by key — used by tv.py connector generation
STREAM_BY_KEY: dict[str, StreamDescriptor] = {s.key: s for s in _STREAMS}


def _get_nested(d: dict[str, Any], path: str) -> dict[str, Any] | str | list[Any] | None:
    """Resolve a dot-separated path into a nested dict.

    Returns None if any key is missing or an intermediate value is not a dict.
    """
    cur: object = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cast("dict[str, Any] | str | list[Any] | None", cur)
