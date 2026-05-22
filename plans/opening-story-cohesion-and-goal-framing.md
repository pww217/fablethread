# Opening Story Cohesion and Goal Framing

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Seed story framing | Make the initial seed produce a more personal, motivated opening with character-tied NPCs, stronger goal context, and less generic choices. |
| 02 | Early-turn narration | Treat the first turns as a distinct onboarding mode so narration grounds the player before expanding the world. |
| 03 | UI goal framing | Present the arc goal with contextual story framing in the sidebar and surface immediate context more clearly. |

## Objective
Improve the player's first-turn story experience so the game feels personal, legible, and motivated from the start. Today the left sidebar shows the arc goal directly, while richer hover treatment already exists for the player bio and NPC details, which makes the core objective read more like a dry mission label than a meaningful story anchor . The plan should make the seed, narration, and UI cooperate so the player quickly understands three things: who they are in this situation, why the current moment matters to them, and what immediate pressure deserves attention now.

## Non-goals
- Do not redesign the long-term arc/thread system.
- Do not add spoiler-heavy exposition, explicit theme statements, or hidden-truth leakage.
- Do not replace the current compact sidebar layout with a large new panel or modal-first design.
- Do not solve this by dumping more lore into the opening turn.
- Do not make the goal tooltip a restatement of the visible goal text.
- Do not add implementation-only polish work unrelated to story framing, such as broad CSS cleanup or unrelated template refactors.
- Do not change downstream turn resolution logic unless a design requirement here cannot be expressed through existing prompt/template structures.

## Implementation — Phase 01: Seed story framing

### Files to pull for context
- `AGENTS.md`
- `ccya/models.py` (CampaignArc model)
- `ccya/pack.py` (SeedEnvelope, SeedScene models)
- `ccya/prompts/generate_seed_system.j2` (seed prompt template with output schema and field guidance)
- `ccya/templates/_state_left.html` (sidebar rendering — for later phases)
- Relevant `docs/architecture/*` files covering narrative structure, turn-0 flow

### Detailed steps

#### Step 1.1 — Define first-turn narrative contract

**File:** confirmed seed prompt template (`generate_seed_system.j2`)

**What:** Establish a clear design rule that the seed is responsible for producing an emotionally legible opening, not just a structurally valid one. The opening must answer, through scene design rather than summary: why this moment matters now, what the character stands to lose, and why at least one person in the scene matters to them personally.

**Why:** The current experience is over-indexed on abstract story structure and under-indexed on attachment. The executor needs a stable design target so prompt edits do not drift toward "more detail" instead of "more personal relevance."

**Code Snippet**
```python
# No code change in this step.
# The deliverable is documented prompt-design guidance that the later prompt edits implement.
```

**Validation:** The documented contract explicitly distinguishes:
- personal motive vs. visible objective,
- grounding vs. lore,
- attached NPC vs. ambient NPC,
- immediate pressure vs. medium-term arc.

#### Step 1.2 — Add goal-context field to the seed

**File:** `ccya/models.py` (CampaignArc model) and confirmed seed prompt template (`generate_seed_system.j2`)

**What:** Add a one-time generated arc field for goal hover context. This should be 2–3 sentences that explain why the visible goal matters to this character specifically, what inner cost or pressure makes it emotionally loaded, and how it quietly resonates with the larger theme without stating that theme outright.

First: add `goal_context` as a new field on CampaignArc in models.py so Pydantic accepts it during SeedEnvelope parsing (line 288 of seed.py). Then update the prompt schema and guidance to instruct the LLM to generate it.

**Why:** The current Arc card renders only `visible_goal` and thread summaries . The player needs a compact interpretive layer that makes the goal feel owned by the character, not merely assigned by the plot.

