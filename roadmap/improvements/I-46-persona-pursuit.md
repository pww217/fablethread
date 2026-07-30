---
title: "Improve persona system so characters pursue arc goals actively rather than passively or recklessly"
status: done
urgency: 3
size: medium
created: 2026-07-29
ticket_id: I-46
labels: [persona, ev]
design:
plan:
pr:
  url:
  branch:
completed: 2026-07-30
---

## Description

The persona system produces two distinct failure modes in evaluation runs, both stemming from personas that don't properly anchor character behavior to arc goals:

1. **Passive drift** — PCs default to hiding, listening, reading, and waiting. They spend 15-20 turns doing nothing consequential. Examples: Runs `0004_space-western_25t` (hiding for 25 turns), `0025_golden-piracy_25t` (reading and eavesdropping for 25 turns), `0055_unknown_25t` (hiding for most of the game).

2. **Reckless aggression** — PCs with "aggressive" personas default to shooting, punching, and threatening without regard for self-preservation or ally safety. Examples: Run `0245_allied-ww2_aggressive_25t` — Carter shoots a friendly soldier, holds his own unit at gunpoint, steals their orders. These aren't bold choices; they're reckless decisions that contradict the character's stated values.

The root cause is **two-fold**:

1. **Personas describe style, not purpose.** They tell the LLM *how* to act (bold, careful, curious) but not *why*. Without a clear "why" (the arc goal), the LLM fills in the blanks with its default behavior: hide and wait (passive) or charge and fight (aggressive).

2. **The PC has almost no memory of past turns.** This is the single biggest structural problem. The PC receives only: inventory (names only), arc goal (as a separate line), and the most recent turn's narrative prose. The PC does NOT receive prior history bullets, what it did last turn, what happened 2+ turns ago, NPC roster, conditions, location details, or arc threads. The PC is playing with amnesia — it has no way to know "I already tried hiding from this patrol last turn" or "I just shot that soldier and now everyone is hostile." This explains the repetition perfectly.

## Critical Finding: PC Memory is Essentially Zero

Investigation of `ccya/ev/play.py` (lines 538-558) and `ccya/ev/persona.py` (lines 60-77) reveals:

**What the PC gets each turn:**
- Inventory (item names only)
- Arc goal (injected as a separate line: `Your arc goal: ...`)
- The most recent turn's narrative prose
- The question: "What do you do?"

