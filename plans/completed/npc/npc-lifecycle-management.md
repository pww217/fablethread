# NPC Lifecycle Management — Departed Tracking, Nearby Decay, and Compendium Archive

## Purpose

Implement NPC lifecycle management so the engine distinguishes permanent departure from temporary absence, preserves proximity through location changes, and archives dead/gone NPCs out of prompt context while keeping records for debug and UI.

## Problem Statement

Two problems: (1) `presence: "known"` conflates "left the room" with "died permanently" — the engine has no way to distinguish them, so dead NPCs bloat the compendium forever. (2) Location change demotes present NPCs directly to `known`, losing the proximity signal — logically-following NPCs get forgotten by the LLM.

## Constraints

- Scene extractor LLM controls all narrative signals (departed, nearby, present). Engine never infers narrative state from mechanics.
- No backwards compatibility. Existing NPCs with `presence: "known"` remain as-is.
- Departed/archived NPCs must remain in `state.yaml` for debugging and compendium UI, even when excluded from prompts.
- Minimal blast radius: data model + lifecycle steps + roster filter + prompt changes. Not a pipeline restructuring.

## Non-goals

- NPC revival. Once `departed`, always `departed`. Once `archived`, always `archived`.
- Departed reason/summary displayed in UI. The fields are on the model; UI rendering is separate work.
- Migration of existing saves.

## Solution

Replace the current `present → known` location-change demotion with `present → nearby`, add auto-decay `nearby → known` after 2 turns, add a `departed` presence (single terminal state for all permanent exits) with `departed_reason`/`departed_summary`/`departed_turn` fields, and auto-archive `departed` NPCs after 3 turns by setting `presence: "archived"` — they remain in state.yaml but are excluded from `build_npc_roster()` and therefore never appear in any prompt.

## Firm decisions

01. **One terminal state: `departed`.** Covers all permanent exits (dead, sailed away, comatose, imprisoned for life). No separate `is_dead` field.
02. **`departed_turn` set once on first detection.** `entry.get("departed_turn", current_turn_no)`. Prevents TTL clock reset on repeated LLM emissions.
03. **`nearby` activated for location-change demotion.** `present → nearby` replaces `present → known`. Also teach LLM to optionally set `nearby`.
04. **`nearby` auto-decays to `known` after 2 turns.** Default config `nearby_decay_ttl = 2`.
05. **`departed` auto-archives after 3 turns.** Default config `departed_archive_ttl = 3`. Archive sets `presence: "archived"` — full record kept, excluded from all prompts.
06. **`build_npc_roster()` pre-filters out `archived`.** They never appear in prompt context. Departed NPCs during TTL appear at bottom with `[DEPARTED]` tag.
07. **Scene extractor can re-promote `nearby → present`.** Prompt teaches: if NPC was engine-demoted but narration says they followed, re-promote — don't recreate.
08. **`strip_npcs_notes()` skips departed and archived.** No point clearing notes on terminal NPCs.
09. **No deletion.** Archive is presence flag, not removal from `compendium.npcs`.

## Risks, Ambiguities, and Blockers

- **LLM may not consistently set `departed`.** Mitigation: prompt teaches explicitly. Soft failure — NPC stays as `known` (current behavior). No data loss.
- **LLM may create duplicate NPCs after location change instead of re-promoting.** Mitigation: existing dedup pre-check in `extract_scene_system.j2` lines 103-109 already handles this pattern for `known → present`; the new prompt instruction extends it to `nearby → present`.
- **`last_seen` stamp happens before lifecycle steps.** Design doc places lifecycle steps after `last_seen` stamp. No conflict — `last_seen` fires on delta NPCs; lifecycle steps fire on all NPCs.

## Status
`completed`

---

## Phases

4 phases: model/config fields (Phase 1), engine lifecycle (Phase 2), roster exclusion + template (Phase 3), prompt updates (Phase 4). Phase 4 has no dependency on Phase 3 and can execute in parallel.

