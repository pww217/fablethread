# Documentation Cleanup — Post-Phase Update

## Status
`completed` — all doc files updated and committed in 4733979.

## Phases

1 phase: update all documentation files (repomap, architecture docs, AGENTS.md) to reflect production code changes from prior phases. One coherent pass over the entire `docs/` tree and root-level config docs.

## Issue

After Phases 0–4 execute, numerous documentation files will reference deleted fields (`recent_events`, `recent_events_evicted`, `recent_events_compact`), old state shapes (static dict world_state instead of tiered list[WorldStateFact]), outdated ArcThread models (missing urgency_set_turn, two-stage latency for scene threads), and stale extraction field routing. These docs are the primary navigation surface for future developers — leaving them inconsistent with source code degrades signal-to-noise ratio and risks misdirecting new work.

## Solution

One documentation pass that updates every file in `docs/` (repomap, architecture subdocs) and root-level config docs (AGENTS.md) to match the post-Phase-4 production state. Each step declares which files it touches; no cross-step dependencies within this phase. Final validation: grep for deleted field names returns zero matches across all documentation.

## Firm decisions
1. Documentation updates are mechanical — name the old reference, replace with new contract. No rewrites or restructuring of existing docs beyond what's required by changed facts.
2. "Navigation path" in AGENTS.md should note that completed plans live in `/plans/completed/` and the executor should verify plan doc status matches implementation state before loading them.
3. REPOMAP updates are part of this phase, not separate per-plan steps (consolidated avoids 4+ redundant repomap edits).

