# I-11 Plan — World step: read NPC profiles from compendium, remove candidate_npcs

**Design Reference:** `roadmap/improvements/I-11-world-step-read-npc-profiles-directly-from-compendium.md`
**Ticket:** `I-11`
**Status:** completed (commit `6bfea4f`)

## Phase Summary

Six phases ordered by dependency: models first (Phase 01), then extraction pipeline removal (Phase 02), then World rewrite (Phase 03), then prompts (Phase 04), then server/tools cleanup (Phase 05), then docs (Phase 06). Each phase is independently executable and testable. The core changes are: remove `candidate_npcs` from the entire extraction pipeline, rewrite World to read NPC profiles directly from the compendium via `build_npc_roster()`, and add `npcs` field to beat output.

---

## Phase 01: Models

**File:** `ccya/models/extraction.py`

**What:**
- Remove `candidate_npcs: list[dict[str, Any]]` field and its docstring from `SceneExtractResult` (lines 122-125).
- Add `npcs: list[str] = Field(default_factory=list)` to `GMBeat` model (after `effect` field, line 211).

```python
class GMBeat(BaseModel):
    type: Literal[...] | None = None
    effect: str = ""
    npcs: list[str] = Field(default_factory=list)
```

**Why:** Foundation change. Removing `candidate_npcs` from `SceneExtractResult` means the scene extractor LLM no longer needs to produce it. Adding `npcs` to `GMBeat` means World can output which NPCs drive each beat, and the field flows through validation naturally.

**Validation:** `SceneExtractResult` no longer has a `candidate_npcs` attribute. `GMBeat` accepts an optional `npcs` field. Any code referencing `scene_result.candidate_npcs` will fail at import/runtime — catch in Phase 02.

---

## Phase 02: Engine — Extraction

**Files:** `ccya/engine/extraction/context.py`, `ccya/engine/extraction/pipeline.py`, `ccya/engine/turn.py`

### context.py

**What:**
- Remove `candidate_npcs: list[dict[str, Any]]` field from `_ExtractionContext` dataclass (lines 28-29).
- Remove `candidate_npcs=_filter_unnamed_personality(...)` from `_build_extraction_context()` return (line 74).
- Remove `_filter_unnamed_personality()` function (lines 92-118).
- Remove `_is_named()` function (lines 80-89) — it's unused after this removal.

### pipeline.py

