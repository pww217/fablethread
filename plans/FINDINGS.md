# Findings — Consolidated Inventory

Consolidated from `plans/EVAL-FINDINGS.md`, `plans/tech-debt-findings.md`, and
the 2026-05-23 pipeline audit. Organized by shared concern, not severity — because
a broken extraction and a Jina syntax error are both "critical" but require
different responders.

Sources tagged: **[eval]** = eval run evidence, **[debt]** = code audit, **[audit]** = pipeline audit (this session).

---

## 1. Extraction Accuracy

LLM extraction streams produce wrong values or miss items entirely. The extractors
see the right context but emit incorrect JSON. These are not prompt-structure bugs;
they're instruction-adherence failures.

| # | Finding | Priority | Source | Status |
|---|---------|----------|--------|--------|
| 1.1 | Credits parsed as 5 instead of 200 at T3. Prompt says "emit that exact number" with "drop 200 credits" as example. | **P0** — economy collapsed to zero, cascaded across 5 subsequent turns | [eval] | open |
| 1.2 | Ledger + merchant_seal never extracted at T3 despite narration listing them explicitly. Phantom lifecycle: remove at T7 silently passes, re-add at T12 with no explanation. | **P0** — item exists in story but not state for 8 turns; causal break on thread resolve | [eval] | open |
| 1.3 | Halden NPC re-added as new at T12 (`npc_add` with full bio) despite being in compendium since turn 0. Should have been `npc_update` or no-op. | **P1** — state drift: NPC silently relocates between turns with no narration | [eval] | open |
| 1.4 | `scarred_tough` / `tough_b` NPC dedup failure at T9. Same character re-added as new under different ID. | **P1** — duplicate compendium entries for same NPC | [eval] | open |
| 1.5 | Implicit spending extracted at T13 but mechanically zero (credit stack was 0 since T4). LLM chose `amount: 1` instead of following few-shot "pay the dock boy" → `amount: 2`. | **P2** — no mechanical effect but cascading from 1.1 | [eval] | open |

**Root cause class:** LLM instruction adherence. Prompt rules exist but model
doesn't follow them consistently. The extract prompts have the right text; the
model is the failure mode.

---

## 2. Engine Validation Gaps

The engine allows invalid state operations to pass silently. These are not
extraction errors — the engine should catch them before they reach state.

| # | Finding | Priority | Source | Status |
|---|---------|----------|--------|--------|
| 2.1 | `inventory_remove` for non-existent items passes without rejection. Ledger was never in inventory but got removed at T7 with no warning. | **P0** — enables phantom lifecycle (finding 1.2) | [eval] [debt] | open |
| 2.2 | `reconcile_delta()` mutates `delta.inventory_add` / `pc_condition_add` in-place while also returning warnings. Caller can't distinguish "these are the changes" from "here's what went wrong." | **P0** — fragile delta reasoning; reconciled values overwrite original LLM output | [debt] | open |
| 2.3 | Scene tag assertions fail via exact-string match vs semantic equivalence. "confrontation" != "standoff" despite functional synonymy. | **P2** — false negatives in eval, not a runtime bug | [eval] | open |

**Root cause class:** Missing or weak validation boundaries. The engine trusts
upstream data too much.

---

## 3. Thread Lifecycle

The arc thread processing pipeline has a bug and a fragile pattern.

| # | Finding | Priority | Source | Status |
|---|---------|----------|--------|--------|
| 3.1 | Seed threads with `last_seen_turn=None` silently vanish when never advanced. The loop at `turn.py:147-175` has no else clause for "not advanced, not expired" threads. `santos_ledger` disappeared between T4-T5 with no resolve or demotion logged. | **P0** — thread data loss; cascades to missing context in storytell prompts | [audit] | **fixed** |
| 3.2 | `_apply_thread_resolutions()` uses fragile `dir()` introspection (`'remaining_completed' in dir()`) to detect variable existence instead of a boolean flag or sentinel. | **P3** — breaks silently if loop iteration changes | [debt] | open |

**Root cause class:** Incomplete control flow and fragile runtime detection.

---

## 4. Template & Prompt Bugs

Syntax errors, stale patterns, and rendering failures in prompt templates.

