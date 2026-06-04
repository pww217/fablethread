# Narration Prompt Overhaul: Tighter, Punchier, Less Repetitive

## Purpose

Design authority for plans that revise the narrator and seed system prompts to produce shorter, more active turn narration with less repetition, and a longer, more atmospheric opening seed narrative. Also covers adding frequency penalty to the narrate LLM call.

## Problem Statement

Turn narration averages 306 words with pervasive modifier repetition ("rhythmic" 20×, "sudden" 22×, "like a" 13× across 34 turns). The Style section of `narrate_system.j2` encourages bloat through aspirational instructions ("use colorful imagery, metaphors/similes") that produce formulaic sensory templates (smell of ozone/copper/antiseptic). Opening seed narration is under-producing at 308 words against a 400–700 word constraint.

Three distinct failure modes:

1. **Length**: No word ceiling exists for turn narration — "2–4 short paragraphs" is unenforceable and interpreted liberally. Opening seed is below its own floor.
2. **Repetition**: The model reuses modifiers, similes, and structural patterns (sensory detail → simile → NPC posture → next beat) because no repetition penalty is configured and the prompt explicitly asks for "colorful imagery."
3. **Generic prose**: Style instructions are aspirational ("avoid tropes," "be interesting") rather than concrete ("prefer direct dialogue," "cut the sensory template"). The model defaults to the safest literary formula.

## Constraints

- Model is Qwen3 27B via mlx_lm.server (OpenAI-compatible API). No grammar constraints, no logit bias support.
- Jinja2 prompt templates are shared between streaming narrate and seed — changes must be compatible with both rendering paths.
- No backwards compatibility required. Old prompt behavior is not preserved.
- The 3-movement opening structure (close-up → exposition → crisis) must remain recognizable to avoid confusing the model.
- Word range changes apply to all 6 default packs equally (zombie-survival, sengoku-japan, space-western, golden-piracy, noir-1930s, allied-ww2).

## Non-goals

- Not changing the extract, ruling, or storyteller prompts.
- Not changing the 5-call pipeline structure.
- Not adding new config fields (frequency_penalty is a one-line pass-through, not a new config knob).
- Not implementing a token-budget-based length limiter — we use an instructed word target instead.
- Not changing the seed 3-movement structure itself — only tightening the sub-section word targets.
- Not touching the seed system prompt's JSON schema, generation order, or NPC generation rules — only the opening_narrative prose guidance.

## Current State — What Exists

### Narrate system prompt (`ccya/prompts/narrate_system.j2`, 108 lines)

Section hierarchy:
1. Task/role line (line 1) — "2-4 short paragraphs"
2. Player input is truth (lines 3–17) — conflict resolution with GM beat
3. Inventory (lines 18–23) — hard constraint
4. Never repeat prior narration (lines 25–30) — with self-check instruction
5. Fail-band outcomes (lines 31–46) — explicit do/don't examples
6. NPCs (lines 47–66) — behavior drivers, naming, quantity, death
7. Style (lines 67–77) — 9 aspirational bullets
8. Pragmatic interpretation (lines 78–80) — edge case handler
9. Pacing (lines 82–84) — "No holding patterns"
10. Campaign arc context (lines 86–91) — latent thread push
11. Markdown formatting (lines 93–97)
12. Dynamic sections (lines 98–108) — world_rules, narrator_rules

**Narrate user prompt** (`ccya/prompts/narrate_user.j2`, 102 lines) — renders state data, no prose instructions. Not changing.

### Seed system prompt opening_narrative section (`ccya/prompts/generate_seed_system.j2`, lines 140–162)

3-movement structure with per-section word targets:
- Close-up (~80 words): "Start with a specific sensory detail — an object, texture, sound, smell, or weather."
- Exposition (~100 words): "Describe 2-4 specific environmental details: a locked footlocker, a cracked mirror, a discarded letter..."
- Crisis (remaining words): "The tension arrives or is revealed."

Optional scene bundle ingredients listed as a flat checklist. Opening constrained to `prose_word_range: [400, 700]` in all 6 packs.

### LLM parameters

