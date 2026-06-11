# Priorities — Critical Fixes Ranked by Impact

> Top priorities selected from [FINDINGS-JUNE-6.md](FINDINGS-JUNE-6.md), [MOMENTUM-BEAT-FINDINGS.md](MOMENTUM-BEAT-FINDINGS.md), [BUGS-OBSERVATIONS.md](BUGS-OBSERVATIONS.md), [EVAL-FINDINGS-2026-06-09.md](EVAL-FINDINGS-2026-06-09.md), and [FEATURE-IDEAS.md](FEATURE-IDEAS.md).
> Ranking criteria: severity × confidence × cross-game validation × fidelity impact.
>
> **Status:** Audited 2026-06-10 against source. 14 items confirmed FIXED, 7 PARTIALLY FIXED, 15 still OPEN (4 engine, 11 eval checkers, 3 features). See audit report below.

---

## 1. F-N08/F-N09 — Seed JSON vs hints conflict [H/H] — **FIXED**

**Severity:** High | **Confidence:** High (root cause of multiple downstream issues) | **Scope:** Game setup/pack generation

**Status:** FIXED — `01-seed-fixes.md` plan: when hints are provided, LLM seed generation is skipped entirely and the static pack's `seed_state.yaml` is used instead. Inventory removed from seed instructions. Opening narrative instructions sharpened to weave seed data naturally.

