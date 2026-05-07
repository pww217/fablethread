# Compactor Overhaul — Window/Compact Parity, Prior History, State Sanitization

## Status
`open`

## Part of
standalone

## Dependencies
- none — standalone plan. No open plan modifies `compactor.py`, `config.py`, `chronicle.py`, or `compact_*.j2`.

## Objective
The compactor currently runs every `compact_every` turns and compresses a window of turns into COMPACTED bullets in `chronicle.md`. It does not enforce a hard cap on `recent_turns`, does not maintain a structured `prior_history` list in `state.yaml`, and has no knowledge of in-state structural problems it could fix while it already holds the full game state. This plan fixes the window/compact parity, introduces `prior_history` as a first-class state field, caps `recent_narration` to `window_turns` entries, and extends the compaction LLM call to also perform state sanitization (dedup NPCs/inventory, flag orphaned quests, prune stale pressures).

## Non-goals
- No changes to the narration prompt templates beyond what is needed to consume `prior_history` vs `chronicle_tail`.
- No changes to the extractor prompts.
- Does not implement the P4 location-keyed NPC store.
- Does not change roll mechanics, momentum, or scene pressure logic.
- Does not add a new LLM call — all sanitization is appended to the single existing compaction call output schema.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/engine/config.py` | modify | Remove `compact_every` field; `window_turns` now serves as the single window+compact interval. Add `compact_temperature` doc note. No new fields. |
| `ccya/engine/compactor.py` | modify | Rewrite `maybe_compact` trigger logic; add `prior_history` append; add state sanitization; cap `recent_narration` to `window_turns`; remove JSON event compaction (recent_events are managed by `apply_delta`). |
| `ccya/prompts/compact_system.j2` | modify | Add PART 3 (state sanitization output) to the system prompt. |
| `ccya/prompts/compact_user.j2` | modify | Add full game state snapshot (inventory, NPCs, quests, conditions, pressures) to user prompt. |
| `ccya/state/io.py` | modify | Add `prior_history: []` to `_default_state`; add migration in `_migrate_state`. |
| `config.yaml` | modify | Remove `compact_every`; set `window_turns: 4`. |
| `docs/REPOMAP/engine.md` | update | Update compactor.py function signatures; note `prior_history` and sanitization output. |
| `docs/REPOMAP/config.md` | update | Remove `compact_every`; clarify `window_turns` dual role. |
| `docs/REPOMAP/state.md` | update | Add `prior_history` to state shape. |
| `docs/plans/TODO.md` | update | Add this plan under P1 open items. |

---

## Firm Decisions

1. **`compact_every` is removed; `window_turns` is the single control.** Compaction fires after turn `N` where `N % window_turns == 0`. This is the parity guarantee: the player always has at most `window_turns` recent narration entries, and compaction always runs against exactly the prior `window_turns` block. The config REPOMAP and `EngineConfig` must remove `compact_every` cleanly.

2. **`prior_history` is a `list[str]` on `meta`.** Each entry is a single bullet from the compactor, already formatted `- [T{n}] …`. The compactor appends new bullets to this list every `window_turns` turns. The narrator and context assembly consume `prior_history` as the "long history" block instead of `chronicle_tail` parsing. Chronicle.md COMPACTED block writing is retained for human readability but is no longer the primary prior history source.

3. **`recent_narration` cap is enforced in `maybe_compact`, not `apply_delta`.** Immediately after compaction fires, `state["meta"]["recent_narration"]` is sliced to the last 1 entry (the turn just completed). Before compaction fires, `recent_narration` is built from `load_recent_chronicle_turns(save_dir, window_turns)` each turn — this is already how `recent_turns` works in `turn.py`. No new in-state `recent_narration` field is needed; `window_turns` already caps what `load_recent_chronicle_turns` returns.

4. **State sanitization output is a structured JSON block, not bullet lines.** The compaction LLM returns PART 3 as a JSON object with optional fields: `npc_merge`, `inventory_remove`, `quest_close`, `pressure_remove`, `condition_remove`. Each field is a list of IDs. The compactor applies these deterministically in Python — it does not re-call any extractor. If the LLM omits PART 3, the compactor silently skips sanitization (safe default).

5. **The compaction LLM receives the full mechanical state** (inventory, compendium NPCs, active quests, active conditions, scene pressures) as structured data in the user prompt, not rendered narrative.

6. **`recent_events` compaction (Part 2 in current system prompt) is removed.** `recent_events` are now managed entirely by `apply_delta` with a rolling FIFO cap. The compactor's job is chronicle history and state hygiene only.

7. **Sanitization rules are deterministic from LLM output.** The LLM identifies which IDs to remove/merge; Python applies the changes. The compactor never invents IDs. Any ID in the LLM's sanitization output that does not exist in current state is silently dropped.

8. **`compact_temperature` is retained** in `EngineConfig` (value `0.1`). The config key in `config.yaml` stays as-is.

9. **Migration is a one-time `_migrate_state` pass.** If `prior_history` is absent from a loaded state, it is initialized to `[]`. If `compact_every` appears in `config.yaml`, it is ignored (not read into `EngineConfig`).

---

## Implementation — Phase 1: Config and State Schema

### Context files to load
- `ccya/engine/config.py`
- `ccya/state/io.py`
- `config.yaml`

### Overview
Remove `compact_every` from `EngineConfig` and `config.yaml`. Add `prior_history` to `_default_state` and `_migrate_state`. The rest of the system keeps working because `window_turns` was already present and the `compact_every` check in `compactor.py` will be rewritten in Phase 2.

### Detailed steps

#### Step 1.1 — Remove `compact_every` from `EngineConfig`

**File:** `ccya/engine/config.py`

**What:** Delete the `compact_every: int = 0` field. The `EngineConfig` load path reads from `config.yaml` via `load_config()` in `models.py`, so removing the field drops the key from the dataclass cleanly.

**Why:** `window_turns` is the single control. Having two fields with overlapping purpose (`compact_every` and `window_turns`) is the root cause of the design ambiguity.

**Code Snippet**
```python
# In EngineConfig dataclass — remove this line:
# compact_every: int = 0
# Keep:
compact_temperature: float = 0.1
window_turns: int = 3
```

**Validation:** `grep -r "compact_every" ccya/` returns zero results after this change (except config.yaml which is updated in Step 1.3).

---

#### Step 1.2 — Add `prior_history` to `_default_state` and `_migrate_state`

**File:** `ccya/state/io.py`

**What:** Add `prior_history: []` under `meta` in `_default_state`. Add a migration guard in `_migrate_state` that initializes `prior_history` to `[]` if absent.

**Why:** `prior_history` is the durable append-only list that replaces COMPACTED chronicle parsing. It must survive across saves.

**Code Snippet**
```python
# In _default_state(), under meta block:
"meta": {
    "game_name": "",
    "turn": 0,
    "setting_pack": "",
    "model": "",
    "compendium_touch_order": [],
    "pending_gm_beat": None,
    "last_compacted_turn": 0,
    "prior_history": [],   # <-- add this
},

