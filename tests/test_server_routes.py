"""Tests that server routes are registered on the FastAPI app.

Covers:
- All expected route paths are present
- Routes are callable (not just decorated but registered)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from ccya.server.app import app

    return TestClient(app)


class TestRouteRegistration:
    """Verify every route path is registered on the app."""

    EXPECTED_ROUTES = [
        "/",
        "/turn",
        "/turn/delete",

        "/new-game",
        "/new-game/reroll",
        "/panels/state",
        "/panels/state-left",
        "/panels/state-right",
        "/panels/actions",
        "/panels/debug",
        "/panels/debug/clear-errors",
        "/panels/pack-picker",
        "/panels/char-creation",
        "/panels/turn-log",
        "/turn_viewer",
        "/turn_viewer/data",
        "/turn_viewer/stream",
        "/opening",
        "/healthz",
    ]

    @pytest.mark.parametrize("path", EXPECTED_ROUTES)
    def test_route_registered(self, client, path):
        """Every expected path should be in the app's route table."""
        route_paths = {r.path for r in client.app.routes}
        assert path in route_paths, f"Route {path!r} not registered"

    def test_healthz_returns_json(self, client):
        """GET /healthz should return a JSON response."""
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert "llm" in data
        assert "model" in data
        assert "available" in data

    def test_healthz_mock_mode(self):
        """GET /healthz in MOCK_MODE should report available=True."""
        import os

        os.environ["MOCK_MODE"] = "true"
        try:
            from ccya.server.app import app

            client = TestClient(app)
            resp = client.get("/healthz")
            assert resp.status_code == 200
            data = resp.json()
            assert data["available"] is True
            assert data["mock"] is True
        finally:
            os.environ.pop("MOCK_MODE", None)

    def test_static_files_mounted(self, client):
        """Static files should be mounted at /static."""
        route_paths = {r.path for r in client.app.routes}
        assert "/static" in route_paths

    def test_format_ts(self):
        """_format_ts should convert UTC ISO to human-readable format."""
        from ccya.server.routes import _format_ts

        result = _format_ts("2026-05-09T15:33:00Z")
        # Should not contain ISO date format
        assert "2026-05-09" not in result
        # Should contain human-readable components
        assert "May" in result
        assert "3:33" in result or "03:33" in result
        assert "UTC" in result

    def test_format_ts_fallback(self):
        """_format_ts should return raw string if unparseable."""
        from ccya.server.routes import _format_ts

        assert _format_ts("not-a-date") == "not-a-date"
        assert _format_ts("") == ""

    def test_delete_no_events(self, client, tmp_path):
        """DELETE with no events should return 400."""
        save_dir = tmp_path / "test_delete_empty"
        save_dir.mkdir()
        (save_dir / "state.yaml").write_text("")

        from ccya.server import routes
        orig = routes._app_mod.SAVE_DIR
        routes._app_mod.SAVE_DIR = save_dir
        try:
            resp = client.post("/turn/delete")
            assert resp.status_code == 400
            assert "error" in resp.json()
        finally:
            routes._app_mod.SAVE_DIR = orig

    def test_delete_returns_actions(self, client, tmp_path):
        """DELETE should remove last event and return previous actions."""
        import json

        save_dir = tmp_path / "test_delete_actions"
        save_dir.mkdir()
        (save_dir / "state.yaml").write_text("")

        events_path = save_dir / "events.jsonl"
        events_path.write_text(
            json.dumps({
                "turn": 3,
                "actions": ["Action A", "Action B", "Action C", "Action D"],
                "input": "test input",
            }) + "\n"
        )

        from ccya.server import routes
        orig = routes._app_mod.SAVE_DIR
        routes._app_mod.SAVE_DIR = save_dir
        try:
            resp = client.post("/turn/delete")
            assert resp.status_code == 200
            data = resp.json()
            assert data["actions"] == ["Action A", "Action B", "Action C", "Action D"]
            assert data["turn"] == 3
            remaining = events_path.read_text().strip()
            assert remaining == ""
        finally:
            routes._app_mod.SAVE_DIR = orig
