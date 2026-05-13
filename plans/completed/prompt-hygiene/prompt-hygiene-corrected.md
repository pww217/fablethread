# Prompt Hygiene: Deduplication, Generic Examples, and Rules User Context

## Status

`completed`

## Phase Guide


| Phase | Name                     | Summary                                                              |
| ----- | ------------------------ | -------------------------------------------------------------------- |
| 01    | narrate_system cleanup   | Remove dead duplication; genericize named examples                   |
| 02    | rules_user context       | Replace last-turn narrative with outcome_summary; add assistant stub |
| 03    | extract_progress cleanup | Remove behavioral rules restated in user prompt                      |


## Objective

Several system prompts contain named game characters in illustrative examples (breaking generic reusability and polluting cache-stable content with instance-specific data), duplicate live-state data that already appears in the user prompt, or restate behavioral rules in the user prompt that already exist in the system prompt. This plan cleans those up without touching any prompt logic or behavioral intent.

## Non-goals

- No changes to any behavioral rules, decision logic, or output schemas.
- No changes to extract_scene, extract_state, or compact prompts (examples in those are already generic or justified).
- No creation of shared partials — caching architecture makes this counterproductive.
- No rubric or judge prompt changes.
- No changes to Python code, models, or engine logic.

---

## Implementation — Phase 01: narrate_system cleanup

### Files to pull for context

- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`

### Detailed steps

[Skipped 1.1]

---

#### Step 1.2 — Genericize named examples in `## Fail-band outcomes`

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the two named examples under `## Fail-band outcomes` (lines 101–104) with generic stand-ins using `[NPC_NAME]`, `[ITEM]`, and `[VERB]` placeholders. Preserve the Bad/Good structure and the rule text exactly.

**Why:** `Caron` and the ledger are characters from a specific pack. Using them in a role-level system prompt means the instruction leaks game-specific state into what should be cache-stable, generic guidance. Any pack's narrator will misread this as a hint that Caron is a character in their game.

**Code Snippet**

```jinja2
## Fail-band outcomes (BINDING)

On a FAIL band:
- The PC does not get what they asked for.
- The NPC does NOT engage constructively to help them.
- The NPC may refuse, stall, shut them down, or walk away.

NEVER on FAIL:
- Do not have the NPC offer a counter-deal, partial payment, or softened demand.
- Do not turn FAIL into PARTIAL by giving the PC a consolation prize.

Bad (do NOT do this on FAIL):
  [NPC_NAME] leans back, smiles thinly, and offers a different payment schedule.
Good (correct FAIL):
  [NPC_NAME] closes the ledger and says, "Then we have nothing to discuss," turning away.
```

**Validation:** Diff confirms only `Caron` → `[NPC_NAME]` change. No behavioral content altered.

---

#### Step 1.3 — Genericize named example in `## Player input is truth`

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the `## Conflict example` block's named characters (lines 32–38) with generic placeholders.

**Why:** Same reason as 1.2 — `Halden`, the merchant seal, and the ledger are pack-specific. Replace with `[NPC_NAME]`, `[ITEM_A]`, `[ITEM_B]`.

**Code Snippet**

```jinja2
**Conflict example (READ CAREFULLY):**
- Player says: "I sit across from [NPC_NAME] at his table, slide [ITEM_A] across, and hand him [ITEM_B]."
- GM beat says: "pressure: toughs circle and flank the player"
- WRONG: Narrate the toughs attacking and the player fighting them (this replaces the player's action).
- RIGHT: Narrate the player sitting down and sliding [ITEM_A]/[ITEM_B] across the table FIRST. Then describe the toughs circling and flanking as the player attempts this action — the toughs' presence is the environmental pressure, not the main event. The player's action (sitting, sliding [ITEM_A], handing [ITEM_B]) is the primary narration.
```

**Validation:** Diff confirms only named substitutions. Rule text and structure unchanged.

### Tests to write or update

No behavioral change — no new tests required. Existing `tests/test_engine_pipeline.py` narration path covers regression.

### REPOMAP and architecture updates

None — prompt file changes only, no new functions or signatures.

### Risks

