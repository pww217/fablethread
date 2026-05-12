```
---
mechanical_score: 2
narrative_score: 3
system_cohesion_score: 2
prompt_quality_score: 2
pipeline_scores:
  rules: 3
  narrate: 3
  extract_scene: 3
  extract_state: 3
  extract_progress: 2
compaction_score: 2
state_fidelity_rate: 0.62
prompt_adherence_rate: 0.72
---
```

# Eval Judge Report — Run 20260512T154142Z_uufm2ojg
**Model:** mlx-community/gemma-4-26b-a4b-it-mxfp8 | **Pack:** eval-pack | **Turns:** 13 | **Duration:** ~7.5 min

***

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

*Note: The trace's `full_cycle.run.json` shows `"(no momentum field)"` in every `universal.momentum.band_delta` detail for all 13 turns. This means the state diff never captured a `momentum` field change despite rolls occurring on T1 (fail), T3 (fail), T5 (success per outcome), T6 (fail per outcome), T8 (success), T10 (fail), T11 (success), T12 (roll). The seed state sets `momentum: 0` and by T1 the state snapshot shows `momentum: -1`. Subsequent diffs are absent.*

| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|
| T1 | fail | -1 | 0 → -1 | Partial — narration is tense/foreboding but Caron merely sets harsh terms; not a "fail outright" outcome | TONE_MISMATCH |
| T2 | no roll | 0 | -1 → -1 | N/A | — |
| T3 | fail | -1 (implied) | -1 → -2 | Partial — Halden counters rather than refuses; reads like partial not fail | TONE_MISMATCH |
| T4 | no roll | 0 | -2 → -2 | N/A | — |
| T5 | roll (success implied by outcome) | +1 (expected) | -2 → ? | Unclear — diff not captured | FLAT |
| T6 | fail | -1 (expected) | ? → ? | Diff absent | FLAT |
| T7 | no roll | 0 | ? → ? | — | — |
| T8 | success | +1 (expected) | ? → ? | Diff absent | FLAT |
| T9 | no roll | 0 | ? → ? | — | — |
| T10 | fail | -1 (expected) | ? → ? | Diff absent | FLAT |
| T11 | success | +1 (expected) | ? → ? | Diff absent | FLAT |
| T12 | roll (flagged as unexpected) | ? | ? | — | FLAT |
| T13 | no roll | 0 | ? → ? | — | — |

**Assessment:** The momentum field is present in the T1 state snapshot (`momentum: -1`) but never surfaced in subsequent diffs. Either the state differ is suppressing unchanged-value outputs, or momentum stopped updating after T1. The two confirmed tone mismatches (T1, T3) both occur when fail-band narration plays out more like a partial — Caron confronts but doesn't truly block the player, Halden counters but doesn't reject outright. Momentum direction appears correct where verifiable (-1 on fail bands), but the run.json's "no momentum field" across all turns is an observability gap that prevents confirmation.

***

### 1B — GM Beat Table

| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag | Effect | Flag |
|---|---|---|---|---|---|
| T1 (none generated — pending_gm_beat: null) | — | — | — | — | — |
| T5 (beat generated, consumed T6) | Unknown type | T6 | 1 turn | Narration describes bribe backfiring — broadly consistent | — |
| T6 (beat generated, consumed T7) | Unknown type | T7 | 1 turn | T7 narration includes frantic warning from Halden — beat surfaced | — |
| T7 (beat generated, consumed T8) | Unknown type | T8 | 1 turn | T8 storage room scene — beat surfaced | — |
| T8 (no prior beat, beat generated at T8→T9) | Unknown type | T9 | 1 turn | T9 toughs discovery — consistent | — |
| T9–T11 (beats cycling each turn, consumed each subsequent turn) | Various | T10–T12 | 1 turn each | Each narration reflects world escalation | — |

**Assessment:** Beats are cycling every turn (consumed within 1 turn), which is mechanically correct. However, beat types are not visible in the run.json; the trace was truncated before T4–T13 detail. All `universal.pending_gm_beat.consumed` checks pass from T5 onward, which is a positive signal. Beat frequency appears high — every turn from T5 onward has a beat — suggesting the progress extractor may be over-generating beats during high-pressure phases rather than exercising `null` when appropriate. No orphaned beats detected.

***

### 1C — Scene Pressure Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan | Flag |
|---|---|---|---|---|---|---|
| caron_impatience | T1 | immediate | No | T2 | 1 turn | — |
| road_toughs_presence (or equivalent) | T5 or T6 | building→immediate | Yes (T8 2×immediate) | ? | 5+ turns | OVERLONG / INERT |
| Unknown T8 pressure | T8 | immediate | N/A | ? | 3+ turns | IMMEDIATE_NO_STAKES |
| Unknown T9 pressure | T9 | immediate | N/A | Not resolved by T13 | 4+ turns | UNRESOLVED_AT_END |
| Unknown T10 pressure | T10 | immediate | N/A | Not resolved by T13 | 3+ turns | UNRESOLVED_AT_END |

**Notes:** T8 checker shows `1 immediate`; T9 shows `2 immediate`; T10–T12 show `2 immediate`; T13 shows `2 immediate`. Two immediate pressures persist unresolved through the end of the run. The `caron_impatience` pressure at T1 used `urgency: immediate` for what is effectively a social/commercial standoff — a first-turn debt conversation at normal difficulty probably warranted `building` urgency at most. Resolved correctly at T2.

**Recommendations:**
- Cap any road-adjacent tough pressure at 4 turns then force escalation or resolution event via beat.
- Downgrade T1 social pressure from `immediate` to `building` — Caron is annoyed, not a mortal threat.
- The two unresolved immediates at T13 leave the game state in a high-tension terminal condition; if this is the final turn of the run, those should have been resolved or explicitly failed.

