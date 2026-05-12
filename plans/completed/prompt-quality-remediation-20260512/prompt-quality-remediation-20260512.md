# Prompt Quality Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`completed`

## Objective
Several prompt defects caused spurious rules rolls, fail-band narration that read like partial successes, missing or ignored pressure directives, missing inventory and quest updates, and wasted tokens across the pipeline. These are not engine bugs; they are prompt-spec and few-shot gaps. This plan refactors the prompts and examples for rules, narrate, extract_scene, extract_state, and extract_progress to (1) eliminate known spurious decision patterns, (2) make high-severity directives (fail bands, pressure) unambiguous and binding, and (3) trim cross-prompt redundancy while keeping observability.

## Non-goals
- Changing engine or state logic (`apply_delta`, `_validate`, compactor sanitization) — covered in mechanical and system-cohesion plans.
- Changing eval auto-checker expectations or tokenization — covered in an eval harness plan.
- Redesigning the beat/pressure system beyond what prompt wording can influence.
- Rewriting scenario fixtures; this plan assumes existing fixtures but may call out needed updates.

---

## Implementation — Phase 01: Rules no-roll and payment exceptions

### Files to pull for context
- `docs/REPOMAP/prompts.md`
- `ccya/prompts/rules_system.j2` (rules system prompt)
- `ccya/prompts/rules_user.j2` (rules user prompt)
- `ccya/engine/rules.py` (`_rules_messages`)

### Detailed steps

#### Step 1.1 — Add explicit "no-roll movement" few-shots

**File:** `ccya/prompts/rules_system.j2`

**What:** Append a new section after the existing prose rules (after line 26, the payment exception line) with at least two concrete examples where the correct output is `required=false` for pure movement or movement + retrieval from own inventory.

**Why:** T1 and T12 rolled checks for "walk over and sit down" and "grab item from own coat and sprint," which should be automatic. The prose rule exists at line 24 but is not grounded in examples, and the model defaulted to "when in doubt, roll."

**Code Snippet** — append to `ccya/prompts/rules_system.j2` after the existing prose rules (after line 26):
```jinja
## No-roll movement examples

These examples illustrate when `check.required` must be `false`:

- User: "I walk over to Caron's table and sit down."
  Required: false
  Reason: Pure approach/sit action with no resisting force; no one is blocking the way, no threat, no obstacle.

- User: "I pull the ledger from my own coat pocket and stride out the door at a normal pace."
  Required: false
  Reason: The item is already in the PC's inventory, and the movement is not contested or chased.

- User: "I walk through the corridor to the airlock."
  Required: false
  Reason: Unimpeded movement in the same scene with no obstacle or opposition.
```

**Validation:** After implementation, run the existing eval scenario that produced T1/T12. Inspect `rules` responses to confirm `required=false` on those inputs.

---

#### Step 1.2 — Clarify willing-merchant payment exception with example

**File:** `ccya/prompts/rules_system.j2`

**What:** Add a focused example and a short "exception" subsection describing when payment negotiations with a willing NPC do *not* roll. This extends the existing prose rule at line 26.

**Why:** T3 treated a willing merchant payment ("Halden offering courier job, Aren naming a price") as a charisma check because the payment exception was buried in prose and never exemplified.

**Code Snippet** — append to `ccya/prompts/rules_system.j2` after the no-roll movement examples (or as a new subsection under the existing payment prose at line 26):
```jinja
## Payment exception example

- User: "Halden offers me a courier job for 500 credits. I say, 'Make it 600 and you've got a deal.'"
  NPC intent: Halden wants the job done and is already willing to pay.
  Required: false
  Reason: This is ordinary haggling with a willing merchant. The worst outcome is "no deal." When an NPC is already willing to pay and the only risk is the deal not happening, do NOT roll. Just let the narrator resolve the price or end the offer.
```

**Validation:** Re-run the T3 scenario with the same pack; confirm the rules step produces `required=false` and an explanation citing the payment exception.

---

