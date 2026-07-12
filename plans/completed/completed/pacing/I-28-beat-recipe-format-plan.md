# I-28: Beats — recipe format with NPC personality priority

**Depends on:** None
**Status:** completed
**Ticket:** I-28
**Design Reference:** `roadmap/improvements/I-28-beat-recipe-format.md`

## Purpose

Refactor beat generation to use a structured recipe format (bracket tags instead of prose), enforce NPC-first agency in world model output, and fix the `npcs` data flow gap. Rename pacing buckets and drop the unused `hazard` type.

---

## Phase 01: Model + ruling fix — formalize `npcs`

**Depends on:** None
**Files:** `ccya/models/extraction.py`, `ccya/engine/ruling.py`

### Task 01-01: Make `npcs` required on `GMBeat` model

**File:** `ccya/models/extraction.py`
**Line:** 207

**What:**
- Change `npcs: list[str] = Field(default_factory=list)` to `npcs: list[str] = Field(default_factory=list)` — keep the default factory (LLM may omit it), but add a `model_validator` that rejects beats with empty `npcs` unless the beat is purely environmental.
- The validator should: if `npcs` is empty and `effect` does not contain `[environment]`, raise a validation error. This forces the world model to populate `npcs` for NPC-driven beats.

**Why:** Decision #5. Making `npcs` part of the Pydantic validation contract means the world model LLM is constrained to populate it. Currently `npcs` is optional and defaults to empty.

**Interface contract — validator addition:**
```python
@model_validator(mode="after")
def _validate_npcs(self) -> "GMBeat":
    if not self.npcs and "[environment]" not in (self.effect or ""):
        raise ValueError("npcs is required for NPC-driven beats")
    return self
```

**Validation:**
- `GMBeat(type="pressure", effect="[npcs: petty] [highlight: fear]", npcs=["petty"])` — passes
- `GMBeat(type="pressure", effect="[thread_pressure: patrols]", npcs=[])` — fails validation
- `GMBeat(type="pressure", effect="[environment] The wind howls", npcs=[])` — passes (environmental)

### Task 01-02: Pass `npcs` through ruling to `pending_gm_beat`

**File:** `ccya/engine/ruling.py`
**Line:** 212

**What:**
- Change line 212 from:
  ```python
  state = state.model_copy(update={"meta": state.meta.model_copy(update={"pending_gm_beat": {"type": beat["type"], "effect": beat.get("effect", "")}})})
  ```
  to:
  ```python
  state = state.model_copy(update={"meta": state.meta.model_copy(update={"pending_gm_beat": {"type": beat["type"], "effect": beat.get("effect", ""), "npcs": beat.get("npcs", [])}})})
  ```

**Why:** Decision #6. Currently `ruling.py:212` drops `npcs` when constructing `pending_gm_beat`. The narrator never sees which NPCs to feature.

**Validation:**
- `rg -n "pending_gm_beat" ccya/engine/ruling.py` — line 212 now includes `"npcs": beat.get("npcs", [])`
- No other locations construct `pending_gm_beat` (validated: only line 212 and line 214 which sets it to `None`)

### Task 01-03: Update world.py beat construction to preserve `npcs`

**File:** `ccya/engine/world.py`
**Line:** 188

**What:**
- Line 188 is already `valid_beats.append({"type": beat.type, "effect": beat.effect, "npcs": entry.get("npcs", [])})` — no change needed.
- Verify no other code path strips `npcs` from valid beats.

**Why:** Sanity check. Confirm `npcs` is preserved through world.py.

**Validation:**
- `rg -n "npcs" ccya/engine/world.py` — line 188 is the only place `npcs` is extracted from LLM response
- No other code path strips `npcs`

---

## Phase 02: Prompt changes — recipe format + NPC priority

**Depends on:** None
**Files:** `ccya/prompts/world_system.j2`, `ccya/prompts/narrate_system.j2`, `ccya/prompts/narrate_user.j2`

### Task 02-01: Rewrite `world_system.j2` — recipe format, NPC priority, thread ban

**File:** `ccya/prompts/world_system.j2`
**Lines:** 1-54

**What:**
Replace the current prompt with recipe-format instructions. Key changes:

1. **Schema section (lines 3-11):** Update JSON schema example to show recipe format:
   ```json
   [
     {"type": "pressure", "effect": "[npcs: petty] [highlight: fear] [thread: faction_patrols]", "npcs": ["petty"]}
   ]
   ```

2. **Generation rules (lines 13-35):** Restructure priority order:
   - **Primary (equal):** NPC+NPC (cross-NPC blending), NPC+thread (one NPC + active thread)
   - **Fallback:** Single NPC on psychological field
   - **Last resort:** Thread+thread (rare), Environmental (only when no NPCs exist)

3. **NPC-only beats rule:** Threads may only be touched in combination with an NPC. No single-thread-only or thread+thread beats unless no NPCs with psychological fields exist.

4. **5-turn thread ban:** Explicit ban on re-raising the same thread within a 5-turn window. Hard rule.

5. **`effect` format (line 21):** Replace prose examples with recipe examples:
   - `[npcs: petty] [highlight: fear] "The guard captain's paranoia spikes as rumors of the patrol reach her"`
   - `[npcs: petty, silas] [blend: motivation vs fear] "Silas's need for the ledger collides with the captain's terror of exposure"`
   - `[npcs: petty] [thread: faction_patrols] "The patrol captain pushes her scouts deeper into the thistle fields"`
   - `[environment] "The ventilation system hums with an irregular rhythm"`

6. **`npcs` emphasis (line 30):** Strengthen: "You MUST populate `npcs` with actual NPC IDs. If `npcs` is empty, you skipped the NPC roster — fix your beat."

7. **Diversity (lines 36-47):** Keep existing diversity rules. Add 5-turn thread ban.

8. **Roll band guidance (lines 49-53):** Keep as-is.

**Why:** Decision #1 (recipe format), Decision #2 (NPC priority), Decision #3 (NPC-only beats), Decision #4 (5-turn thread ban).

**Validation:**
- `ev.py prompt-eval dump <save-dir> --turn N --stream world` — world prompt renders recipe examples
- No prose scene descriptions in `effect` examples
- NPC priority order is explicit and ordered
- 5-turn thread ban is stated as a hard rule

### Task 02-02: Update `narrate_system.j2` — bracket syntax explanation

**File:** `ccya/prompts/narrate_system.j2`
**Lines:** (add after line 1, before "Player input is truth")

**What:**
Add a new section explaining recipe-format bracket syntax. Insert after line 1:

```
## Beat recipe syntax

When `pending_gm_beat` is present, its `effect` field uses bracket tags — not prose. Interpret them as narrative guidance:

- `[npcs: name1, name2]` — feature these NPCs in the narration. Use their names.
- `[highlight: motivation|fear|leverage|tie]` — exercise this psychological aspect. Let it drive NPC behavior.
- `[thread: thread_id]` — this is the underlying pressure. Show it through NPC action or world state.
- `[blend: field1 vs field2]` — two NPCs (or an NPC and a thread) collide. Write the tension.
- `[environment]` — no NPCs. Describe the world reacting.

The narrator infers meaning from context. Do not translate tags literally. Do not write "the npcs field says..." — just write the scene.
```

**Why:** Decision #9. Narrator needs to understand bracket syntax. No prose translation — just interpretation.

**Validation:**
- `ev.py prompt-eval dump <save-dir> --turn N --stream narrate` — narrate prompt includes bracket syntax section
- Narrator interprets `[npcs: petty]` as "feature Petty" not "the text says npcs: petty"

### Task 02-03: Update `narrate_user.j2` — recipe beat rendering

**File:** `ccya/prompts/narrate_user.j2`
**Line:** 91-93

**What:**
Change line 93 from:
```
**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — {{ pending_beat.effect }}. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```
to:
```
**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — {{ pending_beat.effect }}
```
Remove "Use this as creative guidance..." and "Do not recite beat metadata..." — the system prompt already handles this. The recipe format is self-explanatory.

**Why:** Cleaner rendering. The recipe tags ARE the creative guidance. No need for meta-instructions.

**Validation:**
- `ev.py prompt-eval dump <save-dir> --turn N --stream narrate` — beat line is clean: `**Beat:** PRESSURE — [npcs: petty] [highlight: fear]`
- No "creative guidance" text

---

## Phase 03: Pacing bucket rename + drop hazard

**Depends on:** None
**Files:** `ccya/engine/_pacing.py`

