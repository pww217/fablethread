# Phase 3: Mechanics enhancements, stream aliases, summary format, legacy deprecation

## Status
`open`

## Phases

3 phases: (1) state + diff commands, (2) trace + search commands, (3) mechanics improvements + stream aliases + legacy deprecation

**Dependency:** No dependency on Phase 1 or 2. Can run independently.

## Issue

The `mechanics` command omits the narrative output the player received. Its section extraction uses exact markdown header matching (brittle against prompt changes). Stream names mismatch between the skill doc (`rules`/`progress`) and the data model (`ruling`/`storytell`). Eleven legacy shell scripts duplicate `ev.py` functionality. `summary` has no machine-readable output format.

## Solution

Add narrative output to `mechanics`. Replace exact header matching with regex patterns. Add stream name aliases. Add `--format json` to `summary`. Deprecate all legacy shell scripts by replacing bodies with one-liners delegating to `ev.py`. Zero engine changes.

## Firm decisions

1. `mechanics` shows the first 500 chars of `narrate_prompt.output`, with a hint to use `compact <N> narrate` for full text. The 500-char truncation keeps the output readable while directing users to the full source.
2. `SECTION_MARKERS` is a module-level dict in ev.py. Markers are compiled to regex on module load. Adding a new marker is a one-line edit.
3. Stream aliases map user-facing names (`rules`, `progress`) to data model names (`ruling`, `storytell`). Both accepted in stream arguments.
4. Legacy scripts are not deleted. Their bodies become one-liners: `exec python3 "$(dirname "$0")/ev.py" <command> "$@"`. No deprecation message — they just forward silently.
5. `summary --format json` outputs one JSON object per line (JSONL format) to stdout.

## Non-goals

- Changing the data model stream names. Aliases only.
- Deleting legacy scripts. Repointing only.
- Changing `mechanics` output order. Adding sections, not rearranging.

## Risks, Ambiguities, and Blockers

- The exact names in the narrate user prompt sections (`### Campaign Arc` vs `## Campaign Arc`) vary across pack templates. The regex must match both `###` and `##` prefixes. Survey all pack templates: `grep -r 'Campaign Arc' packs/` to confirm `### Campaign Arc` is the only variant. The regex uses `$` end anchor to avoid matching sub-headers.
- Some legacy scripts map to ev.py commands that take different argument orders. Verify each mapping before replacing. `get-turn-viewer.sh` is currently broken (no command prefix) — the plan fixes it via the mapping table.
- `summary --format json` must not break existing downstream consumers that scrape the summary output. The default format (no `--format` flag) must be identical to current behavior.
- `SECTION_MARKERS.get(s)` silently returns `None` for unknown stop names — any caller passing an undefined marker as a stop will have it silently ignored. Always define stop markers before referencing them as stop names.

## Implementation — Phase 3: Mechanics enhancements, stream aliases, summary format, legacy deprecation

### Context files to load

- `scripts/debug/ev.py` (704 lines) — full file. Multiple small edits.
- `scripts/debug/get-*.sh` (11 files) — all legacy scripts.
- `scripts/debug/README.md` — update stream names and command table.

### Detailed steps

#### Step 3.1 — Define `SECTION_MARKERS` and replace `extract_section_by_pattern()`

**File:** `scripts/debug/ev.py`

**What:** Add a module-level config dict and update `extract_section_by_pattern()` to use it.

Add at module level (after `STREAMS`):

```python
import re

SECTION_MARKERS: dict[str, str] = {
    "gm_beat": r"^## gm_beat$",
    "campaign_arc": r"^#{1,3}\s*Campaign Arc$",
    "deescalate": r"^## deescalate$",
    "pressures": r"^## Current Pressures$",
    "rules_stakes": r"^## rules_stakes$",
    "pending_beat": r"^## pending_beat$",
    # Reserved as stop markers — not used as start markers currently
    "pacing_context": r"^## pacing_context$",
    "last_turn_narration": r"^## last_turn_narration$",
}

# Compiled once at module load
_COMPILED_SECTIONS: dict[str, re.Pattern] = {
    name: re.compile(pattern) for name, pattern in SECTION_MARKERS.items()
}
```

Replace the body of `extract_section_by_pattern()`:

```python
def extract_section_by_pattern(text: str | None, start_name: str, *stop_names: str) -> str:
    """Extract text between a section header (matched by name from SECTION_MARKERS) and the next stop header."""
    if not text or start_name not in _COMPILED_SECTIONS:
        return ""
    start_re = _COMPILED_SECTIONS[start_name]
    stop_re_list = [_COMPILED_SECTIONS.get(s) for s in stop_names if s in _COMPILED_SECTIONS]

    lines = text.splitlines()
    found = False
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if found:
            # Stop if we hit any of the stop markers
            if any(r.search(stripped) for r in stop_re_list if r):
                break
            # Skip future headers that aren't stop markers
            if stripped.startswith("#") and not any(r.search(stripped) for r in stop_re_list if r):
                continue
            if stripped:
                result.append(line)
        elif start_re.search(stripped):
            found = True
    return "\n".join(result).strip()
```

Update callers in `cmd_mechanics` to use section names instead of raw header strings:

```python
# Before (line 263):
beat = extract_section_by_pattern(storytell_event, "## gm_beat", "## pending_beat", "## pacing_context", "## last_turn_narration")

# After:
beat = extract_section_by_pattern(storytell_event, "gm_beat", "pending_beat")
```

```python
# Before (line 270):
arc = extract_section_by_pattern(narrate_user, "### Campaign Arc", "### Characters")

# After:
arc = extract_section_by_pattern(narrate_user, "campaign_arc")
```

**Why:** Regex-based matching survives header level changes (`###` → `##`). A single dict edit fixes extraction if prompt templates change. Section names make call sites self-documenting.

**Validation:** Run `python3 scripts/debug/ev.py mechanics <turn>` and verify the GM Beat and Campaign Arc sections still produce the same content as before (compare against a saved reference for one turn).

#### Step 3.2 — Add narrative output to `cmd_mechanics()`

**File:** `scripts/debug/ev.py`, function `cmd_mechanics()`

**What:** Between the "Campaign Arc" block and the "State Deltas" block, add a new section:

```python
    # Narrative output (player received)
    print("--- Narrative (player received) ---")
    narrate_output = extract_prompt(ev, "narrate")["output"]
    if narrate_output and len(narrate_output) > 500:
        print(narrate_output[:500])
        print("…")
        print(f"(full text: python3 scripts/debug/ev.py compact {ev.get('turn', '?')} narrate)")
    elif narrate_output:
        print(narrate_output)
    else:
        print("(empty)")
    print()
```

Insert between the arc section (currently line 272) and the state deltas section (currently line 274).

**Why:** Users most often need to see the prose output alongside the mechanics. Currently requires a separate `compact <N> narrate` call.

**Validation:** Run `python3 scripts/debug/ev.py mechanics <turn>` and verify the narrative section appears between Campaign Arc and State Deltas.

#### Step 3.3 — Add stream name aliases

**File:** `scripts/debug/ev.py`

**What:** Add a mapping dict and a resolver function. Update `main()` to resolve aliases before lookup.

Add at module level:

```python
STREAM_ALIASES: dict[str, str] = {
    "rules": "ruling",
    "ruling": "ruling",
    "progress": "storytell",
    "storytell": "storytell",
    "narrate": "narrate",
    "scene": "scene",
    "state": "state",
}

def _resolve_stream(name: str) -> str:
    """Map a user-facing stream name to the canonical data-model key. Dies on unknown names."""
    canonical = STREAM_ALIASES.get(name)
    if not canonical:
        print(f"Unknown stream: {name}. Valid: {', '.join(sorted(STREAM_ALIASES))}", file=sys.stderr)
        sys.exit(1)
    return canonical
```

Update all stream argument parsing in `main()` to use `_resolve_stream()`:

```python
# Before (line 635):
if stream not in STREAMS:
    print(f"Unknown stream: {stream}", file=sys.stderr)
    sys.exit(1)

# After:
stream = _resolve_stream(stream)
```

This pattern occurs in `props`, `compact`, and `prompt` commands.

Update the module-level `STREAMS` tuple to be the canonical data-model keys only (it already is — no change needed to the tuple itself).

**Why:** Users can use either naming convention. The skill doc says `progress`, the data model uses `storytell`. Both work.

**Validation:** `python3 scripts/debug/ev.py compact 5 progress` and `python3 scripts/debug/ev.py compact 5 storytell` must produce identical output.

#### Step 3.4 — Add `--format json` to `cmd_summary()`

**File:** `scripts/debug/ev.py`, function `cmd_summary()`

**What:** Accept a `--format` argument (`text` default, `json` for JSONL output). When `--format json`, print one JSON object per line instead of formatted text.

