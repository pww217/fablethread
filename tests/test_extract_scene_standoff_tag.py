"""Verify extract_scene_system.j2 renders the standoff/confrontation scene-tag examples."""

from pathlib import Path

from ccya.engine import _build_jinja_env, _extract_scene_messages


class TestExtractSceneStandoffTag:
    """Verify the standoff and verbal confrontation examples are rendered in the system prompt."""

    def _env(self):
        return _build_jinja_env(str(Path(__file__).parent.parent / "ccya" / "prompts"))

    def test_standoff_example_present(self):
        env = self._env()
        msgs = _extract_scene_messages(env, "N.", {})
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "standoff" in system
        assert "Two armed toughs block the doorway" in system

    def test_verbal_confrontation_example_present(self):
        env = self._env()
        msgs = _extract_scene_messages(env, "N.", {})
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "tense_confrontation" in system
        assert "guard captain steps into your path" in system
