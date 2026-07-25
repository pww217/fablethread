# Pack Archetype Subversion — Compelling Rewrite — Design Document

> **Status:** implemented
> **Source of truth:** [docs/findings/pack-archetypes-inspiration.md](../../findings/pack-archetypes-inspiration.md) (inventory of current state)
> **Related tickets:**
> - [I-43: Subvert and sharpen seed pools across all 5 default packs with maximum per-entry diversity](../../roadmap/improvements/I-43-pack-archetypes-subversion.md)

## Problem

The five default packs ship seed pools that are structurally competent but creatively flat. Three failure modes recur:

1. **Database-column language.** `situation_archetypes` and especially `arc_categories` read like schema fields, not story seeds. `institutional_corruption`, `power_struggle`, `resource_scarcity`, `territorial_control` — these are *tags*, not *hooks*. An LLM handed these generates the most generic possible scenario; a human reader feels nothing.
2. **Tropes played straight with no friction.** Each pack ships the genre's default posture: noir's good-detective-bad-city, zombie's last-humans-vs-monsters, space-western's plucky-underdog-Rim, piracy's romantic-democracy-of-rascals, WW2's brotherhood-of-arms. Nothing subverts, nothing surprises, nothing *wows*.
3. **PC situation schema is a character sheet, not a story prompt.** "Where do you live?", "What's your reputation?", "Who's your commanding officer?" — these seed nothing. They describe a status instead of charging a wound.

Compounding failure: even where individual entries are sharpened, they frequently **collide into a pack-level monoculture**. When every noir entry subverts toward "the institution is the villain," every sampled seed produces the same story with different nouns. The cross-product (situation × arc × dynamic × bond × scene × pc) — the entire point of a pool-based seed system — collapses to one story per pack.

This design targets maximum **combinatorial diversity**: every entry in every pool must subvert in its own direction, so any two seeds sampled from the same pack can yield wildly different stories.

## Firm Decisions

1. **Per-entry subversion, not per-pack.** Every entry in every pool carries its own distinct subversion direction. No two entries in the same pool subvert in the same direction. A pack's "posture" (below) is the genre default each entry pushes against — it is orientation, not a unified thesis.
2. **Combinatorial diversity is the design success criterion.** The seed sampler pulls N entries from M pools; the design succeeds when two random seeds from the same pack can produce two stories that share no central tension. The failure mode is two seeds producing the same story with different noun-substitutions.
3. **All pools in scope, plus missing world.md files.** `situation_archetypes`, `arc_categories`, `character_dynamics`, `npc_bonds`, `scene_detail_bundles`, `pc_situation_schema`, sharpened `baseline_facts` — and authoring `packs/default/{zombie-survival,space-western,allied-ww2}/world.md` (currently missing per inventory). The three new world bibles must establish a posture that the per-entry subversions in their pack push against; bundling them in this design guarantees that agreement.
4. **Schema unchanged.** YAML contracts stay identical: `id` + `tags` + optional `description`/`incompatible_with` for pools that have them; `items`/`conditions`/`sensory` for scene bundles; `key`/`description`/`required`/`persist` for pc_situation_schema. No new fields. IDs remain `snake_case` ASCII. Pool counts are unchanged (14 arcs, 8 dynamics, 8 bonds, 7 scenes, 4 pc schema per pack) — only content changes.
5. **IDs must be evocative, not bureaucratic.** Renaming IDs is in scope. `infrastructure_failure` → `the_well_that_drinks_people`. `power_struggle` → `the_reform_that_was_the_trap`. The ID is the hook; the tags confirm it. Tags stay noun-y for lexical matching; IDs carry the prose weight.
6. **NPC bonds stay strongest, get a "loaded" pass.** Most bonds already read like prose. The change: every bond carries a *cost* — a debt that is also surveillance; love that is also blackmail; trust whose proof is a crime; forgiveness that is the weight. Mutually binding, not sentimental. Bonds within a pack span different cost-structures (debt, secret, blackmail, blood, witness) — no two bonds in a pack charge the same way.
7. **Scene bundles get one wrong detail each, and the wrong details differ.** Every bundle keeps its atmosphere but adds exactly one period-plausible-but-story-generating detail. Across a pack's seven scenes, the wrong details should span different registers — never the same kind of wrongness twice.
8. **PC situation schema rewrites from status to wound.** Each field asks not "what is your situation" but "what is the thing about your situation that will hurt to discuss." The four fields in a pack must wound from four different directions (place, name/reputation, command/family, the secret) — no two fields wound the same way.
9. **No provenance restriction.** New IDs can contradict real-world history or in-fiction tropes where subversion demands; packs are fiction, not source material.
10. **No `moral_pressures` revival.** Per AGENTS.md note, that field had no structured target. Tension lives in IDs and descriptions.
11. **It is an improvement, not a feature.** Ticket is `I-43`. We are improving existing packs, not adding new ones.
12. **Full phrasing in the design.** Every entry in every pool (ID, tags, `description`, `items`, `conditions`, `sensory`, `key`, `required`, `persist`) is written verbatim in this doc, ready to paste into `scenario.yaml`. Plan/execute work is mechanical copy + verification (lint, typecheck, prompt-eval). The three new `world.md` files are written in full as exhibits. The design is the source of truth for content; no creative phrasing is left to plan/execute.

## Design Principles

- **One specific hook per entry.** A situation should imply a scene; an arc should imply a turn; a bond should imply a debt. Generic entries are rejected at write time.
- **The hook is in the ID.** Tags support the ID; they do not carry it. If the ID could appear unchanged in any pack, it's wrong.
- **Subvert toward a tension the genre already contains — but a different tension per entry.** Noir contains many tensions (institution-as-villain, the witness-is-the-perpetrator, the-cop-cleaner-than-the-room, the-dead-still-writing, evidence-that-returns, the-reunion-of-strangers-pretending-not-to-know). Each entry picks one. No pack rhymes with itself.
- **Concrete over atmospheric.** "The dockyard" is atmospheric. "The Customs manifest with a page torn out and a name printed in the wrong ink" is concrete. Always the latter.
- **One wrong detail, not many.** A scene with a single impossible-seeming element generates story; a scene swimming in weirdness generates noise.
- **Moral weight in seeds, not sermons.** Pools make moral choice *available* without dictating it. Frames like "the medic who decides who is salvageable" force the issue; the player chooses their side.
- **The conspiracy of silence beats the conspiracy of action.** Where genre defaults to a hidden plot, prefer a known truth no one will say aloud. More noir than noir — but use this axis only once or twice per pack; overuse collapses diversity.
- **No sentimentality.** Bonds that read "they'd die for each other" without a cost are rejected. Bonds must include the cost.
- **Diversity rule (load-bearing):** Within a single pool in a single pack, no two entries may subvert in the same direction. The subversion-axis annotation tables after each pool are the audit artifacts; duplicate axes are rejected at review-design.

## Target State

Per pack:
- **Posture** — the genre default being subverted against (orientation only).
- **World bible** — existing (noir, piracy) verified for alignment; new (zombie, space-western, allied-ww2) authored in full as exhibits.
- **Full pool entries** — every ID, tag, description, item, condition, sensory, key verbatim in YAML blocks ready to paste into `scenario.yaml`.
- **Subversion-axis tables** — per pool per pack, listing each entry's axis for diversity audit.

### Subversion axes vocabulary (distribute across pools, one per entry within a pool)

`institution_as_antagonist` · `truth_everyone_knows` · `loyalty_costs_more_than_betrayal` · `reform_was_the_trap` · `thing_that_keeps_coming_back` · `witness_is_perpetrator` · `clean_one_is_the_problem` · `dead_still_writing` · `reunion_pretending_not_to_know` · `decision_already_made` · `victim_engineered_it` · `genuine_thing_in_corrupt_room` · `mercy_that_was_cruelty` · `cruelty_that_was_mercy` · `record_doesnt_match` · `squad_held_by_secret` · `bond_whose_proof_is_crime` · `love_is_also_blackmail` · `debt_paid_in_whoever_else` · `innocent_who_is_guilty` · `guilty_who_is_innocent` · `place_that_wasnt_supposed_to_be_there` · `place_that_was_supposed_to_be_and_isnt` · `gospel_of_the_bloom` · `bloom_that_learns` · `child_who_remembers` · `child_who_doesnt_but_pretends` · `pressed_one_who_chose` · `pardon_kept_offered` · `war_that_will_not_be_over` · `occupation_forgot_why` · `guild_sells_members` · `articles_under_pressure` · `human_cargo` · `captain_engineered_mutiny` · `medic_decides_who_counts` · `enemy_recognized_not_dehumanized` · `engineer_already_wired_it` · `order_keeps_repeating_until_enforced` · `letter_from_home_doesnt_match` · `replacement_keeps_showing` · `conspiracy_inertia`

---

### 1. Noir — 1930s

**Posture:** good-detective-bad-city, gangster-as-villain, the case is solvable. Each entry subverts a different piece of this.

**World bible (existing — verify alignment):** Already supports "institution as antagonist"; design treats this as ONE axis among many, not the pack thesis. No changes needed to `packs/default/noir-1930s/world.md`.

**World facts (unchanged):**
1. The city is gripped by corruption spanning police, politics, and organized crime that no reform can touch.
2. Prohibition has created a black market that funds everything from speakeasies to bootleg operations and smuggling rings.
3. The economic depression has driven desperate people to crime while the wealthy insulate themselves behind wealth and influence.

**Baseline facts (sharpened, 3):**
1. The city runs on violence and money — gangsters control the docks, the unions, and the night; the police take a cut; ask too many questions and you get a bullet or a frame-up. The system works because the system works.
2. Every man has an angle, and the angle is often still the man you knew — the betrayal is the recognition, not the knife.
3. The city at night is not a character; it is a witness — it arranges itself so the thing you didn't want to see is unavoidable.

**Situation archetypes (count=10):**

```yaml
situation_archetypes:
  - id: witness_who_tried_to_confess
    tags: [witness, confession, police_complicity, refused_testimony]
    incompatible_with: []
  - id: scandal_that_never_breaks
    tags: [scandal, press_complicity, public_silence, known_truth]
    incompatible_with: []
  - id: heist_that_wasnt_the_crime
    tags: [heist, misdirection, simultaneous_crime, real_target]
    incompatible_with: []
  - id: murder_the_city_doesnt_want_solved
    tags: [murder, sanctioned_killing, institutional_interest, closed_case]
    incompatible_with: []
  - id: judge_who_kept_two_verdicts
    tags: [judge, sealed_verdict, courthouse altar, sealed_record]
    incompatible_with: []
  - id: the_case_you_didnt_take
    tags: [refused_case, returning_problem, recurring_file, unsought_work]
    incompatible_with: []
  - id: the_informant_who_keeps_sending_notes
    tags: [dead_informant, posthumous_contact, missing_person_mail]
    incompatible_with: []
  - id: evidence_that_names_you
    tags: [self_incriminating, victim_library, planted_or_chosen, dead_mans_letters]
    incompatible_with: []
  - id: the_suspect_you_let_walk
    tags: [prior_mercy, present_cost, returned_favor, framed_clear]
    incompatible_with: []
  - id: the_one_honest_cop_in_the_precinct_with_a_reason_to_lie
    tags: [honest_cop, necessary_lie, pressured_integrity, clean_room_dirty_corner]
    incompatible_with: []
```

**Situation archetype axes:**
- `witness_who_tried_to_confess` → witness_is_perpetrator
- `scandal_that_never_breaks` → truth_everyone_knows
- `heist_that_wasnt_the_crime` → decision_already_made
- `murder_the_city_doesnt_want_solved` → institution_as_antagonist
- `judge_who_kept_two_verdicts` → clean_one_is_the_problem
- `the_case_you_didnt_take` → thing_that_keeps_coming_back
- `the_informant_who_keeps_sending_notes` → dead_still_writing
- `evidence_that_names_you` → victim_engineered_it
- `the_suspect_you_let_walk` → mercy_that_was_cruelty
- `the_one_honest_cop_in_the_precinct_with_a_reason_to_lie` → genuine_thing_in_corrupt_room

**Arc categories (count=14):**

```yaml
arc_categories:
  - id: the_reform_that_was_the_trap
    tags: [reform, trap, folded_investigation, false_progress]
    incompatible_with: []
  - id: the_rot_that_passes_for_weather
    tags: [inertia, background_corruption, no_conspiracy, ambient_rot]
    incompatible_with: []
  - id: the_loyalty_that_costs_more_than_betrayal
    tags: [loyalty, costly_binding, refusing_to_betray, weight_of_fidelity]
    incompatible_with: []
  - id: the_story_the_paper_already_wrote_before_it_happened
    tags: [press, prepared_narrative, mismatched_record, prewritten_news]
    incompatible_with: []
  - id: the_turf_war_no_one_will_admit_is_over
    tags: [turf_war, settled_quietly, fait_accompli, public_pretense]
    incompatible_with: []
  - id: the_evidence_that_keeps_coming_back
    tags: [destroyed_evidence, recurring_object, persistent_material, returns]
    incompatible_with: []
  - id: the_witness_who_was_the_perpetrator
    tags: [witness, hidden_role, inverting_testimony, complicit_witness]
    incompatible_with: []
  - id: the_judge_with_two_verdicts
    tags: [judge, sealed_verdict, dual_record, courthouse_secret]
    incompatible_with: []
  - id: the_racket_that_is_also_a_service
    tags: [racket, working_service, institutional_care, extortion_and_aid]
    incompatible_with: []
  - id: the_union_that_voted_against_itself
    tags: [union, manipulated_vote, members_betrayed, rigged_referendum]
    incompatible_with: []
  - id: the_cop_who_keeps_his_cut_in_a_church_envelope
    tags: [cop, tithe, clean_dirty_mix, ritualized_corruption]
    incompatible_with: []
  - id: the_shakedown_that_keeps_hands_off_the_one_thing
    tags: [shakedown, off_limits_item, protected_secret, named_leverage]
    incompatible_with: []
  - id: the_ward_boss_who_will_not_say_your_fathers_name
    tags: [ward_boss, family_secret, held_name, forbearance_as_threat]
    incompatible_with: []
  - id: the_suppression_that_targets_the_witness_not_the_evidence
    tags: [suppression, witness_targeted, evidence_preserved, threat_to_person]
    incompatible_with: []
```