**Code Snippet — models.py CampaignArc (line 61–70):**
```python
class CampaignArc(BaseModel):
    visible_goal: str = ""
    thematic_question: str = ""
    hidden_truths: list[str] = Field(default_factory=list)
    discovered_truths: list[str] = Field(default_factory=list)
    threads: list[ArcThread] = Field(default_factory=list)  # unified arc.threads[] replaces active_threads/latent_threads split

    completed_threads: list[ArcThread] = Field(default_factory=list)
    pc_drive: str = ""
    goal_context: str = ""  # NEW: 2–3 sentences explaining why visible_goal matters to this character specifically
```

**Code Snippet — generate_seed_system.j2 output schema (line ~107 and line ~111):**
Update BOTH arc type declarations in the TypeScript-style schema. Line 107 is inside the response JSON schema under "state"; line 111 is a standalone top-level output field. Both must be updated to avoid inconsistent LLM output parsing:

From (both lines):
```ts
arc: {visible_goal: string, thematic_question: string, hidden_truths: string[], discovered_truths: string[], active_threads: ArcThread[], latent_threads: ArcThread[], pc_drive: string} | null,
```
To (both lines):
```ts
arc: {visible_goal: string, goal_context: string, thematic_question: string, hidden_truths: string[], discovered_truths: string[], threads: ArcThread[], completed_threads: ArcThread[], pc_drive: string} | null,
```

**Code Snippet — generate_seed_system.j2 Campaign Arc Generation section (line ~169–178):**
Update the field list to include goal_context with these constraints:
- no hidden-truth spoilers,
- no restating visible_goal,
- no direct statement of the thematic question,
- must connect character motive, story stakes, and emotional cost.

Also update lines 175–176 which currently instruct the LLM to emit `active_threads` and `latent_threads`. CampaignArc uses unified `threads[]` with an `active` boolean flag per thread — if the LLM emits active_threads/latent_threads (as currently instructed), Pydantic validation at seed.py:288 will fail. Replace with instructions for a single `threads` list where each thread has `{id, summary, tags, urgency, scope}` and an `active` field managed by Python age rules, plus a separate `completed_threads` list for resolved/failed threads.

**Validation:** The prompt guidance for `goal_context` makes these constraints explicit as listed above. Pydantic validation at seed.py:288 accepts the new field because it is declared on CampaignArc. Both schema type declarations (line 107 and line 111) are updated to match. Generation instructions (lines 169–178) produce output compatible with CampaignArc model shape — unified `threads[]` instead of split active/latent lists.

#### Step 1.3 — Make opening NPCs relational, not ornamental

**File:** confirmed world-seed prompt template (`generate_seed_system.j2`)

**What:** Change the opening-NPC design so each opening NPC has a defined narrative job. One NPC should be personally tied to the player character's motive or vulnerability; the other should carry immediate external pressure from the world, institution, or conflict pressing on the scene. Require the seed to encode the PC-facing relevance of each NPC, not just who they are in general.

Update both:
1. The output schema for present_npcs at `generate_seed_system.j2` (line ~104) — currently `{id: string, name: string, title: string, notes: string, bio: string}` to add a relation field.
2. The NPC description guidance in the same template.

**Why:** The sidebar already supports richer NPC tooltip content than simple name/title/notes, including fields like motivation, fear, and leverage when present . The opening should use that affordance for attachment, not just exposition.

**Code Snippet — generate_seed_system.j2 output schema (line ~104):**
Update present_npcs type from:
```ts
present_npcs: Array<{id: string, name: string, title: string, notes: string, bio: string}>
```
to:
```ts
present_npcs: Array<{id: string, name: string, title: string, notes: string, bio: string, relation: string}>
```

**Validation:** A seeded opening should fail review if both opening NPCs could be swapped into another scene with minimal changes. At least one must matter specifically to this PC, now.

#### Step 1.4 — Reframe `pc_drive` as latent fuel, not blunt copy

**File:** confirmed world-seed prompt template (`generate_seed_system.j2`)

**What:** Keep `pc_drive`, but do not plan to print it directly as a labeled UI fact. Instead, require the seed to express that motive indirectly through `goal_context`, NPC relations, opening situation, and action language. The drive should be the hidden emotional engine of the opening, not a subtitle.

