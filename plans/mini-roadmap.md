# Mini Roadmap — Iteration Fixes (Easiest → Hardest)

## 1. Dice Roll Mechanics
**Files:** `ccya/rules.py` (lines 120-131, 172-221), `ccya/prompts/` (roll display templates)

### 1a. Critical success threshold includes modifiers
Currently `compute_band()` only checks raw_die == 1 or 12 for crit_fail/crit_success (rules.py:120-124). A roll of e.g. 11 + 1 modifier = 12 should arguably be a critical success since the final_total hits the threshold. Need to decide: should crit thresholds apply to raw_die only, or also check final_total? If including modifiers, update `compute_band()` to treat final_total >= 9 (not just raw_die == 12) as potential crit_success when the die itself is high enough (e.g., raw_die >= 10).

### 1b. Roll display: show skill name
When narration references a roll result ("X + Y = Z"), it should specify which skill Y represents, e.g., "8 + 2 (Strength) = 10". Find where rolls are rendered in prompts/narration and ensure the skill label is included from `RulesOutcome.skill`.

### 1c. Raise recent_events repeat threshold
`recent_events` currently allows similar outcomes to persist too long. Increase the dedup/similarity window so that a new event won't be added if it's too close in meaning to an existing one. This likely involves adjusting logic in `ccya/engine/turn.py` where events are appended (around line 916) or adding a similarity check before insertion.

---

## 2. Compactor — Sanitization Reasons
**Files:** `ccya/models.py` (CompactorSanitizationAction, lines 320-324), `ccya/engine/compactor.py` (_parse_compact_response, _apply_sanitization)

Add a `reason: str | None = None` field to `CompactorSanitizationAction`. Update the compact prompt (`ccya/prompts/compact_system.j2`) to instruct the LLM to include reasons. Wire the reason through `_parse_compact_response()` → `_apply_sanitization()` → event payload (compaction record at compactor.py:126-131) → server UI (server/tv.py:376-386). The sanitization display in `tv.py` should render reasons alongside each action.

---

## 3. Inventory Durability Gate
**Files:** Wherever the durability gate logic lives — likely in compactor or inventory management code. Flip the condition so that items NOT owned by the player are protected from removal (reverse original intention). This is a single conditional inversion once located.

---

## 4. Narrator Behavior & Prompts
**Files:** `ccya/prompts/` (narrator templates), any narrator-related prompt sections

### 4a. NEVER repeat/rehash narration
Add an explicit directive to the narrator system/user prompts: "NEVER repeat or rehash what has already been said in prior turns." This is a prompt-only change.

### 4b. Known characters integration
Instruct the narrator to weave known compendium NPCs into scenes when there's a natural opening, but only if they have a narrative role (not just seed-fillers). Add guidance to skip NPCs with no motivation/fear/leverage fields set — they're not ready for story integration yet.

### 4c. Prompt restructuring
Review narrator and storyteller prompt templates for accuracy issues. This is iterative refinement based on observed behavior, so scope is open but changes are localized to template files.

---

## 5. NPC Management (Names, Notes, Bios)
**Files:** Scene extractor prompts, compendium management code, npc bio/notes logic in extraction pipeline

### 5a. Bio vs notes separation
Scene extractor should distinguish persistent bios from transient notes:
- **Bio** = appearance + personality only (persistent across turns)
- **Notes** = current situation relevance to arc/player/story (transient)

Currently they're conflated. Update the scene extraction prompt and any post-processing that merges bio/notes into compendium entries.

### 5b. NPC notes staleness instead of zeroing
Instead of zeroing `npc.notes` when not updated, mark them stale (e.g., add a `_stale: bool` flag or similar). This preserves context while signaling the narrator that this info is outdated. Decision point: how to represent "stale" in the compendium model and prompt system.

### 5c. Shorter, situational NPC notes
Notes should reflect relevance to arc/player/overarching story, not just transcribe narration. Update extraction prompts to constrain note length and require narrative relevance justification.

### 5d. Generic name reduction
Too many generic NPC/location names. This likely involves improving the seed/name generation prompts or adding a naming pool/constraint in `ccya/pack.py` (SeedCompendium) or wherever names are generated during seeding/extraction.

---

## 6. State/Save Bugs
**Files:** `ccya/engine/turn.py` (_apply_thread_resolutions, lines 423-500), state persistence code

### 6a. Thread resolve outcome not saved to state
`_apply_thread_resolutions()` sets `resolution_state` and `outcome` on the thread object (lines 484-487) but may fail to persist it back into `state["arc"]`. The function returns a CampaignArc but the caller at turn.py:1364 needs to verify the arc is written back. Trace the full flow from storyteller output → `_apply_thread_resolutions()` → state mutation → save to disk.

### 6b. "Seen" empty too often
The `seen` field (likely in compendium/npc tracking) is underpopulated. Options: replace with a fallback "you are alone" narration when seen is empty, or always require at least one presence indicator. Locate where `seen` is populated and decide on the fix approach.

---

## 7. Arc System
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