### Tests to write or update
- Update or add a rules-LLM FakeLLM test (in `tests/test_engine_smoke.py` or `tests/test_rules.py`) that feeds the T1/T12 and T3 texts into `_rules_messages` + FakeLLM and asserts parsed outputs have `required=false` with the expected reasoning patterns.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: document that rules prompts now include explicit no-roll movement/payment examples.

### Risks
1. Over-generalizing the payment exception could remove legitimate social rolls (e.g., extorting money). Mitigation: examples must emphasize "already willing, stakes are just price or deal/no-deal."

---

## Implementation — Phase 02: Narrate fail bands and pressure directives

### Files to pull for context
- `docs/REPOMAP/prompts.md`
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/engine/narrate.py` (`_narrate_messages`)

### Detailed steps

#### Step 2.1 — Harden fail-band directive against partial outcomes

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a new section after the existing band/directive guidance (after the "This Turn's Result" section in the user prompt context, but as a system-prompt rule) with an explicit prohibition against constructive NPC engagement on `fail` bands and show one or two counter-examples of what *not* to do.

**Why:** At T1/T3, fail-band narration had Caron engaging constructively (parchment, proof demand) and Halden counter-offering split payment; these read as partial success.

**Code Snippet** — add to `ccya/prompts/narrate_system.j2` after the existing style sections (before the `## Output discipline` section around line 89):
```jinja
## Fail-band outcomes (BINDING)

On a FAIL band:
- The PC does not get what they asked for.
- The NPC does NOT engage constructively to help them.
- The NPC may refuse, stall, shut them down, or walk away.

NEVER on FAIL:
- Do not have the NPC offer a counter-deal, partial payment, or softened demand.
- Do not turn FAIL into PARTIAL by giving the PC a consolation prize.

Bad (do NOT do this on FAIL):
  Caron leans back, smiles thinly, and offers a different payment schedule.
Good (correct FAIL):
  Caron closes the ledger and says, "Then we have nothing to discuss," turning away.
```

**Validation:** Re-run T1/T3 scenario; check that `fail` bands now produce narration with outright refusals or shutdowns, no counter-offers.

---

#### Step 2.2 — Make pressure directive a binding weaving instruction

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a new section in the system prompt that, when `scene_pressure` is provided in the user context, instructs the model to quote or paraphrase the active pressure text in the first 2–3 sentences. The `scene_pressure` context is already passed via `_narrate_messages` (line 34 of `narrate.py`) and rendered in `narrate_user.j2` under "Active Threats" (line 37-41).

**Why:** Even when the pressure directive was present in the prompt, the narrator often ignored it or deferred it deeper into the paragraph.

**Code Snippet** — add to `ccya/prompts/narrate_system.j2` after the existing sections (before `## Output discipline` around line 89):
```jinja
{% if scene_pressure %}
## Active pressures (BINDING)

The following pressures are active right now. You MUST weave the current pressure into your opening:
- In the FIRST 2–3 sentences, explicitly reference the active pressure text below.
- Do not bury this in the middle or end of the narration.

Active pressures:
{% for p in scene_pressure %}- [{{ p.urgency | upper }}] {{ p.text }}
{% endfor %}

If you do NOT mention this pressure in the opening, your answer is incorrect.
{% endif %}
```

**Validation:** For turns with immediate pressures (like T9–T12), confirm the first lines of narration explicitly mention the pressure text.

---

### Tests to write or update
- A FakeLLM snapshot test that feeds `_narrate_messages` a state with `scene_pressure` active and asserts the rendered user prompt includes the "FIRST 2–3 sentences" instruction and the pressure text.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: narrate section should note the explicit pressure weaving requirement and the strengthened fail-band semantics.

### Risks
1. Over-constraining fail bands and pressure could make narration feel repetitive. Mitigation: examples should show variety in how failure/pressure is described, not just the fact that it occurs.

---

## Implementation — Phase 03: Extractor prompts (inventory, quests, scenes)