**Arc axes:**
- `the_reform_that_was_the_trap` → reform_was_the_trap
- `the_rot_that_passes_for_weather` → conspiracy_inertia
- `the_loyalty_that_costs_more_than_betrayal` → loyalty_costs_more_than_betrayal
- `the_story_the_paper_already_wrote_before_it_happened` → record_doesnt_match
- `the_turf_war_no_one_will_admit_is_over` → truth_everyone_knows
- `the_evidence_that_keeps_coming_back` → thing_that_keeps_coming_back
- `the_witness_who_was_the_perpetrator` → witness_is_perpetrator
- `the_judge_with_two_verdicts` → clean_one_is_the_problem
- `the_racket_that_is_also_a_service` → genuine_thing_in_corrupt_room
- `the_union_that_voted_against_itself` → victim_engineered_it
- `the_cop_who_keeps_his_cut_in_a_church_envelope` → mercy_that_was_cruelty
- `the_shakedown_that_keeps_hands_off_the_one_thing` → love_is_also_blackmail
- `the_ward_boss_who_will_not_say_your_fathers_name` → squad_held_by_secret
- `the_suppression_that_targets_the_witness_not_the_evidence` → debt_paid_in_whoever_else

**Character dynamics (count=8):**

```yaml
character_dynamics:
  - id: cop_with_one_clean_case_left
    tags: [police, single_clean_record, last_integrity, isolated_loyalty]
    incompatible_with: [the_one_outsider_the_city_lets_in, free_agent_who_keeps_getting_handed_the_same_case]
  - id: the_one_outsider_the_city_lets_in
    tags: [outsider, permitted_access, city_consent, conditional_inside]
    incompatible_with: [cop_with_one_clean_case_left, professional_who_already_paid_off_the_debt]
  - id: professional_who_already_paid_off_the_debt
    tags: [professional, paid_in_full, prior_compromise, settled_account]
    incompatible_with: [the_one_outsider_the_city_lets_in, free_agent_who_keeps_getting_handed_the_same_case]
  - id: broker_who_believes_their_own_lies
    tags: [broker, internalized_cover, self_deception, information_economy]
    incompatible_with: []
  - id: authority_who_fears_their_own_rank
    tags: [authority, rank_burden, promotion_trap, command_fear]
    incompatible_with: [the_one_outsider_the_city_lets_in, free_agent_who_keeps_getting_handed_the_same_case]
  - id: the_reformed_something
    tags: [reformed, former_role, displaced_identity, prior_life]
    incompatible_with: []
  - id: the_one_witness_left_breathing
    tags: [witness, sole_survivor, kept_alive, conditional_life]
    incompatible_with: []
  - id: free_agent_who_keeps_getting_handed_the_same_case
    tags: [independent, recurring_assignment, unsought_specialty, returned_work]
    incompatible_with: [cop_with_one_clean_case_left, authority_who_fears_their_own_rank]
```

**Dynamic axes:**
- `cop_with_one_clean_case_left` → clean_one_is_the_problem
- `the_one_outsider_the_city_lets_in` → institution_as_antagonist
- `professional_who_already_paid_off_the_debt` → loyalty_costs_more_than_betrayal
- `broker_who_believes_their_own_lies` → truth_everyone_knows
- `authority_who_fears_their_own_rank` → reform_was_the_trap
- `the_reformed_something` → squad_held_by_secret
- `the_one_witness_left_breathing` → witness_is_perpetrator
- `free_agent_who_keeps_getting_handed_the_same_case` → thing_that_keeps_coming_back

**NPC bonds (count=8):**

```yaml
npc_bonds:
  - id: former_partner
    tags: [partnership, recurrence, unfinished_case]
    description: The NPC was the PC's detective partner before the split — they know each other's tells, codes, and the case that ended the partnership. That case is back on one of their desks; neither will say which one of them wanted the other to take it.
  - id: corrupted_witness
    tags: [testimony, bribery, mutual_complicity, recurring_pressure]
    description: The NPC was a witness in a case the PC worked; the PC paid to make the testimony fall apart. Now the witness wants paying again, and the price is no longer money. The proof of the bond is the crime.
  - id: old_war_buddy
    tags: [war, veteran, shared_change, mutual_silence]
    description: The NPC served in the same unit as the PC overseas. One of them came back different; both know which one. Neither has said since.
  - id: locked_up_together
    tags: [prison, sacrifice, unequal_sentence, unspoken_debt]
    description: The NPC and PC shared a cell block — and at sentencing the NPC took the months that should have been the PC's. They've both been out for years. Neither mentions it.
  - id: debt_to_informant
    tags: [informant, love_as_leverage, escalating_debt, dependency]
    description: The NPC is a former informant who saved the PC's skin on a dockyard case. The informant loves the PC, which is why the favor keeps getting called in, and why each call costs more than the last.
  - id: childhood_friend
    tags: [childhood, prior_self, exposed_continuity, vulnerability]
    description: The NPC grew up with the PC on the same streets and got out a different way. They are the only person in the city who knew the PC before the city made the PC what the PC is. Their continued existence is the PC's exposure.
  - id: family_connection
    tags: [family, prior_cover, debt_repayment, loved_target]
    description: The NPC is connected to the PC through family — and the family once covered for the PC, which the PC will now be asked to repay against someone the PC loves more.
  - id: case_from_before
    tags: [prior_case, polite_enmity, shared_record, known_history]
    description: The NPC and PC crossed paths on a previous case — one helped, one hindered. Both know perfectly well which did which. Both intend to keep pretending it's a polite question when they meet again.
```

**Bond axes (the cost structure each bond charges against):**
- `former_partner` → reunion_pretending_not_to_know
- `corrupted_witness` → bond_whose_proof_is_crime
- `old_war_buddy` → squad_held_by_secret
- `locked_up_together` → debt_paid_in_whoever_else
- `debt_to_informant` → love_is_also_blackmail
- `childhood_friend` → genuine_thing_in_corrupt_room
- `family_connection` → mercy_that_was_cruelty
- `case_from_before` → truth_everyone_knows

**Scene detail bundles (count=7):**

```yaml
scene_detail_bundles:
  - id: back_alley
    items: [a fire escape ladder bolted to the brickwork, a payphone with the receiver dangling, a child's shoe placed sole-up beneath the dial]
    conditions: [wet from last night's rain, the streetlamp out]
    sensory: [the hiss of a flickering neon sign, footsteps echoing from the next block]
  - id: police_precinct
    items: [a typewriter with a stuck 'e' key, a filing cabinet with the bottom drawer padlocked, a duty board with one name scraped off with a knife — the names above and below are clean]
    conditions: [the floor slick from tracked-in rain, smoke hanging under the ceiling lights]
    sensory: [the clatter of a teletype machine, the smell of stale coffee and cheap tobacco]
  - id: speakeasy
    items: [a brass rail worn smooth by shoe leather, a glass with lipstick on the rim, a phonograph cylinder labeled in a hand the PC recognizes as their mother's]
    conditions: [the room hazy with cigarette smoke, the music from the phonograph skipping]
    sensory: [the low laughter from a back room, the clink of glasses behind the bar]
  - id: hotel_room
    items: [a telephone with the cord cut, a hat left on the bedpost, a second hat on the other bedpost identical to the PC's — which the PC has not yet removed from their own head]
    conditions: [the radiator knocking, the window onto a fire escape that doesn't reach the ground]
    sensory: [the drip of a leaky faucet, voices from the room next door through thin walls]
  - id: dockyard
    items: [a crane with its load suspended halfway, a Customs manifest page folded into a paper bird and set on the bollard]
    conditions: [thick fog rolling off the water, the pier slick with oil]
    sensory: [the clang of metal on metal from a warehouse, the deep horn of a departing freighter]
  - id: rooftop_chase
    items: [a water tower with a loose ladder, a fire escape that ends six feet short]
    conditions: [the tar roof blistering in the sun, the gap between buildings wider than it looks, the ladder's rungs missing every third one in a pattern as if someone climbed who already knew]
    sensory: [the wail of a siren from the street below, the clatter of a loose antenna in the wind]
  - id: morgue_basement
    items: [a body drawer half-open with a tag attached, a dictaphone with a half-finished recording, a toe tag written out with the PC's home address]
    conditions: [the fluorescent light buzzing, the floor drain stained]
    sensory: [the sharp smell of formaldehyde, the hum of the refrigeration unit]
```