---

## Implementation — Phase 1: Model and config changes

### Context files to load

- `ccya/models.py` lines 23-26 (NpcPresence enum), lines 245-258 (CompendiumNpcUpdate)
- `ccya/engine/config.py` lines 85-179 (EngineConfig dataclass)

### Detailed steps

#### Step 1.1 — Add `DEPARTED` to `NpcPresence` enum

**File:** `ccya/models.py:23-27`

**What:** Add `DEPARTED = "departed"` to the `NpcPresence` enum after `KNOWN`. `ARCHIVED` is NOT added (engine-internal state, not LLM-settable).

**Why:** Design decision: one terminal presence state for all permanent exits, set by the LLM.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.models import NpcPresence; print(NpcPresence.DEPARTED.value)"
```
Should print `departed`.

#### Step 1.2 — Add `departed_reason`, `departed_summary`, `departed_turn` to `CompendiumNpcUpdate`

**File:** `ccya/models.py:245-258`

**What:** Add three optional fields to `CompendiumNpcUpdate`:

```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    aliases: list[str] = Field(default_factory=list)
    allegiance: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None   # "present" | "nearby" | "known" | "departed"
    notes: str | None = None
    first_seen_turn: int | None = None
    departed_reason: str | None = None     # NEW
    departed_summary: str | None = None    # NEW
    departed_turn: int | None = None       # NEW — engine sets on first presence:"departed"
```

Also update the comment on `presence` field (line 255) to include `"departed"`.

**Why:** The LLM emits `departed_reason` (short label) and `departed_summary` (prose) alongside `presence: "departed"`. `departed_turn` is engine-set on first detection.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.models import CompendiumNpcUpdate; u = CompendiumNpcUpdate(id='x', presence='departed', departed_reason='killed', departed_summary='died in battle'); print(u.model_dump(exclude_none=True))"
```
Should show all three departed fields.

#### Step 1.3 — Add `nearby_decay_ttl` and `departed_archive_ttl` to `EngineConfig`

**File:** `ccya/engine/config.py` (after line ~166, before `debug_mode`)

**What:** Add two new config fields:

```python
nearby_decay_ttl: int = 2       # turns before nearby → known auto-decay
departed_archive_ttl: int = 3  # turns as "departed" before → archived
```

Place them near the existing TTL/thread fields (after `thread_memory_ttl` / before `debug_mode`).

