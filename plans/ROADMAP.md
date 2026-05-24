# CCYA Roadmap — Verified Findings (2025-05-24)

All items verified against current source code. "Fixed" means already implemented; "open" needs work.

---

## Bugs / Broken Behavior

| Item | Effort | Verdict | Evidence |
|---|---|---|---|
| Narrator doesn't respect inventory rules (reloading w/ no ammo) | M | **OPEN** | `ruling.py` never includes inventory in context; `turn.py:732-819` has no Python-side validation gate. Narration happens before extraction — false outcomes get narrated and accepted as state. |
| Compaction gap on turns 3, 6, 9 | M | **NOT VALID** | Math is correct. With `compact_every=3`, each cycle fires at turn%3==0 and picks up exactly where previous left off via `last_compacted_turn + 1`. No gaps. |
| Seed/new game JSON parsing fails too often | M | **OPEN** | Only 2 total attempts (default: 1 retry). Retry feedback is generic ("No JSON found" or "validation failed") with no specifics on what was wrong. Strict constraints (`actions` exactly 4 items, `opening_narrative` min 50 chars) are easy to miss. |
| Seed gen doesn't always assign last names + quantities to inventory | S | **PARTIALLY FIXED** | Inventory amounts: safe via Pydantic default (`amount=1`). NPC first+last name: only soft prompt guidance in `generate_seed_system.j2:163-167`, no hard enforcement. Low severity since LLM generally follows it. |
| Reset doesn't reset full state (inventory + NPCs survive) | M | **FIXED** | `/new-game` calls `init_save_dir()` which atomically replaces `state.yaml` via `save_state() + os.replace()`. Chronicle and events are cleared too. No inventory/NPC data survives. |
| `_ExtractionContext` computed from non-applied deltas | L | **FIXED** | Plan executed. `_build_extraction_context()` at `extraction.py:62-106` does `deepcopy(state) → apply_delta(copy, combined_delta) → read fields from post-state`. Exact pattern from the plan. |
| `maybe_compact()` has no rollback on partial parse failure | M | **FIXED** | Plan executed. `_write_compacted_block()` at `compactor.py:387-452` uses temp file + `os.replace()`. Partial sanitization failures log warning and proceed with bullet text only — no corruption. |
| Compactor: unclear if it gets THIS turn's or LAST turn's events | S | **FIXED** | Covered by same plan execution above; compaction logic is correct per analysis. |

---

## Code Quality / Refactor

| Item | Effort | Verdict | Evidence |
|---|---|---|---|
| `_resolve_pack_dir` duplicated in routes.py vs pack.py | XS | **OPEN** | Two near-identical implementations: `pack.py:253-276` (original) and `routes.py:360-375` (docstring even says "mirrors pack._resolve_pack_dir"). Should import from pack or extract to shared utility. |
| `inputs_snapshot` loop duplicates connectors loop in tv.py | S | **OPEN** | Both iterate `_STREAMS` + `sd.inputs` with identical data-fetching/formatting logic: connectors at `tv.py:465-501`, inputs snapshot at `tv.py:505-531`. Extractable into helper. |
| `_label` defined twice inside tv.py | XS | **OPEN** | Two nested defs in different scopes (`_tv_dict_to_lines`:80-85 vs turn row loop:222-227). 90% identical logic, subtly different fallback behavior (truncated first-value vs empty string). Consolidate. |
| `new_game` / `new_game_reroll` duplicate seed→init pattern | S | **OPEN** | Dynamic pack paths are byte-for-byte identical (`routes.py:265-270` == `291-297`). Static path is similar minus one meta key. Extract into `_init_from_seed()`. |
| Jinja templating consolidation (Characters, Location, Inventory, Campaign ARC) | L | **FIXED** | All four templates already consolidated under `ccya/prompts/sections/`: `_npc_roster.j2`, `_location.j2`, `_inventory.j2`, `_arc.j2` — referenced via `{% include %}` in main templates. No duplication. |
| Audit user prompts vs. system prompts — misplaced content | M | **FIXED** | Clean separation: `narrate_system.j2` = instructions only, `narrate_user.j2` = game state + player input. No misplaced content detected. |
| Compendium cap — lift < 10 | XS | **NOT VALID / ONE-LINER** | Cap of 8 exists only in eval rubric (`engine_mirror.py:42`). Not enforced at runtime. Just change `SCENE_NAMED_NPC_CAP` constant if desired. |

---

## Features