- `narrate_temperature`: 0.9 (config.yaml line 8)
- `generate_seed_temperature`: 0.9
- No frequency_penalty, presence_penalty, or repeat_penalty passed to any LLM call
- `chat_stream()` in `ccya/llm_client.py` passes only `temperature` (and `stream_options`) to the API (lines 120–129)

### Call site (`ccya/engine/turn.py`, lines 917–924)

```python
async for chunk in llm_chat_stream(
    config.host,
    config.model,
    narr_messages,
    temperature=config.narrate_temperature,
    timeout=float(config.request_timeout_s),
    stream_stats=narr_stream_stats,
):
```

No `frequency_penalty` or other extra params.

### Problems with Current State

1. **"2-4 short paragraphs" is not a length target.** A "short paragraph" in fiction is 50–150 words. 4 paragraphs × 150 words = 600 words. The model naturally expands to fill available output budget. Real output averages 306 words with a ceiling of 409.

2. **Style section demands "colorful imagery, metaphors/similes" — this causes the repetition problem.** The model treats this as a checklist: sensory detail + simile per paragraph. "like a trapped bird" appears twice verbatim. "rhythmic" 20×, "sudden" 22×. The instruction incentivizes decorative rather than functional prose.

3. **Smell template is a persistent anti-pattern.** "the air smells of ozone/copper/antiseptic/blood/rot" appears in nearly every turn. The model has learned a sensory template and applies it mechanically.

4. **"Open with the player's action" is buried as a sub-bullet under Player Input (line 17).** This is the single most effective fluff-cutting rule and it has sub-bullet visual weight. It needs to be a top-level hard rule.

5. **Anti-repetition self-check is phrased as a suggestion ("does any sentence...") rather than a command ("BEFORE OUTPUTTING: scan every sentence. Delete anything...").** The self-check is routinely ignored — every turn re-describes established NPC posture.

6. **Pacing section is under-weighted.** "No holding patterns, no extended descriptions" is the core of the fluff problem but lives at line 82 with no visual prominence.

7. **NPC naming rule is 6 lines for a 20-word idea.** "Every NPC name must include a given name and family name." That's it.

8. **NPC death instruction is present but ineffective.** The model defaults to non-lethal outcomes ("stumbles back," "retreats") in high-stakes scenes because training data biases toward keeping characters alive.

9. **Latent thread section mentions "Build the 4 player choices"** — the narrator no longer writes choices. This is stale.

10. **Seed opening close-up (~80 words) is too long for what it does.** 80 words of sensory detail before the scene starts means 25% of a 308-word opening is orientation. With the target of 530–930 words, 80 words is reasonable, but the problem is the model *only* writes 308 words total. The close-up is eating proportionally too much.

11. **Scene bundle ingredients are presented as a checklist.** "Objects: ..., Conditions: ..., Sensory: ..." — the model treats these as mandatory rather than optional inspiration.

## Proposed Solution

### Core Changes

#### A. Narrate system prompt rewrite

**Line 1 — Length target:**
```
2-3 short paragraphs → 2-3 paragraphs, ~180 words. Hard ceiling: 250 words.
```

**New Hard Rule #2 — Open with player action:**
```
## Open with the player's action (BINDING)
First sentence addresses what the player does this turn. No establishing shots, no "you scan the room," no throat-clearing. If location or focus changed, start at the arrival — never narrate the journey there.
```

**Style section (replace entirely):**
```
## Style
- Keep it tight — each turn is a scene beat, not a chapter. Every sentence must advance.
- Subvert the obvious. If the reader can predict the next sentence, rewrite it.
- Prefer direct dialogue over summarized speech. When a character speaks, write the quote.
  When the player reads a book, sign, or terminal, show the text verbatim in `> blockquote`.
- One simile per turn maximum. If it doesn't earn its place, cut it.
- Describe new characters briefly on first appearance.
- No sensory templates. "The air smells of" is banned. If a smell matters to the action, say it in 3 words. If it doesn't, cut it.
- Concrete phrases observed repeating 20+ times across recorded sessions — treat them as a signal the model is falling back on trained patterns: "The air smells of", "rhythmic", "sudden", "like a". If you catch yourself writing these, cut or replace.
- Spatial clarity when positioning matters (combat, stealth, formations). Say where things are relative to each other.
```

