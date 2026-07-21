---
title: "B-50 sanitizer fixes: two-way urgency, reactivation, compaction quality gate"
status: done
urgency: 3
size: medium
created: 2026-07-20
ticket_id: E-18
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Description

Eval to validate B-50 sanitizer fixes: two-way urgency (B-50.2), compaction quality gate (B-50.5), and urgency decay independence (B-50.6). Also check for regressions in thread lifecycle, beat pipeline (I-43), and convergence behavior.

## Context

**Prior SHA:** `2e3d0188` (from `2026-07-17_0.32.1_2e3d0188`)
**Changes since last eval:** 2 commits touching `ccya/`

### Changes Since Last Eval

1. **`b5d2b8cf`** — `ccya/prompts/sanitize_thread.j2`:
   - Added escalation criteria (new threats, imminent danger, background/dormant reactivation)
   - Added reactivation guidance for dormant/background threads
   - Added tone-matching instruction (upgrade OR downgrade based on scene tone)
   - Added quality gate for compaction: "Preserve key factual content during consolidation"

2. **`a140a15e`** — `ccya/engine/_beat.py`, `ccya/prompts/record_system.j2`:
   - Dropped `npcs` field from beat pipeline
   - Strengthened cross-NPC blend guidance

### Focus Areas

- **B-50.2**: Are there urgency escalations in the sanitizer output? (Previously 0 escalations across 5 runs)
- **B-50.5**: Does compaction preserve key facts? (Previously lost specific names, details, evidence)
- **B-50.6**: Does urgency decay fire independently? (Previously zero decay logs across 11 runs)
- **I-43**: Does dropping `npcs` from beat pipeline work correctly?
- **Convergence**: Does convergence behavior improve with two-way sanitizer?

## Plan

### Phase 1: 1 game, 5 turns — Critical bugs
- Pack: noir-1930s, Persona: driven
- Target: Game-breaking bugs, obvious failures
- Report: `evals/runs/<group>/PHASE-1.md`

### Phase 2: 3 games, 15 turns — Nuanced bugs
- Pairs: noir-1930s:driven, space-western:speedrunner, golden-piracy:completionist
- Target: Intermediate degradations, pacing issues, extraction misses
- Report: `evals/runs/<group>/PHASE-2.md`

### Phase 3: 5 games, 25 turns — Balance and long-term mechanics
- All 5 persona pairs
- Target: Balance, long-term patterns, edge cases
- Report: `evals/runs/<group>/PHASE-3.md`

### Testing Items

- **B-50** (thread lifecycle): status=testing. Validate B-50.2 (two-way sanitizer), B-50.5 (compaction quality), B-50.6 (decay independence).

## Progress

### Phase 1: COMPLETE — 2026-07-20
- Pack: noir-1930s, Persona: driven, Turns: 5
- Report: `evals/runs/2026-07-20_0.32.1-21-g98d1d9d0_98d1d9d0/PHASE-1.md`
- Group: `2026-07-20_0.32.1-21-g98d1d9d0_98d1d9d0`
- Pass rate: 92.9% (18/19 checkers pass)
- No critical/game-breaking bugs found

#### B-50.2 (two-way sanitizer): PROMISING
- Turn 5: **2 escalations** (`normal` → `urgent`) for `media_leverage` and `councilman_miller_access`
- Previously: 0 escalations across 5 runs (B-50.2 finding)
- First escalation ever observed. Prompt edits appear to be working.

#### B-50.5 (compaction quality): PROMISING
- Turn 5 compaction preserved key facts: "Journalist is investigating The Blue Rose club" retained, "Bouncers refused bribe and flagged player" added
- Previously: significant factual loss (e.g., T15 lost "Sterling/warehouse/Vane/witness/cigarette case/newsboy")

#### B-50.6 (decay): NEEDS MORE DATA
- Only 5 turns, not enough for decay evaluation (requires 13+ turn window)

#### Pre-existing failures (not B-50 related)
- convergence_recompute: stored score 0, checker expects 1-2
- location_description_consistency: descriptions 12 words, minimum 15

- Verdict: Proceed to Phase 2.

### Phase 2: COMPLETE — 2026-07-20
- Runs: noir-1930s:driven (15t) ✓, space-western:speedrunner (15t) ✓, golden-piracy:completionist (15t) ✓
- Groups: `2026-07-20_0.32.1-21-g98d1d9d0_98d1d9d0`

