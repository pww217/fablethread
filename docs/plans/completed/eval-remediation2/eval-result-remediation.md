I have everything I need. Here is the comprehensive plan.

***

# Plan: Eval Run `20260509T053631Z` — Full Remediation

## Table of Contents

1. [Status](#status)
2. [Part of](#part-of)
3. [Dependencies](#dependencies)
4. [Objective](#objective)
5. [Non-goals](#non-goals)
6. [Affected Files](#affected-files)
7. [Firm Decisions](#firm-decisions)
8. [Phase 01 — Suppress Thinking on All Pipeline Steps](#phase-01)
9. [Phase 02 — Actions Date Plain Text](#phase-02)
10. [Phase 03 — Narrator Inventory Binding Rule](#phase-03)
11. [Phase 04 — Narrator Tense Conflict Resolution](#phase-04)
12. [Phase 05 — State Extractor Inventory Mapping Rule](#phase-05)
13. [Phase 06 — Progress: Turn Stamp Injection](#phase-06)
14. [Phase 07 — Progress: Quest Deduplication Rule](#phase-07)
15. [Phase 08 — Progress: Quest Objective Completion on Contact](#phase-08)
16. [Phase 09 — Rules: Soft-Fail / Narrative Bridge Directive](#phase-09)
17. [Phase 10 — Scene: Location Description Novelty Guard](#phase-10)
18. [Phase 11 — Auto-Checker: NPC False-Positive Suppression](#phase-11)
19. [Phase 12 — REPOMAP and TODO Updates](#phase-12)
20. [Ambiguities Requiring Resolution](#ambiguities-requiring-resolution)

***

## Status
`open`

## Part of
`docs/plans/eval-remediation-2/`

## Dependencies
- Plans A–E under `docs/plans/eval-results-remediation/` must be merged and complete. All are marked `[x]` in TODO.md as of this writing.
- No other open plans touch the files listed here.

## Objective
The eval run `20260509T053631Z_eklk7z_8` surfaced ten distinct actionable failure modes across all five pipelines plus the auto-checker harness. The two highest-severity are: (1) thinking tokens leaking into every pipeline step, creating latency with no benefit since none of the extractors or rules step require chain-of-thought, and (2) the `actions` date field rendering as a raw ISO timestamp string in the UI. Beyond those, the eval identified narrator-state desync on inventory (the single most severe mechanical flaw per the judge), a tense contradiction between `narrate_system.j2` and pack `style.md`, state extractor hallucinating inventory IDs, progress extractor hard-coding `turn: 0`, progress extractor creating duplicate quests, overly conservative objective completion on "contact/meet" objectives, rules pipeline lacking a `soft_fail` directive for near-misses, scene extractor redundantly re-emitting unchanged location descriptions, and an auto-checker regex producing false-positive NPC name failures. This plan addresses all of them in dependency order.

## Non-goals
- Does NOT change model selection, temperature, or any `EngineConfig` numeric parameters beyond the thinking flags.
- Does NOT redesign the momentum system or add momentum-recovery mechanics (noted in the eval's "Additional Observations" but out of scope for a prompt/mechanics fix).
- Does NOT implement prompt deduplication / condensed Recent Events for extractors (noted in eval's "Prompt Redundancy Analysis" as a potential optimization — left for a future plan).
- Does NOT add a `narrative_bridge` mechanic to the rules output schema (Phase 09 adds a directive instruction only; schema expansion is a separate P2 effort).
- Does NOT touch compaction — compaction did not fire in this run and its eval is deferred to a longer run.
- Does NOT change the `_FakeLLM` or test fixtures beyond what is needed for thinking suppression.

## Affected Files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/engine/llm_client.py` | modify | Phase 01: verify/fix `apply_thinking` call — ensure `/no_think` is emitted unconditionally for all streams unless flag explicitly enables thinking |
| `ccya/engine/narrate.py` | modify | Phase 01: confirm `enable_narrate_thinking` default is `False` and wired |
| `ccya/engine/extraction.py` | modify | Phase 01: confirm `enable_extract_thinking` default is `False` and wired to all three extractors |
| `ccya/engine/rules.py` | modify | Phase 01: add `/no_think` suppression to the rules LLM call |
| `ccya/models.py` | investigate | Phase 01: confirm `EngineConfig` thinking flag defaults |
| `ccya/server/routes.py` | modify | Phase 02: format `ts` field as human-readable date string before serializing to the actions/events response |
| `ccya/prompts/narrate_system.j2` | modify | Phases 03 + 04: add hard inventory cross-reference rule; remove conflicting tense declaration |
| `ccya/prompts/narrate_user.j2` | modify | Phase 03: ensure inventory list block is prominently positioned with a heading the LLM cannot skip |
| `ccya/prompts/extract_state_system.j2` | modify | Phase 05: add canonical ID mapping rule for generic currency/item terms |
| `ccya/prompts/extract_progress_system.j2` | modify | Phases 06 + 07 + 08: add turn injection rule; add quest dedup rule; soften contact-objective completion threshold |
| `ccya/prompts/extract_progress_user.j2` | modify | Phase 06: inject `{{turn_no}}` variable into `recent_events_add` schema line |
| `ccya/prompts/rules_system.j2` | modify | Phase 09: add `soft_fail` / `narrative_bridge` directive for near-miss rolls |
| `ccya/prompts/extract_scene_system.j2` | modify | Phase 10: strengthen location_description novelty guard |
| `ccya/eval/universal_asserts.py` | modify | Phase 11: tighten NPC mention regex to exclude PC name and sentence-initial capitals |
| `docs/plans/TODO.md` | modify | Phase 12: add this plan entry |
| `docs/REPOMAP/engine.md` | modify | Phase 12: note thinking suppression change in rules pipeline |

***

## Firm Decisions

1. **Thinking is suppressed unconditionally on all five pipeline steps.** The narrate, extract_scene, extract_state, extract_progress, and rules calls all get `/no_think` unless the corresponding `enable_*_thinking` flag is `True`. The latency cost is not justified for structured JSON extraction or rules classification. This is not configurable per-turn — it is controlled only by `EngineConfig`.
2. **The actions/events `ts` field is formatted at the server boundary, not in the engine.** The engine continues to store UTC ISO strings internally in `events.jsonl`. The formatting transform lives in the route or serializer that produces the UI response. This preserves a queryable timestamp in storage.
3. **The narrator's tense is determined by `pack_style` / `narrator_rules` when present; `narrate_system.j2` defers to the pack.** The system prompt's "Second person, present tense" declaration is softened to "Second person" and the tense is left to the pack's style block. When no pack style is present, the system prompt default is past tense (the more natural storytelling tense and the pack default).
4. **Inventory cross-reference is a hard rule in `narrate_system.j2`, not a suggestion.** The wording uses the imperative and is placed in the existing `## Items and inventory` section where it will be read before prose generation.
5. **State extractor mapping for generic currency terms is explicit and bounded.** The rule maps a short list of known generic terms (`coin`, `silver`, `iron`, `gold`, `credits`, `cash`, `roll of`, `stack of`) to the canonical `credits` ID in the default pack. This is pack-specific — the rule uses the variable `{{currency_id}}` injected from the pack config if it exists, otherwise hardcodes `credits`. **Ambiguity: it is unclear if the pack config exposes a `currency_id` field. This must be resolved before execution — see Ambiguities.**
6. **Turn number injection into `recent_events_add` is engine-side, not LLM-side.** The correct fix is to have the engine post-process the extractor's JSON output and overwrite `turn` on every element of `recent_events_add` before delta application. This is more reliable than instructing the LLM to fill it. The prompt rule is added as a belt-and-suspenders fallback only.
7. **Quest dedup threshold in the prompt is 60% title token overlap, not 50%.** The judge suggested 50% but that would false-positive on generic quest words ("deliver the", "find the"). 60% is tighter.
8. **The `soft_fail` directive is a prompt-only addition.** It does not add a new `band` value or change the `RulesOutcome` schema. It adds a narrative instruction to the rules system prompt: when the final roll total is within 1 of the success threshold, the narrator is given latitude to treat the outcome as a "complication-only" beat rather than a full punishment.
9. **Auto-checker NPC false-positive fix is in `universal_asserts.py` only.** No prompt changes are needed for this issue.

***

## Phase 01 — Suppress Thinking on All Pipeline Steps

### Context files to load
- `ccya/engine/llm_client.py` (full)
- `ccya/engine/rules.py` (full)
- `ccya/engine/narrate.py` (full)
- `ccya/engine/extraction.py` (lines 1–100 for the top-level call scaffolding, then the three extractor call sites)
- `ccya/models.py` (the `EngineConfig` class)
- `AGENTS.md`

### Overview
Qwen3 models (and any model that supports `/think` / `/no_think` tokens) will produce thinking tokens by default unless explicitly suppressed. The current code appends `/no_think` only when the engine config flag is `True` — but the flags default to `False`, meaning `/no_think` is never appended unless the caller explicitly sets it. This inverts the intended behavior: thinking should be opt-in, not opt-out. Every pipeline step except a possible future debug mode should run with thinking suppressed.

### Detailed steps

#### Step 01.1 — Read and confirm `apply_thinking` in `llm_client.py`

**File:** `ccya/engine/llm_client.py`

**What:** Locate `apply_thinking` (or equivalent function that appends `/think` or `/no_think` to the message content). Confirm its current logic. Expected current shape:

```python
def apply_thinking(messages, enable: bool) -> list:
    if enable:
        # append /think
    else:
        # append /no_think  ← this branch must exist and be the default path
```

If the function only appends `/think` when `enable=True` and does nothing when `enable=False` (i.e., no `/no_think` emitted), rewrite the `else` branch to emit `/no_think`:

```python
def apply_thinking(messages: list[dict], enable: bool) -> list[dict]:
    """Append /think or /no_think to the last user message."""
    if not messages:
        return messages
    messages = [m.copy() for m in messages]
    last = messages[-1]
    suffix = " /think" if enable else " /no_think"
    last["content"] = last["content"].rstrip() + suffix
    messages[-1] = last
    return messages
```

**Why:** Thinking tokens add 2–5 seconds of latency per call on a 7B model. None of the structured JSON extractors benefit from chain-of-thought. The rules step performs a simple classification. `/no_think` must be explicit because the model's default is to think.

**Validation:** `grep -n "apply_thinking\|/no_think\|/think" ccya/ccya/engine/llm_client.py` — confirm both branches exist.

#### Step 01.2 — Confirm `rules.py` calls `apply_thinking`

**File:** `ccya/engine/rules.py`

**What:** Locate the LLM call site. If `apply_thinking` is not called before the rules LLM call, add it. The rules pipeline has no thinking flag in `EngineConfig` currently — add a call with `enable=False` (hardcoded, not configurable, since rules classification never needs chain-of-thought):

```python
messages = apply_thinking(messages, enable=False)
```

Place this immediately before the `await env.llm(...)` or equivalent call.

**Why:** The judge traces show the rules pipeline producing thinking tokens. This is the confirmed leak source for at least the rules step.

**Validation:** Run a single eval turn with a Qwen3 model and confirm `<think>` does not appear in the rules stream output. If `FakeLLM` is used in tests, this is a no-op (FakeLLM doesn't produce thinking tokens).

#### Step 01.3 — Confirm `narrate.py` and `extraction.py` call `apply_thinking` through the config flags

**File:** `ccya/engine/narrate.py`, `ccya/engine/extraction.py`

**What:** Confirm both files call `apply_thinking(messages, enable=config.enable_narrate_thinking)` and `apply_thinking(messages, enable=config.enable_extract_thinking)` respectively, AND that `apply_thinking` now correctly emits `/no_think` when `enable=False` (ensured by Step 01.1).

If either call site is missing, add it.

**Validation:** `grep -n "apply_thinking" ccya/ccya/engine/narrate.py ccya/ccya/engine/extraction.py` — must show at least one call per file.

#### Step 01.4 — Confirm `EngineConfig` defaults

**File:** `ccya/models.py`

**What:** Locate `EngineConfig`. Confirm:
```python
enable_narrate_thinking: bool = False
enable_extract_thinking: bool = False
```
If either defaults to `True`, change to `False`. No new fields needed.

**Validation:** `grep -n "enable.*thinking" ccya/ccya/models.py` — both must be `False`.

### Tests to write or update
No new tests. Existing `test_engine_smoke.py` and `test_engine_pipeline.py` use `FakeLLM` which ignores `/no_think`. The behavioral fix is verified by a real eval run.

If a test exists that calls `apply_thinking` directly, update it to assert `/no_think` is appended when `enable=False`.

### REPOMAP updates required
`docs/REPOMAP/engine.md` — note that `apply_thinking` now unconditionally emits one of the two tokens (never a no-op). Update the function description if it currently says "appends /think when enabled."

### Risks
1. If the model doesn't support `/no_think` (non-Qwen3 model in use), the suffix will appear as literal text in the prompt. **Mitigation:** The executor must confirm the configured model supports these control tokens. If not, `apply_thinking` should be a no-op for non-Qwen models — add a model name check if needed. **Flag this as an ambiguity if model identity is not confirmed in `EngineConfig`.**
2. The `/no_think` suffix is appended to the last user message. If the user message is empty or only whitespace, this may create a malformed message. **Mitigation:** The `rstrip()` + append pattern handles this; confirm no test has a zero-content user message.

***

## Phase 02 — Actions Date Plain Text

### Context files to load
- `ccya/server/routes.py` (full, or the section that serializes `events.jsonl` or `actions` to the UI response)
- `ccya/engine/turn.py` (the section that writes the `ts` field to events, to confirm format)

### Overview
The `ts` field on action/event entries is stored and rendered as a UTC ISO string (e.g., `2026-05-09T15:33:00Z`). The UI renders this raw string directly. It should be a human-readable relative or absolute time string. This is a server/serialization fix, not an engine fix.

### Detailed steps

#### Step 02.1 — Locate `ts` write site in `turn.py`

**File:** `ccya/engine/turn.py`

**What:** Find where `ts` is written to the event dict. Expected:
```python
"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
```
Do NOT change this. The engine stores the machine-readable format. The formatting transform is server-side.

**Validation:** Confirm the format string. Note the exact key name (`ts`, `timestamp`, or other).

#### Step 02.2 — Add formatting transform in `routes.py`

**File:** `ccya/server/routes.py`

**What:** Locate the route that returns the actions list or events feed to the UI. Before serializing each event/action to the JSON response, apply a display formatting function to the `ts` field:

```python
def _format_ts(ts_str: str) -> str:
    """Convert UTC ISO string to a human-readable display string."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        # Display as: "May 9 · 3:33 PM"  (local server time is not available; use UTC)
        return dt.strftime("%-d %b · %-I:%M %p UTC")
    except (ValueError, AttributeError):
        return ts_str  # fallback: return raw if unparseable
```

Apply this to the `ts` field of each action/event dict before it leaves the route handler. Do not mutate the stored dict — copy it first:

```python
display_event = {**event, "ts": _format_ts(event.get("ts", ""))}
```

**Why:** The UI renders the raw `ts` value directly. The player sees `2026-05-09T15:33:00Z` in the actions list. This is confirmed visible in the UI per the user's report.

**Validation:** Run the server locally and inspect the actions panel. The `ts` field should now display as e.g. `9 May · 3:33 PM UTC`. Confirm no `T` or `Z` characters appear.

### Tests to write or update
Add a unit test in `tests/test_server.py` (or equivalent) asserting that `_format_ts("2026-05-09T15:33:00Z")` returns a string containing neither `T` nor `Z` and matches the expected format pattern.

### REPOMAP updates required
None. This is a display-only transform; no schema change.

### Risks
1. `%-d` and `%-I` strftime directives are Linux-only (strip leading zero). On macOS in CI: use `%d` and `%I` and strip manually, or use `%e`. **Mitigation:** Use `dt.strftime("%d %b · %I:%M %p UTC").lstrip("0")` which is portable.
2. The UI may display `ts` in multiple places (actions panel, turn history). Confirm all sites use the same serialization path before closing.

***

## Phase 03 — Narrator Inventory Binding Rule

### Context files to load
- `ccya/prompts/narrate_system.j2` (full — already read)
- `ccya/prompts/narrate_user.j2` (full)

### Overview
The narrator consistently invents item spending that contradicts the canonical `state.inventory`. The existing `## Items and inventory` section in `narrate_system.j2` does not include a cross-reference obligation. The user prompt provides the inventory list but does not label it as a constraint. Add a hard binding rule and ensure the inventory block in the user prompt has a prominent heading.

### Detailed steps

#### Step 03.1 — Add inventory cross-reference rule to `narrate_system.j2`

**File:** `ccya/prompts/narrate_system.j2`

**What:** In the `## Items and inventory` section, immediately after the existing paragraph about quantification and bolding, add:

```
**Inventory is a hard constraint.** Before narrating any item usage, spending, or consumption, verify the item appears in the `## inventory` list in the user prompt. If the player's action implies spending an item not in that list, narrate the *attempt* or *intent* without confirming a successful transfer. Never describe the player producing, spending, or losing an item that is not in their current inventory. If the inventory list shows `credits: 500`, the player has 500 credits — do not invent `iron_coin`, `silver`, or other substitute denominations.
```

**Why:** The judge identified this as the most critical mechanical flaw. The narrator hallucinated spending `credits` when the balance was 0, and invented `iron_coin` when the canonical field was `credits: 500`. The state extractor then tried to honor these fictional spends, failed delta validation, and wasted tokens.

**Validation:** Visually inspect the template renders in a test eval run. The narrator must not invent items absent from inventory.

#### Step 03.2 — Ensure inventory block has a prominent heading in `narrate_user.j2`

**File:** `ccya/prompts/narrate_user.j2`

**What:** Locate the block that renders `state.inventory` in the user prompt. It currently may render as a flat list under a generic heading or without a heading. Ensure it is labeled:

```jinja
{% if inventory %}
## inventory (cross-reference before describing item use)
{% for item in inventory %}- {{ item.id }}: {{ item.qty }}{% if item.description %} — {{ item.description }}{% endif %}
{% endfor %}
{% endif %}
```

The parenthetical `(cross-reference before describing item use)` acts as a per-call reminder reinforcing the system rule.

**Why:** LLMs skip sections that blend into the surrounding context. A labeled heading with an explicit callout is less likely to be ignored.

**Validation:** Render `narrate_user.j2` with a non-empty inventory and confirm the heading and parenthetical appear.

### Tests to write or update
`tests/test_prompt_audit.py` — add a byte-stability assertion for the rendered `narrate_system.j2` to detect unintended drift after this change.

### REPOMAP updates required
None structural. The PROMPTING.md note about narrator inventory rules may be worth updating, but is not required.

### Risks
1. Adding a prominent heading may shift the character count of `narrate_user.j2`. If a token ceiling test exists for this prompt, it will need updating. Per Plan E firm decision 1, token ceilings are commented out — no action needed.
2. The instruction "narrate the *attempt* without confirming a transfer" may produce narratively awkward output when the player insists on spending an item they don't have. The alternative is to let the narrator refuse the action silently, which is worse. Accept the awkwardness as a graceful failure mode.

***

## Phase 04 — Narrator Tense Conflict Resolution

### Context files to load
- `ccya/prompts/narrate_system.j2` (full — already read)
- The default world pack's `style.md` or `scenario.yaml` narrator_rules / pack_style field (location unclear — see Ambiguities)

### Overview
`narrate_system.j2` opens with "Second person, present tense." The default world pack's style block demands past tense. The narrator defaults to present tense, violating the pack style. The system prompt tense declaration must be removed or softened so the pack style takes precedence.

### Detailed steps

#### Step 04.1 — Soften tense declaration in `narrate_system.j2`

**File:** `ccya/prompts/narrate_system.j2`

**What:** Change the opening line from:
```
Narrate the next beat of a text adventure. Second person, present tense, 2-4 short paragraphs.
```
To:
```
Narrate the next beat of a text adventure. Second person. Follow the tense specified in the ## Genre tone section below; if no tense is specified, use past tense. 2-4 short paragraphs.
```

**Why:** The opening declaration overrides the `## Genre tone` block because it appears first and is stated declaratively. Moving tense authority to the pack style block allows each pack to control its own voice.

**Validation:** Run a short eval with the default pack. Narrator output should use past tense (e.g., "You stepped through the door" not "You step through the door"). If the pack style block includes an explicit tense instruction, confirm the narrator honors it.

#### Step 04.2 — Verify the default pack's style block includes a tense instruction

**File:** Default pack's `scenario.yaml` or `style.md` (path unknown — see Ambiguities)

**What:** Confirm the default pack's `pack_style` or `narrator_rules` includes a tense statement. If it does not, add one. Example:
```
Narrate in second person, past tense.
```

**Why:** If the pack style block is silent on tense, the narrator's fallback (now past tense per Step 04.1) is correct for most packs, but explicit is safer.

**Validation:** Render `narrate_system.j2` with the default pack loaded. Confirm the `## Genre tone` section contains a tense instruction.

### Tests to write or update
No automated test for prose tense. This is validated by eval run inspection.

### REPOMAP updates required
`docs/PROMPTING.md` — note that tense authority belongs to the pack style block, not the system prompt.

### Risks
1. Existing packs that relied on "present tense" as a system-level default will now get past tense. Only the default pack is known. If custom packs exist, audit their style blocks. **Mitigation:** The executor must `grep -rn "tense" ccya/packs/` before applying.

***

## Phase 05 — State Extractor Inventory Mapping Rule

### Context files to load
- `ccya/prompts/extract_state_system.j2` (full)
- `ccya/prompts/extract_state_user.j2` (full)

### Overview
The state extractor invented `iron_coin` as an inventory ID when the narrator used the phrase "iron coin." The extractor must map generic currency language to the canonical ID rather than inventing new IDs. This is an extraction prompt rule, not a schema change.

### Detailed steps

#### Step 05.1 — Add canonical ID mapping rule to `extract_state_system.j2`

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Locate the inventory rules section (the block that describes `inventory_add` / `inventory_remove` field rules). Add immediately after the existing rules:

```
**Generic item mapping:** If the narration references a generic denomination or container term (e.g., "coin", "silver", "iron coin", "gold piece", "roll of cash", "stack of credits", "pouch of money"), map it to the closest matching ID in the `## inventory` list provided in the user prompt. Do NOT invent a new inventory ID for a generic term. If no inventory item clearly matches, do NOT emit an inventory_remove or inventory_add for that reference — the narrator's language is imprecise and the state should not change.
```

**Why:** The extractor is doing the right thing mechanically (following the narrator's prose) but the narrator is using imprecise language that doesn't map to canonical IDs. This rule gives the extractor a fallback: prefer a fuzzy match over ID invention.

**Validation:** In a test eval where the narrator says "iron coin," the extractor must map to `credits` (the only matching inventory ID) or emit nothing. It must not emit `iron_coin`.

### Tests to write or update
`tests/test_engine_pipeline.py` — add a `Class D` or new class test: given a narration containing "iron coin" and an inventory with `credits: 500`, assert that `extract_state` does not produce `inventory_remove: [{id: "iron_coin", ...}]`.

### REPOMAP updates required
None.

### Risks
1. The mapping rule is heuristic — "closest matching ID" is subjective. The LLM may still mis-map in edge cases. **Mitigation:** The delta validation pipeline rejects non-existent IDs, so the worst case is a rejected delta, not a corrupted state. This is the existing safety net.

***

## Phase 06 — Progress: Turn Stamp Injection

### Context files to load
- `ccya/prompts/extract_progress_system.j2` (full — already read)
- `ccya/prompts/extract_progress_user.j2` (full — already read)
- `ccya/engine/extraction.py` (the `_run_progress_extraction` call site and post-processing block)

### Overview
The progress extractor's `recent_events_add` schema includes `"turn": 0` as a placeholder. The LLM copies the `0` literally. The correct fix is engine-side: after receiving the extractor's JSON, overwrite `turn` on every element of `recent_events_add` with the actual `turn_no`. The prompt rule is added as belt-and-suspenders.

### Detailed steps

#### Step 06.1 — Engine-side turn stamp overwrite in `extraction.py`

**File:** `ccya/engine/extraction.py`

**What:** After deserializing the progress extractor's JSON output into a `ProgressExtractResult` (or equivalent dict), and before returning it, add a post-processing step:

```python
# Overwrite turn stamp on any newly added events — the LLM cannot know the
# current turn number reliably; the engine stamps it authoritatively.
if progress_result and progress_result.recent_events_add:
    for event in progress_result.recent_events_add:
        event["turn"] = turn_no  # or event.turn = turn_no if Pydantic model
```

**Why:** This is the most reliable fix. Regardless of what the LLM outputs in the `turn` field, the engine knows the correct value and overwrites it. The LLM instruction is belt-and-suspenders only.

**Validation:** `universal_asserts.py` `universal.recent_events_add.turn_stamped` assertion must pass on the next eval run. Turns 2 and 3's events must have `turn: 2` and `turn: 3` respectively, not `0`.

#### Step 06.2 — Add turn injection instruction to `extract_progress_system.j2`

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** In the `recent_events_add` field rules section, change the schema line:
```
Each: `{"id": "snake_case_id", "text": "Event description", "turn": 0}`.
```
To:
```
Each: `{"id": "snake_case_id", "text": "Event description", "turn": <CURRENT_TURN>}`. The current turn number is shown at the top of the user prompt under `## turn`. Always use that value — never 0.
```

#### Step 06.3 — Add `## turn` block to `extract_progress_user.j2`

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Add as the very first line of the template (before `## active_domains`):

```jinja
## turn
{{ turn_no }}

```

**Why:** The system prompt rule references `## turn` in the user prompt. It must exist.

**Validation:** Render the template with `turn_no=5`. The first line must be `## turn\n5\n`.

#### Step 06.4 — Confirm `turn_no` is passed to the progress extractor call

**File:** `ccya/engine/extraction.py`

**What:** Locate the call that renders `extract_progress_user.j2`. Confirm `turn_no` is in the Jinja context. If it is not, add it.

**Validation:** `grep -n "turn_no" ccya/ccya/engine/extraction.py` — must appear in the progress user context dict.

### Tests to write or update
`tests/test_engine_pipeline.py` — add an assertion in the progress extraction tests that every element of `recent_events_add` has `turn == <expected_turn_no>` after pipeline execution. Use `FakeLLM` returning `"turn": 0` to confirm the engine overwrite fires.

### REPOMAP updates required
`docs/REPOMAP/engine.md` — note the post-processing turn-stamp overwrite on `recent_events_add`.

### Risks
1. If `ProgressExtractResult.recent_events_add` is a list of Pydantic models with `turn: int`, direct dict mutation won't work — must use `event.turn = turn_no`. **Mitigation:** Executor must check whether the result is deserialized into Pydantic models or raw dicts before writing the overwrite. If Pydantic, use attribute assignment. If raw dict (post-JSON-parse before model construction), use `event["turn"] = turn_no`.

***

## Phase 07 — Progress: Quest Deduplication Rule

### Context files to load
- `ccya/prompts/extract_progress_system.j2` (full — already read)
- `ccya/prompts/extract_progress_user.j2` (full — already read)

### Overview
Turn 6 created `deliver_stained_ledger` as a new quest when `deliver_the_ledger` already existed. The progress extractor system prompt already instructs the model to use the quest threshold directive, but it does not include an explicit deduplication rule. Adding one closes the gap.

### Detailed steps

#### Step 07.1 — Add quest dedup rule to `extract_progress_system.j2`

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** In the `quest_updates` field rules, after the existing "New quest threshold guidance for this turn is in the user prompt" line, add:

```
**Quest deduplication:** Before creating a new quest, scan the `## active_quests` list in the user prompt. If a new quest would share a similar subject, target NPC, or object with an existing quest (e.g., both involve delivering the same item, finding the same person, or resolving the same conflict), update the existing quest instead of creating a new one. New quest IDs that differ only in word choice from existing IDs (e.g., `deliver_stained_ledger` vs `deliver_the_ledger`) are duplicates. Prefer the shorter, more general existing ID. Only create a genuinely new quest if the task, target, and context are all distinct from every active quest.
```

**Why:** The LLM generated a near-duplicate quest ID because it interpreted the noun "stained ledger" as a unique object warranting its own quest, ignoring the existing `deliver_the_ledger` quest that covered the same task.

**Validation:** In a test eval scenario where an existing `deliver_the_ledger` quest is active and the narration references the ledger, the progress extractor must not emit a new `deliver_stained_ledger` quest — it must emit a `quest_updates` with the existing ID instead.

### Tests to write or update
`tests/test_engine_pipeline.py` — add a `Class D` test: given an active quest `deliver_the_ledger` and a narration referencing the stained ledger, assert that `extract_progress` does not produce a new quest with a different ID for the same delivery task.

### REPOMAP updates required
None.

### Risks
1. The dedup rule may suppress genuinely new quests that happen to share a word with an existing quest. **Mitigation:** The rule requires multiple dimensions of similarity (subject AND target AND context), not just ID string similarity. This should prevent false suppression.

***

## Phase 08 — Progress: Quest Objective Completion on Contact

### Context files to load
- `ccya/prompts/extract_progress_system.j2` (full — already read)

### Overview
Turn 8 failed to mark ledger delivery objectives as done despite clear narration of delivery. The existing `## Contact and meet objective rule` is well-written but was not triggered because the system prompt's general rules-outcome guidance ("No dice roll: do NOT complete quest objectives unless the narration explicitly and unambiguously states") created a conflicting prior. The contact rule needs to be positioned as an explicit override of the general rule.

### Detailed steps

#### Step 08.1 — Elevate the contact rule as an override in `extract_progress_system.j2`

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** The existing `## Contact and meet objective rule` section is already correct in content. Add a single line at the start of that section to make its override status explicit:

```
**This rule overrides the general rules-outcome guidance above.** Contact and meet objectives resolve on narrative presence, not roll outcome, even when no dice were rolled.
```

Additionally, add a note in the general rules-outcome guidance section to point back:

```
- No dice roll: do NOT complete quest objectives unless the narration explicitly and unambiguously states the objective is fulfilled. **Exception: see Contact and meet objective rule below.**
```

**Why:** The LLM honored the general rule and ignored the specific rule. Making the override relationship explicit in both places removes the ambiguity.

**Validation:** In a test eval where a "deliver the ledger to Halden" objective exists and the narration clearly shows Halden receiving the ledger, assert the objective is marked `done: true` regardless of `rules_outcome.band`.

### Tests to write or update
`tests/test_engine_pipeline.py` — add a test: given a `contact` objective and a narration confirming contact occurred, with `rules_outcome.rolled = false`, assert the objective is marked done.

### REPOMAP updates required
None.

### Risks
Low. The existing contact rule logic is correct — this is purely a precedence/clarity fix.

***

## Phase 09 — Rules: Soft-Fail / Narrative Bridge Directive

### Context files to load
- `ccya/prompts/rules_system.j2` (full)
- `ccya/engine/rules.py` (the `RulesOutcome` model construction and directive generation)
- `ccya/engine/directives.py` or equivalent (if `build_directive` lives in a separate module)

### Overview
Turns 7, 8, 10, and 11 produced successive `fail` / `setback` outcomes with no narrative bridge. The rules pipeline correctly classified these as failures, but the directive it passed to the narrator was fully punitive with no latitude for "interesting failure" narration. A `soft_fail` directive concept — applied when the roll total is within a configurable margin of the success threshold — would give the narrator permission to make failures narratively generative rather than just punishing.

This is a **prompt-only** addition. The `RulesOutcome` schema does not change. The directive text is what changes.

### Detailed steps

#### Step 09.1 — Add soft-fail directive to `build_directive` in `rules.py` (or directives module)

**File:** `ccya/engine/rules.py` (or wherever `build_directive` lives — **executor must locate this**)

**What:** In `build_directive`, locate the branch that handles `band == "fail"`. Currently it likely produces a directive along the lines of "The action fails. Narrate consequences." Add a sub-branch for near-miss fails:

```python
# Near-miss threshold: within 1 point of the success floor (band-specific)
# This is a narrative latitude instruction only — the band remains "fail"
NEAR_MISS_MARGIN = 1  # configurable if EngineConfig exposes it later

if band == "fail" and roll_total >= (success_floor - NEAR_MISS_MARGIN):
    complication_note = (
        " The roll was close — narrate a complication or setback that still "
        "allows the story to move forward, rather than a full dead-end punishment."
    )
else:
    complication_note = ""
```

Then append `complication_note` to the fail directive string.

**Ambiguity: The executor must confirm that `roll_total` and `success_floor` are available at the point where `build_directive` is called. If not, this approach must be adapted. See Ambiguities.**

**Why:** The judge noted the binary success/failure mode creates a "death spiral" when multiple consecutive failures occur. A near-miss modifier gives the narrator a single sentence of latitude to break the spiral without changing the mechanical outcome.

**Validation:** In a test where `band == "fail"` and `roll_total` is within 1 of `success_floor`, assert the directive string contains "complication" or "move forward." For rolls clearly below the threshold, assert the standard fail directive is unchanged.

#### Step 09.2 — Document the near-miss directive in `rules_system.j2`

**File:** `ccya/prompts/rules_system.j2`

**What:** Locate the section describing directive values and add a note explaining that `fail` directives may include a near-miss complication note:

```
When a `fail` directive includes a near-miss note, the narration should describe a setback or complication that changes the situation without completely blocking the player. The player still fails — but the story advances.
```

**Validation:** Visual inspection of the rules system prompt. The note should appear in the directive description section.

### Tests to write or update
`tests/test_engine_pipeline.py` — add a test for `build_directive` with `band="fail"` at near-miss and clearly-failed rolls. Assert directive content differs appropriately.

### REPOMAP updates required
`docs/REPOMAP/engine.md` — note the near-miss complication modifier in the directive builder.

### Risks
1. `success_floor` may not be an accessible value at directive build time. **Mitigation:** This is the main ambiguity — see below. If the value is not available, a simpler fallback is to use the raw dice total relative to a fixed threshold (e.g., total >= 5 on a 2d6 scale counts as near-miss), but this is less accurate.
2. The complication note adds ~20 tokens to the rules output. Negligible.

***

## Phase 10 — Scene: Location Description Novelty Guard

### Context files to load
- `ccya/prompts/extract_scene_system.j2` (full)

### Overview
Turn 2 emitted a `location_description` that was identical to the seed state. The system prompt says "Do not re-describe unchanged surroundings" but the model ignored it. The instruction needs to be made more binding and operationalized — "how do you know if it's unchanged?" must be answered explicitly.

### Detailed steps

#### Step 10.1 — Strengthen the novelty guard in `extract_scene_system.j2`

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Locate the `location_description` field rule. Replace or augment the existing guidance with:

```
`location_description`: A short prose description of the current location's notable features. **Only emit if the narration introduces NEW environmental details not present in the prior location description shown in the user prompt.** Decision rule: compare the content of `## current_location_description` in the user prompt against what the narration reveals. If the narration adds no new spatial, atmospheric, or structural information, set `location_description` to `null`. If you are unsure whether the detail is new, set it to `null` — omission is safer than redundant re-description.
```

**Why:** The current instruction is a soft "do not re-describe" nudge. The LLM needs an explicit comparison anchor (`## current_location_description`) and a default-to-null tie-breaking rule.

#### Step 10.2 — Confirm `current_location_description` block exists in `extract_scene_user.j2`

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** Confirm the user prompt includes the existing `location_description` field value under a clear heading. If the heading is not `## current_location_description`, note the actual heading name so the system prompt instruction in Step 10.1 references the correct label. If the block does not exist, add it:

```jinja
{% if scene.location_description %}
## current_location_description (emit location_description only if narration adds NEW details)
{{ scene.location_description }}
{% endif %}
```

**Validation:** Render with a non-empty `scene.location_description`. Confirm the heading appears.

### Tests to write or update
None required beyond the existing scene extraction tests. Confirm existing tests still pass.

### REPOMAP updates required
None.

### Risks
1. Being too conservative about `location_description` novelty may cause the engine to miss genuine environmental updates. **Mitigation:** The judge scored `extract_scene` at 4/5 — this is a minor fix on an otherwise well-performing pipeline. The default-to-null tie-breaker is acceptable.

***

## Phase 11 — Auto-Checker: NPC False-Positive Suppression

### Context files to load
- `ccya/eval/universal_asserts.py` (full)

### Overview
The `universal.npc_mention.extracted` assert regex flagged `Voss` (the PC), `Who`, `Instead`, and `Your` as unregistered NPC names. These are false positives. The PC name must be excluded from the NPC mention check, and sentence-initial capitals must be filtered.

### Detailed steps

#### Step 11.1 — Fix the NPC mention regex in `universal_asserts.py`

**File:** `ccya/eval/universal_asserts.py`

**What:** Locate the `universal.npc_mention.extracted` assert (or equivalent). It currently extracts capitalized words from narration text and checks each against the known NPC registry. Apply two filters:

1. **Exclude PC name:** Before checking any token, skip it if it matches `state["pc"]["name"]` (case-insensitive).
2. **Exclude sentence-initial capitals:** Strip the first word of each sentence from the candidate set. A simple heuristic: after splitting narration into sentences (split on `. `, `! `, `? `), remove the first token of each sentence from the candidate list.

```python
def _extract_candidate_names(narration: str, pc_name: str) -> set[str]:
    """Extract capitalized tokens that are candidates for NPC names."""
    # Split into sentences and remove sentence-initial words
    sentences = re.split(r'(?<=[.!?])\s+', narration)
    sentence_starters = {s.split()[0].strip("\"'") for s in sentences if s.split()}
    
    # All capitalized words (not all-caps, not PC name, not sentence starters)
    candidates = set()
    for token in re.findall(r'\b[A-Z][a-z]{1,}\b', narration):
        if token.lower() == pc_name.lower():
            continue
        if token in sentence_starters:
            continue
        candidates.add(token)
    return candidates
```

**Why:** The current regex-based check has no awareness of grammatical context. Sentence-initial words and the PC's name are the two main false-positive sources confirmed in the eval output.

**Validation:** Run the auto-checker on the Turn 2 and Turn 11 narrations from the eval trace. The `Voss`, `Who`, `Instead`, and `Your` false positives must not appear. Legitimate NPC names (`Caron`, `Halden`) must still be caught when unregistered.

### Tests to write or update
`tests/test_universal_asserts.py` (or equivalent) — add a test asserting that `_extract_candidate_names` excludes PC name and sentence starters, but includes genuine NPC names.

### REPOMAP updates required
None.

### Risks
1. The sentence-starter heuristic will miss NPC names that happen to appear at the start of a sentence. **Mitigation:** This is a known tradeoff — reduce false positives at the cost of some true-positive misses. The assert is for eval harness hygiene, not production logic. Acceptable.
2. If narration contains dialogue (`"Halden said, ..."`), `Halden` would be a sentence-starter after the quote attribution. **Mitigation:** The regex `\b[A-Z][a-z]{1,}\b` already requires at least 2 characters. Most sentence starters after dialogue attribution are names the harness should catch. Accept the edge case for now.

***

## Phase 12 — REPOMAP and TODO Updates

### Context files to load
- `docs/plans/TODO.md`
- `docs/REPOMAP/engine.md`
- `docs/PROMPTING.md`

### Detailed steps

#### Step 12.1 — Add this plan to `TODO.md`

Add under `P3 — Inference Speed and Evaluation`:
```
- [ ] **Eval run remediation #2** — `eval-remediation-2/` — thinking suppression all pipelines, actions date format, narrator inventory binding, tense conflict, state extractor ID mapping, progress turn stamp + quest dedup + contact objective fix, rules soft-fail directive, scene novelty guard, auto-checker NPC regex — see `[eval-remediation-2/main.md](eval-remediation-2/main.md)`
```

#### Step 12.2 — Update `docs/REPOMAP/engine.md`

- Under `llm_client.py`: note that `apply_thinking` now emits `/no_think` when `enable=False` (not a no-op).
- Under `extraction.py`: note that `recent_events_add.turn` is overwritten engine-side post-extraction.
- Under `rules.py`: note that `build_directive` emits a near-miss complication note for `fail` band within 1 point of success floor.

#### Step 12.3 — Update `docs/PROMPTING.md`

- Add a note that `narrate_system.j2` tense authority was moved to the pack style block.
- Add a note that `extract_progress_system.j2` contact/meet objective rule is an explicit override of the general no-dice-roll rule.

### Final validation gate
`make check && make test` — all checks and tests pass.

***

## Ambiguities Requiring Resolution Before Execution

1. **`apply_thinking` exact current behavior.** The plan assumes it exists and is a no-op when `enable=False`. If it currently raises, is missing, or works differently, Phase 01 must be adapted. **Options:** A) It exists with a no-op else branch — add `/no_think` emission to that branch. B) It exists and already emits `/no_think` when `False` — then the real bug is that it's not being called for the rules pipeline. C) It doesn't exist — create it from scratch.

2. **Model identity and `/no_think` support.** The fix in Phase 01 assumes the configured model supports Qwen3-style `/think` / `/no_think` control tokens. If the model is not Qwen3 (or a compatible fork), appending `/no_think` will appear as literal text in the prompt. **Options:** A) Confirm Qwen3 is the configured model and proceed. B) Gate `apply_thinking` on a `model_supports_thinking_tokens: bool` field in `EngineConfig`.

3. **Pack `currency_id` field.** Phase 05 mentions mapping generic terms to a `{{currency_id}}` variable. It is unclear whether the pack schema exposes this field. **Options:** A) Hardcode `credits` as the default in the prompt and note it is pack-specific. B) Add a `currency_id` field to the pack schema (requires a separate schema change). C) Use a dynamic list of known currency-like terms and let the extractor fuzzy-match to whatever inventory ID looks most like currency.

4. **`roll_total` and `success_floor` availability in `build_directive`.** Phase 09 assumes these values are available when the directive is built. If the directive builder only receives the `band` string and not the raw roll numbers, the near-miss check cannot be implemented as described. **Options:** A) Pass `roll_total` and `success_floor` into `build_directive`. B) Compute the near-miss flag upstream in `rules.py` before calling `build_directive` and pass a boolean. C) Simplify: add the complication note to ALL `fail` bands (not just near-miss), and rely on the narrator's judgment to apply it appropriately.

5. **Default pack `style.md` / `scenario.yaml` path.** Phase 04 requires confirming and possibly editing the default pack's style block. The exact path is unknown from the files read. **Resolution:** Executor should `find ccya/packs/ -name "*.yaml" -o -name "style.md"` and locate the default pack's tense instruction before applying Phase 04.

6. **`routes.py` — which route(s) serialize actions/events.** Phase 02 assumes there is a single serialization path. If multiple routes return action/event data, all must apply the `_format_ts` transform. **Resolution:** Executor should `grep -rn '"ts"' ccya/ccya/server/` to find all serialization sites before applying.

## TODO.md Update
Add under `P3 — Inference Speed and Evaluation`, after the last `~~` completed item:

```
- [ ] **Eval run remediation #2** — thinking suppression all pipelines, actions date format, narrator inventory binding + tense fix, state extractor ID mapping, progress turn stamp + quest dedup + contact objective fix, rules soft-fail directive, scene novelty guard, auto-checker NPC regex — see `[eval-remediation-2/main.md](eval-remediation-2/main.md)`
```