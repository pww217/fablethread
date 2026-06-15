# Linear Reorganization Plan

> **Status: Completed** — All 6 parent issues created, 50+ tickets organized, 9 closed/canceled, all docs updated. 2026-06-14.

> Execution-ready. Step through implementation order below.

---

## Ticket templates

### Bug (status: New)

```
## Detail

[One-sentence summary of what's broken]

## How to Replicate

1. [Step to reproduce]
2. [Step to reproduce]
3. [Where the bug manifests]

## Evidence

- [File path:line] — [what's wrong]
```

No fix suggestions. No proposed solutions. After validation (Accepted), append `## Validation` with findings. After fix (Validating), add a comment describing the fix.

### Feature (status: Idea / Backlog)

```
## Detail

[What this is — one paragraph]

## Motivation

[Why this matters — what problem it solves]

## Scope

- **In scope:** [what the feature covers]
- **Out of scope:** [what it explicitly does not cover]

## Systems Affected

- [Modules, buckets, prompts, or templates this touches]
```

After scoping: append `## Scoping` with `### What exists`, `### What's missing`, `### Open questions`, `### Recommended approach`.

### Improvement (status: Idea / Backlog)

Same as Feature template above.

---

## Status workflows

**Features / Improvements:**
`Idea` → `Backlog` → `Scoping` → `Up Next` → `In Progress` → `Validating` → `Completed`

- Idea: greenfield/new concept, not yet committed to
- Backlog: accepted as worth doing, queued
- Scoping: exploratory research before planning
- Up Next: ready to start
- In Progress: being worked on
- Validating: testing fix — mandatory unless explicitly overridden
- Completed: done

**Bugs:**
`New` → `Accepted` → `In Progress` → `Validating` → `Completed`

- New: unverified bug report
- Accepted: validated as real bug
- In Progress: being fixed
- Validating: testing the fix — mandatory unless explicitly overridden
- Completed: fixed

---

## Label system

Every ticket gets exactly **two** labels: one **type** + one **bucket** (9 total labels).

### Type labels

| Label | Use |
|---|---|
| `Bug` | Something is broken |
| `Feature` | New capability |
| `Improvement` | Enhancement to existing capability |

### Bucket labels

| Label | Scope |
|---|---|
| `World Building` | Threads, Arcs & World State |
| `Extraction` | Extraction pipeline & Conditions (absorbs NPC + Conditions) |
| `UI` | Root UI & Chronicle |
| `Balancing` | Balance & Settings |
| `Tooling` | Developer Tooling & Infrastructure |
| `Tech Debt` | Cross-cutting tech debt |

### Title prefixes

All tickets should use a title prefix to disambiguate the subsystem. Prefixes are a convention, not labels — no Linear admin needed.

| Prefix | Applies to | When |
|---|---|---|
| `[Scene]` | Extraction | Scene extraction |
| `[State]` | Extraction | State extraction (inventory, conditions, location) |
| `[Storytell]` | Extraction | Storyteller (beats, thread operations) |
| `[Narrator]` | Extraction | Narrator extraction |
| `[Ruling]` | Extraction | Ruling extraction (intent → skill) |
| `[NPC]` | Extraction | NPC extraction & compendium |
| `[Conditions]` | Extraction | Conditions lifecycle |
| `[Prompt]` | Any bucket | Prompt template change (cross-cutting) |
| `[EV]` | Tooling | ev.py, checkers |
| `[Infra]` | Tooling | OMLX, providers |

---

## Current Linear state (June 2026)

### Labels (workspace-level)
| Name | Keep? | Note |
|---|---|---|
| `Bug` | ✅ | |
| `Feature` | ✅ | |
| `Improvement` | ✅ | |
| `World Building` | ✅ | Already created by user |
| `Extraction` | ✅ | |
| `UI` | ✅ | |
| `Balancing` | ✅ | |
| `Tooling` | ✅ | |
| `Tech Debt` | ✅ | |
| `Narrative` | ❌ Delete | Replaced by World Building |
| `Conditions` | ❌ Delete | Absorbed into Extraction bucket |
| `NPC` | ❌ Delete | Absorbed into Extraction bucket |
| `Docs` | ❌ Delete | User dropped it |

### Label actions (Linear console)
1. Create: `World Building` (already done)
2. Delete: `Narrative`, `Conditions`, `NPC`, `Docs`
3. Final set: Bug, Feature, Improvement, World Building, Extraction, UI, Balancing, Tooling, Tech Debt

---

## Bucket 1: World Building

**Parent issue**: World Building

Narrative integrity — threads as lower-level objectives/world facts, arcs as high-level objectives, thread updates as journal/log, world state as immutable seed + promoted facts from resolved arcs/threads. Also covers sanitizer correctness, pacing gates, and multiple concurrent arcs.

