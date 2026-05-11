# Eval Remediation — Extraction Quality & Compaction Trigger

## Status
`open`

## Part of
Eval remediation cycle (May 2026)

## Dependencies
- Completed: `eval-remediation/01-extractor-grounding-and-compactor-fix.md` (recent_events overhaul, quest dedup, compactor fix)
- Completed: `eval-remediation2/eval-result-remediation.md` (currency mapping, auto-checker NPC suppression)
- Completed: `eval-13-turn-expansion.md` (13-turn scenario with dual compaction)
- Open: `eval-rubric-architecture-update.md` — coordinate rubric updates (this plan adds extraction-quality criteria; that plan covers structural reorganization and new storytelling criteria)

## Conflicts and overlap
- **Rubric updates**: This plan adds extraction-quality criteria (inventory amount accuracy, quest dedup, ambient NPC over-extraction) to the rubric. The `eval-rubric-architecture-update.md` plan covers structural reorganization and new storytelling criteria. Both plans modify `evals/rubrics/default.md`. Recommendation: execute this plan first (it adds concrete criteria), then the rubric-architecture plan (it restructures and adds storytelling criteria). The extraction-quality criteria should be added to Section 3 (Mechanical Design Critique) under each pipeline's Issues subsection.
- **Compaction trigger**: The compaction trigger mismatch is a logging artifact, not a compaction logic bug. The compactor code correctly fires only at `compact_every` intervals. The trace signals showing compaction on non-multiples of 6 come from the phase emission in `turn.py` which fires before the compactor checks its trigger. This plan fixes the misleading phase emission.
- **Currency mapping follow-up**: TODO item `Currency mapping failure (follow-up)` is a separate issue (LLM still emits `iron_coins`). This plan's state extractor prompt improvements address the root cause (amount parsing) which should also help currency mapping.

## Objective
Fix four extraction-quality issues surfaced by the May 10 eval (13-turn full_cycle run): (1) compaction phase logging fires on every turn creating false trace signals, (2) state extractor fails to parse explicit amounts from narration (Turn 6: "drop 200 credits" → amount:50), (3) progress extractor re-emits completed quest objectives (Turn 4), (4) scene extractor forced to emit ambient NPCs by a hard rule (Turns 3, 8), and (5) auto-checker false positives on bolded inventory items. Also add extraction-quality criteria to the rubric so future evals catch these issues earlier.

## Non-goals
- Fixing the compactor's LLM prompt (the compactor fires correctly at T6/T12 and produces bullets; the issue is phase logging on non-multiples).
- Fixing the narrator's repetitive NPC reactions (Turns 5, 6) — this is a narration quality issue, not an extraction issue.
- Fixing the rules prompt's over-rolling of trivial actions (Turns 9, 13) — this is a rules classification issue, not an extraction issue.
- Fixing the generic beat instructions (Turns 5, 9) — this is a progress extractor quality issue that would require a larger prompt redesign.
- Adding new Pydantic models or state schema changes.
- Modifying the engine turn pipeline code (turn.py, extraction.py) — all fixes are prompt-only or auto-checker-only.

## Affected files

| File | Change type | Summary |
|---|---|---|
| `ccya/engine/compactor.py` | modify | Move compact phase emission to after compaction decision; only emit compact_start/compact_done when compaction actually runs |
| `ccya/prompts/extract_state_system.j2` | modify | Strengthen amount parsing rules; add explicit spending-action rule |
| `ccya/prompts/extract_progress_system.j2` | modify | Add completed-objective dedup rule |
| `ccya/prompts/extract_scene_system.j2` | modify | Replace "always emit NPC" with "emit ambient only when no named NPCs present" |
| `ccya/eval/universal_asserts.py` | modify | Improve `_extract_candidate_names` to filter more inventory/location terms |
| `evals/rubrics/default.md` | modify | Add extraction-quality criteria to Mechanical Design Critique section |
| `docs/REPOMAP/engine.md` | update | Note compactor phase emission change |
| `docs/REPOMAP/prompts.md` | update | Note prompt changes |
| `docs/REPOMAP/eval.md` | update | Note auto-checker improvement |
| `docs/plans/TODO.md` | update | Add new items, mark completed |

## Firm decisions

1. **All extraction fixes are prompt-only.** No engine code changes in extraction.py, turn.py, or state.py. The LLM just needs better instructions.
2. **Compaction trigger fix is a logging fix.** The compactor logic is correct. The fix is in turn.py's phase emission — only emit compact_start/compact_done when compaction actually runs.
3. **Auto-checker improvement is conservative.** We expand the inventory name filter in `_extract_candidate_names` but keep the existing heuristic structure. No changes to the assertion logic.
4. **Rubric additions go under Mechanical Design Critique.** New extraction-quality criteria are added to the pipeline-specific Issues subsections, not as new top-level sections.
5. **No new config keys.** All fixes use existing config. No new EngineConfig fields.

