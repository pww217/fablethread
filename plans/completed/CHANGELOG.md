# CHANGELOG — ccya remediation

> **Experiment context**: this file documents a head-to-head comparison between a
> **local agent** (scaffolding pass, one-shot, smollm-class model) and a
> **frontier cloud agent** (remediation pass, Sonnet 4.6) working from the same
> `plan.md` design document. The goal: quantify where local-model one-shot
> scaffolding succeeds and fails, and whether the failure modes are predictable.
>
> *Archived: original at `docs/CHANGELOG.md`. This is a reference document, not a living log.*

---

## Unreleased (2026-04-30)

### Pack system & world generation
- **Pack picker:** New Game button opens a modal listing all packs from `packs/`; each card shows name, mode badge (dynamic/static), description, and tone tags. Selecting a card posts `pack_id` to `/new-game` and switches the active pack for the session. `POST /new-game` now accepts optional `pack_id` form field; `list_packs()` drives the new `GET /panels/pack-picker` endpoint.
- **expanse-belter → dynamic:** Converted from static (`seed_state.yaml` + `opening_scene.md`) to dynamic pack. Added `world.md` (canon: physics, political landscape, OPA/UN/MCRN factions, Ceres economics), `scenario.yaml` (constraints, inspiration blocks for PC / opening / NPCs / inventory / quests, cliché guards). Every new game now generates a fresh Belter scenario via `generate_seed`.
- **Established facts overhaul:** Prompt now requires exactly **12 facts: 5 global + 7 local**. Global facts must consolidate (one entry covers a faction's full picture, not one entry per slang word). Local facts must be substantial and consequential, drawn from four categories: faction/power, recent major event, infrastructure/resource, local history. Hard ban on glossary entries, character traits, NPC opinions, genre platitudes, and portable facts. Belter creole glossary removed from `world.md` (already in `style.md`); moved from facts to style where it belongs.
- **Cliché guards (zombie-survival):** Added `"chronic illness or disability as a defining character trait"` and `"mysterious past illness"` to `forbid_cliches`. PC inspiration block now explicitly says most survivors are just tired, not sick.

### UI & UX
- **Chronicle (turn log):** Moved from an absolute overlay above the narrative panel to a pill in the **header bar**, centered between the logo (left, flex:1) and the meta group (right, flex:1). Blue accent (`#60a5fa` border/fill), 📖 emoji, uppercase label. Opens an overlay anchored to `.narrative-column` (`position: absolute; inset: 0; z-index: 20`); backdrop blurs the narrative; panel fills the column. Zero footprint when closed.
- **Scrolling fixed:** Removed broken `narrative-panel-wrap` wrapper that was collapsing the flex chain (and the stray closing `</div>` from a partial edit). `narrative-column` is now `position: relative`; `narrative-panel` inherits `flex: 1; min-height: 0; overflow-y: auto` correctly.
- **Stop button:** Removed the separate Stop button from the input bar. The Send button turns red (`--accent-error`) with a white spinner while inference is running; clicking it calls `stopTurn()`. Same size, same position, same spin animation.
- **Turn summary modal:** Enter key (in addition to Escape and clicking Dismiss) now closes the modal. Dismiss hint ("Press Enter or Esc to dismiss") rendered as a small italic centered line below the Dismiss button.
- **Scene card:** Removed atmospheric `scene-tags-row` chips from the top of the Scene card. NPC `notes` render without `data-md` (plain text, not markdown-parsed) so font sizing is preserved; `.npc-item .npc-notes-inline, .npc-item .npc-notes-inline *` rule gives high-specificity 11px / muted / italic styling matching `.npc-title`.
- **Debug panel:** Removed trace ID column, TTFT (1st tok) column, retry column, "LLM I/O log" row, "Log file" row, and `tail -f` hint. Columns: `# / narrate / extract / tok in/out`. Tok in/out rendered on two lines (`N…/…\nE…/…`, `white-space: pre-line`). Order: turns table → status → errors (errors section hidden when empty).
- **Narration metrics:** Token counts removed from the inline metrics row under each turn block; only timing (`narrate Xs · extract Ys`) shown. Token counts remain in Debug panel and `events.jsonl`.
- **CSS cache-busting:** `app.css?v={mtime}` query string injected at page render time so CSS reloads automatically after `make css`.

### Prompts
- **`extract_system.j2`:** Five user-authored guidance lines moved from the preamble into their matching field guidance entries verbatim.

## Unreleased (2026-04-28)

*(Full entry preserved in `docs/CHANGELOG.md`)*

---

*Remediation completed: 2026-04-27 by Sonnet 4.6 (cloud agent).*
*Scaffolding completed: 2026-04-26 by local agent (model unknown, likely smollm-class based on config.yaml `model: smollm:135m`).*