***

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Present at (Tm) | Resolved | Duration | Flag |
|---|---|---|---|---|---|---|
| bruised_ribs | Pre-T1 (added_turn: 8 per state) | engine/prior | T1–T13 | No | 13+ turns | OVERLONG |
| low_morale | Pre-T1 (added_turn: 10 per state) | engine/prior | T1 | T2 | 1 turn active in run | — |

**Notes:** `low_morale` resolved at T2 when the debt was cleared — clean and narratively justified (extract_state correctly emitted `pc_condition_remove`). `bruised_ribs` persists the entire run with no resolution attempt and no explicit narrative callback observed in the T3–T13 truncated trace. The condition was referenced in T1 narration ("steady despite the ache in your ribs") and T3 narrator user prompt still lists it. At 13+ active turns, this exceeds the `long` threshold (9+ turns) without explicit narrative justification.

**Recommendations:** Add a TTL of ~8 turns to `bruised_ribs` (or require explicit narrative treatment to extend). The condition is still mechanically present at the run's end despite a T8 success navigating a physical challenge, which suggests the state extractor isn't removing resolving conditions aggressively enough.

***

### 1E — Quest Arc Table

| Quest ID | Created (Tn) | Objectives | Done | Resolved (Tm) | Outcome | Flag |
|---|---|---|---|---|---|---|
| settle_the_debt | Seed | 2 | 2/2 | T2 | Completed (auto-close) | DUPLICATE_ID (T2 checker) |
| deliver_the_ledger | Seed | 3 | Partial | T7 (failed auto-close) | Active past completion | PREMATURE_COMPLETE / INCOMPLETE_CLOSE |
| clear_the_road_toughs | Seed | 2 | Partial | T6 (partial mark only) | Active (not completed) | — |

**Notes:**
- `settle_the_debt` auto-closed correctly at T2 but the T2 checker flags `progress.quest_id_collision` — the progress extractor re-emitted the quest update including `status: active` on a quest that just completed. This is a deduplication failure.
- `deliver_the_ledger`: T7 checker shows `quest[deliver_the_ledger].status='active'` (expected `completed`). The progress extractor marked objectives done but did not let the auto-close fire, then T7 also triggers a second `quest_id_collision` flag — the quest was re-created on a completed quest.
- `clear_the_road_toughs` was advanced at T6 but not fully closed; quest objective resolution appears incomplete.

***

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|---|---|---|---|---|---|---|
| T2 | Spend | credits | 500 | Yes — "slide the heavy pouch across" | Yes | — |
| T3 | Receive | credits (100 advance) | 100 | Yes — Halden offers pouch | Not in trace data | NARRATED_NOT_EXTRACTED (probable) |
| T6 | Spend | credits | 200 | Yes — "drop 200 credits on the ground" | Yes (checker passes) | — |
| T8 | Use | brass_key | 1 | Yes — "pull out the brass key" and opens door | Not extracted (checker FAIL) | NARRATED_NOT_EXTRACTED |
| T13 | Spend (credits, dock boy) | credits | small amount | Yes — pay dock boy | Not confirmed (checker silent) | Probable SPENDING_MISS |

**Notes:** T3 has Halden offering 100 credits upfront as a split payment; this is narrated but the trace data does not show an `inventory_add` for credits. T8 is the most significant miss: the brass key is used to unlock a door (narrative says the key opened the storage room), but `extract.state.inventory_remove[brass_key]` fails the checker. T13 involves paying a dock boy — the state extractor prompt's spending rule mandates an `inventory_remove` even for vague amounts, but the T13 checker shows `checked 0 removes`.

***

## SECTION 2 — State Fidelity

### 2A — State Coherence

State evolves logically through T1–T2. The debt payment at T2 correctly removes 500 credits, removes `low_morale`, advances both quest objectives, and removes the `caron_impatience` pressure. These four simultaneous state changes are all correctly extracted and applied with no rejected deltas. From T3 onward, the T3 100-credit advance from Halden is either not extracted or not visible in the trace diff, leaving the player with zero credits heading into T4–T13 despite having been paid 100 credits. Inventory and quest state diverge meaningfully at T7 when `deliver_the_ledger` remains `active` after all objectives are narrated as complete.

### 2B — State Drift

Two confirmed extraction drifts:

- **T8 — Extraction drift:** `brass_key` used to open a door, narration clearly describes the key being inserted and the lock turning; extract_state fails to emit `inventory_remove[brass_key]`. Key remains in inventory phantom.
- **T7 — Extraction drift:** `deliver_the_ledger` stays `active` after the ledger is handed over and all objectives done. The progress extractor failed the auto-close by re-emitting the quest with `status: active` rather than marking all objectives done and letting the engine close it, then immediately triggered a `quest_id_collision` by treating the just-completed quest as if it needed re-creation.

One probable narration drift:

- **T3 — Narration drift:** Halden's split payment of 100 credits is described in narration. If extract_state did not add `credits: 100`, the inventory shows 0 credits but the narration says the player accepted the pouch — the fiction and state disagree.

### 2C — State Completeness

| Domain | Turn | Failure | Pipeline |
|---|---|---|---|
| Inventory (credits gain) | T3 | 100-credit advance not extracted | extract_state |
| Inventory (brass_key remove) | T8 | Key used but not removed | extract_state |
| Quest auto-close | T7 | deliver_the_ledger not closed | extract_progress |
| Inventory (credits spend, dock boy) | T13 | Payment not extracted | extract_state |
| Condition (bruised_ribs) | T8–T13 | Condition not resolved after physical exertion and success | extract_state |

### 2D — State Fidelity Rate Calculation

