var CCYA_CARD_KEY = (name) => 'ccya_card_' + name;

// Per-NPC color palette — 12 distinguishable muted colors for dark backgrounds
const _NPC_PALETTE = [
    '#e06c75', '#c67b40', '#e5c07b', '#7eb8da',
    '#56b6c2', '#61afef', '#bb85f0', '#be5046',
    '#d19a66', '#7eb8da', '#528bff', '#c678dd',
];

function _npcColor(id) {
    let h = 0;
    for (let i = 0; i < id.length; i++) {
        h = ((h << 5) - h) + id.charCodeAt(i);
        h |= 0;
    }
    return _NPC_PALETTE[Math.abs(h) % _NPC_PALETTE.length];
}

function _configureMarked() {
    if (typeof marked === 'undefined' || !marked.use) return;
    marked.use({ gfm: true, breaks: false });
}

function _headerTaglineFromState(st) {
    if (!st || typeof st !== 'object') return 'Choose Your Own Adventure';
    const meta = st.meta || {};
    const name = (meta.session_name && String(meta.session_name).trim()) || '';
    if (name) return name;
    const pc = st.pc || {};
    const loc = st.location || {};
    if (loc.id && (pc.name || loc.name)) {
        return (pc.name || 'Player') + ' @ ' + (loc.name || loc.id);
    }
    return 'Choose Your Own Adventure';
}

function _groupChangeLines(lines) {
    const invGain = [], invLoss = [], pl = [], loc = [], fa = [], thAdded = [], thUpdated = [], thResolved = [], thFailed = [], thAbandoned = [], thRemoved = [], ar = [];
    lines.forEach(s => {
        s = String(s);
        if (s.startsWith('🎒')) {
            const isGain = s.includes(' + ') || s.includes('×') && !s.includes(' − ');
            const isLoss = s.startsWith('🎒 −') || s.includes(' − ');
            if (isLoss) invLoss.push(s);
            else invGain.push(s);
        }
        else if (s.startsWith('🩺')) pl.push(s);
        else if (s.startsWith('🗺️')) loc.push(s);
        else if (s.startsWith('📜')) fa.push(s);
        else if (s.startsWith('📓')) {
            if (s.includes(' ↻ ')) thUpdated.push(s);
            else if (s.includes(' ✓ ')) thResolved.push(s);
            else if (s.includes(' ✗ ')) thFailed.push(s);
            else if (s.includes(' ⊘ ')) thAbandoned.push(s);
            else if (s.startsWith('📓 −')) thRemoved.push(s);
            else thAdded.push(s);
        }
        else if (s.startsWith('🏁')) ar.push(s);
        else invGain.push(s);
    });
    return { invGain, invLoss, pl, loc, fa, thAdded, thUpdated, thResolved, thFailed, thAbandoned, thRemoved, ar };
}

function _buildTurnChanges(changeLines) {
    if (!changeLines || !changeLines.length) return null;
    const g = _groupChangeLines(changeLines);
    const sections = [
        ['tc-inv-gain', g.invGain],
        ['tc-inv-loss', g.invLoss],
        ['tc-th-added', g.thAdded],
        ['tc-th-updated', g.thUpdated],
        ['tc-th-resolved', g.thResolved],
        ['tc-th-failed', g.thFailed],
        ['tc-th-abandoned', g.thAbandoned],
        ['tc-th-removed', g.thRemoved],
        ['tc-ar',       g.ar],
        ['tc-pl',       g.pl],
        ['tc-loc',      g.loc],
        ['tc-fa',       g.fa],
    ];
    const hasAny = sections.some(([, rows]) => rows.length > 0);
    if (!hasAny) return null;

    const wrap = document.createElement('div');
    wrap.className = 'turn-changes';
    sections.forEach(([cls, rows]) => {
        rows.forEach((ln) => {
            const line = document.createElement('div');
            line.className = 'turn-changes-line ' + cls;
            line.setAttribute('data-md', '');
            line.textContent = ln;
            wrap.appendChild(line);
        });
    });
    return wrap;
}

