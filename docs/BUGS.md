# Known Bugs

## TRACE_IMMUTABLE markers leaking into production prompts

**File:** `ccya/prompts/narrate_user.j2` (and possibly `extract_scene_user.j2`, `extract_progress_user.j2`)

**Symptom:** Rendered user prompts sent to the LLM contain `<<>>` artifacts and the text `Immutable Reference` appearing mid-prompt. Example:

```
        Acquire a fresh shipment of chemical stabilizers.

<<>>
Immutable Reference 
World State
```

**Suspected cause:** The `strip_trace_markers()` regex in `ccya/engine/markers.py` is `r"<<<TRACE_IMMUTABLE_(?:START|END)>>>\s*\n?"` — if the stripping is partially matching or the regex is not being applied at all call sites, leftover `<<>>` fragments and the `Immutable Reference` header text leak into the prompt sent to the LLM.

**Relevant code:**
- `ccya/engine/markers.py` — `strip_trace_markers()` / `strip_trace_markers_in_messages()`
- `ccya/engine/turn.py` — calls `strip_trace_markers_in_messages()` at rules (line 313), narrate (lines 495, 1055), and extraction (lines 426, 476, 524)
- `ccya/prompts/narrate_user.j2` — uses `<<<TRACE_IMMUTABLE_START>>>` / `<<<TRACE_IMMUTABLE_END>>>` markers

**Note:** The markers are intentional for eval dedup. The engine strips them before chat. The `rendered_user` in events.jsonl intentionally retains them. The bug is that stripping is not working correctly in production, or a call site is missing the strip call.
