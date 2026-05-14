"""Tests for momentum event emission in events.jsonl."""

import json
import tempfile
from pathlib import Path

from ccya.engine import EngineConfig
from ccya.state import save_state
from tests.test_engine_smoke import _FakeLLM, _make_state, _run

def _make_save_dir() -> Path:
    return Path(tempfile.mkdtemp())

_RULES_WITH_ROLL = json.dumps({
    "intent": "player action",
    "intent_verb": "attack",
    "target": "the guard",
    "stakes": "getting past",
    "check": {
        "required": True,
        "skill": "strength",
        "difficulty": "hard",
        "stat_mod": 0,
        "diff_mod": 0,
        "cond_mod": 0,
    },
    "outcome": {
        "rolled": True,
        "skill": "strength",
        "difficulty": "hard",
        "dice": [3, 4],
        "stat_mod": 0,
        "diff_mod": 0,
        "cond_mod": 0,
        "final_total": 7,
        "band": "success",
        "directive": "You get past but take a hit.",
    },
})

_RULES_NO_ROLL = json.dumps({
    "intent": "player action",
    "intent_verb": "act",
    "target": "",
    "stakes": "",
    "check": {"required": False},
})


class TestMomentumEventEmission:
    """Momentum fields should appear in events.jsonl rules sub-object when a roll occurs."""

    async def test_momentum_fields_in_rules_event(self) -> None:
        save_dir = _make_save_dir()
        state = _make_state()
        save_state(save_dir, state)

        fake = _FakeLLM(rules_response=_RULES_WITH_ROLL)
        with fake:
            await _run(save_dir, "attack the guard", config=EngineConfig())

        events = (save_dir / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(events[0])
        rules = event["rules"]
        assert "momentum_before" in rules
        assert "momentum_after" in rules
        assert "momentum_delta" in rules
        assert rules["momentum_delta"] != 0

    async def test_no_momentum_fields_when_no_roll(self) -> None:
        save_dir = _make_save_dir()
        state = _make_state()
        save_state(save_dir, state)

        fake = _FakeLLM(rules_response=_RULES_NO_ROLL)
        with fake:
            await _run(save_dir, "look around", config=EngineConfig())

        events = (save_dir / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(events[0])
        rules = event["rules"]
        assert "momentum_before" not in rules
        assert "momentum_after" not in rules
        assert "momentum_delta" not in rules
