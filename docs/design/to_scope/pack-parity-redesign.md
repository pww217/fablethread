# Pack Parity Redesign

> **Status:** reviewed
> **Related designs:**
> - [Pack Validation](./pack-validation-design.md) — **depends on this.** Pack parity requires a single validation gate that both YAML authoring and LLM generation paths must pass.
> - [Dynamic Factions](./dynamic-factions-redesign.md) — **related.** Dynamic factions need to generate factions that conform to the same schema as hardcoded factions. Pack parity should ensure generated factions meet the same quality bar as default pack factions.
> - [World Creator Seed Pack](./world-creator-seed-pack.md) — **related.** User-authored packs need the same parity as auto-generated ones. Both should pass the same validation gate.
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work. Write the plan only after [Pack Validation](./pack-validation-design.md) is implemented.

## Problem Statement

Generated packs and default packs should play identically at runtime. Both paths must
pass the same `validate_pack()` gate (from pack-validation), but parity goes further:
content quality should be equivalent — generated pools should be as rich as hand-authored
ones, factions should be as well-defined, and the overall seed should feel as crafted.

Pack validation enforces structural correctness by construction. Pack parity enforces
content quality — ensuring the LLM produces packs that don't just conform to the schema
but actually play as well as default packs.

## Non-Goals

- **Content quality.** Validation checks structure, not whether pool descriptions are well-written or factions are interesting. That's eval territory.
- **Dynamic factions.** Factions will be redesigned separately (see [Dynamic Factions](./dynamic-factions-redesign.md)).
- **World creator seed pack.** The step before seed generation (for users who want to make their own packs) needs separate design work (see [World Creator Seed Pack](./world-creator-seed-pack.md)).
- **Backward compatibility.** No migration shims for old pack formats. Old packs that don't conform are simply invalid.

## Open Questions

- What content quality gaps exist between default pack and generated pack output?
- How should we measure "parity" — via eval rubric, via manual comparison, or both?
- What's the minimum viable parity for this redesign?
- How does `pc_situation_schema` vary between packs, and should generated packs match default pack schemas?
- How do dynamic factions interact with generated packs — should they generate factions at seed time or pack time?

## Scope

This design assumes [Pack Validation](./pack-validation-design.md) is already implemented.
It needs contract alignment with seed worldbuilding redesign and world state lifecycle,
but should focus on content quality rather than structural correctness (which validation
handles).

## Review Findings (2026-07-10)

### FATAL: Design doc claims are stale

- **[FATAL] pack-parity-redesign.md:5** — Claims pack-validation is "already implemented" but
  the pack-validation design doc (`pack-validation-design.md:3`) still shows `status: scoping`.
  F-15 was merged (commit `bb67363f` on origin/main) but **origin/main has diverged from local main**.
  Local workspace is at `5062ae64` (I-39), while origin/main is at `bb67363f`. The validate_pack()
  function exists on origin/main but not in the local workspace. **Action: `git pull` to sync.**

- **[FATAL] pack-validation-design.md:69** — Shows `baseline_facts` in the proposed PackManifest schema.
  **Source check:** baseline_facts was removed from PackManifest in F-15. The current PackManifest
  (`ccya/pack.py:237-245`) has `extra: ignore` (NOT `extra: forbid`), and does NOT have
  `description`, `version`, `mode`, `files`, or `PackFiles`. **The pack-validation design doc is
  factually wrong about its own implementation.** It describes a schema that was never committed.

- **[CRITICAL] pack-parity-redesign.md:14-17** — Problem statement says "generated packs and default
  packs should play identically" but this is an aspiration, not a diagnosis. The actual gaps are:
  1. **Generated packs are missing manifest fields:** `generate_pack.py:149-155` creates PackManifest
     with only `id`, `name`, `tone_tags`, `name_locales`, `use_male_only_names`. Missing:
     `description`, `files` — both of which default packs have. `version` and `mode` are dead fields
     (removed in pack-parity redesign).
  2. **No content quality enforcement:** validate_pack() checks structural integrity (unique IDs,
     valid refs, min lengths) but does NOT check that generated pool content is "rich" or
     "interesting." This is inherently eval-bound, not code-enforceable.
  3. **generate_pack.py has no validation:** `generate_pack.py:126` creates ScenarioBrief from LLM
     output without calling validate_pack(). Files are written to disk, and validation only runs
     at load_pack() time. A malformed generated pack crashes the game at startup, not at generation
     time.

### Design Ambiguities

- **[QUESTION]** What does "content quality" mean operationally? The design asks "how should we
  measure parity?" but never answers. Possible interpretations:
  - Structural parity (all required fields populated) — enforceable via validate_pack() extension
  - Content richness (generated pools have comparable detail to default packs) — eval-only
  - Behavioral parity (games feel equivalent) — eval-only
  The plan should focus on **structural parity** (enforceable) and defer **content quality** (eval).

- **[QUESTION]** Should validate_pack() enforce minimum pool sizes? Currently ScenarioBrief has
  `max_length` constraints on pools but no `min_length`. validate_pack() checks `world_facts >= 3`
  but not `situation_archetypes >= 1`, `arc_categories >= 1`, etc. Empty pools cause
  `_select_from_pool()` to raise ValueError at seed time. Should validation catch this earlier?

- **[QUESTION]** What contract alignment with seed worldbuilding redesign is needed?
  Answer: **none needed** — the seed worldbuilding redesign's contract is already implemented:
  - pc_situation_schema is the only pack-specific field that legitimately varies between packs
  - The funnel design (generation order) is implemented in seed.py:132-152
  - pc_situation_schema flows through routes.py → seed prompt → engine consistently
  - No contract change needed for pack parity

### Non-blocking concerns

#### Suggested Improvements

- **[WARN] pack-parity-redesign.md:25-29** — Open Questions mix structural and content concerns.
  Separate them: structural questions (what fields must be populated, min counts, validation rules)
  vs. content questions (richness, quality, eval metrics). The structural questions can be answered
  by plan; the content questions require eval infrastructure.

- **[WARN] pack-validation-design.md:184** — "Non-Goals: Pool emptiness" says "Seed generation already
  validates pool emptiness via `_select_from_pool()` ValueError." This is a late failure mode. The
  plan should consider adding `min_length` to validate_pack() so empty pools are caught at pack load
  time, not at seed time.

- **[WARN] pack-validation-design.md:148-150** — `list_packs()` warning behavior: "mark the pack as
  invalid" but PackManifest has no `valid` field. The current implementation (`pack.py:354`) just logs
  and skips. To support UI "invalid pack" markers, either add a `valid: bool` field or return a
  wrapper type.

#### Minor Notes

- **[MINOR] pack-parity-redesign.md:9-10** — "This is a placeholder" note is accurate. Consider
  renaming the file to `pack-parity-redesign-PLACEHOLDER.md` or moving to a `drafts/` directory
  to signal "not ready for review" more explicitly.

- **[MINOR] pack-validation-design.md:106** — Pool fields list omits `factions` from the
  `_validate_pool_entries()` check but factions have their own uniqueness check (section 4).
  This is correct but the comment "all pool fields in ScenarioBrief" is misleading since factions
  are handled separately.

- **[MINOR] pack-parity-redesign.md:28** — `pc_situation_schema` question is valid but the answer
  is already in source: `ccya/pack.py:136-143` defines it as per-pack keys. The only constraint is
  unique keys (enforced by validate_pack()). No minimum count — a pack may legitimately have 0 keys.
