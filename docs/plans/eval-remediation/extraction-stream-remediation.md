# Extraction Stream Remediation

## Status
`open`

## Part of
Standalone

## Dependencies
- Completed plans: `scene-progress-fixes.md`, `eval-remediation-may10/02-extraction-quality.md`, `eval-remediation-may10/01-eval-remediation-may10.md`
- None of the phases depend on each other except Phase 1 must precede Phase 2 (Phase 2 reads `_rules_messages` which Phase 1 modifies)

## Conflicts and overlap
- Phase 1 modifies `_rules_messages()` and `rules_user.j2` — no overlap with other phases.
- Phase 2 modifies `_extract_scene_messages()`, `_extract_state_messages()`, `_extract_progress_messages()` and their user templates — no overlap with other phases.
- Phase 3 modifies `compact_system.j2` — no overlap.
- Phase 4 modifies `models.py` and `narrate_system.j2` — no overlap.
- No file overlap between phases. Safe to execute sequentially.

## Objective
Remediate four categories of issues identified in the May 10 eval run and user testing: (1) insufficient NPC context in rules and narration prompts, (2) bloated/incorrect context in extraction stream prompts, (3) compactor sanitization failure, and (4) minor output/format issues. Each phase is independently testable and targets a coherent set of concerns.

## Non-goals
- No changes to the turn pipeline orchestration in `turn.py` (only prompt context and templates).
- No changes to Pydantic model schemas (no new fields on `StateDelta`, `SceneExtractResult`, etc.).
- No changes to the auto-checker or eval harness.
- No changes to the frontend rendering logic.
- No changes to the compactor's bullet generation logic (only the sanitization directives).
- No changes to `run_turn_retry()` — the user is reworking that system separately.

## Affected files

| File | Change type | Summary |
|---|---|---|
| `ccya/engine/rules.py` | modify | Add `present_npcs` param to `_rules_messages()`, inject NPC context block |
| `ccya/prompts/rules_user.j2` | modify | Add `## present_npcs` block with notes |
| `ccya/engine/narrate.py` | modify | Add `compendium_bios` param to `_narrate_messages()`, inject into user context |
| `ccya/prompts/narrate_system.j2` | modify | Add compendium bio injection rule + null-omission output discipline rule |
| `ccya/engine/extraction.py` | modify | Remove `active_domains`, `rules_outcome` from scene/progress message builders; remove `active_domains`, `rules_outcome`, `stakes`, `band`, `scene_result` from state message builders; remove dead `band_examples` block from state template; restructure progress user prompt |
| `ccya/prompts/extract_progress_user.j2` | modify | Remove `active_domains`, `rules_outcome` blocks; relabel `prior_turn_narration` → `last_turn_narration`; move above current turn; fix `quest_ages` field name (`q.age` → `q.stalled_turns`) |
| `ccya/prompts/extract_state_user.j2` | modify | Remove `active_domains`, `scene_result`, `roll_context`, `rules_stakes_hint`, `band_examples` blocks |
| `ccya/prompts/extract_scene_user.j2` | modify | Remove `rules_outcome` and `active_domains` blocks |
| `ccya/prompts/compact_system.j2` | modify | Strengthen Part 2 sanitization directives with explicit checklist and examples |
| `ccya/models.py` | modify | Add `text` key to `_coerce_actions` fallback |
| `ccya/engine/turn.py` | modify | Pass `turn_no=0` to `_rules_messages()` on first turn; compute `_compendium_bios` and pass to `_narrate_messages()` |
| `docs/REPOMAP/engine.md` | update | Reflect `_rules_messages` and `_extract_*_messages` signature changes |
| `docs/REPOMAP/prompts.md` | update | Reflect template changes |
| `docs/plans/TODO.md` | update | Add new items under Eval Remediation section |

---

## Firm decisions

