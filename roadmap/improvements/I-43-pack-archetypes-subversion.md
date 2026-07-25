---
title: "Subvert and sharpen seed pools across all 5 default packs with maximum per-entry diversity"
status: scoping
urgency: 3
size: medium
created: 2026-07-25
ticket_id: I-43
labels: [seeds, packs, creative-content]
design: docs/design/pack-archetypes-subversion-design.md
plan:
pr:
  url:
  branch:
---

## Description

Creative rewrite of all seed pools across the five default packs (`noir-1930s`, `zombie-survival`, `space-western`, `golden-piracy`, `allied-ww2`). Driven by inventory in `docs/findings/pack-archetypes-inspiration.md`, which flagged `situation_archetypes` and `arc_categories` as database-column language and `pc_situation_schema` as character-sheet blanks.

Improvement, not a feature — packs already exist; we are improving their content, not adding new capability.

## Core mandate

**Per-entry subversion, not per-pack.** Every entry in every pool carries its own distinct subversion direction; no two entries in the same pool subvert in the same direction. The point is **combinatorial diversity**: when the seed sampler pulls N entries from M pools, two random seeds from the same pack should be able to produce two stories that share no central tension.

Prior draft used "one subversion angle per pack" — rejected by review because it collapses the cross-product to one story per pack, defeating the pool-based seed system.

## Scope (in this ticket)

- All 5 default pack `scenario.yaml` files rewritten verbatim from the design's YAML exhibits
- 7 pools per pack × 5 packs = 35 pool rewrites (241 id-bearing entries + 20 pc_schema fields total)
- Author 3 new `packs/default/{zombie-survival,space-western,allied-ww2}/world.md` files from the design's world-bible exhibits (verbatim copy)
- YAML contracts unchanged; IDs renamed where sharpening demands; **lowercase snake_case ASCII enforced** (id renames verified post-write)
- Pool counts unchanged (noir/zombie: 10 situations / 14 arcs / 8 dyn / 8 bonds / 7 scenes / 4 pc; space-western/piracy/ww2: 12 situations / 14 arcs / 8 dyn / 8 bonds / 7 scenes / 4 pc)
- `world_rules` block on noir and piracy preserved (no supernatural, period-bound)

## Verification

- `make check` passes
- ≥1 `ev.py prompt-eval` per pack; subverted seeds produce charged openings, not jokes/self-references
- Per-pack subversion-axis tables embedded in design (post-axis-revision) — review-design rejects any duplicate axis within a pool
- 3 randomly-sampled seeds per pack reviewed blind; central tensions must differ (or axis table rejected)
- Token delta on representative seed prompt per pool ≤15%
- `incompatible_with` pairs preserved across renames (rename table verified against the design's YAML blocks; noir, zombie, piracy each have non-empty incompatible edges; space-western has one pair; ww2 has none)
- Each new `pc_situation_schema` field accepts ≥2 distinct valid answers from different PCs
- Each scene bundle retains its atmosphere (period-appropriate) plus exactly one period-plausible-but-story-generating wrong detail

## Status

Design complete in full (firm decision #12 — full phrasing). All YAML exhibits and world-bible exhibits are copy-paste-ready. The plan phase is mechanical: copy design → `packs/default/<pack>/scenario.yaml` (+ world.md exhibits for the three new bibles); run `make check`; run `ev.py prompt-eval` per pack; run blind triage of 3 sampled seeds per pack.

Ready for `review-design` pass.

## Done when

- All five `scenario.yaml` files rewritten against the design bar (verbatim copy from exhibits)
- Three new `world.md` files authored under the design's postures (verbatim copy from exhibits)
- All verification items above pass
- Design status flipped to `implemented` via execute skill