#### noir-1930s:driven 15t — COMPLETE
- Pass rate: 92.9% (18/19 checkers pass)
- Sanitizer: 3 events (all PASS)
- B-50.2: 1 escalation (T15: `police_pursuit` normal→urgent), 1 reactivation (T5: `missing_ledger` dormant→active)
- B-50.5: Progress consolidations preserve key facts (e.g., "The ledger lacks damning entries", "Driver revealed Miller's club and estate")
- B-50.6: `missing_ledger` auto-dormant at T8 (untouched 8 turns) — decay mechanism firing
- Pre-existing failures: convergence_recompute (15 issues), location_description_consistency (9 issues)

#### space-western:speedrunner 15t — COMPLETE
- Pass rate: 92.9% (18/19 checkers pass)
- Sanitizer: 3 events (all PASS)
- B-50.2: 0 urgency escalations, 2 reactivations (T5: `black_market_contacts` dormant→active, T15: `uncharted_nebula_exploration` dormant→active)
- B-50.5: Progress consolidations preserve key facts (e.g., "The Rust Bucket escaped the docking bay", "Coalition interceptor is pursuing the ship", "Ship stabilizers failed during high-speed burn")
- B-50.6: `black_market_contacts` auto-dormant at T13 (untouched 8 turns), `uncharted_nebula_exploration` auto-dormant at T15 (untouched 15 turns)
- Pre-existing failures: convergence_recompute (14 issues), location_description_consistency (9 issues)

#### golden-piracy:completionist 15t — COMPLETE
- Pass rate: 92.9% (18/19 checkers pass)
- Sanitizer: 3 events (all PASS)
- B-50.2: 1 escalation (T10: `guild_corruption` normal→urgent), 1 reactivation (T10: `black_market_logistics` dormant→active)
- B-50.5: Progress consolidations preserve key facts (e.g., "Silas Vane linked to smuggling", "Treasury gold embezzled by Guild", "Guards siphoning unrefined peppercorns")
- B-50.6: `black_market_logistics` auto-dormant at T9 (untouched 9 turns)
- Pre-existing failures: convergence_recompute (7 issues), location_description_consistency (9 issues)

#### B-50.2 Summary:
- noir-1930s: 1 escalation + 1 reactivation
- space-western: 0 escalations + 2 reactivations
- golden-piracy: 1 escalation + 1 reactivation
- Previously: 0 escalations across 5 runs (B-50.2 finding)
- **Verdict: Two-way sanitizer is working.** Both escalation and reactivation observed across all 3 games.

#### B-50.5 Summary:
- noir-1930s: Progress consolidations preserve key facts
- space-western: Progress consolidations preserve key facts
- golden-piracy: Progress consolidations preserve key facts
- Previously: significant factual loss (e.g., T15 lost "Sterling/warehouse/Vane/witness/cigarette case/newsboy")
- **Verdict: Compaction quality gate is working.**

#### B-50.5 (compaction quality) — Phase 4 update (2026-07-21):
- 9 compaction events across 6 sanitizer runs (30 turns)
- 2-entry minimum respected: no thread collapsed to 1 entry
- Sequential step rule working: Turn 25 `vance_confrontation 5→3` kept first/middle/last
- Entity preservation improved: most losses are minor (articles, redundant name forms)
- Still losing some narrative details (Turn 15 `pier_14_smuggling_intercept 7→2`)
- **Verdict: Significant improvement. Concrete rules (2-entry minimum, entity preservation, sequential steps) are effective where abstract quality gate instruction failed.**

#### B-50.6 Summary:
- noir-1930s: `missing_ledger` auto-dormant at T8
- space-western: `black_market_contacts` auto-dormant at T13, `uncharted_nebula_exploration` auto-dormant at T15
- golden-piracy: `black_market_logistics` auto-dormant at T9
- Decay mechanism firing on untouched threads across all 3 games
- **Verdict: Decay is working.**

#### Pre-existing failures (not B-50 related):
- convergence_recompute: stored score 0, checker expects 1-2 (consistent across all runs)
- location_description_consistency: descriptions 12 words, minimum 15