**Why:** Design decision: both TTLs configurable per-save via config.yaml. Defaults: 2 turns for nearby decay, 3 turns for departed archive window.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); print(c.nearby_decay_ttl, c.departed_archive_ttl)"
```
Should print `2 3`.

### Documentation update

Update `docs/repomap.md`:
- Under `ccya/models.py` entry (line 9), add `DEPARTED` to the `NpcPresence` enum description and note the new fields on `CompendiumNpcUpdate` (`departed_reason`, `departed_summary`, `departed_turn`).
- Under `ccya/engine/config.py` entry (line 12), note the new config fields (`nearby_decay_ttl`, `departed_archive_ttl`).
- Under `ccya/engine/npc_roster.py` entry (line 22), note the archived filter and departed_reason output.
- Under `ccya/state/npcs.py` entry (line 28), note the changed `strip_npcs_notes()` behavior.

No architecture doc changes needed — the lifecycle changes are internal to existing modules and don't alter the 5-call pipeline structure.

### Tests to write or update

None. Tests are temporarily removed during refactor per AGENTS.md.

---

## Implementation — Phase 2: Engine lifecycle steps

### Context files to load

- `ccya/state/delta_builder.py` lines 216-228 (location-change NPC demotion)
- `ccya/state/npcs.py` full file (97-171: apply_npc_scene_management, 85-94: strip_npcs_notes)
- `ccya/engine/turn.py` lines 1229-1240 (post-delta last_seen stamp), lines 1242+ (arc/thread follow-on), lines 51-65 (imports), lines 904-928 (run_turn signature, strip_npcs_notes call)

### Detailed steps

#### Step 2.1 — Change location-change demotion from `known` to `nearby`

**File:** `ccya/state/delta_builder.py:222-228`

**What:** In the `if delta.location_change:` block, change:

```diff
- entry["presence"] = "known"
+ entry["presence"] = "nearby"
+ entry["nearby_since_turn"] = state.get("meta", {}).get("turn", 0) + 1
```

Note: `current_turn` (defined at line 242) is NOT in scope inside the location-change block. Use inline computation. The `+ 1` matches the `turn_no` convention used in `turn.py` so the TTL comparison in the lifecycle steps counts correctly (see Phase 2 Step 2.4).

**Why:** Design decision: preserve proximity on location change. NPCs left behind at a prior location are `nearby`, not `known`. The `nearby_since_turn` clock starts the auto-decay countdown.

**Validation:** Read the modified lines — should show `"nearby"` and `"nearby_since_turn"`. No automated test (tests disabled).

#### Step 2.2 — Update `apply_npc_scene_management()` for departed and nearby

**File:** `ccya/state/npcs.py:apply_npc_scene_management()`, after line ~166 (presence merge block)

**What:** After the existing `if comp_upd.presence is not None:` block (lines 162-167), add:

```python
if comp_upd.presence == "departed":
    if comp_upd.departed_reason is not None:
        entry["departed_reason"] = comp_upd.departed_reason
    if comp_upd.departed_summary is not None:
        entry["departed_summary"] = comp_upd.departed_summary
    if current_turn_no is not None:
        entry["departed_turn"] = entry.get("departed_turn", current_turn_no)
    entry.pop("notes", None)

if comp_upd.presence == "nearby":
    if current_turn_no is not None:
        entry["nearby_since_turn"] = entry.get("nearby_since_turn", current_turn_no)
```

The existing presence block (lines 162-167) handles `presence: "present"` (touch order) and `presence: "known"` (clear notes). The new departed block stores reason/summary, stamps `departed_turn` once, and clears notes. The new nearby block stamps `nearby_since_turn` once (for LLM-set `nearby`; the engine also sets it in delta_builder.py step 2.1).

**Why:** `departed_turn` is set only on first detection (`entry.get("departed_turn", current_turn_no)`) so repeated LLM emissions don't advance the archive clock. `nearby_since_turn` is set only on first transition to nearby.

**Validation:**
```bash
source .venv/bin/activate && python -c "
from ccya.state.npcs import apply_npc_scene_management
from ccya.models import SceneExtractResult, CompendiumNpcUpdate
state = {'compendium': {'npcs': {}}}
result = SceneExtractResult(compendium_npc_update=[
    CompendiumNpcUpdate(id='bob', name='Bob', presence='departed', departed_reason='died', departed_summary='Bob died in battle'),
])
state = apply_npc_scene_management(state, result, current_turn_no=5)
e = state['compendium']['npcs']['bob']
print(e['presence'], e['departed_reason'], e['departed_turn'])
"
```
Should print `departed died 5`. Run again with same data — `departed_turn` should stay `5`.

#### Step 2.3 — Update `strip_npcs_notes()` to skip departed and archived

**File:** `ccya/state/npcs.py:85-94`

**What:** Change the note-clearing loop to skip departed and archived NPCs:

```diff
- if isinstance(entry, dict):
-     entry.pop("notes", None)
+ if isinstance(entry, dict) and entry.get("presence") not in ("departed", "archived"):
+     entry.pop("notes", None)
```

**Why:** Departed and archived NPCs are out of the active lifecycle. No need to clear notes that will never be rendered.

**Validation:** Read the modified function — the condition should exclude `"departed"` and `"archived"`.

#### Step 2.4 — Add nearby-decay and departed-archive steps in `turn.py` post-delta

**File:** `ccya/engine/turn.py`, after line 1240 (`last_seen` stamp block) and before line 1242 (arc director block), OR after line 1293 (end of thread/arc block) and before line 1339 (narrative strip). Place after arc/thread processing to keep all lifecycle steps together.

_Design decision: place lifecycle steps after arc/thread processing (line ~1338) and before `narrative = _strip_fallback(...)` (line 1339). This runs after all delta/state work is complete but before the turn finalizes._

**What:** Add two blocks:

```python
# --- Nearby decay: nearby → known after TTL ---
nearby_ttl = config.nearby_decay_ttl if config else 2
comp = state.get("compendium", {}).get("npcs", {})
for entry in comp.values():
    if not isinstance(entry, dict):
        continue
    if entry.get("presence") == "nearby":
        nearby_since = entry.get("nearby_since_turn")
        if isinstance(nearby_since, int) and turn_no - nearby_since >= nearby_ttl:
            entry["presence"] = "known"

