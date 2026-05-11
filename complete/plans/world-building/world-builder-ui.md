***

# World Builder UI — New Game Flow with Custom World Generation

## Status
`completed`

## Part of
standalone

## Dependencies
- `world-rules.md` must be **completed first**. This plan depends on `ScenarioBrief.world_rules` existing as a validated field and on the `generate_pack_system.j2` instruction producing it. The world builder UI submits a `world_rules` block as part of pack generation; if the model field does not exist the server will reject the submission.

## Objective
Players currently have no way to create a custom world from the browser. The only path into a game is selecting a pre-authored pack. This plan adds a full in-browser world-builder flow triggered by a "Create Your Own" option in the existing pack-picker modal. The flow is: pack picker → world builder dialogue (multi-step form that collects enough detail to generate a `ScenarioBrief` via the pack-gen LLM) → existing character creator → begin game. The world builder runs pack generation in-process on the server behind a streaming SSE progress endpoint, then boots a new game with the result. No new pages, no new Python modules — the flow lives inside the existing modal and wires to a new `/new-game/generate-pack` endpoint.

## Non-goals
- No saving or exporting of generated packs to disk as permanent user-authored packs.
- No editing or re-prompting of the generated `ScenarioBrief` after generation — it is used as-is.
- No changes to the existing pre-authored pack cards or the pack-picker layout for those cards.
- No changes to the existing character creation form (`_char_creation.html`).
- No changes to the turn engine, extraction, or narration pipeline.
- No authentication, user accounts, or per-user pack storage.
- No mobile-specific layout work beyond not breaking existing responsive behavior.
- No admin UI for managing generated packs.

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/templates/_pack_picker.html` | modify | Add "Create Your Own" card at the bottom of the pack list |
| `ccya/templates/_world_builder.html` | create | New multi-step world builder form template (steps: concept → tone/genre → world rules → factions → review) |
| `ccya/templates/index.html` | modify | Add world builder step to `openPackPicker()` modal step machine; add `startWorldBuilder()` method; add `startNewGameFromGenerated()` method; add SSE progress wiring for pack generation |
| `ccya/server/routes.py` | modify | Add `POST /new-game/generate-pack` SSE endpoint; add `GET /panels/world-builder` panel endpoint |
| `ccya/engine/generate_pack.py` | create | New module: `generate_pack_from_brief(inputs) -> AsyncIterator[str]` — wraps pack-gen LLM call, parses `ScenarioBrief`, writes ephemeral pack to `packs/generated/`, returns SSE events including `pack_ready` with pack ID |
| `ccya/static/app.css` | modify | Add styles for `.world-builder-*`, `.wbstep-*`, `.pack-generate-progress` classes |
| `docs/REPOMAP/server.md` | modify | Document new `/new-game/generate-pack` and `/panels/world-builder` endpoints |
| `docs/REPOMAP/engine.md` | modify | Document new `generate_pack.py` module and `generate_pack_from_brief` function |
| `docs/plans/TODO.md` | modify | Add this plan entry |

## Firm decisions

1. **The world builder lives entirely inside the existing pack-picker modal.** No new page, no new `<dialog>` element. The modal's step machine (`_modalStep`) gains two new steps: `'worldbuilder'` and `'worldbuilder-generating'`. This reuses the existing modal frame, close button, title bar, and ESC key handler without duplication.
2. **World builder is a 4-step form, not a single freeform textarea.** The four steps are: (1) Concept — one-sentence world summary and optional name; (2) Tone/Genre — checkbox grid of genre tags and mood words; (3) World Rules — three text inputs, pre-labeled, for physical laws (this directly maps to `world_rules` from the preceding plan); (4) Review — a read-back of all inputs with a "Generate World" button. Each step is shown/hidden via Alpine.js `x-show` on a single injected subtree. No server round-trips between steps.
3. **Pack generation is async SSE behind `POST /new-game/generate-pack`.** The endpoint accepts the world builder form data, calls `generate_pack_from_brief()`, and streams `phase` and `pack_ready` events. The client modal shows a progress screen during generation — identical pattern to the turn progress strip. On `pack_ready` the client automatically advances to the character creation step using the generated `pack_id`.
4. **Generated packs are written to `packs/generated/<uuid>/`.** They are ephemeral — not listed in the standard pack picker, not committed. The generated directory is gitignored. `load_pack()` already accepts any path so no changes to the pack loader are needed. The generated pack contains only `scenario.yaml` and a minimal `manifest.yaml`; it does not contain `seed/` (seed generation happens at `/new-game` time as usual).
5. **`generate_pack.py` is a new engine module, not inlined in routes.** Per AGENTS.md module boundary rules — heavy LLM logic does not live in route handlers. The route calls `generate_pack_from_brief()` and streams its output.
6. **No new config key for enabling/disabling the world builder.** The "Create Your Own" card is always visible. If pack generation fails (LLM unreachable, parse error), the SSE stream emits a `generation_error` event and the client returns the user to the concept step with an inline error message.
7. **World builder `world_rules` inputs are optional per field.** If the user leaves a rule blank it is omitted from the submitted list. The review step shows only non-empty rules. The LLM will fill in what it can from the concept if rules are sparse.
8. **The generated pack's `manifest.yaml` mode is always `dynamic`.** Custom worlds are by definition dynamically seeded.

***

## Implementation — Phase 1: World Builder Form Template and CSS

### Context files to load
```
ccya/templates/_pack_picker.html
ccya/templates/_char_creation.html
ccya/static/app.css
```

### Overview
Create the new `_world_builder.html` template containing the 4-step Alpine.js form. Add the "Create Your Own" entry to `_pack_picker.html`. Add all necessary CSS classes to `app.css`. No JavaScript or server changes in this phase — the template is inert until wired in Phase 2.

### Detailed steps

#### Step 1.1 — Add "Create Your Own" card to `_pack_picker.html`

**File:** `ccya/templates/_pack_picker.html`

**What:** Append a visually distinct "Create Your Own" button card after the `{% else %}` / `{% endfor %}` block. Give it `data-pack-id="__create__"` so the existing click handler in `openPackPicker()` can detect it by the sentinel value and branch to the world builder instead of proceeding to character creation.

**Why:** The existing `onCardClick` handler already listens for `[data-pack-id]` clicks. A sentinel ID (`__create__`) lets us intercept this one card without altering the handler's logic for all other cards. The card must be visually distinct (dashed border, different icon) so it reads as "generative" rather than a pre-authored option.

**Code Snippet**

```html
{# Existing pack loop above this line — do not modify #}

<button type="button"
        class="pack-card pack-card--create"
        data-pack-id="__create__">
    <div class="pack-card-header">
        <span class="pack-card-name">✦ Create Your Own</span>
        <span class="pack-card-mode pack-card-mode--dynamic">dynamic</span>
    </div>
    <p class="pack-card-desc">Describe a world and let the engine build it for you. Takes about 30–60 seconds.</p>
    <div class="pack-card-tags">
        <span class="pack-card-tag">custom</span>
        <span class="pack-card-tag">generated</span>
    </div>
</button>
```

**Validation:** Load `/panels/pack-picker` in a browser and confirm the new card appears at the bottom of the list with the `pack-card--create` class applied and `data-pack-id="__create__"` on the element.

***

#### Step 1.2 — Create `_world_builder.html`

**File:** `ccya/templates/_world_builder.html`

**What:** A Jinja2/Alpine.js template for the 4-step world builder form. The root element is `<div x-data="worldBuilder()" ...>`. Steps are shown/hidden with `x-show`. Step navigation uses `currentStep` (integer 1–4). The form does not submit — data collection only; actual submission is triggered by the JS layer in Phase 2.

**Why:** Keeping this as a server-rendered partial (fetched via `/panels/world-builder`) follows the same pattern as `_char_creation.html` and `_pack_picker.html`. The server renders it and the client injects it into `#pack-picker-body`. Alpine.js `initTree()` is called after injection just as it is for char creation.

**Code Snippet**

```html
{# _world_builder.html — injected into #pack-picker-body #}
<div x-data="worldBuilder()" class="world-builder">

    {# ── Step 1: Concept ──────────────────────────────── #}
    <div class="wbstep" x-show="currentStep === 1">
        <p class="wbstep-hint">Describe your world in one or two sentences. This is the seed for everything.</p>

        <label class="wbfield-label" for="wb-concept">World concept <span class="wbfield-required">*</span></label>
        <textarea id="wb-concept"
                  class="wbfield-textarea"
                  x-model="concept"
                  placeholder="e.g. A city-state floating on a dead god's back, slowly dissolving into the ocean below."
                  rows="3"
                  maxlength="400"></textarea>
        <span class="wbfield-counter" x-text="concept.length + ' / 400'"></span>

        <label class="wbfield-label" for="wb-name">World name <span class="wbfield-optional">(optional)</span></label>
        <input id="wb-name"
               type="text"
               class="wbfield-input"
               x-model="worldName"
               placeholder="Leave blank to let the engine choose"
               maxlength="60">
    </div>

    {# ── Step 2: Tone and Genre ────────────────────────── #}
    <div class="wbstep" x-show="currentStep === 2">
        <p class="wbstep-hint">Select up to 4 tags that define the feel of your world. These become <code>tone_tags</code> on the generated pack.</p>

        <div class="wbtag-grid">
            <template x-for="tag in availableTags" :key="tag">
                <button type="button"
                        class="wbtag"
                        :class="{ 'wbtag--selected': selectedTags.includes(tag) }"
                        @click="toggleTag(tag)"
                        :disabled="!selectedTags.includes(tag) && selectedTags.length >= 4"
                        x-text="tag">
                </button>
            </template>
        </div>

        <label class="wbfield-label" for="wb-mood">Additional mood note <span class="wbfield-optional">(optional)</span></label>
        <input id="wb-mood"
               type="text"
               class="wbfield-input"
               x-model="moodNote"
               placeholder="e.g. melancholy, sun-bleached, claustrophobic"
               maxlength="120">
    </div>

    {# ── Step 3: World Rules ───────────────────────────── #}
    <div class="wbstep" x-show="currentStep === 3">
        <p class="wbstep-hint">Define up to 3 physical laws of this world — hard constraints on what is possible here. Leave blank to let the engine decide.</p>

        <template x-for="(rule, idx) in worldRules" :key="idx">
            <div class="wbrule-row">
                <label class="wbfield-label" :for="'wb-rule-' + idx" x-text="'Law ' + (idx + 1)"></label>
                <input :id="'wb-rule-' + idx"
                       type="text"
                       class="wbfield-input"
                       x-model="worldRules[idx]"
                       placeholder="e.g. The dead do not stay dead — they animate within hours unless burned."
                       maxlength="200">
            </div>
        </template>
    </div>

    {# ── Step 4: Review ────────────────────────────────── #}
    <div class="wbstep" x-show="currentStep === 4">
        <p class="wbstep-hint">Review your world before generating.</p>

        <dl class="wbreview-list">
            <dt>Concept</dt>
            <dd x-text="concept || '—'"></dd>

            <template x-if="worldName">
                <dt>Name</dt>
            </template>
            <template x-if="worldName">
                <dd x-text="worldName"></dd>
            </template>

            <dt>Tone</dt>
            <dd x-text="selectedTags.length ? selectedTags.join(', ') : '(none selected)'"></dd>

            <template x-if="nonEmptyRules.length">
                <dt>World laws</dt>
            </template>
            <template x-if="nonEmptyRules.length">
                <dd>
                    <ul class="wbreview-rules">
                        <template x-for="r in nonEmptyRules" :key="r">
                            <li x-text="r"></li>
                        </template>
                    </ul>
                </dd>
            </template>
        </dl>

        <p class="wbfield-hint" x-show="nonEmptyRules.length === 0">No world laws specified — the engine will invent them.</p>
    </div>

    {# ── Navigation bar ────────────────────────────────── #}
    <div class="wbnav">
        <button type="button"
                class="char-creation-btn--back"
                @click="back()"
                x-text="currentStep === 1 ? '← Worlds' : '← Back'">
        </button>

        <span class="wbstep-indicator" x-text="currentStep + ' / 4'"></span>

        <button type="button"
                class="char-creation-btn--confirm wb-next-btn"
                x-show="currentStep < 4"
                @click="next()"
                :disabled="currentStep === 1 && concept.trim().length < 10"
                x-text="'Next →'">
        </button>

        <button type="button"
                class="char-creation-btn--confirm wb-generate-btn"
                x-show="currentStep === 4"
                @click="$dispatch('wb-generate')">
            ✦ Generate World
        </button>
    </div>

</div>
```

**Validation:** Fetch `/panels/world-builder` after the route is wired (Phase 3 Step 3.1). Confirm the HTML is returned with no Jinja2 errors. Confirm Alpine.js `worldBuilder()` component mounts without console errors after `Alpine.initTree()`.

***

#### Step 1.3 — Add CSS to `app.css`

**File:** `ccya/static/app.css`

**What:** Append a new CSS block at the end of the file containing all `.world-builder-*`, `.wbstep-*`, `.wbtag-*`, `.wbrule-*`, `.wbreview-*`, `.wbnav`, and `.pack-card--create` styles. No changes to existing rules.

**Why:** AGENTS.md requires no dead CSS — every rule added must be used. All classes added here are used by `_world_builder.html` (Phase 1 Step 1.2) and `_pack_picker.html` (Phase 1 Step 1.1).

**Code Snippet**

```css
/* ── World Builder ─────────────────────────────────────── */

.pack-card--create {
    border: 1.5px dashed var(--border-subtle, oklch(from var(--text-primary, #ccc) l c h / 0.25));
    opacity: 0.85;
    margin-top: var(--space-3, 12px);
}
.pack-card--create:hover {
    opacity: 1;
    border-color: var(--accent-primary, #4f98a3);
}

.world-builder {
    display: flex;
    flex-direction: column;
    gap: 0;
    min-height: 260px;
}

.wbstep {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding-bottom: 8px;
}

.wbstep-hint {
    font-size: 13px;
    color: var(--text-muted, #797876);
    margin: 0 0 4px;
    line-height: 1.5;
}

.wbfield-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary, #cdccca);
    margin-bottom: 2px;
    display: block;
}

.wbfield-required {
    color: var(--accent-error, #dd6974);
    margin-left: 2px;
}

.wbfield-optional {
    font-weight: 400;
    color: var(--text-muted, #797876);
    font-size: 12px;
}

.wbfield-input,
.wbfield-textarea {
    width: 100%;
    background: var(--surface-2, #1c1b19);
    border: 1px solid var(--border, #393836);
    border-radius: 6px;
    color: var(--text-primary, #cdccca);
    font-size: 13px;
    padding: 8px 10px;
    line-height: 1.5;
    resize: vertical;
    transition: border-color 160ms ease;
}

.wbfield-input:focus,
.wbfield-textarea:focus {
    outline: none;
    border-color: var(--accent-primary, #4f98a3);
}

.wbfield-counter {
    font-size: 11px;
    color: var(--text-muted, #797876);
    text-align: right;
    margin-top: -8px;
}

.wbfield-hint {
    font-size: 12px;
    color: var(--text-muted, #797876);
    font-style: italic;
    margin: 4px 0 0;
}

.wbtag-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.wbtag {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 99px;
    border: 1px solid var(--border, #393836);
    background: transparent;
    color: var(--text-muted, #797876);
    cursor: pointer;
    transition: background 160ms, color 160ms, border-color 160ms;
}

.wbtag:hover:not(:disabled) {
    border-color: var(--accent-primary, #4f98a3);
    color: var(--text-primary, #cdccca);
}

.wbtag--selected {
    background: var(--accent-primary, #4f98a3);
    border-color: var(--accent-primary, #4f98a3);
    color: #fff;
}

.wbtag:disabled:not(.wbtag--selected) {
    opacity: 0.35;
    cursor: not-allowed;
}

.wbrule-row {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.wbreview-list {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 6px 16px;
    font-size: 13px;
}

.wbreview-list dt {
    color: var(--text-muted, #797876);
    font-weight: 600;
    padding-top: 2px;
}

.wbreview-list dd {
    color: var(--text-primary, #cdccca);
    margin: 0;
}

.wbreview-rules {
    margin: 0;
    padding-left: 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    color: var(--text-primary, #cdccca);
    font-size: 13px;
}

.wbnav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 20px;
    padding-top: 12px;
    border-top: 1px solid var(--border-subtle, oklch(from var(--text-primary, #ccc) l c h / 0.1));
}

.wbstep-indicator {
    font-size: 12px;
    color: var(--text-muted, #797876);
}

/* Pack generation progress — appears in modal body during LLM call */
.pack-generate-progress {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    min-height: 200px;
    text-align: center;
}

.pack-generate-progress__spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border, #393836);
    border-top-color: var(--accent-primary, #4f98a3);
    border-radius: 50%;
    animation: pgSpin 0.8s linear infinite;
}

@keyframes pgSpin {
    to { transform: rotate(360deg); }
}

.pack-generate-progress__label {
    font-size: 14px;
    color: var(--text-primary, #cdccca);
}

.pack-generate-progress__sublabel {
    font-size: 12px;
    color: var(--text-muted, #797876);
}

.pack-generate-progress__error {
    font-size: 13px;
    color: var(--accent-error, #dd6974);
    max-width: 340px;
}
```

**Validation:** Lint `app.css` (or run `make check` if that includes a CSS linter). Visually verify pack picker modal still looks correct before and after the new card — no layout regressions.

***

### Tests to write or update

No unit tests for CSS or HTML templates per AGENTS.md (template tests live at integration level). Validation is visual at step completion.

### REPOMAP updates required

None in Phase 1 — no new Python modules.

### Risks

1. **CSS variable name mismatches.** The existing `app.css` may use different custom property names than the ones used in the snippet above (`--border-subtle`, `--text-primary`, etc.). The executor must grep the existing `app.css` for the actual variable names and align all new rules before committing.
2. **Alpine.js `x-show` vs `x-if` on step containers.** `x-show` keeps all step DOM in place (simpler, no re-init cost) but adds hidden-element cost. For 4 small steps this is acceptable. If the executor sees layout issues caused by hidden steps affecting flex sizing, wrap each `wbstep` in `position: absolute; width: 100%` inside a `position: relative` parent.

***

## Implementation — Phase 2: Alpine.js `worldBuilder()` Component

### Context files to load
```
ccya/templates/index.html   (charCreation() and openPackPicker() functions)
ccya/templates/_world_builder.html   (created in Phase 1)
```

### Overview
Add the `worldBuilder()` Alpine.js component function to `index.html`. Extend `openPackPicker()` to detect `data-pack-id="__create__"` and advance to the world builder step. Add `startWorldBuilder()` which fires the SSE generation request. Add `startNewGameFromGenerated(packId)` which — after pack generation completes — advances the modal to the existing char creation step with the generated pack ID.

### Detailed steps

#### Step 2.1 — Add `worldBuilder()` component function to `index.html`

**File:** `ccya/templates/index.html`

**What:** Insert the `worldBuilder()` function immediately after the closing `}` of the `charCreation()` function (before the `game()` function). This follows the existing code organization pattern.

**Why:** All Alpine.js component factories live in `index.html`'s inline `<script>` block. Adding `worldBuilder()` here is consistent with `charCreation()` and avoids a separate JS file load.

**Code Snippet**

```javascript
function worldBuilder() {
    return {
        currentStep: 1,
        concept: '',
        worldName: '',
        selectedTags: [],
        moodNote: '',
        worldRules: ['', '', ''],

        availableTags: [
            'dark fantasy', 'science fiction', 'post-apocalyptic', 'cyberpunk',
            'horror', 'noir', 'mystery', 'survival', 'political intrigue',
            'solarpunk', 'weird west', 'cosmic horror', 'biopunk', 'mythic',
            'military', 'heist', 'espionage', 'slice of life', 'isekai',
        ],

        get nonEmptyRules() {
            return this.worldRules.filter(r => r.trim().length > 0);
        },

        toggleTag(tag) {
            const idx = this.selectedTags.indexOf(tag);
            if (idx >= 0) {
                this.selectedTags.splice(idx, 1);
            } else if (this.selectedTags.length < 4) {
                this.selectedTags.push(tag);
            }
        },

        next() {
            if (this.currentStep < 4) this.currentStep++;
        },

        back() {
            if (this.currentStep > 1) {
                this.currentStep--;
            } else {
                // Signal the modal to go back to pack picker
                this.$dispatch('wb-back-to-packs');
            }
        },

        serialize() {
            return {
                concept: this.concept.trim(),
                world_name: this.worldName.trim(),
                tone_tags: this.selectedTags,
                mood_note: this.moodNote.trim(),
                world_rules: this.nonEmptyRules,
            };
        },
    };
}
```

**Validation:** Open browser console. After `Alpine.initTree()` is called on a `_world_builder.html`-injected subtree, `document.querySelector('.world-builder').__x.$data.currentStep` should equal `1`.

***

#### Step 2.2 — Extend `openPackPicker()` to handle `__create__` and world builder steps

**File:** `ccya/templates/index.html`

**What:** Inside the existing `onCardClick` listener in `openPackPicker()`, add a branch at the top: if `card.dataset.packId === '__create__'`, advance to the world builder step instead of char creation. Also add event listeners inside the world builder step for `wb-generate` (fires `startWorldBuilder()`) and `wb-back-to-packs` (returns to pack list). Also extend the back button logic in the world builder step to re-show the pack picker HTML.

**Why:** The existing `onCardClick` already handles the pack → char-creation transition. The world builder intercepts at the same click point with a sentinel value check, keeping all modal step logic colocated.

**Code Snippet**

Find the existing `body.addEventListener('click', function onCardClick(e) {` block inside `openPackPicker()`. Replace just its interior `if (!card) return;` continuation with:

```javascript
body.addEventListener('click', function onCardClick(e) {
    const card = e.target.closest('[data-pack-id]');
    if (!card) return;
    body.removeEventListener('click', onCardClick);

    // ── "Create Your Own" branch ──
    if (card.dataset.packId === '__create__') {
        self._modalStep = 'worldbuilder';
        document.getElementById('pack-picker-title').textContent = 'Build Your World';
        body.innerHTML = '<p class="empty-state">Loading world builder…</p>';
        fetch('/panels/world-builder')
            .then(r => r.text())
            .then(wbHtml => {
                body.innerHTML = wbHtml;
                if (window.Alpine) Alpine.initTree(body);

                // wb-generate: user clicked "Generate World" on step 4
                body.addEventListener('wb-generate', function onGenerate() {
                    body.removeEventListener('wb-generate', onGenerate);
                    const wbComp = body.querySelector('.world-builder');
                    const wbData = wbComp && wbComp.__x ? wbComp.__x.$data : null;
                    if (!wbData) return;
                    self.startWorldBuilder(wbData.serialize(), close, html);
                });

                // wb-back-to-packs: user hit back on step 1
                body.addEventListener('wb-back-to-packs', function onBackToPacks() {
                    body.removeEventListener('wb-back-to-packs', onBackToPacks);
                    self._modalStep = 'pack';
                    document.getElementById('pack-picker-title').textContent = 'Choose a World';
                    body.innerHTML = html;
                    if (window.Alpine) Alpine.initTree(body);
                    body.addEventListener('click', onCardClick);
                });
            })
            .catch(() => { body.innerHTML = '<p class="empty-state">Failed to load world builder.</p>'; });
        return;
    }

    // ── Existing: pre-authored pack selected ──
    if (!self.characterCreationEnabled) {
        close();
        self.startNewGame(card.dataset.packId);
        return;
    }
    self._selectedPackId = card.dataset.packId;
    self._modalStep = 'character';
    document.getElementById('pack-picker-title').textContent = 'Create Your Character';
    body.innerHTML = '<p class="empty-state">Loading character creation…</p>';
    fetch('/panels/char-creation')
        .then(r => r.text())
        .then(charHtml => {
            body.innerHTML = charHtml;
            if (window.Alpine) Alpine.initTree(body);
            const confirmBtn = body.querySelector('.char-creation-btn--confirm');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', function onConfirm(e) {
                    if (confirmBtn.disabled) return;
                    e.preventDefault();
                    close();
                    self.startNewGameWithCharCreation();
                });
            }
            const backBtn = body.querySelector('.char-creation-btn--back');
            if (backBtn) {
                backBtn.addEventListener('click', function onBack(e) {
                    e.preventDefault();
                    self._modalStep = 'pack';
                    document.getElementById('pack-picker-title').textContent = 'Choose a World';
                    body.innerHTML = html;
                    if (window.Alpine) Alpine.initTree(body);
                    body.addEventListener('click', onCardClick);
                });
            }
        })
        .catch(() => { body.innerHTML = '<p class="empty-state">Failed to load character creation.</p>'; });
});
```

**Validation:** Click "Create Your Own" in pack picker — modal title should change to "Build Your World" and world builder steps should render. Step navigation (Next/Back) should work. Back on step 1 should return to pack picker with all cards.

***

#### Step 2.3 — Add `startWorldBuilder()` and `startNewGameFromGenerated()` to `game()`

**File:** `ccya/templates/index.html`

**What:** Add two new methods to the `game()` function object, after `startNewGameWithCharCreation()`.

**Why:** `startWorldBuilder()` fires the SSE generation request and manages the modal's progress state. `startNewGameFromGenerated()` is called when generation succeeds — it stores the generated `pack_id` and immediately advances the modal to the character creation step. Both methods follow the same fetch/SSE pattern as the existing turn submission code.

**Code Snippet**

```javascript
async startWorldBuilder(worldData, closeModal, packPickerHtml) {
    const body = document.getElementById('pack-picker-body');
    document.getElementById('pack-picker-title').textContent = 'Generating World…';
    body.innerHTML = `
        <div class="pack-generate-progress" id="pack-gen-progress">
            <div class="pack-generate-progress__spinner"></div>
            <div class="pack-generate-progress__label">Building your world…</div>
            <div class="pack-generate-progress__sublabel">This takes 30–60 seconds.</div>
        </div>`;

    const self = this;
    const progressEl = body.querySelector('.pack-generate-progress__label');
    const sublabelEl = body.querySelector('.pack-generate-progress__sublabel');

    const formData = new FormData();
    formData.append('concept', worldData.concept);
    formData.append('world_name', worldData.world_name || '');
    formData.append('tone_tags', JSON.stringify(worldData.tone_tags));
    formData.append('mood_note', worldData.mood_note || '');
    formData.append('world_rules', JSON.stringify(worldData.world_rules));

    try {
        const resp = await fetch('/new-game/generate-pack', {
            method: 'POST',
            body: formData,
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        if (!resp.body) throw new Error('No response body');

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buf = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });

            const lines = buf.split('\n');
            buf = lines.pop(); // keep incomplete last line

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                let evt;
                try { evt = JSON.parse(line.slice(6)); } catch { continue; }

                if (evt.type === 'phase') {
                    if (progressEl) progressEl.textContent = evt.label || 'Generating…';
                } else if (evt.type === 'pack_ready') {
                    self.startNewGameFromGenerated(evt.pack_id, closeModal, packPickerHtml);
                    return;
                } else if (evt.type === 'generation_error') {
                    body.innerHTML = `
                        <div class="pack-generate-progress">
                            <div class="pack-generate-progress__error">
                                ✕ ${_escapeHtml(evt.error || 'World generation failed. Please try again.')}
                            </div>
                        </div>`;
                    document.getElementById('pack-picker-title').textContent = 'Build Your World';
                    // Retry: re-fetch world builder form
                    setTimeout(() => {
                        fetch('/panels/world-builder')
                            .then(r => r.text())
                            .then(wbHtml => {
                                body.innerHTML = wbHtml;
                                if (window.Alpine) Alpine.initTree(body);
                            });
                    }, 2500);
                    return;
                }
            }
        }
    } catch (err) {
        body.innerHTML = `
            <div class="pack-generate-progress">
                <div class="pack-generate-progress__error">
                    ✕ ${_escapeHtml(err.message || 'Connection failed.')}
                </div>
            </div>`;
        document.getElementById('pack-picker-title').textContent = 'Build Your World';
    }
},

startNewGameFromGenerated(generatedPackId, closeModal, packPickerHtml) {
    this._selectedPackId = generatedPackId;
    this._modalStep = 'character';
    document.getElementById('pack-picker-title').textContent = 'Create Your Character';
    const body = document.getElementById('pack-picker-body');
    body.innerHTML = '<p class="empty-state">Loading character creation…</p>';
    const self = this;
    fetch('/panels/char-creation')
        .then(r => r.text())
        .then(charHtml => {
            body.innerHTML = charHtml;
            if (window.Alpine) Alpine.initTree(body);
            const confirmBtn = body.querySelector('.char-creation-btn--confirm');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', function onConfirm(e) {
                    if (confirmBtn.disabled) return;
                    e.preventDefault();
                    closeModal();
                    self.startNewGameWithCharCreation();
                });
            }
            const backBtn = body.querySelector('.char-creation-btn--back');
            if (backBtn) {
                backBtn.addEventListener('click', function onBack(e) {
                    e.preventDefault();
                    // Back from char creation after generation returns to pack picker (not world builder)
                    self._modalStep = 'pack';
                    document.getElementById('pack-picker-title').textContent = 'Choose a World';
                    body.innerHTML = packPickerHtml;
                    if (window.Alpine) Alpine.initTree(body);
                });
            }
        })
        .catch(() => { body.innerHTML = '<p class="empty-state">Failed to load character creation.</p>'; });
},
```

**Validation:** Full manual flow test after Phase 3 is complete. Unit-level: confirm `startWorldBuilder` is defined on the `game()` returned object. Confirm `startNewGameFromGenerated` sets `this._selectedPackId` to the given packId and calls `fetch('/panels/char-creation')`.

***

### Tests to write or update

No automated tests for JS behavior per AGENTS.md (JS is template-layer; tests live at integration/E2E level). Manual validation checklist is in Risks below.

### REPOMAP updates required

None in Phase 2 — no Python module changes.

### Risks

1. **Alpine.js `__x.$data` access pattern.** The `wbComp.__x.$data` pattern for accessing Alpine component data from outside the component is Alpine v2. If the project uses Alpine v3, the pattern is `Alpine.$data(wbComp)`. The executor must check which Alpine version is loaded (check `ccya/static/vendor/alpine.min.js` filename or header) and use the appropriate pattern.
2. **`wb-generate` custom event bubbling.** Alpine's `$dispatch` fires a `CustomEvent` with `bubbles: true` by default. The `body.addEventListener('wb-generate', ...)` listener on the modal body will catch it. If the executor sees it not firing, verify the event name matches exactly and that `bubbles` is not suppressed.
3. **Back button from char creation after generation.** When the user goes back from char creation after a successful generation, returning them to the pack picker (not back into the world builder) is the safer UX — the generated pack no longer exists in an editable state. This decision is encoded in `startNewGameFromGenerated`'s back button handler.

***

## Implementation — Phase 3: Server Routes and Pack Generator

### Context files to load
```
ccya/server/routes.py
ccya/engine/generate_pack.py   (does not exist yet — read generate_seed.py for pattern reference)
ccya/pack.py
ccya/models.py   (after world-rules.md plan is applied)
docs/REPOMAP/engine.md
docs/REPOMAP/server.md
```

### Overview
Add `GET /panels/world-builder` and `POST /new-game/generate-pack` to the server routes. Create `ccya/engine/generate_pack.py` with `generate_pack_from_brief()`. The generator calls the pack-gen LLM prompt, parses the response into `ScenarioBrief`, writes the result as an ephemeral pack to `packs/generated/<uuid>/`, and yields SSE events. On success the final event carries `pack_id` pointing to the generated directory — the client uses this as a normal pack ID for the subsequent `/new-game` POST.

### Detailed steps

#### Step 3.1 — Add `/panels/world-builder` GET route

**File:** `ccya/server/routes.py`

**What:** Add a new route `GET /panels/world-builder` that renders `_world_builder.html` with no template variables. Follow the exact same pattern as the existing `/panels/char-creation` route.

**Why:** The client fetches this URL to inject the world builder form into the modal. Must be server-rendered (not a static file) in case future iterations pass pack-specific context.

**Code Snippet**

Read `routes.py` first to find the `/panels/char-creation` handler. Then add immediately after it:

```python
@router.get("/panels/world-builder")
async def panel_world_builder(request: Request) -> HTMLResponse:
    log = logging.getLogger(__name__)
    log.debug("panel_world_builder")
    return templates.TemplateResponse("_world_builder.html", {"request": request})
```

**Validation:** `curl http://localhost:PORT/panels/world-builder` returns 200 with HTML containing `class="world-builder"`.

***

#### Step 3.2 — Create `ccya/engine/generate_pack.py`

**File:** `ccya/engine/generate_pack.py`

**What:** New engine module. Exposes one public async generator function:

```python
async def generate_pack_from_brief(
    inputs: dict,
    pack_dir: Path,
    llm_client,
    trace_id: str,
) -> AsyncIterator[dict]:
```

The function:
1. Emits `{"type": "phase", "label": "Generating scenario…"}`.
2. Builds the prompt context from `inputs` (concept, world_name, tone_tags, mood_note, world_rules).
3. Calls `llm_client` with `generate_pack_system.j2` and `generate_pack_user.j2` (non-streaming, single call — pack gen is not streamed token by token).
4. Emits `{"type": "phase", "label": "Parsing world…"}`.
5. Parses the LLM response into a `ScenarioBrief` via Pydantic.
6. Writes `scenario.yaml` and `manifest.yaml` to `pack_dir / uuid`.
7. Emits `{"type": "pack_ready", "pack_id": str(uuid_path)}`.
8. On any exception, emits `{"type": "generation_error", "error": str(e)}`.

**Why:** Per AGENTS.md, LLM calls belong in `ccya/engine/`, not in route handlers. This mirrors `ccya/engine/seed.py` which handles seed generation as a standalone LLM call.

**Code Snippet**

Read `ccya/engine/seed.py` for the prompt rendering and LLM call pattern before writing. Then implement:

```python
"""generate_pack.py — LLM-driven pack generation from player-supplied world brief."""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, AsyncIterator

import yaml

log = logging.getLogger(__name__)


async def generate_pack_from_brief(
    inputs: dict[str, Any],
    packs_root: Path,
    llm_client: Any,
    trace_id: str,
) -> AsyncIterator[dict[str, Any]]:
    """
    Generate an ephemeral pack from a player-supplied world brief.

    Yields server-sent event dicts: phase, pack_ready, or generation_error.
    Writes the result to packs_root / 'generated' / <uuid>/.
    """
    pack_id = f"generated/{uuid.uuid4().hex[:12]}"
    out_dir = packs_root / "generated" / pack_id.split("/")[1]
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info(
        "generate_pack_from_brief start",
        extra={"trace_id": trace_id, "pack": pack_id},
    )

    try:
        yield {"type": "phase", "label": "Generating scenario…"}

        # Build prompt messages — reuse the same Jinja2 env as the rest of the engine.
        # Import here to avoid circular imports; follow same pattern as seed.py.
        from ccya.engine.prompts import render_template  # noqa: PLC0415

        concept = inputs.get("concept", "")
        world_name = inputs.get("world_name", "")
        tone_tags = inputs.get("tone_tags", [])
        mood_note = inputs.get("mood_note", "")
        world_rules = inputs.get("world_rules", [])

        system_prompt = render_template(
            "generate_pack_system.j2",
            {},
        )
        user_prompt = render_template(
            "generate_pack_user.j2",
            {
                "concept": concept,
                "world_name": world_name,
                "tone_tags": tone_tags,
                "mood_note": mood_note,
                "world_rules": world_rules,
            },
        )

        log.debug(
            "generate_pack_from_brief LLM call",
            extra={"trace_id": trace_id, "pack": pack_id},
        )

        response_text = await llm_client.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            trace_id=trace_id,
        )

        yield {"type": "phase", "label": "Parsing world…"}

        # Parse YAML from LLM response — the pack-gen prompt instructs YAML output.
        # Strip markdown fences if present.
        raw = response_text.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])

        scenario_data = yaml.safe_load(raw)

        # Validate through ScenarioBrief Pydantic model.
        from ccya.models import ScenarioBrief  # noqa: PLC0415
        brief = ScenarioBrief(**scenario_data)

        # Write scenario.yaml
        (out_dir / "scenario.yaml").write_text(
            yaml.dump(brief.model_dump(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        # Write minimal manifest.yaml
        manifest = {
            "id": pack_id,
            "name": world_name or brief.inspiration.setting or "Custom World",
            "description": concept[:120] if concept else "A generated world.",
            "mode": "dynamic",
            "tone_tags": tone_tags,
        }
        (out_dir / "manifest.yaml").write_text(
            yaml.dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        log.info(
            "generate_pack_from_brief complete",
            extra={"trace_id": trace_id, "pack": pack_id},
        )

        yield {"type": "pack_ready", "pack_id": pack_id}

    except Exception as exc:
        log.exception(
            "generate_pack_from_brief error",
            extra={"trace_id": trace_id},
        )
        yield {"type": "generation_error", "error": str(exc)}
```

**Validation:** Write a unit test (see Tests section below). Confirm `ScenarioBrief` round-trip works: `ScenarioBrief(**yaml.safe_load(yaml.dump(brief.model_dump())))` does not raise.

***

#### Step 3.3 — Add `POST /new-game/generate-pack` SSE route

**File:** `ccya/server/routes.py`

**What:** Add a streaming SSE POST endpoint. It reads form data, validates `concept` is non-empty, resolves `packs_root` from app config, calls `generate_pack_from_brief()`, and streams the yielded event dicts as `data: <json>\n\n`. Uses `StreamingResponse` with `media_type="text/event-stream"`.

**Why:** SSE over a POST is the same pattern as `/turn`. The client reads it with a `ReadableStream` reader (not `EventSource`, which only supports GET). The `startWorldBuilder()` method in Phase 2 already implements the reader loop.

**Code Snippet**

Read `routes.py` to find the `/turn` streaming endpoint for pattern reference. Then add:

```python
@router.post("/new-game/generate-pack")
async def new_game_generate_pack(
    request: Request,
    concept: str = Form(""),
    world_name: str = Form(""),
    tone_tags: str = Form("[]"),
    mood_note: str = Form(""),
    world_rules: str = Form("[]"),
) -> StreamingResponse:
    import json as _json  # noqa: PLC0415
    import uuid as _uuid  # noqa: PLC0415
    from ccya.engine.generate_pack import generate_pack_from_brief  # noqa: PLC0415

    log = logging.getLogger(__name__)
    trace_id = _uuid.uuid4().hex[:8]

    log.info(
        "new_game_generate_pack",
        extra={"trace_id": trace_id, "concept_len": len(concept)},
    )

    if not concept.strip():
        async def _err():
            yield 'data: {"type":"generation_error","error":"Concept is required."}\n\n'
        return StreamingResponse(_err(), media_type="text/event-stream")

    try:
        tags = _json.loads(tone_tags)
        rules = _json.loads(world_rules)
    except Exception:
        tags = []
        rules = []

    inputs = {
        "concept": concept.strip(),
        "world_name": world_name.strip(),
        "tone_tags": tags,
        "mood_note": mood_note.strip(),
        "world_rules": rules,
    }

    # packs_root comes from app state — follow same pattern as other routes that load packs
    packs_root = request.app.state.packs_root
    llm_client = request.app.state.llm_client

    async def _stream():
        async for event in generate_pack_from_brief(
            inputs=inputs,
            packs_root=packs_root,
            llm_client=llm_client,
            trace_id=trace_id,
        ):
            yield f"data: {_json.dumps(event)}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")
```

**Validation:** `curl -X POST http://localhost:PORT/new-game/generate-pack -d 'concept=A+test+world'` should stream at least one `data:` line. After full flow: `packs/generated/` should contain a new directory with `scenario.yaml` and `manifest.yaml`.

***

#### Step 3.4 — Gitignore `packs/generated/`

**File:** `.gitignore` (root)

**What:** Add `packs/generated/` to the root `.gitignore`.

**Why:** Generated packs are ephemeral session artifacts. They must not be committed to the repo. This is the same treatment as other runtime-generated files.

**Code Snippet**

```
packs/generated/
```

**Validation:** `git status` after writing a test generated pack should show `packs/generated/` as untracked and ignored.

***

#### Step 3.5 — Verify `/new-game` POST handles `generated/*` pack IDs correctly

**File:** `ccya/server/routes.py` (read-only verification, possibly modify)

**What:** Read the existing `POST /new-game` handler. Confirm that the `pack_id` it receives is passed directly to `load_pack(pack_id, packs_root)` without any allowlist or prefix filtering. If there is filtering (e.g., only loading from a specific subdirectory), extend it to allow the `generated/` prefix.

**Why:** The generated pack's ID is `generated/<hex>`. If the route only accepts pack IDs from the default pack directory it will 404 or error on a generated pack. `load_pack()` itself uses `packs_root / pack_id` as the path, so as long as the directory exists and the route passes the ID through, it works.

**Validation:** After full flow: completing the world builder → char creation → clicking Begin should successfully call `POST /new-game` with `pack_id=generated/<hex>` and the server should return 200 and redirect to the game.

***

### Tests to write or update

**File:** `tests/test_generate_pack.py` (create)

```python
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import yaml
import pytest


@pytest.fixture
def tmp_packs(tmp_path):
    return tmp_path


def _make_llm_response():
    """Minimal valid ScenarioBrief YAML output."""
    return yaml.dump({
        "constraints": {},
        "world_facts": ["The world is covered in perpetual mist."],
        "narrator_rules": ["Write in second person."],
        "world_rules": [
            "Mist-navigation requires a tuned compass — GPS does not function.",
            "The sun has not been seen in forty years.",
            "Animals above rodent size no longer exist.",
        ],
        "factions": [],
        "locations": [],
        "name_locales": [],
        "name_seed": 1,
        "inspiration": {},
    })


@pytest.mark.asyncio
async def test_generate_pack_from_brief_happy_path(tmp_packs):
    from ccya.engine.generate_pack import generate_pack_from_brief

    llm = MagicMock()
    llm.complete = AsyncMock(return_value=_make_llm_response())

    inputs = {
        "concept": "A world of perpetual mist where the sun never shines.",
        "world_name": "The Murk",
        "tone_tags": ["horror", "survival"],
        "mood_note": "bleak",
        "world_rules": [
            "Mist-navigation requires a tuned compass.",
            "The sun has not been seen in forty years.",
        ],
    }

    events = []
    async for evt in generate_pack_from_brief(
        inputs=inputs,
        packs_root=tmp_packs,
        llm_client=llm,
        trace_id="test0001",
    ):
        events.append(evt)

    types = [e["type"] for e in events]
    assert "pack_ready" in types
    assert "generation_error" not in types

    pack_ready = next(e for e in events if e["type"] == "pack_ready")
    pack_path = tmp_packs / pack_ready["pack_id"].replace("/", str(Path("/")))
    assert (tmp_packs / "generated").exists()


@pytest.mark.asyncio
async def test_generate_pack_from_brief_llm_error(tmp_packs):
    from ccya.engine.generate_pack import generate_pack_from_brief

    llm = MagicMock()
    llm.complete = AsyncMock(side_effect=RuntimeError("LLM offline"))

    events = []
    async for evt in generate_pack_from_brief(
        inputs={"concept": "test"},
        packs_root=tmp_packs,
        llm_client=llm,
        trace_id="test0002",
    ):
        events.append(evt)

    assert any(e["type"] == "generation_error" for e in events)
```

### REPOMAP updates required

- `docs/REPOMAP/engine.md` — add entry for `generate_pack.py`: function `generate_pack_from_brief(inputs, packs_root, llm_client, trace_id) -> AsyncIterator[dict]`; describe ephemeral pack output, SSE event types (`phase`, `pack_ready`, `generation_error`).
- `docs/REPOMAP/server.md` — add entries for `GET /panels/world-builder` (returns `_world_builder.html` fragment) and `POST /new-game/generate-pack` (SSE endpoint; streams pack generation events; writes to `packs/generated/`).

### Risks

1. **`render_template` import path.** The executor must verify the exact import path for the Jinja2 rendering helper in `ccya/engine/`. If no `prompts.py` utility exists in `engine/`, check how `seed.py` loads and renders its templates and replicate that exact pattern. Do not invent a module that doesn't exist.
2. **`request.app.state.llm_client` key name.** The executor must grep `routes.py` for the actual attribute name on `app.state` used for the LLM client. It may be `llm`, `client`, `ollama_client`, or similar — use the existing name.
3. **`request.app.state.packs_root` key name.** Same as above — grep for the existing attribute.
4. **`generate_pack_user.j2` may not exist.** The plan assumes the pack-gen LLM is driven by a system + user prompt pair. If `generate_pack_system.j2` is a single self-contained prompt (no user message), the executor must adapt — pass the world brief inputs as part of the system prompt context variables instead of a separate user template. Read the current `generate_pack_system.j2` carefully before writing the LLM call.
5. **`llm_client.complete()` signature.** The `generate_pack_from_brief` code calls `await llm_client.complete(messages=[...], trace_id=...)`. Read `llm_client.py` to confirm the actual method name and signature — it may be `chat()`, `generate()`, or something else entirely.
6. **`brief.model_dump()` vs `brief.dict()`.** Pydantic v1 uses `.dict()`, v2 uses `.model_dump()`. Check the Pydantic version before writing the serialization call (same caveat as the `world-rules.md` plan).

***

## Ambiguities requiring resolution before execution

1. **Alpine.js version.** Phase 2 Step 2.2 accesses component data as `wbComp.__x.$data`. This is Alpine v2. Alpine v3 uses `Alpine.$data(wbComp)`. The executor must check `ccya/static/vendor/alpine.min.js` to determine the version before implementing. Options: A) Alpine v2 — use `__x.$data`. B) Alpine v3 — use `Alpine.$data(el)`.