function _prependTurnLogTurn(turn, changeLines, rules) {
    const body = document.getElementById('turn-log-body');
    if (!body || !changeLines || !changeLines.length) return;
    const wrap = document.createElement('div');
    wrap.className = 'turn-log-block turn-log-block--fresh';
    const head = document.createElement('div');
    head.className = 'turn-log-turn';
    head.textContent = 'Turn ' + turn;
    wrap.appendChild(head);
    if (rules && (rules.rolled || rules.outcome_summary)) {
        const badge = _buildOutcomeBadge(rules);
        if (badge) { badge.style.margin = '4px 0 6px'; wrap.appendChild(badge); }
    }
    changeLines.forEach((ln) => {
        const row = document.createElement('div');
        const s = String(ln);
        let cls = 'turn-log-line';
        if (s.startsWith('🎒 −')) cls += ' tl-inv-loss';
        else if (s.startsWith('🎒 +') || s.startsWith('🎒 ~') || s.startsWith('🎒 ⚠')) cls += ' tl-inv-gain';
        else if (s.startsWith('🩺')) cls += ' tl-pl';
        else if (s.startsWith('🗺️')) cls += ' tl-loc';
        else if (s.startsWith('📜')) cls += ' tl-fa';
        else if (s.startsWith('📓')) {
            if (s.includes(' ↻ ')) cls += ' tl-th-updated';
            else if (s.includes(' ✓ ')) cls += ' tl-th-resolved';
            else if (s.includes(' ✗ ')) cls += ' tl-th-failed';
            else if (s.includes(' ⊘ ')) cls += ' tl-th-abandoned';
            else if (s.startsWith('📓 −')) cls += ' tl-th-removed';
            else cls += ' tl-th-added';
        }
        else if (s.startsWith('🏁')) cls += ' tl-ar';
        row.className = cls;
        row.setAttribute('data-md', '');
        row.textContent = ln;
        wrap.appendChild(row);
    });
    body.insertBefore(wrap, body.firstChild);
    _applyMarkdown(wrap);
}

function _fmtTokens(n) {
    if (n == null) return '—';
    n = Number(n);
    if (n < 1000) return n.toString();
    return (n / 1000).toFixed(2).replace(/\.?0+$/, '') + 'k';
}

function _formatMetricsRow(metrics) {
    if (!metrics || typeof metrics !== 'object') return '';
    const r = metrics.ruling || {};
    const n = metrics.narrate || {};
    const x = metrics.extract || {};
    const streams = x.streams || {};

    function fmtStep(ms, ti, to) {
        const t = (ms != null) ? (Number(ms) / 1000).toFixed(1) + 's' : '—';
        if (ti != null && to != null) return t + ' (' + _fmtTokens(ti) + '/' + _fmtTokens(to) + ')';
        return t;
    }

    const parts = [];
    parts.push('Rul ' + fmtStep(r.total_ms, r.tokens_in, r.tokens_out));
    parts.push('Nar ' + fmtStep(n.total_ms, n.tokens_in, n.tokens_out));
    const sc = streams.scene;
    if (sc && !sc.skipped) parts.push('Scn ' + fmtStep(sc.ms, sc.tokens_in, sc.tokens_out));
    const st = streams.state;
    if (st && !st.skipped) parts.push('Ste ' + fmtStep(st.ms, st.tokens_in, st.tokens_out));
    const pg = streams.storytell;
    if (pg && !pg.skipped) parts.push('Rec ' + fmtStep(pg.ms, pg.tokens_in, pg.tokens_out));
    const san = metrics.sanitize;
    if (san) parts.push('San ' + fmtStep(san.ms, null, null));
    const wr = streams.world;
    if (wr && !wr.skipped) parts.push('Wld ' + fmtStep(wr.ms, wr.tokens_in, wr.tokens_out));
    return parts.join('   ·   ');
}

function _narrativePanelEl() {
    return document.getElementById('narrative-panel');
}

/**
 * Scroll container so targetEl's top edge aligns with container's top.
 * Uses a steady rate (px/second) anchored to the element's position.
 * User scroll aborts the animation. Cancels any in-progress scroll on same
 * container before starting a new one.
 */
