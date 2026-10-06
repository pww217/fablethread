# Seed Generation: Temperature, Reliability, and the Two-Step Hypothesis

> **Date:** 2026-06-24
> **Context:** Implementing `pc_situation_schema` per-pack keys, `arc_origin`, NPC handoff from `pc_situation`, and opening-narrative weaving requirements from `03-seed-worldbuilding-redesign.md`.
> **LLM backend:** Ollama (local), model `local Gemma 4 26B (Ollama)`
> **Engine default temperature:** 0.9 (since changed to 0.65)

---

## 1. The Fundamental Tension

Seed generation has two jobs that require *opposite* temperatures:

| Job | Ideal temp | Failure mode |
|---|---|---|
| Structured JSON (world state, locations, pc_situation, arc, compendium NPCs, inventory) | 0.2–0.4 | Malformed keys (`"dormant: true`), truncated output, mismatched brackets, schema violations |
| Creative prose (opening_narrative weaving pc_situation, arc_origin, world facts into a grounded scene) | 0.7–0.9 | Bland, generic, formulaic narration; facts listed rather than woven |

At temp 0.9, seed generation fails ~50% of first attempts with "No JSON found" — the LLM produces valid-looking JSON with a single malformed key (e.g. `"dormant: true` missing its opening quote after a comma). Retry succeeds ~80% of the time, but wastes tokens and time.

At temp 0.65, JSON reliability improves to ~80% first-attempt success, but the opening narration loses some vividness — sensory details become more generic ("the air was thick with smoke" vs "the sharp hiss of a low-fuel lantern cut through the heavy, smoke-filled air").

## 2. Specific Failure Modes Observed

### 2.1 JSON Syntax Errors (temp 0.7–0.9)
- **Missing opening quote after comma:** `"type": "complication",\n          "dormant: true,` — the LLM skips the `\"` before `dormant`. Most common at 0.9.
- **Truncation:** Response cuts off mid-JSON, often at the `actions` array. Happens ~5% of the time, regardless of temp.
- **Extra closing braces:** The LLM adds `}}` at the end where only `}` is valid.

### 2.2 Schema Conformance Errors
- **Wrong presence value:** Using "far" or "located" instead of `"present" | "nearby" | "known"`.
- **Missing mandatory fields:** Named NPCs missing `personality`, `motivation`, `fear`, `leverage`, or `bond`.
- **Wrong key names:** Using `pc.situation` keys not in the pack's `pc_situation_schema`.
- **`arc_origin` in wrong location:** Sometimes at the top level of the response, sometimes inside `seed_state` as expected, but the `SeedEnvelope` model previously lacked a top-level `arc_origin` field — fixed in this session.

### 2.3 Content Issues
- **NPC handoff from pc_situation unreliable:** Named family members (e.g., "Wife Clara Terrell in Daviston") appear in `pc_situation` but not in the compendium ~50% of the time. The instruction "After generating opening-scene NPCs, check pc_situation one more time" is not sticky. LLM generates scene NPCs and forgets to add family members.
- **Family member format inconsistency:** The LLM alternates between "Mother Elena Vance" (full name, good), "Sister Clara" (no surname, bad), and "Wife Clara Terrell in Daviston" (full name, good). The PC situation section needed an explicit instruction to use full names.
- **arc_origin woven indirectly:** The world-level event is mentioned in the narrative's background but rarely explicitly connected to the PC's situation.

## 3. Instruction Placement Sensitivity

Instructions placed *after* the archetype table or *after* the field requirements section are less reliably followed than instructions in the numbered generation order (steps 1–8).

**What worked:**
- Moving the NPC handoff into the generation order as `7b` (after `7a. Generate scene NPCs`)
- Putting the full-name requirement in the numbered pc_situation section rather than in a separate note

**What didn't work:**
- `**NPC generation from pc_situation (mandatory):**` styled as bold text after the archetype table — visually prominent but the LLM still skipped it ~50% of the time
- "After generating all scene NPCs, re-read pc_situation..." — the LLM didn't re-read; it generated NPCs once and moved on

**Lesson:** For LLM prompt engineering, position trumps emphasis. Numbered steps in the generation order are followed more reliably than bolded admonitions in footnotes.

## 4. Key Prompt Changes in This Session

