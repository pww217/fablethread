# Plan: Remove NPC Personality Field

**Status: scoping**

**Ticket:** I-23 (Engine core tech debt consolidation)

## Purpose

Remove the `personality` field from NPC state. Motivation, fear, leverage, and ties already express what matters. The personality field is a label that duplicates behavioral drivers while costing ~100-200 tokens/turn in roster context plus extraction overhead.

**Goal:** Eliminate `personality` from state model, prompts, templates, and all engine code. The narrator should center on motivation/fear/leverage/ties as the behavioral drivers.

## Constraints

- No backward compatibility — state model changes are breaking
- Player personality presets (ev/personality.py: resolve_personality for LLM player) are separate from NPC personality archetypes — those stay
- The `personality.py` module (NPC archetypes, ARCHETYPES, assign_personality, validate_and_resolve) is deleted entirely
- Unnamed NPCs never had personality — no change there

## Phase 1: State model

**Files:** `ccya/models/state.py`

**Dependencies:** None

### Step 1.1 — Remove personality fields from NPCEntry

**File:** `ccya/models/state.py`

**What:**
- Remove from `NPCEntry` class (around line 86-88):
  ```python
  personality: str | None = None
  personality_label: str = ""
  personality_traits: str = ""
  ```
- Also check for `personality_speech_hint` if present

**Why:** These fields are no longer needed. The state model is the source of truth.

## Phase 2: Delete personality.py module

**Files:** `ccya/personality.py`

**Dependencies:** None

### Step 2.1 — Delete the module

**File:** `ccya/personality.py`

**What:**
- Delete `ccya/personality.py` entirely (203 lines)
- This removes: `NpcPersonality` dataclass, `ARCHETYPES` dict, `assign_personality()`, `validate_and_resolve()`, `_score_archetype()`

**Why:** The module's sole purpose is assigning personality archetypes. Without the state field, it has no callers.

## Phase 3: Update engine code

**Files:** `ccya/engine/extraction/scene.py`, `ccya/engine/npc_roster.py`, `ccya/engine/world.py`, `ccya/engine/ruling.py`, `ccya/engine/seed.py`, `ccya/state/npcs.py`, `ccya/engine/narrate.py`

**Dependencies:** Phase 1

### Step 3.1 — Remove personality_registry from npc_roster.py

**File:** `ccya/engine/npc_roster.py`

**What:**
- Remove `personality_registry` parameter from `build_npc_roster()` signature (line 60)
- Remove the block that enriches roster entries with personality data (lines 107-113):
  ```python
  if personality_registry:
      arch_id = entry.get("personality")
      if arch_id and arch_id in personality_registry:
          arch = personality_registry[arch_id]
          seen[nid]["personality_label"] = getattr(arch, "label", arch_id)
          seen[nid]["personality_traits"] = ", ".join(arch.traits)
          seen[nid]["personality_speech_hint"] = getattr(arch, "speech_hint", "")
  ```

**Why:** No personality field to enrich. The roster no longer needs the registry.

### Step 3.2 — Remove personality_registry from all callers

**Files:** `ccya/engine/extraction/scene.py`, `ccya/engine/world.py`, `ccya/engine/ruling.py`, `ccya/engine/narrate.py`

**What:**
- Remove `from ccya.personality import ARCHETYPES` from all 4 files
- Remove `personality_registry=ARCHETYPES` from all `build_npc_roster()` calls
- In `narrate.py:242`, the call already uses `personality_registry=None` — just remove the import

**Why:** No more personality_registry to pass.

### Step 3.3 — Remove personality assignment from state/npcs.py

**File:** `ccya/state/npcs.py`

**What:**
- Remove `"personality": None` from unnamed NPC guard (line 88)
- Remove the personality assignment block (lines 99-105):
  ```python
  if comp_upd.personality is not None and not entry.personality:
      updates["personality"] = comp_upd.personality
      _log.info(...)
  ```
- Remove the engine fallback assignment (lines 106-116):
  ```python
  if not entry.personality and entry.name:
      if _is_named(entry.name):
          from ccya.personality import assign_personality
          arch = assign_personality(...)
          updates["personality"] = arch.id
  ```

**Why:** No personality field to assign or update.

### Step 3.4 — Remove personality assignment from seed.py

**File:** `ccya/engine/seed.py`

**What:**
- Remove `from ccya.personality import assign_personality, validate_and_resolve` (line 316)
- Remove the entire personality assignment block (lines 318-341):
  ```python
  for npc_id, npc_entry in state_envelope.seed_state.compendium.npcs.items():
      _name = (getattr(npc_entry, "name", "") or "").strip()
      if _name and not _is_named(_name):
          continue
      if not hasattr(npc_entry, "personality") or not getattr(npc_entry, "personality"):
          arch = assign_personality(...)
          object.__setattr__(npc_entry, "personality", arch.id)
      else:
          resolved = validate_and_resolve(...)
          if resolved is None:
              _log.warning(...)
              arch = assign_personality(...)
              object.__setattr__(npc_entry, "personality", arch.id)
  ```