function _smoothScrollContainerToTop(container, targetEl, pxPerSec) {
    if (!container || !targetEl) return;
    pxPerSec = pxPerSec == null ? 80 : pxPerSec;

    const startScrollTop = container.scrollTop;
    const containerTop = container.getBoundingClientRect().top;
    const startDelta = targetEl.getBoundingClientRect().top - containerTop;

    const totalPx = Math.abs(startDelta);
    if (totalPx < 4) return;
    const duration = (totalPx / pxPerSec) * 1000;
    const direction = startDelta > 0 ? 1 : -1;

    let rafId = null;
    const abortHandler = () => {
        cancelAnimationFrame(rafId);
        container.removeEventListener('scroll', abortHandler, { passive: true });
    };
    container.addEventListener('scroll', abortHandler, { passive: true });

    const startTime = performance.now();

    function ease(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    function tick(now) {
        const elapsed = now - startTime;
        const t = Math.min(elapsed / duration, 1);
        const easedT = ease(t);
        const newScroll = startScrollTop + totalPx * easedT * direction;
        container.scrollTop = newScroll;

        if (t < 1) {
            rafId = requestAnimationFrame(tick);
        } else {
            container.removeEventListener('scroll', abortHandler, { passive: true });
        }
    }

    rafId = requestAnimationFrame(tick);
}

// Display drain: decouples token arrival from visual text reveal.
// pendingQueue accumulates raw text; the drain loop reveals it at CHARS_PER_FRAME
// characters per animation frame (~60 fps).
let _drainRafId  = null;
let _drainRender = null;

const CHARS_PER_FRAME = 6;

function _startDisplayDrain(state, renderFn) {
    if (_drainRafId !== null) return;

    function drain() {
        if (state.pendingQueue.length === 0) {
            _drainRafId  = null;
            _drainRender = null;
            return;
        }
        const chunk = state.pendingQueue.slice(0, CHARS_PER_FRAME);
        state.pendingQueue = state.pendingQueue.slice(CHARS_PER_FRAME);
        state.displayBuf  += chunk;
        renderFn(state.displayBuf);
        _drainRafId = requestAnimationFrame(drain);
    }

    _drainRender = renderFn;
    _drainRafId  = requestAnimationFrame(drain);
}

function _stopDisplayDrain() {
    if (_drainRafId !== null) {
        cancelAnimationFrame(_drainRafId);
        _drainRafId  = null;
        _drainRender = null;
    }
}

function _progressStripHTML() {
    return '<span class="progress-spinner" aria-hidden="true"></span>'
        + '<span class="progress-label">Determining outcome…</span>'
        + '<span class="progress-metas">'
        + '<span class="progress-eta"></span>'
        + '<span class="progress-elapsed">0.0s</span>'
        + '</span>';
}

const BAND_LABELS = {
    crit_fail: 'CRITICAL FAIL',
    fail: 'FAIL',
    setback: 'SETBACK',
    mixed: 'MIXED',
    boon: 'BOON',
    success: 'SUCCESS',
    crit_success: 'CRITICAL SUCCESS',
};

function _buildOutcomeBadge(payload) {
    if (!payload) return null;
    const isRoll = payload.rolled && payload.band;
    if (!isRoll && !payload.outcome_summary) return null;

    if (isRoll) {
        const badge = document.createElement('div');
        badge.className = 'roll-badge roll-badge--' + payload.band;

        // Line 1: skill · difficulty
        const skillLabel = (payload.skill || '').toUpperCase();
        const diffLabel = (payload.difficulty || '').toLowerCase();
        const hdr = document.createElement('div');
        hdr.className = 'roll-header';
        if (payload.reason) {
            hdr.innerHTML = '🎲 <strong>' + skillLabel + '</strong> &nbsp;·&nbsp; <span class="has-tooltip">' + diffLabel + '<span class="tooltip-body">' + payload.reason + '</span></span>';
        } else {
            hdr.innerHTML = '🎲 <strong>' + skillLabel + '</strong> &nbsp;·&nbsp; ' + diffLabel;
        }
        badge.appendChild(hdr);

        // Line 2: dice + labeled modifiers + total
        const dieVal = (payload.dice || [])[0] || 0;
        const totalMod = (payload.stat_mod || 0) + (payload.diff_mod || 0);
        const diffLabels = {hard: 'Hard', extreme: 'Extreme'};
        let parts = ['Roll = ' + dieVal];
        if (payload.stat_mod !== 0) {
            const sign = payload.stat_mod > 0 ? '+' : '-';
            parts[0] += ' ' + sign + ' ' + Math.abs(payload.stat_mod) + ' (' + (payload.skill || '').charAt(0).toUpperCase() + (payload.skill || '').slice(1) + ')';
        }
        if (payload.diff_mod !== 0) {
            const label = diffLabels[payload.difficulty] || (payload.difficulty || '').charAt(0).toUpperCase() + (payload.difficulty || '').slice(1);
            const sign = payload.diff_mod > 0 ? '+' : '-';
            parts[0] += ' ' + sign + ' ' + Math.abs(payload.diff_mod) + ' (' + label + ')';
        }
        parts[0] += ' = <strong>' + payload.final_total + '</strong>';
        const math = document.createElement('div');
        math.className = 'roll-math';
        math.innerHTML = parts.join(' &thinsp;·&thinsp; ');
        badge.appendChild(math);

        // Line 3: band pill with intent tooltip
        const bandLabel = BAND_LABELS[payload.band] || (payload.band || '').toUpperCase().replace(/_/g, ' ');
        const bandWrapper = document.createElement('span');
        bandWrapper.className = 'has-tooltip';
        const res = document.createElement('div');
        res.className = 'roll-result roll-band--' + payload.band;
        res.textContent = bandLabel;
        bandWrapper.appendChild(res);
        if (payload.intent) {
            const tip = document.createElement('div');
            tip.className = 'tooltip-body';
            tip.textContent = payload.intent;
            bandWrapper.appendChild(tip);
        }
        badge.appendChild(bandWrapper);

        if (payload.outcome_summary) {
            const outcomeText = document.createElement('div');
            outcomeText.className = 'roll-outcome';
            outcomeText.textContent = _capitalizeFirst(payload.outcome_summary);
            badge.appendChild(outcomeText);
        }

        return badge;
    }

    // Non-roll: centered banner with outcome text, tooltip on text
    const badge = document.createElement('div');
    badge.className = 'roll-badge roll-badge--outcome';

    const el = document.createElement('div');
    el.className = 'roll-outcome' + (payload.reason ? ' has-tooltip' : '');
    el.textContent = _capitalizeFirst(payload.outcome_summary);
    badge.appendChild(el);

    if (payload.reason) {
        const tip = document.createElement('div');
        tip.className = 'tooltip-body';
        tip.textContent = payload.reason;
        el.appendChild(tip);
    }
    return badge;
}

function _setProgressFromPhase(strip, payload) {
    const p = (payload && payload.phase) || '';
    strip.setAttribute('data-phase', p);
    const label = strip.querySelector('.progress-label');
    const eta = strip.querySelector('.progress-eta');
    if (p === 'ruling_start') {
        label.textContent = 'Determining outcome…';
        strip._phaseStart = Date.now();
        if (eta && payload && payload.expected_ms > 0) {
            eta.textContent = '~' + (payload.expected_ms / 1000).toFixed(0) + 's avg';
        } else if (eta) { eta.textContent = ''; }
    } else if (p === 'ruling_done') {
        if (eta) eta.textContent = '';
    } else if (p === 'narrate_start') {
        label.textContent = 'Composing narrative…';
        strip._phaseStart = Date.now();
        if (eta && payload && payload.expected_ms > 0) {
            eta.textContent = '~' + (payload.expected_ms / 1000).toFixed(0) + 's avg';
        } else if (eta) { eta.textContent = ''; }
    } else if (p === 'narrate_first_token') {
        const ft = (payload && payload.first_token_ms) || 0;
        if (eta) eta.textContent = '~' + (ft / 1000).toFixed(1) + 's ttft';
    } else if (p === 'narrate_done') {
        label.textContent = 'Reviewing outcome…';
        if (eta) eta.textContent = '';
    } else if (p === 'extract_start') {
        label.textContent = 'Updating game state…';
        strip._phaseStart = Date.now();
        if (eta && payload && payload.expected_ms > 0) {
            eta.textContent = '~' + (payload.expected_ms / 1000).toFixed(0) + 's avg';
        } else if (eta) { eta.textContent = ''; }
    } else if (p === 'extract_retry') {
        const n = (payload && payload.attempt) || '?';
        label.textContent = 'Re-checking state (try ' + n + ')…';
        if (eta) eta.textContent = '';
    } else if (p === 'extract_done') {
        label.textContent = 'Saving…';
        if (eta) eta.textContent = '';
    } else if (p === 'extract_stream_start') {
        const stream = (payload && payload.stream) || '';
        if (stream === 'scene') {
            label.textContent = 'Refreshing scene…';
        } else if (stream === 'state') {
            label.textContent = 'Updating state…';
        } else if (stream === 'record') {
            label.textContent = 'Recording Outcome…';
        } else {
            label.textContent = 'Updating game state…';
        }
        strip._phaseStart = Date.now();
        if (eta) eta.textContent = '';
    } else if (p === 'extract_stream_done') {
        if (eta) eta.textContent = '';
    } else if (p === 'persist') {
        label.textContent = 'Saving…';
        if (eta) eta.textContent = '';
    } else if (p === 'sanitize_start') {
        label.textContent = 'Sanitizing state…';
        if (eta) eta.textContent = '';
    } else if (p === 'sanitize_done') {
        if (eta) eta.textContent = '';
    }
}

function _clearProgressStrip(strip) {
    if (strip) {
        if (strip._tick) clearInterval(strip._tick);
        strip._tick = null;
        strip.remove();
    }
}

function _bindProgressTimer(strip) {
    strip._phaseStart = Date.now();
    const elapsedEl = strip.querySelector('.progress-elapsed');
    strip._tick = setInterval(() => {
        if (!elapsedEl) return;
        const s = (Date.now() - strip._phaseStart) / 1000;
        elapsedEl.textContent = (s < 10 ? s.toFixed(1) : s.toFixed(0)) + 's';
    }, 250);
}

function applyCardOpenStateFromStorage() {
    document.querySelectorAll('aside.sidebar details.sidebar-card[data-card]').forEach((d) => {
        const v = localStorage.getItem(CCYA_CARD_KEY(d.dataset.card));
        if (v === '1') d.setAttribute('open', '');
        else if (v === '0') d.removeAttribute('open');
    });
}
function _capitalizeFirst(str) {
    const s = String(str || '');
    if (!s) return s;
    return s.charAt(0).toUpperCase() + s.slice(1);
}

function _restoreDebugMetadata() {
    try {
        const stateScript = document.getElementById('initial-state');
        if (!stateScript) return;
        const initState = JSON.parse(stateScript.textContent);
        const metaScript = document.getElementById('initial-state-meta');
        let lastHistoryTurn = null;
        if (metaScript) {
            try { lastHistoryTurn = JSON.parse(metaScript.textContent).last_history_turn; } catch {}
        }
        const sessionName = (initState.meta || {}).session_name || 'default';
        const raw = localStorage.getItem('ccya_debug_' + sessionName);
        if (!raw) return;
        const data = JSON.parse(raw);
        if (!data || !data.turn) return;
        // Only restore if the saved turn matches the last history turn.
        if (data.turn !== lastHistoryTurn) return;
        // Find the last narrative block and append the debug row.
        const blocks = document.querySelectorAll('.narrative-block');
        if (!blocks.length) return;
        const lastBlock = blocks[blocks.length - 1];
        const existing = lastBlock.querySelector('.debug-metadata-row');
        if (existing) return;
        const debugDiv = document.createElement('div');
        debugDiv.className = 'debug-metadata-row';
        const gmText = data.gm_beat?.type ? `${data.gm_beat.type} — ${data.gm_beat.effect || '—'}` : '\u2014';
        debugDiv.innerHTML = `<span class="debug-label">Phase:</span> ${_capitalizeFirst(data.scene_phase || '')}&ensp;|&ensp;<span class="debug-label">GM Beat:</span> ${gmText}&ensp;|&ensp;<span class="debug-label">Hint:</span> ${_capitalizeFirst(data.outcome_hint || '')}&ensp;|&ensp;<span class="debug-label">Summary:</span> ${_capitalizeFirst(data.summary || '')}`;
        lastBlock.appendChild(debugDiv);
    } catch { /* skip */ }
}

function _escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function _renderMarkdown(text) {
    if (!text) return '';
    if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
        // Strip inter-element newlines so white-space: pre-wrap doesn't
        // render phantom gaps during streaming.
        return marked.parse(String(text)).replace(/>\n+</g, '><');
    }
    let s = _escapeHtml(text);
    s = s.replace(/^# (.+)$/gm,  '<h2>$1</h2>');
    s = s.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*(.+?)\*/g,     '<em>$1</em>');
    s = s.replace(/`([^`]+)`/g,     '<code>$1</code>');
    s = s.replace(/((?:^- .+$\n?)+)/gm, (match) => {
        const items = match.trim().split('\n')
            .map(l => '<li>' + l.replace(/^- /, '') + '</li>')
            .join('');
        return '<ul>' + items + '</ul>';
    });
    const parts = s.split(/\n\n+/);
    return parts.map(p => {
        p = p.trim();
        if (!p) return '';
        if (/^<(h[23]|ul|ol|li)/.test(p)) return p;
        return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
    }).filter(Boolean).join('');
}

function _renderMarkdownInline(text) {
    if (!text) return '';
    if (typeof marked !== 'undefined' && typeof marked.parseInline === 'function') {
        return marked.parseInline(String(text));
    }
    return _renderMarkdown(text);
}

function _applyMarkdown(root) {
    _configureMarked();
    (root || document).querySelectorAll('.narrative-text[data-raw]').forEach(el => {
        el.innerHTML = _renderMarkdown(el.textContent);
        el.removeAttribute('data-raw');
    });
    (root || document).querySelectorAll('[data-md]').forEach(el => {
        el.innerHTML = _renderMarkdownInline(el.textContent);
        el.removeAttribute('data-md');
    });
}

// ---------------------------------------------------------------------------
// Entity highlighting — wraps known NPC/item/PC/location names in colored
// <span> tags after markdown rendering.
// ---------------------------------------------------------------------------
function _highlightEntities(container, state) {
    if (!state || !container) return;
    const names = [];

    // Collect NPC names with their colors
    const npcs = (state.compendium && state.compendium.npcs) || {};
    const numericWords = new Set(['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']);
    for (const id in npcs) {
        const entry = npcs[id];
        if (entry && entry.name) {
            const color = entry.color || _npcColor(id);
            names.push({ name: entry.name, cls: 'entity-npc', color: color });
            const parts = entry.name.split(/\s+/);
            if (parts.length > 1) {
                if (!numericWords.has(parts[0].toLowerCase())) names.push({ name: parts[0], cls: 'entity-npc', color: color });
                const last = parts[parts.length - 1];
                if (!numericWords.has(last.toLowerCase())) names.push({ name: last, cls: 'entity-npc', color: color });
            }
        }
    }

    // Collect inventory item names
    const inv = state.inventory || [];
    for (const item of inv) {
        if (item && item.name) names.push({ name: item.name, cls: 'entity-item' });
    }

    // Collect PC name
    if (state.pc && state.pc.name) {
        const pcName = state.pc.name;
        names.push({ name: pcName, cls: 'entity-pc' });
        const pcParts = pcName.split(/\s+/);
        if (pcParts.length > 1) {
            if (!numericWords.has(pcParts[0].toLowerCase())) names.push({ name: pcParts[0], cls: 'entity-pc' });
            const last = pcParts[pcParts.length - 1];
            if (!numericWords.has(last.toLowerCase())) names.push({ name: last, cls: 'entity-pc' });
        }
    }

    // Collect location name
    if (state.location && state.location.name) names.push({ name: state.location.name, cls: 'entity-location' });

    if (!names.length) return;

    // Sort descending by length to match longest first
    names.sort((a, b) => b.name.length - a.name.length);

    // Precompile regexes with word-boundary matching:
    // - Entity name must not be preceded/followed by word chars or apostrophe
    // - Trailing word chars (plural 's', possessive 's) are consumed into the highlight
    const escaped = names.map(n => ({
        ...n,
        regex: new RegExp(
            '(?<![a-z0-9\'])' +
            n.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') +
            '(?![a-z0-9\'])' +
            '(?:\\B\\w+)?',
            'i'
        )
    }));

    // Walk text nodes
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);

    for (const textNode of textNodes) {
        const p = textNode.parentNode;
        if (p && (p.tagName === 'STRONG' || p.tagName === 'A'
            || (p.tagName === 'SPAN' && p.className && p.className.startsWith('entity-')))) {
            continue;
        }

        const text = textNode.textContent;
        const frag = document.createDocumentFragment();
        let pos = 0;

        while (pos < text.length) {
            let best = null;
            for (const { name, cls, color, regex } of escaped) {
                const m = text.slice(pos).match(regex);
                if (!m) continue;
                const absIdx = pos + m.index;
                if (!best || absIdx < best.absIdx) {
                    best = { absIdx, name, cls, color, match: m[0] };
                }
            }
            if (!best) break;
            if (best.absIdx > pos) {
                frag.appendChild(document.createTextNode(text.slice(pos, best.absIdx)));
            }
            const span = document.createElement('span');
            span.className = best.cls;
            span.style.color = best.color;
            span.textContent = best.match;
            frag.appendChild(span);
            pos = best.absIdx + best.match.length;
        }
        if (pos < text.length) {
            frag.appendChild(document.createTextNode(text.slice(pos)));
        }
        if (frag.childNodes.length > 0) {
            textNode.parentNode.replaceChild(frag, textNode);
        }
    }
}

// ---------------------------------------------------------------------------
// Tooltip portal — per-anchor mouseenter/mouseleave (no hover bridge)
// ---------------------------------------------------------------------------
const TT_MARGIN = 8;
let _ttAnchor = null;

function _ttTip() {
    const p = document.getElementById('tooltip-portal');
    return p ? p.querySelector('.tooltip-body') : null;
}

function _ttPosition(rect) {
    const t = _ttTip();
    if (!t) return;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const tw = t.offsetWidth || 280;
    const th = t.offsetHeight || 100;
    let top = rect.bottom + TT_MARGIN;
    let left = rect.left;
    if (top + th > vh - TT_MARGIN) top = rect.top - th - TT_MARGIN;
    if (left + tw > vw - TT_MARGIN) left = vw - tw - TT_MARGIN;
    if (left < TT_MARGIN) left = TT_MARGIN;
    t.style.top = top + 'px';
    t.style.left = left + 'px';
}

function _tooltipShow(anchor) {
    const src = anchor.querySelector(':scope > .tooltip-body');
    if (!src) return;
    const t = _ttTip();
    if (!t) return;
    _ttAnchor = anchor;
    t.innerHTML = src.innerHTML;
    _configureMarked();
    t.querySelectorAll('[data-md-compendium]').forEach((el) => {
        el.innerHTML = _renderMarkdown(el.textContent);
        el.classList.add('compendium-tooltip');
        el.removeAttribute('data-md-compendium');
    });
    t.querySelectorAll('[data-md]').forEach((el) => {
        el.innerHTML = _renderMarkdownInline(el.textContent);
        el.removeAttribute('data-md');
    });
    _ttPosition(anchor.getBoundingClientRect());
    t.classList.add('tt-visible');
}

function _tooltipHide() {
    const t = _ttTip();
    if (t) { t.classList.remove('tt-visible'); t.innerHTML = ''; }
    _ttAnchor = null;
}

function _bindTooltips(root) {
    (root || document).querySelectorAll('.has-tooltip').forEach((anchor) => {
        if (anchor.dataset.ttBound) return;
        anchor.dataset.ttBound = '1';
        anchor.addEventListener('mouseenter', () => { _tooltipShow(anchor); });
        anchor.addEventListener('mouseleave', (e) => {
            const rel = e.relatedTarget;
            if (rel && anchor.contains(rel)) return;
            _tooltipHide();
        });
    });
}

window.addEventListener('scroll', () => {
    if (_ttAnchor) _ttPosition(_ttAnchor.getBoundingClientRect());
}, { passive: true, capture: true });


window.addEventListener('resize', () => {
    if (_ttAnchor) _ttPosition(_ttAnchor.getBoundingClientRect());
});

function _showGameOver(gameInstance) {
    const goBackdrop = document.getElementById('game-over-backdrop');
    const modal = document.getElementById('game-over-modal');
    const sub = document.getElementById('game-over-sub');
    const btn = document.getElementById('game-over-new-game');
    if (!goBackdrop || !modal) return;

    document.getElementById('player-input').disabled = true;
    document.querySelectorAll('.action-pill').forEach(p => { p.disabled = true; });
    document.querySelectorAll('.send-btn').forEach(b => { b.disabled = true; });

    goBackdrop.hidden = false;
    modal.hidden = false;

    const tagline = document.getElementById('header-logo')?.textContent?.trim();
    sub.textContent = tagline ? `"${tagline.replace(/[*_`]/g, '')}"` : '';

    const dismiss = () => {
        goBackdrop.hidden = true;
        modal.hidden = true;
    };

    btn.onclick = () => {
        dismiss();
        gameInstance._forceNewGame = true;
        gameInstance.openPackPicker();
    };

    goBackdrop.onclick = dismiss;
}

let _pillScrollHandler = null;
let _pillThrottledHandler = null;
let _pillsVisible = false;

/*
  Pills live inside the narrative panel (last child) so they scroll
  naturally with the content — no show/hide state machine needed.
*/
function _inlinePillsLayout() {
    const zone = document.getElementById('actions-zone');
    const np = document.getElementById('narrative-panel');
    if (!zone || !np) return;

    // Tear down any stale scroll listener from previous state
    if (_pillThrottledHandler) {
        np.removeEventListener('scroll', _pillThrottledHandler);
        _pillThrottledHandler = null;
        _pillScrollHandler = null;
    }
    _pillsVisible = false;

    np.appendChild(zone);
    // Ensure pills are visible in normal document flow
    zone.style.removeProperty('display');
    zone.style.removeProperty('opacity');
    zone.style.removeProperty('pointer-events');
}

function _revealPillsOnScroll() {
    // Pills are always inline in the narrative panel — no scroll-based toggle.
    _inlinePillsLayout();
}

function initTurnLogUi() {
    const toggle = document.getElementById('turn-log-toggle');
    const shell = document.getElementById('turn-log-shell');
    const closeBtn = document.getElementById('turn-log-close');
    const backdrop = document.getElementById('turn-log-backdrop');
    const refreshBtn = document.getElementById('turn-log-refresh');
    if (!toggle || !shell) return;
    let loaded = false;
    function openShell() {
        shell.hidden = false;
        toggle.setAttribute('aria-expanded', 'true');
        if (!loaded && typeof htmx !== 'undefined') {
            loaded = true;
            htmx.ajax('GET', '/panels/turn-log?limit=50', { target: '#turn-log-body', swap: 'innerHTML' });
        }
    }
    function closeShell() {
        shell.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
    }
    toggle.addEventListener('click', () => {
        if (shell.hidden) openShell(); else closeShell();
    });
    closeBtn?.addEventListener('click', (ev) => { ev.stopPropagation(); closeShell(); });
    backdrop?.addEventListener('click', closeShell);
    refreshBtn?.addEventListener('click', (ev) => {
        ev.stopPropagation();
        if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', '/panels/turn-log?limit=50', { target: '#turn-log-body', swap: 'innerHTML' });
        }
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !shell.hidden) closeShell();
    });
}

function _renderNpcListItem(npc) {
    const name = npc.display_name || npc.name || npc.id || '?';
    const title = npc.title || '';
    const position = npc.position || '';
    const bio = npc.bio || '';
    const pl = npc.personality_label || '';
    const pt = npc.personality_traits || '';
    const mot = npc.motivation || '';
    const tie = (npc.tie_label || npc.tie || '');
    const hasTooltip = bio || pl || mot || tie;
    const color = npc.color || _npcColor(npc.id || name);
    const borderColor = npc.presence === 'nearby' ? 'var(--border-subtle)' : color;
    const nameHtml = title ? `${_escapeHtml(name)}<span class="npc-title"> — ${_escapeHtml(title)}</span>` : _escapeHtml(name);
    const posHtml = position ? `<span class="npc-position-inline">${_escapeHtml(position)}</span>` : '';
    let tipHtml = '';
    if (hasTooltip) {
        if (bio) tipHtml += `<p>${bio}</p>`;
        if (pl) tipHtml += `<p><strong>Personality:</strong> ${_escapeHtml(pl)}${pt ? ' — ' + _escapeHtml(pt) : ''}</p>`;
        if (mot) tipHtml += `<p><strong>Motivation:</strong> ${_escapeHtml(mot)}</p>`;
        if (tie) tipHtml += `<p><strong>Tie:</strong> ${_escapeHtml(tie)}</p>`;
    }
    return `<div class="npc-item${hasTooltip ? ' has-tooltip' : ''}" style="border-left-color:${borderColor}"><span class="npc-name-row"><span class="npc-name">${nameHtml}</span><span class="npc-party-toggle${npc.party ? ' active' : ''}" data-npc-id="${npc.id || ''}" data-party="${npc.party ? 'true' : 'false'}" onclick="toggleNpcParty('${npc.id || ''}')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span></span>${posHtml}${hasTooltip ? `<div class="tooltip-body" data-md-compendium>${tipHtml}</div>` : ''}</div>`;
}