**Anti-repetition self-check (rewrite to imperative):**
```
BEFORE OUTPUTTING: scan every sentence. If it restates information from a prior turn — an NPC's attitude, a room's atmosphere, a known condition — delete it. Replace with what is NEW this turn. If two sentences say the same thing, keep the tighter one.
```

**Pacing section (move to after Style, add directive override rule):**
```
## Pacing
Each beat must advance the plot meaningfully. No holding patterns, no extended descriptions of static scenes.

Override rule: The Outcome directive and pending GM beat are authoritative scene signals. Do not override them because the prose feels like it should go a different direction.
```

**NPC naming (collapse to 2 lines):**
```
## NPC naming
Every NPC must be referred to by a given name and family name (e.g. "Mira Sovak", "Dren Calloway"). Titles are optional. Descriptive labels like "scarred veteran" are aliases, not names — use the NPC's real name.
```

**NPC death (harden):**
```
NPCs die. In any scene with stakes, losing a confrontation means death, incapacitation, or removal from the scene. If you find yourself writing "stumbles back" or "retreats" in a high-stakes beat, replace it with a decisive outcome. The narrator and storyteller adjust — preserving plot by keeping characters alive is forbidden.
```

**Latent thread section (remove stale "4 choices" reference):**
```
Your job is to push the player gently towards [latent threads] through narration, environmental detail, and NPC behaviour — without explicitly exposing the thread content. Show, don't tell. An NPC glancing nervously at a locked door, a flicker of torchlight from an unexplored tunnel, a curious sound carried on the wind.
```

#### B. Seed opening narrative section rewrite

**prose_word_range: `[400, 700]` → `[530, 930]`** in all 6 pack scenario.yaml files.

**Replace per-section word targets with unified target + loose structure:**
```
~700 words. Second person, present tense.

Structure the opening in three movements — these are loose beats, not word-count quotas:

1. **Close-up** (1–3 sentences): Start with one live sensory detail that matters. Orients the player in the character's immediate physical reality. No summary, no biography.

2. **Exposition** (the middle): What is around the PC to see, examine, or potentially interact with — weave 1–2 environmental details into the scene. These aren't a checklist; every detail should imply recent action, conflict, or presence.

   Optional ingredients — use what fits, ignore what doesn't:
   Objects: ... Conditions: ... Sensory: ...

3. **Crisis/gameplay moment** (the bulk): The tension arrives or is revealed. Present NPCs act. The moment the player must respond to. This is where the "mid-scene" feel belongs — earned after the orientation.
```

The scene bundle block in `generate_seed_system.j2` gets an explicit optional preamble wrapping the entire block: `{% if pool_selection and pool_selection.scene_bundle -%}Optional ingredients — use what fits, ignore what doesn't:`.

#### C. Frequency penalty for narrate

**`config.yaml` — new field under `llm:`:**
```yaml
llm:
  narrate_frequency_penalty: 0.3
```

**`ccya/engine/config.py` — new `EngineConfig` field:**
```python
narrate_frequency_penalty: float = 0.3
```
Read in `build_engine_config()` from `llm.get("narrate_frequency_penalty", 0.3)`.

**`ccya/llm_client.py` — `chat_stream()` (line 129):**
Add `frequency_penalty` to kwargs:
```python
kwargs["frequency_penalty"] = frequency_penalty
```

Function signature gains `frequency_penalty: float | None = None` parameter. Default is None (no penalty) for backward compatibility; narrate caller passes `narrate_frequency_penalty` from config, while extract/storytell streams pass None.

**`ccya/engine/turn.py` (lines 917–924):**
Add `frequency_penalty=config.narrate_frequency_penalty` to the `llm_chat_stream()` call for narrate only. Other streaming calls (extract scene, extract state, storytell) pass None or omit the parameter.

