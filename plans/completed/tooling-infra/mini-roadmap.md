# Mini Roadmap — Iteration Fixes (Easiest → Hardest)

## Status
`completed` — item 7 moved to `arc-system.md`

## 1. Dice Roll Mechanics — PARTIAL
1a done (`2ac48d2`). 1b (skill name display) remains open. 1c (recent_events dedup) is NOOP — dropped.
**Files:** `ccya/rules.py` (lines 120-131, 172-221), `ccya/prompts/` (roll display templates)

### 1a. Critical success threshold includes modifiers
Done (`2ac48d2`).

### 1b. Roll display: show skill name
When narration references a roll result ("X + Y = Z"), it should specify which skill Y represents, e.g., "8 + 2 (Strength) = 10". `RulesOutcome` already has `skill`, `stat_value`, `dice`, `raw_total`, `final_total` — but `narrate_user.j2` only shows `band` and `directive`. Need to surface the skill name and roll math in the template or add guidance to the storyteller.

---

## 2. Compactor — Sanitization Reasons — DONE
Add a `reason: str | None = None` field to `CompactorSanitizationAction`. Update the compact prompt (`ccya/prompts/compact_system.j2`) to instruct the LLM to include reasons. Wire the reason through `_parse_compact_response()` → `_apply_sanitization()` → event payload (compaction record at compactor.py:126-131) → server UI (server/tv.py:376-386). The sanitization display in `tv.py` should render reasons alongside each action.

Committed `d7b3f21`.

---

## 3. Inventory Durability Gate — DONE
**Commit:** `c82a208`. Replaced with fuzzy-match inventory_remove + silent cancellation. Durability gate for inventory_add remains unchanged.
**Files:** Wherever the durability gate logic lives — likely in compactor or inventory management code. Flip the condition so that items NOT owned by the player are protected from removal (reverse original intention). This is a single conditional inversion once located.

---

## 4. Narrator Behavior & Prompts — DONE
**Completed:** `b180e12`, `a36ad79` (quality review passes), `abdfdb0` (dead code removal). Fixed: narrator dedup, NPC re-use ×3, metaphor typo, stakes→pacing directive, always-quantified contradiction, tense dangling ref, empty arrays vs omit null, beat diversity dupe coalesced. Dead render vars removed from all prompt renders.
**Files:** `ccya/prompts/narrate_system.j2`, `ccya/prompts/storytell_system.j2`

### 4a. NEVER repeat/rehash narration — DONE (implicit via anti-repetition plan + quality review fixes)

### 4b. Known characters integration — DONE (implicit via anti-repetition plan + quality review fixes)
Known NPCs woven into scenes per existing compendium guidance; narrator prompt already instructs to use known character names from compendium section.

### 4c. Prompt restructuring — DONE (`e77f6cb`)
All narrator/storyteller templates restructured with consistent 4-section hierarchy (Purpose, Output Discipline, Rules, Input). Dead code removed throughout.

---

## 5. NPC Management (Names, Notes, Bios) — DONE
**Completed:** `dd4ceee`, `36d7a76` (bio/notes tightening), `baeb29c` (anti-repetition + NPC favoring), `abdfdb0` (dead code removal). Fixed: bio schema description tightened to two-sentence format, notes constrained to one short sentence with relevance guidance, examples section added for both fields.

### 5a. Bio vs notes separation — DONE
Bio = appearance/demeanor + durable personality/facts; Notes = situational relevance to arc/player/story. Schema descriptions updated in `extract_scene_system.j2`.

### 5b. NPC notes staleness instead of zeroing — WON'T DO (no mechanism needed)

### 5c. Shorter, situational NPC notes — DONE
Notes schema description constrained; examples section added showing correct vs incorrect extraction.

### 5d. Generic name reduction — DEFERRED (blacklist approach rejected)

---

## 6. State/Save Bugs — IN PROGRESS (plan: state-save-bugs.md)
**Files:** `ccya/state/npcs.py` (apply_npc_scene_management), compendium tracking code

