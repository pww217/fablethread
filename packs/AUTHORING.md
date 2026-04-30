# Pack Authoring Guide

This document is the spec for creating world packs. It is also the canonical prompt context for the future **"Make My Own Scenario"** generator tool (`generate_pack()`).

---

## Two modes

| | `static` | `dynamic` |
|---|---|---|
| **Seed** | Hand-authored `seed_state.yaml` | LLM-generated each New Game |
| **Opening** | Hand-authored `opening_scene.md` | LLM-generated each New Game |
| **Replayability** | Identical every run | Fresh scenario each run |
| **Required files** | `pack.yaml`, `seed_state.yaml`, `opening_scene.md` | `pack.yaml`, `world.md`, `scenario.yaml` |
| **Optional files** | `style.md`, `extract_examples.yaml` | `style.md`, `extract_examples.yaml` |

---

## File reference

### `pack.yaml` (required — both modes)

```yaml
id: my-pack              # snake-case, used in config.yaml and packs/ directory name
name: "My Pack Title"
description: "One sentence about the setting."
genre: post-apocalyptic  # free text; used for display only
tone_tags: [gritty, scarcity]  # free list; display only
version: 1
mode: dynamic            # "static" or "dynamic"
files:
  # static mode (required if static):
  seed: seed_state.yaml
  opening: opening_scene.md
  # dynamic mode (required if dynamic):
  world: world.md
  scenario: scenario.yaml
  # both modes (optional; omit to skip):
  style: style.md
  extract_examples: extract_examples.yaml
```

All `files` values are filenames relative to the pack directory. Defaults are used if omitted from `files` but the file exists (e.g., `seed_state.yaml` is tried automatically for static packs).

---

### `seed_state.yaml` (static mode — required)

Full initial game state. Hand-edit to taste.

```yaml
meta:
  game_name: default
  turn: 0
  setting_pack: my-pack
  model: ""              # stamped at New Game by engine

pc:
  name: "Character Name"
  tagline: "Role and defining trait — 5–10 words"
  bio: |
    2–4 sentences of pre-game history and motivation.
  stats:
    body: 2              # physical capability
    mind: 3              # perception, problem-solving
    tech: 2              # mechanical, electronic competence
    social: 3            # persuasion, reading people
  conditions: []         # active status effects (e.g. "infected", "wanted")

location:
  id: location-id-slug
  name: "Location Display Name"
  description: |
    2–4 sentences — what the player sees, smells, hears on arrival.

inventory:               # 1–12 items; InventoryItem schema
  - id: credits          # universal currency — always use this id
    name: Credits
    amount: 1800
    notes: "Context about what this buys."
  - id: item-slug
    name: "Item Display Name"
    amount: 1
    notes: "Condition, history, or what it's good for."

quests:                  # 1+ quests
  - id: quest-slug
    title: "Quest Title"
    status: active
    objectives:
      - description: "Specific, measurable objective."
        done: false
      - description: "Second objective."
        done: false

scene:
  tagline: ""            # 3–6 words — shown in UI header; leave empty for auto
  tags: [arrival, exposition]
  present_npcs:          # who is in the scene at game start
    - id: npc-slug
      name: "Full Name"
      title: "Role or occupation"
      notes: "Current attitude toward the player."
      bio: "1–3 sentences of durable identity and motivation."
  established_facts:     # world/situation facts the narrator never contradicts
    - "One concise sentence per fact (~10–25 words)."

compendium:
  npcs: {}               # leave empty; engine manages this
```

---

### `opening_scene.md` (static mode — required)

Plain markdown prose. Second person, present tense. 200–500 words.

Shown to the player before their first action. Sets tone, introduces the situation, and ends on a question or implied choice that invites the first input.

---

### `world.md` (dynamic mode — required)

Plain markdown. The world bible — durable facts about how this world works, regardless of who the player is.

**Structure rules:**
- H1/H2 headings (`# Title`) for sections — skipped as facts
- Bullet lines (`- fact`) and plain non-heading lines → each becomes one `established_facts` entry
- Keep individual facts to ~10–25 words
- Cover: the world's physics/biology/rules, factions and power structures, resource constraints, calendar/timeline, what still works

The engine parses these into `established_facts` at New Game time and prepends them before any scenario-specific facts the LLM adds. The LLM cannot contradict them.

---

### `scenario.yaml` (dynamic mode — required)

