# Fix Prompt Redundancy: Location + NPC + Pressure Context

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Audit variable duplication | Catalog all duplicated context vars across the five pipeline prompts |
| 02 | Deduplicate via shared section macros | Replace inline repeats with `{% include %}` sections or trimmed variable passing |

## Objective
The same context blocks — `location.description`, `present_npcs`, and `scene_pressure` — are rendered in full for all five LLM pipelines (rules, narrate, scene extract, state extract, progress extract). This is wasteful: each extra token is latency. The rules pipeline does not need a full location description. The state extractor does not need present NPCs. The goal is to pass each pipeline only the subset of context it actually needs to do its job, without altering any pipeline's effective behavior.

## Non-goals
- Do not change prompt wording for any pipeline.
- Do not change field names in `_narrate_messages`, `_extract_scene_messages`, `_extract_state_messages`, `_extract_progress_messages`, or `_rules_messages`.
- Do not touch `narrate_system.j2` or any system prompt.
- Do not alter the schema or output behavior of any extractor.
- Do not move logic from `narrate.py` or `extraction.py` — only template rendering changes.

## Implementation — Phase 01: Audit variable duplication

### Files to pull for context
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/rules_user.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/engine/narrate.py`
- `ccya/engine/extraction.py`
- `ccya/engine/rules.py`

### Detailed steps

#### Step 1.1 — Read each user template and catalog every rendered variable

**What:** For each of the five user-side templates, list every Jinja variable that is expanded and note its approximate rendered character cost (small = <200 chars, medium = 200-800, large = >800).

**Why:** Establishes the ground truth of what each pipeline currently receives before any changes.

**Validation:** Produce a table (in a scratch note or comment in the plan) of: pipeline × variable → presence (yes/no) × size tier.

#### Step 1.2 — Identify pure redundancy (variable used identically in two or more pipelines that do not share purpose)

**What:** Cross-reference the table. Flag any variable that appears verbatim in a pipeline that has no structural reason to receive it. Specifically:
- `location.description` in `rules_user.j2` — rules engine only needs `location.id` and `location.name` for intent classification; full description is unused.
- `present_npcs` (full list with bios) in `extract_state_user.j2` — state extractor only cares about inventory and conditions; NPC bios are irrelevant.
- `scene_pressure` full list in `extract_state_user.j2` — state extractor never emits pressure ops; receiving this is pure waste.

**Why:** Prevents removing something a pipeline actually silently depends on.

**Validation:** Confirm by reading the actual template files that each flagged variable is either: (a) not referenced in the template at all, or (b) referenced only in a block that could receive a stripped version.

### Tests to write or update
None for Phase 01 — this is a read-only audit phase.

### REPOMAP and architecture updates
None.

### Risks
1. A variable appears to be unused but the template includes a sub-template (`{% include %}`) that uses it — mitigation: grep all included sections before flagging.
2. Audit result may find zero redundancy — plan would be abandoned after Phase 01.

## Implementation — Phase 02: Deduplicate via trimmed variable passing

### Files to pull for context
- All files from Phase 01.
- `ccya/prompts/sections/` (list contents — may include `_location.j2`, `_inventory.j2`, `_arc.j2`).
- `ccya/engine/rules.py` — specifically `_rules_messages()` signature to confirm what vars it passes.

### Detailed steps

#### Step 2.1 — Trim `location` passed to rules pipeline

**File:** `ccya/engine/rules.py`

**What:** In `_rules_messages()`, confirm that `location` is passed to `rules_user.j2`. If `rules_user.j2` renders `location.description`, replace the passed value with a dict containing only `id` and `name`:

```python
_location_trimmed = {
    "id": (state.get("location") or {}).get("id", ""),
    "name": (state.get("location") or {}).get("name", ""),
}
```

Pass `_location_trimmed` as `location` in the template context instead of `state.get("location") or {}`.

**Why:** Rules intent classification requires location identity for context-grounding (e.g., "are you in a market?") but never needs a prose description that can run 300+ characters.

**Validation:** Render `rules_user.j2` in a unit test with a state that has a long `location.description`. Confirm the rendered output does not contain the description string. Confirm the location name is still present.

#### Step 2.2 — Strip `present_npcs` and `scene_pressure` from state extractor

**File:** `ccya/engine/extraction.py` — `_extract_state_messages()`

**What:** Confirm that `extract_state_user.j2` currently receives `present_npcs` or `scene_pressure`. If so, remove those variables from the context dict passed to that template. If the template references them, remove those blocks from the template (they are unused noise).

```python
user_text = _render(
    env,
    "extract_state_user.j2",
    {
        "narration": narration,
        "pc": pc,
        "conditions": list(pc.get("conditions") or []),
        "inventory": state.get("inventory") or [],
        "intent": intent,
        "turn_no": turn_no,
        # present_npcs and scene_pressure deliberately omitted — state extractor
        # owns only inventory and conditions; NPC/pressure context is noise here.
    },
)
```

**Why:** The state extractor's only job is to detect inventory_add/remove/update and pc_condition_add/remove from the narration. Sending NPC bios and pressure text inflates the prompt without improving accuracy.

**Validation:** Render `extract_state_user.j2` with a full state. Confirm the rendered output does not reference NPC names or pressure text. Run `make check && make test`.

#### Step 2.3 — Audit `extract_scene_user.j2` for redundant full-description location block

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** Check if `extract_scene_user.j2` renders `location.description`. If yes, and if the scene extractor does not need the full prose description (it only needs to know if a `location_change` occurred), replace it with:

```jinja2
**Current location:** {{ location.name or location.id or "unknown" }}
```

If the scene extractor does use the description to judge whether a location_change is warranted (e.g., comparing narration to existing description), leave it.

**Why:** Scene extractor compares the narration against the current location to detect movement. The name is sufficient for identity; the description may help with ambiguous cases but is often 300+ chars of sunk cost.

**Validation:** Confirm the scene extractor still correctly detects location changes in the smoke test. Run `make check && make test`.

### Tests to write or update
- `tests/test_prompt_audit.py`: add assertions verifying `extract_state_user.j2` rendered output does not contain NPC bio text when `present_npcs` is populated.
- `tests/test_prompt_audit.py`: add assertion that `rules_user.j2` rendered output does not contain `location.description` when a long description is provided.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: update notes on what context vars each user template receives.
- `docs/REPOMAP/engine.md`: update `_extract_state_messages` signature notes if any params are removed.

### Risks
1. `extract_state_user.j2` references `present_npcs` indirectly via an `{% include %}` — mitigation: read the file and all its includes before removing the var.
2. Removing `location.description` from rules prompt causes a regression where the rules engine can no longer distinguish actions that require location knowledge (e.g., "pick up the item on the shelf" in a context where the shelf only exists in the description) — mitigation: check eval logs for any rules calls that appear to use location prose; if present, keep description in rules.

## Ambiguities requiring resolution before execution
1. Does `rules_user.j2` render `location.description` at all? If not, Step 2.1 is a no-op. Options: A) Read the file before executing, B) execute anyway and verify at validation step.
2. Does `extract_state_user.j2` currently reference `present_npcs`? Options: A) Yes — remove it. B) No — Step 2.2 scope narrows to just verifying it doesn't accidentally get added in the future (add a test assertion).
