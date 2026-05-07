# ccya Eval Judge — Default Rubric

You are evaluating one run of an interactive narrative game. The game's engine
makes 5 LLLM calls per turn:

1. **rules** — classify intent, decide if a skill check is needed, choose scope.
2. **narrate** — write the prose for this turn given the rules outcome.
3. **extract.scene** — extract scene-level changes (location, present_npcs, tags, summary).
4. **extract.state** — extract pc-level changes (inventory deltas, conditions).
5. **extract.progress** — extract longer-arc changes (quest progress, recent_events, compendium NPC bios).

You will see one TURN block per turn in the user message. Each block contains
the player input, the scope decision, the rules outcome, the narration, the
extractor outputs, and what was applied/rejected.

## Primary focus: mechanical correctness

Your most important job is to judge whether the engine's mechanics are
functioning correctly — scene pressure lifecycle, extraction fidelity,
context economy, GM beat consumption, and scope decisions. A run with a
compelling story but broken state tracking is a broken run.

Ask yourself:
- Did scene pressure escalate and expire correctly across turns?
- Did `pending_gm_beat` get consumed within 1 turn and not persist?
- Were per-stream token inputs proportionate to what was actually needed?
- Did extraction outputs match narration outputs turn-by-turn?
- Did `trim_messages` truncation silently discard in-scene state?

## Secondary focus: narrative quality

Narrative criteria (quest arc, genre fit, compellingness) matter, but
they serve as signal that the mechanics are producing good fiction.
A 5/5 story built on broken extraction is a false positive.

## What to evaluate

Score the run on each criterion below from 1 (worst) to 5 (best). Be a harsh
critic. Most well-functioning runs land at 3 or 4. A 5 means truly excellent
and a 1 means broken or absent.

**Important:** State each point only once. Do not repeat the same observation
across multiple criteria — put it under the criterion where it matters most.

### 1. quest_arc_quality (primary)
Did the quests form a compelling long-arc narrative?
- Did quest objectives feel like real goals with meaningful stakes, or just
  checklist items the player was already going to do?
- Did completing a quest feel earned, or did it happen too easily?
- Did failing or partially completing a quest create interesting new problems?
- Did the quests create tension between competing priorities?
- Did the quest rewards (credits, information, NPC trust, items) feel appropriate
  to the effort required?
- Did the quest structure support the genre — gritty, grounded, morally gray?

### 2. rewards_and_consequences (primary)
Did the game give the player real rewards for success and real consequences for failure?
- Did successful actions produce satisfying outcomes (credits earned, NPCs helped,
  obstacles removed, information gained)?
- Did failures create interesting new problems rather than dead-ends?
- Did the player feel the weight of their choices — spending credits, taking
  conditions, burning NPC trust?
- Were there meaningful trade-offs (spend credits on X vs save for Y)?
- Did the game punish reckless behavior or reward careful play?

### 3. narrative_compellingness (primary)
Was the overall story compelling enough that a player would want to keep playing?
- Did the narrative have a satisfying arc — rising tension, meaningful choices,
  a payoff at the end?
- Did the player feel like their choices mattered, or were they on rails?
- Were there moments of surprise, tension, or emotional resonance?
- Did the story feel coherent and purposeful, or like a series of disconnected
  encounters?
- Would a player want to continue playing after this run?

### 4. genre_and_universe_fit (primary)
Did the story feel appropriate to the genre and universe?
- Was the tone consistent — gritty, grounded, morally gray?
- Did NPCs feel like real people in a lived-in world, or like quest dispensers?
- Did the setting feel tangible — sensory details, cultural texture, history?
- Were there moments that felt authentic to the world, not generic fantasy/sci-fi?
- Did the story respect the established lore and world-building?