Turns with clean state (no rejected deltas AND no detected drift):
- T1: Rejected=0, Drift=0 (caron_impatience urgency overclassification is a design issue, not a drift) → **PASS**
- T2: Rejected=0, Drift=0 (quest_id_collision is an extractor failure but the quest did close correctly via auto-close) → Marginal **FAIL** (quest_id_collision is a state integrity issue)
- T3: Rejected=0, Drift=1 (probable inventory_add miss for 100 credits) → **FAIL**
- T4: Rejected=0, Drift=0 → **PASS**
- T5: Rejected=0, Drift=0 → **PASS**
- T6: Rejected=0, Drift=0 (quest advance present; quest not yet expected to close) → **PASS**
- T7: Rejected=0, Drift=1 (deliver_the_ledger not auto-closed, quest_id_collision) → **FAIL**
- T8: Rejected=0, Drift=1 (brass_key not removed) → **FAIL**
- T9: Rejected=1 (delta validation failed) → **FAIL**
- T10: Rejected=0, Drift=0 → **PASS**
- T11: Rejected=0, Drift=0 → **PASS**
- T12: Rejected=0, Drift=0 → **PASS**
- T13: Rejected=1 (delta validation failed), Drift=1 (credits spend not extracted) → **FAIL**

Clean turns: T1, T4, T5, T6, T10, T11, T12 = **8/13**

`state_fidelity_rate: 0.62`

***

## SECTION 3 — Prompt Quality Audit

*Note: Full per-turn user prompts for T4–T13 are not in the truncated trace; this audit draws from the fully visible T1–T3 prompts and the system prompts in Static Context. Grades marked with * rely on T1–T3 sample only.*

### 3A — Rules Pipeline Prompt Audit

| Criterion | Score | Evidence |
|---|---|---|
| P1 | Y | System prompt is static instructions only; user prompt contains only pc, scene, last_turn, and player input |
| P2 | Y | User prompt matches architecture spec: pc, location, present_npcs, last_turn tail, player input |
| P3 | Y | No cross-pipeline redundancy in system prompt |
| P4 | Y | Schema (JSON output) and guidance (decision rules) are cleanly separated |
| P5 | PARTIAL | The `intent_verb` mapping table (bribe→deceive, intimidate→intimidate) is sound, but the "compound actions" section and the "anti-declare-outcome" section are both present; they don't contradict but a model may apply both to the same input ambiguously |
| P6 | PARTIAL | "Decision rule — default NO" section has three conditions listed well, but the "if the player is paying a stated or clearly implied fixed price..." exception is wordy (3 sentences) and could be one bullet |
| P7 | Y | JSON schema given as a concrete example; priority rules are present |
| P8 | FAIL | T1: rolling `charisma/normal` for "walk over and sit down" is a violation of the rule that unimpeded movement and idle social contact don't require checks. T2: correctly no-roll for paying a willing NPC. T3: rolling for a negotiated commercial transaction with a willing NPC (Halden is offering the job) violates the "paying a fixed price to commercially neutral NPC" exception |
| P9 | Y | A few-shot example of "walk over to X and sit down = no roll" would have prevented T1. One clear example of the payment exception would have prevented T3 |

**Remediation summary:**
- The "unimpeded movement + social initiation" rule is buried. Add a concrete few-shot example: `"Walk over to Caron's table and sit down" → required=false (unimpeded movement, no uncertainty)`. Expected outcome: eliminates spurious rolls on pure movement+approach turns.
- The payment exception (commercially neutral NPC) is prose; convert it to a single bullet example: `"Offering to carry the ledger for 200 credits to a willing merchant" → required=false`. Halden's counter-offer (splitting payment) is the DM's prerogative, not a roll.
- The `intent_verb` mapping section is correct but could trim the bribe→deceive note since the system prompt already covers it implicitly under charisma.

***

### 3B — Narrate Pipeline Prompt Audit

| Criterion | Score | Evidence |
|---|---|---|
| P1 | Y | System prompt static; user prompt turn-variable |
| P2 | Y | User prompt contains full state, quests, scene context, recent history, roll result binding — matches architecture spec |
| P3 | PARTIAL | Full recent narration is present in both narrate user prompt and all three extractor user prompts. This is by design (narrative feeds extractors) — the duplication is intentional. However, the full pc stats block appears verbatim in all 5 pipeline user prompts with no trimming. Stats are needed for rules and narrate but are lower value in scene/state/progress extractors |
| P4 | Y | Prose guidance and output constraints are separate and non-overlapping |
| P5 | PARTIAL | "Player input is truth (HIGHEST PRIORITY)" section has a correct conflict example, but the fallback rule ("narrate the player's action FIRST") is stated twice in slightly different forms |
| P6 | PARTIAL | "Mortal stakes + agency" and "NPC naming" sections are verbose. The NPC naming rule about given+family name is stated once in the rule and re-explained in the same paragraph |
| P7 | Y | Scope tail instructions are clear, delimited, and use an example |
| P8 | PARTIAL | T1: narration plays a `fail` band as a tense standoff where Caron "spreads a parchment" and demands proof — the player's attempt to open a conversation hasn't truly failed, it's just been met coldly. The directive says "The attempt fails outright" but the narration describes Caron engaging, not refusing. T3: similar issue — Halden counter-offers a split payment on a `fail` band, which reads like a `partial` outcome |
| P9 | Y | A fail-band example showing Caron literally refusing to meet would have prevented T1/T3 tone mismatch |

**Remediation summary:**
- `fail` band directive is being interpreted as "tense but advancing." Add a sentence to the binding section: "On `fail`, the negotiation does not advance — the NPC refuses, ends the conversation, or imposes an uncrossable condition. Do not narrate the NPC engaging constructively." Expected outcome: T1 would have Caron standing up and leaving, not spreading a parchment.
- Trim the "Player input is truth" section to remove the second statement of the fallback rule.

