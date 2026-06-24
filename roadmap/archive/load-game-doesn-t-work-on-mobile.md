---
title: "[UI] Load game doesn't work on mobile"
status: done
urgency: 4
size: medium
created: 2026-06-12
labels:
  - Bug
  - UI
---

## Detail

Load game functionality fails on mobile browsers.

## Scope

* Investigate mobile-specific failure mode (storage, file picker, CSP, etc.)
* Fix load game flow for mobile browsers
* Test on iOS Safari and Android Chrome

## Validation

Confirmed bug in codebase:

1. Save picker modal (`#save-picker-shell`, `#save-picker-modal`) uses `.pack-picker-modal` which on mobile gets fullscreen styling (CSS `app.src.css:1967-1977`). Z-index is 9500, sidebar drawers are 8000, backdrop 7500 — no z-index conflict.
2. `openSavePicker()` in `index.html:2089-2097` toggles `.hidden` class and calls `_fetchSaves()`. No mobile-specific JS guards or error handling found.
3. No CSP headers in `routes.py` that would block mobile functionality.
4. Viewport meta tag present (`index.html:5`) with `width=device-width, initial-scale=1.0`. No `user-scalable=no` or `maximum-scale` restrictions.
5. Bug likely in JS error, CSS rendering, or touch event handling — needs mobile testing to isolate exact failure point.