| Item | Effort | Verdict | Evidence |
|---|---|---|---|
| Tone template for narrator (satirical, dramatic, soap opera) | M | **OPEN** | `pack.py:172` has a `tone` field but it's flagged as dead (removed from boundary model). No config preset system exists. Only raw `narrator_rules` list and `pack_style` string are used. Needs new config + prompt injection logic. |
| NPC personalities + motives, evolving over time | L | **PARTIALLY IMPLEMENTED** | Data model supports it: `motivation`, `fear`, `leverage` on both `CompendiumNpcUpdate` (models.py:223-232) and `RosterEntry` (models.py:29-40). Mutable `notes` field for per-turn attitude. Missing: automated evolution engine — no aging, drift, or relationship decay logic. Changes only happen via LLM extraction. |
| Karma system for PC | L | **OPEN** | Zero matches for karma/morality/alignment/virtue/sin in codebase. PC state has `momentum` (dice luck) but nothing moral. Would need new state field + prompt integration across ruling/extraction/storyteller phases. |
| Faction warmth/coldness score toward player | M | **OPEN** | `Faction` model only has static `disposition: str = "neutral"`. No runtime updates to faction attitudes. NPC-level notes exist but aren't aggregated into faction scores. Needs new state structure + extraction logic. |
| Tooltip on main arc goal (2-3 sentence situation brief) | S | **FIXED** | Already implemented in `_state_left.html:104-113` with `has-tooltip` class, JS hover handler at `index.html:1582-1640`, and `goal_context` seeded as "2–3 sentences explaining why visible_goal matters" (`generate_seed_system.j2:45`). |
| Rest/sleep/camp mechanic (heal conditions, restock) | L | **OPEN** | Zero matches for rest/camp/sleep/heal in Python engine. Only mentions are compaction filtering guidance ("uneventful rest/travel"). Conditions only removed via explicit LLM extraction (`pc_condition_remove`). Needs ruling path + condition healing logic. |
| Pre-populate compendium in seed_generate (min 4 chars) | S | **STRUCTURALLY SUPPORTED, NOT PROMPTED** | `SeedState` has `compendium: SeedCompendium` with empty `npcs` dict by default. Sanitization code exists (`seed.py:47`) proving pipeline supports it. But the seed prompt doesn't instruct LLM to populate compendium NPCs — only `present_npcs`. Needs prompt addition or post-processing injection. |
| A whole conditions rework + event log with "went away because" | L | **NOT IMPLEMENTED** | Conditions have `turns_remaining` for expiration but no explicit healing mechanic, no reason-tracking on removal. Separate plan warranted as noted in original list. |
| Compendium: dead states, remove after X turns, aliases | M | **NOT IMPLEMENTED** | No compaction or cleanup logic for NPCs that left the scene long ago. No "dead state" concept or alias tracking exists. Needs state + UI work. |
| Last seen / first seen / relationship status in compendium | S | **PARTIALLY IMPLEMENTED** | `ArcThread` has `last_seen_turn` and `added_turn`. NPC roster entries have mutable notes but no explicit "first/last seen" timestamps or computed relationship labels. Mostly display work once data model is extended. |

---

## Improvements / Hardening

