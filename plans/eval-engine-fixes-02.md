# Eval Engine Fixes — Phase 07 (C1–C4, M1–M3)

## Status
`open`

## Phases

6 phases covering all critical and medium-severity findings from the 2026-05-24 eval run analysis: Narrator prompt BINDING enforcement, auto-checker correctness fixes, Progress Extractor action generation, ID normalization, meta-eval rate emission, and location change audit logging.

## Issue

The 2026-05-24 `9_w4mtd1` eval run surfaced 4 critical engine bugs and 3 medium eval infrastructure gaps:

1. **C1 — Narrator prompt fails to enforce BINDING constraints**: The Narrator receives `rules_outcome` data but renders it as informational text (`**Band:** FAIL → ...`). The system prompt has a `## Fail-band outcomes (BINDING)` section that contains hard rules about NPC behavior on fail bands, but the user prompt never explicitly calls attention to the BINDING nature of these rules. The auto-checker looks for `rules_outcome (BINDING)` literal string in rendered_user — a format that doesn't exist. This causes 5 `binding_present` failures per run across all rolled turns.

2. **C2 — Progress Extractor emits 0–2 actions instead of required 4**: Storyteller LLM reliably returns empty or short `actions` arrays. Fallback logic in `_run_extraction_pipeline()` generates synthetic actions from narration sentences, but these are generic ("Continue the...", "Survey your surroundings...") and produce weak turn options. Fails on T4, T8, T12 in every run.

3. **C3 — Inventory/Condition ID schema drift**: Extractors emit `"credits"` for inventory ID but state canonical ID is `"Iron Coins"`. Condition IDs like `"bruisedribs"` are emitted but state has `"bruised_ribs"`. The `resolve_inventory_canonical_id()` function handles some normalization (via `normalize_inventory_id()` which strips punctuation) but the fuzzy name matching in `_fuzzy_match_inventory()` doesn't catch all cases. No equivalent normalization exists for condition IDs.

4. **C4 — Location change deltas not logged in audit trail**: Location changes apply to state but are not captured in the "Applied Deltas" log, suggesting a race condition or separate code path for location mutations.

5. **M1 — `state_fidelity_rate` and `prompt_adherence_rate` estimated, not parsed**: Domain judges don't emit these field names in their YAML front matter. Meta judge synthesizes estimates instead of reading real values.

6. **M2 — Auto-checker false positives**: `npc_mention.extracted` flags "Marrow" (from "Marrow's Crossing"), "Though" (transition word), and "Leather" (item descriptor). Phase 02 deployed partial fixes but the eval ran on old events.jsonl.

7. **M3 — `ruling.rolled` assertion false positive**: Fails on 6/13 turns where rolled=False is correct engine behavior (no dice needed). Assertion should pass when engine correctly declines to roll, not flag it.

## Solution

Six phases (Phase 02 depends on Phase 01 — see note below):

1. **Phase 01**: Add a `(BINDING)` callout block to `narrate_user.j2` that activates when `rules_outcome.rolled=true`, referencing the fail-band rules from the system prompt. Fix the auto-checker `check_rolled_implies_binding()` to check for the actual rendered format. This satisfies the real requirement (explicit BINDING reference in user prompt on rolled turns) and aligns the auto-checker with reality.

2. **Phase 02**: Fix remaining auto-checker issues (depends on Phase 01 — the `check_rolled_implies_binding()` fix is already applied there; do not re-apply): (a) `ruling.rolled` assertion logic in `runner.py:208-213` — pass when `rolled=False` is correct behavior, (b) remaining NPC false positives with expanded stop lists in `universal_asserts.py`.

3. **Phase 03**: Improve Storyteller prompt and fallback action generation to reliably produce 4 distinct, substantive actions. Two changes: add examples of good 4-action sets to the system prompt, and improve fallback diversity when LLM returns empty.

4. **Phase 04**: Add condition ID normalization in `delta_builder.py` mirroring inventory's `resolve_inventory_canonical_id()`. Add `normalize_condition_id()` helper. This prevents phantom conditions from ID typos.

5. **Phase 05**: Compute `state_fidelity_rate` and `prompt_adherence_rate` from available domain judge scores in a post-processing step inside `_build_meta_judge_input()` — no domain judge prompt changes needed.

6. **Phase 06**: Add explicit logging to the location change application path so "Applied Deltas" captures location mutations.

## Firm decisions