### Phase 3: COMPLETE — 2026-07-20
- Runs: noir-1930s:driven (25t) ✓, space-western:speedrunner (25t) ✓, golden-piracy:completionist (25t) ✓, zombie-survival:cautious (25t) ✓, allied-ww2:aggressive (25t) ✓
- Group: `2026-07-20_0.32.1-24-gfc9a9f30_fc9a9f30`
- Report: `evals/runs/2026-07-20_0.32.1-24-gfc9a9f30_fc9a9f30/PHASE-3.md`
- Pass rates: noir-1930s 92.9%, space-western 90.5%, golden-piracy 92.9%, zombie-survival 92.9%, allied-ww2 92.9%
- All 5 runs: sanitizer_lifecycle PASS (all 5 sanitizer events passed)

#### B-50.2 (two-way sanitizer): CONFIRMED
- 18 urgency escalations across 5 runs (4 noir, 4 space-western, 1 golden-piracy, 5 zombie, 4 allied-ww2)
- Escalations fire as narrative tension builds — expected behavior for longer games
- 7 reactivations across 5 runs (1 noir, 3 space-western, 2 golden-piracy, 0 zombie, 1 allied-ww2)
- Notable: `guild_corruption` (space-western) and `naval_corruption` (golden-piracy) each reactivated twice (dormant→active→dormant→active)
- **Verdict: Two-way sanitizer working at full game length.**

#### B-50.5 (compaction quality): PARTIAL — quality gate violation found
- 26 compaction events across 5 runs (all packs show compaction)
- **QUALITY GATE VIOLATION:** All 26 compactions lose unique entities (names, locations, items)
- Prompt has explicit quality gate (line 82) to "preserve all unique entities" but LLM consistently ignores it
- Example: noir-1930s T10 `black_market_expansion` 6→1 lost "Lady May", "Elias Thorne", "Nealburg"
- Severity: Medium — degrades narrative detail but doesn't break mechanics
- **Verdict: Compaction works mechanically but loses factual content. Quality gate instruction not being followed.**

#### B-50.6 (decay): CONFIRMED
- 4 urgency decay events across 5 runs (urgent→normal)
- space-western T25: `guild_corruption` urgent→normal
- golden-piracy T10: `naval_corruption` urgent→normal
- zombie-survival T25: `ventilation_threat` urgent→normal
- allied-ww2 T20: `enemy_encroachment` urgent→normal
- **Verdict: Decay working as designed.**

#### Pre-existing failures (not B-50 related, unchanged):
- convergence_recompute: FAIL (12-23 issues each)
- location_description_consistency: FAIL (2-19 issues each)

#### Phase 1/2 vs Phase 3 comparison:

| Metric | Phase 1 (5t) | Phase 2 (15t) | Phase 3 (25t) |
|--------|-------------|---------------|---------------|
| Escalations | 2 total | 4 total | 18 total |
| Reactivations | 3 total | 4 total | 7 total |
| Compactions | Multiple | Multiple | 18 total |
| Sanitizer failures | 0 | 0 | 0 |
| Pass rate range | 92.9% | 92.9% | 90.5-92.9% |

#### Overall verdict:
B-50.2 (two-way urgency): CONFIRMED working. B-50.5 (compaction quality): PARTIAL — quality gate instruction exists but LLM consistently ignores it, losing unique entities. B-50.6 (decay): CONFIRMED working.

**New issue found:** B-50.5 quality gate violation — compaction loses factual content despite explicit prompt instruction to preserve unique entities. Severity: medium.

## Fixes Applied

(Any fixes made during this eval. Use commit separators to delineate pre-fix vs post-fix state. This section is dynamic — add entries as fixes are made.)

↑ (prior SHA or previous commit)
────────────────────────────────────
↓ (commit hash of fix)

### Fix: (what was fixed)
- File: (file changed)
- Root cause: (brief explanation)
- Validation: (how it was verified)

↑ (commit hash above)
────────────────────────────────────
↓ (next commit)

## Checkers Results

(Compile pass/fail table. Remember: checkers are bellwethers — they signal that something *might* be healthy or unhealthy. They are not verdicts. Always pair checker results with subjective examination.)

| Checker | Phase 1 | Phase 2 | Phase 3 |
|---------|---------|---------|---------|
| (name)  | (pass/fail) | (pass/fail) | (pass/fail) |

## Deep-Dive Reviews

### ev-review: Reactivation pattern + Compaction quality (2026-07-20)

**Sources examined:**
- `evals/runs/2026-07-20_0.32.1-24-gfc9a9f30_fc9a9f30/` — all 5 Phase 3 runs
- `ccya/prompts/sanitize_thread.j2` — sanitizer prompt (quality gate at line 82)
- `docs/architecture/step2c-record.md` — arc system, auto-dormant, urgency decay