function _renderInventoryItem(item) {
    if (!item) return '';
    const name = item.name || item.id || '?';
    const amt = item.amount || 1;
    const notes = item.notes || '';
    const cls = 'inventory-item' + (item.id === 'credits' ? ' inventory-item-credits' : '') + (notes ? ' has-tooltip has-tooltip-right' : '');
    const amtHtml = (amt > 1 || item.id === 'credits') ? ` <span class="inventory-item-amount">×${amt}</span>` : '';
    const tipHtml = notes ? `<div class="tooltip-body" data-md>${_escapeHtml(notes)}</div>` : '';
    const dropBtn = `<span class="inv-drop-btn" onclick="dropInventoryItem('${_escapeHtml(item.id)}', ${amt}, this)" title="Drop item"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></span>`;
    return `<div class="${cls}"><span class="inventory-item-name">${_escapeHtml(name)}${amtHtml}</span>${dropBtn}${tipHtml}</div>`;
}

function _renderConditionPill(cond) {
    if (!cond) return '';
    const label = cond.label || (typeof cond === 'string' ? cond : '');
    const desc = cond.description || '';
    const cls = 'condition-pill' + (desc ? ' has-tooltip' : '');
    const tipHtml = desc ? `<div class="tooltip-body">${_escapeHtml(desc)}</div>` : '';
    return `<span class="${cls}">${_escapeHtml(label)}${tipHtml}</span>`;
}