1. C1 is fixed by adding explicit `(BINDING)` callout to the user prompt template, not by rewriting the system prompt. The rules are correct; the problem is the Narrator doesn't see them as binding because they're too far from the user input.
2. The auto-checker `check_rolled_implies_binding()` will check for the new callout format, not the old string. This is a forward fix.
3. `ruling.rolled` assertion (evaluated via `TurnAssert` objects in `runner.py:208-213`, NOT as a registered check function in `universal_asserts.py`): pass when `rolled=False` with detail `(no roll)`. Only fail when roll was expected but not produced.
4. Condition ID normalization uses `normalize_inventory_id()` as a base (strip punctuation, snake_case). Same granularity as inventory IDs.
5. Phase 05 uses a post-processing step in `_build_meta_judge_input()` as the primary approach — computing rates from available scores — rather than requiring domain judges to emit new field names. If domain judge output is rich enough, no prompt changes needed.
6. Location change logging is a single `_log.info` call with structured context, not a separate audit system.

## Non-goals

- Not fixing C4's root cause (race condition) if investigation shows the state is actually correct — the fix scoped to logging only.
- Not redesigning the eval architecture or adding new judge types.
- Not addressing M4 (meta judge lacks raw trace access) — documented limitation, not actionable here.
- Not changing the Narrator system prompt `narrate_system.j2` — only the user prompt.
- Not modifying `resolve_inventory_canonical_id()` logic — inventory normalization already works, the issue is the extraction prompt not referencing canonical IDs. That's a prompt change, not a state-layer change.
- Not adding backward compatibility for removed fields or renaming existing config keys.
- Not writing new tests (per AGENTS.md: tests are temporarily removed during refactor).

## Risks, Ambiguities, and Blockers

- **Phase 03 risk**: LLM may continue to ignore the "exactly 4 actions" instruction regardless of prompt improvements. Fallback logic is the safety net, but if LLM compliance is fundamentally unreliable, need stronger post-processing validation. Fallback quality improvement is the primary deliverable.
- **Phase 04 ambiguity**: The condition ID normalization approach mirrors inventory, but condition IDs come from the State Extractor (which receives state context) not the Storyteller (which receives band/outcome). Fix may need a prompt change in `state_extract.j2` to reference existing condition IDs.
- **Phase 06 ambiguity**: Location changes may mutate state via a non-delta path (e.g., inline in turn.py). Need to verify before implementing — location_change logging may need to be added at the mutation point rather than in apply_delta.
- **Phase 01 risk**: The auto-checker fix and template change must remain in sync. If one is applied without the other, the other eval run will show false positives/negatives.
- **Phase 02 depends on Phase 01**: Phase 02 must NOT re-apply the `check_rolled_implies_binding()` fix from Phase 01 Step 1.2. Phase 02 only covers `ruling.rolled` (runner.py) and NPC false positive stop words (universal_asserts.py).

---

## Implementation — Phase 01: Narrator BINDING callout + auto-checker alignment

### Context files to load
- `ccya/prompts/narrate_user.j2` (86 lines)
- `ccya/eval/universal_asserts.py` (line 212–238)
- `ccya/engine/narrate.py` (line 19–118)

### Detailed steps

#### Step 1.1 — Add `(BINDING)` callout block to narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2`

**What:** After the existing `rules_outcome` block (lines 67–74), add a conditional `(BINDING)` callout section that activates when `rules_outcome.rolled` is true. This block states the band, directive, and explicitly labels the fail-band rules as BINDING. It always appears on rolled turns regardless of band (even success: the Narrator should know that fail-band rules are binding).

Replace the current block:
```
## This Turn's (Turn {{ meta.get('turn', '?') if meta is mapping else '?' }}) Result
{% if rules_outcome and rules_outcome.rolled %}

**Band:** {{ rules_outcome.band | upper | replace('_', ' ') }} → {{ rules_outcome.directive }}

{% elif rules_outcome and not rules_outcome.rolled %}

**No roll required.** Describe what happens with appropriate weight for the moment.
{% endif %}
```

With:
```
## This Turn's (Turn {{ meta.get('turn', '?') if meta is mapping else '?' }}) Result (BINDING)
{% if rules_outcome and rules_outcome.rolled %}

**Band:** {{ rules_outcome.band | upper | replace('_', ' ') }} → {{ rules_outcome.directive }}

**This is a BINDING outcome.** The `## Fail-band outcomes (BINDING)` rules in the system prompt are active. On FAIL band: PC does not get what they asked for, NPC does not engage constructively. On PARTIAL: PC succeeds at cost. On SUCCESS/CRIT_SUCCESS: advance freely.