---

## Implementation — Phase 1: Compaction Phase Logging Fix

### Context files to load
- `ccya/engine/compactor.py` — `maybe_compact()` function
- `ccya/engine/turn.py` — `run_turn()` function, lines 767-774 (compaction section)

### Overview
The compaction phase signals (`compact_start`, `compact_done`) are emitted in `turn.py` before `maybe_compact()` is called. Since `maybe_compact()` returns early on non-trigger turns, the phase signals fire on every turn, creating false trace signals. This phase moves the phase emission inside the compactor so it only fires when compaction actually runs.

### Detailed steps

#### Step 1.1 — Move phase emission into compactor

**File:** `ccya/engine/compactor.py`

**What:** Add phase emission to `maybe_compact()` at the start (before the early return) and at the end (after successful compaction). Remove phase emission from `turn.py`.

**Why:** The phase signals should only appear in traces when compaction actually occurs. Currently they appear on every turn because `turn.py` emits them before the compactor checks its trigger.

**Code Snippet**

```python
# In ccya/engine/compactor.py, modify maybe_compact():

async def maybe_compact(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
    on_phase: Any | None = None,
) -> dict[str, Any]:
    """Run compaction if current turn triggers it.

    Trigger: current_turn % compact_every == 0.
    Compacts turns [last_compacted_turn+1 .. retain_from-1].
    retain_from = max(1, current_turn - window_turns + 1).
    Sets last_compacted_turn = compact_end (NOT current_turn).

    Args:
        on_phase: Optional callback(phase: str, **kwargs) for phase emission.
                  If None, no phase signals are emitted.
    """
    if config.compact_every <= 0:
        return state

    current_turn = int((state.get("meta") or {}).get("turn", 0) or 0)
    if current_turn == 0:
        return state

    if current_turn % config.compact_every != 0:
        return state

    # Emit compact_start phase signal (only reached when trigger fires)
    if on_phase is not None:
        on_phase("compact_start", expected_ms=0)

    last_compacted_turn = int((state.get("meta") or {}).get("last_compacted_turn", 0) or 0)
    retain_from = max(1, current_turn - config.window_turns + 1)
    compact_end = retain_from - 1
    compact_start = last_compacted_turn + 1

    if compact_start > compact_end:
        _log.info(
            "compactor: nothing to compact at turn %d (compact_start=%d > compact_end=%d)",
            current_turn, compact_start, compact_end,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
        if on_phase is not None:
            on_phase("compact_done", ms=0)
        return state

    _log.info(
        "compactor: compacting turns %d–%d at turn %d (window=%d, compact_every=%d)",
        compact_start, compact_end, current_turn, config.window_turns, config.compact_every,
        extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
    )

    # ... [existing LLM call and parsing code unchanged] ...

    t_compact_start = asyncio.get_running_loop().time()

    # ... [existing compaction logic: bullets, sanitization, write] ...

    state.setdefault("meta", {})["last_compacted_turn"] = compact_end

    compact_ms = (asyncio.get_running_loop().time() - t_compact_start) * 1000
    if on_phase is not None:
        on_phase("compact_done", ms=round(compact_ms, 1))

    return state
```

**File:** `ccya/engine/turn.py`

**What:** Modify the compaction section in `run_turn()` to pass a phase callback to `maybe_compact()` and remove the standalone phase emissions.

**Why:** The phase signals are now emitted by the compactor itself, only when compaction actually runs.

**Code Snippet**

```python
# In ccya/engine/turn.py, replace the compaction section (around lines 767-774):

# === Compaction (after persist, before yield complete) ===
if config.compact_every > 0:
    t_compact = asyncio.get_running_loop().time()
    state = await maybe_compact(
        save_dir, state, config,
        on_phase=lambda phase, **kw: asyncio.ensure_future(
            _emit_phase(phase, **kw)
        ),
    )
    save_state(save_dir, state)
    compact_ms = (asyncio.get_running_loop().time() - t_compact) * 1000
    # compact_done phase is emitted by maybe_compact if compaction ran
    # If compaction didn't run (early return), no phase signals emitted
```

Wait — the above approach with `asyncio.ensure_future` is awkward. Let me use a simpler approach: emit phases synchronously from the compactor and have the caller yield them.

Actually, the cleanest approach is to have `maybe_compact()` return a flag indicating whether compaction ran, and let `turn.py` emit phases based on that flag.

**Revised Code Snippet**