function toggleNpcParty(npcId) {
    fetch('/api/npc/' + npcId + '/toggle-party', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            const toggle = document.querySelector(`.npc-party-toggle[data-npc-id="${npcId}"]`);
            if (toggle) {
                const isParty = data.party;
                toggle.setAttribute('data-party', String(isParty));
                toggle.classList.toggle('active', isParty);
                toggle.style.color = isParty ? 'var(--accent-blue)' : '';
            }
        })
        .catch(err => {
            console.error('toggleNpcParty failed:', err);
        });
}

function dropInventoryItem(itemId, amount, el) {
    const modal = document.getElementById('drop-modal');
    const nameEl = document.getElementById('drop-modal-item-name');
    const qtyRow = document.getElementById('drop-modal-qty-row');
    const slider = document.getElementById('drop-modal-qty-slider');
    const qtyVal = document.getElementById('drop-modal-qty-val');
    if (!modal || !nameEl) return;

    const itemName = el?.closest?.('.inventory-item')?.querySelector('.inventory-item-name')?.textContent?.trim() || itemId;
    nameEl.textContent = itemName;

    if (amount <= 1) {
        qtyRow.style.display = 'none';
        slider.max = 1;
        slider.value = 1;
        qtyVal.textContent = '1';
    } else {
        qtyRow.style.display = 'flex';
        slider.min = 1;
        slider.max = amount;
        slider.value = amount;
        qtyVal.textContent = String(amount);
    }

    modal.hidden = false;
    modal._dropData = { itemId, maxAmount: amount };
}

