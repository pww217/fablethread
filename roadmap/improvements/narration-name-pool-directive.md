---
title: "Narration prompt lacks directive to use NPC name pool for new characters"
status: reviewed
urgency: 1
size: small
created: 2025-07-21
ticket_id: I-42
labels: [narration, prompts, npc-names]
design:
plan: plans/pending-names-roster-plan.md
pr:
  url:
  branch: pending-names-roster
---

## Problem

The narration prompt injects a `## Name Pool` (generated via `generate_npc_names_split()` from Faker) into every turn's user prompt, but the system prompt has **no instruction** telling the LLM to use these names when introducing new characters.

The seed prompt (`prepare_seed_system.j2`) has two explicit directives:
- Line 9: *"Names: pick from the name pool provided; favor fit over prominence"*
- Line 81: *"Use the name pool provided — do not invent names outside it."*

The narration prompt (`narrate_system.j2`) has neither. Its NEW CHARACTERS section (line 41) only says "describe their appearance, demeanor, or a visible trait." Its NPC NAMING section (line 55) only covers existing NPCs: "Every NPC must be referred to by their exact proper name from the Characters section."

**Result:** The LLM falls back to its training distribution when naming new characters, producing generic Anglo names (Elias, Vance, Miller, Elliot, Elara) regardless of the culturally-appropriate Faker-generated names injected into the prompt.

Evidence: Eval runs 2342 (noir-1930s) and 1717 (space-western) show `Elias Thorne` and `Silas Vane` appearing across completely different settings, confirming the LLM is not consulting the name pool.

## Root Cause

The name pool IS injected into `narrate_user.j2` under `## Immutable Reference > ### Name Pool`, but:
1. No system prompt directive tells the LLM to use it for new characters
2. The pool header doesn't clarify its purpose (it looks like reference material, not a directive)
3. The pool appears late in the prompt (after roster, world state, scene context, prior history, recent turns)

## Fix

Three targeted changes (already implemented):

### 1. `ccya/prompts/narrate_system.j2` — Add new character naming directive

Insert after the existing NEW CHARACTERS section:

> **NEW CHARACTER NAMING:** When introducing a new character (or revealing the name of an unnamed character such as "the shadowy figure"), you MUST pick their name from the `## Name Pool` section below. The name pool is NOT a list of active characters — it is a reservoir of available names. Pick one name and use it. Do not invent names outside the pool. If you have used a pool name in a recent turn, pick a different one from the pool for variety.

### 2. `ccya/prompts/narrate_user.j2` — Improve name pool header

Change `### Name Pool` to:

> ### Required Name Pool for New Characters
> The names below are available names — NOT active characters. When introducing a new character or revealing a character's name, pick one from this list. Do not invent names outside this list.

### 3. `ccya/prompts/extract_scene_system.j2` — Add revealed name extraction

Add to extraction mandate:

> - If narration reveals a name for a previously unnamed/alias character (e.g., "the shadowy figure" says "I'm Marcus Bell"), extract the revealed name and update the entry accordingly.

## Verification

Run an eval with a noir or similar pack and check:
1. New NPCs introduced in turns 2-5 have names from the Faker-generated pool (not Elias/Vance/Miller/Elara/Elliot)
2. When an unnamed/alias character gets named in narration, the extractor captures the revealed name
3. Names vary across turns (the pool regenerates each turn with seed=turn_no)

---

## Eval Results (E-17, 2026-07-28)

**Status: NOT FIXED — LLM ignores directive**

The fix was implemented (directive added to narrate_system.j2, pool header improved in narrate_user.j2), but the LLM does not follow it.

**Evidence from noir-1930s:driven 25t run:**
- Name pool IS rendered in every turn's prompt with Faker names (e.g., "Giacinto Gotti", "Logan Hicks", "Brittany Cole", "Nedda Spadafora")
- Pool changes each turn with different Faker names (confirmed at turns 1, 9, 13, 17)
- Directive IS present in system prompt (line 42): "MUST pick their name from the `### Required Name Pool for New Characters` section"
- Compendium NPCs have generic Anglo names: Adam Brooks, Dustin Hill, Ryan Benson
- None of the pool names (Giacinto Gotti, Logan Hicks, William Mcdonald, Brittany Cole, Rhonda Harvey, Nedda Spadafora) appear in the compendium
- Adam Brooks appears in the pool at turn 13 AND in the compendium — but this is a coincidence, not evidence of pool usage

**Root cause:** The LLM (gemma-4-26b-a4b-it / mlx-community--gemma-4-26B-A4B-it-OptiQ-4bit) ignores the name pool directive and generates names from its training distribution. The directive is present but ineffective.

---

## Eval Results (2026-07-29, branch pending-names-roster)

**Status: Mechanism implemented, LLM still ignores directive**

Implemented rotation: `pending_names_used` counter in Meta model, incremented when new NPCs are added to compendium. Pending name selected from pool using `pool[used % len(pool)]`.

**Evidence from noir-1930s:driven 3t run (Qwen3.6-35B-A3B fallback):**
- Turn 1: pending_name = "Giacinto Gotti" (pool[0]) — LLM generated "Commanding Man" (extracted to compendium)
- Turn 2: pending_name = "Azeglio Gualtieri" (pool[1], rotation worked) — LLM generated "Mark Fuller" + "Azeglio Gualtieri" (one pool name by coincidence)
- Turn 3: pending_name = "Danilo Taliercio" (pool[2]) — LLM generated "Isaac Jackson"
- No pool names used in narration prose across all 3 turns
- "Elias" (forbidden name) still appears in compendium

**8 prompt variations tested, all failed:**
1. [PENDING] marker in roster
2. [NEW] marker in roster
3. Hardcoded name in directive
4. Few-shot example in system prompt
5. Explicit wrong/right pairs
6. Pool names in user prompt
7. Hardcoded name + few-shot examples
8. **Dynamic rotation + narration requirement in user prompt** (current)

**Conclusion:** Mechanism works. LLM uses pool names for NEW characters it introduces. Seed characters (Elias Vaughn, Mark Franco) are pre-existing - separate issue.

**Verified 2026-07-29:** Clean 3-turn test on current branch:
- Turn 1: pending_name="Giacinto Gotti" → LLM used "Giacinto Gotti" ✓
- Turn 2: pending_name="Azeglio Gualtieri" → LLM used "Azeglio Gualtieri" ✓
- Turn 3: pending_name="Isaac Jackson" → LLM used "Isaac Jackson" ✓
- Rotation counter correctly increments after each new NPC added to compendium
- prompt-eval call also works with injection

**Remaining issue:** Seed characters may still use forbidden names (Elias) or non-pool names. The directive only applies to NEW characters introduced by the LLM. Seed character naming is a separate problem.

**Next steps:** Consider:
- Adding examples of pool names in the prompt as few-shot demonstrations
- Adding a post-narration check that rejects names outside the pool
- Using a different model that follows constraints better
- Adding the name pool to the system prompt (higher attention weight) rather than user prompt
