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


class TestSeedSystemNPCCount:
    """generate_seed_system.j2 present_npcs count must be configurable."""

    def _seed_system_ctx(self):
        from ccya.pack import Constraints, ScenarioBrief

        return {
            "scenario": ScenarioBrief(
                constraints=Constraints(min_named_npcs=2),
            ),
            "overrides": None,
            "name_pool": None,
            "name_seed": 0,
            "world_text": "",
            "style_text": "",
        }

    def test_seed_system_npc_count_override_3(self):
        """npc_count_override=3 must render 'Exactly 3 NPCs'."""
        env = _env()
        ctx = self._seed_system_ctx()
        ctx["npc_count_override"] = 3
        text = env.get_template("generate_seed_system.j2").render(**ctx)
        assert "Exactly 3 NPCs" in text

    def test_seed_system_npc_count_override_0(self):
        """npc_count_override=0 must render 'Exactly 2 NPCs'."""
        env = _env()
        ctx = self._seed_system_ctx()
        ctx["npc_count_override"] = 0
        text = env.get_template("generate_seed_system.j2").render(**ctx)
        assert "Exactly 2 NPCs" in text


class TestSeedUserNPCCount:
    """generate_seed_user.j2 must render npc_count block when override > 0."""

    def _seed_user_ctx(self):
        return {
            "scenario": None,
            "overrides": None,
            "name_pool": None,
            "name_seed": 0,
            "npc_count_override": 0,
        }

    def test_seed_user_npc_count_block_rendered(self):
        """npc_count_override=3 must render npc_count block."""
        env = _env()
        ctx = self._seed_user_ctx()
        ctx["npc_count_override"] = 3
        text = env.get_template("generate_seed_user.j2").render(**ctx)
        assert "## npc_count" in text
        assert "3 NPCs" in text

    def test_seed_user_npc_count_block_absent(self):
        """npc_count_override=0 must not render npc_count block."""
        env = _env()
        ctx = self._seed_user_ctx()
        ctx["npc_count_override"] = 0
        text = env.get_template("generate_seed_user.j2").render(**ctx)
        assert "## npc_count" not in text


class TestSeedNPCAlignmentRule:
    """generate_seed prompts must include NPC role alignment when factions present."""

    def _seed_system_ctx_with_factions(self):
        from ccya.pack import Constraints, Faction, ScenarioBrief

        return {
            "scenario": ScenarioBrief(
                constraints=Constraints(min_named_npcs=2),
                factions=[Faction(id="f1", name="Guard", description="City defenders", disposition="neutral")],
            ),
            "overrides": None,
            "name_pool": None,
            "name_seed": 0,
            "world_text": "",
            "style_text": "",
            "npc_count_override": 0,
        }

    def _seed_user_ctx_with_factions(self):
        from ccya.pack import Faction, ScenarioBrief

        return {
            "scenario": ScenarioBrief(
                factions=[Faction(id="f1", name="Guard", description="City defenders", disposition="neutral")],
                narrator_rules=["Keep it gritty"],
                world_facts=["The city is under siege."],
            ),
            "overrides": None,
            "name_pool": None,
            "name_seed": 0,
            "npc_count_override": 0,
        }

    def test_seed_system_alignment_rule_rendered(self):
        """scenario.factions must trigger NPC ROLE ALIGNMENT RULE in system prompt."""
        env = _env()
        ctx = self._seed_system_ctx_with_factions()
        text = env.get_template("generate_seed_system.j2").render(**ctx)
        assert "NPC ROLE ALIGNMENT RULE" in text
        assert "MANDATORY" in text

    def test_seed_user_npc_generation_context_rendered(self):
        """scenario.factions must trigger npc_generation_context block in user prompt."""
        env = _env()
        ctx = self._seed_user_ctx_with_factions()
        text = env.get_template("generate_seed_user.j2").render(**ctx)
        assert "## npc_generation_context" in text
        assert "Guard" in text
        assert "City defenders" in text
        assert "Keep it gritty" in text
        assert "The city is under siege." in text