### Task 03-01: Rename buckets and drop hazard

**File:** `ccya/engine/_pacing.py`
**Lines:** 21-33

**What:**
1. Rename `BEAT_BUCKETS` (line 21-25):
   ```python
   BEAT_BUCKETS: dict[str, list[str]] = {
       "tension":  ["pressure", "complication", "escalation", "setback"],
       "discovery": ["revelation", "twist", "callback"],
       "respite":  ["opportunity", "breathing_room"],
   }
   ```
   Remove `"hazard"` from all buckets. Remove `"situation"` and `"relief"` bucket names.

2. Update `BEAT_PHASE_MAP` (line 27-33):
   - Remove `"hazard"` from all phase lists
   - No other changes — allowed types per phase stay the same (just without hazard)

3. Update `derive_allowed_beat_types` (line 48-50):
   - Remove `"hazard"` from the `extra` list

**Why:** Decision #9 (drop hazard). Decision #10 (bucket rename). `hazard` is essentially never chosen. Bucket names renamed to narrative-centric terms.

**Validation:**
- `rg -n "hazard" ccya/engine/_pacing.py` — no results
- `rg -n "BEAT_BUCKETS" ccya/engine/_pacing.py` — buckets are tension/discovery/respite
- `rg -n "situation\|relief" ccya/engine/_pacing.py` — no results (except in comments if any)

### Task 03-02: Update convergence scoring reference

**File:** `ccya/engine/_pacing.py`
**Line:** 96

**What:**
- Line 96: `pressure_types = set(BEAT_BUCKETS["pressure"])` → `pressure_types = set(BEAT_BUCKETS["tension"])`
- Update comment on line 95 if present.

**Why:** Convergence scoring uses `BEAT_BUCKETS["pressure"]` to count tension beats. Rename to `"tension"`.

**Validation:**
- `rg -n "BEAT_BUCKETS\[.pressure.\]" ccya/engine/_pacing.py` — no results
- `rg -n "BEAT_BUCKETS\[.tension.\]" ccya/engine/_pacing.py` — line 96

### Task 03-03: Update EV checker convergence reference

**File:** `ccya/ev/checkers/pacing_convergence.py`
**Line:** 266

**What:**
- Line 266: `pressure_types = set(BEAT_BUCKETS["pressure"])` → `pressure_types = set(BEAT_BUCKETS["tension"])`

**Why:** EV checker also uses `BEAT_BUCKETS["pressure"]` for convergence validation. Must match engine.

**Validation:**
- `rg -n "BEAT_BUCKETS\[.pressure.\]" ccya/ev/checkers/pacing_convergence.py` — no results
- `rg -n "BEAT_BUCKETS\[.tension.\]" ccya/ev/checkers/pacing_convergence.py` — line 266

### Task 03-04: Delete dead `PRESSURE_BEAT_TYPES` from turn.py

**File:** `ccya/engine/turn.py`
**Line:** 60

**What:**
- Delete line 60: `PRESSURE_BEAT_TYPES = ("pressure", "escalation", "complication", "setback")`

**Why:** Dead code. No callers in engine code. EV checkers no longer import it (cross-module-contracts.md line 5 is stale). Removing eliminates confusion with the renamed "tension" bucket.

**Validation:**
- `rg -n "PRESSURE_BEAT_TYPES" ccya/engine/turn.py` — no results
- `rg -n "PRESSURE_BEAT_TYPES" ccya/ev/` — no results (already none)

---

## Phase 04: Arch doc updates

**Depends on:** Phase 01, Phase 02, Phase 03
**Files:** `docs/architecture/pacing-systems.md`, `docs/architecture/state-models.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/cross-module-contracts.md`, `docs/repomap.md`

### Task 04-01: Update `pacing-systems.md`

**File:** `docs/architecture/pacing-systems.md`
**Lines:** 76-89 (beat types table), 22 (bucket references), 391 (convergence score)

**What:**
1. Update beat types table (lines 76-89):
   - Remove `hazard` row
   - Update bucket column: pressure/situation/relief → tension/discovery/respite
   - Update `setback` description: "PC loses ground" (stays in tension)
   - 8 types total (was 9)

2. Update convergence score description (line 53):
   - "beat streak: ≥60% tension beats" (was "pressure beats")