```python
# In ccya/engine/compactor.py, modify maybe_compact() return value:

async def maybe_compact(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
) -> tuple[dict[str, Any], bool]:
    """Run compaction if current turn triggers it.

    Returns:
        (state, compaction_ran) — compaction_ran is True only when
        compaction actually produced bullets or sanitization.
    """
    if config.compact_every <= 0:
        return state, False

    current_turn = int((state.get("meta") or {}).get("turn", 0) or 0)
    if current_turn == 0:
        return state, False

    if current_turn % config.compact_every != 0:
        return state, False

    last_compacted_turn = int((state.get("meta") or {}).get("last_compacted_turn", 0) or 0)
    retain_from = max(1, current_turn - config.window_turns + 1)
    compact_end = retain_from - 1
    compact_start = last_compacted_turn + 1

    if compact_start > compact_end:
        _log.info(
            "compactor: nothing to compact at turn %d (compact_start=%d > compact_end=%d)",
            current_turn, compact_start, compact_end,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
        return state, False

    _log.info(
        "compactor: compacting turns %d–%d at turn %d (window=%d, compact_every=%d)",
        compact_start, compact_end, current_turn, config.window_turns, config.compact_every,
        extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
    )

    turns = _extract_turns_for_compact(save_dir, compact_start, compact_end)
    if not turns:
        return state, False

    env = state.get("_jinja_env")
    if env is None:
        from ccya.engine.config import _build_jinja_env

        template_dir = str(Path(__file__).parent.parent / "prompts")
        env = _build_jinja_env(template_dir)

    messages = _build_compact_messages(env, state, turns)

    try:
        resp = await llm_chat(
            config.host,
            config.model,
            messages,
            temperature=config.compact_temperature,
            timeout=float(config.request_timeout_s),
        )
        response_text = resp.get("response", "")
    except Exception as exc:
        _log.warning("compactor: LLM call failed, skipping: %s", exc)
        return state, False

    bullets_text, sanitization = _parse_compact_response(response_text)

    if not bullets_text.strip():
        _log.warning(
            "compactor: LLM returned empty bullets at turn %d, skipping",
            current_turn,
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
        return state, False

    new_bullets = [b.strip() for b in bullets_text.splitlines() if b.strip()]
    state.setdefault("meta", {}).setdefault("prior_history", []).extend(new_bullets)

    _write_compacted_block(save_dir, bullets_text, compact_start, compact_end)

    recent_events_count = len(state.get("scene", {}).get("recent_events") or [])

    compaction_ran = True

    if sanitization is not None:
        _apply_sanitization(state, sanitization)

        if sanitization.recent_events_compact:
            scene = state.setdefault("scene", {})
            scene["recent_events"] = [
                {
                    "id": e.id,
                    "text": e.text,
                    "turn": e.turn or current_turn,
                }
                for e in sanitization.recent_events_compact
            ]
            _log.info(
                "compactor: compacted %d → %d recent_events",
                recent_events_count,
                len(sanitization.recent_events_compact),
                extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
            )

    state.setdefault("meta", {})["last_compacted_turn"] = compact_end

    return state, compaction_ran
```

**File:** `ccya/engine/turn.py`

**What:** Update the compaction section to use the new return value and emit phases only when compaction ran.

**Code Snippet**

```python
# In ccya/engine/turn.py, replace the compaction section (around lines 767-774):

# === Compaction (after persist, before yield complete) ===
if config.compact_every > 0:
    t_compact = asyncio.get_running_loop().time()
    state, compaction_ran = await maybe_compact(save_dir, state, config)
    if compaction_ran:
        yield ("phase", {"phase": "compact_start", "expected_ms": 0})
        yield ("phase", {"phase": "compact_done", "ms": round(
            (asyncio.get_running_loop().time() - t_compact) * 1000, 1
        )})
    save_state(save_dir, state)
```

**Validation:** 
- Run `make check` to verify type checking passes.
- Run `make test` to verify existing tests pass (they may need updating for the new return type).
- Verify that in a test run, compact_start/compact_done phases only appear at turns that are multiples of `compact_every`.

### Tests to write or update
- `tests/test_engine_pipeline.py` — Add a test that verifies `maybe_compact()` returns `(state, False)` on non-trigger turns and `(state, True)` on trigger turns.
- Update any existing tests that call `maybe_compact()` to handle the new 2-tuple return value.

### REPOMAP updates required
- `docs/REPOMAP/engine.md` — Update `maybe_compact()` signature: returns `tuple[dict, bool]` (state, compaction_ran) instead of just `dict`.

### Risks
1. **Breaking existing callers:** `maybe_compact()` is called from `run_turn()` and `run_turn_retry()`. Both need to be updated to handle the 2-tuple return. This is a small, contained change.
2. **Test failures:** Existing tests that mock `maybe_compact()` need to return a 2-tuple. Update test mocks.