| Change | Purpose | Effect |
|---|---|---|
| Dynamic `pc_situation` keys in JSON schema | Show actual pack keys (e.g., `{ residence: string, office_location: string, reputation: string, family: string }`) instead of literal `{ key: string }` | LLM stopped generating `pc.situation: { key: "value" }` and started using real keys |
| Full-name instruction in pc_situation section | "BAD: 'Wife Clara in Morganstead.' GOOD: 'Wife Clara Vance in Morganstead.'" | Improved family member name quality |
| NPC handoff as `7b` in generation order | "For every person named in pc_situation, create a compendium entry" | ~75% reliable |
| `arc_origin` on `SeedEnvelope` model | Prompt schema showed `arc_origin` in `seed_state` but `SeedEnvelope` didn't have it | arc_origin now correctly stored |
| arc_origin weaving instruction | "make the arc_origin felt as a background pressure" | arc_origin appears in narrative backdrop but rarely explicitly |
| Key location setting instruction | "The opening scene must be set in or near one of the key locations from `world.locations`" | Scenes now set at a key location |
| `generate_seed_temperature` default changed from 0.9 to 0.65 | Reduce JSON failure rate | ~80% first-attempt success vs ~50% |

## 5. The Two-Step Hypothesis

The data strongly suggests splitting seed generation:

### Step 1: Structured Generation (temp 0.2–0.4)
Generate everything except the opening narrative in a single JSON call:
- World facts (global + local)
- Key locations
- arc_origin
- PC situation
- Campaign arc (long_term_objective + threads)
- Compendium NPCs (including pc_situation handoff)
- Inventory
- PC bio, stats, tagline

Temperature 0.2–0.4 eliminates JSON syntax errors and schema violations. The output is fully validated against `SeedEnvelope` before proceeding.

### Step 2: Narrative Generation (temp 0.7–0.9)
Feed the validated Step 1 output as context and generate only:
- opening_narrative
- outcome_summary
- actions (4 choices)

At high temperature, the LLM produces vivid, grounded prose that weaves in pc_situation, arc_origin, world facts, and key locations naturally — without the cognitive load of simultaneously maintaining JSON schema conformance.

**Expected benefits:**
- Near-zero retry rate for Step 1 (JSON reliability)
- Higher narration quality for Step 2 (no schema distraction)
- Total token cost likely similar or lower (no retries)
- Simpler prompt per step (each prompt has one concern)

**Expected risks:**
- Two LLM calls instead of one (latency)
- Step 2 might contradict or ignore Step 1 output (mitigated by giving Step 2 only the validated fields it needs)
- Need to pass Step 1 output through to Step 2 context (straightforward)

## 6. Per-Pack Observations

| Pack | pc_situation_schema | Notes |
|---|---|---|
| noir-1930s | residence, office_location, reputation, family | Family handoff works ~75%. office_location often implied rather than explicit. |
| zombie-survival | home_settlement, transport, nearby_area, family_status | Most consistent handoff. "nothing" as transport value respected by LLM. |
| space-western | vessel, home_port, reputation, filiation | Cleanest generation. No family members to hand off. |
| golden-piracy | vessel, home_port, reputation, alliance_status | No family members. "Independent" frequently used for alliance_status. |
| allied-ww2 | unit, theater, family_back_home, chain_of_command | Most inconsistent handoff for family names. Wife/sister names missed ~50%. |

## 7. Recommended Follow-Up

1. **Implement two-step seed generation** — the single highest-impact change for reliability and quality.
2. **Add seed.py validation** — before proceeding to turn 1, verify every named person in `pc.situation` has a compendium entry. Log a soft warning (not a hard error) so the game can proceed but the gap is recorded.
3. **Remove `generate_seed_temperature` from config** — if two-step is implemented, Step 1 doesn't need a temperature config (use a fixed low value), and Step 2 can use the existing `narrate_temperature`.
4. **Revisit `strip_thinking`** — the Qwen thinking model outputs non-standard thinking format; `_THINK_RE` only handles `<think>...</think>`. Add handling for Qwen's native format if Qwen is the selected model.
5. **Evaluate arc_origin weaving** — current prompt produces indirect weaving (background pressure) rather than explicit mention. Decide which is desired and update the instruction accordingly.