**Why:** This matches the design goal: preserve subtlety while still making the player feel the character's motivation from the first turn.

**Code Snippet**
```python
# No direct UI field addition for pc_drive in this phase.
# The change is prompt-level: pc_drive must be materially reflected
# in goal_context, present_npcs, opening_narrative, and actions.
```

**Validation:** Reviewers can point to where the drive is felt in the opening without needing a literal "Drive:" label anywhere in the UI.

#### Step 1.5 — Rewrite action guidance around character and scene pressure

**File:** confirmed world-seed prompt template (`generate_seed_system.j2`)

**What:** Change action generation so choices are written as character-shaped, scene-specific moves. Each option should feel like something this character would plausibly choose because of their motive, current relationships, known skills, or pressure from the visible arc.

**Why:** Generic choices flatten the character and undercut the opening. Action text is one of the strongest levers for making the player feel who they are before they type anything.

**Code Snippet**
```text
Actions must:
- be written from the PC's point of view or voice,
- be grounded in a present NPC, immediate risk, active thread, or character motive,
- differ in emotional posture (confront, deflect, investigate, protect, exploit, withdraw, etc.),
- avoid generic verbs that could fit any protagonist in any setting.
```

**Validation:** None of the four starting choices should read like template filler. At least two should reveal something about the character's priorities or relationships.

### Tests to write or update
- Note: tests are temporarily removed during refactor per AGENTS.md policy ("Tests are temporarily removed during refactor"). When test phase resumes, add acceptance criteria for goal_context presence and non-empty relation fields on opening NPCs.

### REPOMAP and architecture updates
- Update the architecture doc that defines seed responsibilities so it explicitly says the seed owns first-turn emotional framing, not just world and arc scaffolding.
- Update the REPOMAP doc for prompts/models to document the new `goal_context` arc field and any new NPC relation field.
- Update any architecture doc describing sidebar semantics so `visible_goal` + `goal_context` are described as paired layers: public objective and private story meaning.

### Risks
1. The model may over-explain the goal context and make it feel like synopsis text; mitigate by stressing "deepen, don't summarize."
2. NPC relevance fields may become formulaic ("owes / fears / needs" every time); mitigate by defining narrative function, not fixed vocabulary.
3. Actions may become too character-voiced and less mechanically legible; mitigate by preserving concrete verbs and scene anchors.

## Implementation — Phase 02: Early-turn narration

### Files to pull for context
- `AGENTS.md`
- The exact narration prompt template (`ccya/prompts/narrate_system.j2`) used for turn narration
- The narration-context assembly file (`ccya/engine/narrate.py`, function `_narrate_messages`)
- The arc subtemplate injected into user prompts (`ccya/prompts/sections/_arc.j2`)
- Relevant `docs/architecture/*` files covering turn flow and narrator responsibilities

### Detailed steps

#### Step 2.1 — Treat turns 0–2 as a distinct narrative mode

**File:** confirmed narration prompt template (`narrate_system.j2`)

**What:** Add an explicit opening-turn instruction block that changes narrator priorities for the first few turns. In this mode, narration should ground the player in person, place, and pressure before broadening into larger arc exposition. The narrator should assume the player has no attachment yet and must create it.

Use approach B below. Approach A (turn counting) is not viable with current context structure: `current_arc` in the system prompt receives `current_arc_ctx` from narrate.py line 110, which does NOT contain a `meta.turn` key — it only has visible_goal, thematic_question, phase, threads, pc_drive, hidden_truths. The turn number is available as `meta.turn` at user-prompt level (user_ctx line 85) but not under current_arc in system context. Approach B avoids this structural dependency entirely and relies on the presence of goal_context itself as the early-turn signal.

**Why:** Early turns are currently being handled like ordinary campaign turns. That loses the onboarding moment and causes the story to feel generic even when the underlying seed has good material.