**See also:** [F-N08](./FEATURE-IDEAS.md#f-n08-seed-json-vs-hints-conflict-net-new--priority-1--fixed) | [F-N09](./FEATURE-IDEAS.md#f-n09-disable-seed-json-when-hints-given-net-new--priority-1--fixed) | [F-N01](./FEATURE-IDEAS.md#f-n01-alias-consolidation-net-new--priority-2--fixed) | [F-N02](./FEATURE-IDEAS.md#f-n02-stale-character-cleanup-net-new--priority-2--partially-fixed) | [F-I01](./FEATURE-IDEAS.md#f-i01-bond-naming-fix-improvement) | [F-I09](./FEATURE-IDEAS.md#f-i09-bonds-generate-arc-objectives-at-start-net-new) | [F-I02](./FEATURE-IDEAS.md#f-i02-turn-1-seed-integration-net-new--priority-6--fixed) | [B11 (Elias)](./EVAL-FINDINGS-2026-06-09.md#bug-11-key-npc-never-extracted-from-narration--scene-extraction-prompt-blind-spot-medium) | [B7](./BUGS-OBSERVATIONS.md#b7-h-location-changes-silently-dropped-from-canonical-state---confirmed-in-baseline) | [01-seed-fixes.md](../completed/01-narration/01-seed-fixes.md)

### Evidence

When both seed JSON and player hints are provided at game creation, they conflict — both inject into the same initial state, causing:
- Compendium duplication (introducing new chars too fast, not reusing existing)
- Missing NPCs (seed NPCs not in compendium, e.g., Elias)
- Bond issues (family referred to generically as "kin" instead of named)
- Location never changing (seed location overrides hints or vice versa)
- No clear story opening (seed data lists things rather than weaving into narrative)

### Impact

This is the root cause of multiple compendium, narrative, and fidelity issues. Fixing it would resolve or significantly reduce: F-N01, F-N02, F-I01, F-I09, F-I02, B11 (Elias), and potentially B7 (location changes).

### Fix direction

- Define merge/override semantics: when hints are provided, seed JSON should be disabled or merged with clear precedence rules
- Seed JSON should not inject NPCs that hints already define
- Seed location should be compatible with hint-provided context
- Ensure bond data from seed is used to generate concrete arc objectives, not abstract "secure family safety"

---

## 2. F-N01/F-N02 — Compendium dedup + stale character cleanup [H/M]

**Severity:** High | **Confidence:** High (confirmed across multiple games) | **Scope:** Compendium lifecycle

**Status:** F-N01 (alias consolidation) FIXED — `02-npc-compendium-hardening.md` plan: alias-first naming instruction in extraction prompt prevents duplicate entries. F-N02 (stale character cleanup) still open — TTL-based removal of unnamed non-key NPCs not yet addressed.

**See also:** [F-N01](./FEATURE-IDEAS.md#f-n01-alias-consolidation-net-new--priority-2--fixed) | [F-N02](./FEATURE-IDEAS.md#f-n02-stale-character-cleanup-net-new--priority-2--partially-fixed) | [F-N03](./FEATURE-IDEAS.md#f-n03-npc-deathremoval-lifecycle-net-new) | [B11 (Elias)](./EVAL-FINDINGS-2026-06-09.md#bug-11-key-npc-never-extracted-from-narration--scene-extraction-prompt-blind-spot-medium) | [02-npc-compendium-hardening.md](../completed/06-npc/02-npc-compendium-hardening.md)

### Evidence

Compendium accumulates characters that are no longer relevant (unnamed guards killed/passed through) because there's no removal mechanism. Characters introduced with aliases/descriptions ("Scarred Soldier") aren't mapped to their proper name when revealed later, resulting in two entries for the same person.

### Impact

UI fidelity degrades over time — by turn 20+, compendium is cluttered with stale entries. Duplicate identities corrupt NPC tracking, relationship maps, and state diff reports.

### Fix direction

- **Alias consolidation** — **FIXED** (02-npc-compendium-hardening.md)
- **Stale character cleanup:** TTL-based removal for non-key NPCs who aren't named/key (F-N02)
- **NPC death/removal lifecycle:** Mark dead/incapacitated, UI retention for 2-3 turns, backend TTL ~10 turns (F-N03)
- **Key NPC exception:** Named/key NPCs exempt from auto-removal (F-N03)

---

## 3. F-I01/F-I09 — Bond naming + arc objectives from bonds [H/M]

**Severity:** High | **Confidence:** Medium (pattern observed, needs testing) | **Scope:** Narrative setup, bond system

**See also:** [F-I01](./FEATURE-IDEAS.md#f-i01-bond-naming-fix-improvement) | [F-I09](./FEATURE-IDEAS.md#f-i09-bonds-generate-arc-objectives-at-start-net-new) | [F-I02](./FEATURE-IDEAS.md#f-i02-turn-1-seed-integration-net-new)

### Evidence

Close bonds (family, spouse) are referred to generically as "kin" or "family" instead of by proper name/role ("wife", "daughter"). This happens mid-game too — when family appears, narrator still uses generic terms. Bonds don't generate concrete arc objectives at game start.

### Impact

Story opening feels abstract and disconnected. Player has no clear narrative direction from turn 1. "Find my lost brother" is more actionable than "secure family safety."

### Fix direction

- **Bond naming:** Explicit instruction to use named relationships, not abstract kinship labels (F-I01)
- **Bond-generated arcs:** Close bonds should seed concrete arc objectives at game start (F-I09)
- **Expand groups naturally:** When family is mentioned, use specific roles (sister, brother, spouse) not generic "kin"

---

## 4. F-N06 — Interactive inventory in scenes [M/M]

**Severity:** Medium | **Confidence:** Medium (design question) | **Scope:** Scene mechanics

**See also:** [F-N06](./FEATURE-IDEAS.md#f-n06-interactive-inventory-items-in-scenes-net-new) | [F-N04](./FEATURE-IDEAS.md#f-n04-grounded-location-descriptions--nearby-pois-net-new)

### Evidence

Inventory items are passive — mentioned in narration but not interactive within scene mechanics. State extractor doesn't handle item interactions (pick up, use, examine) as first-class actions.

### Impact

Inventory feels disconnected from gameplay. Players can't meaningfully interact with items in scenes. Narrator should mention nearby interactable items when relevant to scene.

### Fix direction

- Make inventory items interactive within scene mechanics
- State extractor handles item interactions as first-class actions
- Narrator mentions nearby interactable items when relevant to scene

---

## 5. F-I02 — Turn 1 seed integration [M/M] — **FIXED**

**Severity:** Medium | **Confidence:** Medium (design question) | **Scope:** Narrative setup

**Status:** FIXED — `01-seed-fixes.md` plan phase 3: updated `generate_seed_system.j2` opening narrative instructions to weave world state facts, NPC relationships, and compendium NPCs naturally into the narration rather than listing them. Seed data is now woven into turn 1 narration.

**See also:** [F-I02](./FEATURE-IDEAS.md#f-i02-turn-1-seed-integration-net-new--priority-6--fixed) | [F-N08](./FEATURE-IDEAS.md#f-n08-seed-json-vs-hints-conflict-net-new--priority-1--fixed) | [F-I01](./FEATURE-IDEAS.md#f-i01-bond-naming-fix-improvement) | [F-I09](./FEATURE-IDEAS.md#f-i09-bonds-generate-arc-objectives-at-start-net-new) | [01-seed-fixes.md](../completed/01-narration/01-seed-fixes.md)

### Evidence

Initial seed JSON sets up world state (locations, factions, relationships) but turn 1 narration doesn't actively USE it — it lists things rather than weaving them into narrative choices and arc setup. Opening should be driven by seed data where relevant to existing threads/arcs.

### Impact

Story opening feels disconnected from the world that was set up. Seed data is wasted if it's not woven into the opening narrative.

### Fix direction

- Seed data should drive turn 1 narration, not just populate state
- Weave seed locations, factions, relationships into narrative choices
- Ensure seed narration has all inputs it needs (prompt completeness)
- Create clear, concrete story opening from seed data

---

## 6. F-N07 — Left-behind tracking [M/M]

**Severity:** Medium | **Confidence:** High (confirmed across games) | **Scope:** NPC mechanics, location

**See also:** [F-N07](./FEATURE-IDEAS.md#f-n07-left-behind-tracking-on-location-change-net-new) | [B7](./BUGS-OBSERVATIONS.md#b7-h-location-changes-silently-dropped-from-canonical-state---confirmed-in-baseline)

### Evidence

When player changes locations, characters who should logically stay behind aren't tracked as such. Example: companion stays at home while PC goes across town — they shouldn't magically appear in the new scene.

### Impact

NPC teleportation breaks immersion. Narrator can't reference "your sister is still back at the safehouse" because there's no state for "left behind" NPCs.

### Fix direction

- Explicit state for "left behind" NPCs with last known location
- Narrator can reference left-behind NPCs appropriately
- Party members exempt from left-behind logic unless explicitly separated by narrative events
- Non-party NPCs in previous scene should have location tracked separately

---

## 7. Bug 15 — Autoplay momentum spiral [M/M]

**Severity:** Medium | **Confidence:** High (verified across two saves) | **Scope:** Autoplay, momentum system

**See also:** [Bug 15](./EVAL-FINDINGS-2026-06-09.md#bug-15-autoplay-momentum-spiral-on-continue-the-story-medium) | [MB-3](./MOMENTUM-BEAT-FINDINGS.md#finding-mb-3-floor-relief-beats-deepen-de-escalation-during-momentum-crisis) | [MOMENTUM-BEAT-FINDINGS.md](./MOMENTUM-BEAT-FINDINGS.md)

### Evidence

Autoplay loop has no guard against consecutive impossible actions. Each turn drains momentum by 1, and once at floor, there's no escape mechanism. On cordyceps-06-09, this cascade ran for 12 consecutive turns (20-31), dropping momentum from 3 to -3 and then stuck at floor for 7+ turns with beat_locked=True, consecutive pressure=8, and no escape mechanism.

### Impact

Autoplay sessions can spiral into momentum death spirals if the LLM generates passive inputs. Once at floor, the system has no mechanism to break out: MB-3 prevents floor relief (correctly) but the storyteller overrides any remaining relief signals with escalation, and beat_locked prevents scene progression.

### Fix direction

- Add detection in `play.py` autoplay mode: if 2+ consecutive impossible-action turns are generated, inject a proactive input suggestion or pause for intervention
- Consider a "momentum floor escape hatch" for beat_locked: after 3+ turns at floor with beat_locked, force a breathing_room regardless of triggered_by_momentum

---

## 8. N4 — Grounded location descriptions + nearby POIs [M/M]

**Severity:** Medium | **Confidence:** Medium (design question) | **Scope:** Scene mechanics

**See also:** [F-N04](./FEATURE-IDEAS.md#f-n04-grounded-location-descriptions--nearby-pois-net-new) | [F-N06](./FEATURE-IDEAS.md#f-n06-interactive-inventory-items-in-scenes-net-new) | [B7](./BUGS-OBSERVATIONS.md#b7-h-location-changes-silently-dropped-from-canonical-state---confirmed-in-baseline)

### Evidence

Location descriptions feel generic and abstract. No nearby locations or points of interest (POIs) provided to give players sense of wider area.

### Impact

World feels flat and ungrounded. Players can't explore beyond immediate scene because they don't know what's nearby.

### Fix direction

- More grounded, spatial location descriptions
- Include nearby locations/POIs in scene context
- Make world feel alive beyond immediate scene

---

## 9. DQ03 — Threads vs fact sheet separation [M/M]

**Severity:** Medium | **Confidence:** Medium (design question) | **Scope:** Thread & arc management

**See also:** [DQ03](./FEATURE-IDEAS.md#dq03-threads-vs-arcs-decoupling--cognitive-load-design-question) | [O4](./BUGS-OBSERVATIONS.md#o4-auto-demote-arc-threads-to-latent-fixed--step-013a--step-021) | [O6](./BUGS-OBSERVATIONS.md#o6-latent-thread-activation-ceiling)

### Evidence

Threads are overloaded as both a fact sheet (tracking world state/events) and an objective list (player goals). This creates high cognitive load for the player: they see threads with sub-objectives, arc visible_goals, and sometimes overlapping content.

### Impact

UI clarity suffers. Players confused about whether threads are objectives or event logs. Cognitive load increases over time.

### Fix direction

- **Arcs/threads should be objectives only** — guidance to storyteller that arcs define what player is trying to accomplish
- **Thread updates should be factual journal entries** — not goals but records of events
- May already be sufficiently differentiated via `visible_goal` vs thread progress, but worth testing

---

## 10. F-I06/F-I07 — UI turn numbers + debug panel [L/L]

**Severity:** Low | **Confidence:** High (confirmed UI gap) | **Scope:** UI improvements

**See also:** [F-I06](./FEATURE-IDEAS.md#f-i06-turn-number-display-improvement) | [F-I07](./FEATURE-IDEAS.md#f-i07-debugdeveloper-panel-toggle-net-new) | [EV-1](./EVAL-EV-BUGS.md#ev-1-prompt--system-returns-data-from-a-different-game) | [EV-10](./EVAL-EV-BUGS.md#ev-10-play-command-format-bug-:d-on-float-momentum_delta)

### Evidence

Turn number `()` missing after thread updates in UI. No debug/developer mode for troubleshooting. Currently debug info only visible via `ev` tooling or Turn Viewer.

### Impact

Minor quality-of-life issue. Players lose context about where they are in game flow. Developers can't easily troubleshoot without external tools.

### Fix direction

- Add turn number `()` after thread updates in UI
- Developer mode toggle: show debug info (turn numbers, state snapshots, extraction outputs)
- Player mode (default): clean, polished view with minimal verbosity

---

## 11. F-N05 — Proactive NPC agency [L/L]

**Severity:** Low | **Confidence:** Low (speculative) | **Scope:** Storytelling pipeline

**See also:** [F-N05](./FEATURE-IDEAS.md#f-n05-proactive-npc-agency-net-new--tentative) | [DQ02](./FEATURE-IDEAS.md#dq02-gm-beats-vs-proactive-npc-actions-undecided) | [F-I05](./FEATURE-IDEAS.md#f-i05-gm-beats-replacement-design-question) | [MB-1](./MOMENTUM-BEAT-FINDINGS.md#finding-mb-1-breathe-directive-dominates-because-no-urgent-scene-threads-exist-at-low-momentum) | [MB-3](./MOMENTUM-BEAT-FINDINGS.md#finding-mb-3-floor-relief-beats-deepen-de-escalation-during-momentum-crisis)

### Evidence

Current turn flow is player-centric: "I do a thing → world/NPCs respond." NPCs are reactive and world feels static around only the protagonist.

### Impact

Unclear — speculative improvement. Would make world feel more alive but adds complexity.

### Fix direction

- Storytell→Ruling→Narrate pass-through: storyteller identifies NPC with reason to act, passes intent to ruling extractor
- Turn starts with "This NPC does X" instead of "Player does Y → world responds"
- Not every turn needs this — just enough that world feels alive beyond player actions
- May replace or supplement GM beat system (DQ02)

---

## 12. F-I11 — Cached universal system prompt [L/L]

**Severity:** Low | **Confidence:** Low (unlikely feasible) | **Scope:** Pipeline efficiency

**See also:** [F-I08](./FEATURE-IDEAS.md#f-i08-extractors-suppress-all-null-fields-improvement--needs-verification) | [TECH-DEBT.md](./other/TECH-DEBT.md) (dead code, duplicated functions)

### Evidence

Investigate whether any stage-agnostic base system prompt could be cached. Unlikely to be feasible given how much system prompt content varies by pipeline stage.

### Impact

Minor token savings if feasible, unlikely to be worth the complexity.

### Fix direction

- Nice-to-have, low priority
- Worth a look if it saves tokens without degrading quality

---

## 13. F-I12 — PC point total: 11 not 10 [L/L]

**Severity:** Low | **Confidence:** High (balance issue) | **Scope:** Character creation

**See also:** [MB-7](./MOMENTUM-BEAT-FINDINGS.md#finding-mb-7-difficulty-assignment-produces-42-hard-checks-against-a-2-max-character) (difficulty balance context)

### Evidence

Character creation gives PC 10 points but should be 11 for better balance. Simple balance tweak.

### Impact

Minor balance improvement. Verify against current rules before implementing.

### Fix direction

- Change PC point total from 10 to 11
- Verify against current rules/character creation flow

---

## Previously Fixed (for reference)

| # | Finding | Status | Fix | See also |
|---|---|---|---|---|
| MB-1 through MB-6 | Momentum death spiral | **FIXED** | momentum-thread-goal-fixes plan (steps 01.1-01.4). Verified: `momentum.py:27-33` (depth catch-up), `turn.py:594-596` (Breathe guard), `turn.py:1091-1106` (momentum guard on floor relief), `turn.py:1108-1116` (counter reads post-floor-relief beat) | [MOMENTUM-BEAT-FINDINGS.md](./MOMENTUM-BEAT-FINDINGS.md) |
| MB-7 | Difficulty assignment (42% hard) | **CONFIRMED** | Outside scope of momentum plan | [MOMENTUM-BEAT-FINDINGS#MB-7](./MOMENTUM-BEAT-FINDINGS.md#finding-mb-7-difficulty-assignment-produces-42-hard-checks-against-a-2-max-character) |
| F-N03 | NPC death/removal lifecycle | **FIXED** | departed presence + TTL archive (turn.py:1334, npc_roster.py, config.py). Commit `f9f09576` | [FEATURE-IDEAS.md#f-n03](./FEATURE-IDEAS.md#f-n03-npc-deathremoval-lifecycle-net-new) |
| G3 | Goal stagnation | **FIXED** | Step 02.2 explicit trigger events | [PRIORITIES (old)](./PRIORITIES.md#3-g3j--goal-stagnation--sanitizer-too-slow-to-pivot-mh) |
| B7 | Location changes dropped | **PARTIALLY FIXED** | Engine path at `delta_builder.py:216-241` correctly applies location changes; prompt tightened. No engine bug. | [BUGS-OBSERVATIONS#B7](./BUGS-OBSERVATIONS.md#b7-h-location-changes-silently-dropped-from-canonical-state---confirmed-in-baseline) |
| O4 | Thread accumulation | **FIXED** | Steps 01.3a (auto-latent, commit `e484ee44`) + 02.1 (temporal decay, commit `3912f779`) | [BUGS-OBSERVATIONS#O4](./BUGS-OBSERVATIONS.md#o4-auto-demote-arc-threads-to-latent-fixed--step-013a--step-021) |
| B11 | Condition schema drift | **SUPERSEDED** | Ruling agent replaces CONDITION_MODS entirely (commit `bbbf7d41`) | [BUGS-OBSERVATIONS#B11](./BUGS-OBSERVATIONS.md#b11-condition-schema-drift-systemic-across-all-runs---confirmed) |
| B8 | Momentum sign inversion | **ELIMINATED** | False positive from auto-checker artifact (index-based matching). Actual momentum code is correct. | [MOMENTUM-BEAT-FINDINGS.md](./MOMENTUM-BEAT-FINDINGS.md) |
| B1 | Ammo decrement wrong operation | **FIXED** | `InventoryRemove` model at `models.py:228-233`; validation at `turn.py:1563-615`; prompt uses `inventory_remove` with `amount` | [BUGS-OBSERVATIONS#B1](./BUGS-OBSERVATIONS.md#b1) |
| B5 | Scene tag volatility | **FIXED** | `grounded-state-extraction` plan (commits `f93b6740` + `02c6a91a`) removed `scene_tags` entirely from pipeline | [BUGS-OBSERVATIONS#B5](./BUGS-OBSERVATIONS.md#b5-m-scene-tags-reset-between-consecutive-turns-confidence-h) |
| B12 | actions_quality on system events | **OBSOLESCED** | New ev.py checkers handle this differently | [EVAL-FINDINGS-2026-06-09.md](./EVAL-FINDINGS-2026-06-09.md) |
| B13 | consecutive_pressure_tracking mismatch | **OBSOLESCED** | New `pacing_directives` checker uses `post_extraction_consecutive_pressure_turns` (written at `turn.py:1426`) | [EVAL-FINDINGS-2026-06-09.md](./EVAL-FINDINGS-2026-06-09.md) |
| Bug 1 (EVAL-FINDINGS) | impossible not stored | **FIXED** | Commit `430016d9` adds `impossible` and `reason` to ruling_event | [EVAL-FINDINGS-2026-06-09.md](./EVAL-FINDINGS-2026-06-09.md) |
| Bug 10 (EVAL-FINDINGS) | duplicate NPC entries | **FIXED** | Dedup logic at `extraction.py:618-625` | [EVAL-FINDINGS-2026-06-09.md](./EVAL-FINDINGS-2026-06-09.md) |
| F-N08/F-N09 | Seed JSON vs hints conflict | **FIXED** | `01-seed-fixes.md` plan: skip LLM seed on hints, use static pack fallback. Inventory removed from seed instructions. Opening narrative sharpened. | [FEATURE-IDEAS.md](./FEATURE-IDEAS.md) |
| F-N01 | Alias consolidation | **FIXED** | `02-npc-compendium-hardening.md` plan: alias-first naming in extraction prompt (descriptive labels → aliases, proper names → name, keep historical aliases on promotion). | [FEATURE-IDEAS.md](./FEATURE-IDEAS.md) |
| F-I02 | Turn 1 seed integration | **FIXED** | `01-seed-fixes.md` plan phase 3: updated `generate_seed_system.j2` opening narrative instructions to weave world state, NPC relationships, and compendium NPCs naturally. | [FEATURE-IDEAS.md](./FEATURE-IDEAS.md) |
| Bug 11 (EVAL-FINDINGS) | Key NPC never extracted (Elias) | **FIXED** | `02-npc-compendium-hardening.md` plan: passive NPC extraction instruction + alias-first naming prevents passive/recipient NPCs from being missed. | [EVAL-FINDINGS-2026-06-09.md](./EVAL-FINDINGS-2026-06-09.md) |

---

## What was excluded

- **B6** (non-deterministic beats): LLM quality problem — storytell sometimes emits `null` instead of explicit `breathing_room`. No engine-level guarantee. [B6](./BUGS-OBSERVATIONS.md#b6-m-beat-generation-is-non-deterministic--not-every-turn-emits-a-gm_beat-confidence-h)
- **B10** (inventory extraction hallucination): Validation at `turn.py:1563-615` blocks damage (missing targets, zero balances). LLM still emits garbage into events.jsonl — quality issue. [B10](./BUGS-OBSERVATIONS.md#b10-m-inventory-extraction-hallucination-persists-across-all-runs---confirmed)
- **B4** (pressure counter desync): Engine is FIXED (reads post-floor-relief beat at `turn.py:1108-1116`). But `pacing_directives` checker has fallback to stale `state_snapshot` when `post_extraction_consecutive_pressure_turns` is missing. Eval-only issue. [B4](./BUGS-OBSERVATIONS.md#b4-m-mb-5-pressure-counter-desyncs-when-storytell-emits-no-beat-confidence-h)
- **B9** (floor relief injection failure at T12): Engine is FIXED (momentum guard at `turn.py:1091-1106`). But `gm_beat_lifecycle` checker at `gm_beat.py:75-86` still expects `breathing_room` on ALL `beat_locked` turns without the `triggered_by_momentum` guard. Eval-only issue. [B9](./BUGS-OBSERVATIONS.md#b9-h-floor-relief-injection-failure)
- **B3** (thread lifecycle loses tracking): `removed_threads` path removed (cb623f4). But `sanitizer_lifecycle` checker still requires `threads_removed` field that doesn't exist in events. Partial. [B3](./BUGS-OBSERVATIONS.md#b3-m-thread-lifecycle-loses-tracking-on-exit)
- **EV tooling bugs** (EV-1 through EV-10): Tooling issues, not game fidelity issues. Should be fixed but lower priority than game mechanics. [EVAL-EV-BUGS.md](./EVAL-EV-BUGS.md)
- **Eval checker bugs** (Bug 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 15): Eval/checker tooling bugs — break testing infrastructure but don't affect actual game play. Bug 1 (impossible not stored) and Bug 10 (duplicate NPCs) already fixed. Bug 13 (threads divergence) is by design. Bug 14 (narrative_velocity) is documented and used in server/UI. [EVAL-FINDINGS-2026-06-09.md](./EVAL-FINDINGS-2026-06-09.md)