1. **No model schema changes.** All fixes are prompt-level or minimal Python context-passing. No new Pydantic fields.
2. **Extraction extractors never receive `active_domains`.** The system prompts already encode all extraction rules; the `active_domains` block in user prompts is dead context that wastes tokens. Remove from function signatures, context dicts, and templates.
3. **Scene/progress extractors never receive `rules_outcome`.** The system prompts already have band-aware extraction guidance. Remove from function signatures, context dicts, and templates.
4. **State extractor never receives `active_domains`, `rules_outcome`, `scene_result`, `stakes`, `band`, or `band_examples`.** All dead context — the state system prompt already has all necessary rules. `band_examples` was never passed in the context dict (dead block). `stakes`/`band` were only used by `rules_stakes_hint` (being removed). Remove from function signatures, context dicts, and templates.
5. **State extractor conditionals simplified.** Since the state stream only runs when `inventory` or `pc_condition` is active, remove `active_domains` conditionals and show conditions/inventory unconditionally.
6. **`prior_turn_narration` in progress prompt is mislabeled.** It shows the most recent turn's narration, which is "this turn" context for the progress extractor (not "prior"). Rename to `last_turn_narration` and position it above `## CURRENT TURN NARRATION`.
7. **`beat_expires_turn` label.** The field on `GMBeat` is `beat_expires_turn` in the model. We only change the *prompt label*, not the model field. The prompt should say "Expires at turn: T{N}" to avoid confusing the LLM about what the number means.
8. **Compactor sanitization is a prompt fix, not an engine fix.** The compactor engine already applies sanitization correctly (`_apply_sanitization`). The LLM just isn't emitting sanitization actions. Fix the system prompt.
9. **Actions coercion handles `text` key.** The LLM sometimes emits `{"text": "..."}` instead of plain strings. Add `text` as a fallback key in `_coerce_actions`.
10. **Turn numbers are consistent.** Turn 0 = world seed/intro, turn 1 = first actual turn. Pass `turn_no` as-is (the engine already computes `state.meta.turn + 1`).
11. **`run_turn_retry()` is out of scope.** The user is reworking that system separately.

---

## Implementation — Phase 1: Rules + Narration NPC Context Enrichment

### Context files to load
- `ccya/engine/rules.py` — `_rules_messages()`
- `ccya/prompts/rules_user.j2`
- `ccya/engine/narrate.py` — `_narrate_messages()`
- `ccya/prompts/narrate_system.j2`
- `ccya/engine/turn.py` — `_rules_messages()` call site (line ~303)
- `ccya/engine/narrate.py` — `_known_characters_for_extract()` (for bio access)

### Overview
Give the rules engine NPC context (same as narration receives) so it can classify intent more accurately when actions target specific NPCs. Also inject compendium bios into the narration prompt so the narrator has richer NPC identity data alongside last_seen.

### Detailed steps

#### Step 1.1 — Add present_npcs to rules prompt

**File:** `ccya/engine/rules.py`

**What:** Add `present_npcs` parameter to `_rules_messages()` and inject a `## present_npcs` block into the user prompt template context.

**Why:** The rules engine needs to know which NPCs are present to classify intent correctly (e.g., "I talk to Caron" vs "I talk to someone"). Narration already receives this context; rules should too.

**Code Snippet**
```python
def _rules_messages(
    env: Environment,
    state: dict[str, Any],
    user_input: str,
    *,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    present_npcs: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build [system, user] messages for Call 0 (intent classification + dice)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    meta = state.get("meta") or {}

    system_text = _render(env, "rules_system.j2", {})
    user_text = _render(
        env,
        "rules_user.j2",
        {
            "pc": pc,
            "location": location,
            "recent_turns": recent_turns or [],
            "meta": meta,
            "user_input": user_input,
            "present_npcs": present_npcs or [],
            "turn_no": turn_no,
        },
    )
    msgs: list[dict[str, str]] = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, False)
    return msgs
```

**File:** `ccya/prompts/rules_user.j2`

**What:** Add a `## present_npcs` block after the `## scene` block.

**Code Snippet**
```jinja2
## pc
{{ pc.name or "Unnamed" }} | {{ pc.tagline or pc.concept or "" }}
Stats: {% for k, v in (pc.stats or {}).items() %}{{ k }}={{ v }}{% if not loop.last %} {% endif %}{% endfor %}
Conditions: {% if pc.conditions %}{% for c in pc.conditions %}{{ c.label if c is mapping else c }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}

## scene
Location: {{ location.name or location.id or "Unknown" }}
{%- if present_npcs %}
## present_npcs (in scene — use these IDs for intent targeting)
{% for n in present_npcs %}- `{{ n.id }}` | {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor -%}
{% endif -%}
{%- if recent_turns %}
## last_turn (tail of the most recent narrative)
{%- set t = recent_turns[-1] %}
T{{ t.turn }}: {{ t.input }} — {{ t.narrative }}

{% endif -%}
## Current Turn: {{ meta.turn | default('?') }}
=== PLAYER INPUT ===
{{ user_input }}
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.
```

**Validation:** Rules prompt now includes present NPCs with notes. The `present_npcs` block appears between `## scene` and `## last_turn`.

#### Step 1.2 — Pass present_npcs from turn.py

**File:** `ccya/engine/turn.py`

