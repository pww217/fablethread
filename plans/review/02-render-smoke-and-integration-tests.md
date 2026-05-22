# 02-render-smoke-and-integration-tests

## Status
`open`

## Phases

4 phases covering render tests (Layer 2), FakeLLM infrastructure, smoke tests (Layer 3 part A), and eval framework integration with pytest.

## Issue

After Plan 1 establishes typed boundary models and alignment checks, there are no tests that exercise actual template rendering or the engine pipeline. Without these:
- Template bugs (broken includes, wrong variable names in templates) go undetected until a turn fails at runtime
- Wiring mistakes between prompt builders and their callers aren't caught
- The eval scenario framework exists but can only be run through its own runner — not reused as pytest fixtures for pipeline-level testing

## Solution

Build three execution-layer test types:
1. **Render tests** that call `_render()` directly with synthetic context, asserting structural properties of template output (not golden snapshots)
2. **Smoke tests** that run the full engine pipeline with a FakeLLM returning controlled responses per pipeline step
3. **Integration tests** that import existing eval scenarios as pytest fixtures and run them through the engine pipeline

## Firm decisions

1. Render tests call `_render()` directly — they do NOT go through prompt builder functions (`_rules_messages`, etc.). This keeps render tests focused on template correctness, not context assembly logic (that's covered by Plan 1's schema tests).
2. FakeLLM is a single shared fixture in `tests/conftest.py` that both smoke and integration tests use. It implements the async methods needed to replace `llm_chat` and `llm_chat_stream`.
3. Eval scenarios are NOT modified or moved. They stay as Python modules under `evals/scenarios/` importable by pytest via dynamic module loading (same mechanism used by existing eval runner).
4. No golden snapshots of full prompt text. Tests assert structural properties: specific blocks appear when data is populated, absent when not. This survives whitespace-only template reformatting.
5. FakeLLM responses are stored as inline strings in test files — no external fixture files needed. Each pipeline step (rules/narrate/scene/state/progress) has its own response per turn.

## Non-goals