# --- Departed archive: departed → archived after TTL ---
archive_ttl = config.departed_archive_ttl if config else 3
archived_ids = []
for nid, entry in comp.items():
    if not isinstance(entry, dict):
        continue
    if entry.get("presence") == "departed":
        dep_turn = entry.get("departed_turn")
        if isinstance(dep_turn, int) and turn_no - dep_turn >= archive_ttl:
            entry["presence"] = "archived"
            archived_ids.append(nid)
if archived_ids:
    _log.info(
        "archived_departed_npcs ids=%s", sorted(archived_ids),
        extra={"turn": turn_no},
    )
```

Both blocks use `turn_no` (already in scope at line 1230+, computed at line 969 as `state meta turn + 1`).

**Why:** Nearby decay prevents `nearby` bloat — NPCs left at a prior location decay to `known` within 2 turns. Departed archive transitions terminal NPCs out of prompt context after 3 turns.

**Validation:** Can't easily unit test without running a full turn. Verify by reading the code: `presence` is set to `"known"` for expired nearby, `"archived"` for expired departed. Log fires for archived IDs.

### Tests to write or update

None (tests temporarily removed during refactor per AGENTS.md).

---

## Implementation — Phase 3: Roster exclusions and template

### Context files to load

- `ccya/engine/npc_roster.py` full file (74 lines)
- `ccya/prompts/sections/_npc_roster.j2` full file (16 lines)

### Detailed steps

#### Step 3.1 — Pre-filter archived NPCs in `build_npc_roster()`

**File:** `ccya/engine/npc_roster.py:29-37`

**What:** Add an `archived` skip in the main loop, before the name check, and add `departed_reason` to the output dict:

```diff
     for nid, entry in comp.items():
         if not isinstance(entry, dict):
             continue
+        if entry.get("presence") == "archived":
+            continue
         presence = entry.get("presence") or NpcPresence.KNOWN.value
```

Also add `departed_reason` to the output dict built at lines 38-50:

```diff
         seen[nid] = {
             "id": nid,
             "name": name,
             "title": _strip_non_ascii(entry.get("title") or ""),
             "bio": (entry.get("bio") or "").strip() or None,
             "presence": presence,
             "motivation": entry.get("motivation") or None,
             "fear": entry.get("fear") or None,
             "leverage": entry.get("leverage") or None,
             "bond": entry.get("bond") or None,
             "notes": entry.get("notes") or None,
             "last_seen": entry.get("last_seen") or None,
+            "departed_reason": entry.get("departed_reason") or None,
         }