**Why:** No personality field to assign during seed.

## Phase 4: Update prompts

**Files:** `ccya/prompts/extract_scene_system.j2`, `ccya/prompts/prepare_seed_system.j2`, `ccya/prompts/narrate_system.j2`, `ccya/prompts/sections/_npc_roster.j2`, `ccya/prompts/world_user.j2`

**Dependencies:** Phase 1

### Step 4.1 — Remove personality from extraction prompt

**File:** `ccya/prompts/extract_scene_system.j2`

**What:**
- Remove `"personality": "..."` from the JSON schema example (line 21)
- Remove personality from bio description (line 32): "personality traits or tangible facts" → "tangible facts"
- Remove personality from field requirements (line 37): the entire bullet about `personality: archetype_id`
- Remove personality from named NPC requirements (line 69): change "Must have `bio` + `personality` + `motivation` + 2 of {fear, leverage, tie} = 5 fields minimum" to "Must have `bio` + `motivation` + 2 of {fear, leverage, tie} = 4 fields minimum"
- Remove personality from unnamed NPC rules (line 70): already correct (unnamed NPCs don't get personality)
- Remove personality from examples (line 101): "second sentence just restates their role, not giving personality or tangible facts" → "second sentence just restates their role"

**Why:** The LLM should not output personality.

### Step 4.2 — Remove personality from seed prompt

**File:** `ccya/prompts/prepare_seed_system.j2`

**What:**
- Remove personality from field requirements (line 88): "NPCs have 5 personality-related fields: `personality`, `motivation`, `fear`, `leverage`, `tie`" → "NPCs have 4 behavioral fields: `motivation`, `fear`, `leverage`, `tie`"
- Remove personality from unnamed NPC rules (line 92): "Do NOT add personality, fear, leverage, or tie" → "Do NOT add fear, leverage, or tie"
- Remove personality from named NPC rules (line 93): "Must have `bio`, `personality` (from the table below), `motivation`, and 2 of {fear, leverage, tie} — 5 fields minimum" → "Must have `bio`, `motivation`, and 2 of {fear, leverage, tie} — 4 fields minimum"
- Remove the entire "Personality archetypes" section (lines 101-109): the table of 12 archetypes

**Why:** The seed generator should not output personality.

### Step 4.3 — Update narrator prompt

**File:** `ccya/prompts/narrate_system.j2`

**What:**
- Remove "Personality + speech" from NPC BEHAVIOR DRIVERS (line 45): change from 5 drivers to 4:
  ```
  - **Motivation** — what they fundamentally want. Drive their actions toward it.
  - **Fear** — what they dread. Have them avoid it or overreact to it.
  - **Leverage** — what they can offer, threaten, or withhold. Use it as a bargaining chip.
  - **Bond** — their relationship to the PC. Let it color interactions.
  ```
- Update line 48: "Give a brief physical and personality-based description" → "Give a brief physical description"

**Why:** The narrator should center on motivation/fear/leverage/bonds as behavioral drivers.

### Step 4.4 — Remove personality from NPC roster template

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:**
- Remove personality display from line 8:
  ```
  {%- if n.personality_traits %} | personality: **{{ n.personality_label }}** ({{ n.personality_traits }}). Speech: {{ n.personality_speech_hint }}.{%- endif %}
  ```

**Why:** No personality data to display.

### Step 4.5 — Remove personality from world user prompt

**File:** `ccya/prompts/world_user.j2`

**What:**
- Remove line 10: `{% if n.personality_label %}- personality: {{ n.personality_label }}{% endif %}`

**Why:** No personality data to display.

## Phase 5: Update templates

**Files:** `ccya/templates/_state_left.html`

**Dependencies:** Phase 1

### Step 5.1 — Remove personality from state display

**File:** `ccya/templates/_state_left.html`

**What:**
- Remove lines 53-54: `{% set npc_pl = npc.personality %}` and `{% set npc_pt = npc.personality_traits %}`
- Update line 55: `{% set _has_tt = npc_bio or npc_pl or _mot or npc_tie %}` → `{% set _has_tt = npc_bio or _mot or npc_tie %}`
- Remove line 64: `{% if npc_pl %}<p><strong>Personality:</strong> {{ npc_pl }}{% if npc_pt %} — {{ npc_pt }}{% endif %}</p>{% endif %}`
- Also check for other personality references in the template (lines 184+)

**Why:** The UI should not display personality.

## Phase 6: Update ev scripts

**Files:** `ccya/ev/prompt_context.py`, `ccya/ev/status.py`, `ccya/ev/init.py`, `ccya/ev/play.py`, `ccya/ev/session_config.py`, `ccya/ev/scenario.py`, `ccya/ev/eval.py`

**Dependencies:** Phase 1

### Step 6.1 — Remove personality from ev/prompt_context.py

**File:** `ccya/ev/prompt_context.py`

**What:**
- Remove lines 53-55: `"personality_label": ""`, `"personality_traits": ""`, `"personality_speech_hint": ""`

**Why:** No personality data in ev context.

### Step 6.2 — Remove personality from ev/status.py

**File:** `ccya/ev/status.py`

**What:**
- Remove lines 49-50: the `if player.get("personality")` block that prints personality

**Why:** No personality to display.

### Step 6.3 — Remove personality from ev/init.py

**File:** `ccya/ev/init.py`

**What:**
- Remove lines 58-59: the `if personality:` block that writes personality to ev.yaml

**Why:** No personality to persist.

### Step 6.4 — Remove personality from ev/play.py

**File:** `ccya/ev/play.py`

**What:**
- Remove `from ccya.ev.personality import resolve_personality` (line 19)
- Remove `personality` parameter from `_create_play_session()` (line 351)
- Remove `"personality": persona or "unknown"` from meta (line 337)
- Remove `personality` parameter from `_llm_session()` (line 491)
- Remove `personality=personality` from `_create_play_session()` call (line 504)
- Remove `system_prompt = resolve_personality(...)` (line 512) — replace with a simple default prompt
- Remove `"personality": personality or "unknown"` from report context (line 661)
- Remove `--personality` from help text (line 703)
- Remove `personality=player_cfg["personality"]` from `_llm_session()` call (line 769)
- Remove `personality` from `resolve_player_config` usage

**Why:** The ev play system should not reference NPC personality.

### Step 6.5 — Remove personality from ev/session_config.py

**File:** `ccya/ev/session_config.py`

**What:**
- Remove personality from `resolve_player_config()` return value
- Remove personality from ev.yaml parsing

**Why:** No personality in session config.

### Step 6.6 — Remove personality from ev/scenario.py

**File:** `ccya/ev/scenario.py`

**What:**
- Remove `personality: str = "custom"` from Scenario dataclass (line 35)

**Why:** No personality in scenarios.

### Step 6.7 — Remove personality from ev/eval.py

**File:** `ccya/ev/eval.py`

**What:**
- Remove `"personality": scenario.personality` (line 388)

**Why:** No personality in eval output.

## Verification

- `make typecheck` passes
- `make lint` passes
- `ev.py turn 3 --save-dir evals/runs/latest` produces identical extraction (no personality field in output)
- Server starts and `/` loads
- NPC state display works without personality field
- Seed generation works without personality assignment

## Files changed

| File | Before | After | Delta |
|------|--------|-------|-------|
| `models/state.py` | 453 lines | 450 lines | -3 |
| `personality.py` | 203 lines | deleted | -203 |
| `npc_roster.py` | 138 lines | 125 lines | -13 |
| `scene.py` (extraction) | 40 lines | 38 lines | -2 |
| `world.py` | ~50 lines | ~48 lines | -2 |
| `ruling.py` | ~200 lines | ~198 lines | -2 |
| `narrate.py` | 247 lines | 245 lines | -2 |
| `seed.py` | 677 lines | 640 lines | -37 |
| `state/npcs.py` | 145 lines | 130 lines | -15 |
| `extract_scene_system.j2` | 133 lines | 115 lines | -18 |
| `prepare_seed_system.j2` | 204 lines | 185 lines | -19 |
| `narrate_system.j2` | 107 lines | 103 lines | -4 |
| `_npc_roster.j2` | 12 lines | 10 lines | -2 |
| `world_user.j2` | 50 lines | 49 lines | -1 |
| `_state_left.html` | 205 lines | 195 lines | -10 |
| `ev/prompt_context.py` | 333 lines | 330 lines | -3 |
| `ev/status.py` | 55 lines | 52 lines | -3 |
| `ev/init.py` | 69 lines | 64 lines | -5 |
| `ev/play.py` | 820 lines | 780 lines | -40 |
| `ev/session_config.py` | 42 lines | 38 lines | -4 |
| `ev/scenario.py` | 184 lines | 182 lines | -2 |
| `ev/eval.py` | 631 lines | 630 lines | -1 |

## Done when

- Personality field removed from state model
- `personality.py` module deleted
- All engine code updated (extraction, seed, state/npcs, npc_roster)
- All prompts updated (extraction, seed, narration, roster, world)
- All templates updated (state display)
- All ev scripts updated
- `make check` passes
- `docs/repomap.md` updated if module boundaries change