---

## Implementation — Phase 2: State Extractor — Amount Parsing & Spending Actions

### Context files to load
- `ccya/prompts/extract_state_system.j2` — State extractor system prompt
- `ccya/prompts/extract_state_user.j2` — State extractor user prompt

### Overview
The state extractor fails to parse explicit amounts from narration (Turn 6: "drop 200 credits" → amount:50) and misses spending actions (Turn 13: dock boy payment not extracted). This phase strengthens the amount parsing rules and adds an explicit spending-action rule.

### Detailed steps

#### Step 2.1 — Strengthen amount parsing in state extractor system prompt

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Replace the existing quantity paragraph (lines 22-25) with stronger, more explicit rules.

**Why:** The current rules say "Quantities are exact" but don't emphasize that explicit numbers in narration override all inference. The LLM needs a clear hierarchy: explicit number > inference > omit.

**Code Snippet**

```jinja2
## Quantities are exact.

**Priority 1 — Explicit numbers.** If narration states a specific number ("drop 200 credits", "used three bandages", "gave him 50 gold"), emit that exact number. The number in the narration is authoritative — never substitute a different value.

**Priority 2 — Inference.** If no number is stated, infer from context: "used some bandages" → 2-3, "fired multiple rounds" → 3-6, "spent all your money" → full stack.

**Priority 3 — Omit for full-stack.** If the player used the entire stack and no number is stated, omit `amount` (treated as full remove).

Read the current stack from the user prompt before emitting `amount`. Never emit `amount` greater than the current stack — if the player used the entire stack, omit `amount` (treated as full remove).
```

#### Step 2.2 — Add spending-action rule

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Add a new rule in the `inventory_remove` field description emphasizing that spending/giving actions must always produce an `inventory_remove`, even with vague amounts.

**Why:** Turn 13's dock boy payment was missed entirely. The current rule says "If the narration describes the player parting with an item... emit the remove" but the LLM still missed it. Need to make this more prominent.

**Code Snippet**

```jinja2
`inventory_remove`: items lost, used, destroyed, or spent. Each: `{"id": "exact_existing_id", "amount": N}` or omit `amount` to remove the entire stack. Use the exact id from the inventory list shown in the user prompt. Never emit add and remove for the same id in one turn.

**Spending/giving rule:** If narration describes the player spending, giving away, or parting with currency or items (e.g., "dropped credits on the ground", "handed over the key", "pressing a few Credits into his palm", "paid the dock boy"), ALWAYS emit `inventory_remove`. Even if the amount is vague ("a few", "some"), emit the remove with a reasonable amount or omit `amount` for full-stack. If the narration later says the recipient rejected it or the action failed, still emit the remove — the state should reflect what the player attempted, not just what succeeded.
```

**Validation:**
- Read the updated prompt and verify the hierarchy is clear (explicit > inference > omit).
- Verify the spending rule is prominent and uses concrete examples.
- Run a quick mental check: "drop 200 credits" → Priority 1 → amount: 200. "pressing a few Credits into his palm" → spending rule → inventory_remove with vague amount or omit.

### Tests to write or update
- No new tests needed for prompt-only changes. Tier 1 tests with FakeLLM would need updated mock responses to test the new prompt behavior, but this is low priority for a prompt-only fix.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md` — Note: `extract_state_system.j2` strengthened quantity parsing rules with explicit priority hierarchy; added spending/giving rule to `inventory_remove` field description.

### Risks
1. **Prompt length increase:** The new rules add ~15 lines to the system prompt. This is acceptable — the state extractor prompt is already well-structured and the additions are focused.
2. **LLM still fails:** If the LLM continues to miss amounts, the fix may need to be in the user prompt (showing the narration with highlighted numbers) rather than the system prompt. This is a follow-up concern.

---

## Implementation — Phase 3: Progress Extractor — Quest Deduplication

### Context files to load
- `ccya/prompts/extract_progress_system.j2` — Progress extractor system prompt

### Overview
The progress extractor re-emits completed quest objectives (Turn 4: `deliver_the_ledger` objective 1 marked done again). This phase adds a completed-objective dedup rule that explicitly forbids re-emitting objectives already marked done.

### Detailed steps

#### Step 3.1 — Add completed-objective dedup rule

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Add a new rule after the existing quest deduplication section (after line 34) that specifically addresses completed-objective dedup.

**Why:** The existing quest dedup rule prevents creating new quest IDs for existing quests, but doesn't prevent re-emitting objectives that are already done. The LLM needs an explicit rule: "if an objective is already done, do not re-emit it."

**Code Snippet**

```jinja2
- **Completed-objective dedup (MANDATORY):** Before emitting any `quest_updates`, check the `## active_quests` list. If an objective is already marked `done: true` in the existing quest, DO NOT re-emit it in your `quest_updates`. Only emit objectives that changed state this turn (newly done, newly failed, or newly added). Re-emitting already-done objectives is a waste of tokens and causes redundant state updates.

