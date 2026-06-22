# Phase B: Promote world_state to Mutable Tiered Structure

## Status
`completed`

## Phases

1 phase promoting `scene.world_state` from an immutable list of strings (seed-authored, never mutated) to a mutable tiered structure (`WorldStateFact` with permanent/persistent tiers), wiring up LLM write access via new delta fields, and updating all prompt templates to always show world_state to the Storyteller. Phase A must complete first — this phase depends on recent_events being removed from models and state shape.

## Issue

`scene.world_state` is completely inert after seed time: a list of plain strings that cannot be modified during play. Permanent capability changes — destroyed routes, lost objects, dead key NPCs — have no appropriate home in the current system because they do not belong in arc threads (forward-looking plot machinery), conditions (PC-scoped), or recent_events (expires, narrative-flavored). The Storyteller also only receives world_state when `all_threads` is empty (`{% if not all_threads %}` gate at storytell_user.j2:26), meaning persistent world facts are invisible to the LLM during active gameplay — precisely when they should be most relevant.

## Solution

Promote `scene.world_state` from a list of strings to a list of `WorldStateFact` objects with two tiers:
- **permanent**: seed-authored, never written or removed by the LLM (tier preserved on load for backward compatibility during Phase B only; no migration function after Phase A removes old state files).
- **persistent**: LLM-authored at runtime via new `world_state_add` field; survives compaction indefinitely (compactor never removes); removable via `world_state_remove` when no longer relevant.

Add `world_state_add: list[WorldStateFact]` and `world_state_remove: list[str]` fields to both `StorytellerResult` and `StateDelta`. Apply these changes in `apply_delta()` — persistent facts are appended/updated by id, removed facts deleted from the list. Permanent facts are never touched by apply_delta or LLM output validation.

Update prompt templates: always show world_state to Storyteller (remove `{% if not all_threads %}` gate), rewrite `_world_state.j2` to render `WorldStateFact.text` instead of plain strings, update storytell_system.j2 JSON schema and instructions with tier rules constraint ("emit only for facts that would still be true 10 turns from now in a different location").

