# Changes — All Plans Combined

Complete catalog of every mechanical (code/structure) and substantive (behavior/runtime) change across all active plans, ordered by execution phase per `ORDERING.md`.

---

## Phase 0: World-State History Redesign

**Source:** `world-state-history-redesign/` design doc + implementation sub-plans
**Ordering position:** First — structural removal that changes model shapes, state schema, and prompt templates. All other plans either depend on the new state shape or fight over fields this plan removes.
**Sub-phases:** A (delete recent_events), B (promote world_state tiers), C (thread resolution outcomes)

### Phase A: Delete Recent Events System
**Plan:** `world-state-history-redesign/01-delete-recent-events.md` (~20 files, ~80 changes)

#### Mechanical Changes

| File | Change |
|---|---|
| `models.py` | Remove 3 Pydantic models (`RecentEvent`, `RecentEventUpdate`, `CompactorRecentEventCompact`). Remove 6 fields from StateDelta and StorytellerResult (`recent_events_add/update/remove`). Remove field from CompactorSanitizationResult. |
| `state/delta_builder.py:124` | `apply_delta()` signature drops `recent_events_max, current_turn_no`. Return changes from `(dict, bool)` to just `dict`. Delete entire ring buffer block (~lines 291-325) and the inventory durability gate (checked `delta.recent_events_add or []` AND `delta.actions or []` — removed entirely, had more false positives than value). |
| `state/delta.py:30,36,37` | Thin wrapper matches new signature and return type. |
| `engine/turn.py:965-966,1203,1216,1536,1543` | Remove local vars `recent_events`, `recent_events_evicted`. Fix unpacking at line 1203 from `state, recent_events_evicted = apply_delta(...)` to `state = apply_delta(...)`. Remove TurnResult constructor args. Rename `load_recent_events` import and call site to `load_recent_turns`. |
| `engine/extraction.py:249,267,548-556,605,607,639,653-655` | Remove recent_events from storytell_user.j2 render context. Delete turn-stamping block on StorytellerResult.recent_events_add (dead after model deletion). Remove 3 logging references to `events_add`. Remove StateDelta construction args for the three deleted fields. |
| `engine/compactor.py:119-154,140-141` | Delete recent_events_compact replacement block (~lines 119-135). Remove compaction count from sanitization payload dict at line 154. Update post-compaction logging format string and args to remove `recent_events=%d`. |
| `engine/changes.py:33-220` | Delete 3 loops iterating over `applied.get("recent_events_*")` that produce emoji diff lines for UI toast. Delete entire fact computation block (pre/post event ID comparison, added/removed/updated facts). Remove `"recent"` entries from returned changes list. |
| `state/chronicle.py:50-86` | Rename `load_recent_events()` → `load_recent_turns()`. Reads events.jsonl turn logs (not scene.recent_events). All imports and call sites updated. |
| `state/io.py:86,133-157` | Remove `"recent_events": []` from `_default_state()` scene section at line 86. Delete entire `_convert_seed_recent_events()` function and its call in `init_save_dir()`. |
| `server/routes.py:189` | Remove `"recent_events_evicted"` from JSON response dict. Rename `load_recent_events` import and call site to `load_recent_turns`. |
| `eval/universal_asserts.py:23-56,427-449,~930-970` | Delete both asserter functions (`check_recent_events_turn_stamped`, `check_recent_events_ring_size`) and their invocations from checker list. |
| `eval/compaction_signals.py:99,108-159` | Remove recent_events size tracking (before/after compaction metrics) and summary formatting line. |
| `prompts/storytell_system.j2` | Delete JSON schema example showing empty arrays for the three event fields (~lines 7-9). Delete instruction paragraph about emitting new events with turn stamps and IDs (line 44). Delete update/remove semantics descriptions (lines 46, 48, 50). |
| `prompts/storytell_user.j2` | Delete `{% if recent_events %}` section header + event listing loop (~lines 22-24) — removes "Recent events" context block from storyteller prompt. |
| `prompts/compact_system.j2:58,74-132` | Bold instruction line (58), JSON example with schema (74-80), compacted events description section (lines 102, 129-132). |
| `prompts/compact_user.j2:57-58` | `{% if recent_events %}` loop rendering event list for compactor prompt. |
| `templates/index.html:1400` | Remove evicted toast condition check (`if (result.recent_events_evicted)`). **Preserved:** else branch that renders general changes via `_buildTurnChanges()`. |
| `templates/_turn_viewer.html:100-101` | Delete template showing "Recent events compacted to:" count in compaction event rows. |
| `templates/_state_right.html:2` | **Delete entire file** — renders recent_events on state sidebar, now dead rendering code. |
| `scripts/debug/ev.py:50,861` | Remove `"recent_events"` from SECTION_MARKERS dict (removes search command). Update scene rendering trigger to remove "recent_events" key from OR-list. Delete any orphaned `_render_recent_events()` function. |
| `prompts/context.py:269,281` | Remove StorytellerBoundary model field and docstring reference. |
| `pack.py:65` (SeedScene class) | Remove `recent_events: list[str] = Field(default_factory=list)` from the SeedScene dataclass. |
| `engine/seed.py:40-41` | Delete for-loop iterating over `envelope.seed_state.scene.recent_events`. Static pack seeds with old-format scene data simply won't have recent_events anymore (no migration needed). |
| `engine/config.py:68,152` | Remove `recent_events_max: int = 20` field from EngineConfig and its loading line. |

