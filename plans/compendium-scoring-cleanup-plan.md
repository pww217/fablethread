# Compendium Scoring and Cleanup Plan

## Purpose

Implement a scoring system for NPC compendium entries — recency + psychological richness — so the 12-slot roster includes the most relevant NPCs instead of alphabetically truncating at 10.

## Design Reference

`docs/design/compendium-scoring-cleanup-design.md`

## Problem Statement

`build_npc_roster()` caps at `max_entries=10` and sorts by presence priority then alphabetically by name. Unnamed NPCs (alias-only, no psychological fields) compete equally for roster slots with richly-developed named characters. Over a long campaign, the roster fills with forgotten or throwaway NPCs, and meaningful characters get alpha-cut.

## Constraints

- No prompt template changes — all scoring is backend-only.
- Party members (`party: true`) exempt from scoring (hard-coded to max score 6).
- Unnamed NPCs hard-coded to score 0.
- No new config keys, no new models, no new state fields.
- `turn_no` parameter added with default 0 for backwards compatibility with eval tooling.

## Non-goals

- No auto-archival of unnamed NPCs.
- No prompt injections or periodic reminders.
- No changes to `candidate_npcs` selection logic.
- No migration of existing saves.

## Solution

Add a `_compute_npc_score()` function to `npc_roster.py` that scores each NPC (0-6) by recency + psychological richness. Unnamed NPCs get 0, party members get 6. Replace the alphabetical sort with score-descending + recency-descending sort. Raise `max_entries` from 10 to 12. Add `turn_no` parameter to `build_npc_roster()` and thread it through all call sites.

## Firm decisions

1. Unnamed NPCs (name matches alias) always get score 0 — hard-coded, not computed.
2. Party members always get score 6 — never evicted from roster.
3. Score = recency (0-2) + richness (0-4) = 0-6.
4. Recency tiers: 2pt if `last_presence_turn < 5` turns ago, 1pt if `< 10`, 0pt otherwise.
5. Richness count: non-None, non-"unknown" among {motivation, fear, leverage, bond}.
6. Sort: presence priority (asc) → score (desc) → recency (desc) → name (asc).
7. `max_entries` raised from 10 to 12.
8. `turn_no` parameter added with default 0 for eval callers that don't need scoring.

## Risks, Ambiguities, and Blockers

- Eval tooling (`ccya/ev/prompt_context.py`) has its own `_build_npc_roster()` separate from the engine's `build_npc_roster()`. It's unaffected but left as-is — it doesn't score. This means eval prompt inspections will show a different roster order than live gameplay. Acceptable — eval tooling is diagnostic.

## Status
`completed`

## Phases

1 phase: core logic change + call site updates + documentation.

## Implementation — Phase 1: Scoring function, sort change, and call site wiring

### Context files to load

- `ccya/engine/npc_roster.py` (entire file — 98 lines)
- `ccya/engine/narrate.py:29-55` (`_narrate_messages()` signature and internal roster build)
- `ccya/engine/narrate.py:150-286` (`_narrate_setup()` — second `build_npc_roster` call)
- `ccya/engine/extraction/scene.py:13-40` (`_extract_scene_messages()`)
- `ccya/engine/extraction/storytell.py:22-107` (`_storytell_messages()`)
- `ccya/engine/ruling.py:199-230` (`_ruling_phase()`)
- `ccya/state/npcs.py:263-267` — unnamed NPC detection pattern
- `docs/repomap.md:25` — `npc_roster.py` entry
- `docs/architecture/OVERVIEW.md:55-58` — `build_npc_roster()` references
- `docs/architecture/prompt-variable-contracts.md:13-14` — `npc_roster` var references

### Detailed steps

#### Step 1.1 — Add `_compute_npc_score()` to `npc_roster.py`

**File:** `ccya/engine/npc_roster.py`

**What:** Add a module-level function `_compute_npc_score(entry: dict, turn_no: int) -> int` before `build_npc_roster()`.

Logic per the design doc:
- Check unnamed first (name matches alias, case-insensitive) → return 0
- Check `party is True` → return 6
- Compute recency (0-2) from `last_presence_turn` relative to `turn_no`
- Compute richness (0-4) from count of non-None, non-"unknown" among motivation/fear/leverage/bond
- Return `recency + richness`

**Why:** The scoring function is the core of the design — it determines which NPCs stay in the roster.

**Validation:** Write a minimal `/tmp/test_score.py` script that imports `_compute_npc_score` and asserts:
- unnamed returns 0 (name matches alias)
- party member returns 6
- named with 4 fields, last_seen=3, turn_no=5 → recency=2 + richness=4 = 6
- named with 0 fields, last_seen=20, turn_no=30 → recency=0 + richness=0 = 0
Run with `.venv/bin/python /tmp/test_score.py`. No failures.

#### Step 1.2 — Update `build_npc_roster()` signature and sort

**File:** `ccya/engine/npc_roster.py`

