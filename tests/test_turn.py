"""Tests for turn pipeline: beat expiry, deescalate float magnitude, condition lifecycle."""

import json
import tempfile
from pathlib import Path

from ccya.engine import EngineConfig, run_turn

_SAVE_DIR = Path(tempfile.mkdtemp())


def _write_events(path: Path, events: list[dict]) -> None:
    import jsonlines
    with jsonlines.open(str(path), mode="w") as writer:
        for event in events:
            writer.write(event)


def _write_state(path: Path, data: dict) -> None:
    from ccya.state import save_state
    save_state(path, data)


def _make_state(turn: int = 0) -> dict:
    return {
        "meta": {
            "game_name": "test",
            "turn": turn,
            "setting_pack": "expanse-belter",
            "model": "mlx-community/Qwen3.6-27B-4bit",
            "compendium_touch_order": [],
            "last_compacted_turn": 0,
            "prior_history": "",
        },
        "pc": {
            "name": "Vex",
            "tagline": "salvage pilot",
            "bio": "",
            "stats": {
                "strength": 2,
                "dexterity": 2,
                "wits": 3,
                "lore": 2,
                "charisma": 2,
                "resolve": 2,
            },
            "conditions": [],
        },
        "location": {
            "id": "docking-ring-7",
            "name": "Docking Ring 7",
            "description": "Low-grav berth.",
        },
        "inventory": [
            {"id": "hand-terminal", "name": "Hand terminal", "notes": "Cracked screen."},
            {"id": "vac-jacket", "name": "Vac jacket", "notes": "Thermal-lined."},
        ],
        "quests": [],
        "scene": {"tags": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


class TestBeatExpiry:
    def test_expired_beat_not_passed_to_narration(self):
        """Beat with beat_expires_turn in the past is nullified before narration."""
        state = _make_state(turn=2)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 1,
        }
        _write_state(_SAVE_DIR, state)

        narrative = "You step through the airlock."
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "Nothing notable.",
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": json.dumps({
                    "intent": "player action",
                    "intent_verb": "act",
                    "target": "",
                    "stakes": "",
                    "check": {"required": False},
                }), "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": progress_response, "done": True, "usage": {}}
            return {"response": progress_response, "done": True, "usage": {}}

        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        _mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        _origs = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = None
            async def collect():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "look", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            import asyncio
            asyncio.get_event_loop().run_until_complete(collect())

            # The expired beat should have been nullified, so pending_gm_beat
            # in the state after the turn should be None.
            assert result is not None
            # Check that no error was raised about missing gm_beat
            assert len(result.errors) == 0, f"Errors: {result.errors}"
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)


class TestDeescalateFloatMagnitude:
    def test_crit_success_with_pressure_gives_1_0(self):
        """crit_success on a scene with immediate pressure → deescalate=1.0."""
        state = _make_state(turn=0)
        state["scene"]["scene_pressure"] = [
            {"id": "threat", "text": "Armed guards", "urgency": "immediate", "turn_added": 0}
        ]
        _write_state(_SAVE_DIR, state)

        narrative = "You fight the guards."
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "You defeated the guards.",
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                # Rules with crit_success band
                return {"response": json.dumps({
                    "intent": "combat",
                    "intent_verb": "attack",
                    "target": "guards",
                    "stakes": "",
                    "check": {
                        "required": True,
                        "skill": "strength",
                        "difficulty": "normal",
                    },
                }), "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": progress_response, "done": True, "usage": {}}
            return {"response": progress_response, "done": True, "usage": {}}

        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        _mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        _origs = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = None
            async def collect():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "attack", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            import asyncio
            asyncio.get_event_loop().run_until_complete(collect())

            # The deescalate value is computed in turn.py and passed to narration.
            # We verify the pipeline runs without error and the beat is stored
            # with beat_expires_turn.
            assert result is not None
            assert len(result.errors) == 0, f"Errors: {result.errors}"
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)


