"""Engine package: turn pipeline, seed generation, and configuration."""

from ccya.engine.compactor import maybe_compact
from ccya.engine.config import (
    EngineConfig,
    build_engine_config,
    is_turn_in_progress,
)
from ccya.engine.seed import generate_seed
from ccya.engine.pack_gen import generate_pack
from ccya.engine.changes import format_change_lines
from ccya.engine.turn import run_turn, warmup

# Internal helpers re-exported for tests
from ccya.engine.config import _build_jinja_env
from ccya.engine.narrate import _narrate_messages
from ccya.engine.extraction import (
    _extract_scene_messages,
    _extract_state_messages,
    _extract_progress_messages,
    _scene_npc_roster,
)
from ccya.engine.rules import _rules_messages

from ccya.engine.turn import _validate

# LLM client functions re-exported for test patching (tests do
# `import ccya.engine as eng; eng.llm_chat_stream = ...`)
from ccya.llm_client import chat as llm_chat
from ccya.llm_client import chat_stream as llm_chat_stream

__all__ = [
    "EngineConfig",
    "build_engine_config",
    "_build_jinja_env",

    "_extract_progress_messages",
    "_extract_scene_messages",
    "_extract_state_messages",
    "_narrate_messages",
    "_rules_messages",
    "_scene_npc_roster",
    "_validate",
    "format_change_lines",
    "generate_pack",
    "generate_seed",
    "is_turn_in_progress",
    "llm_chat",
    "llm_chat_stream",
    "maybe_compact",
    "run_turn",
    "warmup",
]