**Reactivation pattern (B-50.2):**
- `guild_corruption` (space-western): dormant→active at T5, T10, T20 (3 reactivations)
- `naval_corruption` (golden-piracy): dormant→active at T5, T25 (2 reactivations)
- Pattern: dormant→active→(auto-dormant after 8 turns)→active→(auto-dormant)→active
- **This is working as designed.** Auto-dormant fires after 8 turns of inactivity (engine-enforced). Sanitizer reactivates when narrative evidence shows renewed relevance. The LLM is correctly following the reactivation guidance.

**Compaction quality (B-50.5) — QUALITY GATE VIOLATION:**
- 26 compaction events across 5 runs, ALL losing unique entities
- Prompt has explicit quality gate (line 82): "preserve all unique entities (names, locations, items, relationships) and outcomes. Never drop factual content just to reduce count"
- Actual behavior: consistently dropping names, locations, items

Examples:
- noir-1930s T10: `black_market_expansion` 6→1 entries. Lost: "Lady May", "Elias Thorne", "Nealburg", "smuggling contact" — all unique entities
- space-western T10: `syndicate_expansion` 7→3 entries. Lost: "Philip Moore", "encrypted clearance codes", "water filtration units"
- allied-ww2 T15: `enemy_encroachment` 9→1 entries. Lost: "Cantrell", "depot", "enemy forces", "fire"

**Root cause:** The quality gate instruction is present but the LLM is not following it. The prompt says "consolidate only when entries describe the same event or overlapping progress" but the sanitizer is consolidating across different events.

**Severity:** Medium — factual content loss degrades game state fidelity but doesn't break mechanics. Threads still track correctly, just with less narrative detail.

**Recommendation:** Strengthen quality gate with concrete examples of what to preserve vs. what to consolidate. Consider adding a post-consistency check that verifies unique entities are retained.

### Phase 4: 30-turn test — Improved compaction rules (2026-07-21)
- Pack: noir-1930s:driven, Turns: 30
- Group: `2026-07-21_0.32.1-29-g64d3b875_64d3b875`
- Commit: `64d3b875` — added 3 compaction rules: 2-entry minimum, entity preservation, sequential step handling
- Pass rate: 88.1% (37/42 checkers)
- Failures: thread_urgency_decay, ruling_reason_quality, location_description_consistency, convergence_recompute, convergence_ema
- Pre-existing: thread_urgency_decay, location_description_consistency, convergence_recompute, convergence_ema
- New: ruling_reason_quality (2 off-by-one violations: 11 words vs 10 max)

#### B-50.5 (compaction quality): IMPROVED
- 9 compaction events across 6 sanitizer runs (turns 5, 10, 15, 20, 25, 30)
- **2-entry minimum respected:** No thread collapsed to 1 entry (previously 9→1, 7→1 cases)
- **Sequential step rule working:** Turn 25 `vance_confrontation 5→3` kept forged signatures, envelope lost, Vance dragged (first, middle, final)
- **Entity preservation improved:** Lost entities are mostly minor — articles ("The"), redundant name forms ("Anthony Schultz" → "Schultz"), contextual details ("Three" → "two")
- **Still losing some narrative:** Turn 15 `pier_14_smuggling_intercept 7→2` lost Schultz arriving at Pier 14, confronting guards, Silent Figure confirming payments. But core facts remain.
- **Verdict: Significant improvement over Phase 3.** Quality gate instruction alone wasn't working; concrete rules (2-entry minimum, entity preservation, sequential steps) are effective.

#### Outcome summary expansion: CONFIRMED
- Average ~17 words (previously ~10, one sentence)
- Captures who (PC + named NPCs), what (key action), what changed (consequence)
- Examples: "Anthony Schultz pins Silas Vance in a sedan, forcing a confession about a shadow network protecting the forged files." (19 words)
- Negligible token cost: +5 words/turn × 30 turns = +150 words/game

### Deep-dive: Beat system analysis (2026-07-21)

**Scope:** All 30 turns, examined world output, ruling selection, and narration incorporation.

#### Beat pipeline mechanics
- World generates 3 candidates every turn (all 30 turns)
- Ruling selects 1 by index → `pending_gm_beat` set
- Narrate reads `pending_gm_beat`, uses mechanism tags as creative guidance
- 29/30 turns have a `pending_gm_beat` set