#### Substantive Changes

- **Storyteller prompt shrinks** — no longer manages event log state or produces compaction output (~30 tokens saved per storyteller call).
- **Compactor produces one less LLM output field** — `recent_events_compact` removed from CompactorSanitizationResult.
- **UI loses evicted toast notifications** — no ring buffer to evict from, so pruning warnings are gone. General state changes still display via `_buildTurnChanges()`.
- **Durability gate narrows scope** — items added without loot context in actions will now be rejected (previously could pass if they had recent_events_add entries). This is intentional: only action-referenced items survive the gate.
- **`apply_delta()` signature simplified** — from `(state, delta, recent_events_max=20, current_turn_no=N) → (dict, bool)` to `(state, delta) → dict`. All 9 call sites updated simultaneously.
- **Old state files fail on load intentionally** — no migration function; `scene.recent_events` field removed from default_state shape at step A.10.

### Phase B: Promote world_state to Mutable Tiered Structure
**Plan:** `world-state-history-redesign/02-promote-world-state-tiers.md` (~9 files)

#### Mechanical Changes

| File | Change |
|---|---|
| `models.py:~225` | **New model:** `class WorldStateFact(BaseModel)` with fields `id: str`, `text: str`, `tier: Literal["permanent", "persistent"] = "persistent"`. Add to StorytellerResult and StateDelta: `world_state_add: list[WorldStateFact] = Field(default_factory=list)`, `world_state_remove: list[str] = Field(default_factory=list)`. |
| `state/delta_builder.py` (new block after inventory/NPC logic) | Insert world_state handling in apply_delta: persistent facts appended/updated by id; removed facts deleted from list by id. Permanent tier never touched regardless of what LLM emits. No eviction cap — grows organically with discovered durable facts. |
| `state/io.py:85` | Default state keeps `"world_state": []` (empty list valid default). Dynamic packs populate permanent-tier facts during seeding; static pack seeds may have plain strings handled by strip loop type check. |
| `engine/seed.py:38-41, 346-348` | Strip loop checks element type — dict-like accesses `.text` / `["text"]`, plain string applies `_strip_non_ascii(evt)` directly. Dynamic seed baseline_facts merge produces `{"id": f"baseline_{i}", "text": text, "tier": "permanent"}` objects instead of strings. |
| `engine/extraction.py:250, 268` | No functional change — already reads world_state list from state regardless of element type and passes to template layer. Verification only after Phase A removes recent_events from same function. |
| `prompts/storytell_user.j2:~26` | Change `{% if not all_threads and world_state %}` → just `{% if world_state %}` — always show when entries exist, regardless of thread activity status. |
| `prompts/sections/_world_state.j2` (entire file) | Replace single-line template with tier-aware rendering: dict objects render `[permanent]` / `[persistent] {{ fact.text }}`; legacy strings render as-is for any old state files that somehow load. Uses Pydantic attribute access (`fact.tier`, `fact.text`) not `.get()`. |
| `prompts/storytell_system.j2:1-50+` | Replace JSON schema example (lines 6-17): remove recent_events fields, add world_state_add/remove entries with tier rules. Replace instruction paragraph (lines 42-50) with new world_state instructions including "emit only for facts true 10 turns from now in a different location" constraint and max 2 per turn limit. |

