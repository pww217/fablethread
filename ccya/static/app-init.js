// Settings panel: escape key closes it; backdrop click closes it
document.addEventListener('DOMContentLoaded', () => {
    // Settings panel
    const settingsBackdrop = document.getElementById('settings-backdrop');
    const settingsModal = document.getElementById('settings-modal');
    if (settingsBackdrop && settingsModal) {
        settingsBackdrop.addEventListener('click', () => {
            window._gameInstance?.closeSettingsPanel();
        });
        settingsModal.querySelector('.settings-close').addEventListener('click', () => {
            window._gameInstance?.closeSettingsPanel();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !settingsModal.classList.contains('hidden')) {
                e.preventDefault();
                window._gameInstance?.closeSettingsPanel();
            }
        });
    }

    // Save picker "New Game" event
    document.addEventListener('savepicker:new-game', () => {
        window._gameInstance?.openPackPicker();
    });

    // Landing page "Load Save" button
    document.getElementById('landing-load-save-btn')?.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const el = document.getElementById('save-picker-shell');
        if (el) Alpine.$data(el).open(window._gameInstance?.activeSaveName || '');
    });
});
document.addEventListener('DOMContentLoaded', () => {
    _configureMarked();
    _applyMarkdown();

    // Highlight known entity names in server-rendered history blocks
    const stateScript = document.getElementById('initial-state');
    if (stateScript) {
        try {
            const initState = JSON.parse(stateScript.textContent);
            document.querySelectorAll('.narrative-block .narrative-text').forEach(el => {
                _highlightEntities(el, initState);
            });
        } catch (e) { /* state JSON parse failure — skip highlighting */ }
    }

    _bindTooltips(document);
    initTurnLogUi();

    // Collapsed/open state for sidebar <details> cards.
    // `toggle` does NOT bubble — must use capture phase for delegation.
    applyCardOpenStateFromStorage();
    document.addEventListener('toggle', (e) => {
        const t = e.target;
        if (t.matches && t.matches('details.sidebar-card[data-card]')) {
            localStorage.setItem(CCYA_CARD_KEY(t.dataset.card), t.open ? '1' : '0');
        }
    }, true);  // capture=true required: toggle doesn't bubble
    document.body.addEventListener('htmx:afterSwap', (e) => {
        const id = e.target && e.target.id;
        if (id === 'state-panel-left' || id === 'state-panel-right') {
            applyCardOpenStateFromStorage();
            _applyMarkdown(e.target);
            _bindTooltips(e.target);
        }
        if (id === 'debug-content') {
            _applyMarkdown(e.target);
        }
        if (id === 'turn-log-body') {
            _applyMarkdown(e.target);
            _bindTooltips(e.target);
        }
        if (e.target && e.target.matches && e.target.matches('#opening-block .narrative-text')) {
            _applyMarkdown(e.target);
            const stateScript = document.getElementById('initial-state');
            if (stateScript) {
                try {
                    const initState = JSON.parse(stateScript.textContent);
                    _highlightEntities(e.target, initState);
                } catch (e) { /* skip */ }
            }
        }
    });

    // Inline pills inside the narrative panel so they scroll naturally with content.
    _inlinePillsLayout();
    window.addEventListener('resize', _inlinePillsLayout);

    // Auto-scroll narrative to bottom (shows most recent history entry)
    const np = document.getElementById('narrative-panel');
    if (np) np.scrollTo({ top: np.scrollHeight, behavior: 'instant' });

    // Ensure pills are inline after auto-scroll.
    _revealPillsOnScroll();

    // Focus input if a game is already in progress (desktop only)
    const inp = document.getElementById('player-input');
    if (inp && !inp.disabled && window.innerWidth > 768) inp.focus();

    // Fetch Ollama status and update the header dot
    fetch('/healthz').then(r => r.json()).then(data => {
        const dot = document.getElementById('mock-dot');
        if (!dot) return;
        const ver = data.ollama_version ? ` — Ollama ${data.ollama_version}` : '';
        if (data.mock) {
            dot.classList.add('mock');
            dot.title = 'Mock mode (no Ollama)';
        } else if (data.ollama === 'ok' && data.available) {
            dot.classList.add('ready');
            dot.title = data.model + ' — ready' + ver;
        } else {
            dot.classList.add('error');
            dot.title = (data.ollama === 'fail'
                ? 'Ollama unreachable'
                : 'Model ' + data.model + ' not loaded') + ver;
        }
    }).catch(() => {
        const dot = document.getElementById('mock-dot');
        if (dot) { dot.classList.add('error'); dot.title = 'Status unknown'; }
    });

    // Set up gutter drag-resize listeners after Alpine init.
    window._gameInstance?.initGutters();

    // Track mouse position for edge hover detection — show hints near screen edges when panels are collapsed.
    (function setupCollapsedHints() {
        const LEFT_ZONE = 20;
        const RIGHT_ZONE = 20;

        function showHint(side, visible) {
            const hint = document.getElementById('hint-' + side);
            if (!hint) return;
            if (visible && !hint.classList.contains('visible')) {
                hint.classList.add('visible');
            } else if (!visible && hint.classList.contains('visible')) {
                hint.classList.remove('visible');
            }
        }

        document.addEventListener('mousemove', (e) => {
            const gi = window._gameInstance;
            if (!gi) return;

            if (e.clientX < LEFT_ZONE && gi.leftCollapsed) {
                showHint('left', true);
            } else {
                showHint('left', false);
            }

            const fromRight = window.innerWidth - e.clientX;
            if (fromRight < RIGHT_ZONE && gi.rightCollapsed) {
                showHint('right', true);
            } else {
                showHint('right', false);
            }
        });

        document.getElementById('hint-left')?.addEventListener('click', () => window._gameInstance?.restorePanel('left'));
        document.getElementById('hint-right')?.addEventListener('click', () => window._gameInstance?.restorePanel('right'));
    })();
});
