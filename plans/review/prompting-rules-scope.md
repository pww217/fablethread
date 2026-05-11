# Prompting: Rules Scope, Extract Scene, and Difficulty Calibration

## Status
`open`

## Part of
standalone

## Dependencies
- none (can run in parallel)

## Objective
Three prompting failures are responsible for the most visible mechanical breakdowns in evals: (1) the rules pipeline decides `active_domains` too conservatively on social/transactional turns, causing `extract_scene` to be skipped on turns 3 and 4, which eliminates player action choices entirely; (2) `extract_scene` emits `location_description` on turns where nothing environmental changed, adding ~50 tokens of noise per turn; (3) the rules pipeline's difficulty heuristic is too lenient for social turns involving significant credits or quest-gating actions, producing `easy` ratings that should be `normal` or `hard`. All three are prompt-level fixes — no engine logic changes required.

## Non-goals
- Does not change the engine's `active_domains` enforcement logic — that is the rules extractor's output that drives it, so the fix is in the rules prompt.
- Does not change the `actions` schema or how choices are presented to the player.
- Does not change dice resolution math.
- Does not touch narrate, compact, or progress prompts.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/extract_rules_system.j2` | modify | Add explicit `scene` domain inclusion rule for NPC-interaction turns; tighten difficulty heuristic for credit/quest-gating actions |
| `ccya/prompts/extract_rules_user.j2` | modify | Add `pending_gm_beat` and `scene_pressure` to rules user prompt so scope decisions are pressure-aware |
| `ccya/prompts/extract_scene_system.j2` | modify | Tighten `location_description` constraint; add few-shot negative example for static environment |
| `docs/REPOMAP/prompts.md` | update | Document new scope rule and difficulty heuristic additions |

## Firm decisions

1. The rules extractor owns the `active_domains` decision. Fixing the scope requires fixing the rules prompt, not adding a separate engine override pass.
2. `scene` must always be included in `active_domains` when: the player's input involves speaking to, fighting, or moving toward an NPC, OR a `scene_pressure` is active that involves an NPC, OR a `pending_gm_beat` is non-null. This is the clearest expression of "scene is open."
3. Difficulty heuristic: any action involving transfer or negotiation of ≥ 100 credits, or directly completing a quest objective, cannot be rated `easy` — minimum `normal`. If an NPC is described as suspicious, wary, or has an opposing motivation in their bio, minimum `hard`.
4. `location_description` in `extract_scene` should only be emitted when: weather changed, lighting changed, crowd density changed, a significant physical object was destroyed/created, or the player moved to a new location. Ambient re-description is forbidden.
5. The rules user prompt must receive `scene_pressure` (list of active pressures) and `pending_gm_beat` so the rules extractor can factor them into scope.

## Implementation — Phase 1: Rules Scope and Difficulty

### Context files to load
- `ccya/prompts/extract_rules_system.j2`
- `ccya/prompts/extract_rules_user.j2`
- `ccya/engine/turn.py` (to confirm what variables are currently passed to rules render)

### Overview
Add an explicit `scene` domain inclusion rule to the rules system prompt. Add a difficulty heuristic tightener for credits/quest-gating. Add `scene_pressure` and `pending_gm_beat` to the rules user prompt.

### Detailed steps

#### Step 1.1 — Add scene domain inclusion rule to extract_rules_system.j2

**File:** `ccya/prompts/extract_rules_system.j2`

**What:** Add a new rule in the `active_domains` section:

```
**SCENE DOMAIN RULE (MANDATORY):** Always include `scene` in `active_domains` if ANY of the following are true:
- The player's input involves speaking to, approaching, fighting, or observing a named NPC.
- One or more `scene_pressure` entries are active in the current state (a pressure means the scene is unresolved and must be tracked).
- `pending_gm_beat` is non-null (a beat requires scene context to land).
- The player moves to a new location or sub-location.
Omit `scene` ONLY if: the player's action is purely internal (thinking, reading a document they already possess, resting in a confirmed safe room with no active pressures).
```

**Why:** The current prompt has no positive rule for when to include `scene` — it only describes what domains cover. Without an affirmative rule, the model defaults to the minimum set. Making inclusion mandatory under common conditions eliminates the 3-turn `actions` blackout.

**Validation:** Render `extract_rules_system.j2`. Confirm the SCENE DOMAIN RULE block appears. In the next eval run, confirm `scene` is in `active_domains` on turns involving NPC interaction.

***

#### Step 1.2 — Add difficulty heuristic rule to extract_rules_system.j2

**File:** `ccya/prompts/extract_rules_system.j2`

**What:** Add a difficulty floor rule adjacent to the existing difficulty descriptions:

```
**DIFFICULTY FLOOR RULE:**
- Any action that transfers, wagers, or negotiates ≥ 100 credits is at minimum `normal`, not `easy`.
- Any action that directly completes or gates a named quest objective is at minimum `normal`.
- Any NPC whose bio describes them as suspicious, wary, hostile, or with a conflicting motivation upgrades the floor to `hard` for social actions targeting them.
- `easy` is reserved for: clearly non-opposed actions, actions against distracted or incapacitated targets, and actions where the player has overwhelming advantage (e.g., stat + 3 vs. difficulty 0).
```

**Why:** The `easy` rating on Halden's 200-credit negotiation is the direct cause of the single-turn quest over-completion and under-tension. A floor rule is more reliable than relying on the model to calibrate from examples alone.

**Validation:** Render the rules prompt for a 200-credit negotiation scenario. Confirm `easy` would not be selected by the model's reasoning given the floor rule.

***

#### Step 1.3 — Add scene_pressure and pending_gm_beat to extract_rules_user.j2

**File:** `ccya/prompts/extract_rules_user.j2`

**What:** Add two new blocks to the user prompt, after the existing state summary block:

```
## active_pressures
{% if scene_pressure %}
{% for p in scene_pressure %}
- {{ p.id }} ({{ p.urgency }}): {{ p.description }}
{% endfor %}
{% else %}
none
{% endif %}