**What:**
1. Add `turn_no: int = 0` keyword parameter after `comp` (before `presence_filter`).
2. Change `max_entries: int = 10` to `max_entries: int = 12`.
3. In the non-LRU sort branch (line 88), replace the entire sort key expression `(order.get(str(e.get("presence") or ""), 3), e["name"])` with a flat 4-element tuple:
    ```python
    (
        order.get(str(e.get("presence") or ""), 3),
        -_compute_npc_score(e, turn_no),
        -(e.get("last_presence_turn") or 0),
        e["name"],
    )
    ```
4. In the LRU sort branch (line 85), add scoring as a tertiary key after the LRU index — change to `(order.get(…), lru_idx.get(…), -_compute_npc_score(e, turn_no))`. Note: `sort_by_lru=True` is never passed by any caller today — this branch is dead code. The change is for correctness if it's ever activated.

**Why:** Score-based sort replaces alphabetical. LRU branch gets scoring as a secondary key to break ties within LRU ordering.

**Validation:** `make check` passes.

#### Step 1.3 — Thread `turn_no` through `_narrate_messages()` internal call

**File:** `ccya/engine/narrate.py`

**What:** In `_narrate_messages()` (line 54), change the fallback roster build to pass `turn_no`:
```python
npc_roster = build_npc_roster(comp, turn_no=turn_no, personality_registry=ARCHETYPES)
```

**Why:** When `_narrate_messages` is called without a pre-built roster (e.g., from tests), the internal call needs the turn number for scoring.

**Validation:** `make check` passes.

#### Step 1.4 — Thread `turn_no` through `_narrate_setup()` call

**File:** `ccya/engine/narrate.py`

**What:** In `_narrate_setup()` (line 281), pass `turn_no` to `build_npc_roster()`:
```python
npc_roster=build_npc_roster(_comp, turn_no=turn_no, personality_registry=None),
```

Note: `personality_registry=None` is intentional (existing code). The `turn_no` variable is already available at line 154 in `_narrate_setup()`.

**Why:** This is the primary call site for narrator prompt assembly. Without `turn_no`, scoring defaults to 0 for all NPCs.

**Validation:** `make check` passes.

#### Step 1.5 — Thread `turn_no` through `_extract_scene_messages()` call

**File:** `ccya/engine/extraction/scene.py`

**What:** In `_extract_scene_messages()` (line 22), pass `turn_no` to `build_npc_roster()`:
```python
npc_roster = build_npc_roster(comp, turn_no=turn_no, personality_registry=ARCHETYPES)
```

The `turn_no` parameter is already available at line 18.

**Why:** Scene extraction shows the NPC roster to the LLM. It needs scored ordering.

**Validation:** `make check` passes.

#### Step 1.6 — Thread `turn_no` through `_storytell_messages()` call

**File:** `ccya/engine/extraction/storytell.py`

**What:** In `_storytell_messages()` (line 63), pass `turn_no` to `build_npc_roster()`:
```python
npc_roster = build_npc_roster(extraction_ctx.comp_this_turn, turn_no=turn_no, personality_registry=ARCHETYPES, slim=True)
```

The `turn_no` parameter is already available at line 31.

**Why:** Storytell receives the slimmed roster. Without scoring, it uses the fallback alphabetical sort.

**Validation:** `make check` passes.

#### Step 1.7 — Thread `turn_no` through `_ruling_phase()` call

**File:** `ccya/engine/ruling.py`

**What:** In `_ruling_phase()` (line 216), pass `turn_no` to `build_npc_roster()`:
```python
npc_roster=build_npc_roster(_comp, turn_no=turn_no, personality_registry=ARCHETYPES),
```

The `turn_no` variable is already available at line 204.

**Why:** The ruling phase shows the NPC roster. It needs scored ordering.

**Validation:** `make check` passes.

#### Step 1.8 — Update documentation

**File:** `docs/repomap.md` (line 25)

**What:** Update the `ccya/engine/npc_roster.py` entry to mention scoring:
```
| `ccya/engine/npc_roster.py` | NPC roster builder: presence filter, recency+richness scoring, top-12 selection |
```

**Files checked (no change needed):**
- `docs/architecture/OVERVIEW.md` — references `build_npc_roster()` by name only. Scoring is internal.
- `docs/architecture/prompt-variable-contracts.md` — `npc_roster` variable shape unchanged.
- `docs/architecture/step2a-scene.md` — references `build_npc_roster()` by name only.
- `docs/architecture/step2c-storytell.md` — same.
- `AGENTS.md` — no build commands or signposts related to `npc_roster.py`.

**Why:** Documentation must match the new behavior. Architecture docs reference the function by name, which is unchanged — only internal ordering changed.

**Validation:** No broken links or stale references.

### Tests to write or update

No existing tests to update (tests are temporarily removed during refactor per AGENTS.md). After tests return, add assertions for:
- `_compute_npc_score()`: unnamed returns 0, party returns 6, named with 4 fields at turn=3 returns 6, named with 0 fields at turn=20 returns 0.
- `build_npc_roster()`: verify high-scoring known NPCs sort before low-scoring known NPCs.
- `build_npc_roster()`: verify max_entries=12 cap still applies.