**What:** In `run_turn()`, pass `_present_npcs` to `_rules_messages()` call. Pass `turn_no` as-is (turn 0 is world seed/intro, turn 1 is first actual turn — the engine already computes this correctly as `state.meta.turn + 1`).

**Why:** The rules engine needs the same NPC context that narration gets.

**Code Snippet**
```python
        # Line ~300 in run_turn(): compute present_npcs before rules call
        _present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])

        rules_messages = _rules_messages(
            env, state, user_input, recent_turns=recent_turns[-1:],
            turn_no=turn_no,
            present_npcs=_present_npcs,
        )
```

Note: `_present_npcs` is already computed earlier in `run_turn()` at line ~425. The call to `_rules_messages` is at line ~303, which is *before* `_present_npcs` is computed. We need to compute `_present_npcs` earlier. The simplest fix: compute it right before the rules call.

**Validation:** Rules prompt includes present NPCs. Turn numbers are consistent (turn 0 = world seed, turn 1 = first actual turn).

#### Step 1.3 — Inject compendium bios into narration context

**File:** `ccya/engine/narrate.py`

**What:** Add a `compendium_bios` parameter to `_narrate_messages()` that passes full compendium NPC entries (with bios) alongside the existing `known_npcs` (which only has name + last_seen).

**Why:** The user reported that narration could use compendium bios alongside last_seen. Currently `known_npcs` only has `id`, `name`, and `last_seen` (compact=True). The narrator has access to the full state dict but the prompt template only renders `known_npcs` which lacks bios.

**Code Snippet**
```python
def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    chronicle_tail: str = "",
    recent_turns: list[dict[str, Any]] = [],
    enable_narrate_thinking: bool = False,
    pack_style: str = "",
    narrator_rules: list[str] = [],
    world_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    recently_left: list[dict[str, Any]] = [],
    momentum: int = 0,
    pending_gm_beat: dict[str, Any] | None = None,
    deescalate: float = 0.0,
    ages: dict[str, int] | None = None,
    known_npcs: list[dict[str, Any]] = [],
    present_npcs: list[dict[str, Any]] = [],
    compendium_bios: list[dict[str, Any]] = [],
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    pc_allegiance: str | None = None,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    user_ctx = {
        "state": state,
        "chronicle_tail": chronicle_tail,
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "recently_left": recently_left,
        "user_input": user_input,
        "momentum": momentum,
        "pending_gm_beat": pending_gm_beat,
        "meta": {"turn": turn_no},
        "scene": state.get("scene", {}),
        "deescalate": deescalate,
        "ages": ages or {},
        "known_npcs": known_npcs,
        "present_npcs": present_npcs,
        "compendium_bios": compendium_bios,
        "world_factions": world_factions,
        "world_locations": world_locations,
        "pc_allegiance": pc_allegiance,
    }
    system_text = _render(env, "narrate_system.j2", {
        "pack_style": pack_style,
        "narrator_rules": narrator_rules,
        "world_rules": world_rules,
        "world_factions": world_factions,
        "world_locations": world_locations,
    })
    user_text = _render(env, "narrate_user.j2", user_ctx)
    msgs: list[dict[str, str]] = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_narrate_thinking)
    return msgs
```

**File:** `ccya/engine/turn.py`

**What:** In `run_turn()`, compute `compendium_bios` from the compendium and pass it to `_narrate_messages()`. Limit to NPCs present in scene or recently left.

**Why:** The narrator needs bio data for NPCs it's interacting with. Passing all compendium bios would waste tokens; only pass relevant ones.

**Code Snippet**
```python
        # Line ~422 in run_turn(): after _known_npcs computation
        _compendium_bios: list[dict[str, Any]] = []
        comp = state.get("compendium", {}).get("npcs", {})
        for nid in (state.get("scene") or {}).get("present_npcs", []):
            nid_str = str(nid.get("id", "")) if isinstance(nid, dict) else str(nid)
            entry = comp.get(nid_str, {})
            if entry and entry.get("bio"):
                _compendium_bios.append({
                    "id": nid_str,
                    "name": entry.get("name", ""),
                    "bio": entry.get("bio", ""),
                })
        for rl in (state.get("scene") or {}).get("recently_left", []):
            nid_str = str(rl.get("id", "")) if isinstance(rl, dict) else str(rl)
            entry = comp.get(nid_str, {})
            if entry and entry.get("bio"):
                _compendium_bios.append({
                    "id": nid_str,
                    "name": entry.get("name", ""),
                    "bio": entry.get("bio", ""),
                })
```

