"""Tests for _strip_fallback — removes fallback sentinel lines from narration."""

import logging

import pytest

from ccya.engine.turn import _FALLBACK_SENTINEL, _strip_fallback


@pytest.fixture()
def _caplog_for_strip():
    """Ensure caplog captures WARNING level from ccya.engine.turn."""
    with pytest.LogCaptureLevel(logging.WARNING):
        yield


class TestStripFallback:
    def test_strips_sentinel_line(self, caplog):
        narration = "You enter the room.\n\n*That action didn't resolve as expected. Trace `abc123` — try rephrasing.*"
        result = _strip_fallback(narration, trace_id="abc123", turn=5)
        assert _FALLBACK_SENTINEL not in result
        assert "You enter the room." in result
        assert any("Fallback message stripped" in r.getMessage() for r in caplog.records)

    def test_no_sentinel_unchanged(self, caplog):
        narration = "You enter the room and see a door."
        result = _strip_fallback(narration, trace_id="abc123", turn=5)
        assert result == narration
        assert not any("Fallback message stripped" in r.getMessage() for r in caplog.records)

    def test_mid_line_not_stripped(self):
        narration = "You say: *That action didn't resolve as expected.* Then you leave."
        result = _strip_fallback(narration, trace_id="abc123", turn=5)
        assert _FALLBACK_SENTINEL in result
        assert "You say:" in result

    def test_multiple_sentinel_lines(self):
        narration = "Line 1.\n\n*That action didn't resolve as expected. Trace `a` — try rephrasing.*\nLine 2.\n\n*That action didn't resolve as expected. Trace `b` — try rephrasing.*"
        result = _strip_fallback(narration, trace_id="abc123", turn=5)
        assert _FALLBACK_SENTINEL not in result
        assert "Line 1." in result
        assert "Line 2." in result

    def test_empty_narration(self):
        result = _strip_fallback("", trace_id="abc123", turn=5)
        assert result == ""

    def test_only_sentinel(self):
        narration = "*That action didn't resolve as expected. Trace `abc` — try rephrasing.*"
        result = _strip_fallback(narration, trace_id="abc123", turn=5)
        assert result == ""
