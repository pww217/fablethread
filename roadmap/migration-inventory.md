# Linear → Roadmap Migration Inventory

Generated: 2026-06-21
Source: Linear team `TICK`, project `CCYA` (80 total tickets)

## Summary

| Category | Count | Destination |
|---|---|---|
| **Active (Idea/Backlog/Validating)** | 25 | `roadmap/features/` or `roadmap/bugs/` |
| **Completed** | 25 | `roadmap/archive/` (status: `done`) |
| **Canceled (unique)** | 16 | `roadmap/archive/` (status: `canceled`) |
| **Canceled duplicates** | 8 | Skip (recreated under new bucket system) |
| **Bucket parents** | 6 | Skip (organizational artifacts) |
| **Total** | **80** | **66 files created** |

## Status mapping

| Linear status | Roadmap status | Notes |
|---|---|---|
| `Idea` | `idea` | For features; no bugs in this status |
| `Backlog` | `scoping` (feature) / `new` (bug) | Needs scoping before planning |
| `Validating` | `validated` | Being verified |
| `Completed` | `done` | Finished work → archive |
| `Canceled` | `canceled` | Abandoned → archive |

## Priority → urgency mapping

| Linear priority | Roadmap urgency |
|---|---|
| 1 (Urgent) | 1 |
| 2 (High) | 2 |
| 3 (Medium) | 3 |
| 4 (Low) | 4 |
| 0 (None) | 4 |

## Edge cases found

### 7 duplicate pairs (14 tickets)

These are the same work item in both Canceled (old "World" bucket era) and active/Completed (new bucket system). Keep only the non-Canceled version.

| Old (Canceled) | Replacements | Resolution |
|---|---|---|
| TICK-60 | TICK-86 (Canceled) | Skip both (both canceled) |
| TICK-61 | TICK-87 (Completed) | Keep TICK-87 |
| TICK-62 | TICK-88 (Idea) | Keep TICK-88 |
| TICK-63 | TICK-89 (Backlog) | Keep TICK-89 |
| TICK-64 | TICK-90 (Backlog) | Keep TICK-90 |
| TICK-65 | TICK-91 (Backlog) | Keep TICK-91 |
| TICK-66 | TICK-92 (Completed) | Keep TICK-92 |

### Missing type label (1 ticket)

TICK-42 — no `Bug`/`Feature`/`Improvement` label, no bucket, no parent. Title: "Consolidate EV checkers — fix requires_fields, logic bugs, runner issues". Likely `Bug` + `Tooling`. Needs manual triage.

### Missing bucket label (10 tickets)

These are real tickets with no bucket label. Some have a type-only label (one label only), some have two labels but neither is a bucket (e.g., TICK-40 has `UI, Feature` — `UI` is a title prefix, not a bucket). Need manual bucket assignment.

Affected: TICK-11, TICK-18, TICK-19, TICK-20, TICK-23, TICK-42, TICK-44, TICK-46, TICK-47, TICK-49

### Label order anomalies (3 tickets)

Labels present but in wrong order (bucket first instead of type first). Not a blocker — migration script should identify type by value not position.

Affected: TICK-40, TICK-89, TICK-90

### Bucket parents to skip (6 tickets)

These are Linear organizational artifacts with no real content. TICK-53 to TICK-58.

---

## Full ticket inventory

### → `roadmap/archive/` (Completed — `status: done`)

