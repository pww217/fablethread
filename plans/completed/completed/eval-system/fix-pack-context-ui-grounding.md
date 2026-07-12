# Fix: Pack Loading, LLM Player Context, and UI Grounding

## Purpose

Ensure eval sessions always load scenario context, give the LLM player enough information to act meaningfully, and make UI elements (scene taglines, action choices) provide grounded additional context rather than repeating the narration.

## Problem Statement

Three independent but compounding failures in the eval session pipeline:

1. **Pack loading is optional** — sessions can start without `--pack`, producing empty state (Unnamed PC, no inventory, "Unknown" location). The eval session that produced steampunk hallucinations started without the pack flag.

2. **LLM player receives almost no scenario context** — at turn 1 it only gets the arc goal. At subsequent turns it gets arc goal + 2-3 recent player inputs + last narrative. It never sees the opening scene, setting description, present NPCs, inventory, or scene context. This is dramatically less context than the human player's turn pipeline receives.

3. **UI elements repeat the narration** — scene taglines are dramatic summaries of events ("Shadows in the Corridor"), and action choices are variations of the same exploration posture ("Press forward", "Investigate shadows", "Check walls", "Hold position"). They should provide grounded, practical information about location, world position, and situation.

## Constraints

- Must not break the server path (which uses dynamic seed generation).
- Must not break interactive play mode.
- Static packs (seed_state.yaml) and dynamic packs (scenario.yaml) must both work.
- The LLM player prompt must fit within token budgets.
- Scene tagline must remain 3-6 words.
- Actions must remain exactly 4, ~10 words each.

## Non-goals

- Do not change the human player turn pipeline (ruling → narrate → extract → storytell).
- Do not change the narrator prompt or system prompts.
- Do not change the scene extraction or state extraction pipelines.
- Do not add new pack file types or change the pack directory structure.
- Do not change the eval checker infrastructure.

## Solution

1. Make `--pack` required in the CLI play command.
2. Load `opening_scene.md` and `style.md` from packs and include them in the LLM player prompt at turn 1.
3. Add scenario context (location, present NPCs, inventory summary, scene tagline) to the LLM player prompt at every turn.
4. Change the scene tagline prompt to ask for grounded location/situation info instead of dramatic event summaries.
5. Change the action generation prompt to require grounded, practical options that reference the actual game state.

## Firm decisions

1. `--pack` is mandatory only when creating a new session (no `--save-dir`). When `--save-dir` is provided, load pack params from the save's `setting_pack` field.
2. Opening scene and style files are added as optional Pydantic fields to the `Pack` dataclass (parity with game engine architecture). Loaded for all pack types (static and scenario).
3. LLM player prompt structure: scenario context (every turn) + opening scene (turn 1 only) + recent turns + last narrative.
4. Scene tagline must describe the current location/situation, not summarize events.
5. Actions must reference actual game state (NPCs, inventory, location) and must not be generic exploration options.
6. If a pack has no scenario data, the LLM player prompt shows "Scenario: No scenario data loaded" as a placeholder.

## Risks, Ambiguities, and Blockers

- **Token budget**: Adding scenario context to the LLM player prompt increases token usage. Need to verify this stays within budget.
- **Style.md loading**: The file may contain markdown formatting. Need to decide whether to strip formatting or include as-is.
- **Backward compatibility**: Making --pack required will break any existing scripts that run without it. Need to update documentation.
- **Scene tagline change**: Existing sessions have dramatic taglines. The new prompt will produce different taglines. This is intentional but may look different in the UI.

## Status

`completed`

## Phases

5 phases: CLI enforcement, scenario context loading, LLM player prompt enrichment, scene tagline grounding, action generation grounding.

**Dependency graph:**
- Phase 1: independent (can run first)
- Phase 2: depends on nothing (can run in parallel with Phase 1)
- Phase 3: depends on Phase 2 (needs opening_scene/style in Pack dataclass)
- Phase 4: independent (only changes prompt template)
- Phase 5: independent (only changes prompt template + fallback code)

---

## Implementation — Phase 1: Make --pack Required for New Sessions

### Context files to load
- `ccya/ev/play.py` — CLI play command entry points (`cmd_play`, `_interactive_session`, `_llm_session`)
- `scripts/debug/README.md` — documentation to update

### Detailed steps

#### Step 1.1 — Require --pack when creating new sessions (no --save-dir)

**File:** `ccya/ev/play.py`

**What:** In `cmd_play()` (line 479-534), when no `--save-dir` flag is provided and no `--pack` flag is provided, print an error and exit with a helpful message showing available packs. When `--save-dir` is provided, skip the pack requirement (the save already has scenario state). In `_interactive_session()` and `_llm_session()`, require `--pack` when no existing save is being continued.

