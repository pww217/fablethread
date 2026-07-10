---
title: "[Infra] Pack validation gate — default vs generated packs"
status: done
urgency: 3
size: medium
created: 2026-06-16
ticket_id: F-15
design: docs/design/to_scope/pack-validation-design.md
plan: plans/completed/tooling-infra/f-15-pack-validation-plan.md
labels:
  - Improvement
  - Tech Debt
---

## Note

F-15 was originally a discovery ticket for pack parity gaps. It was canceled but re-purposed for this implementation. The gap analysis findings were absorbed into `pack-validation-design.md` and `pack-parity-redesign.md`. This plan implements the validation gate.

## Detail

Default packs (packs/default/) and generated packs (packs/generated/) have major structural parity gaps — default packs are much sparser. Generated packs produce predictable starts because their world_facts name real locations and are treated as "non-negotiable canon" by the seed prompt, while defaults have zero world_facts and zero narrator_rules, giving the LLM complete freedom.

## Motivation

Predictable starts for generated packs defeat the purpose of seed randomization. The two pack types should be structurally identical (same fields populated) even if content differs in theme. Currently defaults are under-equipped (no world facts, no narrator rules, no factions) and generated are over-constrained (world facts with real place names pin location regardless of seed).

## Scope

* **In scope:** Identify every field mismatch between packs/default/ and packs/generated/ for both ScenarioBrief (scenario.yaml) and PackManifest (pack.yaml)
* **Out of scope:** Fixing the gaps — this is a discovery ticket for later decision

## Systems Affected

* `ccya/pack.py` — ScenarioBrief model
* `ccya/engine/generate_pack.py` — pack generation output
* `packs/default/*/scenario.yaml` — 6 default pack files
* `packs/default/*/pack.yaml` — 6 default pack manifest files
* `packs/generated/*/scenario.yaml` — 4 generated pack files
* `packs/generated/*/pack.yaml` — 4 generated pack manifest files
* `ccya/engine/seed.py:166` — name_seed resolution bug (already fixed separately)

## Evidence

### ScenarioBrief fields — present in generated, ABSENT from default

| Field | Default (6 packs) | Generated (4 packs) | Impact |
| -- | -- | -- | -- |
| world_facts | NONE (empty list) | 5 facts each, real place names (e.g. "The initial outbreak was traced to the Santa Monica Medical Center at sunrise") | **#1 cause of predictable starts** — facts are "non-negotiable canon" per seed prompt rule 3. Pins location regardless of seed value. |
| narrator_rules | NONE (empty list) | 8 rules each (e.g. "Zombies move with frantic, unpredictable sprinting speeds") | Generated guides LLM tone; defaults let LLM free-form |
| factions | NONE (empty list) | 3-4 modeled factions with id, name, description, disposition | Shapes political landscape, constrains NPC possibilities |
| world_name | Empty string | "Santa Monica Zero Hour" etc. | Minor, but reinforces identity |
| name_seed | Default 0 → random per bug on line 166 | 1203, 1977, 2026 — deterministic pool selection | Generated pool pre-selection is always same; default always randomizes |

### ScenarioBrief fields — present in default, ABSENT or partial in generated

| Field | Default | Generated |
| -- | -- | -- |
| world_rules | 4 of 6 have 1 rule | 4 of 4 have 2-3 rules (more rules, always present) |
| inspiration | 4 of 6 filled | 4 of 4 filled (always present) |
| currency_id | All 6 set (themed: dollars, credits, ryō, doubloons) | 2 of 4 set to empty string; 2 absent entirely |
| starting_currency_amount | All 6 set (varied: 0-100) | Same 2 of 4 set to 0 |

### PackManifest (pack.yaml) fields — present in default, ABSENT from generated

| Field | Default | Generated |
| -- | -- | -- |
| description | Rich paragraph per pack | NOT SET (missing entirely) |
| version | 1-3 | NOT SET |
| mode | dynamic | NOT SET |
| files | world.md + scenario.yaml refs | NOT SET |
| use_male_only_names | Mixed (4 true, 2 false) | All false |
| baseline_facts | 3 rich facts | Empty list |

### Dead keys in default only

Default packs have `min_objectives_per_quest` and `starting_quest_count` under `constraints:` in YAML — silently ignored by Pydantic (no model fields, extra='ignore'). Generated packs don't have these.

### Near-parity fields (both set with comparable content)

constraints, situation_archetypes, arc_categories, character_dynamics, moral_pressures, npc_bonds, scene_detail_bundles, name_locales, tone_tags

### Related bug already fixed

`ccya/engine/seed.py:166` had `name_seed = (scenario.name_seed if scenario and scenario.name_seed else 0) or random.randint(...)` — the `0 or random` fallback conflated `name_seed: 0` (explicit) with `name_seed` absent. Changed `name_seed: int = 0` to `name_seed: int | None = None` in [pack.py](<http://pack.py>) and fixed the guard to check `is not None`.
