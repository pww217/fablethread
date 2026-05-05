# Phase 2 — Eval pack (static, deterministic)

**Goal:** Hand-author the static `eval-pack` under `evals/packs/eval-pack/`. After
this phase the pack loads via the existing `load_pack()` function and produces a
mid-game state that exercises every system the eval harness needs to test.

**Prerequisites:** Phase 1 complete (`ccya/eval/` exists, `evals/config.yaml` exists).

**Estimated context:** ~40K tokens.

---

## Files to read first

Only these. Do not load `engine.py` or other large files.

- `ccya/plans/p3-inference/eval-harness.md` — overview
- `ccya/plans/p3-inference/eval-harness/01-foundations.md` — handoff state
- `ccya/packs/AUTHORING.md` — pack file spec (already read by humans; read here as the canonical schema)
- `ccya/ccya/pack.py` lines 22-100 — Pydantic schemas: `SeedPC`, `SeedLocation`, `SeedQuest`, `SeedScene`, `SeedState`, `SeedCompendium`
- `ccya/ccya/pack.py` lines 207-298 — `Pack`, `_check_mode_files`, `load_pack` (note: static packs require BOTH `seed` and `opening_text`)
- `ccya/ccya/models.py` lines 95-105 — `InventoryItem` schema (id/name/notes/amount/aliases)
- `ccya/ccya/models.py` lines 142-156 — `NpcRef`, `CompendiumNpcUpdate` schemas
- `ccya/packs/expanse/pack.yaml` — example pack manifest (mode: dynamic — note differences)
- `ccya/packs/expanse/seed_state.yaml` — reference seed format (NOTE: this pack is dynamic; we want static)
- `ccya/packs/expanse/extract_examples.yaml` — example extract examples format

That's it. Do NOT read engine.py, state.py, or any other pack's full contents.

---

## Design constraints (MUST satisfy these)

The eval pack is purpose-built to exercise every system the eval harness checks.
Hand-author every value — no LLM generation, no copy-paste from existing packs.

**Mid-game starting state (turn=12):**
- 5 NPCs total in compendium:
  - 2 friendly (one currently present, one in compendium-only)
  - 2 hostile (both currently present)
  - 1 ambient (in compendium, NOT present — tests `recently_left` carryover via prior delta)
- 3 quests, mixed states:
  - quest A: `active`, 2 objectives both open
  - quest B: `active`, 1 objective done + 1 open
  - quest C: `active`, 2 objectives done + 1 open (close to completion — tests auto-complete logic when player finishes the last)
- Inventory (must satisfy `min_length=1, max_length=12` per `SeedState`):
  - `credits` (universal currency, amount 850)
  - 1 weapon: `iron_dagger` amount 1
  - 1 ammo-style consumable: `bandages` amount 3 (tests quantity arithmetic)
  - 1 single-use: `brass_key` amount 1 (tests full-stack remove)
  - 1 quest item: `merchant_seal` amount 1
  - 1 mundane: `traveler_cloak` amount 1, with aliases `["cloak", "travel cloak"]` (tests alias resolution + fuzzy match)
- 2 active conditions on PC:
  - `bruised_ribs` added_turn=8
  - `low_morale` added_turn=10
- `scene.world_state` (3 facts, immutable after seed)
- `scene.recent_events` (5 entries — note: `SeedScene.recent_events` is `list[str]`
  in pack schema; the engine's `_migrate_recent_events()` upgrades these to
  `{id, text, turn}` objects on first load — let it do its job)
- `scene.scene_pressure`: NOT a `SeedScene` field — leave it out of the seed.
  The eval harness will surface scene_pressure naturally as turns progress, OR
  we'll add it via a manual delta in the runner (phase 3 decides).

**Pack manifest fields:**
- `mode: static` — do NOT use dynamic mode (we want zero LLM noise during seed load)
- `id: eval-pack`
- `name_locales`: provide one entry only (`en_US` weight 1.0) to keep name generation deterministic

**Style.md and extract_examples.yaml:**
- `style.md` is intentionally NEUTRAL — no genre flavor — so it doesn't bias the
  judge's narrative-quality score across runs.
- `extract_examples.yaml` provides 3 examples covering: inventory remove with
  amount, condition add, quest objective by index. Keep them eval-pack-flavored
  (use `iron_dagger`, `bandages`, etc.).

---

## Files to create

### 1. `evals/packs/eval-pack/pack.yaml`