| # | Finding | Priority | Source | Status |
|---|---------|----------|--------|--------|
| 4.1 | `compact_user.j2:11` — unclosed `{% if arc %}` block. No `{% endif %}` before inventory/compendium sections. Crashes on every compaction turn (T3, T6, T9, T12). | **P0** — game breaks on compaction | [eval] [debt] | open |
| 4.2 | `narrate_system.j2` priority ordering references "stakes/directive" as third priority — the word "stakes" is architecturally ambiguous (general narrative concept vs removed data field). Not a runtime bug but perpetuates confusion. | **P4** — cosmetic | [audit] | open |
| 4.3 | `extract_scene_system.j2` NPC dedup rules exist (line 81) but model doesn't cross-reference compendium before `npc_add`. Prompt instructions are correct; adherence is the failure. | **P1** (paired with 1.3/1.4) | [eval] | open |

**Root cause class:** Template syntax error (4.1), stale language (4.2), instruction
adherence gap (4.3 — same class as section 1).

---

## 5. State / Docs vs. Code Drift

Dead fields in the codebase, stale configuration surfaces, and documentation
that describes things that no longer exist.

| # | Finding | Priority | Source | Status |
|---|---------|----------|--------|--------|
| 5.1 | `narrate.py:58` — dead `"phase": arc.get("phase", "setup")` in `current_arc_ctx`. No template consumes this field. | **P2** — dead code, misleading readers | [audit] | **fixed** |
| 5.2 | Four dead `EngineConfig` fields: `thread_urgency_building_at`, `thread_urgency_immediate_at`, `thread_urgency_immediate_ttl`, `avoidance_decay_per_turn`. Defined, set, configurable — never read. | **P2** — config surface bloat; users set keys that do nothing | [debt] | open |
| 5.3 | `warmup_on_start` — config says `false`, code default says `True`. File wins at runtime, but removing the key silently enables warmup. | **P2** — silent behavior change on config edit | [debt] | open |
| 5.4 | `setting_pack` config key labeled "Remove this, legacy" but still actively read by app startup. Code default (`expanse-belter`) doesn't match config value (`zombie-survival`). | **P2** — misleading "legacy" label | [debt] | open |
| 5.5 | `SYSTEM_PROMPTING.md` lists `stakes` as a field on `IntentEnvelope` — removed from model during simplification pass. | **P3** — stale documentation | [audit] | **fixed** |
| 5.6 | `judge.py:86,94` comments reference `stakes` in ruling output — removed field. | **P3** — stale comments | [audit] | **fixed** |
| 5.7 | `docs/architecture/campaign-arcs.md` references `phase` across 6 diagram/flow locations. Field removed from `CampaignArc` model. | **P3** — stale diagrams and prose | [audit] | **fixed** |
| 5.8 | `docs/architecture/OVERVIEW.md:55` lists `pending_beat` as input to Step 2c (Storytell). It only flows to narrate. | **P3** — stale documentation | [audit] | **fixed** |
| 5.9 | `docs/repomap.md:86` "velocity/pressures" — pressures system eliminated, now unified threads. | **P3** — stale terminology | [audit] | **fixed** |

**Root cause class:** Refactoring removed features without cleaning up parallel
representations (code fields, config surface, docs). Each removal needs a
coordinated sweep of all artifact types.

---

## 6. Code Quality & Structure

Monoliths, duplication, fragile patterns, and boundary violations.

| # | Finding | Priority | Source | Status |
|---|---------|----------|--------|--------|
| 6.1 | `run_turn()` — 800-line async generator monolith with ~15 responsibilities, complex error recovery, and yield-protocol dependency. | **P1** — prevents unit testing, blocks pipeline extension | [debt] | open |
| 6.2 | `apply_delta()` — 420-line function with 5 nested closures. NPC management (~220 lines) is an extractable module. | **P1** — hard to reason about, can't independently test | [debt] | open |
| 6.3 | Circular dependency: `engine` imports from `state` (local import to avoid cycle), imports private `_merge_arc_update`. Module boundary is wrong. | **P2** — non-standard import pattern, encapsulation violation | [debt] | open |
| 6.4 | Triple-duplicated averaging functions (`_avg_narrate_ms`, `_avg_extract_ms`, `_avg_ruling_ms`) — same logic, different field path. | **P1** — copy-paste debt; fix one bug in all three | [debt] | open |
| 6.5 | `apply_thinking()` no-op called from 6 locations with config keys that control nothing. | **P1** — dead code paths, misleading API surface | [debt] | open |
| 6.6 | 101 lines of mock infrastructure in production `llm_client.py` gated by env var. | **P1** — 33% of file is dead code during normal operation | [debt] | open |
| 6.7 | Duplicated coercion validators across `StateDelta` and `StateExtractResult` — identical logic, subtly different punctuation stripping on condition-remove. | **P2** — latent bug from divergent copies | [debt] | open |
| 6.8 | `fuzzy_match_inventory` exported in `__all__` despite underscore-private naming convention. | **P4** — misleading API surface | [debt] | open |
| 6.9 | `_capitalize_inventory_names()` mutates parameters in-place (side effect) while returning a value (suggests purity). | **P3** — violates principle of least surprise | [debt] | open |