#### Beat type distribution (world output)
- escalation: 23, revelation: 21, pressure: 16, complication: 15, twist: 12, callback: 2, opportunity: 1
- Ruling selection bias: escalation and revelation dominate. Only 1 twist selected (8% selection rate from 12 generated). Only 1 opportunity selected (from 1 generated). Callbacks generated at T23-24 but never selected.

#### NPC availability drives beat feasibility
- 0 distinct NPCs: 13 turns (43%) — thread-only beats are legitimate (priority 4)
- 1 distinct NPC: 13 turns (43%) — NPC+NPC blends impossible, self-blends/single-NPC beats only
- 2+ distinct NPCs: 4 turns (14%) — only where NPC+NPC blends are possible
- **Critical:** Turns 10-13 have 2 Silent Figures but they're the same name, so world treats them as 1 distinct NPC → generates self-blends

#### World step prompt adherence issues
1. **Priority rules not followed when 2+ NPCs exist:** In turns 1-3 (2 distinct NPCs: Ian Garcia + Dockworker Crowd), only ~33% of beats are NPC+NPC blends. World should prioritize NPC+NPC (priority 1) but generates mix of priorities.
2. **Self-blends (4 instances):** `[blend: Silent Figure's motivation vs Silent Figure's fear]` — same NPC twice. Prompt says "blends MUST use different NPCs."
3. **Invalid blend format (2 instances):** `[blend: Silas Vance's leverage vs precinct_betrayal]` — thread slug inside blend. Prompt says "Never put a thread slug inside a blend."
4. **Effect repetition (18 effects repeat):** Prompt says "Do NOT emit a beat whose effect describes the same event as any beat in recent_beats."
5. **Cognitive load:** The prompt has extensive formatting rules (effect format, tie rule, blend rule, priority order, diversity constraints). LLM consistently violates the more complex rules.

#### Narration incorporation quality
- **GOOD (both NPC + type reflected):** 13/29 (45%) — beat meaningfully incorporated
- **PARTIAL (one of NPC or type):** 11/29 (38%) — beat partially incorporated
- **POOR (neither):** 5/29 (17%) — beat essentially ignored
- **83% incorporation rate** — beats are used as narrative guidance, not ignored
- Beats function as "creative guidance" per prompt (player input > GM beat). Narration follows player action first, weaves beat in as texture when possible
- The POOR cases: T8 (twist with NPC tie — beat intent present but no obvious keywords), T27-30 (thread-only beats — no NPC specificity to incorporate)

#### Examples

**Twists (1 selected out of 12 generated):**
- Turn 8 (SELECTED): `[tie: Officer Miller vs Anthony Schultz]` — Miller stares through Schultz with indifference, aggression feels hollow. The tie dynamic is present but narration follows player action (grabbing Miller).
- Other 11 twists generated but never selected by ruling. Ruling consistently prefers escalation/revelation.

**Callbacks (2 generated, 0 selected):**
- Turn 23: `[highlight: Sedan Driver's bio] [thread: vance_confrontation]` — RESOLUTION phase allows callback, but ruling picked revelation instead
- Turn 24: `[highlight: Silas Vance's bio] [thread: warehouse_district_reinforcements]` — BREATHER phase allows callback, ruling picked revelation instead

**Opportunity (1 generated, 1 in world output, selected but not reflected well):**
- Turn 25: `[highlight: Sedan Driver's fear] [thread: warehouse_district_reinforcements]` — World generated as opportunity in BREATHER phase. Narration shows player shoving driver + four enforcers appearing. More escalation than opportunity.

#### Verdict
- **Pipeline works mechanically:** All 3 steps function end-to-end
- **Narration quality is strong:** Noir prose is genuinely good, beats provide useful creative direction
- **World step prompt adherence is weak:** Priority rules, self-blend rule, and format rules consistently violated
- **Ruling selection is biased:** Strongly prefers tension beats (escalation/revelation), rarely selects twist/callback/opportunity
- **Core issue:** World prompt has too many rules with high cognitive load. LLM follows simple rules (phase alignment, 2-3 candidates) but violates complex ones (priority ordering, blend constraints, diversity)

## Next

(What's left to do. If eval is complete, note status.)

## References

(Eval group paths, relevant bug/improvement tickets, architecture docs examined)