**Sub-issues:**

| ID | New Status | Type | Prefix | Description |
|---|---|---|---|---|
| **TICK-52** | In Progress → **Validating** | Improvement | — | Sanitizer text replacement — was replacing thread updates with verbatim text. Confirm fix. |
| **TICK-33** | Backlog | Improvement | — | World state bloat — surface active constraints, not background lore. |
| **TICK-38** | Backlog → **Idea** | Improvement | — | Off-turn sanitization. |
| **TICK-21** | Close | — | — | Canceled (absorbed into mechanics overhaul). |
| **TICK-36** | Close | — | — | Canceled (moot). |
| **TICK-48** | Close | — | — | Canceled (moot). |
| **TICK-50** | Close | — | — | Canceled (moot). |
| **TICK-84** | Close | — | — | Completed — root cause was TICK-50. (Auto-assigned as TICK-84 in Linear.) |
| **NEW** | Idea | Feature | — | Threads as fact sheet + objectives, multiple arcs — should threads split? 2-3 concurrent arcs as objectives? |
| **NEW** | Backlog | Improvement | — | Active vs urgency redundancy — if background=latent and anything else=active, does urgency add value? |
| **NEW** | Backlog | Improvement | — | Sanitizer dormant vs resolve — set threads dormant rather than resolving. |
| **NEW** | Idea | Feature | — | Scene = NPC mgmt only — move location to state extractor to spread load. Refactor. |
| **NEW** | Backlog | Feature | — | Arcs need firmer goals — named person, place, objective, tangible milestones. |
| **NEW** | Backlog | Feature | — | Opening arc improvement — "where am I going and why" not concrete enough. |
| **NEW** | Backlog | Improvement | [Prompt] | Choices tied to arcs/threads — prompt guidance to tie choices to active arcs/threads instead of random. |
| **NEW** | Backlog | Improvement | — | Stale thread prompt trim — engine may handle this now; validate and trim prompts. |

---

## Bucket 2: Extraction

**Parent issue**: Extraction Pipeline

Everything the pipeline emits and manages: scene, state, storytell, narrator, ruling extraction, plus NPC lifecycle (compendium, spatial, death, party) and condition lifecycle.

**Sub-issues:**

| ID | New Status | Type | Prefix | Description |
|---|---|---|---|---|
| **TICK-34** | Validating | Bug | [State] | Future transactions — extractor records trades-for-later as already happened. |
| **TICK-37** | Accepted | Bug | [State] | Inventory change reason — fires when nothing changed, or gives wrong reason. |
| **TICK-41** | Accepted | Feature | [NPC] | Compendium overhaul — last_seen turn number, last action field, alias priority, longer bios. |
| **TICK-39** | Accepted | Feature | [NPC] | Spatial awareness & location system — entry/exit tracking, location web, proximity UI. |
| **TICK-30** | Accepted | Improvement | [NPC] | NPC quantity display — always show count for plural NPCs. |
| **TICK-22** | Backlog | Improvement | [Conditions] | Condition age display — show age in prompts alongside TTL; system guidance for pruning. |
| **TICK-32** | Completed (needs fix) | Improvement | [NPC] | Character highlighting — scope to narration text only. |
| **TICK-45** | Close | — | — | Canceled — soft cap is fine. |
| **TICK-17** | Close | — | — | Superseded by TICK-41. |
| **TICK-43** | Close | — | — | False positive. |
| **TICK-10** | Close | — | — | Superseded by mechanics overhaul. |
| **NEW** | New (→ triage → Validating) | Bug | [State] | Choices show IDs/present tense — choice options render inventory IDs, reference past items. |
| **NEW** | Idea | Feature | [Scene] | Interactive inventory items — nearby interactable items as separate concept. |
| **NEW** | Backlog | Improvement | [State] | ID vs name normalization — human-readable names vs camelCase IDs for state keys. |
| **NEW** | Backlog | Feature | [Conditions] | TTL design question — force narrative resolution vs long TTLs as insurance? |
| **NEW** | Backlog | Improvement | [Conditions] | Ghost removal visibility — when engine removes by TTL, surface in UI (delta or log). |
| **NEW** | Backlog | Improvement | [Prompt] | Prompt tightening — stop inferring TTL-removed conditions from narration. |
| **NEW** | Backlog | Feature | [NPC] | Departed reason in UI — 1-2 sentence summary when NPC departs (died, sailed away, etc.). |
| **NEW** | Idea | Feature | [NPC] | Party designation — boolean on NPC model for auto-tracking across location changes. |
| **NEW** | Backlog | Bug | [NPC] | NPC bonds display bug — UI shows bond ID instead of description. |
| **NEW** | Backlog | Bug | [NPC] | NPC presence gaps — some NPCs still absent when they should be present. Needs scoping. |

