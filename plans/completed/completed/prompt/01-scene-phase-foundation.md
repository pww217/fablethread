# Plan 1: Foundation — Models, Config, and Ruling Signal

## Purpose

Add the new model fields, config thresholds, and `tension_delta` ruling signal that all subsequent scene-phase plans depend on.

## Problem Statement

The scene phase system cannot be implemented until its core data types exist. The `tension_delta` signal (the ruling engine's player-action tension classification) must be emitted before it can be consumed by phase transitions. Config thresholds that drive phase transitions must be defined in `EngineConfig` before phase logic references them.

## Constraints

- No backwards compatibility — old state can be discarded.
- `tension_delta` defaults to `"maintains"` when the LLM omits the field — safest neutral default.
- No new LLM calls — only adding a field to an existing output schema.
- `tension_delta` lives on `IntentEnvelope`, not `RulesOutcome`. It's an LLM-classified intent signal (what the player is doing), orthogonal to the roll outcome. This matches the existing pattern of `scene_motion` on `IntentEnvelope`.

## Non-goals

- No phase engine logic (`_compute_scene_phase()`).
- No directive computation changes.
- No prompt changes outside `ruling_system.j2` — storytell/narrate prompt updates are Plan 3.
- No deletion of old fields (`momentum`, `narrative_velocity`, etc.) — that's Plan 4.
- No extraction.py changes — `scene_phase` and `allowed_beat_types` context passing is Plan 2.

## Solution

Three additive changes, zero behavioral effect until downstream plans wire the signals in:

1. Add `tension_delta` field to `IntentEnvelope` with default `"maintains"`.
2. Add 3 new `EngineConfig` fields for scene phase thresholds.
3. Update `ruling_system.j2` schema and field rules so the LLM emits `tension_delta`.

## Firm decisions

1. `tension_delta` lives on `IntentEnvelope` (line 167), not `RulesOutcome` — it's an LLM-classified signal, not a roll result. Orthogonal to the existing `scene_motion` field (line 174).
2. Default value `"maintains"` — preserves behavior when LLM omits the field.
3. `scene_pressure_threshold` (line 157) and `scene_imperative_threshold` (line 158) already exist in `EngineConfig` — no new fields needed for those. The design doc's config table includes them for completeness.
4. The 3 new config fields (`crisis_urgency_threshold`, `crisis_turn_limit`, `breather_max_turns`) are purely additive. No existing code references them yet — they won't affect behavior until Phase 2.
5. `TensionDelta` type alias joins the other Literal types at the top of `models.py` (~line 16-20), alongside `SkillName`, `Difficulty`, `Band`.

## Risks, Ambiguities, and Blockers

- The ruling LLM may not reliably emit `tension_delta` immediately after the prompt update. The `"maintains"` default covers this, but the signal will be weak until prompt tuning settles.
- The `tension_delta` prompt guidance in `ruling_system.j2` must be carefully worded to avoid confusing the LLM with the existing `scene_motion` field. The distinction: `scene_motion` = "is the player leaving the scene?" vs `tension_delta` = "is the player's action aggressive or de-escalating?"
- `_compute_pacing_context()` in `turn.py:450` has `scene_imperative_threshold: int = 5` as a default, but `EngineConfig.scene_imperative_threshold` defaults to 4. Executor should fix the function default to 4 to avoid silent inconsistency. This is a pre-existing bug, not caused by this plan.
- `docs/architecture/pacing-systems.md` is intentionally out of scope — it will be deleted or rewritten from scratch in a later plan due to major architectural changes.

## Status

`completed`

## Phases

Single phase — all changes are additive and tightly coupled to the same models/config/prompt schema.

## Implementation — Phase 1: Foundation

### Context files to load

- `ccya/models.py` — `IntentEnvelope` class (line 167), type aliases (lines 16-20)
- `ccya/engine/config.py` — `EngineConfig` dataclass (line 98), `build_engine_config()` (line 193)
- `ccya/prompts/ruling_system.j2` — JSON schema (lines 56-69), field rules (lines 72-81)
- `docs/architecture/step0-ruling.md` — IntentEnvelope/RulesOutcome output shapes (lines 31-32)
- `docs/architecture/OVERVIEW.md` — IntentEnvelope field list (line 82)
- `docs/repomap.md` — IntentEnvelope entry (line 9), config fields (line 12)

### Detailed steps

#### Step 1.1 — Add `TensionDelta` type alias and field to `IntentEnvelope`

**File:** `ccya/models.py` (line 17, then line 174 after `scene_motion`)

**What:** Add `TensionDelta = Literal["escalates", "maintains", "de-escalates"]` alongside other type aliases (~line 17). Add `tension_delta: TensionDelta = "maintains"` to `IntentEnvelope` after the existing `scene_motion` field (line 174).

**Why:** The type alias keeps the Literal definition in one place, matching the existing pattern of `SkillName`, `Difficulty`, `Band`. The field on `IntentEnvelope` makes `tension_delta` an LLM-emitted classification of player action intent, parsed automatically from the LLM JSON with a safe default.

**Validation:** `from ccya.models import TensionDelta, IntentEnvelope; ie = IntentEnvelope(); assert ie.tension_delta == "maintains"`

#### Step 1.2 — Add new config fields to `EngineConfig`

**File:** `ccya/engine/config.py` (line 98, after `scene_imperative_threshold` at line 158)

**What:** Add three new `EngineConfig` fields:

```python
crisis_urgency_threshold: int = 2   # urgent threads needed for SETUP/RISING → CRISIS transition
crisis_turn_limit: int = 4          # max turns in CRISIS before forced RESOLUTION
breather_max_turns: int = 3         # max turns in BREATHER before forced RISING transition
```

**Why:** These are the hard configurable thresholds that drive phase transitions. Defaults are conservative starting points per the design doc. Pack authors override via `config.yaml`.

**Validation:** `from ccya.engine.config import EngineConfig; ec = EngineConfig(); assert ec.crisis_urgency_threshold == 2; assert ec.crisis_turn_limit == 4; assert ec.breather_max_turns == 3`

#### Step 1.3 — Wire new config fields in `build_engine_config()`

**File:** `ccya/engine/config.py` (line 193, after line 278 near the existing game config mappings)

**What:** Add three lines after the `scene_imperative_threshold` mapping (~line 277):

```python
crisis_urgency_threshold=int(game.get("crisis_urgency_threshold", 2)),
crisis_turn_limit=int(game.get("crisis_turn_limit", 4)),
breather_max_turns=int(game.get("breather_max_turns", 3)),
```

**Why:** `build_engine_config()` is the single mapping function from raw `config.yaml` dict to `EngineConfig`. Without this, config.yaml overrides of these fields are silently ignored.

**Validation:** `from ccya.engine.config import build_engine_config; ec = build_engine_config({"game": {"crisis_turn_limit": 6}}); assert ec.crisis_turn_limit == 6`

#### Step 1.4 — Add `tension_delta` to `ruling_system.j2` schema

**File:** `ccya/prompts/ruling_system.j2`

**What:** Four changes:

1. Add a **Tension delta** section before the **Scene motion** section (lines 48-52) or after it, documenting the field's semantics:

```
## Tension delta

- `escalates`: Player is attacking, confronting, pushing forward aggressively — tension is rising.
- `maintains`: Player is acting with normal intent — no significant change in tension.
- `de-escalates`: Player is retreating, hiding, calming, avoiding conflict — tension is dropping.
```

2. Add `"tension_delta": "escalates|maintains|de-escalates"` to the JSON schema example (~line 63, after `scene_motion`).

3. Add `"tension_delta": escalate | maintain | de-escalate.` to the Field rules section (~line 79, after `scene_motion` rule).

**Why:** Without the schema and field rule in the prompt, the LLM won't emit `tension_delta`. The field default (`"maintains"` on `IntentEnvelope`) handles missing values gracefully — but for the signal to have any useful signal beyond the default, the LLM needs to know about it.

**Validation:** Render the template with an empty context: the schema JSON must contain `tension_delta` and the field rules must mention it. No Python test needed — visual inspection of rendered prompt confirms.

#### Step 1.5 — Update step0-ruling.md architecture doc

**File:** `docs/architecture/step0-ruling.md`

**What:** Add `tension_delta: escalates|maintains|de-escalates` to the `IntentEnvelope` output shape (line 31). Update the `IntentEnvelope` list in the LLM output node.

**Why:** Architecture docs must reflect the actual output shape of each pipeline stage. Stale docs are bugs.

**Validation:** `grep 'tension_delta' docs/architecture/step0-ruling.md` returns a hit.

#### Step 1.6 — Update OVERVIEW.md IntentEnvelope field list

**File:** `docs/architecture/OVERVIEW.md`

**What:** Add `tension_delta` alongside the existing `scene_motion` in the IntentEnvelope field list at line 82. It should read: `intent`, `intent_verb`, `target`, `check.required`, `check.skill`, `check.difficulty`, `impossible`, `reason`, `scene_motion`, `tension_delta`.

**Why:** The quick-reference table in OVERVIEW.md is the first place implementors look for pipeline output shapes.

**Validation:** `grep 'tension_delta' docs/architecture/OVERVIEW.md` returns a hit.

#### Step 1.7 — Update repomap.md for IntentEnvelope and EngineConfig

**File:** `docs/repomap.md`

**What:** Two changes:

1. Add `tension_delta` to the IntentEnvelope entry in line 9 (models.py module description).
2. Add the 3 new config fields to the EngineConfig entry in line 12 (config.py module description).

**Why:** Repomap is the signpost for module boundaries and public APIs. New fields are public API.

**Validation:** `grep 'tension_delta\|crisis_urgency_threshold\|crisis_turn_limit\|breather_max_turns' docs/repomap.md` — all four return hits.

### Tests to write or update

No test changes. This plan is purely additive — no existing behavior changes. The validation steps above are manual assertions, not automated tests. Automated tests for the phase system will be written when functional behavior is added in Plan 2.