### Files to pull for context
- `docs/REPOMAP/prompts.md`
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_system.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/engine/extraction.py` (to see what context each extractor actually receives)

### Detailed steps

#### Step 3.1 — Add key-use and NPC-payment examples to extract_state

**File:** `ccya/prompts/extract_state_system.j2`

**What:** The `extract_state_system.j2` already has a "Spending/giving examples (FEW-SHOT)" section at lines 71-77. Add new examples for key use and NPC paying the PC, extending this existing section.

**Why:** T8 did not remove the brass key after use; T3 likely failed to add Halden's 100 credits; T13 ignored vague payment.

**Code Snippet** — extend the existing "Spending/giving examples (FEW-SHOT)" section in `ccya/prompts/extract_state_system.j2` (after line 77):
```jinja
- Narration: `"You slide the brass key into the lock. It turns with a click and the door swings open."` → `{"inventory_remove": [{"id": "brass_key"}]}` (full remove, no amount)
- Narration: `"Halden counts out a hundred credits into a small pouch and presses it into your hand."` → `{"inventory_add": [{"id": "credits", "amount": 100}]}`
- Narration: `"You press a few coins into the dock boy's palm."` → `{"inventory_remove": [{"id": "credits", "amount": 1}]}` (use 1 when an unspecified small payment occurs)
```

Note: The vague payment example already exists at line 73 with `amount: 5`. Update it to `amount: 1` to match the plan's intent for minimal vague payments.

**Validation:** Re-run T8/T13 equivalent narratives through extract_state; verify key removal and vague payment removal are emitted.

---

#### Step 3.2 — Quest dedup and auto-close few-shots in extract_progress

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Add a "NEVER DO THIS" subsection to the existing quest dedup rules (around lines 29-45) demonstrating what *not* to do after a quest just completed.

**Why:** T2/T7 re-emitted just-completed quests as `status: active`, colliding with engine auto-close.

**Code Snippet** — add to `ccya/prompts/extract_progress_system.j2` after the existing few-shot examples (after line 40):
```jinja
- **NEVER emit a completed quest again:**
  State says: `settle_the_debt.status = "completed"`
  Narration: "You shake hands; the debt is settled."
  Wrong extract: `{"id": "settle_the_debt", "status": "active", "objectives": [...]}` — This is WRONG. Do not re-activate completed quests.
  Correct extract: (omit entirely — the quest is already completed, no update needed)
```

**Validation:** Use a test state where a quest is already `completed`; feed it and a neutral narration through progress extractor; assert no quest update is emitted.

---

#### Step 3.3 — Add standoff/confrontation scene-tag examples

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add new examples after the existing NPC examples (after line 63) explicitly mapping verbal confrontations and tense standoffs to tags such as `standoff`, `tense_confrontation`, or `intimidation`.

**Why:** The scene extractor left T5 untagged; the checker's expectation of `combat` was wrong, but *some* tension tag should be emitted.

**Code Snippet** — add to `ccya/prompts/extract_scene_system.j2` after the existing examples (after line 63):
```jinja
EXAMPLE — Standoff / tense confrontation:
Narration: "Two armed toughs block the doorway, hands hovering near their weapons as you argue."
→ Emit: `scene_tags: ["standoff", "intimidation"]`