- **NEVER create a new quest ID when an existing active quest covers the same objective.** Examples of what NOT to do:
  - Do NOT create `deliver_ledger_to_inn` when `deliver_the_ledger` already exists — update `deliver_the_ledger` instead.
  - Do NOT create `caron_debt` when `settle_the_debt` already exists — update `settle_the_debt` instead.
  - Do NOT create `find_the_ledger` when `deliver_the_ledger` already exists — update `deliver_the_ledger` instead.
```

**Validation:**
- Read the updated prompt and verify the completed-objective dedup rule is clear and prominent.
- Verify the rule is placed before the quest creation examples so it's read first.

### Tests to write or update
- No new tests needed for prompt-only changes.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md` — Note: `extract_progress_system.j2` added completed-objective dedup rule.

### Risks
1. **Minimal risk:** This is a single rule addition to an existing prompt section. Low chance of unintended side effects.

---

## Implementation — Phase 4: Scene Extractor — Ambient NPC Rule

### Context files to load
- `ccya/prompts/extract_scene_system.j2` — Scene extractor system prompt

### Overview
The scene extractor is forced to emit ambient NPCs by a hard rule ("Always emit at least one NPC entry"). This causes compendium bloat with bystanders, inn_patrons, etc. (Turns 3, 8). This phase replaces the hard rule with a conditional one.

### Detailed steps

#### Step 4.1 — Replace "always emit NPC" with conditional rule

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the "Always emit at least one NPC entry" constraint (line 64) with a conditional rule that only emits ambient NPCs when no named NPCs are present.

**Why:** The hard rule forces ambient NPC entries even when named NPCs are already present, causing compendium bloat. The conditional rule ensures ambient NPCs are only emitted when the scene genuinely has no named characters.

**Code Snippet**

```jinja2
## Constraints

- **NPC emission:** Only emit `npc_add` for named characters or entities that interact with the player or quest. If no named NPCs are present in the scene, emit ambient presence (e.g., "crowd", "bystanders", "inn_patrons") with a generic ID. Do NOT emit ambient presence when named NPCs are already present — the named NPCs are sufficient.
- **Never invent location IDs.** Only use location IDs from the `## Current Location` section or well-known locations from the compendium.
- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.
- **Limit `npc_add` to at most 3 per turn.** Only add NPCs that are meaningfully present or interact with the player. Background extras go in ambient presence.
```

**Validation:**
- Read the updated prompt and verify the conditional rule is clear.
- Verify the rule prevents ambient NPC emission when named NPCs are present.

### Tests to write or update
- No new tests needed for prompt-only changes.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md` — Note: `extract_scene_system.j2` replaced "always emit NPC" with conditional ambient NPC rule.

### Risks
1. **Empty NPC list:** If the scene has no named NPCs and the conditional rule prevents ambient emission, the `npc_add` list could be empty. This is acceptable — an empty list is valid JSON and the engine handles it. The previous behavior (forcing ambient NPCs) was worse (compendium bloat).

---

## Implementation — Phase 5: Auto-Checker — Inventory Name Filtering

### Context files to load
- `ccya/eval/universal_asserts.py` — `_extract_candidate_names()` and `check_npc_mention_extracted()`

### Overview
The auto-checker flags bolded inventory items and location names as unsanctioned NPCs (Turns 1-11). The `_extract_candidate_names()` function already filters inventory names, but the filter is incomplete — it only matches exact lowercase names, not partial matches or compound terms. This phase improves the filtering.

### Detailed steps

#### Step 5.1 — Improve inventory name filtering in auto-checker

**File:** `ccya/eval/universal_asserts.py`

**What:** Enhance `_extract_candidate_names()` to filter more inventory and location terms. The current filter does exact lowercase matching (`token.lower() in inv_lower`), but inventory names like "Leather-bound ledger" won't match the token "Leather" because "leather-bound ledger" != "leather". We need partial matching.

**Why:** The auto-checker flags "Leather", "Crossed", "Marrow", "Credit", "Passage" as missing NPC names, but these are parts of bolded inventory/location terms like "**Leather-bound ledger**", "**Crossed Keys Inn**", "**Marrow's Crossing**", "**Credits**".

**Code Snippet**