**Code Snippet — approach B (preferred, no turn counting):**
Add a general instruction block: "When goal_context is present on the arc, treat it as narrative guidance for early turns: ground the player in personal stakes before broad exposition." This avoids turn-counting entirely and relies on the presence of goal_context itself as the signal.

**Code Snippet — approach A (fallback only if meta.turn is added to current_arc_ctx):**
```jinja
{% if current_arc.meta.turn <= 2 %}
# Opening-turn mode
Prioritize personal grounding over broad exposition.
Make the scene legible through one concrete pressure, one personally relevant NPC beat,
and one consequence that matters specifically to this character.
{% endif %}
```

This would require adding `"meta": {"turn": turn_no}` to `current_arc_ctx` in narrate.py (in addition to Step 2.3's goal_context wiring). Only use if turn-counting is preferred over the simpler approach B.

**Validation:** A first-turn narration review should identify:
- one concrete personal stake,
- one NPC moment with emotional charge,
- one immediately actionable pressure,
before any broader lore explanation.

#### Step 2.2 — Use theme as a lens, never a thesis

**File:** confirmed narration prompt template (`narrate_system.j2`)

**What:** Instruct the narrator to let the thematic question shape emphasis and selection rather than direct statement. Theme should influence which details get noticed, what dialogue tension is foregrounded, and what emotional contrast is made legible, but it should not appear as overt moralizing.

**Why:** You want thematic coherence without bluntness. The right design is not "state the theme softly"; it is "let the theme determine what the scene pays attention to."

**Code Snippet**
```text
The thematic question is never stated outright.
Use it as a lens for emphasis: what detail feels loaded, what silence matters,
what tension between people is given weight.
```

**Validation:** Reviewers should be able to infer the thematic pressure after reading a few opening turns, but should not find theme-language paraphrased in narration.

#### Step 2.3 — Make narration consume the seed's emotional scaffolding

**File:** confirmed narration prompt template (`narrate_system.j2`) and context assembly file (`ccya/engine/narrate.py`, function `_narrate_messages`)

**What:** Ensure narration explicitly privileges `goal_context`, opening NPC relational data, and the implicit force of `pc_drive` during early turns. The narrator should not recite these fields; it should convert them into scene texture, dialogue pressure, and what the prose lingers on.

This requires two changes:
1. Add `"goal_context": arc.get("goal_context", "")` to the `current_arc_ctx` dict constructed at narrate.py line 51–68 so goal_context is available in both system and user prompt rendering.
2. Update `_arc.j2` (the subtemplate injected into narration user prompts) to include goal_context as hidden context for the narrator — not displayed to player but used by the LLM for narrative guidance.

**Why:** If Phase 01 creates better emotional scaffolding but narration ignores it, the UX does not improve.

**Code Snippet — narrate.py current_arc_ctx (line ~51–68):**
Add goal_context extraction:
```python
current_arc_ctx = {
    "visible_goal": arc.get("visible_goal", ""),
    "goal_context": arc.get("goal_context", ""),  # NEW
    "thematic_question": arc.get("thematic_question", ""),
    ...
}
```

**Code Snippet — _arc.j2:**
Add goal_context as narrator context (hidden from player display):
```jinja
{% if current_arc.goal_context -%}
<!-- Narrator note: this is the character's personal stake in the visible_goal. Use it to shape emphasis, not exposition. -->
**Narrative guidance — goal context:** {{ current_arc.goal_context }}

{%- endif %}
```

Note: `_arc.j2` is injected into LLM user prompts (not human-facing output). Text inside HTML comments (`<!-- -->`) WILL be visible to the model as comment markup, which is fine since the narrator needs to read goal_context. If executor wants it truly hidden from both human and model display, use `{# #}` Jinja comment syntax instead — but this would prevent the LLM from reading the guidance, defeating the purpose of Step 2.3.

**Validation:** In first-turn outputs, reviewers can trace at least one meaningful prose choice back to each of:
- personal motive (via goal_context),
- opening NPC relationship (via relation field on present_npcs),
- immediate scene pressure.

### Tests to write or update
- Note: tests are temporarily removed during refactor per AGENTS.md policy ("Tests are temporarily removed during refactor"). When test phase resumes, add golden/snapshot coverage for turn 0/1 narration behavior showing stronger grounding and NPC-personal relevance.

### REPOMAP and architecture updates
- Update narration architecture docs to document opening-turn mode as a first-class narrative phase.
- Update REPOMAP prompt docs to describe how seed emotional context should be consumed by the narrator.

### Risks
1. The early-turn block may over-constrain prose and make openings feel samey; mitigate by defining priorities, not rigid beats.
2. Theme guidance may become pseudo-literary and vague; mitigate by framing it as selective emphasis in concrete scene writing.
3. Narration may become too withholding if "subtle" is interpreted as "omit motive"; mitigate by requiring felt stakes, not explicit labels.

## Implementation — Phase 03: UI goal framing

### Files to pull for context
- `AGENTS.md`
- `ccya/templates/_state_left.html` (sidebar rendering)
- Any CSS/JS files that implement shared tooltip behavior for `.has-tooltip` and `.tooltip-body`
- Relevant `docs/architecture/*` files covering sidebar information hierarchy

### Detailed steps

#### Step 3.1 — Add hover/focus goal tooltip using the existing tooltip pattern

**File:** `ccya/templates/_state_left.html`

**What:** Convert the arc goal into a hover/focus target that uses the same tooltip convention already used for the player bio, stat explanations, condition details, scene NPCs, and compendium entries . The tooltip body should render `goal_context`.

The existing pattern nests `.tooltip-body` INSIDE the element with `has-tooltip` (see lines 6–10 for player bio, line 27–30 for stats, line 39 for conditions). Follow this exact nesting structure.

**Why:** This is the least disruptive UI change with the highest narrative payoff. The sidebar already teaches the user that hover reveals deeper meaning; the arc goal should participate in that pattern instead of remaining a flat label .

**Code Snippet — _state_left.html (replace lines 99–120):**
```html
{% set _arc = state.get('arc') %}
{% if _arc %}
<details class="sidebar-card" id="card-arc" data-card="arc" open>
    <summary><span>Arc</span></summary>
    <div class="sidebar-card-body arc-card-body">
        {% set _goal = _arc.get('visible_goal', '') %}
        {% set _goal_ctx = _arc.get('goal_context', '') %}

        {% if _goal %}
        <div class="arc-goal{% if _goal_ctx %} has-tooltip{% endif %}" data-md>
            {{ _goal }}
            {% if _goal_ctx %}
            <div class="tooltip-body" data-md>{{ _goal_ctx }}</div>
            {% endif %}
        </div>
        {% endif %}

        {# Fix: use unified threads[] with active filter instead of non-existent active_threads #}
        {% set _active = (_arc.get('threads') | selectattr('active', 'equalto', true) | list) if _arc.get('threads') else [] %}
```

This single edit addresses two things: (1) the goal tooltip with correct nesting pattern, and (2) the pre-existing bug where `_arc.get('active_threads', [])` reads a non-existent field — CampaignArc uses unified `threads[]` with an active boolean flag.

**Additional file:** Also fix `ccya/prompts/compact_user.j2` lines 11–16 which has the same bug: `{% if arc and arc.get('active_threads') -%}` followed by `{% for t in arc.get('active_threads') -%}`. Replace with unified threads filter matching _state_left.html pattern. Without this fix, active threads will silently fail to display during compaction prompts after _state_left.html is corrected — inconsistent behavior between sidebar UI and prompt context.

**Validation:** The Arc card still reads cleanly at a glance, but on hover/focus the player gets 2–3 sentences that make the goal feel personally and thematically grounded. Active threads display correctly (fixing pre-existing bug).

#### Step 3.2 — Refine sidebar information hierarchy around "what matters now"

**File:** `ccya/templates/_state_left.html` and any related sidebar style/template files

**What:** Keep the compact card structure, but adjust emphasis so the sidebar supports immediate orientation rather than encyclopedic state browsing. The Arc card should answer "why this matters," while the Scene card should answer "who is here and why they matter now."

**Why:** The current left sidebar already has the right primitives—Player, Scene, Location, Arc, Compendium . The problem is hierarchy of meaning, not lack of data.

**Code Snippet**
```python
# No required structural rewrite.
# Preserve the current card layout and tooltip idiom.
# Adjust rendering only where narrative meaning is currently too flat.
```

**Validation:** A player scanning only the left sidebar on turn 1 should understand:
- who they are,
- who is immediately relevant,
- what the current goal is,
- why that goal matters emotionally.

#### Step 3.3 — Consider surfacing one lightweight scene-or-world grounding line

**File:** `ccya/templates/_state_left.html` and confirmed state source fields

**What:** If the architecture and state already provide a concise scene tagline or equivalent short atmospheric/context line, surface it near Scene or Location as a low-noise grounding aid. Do not add a lore box. Use this only if it improves immediate orientation.

Note: `SeedScene` has a `tagline` field (`ccya/pack.py:52`) and `StateDelta.scene_tagline` is persisted to `state.scene.tagline`. Check whether live gameplay data populates this field before implementing. If not populated, defer this step.

**Why:** A short framing line can soften the jump from abstract card labels into proper-noun lists, but only if it stays subordinate to character and scene pressure.

**Code Snippet — conditional (if tagline is confirmed as populated):**
```html
{% if state.scene.tagline %}
<div class="scene-tagline" data-md>{{ state.scene.tagline }}</div>
{% endif %}
```

**Validation:** The added line improves orientation without becoming a second block of exposition. If it reads like lore summary, cut it.

### Tests to write or update
- Note: tests are temporarily removed during refactor per AGENTS.md policy ("Tests are temporarily removed during refactor"). When test phase resumes, update template rendering tests for `_state_left.html` to cover arc goal tooltip behavior when `goal_context` is present/absent. Add accessibility checks for focus-triggered tooltip visibility on the arc goal if existing tooltip system has such coverage.

### REPOMAP and architecture updates
- Update the UI architecture doc to describe the Arc card as a two-layer presentation: visible goal plus optional contextual hover text.
- Update REPOMAP docs for templates/sidebar rendering to document the narrative purpose of the Arc and Scene cards, not just their fields.

### Risks
1. The tooltip may hide too much meaning on touch devices; mitigated — existing tooltip system already handles keyboard focus and touch interactions.
2. The new context text may make the Arc card feel too dense; mitigate by enforcing 2–3 sentence max and banning recap text in prompt guidance (Step 1.2).
3. Optional scene-tagline surfacing may add noise; mitigated by making it conditional on confirmed data population (Step 3.3).

## Ambiguities requiring resolution before execution
1. Which exact prompt files generate the world seed and turn narration? Answer: `ccya/prompts/generate_seed_system.j2` / `generate_seed_user.j2` for seeding; `narrate_system.j2` / `narrate_user.j2` for narration — confirmed by source inspection.
2. Where is the authoritative seed/arc schema enforced? Answer: both prompt output contract (in generate_seed_system.j2 TypeScript-style schema) AND Python model layer (`ccya/models.py` CampaignArc). The executor must update BOTH — adding `goal_context` to models.py first so Pydantic accepts it during SeedEnvelope parsing.
3. Does the existing tooltip system already support keyboard and touch interaction for arbitrary sidebar rows? Answer: yes, confirmed by reviewer. No additional UI behavior work needed.
4. Is there an existing short scene/tagline field already passed to the sidebar in live gameplay? Answer: `state.scene.tagline` exists as a data path (SeedScene has tagline field; StateDelta persists scene_tagline). The executor must verify whether it is populated during normal seed generation before implementing Step 3.3. If not populated, defer this step.
5. Are there existing prompt snapshot/eval tests for seed and narration quality? Answer: per AGENTS.md policy ("Tests are temporarily removed during refactor"), test work is deferred until the refactor phase completes.