Then pass `_compendium_bios` to `_narrate_messages()`:
```python
        narr_messages = _narrate_messages(
            env,
            state,
            user_input,
            # ... existing params ...
            known_npcs=_known_npcs,
            present_npcs=_present_npcs,
            compendium_bios=_compendium_bios,
            # ... rest of params ...
        )
```

**File:** `ccya/prompts/narrate_user.j2`

**What:** Add a `## Compendium Bios` block after `## NPCs Present in Scene`.

**Code Snippet**
```jinja2
{% if present_npcs -%}
## NPCs Present in Scene
{% for n in present_npcs %}- {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor -%}
{% endif -%}
{% if compendium_bios -%}
## Compendium Bios (identity context for present/recent NPCs)
{% for b in compendium_bios %}- **{{ b.name }}**: {{ b.bio }}
{% endfor -%}
{% endif -%}
```

**Validation:** Narration prompt includes compendium bios for present and recently-left NPCs. Bios appear after the present NPCs block.

---

## Implementation — Phase 2: Extraction Stream Prompt Cleanup

### Context files to load
- `ccya/engine/extraction.py` — `_extract_scene_messages()`, `_extract_state_messages()`, `_extract_progress_messages()`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/extract_progress_user.j2`
- `docs/REPOMAP/engine.md`

### Overview
Remove dead/redundant context blocks from all three extraction stream prompts. Restructure the progress prompt to put `last_turn_narration` above `current_turn_narration` and fix the misleading label. Remove `active_domains` and `rules_outcome` from progress and state prompts. Remove `rules_outcome` from scene prompt.

### Detailed steps

#### Step 2.1 — Clean scene extractor prompt

**File:** `ccya/engine/extraction.py`

**What:** Remove `active_domains` and `rules_outcome` from `_extract_scene_messages()` parameters and context dict.

**Why:** The scene extractor doesn't need rules outcome or active domains — it only extracts NPC presence, location change, scene tags, and location description. The system prompt already has all necessary rules.

**Code Snippet**
```python
def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    enable_thinking: bool = False,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 1 (NPC presence, location, tags)."""
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    conditions = list(pc.get("conditions") or [])
    known_characters = _known_characters_for_extract(state, compact=False)
    npc_roster = _scene_npc_roster(known_characters)
    present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])

    system_text = _render(env, "extract_scene_system.j2", {})
    user_text = _render(
        env,
        "extract_scene_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "location": location,
            "conditions": conditions,
            "npc_roster": npc_roster,
            "present_npcs": present_npcs,
            "recent_turns": recent_turns or [],
            "turn_no": turn_no,
        },
    )
    msgs: list[dict[str, str]] = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs
```

**File:** `ccya/prompts/extract_scene_user.j2`

**What:** Remove the `## rules_outcome` / `## no_dice_roll` block at the top. Remove `## active_domains` block.

**Code Snippet**
```jinja2
## Current Turn: {{ turn_no }}

## pc
{{ pc.name }} — {{ pc.tagline }}
Stats: {% for k, v in (pc.stats or {}).items() %}{{ k }}={{ v }}{% if not loop.last %} {% endif %}{% endfor %}
{% if conditions -%}
Conditions: {% for c in conditions %}{{ c.label if c is mapping else c }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}
## location
`{{ location.id }}` | {{ location.name }}
{{ location.description }}

{% if present_npcs -%}
## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
{% for n in present_npcs %}- `{{ n.id }}` | {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor %}
{% endif -%}
{% if npc_roster -%}
<<<TRACE_IMMUTABLE_START>>>
## known_characters (compendium — reuse `id` for npc_add/npc_update/compendium_npc_update)
{% for n in npc_roster %}- `{{ n.id }}` | {{ n.name }} [{{ n.tags | join(",") }}]{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor %}
<<<TRACE_IMMUTABLE_END>>>
{% endif -%}
{% if scene_location_description -%}
## current_location_description (emit location_description only if narration adds NEW details)
{{ scene_location_description }}
{% endif -%}
{% if recent_turns -%}
{% set prev = recent_turns[-1] if recent_turns | length >= 1 else none %}
{% if prev %}
## previous_turn_narration (T{{ prev.turn }} context)
{{ prev.narrative }}
{% endif %}
{% endif -%}
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

**Validation:** Scene prompt no longer has `rules_outcome` or `active_domains` blocks. Saves ~200 tokens per scene extraction.

#### Step 2.2 — Clean state extractor prompt

**File:** `ccya/engine/extraction.py`

**What:** Remove `active_domains`, `rules_outcome`, `stakes`, `band`, and `scene_result` from `_extract_state_messages()` parameters and context dict.

**Why:** The state system prompt already has all extraction rules. `rules_outcome` was only used for `## EXTRACT EXAMPLES` (which was dead — `band_examples` was never passed) and `rules_stakes_hint` (which is being removed). `stakes`/`band` were only used by `rules_stakes_hint`. `scene_result` was only used for the `## scene_result` block which is dead context.

**Code Snippet**
```python
def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
    enable_thinking: bool = False,
    turn_no: int = 0,
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 2 (inventory + conditions)."""
    pc = state.get("pc") or {}

    system_text = _render(env, "extract_state_system.j2", {})
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "conditions": list(pc.get("conditions") or []),
            "inventory": state.get("inventory") or [],
            "turn_no": turn_no,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs
```

**File:** `ccya/prompts/extract_state_user.j2`

**What:** Remove `## active_domains`, `## rules_outcome`/`## no_dice_roll`, `## roll_context`, `## scene_result`, `## EXTRACT EXAMPLES` (dead — `band_examples` never passed), `## rules_stakes_hint` blocks. Remove `active_domains` conditionals — the state stream only runs when `inventory` or `pc_condition` is active, so we show them unconditionally.

**Code Snippet**
```jinja2
## Current Turn: {{ turn_no }}

## pc
{{ pc.name }} — {{ pc.tagline }}

{% if conditions -%}
## active_conditions
{% for c in conditions %}- `{{ c.id if c is mapping else c }}` | {{ c.label if c is mapping else c }}{% if c is mapping and c.get('description') %} — {{ c.description }}{% endif %}
{% endfor %}
{% endif -%}
{% if inventory -%}
## inventory (current stacks — read amount before emitting `inventory_remove`)
{% for item in inventory %}- `{{ item.id }}` | {{ item.name }} ×{{ item.amount or 1 }}{% if item.notes %} — {{ item.notes }}{% endif %}
{% endfor %}
{% endif -%}
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

**Validation:** State prompt no longer has `active_domains`, `rules_outcome`, `scene_result`, `roll_context`, `rules_stakes_hint`, or `band_examples` blocks. Saves ~400 tokens per state extraction.

#### Step 2.3 — Restructure progress extractor prompt

**File:** `ccya/engine/extraction.py`

**What:** Remove `active_domains` and `rules_outcome` from `_extract_progress_messages()` parameters and context dict. Keep `stakes`/`band` — they're used in the `## rules_stakes` block in the progress template.

**Code Snippet**
```python
def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    state_result: "StateExtractResult",
    enable_thinking: bool = False,
    intent: "IntentEnvelope | None" = None,
    deescalate: float = 0.0,
    quest_ages: list[dict[str, Any]] = [],
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    stakes: str = "",
    band: str = "",
) -> list[dict[str, str]]:
    """Build [system, user] messages for stream 3 (quests + facts + actions + outcome_summary)."""
    pc = state.get("pc") or {}
    scene = state.get("scene") or {}

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    recent_events = list(scene.get("recent_events") or [])
    world_state = list(scene.get("world_state") or [])

    # Cross-stream: minimal surfaces
    state_ctx = {
        "items_gained": [it.name for it in state_result.inventory_add],
        "items_lost": [it.id for it in state_result.inventory_remove],
    }

    system_text = _render(env, "extract_progress_system.j2", {})
    pending_beat = (state.get("meta") or {}).get("pending_gm_beat") or None
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            "narration": narration,
            "pc": pc,
            "active_quests": active_quests,
            "recent_events": recent_events,
            "world_state": world_state,
            "scene_pressure": list((state.get("scene") or {}).get("scene_pressure") or []),
            "state_result": state_ctx,
            "quest_threshold_directive": _quest_threshold_directive(active_quests),
            "intent": intent,
            "deescalate": deescalate,
            "quest_ages": quest_ages,
            "recent_turns": recent_turns or [],
            "turn_no": turn_no,
            "stakes": stakes,
            "band": band,
            "pending_beat": pending_beat,
        },
    )
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
    msgs = apply_thinking(msgs, enable_thinking)
    return msgs
```

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Major restructure:
1. Remove `## active_domains` block
2. Remove `## rules_outcome` / `## no_dice_roll` block
3. Rename `## prior_turn_narration` → `## last_turn_narration` and move it above `## CURRENT TURN NARRATION`
4. Change label text from "(T{{ ... }} — for outcome_summary and actions context)" to "(T{{ ... }} — context for this turn's outcome)"
5. Rename `beat_expires_turn` reference in `## pending_beat` block to "expires at turn"
6. Keep `## items_gained`, `## items_lost`, `## rules_stakes`, `## gm_beat`, `## deescalate`, `## quest_ages`, `## Current Pressures`