2. **LLM client method name.** `generate_pack_from_brief` calls `await llm_client.complete(messages, trace_id)`. The executor must read `ccya/llm_client.py` to find the actual public method name and signature for a non-streaming single-completion call. Options: A) `.complete()`. B) `.chat()`. C) `.generate()`. D) A different pattern entirely — in which case adapt accordingly.

3. **Pack generation prompt structure.** Does `generate_pack_system.j2` expect a separate user message with world-specific content, or does it take all context as Jinja2 variables? Options: A) System + user message pair — create `generate_pack_user.j2` with the world brief variables. B) Single system prompt with Jinja2 context — pass all inputs as template context to `generate_pack_system.j2` only. The executor must read the existing `generate_pack_system.j2` to determine which before writing the LLM call.

4. **`packs_root` resolution in route.** The executor must find the actual attribute name on `request.app.state` for the packs root directory. Grep `routes.py` for `app.state.` references. If it is not stored on app state, find where `load_pack()` is called in `routes.py` and read how it resolves the path — then replicate that resolution in the generate-pack route.

If any of these are unresolved, the executor must NOT write code that guesses — read the source first.

***

## TODO.md update

Add under the `## Standalone` section created by the `world-rules.md` plan (directly after that entry):

```markdown
- [x] **World Builder UI — new game flow with custom world generation** — "Create Your Own" pack picker card → world builder 4-step form → SSE pack generation → char creator → begin game; new `generate_pack.py` engine module, `_world_builder.html` template, `/new-game/generate-pack` SSE endpoint — see [`world-builder-ui.md`](world-builder-ui.md) — **depends on `world-rules.md`**
```