**Scene wrong-detail registers (all distinct):**
- `back_alley` → personal_artifact (the placed shoe)
- `police_precinct` → procedural_impossible (the singled-out scraped name)
- `speakeasy` → supernatural_tangential (mother's labeled cylinder)
- `hotel_room` → temporal_dislocated (the second identical hat)
- `dockyard` → transformational (the folded paper bird replacing the torn page)
- `rooftop_chase` → patterned_impossible (every-third-rung missing)
- `morgue_basement` → identificatory (PC's home address on the toe tag)

**PC situation schema (count=4):**

```yaml
pc_situation_schema:
  - key: the_address_you_dont_give_cabbies
    description: Where does the PC actually sleep, and why won't they say it to a stranger? (Apartment, boarding house, hotel room — and what the silence around the address is for.)
    required: false
    persist: true
  - key: the_room_where_you_take_cases_you_shouldnt
    description: Where does the PC take the work they won't take downtown — what's painted on the door, and what's not on the lease?
    required: false
    persist: true
  - key: the_name_the_city_uses_for_you_when_its_talking_to_itself
    description: Not how cops greet the PC to their face, but what the city calls the PC when the city is talking to itself.
    required: false
  - key: the_people_who_would_be_safer_if_you_hadnt_known_them
    description: Whose name has been made more dangerous by association with the PC? (Family, lover, partner, witness — and which of them is still alive.)
    required: false
```

**PC schema wound directions (all distinct):**
- `the_address_you_dont_give_cabbies` → place
- `the_room_where_you_take_cases_you_shouldnt` → vocation
- `the_name_the_city_uses_for_you_when_its_talking_to_itself` → name
- `the_people_who_would_be_safer_if_you_hadnt_known_them` → love

---

### 2. Zombie Survival — Cordyceps: Year Twenty

**Posture:** last-humans-vs-monsters, infected-as-enemy, fortress-as-salvation, survival-as-fight. Each entry subverts a different piece.

**World bible (new — to be written into `packs/default/zombie-survival/world.md`):**

```md
# World Bible — Cordyceps: Year Twenty

The infection called Ophiocordyceps novum is not the enemy; it is the weather. Twenty years on, the infected are not undead — they are the Comes-Back, sometimes called. The Clickers, Stalkers, and Runners are partly the people they were; the Stalkers watch because they remember why they came. The horror is recognition, not monstrosity.

Every survivor over the age of reason is guilty of something specific. Settlements are not shelters; they are confederations of guilt, holding together because the alternative is confessing what each member did to still be alive. The mycelium is organizing, not just spreading — abandoned subway lines rerouted into something like roads, the city being reshaped by something that knows what a road is for. The infected are not the threat. The living are.
```

**World facts (sharpened, 3):**
1. The infection is no longer a plague to be survived; it is a rearranged ecosystem the survivors must live inside, and the infected are partly the people they were.
2. Settlements persist as confederations of guilt — each member did something to still be here, and the settlement holds because admitting the alternative is the death of the group.
3. The mycelium is not spreading randomly; it is organizing. Roads form where there were none. The infected gather in patterns that resemble congregation more than hunt.

**Baseline facts (sharpened, 3):**
1. Ophiocordyceps novum spreads via airborne spores in enclosed or still air; outdoors is wind-dependent; a sealed mask buys twenty minutes against a two-hour conversion; masks are harder to find than bullets.
2. The infected are not mindless — Clickers echolocate with skull-bloomed faces, Stalkers watch and wait because they remember why they came, Runners hesitate at the scent of those they loved. The hesitation is the worst thing. They are all connected by an underground mycelial network that remembers what they chose to forget.
3. Twenty years on, the cities are forests — roots cracked foundations, vines collapsed floors, rivers rerouted through subways. The infrastructure is not decayed; it is being organized into something. The city is a living, hostile landscape that knows what a road is for.

**Situation archetypes (count=10):**

```yaml
situation_archetypes:
  - id: the_well_that_drinks_people
    tags: [water_source, tainted_ground, slow_death, kept_mercy]
    incompatible_with: []
  - id: the_mother_who_rations_her_own_child_last
    tags: [ration_order, family_secret, public_kindness_private_cruelty]
    incompatible_with: []
  - id: the_uninfected_quarantine
    tags: [unbitten_survivor, record_of_survival, quarantined_clean]
    incompatible_with: []
  - id: the_winter_we_ate_the_seed_corn
    tags: [consumed_future, spring_came, no_crop_now, fait_accompli]
    incompatible_with: []
  - id: the_council_that_keeps_voting_the_way_the_gun_wants
    tags: [gun_council, voted_vote, coerced_democracy, armed_quorum]
    incompatible_with: []
  - id: the_settlement_that_wasnt_supposed_to_still_be_there
    tags: [off_map, smoke_says_otherwise, unrecognized_survivor]
    incompatible_with: []
  - id: the_two_settlements_that_share_a_wall
    tags: [shared_wall, mutual_misread, mirror_threat, divided_perception]
    incompatible_with: []
  - id: the_gates_that_someone_keeps_opening
    tags: [gates_opening, inside_saboteur, not_infected, nominate_within]
    incompatible_with: []
  - id: the_gospel_of_the_bloom
    tags: [voluntary_infection, infect_as_worship, bloom_recruitment]
    incompatible_with: []
  - id: the_child_who_remembers_the_before
    tags: [child_memory, before_world_knowledge, untaught_recollection]
    incompatible_with: []
```

**Situation axes:**
- `the_well_that_drinks_people` → cruelty_that_was_mercy
- `the_mother_who_rations_her_own_child_last` → mercy_that_was_cruelty
- `the_uninfected_quarantine` → clean_one_is_the_problem
- `the_winter_we_ate_the_seed_corn` → decision_already_made
- `the_council_that_keeps_voting_the_way_the_gun_wants` → institution_as_antagonist
- `the_settlement_that_wasnt_supposed_to_still_be_there` → place_that_wasnt_supposed_to_be_there
- `the_two_settlements_that_share_a_wall` → conspiracy_inertia
- `the_gates_that_someone_keeps_opening` → witness_is_perpetrator
- `the_gospel_of_the_bloom` → gospel_of_the_bloom
- `the_child_who_remembers_the_before` → child_who_remembers

**Arc categories (count=14):**

```yaml
arc_categories:
  - id: the_quiet_coup_with_a_gun_at_the_family
    tags: [coup, family_pressure, coerced_authority, settled_force]
    incompatible_with: []
  - id: the_hunger_you_can_walk_faster_than
    tags: [hunger, walking_away_consequence, slow_catch, future_cost]
    incompatible_with: []
  - id: the_reunion_of_people_who_pretend_they_dont_know_each_other
    tags: [reunion, denied_acquaintance, false_strangers, common_past]
    incompatible_with: []
  - id: the_return_of_the_unburied
    tags: [unburied, returned_body, missing_rites, bloom_returns_dead]
    incompatible_with: []
  - id: the_bloom_that_learns_to_wait
    tags: [bloom_learns, patient_infection, deferred_bloom, network_intelligence]
    incompatible_with: []
  - id: the_quarantine_that_was_already_broken
    tags: [broken_quarantine, silent_breach, known_inside, kept_secret]
    incompatible_with: []
  - id: the_vote_no_one_will_hold_while_the_food_is_low
    tags: [delayed_vote, food_pressure, deferred_governance, food_before_consent]
    incompatible_with: []
  - id: the_thing_everyone_did_that_no_one_names
    tags: [shared_thing, collective_unspoken, common_act, named_aloud_breach]
    incompatible_with: []
  - id: the_supply_route_that_came_back_under_a_different_name
    tags: [route_returned, renamed_route, recurring_supply, false_newness]
    incompatible_with: []
  - id: the_leader_who_stepped_down_voluntarily
    tags: [leader_quit, voluntary_resignation, gun_behind_them, succession_pressure]
    incompatible_with: []
  - id: the_pact_with_the_both_sides_true
    tags: [shared_lie, mutual_covered, both_protecting, two_guilties]
    incompatible_with: []
  - id: the_child_who_says_the_names_aloud
    tags: [child_recites, untaught_names, named_unburied, refuses_silence]
    incompatible_with: []
  - id: the_quarantine_that_was_supposed_to_keep_them_in
    tags: [quarantine_inverted, kept_inside, kept_from_leaving, kept_safe_or_kept]
    incompatible_with: []
  - id: the_returning_one_brought_something_back
    tags: [returned_brought, follower_return, came_back_with, returned_with_other]
    incompatible_with: []
```

**Arc axes:**
- `the_quiet_coup_with_a_gun_at_the_family` → institution_as_antagonist
- `the_hunger_you_can_walk_faster_than` → decision_already_made
- `the_reunion_of_people_who_pretend_they_dont_know_each_other` → reunion_pretending_not_to_know
- `the_return_of_the_unburied` → bloom_that_learns
- `the_bloom_that_learns_to_wait` → bloom_that_learns — **duplicate axis within pool** ⚠ see revision below
- `the_quarantine_that_was_already_broken` → truth_everyone_knows
- `the_vote_no_one_will_hold_while_the_food_is_low` → reform_was_the_trap
- `the_thing_everyone_did_that_no_one_names` → squad_held_by_secret
- `the_supply_route_that_came_back_under_a_different_name` → thing_that_keeps_coming_back
- `the_leader_who_stepped_down_voluntarily` → reform_was_the_trap — **duplicate axis within pool** ⚠ see revision below
- `the_pact_with_the_both_sides_true` → genuine_thing_in_corrupt_room
- `the_child_who_says_the_names_aloud` → child_who_remembers
- `the_quarantine_that_was_supposed_to_keep_them_in` → innocent_who_is_guilty
- `the_returning_one_brought_something_back` → place_that_wasnt_supposed_to_be_there

**Axis collision revision (zombie arcs):** Two duplicate axes detected within pool — `the_bloom_that_learns_to_wait` and `the_return_of_the_unburied` both annotated `bloom_that_learns`; `the_leader_who_stepped_down_voluntarily` and `the_vote_no_one_will_hold_while_the_food_is_low` both `reform_was_the_trap`. Recast:
- `the_return_of_the_unburied` → **victim_engineered_it** (the unburied were not lost; they were given back).
- `the_leader_who_stepped_down_voluntarily` → **mercy_that_was_cruelty** (their resignation was a kindness that cost the settlement its only truth-teller).

After revision, all 14 arc axes are distinct within the pool.

**Character dynamics (count=8):**

```yaml
character_dynamics:
  - id: the_one_who_keeps_the_settlements_secret
    tags: [secret_keeper, settlement_conscience, burdened_keeper, compromised_confidant]
    incompatible_with: [the_one_the_settlement_does_not_admit_it_exiled, the_one_who_buried_the_first_dead]
  - id: the_one_who_knows_where_the_roads_go
    tags: [mycelium_roads, knows_routes, has_traveled, comes_back_mapping]
    incompatible_with: [the_one_who_keeps_the_settlements_secret, the_leader_who_stepped_down_voluntarily]
  - id: the_one_who_says_aloud_that_the_founder_failed
    tags: [founder_failure, public_naming, breaks_silence, uneasy_truth]
    incompatible_with: [the_one_who_buried_the_first_dead]
  - id: the_leader_who_stepped_down_voluntarily
    tags: [ex_leader, voluntary_resignation, gun_resignation, displaced_conscience]
    incompatible_with: [the_one_who_keeps_the_settlements_secret, the_one_who_buried_the_first_dead]
  - id: the_one_the_settlement_does_not_admit_it_exiled
    tags: [exiled_unacknowledged, returned_unofficially, denied_banishment, faces_back]
    incompatible_with: [the_one_who_keeps_the_settlements_secret, the_one_who_knows_where_the_roads_go]
  - id: the_quartermaster_who_knows_the_real_numbers
    tags: [quartermaster, real_numbers, hidden_ledger, count_against_words]
    incompatible_with: []
  - id: the_returning_one
    tags: [returning, left_came_back, returned_with_other, left_behind_now_back]
    incompatible_with: []
  - id: the_one_who_buried_the_first_dead
    tags: [first_burial, unrepeatable_rite, original_grave, singular_duty]
    incompatible_with: [the_one_who_keeps_the_settlements_secret]
```

**Dynamic axes:**
- `the_one_who_keeps_the_settlements_secret` → squad_held_by_secret
- `the_one_who_knows_where_the_roads_go` → bloom_that_learns
- `the_one_who_says_aloud_that_the_founder_failed` → truth_everyone_knows
- `the_leader_who_stepped_down_voluntarily` → reform_was_the_trap
- `the_one_the_settlement_does_not_admit_it_exiled` → reunion_pretending_not_to_know
- `the_quartermaster_who_knows_the_real_numbers` → clean_one_is_the_problem
- `the_returning_one` → place_that_wasnt_supposed_to_be_there
- `the_one_who_buried_the_first_dead` → mercy_that_was_cruelty

**NPC bonds (count=8):**

```yaml
npc_bonds:
  - id: saved_from_infected
    tags: [rescue, displaced_cost, secret_life_debt, hidden_payment]
    description: The NPC pulled the PC out of a horde encounter. The debt is not discussed. The repayment was someone else's life; that person does not know.
  - id: lost_child_found
    tags: [found_child, false_match, protective_pretense, mutual_complicity]
    description: The NPC is a child the PC found and has been protecting. The child is not the child the PC was looking for. The child knows this. The child is pretending not to.
  - id: ration_debt
    tags: [winter_debt, witnessed_theft, kept_secret, ration_origin]
    description: The NPC kept the PC alive through a bad winter by sharing rations — and the ration the NPC shared was a theft the PC witnessed and did not report, which is the proof of the bond.
  - id: faction_double_agent
    tags: [double_agent, faction_knows, undecided_faction, personal_across_line]
    description: The NPC is part of a faction the PC distrusts. The faction knows the bond is there; the faction has not decided what to do with that knowledge yet, and the NPC knows that the faction has not decided.
  - id: held_a_gate_together
    tags: [shared_defense, one_held_one_ran, both_alive, mutual_witness]
    description: The NPC and PC once held a breach together while others fled. One of them held; one of them ran. Both are alive. Both know which one did which.
  - id: settlement_founder
    tags: [founder, displaced_builder, continuation_threat, lost_control]
    description: The NPC helped build the settlement the PC lives in — dug the first well, stood the first wall, buried the first dead. Whoever took the settlement took it from them; their continued existence is now the threat to that person.
  - id: scavenging_partner
    tags: [scavenging, mutual_origin_knowledge, unspoken_source, shared_secret]
    description: The NPC has run dozens of scavenging runs with the PC. Both know where the things they scavenged came from. Neither says.
  - id: before_world_neighbor
    tags: [before_world, mutual_recognition, pretended_strangers, chosen_anonymity]
    description: The NPC lived three doors down from the PC before the collapse. Both remember each other's before-names. Both pretend not to recognize each other — because the things they did to survive are easier done among strangers.
```

**Bond axes (cost structures):**
- `saved_from_infected` → debt_paid_in_whoever_else
- `lost_child_found` → child_who_doesnt_but_pretends
- `ration_debt` → bond_whose_proof_is_crime
- `faction_double_agent` → love_is_also_blackmail
- `held_a_gate_together` → squad_held_by_secret
- `settlement_founder` → genuine_thing_in_corrupt_room
- `scavenging_partner` → witness_is_perpetrator
- `before_world_neighbor` → reunion_pretending_not_to_know

**Scene detail bundles (count=7):**

```yaml
scene_detail_bundles:
  - id: abandoned_hospital
    items: [a gurney with torn restraints, a syringe half-filled with something dark, a wall calendar with today's date circled in fresh ink]
    conditions: [the power flickering on backup battery, patient charts water-damaged into illegibility]
    sensory: [the hum of a surgical light on backup power, the smell of rot from a locked ward]
  - id: settlement_wall
    items: [a guard post with a periscope and a cracked optic, a cache of molotov cocktails wrapped in newspaper]
    conditions: [the wall patched in three places, gravel piled for quick fills, a name carved into the inside of the wall and defaced]
    sensory: [the constant low moan from beyond the wall, the creak of the watchtower ladder under weight]
  - id: overgrown_street
    items: [a burned-out car with saplings growing through the chassis, a row of mailboxes all still labeled and still being filled, a crate of bottled water]
    conditions: [a mattress dragged halfway across the intersection, the grocery store windows boarded but the door swinging]
    sensory: [the buzz of flies over something unseen, glass crunching underfoot with every step]
  - id: underground_bunker
    items: [a military radio tuned to static, a loaded pistol left on the table, a chair still warm with no one sitting in it]
    conditions: [the water filtration pump with a cracked housing, the air stale and metallic]
    sensory: [the echo of footsteps down the corridor, the drip of condensation from a pipe overhead]
  - id: quarantine_zone
    items: [a decontamination tent with the flap torn, a loudspeaker on a pole repeating a recorded warning]
    conditions: [the fence layered with biohazard tape, the bedding pile abandoned, the warning loop in a voice the PC recognizes]
    sensory: [the endless loop of a recorded warning echoing off concrete, the acrid smell of bleach concentrate]
  - id: radio_station
    items: [a broadcast microphone with the foam chewed off, a stack of records with hand-painted labels, a child's drawing pinned to the wall — the family in it has too many members]
    conditions: [the window boarded but light coming through the cracks, the transmitter humming but untuned]
    sensory: [the crackle of static, the echo of footsteps on the tiled floor]
  - id: farm_outskirts
    items: [a tractor with the battery pulled, a root cellar door bolted from the outside]
    conditions: [the field overgrown with thistle, the fence line down in three places, the cattle arranged in a circle standing dead]
    sensory: [the low of cattle left untended, the rustle of dry corn stalks in the wind]
```

**Scene wrong-detail registers (all distinct):**
- `abandoned_hospital` → temporal_dislocated (today's date circled in fresh ink)
- `settlement_wall` → identificatory (defaced name carved on inside)
- `overgrown_street` → procedural_impossible (mail still being filled)
- `underground_bunker` → temporal_dislocated_replacement (warm chair) ⚠ sees `temporal_dislocated` already used; recast → **presence_implied** (warm chair without body)
- `quarantine_zone` → personal_recognition (known voice on warning loop)
- `radio_station` → child_who_remembers (family drawing with too many members)
- `farm_outskirts` → patterned_impossible (cattle arranged in a circle, dead standing)

Revised registers (all distinct): temporal_dislocated, identificatory, procedural_impossible, presence_implied, personal_recognition, child_who_remembers, patterned_impossible.

**PC situation schema (count=4):**

```yaml
pc_situation_schema:
  - key: the_settlement_that_does_not_know_what_you_did_before_you_came
    description: The settlement the PC lives in does not know what the PC did to get there. What did the PC do, and why have they not said it?
    required: false
    persist: true
  - key: the_vehicle_you_did_not_earn
    description: The PC has a vehicle — a bike, a truck, a horse, a working pair of boots. How did the PC come by it, and what happened to the person who had it before?
    required: false
    persist: true
  - key: the_place_you_left_in_a_hurry
    description: What did the PC leave behind to come here — and is whatever chased the PC out of there still following, still searching, or already inside this place?
    required: false
  - key: the_person_you_are_going_to_find_dead_or_kill
    description: One name. The PC already knows whether they are going to find this person dead, kill them, or be killed trying. Which is it, and do they have it right?
    required: false
```

**PC schema wound directions (all distinct):**
- `the_settlement_that_does_not_know_what_you_did_before_you_came` → arrival
- `the_vehicle_you_did_not_earn` → possession
- `the_place_you_left_in_a_hurry` → origin
- `the_person_you_are_going_to_find_dead_or_kill` → intention

---

### 3. Space Western — The Outer Rim After Unification

**Posture:** plucky-underdog-Rim, evil-Coalition, Browncoat-as-nostalgia, Companion-Guild-as-glamorous, frontier-as-romantic. Each entry subverts a different piece.

**World bible (new — to be written into `packs/default/space-western/world.md`):**

```md
# World Bible — The Outer Rim After Unification

The war didn't end twelve years ago; it went quiet. The Coalition took the inner worlds and left the Rim as the loser's hospital — the place that lost a war and is still pretending it didn't. The Coalition is not evil; it is tired, and tired empires do worse things than evil ones. The patrols still run on inertia; no one in the inner systems can quite remember why.

The Companion Guild is a regulated trade whose members are licensed, not glamorous. The licenses are property. The Rim is held together by name-debts, not loyalty — names kept by other people because the bearer cannot afford to carry their own.
```

**World facts (sharpened, 3):**
1. Humanity is spread across scattered colonies with no central authority and no reliable communication; the Coalition holds the inner systems on inertia and the outer systems survive on scavenging, growing, and fighting.
2. Space travel is dangerous, expensive, and unpredictable — jump drives misfire, supply runs take weeks, and the Coalition has stopped quite knowing why it patrols.
3. Frontier worlds operate by their own rules; whoever controls the resources governs, and resources are disappearing from surveys that once certified them present.

**Baseline facts (sharpened, 3):**
1. The Rim is not the frontier of dust, debt, and old loyalties — it is the loser's hospital. Twelve years after the war ended, people here are stubborn, resourceful, and suspicious of inner-worlders because they lost, they remember that they lost, and pretending they didn't is the work of every day.
2. The ship is everything — home, livelihood, and the only way out. Every pilot loves their vessel and has modifications keeping it flying; a broken ship is a death sentence, and the love is therefore also the fear.
3. Frontier danger is people — rival crews, hostile settlements, Coalition patrols running on inertia, harsh environment. The storm kills as fast as a plasma bolt, and no one in the inner systems can remember anymore why the patrols are still running.

**Situation archetypes (count=12):**

```yaml
situation_archetypes:
  - id: inspection_with_a_warrant_that_names_you
    tags: [inspection, warrant_with_name, prior_known, prearrived_authority]
    incompatible_with: []
  - id: standoff_over_a_dead_mans_debt
    tags: [standoff, dead_owed, transferred_debt, saloon_quiet]
    incompatible_with: []
  - id: the_coordinates_someone_died_to_send_you
    tags: [transmitted_coords, dying_message, chose_recipient, unsought_inheritance]
    incompatible_with: []
  - id: the_settlement_the_coalition_decommissioned
    tags: [decommissioned_settlement, still_occupied, official_empty, lived_in_paper]
    incompatible_with: []
  - id: crossing_with_someone_the_coalition_wants_back
    tags: [crossing_passenger, wanted_back, supposed_clear, absolved_unclear]
    incompatible_with: []
  - id: firefight_over_the_ore_that_was_supposed_to_be_depleted
    tags: [depleted_lie, active_mine, survey_false, profitable_quiet]
    incompatible_with: []
  - id: ambush_that_looks_too_well_planned_to_be_bandits
    tags: [well_planned_ambush, uniform_information, institutional_hand, false_bandit]
    incompatible_with: []
  - id: outpost_that_keeps_sending_signal_after_everyone_is_dead
    tags: [dead_outpost, ongoing_signal, posthumous_beacon, handless_transmit]
    incompatible_with: []
  - id: the_pardon_someone_keeps_offering
    tags: [recurring_pardon, kept_offered, refusing_amnesty, named_offer]
    incompatible_with: []
  - id: the_browncoat_who_does_not_age
    tags: [browncoat, unaged, war_record_unread, body_year_mismatch]
    incompatible_with: []
  - id: the_companion_whose_registry_has_someone_elses_name_on_purpose
    tags: [companion, registry_swap, guild_approved, assumed_license]
    incompatible_with: []
  - id: the_freighter_that_was_supposed_to_have_been_recovered_last_year
    tags: [recovered_on_paper, still_here, official_salvage_log, false_wreck_tidy]
    incompatible_with: []
```

**Situation axes:**
- `inspection_with_a_warrant_that_names_you` → decision_already_made
- `standoff_over_a_dead_mans_debt` → debt_paid_in_whoever_else
- `the_coordinates_someone_died_to_send_you` → squad_held_by_secret
- `the_settlement_the_coalition_decommissioned` → occupation_forgot_why
- `crossing_with_someone_the_coalition_wants_back` → innocent_who_is_guilty
- `firefight_over_the_ore_that_was_supposed_to_be_depleted` → truth_everyone_knows
- `ambush_that_looks_too_well_planned_to_be_bandits` → institution_as_antagonist
- `outpost_that_keeps_sending_signal_after_everyone_is_dead` → dead_still_writing
- `the_pardon_someone_keeps_offering` → pardon_kept_offered
- `the_browncoat_who_does_not_age` → place_that_was_supposed_to_be_and_isnt
- `the_companion_whose_registry_has_someone_elses_name_on_purpose` → guild_sells_members
- `the_freighter_that_was_supposed_to_have_been_recovered_last_year` → place_that_was_supposed_to_be_and_isnt — **duplicate axis within pool** ⚠ recast
  - Recast: `the_browncoat_who_does_not_age` → **war_that_will_not_be_over** (in the body of someone who should be older).
  - Now both freighter and freighter-slot axes resolve.
  - Final: `the_browncoat_who_does_not_age` → war_that_will_not_be_over; `the_freighter_that_was_supposed_to_have_been_recovered_last_year` → place_that_was_supposed_to_be_and_isnt.

After revision, all 12 situation axes are distinct within the pool.

**Arc categories (count=14):**

```yaml
arc_categories:
  - id: the_war_that_refuses_to_be_over
    tags: [unfinished_war, body_keeps_score, generation_quiet, continuing_loss]
    incompatible_with: []
  - id: the_deed_signed_in_a_dead_language
    tags: [deed, dead_language, signed_dispatch, prior_author]
    incompatible_with: []
  - id: the_rebellion_that_already_lost_and_will_not_admit_it
    tags: [rebellion_denial, pretense_continues, lost_still_fought, mutual_performance]
    incompatible_with: []
  - id: the_occupation_that_forgot_why_it_came
    tags: [occupation_inertia, forgotten_reason, patrols_continue, reasons_lost]
    incompatible_with: []
  - id: the_guild_that_sells_its_members_as_licenses
    tags: [guild, members_as_property, license_transferable, body_as_license]
    incompatible_with: []
  - id: the_world_that_was_supposed_to_be_habitable
    tags: [terraforming_failed, survey_lie, supposed_habitable, scheduled_abandon]
    incompatible_with: []
  - id: the_settlement_the_charter_uses_to_count_someone_as_dead
    tags: [charter_dead, living_counted_dead, paper_death, ongoing_life]
    incompatible_with: []
  - id: the_partisans_who_keep_each_other_in_old_rosters
    tags: [partisan_roster, kept_enrolled, mutual_enrollment, never_discharged]
    incompatible_with: []
  - id: the_route_that_closed_because_someone_died_to_open_it
    tags: [closed_route, opening_death, debt_for_passage, route_memory]
    incompatible_with: []
  - id: the_pardon_the_crew_keeps_voting_to_refuse
    tags: [pardon_vote, voting_refusal, recurring_refusal, collective_amnesty_rejection]
    incompatible_with: []
  - id: the_corporate_survey_that_keeps_coming_back_corrected
    tags: [corrected_survey, recurring_revision, paper_correction, hidden_resource]
    incompatible_with: []
  - id: the_militia_assembled_to_protect_a_debt
    tags: [militia_debt, armed_collection, debt_enforcement, owed_gun]
    incompatible_with: []
  - id: the_resource_that_was_never_supposed_to_be_there
    tags: [impossible_resource, survey_omission, suppressed_finding, present_unlisted]
    incompatible_with: []
  - id: the_judge_who_is_also_a_partisan
    tags: [judge_partisan, dual_role, clean_bench_dirty_tribe, conflicted_authority]
    incompatible_with: []
```

**Arc axes:**
- `the_war_that_refuses_to_be_over` → war_that_will_not_be_over
- `the_deed_signed_in_a_dead_language` → decision_already_made
- `the_rebellion_that_already_lost_and_will_not_admit_it` → reunion_pretending_not_to_know
- `the_occupation_that_forgot_why_it_came` → occupation_forgot_why
- `the_guild_that_sells_its_members_as_licenses` → guild_sells_members
- `the_world_that_was_supposed_to_be_habitable` → place_that_was_supposed_to_be_and_isnt
- `the_settlement_the_charter_uses_to_count_someone_as_dead` → innocent_who_is_guilty
- `the_partisans_who_keep_each_other_in_old_rosters` → squad_held_by_secret
- `the_route_that_closed_because_someone_died_to_open_it` → debt_paid_in_whoever_else
- `the_pardon_the_crew_keeps_voting_to_refuse` → pardon_kept_offered
- `the_corporate_survey_that_keeps_coming_back_corrected` → thing_that_keeps_coming_back
- `the_militia_assembled_to_protect_a_debt` → bond_whose_proof_is_crime
- `the_resource_that_was_never_supposed_to_be_there` → place_that_wasnt_supposed_to_be_there
- `the_judge_who_is_also_a_partisan` → clean_one_is_the_problem

**Character dynamics (count=8):**

```yaml
character_dynamics:
  - id: veteran_who_kept_their_browncoat_in_a_box
    tags: [veteran, boxed_browncoat, folded_war, unadmitted_service]
    incompatible_with: []
  - id: deserter_who_keeps_getting_promoted_in_absentia
    tags: [deserter, absentia_promotion, parked_records, advancing_deserter]
    incompatible_with: [officer_who_did_not_retire_in_any_record]
  - id: pilot_who_owes_their_ship_to_someone_dead
    tags: [pilot, ship_debt, dead_prevowner, transferred_care]
    incompatible_with: []
  - id: companion_whose_registry_has_the_wrong_name_on_purpose
    tags: [companion, registry_swap, wrong_name_intended, guild_complicit]
    incompatible_with: []
  - id: scavenger_who_keeps_finding_their_own_abandoned_ships
    tags: [scavenger, returning_wreck, recurring_self_salvage, finds_own_history]
    incompatible_with: []
  - id: the_deputy_who_inherited_the_last_ones_secret
    tags: [deputy, inherited_secret, prior_deputy, memory_in_office]
    incompatible_with: []
  - id: the_trader_who_runs_the_route_someone_died_to_open
    tags: [trader, route_debt, died_to_open, traders_burden]
    incompatible_with: []
  - id: officer_who_did_not_retire_in_any_record
    tags: [officer, missing_record, unretired, paper_absence]
    incompatible_with: [deserter_who_keeps_getting_promoted_in_absentia]
```

**Dynamic axes:**

- `veteran_who_kept_their_browncoat_in_a_box` → reunion_pretending_not_to_know
- `deserter_who_keeps_getting_promoted_in_absentia` → occupation_forgot_why
- `pilot_who_owes_their_ship_to_someone_dead` → debt_paid_in_whoever_else
- `companion_whose_registry_has_the_wrong_name_on_purpose` → guild_sells_members
- `scavenger_who_keeps_finding_their_own_abandoned_ships` → thing_that_keeps_coming_back
- `the_deputy_who_inherited_the_last_ones_secret` → squad_held_by_secret
- `the_trader_who_runs_the_route_someone_died_to_open` → witness_is_perpetrator
- `officer_who_did_not_retire_in_any_record` → place_that_was_supposed_to_be_and_isnt

All 8 dynamic axes distinct within pool.

**NPC bonds (count=8):**

```yaml
npc_bonds:
  - id: coalition_adversary
    tags: [adversary, mutual_competence, respect_with_nowhere, post_armistice_respect]
    description: The NPC was on the opposite side of the war. The PC knows them as an adversary who earned respect through competence; the war ended; both are still competent; the respect has nowhere to go, and the competence has nothing to do.
  - id: shared_smuggling_run
    tags: [smuggling_run, unfinished_cargo, recurring_anonymous_update, mutual_liability]
    description: The NPC and PC ran a smuggling route together. The job paid but the run never finished — the cargo is still aboard somewhere, and both of them get the same anonymous updates about its location.
  - id: partisan_cell
    tags: [partisan_cell, cause_lost, mutual_pretense, kept_cell]
    description: The NPC and PC worked with the same partisan cell during the war. The cause did not outlast the armistice. The cell pretends it did, for each other, because admitting the cause is gone means admitting the people who died for it died for nothing.
  - id: smuggling_connection
    tags: [smuggling_contact, trust_broken_rebuilt, route_dependent, broken_then_repaired]
    description: The NPC was the PC's contact on a smuggling route that went bad. Trust was broken, then rebuilt — the bond is the rebuilding, and the proof of the bond is that the route still runs.
  - id: war_remnant
    tags: [war_remnant, shared_aftermath, untold_truth, silent_comrades]
    description: The NPC served in the same theater of the war as the PC. The war shaped them similarly and neither talks — not because of the war, but because of what they did after, which they also do not talk about.
  - id: old_crewmate
    tags: [crew, sacrifice, charge_displaced, self_replaced_charge]
    description: The NPC served on the same ship as the PC — not friends, but the kind of bond formed by shared cargo holds and close calls. The NPC took a charge that should have been the PC's; the PC watched them take it. The NPC remembers every day; the PC remembers every day.
  - id: the_one_who_keeps_your_real_name
    tags: [name_keeper, only_copy, leverage_love, both_kept]
    description: The NPC keeps the PC's real name — the one the PC doesn't carry anymore, because carrying it is too dangerous. The NPC is the only copy. The love and the leverage are the same thing.
  - id: the_settlement_that_uses_your_face_on_its_recruitment_poster
    tags: [recruitment_poster, used_face, unconsulted_hero, stranger_in_your_face]
    description: The NPC is from a settlement the PC does not live in — a settlement that uses the PC's face on its recruitment posters, and that has not asked the PC's permission, and that the PC has not yet had the heart to disavow in person.
```

**Bond axes (cost structures):**
- `coalition_adversary` → genuine_thing_in_corrupt_room
- `shared_smuggling_run` → thing_that_keeps_coming_back
- `partisan_cell` → reunion_pretending_not_to_know
- `smuggling_connection` → bond_whose_proof_is_crime
- `war_remnant` → squad_held_by_secret
- `old_crewmate` → debt_paid_in_whoever_else
- `the_one_who_keeps_your_real_name` → love_is_also_blackmail
- `the_settlement_that_uses_your_face_on_its_recruitment_poster` → truth_everyone_knows

**Scene detail bundles (count=7):**

```yaml
scene_detail_bundles:
  - id: cargo_bay
    items: [a grav pallet with a broken levitator, a hydro-spanner with an adaptive grip, a manifest line for one passenger not currently in the bay]
    conditions: [the bay depressurized and cold, cargo netting loose and tangled]
    sensory: [the hum of emergency lighting, the hiss of atmosphere cycling through scrubbers]
  - id: town_street
    items: [a holo-sign flickering between two advertisements, a freight droid powered down against a wall, a storefront advertising a business that closed twelve years ago with a current-hours sign in the window]
    conditions: [the street half in shadow, market stalls abandoned mid-day]
    sensory: [the buzz of faulty lighting, the distant shriek of a ship's engines atmo-burn]
  - id: saloon_interior
    items: [a card table with a marked deck in the discard, a synthesizer dispensing something brown into a chipped cup, a glass poured at the empty seat refreshed every hour]
    conditions: [smoke from a hookah hanging in the air, a back door propped open]
    sensory: [the jangle of an out-of-tune piano, the hum of a cooler unit cycling]
  - id: desert_crossing
    items: [a rusted hull fragment half-buried in the dust, a cracked oxygen mask hanging from a post]
    conditions: [the heat shimmer distorting the horizon, the trail marker knocked askew, a second set of footprints joining the PC's from a direction no one walked from]
    sensory: [the dry scrape of windblown sand, the creak of metal expanding in the heat]
  - id: mine_shaft
    items: [a drilling rig with the safety guard removed, a seismic charge with a dead trigger]
    conditions: [the ventilation fan cycling unevenly, the shaft dimly lit, scratching on the wall in a current date in a hand too small to reach]
    sensory: [the echo of dripping water from deep below, the grinding of ore carts on damaged track]
  - id: orbit_station
    items: [an airlock with a jammed seal, a terminal showing docking fees overdue, a docked ship that hasn't moved in eleven years and is still on the registry]
    conditions: [the gravity cycling on and off, the corridor dimly lit with emergency strips]
    sensory: [the low hum of the station's reactors, the click of magnetic boots on grated flooring]
  - id: repair_bay
    items: [a welding torch with a cracked lens, a diagnostic tablet showing red across the board, a tool etched with a name that matches the PC's dead sibling's]
    conditions: [the bay cold from the vacuum seal broken, tools scattered across every surface]
    sensory: [the hiss of a plasma cutter, the ozone smell of a recent electrical fire]
```

**Scene wrong-detail registers (all distinct):**
- `cargo_bay` → identificatory (manifest line for an absent passenger)
- `town_street` → temporal_dislocated (business closed 12 years ago, current hours posted)
- `saloon_interior` → ritualized_presence (refreshed glass at empty seat)
- `desert_crossing` → spatial_impossible (footprints joining from nowhere)
- `mine_shaft` → child_who_remembers (scratching in too-small hand)
- `orbit_station` → temporal_dislocated_replacement (eleven-year docked ship still registered) — recast to avoid duplication with `town_street`
  - Recast: `town_street` → **period_mismatch** (closed business with current hours — a period artifact presented as live); `orbit_station` → **temporal_dislocated** (eleven-year-registered ship).
- `repair_bay` → personal_trace (sibling's etched name)

After revision: identificatory, period_mismatch, ritualized_presence, spatial_impossible, child_who_remembers, temporal_dislocated, personal_trace — all distinct.

**PC situation schema (count=4):**

```yaml
pc_situation_schema:
  - key: the_ship_that_keeps_a_record_you_cannot_erase
    description: The PC's ship keeps something the PC cannot remove — a log entry, a hull stain, a name burned into a beam. What is it, and why can't the PC erase it?
    required: false
    persist: true
  - key: the_port_that_knows_you_under_a_name_that_isnt_yours
    description: The PC has a port that knows them by a name that is not the PC's. Whose name is it, why did the PC take it on, and who would the PC have to be to give it back?
    required: false
    persist: true
  - key: the_thing_you_did_that_a_few_hundred_rim_worlders_decided_was_heroism
    description: A few hundred Rim-worlders have decided something the PC did was heroism. What was the act, and what about it was not heroic?
    required: false
  - key: the_guild_or_flag_you_keep_pretending_you_left
    description: The PC keeps papers in their pocket from a guild or flag they claim to have left. Which is it, and what do those papers still require of the PC?
    required: false
    persist: true
```

**PC schema wound directions (all distinct):**
- `the_ship_that_keeps_a_record_you_cannot_erase` → property
- `the_port_that_knows_you_under_a_name_that_isnt_yours` → name
- `the_thing_you_did_that_a_few_hundred_rim_worlders_decided_was_heroism` → reputation
- `the_guild_or_flag_you_keep_pretending_you_left` → allegiance

---

### 4. Golden Piracy — 1715–1725

**Posture:** romantic-democracy-of-rascals, pirate-as-outlaw-hero, navy-as-villain, treasure-as-prize. Each entry subverts a different piece.

**World bible (existing — verify alignment):** `packs/default/golden-piracy/world.md` already supports Articles-as-real-pressure-test and ex-slave/transportee crews; design treats these as ONE axis among many. No changes needed.

**World facts (sharpened, 3):**
1. The seas are controlled by powerful pirate fleets and colonial navies clashing over trade routes and island holdings — and the two empires agree on one thing: people are cargo.
2. Caribbean island settlements trade in rum, spices, and stolen cargo, with loyalty bought by shares of plunder — and with the lives of those who were cargo before they were crew.
3. Mutiny is common on every vessel, captain's authority depends on keeping crew fed and motivated — and ironically the Articles hold best when the pressure on them is greatest.

**Baseline facts (sharpened, 3):**
1. The pirate ship is a democracy with a knife at its throat — the crew votes on everything and the captain is elected and deposable, but board an enemy ship and the democracy ends and the violence begins; the Articles hold best at the moment of greatest pressure, and that is the Koran of the ship.
2. Scurvy, dysentery, and infection kill more pirates than guns or hanging — no fresh meat or water and the ship is a death trap in weeks; every port stop is a race against rot. The Articles cannot vote away the ship's diet, and that is the equality no one wanted.
3. The Caribbean is a maze of hidden coves, shallow reefs, and coral harbors; the best pirates ambush, strike fast, and vanish into navy-unfollowable waters.

**Situation archetypes (count=12):**

```yaml
situation_archetypes:
  - id: mutiny_the_captain_started
    tags: [mutiny_engineered, captain_provokes, loyalty_by_survival, suspect_removal]
    incompatible_with: []
  - id: the_sick_who_wont_die_fast_enough
    tags: [sick_crew, dying_costs_less, slow_death, articles_silent]
    incompatible_with: []
  - id: treasure_that_belongs_to_someone_who_will_come_for_it
    tags: [treasure_with_owner, returning_owner, named_reclaim, claim_preexists]
    incompatible_with: []
  - id: the_human_cargo_sabotaging_itself_free
    tags: [human_cargo, self_liberation, hold_open, articles_unspoken]
    incompatible_with: []
  - id: the_blockade_registered_to_a_country_that_does_not_admit_it_exists
    tags: [unofficial_blockade, denying_flag, rowed_paper, stateless_patrol]
    incompatible_with: []
  - id: the_governor_who_rents_you_a_safe_harbor_and_reports_you_to_his_superiors
    tags: [double_dealing_governor, harbor_rent, divided_loyalty, paying_both_sides]
    incompatible_with: []
  - id: suppressing_a_mutiny_that_was_actually_a_vote
    tags: [vote_called_mutiny, articles_violation, suppression_inverted, captain_overreads]
    incompatible_with: []
  - id: fight_over_whose_name_goes_on_the_share_list_after_the_death
    tags: [share_list, dead_share, articles_silent, inheritance_disputed]
    incompatible_with: []
  - id: the_pardon_someone_offered_the_crew_but_not_the_captain
    tags: [pardon_divided, crew_amnesty, captain_excluded, divided_offer]
    incompatible_with: []
  - id: the_slaver_ship_taken_for_cargo_but_the_cargo_wont_leave
    tags: [slaver_taken, freed_refuse_leave, learn_articles, refuse_depart]
    incompatible_with: []
  - id: the_court_that_has_to_try_you_because_you_were_observed_doing_nothing
    tags: [trial_for_inaction, crime_of_witness, inaction_offense, observed_idle]
    incompatible_with: []
  - id: the_naval_engagement_you_started_by_accident
    tags: [accidental_engagement, victim_engineered, started_by_misreading, unintended_battle]
    incompatible_with: []
```

**Situation axes:**
- `mutiny_the_captain_started` → decision_already_made
- `the_sick_who_wont_die_fast_enough` → mercy_that_was_cruelty
- `treasure_that_belongs_to_someone_who_will_come_for_it` → thing_that_keeps_coming_back
- `the_human_cargo_sabotaging_itself_free` → innocent_who_is_guilty
- `the_blockade_registered_to_a_country_that_does_not_admit_it_exists` → occupation_forgot_why
- `the_governor_who_rents_you_a_safe_harbor_and_reports_you_to_his_superiors` → truth_everyone_knows
- `suppressing_a_mutiny_that_was_actually_a_vote` → reform_was_the_trap
- `fight_over_whose_name_goes_on_the_share_list_after_the_death` → debt_paid_in_whoever_else
- `the_pardon_someone_offered_the_crew_but_not_the_captain` → pardon_kept_offered
- `the_slaver_ship_taken_for_cargo_but_the_cargo_wont_leave` → human_cargo
- `the_court_that_has_to_try_you_because_you_were_observed_doing_nothing` → witness_is_perpetrator
- `the_naval_engagement_you_started_by_accident` → victim_engineered_it

**Arc categories (count=14):**

```yaml
arc_categories:
  - id: the_vote_that_keeps_happening_until_you_get_it_right
    tags: [repeated_vote, until_correct, ritual_election, consent_extracted]
    incompatible_with: []
  - id: the_repeated_votes_that_no_one_calls_a_mutiny
    tags: [votes_not_named, removed_captain, agreed_narrative, mutiny_unnamed]
    incompatible_with: []
  - id: plying_the_sea_a_free_vessel_built_off_human_cargo
    tags: [free_vessel, cargo_origin, articles_unfreed, hold_unliberated]
    incompatible_with: []
  - id: the_two_empires_that_agree_on_one_thing_people_are_cargo
    tags: [empires_agree, cargo_consensus, common_forget, body_trade]
    incompatible_with: []
  - id: the_quarrel_over_which_empire_the_pirates_will_let_use_them
    tags: [pirate_broker, empire_quarrel, sold_alignment, pirate_as_lever]
    incompatible_with: []
  - id: the_hunt_for_a_thing_someone_will_not_let_be_found
    tags: [hunt_suppressed, hidden_target, refused_recovery, kept_unfound]
    incompatible_with: []
  - id: the_wreck_that_keeps_everyone_honest_in_the_aftermath
    tags: [wreck_aftermath, enforced_honesty, shared_salvage, kept_secret_in_share]
    incompatible_with: []
  - id: the_pardon_offered_to_everyone_except_the_one_who_refused_it
    tags: [pardon_refused, excluder_themselves, exception_self_chosen, holdout_named]
    incompatible_with: []
  - id: the_disease_that_came_aboard_in_the_cargo
    tags: [disease_in_cargo, cargo_as_infection, returning_plague, hold_carrier]
    incompatible_with: []
  - id: the_sabotage_that_keeps_repairing_itself
    tags: [self_repairing_sabotage, fixed_then_again, recurring_break, handless_hand]
    incompatible_with: []
  - id: the_chase_ship_whose_orders_named_you_by_your_real_name
    tags: [chase_orders, your_real_name, file_on_you, named_target]
    incompatible_with: []
  - id: the_court_whose_judge_was_your_old_captain
    tags: [judge_old_captain, reunion_bench, trial_as_reunion, accused_recognized]
    incompatible_with: []
  - id: the_debt_in_a_currency_the_articles_did_not_recognize
    tags: [debt_unrecognized, currency_off_articles, owed_unlisted, debt_outside_charter]
    incompatible_with: []
  - id: the_crew_that_voted_to_keep_their_chains
    tags: [kept_chains, voted_for_chains, mercy_voted_cruelty, elected_subjection]
    incompatible_with: []
```

**Arc axes:**
- `the_vote_that_keeps_happening_until_you_get_it_right` → reform_was_the_trap
- `the_repeated_votes_that_no_one_calls_a_mutiny` → truth_everyone_knows
- `plying_the_sea_a_free_vessel_built_off_human_cargo` → human_cargo
- `the_two_empires_that_agree_on_one_thing_people_are_cargo` → conspiracy_inertia
- `the_quarrel_over_which_empire_the_pirates_will_let_use_them` → occupation_forgot_why
- `the_hunt_for_a_thing_someone_will_not_let_be_found` → innocent_who_is_guilty
- `the_wreck_that_keeps_everyone_honest_in_the_aftermath` → squad_held_by_secret
- `the_pardon_offered_to_everyone_except_the_one_who_refused_it` → pardon_kept_offered
- `the_disease_that_came_aboard_in_the_cargo` → thing_that_keeps_coming_back
- `the_sabotage_that_keeps_repairing_itself` → victim_engineered_it
- `the_chase_ship_whose_orders_named_you_by_your_real_name` → witness_is_perpetrator
- `the_court_whose_judge_was_your_old_captain` → reunion_pretending_not_to_know
- `the_debt_in_a_currency_the_articles_did_not_recognize` → bond_whose_proof_is_crime
- `the_crew_that_voted_to_keep_their_chains` → mercy_that_was_cruelty — **duplicate axis within pool** ⚠ recast
  - Recast: `the_crew_that_voted_to_keep_their_chains` → **guilty_who_is_innocent** (they voted to keep the chains because they were already guilty of being free; the chains now belong to someone else and the vote was their proof of non-complicity).

After recast, all 14 arc axes are distinct within the pool.

**Character dynamics (count=8):**

```yaml
character_dynamics:
  - id: crewman_loyal_to_the_articles_not_the_captain
    tags: [crew, articles_loyalty, captain_excluded, charter_over_person]
    incompatible_with: [officer_who_believes_they_are_upholding_the_articles_better_than_the_captain, the_quartermaster_who_counts_against_the_captain]
  - id: officer_who_believes_they_are_upholding_the_articles_better_than_the_captain
    tags: [officer, articles_strict, better_captain, principled_dissident]
    incompatible_with: [crewman_loyal_to_the_articles_not_the_captain, captain_whose_authority_is_renewed_every_share_day]
  - id: the_pressed_one_who_keeps_getting_voted_into_responsibility
    tags: [pressed, voted_responsibility, unwilling_officer, conscript_promoted]
    incompatible_with: [veteran_who_knows_which_side_of_the_articles_saves_you_in_a_fight, the_quartermaster_who_counts_against_the_captain]
  - id: veteran_who_knows_which_side_of_the_articles_saves_you_in_a_fight
    tags: [veteran, articles_loophole, survival_knowledge, fight_in_archive]
    incompatible_with: []
  - id: the_quartermaster_who_counts_against_the_captain
    tags: [quartermaster, count_against, ledger_dispute, parallel_authority]
    incompatible_with: [officer_who_believes_they_are_upholding_the_articles_better_than_the_captain]
  - id: captain_whose_authority_is_renewed_every_share_day
    tags: [captain, share_day_renewal, renewed_authority, conditional_command]
    incompatible_with: [officer_who_believes_they_are_upholding_the_articles_better_than_the_captain, the_quartermaster_who_counts_against_the_captain]
  - id: the_one_who_keeps_the_articles_and_knows_they_were_written_by_an_older_hand
    tags: [articles_keeper, older_hand, prior_author, suspicious_charter]
    incompatible_with: []
  - id: the_one_whose_family_lost_its_plantation_the_year_they_were_transported
    tags: [transported, plantation_lost, year_record, displaced_to_pirate]
    incompatible_with: []
```

**Dynamic axes:**
- `crewman_loyal_to_the_articles_not_the_captain` → articles_under_pressure
- `officer_who_believes_they_are_upholding_the_articles_better_than_the_captain` → reform_was_the_trap
- `the_pressed_one_who_keeps_getting_voted_into_responsibility` → decision_already_made
- `veteran_who_knows_which_side_of_the_articles_saves_you_in_a_fight` → truth_everyone_knows
- `the_quartermaster_who_counts_against_the_captain` → clean_one_is_the_problem
- `captain_whose_authority_is_renewed_every_share_day` → pardon_kept_offered
- `the_one_who_keeps_the_articles_and_knows_they_were_written_by_an_older_hand` → squad_held_by_secret
- `the_one_whose_family_lost_its_plantation_the_year_they_were_transported` → human_cargo

**NPC bonds (count=8):**

```yaml
npc_bonds:
  - id: the_saved_my_life_but_the_prize_sank
    tags: [saved, prize_sank, soul_owed, family_unpaid]
    description: The NPC pulled the PC from a sinking prize ship — life-debt, plainly. The prize sank anyway, and someone's family elsewhere is still owed that vessel's share under the Articles; the NPC carries that share-debt for the PC.
  - id: the_oath_sworn_over_someone_both_had_reason_to_want_dead
    tags: [oath_sworn, mutual_motive, victim_shared, common_complicity]
    description: The NPC and PC swore a blood oath to stand together through mutiny, battle, or gallows. The oath was sworn over the body of someone both of them had reason to want dead. The oath is the bond; the body is the proof.
  - id: the_displaced_captain_now_shares_your_table
    tags: [displaced_captain, prior_mutiny, justified_articles, table_together_now]
    description: The NPC was the PC's captain — the command ended by mutiny, capture, or shipwreck. The mutiny was justified under the Articles; the PC was on the crew that mutinied. Now they share a table; neither says which seat each belongs in.
  - id: the_debt_of_blood_where_the_forgiver_kept_the_articles
    tags: [debt_of_blood, articles_at_word, took_as_justice, weight_of_forgiveness]
    description: The PC killed someone the NPC loved. The NPC took the Articles at their word — declared it paid, took the share-set, called the matter settled. The forgiveness is the weight; the PC has not yet earned the right to call it settled back.
  - id: the_ransom_paid_with_the_others_secret
    tags: [ransom_together, secret_paid, paid_with_truth, leveraged_release]
    description: The NPC and PC were held for ransom together, once. One paid their ransom with the other's secret. The secret is still in the holder's hand; the bond is the silence around it.
  - id: the_captain_who_transferred_you_off_the_ship_a_week_before_it_sank
    tags: [captain_transferred, mercy_then_loss, ship_sank_week_later, displaced_from_fatal]
    description: The NPC was the PC's captain. The captain transferred the PC off the ship a week before the engagement; the ship went down. The PC survived because the captain said so. The captain cannot say whether the kindness was for the PC or for the captain.
  - id: the_privateer_letter_that_both_know_was_forged
    tags: [privateer_letter, forged_both_know, mutual_perjury, shared_lie]
    description: The NPC and PC sailed together under a letter of marque. Both know the letter was forged; neither has ever said so, and the Articles they wrote together are modeled on the forgery, which is the proof of the bond.
  - id: the_one_who_knows_which_cargo_in_your_hold_came_from_a_slaver
    tags: [slaver_cargo, hold_known, sharer_with_knowledge, divided_with_guilt]
    description: The NPC knows which cargo in the PC's hold came from a slaver ship — and divides every share with that knowledge. The proof of the bond is that the NPC has never reported it.
```

**Bond axes (cost structures):**
- `the_saved_my_life_but_the_prize_sank` → debt_paid_in_whoever_else
- `the_oath_sworn_over_someone_both_had_reason_to_want_dead` → squad_held_by_secret
- `the_displaced_captain_now_shares_your_table` → reunion_pretending_not_to_know
- `the_debt_of_blood_where_the_forgiver_kept_the_articles` → bond_whose_proof_is_crime
- `the_ransom_paid_with_the_others_secret` → love_is_also_blackmail
- `the_captain_who_transferred_you_off_the_ship_a_week_before_it_sank` → mercy_that_was_cruelty
- `the_privateer_letter_that_both_know_was_forged` → truth_everyone_knows
- `the_one_who_knows_which_cargo_in_your_hold_came_from_a_slaver` → witness_is_perpetrator

**Scene detail bundles (count=7):**

```yaml
scene_detail_bundles:
  - id: quarterdeck
    items: [a compass in a gimbaled brass mount, a swivel gun loaded with grapeshot, a name scratched into the rail that no current crewman answers to]
    conditions: [the deck slick with spray, the rigging humming under strain]
    sensory: [the snap of canvas overhead, the creak of the helm under pressure]
  - id: orlop_deck
    items: [a surgeon's saw with a stained handle, a lantern swinging with the ship's roll, a surgery ledger with the date of an operation not yet performed]
    conditions: [oppressively dark, the air thick with bilge and salt]
    sensory: [the groan of the hull timbers, the scurrying of rats in the dark]
  - id: captains_cabin
    items: [a sea chart with course corrections in red ink, a brace of pistols in a felt-lined case, a child's drawing tucked in the chart-easel]
    conditions: [the cabin listing to starboard, the lock on the dispatch box scratched]
    sensory: [the tang of gunpowder and Madeira, the drip of water through a deck seam]
  - id: galley
    items: [an iron kettle over a low fire, a cleaver worn thin from sharpening, a tin cup with a woman's name etched polished back into visibility]
    conditions: [greasy and close, the fire smoking badly]
    sensory: [the sizzle of hardtack frying, the smell of rancid cooking oil]
  - id: cargo_hold
    items: [barrels of salt pork stamped with a naval mark, a broken musket discarded in a corner, a single set of women's shoes paired and set down rather than thrown]
    conditions: [the hold half-flooded, crates shifted and splintered]
    sensory: [the slosh of bilgewater against the hull, the smell of damp timber and spoiled provisions]
  - id: beach_cove
    items: [a longboat pulled up on the sand, a sea chest with the lock smashed, a second longboat burned to the waterline and still warm]
    conditions: [the tide coming in fast, the cove sheltered from the wind]
    sensory: [the hiss of waves on shingle, the cry of gulls overhead]
  - id: warehouse_district
    items: [a hoist with a frayed rope, a ledger open to a page of false weights, a manifest line in a child's hand for "Ma, Pa, self."]
    conditions: [the air thick with dust from spice sacks, a lantern burning low in a wall sconce]
    sensory: [the skitter of rats in the rafters, the muffled shouts from the street outside]
```

**Scene wrong-detail registers (all distinct):**
- `quarterdeck` → identificatory (scratched name no one answers to)
- `orlop_deck` → temporal_dislocated (operation not yet performed)
- `captains_cabin` → child_who_remembers (child's drawing)
- `galley` → personal_trace (woman's name polished back)
- `cargo_hold` → intentional_placement (paired shoes set down, not thrown)
- `beach_cove` → residual_presence (warm second longboat burned)
- `warehouse_district` → child_who_remembers_replacement ⚠ recast (avoid dup of `captains_cabin`)
  - Recast: `warehouse_district` → **child_handwriting** (manifest line in a child's hand — register: child-authored but not necessarily remembering the before; better fit: `unattributable_hand`).

After revision, all 7 scene registers distinct.

**PC situation schema (count=4):**

```yaml
pc_situation_schema:
  - key: the_ship_whose_previous_captain_was_kept_or_killed_by_you
    description: The PC's current vessel had a previous captain, and the transition was not Articles-clean. Did the PC keep the captain, kill the captain, or stand aside while someone did — and what does the crew that watched it happen aboard now say about it to each other?
    required: false
    persist: true
  - key: the_port_that_will_hang_you_or_drink_with_you_depending_on_the_messenger
    description: The PC has a home port. The same port will hang the PC or drink with the PC depending on which message arrived most recently from elsewhere — and the PC does not always know which one arrived.
    required: false
    persist: true
  - key: the_thing_you_did_under_articles_that_made_a_stranger_call_you_pirate_like_it_was_a_name
    description: The PC did something under the Articles — within them, technically — that made a stranger call the PC "pirate" like it was the PC's name. What was the act, and what made it not technically a violation?
    required: false
  - key: the_empire_whose_pardon_letter_is_in_your_sea_chest_unsigned
    description: The PC keeps a pardon letter in their sea chest from an empire that has not yet been answered. Which empire, what did the PC do to be offered it, and why has the PC not yet signed it?
    required: false
    persist: true
```

**PC schema wound directions (all distinct):**
- `the_ship_whose_previous_captain_was_kept_or_killed_by_you` → command
- `the_port_that_will_hang_you_or_drink_with_you_depending_on_the_messenger` → reception
- `the_thing_you_did_under_articles_that_made_a_stranger_call_you_pirate_like_it_was_a_name` → identity
- `the_empire_whose_pardon_letter_is_in_your_sea_chest_unsigned` → allegiance

---

### 5. Allied WW2 — 1940–1945

**Posture:** the-good-war, brotherhood-of-arms, enemy-dehumanized, orders-as-excuse, heroism-as-default. Each entry subverts a different piece.

**World bible (new — to be written into `packs/default/allied-ww2/world.md`):**

```md
# World Bible — Allied WW2 1940-1945

Not the good war. The squad is held together by a shared secret, not by brotherhood — brotherhood is the official version. The enemy is not dehumanized; he shows you his daughter's photo and you go on firing, which is worse. Logistics and fatigue kill more than combat. The medic decides who is salvageable, and the medic is always tired.

Letters from home describe a war the home front believes the Allies are winning — which is not the war the squad is in. The chain of command is obeyed not because the orders are right but because the section will not openly disobey them, and the section has not openly disobeyed an order in a very long time, which is its own failure.
```

**World facts (sharpened, 3):**
1. The war has been raging for years with no clear end and fronts that shift without warning — and the home front is being told a coherent story about it that the men in the line cannot recognize as their own.
2. Occupied territories resist through underground networks while collaborationist governments maintain order under threat — and the line between resister and collaborator is sometimes a letter, sometimes a single missed meeting.
3. Advanced weapons technology and codebreaking are reshaping combat and intelligence — and most of this is happening far from the line, which means the line is dying of decisions made by people who have never been there.

**Baseline facts (sharpened, 3):**
1. The war is fought in mud, snow, and rubble — the tank crew in Normandy is in the same rain and rot as the infantry in Italy, and the weather decides more battles than the generals' plans, and neither weather nor generals will admit it.
2. The soldier's nearest ally is the person standing next to them — not a concept but a reality. They fight to keep the squad alive, not the flag or the map. The bond holds when everything falls apart — and the bond holds because the truth doesn't, which is the part of the brotherhood nobody says.
3. Every front has a different rhythm — the static terror of siege, the sprint-and-dive of assault, the long wait before an attack, the chaos after a breakthrough. Most of the war is the waiting wrapped in fear, and the waiting is what breaks people, not the combat they were prepared for.

**Situation archetypes (count=12):**

```yaml
situation_archetypes:
  - id: the_medic_who_decides_who_is_salvageable
    tags: [medic_tries, salvage_decision, triage_authority, life_assignment]
    incompatible_with: []
  - id: the_drop_that_landed_among_people_who_already_surrendered
    tags: [paratroopers_late, surrendered_already, no_one_to_fight, arrived_after]
    incompatible_with: []
  - id: retreat_through_a_village_that_does_not_know_whose_side_it_is
    tags: [retreat, village_unknown_alignment, civilians_ambiguous, mixed_signals]
    incompatible_with: []
  - id: the_trench_that_was_supposed_to_have_been_reinforced
    tags: [trench_unreinforced, ordered_done, not_done, fallback_blame]
    incompatible_with: []
  - id: ambush_of_people_you_know_the_names_of
    tags: [ambush_named, known_targets, recognizable_enemy, opposite_acquaintance]
    incompatible_with: []
  - id: the_recon_that_keeps_finding_friendly_graves
    tags: [recon_graves, friendly_dead, count_mismatch, where_records_go]
    incompatible_with: []
  - id: the_bridge_the_engineers_already_wired_to_blow
    tags: [bridge_wired, ordered_hold, secretly_mined, hold_knowledge_absent]
    incompatible_with: []
  - id: firefight_with_the_unit_that_was_supposed_to_relieve_you
    tags: [firefight_reliever, friendly_fire, mistaken_unit, overlapping_dispatch]
    incompatible_with: []
  - id: the_officer_who_died_of_his_own_gun
    tags: [officer_dead, own_gun, suicide_or_assistance, ambiguous_death]
    incompatible_with: []
  - id: the_villagers_who_would_not_say_which_way_they_went
    tags: [villagers_silent, direction_withheld, common_secret, misdirection_mercy]
    incompatible_with: []
  - id: the_surrenderer_nobody_in_the_section_wants_to_take
    tags: [surrenderer_unwanted, ration_cost, taking_means_feeding, hard_mercy]
    incompatible_with: []
  - id: the_fire_mission_that_keeps_landing_on_your_position
    tags: [friendly_artillery, own_guns_ranging, wrong_map, mistaken_dispatch]
    incompatible_with: []
```

**Situation axes:**
- `the_medic_who_decides_who_is_salvageable` → medic_decides_who_counts
- `the_drop_that_landed_among_people_who_already_surrendered` → victim_engineered_it
- `retreat_through_a_village_that_does_not_know_whose_side_it_is` → truth_everyone_knows
- `the_trench_that_was_supposed_to_have_been_reinforced` → reform_was_the_trap
- `ambush_of_people_you_know_the_names_of` → reunion_pretending_not_to_know
- `the_recon_that_keeps_finding_friendly_graves` → squad_held_by_secret
- `the_bridge_the_engineers_already_wired_to_blow` → decision_already_made
- `firefight_with_the_unit_that_was_supposed_to_relieve_you` → place_that_was_supposed_to_be_and_isnt
- `the_officer_who_died_of_his_own_gun` → witness_is_perpetrator
- `the_villagers_who_would_not_say_which_way_they_went` → conspiracy_inertia
- `the_surrenderer_nobody_in_the_section_wants_to_take` → mercy_that_was_cruelty
- `the_fire_mission_that_keeps_landing_on_your_position` → clean_one_is_the_problem

**Arc categories (count=14):**

```yaml
arc_categories:
  - id: the_secret_the_squad_keeps_for_each_other
    tags: [shared_secret, squad_silence, mutual_cover, kept_lie]
    incompatible_with: []
  - id: the_enemy_who_showed_you_a_photo_of_his_daughter
    tags: [enemy_recognized, daughter_photo, ongoing_fire, recognized_enemy]
    incompatible_with: []
  - id: the_order_only_one_of_you_can_refuse
    tags: [order_refusable, single_refusal_carries, weighted_no, lone_dissent]
    incompatible_with: []
  - id: the_thing_you_did_that_your_commander_offered_to_report_as_courage
    tags: [commander_cover, courage_label, reclassified_act, sanctioned_violation]
    incompatible_with: []
  - id: the_prisoner_that_does_not_know_what_happened_to_the_last_one
    tags: [prisoner_unaware, prior_prisoner_gone, secret_execution, ignorance_as_mercy]
    incompatible_with: []
  - id: the_one_who_walked_off_line_and_walked_back_two_days_later_changed
    tags: [walked_off, returned_changed, two_days_absent, allowed_back]
    incompatible_with: []
  - id: the_order_that_keeps_being_given_by_different_officers_until_someone_enforces_it
    tags: [recurring_order, rotating_authority, until_enforced, refuses_to_be_forgotten]
    incompatible_with: []
  - id: the_letter_from_home_that_does_not_match_the_war_you_are_in
    tags: [home_letter, mismatched_war, written_home-belief, narrated_victory]
    incompatible_with: []
  - id: the_replacement_who_keeps_showing_up
    tags: [recurring_replacement, lost_three, fourth_here, undaunted_arrival]
    incompatible_with: []
  - id: the_home_town_that_does_not_know_what_happened_to_the_last_boy_they_sent
    tags: [home_town_unaware, prior_boy_uncounted, undisclosed_loss, written_record_gap]
    incompatible_with: []
  - id: the_civilian_who_was_saving_the_thing_you_were_sent_to_destroy
    tags: [civilian_saved, target_preserved, contrary_mercy, opposing_care]
    incompatible_with: []
  - id: the_ration_that_was_yours_today_tomorrow_someone_elses
    tags: [ration_rotation, lottery_death, displaced_share, sliding_assignment]
    incompatible_with: []
  - id: the_medic_who_decides_who_counts_as_wounded
    tags: [medic_tries, wound_recognition, salvage_authority, deferred_care]
    incompatible_with: []
  - id: the_general_who_keeps_visiting_the_line_and_leaving
    tags: [general_visits, soap_smell_departure, brief_presence, leaving_odor]
    incompatible_with: []
```

**Arc axes:**
- `the_secret_the_squad_keeps_for_each_other` → squad_held_by_secret
- `the_enemy_who_showed_you_a_photo_of_his_daughter` → enemy_recognized_not_dehumanized
- `the_order_only_one_of_you_can_refuse` → reform_was_the_trap
- `the_thing_you_did_that_your_commander_offered_to_report_as_courage` → truth_everyone_knows
- `the_prisoner_that_does_not_know_what_happened_to_the_last_one` → witness_is_perpetrator
- `the_one_who_walked_off_line_and_walked_back_two_days_later_changed` → place_that_was_supposed_to_be_and_isnt
- `the_order_that_keeps_being_given_by_different_officers_until_someone_enforces_it` → decision_already_made
- `the_letter_from_home_that_does_not_match_the_war_you_are_in` → letter_from_home_doesnt_match
- `the_replacement_who_keeps_showing_up` → replacement_keeps_showing
- `the_home_town_that_does_not_know_what_happened_to_the_last_boy_they_sent` → debt_paid_in_whoever_else
- `the_civilian_who_was_saving_the_thing_you_were_sent_to_destroy` → innocent_who_is_guilty
- `the_ration_that_was_yours_today_tomorrow_someone_elses` → mercy_that_was_cruelty
- `the_medic_who_decides_who_counts_as_wounded` → medic_decides_who_counts
- `the_general_who_keeps_visiting_the_line_and_leaving` → conspiracy_inertia

**Character dynamics (count=8):**

```yaml
character_dynamics:
  - id: the_medic_who_decides_who_counts_as_wounded
    tags: [medic, triage_judgement, wound_recognized, life_assignment]
    incompatible_with: []
  - id: the_nco_who_keeps_the_real_roster_of_who_is_breaking
    tags: [NCO, real_roster, breaking_known, separate_ledger]
    incompatible_with: []
  - id: the_replacement_whose_first_meal_is_with_a_section_that_knows_a_dead_mans_seat
    tags: [replacement, dead_mans_seat, rite_of_joining, weighted_meal]
    incompatible_with: []
  - id: scout_who_came_back_with_something_they_will_not_say
    tags: [scout, unsaid_return, held_report,came_back_with]
    incompatible_with: []
  - id: the_clerk_who_can_make_a_dead_mans_pay_stop_or_keep_going
    tags: [clerk, pay_record, dead_or_alive_paper, signature_power]
    incompatible_with: []
  - id: radioman_who_decides_which_messages_make_it_through
    tags: [radioman, message_filter, home_dispatch, suppression_in_hand]
    incompatible_with: []
  - id: the_crewmember_who_knows_which_round_was_fired_at_what
    tags: [crew, fired_round, known_target, target_accounting]
    incompatible_with: []
  - id: the_rifleman_whose_letter_from_home_arrived_already_open
    tags: [rifleman, opened_letter, censored_or_read, home_in_hand]
    incompatible_with: []
```

**Dynamic axes:**
- `the_medic_who_decides_who_counts_as_wounded` → medic_decides_who_counts
- `the_nco_who_keeps_the_real_roster_of_who_is_breaking` → squad_held_by_secret
- `the_replacement_whose_first_meal_is_with_a_section_that_knows_a_dead_mans_seat` → replacement_keeps_showing
- `scout_who_came_back_with_something_they_will_not_say` → witness_is_perpetrator
- `the_clerk_who_can_make_a_dead_mans_pay_stop_or_keep_going` → clean_one_is_the_problem
- `radioman_who_decides_which_messages_make_it_through` → letter_from_home_doesnt_match
- `the_crewmember_who_knows_which_round_was_fired_at_what` → debt_paid_in_whoever_else
- `the_rifleman_whose_letter_from_home_arrived_already_open` → record_doesnt_match

**NPC bonds (count=8):**

```yaml
npc_bonds:
  - id: foxhole_brother
    tags: [foxhole, shared_silence, one_back_one_forward, mutual_witness]
    description: The NPC shared a foxhole with the PC during a sustained engagement — they shared ammo, watches, and whatever they had. One of them came back; one of them is still there. The bond is the silence about what happened in the foxhole, which neither has ever said aloud.
  - id: deserted_together_once
    tags: [desertion_shared, section_covered, false_patrol_report, owes_section_member]
    description: The NPC and PC both stepped off the line once, in a moment neither will speak of. The section covered it; the report says they were on patrol. The bond is to the section member who didn't walk — and didn't survive the next week.
  - id: superior_officer_conflict
    tags: [officer_conflict, kept_alive_which, personal_friction, life_friction]
    description: The NPC is a non-com or officer who has clashed with the PC before. The friction is personal — and it is founded in a specific incident: which of them let the other one live.
  - id: the_wounded_where_the_squad_agreed_to_call_it_enemy_fire
    tags: [visible_scar, friendly_origin, squad_covered, narrated_enemy]
    description: The NPC was under the PC's care in a previous engagement and carries a visible scar from it. The visible scar is not from enemy action — the squad agreed to call it enemy action. The bond is the squad's continued agreement.
  - id: shared_pow_experience
    tags: [pow_together, one_ate_one_didnt, hunger_knowledge, deprivation_choice]
    description: The NPC and PC were held together in a POW camp. They survived it together — and in the camp, one of them ate; one of them did not. Both know why that was. The bond is the silence around the choice.
  - id: training_batch
    tags: [training_batch, only_two_back, others_stationed_elsewhere, polite_pretense]
    description: The NPC and PC went through basic training together — the bond of shared misery. Only two of the batch came back; both pretend the others are stationed elsewhere, and neither has visited.
  - id: the_one_who_knows_what_happened_to_the_civilian
    tags: [civilian_dead, two_witnesses, no_report, mutual_complicity]
    description: The NPC is the only other person who knows what happened to a particular civilian — the only other person who did not report it, and did not stop it, and is therefore permanently bonded to the PC by what they both did not do.
  - id: the_one_who_has_a_letter_for_your_next_of_kin_already_written
    tags: [prewritten_letter, next_of_kin, awaiting_death, shelf_letter]
    description: The NPC has already written the letter to the PC's next of kin. The NPC carries it in their pocket. The PC knows the NPC carries it; the NPC knows the PC knows. The bond is that this is not an insult — it is, in the squad's accounting, a kindness.
```

**Bond axes (cost structures):**
- `foxhole_brother` → squad_held_by_secret
- `deserted_together_once` → debt_paid_in_whoever_else
- `superior_officer_conflict` → bond_whose_proof_is_crime
- `the_wounded_where_the_squad_agreed_to_call_it_enemy_fire` → squad_held_by_secret — **duplicate axis within pool** ⚠ recast
  - Recast: `the_wounded_where_the_squad_agreed_to_call_it_enemy_fire` → **mercy_that_was_cruelty** (the squad's agreement to call the wound enemy fire was a mercy to the shooter that costs the wounded a truth).
- `shared_pow_experience` → mercy_that_was_cruelty — now **duplicate axis** within pool (after recast of the prior) ⚠ recast again
  - Recast: `shared_pow_experience` → **guilty_who_is_innocent** (one ate, one did not; the one who ate is now the one who knows; the innocence is now in the other, and the guilt is in the knowing).
- `training_batch` → reunion_pretending_not_to_know
- `the_one_who_knows_what_happened_to_the_civilian` → witness_is_perpetrator
- `the_one_who_has_a_letter_for_your_next_of_kin_already_written` → letter_from_home_doesnt_match

After revision: squad_held_by_secret, debt_paid_in_whoever_else, bond_whose_proof_is_crime, mercy_that_was_cruelty, guilty_who_is_innocent, reunion_pretending_not_to_know, witness_is_perpetrator, letter_from_home_doesnt_match — all distinct.

**Scene detail bundles (count=7):**

```yaml
scene_detail_bundles:
  - id: bombed_out_village
    items: [a church bell lying in the rubble, a field kitchen with its stove still warm, a child's coat on a chair still buttoned]
    conditions: [rubble-choked streets, smoke haze from a recent fire]
    sensory: [the echo of boots on broken stone, the creak of a half-collapsed beam]
  - id: command_post
    items: [a map table with unit positions in grease pencil, a field telephone with the wire trailing out the door, a child's letter in the trash addressed to a name no officer will claim as theirs]
    conditions: [papers strewn across the floor, hastily evacuated]
    sensory: [the drone of distant bombers, the crackle of a radio left on]
  - id: field_hospital
    items: [a triage table with blood-soaked sawdust on the floor, a clipboard of morphine doses signed by different hands, a triage order written in a dead doctor's hand with today's date]
    conditions: [low on supplies, lantern light flickering]
    sensory: [the hiss of a low-fuel lantern, the moan of wounded men through canvas]
  - id: trench_line
    items: [a periscope rifle propped against the parapet, a signal flare pistol with three rounds left, a photo of a German family pinned to the parapet facing the German side]
    conditions: [mud-choked duckboards, crumbling sandbag parapet]
    sensory: [the thump of distant artillery, the sharp smell of cordite and wet earth]
  - id: supply_depot
    items: [a pallet of ammunition crates with different unit codes, a typewriter on a crate with a half-typed inventory sheet, a crate marked with the dead replacement's name unopened]
    conditions: [crates stacked haphazardly in the rain, fuel drums with slow leaks]
    sensory: [the smell of petrol and damp canvas, the clatter of a loose shutter in the wind]
  - id: destroyed_farmhouse
    items: [a piano with a bullet through its frame, a cellar door half-open, a meal still on the table with only one chair knocked over]
    conditions: [the roof collapsed in the center, a dead cow in the yard]
    sensory: [the buzz of flies, the smell of burnt hay]
  - id: river_crossing
    items: [a pontoon bridge anchored with ropes, a crate of waterproofed flares, a body floating downstream in friendly uniform with no bullet wound]
    conditions: [the current running fast, the fog lying low over the water]
    sensory: [the rush of the river, the creak of ropes under tension]
```

**Scene wrong-detail registers (all distinct):**
- `bombed_out_village` → personal_artifact (child's coat still buttoned)
- `command_post` → child_who_remembers (child's letter to a name no officer claims)
- `field_hospital` → temporal_dislocated (dead doctor's hand, today's date)
- `trench_line` → enemy_recognized_not_dehumanized (German family photo facing German side)
- `supply_depot` → identificatory (crate marked with dead replacement's name)
- `destroyed_farmhouse` → intentional_arrangement (meal still on table, one chair knocked)
- `river_crossing` → procedural_impossible (no bullet wound on floating friendly)

**PC situation schema (count=4):**

```yaml
pc_situation_schema:
  - key: the_section_that_has_the_real_body_count_your_commander_does_not
    description: The PC's section has the real body count, which is not the number the commander has. What is the difference between the two numbers, and which of those numbers is the PC's name on?
    required: false
    persist: true
  - key: the_place_you_will_eventually_have_to_describe_to_someone_who_was_not_there
    description: The PC has been in a place they will eventually have to describe to someone who was not there. Which place, who is the person who will ask, and what version of it does the PC currently plan to tell?
    required: false
  - key: the_person_who_writes_you_letters_about_a_war_they_believe_you_are_winning
    description: The PC is being written to by someone back home who believes the PC is winning the war they describe. Who is writing, what war do they think it is, and what does the PC not say back?
    required: false
  - key: the_officer_you_obey_because_the_section_will_not_openly_disobey_them
    description: The PC obeys a specific officer, not because the orders are right — the section knows they are not — but because the section will not openly disobey them. Who is the officer, what is the order the PC has the most difficulty obeying, and what would the section do if the PC stopped obeying?
    required: false
    persist: true
```

**PC schema wound directions (all distinct):**
- `the_section_that_has_the_real_body_count_your_commander_does_not` → accounting
- `the_place_you_will_eventually_have_to_describe_to_someone_who_was_not_there` → testimony
- `the_person_who_writes_you_letters_about_a_war_they_believe_you_are_winning` → home
- `the_officer_you_obey_because_the_section_will_not_openly_disobey_them` → command

---

## Collision / Interaction Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Extraction pipeline** | New IDs are snake_case ASCII, longer than old noun-phrase IDs. Some extraction fields tag-cache by slug; longer slugs are fine, but check for length caps in field-name validation. | Plan phase verifies `extract_stream_*` field handling. No code change anticipated. |
| **Prompt templates (`seed`/`world`)** | Templates that quote the ID verbatim will read differently — that's the point. Templates that interpolate the ID into prose may produce longer, more charged sentences; verify register still works. | Plan phase audits `ccya/prompts/sections/` for places pools are interpolated. Tone check at review-design. |
| **World bibles (noir, piracy existing; zombie, space-western, allied-ww2 new)** | Subversion angles must not contradict the existing or newly-authored world.md. Noir's existing world.md supports "institution as antagonist" — design uses this as ONE axis among many. Piracy's existing world.md supports both Articles-as-pressure-test and ex-slave-crew axes — design uses both as two of many. The three new world.md texts are written in this design as exhibits, ensuring agreement. | Plan phase writes the three new world.md files first (using the exhibits in this design verbatim), then applies the pool rewrites; review-design verifies alignment before any code change. |
| **Seed state model** | `pc_situation_schema` keys change. Code reading state by key name must be updated; saved games using old keys break. | Per AGENTS.md: no backwards compat required. Implementer rips out old keys, replaces with new. Saves from prior versions are invalid — acceptable. |
| **`incompatible_with` for character dynamics** | Some dynamics currently have `incompatible_with` pairs (`embedded_investigator` vs `free_agent`; zombie pairs; piracy pairs; `displaced_officer` ↔ `coalition_deserter`). Renames must preserve those pairs. | The YAML blocks in this design already carry the preserved incompatible edges, renamed through. Plan phase produces a rename table (old → new); validates it against the in-place YAML blocks above. |
| **Tone cohesion across pools** | Aggressive subversion could create tonal mismatch between sharper situations and softer scenes in the same pack. Diversity compounds the risk. | "One wrong detail per scene" rule keeps scenes atmospheric-but-charged; per-pack coherence reviewed at review-design. The subversion-axis tables in this design are the audit artifact. |
| **Tag field semantics** | Tags currently repeat the ID's noun words; with evocative IDs, tags must keep working as lexical bridges. | Tags in this design are noun-y and tag-like (e.g. `witness, confession, police_complicity, refused_testimony`); IDs carry the prose weight, tags carry the matching weight. |
| **Diversity collapse** | Without enforcement, future maintainers might collapse entries to the same axis. This is the failure mode the design exists to prevent. | The per-pool axis tables in this design enforce — and pre-verify — diversity within each pool. Any duplicate axes flagged inline are already recast above (see "axis collision revision" notes for each pack). Review-design confirms distinctness once more before plan. |
| **World bible authoring load** | Three new world.md files added to this design. Increases scope but guarantees alignment between bible and seed subversions. | Plan phase splits: world.md authoring first as phase 1 (copy exhibits verbatim), seed-pool rewrites as phase 2 (copy YAML blocks verbatim). Both are mechanical; no further creative work belongs in plan. |
| **Token load on seed prompts** | Evocative IDs are longer than the old noun-phrase IDs, and there are 8 NPC bonds and 7 scenes with prose, all rewritten. | Plan phase measures token delta on a representative seed prompt per pack. Acceptable bound: ≤15% per-pool token increase. If exceeded, plan phase shortens IDs without losing the hook and reviews the changes against the axes in this design. |

## Risks

1. **Risk:** Aggressively subverted IDs read as "clever" rather than as story seeds. **Mitigation:** At least one generated scenario per pack via `ev.py prompt-eval` (we are testing outputs — mandatory). A seed reading like a joke or self-reference means dialing that entry back; the original entry in this design is the starting position, not a fixed point.
2. **Risk:** Long IDs inflate token cost of seed prompts. **Mitigation:** Plan phase measures token delta on a representative seed prompt per pack. Acceptable bound: ≤15% per-pool token increase. If exceeded, shorten IDs without losing the hook and re-validate against the axis tables in this design.
3. **Risk:** Some `incompatible_with` pairs break silently if renames aren't cross-referenced. **Mitigation:** The YAML blocks in this design already carry the preserved incompatible edges, renamed through. Plan phase produces a rename table (old → new) and validates it against the in-place YAML blocks above.
4. **Risk:** The PC situation schema wound-framing produces a narrow seed answer (a single secret) that implies a single story rather than a frame. **Mitigation:** Each new field key is written to accept at least two distinct valid answers from different PCs. Plan phase stress-tests with two archetypes per pack per field.
5. **Risk:** Scene bundles drift from period accuracy when "wrong details" are added. **Mitigation:** Each wrong detail must be period-plausible but emotionally impossible. Review-design checks plausibility against the world bible for each pack.
6. **Risk:** Subverting WW2 and Piracy toward moral grey reads as cynical or preachy. **Mitigation:** Subversion points toward *availability of moral choice*, not a thesis. WW2 squads with a shared secret is a story frame, not a verdict on the war.
7. **Risk:** World bible authoring for three new packs dilutes focus on the seed pools. **Mitigation:** Plan phase is mechanical copy of exhibits from this design; no further creative authoring is required there. Split: world.md copy as phase 1, pool copy as phase 2.
8. **Risk:** Combinatorial diversity is hard to verify — "no two seeds produce the same story" is a fuzzy test. **Mitigation:** Plan phase produces for each pack 3 randomly-sampled seeds; review-design reads the three seeds blind and rates whether the central tensions differ. If two match, the axis table is re-reviewed and the matching entry recast to a fresh axis.
9. **Risk:** Subversion axes vocabulary is idiosyncratic to this design and could be misapplied by future maintainers. **Mitigation:** The vocabulary is the audit artifact inside this design. Once the plan is complete, the vocabulary is preserved in the plan doc for traceability but not enforced outside this design's scope.
10. **Risk:** Axis annotations construed as canonical rather than as audit scaffolding. **Mitigation:** Annotations appear AFTER each pool as tables, not inline in the YAML. The YAML is copy-paste-ready; the tables are review-only.

## Rejected Alternatives

1. **Subtle subversion / no inversions** — rejected. Inventory doc shows packs already play straight; "sharper prose without subversion" leaves structural blandness in place.
2. **Rewrite IDs to descriptive noun phrases only** — rejected. Database-column language is the disease; the cure is verb/tension framing, not better nouns.
3. **Increase pool counts** — rejected. Inventory confirms structure is fine; the problem is content, not volume. Keeping counts preserves downstream contracts.
4. **Add a `moral_pressures` field back** — rejected. Per AGENTS.md note, that field had no structured target. Tension lives in IDs and descriptions.
5. **One subversion angle per pack** — rejected. This was the first draft and is the core correction of this design: it collapses the cross-product of seed sampling into one story per pack, defeating the entire point of a pool-based seed system.
6. **Author `world.md` for the three missing packs in a sibling design** — rejected (revised). Bundling guarantees the bible and the per-entry subversions agree. Splitting risks the bible landing in a different posture than the seed subversions were written against, requiring costly re-review.
7. **Keep `free_agent` / `information_broker` / `displaced_elite` across packs** — rejected. Generic-role dynamics that perform no work; read as filler. Replaced with pack-specific dynamics in each pack.
8. **Treat as a feature, not an improvement** — rejected. The five packs already exist; the work improves their content rather than adding a new capability. `I-43`, not `F-N`.
9. **Leave exact phrasing to plan phase** — rejected (user 2026-07-25). For a creative-content design the line between "design sets the bar" and "the content itself" is blurred; user requested full phrasing in the design so the design is the source of truth and plan/execute is mechanical. Adopted by Firm Decision #12.
10. **Inline axis annotations as YAML comments** — rejected. Comments would either have to be copied into `scenario.yaml` (cluttering the file) or stripped (creating review-document drift). Tables after each pool keep the YAML copy-paste-ready while preserving the audit artifact.

## Deferred Items

- **Token budget measurement & per-pack tradeoff tuning** — plan phase. The design sets the bar; plan/execute verifies it is reachable without breaching token budgets.
- **Multi-pack tag de-duplication** — currently several tags repeat across packs (e.g. `discovery`, `betrayal`). Out of scope; belongs to a tags-normalization design.
- **Cross-pool axis reuse audit** — within a pool, axes are distinct (enforced above). Across pools, axes ARE reused (e.g. `truth_everyone_knows` appears in noir sit/arc, zombie sit, space-western sit/arc, piracy sit/arc, ww2 arc). That reuse is intentional — same axis in different genre contexts yields different stories. The audit at review-design eyeballs whether within-pack diversity produces visibly different seeds on sampling.
- **Adding any new pool types (e.g. a per-pack "morality" pool)** — out of scope. Schema is unchanged in this design. Future work.
- **Per-pack token-and-idyll probe through `ev.py prompt-eval`** — plan phase. The five packs need at minimum one synthesized seed prompt each pulled through `prompt-eval` to confirm the subverted seeds produce charged openings.

## What an Implementer Needs to Read

- `docs/findings/pack-archetypes-inspiration.md` — authoritative inventory of current state (the before image)
- `docs/design/pack-archetypes-subversion-design.md` — this design (after image, full phrasing)
- `packs/default/<pack>/scenario.yaml` for each of the five packs — the file being rewritten
- `packs/default/noir-1930s/world.md` and `packs/default/golden-piracy/world.md` — existing; verify against the per-pack posture above (no edits)
- The three new world.md files written in this design as exhibits — copy verbatim to `packs/default/{zombie-survival,space-western,allied-ww2}/world.md`
- `ccya/models/state.py` — verify `pc_situation_schema` field-name handling (state model reads state by *key*, no fixed key names expected; implementer confirms)
- `ccya/prompts/sections/` — seed prompt templates that interpolate pool IDs and tags; plan audits these for tonal fit after copy
- `docs/repomap.md` — five-call pipeline section, to confirm pool content lands where expected
- `scripts/debug/README.md` and `docs/ev/EVAL-RUNS.md` — for running `ev.py prompt-eval` per pack as the verification step

## Dependencies on Other Designs

- None — this design absorbs the world.md authoring that prior drafts deferred. The three new bibles are written under this design's posture framework as exhibits.