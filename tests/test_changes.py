"""Tests for momentum observability: summarize_changes diff and format_change_lines rendering."""

from ccya.engine.changes import format_change_lines, summarize_changes


def _pre_state(momentum=0):
    return {
        "pc": {"momentum": momentum, "conditions": [], "stats": {}},
        "inventory": [],
        "location": {"id": "ring-7", "name": "Ring 7"},
        "scene": {"recent_events": []},
        "quests": [],
    }


def _post_state(momentum=0):
    return {
        "pc": {"momentum": momentum, "conditions": [], "stats": {}},
        "inventory": [],
        "location": {"id": "ring-7", "name": "Ring 7"},
        "scene": {"recent_events": []},
        "quests": [],
    }


class TestMomentumSummarizeChanges:
    def test_momentum_diff_when_changed(self):
        changes = summarize_changes(_pre_state(momentum=-1), _post_state(momentum=1), {}, [])
        assert "momentum" in changes
        assert len(changes["momentum"]) == 1
        assert changes["momentum"][0]["kind"] == "momentum_changed"
        assert changes["momentum"][0]["before"] == -1
        assert changes["momentum"][0]["after"] == 1
        assert changes["momentum"][0]["delta"] == 2

    def test_no_momentum_key_when_unchanged(self):
        changes = summarize_changes(_pre_state(momentum=0), _post_state(momentum=0), {}, [])
        assert changes["momentum"] == []

    def test_negative_momentum_delta(self):
        changes = summarize_changes(_pre_state(momentum=2), _post_state(momentum=-1), {}, [])
        assert changes["momentum"][0]["delta"] == -3


class TestMomentumFormatChangeLines:
    def test_momentum_line_rendered(self):
        ch = {"momentum": [{"kind": "momentum_changed", "before": -1, "after": 1, "delta": 2}]}
        lines = format_change_lines(ch)
        assert "⚡ Momentum -1 → +1" in lines

    def test_no_momentum_line_when_empty(self):
        ch = {"momentum": []}
        lines = format_change_lines(ch)
        assert not any("Momentum" in line for line in lines)

    def test_zero_to_zero_summarize_changes_no_entry(self):
        changes = summarize_changes(_pre_state(momentum=0), _post_state(momentum=0), {}, [])
        assert changes["momentum"] == []