```python
def cmd_summary(events: list[dict[str, Any]], format: str = "text") -> None:
    if format == "json":
        for ev in events:
            if ev.get("kind") == "compaction":
                continue
            obj = _build_summary_json(ev)
            print(json.dumps(obj))
        return
    # ... existing text formatting ...
```

Add a helper:

```python
def _build_summary_json(ev: dict[str, Any]) -> dict[str, Any]:
    """Build a structured summary dict for one event for JSON output. All numeric fields are native types."""
    intent = _parse_ruling_intent(ev) or {}
    raw_tt = _total_tt(ev)
    return {
        "turn": ev.get("turn"),
        "streams": _stream_keys(ev),
        "user_input": (ev.get("input") or "")[:100],
        "tokens_in": int(_total_tokens_in(ev)),
        "tokens_out": int(_total_tokens_out(ev)),
        "total_tt_s": float(raw_tt.rstrip("s")) if raw_tt else 0.0,
        "ruling_intent": (intent.get("intent") or "")[:100],
        "deltas": int(_count_state_diff(ev)),
        "has_rejections": bool(_has_rejections(ev)),
    }
```

Update `main()` to parse `--format` using `_strip_flags()` (as defined in Phase 1, step 1.3):

```python
case "summary":
    flags, args = _strip_flags(args, {"--format": 1})
    fmt = flags.get("--format", "text")
    cmd_summary(events, format=fmt)
```

**Why:** Machine-readable output enables downstream tooling (jq, grep, CSV conversion). Using `_strip_flags()` keeps argument parsing consistent with Phase 1 and avoids fragile index-based extraction.

**Validation:** `python3 scripts/debug/ev.py summary --format json | python3 -m json.tool --json-lines` — must produce valid JSON objects. Default `ev.py summary` (no flag) must produce identical output to current behavior.

#### Step 3.5 — Deprecate legacy scripts

**File:** All files: `scripts/debug/get-*.sh`

**What:** Replace each script body with a one-liner that delegates to `ev.py`. No deprecation message — just forward transparently.

The `scripts/debug/README.md` already documents this pattern. The script bodies match the pattern:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" turn "$@"
```

Replace each script's body. The command name after `ev.py` maps as follows:

| Script | ev.py command |
|---|---|
| `get-turn.sh` | `turn` |
| `get-deltas.sh` | `deltas` |
| `get-mechanics.sh` | `mechanics` |
| `get-outputs.sh` | `outputs` |
| `get-summary.sh` | `summary` |
| `get-timing.sh` | `timing` |
| `get-props.sh` | `props` |
| `get-props-compact.sh` | `compact` |
| `get-prompt.sh` | `prompt` |
| `get-props-connector.sh` | `connectors` |
| `get-turn-viewer.sh` | `turn` (same as get-turn.sh) |

Each script body becomes:

```bash
#!/usr/bin/env bash
# Wrapper for `ev.py <command>`. See ev.py --help.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ev.py" <command> "$@"
```

No verification that each script's argument format matches ev.py — the README already documents them as wrappers, and the existing scripts already forward `$@` directly.

**Why:** Eliminates code duplication. The single source of truth is `ev.py`.

**Validation:** `./scripts/debug/get-turn.sh 5` must produce identical output to `python3 scripts/debug/ev.py turn 5`. `./scripts/debug/get-deltas.sh 5` must match `python3 scripts/debug/ev.py deltas 5`.

#### Step 3.6 — Update `scripts/debug/README.md`

**File:** `scripts/debug/README.md`

**What:** Update the command table to include new commands (`state`, `diff`, `trace`, `search`). Update stream name references to show both aliases. Add a note that legacy scripts are thin wrappers (already documented inline but make it prominent).

Add to the command table:

```markdown
| `ev.py state` | Current game state (reads state.yaml) |
| `ev.py diff` | State comparison between two turns |
| `ev.py trace` | Track a field across turns |
| `ev.py search` | Find turns matching criteria |
```

In the stream name references, document the aliases:
```markdown
**Stream names:** `ruling` (also `rules`), `narrate`, `scene`, `state`, `storytell` (also `progress`)
```

**Why:** Documentation keeps pace with new commands.

**Validation:** Review rendered markdown.

### Tests to write or update

No tests to write (tests temporarily removed). Manual verification against the default save.

### REPOMAP updates required

`scripts/debug/README.md` — stream aliases, new commands, legacy script deprecation (covered in Step 3.6). No changes to `docs/repomap.md`.
