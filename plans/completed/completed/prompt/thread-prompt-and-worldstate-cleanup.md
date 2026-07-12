# Thread Prompt Tightening and World State Direct Write Removal

## Purpose

Tighten storyteller prompt guidance for thread management and NPC notes while removing direct world_state writes from the LLM pipeline, consolidating all durable state changes to flow exclusively through arc/thread resolution.

## Problem Statement

The storyteller LLM produces NPC notes that are too long (full sentences instead of quick situational cues), updates thread summaries on every change when they should be static plot-point anchors, generates choices without enough narrative substance or thread focus, and writes world_state facts directly — duplicating the data already flowing through thread promotion. This creates redundant state mutations and dilutes the signal that threads are supposed to carry.

## Constraints

- No significant increase in prompt input tokens for any change.
- Thread promotion via `promote_to_world_state` on arc_resolve/thread_resolve is the sole path for world state changes — must not be removed.
- Existing thread lifecycle mechanics (auto-delete scene threads on location change, TTL pruning) remain unchanged.
- Tests are temporarily disabled; skip test updates.

## Non-goals

- No new fields or models added.
- No changes to how `promote_to_world_state` works in turn.py:395.
- No restructuring of the 5-call pipeline stages.
- No changes to NPC compendium logic beyond notes length guidance.

## Solution

Update prompt files with tighter constraints on NPC notes (5–8 words max), thread summaries (static after creation, only change on fundamental shift), choice generation (thread/arc advancement primary, no meandering), and thread count targets (2 arc + 1 scene ideal). Remove `world_state_add` and `world_state_remove` from all models, extraction pipeline, delta builder, UI display code, and prompt schema — leaving promotion via `promote_to_world_state` as the only world state mutation path. Update architecture docs to reflect these changes.

## Firm decisions

1. NPC notes: hard limit of 5–8 words max in extract_scene_system.j2.
2. Thread summaries: DO NOT change after initial creation unless thread's fundamental nature has shifted — hardest prompt guidance first, keep update code path for now.
3. World state direct writes: full delete `world_state_add` and `world_state_remove` from models.py (both StateDelta and StorytellerResult), extraction.py merge block, delta_builder.py mutation logic, changes.py UI display, storytell_system.j2 prompt schema and guidance section. Promotion via `promote_to_world_state` stays untouched.
4. Thread count targets: target 2 arc + 1 scene thread (3 total), soft cap 3 arc + 2 scene (5 total). Differentiate scope explicitly in prompt.
5. Choice language: strengthened emphasis on narrative substance and thread advancement, no meandering options ("look at that", "talk to them"), structure maintained as one arc-thread / one NPC / one environmental / one freeform with at least 2 of 4 advancing threads/arcs.

## Risks, Ambiguities, and Blockers

- **Thread summary static guidance**: The prompt says "DO NOT change after initial creation" but the code path for updating summaries still exists. If LLM ignores it, we may need to remove the update capability entirely in a follow-up.
- **World state removal impact on evals**: Any eval scenarios that assert `world_state_add` presence will fail — those assertions need review and removal.
- **Thread count targets are soft guidance only**: The prompt enforces "Maximum 5 active threads" already; we're adding arc vs scene differentiation but the engine doesn't enforce scope-based caps at runtime.

## Status
`open`

## Phases

Three phases: (1) prompt updates across extract_scene_system.j2 and storytell_system.j2, (2) code removal of world_state direct writes from models/extraction/delta_builder/changes, (3) documentation updates to OVERVIEW.md, repomap.md, and step2c-storytell.md.

---

## Implementation — Phase 1: Prompt Updates

