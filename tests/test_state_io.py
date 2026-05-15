"""Tests for state/io.py — state I/O and migration."""


class TestMigrateArcThreadStates:
    """Arc thread state migration ensures active/latent lists have correct states."""

    def test_migrate_arc_thread_states(self):
        """Arc threads in active list should be state=active after migration."""
        state = {
            "arc": {
                "active_threads": [{"id": "t1", "state": "latent"}],
                "latent_threads": [{"id": "t2", "state": "active"}],
            }
        }
        from ccya.state.io import _migrate_state
        _migrate_state(state)
        assert state["arc"]["active_threads"][0]["state"] == "active"
        assert state["arc"]["latent_threads"][0]["state"] == "latent"

    def test_migrate_preserves_correct_states(self):
        """Already-correct states should not be changed."""
        state = {
            "arc": {
                "active_threads": [{"id": "t1", "state": "active"}],
                "latent_threads": [{"id": "t2", "state": "latent"}],
            }
        }
        from ccya.state.io import _migrate_state
        _migrate_state(state)
        assert state["arc"]["active_threads"][0]["state"] == "active"
        assert state["arc"]["latent_threads"][0]["state"] == "latent"

    def test_migrate_no_arc(self):
        """State without arc should not crash."""
        state = {}
        from ccya.state.io import _migrate_state
        _migrate_state(state)
        assert "arc" not in state

    def test_migrate_empty_arc(self):
        """State with empty arc should not crash."""
        state = {"arc": {}}
        from ccya.state.io import _migrate_state
        _migrate_state(state)
        assert state["arc"] == {}