| TICK | Title | Priority | Type | Bucket | Proposed slug |
|---|---|---|---|---|---|
| TICK-18 | Compendium alias priority and naming strategy | 3 | Feature | *(missing)* | compendium-alias-priority-naming-strategy |
| TICK-22 | [Conditions] Condition age display + system guidance | 3 | Improvement | Extraction | conditions-condition-age-display-guidance |
| TICK-23 | Fix ev.py play seed generation and default timeout for dynamic packs | 0 | Bug | *(missing)* | fix-ev-play-seed-generation-default-timeout |
| TICK-27 | [UI] Purple highlighting too intense in delta/summary | 3 | Improvement | UI | ui-purple-highlighting-intense-delta-summary |
| TICK-28 | [UI] Load game doesn't work on mobile | 1 | Bug | UI | ui-load-game-mobile |
| TICK-29 | [UI] Outcome in chronicle tab + other info | 3 | Feature | UI | ui-outcome-chronicle-tab |
| TICK-32 | [NPC] Character highlighting/state differentiator in scene | 3 | Improvement | Extraction | npc-character-highlighting-state-scene |
| TICK-34 | [State] State extractor emits future transactions as present | 2 | Bug | Extraction | state-extractor-future-transactions |
| TICK-37 | [State] Inventory change reason emits when not needed, reasons wrong | 2 | Bug | Extraction | state-inventory-change-reason-wrong |
| TICK-40 | Difficulty reasoning tooltip + more tooltips throughout | 3 | UI | Feature | difficulty-reasoning-tooltip |
| TICK-41 | [NPC] NPC compendium overhaul — last_seen, last action, alias priority | 3 | Feature | Extraction | npc-compendium-overhaul-last-seen-alias |
| TICK-42 | Consolidate EV checkers — fix requires_fields, logic bugs, runner issues | 2 | *(missing)* | *(missing)* | consolidate-ev-checkers |
| TICK-44 | Thread ID mismatch — Storyteller emits creature_ambush_threat, sanitizer adds creature_ambush | 2 | Bug | *(missing)* | thread-id-mismatch |
| TICK-46 | 100% empty ruling.reason — All condition additions have empty ruling.reason | 3 | Bug | *(missing)* | empty-ruling-reason |
| TICK-47 | Goal_update format mismatch — Storyteller emits free-form text, sanitizer requires structured dict | 2 | Bug | *(missing)* | goal-format-mismatch |
| TICK-52 | [Storytell] Sanitizer tends to replace thread updates with exact text | 2 | Improvement | World Building | storytell-sanitizer-replaces-thread-updates |
| TICK-67 | [State] Choices show IDs/present tense | 1 | Bug | Extraction | state-choices-ids-present-tense |
| TICK-73 | [NPC] Departed reason in UI | 0 | Improvement | Extraction | npc-departed-reason-ui |
| TICK-75 | [NPC] NPC bonds display bug | 0 | Improvement | Extraction | npc-npc-bonds-display-bug |
| TICK-76 | [NPC] NPC presence gaps | 0 | Feature | Extraction | npc-presence-gaps |
| TICK-87 | Sanitizer dormant vs resolve | 0 | Improvement | World Building | sanitizer-dormant-vs-resolve |
| TICK-92 | Stale thread prompt trim | 0 | Improvement | World Building | stale-thread-prompt-trim |
| TICK-93 | [Scene] Thread urgency locks phase cycle into combat spiral | 3 | Improvement | World Building | scene-thread-urgency-combat-spiral |
| TICK-94 | [UI] Unify roll and non-roll outcome badges into single element | 3 | Improvement | UI | ui-unify-roll-outcome-badges |
| TICK-96 | [State] Remove PLAYER_CONDITIONS_MAX mechanic | 0 | Improvement | Tech Debt | state-remove-player-conditions-max |

### → `roadmap/archive/` (Canceled — `status: canceled`)

| TICK | Title | Priority | Type | Bucket | Proposed slug |
|---|---|---|---|---|---|
| TICK-10 | NPC left-behind tracking on location change | 3 | Feature | Extraction | npc-left-behind-tracking |
| TICK-13 | [EV] Mobile Turn Viewer CSS Tailwind purge strips custom selectors | 2 | Feature | Tooling | ev-mobile-turn-viewer-css |
| TICK-17 | [NPC] Compendium last action recent notes field | 4 | Feature | Extraction | npc-compendium-last-action-notes |
| TICK-21 | Resolved arcs for storytell | 3 | Improvement | World Building | resolved-arcs-storytell |
| TICK-36 | Scene scoping causes thread/arcs duplication | 2 | Bug | World Building | scene-scoping-thread-arcs-duplication |
| TICK-39 | [NPC] Spatial awareness — NPC entry/exit, location announcement | 3 | Feature | Extraction | npc-spatial-awareness-entry-exit |
| TICK-43 | NPC ghosting — NPCs vanish from compendium state | 2 | Bug | Extraction | npc-ghosting-compendium-vanish |
| TICK-45 | Condition cap exceeded — 6 conditions active at T21 | 2 | Bug | Extraction | condition-cap-exceeded |
| TICK-48 | 3 consecutive escalation beats | 3 | Bug | World Building | consecutive-escalation-beats |
| TICK-49 | extraction_context missing from events — 4 checkers fail | 3 | Bug | *(missing)* | extraction-context-missing-events |
| TICK-50 | Pacing gate fires on success instead of failure | 2 | Improvement | World Building | pacing-gate-fires-success |
| TICK-70 | [Conditions] TTL design question | 0 | Improvement | Extraction | conditions-ttl-design |
| TICK-71 | [Conditions] Ghost removal visibility | 0 | Feature | Extraction | conditions-ghost-removal-visibility |
| TICK-72 | [Prompt] Prompt tightening | 0 | Improvement | Extraction | prompt-tightening |
| TICK-77 | [UI] Mobile-friendly website | 0 | Improvement | UI | ui-mobile-friendly |
| TICK-84 | Storyteller→sanitizer ID mismatch | 0 | Bug | World Building | storyteller-sanitizer-id-mismatch |

