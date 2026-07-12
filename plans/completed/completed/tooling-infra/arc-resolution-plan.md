# Arc Resolution Redesign — Implementation Plan

## Purpose

Implement structured successor creation (`new_threads`, `drop_threads`) on arc resolution and add thread→world-state promotion (`promote_to_world_state`) so resolved thread outcomes become permanent world facts.

## Problem Statement

Arc resolution produces successor arcs with no concrete threads to pursue — just a goal string and stale carried-over threads. Separately, resolved thread outcomes vanish after TTL with no mechanism to promote meaningful results to permanent world facts. The prompt also has a JSON schema example that doesn't match the actual model, causing validation errors.

## Constraints

- No backward compatibility or migration.
- Storyteller is the only runtime writer to World State.
- `world_state_add`/`world_state_remove` remain on StorytellerResult (unchanged).
- Tests are temporarily removed during refactor — no test changes in this plan.
- `progress` field on ArcThread and TTL filtering are out of scope (handled by separate arc-system-redesign effort).

## Non-goals

- World state consolidation into thread system (both remain separate).
- Removal of `world_state_add`/`world_state_remove`.
- Changes to ruling engine, seed generation, thread chaining, or auto-culling.

## Solution

Four sequential phases: (1) update models with new fields and delete ThreadDirective, (2) rewrite arc resolution engine logic for `drop_threads` + `new_threads`, (3) add thread→world-state promotion in the resolution pipeline, (4) update prompt templates to match the new model shapes and add guidance on world state consolidation.

## Firm decisions

D1. `drop_threads: list[str]` on ArcResolution — opt-out carry-over (IDs to drop; everything else carries forward).
D2. `new_threads: list[ArcThread]` on ArcResolution — structured successor threads.
D3. `promote_to_world_state: bool` on ThreadResolution — immediate promotion (not gated on arc_resolve).
D4. `thread_directives: list[ThreadDirective]` removed from ArcResolution — replaced by `drop_threads`.
D5. ThreadDirective model deleted — `move_latent` handled via `thread_update {active: false}`.
D6. `world_state_add`/`world_state_remove` kept on StorytellerResult with updated prompt guidance.
D7. World state uses ID-based overwrite semantics (already exists in delta_builder.py:322-343).

## Risks, Ambiguities, and Blockers

- No blocker. **Promotion writes directly to state** — confirmed safe. Pipeline order in `turn.py`: `apply_delta` (line 1085, which writes `storytell_result.world_state_add` to state) runs **before** the arc director (lines 1118-1178), so `_apply_thread_resolutions` can directly mutate `state["scene"]["world_state"]` after the delta has been committed. Both paths use ID-based overwrite semantics, so later writes supersede earlier ones — correct behavior.

## Status

`completed` — all 4 phases implemented. Lint + typecheck pass with no errors or deviations from plan.

## Phases

4 phases: model changes → arc resolution engine → thread promotion engine → prompt updates.

## Implementation — Phase 1: Model changes

### Context files to load

- `ccya/models.py:29-38` (ArcThread)
- `ccya/models.py:344-370` (ThreadResolution, ThreadDirective, ArcResolution)
- `ccya/models.py:213-216` (WorldStateFact)
- `ccya/models.py:413-464` (StorytellerResult — verify arc_resolve field type auto-updates)

### Detailed steps

#### Step 1.1 — Add fields to ArcResolution

**File:** `ccya/models.py:364-369`

**What:** Replace `thread_directives: list[ThreadDirective]` with `drop_threads: list[str]` and `new_threads: list[ArcThread]`. Add import for list type if needed.

**Why:** D1 — opt-out carry-over; D2 — structured successor threads.

**Validation:** `make check` passes. New fields can be instantiated.

```python
class ArcResolution(BaseModel):
    resolution: str
    visible_goal: str
    goal_context: str
    thematic_question: str | None = None
    drop_threads: list[str] = Field(default_factory=list)
    new_threads: list[ArcThread] = Field(default_factory=list)
```

#### Step 1.2 — Add promote_to_world_state to ThreadResolution

**File:** `ccya/models.py:344-349`

**What:** Add `promote_to_world_state: bool = False` field to ThreadResolution.

**Why:** D3 — thread→world-state promotion flag.

**Validation:** `make check` passes.

```python
class ThreadResolution(BaseModel):
    id: str
    resolution_state: Literal["resolved", "failed", "abandoned"]
    outcome: str = ""
    promote_to_world_state: bool = False
```

#### Step 1.3 — Delete ThreadDirective model

**File:** `ccya/models.py:359-361`

**What:** Remove the ThreadDirective class entirely.

**Why:** D5 — replaced by `drop_threads: list[str]`. No replacement needed.

**Validation:** `make check` passes. No references to `ThreadDirective` remain outside models.py. `grep -rn "ThreadDirective"` shows clean except for the deleted lines themselves.

### Tests to write or update

None (tests temporarily removed during refactor).