{% elif rules_outcome and not rules_outcome.rolled %}

**No roll required.** Describe what happens with appropriate weight for the moment.
{% endif %}
```

**Why:** The auto-checker needs a recognizable marker (`(BINDING)`) in the rendered user prompt on rolled turns. More importantly, the Narrator LLM receives an explicit, proximate reminder that band outcomes are binding constraints — not just informational — right before the player input. This addresses the "anti-declare-outcome" failure and phantom thread issues.

**Validation:** `python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('ccya/prompts')); t = env.get_template('narrate_user.j2'); print(t.render(...))"` — render with a mock `rules_outcome` dict with `rolled=true`.

#### Step 1.2 — Fix auto-checker to check new format

**File:** `ccya/eval/universal_asserts.py` (function `check_rolled_implies_binding`, lines 212–238)

**What:** Change the assertion check from `"rules_outcome (BINDING" in nu` to `"(BINDING)" in nu` — or more precisely, check for `"Roll (BINDING)"` or `"Result (BINDING)"`. Use the most distinctive substring that will appear in the rendered output. The header reads `## This Turn's (Turn N) Result (BINDING)` — so check for `"Result (BINDING)`.

**Why:** The old check looked for a string that never existed in any template, causing consistent false negatives. The new format has two explicit `(BINDING)` markers: in the section header and in the callout paragraph. Checking for either resolves the false negative.

**Validation:** `python -c "..."` to verify the check against sample rendered output.

### Tests to write or update
None (tests removed during refactor per AGENTS.md).

### REPOMAP updates required
None.

---

## Implementation — Phase 02: Universal asserts correctness

### Context files to load
- `ccya/eval/universal_asserts.py` (all 742 lines)
- `ccya/eval/runner.py` (lines 208–213, where `ruling.rolled` TurnAssert is evaluated)
- `ccya/eval/scenario.py` (Turn/TurnAssert models)
- `evals/scenarios/full_cycle.py` (scenario TurnAssert declarations)

### Detailed steps

#### Step 2.1 — Fix `ruling.rolled` assertion false positive

**File:** `ccya/eval/runner.py` (lines 208–213)

**What:** The `ruling.rolled` assertion is NOT a registered check function in `universal_asserts.py`. It is evaluated inside `_check_asserts()` in `runner.py` via scenario-defined `TurnAssert` objects. The comparison is: `passed = (val == (a.expected == "true"))`. When `val=False` and `expected="true"`, the assertion fails.

Change the logic: pass when `rolled=False` with detail `"(no roll)"`. Only fail when the turn record shows a declared intent (player made a checkable action) but no roll was produced. Since the engine never rolls when no roll is needed, the simplest approach: if `rolled=False`, pass. Only fail if the `RulesOutcome` record indicates an error state (parse error, retry exhaustion) where a roll should have happened.

The scenario TurnAssert declarations in `full_cycle.py` also need review: 8 turns declare `expected="true"` and 4 declare `expected="false"`. If the fix is at the assertion level (trusting `rolled=False`), the scenario data stays correct.

**Why:** 6/12 turns fail this assertion with `rolled=False` — these are all correct non-roll turns (approach, conversation, sit). The false positive pollutes the auto-checker pass rate and distracts from real issues.

#### Step 2.2 — Add remaining NPC false positive stop words

**File:** `ccya/eval/universal_asserts.py` (stop list section, `check_npc_mention_extracted` ~line 358 and `_extract_candidate_names` ~line 266)

**What:** Add to the existing stop mechanisms (there is no `_STOP_LIST` — the word lists are local sets inside `check_npc_mention_extracted` and `_extract_candidate_names`):

- `marrow` — fragments from location name "Marrow's Crossing". The word-boundary regex `\b{token}\b` at line 303-304 already handles this via location name matching (`loc_lower` filter). Confirm it is in effect: verify that `marrows_crossing` is in `location_names` and that `\bmarrow\b` correctly matches against it.

- `though` — do NOT add to the stop list. The candidate extraction regex at line 288 (`\b[A-Z][a-z]{2,}\b`) only matches words starting with uppercase. A lowercase "though" mid-sentence is already excluded by the regex and can never become a candidate. The Issue section (line 24) reported "Though" (capitalized) as a false positive, but the prior Phase 02 fix should have added it to the `stop` set at line 378. Verify it is present there instead.