EXAMPLE — Verbal confrontation:
Narration: "The guard captain steps into your path, hand on his baton, and demands your papers."
→ Emit: `scene_tags: ["tense_confrontation", "intimidation"]`
```

**Validation:** Feed a T5-like narration through extract_scene; assert one of the tension tags appears.

---

### Tests to write or update
- `tests/test_extract_state_inventory_examples.py` — verify example narratives produce expected JSON.
- `tests/test_extract_progress_quest_dedup.py` — verify completed quests in state are not re-emitted.
- `tests/test_extract_scene_standoff_tag.py` — verify standoff narration yields `standoff` or `intimidation`.

These new test files should follow the pattern in `tests/test_engine_smoke.py` using `_FakeLLM` and `_build_jinja_env`.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: update extract_state/extract_progress/extract_scene sections to mention these new example patterns and rules.

### Risks
1. Using `amount: 1` for all vague payments might under-state larger implied transactions. Mitigation: keep the rule clearly "small payment" and rely on scenario writers to specify large amounts explicitly.

---

## Implementation — Phase 04: Cross-prompt token cuts

### Files to pull for context
- `docs/REPOMAP/prompts.md`
- `ccya/prompts/extract_scene_system.j2`, `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_system.j2`, `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/extract_progress_system.j2`, `ccya/prompts/extract_progress_user.j2`
- `ccya/engine/extraction.py` (`_extract_scene_messages`, `_extract_state_messages`, `_extract_progress_messages`)
- `ccya/engine/narrate.py` (`_known_characters_for_extract`, `build_state_slice`)

### Detailed steps

#### Step 4.1 — Remove PC stats from non-rules/narrate prompts

**Files:** `ccya/prompts/extract_scene_user.j2`, `ccya/prompts/extract_state_user.j2`, `ccya/prompts/extract_progress_user.j2`

**What:** 
- `extract_scene_user.j2`: Does NOT include PC stats currently — no change needed. The context passed to it includes `pc` but the template only renders `location`, `present_npcs`, `npc_roster`, `recent_turns`, and `narration`.
- `extract_state_user.j2`: Currently includes `pc.name` and `pc.tagline` (lines 1-2). Remove these two lines — the state extractor does not need PC identity to parse inventory/conditions.
- `extract_progress_user.j2`: Currently includes `pc_stats` block (lines 4-8). Remove this block — the progress extractor does not need raw stat values for quest/recent-events reasoning.

**Why:** PC stats were duplicated across prompts; scene/state/progress do not need them and they cost tokens. Rules and narrate prompts still include PC stats (via `rules_user.j2` line 3 and `narrate_user.j2` via `_pc.j2`).

**Code Snippet** — in `ccya/prompts/extract_state_user.j2`, remove lines 1-2:
```jinja
## pc
{{ pc.name }} — {{ pc.tagline }}
```
Replace with just the conditions/inventory blocks that follow.

**Code Snippet** — in `ccya/prompts/extract_progress_user.j2`, remove lines 1-8:
```jinja
## pc
{{ pc.name }} — {{ pc.tagline }}

{% if pc.stats -%}
## pc_stats
{% for k, v in pc.stats.items() %}- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}
```
Replace with just the `present_npcs` block that follows.

**Validation:** Confirm via the templates that only rules/narrate prompts render PC stats; rerun an eval to verify extractor behavior is unchanged.

---

#### Step 4.2 — Remove NPC bios duplication in scene prompt

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** The `present_npcs` block (line 7) includes `bio` for each NPC. The `npc_roster` block (line 13) also includes `bio`. These are redundant — `npc_roster` already provides full compendium bios. Remove `bio` from `present_npcs` rendering.

**Why:** The same NPC bios appeared in both `present_npcs` and `npc_roster`, wasting tokens.

**Code Snippet** — in `ccya/prompts/extract_scene_user.j2`, change line 7 from:
```jinja
{% for n in present_npcs %}- `{{ n.id }}` | {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %} — {{ n.bio or "No bio available" }}{% if n.notes %} — {{ n.notes }}{% endif %}{% if n.last_seen %} — last seen in {{ n.last_seen.location_name }}: {{ n.last_seen.last_seen_state }}{% endif %}
```
To:
```jinja
{% for n in present_npcs %}- `{{ n.id }}` | {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}{% if n.last_seen %} — last seen in {{ n.last_seen.location_name }}: {{ n.last_seen.last_seen_state }}{% endif %}
```

**Validation:** Render the scene user prompt for a known state and verify `present_npcs` no longer includes `bio` text while `npc_roster` still does.

---

#### Step 4.3 — Compress last_turn_narration in progress prompt

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Replace the full `recent_turns[-1].narrative` inclusion (lines 107-110) with a truncated version. The engine already passes `recent_turns` as a list of dicts with `narrative` fields. Truncate to the last 300 characters of the narrative.

**Why:** Full narrative duplication in progress prompts added ~2.6k tokens/run with no evidence of quality gains.

**Code Snippet** — in `ccya/prompts/extract_progress_user.j2`, change lines 107-110 from:
```jinja
{% if recent_turns -%}
## last_turn_narration (T{{ recent_turns[-1].turn }})
{{ recent_turns[-1].narrative }}

