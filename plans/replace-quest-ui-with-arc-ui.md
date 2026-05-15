# Replace Quest UI with Arc UI

## Status
`open`

## Objective
Rip out all frontend quest pieces (Quests sidebar card, quest CSS, quest JS, quest form field, quest_close turn viewer) and replace with an Arc sidebar card showing campaign phase, active threads, latent thread teasers, and discovered hidden truths.

## Non-goals
- Backend arc system (covered by `quest-story-arc-revamp.md`)
- NPC motivation/fear/leverage UI (flavor-only, flows to narrator)
- PC drive UI (shown in narrator context, not sidebar)
- Expressed stances UI (internal signal for narrator)

## Firm decisions
1. The Quests card is removed entirely — no migration path, no "legacy" mode.
2. The Arc card goes between Location and Compendium in the sidebar (replacing Quests position).
3. Latent threads are shown as teasers (id + tags only, no summary) to create anticipation without spoilers.
4. Hidden truths start as "[REDACTED]" and reveal text when discovered.
5. The char creation "Quest" field is replaced with "Arc" (maps to existing `arc_hints` in PlayerOverrides).
6. `quest_hints` form field is dead code (PlayerOverrides has `arc_hints`, not `quest_hints`) — removed.
7. `quest_close` sanitization display in turn viewer is removed (compactor no longer has quest_close).

## Conflicts and overlap
- None. This plan touches only frontend files (templates, CSS, JS) and state defaults. The existing `quest-story-arc-revamp.md` plan covers backend models/prompts/engine. No file overlap.

## Implementation — Phase 1: Remove quest frontend

### Context files to load
1. `ccya/templates/_state_left.html`
2. `ccya/static/app.src.css`
3. `ccya/templates/index.html`
4. `ccya/templates/_char_creation.html`
5. `ccya/templates/_turn_viewer.html`
6. `ccya/state/io.py`

### Detailed steps

#### Step 1.1 — Remove Quests card from _state_left.html

**File:** `ccya/templates/_state_left.html`

**What:** Delete lines 99–173 (the entire Quests card block). Replace with an Arc card (see Step 2.1 for the replacement HTML).

**Why:** The Quests card is the only frontend quest UI. It renders `state.quests` which is never populated by the engine (quests are dead code — no extractor emits quest_updates, no delta handler processes them).

#### Step 1.2 — Remove quest CSS from app.src.css

**File:** `ccya/static/app.src.css`

**What:** Remove these CSS sections:
- Lines 505–506: `.sidebar-card[data-card="quests"]` from scrollable card body selector
- Lines 528–529: `.sidebar-card[data-card="quests"]` from scrollbar selector
- Lines 536–537: `.sidebar-card[data-card="quests"]` from scrollbar-thumb selector
- Lines 1005–1193: Entire "SIDEBAR — QUESTS" section (`.quest-item`, `.quest-title`, `.quest-status-badge`, `.objective`, `.quest-objectives`, `.quest-tabs`, `.quest-tab`, `.quest-list-panel`, all status variants)

**Why:** All quest CSS is unused once the Quests card is removed.

#### Step 1.3 — Remove quest JS from index.html

**File:** `ccya/templates/index.html`

**What:** Remove:
- Lines 198–199: `CCYA_QUESTS_TAB` and `CCYA_QUEST_OBJ_KEY` constants
- Lines 575–583: `restoreQuestState()` function (localStorage restore for quest objective open state)
- Lines 585–600: `initQuestTabs()` function (quest tab switching)
- Lines 1622–1623: Event listener for `details.quest-objectives` open state persistence
- Lines 1644–1653: Event listener for quest tab clicks
- Line 601: `quest_hints: ''` in the char creation data object
- Lines 963, 972: `questHintsInput` form field handling (read and append to form)

**Why:** All quest JS is dead once the Quests card is removed. The `quest_hints` form field is also dead code (PlayerOverrides uses `arc_hints`, not `quest_hints`).

#### Step 1.4 — Remove quest field from char creation

**File:** `ccya/templates/_char_creation.html`

**What:** Replace lines 108–113 (the Quest textarea) with an Arc textarea:

```html
<div class="char-creation-field">
    <label class="char-creation-label" for="cc-arc-hints">Arc</label>
    <textarea id="cc-arc-hints" class="char-creation-textarea"
              x-model="arc_hints" rows="2"
              placeholder="e.g. A rescue mission gone wrong"></textarea>
</div>
```

**Why:** The existing `quest_hints` field maps to nothing (PlayerOverrides has `arc_hints`, not `quest_hints`). Rename to `arc_hints` so it actually flows through to seed generation.

