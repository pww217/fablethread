# Turn Retry Investigation — Findings

## What we KNOW for sure

### 1. T2 chronicle.md has 0 chars content, events.jsonl shows 1291 chars narrate output
- `chronicle.md` byte 1675-1719: ONLY `\n\n` between "Turn 2" header and "Turn 3" header — zero narrative text
- Event 2 in `events.jsonl`: `narrate_prompt.output` = 1291 chars of proper noir narration prose
- All 17 events have proper structure, no errors recorded, sequential timestamps (T1: 21:32Z → T17: 22:07Z)
- Only 1 event per turn number — no evidence of retries or re-runs in this save
- `append_chronicle()` called ONLY at line 1290 in `turn.py` using same `narrative` variable as event output (line 1281)
- File modification time: Jun 2 17:07 local — but last event timestamp is T17 at 22:07Z (5 hour discrepancy, possibly timezone/APFS caching issue)

### 2. retryTurn() only removes ONE narrative-block from DOM
```javascript
// index.html line 1760-1766
const blocks = np.querySelectorAll('.narrative-block');
const lastBlock = blocks[blocks.length - 1];
lastBlock.remove();  // ONLY one block removed
fetch('/turn/delete', { method: 'POST' })  // server-side delete happens after
```

### 3. DELETE /turn/delete restores state via pre_turn_state snapshot
- `routes.py` line 245-274: loads last event, removes it + chronicle entry, saves `pre_turn_state` (state_snapshot field)
- Returns `{actions, turn}` — previous actions as buttons for re-submission
- Only deletes ONE event per call (`remove_last_event()` removes last JSONL line only)

### 4. Older turn blocks remain in DOM after retry
- Each completed turn creates a `.narrative-block` div appended to `#narrative-panel` via JS (lines 1538-1559, 1642-1720)
- Structure per block: user input echo → narration text → metrics → roll badge/outcome_summary → changes → hidden progress strip
- `retryTurn()` queries ALL `.narrative-block` elements but only removes the LAST one (`[-1]`)
- Older blocks (T2-T16+) remain as sibling nodes inside same narrative panel — never cleaned up

### 5. narrate_user.j2 rendering structure
```jinja
{# Lines 50-55: Prior History - iterates ALL prior_history items #}
{% for b in prior_history %}{{ b }}{% endfor -%}

{# Lines 57-63: Recent Turns - iterates recent_turns list #}
{% for t in recent_turns %}**T{{ t.turn }}:** {{ t.narrative }}{% endfor -%}

{# Line 65: Campaign Arc include (separate from Recent Turns) #}
{% include "sections/_arc.j2" %}
```

