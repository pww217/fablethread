"""Tests for apply_delta quest terminal-state guard and auto-close."""

import logging

from ccya.models import QuestUpdate, StateDelta
from ccya.state import apply_delta


def _make_state(quests=None):
    state = {
        "meta": {"turn": 5, "compendium_touch_order": []},
        "pc": {"name": "V", "tagline": "pilot", "bio": "", "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2}, "conditions": []},
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": [],
        "quests": quests or [],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }
    return state


class TestQuestTerminalStateGuard:
    def test_completed_quest_update_skipped(self, caplog):
        state = _make_state(quests=[
            {"id": "settle_debt", "title": "Settle Debt", "status": "completed", "objectives": [{"description": "Pay Caron", "done": True}]},
        ])
        delta = StateDelta(quest_updates=[QuestUpdate(id="settle_debt", status="active", objectives=[])])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert state["quests"][0]["status"] == "completed"
        assert any("terminal state" in r.getMessage() for r in caplog.records)

    def test_failed_quest_update_skipped(self, caplog):
        state = _make_state(quests=[
            {"id": "failed_quest", "title": "Failed", "status": "failed", "objectives": [{"description": "x", "done": False, "failed": True}]},
        ])
        delta = StateDelta(quest_updates=[QuestUpdate(id="failed_quest", status="active", objectives=[])])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert state["quests"][0]["status"] == "failed"
        assert any("terminal state" in r.getMessage() for r in caplog.records)

    def test_active_quest_update_applied(self):
        state = _make_state(quests=[
            {"id": "active_quest", "title": "Active", "status": "active", "objectives": [{"description": "x", "done": False}]},
        ])
        delta = StateDelta(quest_updates=[QuestUpdate(id="active_quest", status="active", objectives=[{"index": 1, "done": True}])])
        state, _ = apply_delta(state, delta)
        assert state["quests"][0]["objectives"][0]["done"] is True

    def test_new_quest_created(self):
        state = _make_state(quests=[])
        delta = StateDelta(quest_updates=[QuestUpdate(id="new_quest", title="New", status="active", objectives=[{"description": "Do thing", "done": False}])])
        state, _ = apply_delta(state, delta)
        assert len(state["quests"]) == 1
        assert state["quests"][0]["id"] == "new_quest"
        assert state["quests"][0]["status"] == "active"


class TestQuestAutoClose:
    def test_all_objectives_done_auto_completes(self):
        state = _make_state(quests=[
            {"id": "q1", "title": "Q1", "status": "active", "objectives": [{"description": "x", "done": False}]},
        ])
        delta = StateDelta(quest_updates=[QuestUpdate(id="q1", status="active", objectives=[{"index": 1, "done": True}])])
        state, _ = apply_delta(state, delta)
        assert state["quests"][0]["status"] == "completed"

    def test_auto_close_then_re_emit_skipped(self, caplog):
        state = _make_state(quests=[
            {"id": "q1", "title": "Q1", "status": "completed", "objectives": [{"description": "x", "done": True}]},
        ])
        delta = StateDelta(quest_updates=[QuestUpdate(id="q1", status="active", objectives=[{"index": 1, "done": True}])])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert state["quests"][0]["status"] == "completed"
        assert any("terminal state" in r.getMessage() for r in caplog.records)