**Code Snippet**
```jinja2
## Current Turn: {{ turn_no }}

## quest_threshold
{{ quest_threshold_directive }}

{% if active_quests -%}
## active_quests
{% for q in active_quests %}- `{{ q.id }}` | {{ q.title }}
  objectives:
{% for o in (q.objectives or []) %}    {{ loop.index }}. [{% if o.done %}x{% elif o.failed %}f{% else %} {% endif %}] {{ o.description }}
{% endfor %}{% endfor %}
{% endif -%}

{% if recent_events -%}
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
{% for event in recent_events %}- {{ event.text if event is mapping else event }}
{% endfor %}
{% endif -%}
{% if not active_quests and world_state -%}
<<<TRACE_IMMUTABLE_START>>>
## world_state (read-only — use to reason about new quests only)
{% for f in world_state %}- {{ f if f is string else f.values() | join(': ') }}
{% endfor %}
<<<TRACE_IMMUTABLE_END>>>
{% endif -%}

{% if state_result.items_gained -%}
## items_gained
{{ state_result.items_gained | join(', ') }}

{% endif -%}
{% if state_result.items_lost -%}
## items_lost
{{ state_result.items_lost | join(', ') }}

{% endif -%}
{% if stakes and band -%}
## rules_stakes
Band: {{ band | upper }}. At-risk cost named by rules engine: {{ stakes }}
{% if band in ("crit_fail", "fail") -%}
If a narrative consequence is named above (e.g. an NPC acting, alarm raised, escape cut off), emit it as a scene_pressure_add entry at `immediate` urgency.
{% elif band == "crit_success" -%}
If a named entity was thwarted, consider a gm_beat of type `opportunity` or `escalation` naming that entity's reaction.
{% endif -%}

{% endif -%}
{% if deescalate > 0 -%}
## deescalate
A pressure resolved this turn (magnitude: {{ "%.1f"|format(deescalate) }}).
{% if deescalate >= 0.8 -%}
Strong deescalation. Prefer `breathing_room` beat type or no beat. Do not add new immediate pressures.
{% else -%}
Partial deescalation. Prefer low-urgency beat or no beat.
{% endif -%}

{% endif -%}
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires at turn: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif -%}
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

{% if quest_ages -%}
## quest_ages
{% for q in quest_ages %}- `{{ q.id }}`: {{ q.stalled_turns }} turns stalled
{% endfor %}
{%- endif %}
{% if scene_pressure -%}
## Current Pressures
{% for p in scene_pressure %}- [{{ p.id }}] ({{ p.urgency }}) {{ p.text }}
{% endfor %}
{% endif -%}
{% if recent_turns -%}
## last_turn_narration (T{{ recent_turns[-1].turn }} — context for this turn's outcome)
{{ recent_turns[-1].narrative }}

{% endif -%}
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

**Validation:** Progress prompt no longer has `active_domains` or `rules_outcome` blocks. `last_turn_narration` appears above `## CURRENT TURN NARRATION`. `beat_expires_turn` label changed to "Expires at turn". Saves ~500 tokens per progress extraction.

#### Step 2.4 — Update call sites in `_run_extraction_pipeline`

**File:** `ccya/engine/extraction.py`

**What:** Update the three call sites in `_run_extraction_pipeline()` to remove the dead params.

**Scene stream call (line ~433):**
```python
        scene_msgs = _extract_scene_messages(
            env, narration, state,
            enable_thinking=config.enable_extract_thinking,
            recent_turns=(recent_turns or [])[-1:],
            turn_no=turn_no,
        )
```

**State stream call (line ~487):**
```python
        state_msgs = _extract_state_messages(
            env, narration, state,
            enable_thinking=config.enable_extract_thinking,
            turn_no=turn_no,
        )
```

**Progress stream call (line ~533):**
```python
        progress_msgs = _extract_progress_messages(
            env, narration, state,
            state_result=state_result,
            enable_thinking=config.enable_extract_thinking,
            intent=intent,
            deescalate=deescalate,
            quest_ages=quest_ages or [],
            recent_turns=(recent_turns or [])[-2:],
            turn_no=turn_no,
            stakes=_stakes,
            band=_band,
        )
```

**Validation:** All call sites updated. No dead params passed.

---

## Implementation — Phase 3: Compactor Sanitization Fix

### Context files to load
- `ccya/prompts/compact_system.j2`
- `ccya/engine/compactor.py` — `_build_compact_messages()`, `_apply_sanitization()`