### → `roadmap/features/` (Active: Idea/Backlog/Validating)

| TICK | Status | Title | Priority | Type | Bucket | Proposed slug |
|---|---|---|---|---|---|---|
| TICK-11 | Idea | [Storytell] Proactive NPC agency + GM beats redesign | 4 | Feature | *(missing)* | storytell-npc-agency-gm-beats-redesign |
| TICK-12 | Backlog | [Balancing] Difficulty assignment frequency too many hard rolls | 4 | Improvement | Balancing | balancing-difficulty-hard-rolls |
| TICK-14 | Backlog | [UI] UI improvements turn numbers and developer mode | 4 | Improvement | UI | ui-turn-numbers-dev-mode |
| TICK-19 | Idea | [Storytell] Karma system for player reputation | 4 | Feature | *(missing)* | storytell-karma-reputation |
| TICK-20 | Idea | [Storytell] Rest mechanic (heal, restock, time passes) | 3 | Feature | *(missing)* | storytell-rest-mechanic |
| TICK-30 | Validating | [NPC] Always state quantity on plural NPC notes | 3 | Improvement | Extraction | npc-quantity-plural-notes |
| TICK-33 | Backlog | [World] World state shows bloat, not active constraints | 3 | Improvement | World Building | world-state-bloat-constraints |
| TICK-35 | Backlog | [Balancing] Charisma bias in rulings — analyze ratio | 3 | Improvement | Balancing | balancing-charisma-bias |
| TICK-38 | Idea | [Storytell] Run sanitization on off turns to spread compute | 3 | Improvement | World Building | storytell-sanitization-off-turns |
| TICK-51 | Idea | [Infra] Better names and location names | 3 | Improvement | Tooling | infra-better-names-location-names |
| TICK-68 | Idea | [Scene] Interactive inventory items | 0 | Bug | Extraction | scene-interactive-inventory-items |
| TICK-69 | Backlog | [State] ID vs name normalization | 0 | Feature | Extraction | state-id-vs-name-normalization |
| TICK-74 | Idea | [NPC] Party designation | 0 | Improvement | Extraction | npc-party-designation |
| TICK-78 | Backlog | [Balancing] Settings menu overhaul | 0 | Improvement | Balancing | balancing-settings-overhaul |
| TICK-79 | Backlog | [EV] Turn viewer flippable + default deltas | 0 | Feature | UI | ev-turn-viewer-flippable |
| TICK-80 | Backlog | [EV] Full turn state inspector | 0 | Feature | Tooling | ev-full-turn-state-inspector |
| TICK-81 | Backlog | [Infra] OMLX provider | 0 | Improvement | Tooling | infra-omlx-provider |
| TICK-82 | Backlog | [Tech Debt] Stale documentation sweep | 0 | Feature | Tech Debt | tech-debt-stale-docs-sweep |
| TICK-83 | Backlog | [Tech Debt] Dead imports / parity gaps sweep | 0 | Improvement | Tech Debt | tech-dead-imports-parity-sweep |
| TICK-85 | Idea | Threads as fact sheet + objectives, multiple arcs | 0 | Feature | World Building | threads-fact-sheet-multiple-arcs |
| TICK-88 | Idea | Scene = NPC mgmt only | 0 | Feature | World Building | scene-npc-mgmt-only |
| TICK-89 | Backlog | Arcs need firmer goals | 0 | World Building | Improvement | arcs-firmer-goals |
| TICK-90 | Backlog | Opening arc improvement | 0 | World Building | Improvement | opening-arc-improvement |
| TICK-91 | Backlog | [Prompt] Choices tied to arcs/threads | 0 | Improvement | World Building | prompt-choices-arcs-threads |
| TICK-95 | Backlog | [Infra] Pack parity gaps — default vs generated packs | 3 | Improvement | Tech Debt | infra-pack-parity-gaps |

## Action items before migration

1. **TICK-42**: Assign type label (`Bug` or `Feature`) and bucket (`Tooling` likely)
2. **Missing bucket labels**: Assign buckets to 10 tickets (especially the 5 Storytell features that are bucket-less)
3. **TICK-89, TICK-90**: Label order reversed — assign `Improvement` as type, `World Building` as bucket
4. **TICK-40**: Label order reversed — assign `Feature` as type, `UI` as bucket
5. **Slug review**: Confirm slug format is acceptable before script runs
