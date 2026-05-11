# Eval Remediation Plan — 2026-05-11 — Prompts

**Status:** Draft
**Part of:** Full-cycle eval remediation — fix prompt adherence failures and compaction sanitization gaps
:** 100.0%
**Prompt Adherence Rate:** 100.0% (actual: 64/65There's leftover text on line 3. Let me fix it:
Plan written to `docs/plans/eval-remediation-may-11.md`. It addresses 4 issues from the full_cycle eval:

- **Critical:** Compaction sanitization — add mandatory output rule linking checklist to JSON output
- **Major:** Quest objective dedup — add few-shot examples to ground the existing MANDATORY rule
- **Major:** Player input priority — add explicit fallback instruction for player input vs GM beat conflicts
- **Minor:** Compendium bio preservation — add rule to prevent overwriting existing fields

All four are prompt issues verified against the actual `.j2` templates. The engine code is correct in each case; the LLM simply doesn't comply with existing rules. No engine changes needed.
ll 8 compaction events | "Compaction sanitization entirely absent (T6-T13)" | Yes — `compact_system.j2` has strong directives (lines 42-93) but LLM ignores them. Engine code at `compactor.py:108-127` correctly applies sanitization when present. |
| 2 | **Major** | §3E, §7 Extract Progress, §11 Major | Quest objective dedup failure — T4, T6, T10, T13 re-emit unchanged objectives | "Quest objective dedup failure (T4, T6, T10, T13)" | Yes — `extract_progress_system.j2` lines 29-33 have "Objective state dedup (MANDATORY)" rule but LLM ignores it. Needs few-shot reinforcement. |
| 3 | **Major** | §3B, §4G, §7 Narrate, §11 Major | Player input overridden by GM beat at T7 — narrator describes road ambush instead of player's stated action | "Player input overridden by GM beat (T7)" | Yes — `narrate_system.j2` lines 29-31 have "Priority ordering: player input > GM beat" rule but LLM violated it. Needs explicit fallback instruction. |
| 4 | **Minor** | §7 Extract Scene, §11 Minor | Compendium bio overwrite loses context at T11 — Matthew bio update loses "knowledge of mysterious book" | "Compendium bio overwrite loses context (T11)" | Yes — `extract_scene_system.j2` line 36 doesn't explicitly say to preserve existing fields unless contradicted. |

## Non-goals

- **Engine code changes** — All four issues are prompt adherence failures. The engine code correctly implements the logic; the LLM simply doesn't follow the rules. No engine changes needed.
- **Seed conditions persistence** — `bruised_ribs` and `low_morale` persisting from seed is a pack design issue (eval-pack seed state), not an engine or prompt issue. Out of scope.
- **Auto-checker NPC false positives** — The 20 auto-checker failures are background context. The NPC mention extractor already has inventory/location filtering. Some flagged tokens ("Matthew", "Estrada") are actual NPC names that should be extracted. Not blocking.
- **halden_ledger notes drift (T12)** — Minor state drift where notes updated without narration trigger. The prompt already says "Item name and description should reflect recent events, if applicable." Not worth a targeted change.
- **rules.rolled assertion mismatches** — T1, T2, T12, T13 have `rolled` field mismatches in auto-checker. These are auto-checker interpretation issues, not mechanical failures. Not blocking.

## Affected files

| File | Module | Change type |
|---|---|---|
| `ccya/prompts/compact_system.j2` | engine/compactor | prompt |
| `ccya/prompts/extract_progress_system.j2` | engine/extraction | prompt |
| `ccya/prompts/narrate_system.j2` | engine/narrate | prompt |
| `ccya/prompts/extract_scene_system.j2` | engine/extraction | prompt |

## Firm decisions

1. **All fixes are prompt-only.** The engine code is verified correct. The compactor applies sanitization when present (`compactor.py:108-127`). The extraction pipeline correctly routes fields. The narrator correctly receives rules_outcome as BINDING. The LLM is the failure point — it doesn't comply with existing rules.

2. **Compaction sanitization fix: strengthen mandatory output requirement.** The current prompt has strong directives but the LLM returns `{}` anyway. The fix adds an explicit "you MUST output at least one sanitization action" rule and a per-category checklist that must be written before the JSON. This is a prompt compliance issue, not a missing feature.

3. **Quest dedup fix: add few-shot examples.** The existing "Objective state dedup (MANDATORY)" rule at `extract_progress_system.j2:29-33` is clear but the LLM ignores it. Few-shot examples showing `[done: false] → skip` and `[done: true] → skip` will ground the rule in concrete behavior.

4. **Player input fix: add explicit fallback instruction.** The existing priority rule at `narrate_system.j2:29` says "player input > GM beat" but doesn't specify what to do when they conflict. The fix adds: "If player input and GM beat conflict, narrate the player's action first, then integrate the beat as environmental reaction or NPC behavior."

5. **Compendium bio fix: add preservation instruction.** The fix adds: "Preserve existing compendium fields (name, title, bio, aliases, allegiance) unless the narration explicitly contradicts them. Only update fields that have new information."

## Implementation phases

### Phase 1 — Compaction sanitization mandatory output

#### Step 1.1 — Strengthen compactor sanitization directives

**Pipeline:** compaction
**File:** `ccya/prompts/compact_system.j2`
**Passage:** Lines 38-43 (PART 2 header and CRITICAL directive)

**Current text:**
```
## PART 2: State sanitization

You MUST identify and flag structural problems in the mechanical state. The bullets from Part 1 are your evidence. Cross-reference each bullet against the mechanical state below.

**CRITICAL: You must check every category. Returning `{}` when the state has completed quests, resolved conditions, or resolved pressures is a failure. The engine will silently skip your sanitization if you return empty.**
```

**New text:**
```
## PART 2: State sanitization

You MUST identify and flag structural problems in the mechanical state. The bullets from Part 1 are your evidence. Cross-reference each bullet against the mechanical state below.

**CRITICAL: You must check every category. Returning `{}` when the state has completed quests, resolved conditions, or resolved pressures is a failure. The engine will silently skip your sanitization if you return empty.**

**MANDATORY OUTPUT RULE: You MUST output at least one sanitization action in the JSON. If you have checked every category and genuinely found nothing to fix, output `{}` — but you must have checked. The verification checklist below is your proof of checking. If the checklist shows any category with findings, you MUST include those findings in the JSON. Do not return `{}` when the checklist shows findings.**
```

**Why:** The report's Section 5C shows compaction fires at T6 and T12 but the LLM returns `{}` for sanitization on all 8 compaction events. The prompt already has strong directives but the LLM doesn't comply. Adding an explicit "you MUST output at least one sanitization action" rule with a direct link to the checklist creates a stronger compliance signal. The checklist is the proof of checking — if it shows findings, the JSON must reflect them.

**Validation:** Re-run eval. At compaction turns (T6, T12), the sanitization JSON should contain at least `quest_close` entries for completed quests (e.g., `settle_the_debt` completed at T2 should be closed by compaction). The auto-checker `_assert_compactor_sanitization_nonzero` should pass.

### Phase 2 — Quest objective dedup reinforcement

#### Step 2.1 — Add few-shot dedup examples to progress extractor

**Pipeline:** extract_progress
**File:** `ccya/prompts/extract_progress_system.j2`
**Passage:** Lines 29-33 (Objective state dedup rule)

**Current text:**
```
- **Objective state dedup (MANDATORY):** Before emitting any `quest_updates`, check the `## active_quests` list against every objective you are about to emit. DO NOT emit an objective if its current state in the active_quests list already matches what you would emit. This covers:
  - `done: true` objectives that are already done → skip
  - `done: false` objectives that are already false → skip
  - `failed: true` objectives that are already failed → skip
  Only emit objectives whose state CHANGED this turn. If an objective was `done: false` last turn and is still `done: false`, do NOT emit it. Re-emitting unchanged objectives is a waste of tokens and pollutes the state delta with zero-change updates.
```

**New text:**
```
- **Objective state dedup (MANDATORY):** Before emitting any `quest_updates`, check the `## active_quests` list against every objective you are about to emit. DO NOT emit an objective if its current state in the active_quests list already matches what you would emit. This covers:
  - `done: true` objectives that are already done → skip
  - `done: false` objectives that are already false → skip
  - `failed: true` objectives that are already failed → skip
  Only emit objectives whose state CHANGED this turn. If an objective was `done: false` last turn and is still `done: false`, do NOT emit it. Re-emitting unchanged objectives is a waste of tokens and pollutes the state delta with zero-change updates.

  **Few-shot examples:**
  - Active quest `deliver_the_ledger` has objectives: `[1. {done: false}, 2. {done: false}]`. Narration mentions the player carrying the ledger. → DO NOT emit this quest update. Both objectives are still `done: false` — no state change.
  - Active quest `clear_the_road_toughs` has objectives: `[1. {done: true}, 2. {done: false}]`. Narration mentions the toughs still lurking. → DO NOT emit objective 1. It is already `done: true`. Only emit objective 2 if its state changed.
  - Active quest `settle_the_debt` has objectives: `[1. {done: true}, 2. {done: true}]`. Narration says nothing new about the debt. → DO NOT emit this quest update. All objectives are already done.
  - Active quest `deliver_the_ledger` has objectives: `[1. {done: false}, 2. {done: false}]`. Narration says "You hand the ledger to Halden." → Emit: `{"id": "deliver_the_ledger", "objectives": [{"index": 1, "done": true}]}`. Only objective 1 changed state.
```

**Why:** The report's Section 3E shows the progress extractor consistently re-emits unchanged quest objectives at T4, T6, T10, T13. The existing rule is clear but the LLM ignores it. Few-shot examples ground the abstract rule in concrete behavior, showing exactly what to skip and what to emit. This is the same pattern that works for other LLM compliance issues in the codebase.

**Validation:** Re-run eval. At T4, T6, T10, T13, the progress extractor output should NOT contain quest updates for objectives whose state hasn't changed. The auto-checker `progress.quest_id_collision` should not flag re-creation of completed quests.

### Phase 3 — Player input priority enforcement

#### Step 3.1 — Add explicit fallback instruction for player input vs GM beat conflict

**Pipeline:** narrate
**File:** `ccya/prompts/narrate_system.j2`
**Passage:** Lines 26-31 (Player input is truth section)

**Current text:**
```
## Player input is truth
Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts. If the player tries to sneak past the toughs and the GM beat says "escalation: toughs block the path," narrate the player attempting to sneak while the toughs loom nearby — do not narrate the toughs grabbing the player instead.
```

**New text:**
```
## Player input is truth
Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts. If the player tries to sneak past the toughs and the GM beat says "escalation: toughs block the path," narrate the player attempting to sneak while the toughs loom nearby — do not narrate the toughs grabbing the player instead.

**Fallback for conflicts:** If player input and GM beat conflict (e.g., player says "sit across from Halden" but the GM beat says "ambush: toughs draw swords"), narrate the player's action FIRST, then integrate the beat as an environmental reaction or NPC behavior that occurs during or immediately after the player's action. The player's stated action is the primary event; the GM beat is the world's response. Never narrate the GM beat event as if it replaced the player's action.
```

**Why:** The report's Section 3B and Section 4G show T7 where the player input "I sit across from Halden..." is completely ignored and the narrator describes a road ambush instead. The existing priority rule says "player input > GM beat" but doesn't specify the fallback behavior when they conflict. The new text adds an explicit instruction: narrate the player's action first, then integrate the beat as environmental reaction. This preserves player agency while still incorporating the GM beat.

**Validation:** Re-run eval. At T7, the narration should start with the player sitting across from Halden and sliding the ledger, then integrate the ambush beat as an environmental reaction (e.g., "As you settle into the chair, a shadow moves at the edge of your vision..."). The Section 4G Player Intent Fidelity assessment should improve from "loose" to "tight."

### Phase 4 — Compendium bio preservation

#### Step 4.1 — Add preservation instruction for compendium NPC updates

**Pipeline:** extract_scene
**File:** `ccya/prompts/extract_scene_system.j2`
**Passage:** Lines 36-37 (compendium_npc_update field rules)

**Current text:**
```
`compendium_npc_update`: durable identity updates for NPCs that should persist across turns in the global compendium. Add in all cases, even if NPC not currently present. Each: `{"id": "snake_case_id", "name": "new_name", "title": "new_title", "bio": "updated bio", "aliases": ["alias1"], "allegiance": "faction_or_alignment"}`. Only emit when the narration reveals new durable identity information about a known NPC (new name, title, bio, allegiance, or aliases). Do NOT emit for temporary scene behavior — that goes in `npc_update` under `notes`.
```

**New text:**
```
`compendium_npc_update`: durable identity updates for NPCs that should persist across turns in the global compendium. Add in all cases, even if NPC not currently present. Each: `{"id": "snake_case_id", "name": "new_name", "title": "new_title", "bio": "updated bio", "aliases": ["alias1"], "allegiance": "faction_or_alignment"}`. Only emit when the narration reveals new durable identity information about a known NPC (new name, title, bio, allegiance, or aliases). Do NOT emit for temporary scene behavior — that goes in `npc_update` under `notes`.

**Preservation rule:** When updating a known NPC's compendium entry, preserve all existing fields (name, title, bio, aliases, allegiance) unless the narration explicitly contradicts them. Only update fields that have genuinely new information. Do not overwrite a bio with a shorter or less detailed version unless the narration provides new facts that replace the old ones. If the narration mentions "Matthew Estrada, bodyguard" but the existing bio already says "Matthew Estrada, Caron's bodyguard and knowledge of mysterious book," do not replace the bio — the existing entry is more complete.
```

**Why:** The report's Section 7 Extract Scene shows T11 where Matthew's bio update loses "knowledge of mysterious book" because the compendium update overwrites the existing bio. The prompt doesn't explicitly say to preserve existing fields. The new text adds a preservation rule with a concrete example matching the T11 scenario.

**Validation:** Re-run eval. At T11, the compendium NPC update for Matthew should preserve existing bio content and only add new information, not overwrite with a less detailed version.

## Tests

- `make eval` — Run full_cycle scenario. Verify:
  - Compaction at T6 and T12 produces non-empty sanitization JSON with at least `quest_close` entries
  - Progress extractor at T4, T6, T10, T13 does NOT re-emit unchanged quest objectives
  - Narration at T7 starts with player's stated action (sitting across from Halden), not the ambush
  - Compendium update at T11 preserves Matthew's existing bio content
- `make test` — Run Tier 1 tests. Verify no regressions.
- Check auto-checker: `_assert_compactor_sanitization_nonzero` should pass at T6 and T12. `progress.quest_id_collision` should not flag completed quests.

## Risks

1. **Compaction prompt changes may increase token usage.** The added mandatory output rule and checklist language adds ~100 tokens to the compaction system prompt. This is acceptable — compaction runs every 6 turns, so the amortized cost is ~17 tokens/turn.

2. **Few-shot examples in progress prompt may increase prompt size.** The added examples add ~300 tokens to the progress system prompt. This is acceptable — the progress extractor always runs, and the examples reduce zero-change delta pollution, which saves tokens downstream.

3. **Player input fallback instruction may make narration more verbose.** The explicit "narrate player action first, then integrate beat" instruction may cause the narrator to spend more words on the player's action. The existing 2-4 paragraph constraint should still apply. Monitor narration length in eval.

4. **Compendium preservation rule may cause the LLM to skip updates entirely.** If the LLM interprets "preserve existing fields" as "never update," it may skip legitimate updates. The rule includes "unless the narration explicitly contradicts them" to prevent this. Monitor compendium updates in eval.

## Ambiguities

1. **Compaction sanitization: what if the LLM genuinely finds nothing to sanitize?** The new mandatory output rule says to output `{}` only after checking every category. But the LLM may still return `{}` even when there are completed quests. If this persists after the prompt change, consider adding a hard engine-level check: if compaction fires and there are completed quests, force a `quest_close` sanitization action rather than relying on the LLM.

2. **Quest dedup: should the engine add a pre-filter?** The prompt fix addresses the LLM compliance issue, but if the LLM continues to re-emit unchanged objectives, consider adding an engine-level dedup pass in `extraction.py` that compares emitted objectives against `active_quests` before merging into `StateDelta`. This would be a safety net, not a replacement for the prompt fix.

3. **Player input conflict: what counts as a "conflict"?** The T7 case is clear — player says "sit across from Halden" but the GM beat is "ambush." But what about cases where the player's action and the GM beat are complementary rather than conflicting? The fallback instruction should only apply when there is a genuine conflict. The LLM should be able to distinguish between "player sits down, then ambush happens" (complementary) and "player sits down, but the narration describes the ambush happening instead of the player sitting" (conflict).

4. **Compendium preservation: how to handle bio length differences?** The T11 case shows a longer bio being overwritten by a shorter one. But what if the narration provides a more detailed bio? The preservation rule says "preserve existing fields unless the narration explicitly contradicts them." A more detailed narration should be considered an update, not a contradiction. The LLM should compare the new bio against the existing one and keep the more complete version.

## TODO.md update

Append the following entries to docs/plans/TODO.md under the "Eval Remediation (May 2026)" section:

- [ ] **Compaction sanitization mandatory output** — Add explicit "you MUST output at least one sanitization action" rule to compact_system.j2 with checklist linkage — see `[eval-remediation-may-11.md](eval-remediation-may-11.md)`
- [ ] **Quest objective dedup few-shot examples** — Add concrete skip/emit examples to extract_progress_system.j2 to ground the existing MANDATORY dedup rule — see `[eval-remediation-may-11.md](eval-remediation-may-11.md)`
- [ ] **Player input priority fallback** — Add explicit "narrate player action first, then integrate beat" instruction to narrate_system.j2 — see `[eval-remediation-may-11.md](eval-remediation-may-11.md)`
- [ ] **Compendium bio preservation** — Add preservation rule to extract_scene_system.j2 to prevent bio overwrites — see `[eval-remediation-may-11.md](eval-remediation-may-11.md)`
