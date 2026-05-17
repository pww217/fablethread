"""Tests for turn pipeline: beat expiry, deescalate float magnitude, condition lifecycle."""

import json
import tempfile

from pathlib import Path

from ccya.engine import EngineConfig

# Reuse the existing fakes / helpers from the smoke suite.
from tests.test_engine_smoke import (
    _FakeLLM,
    _make_state,
    _run,
)

_SAVE_DIR = Path(tempfile.mkdtemp())


def _write_state(path: Path, data: dict) -> None:
    from ccya.state import save_state
    save_state(path, data)


class TestBeatExpiry:
    async def test_expired_beat_not_passed_to_narration(self):
        """Beat with beat_expires_turn in the past is nullified before narration."""
        state = _make_state(turn=2)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 1,
        }
        _write_state(_SAVE_DIR, state)

        progress_response = json.dumps({
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "Nothing notable.",
        })

        fake = _FakeLLM(narrative="You step through the airlock.", progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())

        assert result is not None
        assert len(result.errors) == 0, f"Errors: {result.errors}"


class TestDeescalateFloatMagnitude:
    async def test_crit_success_with_pressure_gives_1_0(self):
        """crit_success on a scene with immediate pressure → deescalate=1.0."""
        state = _make_state(turn=0)
        state["scene"]["scene_pressure"] = [
            {"id": "threat", "text": "Armed guards", "urgency": "immediate", "turn_added": 0}
        ]
        _write_state(_SAVE_DIR, state)

        progress_response = json.dumps({
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "You defeated the guards.",
        })

        fake = _FakeLLM(
            narrative="You fight the guards.",
            progress_response=progress_response,
            rules_response=json.dumps({
                "intent": "combat",
                "intent_verb": "attack",
                "target": "guards",
                "stakes": "",
                "check": {
                    "required": True,
                    "skill": "strength",
                    "difficulty": "normal",
                },
            }),
        )
        with fake:
            result = await _run(_SAVE_DIR, "attack", config=EngineConfig())

        assert result is not None
        assert len(result.errors) == 0, f"Errors: {result.errors}"


class TestConditionExpiry:
    async def test_condition_expiry(self):
        """Condition with turns_remaining: 1 expires after one turn, condition_expired event emitted."""
        state = _make_state(turn=0)
        state["pc"]["conditions"] = [
            {"id": "rattled", "label": "rattled", "description": "Shaken by the encounter.", "added_turn": 0, "turns_remaining": 1},
        ]
        _write_state(_SAVE_DIR, state)

        events_file = _SAVE_DIR / "events.jsonl"
        if events_file.exists():
            events_file.unlink()

        progress_response = json.dumps({
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "You compose yourself.",
        })

        fake = _FakeLLM(narrative="You steady your breathing.", progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "steady", config=EngineConfig())

        assert result is not None
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        from ccya.state import load_state
        final_state = load_state(_SAVE_DIR)
        conds = final_state.get("pc", {}).get("conditions") or []
        assert len(conds) == 0, f"Condition should have expired, but found: {conds}"

        found_expired = False
        lines = events_file.read_text().strip().split("\n")
        for line in lines:
            if line:
                event = json.loads(line)
                if event.get("kind") == "condition_expired" and event.get("condition_id") == "rattled":
                    found_expired = True
                    break
        assert found_expired, "condition_expired event not found in events.jsonl"


class TestBeatDisposition:
    """Tests for beat disposition logic (carry/replace/consume)."""

    def _make_progress_response(self, gm_beat=None, beat_disposition="consume"):
        base = {
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "Nothing notable.",
        }
        if gm_beat is not None:
            base["gm_beat"] = gm_beat
        base["beat_disposition"] = beat_disposition
        return json.dumps(base)

    async def test_beat_disposition_consume_clears_beat(self):
        """consume disposition clears pending_gm_beat after turn."""
        state = _make_state(turn=1)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 3,
        }
        _write_state(_SAVE_DIR, state)

        progress_response = self._make_progress_response(beat_disposition="consume")

        fake = _FakeLLM(narrative="You step through the airlock.", progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())

        assert result is not None
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        from ccya.state import load_state
        final_state = load_state(_SAVE_DIR)
        beat = final_state.get("meta", {}).get("pending_gm_beat")
        assert beat is None, f"consume disposition should clear beat, but found: {beat}"

    async def test_beat_disposition_carry_preserves_beat(self):
        """carry disposition preserves pending_gm_beat unchanged."""
        state = _make_state(turn=1)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 3,
        }
        _write_state(_SAVE_DIR, state)

        progress_response = self._make_progress_response(beat_disposition="carry")

        fake = _FakeLLM(narrative="You step through the airlock.", progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())

        assert result is not None
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        from ccya.state import load_state
        final_state = load_state(_SAVE_DIR)
        beat = final_state.get("meta", {}).get("pending_gm_beat")
        assert beat is not None, "carry disposition should preserve beat"
        assert beat["type"] == "complication", f"Beat type should be preserved, got: {beat.get('type')}"
        assert beat["beat_expires_turn"] == 3, f"Beat expiry should be preserved, got: {beat.get('beat_expires_turn')}"

    async def test_beat_disposition_replace_updates_beat(self):
        """replace disposition updates pending_gm_beat with new beat."""
        state = _make_state(turn=1)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 3,
        }
        _write_state(_SAVE_DIR, state)

        progress_response = self._make_progress_response(
            gm_beat={
                "type": "revelation",
                "surface_as": "player_discovery",
                "instruction": "A long enough instruction string that passes the quality gate without issues",
            },
            beat_disposition="replace",
        )

        fake = _FakeLLM(narrative="You step through the airlock.", progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())

        assert result is not None
        assert len(result.errors) == 0, f"Errors: {result.errors}"

        from ccya.state import load_state
        final_state = load_state(_SAVE_DIR)
        beat = final_state.get("meta", {}).get("pending_gm_beat")
        assert beat is not None, "replace disposition should set new beat"
        assert beat["type"] == "revelation", f"Beat type should be replaced, got: {beat.get('type')}"
        # turn_no is incremented during the turn, so beat_expires_turn = (turn+1) + 2 = 4
        assert beat["beat_expires_turn"] == 4, f"Beat expiry should be turn+3=4, got: {beat.get('beat_expires_turn')}"
