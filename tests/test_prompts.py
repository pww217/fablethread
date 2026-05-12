"""Tests for narrate prompt templates — momentum directives, Breathe block, system rules."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def _env():
    return Environment(
        loader=FileSystemLoader(str(Path(__file__).parent.parent / "ccya" / "prompts")),
        autoescape=False,
    )


def _make_narrate_user_ctx():
    return {
        "state": {
            "scene": {
                "world_state": [],
                "scene_pressure": [],
                "recent_events": [],
                "present_npcs": [],
            },
            "pc": {"name": "Vex", "tagline": "pilot", "bio": "", "stats": {}},
            "location": {"id": "loc", "name": "Location", "description": "desc"},
            "inventory": [],
            "quests": [],
            "compendium": {"npcs": {}},
        },
        "recently_left": [],
        "chronicle_tail": "",
        "recent_turns": [],
        "rules_outcome": None,
        "npc_name_pool": {},
        "user_input": "test",
        "momentum": 0,
        "pending_gm_beat": None,
        "meta": {"turn": 1},
        "scene": {"scene_pressure": [], "present_npcs": []},
        "deescalate": 0.0,
        "ages": {},
        "known_npcs": [],
        "present_npcs": [],
        "compendium_bios": [],
        "pc_allegiance": None,
        "scene_pressure": [],
        "world_factions": [],
        "world_locations": [],
    }


class TestMomentumDirectives:
    """Momentum floor and low directives must render at correct thresholds."""

    def test_momentum_floor_at_neg3(self):
        """momentum=-3 must produce 'Momentum FLOOR' directive."""
        env = _env()
        ctx = _make_narrate_user_ctx()
        ctx["momentum"] = -3
        text = env.get_template("narrate_user.j2").render(**ctx)
        assert "Momentum FLOOR" in text
        assert "lowest possible momentum" in text

    def test_momentum_low_at_neg2(self):
        """momentum=-2 must produce 'Momentum LOW' directive."""
        env = _env()
        ctx = _make_narrate_user_ctx()
        ctx["momentum"] = -2
        text = env.get_template("narrate_user.j2").render(**ctx)
        assert "Momentum LOW" in text
        assert "struggling" in text

    def test_momentum_no_low_at_neg1(self):
        """momentum=-1 must not produce any momentum low directive."""
        env = _env()
        ctx = _make_narrate_user_ctx()
        ctx["momentum"] = -1
        text = env.get_template("narrate_user.j2").render(**ctx)
        assert "Momentum FLOOR" not in text
        assert "Momentum LOW" not in text

    def test_momentum_high_at_plus2(self):
        """momentum=+2 must produce 'Momentum HIGH' directive."""
        env = _env()
        ctx = _make_narrate_user_ctx()
        ctx["momentum"] = 2
        text = env.get_template("narrate_user.j2").render(**ctx)
        assert "Momentum:" in text
        assert "HIGH" in text


class TestScenePressureInTemplate:
    """scene_pressure bare variable must render in narrate_user.j2."""

    def test_pressure_directive_with_immediate(self):
        """scene_pressure=[{urgency: immediate}] must render Pressure directive."""
        env = _env()
        ctx = _make_narrate_user_ctx()
        ctx["scene_pressure"] = [{"urgency": "immediate", "text": "test"}]
        text = env.get_template("narrate_user.j2").render(**ctx)
        assert "Pressure" in text
        assert "Active immediate threat" in text


class TestBreatheBlock:
    """Breathe block must include de-escalation reward text."""

    def test_breathe_with_deescalate(self):
        """deescalate=1.0 must render updated Breathe block with de-escalation reward."""
        env = _env()
        ctx = _make_narrate_user_ctx()
        ctx["deescalate"] = 1.0
        text = env.get_template("narrate_user.j2").render(**ctx)
        assert "Breathe:" in text
        assert "the player earned this" in text
        assert "retreated or disengaged" in text


class TestNarrateSystemRules:
    """Narrate system prompt must contain new narrator rules."""

    def test_no_repetition_rule_present(self):
        """narrate_system.j2 must contain NO REPETITION RULE."""
        env = _env()
        text = env.get_template("narrate_system.j2").render(pack_style="")
        assert "NO REPETITION RULE" in text
        assert "Do not reuse sensory details" in text

    def test_npc_quantity_rule_present(self):
        """narrate_system.j2 must contain NPC QUANTITY RULE."""
        env = _env()
        text = env.get_template("narrate_system.j2").render(pack_style="")
        assert "NPC QUANTITY RULE" in text
        assert "four guards" in text
        assert "Named individuals are exempt" in text


class TestConditionDurationGuide:
    """extract_state_system.j2 must contain condition duration taxonomy and relevance rule."""

    def test_extract_state_system_has_duration_guide(self):
        """Confirm CONDITION DURATION GUIDE and CONDITION RELEVANCE RULE present in rendered prompt."""
        env = _env()
        text = env.get_template("extract_state_system.j2").render()
        assert "CONDITION DURATION GUIDE" in text
        assert "CONDITION RELEVANCE RULE" in text
        assert "brief (1–2 turns)" in text
        assert "short (3–4 turns)" in text
        assert "medium (5–8 turns)" in text
        assert "long (9+ turns)" in text


class TestNPCEnterExit:
    """extract_scene_system.j2 must contain NPC enter/exit rules."""

    def test_extract_scene_system_has_npc_enter_exit(self):
        """Confirm NPC ENTER/EXIT RULE with all three examples present."""
        env = _env()
        text = env.get_template("extract_scene_system.j2").render()
        assert "NPC ENTER/EXIT RULE" in text
        assert "absence ≠ departure" in text or "absence != departure" in text
        assert "npc_add" in text
        assert "npc_remove" in text