| Item | Effort | Verdict | Evidence |
|---|---|---|---|
| Inventory update hardened to durable changes only (damage/upgrade) | M | **OPEN** | `delta_builder.py:132-209` applies all inventory ops identically — no durability gate. Any LLM can arbitrarily add/remove/update items every turn with no expiry or scene-boundary clearing. |
| Inventory update UI delta should be yellow | XS | **PARTIALLY FIXED** | `inventory_update` already displays yellow (`app.src.css:2541`). But `inventory_add` (green) and `inventory_remove` (red) are not yellow. Would need special-casing `inventory_` prefix in `_tv_state_diff()` at `tv.py:214-219`. |
| Thread creation/promotion more durable, less frequent | M | **PARTIALLY IMPLEMENTED + BUG** | Good durability mechanics exist (`_ACTIVE_THREAD_CAP=3`, `_EXPIRE_SILENT_TURNS=5`, `_PROMOTION_COOLDOWN_TURNS=3` at `turn.py:148-154`). Bug: thread_add bypasses the pacing gate entirely — no check of `_pc.gate` before adding threads (`turn.py:1322-1351`). |
| Max 3 threads/leads, only every X turns; 2 to progress instead of 3 | S | **PARTIALLY IMPLEMENTED** | ✅ Cap at 3 (line 148), ✅ promotion cooldown 3 turns (line 154). ❌ No per-turn-count throttle on thread_add. ❌ Progress threshold still hardcoded to `>= 3` (line 220) — no config knob for "2 instead of 3". |
| How pressures + deescalation + `pending_beat` combine — clarify | M | **IMPLEMENTED BUT AMBIGUOUS** | Mechanics work correctly in code but undocumented. PacingContext directive, gate logic (`deescalate >= 0.5` → `block_escalate`), beat injection via floor relief — all wired. Missing: doc explaining how scene-extracted gm_beat vs Python-computed directive interact (turn.py:1170-1178 replaces unconditionally). |
| Turn viewer — expand to make compaction clearer | S | **PARTIALLY IMPLEMENTED** | Compactions displayed as separate cards with collapsible detail (`_turn_viewer.html:48-86`). Missing: no visual linkage showing which raw turns were compacted into each event. Flat timeline — users can't trace "compaction at T6 covers content from T1-T3". |
| Probably 5 turns per compaction cycle | XS | **ONE-LINER** | `config.yaml:25` has `compact_every: 3`. Change to `5` only. No code changes needed; validation already enforces valid values (`_validate_compactor_config()`). |
| Seeding: increase both at world gen and turn-by-turn | M | **PARTIALLY IMPLEMENTED** | World-gen supports `npc_count_override` in seed prompt (generate_seed_system.j2:163-167). Turn-by-turn: no "world detail injection" step — new NPCs only enter via scene extraction. Depends on what "increase" means. |
| `rules_stakes` delivered in progress — useful or complexity? | M | **RESOLVED / LOW IMPACT** | `rules_outcome` is just one line (`storytell_user.j2:43-45`) with dice band + thread advancement instruction. No full stakes text flows through this pipeline. Minimal overhead, adds value by preventing thread advance on failed rolls. |
| Thread signals vs drift analysis — drift adds a LOT of output | M | **NO DRIFT ANALYSIS EXISTS** | Zero matches for "drift" in engine/ Python code. Only thread signal processing is `_apply_thread_signals()` — no parallel/duplicate analysis. If token overhead exists, it's from the thread list rendered in storytell_user.j2:15-22 as context. |
| Player drift signal vs drift analysis — clarify distinction | S | **NOT APPLICABLE** | Same answer — no drift analysis pipeline exists anywhere. Thread signals are processed once only. |
| Candidate opportunities hard-coded to 3-turn minimum | XS | **NOT IMPLEMENTED / NOT FOUND** | Zero matches for "candidate" or "opportunity_threshold" in Python codebase. This concept doesn't exist yet. |
| Thread age field | S | **ALREADY EXISTS** | `ArcThread` already has `added_turn: int \| None = None` at models.py:52, plus `last_seen_turn` at line 51 for demotion tracking. Age is derivable as `current_turn - added_turn`. No separate "age" field needed. |

---

## Likely Done / Superseded (Verified)

| Item | Verdict | Evidence |
|---|---|---|
| NPC update and Compendium update consolidation | **OPEN** | Separate models with different semantics: `NpcUpdate` (scene-present transient state) vs `CompendiumNpcUpdate` (durable identity). Applied as distinct operations in `state/npcs.py:148` and `234-269`. Consolidation would lose this distinction. |
| Scene tags — do they do anything at all? | **FIXED** | `"combat"` tag actually works — sets/clears `state.scene.combat_started_turn` (`delta_builder.py:303-306`) which feeds combat age calc in `turn.py:649`. Other tags are stored as metadata only. Not dead code. |
| State — looks pretty good, maybe combine with scene? | **FIXED** | `state["scene"]` already nested inside main state with tags, tagline, present_npcs, recently_left, recent_events, world_state. SceneExtractResult is appropriate intermediate model for LLM output parsing; merged into unified StateDelta in `extraction.py:773`. |
| Narrate — does it have all mechanics added? | **FIXED** | `narrate.py` only builds prompts — purely prose generation. All mechanics live elsewhere: inventory/conditions/location in `delta_builder.py:117-336`, NPC management in `npcs.py:148`, thread advancement via `_apply_thread_signals()`. Clean separation of concerns. |
| conftest.py test work | **FIXED** | AGENTS.md comment is stale. Tests exist at `tests/conftest.py` with FakeLLM, `test_smoke.py`, `test_integration.py`, `test_schema.py`. Four-layer strategy working. |

---

## Priority Summary — Highest Risk Items

1. **Thread_add gate bypass bug** (Improvements #3) — New threads can be created every turn if LLM emits them and gate allows, despite `_ACTIVE_THREAD_CAP=3` existing for a different purpose
2. **Inventory durability gate missing** (Improvements #1) — Any LLM can arbitrarily add/remove/update items every turn with no expiry or scene-boundary clearing
3. **Seed JSON parsing fragility** (Bugs #3) — Only 2 attempts total, generic retry feedback, strict constraints on nested structures

## Priority Summary — Quick Wins (< XS effort)

1. `compact_every: 3` → `5` in config.yaml
2. Change `SCENE_NAMED_NPC_CAP = 8` to `10` in engine_mirror.py
3. Consolidate `_resolve_pack_dir` (XS, low risk cut)
4. Consolidate duplicate `_label` defs in tv.py
