# Plan 6: Config & UI Tweaks (One-Liners)

## Status
`completed`

## Phases

1 phase: three independent one-line changes — compaction cycle config, NPC cap constant for evals, turn viewer compaction clarity.

## Issue

Three low-effort improvements detected during triage review:

1. **Compaction cycle at 3 turns instead of desired 5:** `config.yaml` has `compact_every: 3`. The original plan notes suggest "probably 5 turns per compaction cycle" for better narrative retention before compression.
2. **NPC cap hardcoded to 8 in eval rubric only:** `engine_mirror.py:42` defines `SCENE_NAMED_NPC_CAP = 8`. This is purely an evaluation constant — not enforced at runtime. If the desired cap should be raised to 10 for testing purposes, just change this one line.
3. **Turn viewer compaction cards lack visual linkage:** Compactions are displayed as separate cards with `compact_start` and `compact_end` fields available in event data (`tv.py:342-344`) but the UI doesn't explicitly show which raw turns were compacted into each event. Users can't trace "compaction at T6 covers content from T1-T3" without cross-referencing turn numbers manually.

## Solution

Phase 6 makes three independent one-line changes: update `compact_every` in config.yaml, change NPC cap constant in engine_mirror.py, and add a derived field to compaction event rendering that shows the raw turn range as "Turns N–M" text alongside bullet count.

## Firm decisions

1. `compact_every` changed from 3 to 5 only — no code changes needed since validation already supports any positive integer (`_validate_compactor_config()`).
2. NPC cap changed from 8 to 10 in eval rubric only — this does not affect runtime behavior or compaction logic (there is no runtime NPC cap enforcement; only LLM prompt guidance at `extract_scene_system.j2:117` saying "Limit npc_add to at most 3 per turn").
3. Compaction clarity improvement adds a derived display field `"turn_range": "Turns {compact_start}–{compact_end}"` to compaction event dicts in tv.py. This is rendered in the HTML template as part of the compaction card header alongside bullet count and sanitization badge.

## Non-goals

- Does not change compaction logic, chronicle parsing, or sanitization behavior.
- Does not add collapsible/expandable UI for viewing compacted content details (already exists via `bullets_preview`).
- Does not modify runtime NPC management — only the eval rubric constant.
- Does not refactor turn viewer architecture or data model.

## Risks, Ambiguities, and Blockers

**Risk:** Changing `compact_every` from 3 to 5 means chronicle history is retained raw for longer before compression. This increases file size slightly but improves replayability of recent turns. Acceptable trade-off per original plan notes.

**Ambiguity:** For compaction clarity — should the turn range show inclusive or exclusive bounds? Inclusive: "Turns {compact_start}–{compact_end}" matches Python convention and is what users expect (the compacted content came from those exact turns). This matches existing `compact_start`/`compact_end` semantics in event data.

**Blocker:** None. All three changes are independent one-liners with no cross-module impacts.

---

## Implementation: Config & UI One-Liners

### Context files to load
- `config.yaml` — game section, line 25 (`compact_every`)
- `ccya/eval/engine_mirror.py` — SCENE_NAMED_NPC_CAP constant at line 42
- `ccya/server/tv.py` — compaction event rendering at lines 340-354

### Detailed steps

#### Step 6.1 — Change compact_every from 3 to 5 in config.yaml

**File:** `config.yaml`

**What:** On line 25, change:
```yaml
compact_every: 3
```
to:
```yaml
compact_every: 5
```

**Why:** Original plan notes suggest "probably 5 turns per compaction cycle" for better narrative retention. Compacting every 3 turns compresses history more aggressively; 5 turns gives players more raw turn context before compression while still preventing chronicle from growing unbounded. No code changes needed — validation already supports any positive integer.

**Validation:** Run `make check`. Config file is YAML only — no Python imports or runtime behavior to verify beyond confirming the server loads it without errors on restart.

#### Step 6.2 — Change SCENE_NAMED_NPC_CAP from 8 to 10 in engine_mirror.py

**File:** `ccya/eval/engine_mirror.py`

**What:** On line 42, change:
```python
SCENE_NAMED_NPC_CAP: int = 8
```
to:
```python
SCENE_NAMED_NPC_CAP: int = 10
```

**Why:** Eval rubric constant controls the NPC cap check in `universal_asserts.py` (line 448-464) which flags scenes with more than N named NPCs. Raising from 8 to 10 allows slightly larger cast sizes during evaluation testing without false-positive rubric failures. This is purely an eval concern — runtime code has no NPC cap enforcement.

**Validation:** Run `make check`. No Python logic changes — only a constant value update in the eval module. Existing scenarios with ≤8 NPCs unaffected; those with 9-10 NPCs will now pass instead of flagging yellow.

#### Step 6.3 — Add turn_range derived field to compaction events in tv.py (optional)

**File:** `ccya/server/tv.py` + `ccya/templates/_turn_viewer.html`

**What:** In the compaction event rendering block (lines 340-354), add a derived `"turn_range"` key that formats compact_start/compact_end into human-readable text:
```python
"turn_range": f"Turns {int(ev.get('compact_start') or 0)}–{int(ev.get('compact_end') or 0)}",
```

**Note:** The raw fields `ev["compact_start"]` and `ev["compact_end"]` are already available in the compaction event dict. If the HTML template can format these directly (e.g., via Alpine.js expression like `"Turns " + t.compact_start + "\u2013" + t.compact_end`), this derived field is unnecessary — adding it would duplicate data that's already accessible. Only add `turn_range` if the template cannot easily derive the formatted string from raw fields, or if multiple display locations need the same formatting (DRY benefit).

The HTML template for compaction cards can then display this alongside bullet count:
```html
<span x-text="t.turn_range || 'Turns ' + t.compact_start + '\u2013' + t.compact_end"></span>
```

**Why:** Compaction events have the raw turn range data but don't expose it as a formatted field. Adding `"turn_range"` makes the linkage explicit: users immediately see "Turns 1–3" on the compaction card header rather than having to mentally map `compact_start=0, compact_end=2` (or whatever indexing convention is used). One line of derived data with no logic changes — or alternatively, derive in template only.

**Validation:** Run `make check`. No behavioral changes — same event structure plus one additional derived field (if added), or purely a template change (if deriving in HTML only).

### Tests to write or update

No automated tests needed per AGENTS.md (tests temporarily removed during refactor). Manual verification:
- Load config.yaml and confirm `compact_every` is 5
- Run eval scenarios with NPC counts near the cap boundary — verify rubric passes at ≤10 NPCs
- Open turn viewer for a game that has undergone compaction — verify "Turns N–M" text visible on compaction cards

### REPOMAP updates required

None. All changes are:
- `config.yaml`: scalar value change only, no schema impact
- `ccya/eval/engine_mirror.py`: constant update in eval rubric module
- `ccya/server/tv.py`: one derived field added to event dict — no interface or model changes