```python
def _extract_candidate_names(
    narration: str,
    pc_name: str,
    inventory_names: set[str] | None = None,
    location_names: set[str] | None = None,
) -> set[str]:
    """Extract capitalized tokens that are candidates for NPC names.

    Excludes the PC name (case-insensitive), sentence-initial words,
    short tokens (<=4 chars, likely descriptors), common descriptor words,
    inventory item names (partial match), and location names (partial match).

    Note: sentence-starters heuristic will miss NPC names that happen to
    appear at the start of a sentence. This is an accepted tradeoff to
    reduce false positives — the assert is for eval harness hygiene, not
    production logic.
    """
    sentences = re.split(r'(?<=[.!?])\s+', narration)
    sentence_starters: set[str] = set()
    for s in sentences:
        first = s.split()
        if first:
            sentence_starters.add(first[0].strip("\"'"))

    # Common descriptors and titles that are not NPC names
    descriptor_stop: set[str] = {
        "Scarred", "Tough", "Hooded", "Burly", "Young", "Old", "Tall",
        "Short", "Fat", "Thin", "Lean", "Dark", "Light", "Red", "Blue",
        "Green", "Gold", "Silver", "Iron", "Brass", "Wooden", "Stone",
        "Big", "Small", "Large", "Little", "High", "Low", "Fast", "Slow",
        "Good", "Bad", "New", "Last", "First", "Next", "Other", "Same",
        "Each", "Every", "Both", "All", "Some", "Any", "Many", "Few",
    }

    inv_lower: set[str] = set()
    if inventory_names:
        inv_lower = {n.lower() for n in inventory_names}

    loc_lower: set[str] = set()
    if location_names:
        loc_lower = {n.lower() for n in location_names}

    candidates: set[str] = set()
    for token in re.findall(r'\b[A-Z][a-z]{2,}\b', narration):
        if token.lower() == pc_name.lower():
            continue
        if token in sentence_starters:
            continue
        if token in descriptor_stop:
            continue
        if len(token) <= 4:
            continue
        # Partial match against inventory names (e.g., "Leather" matches
        # "Leather-bound ledger")
        if inv_lower and any(token.lower() in inv_name for inv_name in inv_lower):
            continue
        # Partial match against location names
        if loc_lower and any(token.lower() in loc_name for loc_name in loc_lower):
            continue
        candidates.add(token)
    return candidates
```

**File:** `ccya/eval/universal_asserts.py`

**What:** Update `check_npc_mention_extracted()` to pass location names to `_extract_candidate_names()`.

**Code Snippet**

```python
def check_npc_mention_extracted(event: dict[str, Any]) -> dict[str, Any]:
    """If narration mentions a name AND scope includes scene, scene extract should npc_add/update.

    Heuristic: extract candidate NPC names from narration via simple capitalization
    rule: tokens of length >= 3 that are Capitalized AND not the first token of a
    sentence AND not in a pronoun/article allow-list. If any candidate name does
    NOT appear in applied.npc_add[].name OR applied.npc_update[].name OR existing
    state_snapshot.scene.present_npcs[].name (case-insensitive), flag.

    This is intentionally conservative — we only flag when narration introduces a
    clearly-named character that the scene extractor missed.
    """
    narr = (event.get("narrate_prompt") or {}).get("output") or ""
    if not narr:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": "(no narration)",
            "scope": "universal",
        }
    applied = event.get("applied") or {}
    snap = event.get("state_snapshot") or {}

    pc_name = (snap.get("pc") or {}).get("name", "")

    known_names: set[str] = set()
    for npc in (applied.get("npc_add") or []) + (applied.get("npc_update") or []):
        if isinstance(npc, dict):
            n = npc.get("name") or npc.get("id") or ""
            if n:
                known_names.add(n.lower())
    for npc in (snap.get("scene") or {}).get("present_npcs") or []:
        if isinstance(npc, dict):
            n = npc.get("name") or npc.get("id") or ""
            if n:
                known_names.add(n.lower())
    for cid, c in ((snap.get("compendium") or {}).get("npcs") or {}).items():
        if isinstance(c, dict):
            n = c.get("name") or cid
            if n:
                known_names.add(n.lower())

    # Extract inventory item names for false positive filtering
    inventory_names: set[str] = set()
    for item in (snap.get("inventory") or []):
        if isinstance(item, dict):
            name = item.get("name", "")
            if name:
                inventory_names.add(name)

    # Extract location names for false positive filtering
    location_names: set[str] = set()
    loc = (snap.get("location") or {})
    if loc.get("name"):
        location_names.add(loc["name"])
    # Also check world locations if available
    for wl in (snap.get("world") or {}).get("locations") or []:
        if isinstance(wl, dict) and wl.get("name"):
            location_names.add(wl["name"])
        elif isinstance(wl, str):
            location_names.add(wl)

    candidates = _extract_candidate_names(narr, pc_name, inventory_names, location_names)
    # Filter common false positives: dialogue tags, common nouns.
    stop = {
        "You", "The", "A", "An", "His", "Her", "Their",
        "He", "She", "It", "I", "We", "They",
        "But", "And", "Or", "If", "When", "Then",
        "Now", "Here", "There", "This", "That",
        "These", "Those",
    }
    missing = [c for c in candidates if c not in stop and c.lower() not in known_names]
    if not missing:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": "no missing NPC names detected",
            "scope": "universal",
        }
    # Heuristic — could be locations, items, etc. Flag only if 1-3 missing (not 10+ which is noise).
    if len(missing) > 3:
        return {
            "assertion": "universal.npc_mention.extracted",
            "passed": True,
            "detail": f"{len(missing)} candidates skipped (likely locations/items, not NPCs)",
            "scope": "universal",
        }
    return {
        "assertion": "universal.npc_mention.extracted",
        "passed": False,
        "detail": f"narration mentions names not in npc_add/update or known: {missing}",
        "scope": "universal",
    }
```

