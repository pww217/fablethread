"""Tests for apply_delta quest alias dedup."""

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


class TestQuestAliasDedup:
    def test_alias_redirect_on_title_match(self, caplog):
        state = _make_state(quests=[
            {"id": "deliver_the_ledger", "title": "Deliver the ledger to Halden", "status": "active", "objectives": [{"description": "Find the ledger", "done": True}]},
        ])
        delta = StateDelta(quest_updates=[
            QuestUpdate(id="deliver_halden_ledger", title="Deliver the ledger to Halden", status="active", objectives=[{"description": "Hand it over", "done": False}])
        ])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert len(state["quests"]) == 1
        assert state["quests"][0]["id"] == "deliver_the_ledger"
        assert any("alias collision" in r.getMessage() for r in caplog.records)
        # Objectives should be merged
        obj_descs = [o["description"] for o in state["quests"][0]["objectives"]]
        assert "Find the ledger" in obj_descs
        assert "Hand it over" in obj_descs

    def test_alias_redirect_updates_status(self, caplog):
        state = _make_state(quests=[
            {"id": "q1", "title": "Deliver the ledger", "status": "active", "objectives": []},
        ])
        delta = StateDelta(quest_updates=[
            QuestUpdate(id="q2", title="Deliver the Ledger", status="completed", objectives=[])
        ])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert len(state["quests"]) == 1
        assert state["quests"][0]["id"] == "q1"
        assert state["quests"][0]["status"] == "completed"

    def test_no_alias_when_titles_differ(self):
        state = _make_state(quests=[
            {"id": "q1", "title": "Deliver the ledger", "status": "active", "objectives": []},
        ])
        delta = StateDelta(quest_updates=[
            QuestUpdate(id="q2", title="Settle the debt", status="active", objectives=[])
        ])
        state, _ = apply_delta(state, delta)
        assert len(state["quests"]) == 2
        ids = {q["id"] for q in state["quests"]}
        assert "q1" in ids
        assert "q2" in ids

    def test_alias_case_insensitive(self, caplog):
        state = _make_state(quests=[
            {"id": "q1", "title": "Deliver the ledger to Halden", "status": "active", "objectives": []},
        ])
        delta = StateDelta(quest_updates=[
            QuestUpdate(id="q2", title="deliver  the   LEDGER to HALDEN", status="active", objectives=[])
        ])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert len(state["quests"]) == 1
        assert state["quests"][0]["id"] == "q1"

    def test_alias_no_redirect_when_new_quest_id_already_exists(self):
        state = _make_state(quests=[
            {"id": "q1", "title": "Deliver the ledger", "status": "active", "objectives": []},
            {"id": "q2", "title": "Settle the debt", "status": "active", "objectives": []},
        ])
        delta = StateDelta(quest_updates=[
            QuestUpdate(id="q2", title="Settle the debt", status="completed", objectives=[])
        ])
        state, _ = apply_delta(state, delta)
        assert len(state["quests"]) == 2
        q2 = next(q for q in state["quests"] if q["id"] == "q2")
        assert q2["status"] == "completed"