### Overview
The compactor fires but the LLM returns `{}` for all sanitization actions. The system prompt needs stronger directives, a more explicit checklist, and clearer examples to get the LLM to actually emit sanitization actions.

### Detailed steps

#### Step 3.1 — Strengthen compactor sanitization directives

**File:** `ccya/prompts/compact_system.j2`

**What:** Rewrite Part 2 (State sanitization) with:
1. Stronger opening directive: "You MUST check every category. If you return `{}` when sanitization is needed, you have failed."
2. Explicit per-category checklist with pass/fail criteria.
3. More concrete examples showing what to look for.
4. A "verification step" that forces the LLM to cross-reference bullets with state before outputting.

**Code Snippet**
```jinja2
## PART 2: State sanitization

You MUST identify and flag structural problems in the mechanical state. The bullets from Part 1 are your evidence. Cross-reference each bullet against the mechanical state below.

**CRITICAL: You must check every category. Returning `{}` when sanitization is needed is a failure.**

### What to flag

**npc_merge** — Two compendium NPC entries that are clearly the same person under different IDs (same name, same role, consistent bios). Provide `keep_id` (canonical) and `remove_ids` (duplicates).

**inventory_remove** — An inventory item that appears twice with different IDs but identical name and purpose. Provide the ID of the copy to remove (keep the one with higher amount or richer notes).

**quest_close** — An active quest whose objectives are ALL `done: true` but the quest status is still `active`. ALSO: a quest whose narrative conclusively ended multiple turns ago per the bulletin (e.g., "Player delivered the ledger to Halden" when `deliver_the_ledger` has all objectives done).

**pressure_remove** — A `scene_pressure` entry whose triggering situation has been fully resolved per the bulletin (e.g., "The chase is over" → remove `pursuers_approaching`; "The toughs were paid off" → remove `toughs_extortion_escalation`).

**condition_remove** — A `pc.condition` that the bulletin clearly shows was cured or resolved (e.g., "Player rested at the inn and recovered" → remove `wounded`; "Found a safe place to rest" → remove `shaken`). Do NOT remove conditions that might still plausibly apply.

### Verification checklist (MUST complete before outputting)

Go through each category in order. For each, ask: "Does the bulletin show this should be cleaned up?"

1. **npc_merge:** Are there two NPC entries that are clearly the same person? → If yes, add to `npc_merge`
2. **inventory_remove:** Are there duplicate inventory items with different IDs? → If yes, add to `inventory_remove`
3. **quest_close:** Are there active quests with ALL objectives done? → If yes, add to `quest_close`
4. **pressure_remove:** Are there pressures whose triggering situation is resolved? → If yes, add to `pressure_remove`
5. **condition_remove:** Are there conditions that the bulletin shows as cured/resolved? → If yes, add to `condition_remove`
6. **recent_events_compact:** Can similar events be merged? Is the list too long? → If yes, add to `recent_events_compact`

### Concrete examples

- Quest `deliver_the_ledger` has objectives: `[1. {done: true}, 2. {done: true}]` but status is `active` → add `deliver_the_ledger` to `quest_close`
- Bulletin says "T7: Player delivered ledger to Halden" and `deliver_the_ledger` has all objectives done → add to `quest_close`
- Pressure `pursuers_approaching` (immediate) but bulletin says "T12: Player escaped to river bend, pursuers lost" → add `pursuers_approaching` to `pressure_remove`
- Condition `shaken` but bulletin says "T8: Player found safe haven at the inn, felt calm" → add `shaken` to `condition_remove`
- Inventory `bandages` appears with IDs `bandages` (amount:3) and `medical_bandages` (amount:2), same purpose → add `medical_bandages` to `inventory_remove`

### Output format

After the bullet lines and a blank line, output exactly one JSON object. Each action includes a `confidence` field: `"high"`, `"medium"`, or `"low"`.

```json
{
  "npc_merge": [{"keep_id": "...", "remove_ids": ["..."], "confidence": "high"}],
  "inventory_remove": [{"id": "item_id", "confidence": "high"}],
  "quest_close": [{"id": "quest_id", "confidence": "high"}],
  "pressure_remove": [{"id": "pressure_id", "confidence": "medium"}],
  "condition_remove": [{"id": "condition_id", "confidence": "high"}],
  "recent_events_compact": [{"id": "...", "text": "...", "turn": 0}]
}
```

Omit any key whose list would be empty. If nothing needs fixing, output `{}`. But you MUST have checked every category before deciding nothing needs fixing.

### Confidence guidelines

- **high** — The bulletin explicitly confirms the fix (e.g., "Player delivered the ledger" + all objectives done). Safe to apply.
- **medium** — Strong narrative evidence but not explicit (e.g., "Player rested at the inn" + `wounded` condition). Likely correct but verify.
- **low** — Plausible but uncertain (e.g., two NPCs with similar names but no clear evidence they're the same person). Flag but don't auto-apply.
```