3. Update any other references to old bucket names.

**Why:** Docs must reflect current state. Per AGENTS.md: "Stale docs are bugs."

**Validation:**
- `rg -n "situation\|relief\|pressure.*bucket" docs/architecture/pacing-systems.md` — no results (except "pressure" as beat type which is correct)
- Beat types table shows 8 types with correct buckets

### Task 04-02: Update `state-models.md`

**File:** `docs/architecture/state-models.md`
**Lines:** 85-90 (GMBeat), 111-114 (GMBeat non-obvious behavior)

**What:**
1. Update GMBeat model definition (line 85-90):
   ```
   GMBeat
     type: complication | revelation | opportunity | breathing_room |
           pressure | twist | setback | escalation | callback | None
     effect: str                       # recipe format: bracket tags
     npcs: list[str]                   # required for NPC-driven beats (validated)
   ```

2. Update non-obvious behavior (lines 111-114):
   - Add: "npcs is validated — empty npcs rejected unless effect contains `[environment]`"

**Why:** Reflects model changes.

**Validation:**
- `rg -n "GMBeat" docs/architecture/state-models.md` — npcs field documented as required+validated
- No mention of `npc_id`, `driver`, `beat_expires_turn` (already removed)

### Task 04-03: Update `OVERVIEW.md`

**File:** `docs/architecture/OVERVIEW.md`
**Lines:** 68 (World step), 151-153 (GMBeat)

**What:**
1. Update World step description (line 68):
   - "validates each candidate via `GMBeat(**candidate)` (npcs required for NPC-driven beats)"
   - "strips to `{type, effect, npcs}`"

2. Update GMBeat section (line 151-153):
   - "Fields: `type` (Literal), `effect` (str, recipe format), `npcs` (list[str], required for NPC-driven beats)"

**Why:** Reflects model and format changes.

**Validation:**
- `rg -n "GMBeat" docs/architecture/OVERVIEW.md` — npcs field documented
- No mention of `npc_id`, `driver`, `beat_expires_turn`

### Task 04-04: Update `cross-module-contracts.md`

**File:** `docs/architecture/cross-module-contracts.md`
**Lines:** 5 (PRESSURE_BEAT_TYPES), 44 (BEAT_BUCKETS description)

**What:**
1. Line 5: Remove `PRESSURE_BEAT_TYPES` from the EV checker imports description. The checker library no longer imports it (dead code).
2. Line 44: `BEAT_BUCKETS` groups beat types into `pressure/situation/relief` functional buckets → rename to `tension/discovery/respite`
3. Line 44: Remove `"hazard"` from the list

**Why:** Reflects code changes. Per AGENTS.md: "Stale docs are bugs."

**Validation:**
- `rg -n "PRESSURE_BEAT_TYPES" docs/architecture/cross-module-contracts.md` — no results
- `rg -n "BEAT_BUCKETS" docs/architecture/cross-module-contracts.md` — buckets are tension/discovery/respite
- No mention of "situation" or "relief"

### Task 04-05: Update `repomap.md`

**File:** `docs/repomap.md`
**Lines:** 16 (_pacing.py), 21 (ruling.py), 132 (extraction routing)

**What:**
1. Line 16: Update `_pacing.py` description — "BEAT_BUCKETS (tension/discovery/respite), BEAT_PHASE_MAP (no hazard)"
2. Line 21: Update `ruling.py` — "passes npcs through to pending_gm_beat"
3. Line 132: Update extraction routing — "GMBeat output includes npcs (validated required for NPC-driven beats)"
4. Line 16: Remove `PRESSURE_BEAT_TYPES` from turn.py description (dead code deleted)

**Why:** Reflects code changes.

**Validation:**
- `rg -n "BEAT_BUCKETS\|npcs\|hazard\|PRESSURE_BEAT_TYPES" docs/repomap.md` — all updated

---

## Phase verification

Run `make check` — lint + typecheck must pass.

Run `ev.py prompt-eval dump <save-dir> --turn N --stream world` — world prompt renders recipe format.

Run `ev.py prompt-eval dump <save-dir> --turn N --stream narrate` — narrate prompt includes bracket syntax.

Run `ev.py play --llm --turns 5` — verify beats have `npcs` populated, narrator interprets recipe format.