1. Step 1.1 is SUPERSEDED by `wire-scenario-factions-locations-to-narrator.md`. The wire-scenario plan wires `world_factions`/`world_locations` through the turn pipeline, making the `{% if world_factions or world_locations %}` block in `narrate_user.j2` functional. The prompt-hygiene plan's original intent for Step 1.1 (remove narration directives from system prompt) is moot — there is no such block in `narrate_system.j2`. The directives are enforced via `narrate_user.j2`'s `**Narration Directive:** Pressure/Overwhelm` labels (lines 100–122). No change needed from prompt-hygiene for this step.

---

## Implementation — Phase 02: rules_user context

### Files to pull for context

- `ccya/prompts/rules_user.j2`
- `ccya/prompts/rules_system.j2`
- `ccya/engine/rules.py` — `_rules_messages()` function (lines 18–45) and `_call_rules()` function (lines 48–115)
- `ccya/engine/turn.py` — `_rules_messages()` call site at lines 303–308
- `docs/REPOMAP/engine.md` — to confirm where rules prompt context is built

### Detailed steps

#### Step 2.1 — Replace `## Last Turn Narrative` with `outcome_summary`

**File:** `ccya/prompts/rules_user.j2`

**What:** Replace lines 15–20 (`{%- if recent_turns %}## Last Turn Narrative...{% endif -%}`) with a single `last_outcome` line sourced from the previous turn's progress extractor result. If no prior outcome exists (turn 1), omit the section entirely.

**Why:** The full narrative text is expensive and mostly irrelevant to intent classification. What the rules engine actually needs from prior context is: *what happened* (the outcome), not the full prose. `outcome_summary` is 1–2 sentences and provides the same disambiguation signal (e.g., "You stabbed the guard" → next turn "I finish him" can now resolve "him" correctly) at a fraction of the token cost.

**Code Snippet**

```jinja2
## Player Character
**{{ pc.name or "Unnamed" }}** — {{ pc.tagline or pc.concept or "" }}

**Stats:** {% for k, v in (pc.stats or {}).items() %}{{ k }}={{ v }}{% if not loop.last %} {% endif %}{% endfor %}

**Conditions:** {% if pc.conditions %}{% for c in pc.conditions %}{{ c.label if c is mapping else c }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}

## scene
Location: {{ location.name or location.id or "Unknown" }}
{%- if present_npcs %}
## Present NPCs (in scene right now)
{% for n in present_npcs %}- {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor -%}
{% endif -%}
{%- if last_outcome %}
## Last Turn Outcome
{{ last_outcome }}
{% endif -%}
## Current Turn: {{ meta.turn | default('?') }}
=== PLAYER INPUT ===
{{ user_input }}
=== END PLAYER INPUT ===
```

**Validation:** Confirm `last_outcome` variable is passed to rules prompt context (see Step 2.2). On turn 1, section is absent. On turn 2+, section shows one sentence.

---

#### Step 2.2 — Pass `last_outcome` to rules prompt context

**File:** `ccya/engine/rules.py`

**What:** Add `last_outcome: str | None = None` to the `_rules_messages()` function signature (line 18) and include it in the template context dict (lines 33–40). Source it from the previous turn's `TurnResult.outcome_summary` if available, else `None`.

**Why:** The template now references `last_outcome` — it must be in context or Jinja will raise.

**Code Snippet for `_rules_messages` signature change (line 18):**

```python
def _rules_messages(
    env: Environment,
    state: dict[str, Any],
    user_input: str,
    *,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    present_npcs: list[dict[str, Any]] | None = None,
    last_outcome: str | None = None,
) -> list[dict[str, str]]:
```

**Code Snippet for template context change (lines 33–40):**

```python
    user_text = _render(
        env,
        "rules_user.j2",
        {
            "pc": pc,
            "location": location,
            "recent_turns": recent_turns or [],
            "user_input": user_input,
            "meta": {"turn": turn_no},
            "present_npcs": present_npcs or [],
            "last_outcome": last_outcome,
        },
    )
```

**File:** `ccya/engine/turn.py`

**What:** At the `_rules_messages()` call site (lines 303–308), pass `last_outcome` sourced from the previous turn's result. On turn 1, `prev_turn_result` is `None`, so `last_outcome` will be `None`.

**Code Snippet for turn.py call site (around lines 303–308):**