**Validation:**
- Verify that "Leather" is filtered when inventory contains "Leather-bound ledger" (partial match: "leather" in "leather-bound ledger").
- Verify that "Crossed" is filtered when location contains "Crossed Keys Inn" (partial match: "crossed" in "crossed keys inn").
- Verify that "Marrow" is filtered when location contains "Marrow's Crossing" (partial match: "marrow" in "marrow's crossing").
- Run `make check` to verify type checking passes.
- Run `make test` to verify existing tests pass.

### Tests to write or update
- `tests/test_eval.py` — Add a test for `_extract_candidate_names()` that verifies partial matching against inventory and location names filters correctly.

### REPOMAP updates required
- `docs/REPOMAP/eval.md` — Note: `universal_asserts.py` improved `_extract_candidate_names()` with partial matching against inventory and location names; `check_npc_mention_extracted()` now passes location names.

### Risks
1. **False negatives:** Partial matching could filter out legitimate NPC name tokens. For example, if an NPC named "Leather" exists, the filter would suppress it. Mitigation: the filter only applies to tokens that are part of inventory/location names, and the known_names check (which includes compendium NPCs) runs after the filter. If "Leather" is a known NPC, it won't be in the missing list regardless.
2. **Performance:** Partial matching adds O(n*m) complexity where n is the number of tokens and m is the number of inventory/location names. In practice, inventory has ~5-10 items and locations have ~1-3 names, so this is negligible.

---

## Implementation — Phase 6: Rubric — Extraction Quality Criteria

### Context files to load
- `evals/rubrics/default.md` — Current rubric
- `ccya/prompts/extract_state_system.j2` — For reference on what the state extractor should do
- `ccya/prompts/extract_progress_system.j2` — For reference on what the progress extractor should do
- `ccya/prompts/extract_scene_system.j2` — For reference on what the scene extractor should do

### Overview
Add extraction-quality criteria to the rubric's Mechanical Design Critique section. These criteria will help future evals catch inventory amount mismatches, quest deduplication failures, and ambient NPC over-extraction earlier.

### Detailed steps

#### Step 6.1 — Add extraction-quality subsections to pipeline critiques

**File:** `evals/rubrics/default.md`

**What:** Add new subsections under each pipeline's "Issues" area in the Mechanical Design Critique section. These are evaluation criteria for the judge to assess.

**Why:** The current rubric doesn't have specific criteria for extraction quality (amount accuracy, dedup, ambient NPC filtering). Adding these ensures future evals flag these issues.

**Code Snippet**

Under **Pipeline: extract_state** — add after "Issues":

```markdown
#### Extraction Quality
- **Amount accuracy:** When narration states an explicit number for inventory changes ("drop 200 credits", "used three bandages"), the state extractor must emit that exact number. Flag turns where the extracted amount differs from the stated amount. A mismatch scores 1-2 for this criterion.
- **Spending action extraction:** When narration describes the player spending, giving away, or parting with items/currency, the state extractor must emit `inventory_remove`. Flag turns where spending actions were narrated but no `inventory_remove` was extracted.
```

Under **Pipeline: extract_progress** — add after "Issues":

```markdown
#### Extraction Quality
- **Quest objective deduplication:** Before emitting `quest_updates`, the progress extractor must check `active_quests` and `recent_events`. If an objective is already marked `done: true`, it must NOT be re-emitted. Flag turns where already-done objectives were re-emitted. A dedup failure scores 1-2 for this criterion.
- **Quest completion timing:** The extractor must NOT emit `status: completed` for a quest unless all objectives are done. Let the engine handle auto-completion. Flag premature completion status emissions.
```