### Context files to load
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/storytell_system.j2`

### Detailed steps

#### Step 1.1 — Tighten NPC notes length in extract_scene_system.j2

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the notes guidance at line 41 (`"ONE SHORT SENTENCE about what this NPC is doing right now..."`) with a hard word-count limit. Update both the field definition and the examples section (lines 68–76) to enforce 5–8 words max.

Change:
```
"notes": "ONE SHORT SENTENCE about what this NPC is doing right now that matters — their current stance, action, or motivation as it relates to the last round of narration. Still flavor text; not plot-critical information."
```
To:
```
"notes": "5–8 words max describing the NPC's current stance or action in this scene. No clauses, no conjunctions. Not plot-critical — quick situational cue only."
```

Also update the incorrect notes example at line 73 to show a too-long version that exceeds 8 words (it already does). Add an explicit rule: **"Maximum 8 words. Count them."** after the examples section.

**Why:** NPC notes are averaging too many words, making state bloated and reducing signal-to-noise in UI display.

**Validation:** Read back extract_scene_system.j2 lines 41–76 to confirm changes. No code execution needed — prompt-only change.

#### Step 1.2 — Add thread summary static guidance to storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** In the `thread_update` section (line 30), after the existing guidance about when to emit `summary`, add:
```
DO NOT change a thread's `summary` after its initial creation unless the thread's fundamental nature has shifted. The summary represents a single plot point — it is static, not evolving. Progress entries are how we see things changing. Only update `progress`, never `summary`.
```

**Why:** Thread summaries should be stable anchors representing a single plot point. They change rarely (only on major revelations), while progress updates show actual state changes.

**Validation:** Read back storytell_system.j2 lines 29–31 to confirm the addition is placed correctly within the thread_update section.

#### Step 1.3 — Strengthen choice language in storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** Replace the entire Actions section (lines 88–98) with:
```markdown
## Actions

Emit exactly 4 choices, ~10 words each, active voice as if spoken by the PC. Never emit an empty array. Each choice must escalate, force a decision, or change things irreversibly. No meandering ("look at that", "talk to them"), no passive options (wait, observe), nothing generic enough for any protagonist in any setting.

Structure: one pursues the highest-urgency thread, one involves a named NPC present in the scene, one is an environmental action that changes things, one is freeform rooted in PC background. Span different postures: confront, negotiate, flee, exploit — not variations of the same approach. At least 2 of 4 must directly advance an arc goal or active thread.
```

**Why:** Choices need stronger emphasis on narrative substance and thread focus to prevent meandering options that don't move scenes forward. Retains "force a decision / change irreversibly" from existing prompt as it addresses the same problem more precisely than new language alone.

**Validation:** Read back storytell_system.j2 lines 88–96 after edit. Confirm exactly 3 paragraphs matching the agreed language.

#### Step 1.4 — Add thread count targets and scope differentiation to storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** In the Threads section (after line 32, which currently says "Maximum 5 active threads"), replace that sentence with:
```
Target: 2 arc threads + 1 scene thread at any time. Soft cap: 3 arc threads + 2 scene threads (5 total). Arc threads are tied explicitly to the campaign arc goal and persist across locations. Scene threads are localized, removed on location change, very short-term — if a thread would resolve after one scene, it belongs in `scene` scope or in the narration, not as an arc thread.
```

**Why:** Distinguish between arc-scoped (persistent, plot-driving) and scene-scoped (localized, ephemeral) threads with explicit count targets to prevent thread sprawl.

**Validation:** Read back storytell_system.j2 lines 32–34 after edit. Confirm both scope types are differentiated and counts match the agreed targets.

#### Step 1.5 — Remove direct world_state writes from storytell_system.j2 prompt

**File:** `ccya/prompts/storytell_system.j2`

**What:** Delete these three references:
- Lines 14–15 (JSON schema): `"world_state_remove": ["..."]` and `"world_state_add": [{"id": "...", "text": "...", "tier": "persistent"}]`
- Line 46 (`## World state` section): The entire `world_state_add:` guidance paragraph starting with "`world_state_add`: Durable facts still true 10 turns from now..."

**Why:** The LLM should no longer emit direct world state mutations. Keeping prompt instructions for a field that doesn't exist in the model would confuse the LLM and cause it to emit data that gets silently dropped at validation.

**Validation:** Read back storytell_system.j2 after edit. Confirm schema section has 13 keys (was 15) and no `## World state` heading remains. The thread promotion guidance on line 28 (`promote_to_world_state: true`) stays untouched.

---

## Implementation — Phase 2: Code Removal of World State Direct Writes

