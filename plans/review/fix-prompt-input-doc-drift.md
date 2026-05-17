# Fix Prompt Input / Documentation Drift

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Remove quest system remnants from ARCHITECTURE.md Step 2c | Delete `quest_ages`, `quest_threshold_directive`, `active_quests`, and the standalone `deescalate` named input from the Step 2c input table and diagram |

## Objective
Three stale references to the removed quest system (`quest_ages`, `quest_threshold_directive`, `active_quests`) and one superseded input (`deescalate` — now subsumed by `narrative_velocity`) remain in `docs/ARCHITECTURE.md`'s Step 2c pipeline diagram. The code and templates already reflect the post-quest-system state; only the documentation lags. This plan corrects the documentation to match reality.

## Non-goals
- No changes to any Python source files.
- No changes to any Jinja2 template files.
- No changes to `docs/REPOMAP/prompts.md` (it already documents the quest-system fields as removed).
- No changes to any arc-related prompt or logic.

## Implementation — Phase 01: Remove quest system remnants from ARCHITECTURE.md Step 2c

### Files to pull for context
- `docs/ARCHITECTURE.md` — the only file modified in this phase.

### Detailed steps

#### Step 1.1 — Remove stale inputs from the Step 2c pipeline table

**File:** `docs/ARCHITECTURE.md`

**What:** In the main `## 5-Pipeline Reference` table, the Step 2c row lists these stale inputs in the "Key inputs" cell:
- `active_quests`
- `recent_turns[-2:]` (was documented as T-1 + T-2; confirmed correct in Python — `[-2:]` is passed — but the template renders only `recent_turns[-1]`. The Python slice is intentional headroom; the description is misleading. Update the cell to say `recent_turns[-1:]`.)
- `deescalate: float` (standalone — now fully subsumed by `narrative_velocity`; remove as a named input)
- `quest_ages: list[dict]`
- `quest_threshold_directive`

Also remove `quest_updates` from the "Key outputs" cell — the quest system is gone.

**Why:** These fields no longer exist in `_extract_progress_messages()` (confirmed by reading `extraction.py`). Listing them as inputs misrepresents the pipeline to future readers and plan executors.

**Replacement text for the Step 2c "Key inputs" cell:**

```
`narrative`, `state.pc`, `state.scene.recent_events`, `state.scene.world_state`, `active_threads`, `npc_roster` (tiered: PRESENT/JUST_LEFT/KNOWN), `scene_pressure`, `RulesOutcome`, `intent`, `recent_turns[-1:]`, `stakes`, `band`, `narrative_velocity`, `narration_directive`, `pending_beat`
```

**Replacement text for the Step 2c "Key outputs" cell:**

```
`ProgressExtractResult`: `recent_events_add/update/remove`, `actions` (4 suggested choices), `outcome_summary`, `gm_beat`, `beat_disposition`, `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update`
```

**Validation:** After edit, `grep -n "quest_ages\|quest_threshold_directive\|active_quests" docs/ARCHITECTURE.md` returns zero results (other than any legitimate narrative prose references to the arc system, which don't use those field names).

#### Step 1.2 — Remove stale inputs from the Step 2c Mermaid flowchart

**File:** `docs/ARCHITECTURE.md`

**What:** The `## Step 2c — Progress Extract` section contains a Mermaid `flowchart LR` with an `IN["Inputs"]` subgraph. Remove these nodes entirely:

```
S5[\"active_quests (status=active only)\"]
S10[\"recent_turns[-2:]<br>(T-1 + T-2 prior narration<br>for outcome_summary context)\"]
S13[\"deescalate: float<br>(pressure resolution magnitude)\"]:::xstream
S16[\"quest_ages: list[dict]<br>(stalled-quest signal)\"]
S18[\"quest_threshold_directive<br>(guidance on new-quest aggressiveness)\"]
```

Update the `recent_turns` node (currently `S10`) to reflect 1 prior turn:

```
S10["recent_turns[-1:]<br>(T-1 prior narration)"]
```

Remove `quest_updates` from the `OUT["Outputs — ProgressExtractResult"]` subgraph:

```
O1["quest_updates: list[QuestUpdate]<br>  id, title, status,<br>  objectives[]: index, description,<br>  done, failed"]:::outNode
```

Renumber the remaining `S` and `O` nodes consecutively so the diagram has no gaps (or leave gaps — Mermaid does not require consecutive numbering; leaving gaps is acceptable).

**Why:** The Mermaid diagram is the primary visual reference for the pipeline. Stale nodes create confusion when reading diffs or planning changes.

**Validation:** Paste the updated Mermaid block into the [Mermaid Live Editor](https://mermaid.live) and confirm it renders without errors. Check that no `S` or `O` node in the diagram references quest or deescalate.

#### Step 1.3 — Remove stale `deescalate` named input from the Step 2c prose description

**File:** `docs/ARCHITECTURE.md`

**What:** The inline `> Always runs:` callout after the Step 2c diagram does not mention `deescalate` by name — no change needed there. However, the Step 1 Narrate diagram in the `## Step 1 — Narrate (Streaming)` section still lists `N15["deescalate"]` as a named input node. This is accurate — the narrate step does receive `deescalate` — so **leave it**. No change needed here.

Confirm there are no other standalone references to `deescalate` as a Step 2c input in prose sections. If found, remove them.

**Validation:** `grep -n "deescalate" docs/ARCHITECTURE.md` should only match:
1. The Narration Directive section (where it explains narrative_velocity and deescalation semantics).
2. The Step 1 Narrate diagram (`N15["deescalate"]`).
3. Any narrative prose that explains the historical relationship. Zero matches in the Step 2c section.

### Tests to write or update
No new tests required — this is a documentation-only change. No Python logic is modified.

Run `make check` after editing to confirm no linting errors were introduced (unlikely for a `.md` change, but required by AGENTS.md as the final validation step).

### REPOMAP and architecture updates
`docs/REPOMAP/prompts.md` already correctly documents these fields as removed (confirmed). No REPOMAP update needed.

### Risks
1. **Mermaid node renumbering introduces a gap.** Mermaid handles non-consecutive node IDs fine; renumber only if the executor prefers cleanliness. Risk: none functional.
2. **`recent_turns[-2:]` vs `[-1:]` ambiguity.** Python passes `[-2:]` to the function; the template renders only `[-1]`. The doc should describe what the template actually uses (`[-1:]`). Risk: changing this could confuse someone reading the Python. Mitigation: add a parenthetical — "Python passes `[-2:]`; template renders `[-1]`" — if clarity is preferred over brevity.

## Ambiguities requiring resolution before execution
None. All fields confirmed absent from `_extract_progress_messages()` in `extraction.py` and from `extract_progress_user.j2`. The documentation change is unambiguous.