## Non-goals
- Does NOT rewrite architecture docs for clarity or completeness — only fixes facts that changed due to prior phases.
- Does NOT update prompt templates (those are production code changes in Phases 0–2, not documentation).
- Does NOT move plan docs between directories (that's a housekeeping task the executor handles at the end if desired; ORDERING.md already notes which plans should be moved).

## Risks, Ambiguities, and Blockers
- If any prior phase was abandoned or partially implemented, some "deleted" references may still exist in source. The documentation update must match actual production state, not planned changes. Executor should verify deleted fields are actually gone before removing docs references.
- Architecture subdocs use mermaid diagrams (delta-validate.md). Diagram text is embedded markdown — the executor must edit the diagram nodes directly, which requires reading the file to locate exact line positions.

## Implementation: Documentation Cleanup

### Context files to load
1. `docs/repomap.md` (full file)
2. `docs/architecture/OVERVIEW.md` (full file)
3. `docs/architecture/delta-validate.md` (diagram needs editing)
4. `docs/architecture/step2c-progress.md` (StorytellerResult outputs)
5. `docs/architecture/out-of-band.md` (seed state shape)
6. `docs/architecture/thread-lifecycle.md` (directly affected by Phase 3 urgency decay + two-stage latency — most changes needed in this file)
7. `docs/architecture/narration-ui.md` (SSE event data references deleted field)
8. `docs/architecture/campaign-arcs.md` (ArcThread model, mermaid diagrams)
9. `AGENTS.md` (root-level "Navigation path" section)

### Detailed steps

#### Step 0.1 — Update docs/repomap.md

**File:** `docs/repomap.md`

**What:** One pass over the repomap fixing facts that changed:

- **Line 41** (`universal_asserts.py`): Remove "recent_events turn-stamped" from auto-checker description
- **Lines 52–54** (TurnResult dataclass public API): Delete `recent_events`, `recent_events_evicted` fields. New line: "TurnResult — returned from run_turn(): turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, diff, changes, metrics, errors, ruling, outcome_summary, ts"
- **Line 68** (apply_delta return type): Change "returns deep copy + evicted flag" → "returns deep copy of mutated state dict"
- **Lines 103–109** (Arc thread state machine + lifecycle): Add `urgency_set_turn: int | None` to ArcThread description. Update EXPIRED transition from "5+ silent turns via last_seen_turn tracking" → "two-stage: active→latent after scene_thread_expire_silent_turns (default 5) without progress; latent→removed after another 5 unsurfaced". Add note that arc threads use the same two-stage lifecycle for consistency.
- **Lines 150–154** (Extraction field routing — StorytellerResult entry): Remove "recent_events_add/update/remove" from the description. Replace with "world_state_add: list[WorldStateFact], world_state_remove: list[str]". Add "completed_threads: list[ArcThread]" to the completed threads rendering note.
- **Line 222** (state.yaml scene section): Change `"world_state": [str]           # immutable after seed"` → `"world_state": list[WorldStateFact]   # permanent tier = seed-authored; persistent tier = LLM-added at runtime"`. Remove the entire line for "recent_events: list[Event]" since it no longer exists.
- **Line 216** (arc.threads description): Add "urgency_set_turn tracks when urgency was last set, enabling decay pass".

**Why:** Repomap is the primary navigation surface for developers navigating the codebase. Every deleted field and changed model shape must be reflected here or future work will follow stale guidance.

**Validation:** `rg "recent_events" docs/repomap.md` should return zero matches (except in "completed/" references). Verify ArcThread description includes urgency_set_turn. Verify apply_delta signature shows just dict return type.

#### Step 0.2 — Update docs/architecture/OVERVIEW.md

**File:** `docs/architecture/OVERVIEW.md`

**What:** One pass over the overview fixing facts:

- **Line 55** (Step 2c pipeline table): Remove "recent_events_add/update/remove" from Key outputs column
- **Line 88** (StorytellerResult model glossary): Delete "recent_events_add/update/remove". Add "world_state_add, world_state_remove, completed_threads with outcome sentences"
- **Lines 125–133** (ArcThread model definition): Add `urgency_set_turn: int | None` field. Update the "last_seen_turn, added_turn" line to note two-stage latency for scene threads (active→latent at threshold → removed at 2×threshold). Note that ArcThread.resolution_state is set by _apply_thread_resolutions() when thread_resolve processes resolved/failed/abandoned outcomes
- **Line 137** (StateDelta description): Remove "recent_events_add/update/remove" from the merge list

**Why:** OVERVIEW.md is the first doc most developers read. It must accurately reflect the current pipeline data flow and model shapes.

**Validation:** `rg "recent_events" docs/architecture/OVERVIEW.md` should return zero matches (except in "completed/" references). Verify ArcThread definition includes urgency_set_turn.

#### Step 0.3 — Update docs/architecture/delta-validate.md

**File:** `docs/architecture/delta-validate.md`

**What:** Edit the mermaid diagram nodes:
- Remove "recent_events_add / update / remove" from the StateDelta merge node (around line 19)
- Remove "scene.recent_events (ring buffer, max 20)" from the apply_delta mutation list (around line 23). Replace with "scene.world_state (persistent tier: add/update by id, delete by id; permanent tier immutable)".

**Why:** The mermaid diagram is a visual contract for how deltas flow through validation and application. It must match actual production behavior.

**Validation:** Read the file to confirm the diagram nodes reflect the changes. No shell command validates mermaid rendering — rely on visual inspection after editing.

#### Step 0.4 — Update docs/architecture/step2c-progress.md

**File:** `docs/architecture/step2c-progress.md`

**What:** One pass:
- Remove "recent_events_add", "recent_events_update", "recent_events_remove" from the StorytellerResult output nodes (around lines 32–34). Replace with "world_state_add, world_state_remove".
- Update line 46 narrative to remove "durable history events" reference (replaced by completed_threads in prompts).

**Why:** This subdoc describes Step 2c's outputs. It must match the current StorytellerResult model fields.

**Validation:** `rg "recent_events" docs/architecture/step2c-progress.md` should return zero matches (except "completed/" references).

#### Step 0.5 — Update docs/architecture/out-of-band.md

**File:** `docs/architecture/out-of-band.md`

**What:** Remove "scene.recent_events" from the seed state diagram node (around line 59). The seed generates world_state with tiered facts, not recent_events.

**Why:** Seed envelope no longer produces scene.recent_events — it's been removed by Phase A.

**Validation:** `rg "recent_events" docs/architecture/out-of-band.md` should return zero matches (except "completed/" references).

#### Step 0.6 — Update docs/architecture/thread-lifecycle.md

**File:** `docs/architecture/thread-lifecycle.md`

**What:** One pass over the entire file (160 lines, most changes needed in this doc):
- **Lines 15-16 scope table**: "Scene" expiration "Via scene age rules (indirect)" → "Two-stage: active→latent at threshold → removed at 2×threshold"; "Arc" expiration "5 silent turns → demote to latent" → "two-stage lifecycle for both scopes"
- **Lines 18-19**: "Scene-scoped threads...excluded from engine processing by the `scope == 'arc'` filter" — after Phase 3, scene threads ARE processed (progress tracking extended). Change to "included in engine processing alongside arc threads via scope-aware filters".
- **Line 40** (Phase A table): "Demote: active = False, last_seen_turn = None" → "Stage 1: demote to latent (active=False); Stage 2: remove at 2×threshold if unsurfaced. Also set urgency='background'."
- **Lines 64-66** "5-turn expiry (age-based)" → "two-stage latency for scene threads; arc threads use same lifecycle after Phase 3"
- **Mermaid diagram S2 node** (line 49): "If last_seen_turn < turn_no - 5 → demote active=False" → "Stage 1: if turns_since_last_seen ≥ threshold → set active=False, urgency='background'; Stage 2: if unsurfaced for 2×threshold → remove from arc.threads"
- **Lines 142-151 Constants Reference table**: Add `thread_urgency_max_age` (default 8) and `scene_thread_expire_silent_turns` (default 5). Replace `_EXPIRE_SILENT_TURNS = 5` → "Replaced by config field scene_thread_expire_silent_turns".
- **Line 42**: "Progress ≥ config.thread_completion_threshold" — note that this applies to both arc and scope threads after Phase 3.

**Why:** This is the most directly affected architecture doc by Phase 3 changes (urgency decay + two-stage latency for scene threads). It must reflect the new lifecycle rules or future developers will follow stale guidance.

**Validation:** `rg "5-turn expiry\|_EXPIRE_SILENT_TURNS" docs/architecture/thread-lifecycle.md` should return zero matches (except "completed/" references). Verify Constants Reference table includes thread_urgency_max_age and scene_thread_expire_silent_turns.

#### Step 0.7 — Update docs/architecture/narration-ui.md

**File:** `docs/architecture/narration-ui.md`

**What:** One edit:
- **Line 26**: Remove "recent_events_evicted" from the SSE event data payload description in the DONE node. Current text includes "recent_events_evicted, ts }" — remove "recent_events_evicted, " so it reads "ts }".

**Why:** The "recent_events_evicted" field is deleted by Phase A (TurnResult no longer carries this bool). The SSE event data reflects TurnResult fields and must be updated.

**Validation:** `rg "recent_events_evicted" docs/architecture/narration-ui.md` should return zero matches (except "completed/" references).

#### Step 0.8 — Update docs/architecture/campaign-arcs.md

**File:** `docs/architecture/campaign-arcs.md`

**What:** One pass over the entire file (211 lines, 4 mermaid diagrams):
- **Lines 18-32 ArcThread model definition**: Add `urgency_set_turn: int | None = None`. This field records when urgency was last set, enabling the decay pass.
- **Line 34 "Key change from previous architecture"**: Update "age-based demotion (active: True → False)" → "two-stage lifecycle for scene threads; arc+scene progress tracking". Add note about urgency decay stepwise demotion (urgent→normal→background).
- **Mermaid diagram S2 node** (line 49): "If last_seen_turn < turn_no - 5 → demote active=False" → "Stage 1: if turns_since_last_seen ≥ threshold → set active=False, urgency='background'; Stage 2: if unsurfaced for 2×threshold → remove from arc.threads".
- **Line 64**: "age-based demotion (active: True → False)" → "two-stage latency for scene threads; urgency decay stepwise demotion (urgent→normal→background)".
- **Line 66 "5-turn expiry"**: Replace with "Two-stage lifecycle: active→latent at threshold turns without progress; latent→removed after another threshold unsurfaced. Urgency decays stepwise over thread_urgency_max_age turns."

**Why:** This is the canonical ArcThread data model reference in architecture docs. It must include all fields (including new urgency_set_turn) and reflect the two-stage lifecycle + urgency decay from Phase 3.

**Validation:** Verify ArcThread definition includes urgency_set_turn: int | None = None. Verify "5-turn expiry" text replaced with "two-stage latency". Verify mermaid S2 node updated for two-stage logic.

#### Step 0.9 — Update AGENTS.md "Navigation path" section

**File:** `AGENTS.md` (root-level)

**What:** One edit in the "Runtime context" section:
- Add a note after "Plan selection": "If multiple plans are open in `/plans/review/` or `/plans/`, the user specifies which to execute. If not specified, ask before proceeding." → add "Completed plan docs live in `/plans/completed/`. Before loading any plan doc from that directory, verify its status line matches implementation state (open = implemented but needs status update; abandoned = no longer relevant)."

**Why:** Prevents the executor from loading stale or already-implemented plans as if they were pending work. The "fix-extraction-context" mismatch is an example of this risk.

**Validation:** Read AGENTS.md to confirm the navigation path section includes the completed-plan verification note.

### Tests to write or update

None — documentation-only changes. No code, no tests.

### REPOMAP updates required

This step IS the repomap update (Step 0.1). No additional REPOMAP file needs updating since docs/repomap.md is itself the REPOMAP.