```yaml
id: eval-pack
name: "Eval Pack — Deterministic Test World"
description: "Hand-authored static pack for the ccya eval harness. Mid-game state exercising NPCs, quests, conditions, inventory, recent_events, and aliases."
genre: neutral
tone_tags: [deterministic, test-fixture]
version: 1
mode: static
files:
  seed: seed_state.yaml
  opening: opening_scene.md
  style: style.md
  extract_examples: extract_examples.yaml
name_locales:
  - locale: en_US
    weight: 1.0
```

### 2. `evals/packs/eval-pack/seed_state.yaml`

```yaml
meta:
  game_name: eval
  turn: 12
  setting_pack: eval-pack
  model: ""

pc:
  name: Aren Voss
  tagline: Reluctant courier on the merchant road
  bio: |
    Mid-thirties, broad shoulders, careful with words. Took on a courier contract
    to clear an old debt. Twelve days into a fortnight job and already two days
    behind schedule.
  stats:
    strength: 3
    dexterity: 3
    wits: 2
    lore: 2
    charisma: 3
    resolve: 3
  conditions: []
  momentum: 0

location:
  id: roadside_inn
  name: The Crossed Keys Inn
  description: |
    A timber-framed inn at the junction of the merchant road and the old quarry track.
    Common room half-full, hearth banked low, stew bubbling on the hook. The merchant
    Halden sits at the corner table, ledger open. A pair of road-toughs lean by the
    door, watching everyone who comes in.

inventory:
  - id: credits
    name: Credits
    amount: 850
    notes: Common coin, accepted at any inn or stall on the merchant road.
  - id: iron_dagger
    name: Iron dagger
    amount: 1
    notes: Plain crossguard, edge worn from honing. Belt-carried.
  - id: bandages
    name: Linen bandages
    amount: 3
    notes: Three rolls. Field-grade — won't replace a healer.
  - id: brass_key
    name: Brass key
    amount: 1
    notes: Halden gave you this in trust. You don't yet know what it opens.
  - id: merchant_seal
    name: Halden's merchant seal
    amount: 1
    notes: Pressed wax sigil. Proof of contract — show this only to the right people.
  - id: traveler_cloak
    name: Traveler's cloak
    amount: 1
    notes: Oiled wool, road-stained, hood deep enough to hide a face.
    aliases:
      - cloak
      - travel cloak

quests:
  - id: deliver_the_ledger
    title: Deliver Halden's Ledger
    status: active
    objectives:
      - description: Carry the ledger to the merchant Halden at the Crossed Keys Inn.
        done: false
      - description: Confirm the contract with Halden in person.
        done: false
  - id: clear_the_road_toughs
    title: Clear the Road Toughs
    status: active
    objectives:
      - description: Find out who hired the toughs blocking the road.
        done: true
        failed: false
      - description: Convince, pay, or remove the toughs from the inn.
        done: false
  - id: settle_the_debt
    title: Settle the Old Debt
    status: active
    objectives:
      - description: Earn at least 1000 credits from courier work.
        done: true
        failed: false
      - description: Find Caron, the man you owe.
        done: true
        failed: false
      - description: Pay Caron in person and have him mark the debt cleared.
        done: false

scene:
  tagline: Stew, ledger, watching eyes
  tags:
    - dialogue
    - mid-game
  present_npcs:
    - id: halden
      name: Halden
      title: Merchant
      notes: Sits at the corner table with his ledger open, glances up when the door swings.
      bio: A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
    - id: tough_a
      name: Bald Tough
      title: Road thug
      notes: Leans by the door with arms crossed, watching the room without subtlety.
      bio: Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
    - id: tough_b
      name: Scarred Tough
      title: Road thug
      notes: Stands close to Bald Tough, hand resting on the hilt of a short blade.
      bio: Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
  world_state:
    - The Crossed Keys Inn sits at the junction of the merchant road and the old quarry track, a half-day's walk from the nearest village.
    - Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
    - The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.
  recent_events:
    - You took on Halden's courier contract twelve days ago in Marrow's Crossing.
    - You spent two nights in the open after the bridge at Holt's Ford was washed out.
    - At the village of Brindle's End you were warned that road-toughs were extorting travelers near the Crossed Keys Inn.
    - You arrived at the Crossed Keys Inn this evening and saw Halden already at his corner table.
    - You overheard one of the toughs at the door mention "Caron's coin" before you stepped inside.

compendium:
  npcs:
    halden:
      name: Halden
      title: Merchant
      bio: A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
    tough_a:
      name: Bald Tough
      title: Road thug
      bio: Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
    tough_b:
      name: Scarred Tough
      title: Road thug
      bio: Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
    caron:
      name: Caron
      title: Old creditor
      bio: The man you owe coin to. Lives in Marrow's Crossing. Patient, but not forgiving.
    innkeeper:
      name: Edda
      title: Innkeeper at the Crossed Keys
      bio: Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.
```

