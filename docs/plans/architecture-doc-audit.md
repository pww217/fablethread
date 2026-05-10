# ARCHITECTURE.md audit and correction

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective
`docs/ARCHITECTURE.md` was last authoritatively updated during the eval-system-hardening
series (Phase 01). Since then, the narrative-mechanics-overhaul and scene-progress-fixes
plans migrated substantial mechanical work from the scene extractor into the progress
extractor, and a cleanup pass (Plan E) was supposed to align ARCHITECTURE.md — but it left
several inaccuracies and gaps in place. This plan corrects every identified divergence
between the doc and the five live pipeline prompts so the eval judge's architecture-context
loader receives accurate signal.

## Non-goals
- Does not change any prompt, model, or engine code.
- Does not restructure ARCHITECTURE.md beyond correcting factual content and adding missing sections.
- Does not add documentation for P4/future features that don't exist yet.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `docs/ARCHITECTURE.md` | modify | Correct Step 0 inputs, remove phantom fields, fix extractor ownership table, add missing prompt inputs and fields |
| `docs/plans/TODO.md` | modify | Add entry under Standalone for this plan |

## Firm decisions

1. Every correction must be verified against the actual `.j2` template, not inferred. Do not
   "fix" something without reading the relevant prompt file first.
2. The EVAL_CONTEXT sentinel region (`<!-- EVAL_CONTEXT_START -->` …
   `<!-- EVAL_CONTEXT_END -->`) must be preserved exactly — the
   `architecture_context.py` loader depends on it.
3. Corrections are made in-place in the existing document structure. New sections may be
   added only where content was entirely missing; do not reorganise existing sections.

## Implementation — Phase 1: Correct inaccuracies and fill gaps

### Context files to load
- `docs/ARCHITECTURE.md`
- `ccya/prompts/rules_system.j2`
- `ccya/prompts/rules_user.j2`
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_system.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_progress_user.j2`

### Overview
Read ARCHITECTURE.md and each of the ten prompt files in full. Apply the corrections
enumerated in the Detailed steps below. Verify each correction against the source template
before writing. Commit the updated ARCHITECTURE.md.

### Detailed steps

#### Step 1.1 — Fix Step 0 (Rules) input list

**File:** `docs/ARCHITECTURE.md`

**What:** The Step 0 inputs section claims `state.scene.present_npcs` and
`scene_pressure` are passed to the rules LLM. They are not — `rules_user.j2` passes only:
PC name, stats, conditions (with modifiers), the current location name, `last_turn_tail`,
and `user_input`. Remove the two phantom inputs. If `rules_user.j2` has been updated since
the audit (May 2026) to include additional fields, add those instead.

**Why:** The eval judge uses the EVAL_CONTEXT region to assess whether each pipeline
received the context it needed. Phantom inputs cause false-positive passes.

**Validation:** After editing, grep ARCHITECTURE.md for `present_npcs` and
`scene_pressure` in the Step 0 section — neither should appear in the inputs list.

---

#### Step 1.2 — Remove phantom `check.tags` from IntentEnvelope schema

**File:** `docs/ARCHITECTURE.md`

**What:** ARCHITECTURE.md lists `tags` as a field in the `IntentEnvelope` (Step 0 output)
schema. Confirm whether `rules_system.j2` or `rules_user.j2` actually instructs the LLM to
emit a `tags` field. If the field is absent from both templates, remove it from the
documented schema. If it was added since the audit, update the description to match.

**Why:** Documented output fields that the LLM is never asked to produce mislead the judge
about what mechanical signal flows into downstream steps.

**Validation:** The documented `IntentEnvelope` fields must be a subset of the JSON schema
block in `rules_system.j2`.

---

#### Step 1.3 — Fix extractor ownership table for `compendium_npc_update`

**File:** `docs/ARCHITECTURE.md`

**What:** ARCHITECTURE.md lists `compendium_npc_update` as a Step 2c (Progress) output
field. Read `extract_progress_system.j2` to confirm whether this field is present. If it is
absent (as of the May 2026 audit it was not there; it lives exclusively in
`extract_scene_system.j2`), move it to the Step 2a (Scene) column in the extractor
ownership table.

**Why:** Misattributed field ownership is the most common source of eval judge confusion
about which stream is responsible for a given mutation.

**Validation:** Every field in the extractor ownership table must appear in the JSON schema
of the prompt file attributed to it.

---

#### Step 1.4 — Complete Step 1 (Narrator) input list

**File:** `docs/ARCHITECTURE.md`

**What:** The Step 1 inputs section is materially incomplete. Read `narrate_user.j2` and
add every context block that is actually rendered. At minimum, the following were confirmed
missing as of the May 2026 audit and must be verified and added if still present:

- `world_state` (immutable world facts block)
- `scene_pressure` rendered as `## ACTIVE THREATS`
- `recent_events` ring
- `deescalate` flag (drives the `BREATHE` narrator directive when true)
- `present_npcs` with attitudes
- `pc_allegiance`
- `world_locations` list

For each, note the template block name and the condition under which it is included
(always / conditional on non-empty / conditional on flag).

**Why:** The narrator has the largest input surface of any pipeline. Incomplete docs cause
the judge to under-score turns where the narrator correctly used a context block that wasn't
documented.

**Validation:** After editing, every `{% if %}` / `{% for %}` block in `narrate_user.j2`
that produces a visible section should have a corresponding entry in the Step 1 inputs list.