**Why:** Prevents sessions from starting without scenario context, which is the root cause of the steampunk hallucination. Existing saves already have scenario state so they don't need --pack.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py play "test input" 2>&1 | grep -i "pack"
```
Should show an error about missing --pack flag.

```bash
.venv/bin/python scripts/debug/ev.py play "test input" --save-dir saves/default 2>&1
```
Should NOT require --pack when --save-dir is provided.

#### Step 1.2 — List available packs when --pack is missing

**File:** `ccya/ev/play.py`

**What:** When --pack is not specified in a new session, scan `packs/` directory and list available pack names in the error message. Support both flat packs (`packs/eval/`) and namespaced packs (`packs/default/flooded-world`). Reuse `list_packs()` from `ccya/pack.py` if it exists, otherwise implement inline.

**Why:** Helps users know what packs are available without reading docs.

**Validation:**
```bash
.venv/bin/python scripts/debug/ev.py play "test" 2>&1
```
Should list "eval" and any other available packs.

#### Step 1.3 — Update README documentation

**File:** `scripts/debug/README.md`

**What:** Update the play command documentation to note that --pack is required when creating new sessions. Add a note about available packs. Clarify that --save-dir bypasses the --pack requirement.

**Why:** Users need to know the new requirement.

**Validation:** README reflects the --pack requirement.

---

## Implementation — Phase 2: Load opening_scene.md and style.md from Packs

### Context files to load
- `ccya/pack.py` — pack loading code, Pack dataclass
- `ccya/ev/play.py` — LLM session code, _create_play_session
- `packs/eval/pack.yaml` — pack manifest
- `packs/eval/opening_scene.md` — opening scene file
- `packs/eval/style.md` — style guide file

### Detailed steps

#### Step 2.1 — Add opening_scene and style as optional Pydantic fields to Pack dataclass

**File:** `ccya/pack.py`

**What:** Add optional `opening_scene: str | None = None` and `style: str | None = None` fields to the `Pack` Pydantic model (line 219-228). In `load_pack()` (line 257-299), after constructing the Pack object, read `opening_scene.md` and `style.md` from the pack directory if they exist. Assign them as instance attributes. Load for all pack types (both static seed_state.yaml and scenario.yaml packs).

**Why:** These files exist in packs but are never loaded. Adding as Pydantic fields gives parity with the game engine architecture (SeedEnvelope uses Pydantic). Loading for all pack types ensures scenario packs can also benefit from these files.

**Validation:**
```bash
python3 -c "
from ccya.pack import load_pack
from pathlib import Path
p = load_pack('eval', Path('packs'))
print('opening_scene:', repr(p.opening_scene[:50]))
print('style:', repr(p.style[:50]))
"
```

#### Step 2.2 — Return opening_scene and style from _load_pack_params

**File:** `ccya/ev/play.py`

**What:** Update `_load_pack_params()` (line 304-317) to return `opening_scene` and `style` strings in addition to the existing 5 return values. Update all 3 callers to handle the new 7-tuple return: `_interactive_session` (line 321), `_llm_session` (line 373), `cmd_play` single-turn (line 504).

**Why:** The LLM session needs access to these strings for the scenario context prompt.

**Validation:** `_load_pack_params('eval')` returns 7 values (was 5). All 3 callers unpack correctly.

#### Step 2.3 — Inject opening_scene into state when __seed_meta__ is absent

**File:** `ccya/ev/play.py`

**What:** In `_create_play_session()` (line 260-284), after loading the pack and before calling `init_save_dir()`, check if the pack has `opening_scene` but the state dict lacks `__seed_meta__.opening_narrative`. If so, inject `state_dict["__seed_meta__"] = {"opening_narrative": p.opening_scene}` before calling `init_save_dir()`. This ensures chronicle.md gets the opening scene as "Turn 0 — Seed".

**Why:** Static packs don't have __seed_meta__.opening_narrative in their seed_state.yaml. The opening_scene.md file is the correct source for the opening narrative in static packs. Injection point is `_create_play_session` (not `init_save_dir`) because `init_save_dir` only reads from the seed dict.

**Validation:** A session started with `--pack eval` has opening scene in chronicle.md Turn 0.

---

## Implementation — Phase 3: Enrich LLM Player Prompt

### Context files to load
- `ccya/ev/play.py` — _llm_session function
- `ccya/state/io.py` — state loading
- `ccya/state/__init__.py` — state access patterns

### Detailed steps

#### Step 3.1 — Build scenario context from state

**File:** `ccya/ev/play.py`

**What:** In `_llm_session` (line 366-476), after loading the state, build a scenario context string that includes:
- Location name and description
- Present NPCs (name, title, brief note)
- Inventory summary (item names only, no amounts)
- Scene tagline and tags
- Opening scene (only at turn 1, prepended to scenario context)

If the pack has no scenario data (no opening_scene, no scenario.yaml, no seed), show placeholder: "Scenario: No scenario data loaded".

Format as a concise bullet list, ~100-150 words total.

**Why:** The LLM player needs to know the scenario context to generate meaningful actions. Currently it only has the arc goal.

**Validation:** LLM player prompt at turn 1 includes scenario context + opening scene. At turn 2+, includes scenario context + recent turns + last narrative. If no scenario data, placeholder is shown.

#### Step 3.2 — Insert scenario context into LLM player user prompt

**File:** `ccya/ev/play.py`

**What:** Add the scenario context string to the user prompt in `_llm_session`, before the "Recent:" and "Narrative:" sections. Structure:

```
Scenario:
  Location: Marrow's Crossing — market town at dusk
  Present: Caron (old creditor), Halden (merchant)
  Inventory: Credits, iron dagger, linen bandages, traveler's cloak, brass key
  Scene: Market town at dusk

