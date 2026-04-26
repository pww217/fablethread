// ccya client-side JS — minimal, delegates to HTMX/Alpine
document.addEventListener('DOMContentLoaded', () => {
    // Focus input on load
    const input = document.getElementById('player-input');
    if (input) input.focus();
});