### 6a. Thread resolve outcome not saved to state — VERIFIED CORRECT, NO CODE CHANGE NEEDED
Data flow is correct: `_apply_thread_resolutions()` returns CampaignArc → caller merges via `_merge_arc_update()` → writes both `threads[]` and `completed_threads[]` with resolution_state + outcome fields (non-None) → `save_state()` persists to disk. If outcomes are missing, root cause is LLM not emitting thread_resolve or ID mismatch — prompt/engine issue, not persistence bug.

### 6b. "Seen" empty too often — DONE (this plan)
first_seen_turn now initialized on NPC creation in apply_npc_scene_management(); last_seen set for all new NPCs with turn/location info. Call site updated to pass current_turn_no from delta_builder.py. Fixes both sub-bugs: first_seen_turn defaults no longer needed, newly created NPCs have visible seen history immediately.

---

## 7. Arc System — DEFERRED (broad scope, needs clarification)
**Files:** `ccya/models.py` (CampaignArc, ArcThread), `ccya/engine/turn.py` (_apply_thread_resolutions)

### 7a. Remove unused arc fields
- `promotes: list[str]` on CampaignArc (models.py:46) — not used much anymore
- `unlocked_if` / `unlock_if` on ArcThread (models.py:45) — legacy field, check if still referenced

### 7b. Arc objectives too short/few turns
Current arc objectives resolve in too few turns to be readable/meaningful. Increase minimum turn count for objective completion or add evolution mechanics so completed objectives spawn new ones rather than ending the arc entirely. The objective should be "largely [unspecified — needs clarification from user]."

### 7c. Thematic question + goal context
- Remove `thematic_question` from user-facing prompts (keep it in CampaignArc model for now)
- Keep `goal_context` but move to UI-only display, not fed into narration prompts
- Remove `pc_drive` from prompts (likely remove entirely if unused)

---

## 8. Compactor — Turn Gaps
**Files:** `ccya/engine/compactor.py` (maybe_compact lines 25-63), `_extract_turns_for_compact`, chronicle reading logic

The compaction has a systematic turn gap problem:
- Turn 5 compact → missing turn 1 from bullets
- Turn 8 compact → missing turn 4
- Turn 9 compact → missing turns 4/5
- Turn 10 compact → missing turns 4/5/6

Root cause likely in `_extract_turns_for_compact()` (line 158) or the bullet-writing logic (`_write_compacted_block`). The `compact_start`/`compact_end` calculation at lines 52-54 may be off by one, or turns extracted from chronicle don't align with what gets written back. Need to trace:
1. What turn range is selected for compaction (e.g., compact_every=5 means it fires at turns 5, 10, 15...)
2. What `retain_from` calculation excludes (line 52)
3. How `_extract_turns_for_compact` reads from chronicle.md — does it miss already-compacted sections?
4. Whether bullet deduplication or the COMPACTED block parsing loses turns

The issue is that compaction fires every N turns but the turn range calculation doesn't account for previously compacted blocks properly, causing gaps in what gets included in new bullet summaries.

---

## 9. Seed System
**Files:** `ccya/engine/seed.py` (generate_seed at line 215), `_sanitize_envelope`, pack definitions (`ccya/pack.py`)

### 9a. Char creator seeds not fed to inputs
Char creation seed data is either ignored or not passed through the input pipeline. Trace where char creator seeds are generated and verify they reach the storyteller/narrator prompts as intended (likely in turn.py's message building).

### 9b. Seed item generation — items not owned by player at start
Seeds generate inventory items that don't belong to the PC at game start, causing them to appear in inventory unearned. Adjust seed logic so only starting equipment appears; other items should be discoverable through play. This involves filtering or constraining `SeedState.inventory` during generation (seed.py:36).

### 9c. Arc + seed system robustness
Both systems need cross-validation: seeds should initialize arcs properly, and arc state should survive compaction/reload cycles. This is the broadest item — scope needs clarification but likely involves ensuring seed→arc initialization is deterministic and that arc threads survive compaction sanitization (e.g., pressure_remove doesn't accidentally kill seeded arcs).