### Context files to load
- `ccya/models.py` (lines 258–290, 455–466)
- `ccya/engine/extraction.py` (lines 647–662)
- `ccya/state/delta_builder.py` (lines 308–329)
- `ccya/engine/changes.py` (lines 15–57 for _summarize_applied, lines 36–44 specifically)

### Detailed steps

#### Step 2.1 — Remove world_state fields from StorytellerResult in models.py

**File:** `ccya/models.py`

**What:** Delete these two lines:
```python
    world_state_add: list[WorldStateFact] = Field(default_factory=list)
    world_state_remove: list[str] = Field(default_factory=list)
```
from the `StorytellerResult` class (lines 464–465).

**Why:** The LLM should no longer emit direct world state mutations. All durable facts flow through thread promotion via `promote_to_world_state`.

**Validation:** No code execution needed. Confirm both lines removed from StorytellerResult and that the model validator at line 467 is unaffected (it only touches gm_beat).

#### Step 2.2 — Remove world_state fields from StateDelta in models.py

**File:** `ccya/models.py`

**What:** Delete these two lines:
```python
    world_state_add: list[WorldStateFact] = Field(default_factory=list)
    world_state_remove: list[str] = Field(default_factory=list)
```
from the `StateDelta` class (lines 288–289).

**Why:** StateDelta is the merged pipeline output. Without direct writes from storyteller, these fields have no source and serve no purpose in the delta.

**Validation:** Confirm both lines removed from StateDelta. No other changes needed — this model has no validators that reference world_state fields.

#### Step 2.3 — Remove world_state passing from extraction.py merge block

**File:** `ccya/engine/extraction.py`

**What:** Delete these two lines from the StateDelta construction at lines 660–661:
```python
        world_state_add=storytell_result.world_state_add or [],
        world_state_remove=storytell_result.world_state_remove or [],
```

**Why:** The source fields no longer exist on StorytellerResult. Removing these passes prevents build errors and cleans up the merge pipeline.

**Validation:** Read back extraction.py lines 647–662 after edit. Confirm StateDelta construction has exactly 13 keyword arguments (was 15). No code execution needed.

#### Step 2.4 — Remove world_state mutation logic from delta_builder.py

**File:** `ccya/state/delta_builder.py`

**What:** Delete the entire world state mutation block at lines 308–329:
```python
    # --- World state mutations (persistent tier only) ---
    ws_list: list[dict[str, Any]] = copy.deepcopy(state.setdefault("scene", {}).get("world_state") or [])

    for rem_id in delta.world_state_remove:
        ws_list = [f for f in ws_list if not (isinstance(f, dict) and f.get("id") == rem_id and f.get("tier") != "permanent")]

    for fact in delta.world_state_add:
        tier = fact.tier  # LLM should only emit "persistent"; permanent facts are seed-authored
        text = _strip_non_ascii(fact.text)
        existing = next((f for f in ws_list if isinstance(f, dict) and f.get("id") == fact.id), None)
        if existing:
            if tier != "permanent":  # never overwrite permanent facts even if LLM tries
                existing["text"] = text
                existing["tier"] = tier
        else:
            ws_list.append({
                "id": fact.id,
                "text": text,
                "tier": tier,
            })

    state.setdefault("scene", {})["world_state"] = ws_list
```

**Why:** Without world_state_add/remove on the delta model, this code is dead. Thread promotion in turn.py:395 handles all world state mutations directly from arc resolution outcomes.

**Validation:** Read back delta_builder.py lines 305–331 after edit. Confirm `return state` at line 329 is now immediately after the actions block (no orphaned code). No code execution needed.

#### Step 2.5 — Remove world_state display from changes.py _summarize_applied

**File:** `ccya/engine/changes.py`

**What:** Delete these lines from `_summarize_applied`:
```python
    for f in applied.get("world_state_add") or []:
        if isinstance(f, dict):
            text = f.get("text") or f.get("id", "?")
            short = str(text)[:56]
            lines.append(f"+ {short}{'…' if len(short) > 56 else ''}")
    for f in applied.get("world_state_remove") or []:
        if isinstance(f, str):
            short = f[:40] + ("…" if len(f) > 40 else "")
            lines.append(f"- {short}")
```