```python
        # Get last turn's outcome_summary for rules context
        _prev_outcome = ""
        if turn_no > 1:
            _prev_events = load_recent_events(save_dir, 1)
            if _prev_events:
                _prev_outcome = _prev_events[0].get("rules", {}).get("outcome_summary", "")

        _present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])
        rules_messages = _rules_messages(
            env, state, user_input,
            recent_turns=recent_turns[-1:],
            turn_no=turn_no,
            present_npcs=_present_npcs,
            last_outcome=_prev_outcome if _prev_outcome else None,
        )
```

**Validation:** `make check` passes (type check). On T1 `turn_no == 1` — confirm `last_outcome` is `None` and template omits the section. On T2+, confirm the previous turn's `outcome_summary` appears.

---

#### Step 2.3 — Add assistant-turn stub to rules call

**File:** `ccya/engine/rules.py` (the `_call_rules()` function, lines 48–115)

**What:** Append a single assistant-role message `{"role": "assistant", "content": "{"}` to the messages list before the LLM call for the rules stream only.

**Why:** The rules call emits pure JSON. An assistant stub primes the model to complete the object directly, eliminating any risk of preamble prose. This is safe for this stream because the output schema is rigid and small — unlike narrate or extract streams where you want the model to reason freely before committing to output.

**Code Snippet**

```python
async def _call_rules(
    messages: list[dict[str, Any]],
    config: EngineConfig,
    trace_id: str,
) -> tuple[IntentEnvelope, dict[str, int], str, str]:
    _no_intent = IntentEnvelope(
        intent="",
        intent_verb="act",
        check=RulesCheck(required=False),
    )
    _no_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    parse_error = ""
    for attempt in range(1 + config.max_rules_retries):
        try:
            # Prime JSON completion with assistant stub
            if attempt == 0:
                messages = messages + [{"role": "assistant", "content": "{"}]
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"rules_request_attempt_{attempt}",
                    messages=messages,
                    max_chars=config.log_llm_io_max_chars,
                )
            messages = apply_thinking(messages, False)
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                temperature=config.rules_temperature,
                timeout=float(config.request_timeout_s),
            )
            raw = result.get("response", "") if isinstance(result, dict) else ""
            usage = result.get("usage", {}) if isinstance(result, dict) else _no_usage
            if config.log_llm_io:
                _log_llm_io(
                    trace_id=trace_id,
                    phase=f"rules_response_attempt_{attempt}",
                    response=raw,
                    max_chars=config.log_llm_io_max_chars,
                )
            cleaned = strip_thinking(raw)
            # Prepend the brace back before parsing
            cleaned = "{" + cleaned
            j = _find_json(cleaned)
            if j is None:
                raise ValueError("No JSON found in rules response")
            return IntentEnvelope(**j), {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }, raw, ""
        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "rules parse failed (attempt %d/%d): %s",
                attempt + 1,
                1 + config.max_rules_retries,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_rules_retries:
                fb = (
                    f"Your previous output failed to parse: {parse_error[:200]}. "
                    "Re-emit the IntentEnvelope JSON only. No prose."
                )
                messages.append({"role": "user", "content": fb})

    _log.warning(
        "rules call failed after all attempts — defaulting to no-roll",
        extra={"trace_id": trace_id},
    )
    return _no_intent, _no_usage, "", parse_error
```