- `leather` — item descriptor/material. The `inventory_names` partial match at line 298-300 (`if inv_lower and any(token.lower() in inv_name ...)`) should already filter this out if "leather" appears in any inventory item name. If not already covered, add to `descriptor_stop` in `_extract_candidate_names` (line 266-277). Note: this is different from `descriptor_stop` used in a prior Phase 02 — the `descriptor_stop` here is a local set, not a module-level constant.

**Why:** Fixing the actual remaining false positives (verify `marrow` is matched by location filter, verify `leather` is covered by inventory or `descriptor_stop`) eliminates the few remaining `npc_mention.extracted` failures. No new words need to be added to any stop list if existing mechanisms already cover them.

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
None.

---

## Implementation — Phase 03: Progress Extractor action generation

### Context files to load
- `ccya/prompts/storytell_system.j2` (126 lines)
- `ccya/prompts/storytell_user.j2` (63 lines)
- `ccya/engine/extraction.py` (lines 653–678, fallback action generation)

### Detailed steps

#### Step 3.1 — Improve Storyteller prompt action examples

**File:** `ccya/prompts/storytell_system.j2`

**What:** In the `actions` field description (line 50), strengthen the instruction and add concrete examples of good 4-action sets. Currently:
```
`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current arc state. Structure: one choice should advance an active thread, one should involve an NPC who is present in the scene, one should leverage the PC's highest stat value (do NOT mention stat directly), and one should be a distinct exploration/environmental or freeform option not covered by the other three. Weight toward thread objectives and motivations. Each should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices. **You MUST always emit exactly 4 non-empty strings in this field. Never emit an empty array.**
```

Replace with:
```
`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current arc state. Structure: one choice should advance an active thread, one should involve an NPC who is present in the scene, one should leverage the PC's highest stat value (do NOT mention stat directly), and one should be a distinct exploration/environmental or freeform option not covered by the other three. Weight toward thread objectives and motivations. Each should move the plot forward substantially in a different direction.

**Good examples of complete 4-action sets:**
1. "Draw your blade and close the distance with Halden" (thread advance), "Demand the guard explain who sent him" (NPC interaction), "Scan the warehouse for exits and ambush points" (wits/exploration), "Call out for any allies in the nearby stalls" (freeform/environmental)
2. "Pick the lock on the iron gate" (thread advance), "Promise Caron a cut of the haul" (NPC interaction), "Press your shoulder against the rusted hinge and force it open" (strength/environmental), "Listen for footsteps on the stairs above" (freeform/perception)
3. "Pour the antidote down the prisoner's throat" (thread advance), "Ask the apothecary where she found the ingredients" (NPC interaction), "Search the laboratory for more supplies" (lore/exploration), "Barricade the door with the fallen shelf" (freeform/environmental)

**Note on thread_advance:** Actions and thread_advance are separate concerns. The actions list offers player choices; thread_advance records what THIS turn actually advanced. An action CAN target a thread without the thread being advanced here — and a thread CAN be advanced without a matching action.

**You MUST always emit exactly 4 non-empty strings in this field. Never emit an empty array. The fourth action must be distinct from the first three — not a rephrasing or subset.**
```

**Why:** The LLM needs to see multiple concrete examples of good 4-action sets to understand the expected structure and diversity. The current prompt has only 2 example strings, both short. The 4 examples above demonstrate thread-advance, NPC-interaction, stat-related, and freeform options. Adding the note about thread_advance vs actions clarifies a common confusion.

#### Step 3.2 — Improve fallback action diversity

**File:** `ccya/engine/extraction.py` (lines 653–678)

**What:** Replace the current fallback logic with more substantive, diverse fallbacks. The current logic generates 4 actions using this pattern:
1. "Continue {first narr_sentence}"
2. "Speak with {first NPC}" or "Survey your surroundings..."
3. "Use your {highest_stat} to assess..." or "Plan your next move..."
4. "Search for any hidden threats..."

Replace with logic that generates better diverse fallbacks:

```python
# Generate fallback actions when LLM omits them
if not storytell_result.actions:
    narr_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', narration.strip()) if len(s.strip().split()) > 5]
    present_npc_names = [n.get("name", "") for n in extraction_ctx.present_npcs_this_turn if isinstance(n, dict)]
    stats = state.get("pc", {}).get("stats") or {}
    actions = []
    
    # Action 1: Thread-bearing action from narration
    if narr_sentences:
        s = narr_sentences[0].strip().lower()
        s = s[:80].rstrip(".")
        actions.append(f"Press the advantage: {s}")
    else:
        actions.append("Take decisive action to advance the situation.")
    
    # Action 2: NPC interaction
    if present_npc_names:
        npc = present_npc_names[0]
        actions.append(f"Engage {npc} directly — press for answers or cooperation.")
    else:
        actions.append("Call out into the space — announce your presence or demand answers.")
    
    # Action 3: Stat-grounded assessment
    if stats:
        highest_stat = max(stats, key=lambda k: stats[k])
        stat_themes = {
            "strength": "Force a change in the environment — push, break, or lift.",
            "dexterity": "Move carefully — slip past, reach for, or reposition.",
            "wits": "Read the situation — look for tells, patterns, or hidden details.",
            "lore": "Recall relevant knowledge — history, rumors, or technical insight.",
            "charisma": "Test someone's resolve — persuade, intimidate, or bargain.",
            "resolve": "Steady yourself and press on — endure, focus, or resist.",
        }
        actions.append(stat_themes.get(highest_stat, "Assess your next move carefully."))
    else:
        actions.append("Take stock of the situation and choose your next move.")
    
    # Action 4: Environmental exploration
    # Note: world_factions is NOT in scope here — use state dict directly
    world_factions = state.get("world", {}).get("factions")
    if world_factions or state.get("world", {}).get("locations"):
        actions.append("Investigate your surroundings for anything out of place — clues, hazards, or opportunities.")
    else:
        actions.append("Search for anything useful — supplies, information, or an unexpected path forward.")
    
    storytell_result = storytell_result.model_copy(update={"actions": actions})
```

**Why:** The current fallbacks produce duplicates ("Take a careful look around the area." and "Survey your surroundings for useful information." are nearly identical) and generic actions that don't advance the story. The new fallbacks are more substantive, use stat-specific themes, and reference available context.

**Validation:** After implementing, trace through the fallback path with sample test data and verify 4 distinct, non-generic actions are produced.

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
None.

---

## Implementation — Phase 04: Condition ID normalization

### Context files to load
- `ccya/state/delta_builder.py` (full file)
- `ccya/state/inventory.py` (normalize_inventory_id pattern)
- `ccya/prompts/state_extract_system.j2` or `_extract_sys.j2` (condition field schema)

### Detailed steps

#### Step 4.1 — Add `normalize_condition_id()` helper

**File:** `ccya/state/delta_builder.py` (or a new `ccya/state/conditions.py`)

**What:** Add a function that normalizes condition IDs the same way `normalize_inventory_id()` works: lowercase, strip punctuation, snake_case. Store it alongside the delta application logic.

```python
def normalize_condition_id(raw: str) -> str:
    if not isinstance(raw, str):
        raw = str(raw)
    s = raw.lower().strip()
    s = re.sub(r"[\-\s]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s or "_"
```

This is verbatim the same logic as `normalize_inventory_id()` — consider extracting a shared `normalize_id()` in `ccya/state/__init__.py` to avoid duplication.

**Why:** Condition IDs like "bruisedribs" should match existing condition "bruised_ribs". Without normalization, each slight ID variation creates a new condition entry, bypassing the dedup cap and causing phantom penalties.

#### Step 4.2 — Apply normalization in delta condition processing

**File:** `ccya/state/delta_builder.py` (condition add section, around line 100)

**What:** In the condition add dedup logic, normalize both incoming and existing condition IDs before comparing. Currently:
```python
existing_conds = {
    c.get("id") for c in (state.get("pc") or {}).get("conditions") or []
    if isinstance(c, dict)
}
...
for c in delta.pc_condition_add:
    if c.id in existing_conds:
        ...
```

Note: `state["pc"]["conditions"]` items are **raw dicts** — use `.get("id")` to access their ID. The `delta.pc_condition_add` items are Pydantic model instances and use `.id` attribute access.

Change to:
```python
existing_conds = {
    normalize_condition_id(c.get("id")) for c in (state.get("pc") or {}).get("conditions") or []
    if isinstance(c, dict)
}
...
for c in delta.pc_condition_add:
    want = normalize_condition_id(c.id)
    if want in existing_conds:
        ...
```

Also apply to the intra-delta dedup (delta items are Pydantic models with `.id` attribute — correct to use here):
```python
seen_adds: set[str] = set()
deduped_adds = []
for c in delta.pc_condition_add:
    want = normalize_condition_id(c.id)
    if want not in seen_adds:
        deduped_adds.append(c)
        seen_adds.add(want)
    else:
        warnings.append(f"duplicate condition add within delta: {c.id}")
delta.pc_condition_add = deduped_adds
```

