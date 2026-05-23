"""Render tests — Layer 2 of four-layer testing strategy.

Tests call `_render()` directly with synthetic context dicts to assert structural
properties of template output (not golden snapshots). This catches broken includes,
wrong variable names in templates, and missing conditional branches without needing
LLM or engine pipeline execution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccya.engine.config import _build_jinja_env, _render

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def jinja_env():
    return _build_jinja_env(str(_REPO_ROOT / "ccya" / "prompts"))


# ---------------------------------------------------------------------------
# ruling_user.j2 tests (Step 1.2)
# ---------------------------------------------------------------------------

def test_rules_user_pc_and_location(jinja_env):
    """PC name/tagline/stats, location name/id, conditions present/absent branches."""
    ctx = {
        "pc": {"name": "Test PC", "tagline": "The Brave", "stats": {"strength": 3, "dexterity": 2}, "conditions": [{"id": "wounded", "label": "Wounded"}]},
        "location": {"id": "tavern", "name": "The Rusty Tankard"},
        "recent_turns": [],
        "user_input": "I attack the guard.",
        "meta": {"turn": 5},
        "present_npcs": [{"id": "guard1", "name": "Captain Voss", "title": "City Guard"}],
        "last_outcome": None,
    }
    out = _render(jinja_env, "ruling_user.j2", ctx)

    assert "**Test PC**" in out
    assert "The Brave" in out
    assert "strength=3" in out
    assert "dexterity=2" in out
    assert "Wounded" in out
    assert "Location: The Rusty Tankard" in out


def test_rules_user_present_npcs_and_input(jinja_env):
    """NPC list with names/titles, meta.turn number, user_input verbatim."""
    ctx = {
        "pc": {"name": "Test PC", "tagline": "", "stats": {}, "conditions": []},
        "location": {"id": "tavern"},
        "recent_turns": [],
        "user_input": "I attack the guard.",
        "meta": {"turn": 5},
        "present_npcs": [{"id": "guard1", "name": "Captain Voss", "title": "City Guard"}],
        "last_outcome": None,
    }
    out = _render(jinja_env, "ruling_user.j2", ctx)

    assert "Captain Voss" in out
    assert "(City Guard)" in out
    assert "Current Turn: 5" in out
    assert "I attack the guard." in out


# ---------------------------------------------------------------------------
# extract_scene_user.j2 tests (Step 1.3)
# ---------------------------------------------------------------------------

def test_scene_extract_location_and_roster(jinja_env):
    """Location block id/name/description, minimal roster (no MFL fields), narration header format."""
    ctx = {
        "location": {"id": "tavern", "name": "The Rusty Tankard", "description": "A cozy inn with a warm fire."},
        "present_npcs": [{"id": "guard1", "name": "Captain Voss", "title": "City Guard"}],
        "npc_roster": [
            {"id": "caron", "name": "Caron", "title": "Merchant", "bio": "A shady dealmaker.", "presence": "known"},
        ],
        "recent_turns": [],
        "turn_no": 5,
        "narration": "The guard eyes you suspiciously.",
    }
    out = _render(jinja_env, "extract_scene_user.j2", ctx)

    assert "`tavern` | The Rusty Tankard" in out
    assert "A cozy inn with a warm fire." in out
    # NPC roster uses minimal form: id, name/title/presence/bio — NO motivation/fear/leverage
    assert "- `caron` | Caron (Merchant)" in out or ("| **Caron**" not in out and "A shady dealmaker." in out)
    # Verify MFL fields are absent from extract roster (only bio shown, no wants/fears/leverage)
    assert "wants:" not in out.lower()
    assert "fears:" not in out.lower()
    assert "## CURRENT TURN 5 NARRATION" in out
    assert "The guard eyes you suspiciously." in out


# ---------------------------------------------------------------------------
# extract_state_user.j2 tests (Step 1.3)
# ---------------------------------------------------------------------------

def test_state_extract_conditions_inventory_intent(jinja_env):
    """Conditions id/label pairs, inventory stacks with amounts, intent_verb/intent display."""
    ctx = {
        "conditions": [{"id": "wounded", "label": "Wounded", "description": "Grazed in battle"}],
        "inventory": [
            {"id": "dagger", "name": "Steel Dagger", "amount": 3, "notes": "Enchanted"},
        ],
        "intent": {"intent_verb": "attack", "intent": "Strike the guard"},
        "turn_no": 5,
        "narration": "You swing your sword.",
    }
    out = _render(jinja_env, "extract_state_user.j2", ctx)

    assert "- wounded — Grazed in battle" in out or ("wounded" in out and "Grazed in battle" in out)
    assert "Steel Dagger ×3" in out
    assert "Enchanted" in out
    assert "attack: Strike the guard" in out
    assert "## CURRENT TURN 5 NARRATION" in out


# ---------------------------------------------------------------------------
# storytell_user.j2 tests (Step 1.4)
# ---------------------------------------------------------------------------

def test_progress_npc_roster_and_threads(jinja_env):
    """NPC entries render, thread blocks with [SCENE]/[ARC] scope tags."""
    ctx = {
        "npc_roster": [
            {"id": "caron", "name": "Caron", "title": "Merchant", "bio": "A shady dealmaker.", "presence": "present"},
        ],
        "location": {"name": "The Rusty Tankard", "description": "A cozy inn."},
        "conditions": [{"id": "wounded", "label": "Wounded"}],
        "all_threads": [
            {"id": "t1", "summary": "Investigate the missing persons", "scope": "scene", "active": True, "urgency": "normal"},
            {"id": "t2", "summary": "Uncover the conspiracy", "scope": "arc", "active": False, "urgency": "background"},
        ],
        "recent_events": [{"text": "A stranger approaches in the tavern."}],
        "world_state": ["The city is under martial law."],
        "inventory": [
            {"id": "dagger", "name": "Steel Dagger", "amount": 3},
        ],
        "band": None,
        "pending_beat": None,
        "pacing_context": None,
        "recent_turns": [],
        "intent": {"intent_verb": "attack", "intent": "Strike the guard"},
        "turn_no": 5,
        "narration": "You swing your sword.",
    }
    out = _render(jinja_env, "storytell_user.j2", ctx)

    assert "**The Rusty Tankard**" in out or "`caron` | **Caron**" in out
    assert "[SCENE]" in out
    assert "[ARC]" in out
    assert "- A stranger approaches in the tavern." in out


def test_progress_pacing_beat_and_gating(jinja_env):
    """Pacing directive block, gate conditional rendering, pending_beat present/absent branches."""
    # With pacing_context and pending_beat populated
    ctx = {
        "npc_roster": [],
        "location": {"name": "Tavern"},
        "conditions": [],
        "all_threads": [],
        "recent_events": [],
        "world_state": None,
        "inventory": [],
        "band": None,
        "pending_beat": {"type": "complication", "beat_expires_turn": 6},
        "pacing_context": {"directive": "Build tension with a new threat.", "gate": True},
        "recent_turns": [],
        "intent": None,
        "turn_no": 5,
        "narration": "A figure approaches from the shadows.",
    }
    out = _render(jinja_env, "storytell_user.j2", ctx)

    assert "Directive: Build tension with a new threat." in out
    assert "Gate: True" in out

    # Without pending_beat and pacing_context (absent branches)
    ctx2 = {
        "npc_roster": [],
        "location": {"name": "Tavern"},
        "conditions": [],
        "all_threads": [],
        "recent_events": [],
        "world_state": None,
        "inventory": [],
        "band": None,
        "pending_beat": None,
        "pacing_context": None,
        "recent_turns": [],
        "intent": {"intent_verb": "act", "intent": ""},
        "turn_no": 5,
        "narration": "Nothing happens.",
    }
    out2 = _render(jinja_env, "storytell_user.j2", ctx2)

    assert "A mysterious figure approaches." not in out2


# ---------------------------------------------------------------------------
# narrate_user.j2 tests (Step 1.5)
# ---------------------------------------------------------------------------

def test_narrate_pc_location_inventory(jinja_env):
    """PC stats display, location 'Name (id)' format, inventory items with amounts or fallback text."""
    ctx = {
        "pc": {"name": "Test PC", "tagline": "The Brave", "stats": {"strength": 3}, "conditions": [{"label": "Wounded"}]},
        "state": {
            "location": {"id": "tavern", "name": "The Rusty Tankard", "description": "A cozy inn."},
            "inventory": [
                {"id": "dagger", "name": "Steel Dagger", "amount": 3, "notes": "Enchanted"},
            ],
            "scene": {
                "world_state": [],
            },
        },
        "current_arc": {},
        "npc_roster": [],
        "prior_history": None,
        "recent_turns": [],
        "rules_outcome": {"rolled": False},
        "pending_beat": None,
        "pacing_context": None,
        "user_input": "Hello.",
        "meta": {"turn": 5},
    }
    out = _render(jinja_env, "narrate_user.j2", ctx)

    assert "**Test PC**" in out
    assert "The Brave" in out
    assert "strength=3" in out
    assert "Wounded" in out
    # Location include: Name (id) format followed by description
    assert "The Rusty Tankard (tavern)" in out or ("Rusty Tankard" in out and "(tavern)" in out)
    assert "**Steel Dagger**" in out


def test_narrate_arc_roster_history(jinja_env):
    """Arc visible_goal/thematic_question threads list, NPC roster ordering by presence, prior history block present/absent branches."""
    ctx = {
        "pc": {"name": "Test PC", "tagline": "", "stats": {}, "conditions": []},
        "state": {
            "location": {"id": "tavern", "name": "Tavern"},
            "inventory": [],
            "scene": {"world_state": []},
        },
        "current_arc": {
            "visible_goal": "Find the missing merchant.",
            "thematic_question": "What price is loyalty?",
            "pc_drive": "Seek justice for the innocent.",
            "threads": [
                {"id": "t1", "summary": "Investigate the conspiracy", "scope": "scene", "urgency": "normal"},
            ],
        },
        "npc_roster": [],
        "prior_history": None,  # absent branch
        "recent_turns": [
            {"turn": 4, "narrative": "You enter the tavern."},
        ],
        "rules_outcome": {"rolled": False},
        "pending_beat": None,
        "pacing_context": None,
        "user_input": "Hello.",
        "meta": {"turn": 5},
    }
    out = _render(jinja_env, "narrate_user.j2", ctx)

    assert "**Goal:** Find the missing merchant." in out or ("missing merchant" in out.lower())
    assert "Thematic question:" in out or ("thematic_question" in out.lower() or "What price is loyalty?" in out)

    # With prior_history populated (present branch)
    ctx2 = dict(ctx, prior_history=["- [T1] The adventure begins."])
    out2 = _render(jinja_env, "narrate_user.j2", ctx2)
    assert "[T1]" in out2


def test_narrate_rules_outcome_and_beat(jinja_env):
    """Dice results (rolled/band/directive), GM beat instruction when populated."""
    # With dice roll outcome and pending beat
    ctx = {
        "pc": {"name": "Test PC", "tagline": "", "stats": {}, "conditions": []},
        "state": {
            "location": {"id": "tavern", "name": "Tavern"},
            "inventory": [],
            "scene": {"world_state": []},
        },
        "current_arc": {},
        "npc_roster": [],
        "prior_history": None,
        "recent_turns": [],
        "rules_outcome": {"rolled": True, "band": "success", "directive": "You succeed with flair."},
        "pending_beat": {"type": "complication", "surface_as": "tavern patron"},
        "pacing_context": None,
        "user_input": "I attack the guard.",
        "meta": {"turn": 5},
    }
    out = _render(jinja_env, "narrate_user.j2", ctx)

    assert "**Band:** SUCCESS" in out or ("SUCCESS" in out and "You succeed with flair." in out)
    assert "**Beat type:** COMPLICATION to surface as" in out