**Why:** These fields no longer flow through the pipeline. The UI change display should not show world state additions/removals from direct writes that never happen.

**Validation:** Read back changes.py lines 35–46 after edit. Confirm the loop for `pc_condition_add` at line 45 follows directly after inventory_update block without gap. No code execution needed.

---

## Implementation — Phase 3: Documentation Updates

### Context files to load
- `docs/architecture/OVERVIEW.md` (lines 80–99)
- `docs/repomap.md` (throughout, sections on StorytellerResult and extraction field routing)
- `docs/architecture/step2c-storytell.md`

### Detailed steps

#### Step 3.1 — Update OVERVIEW.md core result types and pipeline sections

**File:** `docs/architecture/OVERVIEW.md`

**What:** Remove world_state_add/world_state_remove from three locations:
- Line 55 (pipeline quick ref table): StorytellerResult output column — remove `, world_state_add/remove` after `gm_beat`. Update to: `...actions, outcome_summary | ...`
- Line 86 (Core Result Types glossary): Replace `- **StorytellerResult**: ..., gm_beat, world_state_add, world_state_remove, actions, ...` with `- **StorytellerResult**: thread_update, goal_update, arc_resolve, thread_resolve (with promote_to_world_state flag), thread_add, gm_beat, actions, outcome_summary`
- Line 99 (StateDelta description): Remove `, world_state_add/remove` from the StateDelta field list. Update to: `...pc_condition_add/remove`. Note: gm_beat is NOT in StateDelta — ...`

**Why:** Documentation must reflect that direct world state writes no longer exist in the pipeline. Only thread promotion produces durable facts. All three locations describe StorytellerResult or StateDelta output and all reference removed fields.

**Validation:** Read back OVERVIEW.md lines 55, 86, and 99 after edit. Confirm both fields removed from all three locations and promote_to_world_state mentioned in line 86 entry for thread_resolve.

#### Step 3.2 — Update repomap.md extraction field routing and pipeline sections

**File:** `docs/repomap.md`

**What:** Remove world_state_add/world_state_remove from three locations:
- Line 90 (5-call pipeline): Storytell entry — remove `, world_state_add/remove` after gate reference. Update to: `...thread_add (gated by PacingContext.gate), actions, gm_beat`
- Line 190 (Extraction field routing): StorytellerResult entry — replace `world_state_add: list[WorldStateFact], world_state_remove: list[str]` with nothing. Update to: `...thread_resolve processed by _apply_thread_resolutions()...`
- Line 204 (Key models — WorldStateFact): Replace `persistent facts are runtime-discovered durable environmental changes added via world_state_add (LLM must always emit "persistent")` with `persistent facts are runtime-added durable environmental changes promoted from thread/arc resolution outcomes`.

**Why:** Repomap is the module boundary reference. It must accurately reflect that world state mutations flow exclusively through thread/arc resolution promotion, not direct LLM emission.

**Validation:** Read back repomap.md lines 90, 190, and 204 after edit. Confirm both fields removed from all three locations and line 204 reflects promotion-only path for persistent facts.

#### Step 3.3 — Update step2c-storytell.md prompt guidance sections

**File:** `docs/architecture/step2c-storytell.md`

**What:** Remove direct world_state references from two locations and add static summary/scope differentiation:
- Line 36 (pipeline diagram): Remove the `world_state_add: list[WorldStateFact]<br>id, text, tier` node. Replace with promotion-only flow — thread_resolve outcomes feed into state.world_state via turn.py promotion logic.
- Line 49 (text description): Replace `feeds next turn's rules call via world_state_add/remove (persistent world facts)` with `feeds next turn's rules call via promoted world state from arc/thread resolution`.
- Add guidance matching Phase 1 prompt updates: static thread summaries ("DO NOT change after initial creation unless fundamental nature shifted") and arc vs scene scope differentiation in the thread operations section.

**Why:** The step doc describes pipeline mechanics including prompt behavior. It must match the updated prompt constraints — no direct world state emission, promotion-only path for durable facts.

**Validation:** Read back step2c-storytell.md lines 36 and 49 after edit. Confirm both references to direct writes removed and replaced with promotion-only language. Thread section includes static summary guidance matching Phase 1 updates.
