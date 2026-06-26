# Development timeline

*A lightly fictionalized tour of how this codebase got from "local LLM MVP" to "what it is now," as told by the release notes themselves.*

> Disclaimer: dates, version numbers, and commit counts are real. Everything else is tone. If the tone lands wrong somewhere, that's on me, not the git log.

---

## The eras

### The MVP (0.1.0 — 2026-04-30)

Six commits. Two of them are essentially "this is what a choose-your-own-adventure engine looks like," and the other four are "now it actually works." The opening scene is set on Ceres Station aboard a ship called the *Wretch* with a captain named Niko Sato. That setting still informs the project today, though the *Wretch* herself has been mostly a background character in every release since.

A note on the initial commit: the first line of `Initial commit: ccya MVP` is short. Every commit after it is a 2,000-character essay about everything that was wrong with the previous one.

### The Foundation Months (0.2.0 – 0.4.0)

Eighty-six commits over roughly a week. This is the period where the project decided what it was: a **pack-based engine** with a **narrate-then-extract** two-call pipeline, a **turn viewer** for replaying sessions, a **sidebars redesign** that is still the skeleton of the UI, and an **eval harness** that would later grow into a small empire.

The skill system was six skills here. Lore and Resolve would not survive.

Also during this era: a four-judge evaluation system was prototyped, thrown out, and rebuilt as a single-judge harness within the same release cycle. This would not be the last time the eval system was rewritten.

### The First Arc (0.5.0 – 0.5.2)

The **arc system** was introduced in 0.5.0. It was already a multi-phase plan with a separate design doc. The first version was called `arc-system-improvements` and shipped in two pieces: 0.5.0 added the mechanic, 0.5.1 fixed it, 0.5.2 fixed the fixes.

0.5.2 is the **"rip out all tests for now"** release. There is a commit in the changelog that is literally `rip out all tests for now`. It sits next to `Replace implementation plan with design documents` and `consolidate repomap: merge 14 files into single docs/repomap.md`. This release is the moment the project decided that **design docs were the spec, and tests were for later**.

(Later still has not arrived.)

### The Eval Era (0.6.0 – 0.9.0)

A quieter period. The eval harness was rebuilt three times in this stretch. NPC behavior was refined. The skill cap was reduced. 0.8.0 brought in a `npc_state` and 0.9.0 added `npc.personality` as a concept that would not pay off for another 16 releases.

The dice system got attention here too: the project moved from 2d6 to 1d12, then experimented with hybrid systems. The verdict on which is better is still out.

### The Great Consolidation (0.10.0 — 2026-05-26)

**110 commits in two days.** This is the single biggest release in the project's history by commit count.

The headline change: the **narration pipeline was mechanically consolidated**. The old system had `ProgressExtractResult` separately from thread operations; the new system unified them into a single model. The migration code that bridged the two was **deleted in the same release**, with a commit message that explicitly says `delete migration code (no backward compat)`.

The era was named `narration-mechanical-consolidation`. It produced, among other things:
- A six-phase plan, of which Phases 01–06 all shipped in this one release
- A `LlmcError` hierarchy and structured logging
- The first appearance of "convergence scoring" as an idea
- A design doc that referenced 14 source files and consolidated them into one

This is also the release that the **prompts** started being treated as first-class code. Every change to a `*.j2` template is now a git event. Before 0.10.0 they were configs. After 0.10.0 they are architecture.

### The Threading Era (0.11.0 – 0.16.0)

A long, busy period that mostly fought the **thread lifecycle**. Threads are the things that track "the player is investigating the cult" and "the player's sword is cursed." The lifecycle of a thread — when it appears, when it advances, when it goes dormant, when it dies — was the source of approximately 80% of all the eval findings in this period.

Highlights:
- **0.13.0**: skills cut from 6 to 4. Lore and Resolve are gone. The commit message for this is `cut-to-four-skills: remove lore/resolve, reduce to strength/dexterity/wits/charisma`. Strength, Dexterity, Wits, Charisma are still the four skills.
- **0.13.0**: also introduced **dual-track evals** (baseline + experimental). The experimentals are still in use.
- **0.14.0**: the **pacing system** is introduced. A four-page plan with five sections. It will not be the last pacing system.
- **0.15.0**: **arc thread overhaul, phase 1**. Phases 2 and 3 ship in the same release.
- **0.16.0**: the **GM beat system** is wired in. The first commit that mentions `gm_beat` shows up here.

### The Pacing Rollercoaster (0.17.0 – 0.27.0)

This is the era that produces the project's most-quoted line.

> `architectural doc updates including rube goldberg pacing system`
> — 0.26.0

A **Rube Goldberg machine** is a device that does a simple thing in the most complicated possible way. The pacing system in 0.26.0 was, by the project's own admission, a Rube Goldberg machine. The next release (0.27.0) replaced it with **convergence scoring**, which is a much simpler idea: count the number of pressure threads of the same direction, and if it crosses a threshold, escalate the scene. The threshold was tuned, retuned, lowered from 3 to 2, and ultimately questioned.