**Pre-condition — verify `frequency_penalty` server support:** Before writing a plan for this change, verify that the running `mlx_lm.server` instance accepts and applies `frequency_penalty` as a chat completions parameter. The verification method: send a test completion request with `frequency_penalty=1.0` against a known repetitive prompt and confirm the output differs measurably from `frequency_penalty=0.0`. If the parameter is silently ignored (no output difference, no error), deprioritize the frequency_penalty change and treat the prompt-only changes as the full intervention. This verification is critical because prior patterns of silent LLM parameter ignores have been documented in this pipeline.

mlx_lm.server supports `frequency_penalty` as a standard OpenAI-compatible chat completions parameter. Positive values penalize tokens proportional to their frequency in the output, directly reducing modifier repetition without affecting structural words.

### Alternatives Considered and Rejected

| Alternative | Rejected because |
|---|---|
| Raise narrate temperature to 1.0+ | 0.9 is already near ceiling for coherent prose. Higher temps produce incoherence, not variety. |
| Add `repeat_penalty` instead of `frequency_penalty` | Repeat penalty is a blunt multiplicative factor on *any* repeated token, including common words like "the" and "a". Frequency penalty targets genuinely overused tokens proportionally. |
| Add `max_tokens` limit to narrate | Would truncate prose mid-sentence. Word target in the prompt is softer but preserves sentence integrity. |
| Lower temperature to reduce repetition | Lower temp increases repetition by making the model more deterministic. Opposite of what we want. |
| Rebuild the seed 3-movement structure entirely | The structure works when the model hits its word target. The problem is under-production, not the structure itself. |
| Remove the anti-repetition self-check | The instruction is correct — it just needs stronger phrasing. Removing it removes the only explicit repetition guard. |

## Decision Table

| Decision | What | Why |
|---|---|---|
| Word target for turn narration | ~180 words per turn, hard ceiling 250 | Cuts average from 306 to ~200 (−33%) |
| "Open with player action" promoted | From sub-bullet to Hard Rule #2 | Most effective fluff-cutting instruction |
| Style section rewritten | Remove "colorful imagery/metaphors" requirement, add "one simile max," ban sensory templates, require direct dialogue | Dead instruction was causing the repetition problem |
| Anti-repetition made imperative | "BEFORE OUTPUTTING: scan..." replaces "does any sentence..." | Stronger enforcement, harder to skip |
| Pacing directive override rule | "Outcome directive and GM beat are authoritative" | Prevents the narrator from vetoing scene signals |
| NPC naming collapsed | 6 lines → 2 lines | Same instruction, less dead weight |
| NPC death hardened | "Stumbles back" → replace with decisive outcome | Model biases toward non-lethal; need stronger override |
| "4 player choices" removed from latent thread section | Stale reference to removed narrate behavior | No longer accurate |
| Seed prose_word_range | `[400, 700]` → `[530, 930]` in all 6 packs | +33% for better exposition and stage-setting |
| Seed close-up tightened | ~80 words → ~30 words, 1–2 sentences | Less orientation padding, more crisis |
| Seed exposition de-checklisted | Optional ingredients are optional | Prevents furniture-catalog problem |
| frequency_penalty added | 0.3 default, config.yaml field `narrate_frequency_penalty` | Reduces modifier overuse without affecting coherence |
| Scene bundle optional in template | `generate_seed_system.j2` scene bundle block wrapped in optional preamble | Makes optional status unambiguous at template render level |
| Seed 3-movement → loose structure | Remove per-section word targets; keep close-up/exposition/crisis as loose structure with unified ~700 word target | Under-production problem partly caused by rigid sub-targets |

## Failure Modes and Risks