## pending_gm_beat
{{ pending_gm_beat if pending_gm_beat else "none" }}
```

**Why:** The rules extractor cannot apply the SCENE DOMAIN RULE (Step 1.1) without seeing active pressures and the pending beat. Currently these are absent from the rules user prompt, making the rule unenforceable.

**Validation:** Render `extract_rules_user.j2` with an active pressure. Confirm the `active_pressures` block renders with the pressure's id, urgency, and description.

**Call site check:** Executor must verify that `scene_pressure` and `pending_gm_beat` are passed to the rules render call in `turn.py`. If not, add them — source from `state.scene.scene_pressure` and `state.pending_gm_beat` (or equivalent field name per REPOMAP).

***

## Implementation — Phase 2: Extract Scene location_description Tightening

### Context files to load
- `ccya/prompts/extract_scene_system.j2`

### Overview
Tighten the `location_description` constraint and add a negative few-shot example showing the correct behavior when the environment has not changed.

### Detailed steps

#### Step 2.1 — Tighten location_description rule in extract_scene_system.j2

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Find the existing `location_description` rule and replace/extend it:

```
**LOCATION DESCRIPTION RULE:** Only emit `location_description` if at least one of the following changed this turn:
- Weather or lighting conditions
- Crowd density or ambient population
- A significant physical object was destroyed, created, moved, or revealed
- The player moved to a previously unvisited location or sub-location

Do NOT re-describe ambient atmosphere, mood, or existing features. If none of the above changed, omit `location_description` entirely. An empty field is correct when the environment is static.

EXAMPLE — static environment (correct: omit):
Turn context: Player spoke to an NPC in the tavern. No environmental changes.
→ Do NOT emit: `"location_description": "The dim light of the Crossed Keys feels oppressive, the smell of stale grain hanging in the air."`
→ Correct: omit `location_description` field entirely.
```

**Why:** The current rule says "do not re-describe unchanged surroundings" but is too vague — the model still emits atmospheric re-description. A concrete negative example with the exact output that is wrong is more effective.

**Validation:** Run an eval turn where the player speaks to an NPC in an existing location with no environmental change. Confirm `location_description` is absent from `extract_scene` output.

***

### Tests to write or update
- `tests/test_prompts.py`: render `extract_rules_user.j2` with active pressure — confirm `active_pressures` block present.
- `tests/test_prompts.py`: render `extract_rules_system.j2` — confirm SCENE DOMAIN RULE and DIFFICULTY FLOOR RULE blocks present.
- `tests/test_prompts.py`: render `extract_scene_system.j2` — confirm updated `location_description` rule with negative example present.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: under `extract_rules_system.j2` — add SCENE DOMAIN RULE and DIFFICULTY FLOOR RULE.
- `docs/REPOMAP/prompts.md`: under `extract_rules_user.j2` — add `active_pressures` and `pending_gm_beat` blocks.
- `docs/REPOMAP/prompts.md`: under `extract_scene_system.j2` — add tightened `location_description` rule with negative few-shot.

### Risks
1. **`pending_gm_beat` field name** — may be `gm_beat_pending`, `next_gm_beat`, or similar. Executor must grep the REPOMAP and state model before using this name.
2. **`scene_pressure` already in rules context?** — if `scene_pressure` is already passed to the rules render, adding a duplicate block will cause Jinja key collision. Executor must check the existing rules user prompt and call site before adding.
3. **SCENE DOMAIN RULE may over-include `scene`** — including scene on every NPC-interaction turn increases total extraction calls. Acceptable cost; the alternative (missing `actions` for 2+ turns) is worse.

## Ambiguities requiring resolution before execution
1. Is `pending_gm_beat` a field on `GameState` directly or nested under a sub-model? The REPOMAP mentions `gm_beat` in the progress extractor but does not clearly state where the pending beat is stored between turns. Executor must resolve this before adding the template variable.

## TODO.md update
Add under **P1 — Critical Bugs**:
```
- [ ] [Prompting: Rules Scope, Extract Scene, Difficulty Calibration](plans/prompting-rules-scope.md)
```