NOTES on this file:

- `pc.conditions` is left as `[]` even though we want 2 active conditions in the
  starting state. **Reason:** `SeedPC.conditions: list[str]` only accepts strings
  — the rich `Condition` object with `added_turn` is created by the engine via
  `_coerce_condition_str()` in `models.py`. To get the rich shape with explicit
  `added_turn`, set them via the runner phase by editing `state.yaml` directly
  after `init_save_dir()` writes the seed. **Phase 3 (runner) handles this.**
- The `compendium.npcs.innkeeper` entry tests "NPC in compendium but NOT in
  present_npcs" — exercising the LRU compendium injection logic.
- The quest `settle_the_debt` is one objective away from auto-complete — the
  full_cycle scenario in phase 6 will trigger that completion.

### 3. `evals/packs/eval-pack/opening_scene.md`

The `Pack` validator requires `opening_text` for static mode. This is shown to
the player only on the very first New Game — for evals the runner always
short-circuits this since the scenario starts mid-game. Keep it minimal but
non-empty.

```markdown
You step into the common room of the Crossed Keys Inn. The hearth is banked low, stew
hangs over coals, and Halden sits at the corner table with his ledger open. Two road-
toughs lean by the door, watching the room without bothering to hide it.

The brass key Halden gave you in Marrow's Crossing is heavy in your pocket. The
merchant seal weighs less but matters more. Your bandages are running low and your
ribs still ache from the bridge crossing two days back.

Twelve days into the contract. The road has been quiet, and quiet on this road usually
means someone is watching. Halden notices you and tips his head — the small, careful
nod of a man who has been waiting longer than he expected to.

What do you do?
```

### 4. `evals/packs/eval-pack/style.md`

Intentionally neutral — no genre flavor — to keep the judge's narrative-quality
score uncontaminated by stylistic preferences across eval runs.

```markdown
# Eval-pack style

This pack is a deterministic test fixture. The narrator should write in a plain,
clear, second-person past-tense register. Keep these in mind:

- Specific over abstract. Name the thing the player did, the object they touched, the
  NPC they spoke to. Avoid generic mood words ("an air of menace") in favor of
  concrete sensory detail.
- One scene per turn. Do not skip ahead in time unless the player explicitly does so.
- Honor the dice. If the rules outcome is `fail` or `setback`, the action did not
  succeed; describe the cost. If `partial`, the action succeeded with a complication.
- Honor the present_npcs. Every named NPC in the scene either acts, reacts, or is
  visibly present in the prose. Do not invent new NPCs unless the player's input
  introduces one.
- Plain language. No archaic phrasing, no fantasy-trope syntax ("Lo, the door...").
  This is a working road in a working world.
- 120-220 words per turn unless the action is large.
```

### 5. `evals/packs/eval-pack/extract_examples.yaml`

Three eval-pack-flavored examples covering inventory remove with amount,
condition add, and quest objective by index. Each `json` block must be valid JSON.

```yaml
examples:
  - title: "Bandages used (2 rolls) — inventory_remove with amount"
    band: partial
    thinking: |
      - Player wrapped Halden's wound. Used 2 of the 3 bandage rolls.
      - Inventory remove by id, amount=2; the engine subtracts from the stack.
    json: |
      {
        "scene_tags": ["dialogue", "first_aid"],
        "scene_tagline": "Bandaged — one roll left",
        "present_npcs": [{"id": "halden", "notes": "Wincing but steady; pressing the wrap with one hand."}],
        "inventory_remove": [{"id": "bandages", "amount": 2}],
        "outcome_summary": "You wrapped Halden's gash. Two rolls used; one remains."
      }

  - title: "Condition added — bruised ribs flare after a brawl"
    band: setback
    thinking: |
      - Strength check failed mid-brawl; ribs cracked harder than the bruising already there.
      - Add a new condition with explicit id, label, description.
    json: |
      {
        "scene_tags": ["combat", "consequence"],
        "scene_tagline": "Ribs cracked — breath comes hard",
        "pc_condition_add": [{"id": "cracked_ribs", "label": "cracked ribs", "description": "Tough hit landed flat on already-bruised ribs; deep breaths sting."}],
        "outcome_summary": "You took the punch flat to the ribs. The bruise just became a fracture."
      }

  - title: "Quest objective done by index"
    band: success
    thinking: |
      - Player handed Halden the ledger; first objective of deliver_the_ledger is done.
      - Use index=1 to mark it; engine resolves index → objective.
    json: |
      {
        "scene_tags": ["dialogue", "delivery"],
        "scene_tagline": "Ledger handed over",
        "present_npcs": [{"id": "halden", "notes": "Takes the ledger with both hands; thumbs the wax seal."}],
        "quest_updates": [{"id": "deliver_the_ledger", "objectives": [{"index": 1, "done": true}]}],
        "outcome_summary": "Halden took the ledger and pressed the seal home with his thumb."
      }
```