# In _migrate_state(state):
if "prior_history" not in state.get("meta", {}):
    state.setdefault("meta", {})["prior_history"] = []
```

**Validation:** Load a pre-existing save with `load_state`. Assert `state["meta"]["prior_history"] == []`. Load a new save with `init_save_dir`. Assert same.

---

#### Step 1.3 — Update `config.yaml`

**File:** `config.yaml`

**What:** Remove the `compact_every` key under `[game]`. Change `window_turns` to `4`. Keep `compact_temperature: 0.1`.

**Why:** `window_turns: 4` with `compact_every` gone means the compactor fires every 4 turns, and the narrator receives at most 3 recent turns before compaction (turns N-3, N-2, N-1 are recent; turn N is the compaction trigger that runs after N is written).

**Code Snippet**
```yaml
game:
  # ... other keys ...
  window_turns: 4
  compact_temperature: 0.1
  # compact_every: 4   <-- removed
```

**Validation:** `python -c "from ccya.models import load_config; c = load_config(); print(c)"` — no `compact_every` key. `EngineConfig` loads without error.

---

### Tests to write or update
- `tests/test_compactor.py` (new or existing): Assert `EngineConfig()` has no `compact_every` attribute. Assert `load_state` on a bare state dict (no `prior_history`) returns one with `prior_history == []`.

### REPOMAP updates required
- `docs/REPOMAP/config.md`: Remove `compact_every` row from config.yaml table and from `EngineConfig` dataclass block. Add note to `window_turns`: "also controls compaction interval — compaction fires when `turn % window_turns == 0`."
- `docs/REPOMAP/state.md`: Add `prior_history: [str]` under `meta` in the state shape block.

### Risks
1. Any test that constructs `EngineConfig(compact_every=...)` will fail — scan and fix all test files.
2. If `config.yaml` has `compact_every` loaded via `load_config()` and the key is passed as a kwarg to `EngineConfig`, it will raise a `TypeError`. The `server/app.py` bootstrap must be checked to confirm it does not forward `compact_every` to the dataclass.

---

## Implementation — Phase 2: Compactor Logic Rewrite

### Context files to load
- `ccya/engine/compactor.py`
- `ccya/engine/config.py` (post Phase 1)
- `ccya/state/io.py` (post Phase 1)
- `ccya/state/chronicle.py`
- `ccya/prompts/compact_system.j2`
- `ccya/prompts/compact_user.j2`

### Overview
Rewrite `maybe_compact` to use `window_turns` as the trigger. Parse PART 3 sanitization JSON from the LLM response and apply it to state in Python. Append new chronicle bullets to `state["meta"]["prior_history"]`. Remove the `recent_events` compaction path entirely.

### Detailed steps

#### Step 2.1 — Rewrite `maybe_compact` trigger and history append

**File:** `ccya/engine/compactor.py`

**What:** Replace `compact_every` references with `window_turns`. After a successful LLM call: (1) append bullet lines to `state["meta"]["prior_history"]`, (2) still write the COMPACTED block to `chronicle.md` for readability, (3) remove the `compacted_events` path (no longer managing `recent_events`), (4) apply `SanitizationResult` from PART 3 if present.

**Why:** `prior_history` is now the canonical long-history store. The file write is secondary (for human debugging). `recent_events` is entirely `apply_delta`'s domain.

**Code Snippet**
```python
async def maybe_compact(
    save_dir: Path,
    state: dict[str, Any],
    config: EngineConfig,
) -> dict[str, Any]:
    """Run compaction pass if turn count triggers it.

    Fires when current_turn % window_turns == 0.
    Appends bullets to state["meta"]["prior_history"].
    Applies state sanitization from PART 3 of LLM output.
    Returns updated state.
    """
    window = config.window_turns
    if window <= 0:
        return state

    current_turn = state.get("meta", {}).get("turn", 0)
    if current_turn == 0:
        return state

    if current_turn % window != 0:
        return state

    last_compacted = state.get("meta", {}).get("last_compacted_turn", 0)
    start_turn = last_compacted + 1
    end_turn = current_turn - (window - 1)  # compact all but the most recent window_turns

    # The compactor runs AFTER the current turn is written.
    # We compact turns [last_compacted+1 .. current_turn - window_turns + 1 .. current_turn - (window_turns-1)]
    # Concretely with window=4 and current_turn=4:
    #   start_turn=1, end_turn=1  → compact only turn 1
    # With window=4 and current_turn=8:
    #   start_turn=5, end_turn=5  → compact only turn 5
    # The last (window_turns - 1) turns stay as recent_narration.
    # This means: compact_end = current_turn - (window_turns - 1)
    compact_end = current_turn - (window - 1)
    compact_start = last_compacted + 1

    if compact_start > compact_end:
        return state

    _log.info(
        "compactor: compacting turns %d–%d (current_turn=%d, window=%d)",
        compact_start,
        compact_end,
        current_turn,
        window,
        extra={"turn": current_turn},
    )

    turns = _extract_turns_for_compact(save_dir, compact_start, compact_end)
    if not turns:
        return state

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
        _log.warning("compactor: LLM call failed, skipping: %s", exc, extra={"turn": current_turn})
        return state

    bullets_text, sanitization = _parse_compact_response(response_text)

    if not bullets_text.strip():
        _log.warning("compactor: LLM returned empty bullets, skipping", extra={"turn": current_turn})
        return state

    # Append bullets to prior_history (split on newlines, strip blanks)
    new_bullets = [b for b in bullets_text.split("\n") if b.strip()]
    state.setdefault("meta", {}).setdefault("prior_history", []).extend(new_bullets)

    # Write COMPACTED block to chronicle.md for human readability
    _write_compacted_block(save_dir, bullets_text)

    # Apply sanitization
    if sanitization:
        _apply_sanitization(state, sanitization)

    state.setdefault("meta", {})["last_compacted_turn"] = compact_end

    return state