---

## Implementation — Phase 2: Arc resolution engine

### Context files to load

- `ccya/engine/turn.py:209-294` (`_apply_arc_resolve`)
- `ccya/engine/turn.py:1118-1140` (arc director pipeline — arc_resolve section)

### Detailed steps

#### Step 2.1 — Rewrite thread directive processing in _apply_arc_resolve

**File:** `ccya/engine/turn.py:264-281`

**What:** Replace the `thread_directives` iteration logic with `drop_threads` list processing. Instead of building `directive_ids` and checking actions, iterate `resolution.drop_threads` and drop matching threads. No `move_latent` dispatch — threads not in `drop_threads` carry over as-is.

**Why:** D4 — `thread_directives` replaced by `drop_threads: list[str]`. Opt-out: everything carries forward unless explicitly dropped.

**Validation:** Build a successor arc with `drop_threads=["t1", "t2"]` and confirm t1/t2 are removed from carried threads, all others persist.

#### Step 2.2 — Add new_threads to successor arc creation

**File:** `ccya/engine/turn.py:282-290`

**What:** After creating the successor `CampaignArc`, append `resolution.new_threads` to the `threads` list. The successor arc gets: surviving (carried-over) threads + `new_threads` fresh threads.

**Why:** D2 — structured successor threads. New adventure needs concrete things to do.

**Validation:** Build with `new_threads=[ArcThread(...), ArcThread(...)]` and confirm both appear in the successor's threads list alongside carried-over threads.

#### Step 2.3 — Update logging in _apply_arc_resolve

**File:** `ccya/engine/turn.py:258-262`

**What:** Update the info log to log `drop_threads` count instead of `directives_count`. Add logging for `new_threads` count.

**Why:** Log message references removed field `resolution.thread_directives`.

**Validation:** Logs show correct counts.

### Tests to write or update

None.

---

## Implementation — Phase 3: Thread promotion engine

### Context files to load

- `ccya/engine/turn.py:297-375` (`_apply_thread_resolutions` — full function)
- `ccya/engine/turn.py:1141-1150` (arc director pipeline — thread_resolve section)
- `ccya/state/delta_builder.py:322-343` (world state overwrite semantics for reference pattern)
- `ccya/models.py:213-216` (WorldStateFact shape)

### Detailed steps

#### Step 3.1 — Add promote_to_world_state handling in _apply_thread_resolutions

**File:** `ccya/engine/turn.py:297-375`

**What:** Inside the resolution loop (where `res` and `thread` are available), check `res.promote_to_world_state`. If true, write a dict entry directly to `state["scene"]["world_state"]` using ID-based overwrite semantics matching `delta_builder.py:322-343`:
```python
ws_list = state.setdefault("scene", {}).get("world_state") or []
existing = next((f for f in ws_list if isinstance(f, dict) and f.get("id") == res.id), None)
if existing:
    existing["text"] = res.outcome
    existing["tier"] = "persistent"
else:
    ws_list.append({"id": res.id, "text": res.outcome, "tier": "persistent"})
state.setdefault("scene", {})["world_state"] = ws_list
```

Follow the exact same pattern as delta_builder.py lines 328-341 (iterate → find by ID → overwrite or append). No model construction needed — write dict entries directly.

**Why:** D3 — immediate promotion; D7 — overwrite semantics.

**Validation:** Turn on with `promote_to_world_state=true` on a thread_resolve, confirm the outcome appears in `state.scene.world_state` after the function runs. Verify overwrite: same thread ID resolves twice — second outcome replaces the first.

#### Step 3.2 — Handle the delta interaction for promoted world state

**File:** `ccya/engine/turn.py:1141-1178`

**What:** No pipeline code change should be needed — `_apply_thread_resolutions` already receives mutable `state` and can write to `state["scene"]["world_state"]` directly. The key constraint: this direct mutation happens BEFORE the StateDelta is yielded and processed by `apply_delta`. Confirm the pipeline order in `turn.py` shows arc director (lines 1118-1178) runs before the delta yield point. If the delta also contains `world_state_add` from `storytell_result`, the delta's `apply_delta` will process it AFTER the arc director. Since both paths use ID-based overwrite, later writes supersede earlier ones — which is correct behavior (delta writes reflect the most recent LLM output).

**Why:** D3 implementation — promotion writes happen at resolution time, delta writes happen later. Order is arc director → delta yield → apply_delta. Verify the ordering.

**Validation:** Trace the pipeline call path from `apply_state_delta` or equivalent entry point to confirm the arc director precedes the delta application in the same turn.

### Tests to write or update

None.

---

## Implementation — Phase 4: Prompt updates

### Context files to load

- `ccya/prompts/storytell_system.j2` (full file — 193 lines, need to read all)
- `ccya/prompts/storytell_system.j2` (lines 11, 99 — `surviving_threads` references — this field does not exist in any model; prompt bug being fixed)
- `ccya/prompts/context.py:248-269` (StorytellerBoundary — verify no changes needed)
- The revised design doc model shapes for reference