**Validation:** Parse result as JSON. Confirm no preamble. Confirm existing JSON parse logic handles the prepended `{` correctly (`_find_json` extracts the JSON object from text, prepending `{` ensures the model's output starts with a brace). Run `make test` — existing rules parse tests must pass.

### Tests to write or update

- `tests/test_engine_pipeline.py` or equivalent: add a test asserting that when a prior `outcome_summary` is available, the rules user prompt contains `## Last Turn Outcome`. Assert it is absent on turn 1.
- Add a test asserting the assistant stub is present in the messages list for the rules LLM call (mock the LLM client, inspect call args).

### REPOMAP and architecture updates

- `docs/REPOMAP/engine.md`: note that `_rules_messages()` now accepts `last_outcome: str | None = None` parameter, and `rules_user.j2` now accepts `last_outcome` (optional string) in its context, sourced from previous `TurnResult.outcome_summary`.
- `docs/REPOMAP/prompts.md` if it exists: update rules_user context variables.

### Risks

1. Assistant stub + `{` prepend: some LLM APIs reject assistant turns that don't end with a complete token boundary. Test with the actual model being used. Mitigation: if rejected, remove the stub — it's a nice-to-have, not load-bearing.
2. `outcome_summary` field: confirmed to exist on `TurnResult` (`models.py:498`) and populated by `_run_extraction_pipeline` via `progress_result.outcome_summary` (`extraction.py:737`). If it's sometimes empty string vs `None`, guard the template with `{% if last_outcome %}` (already done in the snippet above).
3. Turn 1 edge case: `turn_no == 1` on the first turn. The guard `if turn_no > 1` in turn.py ensures `last_outcome` is `None` on T1.

---

## Implementation — Phase 03: extract_progress user cleanup

### Files to pull for context

- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/extract_progress_system.j2`

### Detailed steps

#### Step 3.1 — Remove behavioral rule restatement from `## gm_beat` section in user prompt

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Remove the instruction sentence at line 68 that appears under `## gm_beat`:

```
If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).
```

Replace the header with a minimal label that just signals the section exists for context:

**Code Snippet**

```jinja2
## gm_beat
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires at turn: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif -%}
```

**Why:** The full disposition decision tree (`consume` / `carry` / `replace`) and the beat behavior rules are already stated in `extract_progress_system.j2` under `beat_disposition` (lines 78–87). Restating them in the user prompt adds tokens and creates a potential conflict surface if the two ever drift.

**Validation:** Diff confirms only the instruction text is removed. The `pending_beat` data block is preserved. Run an eval turn where a beat should be carried — confirm `beat_disposition: "carry"` is still emitted correctly by the model.

---

#### Step 3.2 — Remove behavioral rule restatement from `## scene_pressure_add` section in user prompt

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Remove lines 85–87 (the `## scene_pressure_add` instruction block):

```
## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
```

**Code Snippet**

```jinja2
{% if quest_ages -%}
## quest_ages
...
```

**Why:** This is a restatement of system-level rules in the user prompt. It adds ~60 tokens per call with no signal the system prompt doesn't already provide. Unlike the `pending_beat` section, there's no per-turn data here — it's pure instruction. The full rules are in `extract_progress_system.j2` under `scene_pressure_add` (line 89).

**Validation:** Run an eval turn where a new pressure should be generated from a failed roll. Confirm `scene_pressure_add` is still emitted correctly. If not, the rule restatement was doing load-bearing work — restore it and note in Ambiguities.

### Tests to write or update

No new tests required. Existing eval scenario `pressure_lifecycle.py` covers scene pressure add/remove behavior and will catch regressions.

### REPOMAP and architecture updates

None — prompt text changes only.

### Risks

1. `## scene_pressure_add` removal: the instruction block may have been reinforcing system rules that the model was under-weighting at the user-turn boundary. If pressure generation degrades in eval, restore the block. This is the highest-risk change in Phase 03.
2. `## gm_beat` instruction removal: same risk. Beat disposition logic is nuanced (`carry` vs `replace` vs `consume`). If eval shows beat disposition errors increase, restore the abbreviated instruction. Mitigation: run `make eval` with `full_cycle` scenario after this phase before merging.

---

## Ambiguities requiring resolution before execution

1. **Step 2.2 — rules context builder location.** Confirmed: `_rules_messages()` is in `ccya/engine/rules.py` (lines 18–45), called from `ccya/engine/turn.py` at lines 303–308. The executor must pass `last_outcome` through both the function signature and the call site.
2. **Step 2.3 — assistant stub API compatibility.** Does the current `llm_client.chat()` call for the rules stream use a model/provider that accepts assistant-prefill? Options: A) Yes — implement stub as described. B) No or unknown — skip Step 2.3 and note as a follow-up. Do not implement if untested.
3. **Step 1.1 — SUPERSEDED by wire-scenario plan.** The `{% if world_factions or world_locations %}` block referenced in this ambiguity does not exist in `narrate_system.j2` — it only exists in `narrate_user.j2`. The wire-scenario plan wires the data through so this block becomes functional. No narration directives removal is needed from the system prompt. The directive labels (Breathe, Overwhelm, Pressure, etc.) are enforced via `narrate_user.j2`'s `**Narration Directive:** Pressure/Overwhelm` labels (lines 100–122). This ambiguity is resolved — no action needed.