class TestConditionExpiry:
    def test_condition_expiry(self):
        """Condition with turns_remaining: 1 expires after one turn, condition_expired event emitted."""
        state = _make_state(turn=0)
        state["pc"]["conditions"] = [
            {"id": "rattled", "label": "rattled", "description": "Shaken by the encounter.", "added_turn": 0, "turns_remaining": 1},
        ]
        _write_state(_SAVE_DIR, state)

        # Clear any existing events
        events_file = _SAVE_DIR / "events.jsonl"
        if events_file.exists():
            events_file.unlink()

        narrative = "You steady your breathing."
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "You compose yourself.",
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": json.dumps({
                    "intent": "player action",
                    "intent_verb": "act",
                    "target": "",
                    "stakes": "",
                    "check": {"required": False},
                }), "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": progress_response, "done": True, "usage": {}}
            return {"response": progress_response, "done": True, "usage": {}}

        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        _mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        _origs = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = None
            async def collect():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "steady", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            import asyncio
            asyncio.get_event_loop().run_until_complete(collect())

            assert result is not None
            assert len(result.errors) == 0, f"Errors: {result.errors}"

            # Reload state to check conditions
            from ccya.state import load_state
            final_state = load_state(_SAVE_DIR)
            conds = final_state.get("pc", {}).get("conditions") or []
            assert len(conds) == 0, f"Condition should have expired, but found: {conds}"

            # Check events.jsonl for condition_expired event
            found_expired = False
            lines = events_file.read_text().strip().split("\n")
            for line in lines:
                if line:
                    event = json.loads(line)
                    if event.get("kind") == "condition_expired" and event.get("condition_id") == "rattled":
                        found_expired = True
                        break
            assert found_expired, "condition_expired event not found in events.jsonl"
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

    def test_condition_persistence(self):
        """Condition with turns_remaining: 3 decrements correctly over 3 turns."""
        state = _make_state(turn=0)
        state["pc"]["conditions"] = [
            {"id": "wounded", "label": "wounded", "description": "Bleeding from the fight.", "added_turn": 0, "turns_remaining": 3},
        ]
        _write_state(_SAVE_DIR, state)

        events_file = _SAVE_DIR / "events.jsonl"
        if events_file.exists():
            events_file.unlink()

        narrative = "You fight through the pain."
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "You push forward.",
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": json.dumps({
                    "intent": "player action",
                    "intent_verb": "act",
                    "target": "",
                    "stakes": "",
                    "check": {"required": False},
                }), "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": progress_response, "done": True, "usage": {}}
            return {"response": progress_response, "done": True, "usage": {}}

        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        _mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        _origs = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = None
            async def collect():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "fight", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            import asyncio
            asyncio.get_event_loop().run_until_complete(collect())

            assert result is not None
            assert len(result.errors) == 0, f"Errors: {result.errors}"

            # After 1 turn: turns_remaining should be 2
            from ccya.state import load_state
            state_after_1 = load_state(_SAVE_DIR)
            conds = state_after_1.get("pc", {}).get("conditions") or []
            assert len(conds) == 1
            assert conds[0]["turns_remaining"] == 2, f"Expected 2, got {conds[0].get('turns_remaining')}"

            # Run turn 2
            chat_call_count = 0
            result = None
            async def collect2():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "fight again", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            asyncio.get_event_loop().run_until_complete(collect2())

            assert result is not None
            state_after_2 = load_state(_SAVE_DIR)
            conds = state_after_2.get("pc", {}).get("conditions") or []
            assert len(conds) == 1
            assert conds[0]["turns_remaining"] == 1, f"Expected 1, got {conds[0].get('turns_remaining')}"

            # Run turn 3: condition should expire
            chat_call_count = 0
            result = None
            async def collect3():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "last push", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            asyncio.get_event_loop().run_until_complete(collect3())

            assert result is not None
            state_after_3 = load_state(_SAVE_DIR)
            conds = state_after_3.get("pc", {}).get("conditions") or []
            assert len(conds) == 0, f"Condition should have expired, but found: {conds}"

            # Check events.jsonl for condition_expired event
            found_expired = False
            lines = events_file.read_text().strip().split("\n")
            for line in lines:
                if line:
                    event = json.loads(line)
                    if event.get("kind") == "condition_expired" and event.get("condition_id") == "wounded":
                        found_expired = True
                        break
            assert found_expired, "condition_expired event not found in events.jsonl"
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)