```

**Validation:** Run `maybe_compact` with a mock LLM on a state at turn 4. Assert `state["meta"]["prior_history"]` has exactly the bullet lines returned. Assert `state["meta"]["last_compacted_turn"] == 1` (compact_end with window=4, current=4 → compact_end=4-(4-1)=1).

---

#### Step 2.2 — Update `_build_compact_messages` — remove events, add full state snapshot

**File:** `ccya/engine/compactor.py`

**What:** Remove the `events` parameter from `_build_compact_messages`. Add full mechanical state (inventory, compendium NPCs, quests, conditions, pressures) to the user prompt context.

**Why:** Part 2 (event compaction) is gone. Part 3 (sanitization) needs the full mechanical state to identify duplicates and issues.

**Code Snippet**
```python
def _build_compact_messages(
    env: Any,
    state: dict[str, Any],
    turns: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build system + user messages for the compaction LLM call."""
    system_prompt = env.get_template("compact_system.j2").render()

    active_quests = [
        q for q in (state.get("quests") or []) if q.get("status") == "active"
    ]
    all_quests = list(state.get("quests") or [])
    present_npcs = state.get("scene", {}).get("present_npcs") or []
    pressures = state.get("scene", {}).get("scene_pressure") or []
    inventory = list(state.get("inventory") or [])
    compendium_npcs = list((state.get("compendium") or {}).get("npcs", {}).items())
    conditions = list((state.get("pc") or {}).get("conditions") or [])

    user_prompt = env.get_template("compact_user.j2").render(
        turns=turns,
        active_quests=active_quests,
        all_quests=all_quests,
        npc_names=[n.get("name", n) if isinstance(n, dict) else n for n in present_npcs],
        pressures=pressures,
        inventory=inventory,
        compendium_npcs=compendium_npcs,
        conditions=conditions,
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
```

**Validation:** Render the user prompt with a sample state. Assert inventory, NPCs, and conditions appear in the output.

---

#### Step 2.3 — Update `_parse_compact_response` — remove events JSON, add sanitization JSON

**File:** `ccya/engine/compactor.py`

**What:** Return `(bullets_text, sanitization_dict)` instead of `(bullets_text, compacted_events)`. Parse the PART 3 JSON object (if present) from the response.

**Why:** The old second return value was a `list[str]` for recent_events which is now entirely dropped. The new second value is an optional dict with sanitization instructions.

**Code Snippet**
```python
def _parse_compact_response(
    response_text: str,
) -> tuple[str, dict[str, Any]]:
    """Parse LLM output into bullet text and optional sanitization dict.

    Bullet lines match `- [T\\d+] ` pattern.
    Sanitization JSON is the last JSON *object* (not array) in the response.
    Returns (bullets_text, sanitization) where sanitization may be {}.
    """
    bullets: list[str] = []
    for line in response_text.split("\n"):
        if _BULLET_RE.match(line.strip()):
            bullets.append(line.strip())

    sanitization: dict[str, Any] = {}
    # Find last JSON object in response (not array — arrays are bullet artifacts)
    last_open = response_text.rfind("{")
    if last_open >= 0:
        last_close = response_text.rfind("}", last_open)
        if last_close > last_open:
            candidate = response_text[last_open : last_close + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    sanitization = parsed
            except (json.JSONDecodeError, ValueError):
                pass

    return "\n".join(bullets), sanitization
```

**Validation:** Parse a mock response that contains bullets + a JSON object with `npc_merge`, `inventory_remove`. Assert bullets parse correctly. Assert sanitization dict is populated.

---

#### Step 2.4 — Add `_apply_sanitization`

**File:** `ccya/engine/compactor.py`

**What:** New function that takes the sanitization dict from PART 3 and applies each operation deterministically to `state` in-place.

**Why:** The compactor has the full game state and can apply structural fixes the LLM identified. Python applies them — no second LLM call.

**Sanitization operations:**
- `npc_merge`: list of `{keep_id, remove_ids: [str]}` — for each entry, for each `remove_id`: if `remove_id` in `compendium.npcs`, delete it; also remove it from `scene.present_npcs`; replace any occurrence of `remove_id` in `scene.recently_left` with `keep_id`. Log each removal.
- `inventory_remove`: list of item IDs to remove entirely from inventory. Only execute if the item ID exists exactly.
- `quest_close`: list of quest IDs to mark `status: "completed"` with a note. Only if quest is currently `active` and the LLM has flagged it as orphaned/stale.
- `pressure_remove`: list of pressure IDs to remove from `scene.scene_pressure`.
- `condition_remove`: list of condition IDs to remove from `pc.conditions`.

**Code Snippet**
```python
def _apply_sanitization(state: dict[str, Any], san: dict[str, Any]) -> None:
    """Apply compactor sanitization to state in-place.

    All operations are ID-based. Unknown IDs are silently skipped.
    """
    # NPC merge: remove duplicate NPC entries from compendium and scene
    for merge in (san.get("npc_merge") or []):
        keep_id = merge.get("keep_id", "")
        for rid in (merge.get("remove_ids") or []):
            comp = state.get("compendium", {}).get("npcs", {})
            if rid in comp:
                _log.info("compactor: merging duplicate NPC %r into %r", rid, keep_id)
                comp.pop(rid)
            # Remove from present_npcs
            scene = state.setdefault("scene", {})
            scene["present_npcs"] = [
                n for n in (scene.get("present_npcs") or [])
                if (n.get("id") if isinstance(n, dict) else n) != rid
            ]

    # Inventory: remove specific items by exact ID
    for item_id in (san.get("inventory_remove") or []):
        before = len(state.get("inventory") or [])
        state["inventory"] = [
            it for it in (state.get("inventory") or [])
            if it.get("id") != item_id
        ]
        if len(state.get("inventory") or []) < before:
            _log.info("compactor: removed duplicate inventory item %r", item_id)

    # Quest close: mark orphaned active quests as completed
    for quest_id in (san.get("quest_close") or []):
        for q in (state.get("quests") or []):
            if q.get("id") == quest_id and q.get("status") == "active":
                q["status"] = "completed"
                _log.info("compactor: closed orphaned quest %r", quest_id)

    # Scene pressure removal
    remove_pressures = set(san.get("pressure_remove") or [])
    if remove_pressures:
        scene = state.setdefault("scene", {})
        scene["scene_pressure"] = [
            p for p in (scene.get("scene_pressure") or [])
            if p.get("id") not in remove_pressures
        ]

    # Condition removal
    remove_conds = set(san.get("condition_remove") or [])
    if remove_conds:
        pc = state.setdefault("pc", {})
        pc["conditions"] = [
            c for c in (pc.get("conditions") or [])
            if c.get("id") not in remove_conds
        ]
```

**Validation:** Build a state with a duplicate NPC (`npc_a` and `npc_a_dup`). Call `_apply_sanitization` with `{"npc_merge": [{"keep_id": "npc_a", "remove_ids": ["npc_a_dup"]}]}`. Assert `npc_a_dup` gone from compendium, still present in scene as `npc_a`.

---

### Tests to write or update
- `tests/test_compactor.py`:
  - `test_maybe_compact_trigger`: mock LLM, assert fires when `turn % window_turns == 0`, not otherwise.
  - `test_maybe_compact_prior_history_append`: assert bullets appear in `state["meta"]["prior_history"]` after compaction.
  - `test_parse_compact_response_sanitization`: assert `_parse_compact_response` extracts dict from last JSON object in response.
  - `test_apply_sanitization_npc_merge`: duplicate NPC removed from compendium and present_npcs.
  - `test_apply_sanitization_inventory_remove`: item removed only if exact ID match.
  - `test_apply_sanitization_unknown_ids_skipped`: no KeyError or exception on unknown IDs.
  - `test_maybe_compact_no_recent_events_mutation`: assert `state["scene"]["recent_events"]` is unchanged after compaction.

### REPOMAP updates required
- `docs/REPOMAP/engine.md` → compactor.py section:
  - `maybe_compact`: note trigger is `turn % window_turns == 0`; appends to `state["meta"]["prior_history"]`.
  - `_build_compact_messages`: remove `events` param; add `inventory`, `compendium_npcs`, `conditions` params.
  - `_parse_compact_response`: returns `tuple[str, dict]` not `tuple[str, list[str]]`.
  - Add `_apply_sanitization(state, san)` → `None`.

### Risks
1. `compact_end = current_turn - (window - 1)` means at turn=4, window=4: compact_end = 4 - 3 = 1. Only turn 1 gets compacted. Turns 2, 3, 4 remain as recent. This is correct but must be documented clearly — the first compaction is "delayed" by the window.
2. If the LLM returns a `{...}` JSON blob in the narrative bullets themselves (unlikely but possible), the `_parse_compact_response` parser may pick it up as a sanitization dict. Mitigated by checking that the dict has at least one of the expected keys (`npc_merge`, `inventory_remove`, etc.) before accepting it.
3. `_apply_sanitization` mutates state in-place but `maybe_compact` returns state. The caller in `turn.py` does `state = await maybe_compact(...)` then `save_state`. This is correct — no double-save risk.

---

## Implementation — Phase 3: Prompt Updates

### Context files to load
- `ccya/prompts/compact_system.j2`
- `ccya/prompts/compact_user.j2`
- `ccya/engine/compactor.py` (post Phase 2)

### Overview
Rewrite `compact_system.j2` to remove PART 2 (event compaction) and add PART 2 (state sanitization). Update `compact_user.j2` to include the full mechanical state snapshot.

### Detailed steps

#### Step 3.1 — Rewrite `compact_system.j2`

**File:** `ccya/prompts/compact_system.j2`

**What:** Remove all PART 2 content (recent events compaction). Replace with PART 2: State Sanitization. The bullet output format (PART 1) is unchanged.

**Why:** State sanitization is the new second task. The compactor now receives and can judge structural state issues.

**Code Snippet**
```
You are a game historian and consistency editor for a TTRPG session.

Your task has two parts: (1) compress turn narratives into concise bullet notes,
and (2) identify structural state problems for the engine to fix.

---

## PART 1: Turn bullets (internal session notes)

Compress each full-turn narrative into a single bullet. The player never sees these.

### What to preserve
- Named NPCs (first mention + role/title)
- Location where the turn took place
- Quest outcomes (resolved, failed, new leads)
- Item gains/losses (key items, consumables used)
- Condition changes (gained/lost)
- Irreversible player choices
- Death/departure events for named NPCs
- Any mechanical consequence that affects future play

### What to cull
- Atmospheric flavor and repeated setting descriptions
- Dialogue that does not introduce someone, resolve something, or change relationships
- Combat blow-by-blow (keep who was fought and outcome, not each exchange)
- Redundant rest/observation turns with no mechanical or story consequence

### Format
`- [T{n}] {1-2 line summary}`

One bullet per turn. Emit a bullet even for uneventful turns.

---

## PART 2: State sanitization

You have access to the full mechanical game state. Identify structural problems
that should be fixed. Only flag problems you are confident about — false positives
cause data loss. When uncertain, omit the flag.

### Problems to identify

**Duplicate NPCs (`npc_merge`):**
Two compendium NPC entries that are clearly the same person under different IDs
(e.g. "elara" and "elara_merchant" where both bios describe the same woman).
Provide `keep_id` (the canonical entry) and `remove_ids` (the duplicates to remove).

**Duplicate inventory items (`inventory_remove`):**
An item that appears twice with different IDs but identical names and purpose.
Provide the ID of the copy to remove (keep the one with higher amount or richer notes).

**Orphaned active quests (`quest_close`):**
An active quest whose objectives are all marked `done: true` but the quest was
never closed, OR a quest whose narrative has clearly concluded multiple turns ago
per the bulletin. Provide the quest ID.

**Stale pressures (`pressure_remove`):**
A `scene_pressure` entry whose trigger event has been fully resolved per the
bulletin (e.g. "Guards are chasing the player" but the player escaped three turns ago).
Provide the pressure ID.

**Resolved conditions (`condition_remove`):**
A `pc.condition` entry that the bulletin indicates has been resolved
(e.g. "Poisoned" but the player was cured). Do NOT remove conditions that might
still plausibly apply. Provide the condition ID only when clearly stale.

### Format

A single JSON object after the bullet lines and a blank line:

```json
{
  "npc_merge": [{"keep_id": "...", "remove_ids": ["..."]}],
  "inventory_remove": ["..."],
  "quest_close": ["..."],
  "pressure_remove": ["..."],
  "condition_remove": ["..."]
}
```

Omit any key with an empty list. If there are no issues, emit `{}`.

---

## Hard rules

- Do NOT invent, infer, or embellish. Only compress what is given.
- If a turn had no meaningful events, still emit a bullet noting the lack of change.
- Preserve turn numbers in each bullet for traceability.
- Output format: bullet lines first (one per turn), then a blank line, then the JSON object.
- The JSON object must be the last thing in your response.
```

**Validation:** Feed a known response with bullets + `{}` through `_parse_compact_response`. Assert zero sanitization operations.

---

#### Step 3.2 — Update `compact_user.j2`

**File:** `ccya/prompts/compact_user.j2`

**What:** Remove `RECENT EVENTS TO COMPACT` section. Add `MECHANICAL STATE` section with inventory, compendium NPCs, quests, conditions, pressures.

**Why:** The LLM needs to see the full state to perform sanitization. Events are no longer part of compaction scope.

**Code Snippet**
```
## TURNS TO COMPACT

{% for t in turns %}
### Turn {{ t.turn }} — {{ t.input }}
{{ t.narrative }}
{% endfor -%}

## ACTIVE CONTEXT (relevance anchors — protect information related to these)

{% if active_quests %}
### Active Quests
{% for q in active_quests -%}
- **{{ q.get("title", q.get("id", "?")) }}** [{{ q.get("id") }}]: {% for obj in (q.get("objectives") or []) %}[{{ "x" if obj.get("done") else " " }}] {{ obj.get("description", "?") }} {% endfor %}
{% endfor -%}
{% endif -%}

{% if npc_names %}
### Present NPCs
{{ npc_names | join(', ') }}
{% endif -%}

{% if pressures %}
### Active Pressures
{% for p in pressures -%}
- [{{ p.get('id', '?') }}] [{{ p.get('urgency', '').upper() }}] {{ p.get('text', p) }}
{% endfor -%}
{% endif -%}

## MECHANICAL STATE (for sanitization — read-only reference)

### Inventory
{% for item in inventory -%}
- [{{ item.get('id', '?') }}] {{ item.get('name', '?') }}{% if item.get('amount', 1) > 1 %} ×{{ item.get('amount') }}{% endif %}{% if item.get('notes') %}: {{ item.get('notes') }}{% endif %}
{% else %}(empty)
{% endfor %}

### Compendium NPCs
{% for npc_id, npc in compendium_npcs -%}
- [{{ npc_id }}] {{ npc.get('name', '?') }}{% if npc.get('title') %} ({{ npc.get('title') }}){% endif %}{% if npc.get('aliases') %} aka {{ npc.get('aliases') | join(', ') }}{% endif %}
{% else %}(none)
{% endfor %}

### All Quests
{% for q in all_quests -%}
- [{{ q.get('id', '?') }}] {{ q.get('title', '?') }} — {{ q.get('status', '?') }}
{% else %}(none)
{% endfor %}

### PC Conditions
{% for c in conditions -%}
- [{{ c.get('id', '?') }}] {{ c.get('label', '?') }}: {{ c.get('description', '') }}
{% else %}(none)
{% endfor %}
```

**Validation:** Render with a sample state. Assert IDs are present in rendered output. Assert no `RECENT EVENTS TO COMPACT` section appears.

---

### Tests to write or update
- `tests/test_compactor.py`:
  - `test_build_compact_messages_no_events`: assert `_build_compact_messages` result contains `MECHANICAL STATE` and no `RECENT EVENTS TO COMPACT`.
  - `test_system_prompt_renders`: render `compact_system.j2` with empty Jinja env. Assert `PART 1` and `PART 2` headings present, no `PART 2: Compacted recent events` content.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: Update `compact_system.j2` / `compact_user.j2` descriptions.

### Risks
1. The `compact_user.j2` rendering with `compendium_npcs` as a list of `(id, npc_dict)` tuples requires `{% for npc_id, npc in compendium_npcs %}` which is valid Jinja2 tuple unpacking. Verify this works with the installed Jinja2 version before shipping.
2. If the compendium is large (many NPCs), this may push prompt token count past budget. The compactor call does not go through `trim_messages`. For now this is acceptable (compactor runs infrequently). Add a REPOMAP note that this may need trimming at scale.

---

## Ambiguities requiring resolution before execution

1. **`compact_end` window math.** With `window_turns=4` and `current_turn=4`, the formula `compact_end = current_turn - (window - 1)` gives `compact_end = 1`. This means on the first compaction (turn 4), only turn 1 is compacted; turns 2, 3, 4 remain as recent. Is this the intended behavior, or should all of turns 1–4 be compacted (leaving only turn 4 as "recent after compaction")?

   Options:
   - A) `compact_end = current_turn - (window - 1)` → compact 1 turn, keep 3 as recent. Turns 5–7 are the next recent window.
   - B) `compact_end = current_turn` → compact all 4 turns, next turn starts fresh with only turn 4 as prior_history entry. This matches the user's stated intent: "The turn after (turn 5): Recent history will be only the narration from turn 4."

   **This ambiguity must be resolved before Phase 2 is executed.** If B, then `compact_end = current_turn` and `compact_start = current_turn - window + 1` (only compact the window just completed), and after compaction, `recent_turns` for the next turn will be loaded from chronicle which only has turns > compact_end, yielding 0 entries on turn 5 (correct per spec).

2. **`recent_narration` after compaction.** The spec says "recent history will be only the narration from turn 4" on turn 5. Currently `load_recent_chronicle_turns(save_dir, window_turns)` returns the last `window_turns` turns from `chronicle.md`, which includes the compacted turns (they're still in the file). Does "after compaction" mean we need to start tracking a `last_compacted_turn` offset and pass it to `load_recent_chronicle_turns` to skip already-compacted turns? Or does `load_recent_chronicle_turns` naturally handle this if compaction fires at turn 4 and we load on turn 5 (only 1 turn written since last compaction)?

   Options:
   - A) Natural — on turn 5, `load_recent_chronicle_turns(save_dir, 4)` returns turns 2–5... wait, turn 5 hasn't been written yet when narration runs. It loads turns 2, 3, 4 — still 3 entries, not 1. **This does NOT match the spec.**
   - B) Pass `last_compacted_turn` to `load_recent_chronicle_turns` as a `min_turn` filter so it only returns turns > `last_compacted_turn`. After turn 4 compaction, `last_compacted_turn=4`, so on turn 5's narration call, `load_recent_chronicle_turns(save_dir, 4, min_turn=5)` returns [] — which is also wrong (turn 5 hasn't been written).
   - C) The spec means: after compaction of turns 1–4, `recent_turns` on turn 5 = the narration from turn 4 only (the most recent completed turn). This is `load_recent_chronicle_turns(save_dir, 1)` — always just the last turn — after a compaction boundary. This requires `turn.py` to pass `min(window_turns, turns_since_last_compaction)` as `n` to `load_recent_chronicle_turns`. **This is the correct interpretation** and requires a small change to `turn.py`.

   **This ambiguity must be resolved before Phase 2.** Recommended resolution: C — add `turns_since_last_compaction` computation in `turn.py` and pass `min(window_turns, turns_since_last_compaction)` as the `n` to `load_recent_chronicle_turns`.

---

## TODO.md update

Add under **P1 — Story Logical Consistency / Context / Prompt Integrity**:

```
- **Compactor overhaul** — window/compact parity (`compact_every` removed, `window_turns` is single control), `prior_history` state field, state sanitization (NPC dedup, inventory dedup, orphaned quests/conditions/pressures) — see [`compactor-overhaul.md`](compactor-overhaul.md)
```