**Validation:** Compactor prompt now has explicit verification checklist, concrete examples, and stronger directives. The LLM should now emit sanitization actions when appropriate.

---

## Implementation — Phase 4: Minor Fixes

### Context files to load
- `ccya/models.py` — `_coerce_actions`
- `ccya/prompts/narrate_system.j2`
- `ccya/engine/turn.py` — `_rules_messages` call (already modified in Phase 1)

### Overview
Fix the actions coercion to handle `{"text": "..."}` output from the LLM. Add a narration system prompt rule about omitting null fields. Fix quest age display to show the number.

### Detailed steps

#### Step 4.1 — Fix actions coercion for `text` key

**File:** `ccya/models.py`

**What:** In `ProgressExtractResult._coerce_actions`, add `text` as a fallback key alongside `action` and `description`.

**Why:** The LLM sometimes emits `{"text": "..."}` for actions instead of plain strings. The current coercion only handles `action` and `description` keys.

**Code Snippet**
```python
    @field_validator("actions", mode="before")
    @classmethod
    def _coerce_actions(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[str] = []
        for x in v:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                out.append(x.get("action") or x.get("description") or x.get("text") or str(x))
            else:
                out.append(str(x))
        return out
```

**Validation:** Actions that come as `{"text": "..."}` are now correctly coerced to plain strings.

#### Step 4.2 — Add null-omission rule to narration system prompt

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a rule at the end of the system prompt: "When emitting structured data (JSON, scope tags), omit null/empty fields entirely. Do not emit `key: null` — just omit the key."

**Why:** The user reported that null outputs waste output tokens. This is a general instruction for any structured output the narrator produces.

**Code Snippet**
```
# Add to end of narrate_system.j2:

## Output discipline
When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out. This reduces output token waste.
```

**Validation:** Narration system prompt includes null-omission rule.

#### Step 4.3 — Fix quest age display

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** In the `## quest_ages` block, change the display from `{{ q.age }} turns` to `{{ q.stalled_turns }} turns stalled`.

**Why:** The user reported quest ages show "turns" with no number. The model field is `stalled_turns` (set in `_compute_quest_ages`), but the prompt template was using `q.age` which doesn't exist, resulting in empty output.

**Code Snippet**
```jinja2
{% if quest_ages -%}
## quest_ages
{% for q in quest_ages %}- `{{ q.id }}`: {{ q.stalled_turns }} turns stalled
{% endfor %}
{%- endif %}
```

**Validation:** Quest ages now display the number correctly (e.g., "settle_the_debt: 3 turns stalled").

---

## Ambiguities requiring resolution before execution

1. **Compendium bios scope:** We're passing bios for present + recently_left NPCs only. Should we also include bios for NPCs mentioned in the current narration but not in present_npcs? **Recommendation:** No — that would require NLP to extract NPC mentions from narration, which is out of scope. Present + recently_left covers the vast majority of cases.

---

## TODO.md update

Add the following under `## Eval Remediation (May 2026)`:

```markdown
- [ ] **Extraction stream remediation** — Phase 1: rules+narration NPC context enrichment (present_npcs in rules prompt, compendium bios in narration). Phase 2: extraction stream prompt cleanup (remove dead active_domains/rules_outcome from progress/state/scene, restructure progress prompt). Phase 3: compactor sanitization fix (strengthen directives). Phase 4: minor fixes (actions coercion text key, null-omission rule, quest age display) — see `[eval-remediation/extraction-stream-remediation.md](eval-remediation/extraction-stream-remediation.md)`
```

Also update REPOMAP entries:
- `docs/REPOMAP/engine.md`: Update `_rules_messages` signature to include `present_npcs` and `turn_no` params. Update `_extract_scene_messages`, `_extract_state_messages`, `_extract_progress_messages` to note removal of `active_domains`/`rules_outcome` from user context.
- `docs/REPOMAP/prompts.md`: Update `extract_progress_user.j2` description to note removal of `active_domains`/`rules_outcome` blocks and restructured layout. Update `extract_state_user.j2` description to note removal of `active_domains`/`scene_result`/`roll_context`/`rules_stake_hint` blocks. Update `extract_scene_user.j2` description to note removal of `rules_outcome` block. Update `rules_user.j2` to note `present_npcs` block. Update `narrate_user.j2` to note `compendium_bios` block.
