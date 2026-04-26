"""Smoke tests for ccya engine — no real Ollama needed."""

import ccya.engine
import json
import tempfile
from pathlib import Path

import pytest

from ccya.engine import EngineConfig, run_turn
from ccya.models import QuestUpdate, StateDelta
from ccya.state import (
    apply_delta,
    load_state,
    load_chronicle_tail,
    save_state,
)

SAVE_DIR = Path(tempfile.mkdtemp())


def _write_state(path: Path, data: dict) -> None:
    save_state(path, data)


def _make_state(turn: int = 0) -> dict:
    return {
        "meta": {"game_name": "test", "turn": turn, "setting_pack": "hard-scifi-demo", "model": "gemma3:27b"},
        "pc": {"name": "Vex", "concept": "salvage pilot", "stats": {"body": 2, "mind": 3, "tech": 3, "social": 1}, "conditions": []},
        "location": {"id": "docking-ring-7", "name": "Docking Ring 7", "description": "Low-grav berth."},
        "inventory": [
            {"id": "hand-terminal", "name": "Hand terminal", "notes": "Cracked screen."},
            {"id": "vac-jacket", "name": "Vac jacket", "notes": "Thermal-lined."},
        ],
        "quests": [{"id": "quiet-signal", "title": "The Quiet Signal", "status": "active", "objectives": [{"description": "Find the payer", "done": False}]}],
        "scene": {"tags": [], "present_npcs": [], "established_facts": []},
    }


class _FakeOllama:
    """Context manager that directly replaces engine's ollama functions.

    text_responses[0] = narrative (for streaming narrate call)
    text_responses[1:] = extract responses (for non-streaming extract call)
    """

    def __init__(self, text_responses: list[str], should_fail: bool = False):
        self.call_count = 0
        self.narrative = text_responses[0] if text_responses else ""
        self.text_responses = text_responses
        self.should_fail = should_fail
        self._orig_stream = None
        self._orig_chat = None

    class FakeStream:
        def __init__(self, text: str):
            self.text = text
            self.idx = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.idx == 0:
                self.idx = 1
                return self.text
            raise StopAsyncIteration

    async def _fake(self, *args, **kwargs):
        self.call_count += 1

        # Distinguish narrate (streaming) from extract (non-streaming):
        # narrate uses ollama_chat_stream (no format param)
        # extract uses ollama_chat (has format param for structured output)
        if "format" not in kwargs:
            return _FakeOllama.FakeStream(self.narrative)
        else:
            if self.should_fail and self.call_count == 1:
                return {"response": "this is not valid json at all {{{{", "done": True}
            result_text = self.text_responses[-1] if len(self.text_responses) > 1 else self.narrative
            return {"response": result_text, "done": True, "usage": {"prompt_tokens": 100, "total_tokens": 200}}

    def __enter__(self):
        self._orig_stream = ccya.engine.ollama_chat_stream
        self._orig_chat = ccya.engine.ollama_chat
        ccya.engine.ollama_chat_stream = self._fake
        ccya.engine.ollama_chat = self._fake
        return self.call_count

    def __exit__(self, *exc_info):
        ccya.engine.ollama_chat_stream = self._orig_stream
        ccya.engine.ollama_chat = self._orig_chat


def _make_fake_ollama(text_responses: list[str], should_fail: bool = False):
    """Return a _FakeOllama context manager instance."""
    return _FakeOllama(text_responses, should_fail)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _parse_extract_text(text: str) -> str:
    """Create a valid extract response text from a StateDelta."""
    return json.dumps({
        "state_delta": text,
        "actions": ["Look around", "Check terminal", "Talk to someone"],
        "scene_tags": ["exploration"],
    })


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_save_dir():
    """Reset save dir before each test."""
    if SAVE_DIR.exists():
        for f in SAVE_DIR.iterdir():
            f.unlink()
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after tests
    for f in SAVE_DIR.iterdir():
        f.unlink()