Current Goal: Clear your debts and deliver the ledger...

Recent:
  - I approach Caron at his table.
  - Caron asks about the ledger.

Narrative:
  You sit across from Caron...

What do you do?
```

If no scenario data:
```
Scenario: No scenario data loaded

Current Goal: ...
```

**Why:** Clear structure helps the LLM player understand what context is available.

**Validation:** LLM player output references scenario elements (NPCs, inventory, location) correctly.

#### Step 3.3 — Pass scenario context through all play modes

**File:** `ccya/ev/play.py`

**What:** Ensure `_interactive_session` and single-turn play also have access to scenario context. For interactive mode, the scenario context is already in the state (loaded from pack). For single-turn play, load it from the pack params.

**Why:** Consistency across all play modes.

**Validation:** Interactive play and single-turn play both have scenario context available.

---

## Implementation — Phase 4: Ground Scene Tagline Generation

### Context files to load
- `ccya/prompts/extract_scene_system.j2` — scene extraction system prompt

### Detailed steps

#### Step 4.1 — Change scene_tagline prompt to ask for location/situation info

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the scene_tagline field description and examples. Change from:

```
`scene_tagline`: 3–6 words summarizing the scene for the UI header. Grounded in what just happened. Examples: `"A Toll Paid In Blood"`, `"Whispers in the Dark"`, `"The Guard Raises the Alarm"`.
```

To:

```
`scene_tagline`: 3–6 words describing the current location and situation. Grounded in physical reality — where the PC is, what the environment is like, what the immediate stakes are. NOT a dramatic summary of events. Examples: `"Crossed Keys Inn — hearth low, toughs at door"`, `"Marrow's Crossing square — dusk, shops closing"`, `"Behind the inn — narrow alley, locked door"`.
```

**Why:** Current taglines are dramatic event summaries that repeat the narration. New taglines provide grounded location/situation context that adds value.

**Validation:** Scene taglines describe locations and situations, not events. Example: "Crossed Keys Inn — hearth low, toughs at door" instead of "A Toll Paid In Blood".

---

## Implementation — Phase 5: Ground Action Generation

### Context files to load
- `ccya/prompts/storytell_system.j2` — storytell system prompt
- `ccya/engine/extraction.py` — fallback action generation (lines 551-576)

### Detailed steps

#### Step 5.1 — Change action generation prompt to require grounded options

**File:** `ccya/prompts/storytell_system.j2`

**What:** Replace the Actions section (line 78-80) with:

```
## Actions

Emit exactly 4 choices, ~10 words each. Every choice must begin with an active verb.

**Grounding rules:**
- Reference actual game state: named NPCs present, inventory items, location features.
- No generic exploration options ("look around", "check walls", "move forward").
- Each choice must be distinct in approach — not variations of the same action.
- At least one choice must reference an NPC by name.
- At least one choice must reference an inventory item or location feature.
- Choices should escalate, force a decision, or change things irreversibly.
- No passive options, nothing generic enough for any protagonist.

- Departed NPCs (marked with `[DEPARTED]`) are permanently gone and will be archived after a few turns. Reference them from narrative history only — do not create threads or actions involving departed characters.
```

**Why:** Current actions are generic exploration variations ("Press forward", "Investigate shadows", "Check walls", "Hold position"). New actions must reference actual game state.

**Validation:** Actions reference specific NPCs, items, and locations. No generic exploration options.

#### Step 5.2 — Update fallback action generation

**File:** `ccya/engine/extraction.py`

**What:** Update the fallback action generation (lines 551-576) to reference actual game state when the storytell LLM fails. The fallbacks should:
1. Reference the first present NPC by name
2. Reference an inventory item
3. Reference a location feature
4. Reference the arc goal

**Why:** If the storytell LLM fails, the fallbacks should still be grounded in game state, not generic exploration.

**Validation:** Fallback actions reference NPCs, items, and locations when available.

---

## Tests to write or update

No tests to write — tests are temporarily removed during refactor per AGENTS.md.