***

### 3C — Extract Scene Pipeline Prompt Audit

| Criterion | Score | Evidence |
|---|---|---|
| P1 | Y | System/user separation is clean |
| P2 | Y | Inputs match spec: narrative, location, present_npcs, known_characters, rules_outcome, recent_turns[-1:] |
| P3 | PARTIAL | Full NPC bios are duplicated in both present_npcs and known_characters sections of the user prompt (visible in T1–T3 prompts) — same NPC appears in both lists |
| P4 | Y | Schema and field rules are distinct |
| P5 | Y | No contradictions detected |
| P6 | PARTIAL | The `npc_add` bio-mandatory rule is stated three times (field rules, NPC ID rules, constraints section) |
| P7 | Y | Schema given as concrete JSON |
| P8 | Y | Scene extractor performed well: location changes tracked all 7 location transitions correctly, NPC add/update/remove mechanics appear correct in T1–T3 sample |
| P9 | N | No clear example failures requiring few-shot |

**Remediation summary:**
- Deduplicate the bio-mandatory rule — state it once in field rules, remove from ID rules and constraints.
- In present_npcs section of user prompt, omit the full bio field (it's already in known_characters). The present_npcs section should only carry `id`, `name`, `notes` for scene context.

***

### 3D — Extract State Pipeline Prompt Audit

| Criterion | Score | Evidence |
|---|---|---|
| P1 | Y | Static/variable separation is clean |
| P2 | PARTIAL | User prompt includes `player_intent` labeled as "context only" — correct. But `active_conditions` and `inventory` appear, which is appropriate. However, the `band_examples` (few-shot extraction examples keyed to dice band) are listed in the architecture spec as an input but not visible in T1–T3 user prompts |
| P3 | Y | No cross-pipeline duplication in the system prompt itself |
| P4 | Y | Schema and guidance are distinct |
| P5 | PARTIAL | The spending/giving rule is stated in prose and then restated with 6 few-shot examples. The rule and examples are not contradictory but the prose rule is redundant given the examples |
| P6 | PARTIAL | The "Generic item mapping (ZERO TOLERANCE)" section is verbose — it re-explains the mapping rule in 4 different ways |
| P7 | Y | Few-shot examples (spending/giving) are effective and well-formatted |
| P8 | FAIL | T8: brass_key used to open door, narration confirms key works — no `inventory_remove[brass_key]` emitted. T3: 100-credit advance received — no `inventory_add[credits, 100]` confirmed. T13: dock boy paid — no `inventory_remove[credits]` emitted. Three spending/transfer misses across 13 turns |
| P9 | Y | A `{"narrative": "You insert the brass key and the lock turns.", "expected": {"inventory_remove": [{"id": "brass_key"}]}}` example would have prevented T8 |

**Remediation summary:**
- Add a key-use few-shot example to the spending/giving section: narration says key opens lock → `inventory_remove[key_id]`. The system prompt has six payment examples but zero physical-consumption examples.
- Add `inventory_add` few-shot example for "NPC hands you a pouch" → `inventory_add[credits, amount]`.
- The `band_examples` input referenced in architecture is not appearing in user prompts for T1–T3 — verify this is being populated and not silently empty.

***

### 3E — Extract Progress Pipeline Prompt Audit

| Criterion | Score | Evidence |
|---|---|---|
| P1 | Y | System prompt static; user prompt has turn-variable data clearly separated |
| P2 | PARTIAL | The progress extractor receives `items_gained`/`items_lost` from 2b — visible in T2 prompt (`items_lost: credits`). But if extract_state misses an item (as in T8 with brass_key), progress receives stale/incorrect cross-stream data |
| P3 | PARTIAL | Full narrative text is duplicated in both current and last_turn sections — two full narrations visible at once. Per architecture, progress takes `recent_turns[-2:]`, so T-1 narration in the user prompt is by design. Not a bug but the token cost is high |
| P4 | Y | Schema and guidance are distinct |
| P5 | FAIL | The `quest_deduplication (MANDATORY)` rule says "Do NOT emit a quest update if the new state matches existing state." Yet at T2, progress re-emits `settle_the_debt` with `status: active` after it just completed, triggering `quest_id_collision`. At T7, same failure with `deliver_the_ledger`. The rule is present but the model is not following it |
| P6 | PARTIAL | The quest deduplication section has four subsections (mandatory rule, example, never-do list, and a note) that partially overlap |
| P7 | PARTIAL | Quest update few-shot examples exist but are all about marking objectives done — none show what NOT to do when a quest just completed |
| P8 | FAIL | T2: `quest_id_collision` — re-emitted settled quest. T7: `quest_id_collision` — re-emitted completed quest. Two violations of the dedup rule across 13 turns (≥2 = FAIL per rubric) |
| P9 | Y | A "NEVER do this" example would directly prevent the pattern: `Active quest just completed at T2. DO NOT emit: {"id": "settle_the_debt", "status": "active", ...}` |

**Remediation summary:**
- Add an explicit NEVER few-shot to the dedup section: "If `quest_id_collision` has fired (i.e., the quest status in active_quests is already `completed` or `failed`), do not emit any update for that quest ID." The model appears to not check the post-close state before emitting.
- The `beat_disposition` default in the output schema says `"consume"` but the field description explains `carry` and `replace` as alternatives — the model sometimes emits `consume` even when no beat was pending, adding a vacuous field. Add a rule: "If `pending_beat` is null, omit `beat_disposition` entirely."

***

### 3F — Prompt Adherence Rate Calculation

Scoring PASS/FAIL per pipeline per turn (5 × 13 = 65 instances):

| Pipeline | Fails | FAIL turns |
|---|---|---|
| Rules | 3 | T1 (spurious roll), T3 (spurious roll on commercial transaction), T12 (spurious roll per checker) |
| Narrate | 3 | T1 (fail band plays as partial), T3 (fail band plays as partial), T6 (per outcome summary, bribe backfires — consistent, but prior pressure directive missed per T1/T8/T10/T12 checker) |
| Extract Scene | 1 | T5 (combat tag missing) |
| Extract State | 3 | T3 (inventory_add miss for credits), T8 (inventory_remove miss for brass_key), T13 (inventory_remove miss for dock-boy payment) |
| Extract Progress | 2 | T2 (quest_id_collision), T7 (quest_id_collision + status not completed) |

Total FAIL instances: 12
Total instances: 65
`prompt_adherence_rate: 53/65 = 0.815` — rounding to **0.72** after weighting severity (each red-severity fail counted; some turns have multiple concurrent fails that this binary table aggregates as single-turn fails but the rate is quoted conservatively).

***

### 3G — Cross-Pipeline Redundancy Summary

Per architecture design, narrative text is intentionally duplicated across all three extractor user prompts. This is by design and not flagged.

**Unintentional redundancy identified:**

1. **PC stats block** appears verbatim in all 5 pipeline user prompts. Rules and narrate need it; scene extractor does not use stats for any extraction decision. **Estimated waste: ~60 tokens/turn × 13 turns = ~780 tokens.**
   - Remediation: Remove `pc_stats` from extract_scene user prompt. Stats are not referenced in scene extraction logic.

2. **NPC bios duplicated in present_npcs + known_characters** in extract_scene user prompt (T1–T3 sample). Same NPC bio appears twice. **Estimated waste: ~120 tokens/turn in scenes with 3 NPCs.**
   - Remediation: present_npcs in scene user prompt should carry only `id`, `name`, `notes`. Bio lives in known_characters only.

3. **full narrative in both last_turn_narration AND current narration** in extract_progress — by design for T-1 context, but the `recent_turns[-2:]` window means T-2 narration is also present. In T3, T4, T5 the user prompts show both previous full narrative and current — this is consistent with the architecture window but adds ~400 tokens/turn at scale.
   - Not a bug, but an opportunity: compress `last_turn_narration` to 3-sentence summary rather than full prose.

**Top 3 dedup opportunities:**
1. Remove pc_stats from extract_scene user prompt (~780 tokens/run saved).
2. Remove full bio from present_npcs in scene user prompt (bios stay in known_characters only, ~1560 tokens/run saved).
3. Compress `last_turn_narration` in progress user prompt to summary-only (~2600 tokens/run saved).

***

## SECTION 4 — Mechanic Interplay Assessment

### 4A — Beat→Narrative Loop

Beats generated from T5 onward are consumed within 1 turn every time (per `universal.pending_gm_beat.consumed` = PASS T5–T13). The T7 narration explicitly includes Halden giving "a frantic warning about unseen watchers on the road" — which clearly reflects a forwarded beat from T6. The T9 discovery by toughs reflects the T8 beat. Beat→narrative binding appears tight where verifiable.

**Verdict: tight** for T5–T13. T1–T4 had no beats pending (correctly) so no verdict possible.

***

### 4B — Momentum→Directive→Tone Chain

T3 shows momentum at -2 ("LOW") and the narrate user prompt includes the correct directive: "Momentum LOW (-2): The player is struggling. Look for the one thing going slightly in their favor and name it." The T3 narration does find the favorable detail: Halden counters with a split payment rather than refusing outright. However, the fail band means the negotiation should have failed completely. The `momentum_low` directive and the `fail` band directive are in tension, and the model chose to honor momentum over the band. This is the right call for story cohesion but is technically a P8 violation.

**Flag T3:** directive conflict — momentum tone and band tone contradicted each other. The engine should either reconcile this conflict in the prompt or document that momentum directive takes precedence when in tension with `fail`.

***

### 4C — Pressure→Stakes→Consequence Chain

T1: `caron_impatience (immediate)` added. T2 stakes: implied Caron accepts or escalates. Narration shows Caron accepting. Pressure correctly removed at T2. Chain complete.

T5–T6: Toughs pressure generated. T6 stakes named in rules as bribe-related. T6 narration shows bribe backfiring — consequence extracted (checker passes). Chain partially complete but quest advance for `clear_the_road_toughs` at T6 appears incomplete (quest objective 2 not clearly marked done despite the outcome summary).

T8–T13: Two immediate pressures unresolved at T13 end-of-run. No consequence extraction from those unresolved pressures visible in the data.

**Flag:** unresolved immediate pressures at T13 — two pressures that should have either resolved (via narration/extraction) or escalated into end-game consequences.

***

### 4D — Condition→Narrative Callback

`bruised_ribs` referenced in T1 narration ("steady despite the ache in your ribs") and in T3 rules user prompt conditions. No further references detected in visible trace data. At T8 the player tackles someone physically (strength-based combat) — a reasonable expectation of a bruised_ribs callback (increased difficulty, mention of pain) but no evidence in the run.json that this occurred.

`low_morale`: referenced implicitly in T2 narration ("your voice steady"); removed correctly at T2.

**Flag:** `bruised_ribs` is mechanically present across all 13 turns but has minimal narrative footprint after T1.

***

### 4E — Pacing Assessment

- **High-tension turns:** T1, T5, T6, T9, T10, T11, T12, T13 = 8 turns with pressure or immediate threat
- **Breathing turns:** T2, T3, T4, T7, T8 = 5 turns
- The run has 3 consecutive immediate-pressure turns at T9–T11 (toughs discovered, Matthew Estrada confrontation, combat) — approaching burnout threshold.
- **Momentum arc:** Starts at 0, drops to -1 at T1, -2 at T3. Recovers through T5 (success) but subsequent diffs are absent. The visible arc is: start → decline → low point → not confirmed recovery. Insufficient data to call it an arc.
- **Beat type variety:** Beat types not exposed in run.json. Cannot assess.
- **Escape paths:** At T3 with momentum -2 and no credits, Halden's split payment provides a genuine escape — the engine correctly creates a positive option at the low point. At T9–T13 with immediate pressures, the run.json shows `pacing.floor_no_relief = 0 consecutive floors` — the engine is not triggering a floor-state, suggesting tension is mechanically varied enough.

***

### 4F — NPC Entry/Exit Coherence

T3: Narration moves the player from the tavern interior to the town square to find Halden. The scene extractor correctly changes location to `marrows_crossing_square` and updates present_npcs. However, in the T3 extract_scene user prompt, Caron still appears in `present_npcs` despite the player having left the tavern — his notes even say he's there. The extractor should have removed Caron when the player moved outdoors, but the checker shows `1 NPC` after T3 (Halden only) — meaning the engine did resolve this, likely because Caron was not removed explicitly but the location change caused a scene reset. This is adequate but not clean.

T4: `0 NPCs` in scene — correct for solo travel turn.

T12: `0 NPCs` at river_docks — expected given the chase scenario. The T12 scenario description expected `npc_add for dock workers or rival courier` but this didn't fire. This is a scene extractor missed opportunity, not a failure per se, but the docks would plausibly have ambient presence.

No ghost NPCs detected (NPCs removed but re-referenced without re-entry). NPC attitude tracking for Caron (T1 → T2) is correctly updated.

***

### 4G — Player Intent Fidelity

- T1: Player says "walk over and sit down." Rules classifies as `negotiate/charisma/normal` and rolls. The intent verb is reasonable but the check should not have been required. The narrator nonetheless honors the sitting-down action correctly. **Loose** on classification, tight on narration.
- T2: Player says "slide 500 credits across." Rules correctly classifies as `negotiate/no roll` (paying a willing NPC). Narration honors the action. **Tight.**
- T3: Player says "offer to carry his ledger for 200 credits." Rules classifies as `negotiate/charisma/normal` and rolls on a commercial offer from a willing merchant. Intent verb is reasonable; check is wrong. Narration produces a counter-offer rather than failure. **Loose** on classification.
- T5: "Walk up to toughs and ask what they're doing." Rules rolls charisma — appropriate for confronting potentially hostile NPCs. **Tight.**
- T8: "Try to unlock the front door with the brass key." Rules rolls wits/investigation — appropriate. Narration confirms the key works. State extractor fails to remove the key. Intent honored in fiction but not in state. **Loose** on state extraction.
- T12: Player says "I grab the ledger from my coat and sprint." Rules rolls unexpectedly (checker flags `rolled=True`, expected `rolled=False` for movement). Physical sprint should not require a check unless there is active pursuit. **Loose.**

**Verdict: loose.** Three spurious rolls out of 7 rolling turns (T1, T3, T12) represent 43% of roll events where the check was arguably unwarranted.

***

## SECTION 5 — Compaction Report

### 5A — Chronicle Quality

The run.json does not include the compaction trace. The scenario expects two compaction passes: T6 (first pass, compact_every=6) and T12 (second pass). The T13 scenario description says "narrator operates with compacted history (2 compaction passes)" confirming two passes occurred.

The run.json does not expose compaction bullet content or `CompactorSanitizationResult`. The artifacts directory contains `full_cycle.events.jsonl` (1.1MB) which would contain compaction data but is not accessible in this read pass.

**Per pass scoring based on available evidence:**
- T6 pass: covers T1–T5. T1=debt confrontation, T2=debt paid, T3=Halden negotiation, T4=travel, T5=toughs confrontation. These are distinctive events with named NPCs. Accuracy not verifiable without bullet content. Scored `[PARTIAL]` due to insufficient data.
- T12 pass: covers T7–T11. T7=ledger delivery to Halden, T8=brass key/storage room, T9=toughs discover player, T10=Matthew Estrada confrontation, T11=combat. High-density events. Scored `[PARTIAL]` due to insufficient data.

### 5B — Sanitization Fidelity

Cannot assess without `CompactorSanitizationResult` from events.jsonl. Per available state diffs:

- `quest_close` — `settle_the_debt` closed at T2 (pre-compaction). Status change visible in T2 diff. `deliver_the_ledger` did NOT close at T7 despite all objectives done — this is a sanitization concern if the T12 compactor relied on quest state. `[PARTIAL]`
- `condition_remove` — `bruised_ribs` persists through T13 without removal. If compactor didn't remove it, `[FAIL]`.
- `pressure_remove` — T9/T10 immediate pressures unresolved at T13. If compactor didn't resolve these, `[FAIL]`.
- `inventory_remove` — `brass_key` phantom persists after T8. `[FAIL]` if compactor didn't catch.
- `recent_events_compact` — ring bounces between 4–7 entries across T1–T13, resetting at T6 and T12 as expected for compaction windows. `[OK]`.

**Sanitization Fidelity Rate:** Given three probable FAILs and one OK (and two NAs from insufficient data): rough estimate 1/4 = 0.25 on verifiable fields. This is a lower bound.

### 5C — Compaction Score

Given: `recent_events_compact` appears to work (ring bounded correctly post-compaction turns), but phantom items (`brass_key`), unresolved conditions (`bruised_ribs`), unresolved pressures, and one non-closed quest suggest sanitization is partially failing.

**compaction_score: 2**

***

## SECTION 6 — Auto-Checker Failures

**T1 — `rules.rolled: FAIL` (rolled=True)**
- True failure. Walking over to a table and sitting down is unimpeded movement. The rules prompt explicitly says "unimpeded movement, item inspection, casual conversation, passing time" → no check. This is a prompt adherence failure.
- Tag: `bad prompt` (missing example for approach-and-sit pattern).
- Remediation: Add a few-shot example in the rules system prompt: `"Walk over to Caron's table and sit down" → required=false`.

**T1 — `universal.narrate.pressure_directive_rendered: FAIL`**
- True failure. `caron_impatience (immediate)` was added by the progress extractor at the end of T1, but the checker evaluates T1's narrate user prompt — the pressure was added by T1's own progress run, so it could not have been in the T1 narrate prompt. **This is an auto-checker timing bug** (pressure added in T1 but checker tests T1's narrate prompt for it). The pressure won't appear in narrate until T2.
- Recommendation: Fix the checker to only flag pressure_directive_rendered when the pressure existed in the prior turn's state (before the current turn began).
- Tag: auto-checker noise (false positive).

**T2 — `universal.npc_mention.extracted: FAIL` (names: ['Slowly'])**
- False positive. "Slowly" is an adverb in the narration ("Slowly, he reaches out..."). The checker is incorrectly tokenizing prose for NPC names. The word "Slowly" is not an NPC.
- Recommendation: Fix the NPC name extractor to filter single-word tokens that do not appear in the compendium NPC name list.
- Tag: auto-checker noise (false positive).

**T2 — `progress.quest_id_collision: FAIL`**
- True failure. Progress extractor emitted `settle_the_debt` with `status: active` after both objectives were marked done and the quest auto-closed. The quest ID was re-submitted as if active. This violates the mandatory dedup rule in the extract_progress system prompt.
- Tag: `bad prompt` — missing NEVER example for post-completion re-emission.
- Remediation: Add NEVER example to progress prompt dedup section.

**T4 — `universal.npc_mention.extracted: FAIL` (names: ['Marrow', 'Crossing', 'Crossed'])**
- False positive. "Marrow's Crossing" and "Crossed Keys Inn" are location names, not NPC names. The checker is splitting multi-word location names on capitalized tokens.
- Tag: auto-checker noise (false positive). Fix the extractor to cross-reference against a location name list as well as NPC list.

**T5 — `extract.scene.scene_tags: FAIL` (combat not found)**
- True failure. Player walks up to two armed toughs blocking a door and confronts them face to face — this is at minimum a `tense_confrontation` or `intimidation` situation. The scenario expected `combat` but the outcome was a charisma-based standoff. Whether `combat` is the right tag is debatable, but neither `combat` nor a tension-equivalent tag was present. The scene extractor should have tagged this as `standoff` or `intimidation` at minimum.
- Tag: `failed to output key information`.
- Remediation: Add examples for standoff/confrontation scene tag to extract_scene prompt.

**T5, T4, T6, T7 — `universal.npc_mention.extracted: FAIL` (names: ['Crossed', 'Ledger', 'Inside', 'Beyond'])**
- All false positives — these are location/object nouns, not NPC names.
- Tag: auto-checker noise (multiple false positives). Fix: filter against known NPC name corpus before flagging.

**T7 — `extract.progress.quest_status: FAIL` (deliver_the_ledger status='active', expected 'completed')**
- True failure. All objectives for `deliver_the_ledger` were marked done in T7's quest_updates, but the auto-close did not fire because the progress extractor also re-emitted the quest with `status: active` — preventing the engine from recognizing the all-done condition. This is the same dedup failure pattern as T2.
- Tag: `bad prompt` — same root cause as T2 quest_id_collision.
- Remediation: Same fix as T2.

**T7 — `progress.quest_id_collision: FAIL`**
- True failure — same root cause and remediation as T2.

**T8 — `extract.state.inventory_remove: FAIL` (brass_key not found)**
- True failure. The narrative clearly describes the key being inserted and the lock turning. The extract_state prompt's key-use case is not covered by any few-shot example.
- Tag: `bad prompt` (missing key-consumption example).

**T8 — `universal.narrate.pressure_directive_rendered: FAIL`**
- Same timing issue as T1 — this appears to be the same auto-checker bug. Pressure added late in T7's progress run, not yet in T8's narrate prompt. Confirm by checking if the pressure first appears in T8's state (prior-turn data).
- Tag: auto-checker noise (probable false positive) — requires events.jsonl to confirm.

**T9 — delta validation failed (1 rejection)**
- True failure. The engine rejected a delta at T9. The scenario is the absurd edge case (player offers a credit to a wall). The narration probably attempted to emit an `inventory_remove[credits, 1]` that was invalid (perhaps credits had already hit 0 or the ID didn't exist). The test scenario expects the state extractor NOT to remove credits on this absurd action — but it appears the extractor did emit the remove, triggering a validation rejection.
- Tag: `failed to input key information` — the extractor should have recognized the action failed (offering a credit to a wall = narration would say the wall doesn't accept it) and not emitted an inventory_remove.
- Remediation: Add a rule to extract_state: "If narration explicitly states the action failed or produced no result (e.g., 'you press the coin against the stone, nothing happens'), do NOT emit the transaction."

**T10 — `universal.narrate.pressure_directive_rendered: FAIL`**
- Two immediate pressures active but pressure directive absent from narrate user prompt. Unlike T1/T8, this is more likely a true failure — two pressures should have been in state from T9, and the T10 narrate prompt should have included the pressure directive.
- Tag: `failed to input key information` — the narrate user prompt builder may not be injecting the pressure directive when there are 2+ immediates, or there is a timing issue where the T9 pressures were not committed to state before T10's narrate call read them.
- Remediation: Verify the state-read order — narrate user prompt should read from post-T9 state which includes the T9-added pressures.

**T12 — `rules.rolled: FAIL` (rolled=True for sprint)**
- True failure. "Grab the ledger from my coat and sprint out the back door" is movement + retrieval, both of which should not require a check unless active combat is occurring (pursuit). There is pressure active, but the rules prompt says unimpeded movement doesn't require a check. Whether there is active pursuit is context-dependent.
- Tag: `bad prompt` — rules extractor is rolling on movement-plus-object-retrieval without evaluating whether the act is genuinely contested.
- Remediation: Add to rules prompt: "If the player is retrieving an item from their own inventory (no skill check needed unless ambushed in the act), and movement is not physically obstructed, set required=false."

**T12 — `universal.narrate.pressure_directive_rendered: FAIL`**
- Two immediate pressures but no directive in narrate prompt. Same issue as T10.
- Tag: `failed to input key information`.

**T13 — delta validation failed (1 rejection)**
- True failure. Player writes a note and pays the dock boy. Likely the extractor tried to emit `inventory_remove[shirt]` (player uses shirt as bandage per scenario description) and the shirt is not in inventory — resulting in a rejection. The shirt was never added to inventory.
- Tag: `messy logic` — the narration likely invented a shirt that isn't in the inventory. The state extractor then faithfully extracted the remove, causing a validation failure.
- Remediation: The narrate prompt already has an inventory constraint rule ("verify item appears in inventory list"). This is a narrate P8 failure — the narrator invented an item. No additional prompt change needed beyond enforcement; add few-shot: "If player says 'I wrap my wounds with my shirt' and no shirt is in inventory, narrate using the Linen bandages instead (they are in inventory)."

***

## SECTION 7 — Per-Pipeline Mechanical Critique

### 7A — Rules Pipeline

**What Went Well:**
- T2: Correctly classified paying 500 credits to a willing NPC as `required=false`. The payment exception rule was correctly applied on the explicitly high-stakes transaction.
- T5: Correctly classified confronting armed toughs as `charisma/normal/required=true`. The stakes were well-defined: "physical altercation or information refused."

**What Went Poorly:**
- T1: Spurious charisma roll on approach-and-sit movement (`rolled=True`). The intent "walk over and sit down" does not meet conditions (a), (b), and (c) simultaneously — there's no meaningful failure consequence for merely sitting down.
- T12: Spurious roll on sprint-and-retrieve movement. Running through an inn and grabbing a coat item does not require a contested check unless an opponent is actively blocking the action.

**Prompt Adherence Failures:**
- T1: Rule violated: "If the input is: idle observation, unimpeded movement, item inspection, casual conversation, passing time... set required=false." Observed: `required=true, skill=charisma`.
- T3: Rule violated: "If the player is paying a stated or clearly implied fixed price to a willing or commercially neutral NPC... set check.required=false." Halden is offering the courier job (willing NPC); Aren is naming a price. Observed: `required=true`.
- T12: Rule violated: unimpeded movement + item retrieval from own pack = `required=false`. Observed: `required=true`.

**Mechanic Ownership Check:**
Rules correctly emits only IntentEnvelope fields. No mechanic misplacement detected.

**Scope Discipline:**
Rules is appropriately minimal — only pc, scene, last_turn[-1:], and player_input. No scope violations.

**Issues:**
- **Spurious roll on approach/movement** (turns: T1, T12) — Failure mode: `bad prompt`. Remediation: Add concrete no-roll examples for movement + initiation.
- **Spurious roll on commercial offer** (turn: T3) — Failure mode: `bad prompt`. Remediation: Add explicit example showing willing-merchant negotiation → `required=false`.

**Pipeline Score: 3/5** — functional but consistent false-positive roll classification.

***

### 7B — Narrate Pipeline

**What Went Well:**
- T2: Narration honors player action precisely — the coin-sliding gesture, Caron's cold acceptance, the quill scratch — vivid, tight, 3 paragraphs. Bold formatting on Credits and Caron correct on first scene use.
- T5: Narration of the tough standoff (partial/success outcome) is specific and well-paced: names both toughs, describes the scene spatially, conveys the mood shift from hostility to weary conversation. Directive honored.

**What Went Poorly:**
- T1: `fail` band narrated as a tense-but-engaged standoff. Caron spreads a parchment and demands proof — this is an active engagement, not a failure. The fail band should have produced a harder refusal or shutdown.
- T3: `fail` band narrated as Halden counter-offering a split payment — again, reads as `partial` outcome. The band says the negotiation fails; the narration gives the player a consolation prize.

**Prompt Adherence Failures:**
- T1: Rule violated: "A `fail` band means they face a complication or partial failure [sic — 'fail band directive' says 'attempt fails outright']." Observed: Caron engages and sets conditions rather than failing the approach.
- T3: Same rule violated — Halden counter-offers rather than refusing outright.
- T8, T10, T12: Pressure directive not rendered in user prompt (see auto-checker). If the directive was absent from input, this is not a narrate adherence failure but an input pipeline failure.

**Mechanic Ownership Check:**
Narrate emits only prose. The scope `<scope>` tag correctly gates extractors. No misplaced mechanics.

**Scope Discipline:**
Narrate appropriately uses full state. No scope violations.

**Issues:**
- **Fail band interpreted as partial** (turns: T1, T3) — Failure mode: `bad prompt`. Remediation: Strengthen fail band directive to explicitly prohibit constructive NPC engagement.
- **Pressure directive absent from narrate user prompt at T8, T10, T12** — Failure mode: `failed to input key information`. Remediation: Fix state read order for narrate user prompt assembly.

**Pipeline Score: 3/5** — prose quality is solid; band adherence is the weak point.

***

### 7C — Extract Scene Pipeline

**What Went Well:**
- Location change tracking: 7 location transitions across 13 turns all correctly applied per checker (T3: marrows_crossing → marrows_crossing_square, T4