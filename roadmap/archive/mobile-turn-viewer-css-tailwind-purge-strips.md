---
title: "[EV] Mobile Turn Viewer CSS Tailwind purge strips custom selectors"
status: canceled
urgency: 4
size: small
created: 2026-06-11
labels:
  - Bug
  - Tooling
  - UI
---

```
Status: Confirmed — all 178 tv-* classes stripped from app.css by Tailwind v4 purge. Turn viewer layout completely broken.

Recommendation: Separate static CSS file (ccya/static/tv.css) with all tv-* classes, served alongside app.css via link tag in _turn_viewer.html. Bypasses Tailwind processing entirely.

Eval: Not applicable to eval runs (UI-only bug).
```