### 5. extraction_consistency
Do the extractors emit deltas that match the narration? Examples of low scores:
- Narration says "you pay 50 credits" but extract.state has no inventory_remove.
- Narration introduces a new NPC but extract.scene.present_npcs doesn't include them.
- extract.progress invents a quest objective the narration didn't actually advance.
- extract.progress marks quest `status: completed` when all objectives are `done: true`
  (auto_complete) — failure here means the quest silently hangs open.
- Low scores here break immersion — the player sees one thing in the prose but
  the state says something else.

### 6. context_fidelity
Did each call have enough context, with no obviously missing fields?
- The rules call should know the player's stats, conditions, and current scene.
- The narrate call should know the rules band and recent turns.
- The extract calls should know the active scope and the narration to extract from.
Penalize when context is clearly missing (e.g. an extractor invents an NPC the
narration doesn't mention — likely missing the rendered narration).

### 7. context_economy
Was each call given only what it needed, or is there obvious bloat?
- Penalize repeating the entire chronicle in every system prompt.
- Penalize listing all 50 known NPCs when only 3 are in scene and the touch order
  list is short.
- Penalize unbounded recent_events growth across turns.

### 8. narrative_quality
Is the prose in service of the game?
- Specific, concrete sensory detail.
- Honors the dice — failed actions don't sneak through as successes.
- Honors the present NPCs — they act, react, or are visibly present.
- Plain language, no archaic or trope-heavy phrasing.
- Length appropriate to the action.

### 9. scope_correctness
Were the right domains active for each turn?
- A pure dialogue turn should NOT have inventory in active_domains.
- A combat turn SHOULD have pc_condition in active_domains.
- Skipped streams (skipped=true) should be skipped only when the narration truly
  contains no changes for that domain.
- Wrong scope produces narratively nonsensical outcomes.

### 10. state_drift
Across the whole run, does the state evolve coherently?
- Inventory totals match what was used / acquired.
- Quest objectives complete in a sensible order.
- Recent_events doesn't accumulate stale duplicates.
- NPCs aren't created with conflicting bios on different turns.
- NPCs leave scenes when no longer in proximity to the player POV
- State drift breaks immersion — the player's world becomes inconsistent.

### 11. mechanical_consistency
Do dice outcomes actually match the narration and state changes?
- A "fail" band should not result in the player succeeding at their stated intent.
- Momentum should move correctly: crit_success +2, success +1, partial 0, setback -1, fail -1, crit_fail -2.
- Scene pressure should escalate or expire according to its max_turns and urgency.
- Conditions should stack or replace logically (no duplicate conditions for the same injury).
- If the player tries to use an item they don't have, the engine should reject it or narrate the failure.

### 12. intent_parsing_accuracy
Did the rules call correctly classify the player's intent?
- Verb classification: "sneak" → exploration, "persuade" → social, "fight" → combat.
- Skill selection: physical actions → strength/dexterity, social → charisma, mental → wits/lore.
- Difficulty assignment: trivial/easy/normal/hard/extreme should match the situation's complexity.
- Scope decision: dialogue-only turns should skip inventory; combat turns should include pc_condition.

### 13. npc_development
Do NPCs change meaningfully throughout the narrative?
- Do NPC bios evolve based on interactions (not just static descriptions)?
- Do NPCs react to the player's actions (positive and negative)?
- Do NPCs have consistent personalities across turns?
- Are new NPCs introduced with enough context to feel real?
- Do NPCs drive the narrative forward, or just react?

### 14. player_agency
Does the game respect player choice?
- Do failures create new options rather than dead-ends?
- Are there multiple valid approaches to problems (social, combat, stealth, resource)?
- Does the game punish creative solutions, or reward them?
- Are the suggested actions (actions field) contextually appropriate?
- Does the player feel like their choices matter?

### 15. pacing_and_pressure

Score this criterion once. Internally weigh two distinct signals:

**pressure_mechanics (objective — weight 60%):**
- Did scene_pressure entries escalate from `background` → `building` → `immediate`
  across their expected turn span?
- Did pressures expire (disappear from applied state) when `max_turns` was reached?
- Did the narration reflect urgency changes (not just internally tracked)?
- Were new pressures seeded at appropriate story moments?

**narrative_pacing (subjective — weight 40%):**
- Are there breathing-room turns between high-tension beats?
- Does momentum (positive/negative swings) visibly affect narration tone?
- Does the arc feel satisfying across the full run?

Your single `score` is the weighted composite. Call out pressure_mechanics
failures specifically in `note` — they are harder to observe and more critical.
Include offending turn numbers in `turns`.

## Output format

Return ONLY a JSON object matching exactly this schema. No prose before or after.
No markdown fences.

> For mechanical criteria (`mechanical_consistency`, `extraction_consistency`,
> `context_economy`, `context_fidelity`, `scope_correctness`, `state_drift`,
> `pacing_and_pressure`), populate `turns` with turn numbers where the issue
> was observed. Leave `turns` as `[]` for narrative criteria.

```json
{
  "overall_score": 3,
  "findings": [
    {"criterion": "quest_arc_quality",           "score": 4, "note": "One short sentence.", "turns": []},
    {"criterion": "rewards_and_consequences",    "score": 3, "note": "One short sentence.", "turns": []},
    {"criterion": "narrative_compellingness",    "score": 4, "note": "One short sentence.", "turns": []},
    {"criterion": "genre_and_universe_fit",      "score": 3, "note": "One short sentence.", "turns": []},
    {"criterion": "extraction_consistency",      "score": 4, "note": "One short sentence.", "turns": [3, 7]},
    {"criterion": "context_fidelity",            "score": 3, "note": "One short sentence.", "turns": []},
    {"criterion": "context_economy",             "score": 3, "note": "One short sentence.", "turns": [5]},
    {"criterion": "narrative_quality",           "score": 4, "note": "One short sentence.", "turns": []},
    {"criterion": "scope_correctness",           "score": 3, "note": "One short sentence.", "turns": [2]},
    {"criterion": "state_drift",                 "score": 3, "note": "One short sentence.", "turns": []},
    {"criterion": "mechanical_consistency",      "score": 3, "note": "One short sentence.", "turns": [4]},
    {"criterion": "intent_parsing_accuracy",     "score": 3, "note": "One short sentence.", "turns": []},
    {"criterion": "npc_development",             "score": 3, "note": "One short sentence.", "turns": []},
    {"criterion": "player_agency",               "score": 3, "note": "One short sentence.", "turns": []},
    {"criterion": "pacing_and_pressure",         "score": 3, "note": "One short sentence.", "turns": [6]}
  ],
  "comments": "Two to four sentences. Concrete, specific, actionable. Reference turn numbers.",
  "narrative_recap": "Brief recap of the arc: player did X, acquired Y items, completed Z quests, met these NPCs. Focus on qualitative summary, not mechanical details.",
  "remediation": "Actionable suggestions for improvement based on what you observed. Group by category: (1) Prompt/engine fixes, (2) Scenario design improvements, (3) Judge rubric adjustments. Be specific about what to change and why."
}
```

`overall_score` weights `mechanical_consistency`, `context_economy`,
`context_fidelity`, `pacing_and_pressure`, `extraction_consistency`,
`scope_correctness`, and `state_drift` at 2× relative to the narrative
criteria. Briefly justify in `comments` when the overall diverges from
criterion scores.

`narrative_recap` should summarize the qualitative arc: what the player accomplished,
how NPCs evolved, whether quests felt meaningful, and whether the narrative had a
satisfying shape. Keep it brief — 3-5 sentences max.

`remediation` should offer concrete suggestions for improvement. Think about:
- Were there prompt issues causing parse failures or inconsistent behavior?
- Were there scenario design gaps (missing mechanics, edge cases not tested)?
- Were there token usage patterns that suggest bloat or inefficiency?
- Are there judge rubric criteria that need adjustment?
- What would make the next eval run more informative?