#### Step 1.5 — Remove quest_close from turn viewer

**File:** `ccya/templates/_turn_viewer.html`

**What:** Remove lines 73–75:
```html
<template x-if="t.sanitization.quest_close && t.sanitization.quest_close.length">
    <div class="tv-compaction-san-row">Quests closed: <span x-text="t.sanitization.quest_close.length"></span></div>
</template>
```

**Why:** `CompactorSanitizationResult` no longer has `quest_close` (it was removed from the model). This display is dead code.

#### Step 1.6 — Remove quests from state defaults and migration

**File:** `ccya/state/io.py`

**What:** Remove:
- Line 60: `"quests": [],` from `_default_state()`
- Lines 111–114: Quest migration code (`for q in state.get("quests") or []: ...`)

**Why:** `quests` is never populated by the engine. The state key is dead code.

### Tests to update
All test files that include `"quests": []` in mock state dicts should have that key removed. Affected files:
- `tests/test_eval.py` (lines 208, 232, 537)
- `tests/test_compactor.py` (lines 353, 584, 862, 898)
- `tests/test_engine_pipeline.py` (line 112)
- `tests/test_prompt_audit.py` (lines 51, 120)
- `tests/test_pack_loader.py` (lines 64, 110, 600)
- `tests/test_engine_smoke.py` (lines 118, 1512, 1541)
- `tests/test_turn.py` (line 58)
- `tests/test_narrate.py` (line 44)
- `tests/test_extraction_integration.py` (line 23)
- `tests/test_prompts.py` (line 28)
- `tests/test_names.py` (line 163)
- `tests/test_delta_present_npcs_sticky.py` (line 13)
- `tests/test_condition_and_pressure_coexist.py` (line 17)
- `tests/test_delta_inventory_overdraw.py` (line 15)
- `tests/test_delta_inventory_merge.py` (line 13)
- `tests/test_changes.py` (lines 12, 22)
- `tests/test_condition_ttl.py` (line 13)
- `tests/test_extraction_npc.py` (line 13)
- `tests/test_turn_validate.py` (lines 22, 59)
- `tests/test_char_creation.py` (lines 168, 352, 434)

All test files that include `"quest_updates": []` in mock ProgressExtractResult should have that key removed:
- `tests/test_extraction.py` (line 128)
- `tests/test_engine_pipeline.py` (lines 234, 240, 403)
- `tests/test_turn.py` (lines 77, 150, 233, 322, 435)

All test files that reference `quest_close` in mock sanitization should have that key removed:
- `tests/test_eval.py` (line 1144)
- `tests/test_turn_viewer.py` (line 565)

### REPOMAP updates required
- `docs/REPOMAP/frontend.md`: Remove quest-related entries from template descriptions
- `docs/REPOMAP/state.md`: Remove `quests` from state shape documentation

### Risks
1. **Existing saves with `quests` key**: `yaml.safe_load` will load them fine (extra keys are ignored). The engine never reads `state.quests` for anything meaningful, so existing saves are unaffected.
2. **CSS scroll behavior**: The `.sidebar-card[data-card="quests"]` selectors also affect scroll behavior. Removing them means the new Arc card needs its own scroll styling (handled in Step 2.2).

## Implementation — Phase 2: Add Arc UI

### Context files to load
1. `ccya/templates/_state_left.html`
2. `ccya/static/app.src.css`
3. `ccya/templates/index.html`

### Detailed steps

#### Step 2.1 — Add Arc card to _state_left.html

**File:** `ccya/templates/_state_left.html`

**What:** Replace the deleted Quests card (previously lines 99–173) with an Arc card. The card goes between Location and Compendium.