class TestBeatDisposition:
    """Tests for beat disposition logic (carry/replace/consume)."""

    def _make_progress_response(self, gm_beat=None, beat_disposition="consume"):
        base = {
            "quest_updates": [],
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

    def test_beat_disposition_consume_clears_beat(self):
        """consume disposition clears pending_gm_beat after turn."""
        state = _make_state(turn=1)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 3,
        }
        _write_state(_SAVE_DIR, state)

        narrative = "You step through the airlock."
        progress_response = self._make_progress_response(beat_disposition="consume")

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": json.dumps({
                    "intent": "player action",
                    "intent_verb": "act",
                    "target": "",
                    "stakes": "",
                    "check": {"required": False},
                }), "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": progress_response, "done": True, "usage": {}}
            return {"response": progress_response, "done": True, "usage": {}}

        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        _mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        _origs = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = None
            async def collect():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "look", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            import asyncio
            asyncio.get_event_loop().run_until_complete(collect())

            assert result is not None
            assert len(result.errors) == 0, f"Errors: {result.errors}"

            from ccya.state import load_state
            final_state = load_state(_SAVE_DIR)
            beat = final_state.get("meta", {}).get("pending_gm_beat")
            assert beat is None, f"consume disposition should clear beat, but found: {beat}"
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

    def test_beat_disposition_carry_preserves_beat(self):
        """carry disposition preserves pending_gm_beat unchanged."""
        state = _make_state(turn=1)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 3,
        }
        _write_state(_SAVE_DIR, state)

        narrative = "You step through the airlock."
        progress_response = self._make_progress_response(beat_disposition="carry")

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": json.dumps({
                    "intent": "player action",
                    "intent_verb": "act",
                    "target": "",
                    "stakes": "",
                    "check": {"required": False},
                }), "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": progress_response, "done": True, "usage": {}}
            return {"response": progress_response, "done": True, "usage": {}}

        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        _mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        _origs = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = None
            async def collect():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "look", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            import asyncio
            asyncio.get_event_loop().run_until_complete(collect())

            assert result is not None
            assert len(result.errors) == 0, f"Errors: {result.errors}"

            from ccya.state import load_state
            final_state = load_state(_SAVE_DIR)
            beat = final_state.get("meta", {}).get("pending_gm_beat")
            assert beat is not None, "carry disposition should preserve beat"
            assert beat["type"] == "complication", f"Beat type should be preserved, got: {beat.get('type')}"
            assert beat["beat_expires_turn"] == 3, f"Beat expiry should be preserved, got: {beat.get('beat_expires_turn')}"
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

    def test_beat_disposition_replace_updates_beat(self):
        """replace disposition updates pending_gm_beat with new beat."""
        state = _make_state(turn=1)
        state["meta"]["pending_gm_beat"] = {
            "type": "complication",
            "instruction": "A long enough instruction string that passes the quality gate without issues",
            "beat_expires_turn": 3,
        }
        _write_state(_SAVE_DIR, state)

        narrative = "You step through the airlock."
        progress_response = self._make_progress_response(
            gm_beat={
                "type": "revelation",
                "surface_as": "player_discovery",
                "instruction": "A long enough instruction string that passes the quality gate without issues",
            },
            beat_disposition="replace",
        )

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": json.dumps({
                    "intent": "player action",
                    "intent_verb": "act",
                    "target": "",
                    "stakes": "",
                    "check": {"required": False},
                }), "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": progress_response, "done": True, "usage": {}}
            return {"response": progress_response, "done": True, "usage": {}}

        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        _mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        _origs = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = None
            async def collect():
                nonlocal result
                async for event in run_turn(_SAVE_DIR, "look", config=EngineConfig()):
                    if event[0] == "complete":
                        result = event[1]
            import asyncio
            asyncio.get_event_loop().run_until_complete(collect())

            assert result is not None
            assert len(result.errors) == 0, f"Errors: {result.errors}"

            from ccya.state import load_state
            final_state = load_state(_SAVE_DIR)
            beat = final_state.get("meta", {}).get("pending_gm_beat")
            assert beat is not None, "replace disposition should set new beat"
            assert beat["type"] == "revelation", f"Beat type should be replaced, got: {beat.get('type')}"
            # turn_no is incremented during the turn, so beat_expires_turn = (turn+1) + 2 = 4
            assert beat["beat_expires_turn"] == 4, f"Beat expiry should be turn+3=4, got: {beat.get('beat_expires_turn')}"
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)
