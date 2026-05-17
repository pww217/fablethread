# Fix ExtractionContext Delta Divergence and Compactor Partial-Write Risk

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 00 | Review & ambiguity resolution | Verified `apply_delta` returns `(new_state, recent_events_evicted)` — NOT `(new_state, applied, rejected)`. No file I/O side effects. `scene_tags` field exists on `StateDelta`. Test files `tests/test_compactor.py` and `tests/test_extraction_context.py` already exist. |
| 01 | Compactor atomic write | Make `_write_compacted_block` write to a temp file then atomic-rename, matching the pattern used for `state.yaml` |
| 02 | ExtractionContext via apply_delta | Replace manual delta replay in `_build_extraction_context` with a `deepcopy(state)` → `apply_delta()` → read-back pattern |

## Objective
Two independent correctness bugs exist in the engine's extraction and compaction paths.

**Bug 1 (compactor):** `maybe_compact()` in `ccya/engine/compactor.py` mutates `state` in-memory and calls `_write_compacted_block()` to modify `chronicle.md` before those mutations are validated to be coherent. `_write_compacted_block` removes compacted turn sections from `chronicle.md` by writing directly to the file. If the LLM parse or sanitization step raises mid-way (or produces garbage), the chronicle turns are already deleted and the in-memory state mutations are lost — the saved `state.yaml` (written by the caller after `maybe_compact` returns) will be inconsistent with the now-truncated chronicle. The fix is temp-file + `os.replace()` for the chronicle write, exactly as `state.yaml` already does.

**Bug 2 (extraction context):** `_build_extraction_context()` in `ccya/engine/extraction.py` hand-rolls a reimplementation of `apply_delta()`'s merge logic to compute what the world looks like after stream 1 and stream 2 deltas are applied. This reimplementation can drift from `apply_delta()` whenever validation rules in `ccya/state/delta.py` change. Stream 3 (progress extraction) then reasons about a world state that diverges from what `apply_delta()` will actually write. The fix is to call `apply_delta()` on a `copy.deepcopy(state)`, read the resulting dict, and discard the copy.