#### Substantive Changes

- **world_state becomes mutable at runtime** — previously completely inert after seed time, now LLM can add/remove persistent world facts via `world_state_add`/`world_state_remove`.
- **Permanent tier is immutable** — universe facts from seed (e.g., world rules, geography) are never touched by apply_delta or LLM output validation. Persistent tier grows organically with discovered durable environmental changes during gameplay: capability changes like destroyed routes, lost objects, and dead key NPCs belong in the persistent tier and can be added/updated/removed at runtime via `world_state_add`/`world_state_remove`.
- **Storyteller always sees world_state during gameplay** — previously hidden behind `{% if not all_threads %}` gate at line 26, meaning persistent world facts were invisible precisely when most relevant (active gameplay). Now renders independently whenever entries exist.
- **Tier labels visible to Storyteller** — `[permanent]` vs `[persistent]` prefixes help the LLM understand which facts are immutable seed-authored truths vs runtime-discovered changes that can be removed or updated.
- **No hard cap on world_state_add per turn** — relies solely on prompt constraint ("at most 2 entries") to prevent abuse of new write target (user decision #1).
- **narrate_user.j2 TRACE_IMMUTABLE markers split** — world_state moved out of TRACE_IMMUTABLE block into its own header because it now contains mutable persistent facts alongside immutable permanent facts. Factions and name pool remain under TRACE_IMMUTABLE (still seed-authored).
 
### Phase C: Thread Resolution Outcome Field & All-Thread Visibility
**Plan:** `world-state-history-redesign/03-add-thread-resolution-outcome.md` (~7 files)

#### Mechanical Changes

| File | Change |
|---|---|
| `models.py:356-359, 28-45` (ThreadResolution model at line 356; ArcThread model at line 28) | **ThreadResolution:** Add mandatory `outcome: str = ""` field after resolution_state. **ArcThread:** Add nullable `outcome: str | None = None` field after resolution_state (None on active/legacy threads for backward compatibility). |
| `engine/turn.py:421-433` (`_apply_thread_resolutions()`) | Both model_copy update paths now include `"outcome": res.outcome` alongside existing `"resolution_state"` — initial move to completed_threads path and dedup re-update path. |
| `prompts/storytell_system.j2:14, 31-35` (JSON schema at line 14; thread_resolve instructions at lines 31-35) | JSON schema example adds `"outcome": "The enemy retreated into the tunnels after a fierce battle."`. Instruction text updated with explicit outcome requirement: one past-tense sentence describing what happened; future Storyteller calls read these outcomes for continuity. |
| `prompts/storytell_system.j2` (after thread generation rules) | New latent thread handling paragraph: all threads (including dormant/latent) visible; actively push players towards discovery through thread suggestions, beats, and complications — without directly exposing the latent content ("show, don't tell"). |
| `prompts/storytell_user.j2:~18` (after active threads loop) | New conditional block renders completed_threads when any exist: `- \`thread_id\` [RESOLVED/FAILED/ABANDONED] {{ outcome or "(no outcome recorded)" }}`. Directive header: "past resolutions (for continuity — do not re-open resolved tensions)". |
| `engine/narrate.py:74` (`_narrate_messages()`) | Add `"completed_threads": arc.get("completed_threads") or []` to current_arc_ctx dict construction. Previously only included active threads filtered by scope/active status. |
| `prompts/narrate_user.j2:36-42` (Scene Context thread section) | **Replace** scene-scoped-only thread block with all-threads rendering (active + latent, scene + arc) using `current_arc.threads` with fallback to `state.arc.threads`. Each thread shows scope tag `[SCENE]`/`[ARC]`, (latent) marker if dormant, urgency, summary, and last_seen_turn. |
| `prompts/narrate_user.j2:~59` (after `_arc.j2` include) | New conditional block renders completed_threads with outcomes under "### Past Resolutions" header — structured continuity about how specific plot tensions ended, not captured in chronicle tail or compacted history. |
| `prompts/narrate_system.j2` (after thread visibility rules) | New latent thread handling paragraph: all threads (active, latent, completed) visible; push players towards latent threads through narration, environmental detail, NPC behaviour, and 4 choices — without explicit exposition ("show, don't tell"). |

#### Substantive Changes

- **Thread resolutions now have prose records** — previously moved to `completed_threads` with only a label (`resolution_state`) and zero prose context; now each completion has one past-tense sentence describing what happened.
- **Storyteller sees past outcomes when generating new threads** — avoids contradicting established outcomes (e.g., won't suggest rescuing someone whose outcome was "The guard fell in battle").
- **Narrator now sees ALL threads (active + latent) rather than only scene-scoped threads** — narrate_user.j2 previously filtered to scene-scoped threads only, hiding arc-scoped and latent threads. Now all threads render with scope tags and (latent) markers, giving the Narrator full continuity awareness.
- **Narrator gains structured continuity about resolved tensions** — helps narrate consequences of completed actions, especially for abandoned/failed threads where negative outcomes may need forward narration.
- **System prompts gain latent thread guidance** — narrate_system.j2 and storytell_system.j2 instruct LLMs to actively push players towards exploring latent threads through narration, choices, and thread suggestions ("show, don't tell" — hint and invite, never state outright).
- **Legacy completion compatibility** — old completed threads without outcomes show "(no outcome recorded)"; new resolutions require the field per ThreadResolution model validation.

---

## Phase 1a: Beat Timing Observability (independent of Phase 0, can run in parallel)

**Plan:** `ev1-fixes/03-beat-timing-observability.md` (~3 files)
**Ordering position:** Independent — no model changes, no state schema changes. Pure observability/debugging improvements. Can run alongside Phase 0.

### Mechanical Changes

| File | Change |
|---|---|
| `engine/turn.py:873` (`_narrate_setup()`) | Add docstring/comment documenting intentional one-turn beat lag: beats from turn N set atmosphere for turn N+1 narration; immediate feedback handled by roll-band directive, not beat system. |
| `engine/turn.py:~1442-1453` (ruling dict serialization) | Add `"raw_total": outcome.raw_total` to events.jsonl ruling dict alongside existing fields (`final_total`, `dice`, `band`, etc.). Field exists in RulesOutcome model at line 168 but was omitted from serialization. |
| `scripts/debug/ev.py` (new subcommand) | New `dice` subcommand: reads all events with `ruling.rolled=true`, prints formatted dice table (Turn, Skill, Difficulty, Dice, Raw→Final, Band, Modifiers), includes summary row (total rolls, band distribution). Falls back to computing raw_total from sum(dice) + modifiers for pre-fix data. |

### Substantive Changes

- **No behavioral change** — documentation comment only at turn.py:873; `raw_total` addition is purely observability (all dice math already verifiable from persisted fields, just requires manual reconstruction).
- **ev1 dice analysis becomes single-command** instead of requiring custom scripts to query events.jsonl.

---

## Phase 2: Prompt Alignment for Beat Type Selection, Null Emission, and Fail Near-Miss Guidance

**Plan:** `ev1-fixes/01-prompt-alignment.md` (~4 files)
**Ordering position:** After Phase 0 — builds on new storyteller_system.j2 structure from world-state redesign. All changes are prompt-level only; no Python code changes.

### Mechanical Changes

| File | Change |
|---|---|
| `prompts/storytell_system.j2:92` (band-aligned beat selection section top) | Add priority preamble establishing directive/band precedence hierarchy. Three tiers: Breathe → always breathing_room/null; Pressure/Overwhelm → always complication/pressure; Tension or empty → follow band alignment below. |
| `prompts/storytell_system.j2:~96` (setback/fail line) | Add near-miss exception paragraph: fail near-misses within 2 of setback threshold at 7 allow complication beats because near-miss creates narrative friction without compounding punishment; breathing_room or null still valid for de-escalation. |
| `prompts/storytell_system.j2:~73` (beat type diversity section end) + no-roll guidance | Add null emission cadence sentence: emit `gm_beat: null` at least once every 4 turns regardless of pacing directive, giving expiry mechanism chance to fire and creating natural quiet moments during Pressure phases. Update "no roll" guidance to reference the 1-in-4 cadence. |
| `ccya/prompts/narrate_system.j2:30` (priority ordering section) | Add null-beat fallback line after the existing pending_gm_beat guidance: "If no GM beat is present, scene continues without added pressure or relief — narrate purely from pacing directive and player input." |

### Substantive Changes

- **Band-beat contradiction eliminated** — partial outcomes at low momentum producing breathing_room beats becomes *correct* behavior rather than a bug. Breathe directive explicitly overrides band guidance; Pressure/Overwhelm explicitly override it too.
- **Fail near-misses now have distinct beat guidance** — resolves split behavior where T1 chose pressure (following narration) and T4/T10 chose breathing_room (following beat guidance). Near-miss within 2 of threshold allows complication without compounding punishment.
- **Null beats should appear at ~25% frequency** instead of zero across all turns, exercising the expiry mechanism that was previously dead code due to universal non-null emission.
- **Narrator handles null beats gracefully with explicit guidance** — no structural changes to prompt building; just a fallback instruction for when storyteller starts emitting nulls per Phase 1a cadence rule.

---

## Phase 3: Thread Lifecycle Fixes (Key-Branch Black Hole + Urgency Decay + Scene-Scoped Management)

**Plan:** `ev1-fixes/02-thread-lifecycle.md` (~5 files)
**Ordering position:** After Phase 0 for steps 3.1–3.3; Step 3.0 (key-branch fix) is independent and can run in parallel with Phase 0. Resolves C1, C2, C3, C4, C7 from ev2 findings.

### Mechanical Changes

| File | Change |
|---|---|
| `engine/turn.py:1275-1301` (`thread_add` if-elif chain) | **Restructure:** Remove `elif _new_thread.key:` as separate branch (the key-branch black hole). Move scene-scope pass to replace key-check position. Key collision check moves inside the final `else:` (creation path). Non-keyed scene threads still passed through unchanged via new elif position. Variables `_state_arc` and `exact_collision_id` now scoped to inner `if _new_thread.key:` block; reference at line 1311 (`if _new_thread.key and not exact_collision_id`) remains valid — falsy when no key, set correctly when collision check ran. |
| `models.py:28-45` (ArcThread model) | Add optional field `urgency_set_turn: int | None = None`. Records turn number when urgency was last set for decay pass to measure duration at current level. Pydantic v2.12.5 — uses `.model_copy()` method correctly. |
| `engine/seed.py:337-339` (seeded thread loop) | After setting `active=True`, also set `added_turn` and `urgency_set_turn` from current turn meta or 1 if unavailable. |
| `engine/turn.py:675` (`_compute_threat_ages()`) | Add fallback for missing added_turn: derive from current turn number (or default to 1) when both `added_turn` and `last_seen_turn` are absent. Defense-in-depth for pre-existing data without migration. |
| `engine/turn.py:200` (`_apply_thread_signals()`) | Change scope filter from `scope == "arc"` → include both arc and scene scopes via config flag `track_scene_thread_progress: bool = True`. Update function docstring to remove "Scene-scoped threads are not processed here." |
| `engine/config.py` (EngineConfig) | Add new field `thread_urgency_max_age: int = 8` and `track_scene_thread_progress: bool = True`. |
| `engine/turn.py:~251+` (`_apply_thread_signals()`) | New urgency decay pass after advance/expiration loop: evaluates all threads (arc + scene) for demotion when `urgency_set_turn` age >= threshold. Decay steps: urgent → normal → background, resetting `urgency_set_turn` at each step. Also set `urgency_set_turn` during seed generation and thread_add extraction path fallthrough. |
| `engine/turn.py:~251+` (scene expiration) | New scene-scoped two-stage expiration pass after urgency decay: active→latent (`active=False`) after `scene_thread_expire_silent_turns` (default 5) turns without progress; latent→removed from `arc.threads` after `scene_thread_expire_silent_turns * 2` turns without being surfaced, using ID-based removal. Seed creates 1-2 active + 3-5 latent threads at game start. Config flag `scene_thread_expire_silent_turns` controls both latency triggers (default 5). |

### Substantive Changes

- **Scene-scoped threads now enter state** — previously ALL LLM-emitted scene-scoped thread_add entries silently dropped due to key-branch black hole at turn.py:1275. Now they proceed through normal creation path after collision check passes. SEEDED threads were the only ones that ever reached state; now all generated threads do too.
- **Scene-scoped threads can complete via progress tracking** — previously structurally impossible because scope filter excluded them from `_apply_thread_signals()` advance loop (root cause of ev1 finding #3: siege_escalation had scope=scene, so progress stayed at 0 forever). Now tracked alongside arc threads with config flag for rollback. Scene threads follow a two-stage lifecycle: active → latent after 5 inactive turns → removed if unsurfaced for 5 more. Latent scene threads visible to both prompts, which push towards discovery.
- **Urgency now decays naturally** — previously never decayed because no production code read `thread_urgency_max_age` config (ev1 finding #2: siege_escalation remained "urgent" across all 10 turns). Now demotes urgent→normal after 8 turns, normal→background after another 8.
- **Scene-scoped threads silently expire** — previously never removed from state because they were invisible to the compactor (no pressure_remove emitted for scene scope) and had no expiration path in Python code. Now auto-pruned after 5+ turns without advancement.
- **Seed-generated threads now have proper turn tracking** — seeded scene-scoped threads never got `added_turn`, causing `_compute_threat_ages()` to skip them entirely (ev1 finding #2). Fallback added for pre-existing data without migration.

---

## Phase 4: Eval Coverage Gaps — Detection Layer Against Fixed Code

**Plan:** `eval-coverage-gaps.md` (~1 file)
**Ordering position:** Last — detection layer should run against fixed code to validate that fixes actually resolved the issues. No production code changes, purely harness updates.

### Mechanical Changes

| File | Change |
|---|---|
| `eval/engine_mirror.py` | Update `THREAD_ARC_DEMOTE_AGE` reference to match new config key name (`thread_urgency_max_age`). Add asserters for urgency decay timing and scene-scoped progress tracking completion. Remove recent_events-related assert patterns (resolved by Phase A — no coverage needed for dead code paths). |

### Substantive Changes

- **No runtime behavioral change** — eval harness updates only, validates that Phase 3 thread lifecycle fixes work correctly at runtime.
- **Recent events asserters removed** from this plan because Phase A deletes the entire recent_events system; no coverage needed for dead code paths.

---

## Finding Resolution Matrix

| Finding | Severity | Plan & Phase |
|---|---|---|
| C1 — Key-branch black hole drops all scene-scoped threads | CRITICAL | Phase 3, Step 0 (`ev1-fixes/02-thread-lifecycle.md`) |
| C2 — Progress=0 only for scene-scoped threads (arc threads advance correctly) | MEDIUM-HIGH | Phase 3, Step 3.2 (`ev1-fixes/02-thread-lifecycle.md`) |
| C3 — Missing added_turn on seeded threads | HIGH | Phase 3, Steps 3.1+3.2 (`ev1-fixes/02-thread-lifecycle.md`) |
| C4 — Urgency never auto-decays | HIGH | Phase 3, Step 3.3 (`ev1-fixes/02-thread-lifecycle.md`) |
| C5 — Band-beat misalignment on PARTIAL outcomes | CRITICAL | Phase 2 (directive/band priority rule in `ev1-fixes/01-prompt-alignment.md`) |
| C6 — Fail near-miss prompt contradiction | MEDIUM | Phase 2 (near-miss exception guidance in `ev1-fixes/01-prompt-alignment.md`) |
| C7 — Scene threads excluded from lifecycle management | MEDIUM-HIGH | Phase 3, Steps 3.2+3.3 (`ev1-fixes/02-thread-lifecycle.md`) — scene threads now follow active→latent→removed lifecycle, can complete via progress, and latent scene threads are surfaced by both prompts |
| C8 — Beat expiration dead code (zero null beats) | MEDIUM | Phase 2 adds null emission cadence guidance (~1-in-4 turns target). Try prompt first; Python fixes if pattern persists. |
| C13 — Silent directive degradation post-compaction | HIGH | Addressed implicitly by Phase 3 (threads won't be silently dropped) + Phase C latent + completed threads provide fallback context for both prompts |
| C14/C2 — Compactor removes seeded thread | MEDIUM-HIGH | Addressed implicitly by Phase 3 key-branch fix allowing replenishment |
| C15/C17 — Narrator blind to recent_events (resolved by removal) | CRITICAL | Phase A: resolved by removing entire system; completed thread outcomes visible in narrator prompt provide continuity via Phase C |
| C16/C18 — Storytell blind to world_state during gameplay | HIGH | Phase B: world_state always shown, conditional gate removed at storytell_user.j2:26 |

---

## Out-of-Scope Findings (No Plan Exists)

None — all identified findings have corresponding plan coverage. Phase 2's null emission cadence guidance partially addresses C8 but does not guarantee full resolution since it depends on LLM compliance rather than enforcement.

---

## Execution Risk Summary

### apply_delta return value change (Phase 0)
**What:** `turn.py:1203` unpacks as `state, recent_events_evicted = apply_delta(...)` expecting `(dict, bool)`. Phase A removes the evicted boolean from both `delta_builder.apply_delta()` and `delta.apply_delta()`, changing return to just `dict`.

All affected call sites must be updated simultaneously:
- `ccya/state/delta.py` line 30+ — wrapper function signature and return
- `ccya/state/delta_builder.py` lines 123+, 362 — implementation signature and return
- `ccya/engine/turn.py` lines 965-966, 1203, 1536-1543 — local vars, unpacking, constructor args
- `ccya/engine/extraction.py` line 86 — unpacking in deepcopy+apply_delta pattern
- `ccya/models.py:437,450` (TurnResult dataclass) — remove fields `recent_events: list[dict] = field(default_factory=list)` and `recent_events_evicted: bool = field(default=False)`
- `ccya/server/routes.py` line 189 — JSON response dict field
- `templates/index.html` lines 1396-1408 — evicted toast condition (restructure to always render changes)

### apply_delta parameter removal (Phase 0)
**What:** `turn.py:1205` passes `recent_events_max=config.recent_events_max` to apply_delta(). Phase A removes this parameter and the config key simultaneously.

### No migration needed
All plans explicitly require no backward compatibility or data migration. Old state files fail on load intentionally after Phase A changes model shapes and default_state schema. This is a user decision confirmed across all plan docs.