Generation brief — **constraints** (hard rules enforced post-validation) plus **inspiration** (quality guidance, not menus).

```yaml
constraints:
  min_named_npcs: 2          # NPCs with proper personal names
  min_objectives_per_quest: 2
  starting_quest_count: 1
  inventory_size_range: [4, 8]
  pc_stat_range: [1, 4]
  pc_stat_total_range: [8, 12]
  prose_word_range: [200, 450]
  required_inventory_kinds: [weapon, consumable]
  npc_distinct_first_letters: true   # prevent "all names start with M"
  forbid_cliches:
    - "chosen one"
    - "amnesia"
  forbid_player_dependents: true     # no spouse/kids unless player overrides request
  forbid_legendary_items: true       # no rare/exotic gear at start

inspiration:               # quality guidance — describe qualities, NOT examples
  pc: |
    Describe what kind of person fits this world's pressures. What shaped them.
    What they are good at and what they can't do. Avoid archetypes.
    Do NOT give a concrete example character.

  opening_situation: |
    Describe the qualities of a good opening — stakes, immediacy, specificity.
    Do NOT describe a concrete scenario. Tell the generator to surprise itself.

  npcs: |
    Describe what makes a good NPC in this world. Specificity, layered motivation,
    histories. At least one should carry something the player doesn't know.

  inventory: |
    Describe what realistic starting gear looks like in this world — not a list,
    but principles. Quantities matter. Avoid generic loadouts.

  quests: |
    Describe what makes a good starting quest — weight, personal stakes, visible
    cost. Avoid fetch-quest framing.
```

**Critical rule for inspiration prose:** Describe **qualities and anti-patterns only**. Do NOT give concrete examples like "e.g., a medic named Sara" or "perhaps the bridge is collapsing." Concrete examples in the prompt anchor the LLM and kill creative variance. The system prompt instructs the generator to surprise itself and avoid borrowing phrasing.

---

### `style.md` (both modes — optional)

Plain markdown. Genre tone rules appended to the narrator system prompt on every turn.

Write as a concise bullet list of rules the narrator must follow. Examples:
- Physics and resource constraints specific to this world
- How violence works and feels
- What dialogue sounds like (accents, register, idioms)
- What the world values / what causes fear
- Anything the narrator must never do

---

### `extract_examples.yaml` (both modes — optional)

Pack-flavored worked examples for the state extraction call. Replace the 3–5 examples here with ones set in your world — they improve extraction accuracy for your specific setting's items, NPCs, and quest patterns.

```yaml
examples:
  - title: "Brief description of what this example demonstrates"
    thinking: |
      - Bullet: what changed this turn (only rendered when enable_extract_thinking=true)
    json: |
      {"state_delta": {...}, "actions": [...]}
```

Each `json` value must be valid JSON. The `thinking` block is optional. The template renders it only when `enable_extract_thinking: true` in `config.yaml`.

Aim for 3–5 examples covering:
1. Core resource expenditure for your world (ammo, credits, food)
2. Condition add/remove (infection, injury, status change)
3. Quest creation and objective completion
4. NPC introduction with bio
5. Minimal-delta turn (pure dialogue, no state change)

---

## Future generator compatibility

The `generate_pack()` tool (Tool C, future PR) emits a `Pack` Pydantic object that this system validates and writes to disk. Its output contract is:

1. `pack.yaml` → validated by `PackManifest`
2. `world.md` → parsed by `parse_world_facts()`
3. `scenario.yaml` → validated by `ScenarioBrief` (constraints + inspiration)
4. `style.md` → plain text, passed through
5. `extract_examples.yaml` → each `json` field validated as parseable JSON

A generator calling `Pack.model_validate(...)` before writing catches any schema violations. The same `load_pack()` call that loads hand-authored packs loads generator-produced packs — zero special-casing needed.

---

## Player overrides (Tool B — UI deferred)

When the player customization UI ships, players will be able to supply soft hints at New Game time:

- `pc_hints`: "Retired nurse, early 60s, diabetic"
- `npc_hints`: "Include a younger sibling NPC"
- `location_hints`: "Somewhere cold"
- `quest_hints`: "I want a moral dilemma"
- `free_form`: anything else

These are injected into the `generate_seed` prompt as soft guidance. `world.md` canon and `scenario.yaml` constraints take precedence on conflict. Pack authors do not need to do anything special — this is handled by the engine.