- Modifying existing eval scenario definitions or their assertions
- Adding new LLM client features (retry logic, thinking mode toggles for tests)
- Testing compaction behavior in smoke/integration layers (that's a separate concern)
- Covering edge cases like network timeouts or HTTP errors in FakeLLM — that's covered by error handling tests elsewhere

## Risks, Ambiguities, and Blockers

1. **Ambiguity: how to patch LLM calls for testing.** The engine imports `llm_chat` and `llm_chat_stream` from `ccya.llm_client`. Tests need to replace these with FakeLLM methods. The cleanest approach is monkeypatching at the import site in `ccya/engine/rules.py`, `narrate.py`, and `extraction.py` — patching where they're used, not where they're defined (standard Python mock pattern).
2. **Ambiguity: how FakeLLM tracks turn state.** The engine's 5-call pipeline processes rules→narrate→scene/state/progress in sequence per turn. FakeLLM needs to return the correct fixture response for each call and advance its internal counter after progress extraction (which signals end-of-turn). This is a simple state machine with one counter.
3. **Risk: narrate phase uses streaming.** FakeLLM's `stream()` method must yield tokens incrementally, not return all at once. The engine awaits token events during narration — if FakeLLM doesn't properly async-generate, the pipeline will hang or timeout.
4. **Blocker: none.** This plan depends on Plan 1 being complete (boundary models exist for render test context construction), but can be designed independently.

## Implementation — Phase 1: Render tests (Layer 2)

### Context files to load
- `ccya/engine/config.py` — `_render()` function and `_build_jinja_env()` signatures
- All user prompt templates in `ccya/prompts/`: extract_progress_user.j2, narrate_user.j2, rules_user.j2, extract_scene_user.j2, extract_state_user.j2
- Section include files: _arc.j2, _inventory.j2, _location.j2, _npc_roster.j2, _npc_roster_extract.j2, _world_state.j2

### Detailed steps

#### Step 1.1 — Create render test file with Jinja env setup helper

**File:** `tests/test_render.py` (new)

**What:** Pytest module that sets up a shared `jinja_env` fixture and defines render tests for each user prompt template. The fixture creates a Jinja Environment pointing at the prompts directory using an absolute path resolved from the test file location:

```python
from pathlib import Path
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]  # repo root is parent of tests/

@pytest.fixture(scope="session")
def jinja_env():
    from ccya.engine.config import _build_jinja_env
    return _build_jinja_env(str(_REPO_ROOT / "ccya" / "prompts"))
```

Each render test follows this pattern:
1. Build a minimal synthetic context dict that exercises the template's structural branches (populated vs empty data)
2. Call `_render(jinja_env, "template_name.j2", ctx)` directly — NOT through prompt builder functions
3. Assert structural properties of rendered output using targeted string checks

**Why:** Render tests exercise templates in isolation from Python logic. They catch broken includes, wrong variable names in templates, and missing conditional branches. No LLM or engine pipeline needed.

#### Step 1.2 — Write render test for rules_user.j2

**File:** `tests/test_render.py` (continued)

**What:** Test that asserts structural properties of the rules prompt:
- PC name/tagline appear in output when populated
- Stats are rendered as key=value pairs (e.g., "strength=3")
- Conditions list renders condition labels when present, is absent when empty
- Location name/id render correctly
- Present NPCs list appears with names/titles/notes when provided, section header or absence when empty
- `meta.turn` shows the turn number passed in context
- `user_input` text appears verbatim in output

**Context structure:** Minimal dict matching RulesBoundary field names:
```python
ctx = {
    "pc": {"name": "Test PC", "tagline": "The Brave", "stats": {"strength": 3, "dexterity": 2}, "conditions": [{"id": "wounded", "label": "Wounded"}]},
    "location": {"id": "tavern", "name": "The Rusty Tankard"},
    "recent_turns": [],
    "user_input": "I attack the guard.",
    "meta": {"turn": 5},
    "present_npcs": [{"id": "guard1", "name": "Captain Voss", "title": "City Guard"}],
    "last_outcome": None,
}
```

**Why:** Rules prompt is minimal — fewest variables of any template. Good starting point to validate render test infrastructure and structural assertion patterns.

#### Step 1.3 — Write render tests for extract_scene_user.j2 and extract_state_user.j2

**File:** `tests/test_render.py` (continued)

**What:** Two targeted render tests:

**Scene Extract assertions:**
- Location block renders with id/name/description from context
- NPC roster entries appear in minimal form (id, name/title/presence/bio only — NO motivation/fear/leverage)
- Present NPCs list shows names/titles when populated
- Narration appears with numbered header format like "Turn 5: ..."

**State Extract assertions:**
- Conditions render with id/label/description pairs
- Inventory stacks show name, amount (e.g., "Steel Dagger ×3"), and notes
- Intent block renders intent_verb/intent from rules engine output
- Narration appears with numbered header format

These are the simplest templates — 17 lines each. Tests should be equally targeted.

#### Step 1.4 — Write render test for extract_progress_user.j2 (primary target)

**File:** `tests/test_render.py` (continued)

**What:** The most complex user prompt template. Assert structural properties of its key sections:
- NPC roster include renders with entries from context
- Location block shows name/id/description
- PC conditions list appears when populated, absent section when empty
- Thread blocks render with scope tags `[SCENE]` or `[ARC]` prefix
- Recent events appear in output format (bullet/list)
- World state facts render via include when present in scene data
- Inventory stacks show name/amount/notes
- Pacing directive appears as a single block of text
- Gate status renders only when pacing_context.gate is True
- Pending beat instruction surfaces when populated, absent section when None
- Player intent displays intent_verb/intent from rules engine

**Context structure:** Minimal dict matching ProgressExtractBoundary field names with both populated and empty branches exercised.

**Why:** This template has the most complexity — multiple includes, conditional sections, scope-tagged threads. It's the primary target for render coverage per the design doc. If this test passes, confidence in other templates is high.

#### Step 1.5 — Write render tests for narrate_user.j2 (secondary target)

**File:** `tests/test_render.py` (continued)

**What:** The largest user prompt template with most includes. Assert structural properties of its key sections:
- PC block renders name/tagline/stats/conditions when populated
- Location include shows "Name (id)" format followed by description
- Inventory include lists items with amount multipliers, or "Nothing of note." fallback when empty
- Arc include shows visible_goal/thematic_question/pc_drive and active threads list with scope/urgency
- NPC roster include orders entries PRESENT → JUST_LEFT → KNOWN with bio/notes/motivation/fear/leverage for rich variant
- Prior history compaction block appears when prior_history is populated, absent section when empty
- Recent turns window shows correct number of entries with turn numbers and narratives
- Rules outcome displays dice results: rolled status, band string (e.g., "success"), directive text
- GM beat instruction surfaces in pending_beat section when present, absent when None
- Pacing directive renders as single block; beat_hint appears only when non-empty
- World state facts render via include when scene.world_state is populated
- Faction list shows name/disposition pairs when world_factions are provided

**Context structure:** Full dict matching NarratorBoundary field names with rich data exercising most branches.

**Why:** Secondary target per design doc — directive and beat rendering validation. The largest template, so tests should focus on the most structurally significant sections rather than exhaustively checking every variable.

### Tests to write or update

- `tests/test_render.py`:
  - `_get_jinja_env()` session-scoped fixture
  - `test_rules_user_pc_and_location()` — PC name/tagline/stats, location name/id, conditions present/absent branches
  - `test_rules_user_present_npcs_and_input()` — NPC list with names/titles, meta.turn number, user_input verbatim
  - `test_scene_extract_location_and_roster()` — location block id/name/description, minimal roster (no MFL fields), narration header format
  - `test_state_extract_conditions_inventory_intent()` — conditions id/label pairs, inventory stacks with amounts, intent_verb/intent display
  - `test_progress_npc_roster_and_threads()` — NPC entries render, thread blocks with [SCENE]/[ARC] scope tags
  - `test_progress_pacing_beat_and_gating()` — pacing directive block, gate conditional rendering, pending_beat present/absent branches
  - `test_narrate_pc_location_inventory()` — PC stats display, location "Name (id)" format, inventory items with amounts or fallback text
  - `test_narrate_arc_roster_history()` — arc visible_goal/thematic_question threads list, NPC roster ordering by presence, prior history block present/absent branches
  - `test_narrate_rules_outcome_and_beat()` — dice results (rolled/band/directive), GM beat instruction when populated

### REPOMAP updates required

- Add entry for `tests/test_render.py` under "Test suite" section describing render tests as Layer 2 of the four-layer strategy
- Note that render tests call `_render()` directly, not through prompt builder functions

---

## Implementation — Phase 2: FakeLLM infrastructure

### Context files to load
- `ccya/llm_client.py` — `chat()` and `chat_stream()` signatures for understanding what needs mocking
- `ccya/engine/rules.py` — how `_call_rules` uses llm_chat (non-streaming)
- `ccya/engine/narrate.py` — how narrate uses chat_stream (streaming tokens)
- `ccya/engine/extraction.py` — how extraction streams use LLM calls

### Detailed steps

#### Step 2.1 — Create FakeLLM in conftest.py

**File:** `tests/conftest.py` (new or updated if exists)

**What:** Pytest fixture module defining a `FakeLLM` class that replaces both non-streaming (`chat`) and streaming (`chat_stream`) LLM calls at their import sites. The FakeLLM tracks which pipeline step is being called via phase name detection in the messages, returns pre-defined responses per turn, and advances its internal counter after progress extraction (end-of-turn signal).

Key design:
- `responses` dict maps phase names to lists of response strings — one entry per turn
  - `"rules"` → list of JSON strings containing IntentEnvelope + RulesOutcome dicts. Must be valid JSON that survives `_find_json()` in rules.py line 89 (no thinking tags, no markdown code fences). Example: `'{"intent": "attack", "intent_verb": "attack", "check": {"required": false}}'`
  - `"narrate"` → list of prose text strings
  - `"extract_scene"` → list of JSON strings containing SceneExtractResult dicts
  - `"extract_state"` → list of JSON strings containing StateExtractResult dicts  
  - `"extract_progress"` → list of JSON strings containing ProgressExtractResult dicts
- `_turn_counter` tracks current turn number, advances after progress extraction response is returned

**Method signatures (must match `llm_client.py` exactly):**
```python
class FakeLLM:
    def __init__(self):
        self.responses = { ... }  # phase → list of strings per turn
        self._turn_counter = 0
    
    async def chat(self, host: str, model: str, messages: list[dict[str, str]], *, temperature=None, timeout=180.0) -> dict[str, Any]:
        """Non-streaming replacement matching llm_client.chat() signature (llm_client.py line 249)."""
        phase = self._detect_phase(messages)
        response_text = self.responses[phase][self._turn_counter]
        return {"response": response_text, "done": True, "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
    
    async def stream(self, host: str, model: str, messages: list[dict[str, str]], *, temperature=None, timeout=180.0):
        """Streaming replacement matching llm_client.chat_stream() signature (llm_client.py line 209). Async generator yielding strings."""
        phase = self._detect_phase(messages)
        response_text = self.responses[phase][self._turn_counter]
        for token in response_text.split():
            yield token
    
    def _detect_phase(self, messages: list[dict[str, str]]) -> str:
        """Determine phase from message content (system prompt text or template name hints)."""
```

**Rules phase JSON format note:** FakeLLM's `"rules"` responses must be plain JSON strings without thinking tags or markdown code fences. The rules pipeline calls `strip_thinking()` then `_find_json()` on the response (`rules.py:88-89`). If a test needs reasoning, include it as a field in the JSON dict (e.g., `{"intent": "attack", "_reasoning": "...", ...}`).

**Why:** FakeLLM is shared infrastructure needed by both smoke tests (Phase 3) and integration tests with eval scenarios. A single well-designed fixture avoids duplication across test types. The phase-name-based detection follows the existing TurnAwareMockLLM pattern from old plans but simplified for actual use. Method signatures match `llm_client.py` exactly so monkeypatching at import sites works transparently.

#### Step 2.2 — Create helper to patch LLM calls in engine modules

**File:** `tests/conftest.py` (continued) or separate `tests/fixtures/llm_patch.py` if it grows large

**What:** A pytest fixture that patches the LLM client functions at their import sites in engine modules:
- Patch `ccya.engine.rules.llm_chat` with `FakeLLM.chat` bound method
- Patch `ccya.engine.turn.llm_chat_stream` (narrate streaming is called from turn.py line 1066, not narrate.py) with `FakeLLM.stream` bound generator  
- Patch `ccya.engine.extraction.llm_chat` similarly for scene/state/progress extraction calls

The fixture should be auto-used for smoke/integration test modules but NOT for render tests (which don't call the engine pipeline). Implementation pattern:
```python
@pytest.fixture(autouse=False)  # not autouse — only used by smoke/integration tests
def fake_llm_patch(monkeypatch, fake_llm):
    import ccya.engine.rules as rules_mod
    import ccya.engine.turn as turn_mod
    import ccya.engine.extraction as extraction_mod
    
    monkeypatch.setattr(rules_mod, "llm_chat", fake_llm.chat)
    monkeypatch.setattr(turn_mod, "llm_chat_stream", fake_llm.stream)
    monkeypatch.setattr(extraction_mod, "llm_chat", fake_llm.chat)
    
    yield fake_llm  # return the instance so tests can configure responses
    
    fake_llm._turn_counter = 0  # reset for next test
```

**Why:** Python's import system means patching where a name is used, not where it's defined. The engine modules (`rules.py`, `turn.py`, `extraction.py`) each do `from ccya.llm_client import chat as llm_chat` at module level (confirmed in `ccya/engine/__init__.py:28-29`). Monkeypatching at the module attribute level replaces the name in that module's namespace, which is what Python resolves during execution.

### Tests to write or update

- No tests needed for FakeLLM itself — its correctness is validated by smoke/integration tests that use it
- The conftest.py fixture should be importable and usable without errors (pytest's own collection will validate this)

---

## Implementation — Phase 3: Smoke tests (Layer 3 part A)

### Context files to load
- `ccya/engine/turn.py` — `run_turn()` signature, TurnResult dataclass fields
- FakeLLM from Phase 2 of this plan
- Existing state files in packs/default/ or similar for loading baseline state

### Detailed steps

#### Step 3.1 — Create smoke test file with engine pipeline tests

**File:** `tests/test_smoke.py` (new)

**What:** Pytest module that runs the full engine pipeline via `run_turn()` with FakeLLM responses, asserting high-level TurnResult properties. These are the most expensive tests to write and maintain but catch wiring mistakes that render+schema tests can't detect.

Test structure follows this pattern:
1. Set up a minimal save directory with state.yaml (loaded from an existing pack's seed_state or created inline)
2. Apply FakeLLM fixture to replace LLM calls
3. Call `run_turn(save_dir, user_input)` and collect yields until complete event
4. Assert TurnResult properties: narrative non-empty, state_delta applied correctly, rules data present, metrics valid

**Why:** Smoke tests exercise the full pipeline wiring — from state loading through all 5 LLM calls to delta application. They catch broken import paths, wrong argument passing between steps, and unexpected exception propagation. One of each template type is sufficient per turn fixture.

#### Step 3.2 — Write smoke test for basic dialogue turn (no dice roll)

**File:** `tests/test_smoke.py` (continued)

**What:** A single-turn smoke test exercising the simplest pipeline path:
- Input: pure dialogue with no action ("Hello, how are you?")
- FakeLLM returns rules response with `check.required=False` (no dice roll needed)
- Narrator produces prose based on pacing context and input
- Scene extract adds minimal scene data
- State extract makes no inventory/condition changes
- Progress extract advances a thread or generates an action

Assertions:
- TurnResult.narrative is non-empty string (>10 chars)
- TurnResult.rules contains intent classification with `check.required=False`
- TurnResult.state_delta has valid structure (keys match StateDelta model fields)
- TurnResult.metrics contains timing data for each pipeline step
- No errors in TurnResult.errors list

**Why:** This is the simplest complete pipeline path. If this test passes, basic engine wiring works. It's a canary that catches "engine doesn't run at all" regressions immediately.

#### Step 3.3 — Write smoke test for dice roll turn with inventory change

**File:** `tests/test_smoke.py` (continued)

**What:** A single-turn smoke test exercising the dice resolution path:
- Input: action requiring a check ("I swing my sword at the guard")
- FakeLLM returns rules response with `check.required=True`, dice results, band string
- Narrator produces prose incorporating roll outcome and directive
- Scene extract modifies present NPCs (add/remove)
- State extract changes inventory (add an item or remove some amount)
- Progress extract generates recent events and thread signals

Assertions:
- TurnResult.rules.rolled is True with valid dice data
- TurnResult.state_delta contains expected inventory_add or inventory_remove entries
- TurnResult.scene_tags reflects scene context from extraction
- TurnResult.actions list has engine-generated actions (not empty)
- TurnResult.metrics shows rules time > 0 (deterministic Python roll, should be fast)

**Why:** Tests the dice resolution path which is pure Python logic in `rules.resolve_check()` — not LLM-dependent. If this breaks, it's a wiring bug or regression in engine logic that render+schema tests can't catch.

### Tests to write or update

- `tests/test_smoke.py`:
  - `_minimal_state_dict()` helper fixture for creating inline state data
  - `_setup_save_dir(tmp_path)` fixture that writes state.yaml and empty events.jsonl
  - `test_basic_dialogue_turn_no_dice()` — complete pipeline with no dice roll, asserts narrative non-empty + valid TurnResult structure
  - `test_action_with_dice_roll_and_inventory_change()` — complete pipeline with dice resolution, inventory delta applied, rules.rolled=True

### REPOMAP updates required

- Add entry for `tests/test_smoke.py` under "Test suite" section describing smoke tests as Layer 3 of the four-layer strategy
- Note that FakeLLM is in conftest.py and shared by both smoke and integration test modules

---

## Implementation — Phase 4: Eval framework integration with pytest

### Context files to load
- `ccya/eval/scenario.py` — Scenario, Turn, TurnAssert dataclass definitions + loader functions
- All scenario files under `evals/scenarios/`: full_cycle.py, gm_beat_lifecycle.py, pressure_lifecycle.py, momentum_high.py, momentum_low.py
- FakeLLM from Phase 2 of this plan

### Detailed steps

#### Step 4.1 — Create pytest integration test that imports eval scenarios

**File:** `tests/test_integration.py` (new)

**What:** Pytest module that dynamically loads existing eval scenario definitions and runs them through the engine pipeline with FakeLLM, then validates TurnResult properties against each turn's assertions. This makes scenarios reusable: they're consumed by both the existing qualitative eval runner AND pytest integration tests. No duplication of test data.

Integration pattern per scenario:
1. Load scenario via `load_scenario(path)` from ccya.eval.scenario (same function used by existing runner)
2. For each turn in scenario.turns:
   - Write initial state.yaml with any seed_overrides applied to save directory
   - Run FakeLLM responses pre-loaded for this many turns worth of pipeline steps
   - Call `run_turn(save_dir, turn.input)` and collect complete event
   - Validate TurnResult properties against turn.asserts (TurnAssert objects)

**Why:** One source of truth for scenario definitions. The qualitative eval runner reads scenarios from events.jsonl output; pytest integration tests read the same scenarios but validate during pipeline execution via FakeLLM. Both consumers get value without duplicating test data.

#### Step 4.2 — Implement TurnAssert validation against TurnResult

**File:** `tests/test_integration.py` (continued)

**What:** A helper function that maps TurnAssert assertions to TurnResult properties via the phase events yielded by `run_turn()`. The integration test collects all yields from `run_turn()` into a dict keyed by phase name, then validates each TurnAssert against the appropriate phase data.

TurnAssert → phase event mapping:
| TurnAssert.stream | Phase key in run_turn yields | TurnResult field accessed | Example assertion |
|---|---|---|---|
| `"rules"` | `("complete", result)` where `result.rules` exists | `event["rules"].get(field)` or nested via dot notation (e.g., "rolled" → `rules.get("rolled")`) | `TurnAssert(stream="rules", field="rolled", expected="True")` checks `result.rules["rolled"] == True` |
| `"extract.scene"` | `("phase", {"phase": "scene_extract_done"})` or phase events during extraction | `event["state_delta"].get(field)` for npc_add/npc_remove/scene_tags | `TurnAssert(stream="extract.scene", field="npc_add")` checks non-empty list in state_delta.npc_add |
| `"extract.state"` | Phase event during state extraction | `event["state_delta"].get(field)` for inventory_add/inventory_remove/condition changes | `TurnAssert(stream="extract.state", field="inventory_remove", min_amount=1)` checks inventory_remove has entries with amount >= 1 |
| `"extract.progress"` | Phase event during progress extraction | `event["recent_events"]` or `event["state_delta"].get(field)` for thread signals, GM beats | `TurnAssert(stream="extract.progress", field="pending_gm_beat")` checks state_delta has pending_gm_beat populated |
| `"narrate"` | Phase events during narration (`"phase": "narrate_done"`) or complete event's narrative field | `event["narrative"]` for text content, phase events for timing metrics | `TurnAssert(stream="narrate", field="narrative_length_min")` checks len(result.narrative) >= threshold |

Validation helper signature:
```python
def _validate_assertions(phase_events: dict[str, Any], asserts: list[TurnAssert]) -> None:
    """Map each TurnAssert to the appropriate phase event data and assert."""
    for a in asserts:
        if a.stream == "rules":
            data = phase_events["complete"]["rules"]
            value = _get_nested(data, a.field)  # handles dot notation like "check.required"
            assert value == a.expected or (a.expected is None and value is not None)
        elif a.stream.startswith("extract."):
            stream_key = a.stream.split(".", maxsplit=1)[1]  # e.g., "scene", "state", "progress"
            data = phase_events["complete"]["state_delta"]
            _validate_extraction_assertion(data, a, stream_key)
```

**Why:** TurnAssert was designed for events.jsonl validation (qualitative eval). The same assertions can be mapped to phase event data from `run_turn()` in smoke/integration context. This bridges the qualitative and quantitative testing approaches without requiring scenario modifications or duplicating assertion logic.

#### Step 4.3 — Run integration tests with at least one complete scenario

**File:** `tests/test_integration.py` (continued)

**What:** Parameterized pytest test that runs each loaded scenario through the pipeline:
```python
@pytest.mark.parametrize("scenario", load_all_scenarios(), ids=lambda s: s.id)
def test_scenario(scenario):
    # For each turn in scenario.turns, run engine with FakeLLM and validate TurnAsserts
```

Start with `momentum_high.py` or `gm_beat_lifecycle.py` (shorter scenarios = faster feedback). Full cycle can be added later.

**Why:** Validates that existing eval scenarios work end-to-end through the pytest pipeline. If they pass, confidence in both FakeLLM correctness and scenario definition quality is high. Provides a migration path: qualitative-only scenarios gradually gain quantitative validation as FakeLLM responses are tuned per-scenario.

### Tests to write or update

- `tests/test_integration.py`:
  - `_load_all_scenarios()` helper that discovers and loads all scenario files from evals/scenarios/
  - `_run_scenario_turn(scenario, turn_index)` fixture-like function that sets up state dir + FakeLLM for a single turn
  - `_validate_assertions(result, asserts)` mapper converting TurnAssert objects to pytest assertions against TurnResult properties
  - `test_momentum_high_scenario()` — runs momentum_high.py (3 turns) with FakeLLM responses tuned per-turn
  - `test_gm_beat_lifecycle_scenario()` — runs gm_beat_lifecycle.py (5 turns), validates pending_gm_beat lifecycle through engine pipeline

### REPOMAP updates required

- Add entry for `tests/test_integration.py` under "Test suite" section describing integration tests as the pytest consumer of eval scenarios
- Note that scenario definitions in `evals/scenarios/` are shared between qualitative runner and quantitative pytest tests

---

## Sequencing within this plan

1. **Phase 1 (render tests)** — No dependencies on FakeLLM or engine state. Can start immediately after Plan 1 is complete.
2. **Phase 2 (FakeLLM infrastructure)** — Depends only on Phase 1's conftest.py setup being in place. Shared by Phases 3+4.
3. **Phase 3 (smoke tests)** — Depends on FakeLLM from Phase 2. Runs full pipeline with controlled responses.
4. **Phase 4 (integration/eval)** — Depends on FakeLLM + smoke test patterns. Reuses existing scenario definitions without modification.

Build in this order. Do not write Phase 3 until Phases 1-2 exist — FakeLLM must be working before running pipeline tests.

## Final validation step

After all four phases are complete, run:
```bash
make check && make test
```

This should include lint (ruff), typecheck (mypy), alignment checks (Phase 1 of Plan 1), schema tests (Plan 1 Phase 3), render tests (this plan's Phase 1), smoke tests (this plan's Phase 3), and integration tests with eval scenarios (this plan's Phase 4). All must pass.