**What:**
- No changes needed. Pipeline yields `scene_result` but `candidate_npcs` was only ever consumed by World (which we're rewriting). The pipeline itself doesn't reference `candidate_npcs`.

### turn.py

**What:**
- Remove `candidate_npcs` from world start log line (line 561): change from `candidate_npcs=%d` to `npc_roster=%d` or just remove the count.

**Why:** `candidate_npcs` is removed from the extraction pipeline. Context no longer carries it, the filter function is dead code, and turn.py log no longer references it.

**Validation:** `_ExtractionContext` has no `candidate_npcs` attribute. `_filter_unnamed_personality` and `_is_named` (in context.py) are removed. `turn.py` log line no longer references `candidate_npcs`.

---

## Phase 03: Engine — World

**File:** `ccya/engine/world.py`

**What:**
- Remove `candidate_npcs` extraction from `scene_result` (lines 40-42).
- Add import for `build_npc_roster` from `ccya.engine.npc_roster`.
- Add import for `ARCHETYPES` from `ccya.personality`.
- After extracting `arc`, `recent_beats`, `scene_phase`, and `allowed_beat_types`, add NPC roster building:
  ```python
  comp = state.get("compendium", {}).get("npcs", {})
  npc_roster = build_npc_roster(comp, turn_no=turn_no, personality_registry=ARCHETYPES)
  # Filter to present/nearby in Python
  npc_roster = [n for n in npc_roster if n.get("presence") in ("present", "nearby")]
  ```
- Replace `"candidate_npcs": candidate_npcs` in `_render()` call (line 67) with `"npc_roster": npc_roster`.
- Remove `candidate_npcs` from debug log (line 83): change to `npc_roster=%d`.
- In candidate validation loop (lines 131-143): after GMBeat validation, extract `npcs` from the raw entry and add to the validated beat dict:
  ```python
  valid_beats.append({
      "type": beat.type,
      "effect": beat.effect,
      "npcs": entry.get("npcs", []),
  })
  ```

**Why:** World now reads NPC profiles directly from the compendium instead of relying on the scene extractor's `candidate_npcs`. This eliminates the ~20% failure rate from the scene extractor and gives World full psychological profiles (motivation, fear, leverage, tie) for cross-NPC and single-NPC beat blending.

**Validation:** `_run_world_step` no longer references `candidate_npcs`. It calls `build_npc_roster()` and filters for `presence in ["present", "nearby"]`. Beat candidates include `npcs` field.

---

## Phase 04: Prompts

### extract_scene_system.j2

**What:**
- Remove `"candidate_npcs": [...]` from output schema JSON (line 23).
- Remove entire "Beat candidate selection" section (lines 27-64).
- Remove all guidance about selecting/describing candidates, psychological state format by type, grounding rule, examples, pre-check, and DO NOT list.

**Why:** Scene extractor no longer produces `candidate_npcs`. Removing this section eliminates ~40 lines of prompt that the LLM will no longer follow.

**Validation:** `extract_scene_system.j2` no longer references `candidate_npcs` or beat candidate selection.

### world_system.j2

**What:**
- Update blend instruction (line 15): replace "combine 1-2 psychological hints from `candidate_npcs`" with beat priority order:
  1. **Cross-NPC blending** — put NPC A's motivation against NPC B's fear, or NPC A's leverage against NPC B's tie.
  2. **NPC/Thread/Arc blending** — combine one NPC's psychological profile with an active thread or arc goal.
  3. **Single-NPC depth** — take one NPC's full profile (motivation, fear, leverage, tie) and exercise all four simultaneously in a single beat.
  4. **Environmental** — only when no NPCs are present or active.
- Update action rule (line 16): replace "candidate_npcs" reference with "npc_roster".
- Update NPC preference (line 20): replace "no candidate_npcs are available" with "no present/nearby NPCs exist".
- Update blend example to show cross-NPC conflict:
  ```
  Example (cross-NPC): "Anthony wants to protect his sister" + "David fears exposure" → Anthony offers to shield David from scrutiny in exchange for silence.
  Example (NPC/Thread): "Anthony wants to protect his sister" + [URGENT] Sister's debt → Anthony negotiates a dangerous deal to settle the debt.
  Example (single-NPC): "Anthony wants to protect his sister, fears being exposed, holds leverage over David, and owes him his life" → Anthony negotiates a dangerous deal to secure his sister's safety while settling his debt to David.
  ```

**Why:** World now receives full NPC profiles instead of flat hints. Beat priority order ensures cross-NPC conflict is attempted first, with single-NPC depth and environmental as fallbacks.

**Validation:** `world_system.j2` no longer references `candidate_npcs`. Instructions reference `npc_roster` and full psychological profiles (motivation, fear, leverage, tie). Beat priority order is explicit.

### world_user.j2

**What:**
- Replace the entire `candidate_npcs` section (lines 1-8) with an `npc_roster` section:
  ```jinja2
  ## Present NPCs
  {% if npc_roster %}
  {% for n in npc_roster %}
  ### {{ n.name }}{% if n.title %} ({{ n.title }}){% endif %}
  - bio: {{ n.bio or "—" }}
  {% if n.motivation %}- motivation: {{ n.motivation }}{% endif %}
  {% if n.fear %}- fear: {{ n.fear }}{% endif %}
  {% if n.leverage %}- leverage: {{ n.leverage }}{% endif %}
  {% if n.tie %}- tie: {{ n.tie }}{% endif %}
  {% if n.personality_label %}- personality: {{ n.personality_label }}{% endif %}
  {% endfor %}
  {% else %}
  No present or nearby NPCs. Generate beats from narration + threads alone.
  {% endif %}
  ```

**Why:** World receives grouped NPC profiles by ID instead of a flat list of hints. Each NPC's full psychological profile is rendered.

**Validation:** `world_user.j2` no longer references `candidate_npcs`. Renders `npc_roster` grouped by NPC with all psychological fields.

### ruling_user.j2

**What:**
- After `scene_phase` rendering (around line 31), add `allowed_beat_types` rendering:
  ```jinja2
  {% if allowed_beat_types %}
  ## Allowed Beat Types (this phase)
  {{ allowed_beat_types | join(", ") }}
  {% endif %}
  ```
- Update beat candidates display to show `npcs` field:
  ```jinja2
  {% for b in beat_candidates %}{{ loop.index0 }}. **{{ b.type }}** — {{ b.effect }}{% if b.get("npcs") %} (NPCs: {{ b.npcs | join(", ") }}){% endif %}
  {% endfor %}
  ```

**Why:** Ruling needs to know which beat types are allowed in the current phase to make informed beat selection decisions. Showing `npcs` in the ruling prompt helps the LLM understand which NPCs are involved in each beat.

**Validation:** `ruling_user.j2` renders `allowed_beat_types` when present. Beat candidates display includes `npcs` field.

---

## Phase 05: Server + Tools

### tv.py

**File:** `ccya/server/tv.py`

**What:**
- Remove the "Scene candidate_npcs" section (lines 244-261).

**Why:** Turn viewer no longer displays `candidate_npcs` — it's been removed from the pipeline.

**Validation:** `tv.py` no references `candidate_npcs`.

### state_tools.py

**File:** `ccya/ev/state_tools.py`

**What:**
- Remove `"candidate_npcs": []` from beat_entry defaults (line 346).
- Remove `candidate_npcs` extraction from scene output (lines 366-371).
- Remove `candidate_npcs` from pipeline view section (lines 471-489): replace the "Pipeline: candidate_npcs → world candidates → ruling" section with "Pipeline: world candidates → ruling" and remove the `cands`/`candidate_npcs` display.

**Why:** EV state tools no longer display `candidate_npcs`.

**Validation:** `state_tools.py` no references `candidate_npcs`.

### prompt_context.py

**File:** `ccya/ev/prompt_context.py`

**What:**
- Remove `candidate_npcs` extraction from scene event (lines 284-286).
- Replace `"candidate_npcs": candidate_npcs` in return dict (line 302) with `"npc_roster": npc_roster`:
  ```python
  comp = prev_snap.get("compendium", {}).get("npcs", {})
  from ccya.engine.npc_roster import build_npc_roster
  from ccya.personality import ARCHETYPES
  npc_roster = build_npc_roster(comp, turn_no=turn_no, personality_registry=ARCHETYPES)
  npc_roster = [n for n in npc_roster if n.get("presence") in ("present", "nearby")]
  ```

**Why:** Eval prompt context for World step now provides NPC profiles from compendium instead of scene extraction output.

**Validation:** `prompt_context.py` no references `candidate_npcs`. Provides `npc_roster` for World stream.

---

## Phase 06: Docs

### step2a-scene.md

**File:** `docs/architecture/step2a-scene.md`

**What:**
- Remove `candidate_npcs` from the flowchart output section (line 25).
- Remove "Beat candidate selection" section (lines 32-36).
- Update "Key forward dependency" section to remove `candidate_npcs` reference.

### step2d-world.md

**File:** `docs/architecture/step2d-world.md`

**What:**
- Update flowchart inputs: replace `candidate_npcs` with `npc_roster` (from compendium).
- Update inputs table: replace `candidate_npcs | scene_result.candidate_npcs (Scene Extract 2a)` with `npc_roster | build_npc_roster() from compendium`.
- Update beat output description to mention `npcs` field.
- Update beat priority order in text (cross-NPC → NPC/Thread → Single-NPC → Environmental).

### repomap.md

**File:** `docs/repomap.md`

**What:**
- Update `ccya/engine/world.py` entry: reflect new input source (compendium via `build_npc_roster()` instead of `candidate_npcs` from scene).
- Update `ccya/models/extraction.py` entry: reflect `candidate_npcs` removal from `SceneExtractResult` and `npcs` addition to `GMBeat`.
- Update cross-module contracts summary: remove `candidate_npcs` from extraction routing description.

### cross-pipeline.md (if applicable)

**What:** Update any cross-pipeline data flow docs that reference `candidate_npcs`.

**Why:** Keep architecture docs accurate. Stale docs are bugs per AGENTS.md.

**Validation:** All architecture docs no longer reference `candidate_npcs`. World step inputs reflect compendium-based NPC profiles. GMBeat output includes `npcs` field.

---

## Dependency Graph

```
Phase 01 (Models)
  └─> Phase 02 (Extraction) ──> Phase 03 (World) ──> Phase 04 (Prompts) ──> Phase 05 (Server/Tools) ──> Phase 06 (Docs)
```

- Phase 01 must complete before 02 (model field removal).
- Phase 02 must complete before 03 (no more `candidate_npcs` in pipeline).
- Phase 03 must complete before 04 (World prompt changes depend on new input shape).
- Phase 04 must complete before 05 (eval tools render World prompts).
- Phase 06 can run anytime after 01-05 but is last by convention.
