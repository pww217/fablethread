"""Tier-1 engine pipeline tests.

Distinct from test_engine_smoke.py:
- _smoke covers turn-by-turn correctness (parsing, schema, narrate->extract chain).
- _pipeline covers cross-turn invariants, prompt-size budgets, and scope gating.

All tests are mocked end-to-end via _FakeLLM (no real LLM). Stays under
`make test`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccya.engine import (
    EngineConfig,
    _build_jinja_env,
    _extract_progress_messages,
    _extract_scene_messages,
    _extract_state_messages,
    _narrate_messages,
    _rules_messages,
)
from ccya.state import (
    PC_CONDITIONS_MAX,
    load_state,
    save_state,
)

# Reuse the existing fakes / helpers from the smoke suite.
from tests.test_engine_smoke import (
    _FakeLLM,
    _make_state,
    _run,
)


PROMPTS_DIR = str(Path(__file__).parent.parent / "ccya" / "prompts")


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def save_dir(tmp_path: Path) -> Path:
    return tmp_path


def _rich_state(turn: int = 12) -> dict:
    """Eval-pack-equivalent fixture state. Hand-built so this test file does NOT
    depend on the evals/ directory existing.

    Rough shape: 6 inventory items (one with aliases), 3 quests with mixed
    objectives, 2 active conditions, 5 recent_events, 5 compendium NPCs (3
    present), narrative-flavored location.
    """
    return {
        "meta": {
            "game_name": "pipeline-test",
            "turn": turn,
            "setting_pack": "eval-pack",
            "model": "mlx-community/test",
            "compendium_touch_order": ["halden", "tough_a", "tough_b", "caron", "innkeeper"],
        },
        "pc": {
            "name": "Aren Voss",
            "tagline": "Reluctant courier on the merchant road",
            "bio": "Mid-thirties, broad shoulders, careful with words.",
            "stats": {
                "strength": 3,
                "dexterity": 3,
                "wits": 2,
                "lore": 2,
                "charisma": 3,
                "resolve": 3,
            },
            "conditions": [
                {
                    "id": "bruised_ribs",
                    "label": "bruised ribs",
                    "description": "A hard fall left a deep bruise along the right ribs.",
                    "added_turn": 8,
                },
                {
                    "id": "low_morale",
                    "label": "low morale",
                    "description": "Twelve days on the road and an old debt waiting.",
                    "added_turn": 10,
                },
            ],
            "momentum": 0,
        },
        "location": {
            "id": "roadside_inn",
            "name": "The Crossed Keys Inn",
            "description": (
                "A timber-framed inn at the junction of the merchant road and the old "
                "quarry track. Common room half-full, hearth banked low."
            ),
        },
        "inventory": [
            {"id": "credits", "name": "Credits", "amount": 850, "notes": "Common coin."},
            {"id": "iron_dagger", "name": "Iron dagger", "amount": 1, "notes": "Plain crossguard."},
            {"id": "bandages", "name": "Linen bandages", "amount": 3, "notes": "Three rolls."},
            {"id": "brass_key", "name": "Brass key", "amount": 1, "notes": "Halden gave you this."},
            {"id": "merchant_seal", "name": "Halden's merchant seal", "amount": 1, "notes": "Wax sigil."},
            {
                "id": "traveler_cloak",
                "name": "Traveler's cloak",
                "amount": 1,
                "notes": "Oiled wool, hood deep.",
                "aliases": ["cloak", "travel cloak"],
            },
        ],
        "quests": [
            {
                "id": "deliver_the_ledger",
                "title": "Deliver Halden's Ledger",
                "status": "active",
                "objectives": [
                    {"description": "Carry the ledger to Halden.", "done": False, "failed": False},
                    {"description": "Confirm the contract.", "done": False, "failed": False},
                ],
            },
            {
                "id": "clear_the_road_toughs",
                "title": "Clear the Road Toughs",
                "status": "active",
                "objectives": [
                    {"description": "Find out who hired them.", "done": True, "failed": False},
                    {"description": "Convince, pay, or remove them.", "done": False, "failed": False},
                ],
            },
            {
                "id": "settle_the_debt",
                "title": "Settle the Old Debt",
                "status": "active",
                "objectives": [
                    {"description": "Earn 1000 credits.", "done": True, "failed": False},
                    {"description": "Find Caron.", "done": True, "failed": False},
                    {"description": "Pay Caron in person.", "done": False, "failed": False},
                ],
            },
        ],
        "scene": {
            "tagline": "Stew, ledger, watching eyes",
            "tags": ["dialogue", "mid-game"],
            "present_npcs": [
                {"id": "halden", "name": "Halden", "title": "Merchant", "notes": "At the corner table.", "bio": "Honest road merchant."},
                {"id": "tough_a", "name": "Bald Tough", "title": "Road thug", "notes": "By the door.", "bio": "Hired muscle."},
                {"id": "tough_b", "name": "Scarred Tough", "title": "Road thug", "notes": "Hand on hilt.", "bio": "Quick to violence."},
            ],
            "world_state": [
                "The inn sits at a road junction.",
                "Iron coin is universal currency.",
                "The road has been quiet this season.",
            ],
            "recent_events": [
                {"id": "took_contract", "text": "Took Halden's courier contract twelve days ago.", "turn": 0},
                {"id": "bridge_washout", "text": "Two nights in the open after the bridge washed out.", "turn": 4},
                {"id": "warned_at_brindles", "text": "Warned at Brindle's End about road-toughs at the inn.", "turn": 9},
                {"id": "arrived_at_inn", "text": "Arrived at the Crossed Keys this evening.", "turn": 11},
                {"id": "overheard_caron", "text": "Overheard a tough mention 'Caron's coin' before stepping in.", "turn": 12},
            ],
            "scene_pressure": [],
            "turn_entered": 11,
            "recently_left": [],
            "recently_left_turns": 0,
        },
        "compendium": {
            "npcs": {
                "halden": {"name": "Halden", "title": "Merchant", "bio": "Honest road merchant."},
                "tough_a": {"name": "Bald Tough", "title": "Road thug", "bio": "Hired muscle."},
                "tough_b": {"name": "Scarred Tough", "title": "Road thug", "bio": "Quick to violence."},
                "caron": {"name": "Caron", "title": "Old creditor", "bio": "The man you owe coin to."},
                "innkeeper": {"name": "Edda", "title": "Innkeeper", "bio": "Runs the inn alone."},
            },
        },
    }


# ---------------------------------------------------------------------------
# Class A: Token-budget ceilings
# ---------------------------------------------------------------------------


# Character ceilings for each rendered prompt. Picked at ~25% headroom over the
# current eval-pack-shape state. If you intentionally enrich a prompt and these
# break, BUMP the ceiling AND record the change in the commit message — these
# exist to catch unintentional context bloat regressions.
#
# Conversion: ~3.5 chars/token per the engine's trim_messages estimate.
# 25_000 chars ≈ 7.1K tokens, well under prompt_token_budget=32K.
PROMPT_CEILINGS_CHARS = {
    "rules.system": 6_000,
    "rules.user": 8_000,
    "narrate.system": 8_000,
    "narrate.user": 18_000,
    "scene.system": 6_000,
    "scene.user": 14_000,
    "state.system": 8_000,
    "state.user": 14_000,
    "progress.system": 9_000,
    "progress.user": 14_000,
}


class TestTokenBudgetCeilings:
    """Each rendered prompt must stay under its character ceiling.

    Catches context-rot regressions (e.g. unbounded recent_events accumulation,
    forgetting to cap the compendium injection list) before they reach the
    judge or the user.
    """

    @pytest.fixture
    def env(self):
        return _build_jinja_env(PROMPTS_DIR)

    @pytest.fixture
    def state(self):
        return _rich_state()

    def _check(self, msgs: list[dict[str, str]], system_key: str, user_key: str) -> None:
        sys_text = msgs[0]["content"] if msgs and msgs[0]["role"] == "system" else ""
        user_text = msgs[-1]["content"] if msgs else ""
        sys_ceil = PROMPT_CEILINGS_CHARS[system_key]
        user_ceil = PROMPT_CEILINGS_CHARS[user_key]
        assert len(sys_text) < sys_ceil, (
            f"{system_key} prompt exceeded ceiling: {len(sys_text)} >= {sys_ceil} chars"
        )
        assert len(user_text) < user_ceil, (
            f"{user_key} prompt exceeded ceiling: {len(user_text)} >= {user_ceil} chars"
        )

    def test_rules_prompt_under_ceiling(self, env, state):
        msgs = _rules_messages(env, state, "Walk over to Halden and sit down.", recent_turns=[])
        self._check(msgs, "rules.system", "rules.user")

    def test_narrate_prompt_under_ceiling(self, env, state):
        msgs = _narrate_messages(
            env,
            state,
            "Walk over to Halden and sit down.",
            chronicle_tail="",
            recent_turns=[],
        )
        self._check(msgs, "narrate.system", "narrate.user")

    def test_extract_scene_prompt_under_ceiling(self, env, state):
        msgs = _extract_scene_messages(
            env,
            "Walk over to Halden and sit down.",
            state,
            active_domains=["scene"],
        )
        self._check(msgs, "scene.system", "scene.user")

    def test_extract_state_prompt_under_ceiling(self, env, state):
        from ccya.models import RulesOutcome, SceneExtractResult

        scene_result = SceneExtractResult(scene_tags=["dialogue"], outcome_summary="ok")
        msgs = _extract_state_messages(
            env,
            "You crossed the room to Halden's table and sat across from him.",
            state,
            active_domains=["inventory", "pc_condition"],
            scene_result=scene_result,
            rules_outcome=RulesOutcome(rolled=False),
            pack_examples=None,
        )
        self._check(msgs, "state.system", "state.user")

    def test_extract_progress_prompt_under_ceiling(self, env, state):
        from ccya.models import RulesOutcome, SceneExtractResult, StateExtractResult

        scene_result = SceneExtractResult(scene_tags=["dialogue"], outcome_summary="ok")
        state_result = StateExtractResult()
        msgs = _extract_progress_messages(
            env,
            "You crossed the room to Halden's table and sat across from him.",
            state,
            active_domains=["quest_updates", "recent_events", "compendium_npc"],
            scene_result=scene_result,
            state_result=state_result,
            rules_outcome=RulesOutcome(rolled=False),
            deescalate=False,
        )
        self._check(msgs, "progress.system", "progress.user")


# ---------------------------------------------------------------------------
# Class B: Multi-turn invariants
# ---------------------------------------------------------------------------


def _state_response(
    *,
    inv_add: list[dict] | None = None,
    inv_remove: list[dict] | None = None,
    cond_add: list[dict] | None = None,
) -> str:
    return json.dumps(
        {
            "inventory_add": inv_add or [],
            "inventory_remove": inv_remove or [],
            "inventory_update": [],
            "pc_condition_add": cond_add or [],
            "pc_condition_remove": [],
            "failed": [],
        },
    )


def _progress_response(
    *,
    rec_add: list[dict] | None = None,
    quest_updates: list[dict] | None = None,
    npc_updates: list[dict] | None = None,
) -> str:
    return json.dumps(
        {
            "quest_updates": quest_updates or [],
            "recent_events_add": rec_add or [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": npc_updates or [],
        },
    )


def _scene_response(*, tags: list[str] | None = None) -> str:
    return json.dumps(
        {
            "scene_tags": tags or ["dialogue"],
            "scene_tagline": "",
            "location_change": None,
            "location_description": None,
            "actions": ["A", "B", "C", "D"],
            "outcome_summary": "ok",
        },
    )


@pytest.mark.asyncio
async def test_multi_turn_no_inventory_dupes_and_recent_events_bounded(save_dir):
    """Drive 5 turns; each adds the same inventory id repeatedly. Assert that
    the final inventory has no duplicate id (engine merges into a stack via
    apply_delta) and recent_events stays bounded by recent_events_max.
    """
    state = _make_state(turn=0)
    state["scene"]["recent_events"] = []
    save_state(save_dir, state)

    cfg = EngineConfig(recent_events_max=3)

    for turn_idx in range(5):
        with _FakeLLM(
            narrative=f"Turn {turn_idx + 1} narrative goes here, plain prose.",
            scene_response=_scene_response(),
            state_response=_state_response(
                inv_add=[{"id": "torch", "name": "Torch", "amount": 1}]
            ),
            progress_response=_progress_response(
                rec_add=[
                    {"id": f"event_t{turn_idx + 1}", "text": f"thing happened on turn {turn_idx + 1}", "turn": turn_idx + 1},
                ],
            ),
        ):
            await _run(save_dir, f"do thing {turn_idx + 1}", config=cfg)

    final = load_state(save_dir)

    assert final["meta"]["turn"] == 5
    torch_entries = [i for i in final["inventory"] if i["id"] == "torch"]
    assert len(torch_entries) == 1, f"torch was duplicated, not stacked: {torch_entries}"
    assert torch_entries[0]["amount"] == 5, f"expected stack of 5 torches, got {torch_entries[0]}"
    rec = final["scene"]["recent_events"]
    assert len(rec) <= cfg.recent_events_max, (
        f"recent_events exceeded max: {len(rec)} > {cfg.recent_events_max}"
    )


@pytest.mark.asyncio
async def test_multi_turn_compendium_grows_by_unique_npcs(save_dir):
    """Across turns, introducing new + repeated NPCs should grow the compendium
    by the count of unique IDs only (not by raw event count).
    """
    state = _make_state(turn=0)
    state["scene"]["present_npcs"] = []
    save_state(save_dir, state)

    introductions = [
        ["alice"],
        ["alice", "bob"],
        ["bob", "carol"],
        ["alice", "bob", "carol"],
        ["dave"],
    ]

    for turn_idx, ids in enumerate(introductions):
        npc_updates = [
            {"id": nid, "name": nid.title(), "title": "guide", "bio": f"bio of {nid}"}
            for nid in ids
        ]
        with _FakeLLM(
            scene_response=_scene_response(),
            progress_response=_progress_response(npc_updates=npc_updates),
        ):
            await _run(save_dir, f"meet {','.join(ids)}")

    final = load_state(save_dir)
    npcs = final["compendium"]["npcs"]
    assert set(npcs.keys()) == {"alice", "bob", "carol", "dave"}, (
        f"unexpected compendium keys: {sorted(npcs.keys())}"
    )


@pytest.mark.asyncio
async def test_pc_conditions_cap_holds_across_turns(save_dir):
    """Adding more than PC_CONDITIONS_MAX conditions must evict oldest FIFO."""
    state = _make_state(turn=0)
    save_state(save_dir, state)

    for i in range(PC_CONDITIONS_MAX + 2):
        with _FakeLLM(
            state_response=_state_response(
                cond_add=[
                    {
                        "id": f"cond_{i}",
                        "label": f"cond {i}",
                        "description": f"description for cond {i}",
                    },
                ],
            ),
        ):
            await _run(save_dir, f"acquire cond {i}")

    final = load_state(save_dir)
    conds = final["pc"]["conditions"]
    assert len(conds) == PC_CONDITIONS_MAX, (
        f"expected exactly {PC_CONDITIONS_MAX} conditions, got {len(conds)}"
    )
    cond_ids = [c["id"] for c in conds]
    assert "cond_0" not in cond_ids, "oldest condition (cond_0) was not evicted"
    assert f"cond_{PC_CONDITIONS_MAX + 1}" in cond_ids, (
        "newest condition is missing from final state"
    )


# ---------------------------------------------------------------------------
# Class C: Rules + scope correctness
# ---------------------------------------------------------------------------


_RULES_SKIP_STATE = json.dumps(
    {
        "intent": "look around",
        "intent_verb": "observe",
        "target": "",
        "stakes": "",
        "check": {"required": False},
    },
)


class _ScopedFakeLLM(_FakeLLM):
    """Variant of _FakeLLM that yields a narrative with scope tail.

    Routes calls 1=rules (custom), 2=scene, 3=progress (state is skipped
    because narrator emitted active_domains=['scene']).
    """

    def __init__(
        self,
        rules_response: str = _RULES_SKIP_STATE,
        **kwargs,
    ) -> None:
        narrative_with_scope = kwargs.get("narrative", "narrative text") + '\n\n<scope>{"active_domains":["scene","quest_updates","recent_events","compendium_npc"]}</scope>'
        kwargs["narrative"] = narrative_with_scope
        super().__init__(**kwargs)
        self._rules_response = rules_response
        _self = self

        async def _fake_chat(*args, **kwargs):
            _self.call_log.append({"kind": "chat", "args": args, "kwargs": kwargs})
            chat_calls = [c for c in _self.call_log if c["kind"] == "chat"]
            n = len(chat_calls)
            if n == 1:
                return {"response": _self._rules_response, "done": True, "usage": {"prompt_tokens": 30, "total_tokens": 40}}
            if n == 2:
                return {"response": _self._scene_response, "done": True, "usage": {"prompt_tokens": 100, "total_tokens": 200}}
            # When narrator scope excludes state domains the engine should NOT make a state extraction call.
            # The next call is progress.
            return {"response": _self._progress_response, "done": True, "usage": {"prompt_tokens": 90, "total_tokens": 180}}

        self._fake_chat = _fake_chat


@pytest.mark.asyncio
async def test_narration_scope_tail_skip_state_skips_state_extraction(save_dir):
    """If narrator emits <scope>{"active_domains":["scene"]}</scope>, the state
    extraction call must NOT be made AND no inventory_add from a hypothetical
    state response can possibly leak into applied state."""
    state = _make_state(turn=0)
    save_state(save_dir, state)

    fake = _ScopedFakeLLM(
        scene_response=_scene_response(),
        # If state extraction WERE called, this would add a torch. It must not be.
        state_response=_state_response(
            inv_add=[{"id": "torch", "name": "Torch", "amount": 1}]
        ),
        progress_response=_progress_response(),
    )
    with fake:
        result = await _run(save_dir, "look around")

    chat_count = len(fake.chat_calls())
    assert chat_count == 3, (
        f"expected 3 chat calls (rules + scene + progress), got {chat_count}"
    )
    final = load_state(save_dir)
    assert all(i["id"] != "torch" for i in final["inventory"]), (
        "state extraction was supposed to be skipped, but inventory got the torch"
    )
    assert "torch" not in (result.applied.get("inventory_add") or [])


@pytest.mark.asyncio
async def test_rules_no_check_does_not_add_rules_metric(save_dir):
    """When intent is trivial (intent_verb='act' default and check.required=False),
    the engine writes a minimal event without a 'rules' key in the events.jsonl
    entry (or with rolled=False). Verify TurnResult.rules is empty/dict."""
    state = _make_state(turn=0)
    save_state(save_dir, state)

    fake = _FakeLLM()  # uses _RULES_NO_ROLL by default
    with fake:
        result = await _run(save_dir, "stand still")

    assert isinstance(result.rules, dict)
    if result.rules:
        assert result.rules.get("rolled", False) is False, (
            f"unexpected rolled=True for trivial intent: {result.rules}"
        )