**Root cause class:** Organic growth without refactoring boundaries.

---

## 7. Test & Tooling

| # | Finding | Priority | Source | Status |
|---|---------|----------|--------|--------|
| 7.1 | `ev.py mechanics` section markers looked for non-existent headers (`## gm_beat`, `## deescalate`, etc.) — all showed "(empty)" regardless of actual data. | **P2** — debug tool broken; impedes investigation | [audit] | **fixed** |
| 7.2 | `scripts/` not covered by `make check` (ruff + mypy skip it). No type-checking on debug tools. | **P3** — ev.py f-string lint errors weren't caught | [audit] | open |
| 7.3 | Eval scene tag assertions use exact-string membership (`in`) — "standoff" won't match "confrontation" despite functional synonymy. | **P2** — false negatives hide real extraction regressions | [eval] | open |
| 7.4 | NPC mention checker false positives ("Finally", "Trembling") — adverbs/participles not in stop list. | **P3** — eval noise, not a pipeline bug | [eval] | open |
| 7.5 | Eval mirror duplicates thread lifecycle constants (`_ACTIVE_THREAD_CAP`, `_EXPIRE_SILENT_TURNS`, `_PROMOTION_COOLDOWN_TURNS`) from `turn.py`. No sync mechanism. | **P2** — constants drift between engine and eval | [debt] | open |
| 7.6 | No state schema versioning — IO layer already has ad-hoc regex fix for old YAML format. Any future schema change needs more bandaids. | **P2** — silent data corruption risk | [debt] | open |

**Root cause class:** Tooling treated as second-class; eval and debug tools share
engine assumptions without a sync mechanism.

---

## Priority Matrix

| Priority | Criteria | Items |
|----------|----------|-------|
| **P0** | Breaks game at runtime or causes unrecoverable state corruption | 1.1 (credits 5→200), 1.2 (ledger phantom), 2.1 (inventory_remove silent pass), 2.2 (reconcile mutation), 3.1 (seed thread vanish — fixed), 4.1 (Jinja syntax) |
| **P1** | Structural — prevents testing, causes data drift, or blocks changes | 1.3 (Halden NPC), 1.4 (scarred_tough dedup), 4.3 (NPC dedup rules), 6.1 (run_turn monolith), 6.2 (apply_delta monolith), 6.4 (duplicated averaging), 6.5 (apply_thinking no-op), 6.6 (mock in production) |
| **P2** | Design boundary violations, config surface rot, tooling gaps | 1.5 (credits zero), 2.3 (exact tag match), 5.1 (dead phase — fixed), 5.2 (dead config keys), 5.3 (warmup mismatch), 5.4 (setting_pack legacy), 6.3 (circular dep), 6.7 (duplicate validators), 7.1 (ev.py — fixed), 7.3 (tag assertions), 7.5 (eval mirror drift), 7.6 (no schema versioning) |
| **P3** | Quality — fragile patterns, stale docs, side effects | 3.2 (dir() check), 5.5 (SYSTEM_PROMPTING.md stakes — fixed), 5.6 (judge.py comments — fixed), 5.7 (campaign-arcs.md phase — fixed), 5.8 (OVERVIEW.md pending_beat — fixed), 5.9 (repomap.md pressures — fixed), 6.9 (capitalize mutation), 7.2 (scripts not linted), 7.4 (NPC false positives) |
| **P4** | Cosmetic — misleading but harmless | 4.2 (narrate_system "stakes" phrasing), 6.8 (__all__ export) |

