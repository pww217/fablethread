function charCreation() {
    return {
        pc_name: '',
        pc_hints: '',
        npc_hints: '',
        arc_hints: '',
        free_form: '',
        selectedPackId: '',
        stats: [
            { key: 'strength', label: 'Strength', description: 'Force, melee combat, and soak against physical trauma.', value: 2 },
            { key: 'wits', label: 'Wits', description: 'Awareness, perception, and quick thinking under pressure.', value: 2 },
            { key: 'dexterity', label: 'Dexterity', description: 'Reflexes, ranged attacks, and avoiding danger.', value: 2 },
            { key: 'charisma', label: 'Charisma', description: 'Persuasion, leadership, and reading people.', value: 2 },
        ],

        get total() {
            return this.stats.reduce((sum, s) => sum + s.value, 0);
        },

        get isValid() {
            return this.total >= 8 && this.total <= 11
                && this.stats.every(s => s.value >= 1 && s.value <= 4);
        },

        getArchetypeDescriptions() {
            return {
                warrior: 'A frontline fighter. High Strength and Dexterity for melee combat and endurance.',
                scout: 'A nimble tracker. High Dexterity and Wits for stealth, perception, and reflexes.',
                scholar: 'A learned researcher. High Wits and Charisma for knowledge, investigation, and influence.',
                charmer: 'A charismatic leader. High Charisma and Wits for persuasion, leadership, and influence.',
            };
        },

        increment(statKey) {
            const stat = this.stats.find(s => s.key === statKey);
            if (stat && stat.value < 4 && this.total < 11) {
                stat.value++;
            }
        },

        decrement(statKey) {
            const stat = this.stats.find(s => s.key === statKey);
            if (stat && stat.value > 1) {
                stat.value--;
            }
        },

        applyPreset(name) {
            const archetypes = {
                warrior:   { strength: 4, dexterity: 3, wits: 2, charisma: 2 },
                scout:     { strength: 2, dexterity: 4, wits: 3, charisma: 2 },
                scholar:   { strength: 2, dexterity: 2, wits: 4, charisma: 3 },
                charmer:   { strength: 2, dexterity: 2, wits: 3, charisma: 4 },
            };
            const a = archetypes[name];
            if (a) {
                for (const s of this.stats) {
                    if (a[s.key] !== undefined) s.value = a[s.key];
                }
            }
        },

        serializedStats() {
            const obj = {};
            for (const s of this.stats) {
                obj[s.key] = s.value;
            }
            return JSON.stringify(obj);
        },

        init() {
            const packInput = document.querySelector('input[name="pack_id"]');
            if (packInput) {
                this.selectedPackId = packInput.value || '';
            }
        },
    };
}

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