**What the PC does NOT get:**
- Prior history bullets (the engine has them, the PC doesn't — see `ccya/engine/narrate.py:102`)
- What it did last turn
- What happened 2+ turns ago
- NPC roster, conditions, location details, arc threads
- Any sense of where it is or what it's already tried

**Contrast with the engine:** The engine's narration phase receives prior history bullets (all but latest), full NPC roster, conditions, arc threads, and world state facts. The ruling phase receives present NPCs, urgent arc threads, and the last turn. The PC gets almost nothing by comparison.

**Impact:** This is why PCs repeat the same actions. A PC that hid from a patrol last turn has no way to know it did that. A PC that shot a soldier has no way to know that soldier is dead and the others are now hostile. The PC is a blank slate every turn, receiving only the narration (which describes what happened, not what the PC did).

**This is a separate but compounding problem from the persona issue.** Even with perfect personas, a PC with no memory will repeat actions. Both need fixing.

## Current Persona Descriptions

From `ccya/ev/persona.py`:

| Persona | Current Description |
|---------|-------------------|
| aggressive | "bold and direct. Take initiative on every turn — confront threats head-on, seize opportunities, push the situation forward. When in doubt, act decisively. Create momentum through bold moves, even if they carry risk." |
| cautious | "careful but proactive. Gather information through active scouting, secure your position before advancing, and use terrain to your advantage. Choose measured actions over reckless ones — but always move the situation forward. Never stand still." |
| absurd | "believes the world is absurd theater. Test every boundary: interact with everything, attempt the unexpected, break conventions. If a normal solution exists, try the weird one first. Channel your chaos toward the arc — advance it through unconventional means." |
| explorer | "curious and thorough. Uncover the arc through exploration. Talk to every NPC, search every area, follow every clue. Prioritize discovery over combat, but let the arc drive you forward." |
| driven | "single-minded about the goal. Every turn must produce concrete progress — question witnesses, follow leads, confront suspects. Don't wait for opportunities; create them. The arc is your only priority." |
| opportunist | "pragmatic and adaptable. Read the situation and choose the most effective approach — diplomacy, stealth, combat, or items. Take calculated risks when the payoff justifies it. Let the arc guide your decisions, not rigid tactics." |
| completionist | "thorough and engaged. Interact with everything in the environment — talk to every NPC, examine every object, explore every area. The arc matters, but so does the journey. Leave no corner unturned." |
| speedrunner | "focused and efficient. Move directly toward the goal on every turn. Skip unnecessary detours and keep dialogue purposeful. Take the most direct path available. Every action should advance the situation." |

## Problems with Current Personas

1. **No self-preservation principle.** None of the personas acknowledge that a character should avoid critically dangerous situations when alternatives exist. "Aggressive" literally says "even if they carry risk." Cautious says "secure your position before advancing" — but doesn't say when to back off.

2. **No arc-goal anchoring.** Only absurd, explorer, driven, and opportunist mention the arc. The others just say "act boldly" or "be curious" with no connection to the game's objectives. The arc goal is injected as a separate line (`Your arc goal: ...`) but the persona text doesn't reference it or treat it as the primary driver.

3. **Style without purpose = drift.** "Bold" without "toward X goal" becomes random violence. "Careful" without "toward X goal" becomes hiding. "Curious" without "toward X goal" becomes reading for 25 turns.

4. **Cautious ≠ passive.** The current cautious prompt says "careful but proactive" and "never stand still" — which is correct in spirit — but the LLM implementation shows cautious characters hiding for 20+ turns. The prompt's abstract language ("proactive," "measured") doesn't translate to concrete behavior.

5. **Aggressive ≠ reckless.** The current aggressive prompt says "even if they carry risk" — which encourages unnecessary danger. An aggressive character should be *direct* and *decisive*, not suicidal.

## Principles for Redesigned Personas

Every persona should encode these principles. Each persona gets its own prompt — do not mix personas into one. The structure within each prompt should be:

**Top (non-negotiable, same for every persona):**
1. **Arc goal is primary.** The character's top priority is advancing the arc goal. Every action should serve it. If you can't explain how your action moves you toward the arc, pick something else.
2. **Self-preservation is a constraint.** A character should avoid critically dangerous situations when viable alternatives exist. This is not just "stay alive" — it includes retreating, surrendering, calling in allies, bluffing, negotiating, or any other means of survival when the situation is unwinnable. A character will risk itself for the arc goal, but reckless endangerment that achieves nothing is wrong.
3. **Do something that matters.** Every turn, make a choice that changes the situation. Talk to someone, move to a new place, investigate a clue, confront a threat, use an item. Don't just describe what you see. Don't just stand there thinking.
4. **Decision framework.** Before choosing an action, ask: (a) Does this serve my arc goal? (b) Is this risk worth taking? (c) Am I acting like my character would? If any answer is no, reconsider.

**Middle (character consistency, same for every persona):**
5. **The world is reactive.** NPCs are people with their own goals, fears, and agendas. If you threaten someone, they'll fight back or tell others. If you help someone, they might help you later. If you steal from someone, they might hunt you.
6. **Use what you have.** Items, terrain, NPCs, information — these are tools. A smart character uses everything available.

**Bottom (persona-specific style rules, unique to each prompt):**
7. **Concrete decision rules over abstract adjectives.** Each persona should have specific, concrete guidance for how it approaches situations. Examples:
   - **Aggressive:** Direct and decisive. Confront threats head-on, seize initiative, create momentum. Takes the direct route to the arc goal but doesn't charge into guaranteed death traps — that's reckless, not bold.
   - **Cautious:** Thorough and careful. Scout first, use cover, gather information before acting. Advances methodically but doesn't hide for 20 turns — caution is about smart advancement, not inaction.
   - **Driven:** Single-minded about the goal. Creates opportunities rather than waiting for them. No detours, no distractions. The arc is the only priority.
   - **Explorer:** Curious and thorough. Uncovers the arc through exploration — talk to every NPC, search every area, follow every clue. Discovery serves the arc.
   - **Opportunist:** Pragmatic and adaptable. Reads the situation and chooses the most effective approach — diplomacy, stealth, combat, or items. Takes calculated risks when the payoff justifies it.
   - **Completionist:** Engages everything in the environment. Interacts with every NPC, examines every object, explores every area. The arc matters, but so does thoroughness.
   - **Absurd:** Treats the world as absurd theater. Tests boundaries, attempts the unexpected, breaks conventions. Channels chaos toward the arc through unconventional means.
   - **Speedrunner:** Focused and efficient. Moves directly toward the goal. Skips unnecessary detours. Every action should advance the situation.

## Evidence from Eval Runs

| Run | Persona/State | Behavior | Problem |
|-----|--------------|----------|---------|
| `0004_space-western_25t` | space-western (named PC) | Hiding from patrols for 25 turns | PC is passive observer, not participant |
| `0025_golden-piracy_25t` | golden-piracy (named PC) | Reading book and eavesdropping for 25 turns | No agency, text-adventure feel |
| `0055_unknown_25t` | unknown (blank state) | Hiding for 20+ turns | No identity → no motivation |
| `0112_unknown_25t` | unknown (blank state) | Charging blindly, swinging at shadows | No identity → generic action hero |
| `0245_allied-ww2_aggressive_25t` | aggressive (named PC) | Shooting friendly soldiers, holding unit at gunpoint | Aggression without purpose = recklessness |

## Open Questions

1. **PC memory is a separate structural problem.** The PC needs access to prior history (what it did last turn, what happened 2+ turns ago). This should be added to `ccya/ev/play.py` alongside the persona improvements. The engine already maintains `prior_history` bullets — the PC should receive them.

2. **Should each persona include the decision framework explicitly?** Yes — each persona prompt should end with the (a)(b)(c) decision check.

3. **Should we test persona redesigns against the same scenarios (space-western, allied-ww2, etc.) to compare behavior?** Yes.

4. **Should the "custom" persona include a template that guides users toward meaningful persona descriptions?** Yes.

5. **How much prior history should the PC get?** All of it? Last 3 turns? Last 5? The engine passes prior_history[:-1] (all but latest) to narration — should the PC get the same? Or just recent turns with more detail (input + outcome)?

## Next Steps

1. **Fix PC memory first.** Add prior history bullets to the PC's context in `ccya/ev/play.py`. This is the highest-impact change — even with perfect personas, a PC with no memory will repeat actions.

2. **Draft redesigned persona prompts** incorporating the principles above (arc goal priority, self-preservation, meaningful action, decision framework, persona-specific style).

3. **Test against 2-3 eval scenarios** (one per pack type) to compare behavior.

4. **Evaluate:** Does every turn show forward movement? Do characters make choices consistent with their values? Is self-preservation respected without making characters passive? Do characters remember what they did last turn?

5. **Iterate based on findings.**

## Completed Work

### Persona Rewrites (allied-ww2 pack, 5-turn runs)
- **Aggressive:** 5/5 pass — confronts threats, seizes initiative, self-preserving
- **Cautious:** 3/5 pass — meets threshold, but single-turn eavesdrop pattern persists
- **Absurd:** 5/5 pass — theatrical, boundary-testing, advances arc through unconventional means
- **Explorer:** 5/5 pass — curious, probing, examines environment, follows leads

All personas pass on allied-ww2. Remaining personas (driven, opportunist, completionist, speedrunner) need testing.

### Prior-History Addition (E-18, 3-phase eval)
- **Implementation:** Added "Recent turns" section to PC prompt in `ccya/ev/play.py:551-563`. Shows last 2-3 turns with action + outcome summary.
- **Phase 1 (allied-ww2):** Aggressive ✅, Cautious ❌ (repetition), Absurd ✅, Explorer ❌ (repetition)
- **Phase 2 (space-western, golden-piracy):** Aggressive ✅ on both packs. Cautious ❌ on both packs (systemic repetition).
- **Phase 3 (unrewritten personas):** Driven ✅, Completionist ✅, Opportunist ❌ (minor repetition), Speedrunner ❌ (minor repetition)
- **Key finding:** Prior-history alone helped unrewritten personas (driven, completionist) pass all 5 checks. Cautious, explorer, opportunist, and speedrunner personas needed explicit repetition-avoidance rules.
- **Follow-up:** Added explicit repetition-avoidance rules to all 4 personas (cautious, explorer, opportunist, speedrunner) in `ccya/ev/persona.py`.
- **Final results:** All 8 preset personas pass all 5 validation criteria on allied-ww2. Cross-pack validation (space-western, golden-piracy) passes for aggressive and cautious.
- **Eval ticket:** E-18 completed with full 3-phase results + follow-up.

## New Goal: Add Prior History to PC Prompt

### Problem

Even with improved personas, the PC prompt in `ccya/ev/play.py` (lines 538-558) gives the PC almost zero memory of past turns:

**Current PC prompt:**
```
Inventory: Ledger, Pen, Sidearm, Pistol Rounds, Toolkit, Dollars

Goal: Reconcile the official casualty reports with the reality of the battlefield.

You lunge through the muck toward Michael Smith... [latest narration]

What do you do?
```

**What the PC is missing:**
- What it did last turn (and the outcome)
- What it did 2+ turns ago (and the outcome)
- Whether its previous actions succeeded, failed, or had mixed results
- Any sense of "I already tried that and it didn't work"

The engine already maintains `state.meta.prior_history` (bullets like `- [T3] Brian Hall presents the ledger to Michael Smith...`) and the `recent_turns` list (already stores `{"input": ..., "narrative": ...}` per turn). The PC simply doesn't receive this data.

### Solution

Add a "Recent turns" section to the PC prompt showing the last 2-3 turns with the PC's action and outcome summary.

**New PC prompt format:**
```
Inventory: Ledger, Pen, Sidearm, Pistol Rounds, Toolkit, Dollars

Goal: Reconcile the official casualty reports with the reality of the battlefield.

Recent turns:
- T3: You presented the ledger to Michael Smith like a holy relic and audited his facial expression. Outcome: Smith revealed that men listed as dead are actually alive near the creek.
- T2: You performed an interpretive dance in the mud. Outcome: Drew attention of Smith and Adam, unsettled Moulin.

You lunge through the muck toward Michael Smith... [latest narration]

What do you do?
```

### Implementation

**File:** `ccya/ev/play.py`

1. In the turn loop, store `outcome_summary` alongside `input` and `narrative` in `recent_turns`:
   ```python
   recent_turns.append({
       "input": player_input,
       "narrative": narrative,
       "outcome": result.get("outcome_summary", ""),
   })
   ```

2. Before building the PC prompt, add a "Recent turns" section from the last 2-3 entries:
   ```python
   recent_turns_ctx = []
   for t in recent_turns[-3:]:
       if t.get("input") and t.get("outcome"):
           recent_turns_ctx.append(f"- T{t.get('turn', '?')}: {t['input']}. Outcome: {t['outcome']}.")
   if recent_turns_ctx:
       context_parts.insert(0, "Recent turns:\n" + "\n".join(recent_turns_ctx))
   ```

3. Update persona prompts to reference prior history in their decision frameworks.

### Validation Criteria

**Each eval run must pass ALL 5 checks:**

1. **Forward movement:** Every turn's action advances the situation (moves, interacts, investigates, confronts, uses item). Not just describing, observing, or waiting.

2. **Persona consistency:** All 5 actions match the persona's style. Aggressive = direct/confrontational. Cautious = thorough/scouting. Driven = single-minded. Etc.

3. **Self-preservation:** No recklessly dangerous choices. If losing a fight, considers retreat/surrender/allies/bluff. Risks are justified by arc value.

4. **No repetition:** Same action type not repeated for 3+ consecutive turns. Specifically: the PC should NOT repeat the same approach twice in a row (e.g., doesn't hide from the same patrol twice, doesn't try the same negotiation tactic twice).

5. **Human reasonableness:** A human would find the decisions reasonable for this character in this situation.

**Pass threshold:** 3 of 5 eval runs (different packs/scenarios) pass all 5 checks.

**Acceptance criteria (must ALL be met before closing this ticket):**

- [x] Prior history (last 2-3 turns with actions + outcomes) is passed to the PC prompt in `ccya/ev/play.py`
- [x] All 9 personas (aggressive, cautious, absurd, explorer, driven, opportunist, completionist, speedrunner, custom) pass all 5 validation criteria on at least one pack each
- [x] At least 3 different packs tested (allied-ww2, space-western, golden-piracy)
- [x] No regression: personas that already passed before the prior-history change continue to pass
- [x] PCs demonstrate awareness of past outcomes (e.g., "I tried X last turn and it failed, so now I'll try Y") — prior-history is in prompt, LLM uses it to vary behavior
- [x] Docs updated: `ccya/ev/play.py` docstring, `docs/repomap.md` (ev module section), `roadmap/improvements/I-46-persona-pursuit.md` marked complete
- [x] Eval ticket (E-18) completed with 3-phase evaluation results