```html
{% set _arc = state.get('arc') %}
{% if _arc %}
<details class="sidebar-card" id="card-arc" data-card="arc" open>
    <summary>Arc</summary>
    <div class="sidebar-card-body arc-card-body">
        {% set _phase = _arc.get('phase', 'setup') %}
        {% set _goal = _arc.get('visible_goal', '') %}
        {% set _engagement = _arc.get('arc_engagement', 0) %}
        {% set _active = _arc.get('active_threads', []) %}
        {% set _latent = _arc.get('latent_threads', []) %}
        {% set _hidden = _arc.get('hidden_truths', []) %}
        {% set _completed = _arc.get('completed_threads', []) %}

        {% if _goal %}
        <div class="arc-goal">
            <span class="arc-phase-badge {{ _phase }}">{{ _phase | upper }}</span>
            <span class="arc-goal-text" data-md>{{ _goal }}</span>
        </div>
        {% endif %}

        {% if _active %}
        <div class="arc-section">
            <div class="arc-section-label">Active</div>
            {% for thread in _active %}
            {% set _tstate = thread.get('state', 'active') %}
            <div class="arc-thread{% if _tstate != 'active' %} arc-thread-{{ _tstate }}{% endif %}">
                <span class="arc-thread-summary" data-md>{{ thread.get('summary', '') }}</span>
                <span class="arc-thread-meta">
                    {% if thread.get('urgency') and thread.urgency != 'normal' %}
                    <span class="arc-urgency arc-urgency-{{ thread.urgency }}">{{ thread.urgency | upper }}</span>
                    {% endif %}
                    {% if thread.get('progress', 0) > 0 %}
                    <span class="arc-progress">{{ thread.progress }}</span>
                    {% endif %}
                </span>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if _latent %}
        <details class="arc-latent-section">
            <summary class="arc-latent-summary">
                <span class="arc-section-label">Unknown</span>
                <span class="arc-latent-count">{{ _latent | length }}</span>
            </summary>
            <div class="arc-latent-list">
                {% for thread in _latent %}
                <div class="arc-thread arc-thread-latent">
                    <span class="arc-thread-teaser">???</span>
                    <span class="arc-thread-tags">
                        {% for tag in (thread.get('tags') or [])[:3] %}
                        <span class="arc-tag">{{ tag }}</span>{% if not loop.last %}, {% endif %}
                        {% endfor %}
                    </span>
                </div>
                {% endfor %}
            </div>
        </details>
        {% endif %}

        {% if _hidden %}
        <div class="arc-section">
            <div class="arc-section-label">Discovered</div>
            {% for truth in _hidden %}
            <div class="arc-truth">
                <span class="arc-truth-icon">◈</span>
                <span class="arc-truth-text" data-md>{{ truth }}</span>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {% if _completed %}
        <details class="arc-completed-section">
            <summary class="arc-completed-summary">
                <span class="arc-section-label">Completed</span>
                <span class="arc-completed-count">{{ _completed | length }}</span>
            </summary>
            <div class="arc-completed-list">
                {% for thread in _completed %}
                <div class="arc-thread arc-thread-complete">
                    <span class="arc-thread-summary" data-md>{{ thread.get('summary', '') }}</span>
                </div>
                {% endfor %}
            </div>
        </details>
        {% endif %}

        {% if _engagement != 0 %}
        <div class="arc-engagement">
            <span class="arc-engagement-label">Engagement</span>
            <span class="arc-engagement-bar">
                {% for i in range(-3, 4) %}
                <span class="arc-engagement-pip{% if i <= _engagement %} arc-engagement-pip-active{% endif %}"></span>
                {% endfor %}
            </span>
        </div>
        {% endif %}
    </div>
</details>
{% endif %}
```

**Why:** This gives the player:
- **Phase banner** — where they are in the campaign (SETUP/PURSUIT/REVERSAL/CRISIS/RESOLUTION)
- **Visible goal** — the campaign objective
- **Active threads** — what they're currently pursuing (with urgency and progress)
- **Latent teasers** — "Unknown" section showing count and tags but not summaries (creates anticipation)
- **Discovered truths** — hidden truths revealed through play
- **Completed threads** — collapsed by default, shows what's been accomplished
- **Engagement bar** — visual feedback on how aligned the player is with the arc

#### Step 2.2 — Add Arc CSS to app.src.css

**File:** `ccya/static/app.src.css`

**What:** Add after the existing sidebar card body scroll selectors (around line 544), add:
- `.sidebar-card[data-card="arc"] > .sidebar-card-body` to scrollable card body selector (same as quests was)

Then add a new section after the QUESTS section (after line 1193):