### 6. prior_history slicing happens in narrate.py, not template
- `narrate.py` line 76: `"prior_history": list(...get("prior_history") or [])[:-1]` — excludes last bullet (current turn's outcome_summary)
- Template iterates over ALL items passed to it — no additional filtering

### 7. load_last_narration reads chronicle.md, not events.jsonl
```python
# state/chronicle.py line 45-65
def load_last_narration(save_dir: Path, n: int) -> list[dict[str, Any]]:
    text = path.read_text()  # Reads chronicle.md directly
    matches = _TURN_HEADER.finditer(text)  # Regex on ## Turn N headers
    narrative = text[body_start:body_end].strip()  # Extracts content between headers
```

### 8. Turn Viewer reads from events.jsonl snapshots (immutable once written)
- `narrate_prompt.rendered_user` field stores the EXACT template rendering at runtime
- Turn Viewer displays this stored snapshot — it does NOT re-render templates against live state
- What you see in Turn Viewer = what was actually sent to LLM at that moment

### 9. UI-only issue confirmed by user
- T2 showing "T2:" followed immediately by Campaign Arc content is correct behavior for empty narrative text
- Prior History showing [T1] matches `prior_history[:-1]` slice when prior_history had 2 items (T1 + T2 outcome_summary)
- User acknowledged caching artifact where old input + outcome_summary mixed with new content

### 10. State structure after turn completes
```yaml
meta:
  turn: N
  prior_history:   # List of strings, max 20 bullets
    - "[T1] {outcome_summary}"
    - "[T2] {outcome_summary}"
    ...
```

## Open Questions / Things to Verify

### OQ-1: Why does T2 have 0 chars in chronicle.md but 1291 chars narrate output?
**Hypotheses:**
- H1: `append_chronicle()` called with empty narrative at persist time (race condition, crash between event write and chronicle write)
- H2: File handle not flushed before process exit/kill (Python context manager should auto-flush on normal exit)
- H3: Second process/thread overwrote/truncated chronicle.md after T2 completed but before T3 ran
- H4: `narrative.strip()` returned empty string at persist time despite LLM generating 1291 chars

**How to verify:** Check server logs around 2026-06-02T21:33Z for errors/warnings. Look for any code path that could call `append_chronicle` with different content than event output.

### OQ-2: What is the exact user workflow when they say "retry turn 2"?
**Possibilities:**
- P1: Click retry on T17 → removes last block, deletes last event (standard flow)
- P2: Manually click retry button associated with a specific older turn number
- P3: Submit new input for an existing turn number without deleting anything

**How to verify:** Ask user to describe exact sequence of clicks/inputs that led to the issue. Check if there's any way to target a non-last turn via UI buttons.

### OQ-3: What exactly persists in DOM after retry/delete?
**Known:** Only 1 `.narrative-block` removed by `retryTurn()`
**Unknown:** Are older blocks (T2-T16) showing correct content for their turns, or stale/mismatched data? Do they match server state at the moment of deletion?

**How to verify:** Add console logging in retryTurn() to count how many `.narrative-block` elements exist before/after removal. Compare DOM structure against events.jsonl after delete completes.

### OQ-4: Should `retryTurn()` remove ALL blocks that no longer have corresponding server-side data?
**Current behavior:** Only removes last block, returns previous actions as buttons
**Proposed fix:** After DELETE /turn/delete succeeds, compare remaining DOM blocks against current events.jsonl turn numbers and remove any orphaned blocks

**How to verify:** Implement a post-delete sync step that queries `/api/turns` (or similar) for list of existing turns, then removes narrative-block elements whose `data-turn-number` doesn't match.

### OQ-5: What happens when user submits new input after retry?
**Flow:** User clicks action pill → fills input field → submitTurn() creates NEW narrative-block with streaming SSE updates
**Question:** Does the new block get appended correctly alongside older blocks, or does it cause duplication/confusion in scroll position/rendering order?

### OQ-6: Why is file mtime (17:07) 5 hours before last event timestamp (22:07Z)?
**Possibilities:**
- Timezone mismatch between server clock and filesystem metadata
- APFS caching issue where mtime doesn't update properly for append-mode writes
- File was truncated/rewritten at 17:07 by some process, then repopulated

### OQ-7: Does `remove_last_chronicle_turn()` work correctly when called on a file with only 2 turns?
**Current code:** `prev_end = matches[-2].end() if len(matches) >= 2 else 0` — keeps everything up to end of T1 header, removes T2 entirely. This is correct for "remove last turn" semantics but could cause issues if called when there are only 2 turns and then a new T2 needs to be appended (chronicle.md would have proper structure after append).

### OQ-8: What's the relationship between `prior_history` bullets count and Prior History display in Turn Viewer?
**Known:** narrate.py passes `prior_history[:-1]` to template. Template iterates ALL items with no filtering. For turn 3, prior_history had 15 bullets → 14 shown in Prior History section of prompt.
**Question:** Does Turn Viewer show all 14 or does it filter/truncate? User reported seeing ONLY [T1].

### OQ-9: Is there any server-side caching that could cause stale HTML to be served for narrative blocks after retry/delete?
**Current architecture:** Narrative blocks are client-side DOM nodes created via JS (no server rendering). Side panels use htmx which DOES fetch fresh HTML from server.
**Question:** Could any part of the main narrate panel receive cached/stale content from server responses?

### OQ-10: What should happen to action pills when retry/delete occurs?
**Current behavior:** `zone.innerHTML = ''` then restored with previous actions as buttons
**Question:** Should old turn's outcome_summary badge and changes div be cleared/hidden in the UI, or are they correctly removed by `lastBlock.remove()` since they're inside narrative-block?

## Recommended Next Steps (in priority order)

1. **Fix OQ-3/OQ-4**: Add DOM cleanup to retryTurn() — after DELETE succeeds, remove ALL `.narrative-block` elements whose turn number no longer exists in server state
2. **Add debug logging** to track: count of narrative blocks before/after retry, list of existing turns from server vs DOM
3. **Fix OQ-1**: Check server logs around 2026-06-02T21:33Z for any errors during T2 persist phase; add defensive logging in `append_chronicle()` to verify narrative length matches event output
4. **Clarify user workflow** (OQ-2): Get exact click sequence that reproduces the issue