### Detailed steps

#### Step 4.1 — Fix JSON schema example

**File:** `ccya/prompts/storytell_system.j2:5-15`

**What:** Replace the current `arc_resolve` example with one matching the new model shape:
```json
"arc_resolve": {"resolution": "...", "visible_goal": "...", "goal_context": "...", "thematic_question": "...", "drop_threads": ["stale_thread_id"], "new_threads": [{"id": "new_thread", "summary": "...", "scope": "arc", "urgency": "normal"}]}
```

Add `promote_to_world_state: true` to the `thread_resolve` entry in the example (or add a standalone thread_resolve example if one doesn't exist).

**Why:** Fix validation error bug. Current example omits fields that the model requires, causing LLM emission to fail validation.

**Validation:** Render the prompt and confirm all ArcResolution and ThreadResolution fields appear in the JSON example. Cross-check each field name against the model.

#### Step 4.2 — Consolidate duplicate arc resolution sections into one

**File:** `ccya/prompts/storytell_system.j2:70-86, 94-101`

**What:** Merge the two arc resolution sections into a single authoritative section. Remove the duplicate (currently lines 94-101). The merged section should:
- Keep the prose from lines 72-80
- Replace `thread_directives` line 80 with `drop_threads`
- Add `new_threads` bullet
- Keep the timing guidance from lines 88-92
- Remove lines 94-101 entirely

**Why:** D4 — `thread_directives` → `drop_threads`; D2 — `new_threads`. Two sections contradict each other on field schemas.

**Validation:** No duplicate resolution sections remain. All field descriptions match the model shape.

New section should read something like:

```markdown
## Arc resolution

Use `arc_resolve` to signal that this campaign arc has reached its natural conclusion. This tells Python to store the resolved arc and generate a successor with new threads, goal_context from prior context, and thematic_question inherited from the parent.

**Only emit `arc_resolve` when resolving an arc.** If no arc is being resolved, omit the field entirely — do NOT return `"arc_resolve": {}`.

- `resolution`: One-sentence narrative summary of how this arc concluded.
- `visible_goal`: The next arc's visible goal, derived naturally from this arc's outcome.
- `goal_context`: 2–3 sentences explaining why this new goal matters to the PC specifically.
- `thematic_question`: Optional override for the successor arc's thematic question. Omit to inherit.
- `drop_threads`: Optional list of thread IDs to drop. Threads not listed carry over as-is into the successor arc (opt-out). Use `thread_update {active: false}` to mark a thread as dormant instead of dropping it.
- `new_threads`: Optional list of new thread objects to seed the successor arc with fresh narrative tension. At least one new thread recommended per resolution.

Arc resolution timing: Emit `arc_resolve` when the visible_goal has been meaningfully completed, abandoned, or transformed by events. ...
```

#### Step 4.3 — Update thread_resolve section with promote_to_world_state

**File:** `ccya/prompts/storytell_system.j2:56-68`

**What:** Add `promote_to_world_state` documentation to the thread_resolve section. Insert after the `outcome` description:

```markdown
- `promote_to_world_state` (optional, default false): When true, this thread's outcome becomes a persistent world state entry immediately — it will persist beyond TTL windows as a durable fact. Use this for outcomes that are permanently true about the world (a blockade collapsed, a faction turned hostile, a route destroyed). Do NOT use for narrative tension that could still change — that's what unresolved threads are for.
```

**Why:** D3 — flag that promotes thread outcomes to persistent world facts.

**Validation:** Render the prompt and confirm `promote_to_world_state` appears in the thread_resolve section.

#### Step 4.4 — Update world state rules with consolidation guidance

**File:** `ccya/prompts/storytell_system.j2:108-122` (World state rules section)

**What:** Add guidance to the world state rules section:

1. **Prefer update over create:** When a fact already exists in world state, reuse its ID and update the text rather than creating a new entry. The engine merges by ID — reuse the same ID to update, use a new ID to create.
2. **Consolidate overlapping facts:** If two world state entries describe the same reality (e.g., `faction_allied_traders` and `traders_friendly_to_pc`), update one to cover both and remove the other via `world_state_remove`.
3. **Avoid duplication with threads:** If a fact represents narrative tension that could still change, keep it as a thread. Only promote to world state when it's settled durable reality.

Leave the existing separation rule ("Threads track narrative tension; world state tracks durable reality") in place — it's still correct.

**Why:** D6 — world state conciseness without engine enforcement.

**Validation:** Both update-over-create and consolidation guidance are present in the rendered prompt.

*(Step 4.5 omitted — `_get_resolved_arcs()` already exists in `narrate.py:122`, `_arc.j2` already uses `resolved_arcs` and `ra.resolved_turn`, and no `surviving_threads` reference remains. Already implemented by arc-system-md.)*

### Tests to write or update

None.