## Non-goals
- Do not change `apply_delta()`'s signature or validation logic.
- Do not change the `_ExtractionContext` dataclass fields — only change how they are populated.
- Do not add rollback for the `state.yaml` write (already handled by the caller's atomic pattern).
- Do not change `maybe_compact()`'s return type or calling convention.
- Do not add new log keys beyond those already documented in `AGENTS.md`.

---

## Implementation — Phase 01: Compactor atomic write

### Files to pull for context
- `ccya/engine/compactor.py` — full file; the change is in `_write_compacted_block` and its call site in `maybe_compact`.
- `ccya/state/delta.py` — read the atomic write helper (if any) to match the pattern. If none exists, use stdlib `pathlib` + `os.replace`.

### Detailed steps

#### Step 1.1 — Rewrite `_write_compacted_block` to use atomic rename

**File:** `ccya/engine/compactor.py`

**What:** Change `_write_compacted_block` to write the modified chronicle text to a sibling temp file (`chronicle.md.tmp`), then call `os.replace()` to atomically swap it into place. Remove the direct `path.write_text(text)` call at the end of the function.

**Why:** `os.replace()` is atomic on POSIX (rename syscall). If the process crashes or raises between the write and the rename, the original `chronicle.md` is untouched. This is the same invariant `state.yaml` enjoys via its caller's atomic write pattern.

**Code Snippet**
```python
import os  # add to top-level imports if not already present

def _write_compacted_block(
    save_dir: Path,
    bullets_text: str,
    compact_start: int,
    compact_end: int,
) -> None:
    """Write COMPACTED block to chronicle.md and remove compacted turn sections.

    Uses a temp file + atomic rename so a crash mid-write cannot corrupt
    the existing chronicle.
    """
    path = save_dir / "chronicle.md"
    if not path.exists():
        return

    text = path.read_text()
    existing = _COMPACTED_HEADER.search(text)

    if existing:
        block_end = existing.end()
        remaining = text[block_end:]
        next_header = _TURN_HEADER.search(remaining)
        if next_header:
            block_end = block_end + next_header.start()
        new_block = f"\n{bullets_text}\n"
        text = text[:block_end] + new_block + text[block_end:]
    else:
        turn_match = _TURN_HEADER.search(text)
        if turn_match:
            insert_pos = turn_match.start()
            new_block = f"## COMPACTED\n{bullets_text}\n\n"
            text = text[:insert_pos] + new_block + text[insert_pos:]
        else:
            text += f"\n## COMPACTED\n{bullets_text}\n"

    matches = list(_TURN_HEADER.finditer(text))
    turns_to_remove = {int(m.group(1)) for m in matches if int(m.group(1)) <= compact_end}
    if turns_to_remove:
        next_header_start: list[int] = []
        for i in range(len(matches)):
            if i + 1 < len(matches):
                next_header_start.append(matches[i + 1].start())
            else:
                next_header_start.append(len(text))
        new_text_parts: list[str] = []
        prev_end = 0
        for i, m in enumerate(matches):
            turn_num = int(m.group(1))
            section_end = next_header_start[i]
            if turn_num in turns_to_remove:
                new_text_parts.append(text[prev_end:m.start()])
            else:
                new_text_parts.append(text[prev_end:section_end])
            prev_end = section_end
        text = "".join(new_text_parts)

    tmp_path = path.with_suffix(".md.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    os.replace(tmp_path, path)
```

**Validation:** After applying this step, run `grep -n "path.write_text" ccya/engine/compactor.py` — should return no results inside `_write_compacted_block`. Confirm `os.replace` appears once in that function. Confirm `import os` is present at the top of the file.

#### Step 1.2 — Add `encoding` arg to `path.read_text()` call in `_write_compacted_block`

**File:** `ccya/engine/compactor.py`

**What:** Change the `path.read_text()` at the top of `_write_compacted_block` to `path.read_text(encoding="utf-8")` to match the write call.

**Why:** Consistency and correctness on systems where the default encoding is not UTF-8.

**Code Snippet**
```python
    text = path.read_text(encoding="utf-8")
```

**Validation:** Both read and write inside `_write_compacted_block` now specify `encoding="utf-8"`.

### Tests to write or update

**File:** `tests/test_compactor.py` (create if it does not exist; check first with `ls tests/`)

**`test_write_compacted_block_atomic_on_crash`**
- Setup: Create a temp `save_dir` with a minimal `chronicle.md` containing one turn section.
- Monkeypatch `os.replace` to raise `OSError` after the `.tmp` file is written.
- Call `_write_compacted_block(save_dir, "- [T1] bullet", 1, 1)`.
- Assert: the original `chronicle.md` is unchanged (OSError raised, replace never completed).
- Assert: `chronicle.md.tmp` exists (the write happened, the rename did not).

**`test_write_compacted_block_no_tmp_left_on_success`**
- Setup: Create a temp `save_dir` with a minimal `chronicle.md`.
- Call `_write_compacted_block(save_dir, "- [T1] bullet", 1, 1)`.
- Assert: `chronicle.md.tmp` does not exist after the call.
- Assert: `chronicle.md` contains `## COMPACTED` and the bullet.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md`: Under the `compactor.py` section, add a note that `_write_compacted_block` uses atomic rename (`os.replace`) for crash safety.

### Risks
1. On Windows, `os.replace()` can fail if the destination is open in another process. Mitigation: this codebase targets macOS/Linux per AGENTS.md; no action needed.
2. If `save_dir` is on a filesystem that does not support atomic rename (e.g., some NFS mounts), `os.replace` may not be truly atomic. Mitigation: out of scope for this fix; document as a known limitation.

---

## Implementation — Phase 02: ExtractionContext via apply_delta

### Files to pull for context
- `ccya/engine/extraction.py` — full file; changes are in `_build_extraction_context`.
- `ccya/state/delta.py` — read the full `apply_delta` function signature and return type before writing any code. Confirm: does it accept `dict[str, Any]` and return `(dict[str, Any], applied, rejected)` or similar? Verify exact return shape.
- `ccya/models.py` — confirm `StateDelta` model fields, specifically which fields `apply_delta` expects on the delta object.

**STOP:** Do not proceed with this phase until you have read `ccya/state/delta.py` in full and confirmed the exact signature of `apply_delta`. If the signature does not match the assumption below, surface the discrepancy as an ambiguity and do not proceed.

**Actual signature (confirmed from `ccya/state/delta.py:149-151`):**
```python
def apply_delta(
    state: dict[str, Any], delta: StateDelta, *, recent_events_max: int = 20, current_turn_no: int | None = None,
) -> tuple[dict[str, Any], bool]:
    # returns (new_state, recent_events_evicted)
    # Internally does copy.deepcopy(state) — never mutates the input dict
    ...
```

### Detailed steps

#### Step 2.1 — Add `copy` import to `extraction.py`

**File:** `ccya/engine/extraction.py`

**What:** Add `import copy` to the stdlib imports at the top of the file.

**Why:** Required for `copy.deepcopy(state)` in the next step.

**Code Snippet**
```python
import copy
```

**Validation:** `import copy` appears in the imports block. No other imports changed.

#### Step 2.2 — Replace `_build_extraction_context` body with apply_delta-based approach

**File:** `ccya/engine/extraction.py`

**What:** Rewrite `_build_extraction_context` to:
1. Build a combined `StateDelta` from the ops in `scene_result` and `state_result`.
2. Call `apply_delta()` on `copy.deepcopy(state)` with that delta.
3. Read the resulting state dict to populate `_ExtractionContext` fields.
4. Discard the copied state.

**Why:** This eliminates the hand-rolled reimplementation and ensures stream 3 always sees exactly what `apply_delta()` will write — including any validation rejections. If `apply_delta` rejects an NPC add, stream 3 correctly sees that NPC as absent.

**Important:** Before building the `StateDelta`, you must confirm the exact field names expected by `StateDelta` by reading `ccya/models.py`. The snippet below uses the field names visible in the existing `_build_extraction_context` code; adjust to match what `StateDelta` actually accepts.

**Code Snippet**
```python
def _build_extraction_context(
    state: dict[str, Any],
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
) -> _ExtractionContext:
    """Compute this-turn derived context from the two upstream extraction results.

    Calls apply_delta() on a deep copy of state so the progress extractor's
    view of NPCs, inventory, and conditions is guaranteed to match what
    apply_delta() will actually write — including any validation rejections.
    Does NOT mutate ``state``.
    """
    from ccya.state.delta import apply_delta  # local import to avoid circular deps

    # Build a combined StateDelta from scene + state extraction results.
    # Only include the ops that affect the fields _ExtractionContext tracks.
    combined_delta = StateDelta(
        npc_add=list(scene_result.npc_add or []),
        npc_remove=list(scene_result.npc_remove or []),
        npc_update=list(scene_result.npc_update or []),
        compendium_npc_update=list(scene_result.compendium_npc_update or []),
        location_change=scene_result.location_change,
        scene_tags=list(scene_result.scene_tags or []),
        inventory_add=list(state_result.inventory_add or []),
        inventory_remove=list(state_result.inventory_remove or []),
        inventory_update=list(state_result.inventory_update or []),
        pc_condition_add=list(state_result.pc_condition_add or []),
        pc_condition_remove=list(state_result.pc_condition_remove or []),
    )

    state_copy = copy.deepcopy(state)
    post_state, _evicted = apply_delta(state_copy, combined_delta)

    # Read context fields from the post-apply state.
    post_scene = post_state.get("scene") or {}
    post_pc = post_state.get("pc") or {}

    # location: prefer scene_result.location_description for the description
    # since apply_delta writes the location_change name/id but the prose
    # description comes from the extraction result directly.
    location_this_turn = dict(post_state.get("location") or {})
    if scene_result.location_description:
        location_this_turn["description"] = scene_result.location_description

    return _ExtractionContext(
        present_npcs_this_turn=list(post_scene.get("present_npcs") or []),
        location_this_turn=location_this_turn,
        scene_tags_this_turn=list(post_scene.get("tags") or []),
        scene_pressure_this_turn=list(post_scene.get("scene_pressure") or []),
        inventory_this_turn=list(post_state.get("inventory") or []),
        conditions_this_turn=list(post_pc.get("conditions") or []),
    )
```

**Validation:**
- `grep -n "_build_extraction_context" ccya/engine/extraction.py` — should show the function definition and any call sites.
- Confirm the old manual loops (the `for op in (scene_result.npc_remove or []):` blocks etc.) are fully removed.
- Confirm `copy.deepcopy` is called exactly once.
- Confirm the function still returns an `_ExtractionContext`.

#### Step 2.3 — Verify StateDelta field names match (RESOLVED)

**Status:** All fields used in the Phase 02 `StateDelta(...)` constructor exist on the model:
- `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` — present (lines 300-302)
- `location_change` — present (line 289)
- `scene_tags` — present (line 293)
- `inventory_add`, `inventory_remove`, `inventory_update` — present (lines 272-274)
- `pc_condition_add`, `pc_condition_remove` — present (lines 291-292)

No field name corrections needed.

**File:** `ccya/models.py`

**What:** This is a verification-only step. Read the `StateDelta` model definition and confirm every field name used in the `StateDelta(...)` constructor in Step 2.2 exists on the model. If any field name is wrong, correct it before proceeding.

**Why:** `StateDelta` is a Pydantic model; unknown fields may raise or silently be dropped depending on model config. Getting this wrong means `apply_delta` sees an incomplete delta.

**Validation:** `python -c "from ccya.models import StateDelta; print(StateDelta.model_fields.keys())"` — every field passed in Step 2.2 must appear in the output.

### Tests to write or update

**File:** `tests/test_extraction_context.py` (create new)

**`test_build_extraction_context_respects_apply_delta_rejection`**
- Purpose: prove that when `apply_delta` rejects an `inventory_remove` op (e.g., item not in inventory), the `_ExtractionContext` inventory does NOT show the item as removed.
- Setup: state with inventory `[{"id": "sword", "amount": 1}]`. `state_result` has `inventory_remove=[{"id": "sword"}]`. Monkeypatch `apply_delta` to return `(state_copy_unchanged, {}, [{"field": "inventory_remove", "value": "sword", "reason": "not found"}])` — simulating rejection.
- Call `_build_extraction_context(state, scene_result_empty, state_result)`.
- Assert `ctx.inventory_this_turn` still contains `{"id": "sword", ...}`.

**`test_build_extraction_context_npc_add_flows_through`**
- Purpose: confirm an accepted npc_add appears in `present_npcs_this_turn`.
- Setup: state with `scene.present_npcs=[]`. `scene_result` has `npc_add=[NpcAddOp(id="elara", name="Elara")]`.
- Call `_build_extraction_context(state, scene_result, state_result_empty)`.
- Assert `"elara"` appears in `[n["id"] for n in ctx.present_npcs_this_turn]`.

**`test_build_extraction_context_does_not_mutate_state`**
- Setup: any state dict with at least one inventory item.
- Call `_build_extraction_context(state, scene_result_with_inventory_remove, state_result_empty)`.
- Assert the original `state["inventory"]` is unchanged after the call.

Use `FakeLLM` patterns only if these tests require an LLM call — they should not; `_build_extraction_context` is synchronous and pure after this change.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md`: Update the `extraction.py` section. Remove any description of `_build_extraction_context` as "hand-rolling delta application." Replace with: "`_build_extraction_context` calls `apply_delta()` on a deep copy of state to derive the post-turn world view for stream 3. The copy is discarded; `state` is never mutated."

### Risks
1. **Circular import:** `apply_delta` is in `ccya.state.delta`; `extraction.py` is in `ccya.engine`. If importing `apply_delta` at module level creates a circular dependency, the local import inside the function (as shown in the snippet) resolves it. Verify at test time.
2. **`apply_delta` has I/O side effects:** If `apply_delta` writes to disk or logs structured events, those will fire on the throwaway copy. Mitigation: read `ccya/state/delta.py` in full before execution. If side effects exist beyond dict mutation and logging, surface this as an ambiguity and do not proceed until resolved.
3. **Performance:** `copy.deepcopy(state)` on a large state dict adds latency on every turn. For typical game state (< 1MB), this is negligible. If profiling shows otherwise, switch to `json.loads(json.dumps(state))` which is faster for JSON-serializable dicts.
4. **`StateDelta` field coverage:** If `SceneExtractResult` or `StateExtractResult` have ops that don't map cleanly to `StateDelta` fields, those ops will be silently omitted from the combined delta. The executor must verify field-by-field coverage during Step 2.3.

## Ambiguities — All resolved

1. **`apply_delta` return type:** ✅ RESOLVED. Actual signature is `apply_delta(state, delta, *, recent_events_max, current_turn_no) -> (new_state, recent_events_evicted)`. Phase 02 snippet updated to destructure as `post_state, _evicted = apply_delta(...)`. `apply_delta` internally does `copy.deepcopy(state)` at line 152, so calling it on a deepcopy is redundant but harmless — it returns a new dict.

2. **`apply_delta` side effects beyond dict mutation:** ✅ RESOLVED. `apply_delta` has NO file I/O side effects. It only does dict mutation and logging (`_log.info`). Calling it on a throwaway copy is safe — no double-emit risk.

3. **`StateDelta` field names for `scene_tags`:** ✅ RESOLVED. `StateDelta` has a `scene_tags` field (line 293). `apply_delta` handles it at lines 354-361 (sets `state["scene"]["tags"]` and manages `combat_started_turn`). Including it in the combined delta is correct.

4. **Test files:** `tests/test_compactor.py` (929 lines) and `tests/test_extraction_context.py` (73 lines) already exist. Phase 01 and Phase 02 should UPDATE existing tests rather than create new files.
