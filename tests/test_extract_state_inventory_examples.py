"""Verify extract_state_system.j2 renders the new spending/giving examples."""

from pathlib import Path

from ccya.engine import _build_jinja_env, _extract_state_messages


class TestExtractStateInventoryExamples:
    """Verify the spending/giving few-shot examples are rendered in the system prompt."""

    def _env(self):
        return _build_jinja_env(str(Path(__file__).parent.parent / "ccya" / "prompts"))

    def test_key_use_example_present(self):
        env = self._env()
        msgs = _extract_state_messages(env, "N.", {})
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "brass_key" in system
        assert "brass key into the lock" in system

    def test_npc_pays_pc_example_present(self):
        env = self._env()
        msgs = _extract_state_messages(env, "N.", {})
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "Halden counts out a hundred credits" in system
        assert '"amount": 100' in system

    def test_vague_payment_amount_1(self):
        env = self._env()
        msgs = _extract_state_messages(env, "N.", {})
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert '"amount": 1' in system