---

#### Step 1.5 — Document `quest_threshold_directive` in Step 2c inputs

**File:** `docs/ARCHITECTURE.md`

**What:** `extract_progress_user.j2` injects a `quest_threshold_directive` string that
tells the progress LLM how aggressively to create new quests this turn. Confirm the exact
variable name and the logic that computes it (likely in `engine/extraction.py`), then add it
to the Step 2c inputs section with a one-sentence description of what it controls.

**Why:** This signal directly affects quest creation rate; without it in the docs, reviewers
cannot assess whether the extractor is behaving correctly for a given turn's quest load.

**Validation:** The variable name in ARCHITECTURE.md matches the variable name in
`extract_progress_user.j2` exactly.

---

#### Step 1.6 — Document all seven scope domains

**File:** `docs/ARCHITECTURE.md`

**What:** ARCHITECTURE.md documents four scope domains as gating the three extractors.
Read `narrate_system.j2` (or wherever scope domains are defined) and confirm the full list.
As of the May 2026 audit the confirmed domains were: `scene`, `location_change`,
`compendium_npc`, `quest_updates`, `recent_events`, `inventory`, `state` (7 total — verify
exact names and count). Update the scope domain table to list all of them with their owning
extractor and the condition under which the narrator emits each.

**Why:** Missing domains mean the judge cannot tell whether a skipped extractor stream was
correctly skipped or was an error.

**Validation:** Every domain listed must appear in the narrator system prompt's scope
instruction block with a matching name.

---

#### Step 1.7 — Document `band_examples` injection in Step 2b (State) extractor

**File:** `docs/ARCHITECTURE.md`

**What:** `extract_state_user.j2` (or `extract_state_system.j2`) injects few-shot
extraction examples keyed to the current dice band (`band_examples`). Confirm the variable
name, where the examples are sourced from (likely the pack), and add a note under Step 2b
inputs describing this conditional injection and its purpose (grounding extraction behaviour
to outcome severity).

**Why:** Undocumented few-shot injection is a significant context input; the judge should
know to look for band-appropriate extraction behaviour.

**Validation:** The field name in ARCHITECTURE.md matches what appears in the template.

---

#### Step 1.8 — Document `beat_expires_turn` on GMBeat

**File:** `docs/ARCHITECTURE.md`

**What:** `extract_progress_user.j2` references `beat_expires_turn` on the GMBeat object,
implying beats have a TTL. Confirm whether `beat_expires_turn` is a field on the Pydantic
`GMBeat` model in `models.py` and whether `apply_delta` or `engine/pressure.py` enforces
expiry. Document the field in the GMBeat schema section and add a one-paragraph description
of beat lifecycle (emit → pending_gm_beat on meta → narrator consumes → expires at turn N
if not consumed).

**Why:** Beat lifecycle is a core storytelling mechanic with no documented lifecycle path.

**Validation:** Every field documented for GMBeat appears in the Pydantic model definition.

---

#### Step 1.9 — Add scene pressure mutations to `apply_delta` description

**File:** `docs/ARCHITECTURE.md`

**What:** The `apply_delta` section lists the mutations it applies but omits
`scene_pressure_add`, `scene_pressure_remove`, and `scene_pressure_update`. Read
`state/delta.py` and add these to the apply_delta mutation list with the owning extractor
for each (scene for add/update; progress for remove — verify this is still accurate).

**Why:** The apply_delta section is used by the eval judge to assess state-mutation
correctness. Missing mutations cause false negatives.

**Validation:** Every key handled in `apply_delta()` that mutates state appears in the
documented mutation list.

---

### Tests to write or update
None — this plan modifies only documentation. No code changes.

### REPOMAP updates required
None.

### Risks

1. **Templates have changed since the May 2026 audit.** Mitigation: the first action of
   Phase 1 is to re-read all ten prompt files before making any edits. Every step says
   "confirm" — do not skip that confirmation.
2. **EVAL_CONTEXT sentinel region is accidentally modified.** Mitigation: after editing,
   grep for `EVAL_CONTEXT_START` and `EVAL_CONTEXT_END` and confirm both markers are
   present and unchanged.
3. **Step 1.6 scope domain count is wrong.** The May 2026 audit identified 7 domains but
   may have miscounted. Mitigation: enumerate directly from the narrator system prompt's
   scope block rather than relying on the audit memo.

## Ambiguities requiring resolution before execution

1. **`check.tags` current status.** The May 2026 audit found this field absent from
   `rules_system.j2`. If it has since been added as part of the intent-expansion plan
   (currently open in TODO.md), the executor must not remove it — instead update the
   description. Options: A) field absent → remove from docs. B) field present → update
   description to match template.

2. **`compendium_npc_update` stream ownership.** The audit attributed this to scene
   exclusively. If the intent-expansion plan or any other recent work added it to the
   progress stream as well, both streams should be listed. Options: A) scene only → correct
   docs to scene. B) both streams → document both.

## TODO.md update
Add under `## Standalone`:

```
- [ ] **ARCHITECTURE.md audit and correction** — correct Step 0 inputs, remove phantom IntentEnvelope fields, fix extractor ownership for `compendium_npc_update`, complete narrator input list, document `quest_threshold_directive`, all seven scope domains, `band_examples`, `beat_expires_turn`, and scene pressure mutations in `apply_delta` — see [`architecture-doc-audit.md`](architecture-doc-audit.md)
```