During this stretch:
- 0.17.0, 0.17.1, 0.17.2, 0.17.3 are all **hotfix releases** to the same code path. 0.17.3 shipped *after* 0.18.0 in tag-creation order. This is a git-historical fact and we will not be discussing it further.
- 0.18.0 rewrites the **arc system again** in four phases. "Phase 1" through "Phase 4" are real strings in real commit messages.
- 0.21.0 introduces the **NPC compendium** as a first-class idea. 0.22.0 promotes NPC lifecycle to a tracked concern. 0.24.0 finalizes the compendium.
- 0.27.0 ships the **convergence engine**. 47 commits. The header of the release notes reads: *"directive/spiral beat constraint overhaul, 7 new checkers + prompt fix for location descriptions, Add tension_delta field, scene phase config thresholds, and ruling prompt schema."* This is the most ambitious single release since 0.10.0.

### The Second Great Redesign (0.28.0 – 0.29.0)

0.28.0: a smaller release focused on **logging**, **condition TTL**, and **persona prompts**. The `validating→testing` rename happened here, then was immediately renamed back to `validating` in 0.30.0. The reasoning was sound both times.

0.29.0: **119 commits, the most ambitious arc-system rewrite yet.**

The arc system is now built on **semantic thread types**. Each thread has a `type` and a `dormant` flag. The dormant flag replaced the old `active` flag. The change `active → dormant` is a one-line rename. The commit that does it is titled `fix-type-errors: Replace active with dormant across all consuming code + add type to ThreadUpdate`. It is one of seven commits in a five-phase plan called `semantic-thread-types`.

During this era, the project also:
- Migrated from **Linear to roadmap files**. 80 Linear tickets became 66 roadmap files. 14 tickets were lost in translation. (They were mostly duplicates.)
- Rebuilt the turn viewer into a single-column view with output-summary pills.
- Split `turn.py` into `turn_context.py` and `turn_state.py`. Split `engine/extraction/pipeline.py` (803 lines) into a subpackage with 7 files. Split `ccya/models.py` into a subpackage.
- Replaced the **GM beat** with a **scene-driven beat system**. "Replace storytell-generated beats with scene-driven beat generation" is one of the most carefully-written commit messages in the project. The reasoning is real. The transition is real. The next release will probably reconsider the design.

### The Present (0.30.0)

One commit. Renames `testing` to `validating`. The release notes are 13 lines long.

This is the calm after the storm. The storm will be back. It always comes back.

---

## The refrains

### The Arc System That Would Not Die

The arc system has been introduced, redesigned, and re-redesigned three times in this project's history.

- **0.5.0**: first introduction. Arc system v1. Has the concept of a "phase" and a "drift."
- **0.10.0**: unification. Arc threads are now part of the unified thread model. Migration code is deleted.
- **0.18.0**: arc system v2. Four phases. `ArcResolution` gets a structured `successor` field. `CampaignArc` is now a real model.
- **0.29.0**: arc system v3. Semantic thread types. `active` becomes `dormant`. Arc thread origin is now a seed-time concept.

Each of these was the **right call at the time**. Each was driven by a real eval finding or a real prompt-completion bug. None of them was a mistake, in the sense that the project was wrong to do them. They are, however, a pattern: every 10–15 releases, the arc system gets the full treatment.

Predicted next arc-system overhaul: 0.39.0.

### Pacing: A Counting Problem

The pacing system has had four major designs.

1. **Pressure TTL** (0.5.0): every pressure has a time-to-live. If it expires, it decays. Simple. The TTL races against the storyteller, which sometimes emits a `null` beat and forgets to clear `pending_gm_beat`. The whole system was diagnosed as broken in 0.13.0.
2. **Momentum / Floor Relief** (0.13.0): the scene has a "momentum" that decays unless the LLM keeps writing in the same direction. Threshold-based. The thresholds were tuned, retuned, and ultimately questioned.
3. **Convergence Scoring** (0.27.0): count threads pointing the same direction, escalate when the count crosses a threshold. Threshold lowered from 3 to 2. Worked better. Worked *differently* than pressure TTL.
4. **Phase Engine** (0.29.0): scenes have phases (setup → rise → climax → relief). Each phase has allowed beat types. Beats are scene-driven, not LLM-driven.

What these all have in common: **they are all about counting something and escalating when the count gets weird.** The project's opinion on what to count has changed four times.

The "rube goldberg" line in 0.26.0 is funny in retrospect, but it was also honest. The author of the doc knew.

### The NPC Compendium's Long Road to Presence

The NPC system has its own archaeology:

- **0.4.0**: NPCs are `SeedNPC` records in a pack. Compendium is implicit.
- **0.5.1**: `present_npcs` becomes a first-class state field. Compendium starts being treated as separate from the active cast.
- **0.20.0**: NPC **personality** is LLM-assigned from archetypes. Engine fallback if the LLM doesn't pick one.
- **0.21.0**: NPC lifecycle is tracked: `present`, `nearby`, `departed`. Proximity-decay rules added.
- **0.23.0**: the **NPC compendium** is finalized. Departed NPCs get archived.
- **0.27.0**: NPCs default to `presence=present` in seed generation. (The fix for an eval finding where NPCs kept vanishing between scenes.)
- **0.29.0**: NPCs get **distinguishing descriptors** via prompt guidance, so two NPCs named "Guard" don't collapse into one.

The number of commits that touch NPC state is roughly 11% of the total commit count over the project's lifetime. This is a guess, but the order of magnitude is right.

### The Continuous Rename

The project has a strong tradition of renaming things. This is not a complaint; the renames have mostly been improvements. The tradition includes:

- `progress` → `storytell` (0.18.0, 4-phase plan)
- `storytell` → `record` (0.29.0, post-refactor cleanup)
- `rules` → `ruling` (gradual, over several releases)
- `state_snapshot` → `last_turn_state` (0.29.0)
- `active` → `dormant` (0.29.0, semantic-thread-types phase 01)
- `surface_as` → `effect` (0.29.0)
- `validating` → `testing` (0.28.0) → `validating` (0.30.0)

Each rename touched a meaningful fraction of the codebase. Each was justified. The cost of each was real. The total cost of all of them was a non-trivial fraction of the project's total development time, and this is a known and accepted cost of working in a system that is being designed while it is being built.

The fact that the renames were *consistent* — that the project knew what it wanted to call things once it figured it out — is the only thing that prevented this from being a disaster.

### Rip Out All The Tests

0.5.2 has a commit message that is just `rip out all tests for now`.

The full context: the project had a 76-test suite for the turn pipeline. The tests were not bad. They were testing real things. They were also slowing down every refactor, because every refactor had to update them. The decision was made: **the design docs are the spec, the eval scenarios are the verification, and the unit tests can come back later.**

The tests have not come back.

The eval scenarios have. There are now roughly 130 deterministic checkers across 5 packs, and the eval runs after every significant change. The eval scenarios are not as fast as unit tests, and they are not as reliable. They are, however, *the spec*, and that is more important than being fast.

This is the project's most controversial decision. It is also, in retrospect, the decision that made 0.10.0 and 0.29.0 possible.

### The 0.10.0 Effect

The pattern of the project is: **boring, quiet work for a few weeks, then a single release that consolidates everything into a new shape.** 0.10.0 is the canonical example. So is 0.29.0. So is, on a smaller scale, 0.18.0.

These are the releases that produce the most commits, the most eval re-runs, and the most "delete migration code" lines. They are also the releases that future work builds on. Most of the architectural surface of the project today was set in one of these consolidations.

The 0.10.0 Effect: *the boring work is load-bearing.*

---

## The current state

As of 0.30.0:

- **Two-call pipeline** still in place: narrate → extract. The narrate step is now called `record`, and the extract step is now called `ruling`. The pipeline is otherwise the same shape it was in 0.1.0.
- **Four skills**: Strength, Dexterity, Wits, Charisma. This has been stable for ~17 releases.
- **Single arc system** with semantic thread types. This has been stable for one release.
- **Phase-based pacing engine** with convergence scoring underneath. This has been stable for one release.
- **Pydantic models** split into a subpackage. The split is recent enough that not all consumers import from the new location.
- **Eval harness** with 130 checkers across 5 packs, multi-judge synthesis, and a meta-report. The harness is the single most-tested piece of code in the project.
- **Roadmap files** in `roadmap/`, generated by `make roadmap`. Linear is gone.
- **Tests**: zero. This is intentional, see above.
- **Documentation**: substantial. There is a real architecture doc, broken into 13 subdocs. There is a real AGENTS.md, a real repomap, and a real set of release notes (this document included).

---

## Predictions for the next era

Based on the patterns above:

- **0.31.0 will rename something.** Probably something subtle, like `dormant` → `inactive` (in the next round of `active`-avoidance renames).
- **0.32.0 or 0.33.0 will introduce a new check on the eval harness.** New checkers are added roughly every 4–5 releases.
- **0.35.0 will be a consolidation release.** The pattern is too strong to break.
- **0.40.0 will be the next arc-system overhaul.** Give or take two releases.
- **Tests will not come back this year.** Possibly not next year either.
- **The opening scene will still be set on Ceres Station.** The *Wretch* will be mentioned in passing.
- **A new "rube goldberg" line will appear in a commit message within 10 releases.** History rhymes.

---

## Coda

This document is itself a release artifact. It is the only release artifact that is intentionally fun. Future maintainers who find this file in `docs/releases/`: the answer to "is this the real history of the project" is *yes, mostly, with jokes*. The answer to "should I trust the joke more than the git log" is *no, never*.

The git log is the truth. The jokes are just a reminder that the truth was sometimes funny at the time.