{% endif -%}
```
To:
```jinja
{% if recent_turns -%}
## last_turn_narration (T{{ recent_turns[-1].turn }})
{% set _prev = recent_turns[-1].narrative %}{{ _prev[-300:] if _prev|length > 300 else _prev }}

{% endif -%}
```

**Validation:** Render the progress user prompt for a known state and verify the last-turn narration is truncated. Rerun eval to verify quest extraction quality does not regress.

---

### Tests to write or update
- Prompt snapshot tests (add to `tests/test_engine_smoke.py` under a new `TestTokenCuts` class) that render each prompt for a known state and assert:
  - `extract_scene_user.j2` does not contain PC stats.
  - `extract_state_user.j2` does not contain `pc.name` or `pc.tagline`.
  - `extract_progress_user.j2` does not contain `pc_stats`.
  - `extract_scene_user.j2` `present_npcs` does not include `bio`.
  - `extract_progress_user.j2` last-turn narration is truncated to ≤300 chars.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: update each prompt section to describe the leaner context shapes.

### Risks
1. Some few-shot examples might rely on seeing full prior narration in progress prompts. Mitigation: keep a 300-char truncation and verify with eval that quest extraction quality does not regress.
2. Removing NPC bios from `present_npcs` may degrade scene extractor's ability to pick the right tags in edge cases; mitigate by keeping bios in `npc_roster` and documenting that explicitly.

---

## Ambiguities requiring resolution before execution

1. **Exact filenames and locations of templates** — resolved: all prompt templates are in `ccya/prompts/`, not `templates/`. The `templates/` directory contains HTML templates for the web UI.

2. **Whether a summarization helper already exists for `last_turn_narration`** — no dedicated summarization helper exists. Decision: use Jinja2 truncation (`[-300:]`) in `extract_progress_user.j2` rather than adding an LLM call. This is simpler and avoids extra latency.

3. **Whether any existing tests assert on full prompt text that will need updating after token cuts** — `tests/test_engine_smoke.py` has snapshot-style assertions (e.g., `test_extract_scene_no_inventory`, `test_extract_state_user_contains_inventory`) that check for specific substrings in rendered prompts. These will need to be updated if the token cuts remove sections they assert on. Specifically:
   - `test_extract_state_user_contains_conditions` checks for `"injured"` in user content — this will still pass since conditions are not removed.
   - `test_extract_progress_user_contains_quests` checks for `"quiet-signal"` — this will still pass since quests are not removed.
   - No existing test asserts on the presence of `pc_stats` or `pc.name` in extract prompts, so no test changes are needed for the token cuts themselves.

---

## Affected Files

| File | Change |
|---|---|
| `ccya/prompts/rules_system.j2` | Add no-roll movement and payment exception examples |
| `ccya/prompts/narrate_system.j2` | Add fail-band prohibition and pressure weaving sections |
| `ccya/prompts/extract_scene_system.j2` | Add standoff/confrontation scene-tag examples |
| `ccya/prompts/extract_state_system.j2` | Extend spending/giving examples with key-use and NPC-payment |
| `ccya/prompts/extract_progress_system.j2` | Add NEVER example for completed quest dedup |
| `ccya/prompts/extract_scene_user.j2` | Remove `bio` from `present_npcs` rendering |
| `ccya/prompts/extract_state_user.j2` | Remove `pc.name` / `pc.tagline` header |
| `ccya/prompts/extract_progress_user.j2` | Remove `pc_stats` block; truncate `last_turn_narration` |
| `docs/REPOMAP/prompts.md` | Document new examples and leaner context shapes |
| `tests/test_engine_smoke.py` | Add token-cut snapshot tests |
| `tests/test_extract_state_inventory_examples.py` | New: verify inventory example narratives |
| `tests/test_extract_progress_quest_dedup.py` | New: verify completed quest dedup |
| `tests/test_extract_scene_standoff_tag.py` | New: verify standoff scene tags |
