## Master Issue List

## Legend

- **Bug** = broken behavior, engine or prompt produces wrong output against spec
    
- **Improvement** = works but could be tighter/smarter
    
- **Feature** = doesn't exist yet, needs to be built
    

---

## 🔴 Concern: State / Inventory

|#|Issue|Type|Concern|
|---|---|---|---|
|S1|Narrator invents credits spending after stack hits 0 → extractor tries to remove → delta rejected → persists for rest of run|Bug|State / Inventory|
|S2|Empty-stack item used in action should fail the action (weapon with no ammo, depleted item) — currently narration just invents the spend|Bug|State / Inventory + Prompting|
|S3|`bandages` amount drifts (state shows 3, should be 2) — amount mismatch not caught|Bug|State / Inventory|
|S4|World seed / new game generator assigns NPC-held items to player inventory|Bug|World Seed / Generator|
|S5|Item descriptions missing for non-obvious items in inventory|Improvement|World Seed / Generator|
|S6|`bruised_ribs` persists 13 turns (OVERLONG flag), then silently drops at T13 but narration still references it|Bug|State / Conditions|
|S7|Conditions with <5 conditions present not being resolved (bleeding, wounded) when they clearly should be|Bug|State / Conditions + Extraction|

---

## 🔴 Concern: Prompting — Narration

|#|Issue|Type|Concern|
|---|---|---|---|
|M1|Death spiral: bad situation has no mechanical escape valve|Bug|Engine / Mechanics|
|M2|Momentum floor (-3) has no forced break — directive too vague to be honored|Bug|Prompting / Narrate|
|M3|Player-driven de-escalation (retreat, rest) gives no narrative reward or pressure drop|Bug|Prompting / Narrate + Engine|
|M4|`breathing_room` beat not weighted toward momentum ≤ -2|Bug|Prompting / Progress Extract|
|M5|Scene pressure hard cap: up to 7 immediate in combat, needs cap of 3|Bug|Engine / pressure.py|
|M6|Pressure decay: avoidance doesn't age pressures down, only up|Bug|Engine / pressure.py|

---

## 🔴 Concern: Mechanics — Pacing / Death Spiral

|#|Issue|Type|Concern|
|---|---|---|---|
|M1|Death spiral: bad situation → no mechanical escape valve → permanent high pressure|Bug|Engine / Mechanics|
|M2|Momentum floor (-3) has no forced break mechanic — "offer a break" is narrator suggestion, not enforced|Bug|Engine / Mechanics|
|M3|Pressure has no player-driven guaranteed release — only progress extractor can remove it|Bug|Engine / Mechanics|
|M4|No reward for retreating, resting, or disengaging — narration doesn't lower pressure for de-escalation|Bug|Prompting / Narrate + Engine|
|M5|`breathing_room` beat type not biased toward when momentum ≤ -2|Bug|Prompting / Progress Extract|
|M6|Scene pressure cap: up to 7 immediate pressures in combat — needs hard cap (suggest 3)|Bug|Engine / Mechanics|
|M7|Pressure decay: pressures that player avoids don't age down, only up|Bug|Engine / Mechanics|

---

## 🔴 Concern: Compaction

|#|Issue|Type|Concern|
|---|---|---|---|
|C1|Compaction sanitization fidelity 0.25 — `pressure_remove`/`condition_remove` not logged|Bug|Compactor / Prompting|
|C2|Full 6-turn compaction may be redundant given `recent_events` ring + last 2-3 full narrations already capture facts — interval should be longer|**Improvement / Question**|**Engine / Compactor**|

---

## 🟡 Concern: Prompting — Rules / Extraction
|#|Issue|Type|Concern|
|---|---|---|---|
|R1|`intent_verb` drift at T11 (`sneak` for tackle/search) — mixed physical/social actions|Bug|Prompting / Rules|
|R2|`present_npcs` block duplicated verbatim across all 5 prompts (~150 tokens/turn waste)|Improvement|Prompting / All|
|R3|Asking for >2 NPCs in char creator gives only 2 — cap too aggressive or seed prompt issue|Bug|**World Seed / Prompting**|
|R4|Gender guidance broken — world gen assigns female soldiers etc. before game starts|Bug|**World Seed / Prompting (seed only)**|

---

## 🟡 Concern: Quests / Progress

|#|Issue|Type|Concern|
|---|---|---|---|
|Q1|Quest objectives must be positive and actionable: no "avoid X", no continuous "maintain Y"|Bug|World Seed / Quest Design|
|Q2|Quests should represent medium-term goals (3-5 turns), not micro-tasks or permanent states|Improvement|World Seed / Quest Design|
|Q3|Initial quest objectives need clearer marks — ambiguity in what "done" looks like|Improvement|World Seed / Quest Design|

---

## 🟡 Concern: Auto-Checker / Eval Harness

|#|Issue|Type|Concern|
|---|---|---|---|
|E1|`universal.npc_mention.extracted` false-positive on location names ("Crossed", "Crossing") and adverbs ("Finally")|Bug|Eval / Auto-Checker|
|E2|`progress.quest_id_collision` false-positive on re-emission of completed quest for auto-close|Bug|Eval / Auto-Checker|
|E3|Are extractors using thinking tokens without us knowing? Output token counts suggest possible hidden reasoning|Question|Engine / Observability|
|E4|`rules.rolled` assert fires on T1 and T12 — checker may be inverted on those turns|Bug|Eval / Auto-Checker|

---

## 🟢 Concern: Token / Performance

|#|Issue|Type|Concern|
|---|---|---|---|
|T1|`extraction.state` consistently 10-12% above baseline every turn — 8 warnings|Improvement|Prompting / State Extract|
|T2|Total tokens out: 177k for 13 turns — 13.6k/turn output. Extractors may be thinking|Question|Engine / Observability|
|T3|Progress extractor is largest context at 61k total (4.7k/turn) — review what's being passed|Improvement|Prompting / Progress Extract|