```

**Why:** The template `_npc_roster.j2` references `n.departed_reason` to render the `[DEPARTED] — reason` tag. Without this field in the roster output, Jinja2 silently produces empty strings and the reason never appears.

#### Step 3.2 — Add `DEPARTED` to sort order

**File:** `ccya/engine/npc_roster.py:52-56`

**What:** Add departed sort priority below known:

```python
order = {
    NpcPresence.PRESENT.value: 0,
    NpcPresence.NEARBY.value: 2,
    NpcPresence.KNOWN.value: 3,
    "departed": 5,
}
```

Use the string `"departed"` rather than `NpcPresence.DEPARTED.value` for consistency with the existing pattern (or use the enum — either works since `NpcPresence.DEPARTED.value == "departed"`).

**Why:** Departed NPCs during TTL appear at the bottom of the roster (below known), sorted by name.

**Validation:**
```bash
source .venv/bin/activate && python -c "
from ccya.engine.npc_roster import build_npc_roster
comp = {
    'alive_guy': {'name': 'Alice', 'presence': 'present'},
    'dead_guy': {'name': 'Zed', 'presence': 'departed', 'departed_reason': 'died', 'departed_turn': 1},
    'archived_guy': {'name': 'Old', 'presence': 'archived'},
}
roster = build_npc_roster(comp, max_entries=10)
ids = [e['id'] for e in roster]
print(ids)
assert 'archived_guy' not in ids, 'archived NPC should be excluded'
assert ids[-1] == 'dead_guy', 'departed NPC should be last'
"
```
Should not raise.

#### Step 3.3 — Update `_npc_roster.j2` to show departed reason, hide bio for departed

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Update the comment on line 2 to include departed in the sort order description. Replace the single roster line with conditional rendering:

```diff
- {# npc_roster: list[dict], ordered PRESENT → NEARBY → KNOWN #}
+ {# npc_roster: list[dict], ordered PRESENT → NEARBY → KNOWN → DEPARTED (during TTL) #}
```

```diff
- `{{ n.id }}` | {% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.bio %} — {{ n.bio }}{% endif %}
+ `{{ n.id }}` | {% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.presence == "departed" and n.departed_reason %} — {{ n.departed_reason }}{% endif %}{% if n.bio and n.presence != "departed" %} — {{ n.bio }}{% endif %}
```

**Why:** Departed NPCs show `[DEPARTED] — killed in battle` instead of the full bio. Saves tokens while providing context. Comment updated to reflect the full sort order.

**Validation:** No automated template test. Read the modified template — departed NPCs show reason, non-departed NPCs show bio as before.

### Tests to write or update

None (tests temporarily removed).

---

## Implementation — Phase 4: Prompt updates

### Context files to load

- `ccya/prompts/extract_scene_system.j2` full file (122 lines)
- `ccya/prompts/storytell_system.j2` full file (80 lines)
- `ccya/prompts/generate_seed_system.j2` lines 65-94 (NPC rules section)

### Detailed steps

#### Step 4.1 — Update `extract_scene_system.j2` JSON schema presence field

**File:** `ccya/prompts/extract_scene_system.j2:13`

**What:** Change the presence field in the JSON schema example from `"present|known"` to `"present|nearby|known|departed"`.

**Why:** The LLM needs to know all valid presence values.

**Validation:** Read the modified line — schema shows all four values.

#### Step 4.2 — Update `extract_scene_system.j2` NPC ENTER/EXIT rule

**File:** `ccya/prompts/extract_scene_system.j2:80-84`

**What:** Replace the single exit rule with three rules:

```diff
- Emit `compendium_npc_update { presence: "known" }` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
+ Emit `compendium_npc_update { presence: "known" }` for every named NPC who narration indicates has left, fled, fainted, or been removed from the scene.
+ Emit `compendium_npc_update { presence: "departed", departed_reason: "<short label>", departed_summary: "<1-2 sentence prose>" }` for every named NPC who narration indicates is permanently gone — dead, sailed away forever, comatose, imprisoned for life, ascended, or otherwise unreachable. This NPC will be archived after a few turns. The `departed_reason` is a short label (e.g. "killed in battle", "sailed to sea"). The `departed_summary` is 1-2 sentences describing what happened, shown in the compendium UI.
+ Emit `compendium_npc_update { presence: "nearby" }` for NPCs described as being just outside, in the next room, watching from the shadows, or otherwise proximate but not in the immediate scene.
```

Remove "died" from the `known` list since death is now `departed`.

**Why:** Design decision: give LLM vocabulary for three distinct exit types (temporary, permanent, proximate).

**Validation:** Read the modified section — three exit rules instead of one. Death removed from `known` list.

#### Step 4.3 — Add re-promotion rule for engine-demoted NPCs

**File:** `ccya/prompts/extract_scene_system.j2`, in the "How to use compendium_npc_update" section after line 50

**What:** Add a new bullet:

```diff
+ - **NPC re-enters scene after location change:** If an NPC was demoted to `"nearby"` by an engine location change but the narration indicates they followed the player, set `presence: "present"` — do NOT create a new compendium entry. Re-promote the existing NPC.
```

**Why:** Prevents duplicate NPC entries on location change. The existing dedup pre-check (lines 103-109) already teaches `known → present` re-promotion; this extends the same pattern to `nearby → present`.

**Validation:** Read the modified section — new bullet is present.

#### Step 4.4 — Add departed field rules to `extract_scene_system.j2`

**File:** `ccya/prompts/extract_scene_system.j2`, in the "Field rules" section after line 41

**What:** Add two new field rules:

```
`departed_reason`: Required when `presence` is `"departed"`. Short label describing the departure. Examples: "killed in battle", "sailed away", "imprisoned for life".
`departed_summary`: Required when `presence` is `"departed"`. 1-2 sentences describing what happened, for the compendium and UI display.
```

**Why:** LLM needs explicit guidance on what values to emit for these fields.

**Validation:** Read the modified section — two new field rules present.

#### Step 4.5 — Update `extract_scene_system.j2` presence examples

**File:** `ccya/prompts/extract_scene_system.j2:40` and `ccya/prompts/extract_scene_system.j2:29-42`

**What:** In the Universal NPC Channel schema example (line 29-42), update the `presence` field comment from `"present|known"` to `"present|nearby|known|departed"` and add `departed_reason` and `departed_summary` to the example block.

**Why:** The schema example should match the full set of valid values.

**Validation:** Read the modified example — all four presence values shown, departed fields listed.

#### Step 4.6 — Update `storytell_system.j2` with departed NPC guidance

**File:** `ccya/prompts/storytell_system.j2`

**What:** Add a brief note at the end of the system prompt:

```
- Departed NPCs (marked with `[DEPARTED]`) are permanently gone and will be archived after a few turns. Reference them from narrative history only — do not create threads or actions involving departed characters.
```

**Why:** Prevents the storyteller from creating new threads or storylines involving permanently-departed NPCs.

**Validation:** Read the modified file — new instruction present.

#### Step 4.7 — Update `generate_seed_system.j2` presence schema

**File:** `ccya/prompts/generate_seed_system.j2:77-78`

**What:** Update the NPC rules to include `"nearby"` and `"departed"` alongside `"present"` and `"known"`:

```diff
- - **~2 present** (`presence: "present"`) — in the opening scene
- - **2–3 known** (`presence: "known"`) — exist in the world
+ - **~2 present** (`presence: "present"`) — in the opening scene
+ - **1–2 nearby** (`presence: "nearby"`) — just outside, in the next room, proximate
+ - **2–3 known** (`presence: "known"`) — exist in the world, not in the scene
+ - **0–1 departed** (`presence: "departed"`) — permanently gone, referenced in bio/world state
```

Adjust the total count guidance (line 76 says 4-5 total — now 3-6, add a note about flexibility).

**Why:** Seed generator should produce complete NPC spreads including the new presence states.

**Validation:** Read the modified file — all four presence values represented.

### Tests to write or update

None (tests temporarily removed).