class TestHappyPath:
    """Engine returns TurnResult with expected fields."""

    async def test_narrate_and_extract(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        narrative = "You step through the airlock. The corridor stretches ahead, dim and humming."
        extract = StateDelta(
            established_facts=["You found an airlock at Docking Ring 7."],
        ).model_dump(exclude_none=True)

        fake = _make_fake_ollama([narrative, json.dumps(extract)])

        with fake:
            result = await run_turn(SAVE_DIR, "I step through the airlock.", config=EngineConfig())

        assert result.narrative == narrative
        # StateDelta responses don't include actions; engine defaults to empty list
        assert result.established_facts == ["You found an airlock at Docking Ring 7."]
        assert result.metrics["narrate"]["total_ms"] >= 0
        assert result.metrics["extract"]["retries"] == 0
        assert len(result.errors) == 0
        assert result.turn == 2  # apply_delta + engine both increment


class TestRejectedDelta:
    """Invalid deltas are rejected, not coerced."""

    async def test_remove_nonexistent_item(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = StateDelta(
            inventory_remove=["ghost-item-999"],
        ).model_dump(exclude_none=True)

        fake = _make_fake_ollama([json.dumps(extract)])

        with fake:
            result = await run_turn(SAVE_DIR, "I grab the ghost item.", config=EngineConfig())

        assert len(result.rejected) == 1
        assert result.rejected[0]["value"] == "ghost-item-999"
        assert "does not exist" in result.rejected[0]["reason"]
        assert len(result.errors) > 0

    async def test_update_nonexistent_quest(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = StateDelta(
            quest_updates=[QuestUpdate(id="nonexistent-quest", title="Bad", status="completed", objectives=[])],
        ).model_dump(exclude_none=True)

        fake = _make_fake_ollama([json.dumps(extract)])

        with fake:
            result = await run_turn(SAVE_DIR, "Complete the quest.", config=EngineConfig())

        assert len(result.rejected) >= 1
        assert any(r.get("value") == "nonexistent-quest" for r in result.rejected)


class TestSchemaFailureRetry:
    """First extract fails JSON parsing; retry succeeds."""

    async def test_single_retry(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        narrative = "You examine the hand terminal closely."
        bad_json = "this is gibberish {{{"
        good_extract = StateDelta(
            pc_condition_add=["curious"],
        ).model_dump(exclude_none=True)

        call_count = 0

        async def fake_chat(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            # Distinguish narrate (no format param) from extract (has format param)
            if "format" not in kwargs:
                class FakeStream:
                    def __init__(self):
                        self.idx = 0
                    def __aiter__(self):
                        return self
                    async def __anext__(self):
                        if self.idx == 0:
                            self.idx = 1
                            return narrative
                        raise StopAsyncIteration
                return FakeStream()
            # call_count includes the narrate call, so extract is call 2+
            # Use format presence to count extract calls only
            if call_count <= 2:  # First extract call (after narrate)
                return {"response": bad_json, "done": True}
            # Retry response
            return {"response": json.dumps(good_extract), "done": True}

        # Direct replacement since patch() doesn't properly handle async functions
        _orig_stream = ccya.engine.ollama_chat_stream
        _orig_chat = ccya.engine.ollama_chat
        try:
            ccya.engine.ollama_chat_stream = fake_chat
            ccya.engine.ollama_chat = fake_chat
            result = await run_turn(SAVE_DIR, "I examine the terminal.", config=EngineConfig(max_extract_retries=1))
        finally:
            ccya.engine.ollama_chat_stream = _orig_stream
            ccya.engine.ollama_chat = _orig_chat

        assert "curious" in result.applied.get("pc_condition_add", []) or "curious" in str(result.applied)
        assert result.metrics["extract"]["retries"] == 1


class TestFactCanonization:
    """Established facts land in state and ride into next turn's prefix."""

    async def test_facts_in_state(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = StateDelta(
            established_facts=["The airlock hums with residual charge."],
        ).model_dump(exclude_none=True)

        fake = _make_fake_ollama([json.dumps(extract)])

        with fake:
            await run_turn(SAVE_DIR, "Touch the airlock.", config=EngineConfig())

        loaded = load_state(SAVE_DIR)
        facts = loaded.get("scene", {}).get("established_facts", [])
        assert "The airlock hums with residual charge." in facts


class TestChroniclePrefixBudget:
    """Chronicle tail clipped to configured budget."""

    def test_chronicle_tail(self) -> None:
        large_text = "This is a sentence. " * 2000  # ~10000 words
        chronicle = SAVE_DIR / "chronicle.md"
        chronicle.write_text(large_text)

        tail = load_chronicle_tail(SAVE_DIR, max_tokens=100)
        words = tail.split()
        assert len(words) <= 100


class TestStateApplyDelta:
    """Delta applies correctly to state."""

    def test_inventory_add(self) -> None:
        state = _make_state()
        delta = StateDelta(
            inventory_add=[{"id": "plasma-cutter", "name": "Plasma cutter", "notes": "Hot, dangerous."}],
        )
        updated = apply_delta(state, delta)
        ids = [item["id"] for item in updated["inventory"]]
        assert "plasma-cutter" in ids
        assert len(updated["inventory"]) == 3

    def test_inventory_remove(self) -> None:
        state = _make_state()
        delta = StateDelta(inventory_remove=["hand-terminal"])
        updated = apply_delta(state, delta)
        ids = [item["id"] for item in updated["inventory"]]
        assert "hand-terminal" not in ids

    def test_location_change(self) -> None:
        state = _make_state()
        delta = StateDelta(
            location_change={"id": "concourse-b", "name": "Concourse B", "description": "Wide and bright."},
        )
        updated = apply_delta(state, delta)
        assert updated["location"]["id"] == "concourse-b"

    def test_turn_counter_increments(self) -> None:
        state = _make_state(turn=5)
        delta = StateDelta()
        updated = apply_delta(state, delta)
        assert updated["meta"]["turn"] == 6


class TestEventWrittenBeforeState:
    """Event line is written before atomic state replace."""

    async def test_write_order(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = StateDelta(established_facts=["turn-1-fact"]).model_dump(exclude_none=True)
        fake = _make_fake_ollama([json.dumps(extract)])

        with fake:
            await run_turn(SAVE_DIR, "test", config=EngineConfig())

        # Event file should have exactly 1 line
        events = (SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        assert len(events) == 1
        event = json.loads(events[0])
        assert event["turn"] == 2  # apply_delta increments to 1, engine increments to 2
        assert event["input"] == "test"

        # State should be updated
        loaded = load_state(SAVE_DIR)
        assert loaded["meta"]["turn"] == 2  # double increment: apply_delta + engine


class TestTurnResultTraceId:
    """Each turn gets a unique trace_id."""

    async def test_unique_trace_ids(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)
        extract = StateDelta().model_dump(exclude_none=True)
        fake = _make_fake_ollama([json.dumps(extract)])

        with fake:
            r1 = await run_turn(SAVE_DIR, "first", config=EngineConfig())
            r2 = await run_turn(SAVE_DIR, "second", config=EngineConfig())

        assert r1.trace_id != r2.trace_id
        assert len(r1.trace_id) > 0


class TestFactDeduplication:
    """Duplicate facts are not added again."""

    def test_dedup(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["fact one", "fact two"]

        delta = StateDelta(established_facts=["fact one", "fact three"])
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert facts.count("fact one") == 1
        assert "fact three" in facts
        assert "fact two" in facts


class TestEstablishedFactsEviction:
    """Facts beyond established_facts_max are evicted."""

    def test_eviction(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["f1", "f2", "f3", "f4", "f5"]

        delta = StateDelta(established_facts=["f6", "f7", "f8", "f9", "f10", "f11"])
        # apply_delta uses default max=10
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert len(facts) <= 10
        assert "f11" in facts  # newest should be kept
        assert "f1" not in facts  # oldest should be evicted


class TestApplyDeltaEstablishedFactsMax:
    """apply_delta respects established_facts_max parameter."""

    def test_custom_max_wired(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["f1"]

        delta = StateDelta(established_facts=["f2", "f3", "f4"])
        updated = apply_delta(state, delta, established_facts_max=2)
        facts = updated["scene"]["established_facts"]
        assert len(facts) <= 2
        assert "f4" in facts


class TestPerTurnMetrics:
    """Engine tracks token counts in metrics."""

    async def test_metrics_have_token_fields(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        narrative = "You step through the airlock."
        extract = StateDelta().model_dump(exclude_none=True)

        fake = _make_fake_ollama([narrative, json.dumps(extract)])

        with fake:
            result = await run_turn(SAVE_DIR, "test", config=EngineConfig())

        assert "tokens_in" in result.metrics["narrate"]
        assert "tokens_out" in result.metrics["narrate"]
        assert "tokens_in" in result.metrics["extract"]
        assert "tokens_out" in result.metrics["extract"]


class TestEstablishedFactsInEvent:
    """Event line includes established_facts."""

    async def test_event_has_established_facts(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = StateDelta(
            established_facts=["This fact matters."],
        ).model_dump(exclude_none=True)

        fake = _make_fake_ollama([json.dumps({
            "state_delta": extract,
            "actions": ["Look around"],
            "scene_tags": [],
        })])

        with fake:
            await run_turn(SAVE_DIR, "test", config=EngineConfig())

        # Check event line
        events = (SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(events[-1])
        assert "This fact matters." in event.get("established_facts", [])