```css
/* =========================================================
   SIDEBAR — ARC
   ========================================================= */

.arc-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.arc-goal {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}

.arc-phase-badge {
  flex-shrink: 0;
  font-size: 9px;
  font-family: var(--font-mono);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 2px 5px;
  border-radius: 3px;
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid var(--accent);
  opacity: 0.85;
}

.arc-phase-badge.setup {
  background: var(--bg-elevated);
  color: var(--text-muted);
  border-color: var(--border-subtle);
}

.arc-phase-badge.pursuit {
  background: var(--accent-soft);
  color: var(--accent);
  border-color: var(--accent);
}

.arc-phase-badge.reversal {
  background: var(--accent-warning-soft);
  color: var(--accent-warning);
  border-color: var(--accent-warning);
}

.arc-phase-badge.crisis {
  background: var(--accent-error-soft);
  color: var(--accent-error);
  border-color: var(--accent-error);
}

.arc-phase-badge.resolution {
  background: var(--accent-success-soft);
  color: var(--accent-success);
  border-color: var(--accent-success);
}

.arc-goal-text {
  font-size: 12px;
  color: var(--text-primary);
  line-height: 1.4;
}

.arc-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.arc-section-label {
  font-size: 10px;
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 600;
}

.arc-thread {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 4px 0;
  font-size: 12px;
  line-height: 1.4;
}

.arc-thread-summary {
  flex: 1;
  color: var(--text-secondary);
}

.arc-thread-latent .arc-thread-summary {
  color: var(--text-muted);
  font-style: italic;
}

.arc-thread-complete .arc-thread-summary {
  color: var(--text-muted);
  text-decoration: line-through;
  opacity: 0.7;
}

.arc-thread-meta {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.arc-urgency {
  font-size: 9px;
  font-family: var(--font-mono);
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 4px;
  border-radius: 2px;
}

.arc-urgency.immediate {
  background: var(--accent-error-soft);
  color: var(--accent-error);
}

.arc-urgency.building {
  background: var(--accent-warning-soft);
  color: var(--accent-warning);
}

.arc-progress {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.arc-latent-section {
  border: none;
  padding: 0;
  margin: 0;
}

.arc-latent-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 2px 0;
  list-style: none;
  font-size: 12px;
}

.arc-latent-summary::-webkit-details-marker {
  display: none;
}

.arc-latent-count {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  background: var(--bg-elevated);
  padding: 1px 5px;
  border-radius: 3px;
  border: 1px solid var(--border-subtle);
}

.arc-latent-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 0;
}

.arc-thread-teaser {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  opacity: 0.5;
}

.arc-tag {
  font-size: 9px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  background: var(--bg-base);
  padding: 1px 4px;
  border-radius: 2px;
  border: 1px solid var(--border-subtle);
}

.arc-truth {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 4px 0;
  font-size: 12px;
}

.arc-truth-icon {
  flex-shrink: 0;
  color: var(--accent);
  font-size: 10px;
}

.arc-truth-text {
  color: var(--text-secondary);
  line-height: 1.4;
}

.arc-completed-section {
  border: none;
  padding: 0;
  margin: 0;
}

.arc-completed-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 2px 0;
  list-style: none;
  font-size: 12px;
}

.arc-completed-summary::-webkit-details-marker {
  display: none;
}

.arc-completed-count {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.arc-completed-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 0;
}

.arc-engagement {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.arc-engagement-label {
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.arc-engagement-bar {
  display: flex;
  gap: 2px;
}

.arc-engagement-pip {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  background: var(--border-subtle);
}

.arc-engagement-pip-active {
  background: var(--accent);
}
```

#### Step 2.3 — Wire arc_hints in char creation JS

**File:** `ccya/templates/index.html`

**What:** In the `charCreation()` Alpine component:
- Add `arc_hints: ''` to the data object (replacing `quest_hints: ''`)
- In the form submission handler, read `#cc-arc-hints` and append as `arc_hints` to the form (replacing the dead `quest_hints` code)

**Why:** The char creation form needs to actually send `arc_hints` to the server so it flows into `PlayerOverrides` and then into the seed generation prompt.

### Tests to write or update
- No new tests needed for UI changes (frontend is tested via smoke tests)
- Update existing smoke tests that reference `quests` in state (remove the key)
- Update existing smoke tests that reference `quest_updates` in ProgressExtractResult (remove the key)

### REPOMAP updates required
- `docs/REPOMAP/frontend.md`: Update `_state_left.html` description to mention Arc card instead of Quests card
- `docs/REPOMAP/state.md`: Remove `quests` from state shape documentation

### Risks
1. **Arc card visibility**: The card only renders when `state.arc` exists. For saves created before this plan (without arc), the card won't appear. This is acceptable — those saves are legacy.
2. **CSS variable dependencies**: The arc CSS uses existing variables (`--accent`, `--accent-soft`, `--accent-error`, etc.). If any are missing, the arc card will fall back to defaults.

## Ambiguities requiring resolution before execution
1. **Should the Arc card show `thematic_question`?** Currently not included in the UI design. It could be shown as a tooltip on the phase badge or as a subtle subtitle. Decision: omit for now — it's narrator context, not player-facing.
2. **Should latent thread teasers show more than tags?** Currently shows "???" + tags. Could also show the first few words of the summary (truncated). Decision: "???" + tags is sufficient — more would spoil the mystery.
3. **Should the engagement bar show direction (positive/negative)?** Currently all active pips are the same color. Decision: keep it simple — just show magnitude, not direction.