- **Word ceiling ignored**: The model may still over-produce despite the 250-word instruction. Mitigation: monitor average output and tighten further (lower ceiling, add "if your draft exceeds this, cut" enforcement language).
- **Direct dialogue mandate causes pacing issues**: If the model interprets "prefer direct dialogue" as "no summarized action," turns could become all-talk. Mitigation: the instruction says "when a character speaks" — action-first narration still takes priority.
- **[QUESTION: blockquote scope conflict]** Proposed Style says "show text verbatim in `> blockquote`" but current Markdown section limits blockquotes to "signage or quoted broadcast text." If the Style says to show any read text (letters, terminals, books) in blockquote, the Markdown rule blocks it. The executor needs to know: widen the Markdown rule to cover all verbatim text, or remove the limitation? Recommend widening the Markdown section: "`> blockquote` for signage, broadcasts, and any text the player reads verbatim (books, terminals, letters)."
- **frequency_penalty=0.3 is too weak or strong for this model**: Qwen3 may respond differently than other models. If modifier repetition persists, increase to 0.5. If sentence fluency degrades, reduce to 0.15.
- **[frequency_penalty targets all tokens, not just modifiers]** Frequency penalty penalizes every repeated token proportionally to its frequency — common words like "the", "a", "was" get a larger penalty than modifiers because they appear more often. At 0.3 this effect should be mild, but if sentence fluency degrades (unusual article usage, dropped auxiliaries), it's the frequency_penalty, not the content changes. Monitor for unnatural article/auxiliary patterns after deploy.
- **[CRITICAL: frequency_penalty server support unverified]** The design assumes `mlx_lm.server` supports OpenAI-compatible `frequency_penalty`. If it doesn't — ignored silently, errors, or behaves differently — the entire Change C is dead code. The executor must verify this against the running server before implementing. See CONSOLIDATED-EV-FINDINGS.md for prior patterns of silent LLM parameter ignores.
- **Smell ban is too absolute**: Some scenes legitimately need olfactory detail (a sewer, a chemical spill). Mitigation: the instruction says "if a smell matters, say it in 3 words" — it bans gratuitous smell, not all smell.
- **Seed word range increase may not translate to actual longer output**: The model currently under-produces at 308 words against a 400 floor. Raising the floor to 530 doesn't guarantee the model hits it. The rewritten close-up and exposition instructions may help, but the instruction word targets are advisory, not enforced by the engine.
- **Model variance across runs limits confidence in prose improvements**: The prose improvements proposed here (repetition reduction via banned phrases, length control via word target) may produce inconsistent results across model runs or seeds. Empirical data from CONSOLIDATED-EV-FINDINGS.md Finding 0.1 shows that two runs of the same system with the same seed pack produced near-inverse beat profiles, confirming that LLM seed/model variance dominates output character more than prompt structure does. The same variance likely affects prose style and length adherence. The frequency penalty and style rewrites should be evaluated across multiple runs before conclusions are drawn. A single run showing improvement does not confirm the fixes are stable.

## Open Questions

All three from the original design resolved. New questions from review:

- `[OPEN: blockquote scope]` — Proposed Style says "show text verbatim in `> blockquote`" but current Markdown section limits blockquotes to "signage or quoted broadcast text." Recommend widening the Markdown rule to cover all verbatim text.
- `[OPEN: frequency_penalty MLX support]` — The design assumes `mlx_lm.server` supports OpenAI-compatible `frequency_penalty`. This must be verified before implementation. If unsupported, the entire Change C is dead code.

## Decisions (resolved from Open Questions)

| Decision | What | Why |
|---|---|---|
| frequency_penalty → config.yaml field | New `narrate_frequency_penalty` field in config.yaml under `llm:`, default 0.3 | User control; matches existing pattern of `narrate_temperature` |
| Scene bundle marked optional in template | Wrap scene bundle block in `{% if pool_selection and pool_selection.scene_bundle -%}` with preamble text "Optional ingredients — use what fits, ignore what doesn't" | Makes optional status unambiguous at the template level, not just in prose guidance |
| Seed 3-movement → loose structure | Replace per-section word targets (~30 / ~130 / remaining) with one unified target (~700 words) and the three movements as loose structural guidance with no word counts | Model under-produced against tight sub-targets; loose structure gives it room while preserving the close-up/exposition/crisis arc |

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| "Avoid tropes; invent fresh twists, weird details" | narrate_system.j2 Style | Replaced by "Subvert the obvious" |
| "Use direct dialogue when player or NPC is speaking" | narrate_system.j2 Style | Replaced by stronger "Prefer direct dialogue" + verbatim quote requirement |
| "NPCs and scene/location should interact" | narrate_system.j2 Style | Circular guidance, removed |
| "Visceral, gory, and sexual details are allowed" | narrate_system.j2 Style | Replaced by single clause: "No content restrictions" (implicit) |
| "Use colorful imagery, metaphors/similes" | narrate_system.j2 Style | Directly caused repetition problem |
| "Build the 4 player choices" | narrate_system.j2 latent thread section | Narrator doesn't write choices |
| Single-word NPC names | narrate_system.j2 | Contradicts the naming rule anyway |
| Per-section word targets in 3-movement structure | generate_seed_system.j2 | Replaced by unified ~700 word target + loose movement guidance |
| "Describe 2-4 specific environmental details" checklist language | generate_seed_system.j2 | Replaced by "weave 1–2, not a checklist" |