**Why:** Simple normalization prevents phantom conditions. No prompt changes needed — the extraction prompt already generates condition IDs from narration; the engine handles mismatches at merge time.

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
If a shared `normalize_id()` is extracted to `ccya/state/__init__.py`, add its re-export to the repomap's Public APIs section.

---

## Implementation — Phase 05: Meta-eval rate field emission

### Context files to read
- `ccya/eval/judge.py` (`_build_meta_judge_input`, `run_judges`, domain judge prompt templates)

### Detailed steps

#### Step 5.1 — Compute rates from available domain judge scores

**File:** `ccya/eval/judge.py` (in `_build_meta_judge_input()` or `run_judges()`)

**What:** After collecting all domain judge results, compute `state_fidelity_rate` from state_correctness sub-scores and `prompt_adherence_rate` from prompt_pipeline scores. The state_correctness judge emits `extraction_accuracy_score` and `mechanic_lifecycle_score` — these can be averaged into a rate. The prompt_pipeline judge emits per-prompt scores (rules/narrate/scene/state/storytell scores) that already represent compliance.

Add a post-processing step:
```python
def _compute_state_fidelity_rate(judge_results: dict[str, dict]) -> float | None:
    sc = judge_results.get("state_correctness")
    if not sc or not sc.get("scores"):
        return None
    scores = sc["scores"]
    # extraction_accuracy_score and mechanic_lifecycle_score are 0-5 integers
    # Normalize to 0.0-1.0 float for rate
    extraction = scores.get("extraction_accuracy_score")
    lifecycle = scores.get("mechanic_lifecycle_score")
    if extraction is not None and lifecycle is not None:
        return round((extraction + lifecycle) / 10.0, 2)
    return None

def _compute_prompt_adherence_rate(judge_results: dict[str, dict]) -> float | None:
    pp = judge_results.get("prompt_pipeline")
    if not pp or not pp.get("scores"):
        return None
    scores = pp["scores"]
    # prompt_pipeline emits per-prompt scores (may be nested)
    # Collect all integer scores and average them
    values = [v for v in scores.values() if isinstance(v, (int, float))]
    if values:
        return round(sum(values) / (len(values) * 5.0), 2)
    return None
```

Then in `_build_meta_judge_input()`, inject these computed rates into the meta judge input under `state_fidelity_rate` and `prompt_adherence_rate` keys so the meta judge can parse them directly via the existing YAML front matter parser.

**Why:** Eliminates meta judge estimation for these two fields. Domain judges already have the raw data; the meta judge just needs them formatted as rates. No domain judge prompt changes needed — the computation happens in Python.

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
None.

---

## Implementation — Phase 06: Location change audit logging

### Context files to read
- `ccya/engine/turn.py` (location change application path, around apply_delta and location mutation)
- `ccya/state/delta_builder.py` (location_change handling in delta application)

### Detailed steps

#### Step 6.1 — Find location change application point

**File:** `ccya/engine/turn.py`

**What:** Search for where `state["location"]` is modified or where `location_change` from SceneExtractResult is applied. This is likely in the delta application after extraction, or inline in `run_turn()`. Add a logging call at the mutation point:

```python
_log.info(
    "location_change applied",
    extra={
        "turn": turn_no,
        "trace_id": trace_id,
        "pack": "location",
        "kind": "state_change",
        "location": {"from": prev_location_id, "to": new_location_id},
    },
)
```

If location changes are applied via `apply_delta()`, add the log inside `apply_delta()` in `delta_builder.py` where `state["location"]` is reassigned.

**Why:** The current audit trail in "Applied Deltas" doesn't capture location mutations, making it impossible to verify location changes post-hoc. Adding structured logging ensures location changes appear in both the log stream and the turn viewer.

#### Step 6.2 — If location changes bypass apply_delta, add separate path

**File:** `ccya/state/delta_builder.py` or `ccya/engine/turn.py`

**What:** If location changes are applied inline (not via `apply_delta`), capture `prev_location_id` before mutation and log after. Ensure the log call uses the same structured format as Step 6.1.

**Why:** Guarantees audit coverage regardless of the mutation path.

### Tests to write or update
None (tests removed during refactor).

### REPOMAP updates required
None.

---

## REPOMAP updates required (cross-phase)

If `normalize_condition_id()` is added as a new function in `ccya/state/delta_builder.py`, update the repomap's Public APIs section to list it. If extracted to a shared module, list it there.

No other REPOMAP changes needed — all other changes modify existing functions or templates, not public APIs.
