---
title: "[UI] Purple highlighting too intense in delta/summary"
status: done
created: 2026-06-12
labels:
  - Improvement
  - UI
---

## Detail

Delta summary and thread summary use dark purple and deep purple highlighting that's visually overwhelming.

## Scope

* Reduce contrast/vibrancy of purple highlighting in delta summary
* Reduce contrast/vibrancy of purple in thread summary
* Consider brighter alternatives or softer shades
* Test readability at various screen brightness levels

## Files

* `ccya/static/app.src.css` — styling for `tc-inv-gain`, `tc-inv-loss`, `tc-th-added`, `tc-th-resolved`, etc.
* `ccya/templates/` — chronicle and narrative templates using these classes

## Validation

Confirmed bug in codebase:

Thread change line colors in `app.src.css:975-980`:

| Class | Current Color | Issue |
| -- | -- | -- |
| `tc-th-added` | `#d8b4fe` | light purple, moderate |
| `tc-th-updated` | `#c084fc` | medium purple, saturated |
| `tc-th-resolved` | `#9333ea` | dark purple, very intense |
| `tc-th-failed` | `#7e22ea` | dark purple, very intense |
| `tc-th-abandoned` | `#6b21ea` | very dark purple, intense |
| `tc-th-removed` | `#581c87` | very dark purple, intense |

Used in both server-rendered delta (`index.html:210-217`) and JS-rendered delta (`index.html:569-590`). The dark/deep purples (`#9333ea`, `#7e22ea`, `#6b21ea`, `#581c87`) are high-contrast, saturated, and visually overwhelming — especially on bright screens.