## What Is Unchanged

- Narrate user prompt (`narrate_user.j2`) — no changes to how state is rendered for the narrator
- Seed system prompt aside from the opening_narrative section — JSON schema, generation order, constraints, output discipline all untouched. (Scene bundle block template structure changes are listed under "Core Changes — B.")
- Seed user prompt (`generate_seed_user.j2`) — no changes
- `ccya/engine/narrate.py` — prompt building logic unchanged
- `ccya/engine/seed.py` — seed generation logic unchanged (only the template rendering changes)
- `ccya/engine/config.py` — EngineConfig gains `narrate_frequency_penalty: float = 0.3` field
- `ccya/prompts/sections/` — all includes untouched
- Extract, ruling, storyteller prompts — untouched
- Packs' inspiration text, situation_archetypes, arc_categories, pools — untouched (only prose_word_range changes)
- Seeds' 3-movement structure itself — preserved, only tightened
- `narrate_temperature`: 0.9 — unchanged
- `generate_seed_temperature`: 0.9 — unchanged

## New Model Shapes

None. No new types, schemas, or data models. The only state change is:

### EngineConfig

New field:
```python
@dataclass
class EngineConfig:
    narrate_frequency_penalty: float = 0.3
```

### config.yaml

New field under `llm:`:
```yaml
llm:
  narrate_frequency_penalty: 0.3  # default if absent
```

### chat_stream() signature

```python
async def chat_stream(
    host: str,
    model: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    frequency_penalty: float | None = None,  # default None (backward compat)
    timeout: float = 180.0,
    stream_stats: MutableMapping[str, Any] | None = None,
) -> AsyncIterator[str]:
```

### EngineConfig parsing (in `build_engine_config()`)

```python
narrate_freq = float(llm.get("narrate_frequency_penalty", 0.3))
```

### Turn narrate call (in `turn.py`, line 917)

```python
async for chunk in llm_chat_stream(
    ...
    temperature=config.narrate_temperature,
    frequency_penalty=config.narrate_frequency_penalty,
    ...
):
```

Other streaming calls (extract scene, extract state, storytell) omit `frequency_penalty` so it defaults to None internally.

### Pack constraints

```yaml
# prose_word_range in all 6 pack scenario.yaml files:
prose_word_range: [530, 930]  # was [400, 700]
```

## Context for Implementing LLMs

Files to read before writing any plan:

- `ccya/prompts/narrate_system.j2` — the primary target for rewrite. Read the full file to understand current section ordering.
- `ccya/prompts/generate_seed_system.j2` — read lines 140–162 (opening_narrative guidance) and line 82 (prose_word_range reference).
- `ccya/prompts/sections/_arc.j2` — unchanged but provides context for how arc data reaches the narrator.
- `ccya/llm_client.py` — read `chat_stream()` (lines 102–139) to understand where frequency_penalty is injected.
- `ccya/engine/turn.py` — read lines 905–939 to see the narrate call site. No code change needed at this layer.
- `packs/default/*/scenario.yaml` — 6 files, each needs `prose_word_range` updated from `[400, 700]` to `[530, 930]`.
- `ccya/prompts/narrate_user.j2` — read to confirm no changes needed (should be read-only).