Note: `ccya/eval/judge.py` comments and `docs/architecture/*.md` doc fixes are
marked fixed because they were cleaned up during the pipeline audit. All other
items remain open.

---

## Connections Between Findings

```
1.1 (credits 5→200)  ──cascade──▶ 1.5 (implicit spend, zero stack)
                                     │
1.2 (ledger phantom)  ──enabled by──▶ 2.1 (inventory_remove silent pass)
                         │
                         └──enabled by──▶ 3.1 (thread vanish — not directly, but same validation gap)

1.3 (Halden NPC)  ──same root──▶ 1.4 (scarred_tough) ──same root──▶ 4.3 (NPC dedup rules)
     (LLM doesn't cross-reference compendium before npc_add)

3.1 (seed thread vanish)  ──causes──▶ missing context in storytell prompts turns 5+
```

The extraction accuracy cluster (1.1–1.5) is the highest-impact category. If
extractors emit correct values, half the cascading failures disappear. The engine
validation gaps (2.1, 2.2) are the safety net that should catch what extraction
misses, but they're also broken. Fixing both layers (extraction + validation)
would eliminate the entire phantom-item and zero-credit failure chain.

## Quick-Win Recommendations

1. **Fix Jinja syntax** (4.1) — 5 min, unblocks compaction
2. **Fix extraction prompts** (1.1, 1.2, 1.3, 1.4) — prompt adjustments, not code
3. **Add inventory_remove rejection** (2.1) — 2 hr, prevents phantom lifecycle
4. **Remove dead config keys + apply_thinking** (5.2, 6.5) — 30 min, clears surface
5. **Parameterize averaging functions** (6.4) — 1 hr, stop duplication

---

## Execution Ordering (low risk → high risk)

Plans are ordered so safe, mechanical changes run first. High-risk items (large blast radius, subtle logic, hard to validate) are deferred to the end. Each plan builds on prior context — run in sequence.

| Order | Plan | File | Risk | Why this order |
|-------|------|------|------|----------------|
| **01** | Extraction Accuracy | `01-extraction-accuracy.md` | 🟢 | Prompt-only changes — zero code risk, rollback by reverting template. Fixes the highest-impact failures (credits, ledger, NPC dedup) at source. |
| **02** | Test & Tooling | `02-test-and-tooling.md` | 🟢 | Additive only — new warnings, new tests, broader lint. No runtime behavior change. Establishes guardrails for later work. |
| **03** | Code Quality | `03-code-quality.md` | 🟢 | Mechanical refactors — parameterize averaging fns, deduplicate validators, replace `dir()` check, extract mock infra. Zero logic change per phase. **Note:** Phase 4 (mock extraction) touches `llm_client.py` and should wait until after plan 05 removes `apply_thinking()` from the same file. |
| **04** | Critical Pipeline Fixes | `04-critical-pipeline-fixes.md` | 🟡 | Phase 1 trivial (Jinja `{% endif %}`). Phase 2 changes `reconcile_delta()` return type — affects every turn but is a mechanical unpack change at one call site. |
| **05** | Config Surface Cleanup | `05-config-surface-cleanup.md` | 🔴 | Phase 2 (remove `apply_thinking()`) touches 11 sites across 3 files: function definition, 5 call sites, 3 function signatures, 3 pipeline-level kwarg passes, config fields + YAML. One miss = AttributeError at runtime. Validation is import-only, not runtime. |
| **06** | Structural Refactors | `06-structural-refactors.md` | 🔴 | Phase 1 extracts 220 lines of nested closures from `apply_delta()` — subtle capture semantics. Phase 2 decomposes an 844-line async generator with SSE yield protocol — hardest to validate (manual diff). Phase 3 resolves circular dep; Phase 4 adds schema versioning. Plan 04 must run first (Phase 3 depends on `reconcile_delta` return type change). |

### Cross-plan dependency summary

| Plan | Depends on |
|------|-----------|
| 03 (code-quality) Phase 4 | 05 (config-cleanup) Phase 2 — both edit `llm_client.py` |
| 06 (structural-refactors) Phase 3 | 04 (pipeline-fixes) Phase 2 — `reconcile_delta` signature changed |

All other plans are independent and can be executed in any order within their risk tier.