Under **Pipeline: extract_scene** — add after "Issues":

```markdown
#### Extraction Quality
- **Ambient NPC filtering:** The scene extractor should NOT emit `npc_add` for ambient presence (crowds, bystanders, inn_patrons) when named NPCs are already present in the scene. Ambient NPCs should only be emitted when no named characters are present. Flag turns where ambient NPCs were added alongside named NPCs. Over-extraction of ambient NPCs scores 1-2 for this criterion.
```

**Validation:**
- Read the updated rubric and verify the new criteria are clear and actionable.
- Verify the criteria are placed in the correct sections (under each pipeline's Issues area).
- Verify the criteria reference specific failure modes from the eval report.

### Tests to write or update
- No code tests needed. This is a rubric update.
- The next eval run will automatically use the updated criteria.

### REPOMAP updates required
- `docs/REPOMAP/eval.md` — Note: rubric updated with extraction-quality criteria for extract_state, extract_progress, and extract_scene pipelines.

### Risks
1. **Rubric length:** Adding criteria increases the rubric length. Mitigation: the criteria are concise (2-3 lines each) and fit within the existing pipeline structure.
2. **Judge model consistency:** Different judge models may interpret the new criteria differently. Mitigation: the criteria are framed as "flag if" rather than "must always", allowing judge discretion.

---

## Ambiguities requiring resolution before execution

1. **Compaction phase emission approach:** Phase 1 changes `maybe_compact()` to return a 2-tuple `(state, compaction_ran)`. This is the cleanest approach but requires updating all callers. Alternative: keep the single-return signature and add a separate `should_compact()` check in `turn.py`. Recommendation: use the 2-tuple approach (cleaner, more explicit).

2. **Auto-checker partial matching scope:** Phase 5 uses partial matching (`token.lower() in inv_name`) which could filter legitimate NPC names. Alternative: use word-boundary matching (`\b` regex) to only match whole words within inventory names. Recommendation: use partial matching for now (catches more false positives); word-boundary matching can be a follow-up if false negatives become an issue.

3. **Rubric criteria placement:** Phase 6 adds criteria under each pipeline's "Issues" area. Alternative: add a new top-level "Extraction Quality" section. Recommendation: use the existing pipeline structure (less disruptive, easier for judges to associate criteria with the right pipeline).

---

## TODO.md update

### Add to P3 — Inference Speed and Evaluation section (after existing items):

```markdown
- [ ] **Inventory amount parsing fix** — state extractor fails to parse explicit amounts from narration (Turn 6: "drop 200 credits" → amount:50); strengthen prompt with explicit priority hierarchy (explicit > inference > omit) — see `[eval-remediation-may10/02-extraction-quality.md](eval-remediation-may10/02-extraction-quality.md) Phase 2`
- [ ] **Quest objective deduplication fix** — progress extractor re-emits completed objectives (Turn 4); add completed-objective dedup rule to prompt — see `[eval-remediation-may10/02-extraction-quality.md](eval-remediation-may10/02-extraction-quality.md) Phase 3`
- [ ] **Scene extractor ambient NPC filtering** — scene extractor forced to emit ambient NPCs by hard rule (Turns 3, 8); replace "always emit NPC" with conditional rule — see `[eval-remediation-may10/02-extraction-quality.md](eval-remediation-may10/02-extraction-quality.md) Phase 4`
- [ ] **Auto-checker inventory/location name filtering** — auto-checker flags bolded inventory items and location names as unsanctioned NPCs; improve partial matching in `_extract_candidate_names` — see `[eval-remediation-may10/02-extraction-quality.md](eval-remediation-may10/02-extraction-quality.md) Phase 5`
- [ ] **Compaction phase logging fix** — compact_start/compact_done phases fire on every turn creating false trace signals; move phase emission into compactor — see `[eval-remediation-may10/02-extraction-quality.md](eval-remediation-may10/02-extraction-quality.md) Phase 1`
- [ ] **Rubric extraction-quality criteria** — add amount accuracy, quest dedup, and ambient NPC filtering criteria to rubric Mechanical Design Critique — see `[eval-remediation-may10/02-extraction-quality.md](eval-remediation-may10/02-extraction-quality.md) Phase 6`
```

### Mark as completed (items from existing TODO that this plan addresses):

The existing TODO items for "Compactor sanitization failure", "Narrator ignores player input", and "Currency mapping failure (follow-up)" are NOT addressed by this plan — they are separate issues tracked in `eval-remediation-may10/01-eval-remediation-may10.md`. This plan is a separate file (`02-extraction-quality.md`) for the extraction-quality issues.