function closeDropModal() {
    const modal = document.getElementById('drop-modal');
    if (modal) modal.hidden = true;
    if (modal?._dropData) delete modal._dropData;
}

function confirmDropModal() {
    const modal = document.getElementById('drop-modal');
    if (!modal?._dropData) return;
    const { itemId, maxAmount } = modal._dropData;
    const slider = document.getElementById('drop-modal-qty-slider');
    const amt = slider ? parseInt(slider.value, 10) : 1;
    if (isNaN(amt) || amt < 1 || amt > maxAmount) return;
    closeDropModal();
    _doDropItem(itemId, amt);
}

function _doDropItem(itemId, amount) {
    fetch('/api/inventory/drop', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({item_id: itemId, amount: amount}),
    })
        .then(r => r.json())
        .then(data => {
            if (data.inventory) {
                const panel = document.getElementById('card-inventory');
                if (panel) {
                    const body = panel.querySelector('.sidebar-card-body');
                    if (body) {
                        body.innerHTML = data.inventory.length
                            ? `<div class="inventory-drop-container">${data.inventory.map(item => _renderInventoryItem(item)).join('')}</div>`
                            : '<span class="empty-state">You aren\'t carrying anything!</span>';
                    }
                }
            }
        })
        .catch(err => {
            console.error('dropInventoryItem failed:', err);
        });
}