---

## Verification

```bash
# 1. Files exist
test -f evals/packs/eval-pack/pack.yaml
test -f evals/packs/eval-pack/seed_state.yaml
test -f evals/packs/eval-pack/opening_scene.md
test -f evals/packs/eval-pack/style.md
test -f evals/packs/eval-pack/extract_examples.yaml

# 2. The pack loads cleanly via load_pack()
uv run python -c "
from pathlib import Path
from ccya.pack import load_pack
pack = load_pack('eval-pack', Path('evals/packs'))
assert pack.manifest.mode == 'static'
assert pack.seed is not None
assert pack.seed.meta['turn'] == 12
assert pack.seed.meta['setting_pack'] == 'eval-pack'
assert len(pack.seed.inventory) == 6
assert len(pack.seed.quests) == 3
assert len(pack.seed.compendium.npcs) == 5
assert len(pack.seed.scene.present_npcs) == 3
assert len(pack.seed.scene.recent_events) == 5
assert len(pack.extract_examples) == 3
assert pack.opening_text.strip().startswith('You step into')
print('eval-pack loads OK')
print('  inventory:', [i.id for i in pack.seed.inventory])
print('  quests:', [q.id for q in pack.seed.quests])
print('  present:', [n.id for n in pack.seed.scene.present_npcs])
print('  compendium:', list(pack.seed.compendium.npcs.keys()))
"

# 3. Apply seed via init_save_dir + load_state — confirm migrations run cleanly
uv run python -c "
import tempfile, yaml
from pathlib import Path
from ccya.pack import load_pack
from ccya.state import init_save_dir, load_state

pack = load_pack('eval-pack', Path('evals/packs'))
seed = pack.seed.model_dump()
with tempfile.TemporaryDirectory() as tmp:
    save_dir = Path(tmp)
    init_save_dir(save_dir, seed)
    st = load_state(save_dir)
    # recent_events should have been migrated string -> dict
    events = st['scene']['recent_events']
    assert isinstance(events[0], dict), f'recent_events not migrated: {events[0]!r}'
    assert all('id' in e and 'text' in e for e in events)
    # PC stats migration check (no body/mind/tech/social)
    stats = st['pc']['stats']
    assert 'body' not in stats
    assert 'strength' in stats
    print('seed applies + migrates OK; %d recent_events as objects' % len(events))
"

# 4. extract_examples JSON is parseable (Pydantic already validates this on load)
uv run python -c "
import json
from pathlib import Path
from ccya.pack import load_pack
pack = load_pack('eval-pack', Path('evals/packs'))
for ex in pack.extract_examples:
    json.loads(ex.json_text)
print('all %d extract_examples are valid JSON' % len(pack.extract_examples))
"

# 5. Existing tests still pass
uv run pytest -q tests/test_engine_smoke.py tests/test_pack_loader.py
```

If any verification step fails, fix the YAML/markdown and re-run. Common pitfalls:

- Inventory must be 1–12 items (we have 6 — fine)
- Each quest must have ≥1 objective (we have 2-3 each — fine)
- `extract_examples.yaml`: each `json` value must be parseable JSON. If you add
  trailing commas or unquoted keys it will fail Pydantic validation.
- `seed_state.yaml`: `pc.conditions` must be `[]` or `list[str]`. Do not put
  dicts there — that's a runtime-only shape.

---

## STOP HERE

Phase 2 is complete. Verify all checks pass, then stop and start a new chat with
`eval-harness/03-runner.md`.

### Handoff to phase 3

State after this phase:

- `evals/packs/eval-pack/` exists with all 5 files. `load_pack('eval-pack', Path('evals/packs'))` returns a valid `Pack` with `mode=static`, 6 inventory items, 3 quests, 5 compendium NPCs, 3 present NPCs.
- The seed produces a valid mid-game state at turn=12 when written via `init_save_dir`.
- `pc.conditions` is `[]` in the seed — the runner (phase 3) is responsible for adding the two starting conditions (`bruised_ribs` added_turn=8, `low_morale` added_turn=10) directly to `state.yaml` after seed load. Phase 3 is aware of this.
- No runner code yet — `ccya/eval/runner.py` does not exist.
- No scenarios yet — `evals/scenarios/` does not exist.

Phase 3 builds the in-process runner that will execute scenarios against this pack.