---

## Bucket 3: UI & Chronicle

**Parent issue**: Root UI — Game Interface

Player-facing interface — chronicle completeness, visual polish, mobile compatibility, tooltips, debug/production mode.

**Sub-issues:**

| ID | New Status | Type | Prefix | Description |
|---|---|---|---|---|
| **TICK-14a** | Backlog | Improvement | — | Turn numbers + thread display cleanup. |
| **TICK-14b** | Idea | Feature | — | Debug/production UI toggle — all-in on debug for now (sole user). |
| **TICK-27** | Accepted | Improvement | — | Purple highlighting — soften delta/thread summary colors. |
| **TICK-29** | Backlog | Feature | — | Outcome in chronicle — summaries, arc resolution, location/faction transitions. |
| **TICK-28** | Accepted | Bug | — | Load game mobile — fails on mobile browsers. |
| **NEW** | Idea | Feature | — | Mobile-friendly website — make core UI work on mobile. |

---

## Bucket 4: Balancing & Customization

**Parent issue**: Balance & Player Settings

Combat/roll balance, skill-usage fairness, settings menu.

**Sub-issues:**

| ID | New Status | Type | Prefix | Description |
|---|---|---|---|---|
| **TICK-12** | Backlog | Improvement | — | Too many hard rolls — 42% hard difficulty dominates. |
| **TICK-35** | Backlog | Improvement | — | Charisma bias — charisma over-used vs other skills. Analyze. |
| **NEW** | Backlog | Improvement | — | Settings menu overhaul — difficulty, pacing, parameters. Ugly and half-broken. |

---

## Bucket 5: Developer Tooling & Infrastructure

**Parent issue**: Developer Tooling & Infrastructure

EV tools, turn viewer, inspector, provider support.

**Sub-issues:**

| ID | New Status | Type | Prefix | Description |
|---|---|---|---|---|
| **TICK-13** | Idea | Feature | — | Mobile Turn Viewer — reframe as "make TV work on mobile." Prerequisites on web side. |
| **NEW** | Backlog | Improvement | — | Turn viewer flippable + default deltas — single-column, toggle prompts/flows vs deltas. Default deltas. |
| **NEW** | Idea | Feature | [EV] | Full turn state inspector — click a turn for complete state JSON, syntax-highlighted. |
| **NEW** | Idea | Feature | [Infra] | OMLX provider — additional model backend support. |

---

## Bucket 6: Tech Debt (Cross-Cutting)

**Parent issue**: Cross-Cutting Tech Debt

Repo-wide items not specific to one area: dead code, stale docs, dead imports.

**Sub-issues:**

| ID | New Status | Type | Prefix | Description |
|---|---|---|---|---|
| **TICK-15** | Backlog (with note) | Improvement | — | Dead code cleanup — cancel-turn, memory leaks, `_strip_non_ascii` dupes, stream blocks. Needs re-validation after overhaul. |
| **NEW** | Backlog | Improvement | — | Stale documentation sweep. |
| **NEW** | Backlog | Improvement | — | Dead imports / parity gaps sweep. |

---

## Feature Ideas (standalone Idea tickets)

No parent. These stay as individual Idea tickets for future scoping.

| ID | Type | Prefix | Description |
|---|---|---|---|
| **TICK-19** | Feature | — | Karma system — player reputation for NPC reactions. |
| **TICK-20** | Feature | — | Rest mechanic — heal, restock, time passes. |
| **TICK-11** | Feature | — | Proactive NPC agency — storyteller-driven turns from NPC perspective. |
| **TICK-51** | Improvement | — | Better procedural names — surnames not first names for location generation. |

---

## Implementation order

1. **Linear console**: delete `Narrative`, `Conditions`, `NPC`, `Docs` labels
2. **Create 6 parent issues** (one per bucket) — no status, just bucket label
3. **Move existing tickets** under parent issues, add bucket labels, update statuses per tables above
4. **Create new tickets** per tables above with correct statuses, labels, titles (with prefixes)
5. **Close canceled/superseded tickets** with status-change comments (reason required)
6. **Create choices/IDs bug** in `New` → triage to `Accepted` → move to `Validating`
7. **Commit all doc/skill/agents changes**

---

## Disposed items (no ticket)

| Original idea | Reason |
|---|---|
| Inject emergent threads/beats | Axed |
| GM beats keyed to thread state | Axed |
| Pass narration hints to extractors | Axed |
| Recently removed conditions field | Prompt tightening instead |
| Replace options with hardcoded templates | Don't hardcode; prompt guide to arcs/threads |
| NPC bonds model change | Prompt-level UI bug |
| Momentum as dice modifier | Momentum concept dead |