Expected outcome: world_state becomes the correct write target for durable environmental changes discovered or created during play; Storyteller always has persistent world context regardless of thread activity. No hard cap on `world_state_add` per turn, ever — rely solely on prompt constraint (user decision #1).

## Firm decisions
1. Permanent facts come from seed generation and persist indefinitely; never written or removed by LLM or apply_delta
2. Persistent facts survive compaction indefinitely (compactor never removes them). LLM removes stale facts via `world_state_remove` when no longer relevant — judged from narrative context, not tracked by timestamp. No `created_turn` or age tracking on WorldStateFact; the LLM decides staleness from story progression.
3. No hard cap on `world_state_add` per turn — ever. No Python-level enforcement now or later. Rely solely on prompt constraint to prevent abuse.
4. One sentence per outcome is sufficient for ThreadResolution.outcome (Phase C) — no multi-sentence summaries or structured resolution data needed
5. Completed thread outcomes visible in both Storyteller AND Narrator prompts (user decision #2)
6. No migration function — old state files fail on load intentionally after Phase A removes recent_events

## Non-goals
- Do not add compaction-based expiration for persistent facts (Phase D or later)
- Do not fix key-branch black hole at turn.py:1275 (separate phase)
- Do not update Narrator prompt to show completed_threads outcomes (Phase C — outcome field addition must come first)
- Do not write tests — per AGENTS.md, tests are temporarily removed during refactor

## Risks, Ambiguities, and Blockers

**Blocker:** Phase A (`01-delete-recent-events.md`) must complete first. This phase depends on recent_events being fully removed from models.py (RecentEvent model deleted), state shape (scene.recent_events removed from default_state), and apply_delta signature (no more ring buffer logic). Attempting to execute this phase before Phase A will cause conflicts at multiple files: models.py, delta_builder.py, io.py.

**Risk:** `seed.py` line 38-39 iterates over `envelope.seed_state.scene.world_state` assuming each element is a string (calls `_strip_non_ascii(evt)` on it). After this phase, world_state elements are `WorldStateFact` objects with `.text` attribute — the strip loop must be updated to access `.text`. Static pack seeds that still have plain strings in their YAML will need updating or the coercion logic must handle both types.

**Risk:** `_world_state.j2` currently renders `{% for fact in (state.scene.world_state or []) %}- {{ fact }}` assuming each element is a string. After this phase, elements are `WorldStateFact` objects — template must access `.text`. The Jinja template will crash on old state files that still have strings; this is acceptable since Phase A ensures no migration and old states fail to load anyway.

**Ambiguity:** Should persistent facts be labeled in the prompt templates? Design doc says "distinguished by a subtle label only if needed for LLM clarity." Decision: include tier labels in rendering (`[permanent]` / `[persistent]`) so the Storyteller understands which tier it's reading, but do NOT allow the LLM to change or remove permanent facts.

## Implementation — Phase B: Promote world_state to mutable tiered structure

### Context files to load
1. `ccya/models.py` (lines 28-57 for ArcThread/CampaignArc; lines 385-407 for StorytellerResult)
2. `ccya/state/delta_builder.py` (entire file, focus on apply_delta at lines 123-362 and recent_events ring buffer at lines 291-325)
3. `ccya/state/io.py` (lines 83-87 for default_state scene section; line 38-39 for seed strip loop)
4. `ccya/engine/seed.py` (lines 38-39 for world_state non-ascii stripping in _strip_seed_non_ascii)
5. `ccya/prompts/storytell_user.j2` (entire file, focus on line 15 all_threads gate and line 26 world_state conditional)
6. `ccya/prompts/sections/_world_state.j2` (entire file — current 2-line template)
7. `ccya/prompts/storytell_system.j2` (lines 1-17 for JSON schema; lines 42-50 for recent_events rules to replace with world_state instructions)
8. `ccya/engine/extraction.py` (lines 250, 268 for world_state context passing)

### Detailed steps

#### Step B.1 — Add WorldStateFact model and wire into StorytellerResult + StateDelta

**File:** `ccya/models.py`

**What:** Four changes:
1. Insert new Pydantic model after line 225 (after RecentEventUpdate, before StateDelta):
```python
class WorldStateFact(BaseModel):
    id: str
    text: str
    tier: Literal["permanent", "persistent"] = "persistent"
```

2. From `StorytellerResult` (~lines 386-394), remove the three recent_events fields (already deleted by Phase A) and add two new fields after outcome_summary or at end of model definition:
   - Remove existing lines for `recent_events_add`, `recent_events_update`, `recent_events_remove` if not yet removed by Phase A.
   - Add: `world_state_add: list[WorldStateFact] = Field(default_factory=list)` and `world_state_remove: list[str] = Field(default_factory=list)`.

3. From `StateDelta` (~lines 248-252), remove the three recent_events fields (already deleted by Phase A) and add two new fields after compendium_npc_update or near actions field:
   - Add: `world_state_add: list[WorldStateFact] = Field(default_factory=list)` and `world_state_remove: list[str] = Field(default_factory=list)`.

**Why:** WorldStateFact is the new data shape for world_state entries. The permanent/persistent tier distinction lets Python protect seed-authored facts from LLM mutation while allowing runtime discovery of durable environmental changes to be recorded as persistent facts. StorytellerResult and StateDelta carry these mutations through extraction → apply_delta pipeline.

**Validation:** `rg "class WorldStateFact" ccya/models.py` should return exactly one match (the new model definition). `python -c "from ccya.models import StorytellerResult, StateDelta; print('world_state_add' in StorytellerResult.model_fields, 'world_state_remove' in StorytellerResult.model_fields)"` should output True True for both models.

#### Step B.2 — Replace recent_events ring buffer logic with world_state add/remove handling in apply_delta

**File:** `ccya/state/delta_builder.py`

**What:** Three changes (NOTE: step A.2 from Phase A must complete first to remove the recent_events_max parameter and return type change):
1. If Phase A has already removed the recent_events ring buffer section (~lines 291-325 in current source), skip this sub-step entirely — do not attempt to delete code that no longer exists.
2. Insert new world_state handling logic at the position where recent_events ring buffer was (~lines 325+):
```python
    # --- World state mutations (persistent tier only) ---
    ws_list: list[dict[str, Any]] = copy.deepcopy(state.get("scene", {}).get("world_state") or [])
    
     for rem_id in delta.world_state_remove:
         ws_list = [f for f in ws_list if not (isinstance(f, dict) and f.get("id") == rem_id and f.get("tier") != "permanent")]
    
    for fact in delta.world_state_add:
        tier = fact.tier  # LLM should only emit "persistent"; permanent facts are seed-only
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

3. Ensure the new world_state handling is placed after inventory/condition/NPC logic and before any remaining scene mutations (tags/tagline). Do NOT place it inside or near where recent_events ring buffer was — place it as a distinct block following the existing pattern of other delta field handlers in apply_delta.

**Why:** The ring buffer logic was entirely dedicated to managing scene.recent_events as a FIFO capped list, which is being removed by Phase A. World_state mutations follow a different model: persistent facts are additive (new ids appended) or updatable (by id), and deletions remove by id permanently — no eviction cap needed since world_state grows organically with discovered/created durable facts. Permanent facts are never touched by apply_delta regardless of what the LLM emits in world_state_add. The removal guard checks `f.get("tier") != "permanent"` — only non-permanent (persistent) facts can be removed by ID; permanent facts are kept unconditionally.

**Validation:** `rg "recent_events.*ring\|ring.*buffer" ccya/state/delta_builder.py` should return zero matches (except comments). Verify that `delta.world_state_add` and `delta.world_state_remove` are referenced exactly once each in apply_delta logic body.

#### Step B.3 — Update default state shape: world_state from list[str] to list[dict] with permanent tier defaults

**File:** `ccya/state/io.py`

**What:** One change:
1. In `_default_state()` (~lines 83-87), keep `"world_state": []` as-is at line 85 — empty list is valid default since actual seeding of permanent facts happens in seed.py step B.4, not here.

**Why:** Default state shape must match what the engine expects after this phase. The world_state field remains an empty list; dynamic packs populate it with WorldStateFact objects during seeding (step B.4), and static pack seeds may have plain strings that are handled by the strip loop in seed.py step B.4 sub-step 1.

**Validation:** `"world_state": []` remains at line 85 in io.py. Load a static pack and verify world_state loads without TypeError on string elements (handled by seed.py step B.4 sub-step 1).

#### Step B.4 — Update seed.py: handle WorldStateFact objects in non-ascii stripping and permanent tier seeding

**File:** `ccya/engine/seed.py`

**What:** Two changes:
1. In `_strip_seed_non_ascii()` (~lines 38-39), update the world_state strip loop to check element type — if dict-like (WorldStateFact or pre-existing dict from static pack), access `.text` / `["text"]`; if plain string, apply `_strip_non_ascii(evt)` directly.
2. In dynamic seed generation (~lines 346-348 where baseline_facts are merged into world_state), change the merge logic to produce WorldStateFact objects instead of strings: each fact should be wrapped as `{"id": f"baseline_{i}", "text": text, "tier": "permanent"}`.

**Why:** Static pack seeds may have plain string elements in their world_state YAML; dynamic packs generate facts that must conform to the new WorldStateFact shape with permanent tier explicitly set. The strip loop handles both types gracefully without crashing on load of old or new seed data.

**Validation:** `rg "world_state.*tier\|tier.*world_state" ccya/engine/seed.py` should show at least one match (the baseline_facts merge producing permanent-tier facts). Load a dynamic pack and verify world_state entries have `"tier": "permanent"` in state.yaml after seeding.

#### Step B.5 — Update extraction.py: pass world_state to storytell_user.j2 template with new shape handling

**File:** `ccya/engine/extraction.py`

**What:** One change at line 250 and line 268:
1. Line 250 (`world_state = list(scene.get("world_state") or [])`) — no functional change needed; this already reads the world_state list from state regardless of element type (strings or dicts). The template will handle rendering differences in step B.7.
2. Verify line 268 passes `world_state` to storytell_user.j2 context: `"world_state": world_state,`. No changes needed here — this already works correctly for the new shape since it's just passing a list of objects/strings through to the template layer.

**Why:** Extraction.py reads state and passes it to templates; no transformation is needed at this layer because the template (_world_state.j2) handles rendering differences between string elements (legacy) and WorldStateFact dict objects (new). The world_state context variable already exists in the render call — just verify it's still present after Phase A removes recent_events from the same function.

**Validation:** `rg "world_state.*:.*world_state" ccya/engine/extraction.py` should show at least one match confirming world_state is passed to template rendering context. No functional changes needed beyond verification.

#### Step B.6 — Update storytell_user.j2: always show world_state, remove all_threads conditional gate

**File:** `ccya/prompts/storytell_user.j2`

**What:** One change at approximately line 26:
1. Change `{% if not all_threads and world_state %}` to just `{% if world_state %}`. This removes the conditional gate that hides world_state from Storyteller during active gameplay — world_state should render whenever it has entries, regardless of thread activity status.

NOTE: If Phase A has already removed the recent_events section (lines 22-25 in current source), do NOT re-add or modify those lines. This step only changes the world_state conditional gate at line 26.

**Why:** World facts are always relevant context for the Storyteller, not a fallback for empty thread lists. The current gate means persistent world changes are invisible during active gameplay precisely when they should be most visible. Removing the conditional ensures world_state is always rendered to the LLM regardless of whether threads exist or are dormant.

**Validation:** `rg "if.*not all_threads and world_state" ccya/prompts/storytell_user.j2` should return zero matches (the gate removed). Verify that `{% if world_state %}` renders independently at approximately line 26 position after edits.

#### Step B.7 — Rewrite _world_state.j2: render WorldStateFact objects with tier labels

**File:** `ccya/prompts/sections/_world_state.j2`

**What:** Replace the entire current content (one line) with:
```jinja
{% for fact in (state.scene.world_state or []) %}{% if fact is mapping %}- [{% if fact.tier == "permanent" %}permanent{% else %}persistent{% endif %}] {{ fact.text }}
{% elif fact is string %}- {{ fact }}
{% endif -%}
{% endfor -%}
```

**Why:** The current template renders `{%- for fact in (state.scene.world_state or []) %}- {{ fact }}` assuming each element is a plain string. After this phase, world_state elements are `WorldStateFact` dicts with `.text` and `.tier` attributes. Pydantic models support attribute access (`fact.tier`, `fact.text`) but do NOT have a `.get()` method — using `fact.get("tier")` will raise an AttributeError at template render time. The new template handles both types: dict objects render tier label + text; legacy strings render as-is (for any old state files that somehow load). Tier labels help the Storyteller understand which facts are immutable seed-authored permanent truths vs runtime-discovered persistent changes.

**Validation:** Render a test prompt with world_state containing mixed elements and verify output shows `[permanent]` / `[persistent]` prefixes for dict objects and plain text for strings.

#### Step B.8 — Update storytell_system.j2: replace recent_events JSON schema with world_state, add tier rules instructions

**File:** `ccya/prompts/storytell_system.j2`

**What:** Three changes at lines 1-50+:
1. Replace the JSON schema example (lines 6-17) to remove recent_events fields and add world_state fields:
```json
{
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "thread_advance": ["thread_id_1", "thread_id_2"],
  "thread_resolve": [{"id": "thread_id", "resolution_state": "resolved"}],
  "thread_add": {"id": "snake_case_id", "summary": "story tension description", "scope": "arc", "urgency": "normal", "tags": [], "key": "subject_action"},
  "world_state_add": [{"id": "new_fact_id", "text": "durable world fact text", "tier": "persistent"}],
  "world_state_remove": ["fact_id_to_remove"]
}
```

2. Replace the entire recent_events rules section (lines 42 through 50 inclusive) with new world_state instructions:
```markdown
## World state rules

`world_state_add`: Emit only for durable environmental changes that persist beyond this turn — facts that would still be true 10 turns from now in a different location. Capability changes qualify (destroyed routes, lost objects, dead key NPCs). Scene-local observations do NOT qualify. Each entry: `{"id": "snake_case_id", "text": "fact description", "tier": "persistent"}`. The tier must always be `"persistent"` — permanent facts are seed-authored and never written by the LLM. Emit at most 2 world_state_add entries per turn to avoid bloat.

`world_state_remove`: IDs of persistent facts now false, outdated, irrelevant, or superseded (e.g., a blockade lifted, bridge rebuilt). Do NOT remove permanent tier facts — they are immutable seed-authored truths.
```

3. Remove the line at top of file (line 1) that says "Extract recent events" from the system prompt intro: change to "Extract suggested player actions, outcome summary, and thread advancement from a narration."

**Why:** The JSON schema is what the LLM sees as output format — it must match StorytellerResult model fields exactly. Recent_events fields are being removed by Phase A; world_state_add/remove replace them. The tier rules instruction enforces the design constraint that permanent facts cannot be mutated by the LLM, and the "still true 10 turns from now" rule prevents abuse of the new write target (no hard cap in Python per user decision #1). Limiting to 2 entries per turn is a prompt-level guard against bloat.

**Validation:** `rg "recent_event.*add\|world_state_add" ccya/prompts/storytell_system.j2` should show world_state_add references and zero recent_events_add matches (Phase A removes the latter). Verify JSON schema in template matches StorytellerResult model fields after Phase A completion.

#### Step B.9 — Update narrate_user.j2: remove TRACE_IMMUTABLE markers from world_state, rename section header

**File:** `ccya/prompts/narrate_user.j2`

**What:** One structural change at lines 15-34 (the TRACE_IMMUTABLE block). World_state now contains both permanent (seed-authored) and persistent (LLM-authored at runtime) facts — it is no longer purely immutable. Split the block:
1. Move world_state out of `<<<TRACE_IMMUTABLE_START>>>` ... `<<<TRACE_IMMUTABLE_END>>>` markers into its own section above them.
2. Rename `## Immutable Reference` to `## World State` for the world_state section.
3. Keep `<<<TRACE_IMMUTABLE_START>>>` / `<<<TRACE_IMMUTABLE_END>>>` wrapping only factions and name pool (these remain seed-authored and immutable).

New structure at lines 15-34:
```jinja
## World State
{% if state.scene.world_state -%}
{% include "sections/_world_state.j2" %}
{% endif -%}

<<<TRACE_IMMUTABLE_START>>>
## Immutable Reference
{% if world_factions -%}
### Known Factions
{% for f in world_factions %}- **{{ f.name }}** ({{ f.disposition }}){% if f.disposition == "friendly" and pc_allegiance == f.id %} — your faction{% endif %}
{% endfor -%}
{% endif -%}
{% if npc_name_pool -%}
### Name Pool
{% if npc_name_pool.male -%}
**Male:** {{ npc_name_pool.male | join(' · ') }}
{% endif %}{% if npc_name_pool.female -%}
**Female:** {{ npc_name_pool.female | join(' · ') }}
{% endif %}
{% endif -%}
<<<TRACE_IMMUTABLE_END>>>
```

The `{% include "sections/_world_state.j2" %}` now renders outside TRACE_IMMUTABLE because it contains both permanent and persistent facts. The `_world_state.j2` template (updated in Step B.7) already handles the tier labels with `[permanent]` / `[persistent]` prefixes.

**Why:** The TRACE_IMMUTABLE markers signal "this data is read-only, never changes during play." After Phase B, world_state includes persistent facts that ARE mutable at runtime — the markers are misleading. Separating world_state from immutable reference ensures LLMs understand that world_state contains both immutable seed truths and runtime-discovered changes, while factions and name pool remain truly immutable.

**Validation:** `rg "TRACE_IMMUTABLE" ccya/prompts/narrate_user.j2` should show two matches (start/end) wrapping only factions and name pool sections, NOT wrapping world_state. Render a prompt and verify world_state section appears before the TRACE_IMMUTABLE block. Note: world_state is never empty — permanent seed facts always exist at minimum.

### Tests to write or update
None — per AGENTS.md: tests are temporarily removed during refactor. Do not write or reference tests until this phase is complete.

### REPOMAP updates required
1. `docs/repomap.md` line 222 (state shape table): change `"world_state": [str]           # immutable after seed"` to `"world_state": list[WorldStateFact]   # permanent tier = seed-authored; persistent tier = LLM-added at runtime"`.
2. `docs/repomap.md` line 153 (extraction field routing — StorytellerResult entry): remove "recent_events_add/update/remove" from the description and add "world_state_add: list[WorldStateFact], world_state_remove: list[str]".
3. `docs/repomap.md`: Add new model entry for WorldStateFact after line 162 (GMBeat section) or in the Key models section — describe it as a Pydantic model with id, text, tier fields where tier defaults to "permanent" and LLM must always emit "persistent".
4. `docs/repomap.md` line 54 (TurnResult description): verify Phase A changes are reflected there already; do not add world_state references since TurnResult does not carry world_state data directly.