function game() {
    return {
        input: '',
        submitting: false,
        asyncRunning: false,
        starting: false,
        gameStarted: window.__CCYA_INITIAL_STATE__.gameStarted,
        turnNum: window.__CCYA_INITIAL_STATE__.turnNum,
        hasNarrative: window.__CCYA_INITIAL_STATE__.hasNarrative,
        characterCreationEnabled: window.__CCYA_INITIAL_STATE__.characterCreationEnabled,
        activeSaveName: window.__CCYA_INITIAL_STATE__.activeSaveName,
        noSave: window.__CCYA_INITIAL_STATE__.noSave,

        // Width state (px or null for collapsed/using default).
        leftW: (() => {
            const c = localStorage.getItem('ccya_panel_left_collapsed');
            if (c === '1') return null;
            const w = parseInt(localStorage.getItem('ccya_panel_left_w'), 10);
            return isNaN(w) ? null : Math.max(180, w);
        })(),

        rightW: (() => {
            const c = localStorage.getItem('ccya_panel_right_collapsed');
            if (c === '1') return null;
            const w = parseInt(localStorage.getItem('ccya_panel_right_w'), 10);
            return isNaN(w) ? null : Math.max(180, w);
        })(),

        leftCollapsed: localStorage.getItem('ccya_panel_left_collapsed') === '1',
        rightCollapsed: localStorage.getItem('ccya_panel_right_collapsed') === '1',

        // Mobile drawer state (session-only, not persisted)
        leftDrawerOpen: false,
        rightDrawerOpen: false,

        get leftStyle() { return this.leftCollapsed ? 'width: 0; overflow: hidden;' : (this.leftW !== null ? `width: ${this.leftW}px;` : ''); },
        get rightStyle() { return this.rightCollapsed ? 'width: 0; overflow: hidden;' : (this.rightW !== null ? `width: ${this.rightW}px;` : ''); },

        toggleDrawer(side) {
            const key = side + 'DrawerOpen';
            this[key] = !this[key];
            if (!this.leftDrawerOpen && !this.rightDrawerOpen) {
                document.body.style.overflow = '';
            } else if (this[key]) {
                document.body.style.overflow = 'hidden';
            }
        },

        closeDrawer(side) {
            const key = side + 'DrawerOpen';
            if (this[key]) {
                this[key] = false;
                if (!this.leftDrawerOpen && !this.rightDrawerOpen) {
                    document.body.style.overflow = '';
                }
            }
        },

        _dragging: null,

        toggleCollapse(side) {
            const key = side + 'Collapsed';
            if (this[key]) {
                this.restorePanel(side);
            } else {
                this.saveWidth(side);
                this[key] = true;
                if (side === 'left') this.leftW = null;
                else this.rightW = null;
                localStorage.setItem('ccya_panel_' + side + '_collapsed', '1');
            }
        },

        restorePanel(side) {
            const key = side + 'Collapsed';
            const savedW = parseInt(localStorage.getItem('ccya_panel_' + side + '_w') || '320', 10);
            if (side === 'left') this.leftW = Math.max(180, isNaN(savedW) ? 320 : savedW);
            else this.rightW = Math.max(180, isNaN(savedW) ? 320 : savedW);
            this[key] = false;
            localStorage.setItem('ccya_panel_' + side + '_collapsed', '0');
        },

        saveWidth(side) {
            const wKey = 'ccya_panel_' + side + '_w';
            if (side === 'left' && this.leftW !== null) {
                try { localStorage.setItem(wKey, String(this.leftW)); } catch {}
            } else if (side === 'right' && this.rightW !== null) {
                try { localStorage.setItem(wKey, String(this.rightW)); } catch {}
            }
        },

        _sidebarDefault() {
            return window.innerWidth >= 2561 ? 512 : 320;
        },

        resetSidebars() {
            try { localStorage.removeItem('ccya_panel_left_w'); localStorage.removeItem('ccya_panel_right_w'); } catch {}
            const d = this._sidebarDefault();
            this.leftW = d;
            this.rightW = d;
            this.leftCollapsed = false;
            this.rightCollapsed = false;
        },

        onSidebarClick(side, e) {
            if (window.innerWidth <= 768) return; // mobile uses drawer toggles
            if (this[side + 'Collapsed']) {
                this.restorePanel(side);
            } else {
                const selector = side === 'left' ? '.sidebar-left' : '.sidebar';
                const rect = document.querySelector(selector).getBoundingClientRect();
                const isOuterEdge = side === 'left'
                    ? (e.clientX - rect.left) < 12
                    : (rect.right - e.clientX) < 12;
                if (isOuterEdge || window.innerWidth <= 900) {
                    this.toggleCollapse(side);
                }
            }
        },

        _setupGutterResize(side, selector) {
            const gutter = document.querySelector(selector);
            if (!gutter) return;

            gutter.addEventListener('mousedown', (e) => {
                e.preventDefault();
                const gi = window._gameInstance;
                if (!gi || gi[side + 'Collapsed']) return;

                const sidebarW = gi[side === 'left' ? 'leftW' : 'rightW'] || 320;

                this._dragging = {
                    side,
                    startX: e.clientX,
                    startW: sidebarW,
                    gutterEl: gutter,
                };

                document.body.style.cursor = 'col-resize';
                document.body.style.userSelect = 'none';
                gutter.classList.add('active');

                const onMouseMove = (e2) => {
                    let delta = e2.clientX - this._dragging.startX;
                    if (side === 'right') delta = -delta;
                    const newW = Math.max(180, this._dragging.startW + delta);
                    // Re-read container bounds on every tick to handle window resizes during drag.
                    const containerRect = document.querySelector('.app-body').getBoundingClientRect();
                    if (side === 'left') {
                        const maxW = containerRect.width - 400;
                        gi.leftW = Math.min(newW, Math.max(180, maxW));
                    } else {
                        const maxW = containerRect.width - 400;
                        gi.rightW = Math.min(newW, Math.max(180, maxW));
                    }
                    this.saveWidth(side);
                };

                const onMouseUp = () => {
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                    gutter.classList.remove('active');
                    if (this._dragging) {
                        this.saveWidth(this._dragging.side);
                        this._dragging = null;
                    }
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                    window.removeEventListener('beforeunload', onBeforeUnload);
                };

                const onBeforeUnload = () => {
                    this.saveWidth(side);
                };

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
                window.addEventListener('beforeunload', onBeforeUnload);
            });
        },

        initGutters() {
            this._setupGutterResize('left', '.gutter-left');
            this._setupGutterResize('right', '.gutter-right');
        },

        init() {
            window._gameInstance = this;
            this.initReroll();
            _bindTooltips(document);
            if (!this.hasNarrative && !this.noSave) {
                this.$nextTick(() => this.openPackPicker());
            }
            // Close drawers when crossing the 768px boundary (orientation change, etc.)
            this._drawerBoundary = window.matchMedia('(max-width: 768px)');
            this._drawerBoundary.addEventListener('change', (e) => {
                if (!e.matches) {
                    this.leftDrawerOpen = false;
                    this.rightDrawerOpen = false;
                    document.body.style.overflow = '';
                }
            });
            // Adjust sidebar defaults when crossing ultrawide boundary (only if user hasn't manually resized)
            this._ultraBoundary = window.matchMedia('(min-width: 2561px)');
            const adjustSidebarsOnResize = () => {
                const def = window.innerWidth >= 2561 ? 512 : 320;
                ['left', 'right'].forEach((side) => {
                    const wKey = side + 'W';
                    if (!localStorage.getItem('ccya_panel_' + side + '_w')) {
                        this[wKey] = def;
                    }
                });
            };
            this._ultraBoundary.addEventListener('change', adjustSidebarsOnResize);
            // Touch swipe: edge open + drawer dismiss
            this._swipeStartX = 0;
            this._swipeStartY = 0;
            document.addEventListener('touchstart', (e) => {
                if (window.innerWidth > 768) return;
                const t = e.touches[0];
                this._swipeStartX = t.clientX;
                this._swipeStartY = t.clientY;
            }, { passive: true });
            document.addEventListener('touchend', (e) => {
                if (window.innerWidth > 768) return;
                const dx = e.changedTouches[0].clientX - this._swipeStartX;
                const dy = e.changedTouches[0].clientY - this._swipeStartY;
                if (Math.abs(dx) < Math.abs(dy) * 1.5) return;
                if (Math.abs(dx) < 40) return;
                // 3-slide carousel: [left] ←→ [narrative] ←→ [right]
                // Swipe direction determines which adjacent panel opens
                if (dx > 0) {
                    // Swipe right: close left if open, else open left
                    if (this.leftDrawerOpen) {
                        this.closeDrawer('left');
                    } else if (this.rightDrawerOpen) {
                        this.closeDrawer('right');
                    } else {
                        this.toggleDrawer('left');
                    }
                } else {
                    // Swipe left: close right if open, else open right
                    if (this.rightDrawerOpen) {
                        this.closeDrawer('right');
                    } else if (this.leftDrawerOpen) {
                        this.closeDrawer('left');
                    } else {
                        this.toggleDrawer('right');
                    }
                }
            }, { passive: true });
        },

        onEnter(event) {
            if (!event.shiftKey) {
                event.preventDefault();
                this.submitTurn();
            }
        },

        openPackPicker() {
            const backdrop = document.getElementById('pack-picker-backdrop');
            const modal = document.getElementById('pack-picker-modal');
            const body = document.getElementById('pack-picker-body');
            backdrop.style.display = 'block';
            modal.style.display = 'flex';
            body.innerHTML = '<p class="empty-state">Loading packs…</p>';
            this._modalStep = 'pack';

            const self = this;
            const close = () => {
                backdrop.style.display = 'none';
                modal.style.display = 'none';
                document.removeEventListener('keydown', onKey);
            };

            // ── Delete handler (reusable) ──
            const handleDelete = (deleteBtn, currentHtml) => {
                const packId = deleteBtn.dataset.deletePack;
                if (!packId) return;
                if (!confirm(`Delete "${packId}"? This cannot be undone.`)) return;
                fetch(`/packs/${encodeURIComponent(packId)}`, { method: 'DELETE' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) {
                            body.innerHTML = `<p class="empty-state" style="color:var(--accent-red)">${data.error}</p>`;
                            return;
                        }
                        body.innerHTML = '<p class="empty-state">Deleting…</p>';
                        fetch('/panels/pack-picker')
                            .then(r => r.text())
                            .then(newHtml => {
                                body.innerHTML = newHtml;
                                if (window.Alpine) Alpine.initTree(body);
                                self._wirePackCards(newHtml);
                            });
                    });
            };

            // ── Pack card click handler (reusable) ──
            self._wirePackCards = function(originalHtml) {
                // Attach delete handlers directly to each delete button so they
                // fire before the body-level card handler and stop propagation.
                body.querySelectorAll('.pack-card-delete').forEach(btn => {
                    btn.addEventListener('click', function(e) {
                        e.stopImmediatePropagation();
                        handleDelete(btn, originalHtml);
                    });
                });
                body.addEventListener('click', function onCardClick(e) {
                    const card = e.target.closest('[data-pack-id]');
                    if (!card) return;
                    body.removeEventListener('click', onCardClick);

                    if (card.dataset.packId === '__create__') {
                        self._modalStep = 'worldbuilder';
                        document.getElementById('pack-picker-title').textContent = 'Build Your World';
                        body.innerHTML = '<p class="empty-state">Loading world builder…</p>';
                        fetch('/panels/world-builder')
                            .then(r => r.text())
                            .then(wbHtml => {
                                body.innerHTML = wbHtml;
                                if (window.Alpine) Alpine.initTree(body);
                                body.addEventListener('wb-generate', function onGenerate() {
                                    body.removeEventListener('wb-generate', onGenerate);
                                    const wbComp = body.querySelector('.world-builder');
                                    const wbData = wbComp && window.Alpine ? Alpine.$data(wbComp) : null;
                                    if (!wbData) return;
                                    self.startWorldBuilder(wbData.serialize(), close, originalHtml);
                                });
                                body.addEventListener('wb-back-to-packs', function onBackToPacks() {
                                    body.removeEventListener('wb-back-to-packs', onBackToPacks);
                                    self._modalStep = 'pack';
                                    document.getElementById('pack-picker-title').textContent = 'Choose a World';
                                    body.innerHTML = originalHtml;
                                    if (window.Alpine) Alpine.initTree(body);
                                    body.addEventListener('click', onCardClick);
                                });
                            })
                            .catch(() => { body.innerHTML = '<p class="empty-state">Failed to load world builder.</p>'; });
                        return;
                    }
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
                                    body.innerHTML = originalHtml;
                                    if (window.Alpine) Alpine.initTree(body);
                                    body.addEventListener('click', onCardClick);
                                });
                            }
                        })
                        .catch(() => { body.innerHTML = '<p class="empty-state">Failed to load character creation.</p>'; });
                });
            };

            fetch('/panels/pack-picker')
                .then(r => r.text())
                .then(html => {
                    body.innerHTML = html;
                    self._wirePackCards(html);
                })
                .catch(() => { body.innerHTML = '<p class="empty-state">Failed to load packs.</p>'; });

            document.getElementById('pack-picker-close').onclick = close;
            backdrop.onclick = close;

            const onKey = (e) => { if (e.key === 'Escape') close(); };
            document.addEventListener('keydown', onKey);
            window._closePackPicker = close;
        },

        get _selectedPackId() {
            return this.__selectedPackId || '';
        },
        set _selectedPackId(v) {
            this.__selectedPackId = v;
        },

        get _modalStep() {
            return this.__modalStep || 'pack';
        },
        set _modalStep(v) {
            this.__modalStep = v;
        },

        async startNewGame(packId, { force = false } = {}) {
            window._closePackPicker && window._closePackPicker();
            const shouldForce = force || !!this._forceNewGame;
            this._forceNewGame = false;
            if (!shouldForce && this.turnNum > 0 && !confirm('Reset the current game? This cannot be undone.')) return;
            this.starting = true;
            const narrativePanel = document.getElementById('narrative-panel');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'pack-generate-progress';
            loadingDiv.id = 'new-game-loading';
            loadingDiv.innerHTML = `
                <div class="pack-generate-progress__spinner"></div>
                <div class="pack-generate-progress__label">Starting new game…</div>
                <div class="pack-generate-progress__sublabel">Preparing your adventure.</div>`;
            narrativePanel.insertBefore(loadingDiv, narrativePanel.firstChild);
            try {
                const body = new FormData();
                if (packId) body.append('pack_id', packId);
                const resp = await fetch('/new-game', { method: 'POST', body });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                window.location.reload();
            } catch (e) {
                console.error('New game failed:', e);
                loadingDiv.className = 'pack-generate-progress';
                loadingDiv.innerHTML = `
                    <div class="pack-generate-progress__error">
                        ✕ Failed to start new game: ${_escapeHtml(e.message)}
                    </div>`;
                this.starting = false;
            }
        },

        async startNewGameWithCharCreation() {
            this.starting = true;
            const narrativePanel = document.getElementById('narrative-panel');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'pack-generate-progress';
            loadingDiv.id = 'new-game-loading';
            loadingDiv.innerHTML = `
                <div class="pack-generate-progress__spinner"></div>
                <div class="pack-generate-progress__label">Creating your character…</div>
                <div class="pack-generate-progress__sublabel">Preparing your adventure.</div>`;
            narrativePanel.insertBefore(loadingDiv, narrativePanel.firstChild);
            try {
                // Collect character creation form data
                const body = new FormData();
                body.append('pack_id', this._selectedPackId || '');

                // Read from the form fields in the modal body
                const bodyEl = document.getElementById('pack-picker-body');
                const nameInput = bodyEl?.querySelector('#cc-name');
                const pcHintsInput = bodyEl?.querySelector('#cc-pc-hints');
                const npcHintsInput = bodyEl?.querySelector('#cc-npc-hints');
                const arcHintsInput = bodyEl?.querySelector('#cc-arc-hints');
                const freeFormInput = bodyEl?.querySelector('#cc-free-form');
                const statsInput = bodyEl?.querySelector('input[name="pc_stats"]');

                if (nameInput?.value) body.append('pc_name', nameInput.value.trim());
                if (pcHintsInput?.value) body.append('pc_hints', pcHintsInput.value.trim());
                if (npcHintsInput?.value) body.append('npc_hints', npcHintsInput.value.trim());
                if (arcHintsInput?.value) body.append('arc_hints', arcHintsInput.value.trim());
                if (freeFormInput?.value) body.append('free_form', freeFormInput.value.trim());
                if (statsInput?.value) body.append('pc_stats', statsInput.value);

                const resp = await fetch('/new-game', { method: 'POST', body });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                window.location.reload();
            } catch (e) {
                console.error('New game failed:', e);
                loadingDiv.className = 'pack-generate-progress';
                loadingDiv.innerHTML = `
                    <div class="pack-generate-progress__error">
                        ✕ Failed to start new game: ${_escapeHtml(e.message)}
                     </div>`;
                this.starting = false;
            }
        },

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

        // Show reroll button after page loads with an opening (dynamic pack only)
        initReroll() {
            const btn = document.getElementById('reroll-btn');
            const openingBlock = document.getElementById('opening-block');
            if (btn && openingBlock && this.turnNum === 0) {
                btn.style.display = '';
                // Hide reroll once the player takes their first turn
                const obs = new MutationObserver(() => {
                    if (this.turnNum > 0) { btn.style.display = 'none'; obs.disconnect(); }
                });
                obs.observe(document.getElementById('narrative-panel'), { childList: true, subtree: false });
            }
        },

        submitTurn() {
            if (!this.input.trim() || this.submitting || !this.gameStarted) return;
            const np = _narrativePanelEl();
            const prevInput = this.input;
            const prevActions = [];
            document.querySelectorAll('#actions-zone .action-pill').forEach((b) => {
                prevActions.push(b.textContent);
            });

            this.submitting = true;
            const userInput = this.input.trim();
            this.input = '';

            document.querySelectorAll('.action-pill').forEach((p) => { p.disabled = true; });
            const az = document.getElementById('actions-zone');
            if (az) az.innerHTML = '';

            document.getElementById('empty-prompt')?.remove();

            const block = document.createElement('div');
            block.className = 'narrative-block';
            const echo = document.createElement('p');
            echo.className = 'narrative-input-echo';
            echo.textContent = '> ' + userInput;
            const textDiv = document.createElement('div');
            textDiv.className = 'narrative-text';
            textDiv.innerHTML = '<span class="streaming-cursor"></span>';
            textDiv.classList.add('streaming');
            // Detached element cleanup
            // that call `cursor.remove()`. The live cursor span lives inside textDiv
            // and is replaced each render in `_drainRenderFn`.
            const cursor = document.createElement('span');
            const strip = document.createElement('div');
            strip.className = 'progress-strip';
            strip.setAttribute('data-phase', 'ruling');
            strip.innerHTML = _progressStripHTML();
            _bindProgressTimer(strip);
            block.appendChild(echo);
            block.appendChild(textDiv);
            block.appendChild(strip);
            np.appendChild(block);

            // One-time scroll to bottom so "determining outcome" state is visible.
            np.scrollTo({ top: np.scrollHeight, behavior: 'instant' });

            const self = this;
            this._turnEs = null;
            this._turnCancel = function () {
                _stopDisplayDrain();
                const t = self._turnEs;
                if (t) {
                    try { t.close(); } catch (err) { /* ignore */ }
                }
                self._turnEs = null;
                self._turnCancel = null;
                _clearProgressStrip(strip);
                if (cursor.parentNode) cursor.remove();
                if (textDiv) {
                    textDiv.classList.remove('streaming');
                    textDiv.innerHTML = '';
                }
                if (block.parentNode) block.remove();
                self.input = prevInput;
                const zone = document.getElementById('actions-zone');
                if (zone && prevActions.length) {
                    zone.innerHTML = '';
                    prevActions.forEach((action) => {
                        const btn = document.createElement('button');
                        btn.className = 'action-pill';
                        btn.setAttribute('data-md', '');
                        btn.textContent = action;
                        btn.addEventListener('click', () => self.fillFromChoice(action));
                        self._setupPillDblTap(btn, action);
                        zone.appendChild(btn);
                    });
                }
                _revealPillsOnScroll();
                if (zone && prevActions.length === 0) {
                    zone.innerHTML = '<span class="empty-state">Suggested actions appear after each turn.</span>';
                }
                const npReroll = document.getElementById('narrative-panel');
                if (npReroll) npReroll.scrollTo({ top: npReroll.scrollHeight, behavior: 'instant' });
                self.submitting = false;
                if (window.innerWidth > 768) document.getElementById('player-input')?.focus();
            };

            const url = '/turn?input=' + encodeURIComponent(userInput);
            const es = new EventSource(url);
            this._turnEs = es;

            // Streaming: two-buffer architecture.
            // streamBuf  — complete LLM output so far (source of truth for final flush).
            // drainState — mutable object shared with _startDisplayDrain drain loop.
            let streamBuf = '';
            const drainState = { pendingQueue: '', displayBuf: '' };

            const _drainRenderFn = (currentDisplayBuf) => {
                _configureMarked();
                const html = _renderMarkdown(_capitalizeFirst(currentDisplayBuf.replace(/\s+$/, '')));
                textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
                // Highlight known entities as they appear during streaming
                const stateScript = document.getElementById('initial-state');
                if (stateScript) {
                    try {
                        const initState = JSON.parse(stateScript.textContent);
                        _highlightEntities(textDiv, initState);
                    } catch (e) { /* skip */ }
                }
                // Smooth scroll so textDiv top stays near top of narrative-panel.
                // Uses a fresh scroll animation each call — no state carried across calls.
                if (currentDisplayBuf.length > 0) {
                    textDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            };

            es.addEventListener('narrative_token', (e) => {
                const data = JSON.parse(e.data);
                const chunk = data.chunk || '';
                streamBuf            += chunk;
                drainState.pendingQueue += chunk;
                _startDisplayDrain(drainState, _drainRenderFn);
            });

            es.addEventListener('phase', (e) => {
                const payload = JSON.parse(e.data);
                if (payload && payload.phase === 'narrate_done') {
                    _stopDisplayDrain();
                    drainState.displayBuf   += drainState.pendingQueue;
                    drainState.pendingQueue  = '';
                    textDiv.classList.remove('streaming');
                    _configureMarked();
                    textDiv.innerHTML = _renderMarkdown(_capitalizeFirst(streamBuf));
                    const stateScript = document.getElementById('initial-state');
                    if (stateScript) {
                        try { _highlightEntities(textDiv, JSON.parse(stateScript.textContent)); } catch (e) { /* skip */ }
                    }
                }
                if (payload && payload.phase === 'extract_stream_done' && (payload.stream === 'record' || payload.stream === 'state' || payload.stream === 'scene')) {
                    if (payload.stream === 'record') {
                        self.submitting = false;
                        document.getElementById('player-input')?.removeAttribute('disabled');
                    }
                }
                if (payload && (payload.phase === 'sanitize_start' || payload.phase === 'world_start')) {
                    _setProgressFromPhase(strip, { phase: '', reason: '' });
                } else {
                    _setProgressFromPhase(strip, payload);
                }
            });

            es.addEventListener('panel_update', (e) => {
                const data = JSON.parse(e.data);
                if (data.panel === 'scene' && data.data) {
                    const sceneCard = document.getElementById('card-scene');
                    if (sceneCard) {
                        const npcs = data.data.npcs || {};
                        const present = Object.values(npcs).filter(n => n && n.presence === 'present');
                        present.sort((a, b) => (a.display_name || a.name || '').localeCompare(b.display_name || b.name || ''));
                        const listEl = sceneCard.querySelector('.npc-list');
                        if (listEl && present.length > 0) {
                            listEl.innerHTML = present.map(n => _renderNpcListItem(n)).join('');
                        } else if (listEl) {
                            listEl.innerHTML = '<span class="empty-state">No one else is around.</span>';
                        }
                    }
                    const locName = document.querySelector('#card-location .location-name');
                    if (locName && data.data.location) {
                        locName.textContent = data.data.location.name || '—';
                    }
                    const locDesc = document.querySelector('#card-location .card-desc');
                    if (locDesc && data.data.location) {
                        locDesc.innerHTML = data.data.location.description
                            ? `<span data-md>${_escapeHtml(data.data.location.description)}</span>`
                            : '';
                    }
                } else if (data.panel === 'state' && data.data) {
                    const invBody = document.querySelector('#card-inventory .sidebar-card-body');
                    if (invBody) {
                        const items = data.data.inventory || [];
                        if (items.length > 0) {
                            invBody.innerHTML = items.map(i => _renderInventoryItem(i)).join('');
                        } else {
                            invBody.innerHTML = '<span class="empty-state">You aren\'t carrying anything!</span>';
                        }
                    }
                    const locName = document.querySelector('#card-location .location-name');
                    if (locName && data.data.location) {
                        locName.textContent = data.data.location.name || '—';
                    }
                    const locDesc = document.querySelector('#card-location .card-desc');
                    if (locDesc && data.data.location) {
                        locDesc.innerHTML = data.data.location.description
                            ? `<span data-md>${_escapeHtml(data.data.location.description)}</span>`
                            : '';
                    }
                    const playerCard = document.querySelector('#card-player .sidebar-card-body');
                    if (playerCard && data.data.pc) {
                        const conds = data.data.pc.conditions || [];
                        const oldConds = playerCard.querySelector('[style*="margin-top: 8px"]');
                        if (oldConds) oldConds.remove();
                        if (conds.length > 0) {
                            const div = document.createElement('div');
                            div.style.cssText = 'margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;';
                            div.innerHTML = conds.map(c => _renderConditionPill(c)).join('');
                            playerCard.appendChild(div);
                        }
                    }
                } else if (data.panel === 'arc' && data.data) {
                    htmx.ajax('GET', '/panels/state-left', { target: '#state-panel-left' });
                }
            });

            es.addEventListener('turn_complete', (e) => {
                es.close();
                self._turnEs = null;
                self._turnCancel = null;
                const result = JSON.parse(e.data);
                this.turnNum = result.turn || this.turnNum;
                _clearProgressStrip(strip);

                const tagline = result.state ? _headerTaglineFromState(result.state) : null;
                const hl = document.getElementById('header-logo');
                if (hl && tagline) hl.innerHTML = _renderMarkdownInline(tagline);
                if (tagline) document.title = 'CCYA: ' + tagline.replace(/\*\*?([^*]+)\*\*?/g, '$1').trim();

                if (cursor.parentNode) cursor.remove();
                textDiv.classList.remove('streaming');
                textDiv.innerHTML = _renderMarkdown(_capitalizeFirst(result.narrative || ''));
                if (result.state) _highlightEntities(textDiv, result.state);

                const met = document.createElement('div');
                met.className = 'turn-metrics';
                met.textContent = _formatMetricsRow(result.metrics);
                textDiv.after(met);

                // Outcome badge then inline change summary — both after narrative text.
                let lastInserted = met;
                const ruling = result.ruling || {};
                if (ruling.rolled || result.outcome_summary) {
                    const badge = _buildOutcomeBadge(
                        ruling.rolled ? ruling : { outcome_summary: result.outcome_summary, reason: ruling.reason }
                    );
                    if (badge) { lastInserted.after(badge); lastInserted = badge; }
                }
                const changes = _buildTurnChanges(result.change_lines || []);
                    if (changes) { lastInserted.after(changes); lastInserted = changes; }

                // Thread progress is now included in the main change line.

                // Debug-mode metadata row.
                if (result.debug_mode) {
                    const debugDiv = document.createElement('div');
                    debugDiv.className = 'debug-metadata-row';

                    const gmBeatText = result.gm_beat ? `${result.gm_beat.type} — ${result.gm_beat.effect || '—'}` : '\u2014';

                    debugDiv.innerHTML = `<span class="debug-label">Phase:</span> ${_capitalizeFirst(result.scene_phase || '')}&ensp;|&ensp;<span class="debug-label">GM Beat:</span> ${gmBeatText}&ensp;|&ensp;<span class="debug-label">Hint:</span> ${_capitalizeFirst(result.outcome_hint || '')}&ensp;|&ensp;<span class="debug-label">Summary:</span> ${_capitalizeFirst(result.summary || '')}`;
                    lastInserted.after(debugDiv);
                    lastInserted = debugDiv;
                }

                _applyMarkdown(block);

                if (result.rejected && result.rejected.length > 0) {
                    const note = document.createElement('div');
                    note.className = 'rejection-note';
                    note.textContent = `\u26a0 Some changes were rejected (trace\u00a0${result.trace_id})`;
                    block.appendChild(note);
                }

                const zone = document.getElementById('actions-zone');
                if (result.actions && result.actions.length > 0) {
                    zone.innerHTML = '';
                    result.actions.forEach((action) => {
                        const btn = document.createElement('button');
                        btn.className = 'action-pill';
                        btn.setAttribute('data-md', '');
                        btn.textContent = action;
                        btn.addEventListener('click', () => this.fillFromChoice(action));
                        this._setupPillDblTap(btn, action);
                        zone.appendChild(btn);
                    });
                    _applyMarkdown(zone);
                }
                _revealPillsOnScroll();

                _prependTurnLogTurn(result.turn, result.change_lines || [], result.ruling);

                htmx.ajax('GET', '/panels/state-left', { target: '#state-panel-left' });
                htmx.ajax('GET', '/panels/state-right', { target: '#state-panel-right' });
                this.submitting = false;

                if (result.game_over) {
                    _showGameOver(this);
                } else if (window.innerWidth > 768) {
                    setTimeout(() => document.getElementById('player-input')?.focus(), 100);
                }
                _bindTooltips(document);
            });

            es.addEventListener('turn_error', (e) => {
                es.close();
                self._turnEs = null;
                self._turnCancel = null;
                _clearProgressStrip(strip);
                if (cursor.parentNode) cursor.remove();
                const data = JSON.parse(e.data);
                textDiv.innerHTML =
                    `<span style="color:var(--accent-error)">${_escapeHtml(data.error || 'Unknown error')}</span>`;
                htmx.ajax('GET', '/panels/state-left', { target: '#state-panel-left' });
                htmx.ajax('GET', '/panels/state-right', { target: '#state-panel-right' });
                document.querySelectorAll('.action-pill').forEach((p) => { p.disabled = false; });
                this.submitting = false;
            });

            es.onerror = () => {
                es.close();
                self._turnEs = null;
                self._turnCancel = null;
                if (this.submitting) {
                _clearProgressStrip(strip);
                if (cursor.parentNode) cursor.remove();
                    textDiv.insertAdjacentHTML('beforeend',
                        '<span style="color:var(--accent-error)"> [connection\u00a0lost\u00a0\u2014 try again]</span>');
                    document.querySelectorAll('.action-pill').forEach((p) => { p.disabled = false; });
                    this.submitting = false;
                }
            };
        },

        stopTurn() {
            if (!this.submitting || typeof this._turnCancel !== 'function') return;
            fetch('/turn/cancel', { method: 'POST' }).catch(() => {});
            this._turnCancel();
        },

        retryTurn() {
            if (this.submitting || this.turnNum === 0) return;
            const np = _narrativePanelEl();
            const blocks = np.querySelectorAll('.narrative-block');
            const lastBlock = blocks[blocks.length - 1];
            if (!lastBlock) return;

            this.submitting = true;
            lastBlock.remove();

            const zone = document.getElementById('actions-zone');
            zone.innerHTML = '<span class="empty-state">Loading…</span>';

            const self = this;
            fetch('/turn/delete', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.error) throw new Error(data.error);

                    zone.innerHTML = '';
                    if (data.actions && data.actions.length > 0) {
                        data.actions.forEach((action) => {
                            const btn = document.createElement('button');
                            btn.className = 'action-pill';
                            btn.setAttribute('data-md', '');
                            btn.textContent = action;
                            btn.addEventListener('click', () => this.fillFromChoice(action));
                            this._setupPillHold(btn, action);
                            zone.appendChild(btn);
                        });
                        _applyMarkdown(zone);
                    }
                    _revealPillsOnScroll();
                    const npRetry = document.getElementById('narrative-panel');
                    if (npRetry) npRetry.scrollTo({ top: npRetry.scrollHeight, behavior: 'instant' });

                    this.input = '';
                    htmx.ajax('GET', '/panels/state-left', { target: '#state-panel-left' });
                    htmx.ajax('GET', '/panels/state-right', { target: '#state-panel-right' });
                    this.submitting = false;
                    if (window.innerWidth > 768) {
                        setTimeout(() => document.getElementById('player-input')?.focus(), 100);
                    }
                })
                .catch(e => {
                    zone.innerHTML = '<span class="empty-state" style="color:var(--accent-error)">Delete failed: ' + _escapeHtml(e.message) + '</span>';
                    this.submitting = false;
                    if (window.innerWidth > 768) document.getElementById('player-input')?.focus();
                });
        },

        fillFromChoice(text, fromHold = false) {
            if (this.submitting) return;
            const pill = event?.target?.closest('.action-pill');
            if (pill) pill.classList.toggle('selected');
            const trimmed = (text || '').trim();
            if (!trimmed) return;
            const existing = this.input.trimEnd();
            this.input = existing + (existing ? ', ' : '') + trimmed + ' ';
            if (fromHold || window.innerWidth > 768) {
                document.getElementById('player-input')?.focus();
            } else {
                this.submitTurn();
            }
        },

        _setupPillDblTap(btn, text) {
            let lastTap = 0;
            const DOUBLE_TAP_WINDOW = 300;
            const onTap = (e) => {
                const now = Date.now();
                if (now - lastTap < DOUBLE_TAP_WINDOW) {
                    lastTap = 0;
                    e.stopImmediatePropagation();
                    e.preventDefault();
                    this.fillFromChoice(text, true);
                    btn.classList.add('hold-filled');
                    setTimeout(() => btn.classList.remove('hold-filled'), 300);
                    const inp = document.getElementById('player-input');
                    if (inp) { inp.focus(); inp.click(); }
                } else {
                    lastTap = now;
                }
            };
            btn.addEventListener('touchend', onTap);
        },

        // Settings panel state
        savingSettings: false,
        settingsStatus: { text: '', class: '' },
        settings: {},

        async loadSettings() {
            try {
                const resp = await fetch('/api/settings');
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                this.settings = await resp.json();
            } catch (e) {
                console.error('Failed to load settings:', e);
            }
        },

        async saveSettings() {
            this.savingSettings = true;
            this.settingsStatus = { text: '', class: '' };
            
            try {
                const resp = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.settings),
                });
                
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                this.settings = await resp.json();
                
                this.settingsStatus = { text: 'Settings saved.', class: 'settings-status--success' };
            } catch (e) {
                console.error('Failed to save settings:', e);
                this.settingsStatus = { text: `Save failed: ${e.message}`, class: 'settings-status--error' };
            } finally {
                this.savingSettings = false;
            }
        },

        async openSettingsPanel() {
            await this.loadSettings();
            document.getElementById('settings-backdrop').classList.remove('hidden');
            const modal = document.getElementById('settings-modal');
            modal.classList.remove('hidden');
            modal.focus();
        },

        closeSettingsPanel() {
            document.getElementById('settings-backdrop').classList.add('hidden');
            document.getElementById('settings-modal').classList.add('hidden');
        },

        openSavePicker() {
            const el = document.getElementById('save-picker-shell');
            if (el) Alpine.$data(el).open(this.activeSaveName);
        },
    };
}
