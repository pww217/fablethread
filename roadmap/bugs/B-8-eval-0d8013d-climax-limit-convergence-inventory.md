---
title: Eval 0d8013d — CLIMAX hardcoded limit, convergence score, inventory canonical IDs, ruling JSON parse warnings
status: done
created: 2026-06-27
ticket_id: B-8
labels:
  - eval
  - engine
  - pacing
  - inventory
  - tv
---
3-run eval at 0d8013d (noir-1930s/driven, allied-ww2/aggressive, zombie-survival/cautious, 15 turns each). Rubric: 92%, 92%, 96%.

## 1. CLIMAX hardcoded `>= 4` instead of `config.climax_turn_limit`
- **Runs affected:** noir (turn 8), zombie (turn 7)
- **Issue:** `_pacing.py:219` hardcodes `climax_turn_count >= 4`. Works for default config (limit=4) but breaks if a pack overrides `climax_turn_limit`.
- **Fix:** Change `>= 4` to `>= config.climax_turn_limit`.

## 2. Convergence score: all 6 components weighted at 1, threshold 3
- **Runs affected:** noir (turns 5, 15), allied (turn 11)
- **Issue:** RISING→CLIMAX firing at score 2 when threshold is 3. All 6 components (`urgent_thread`, `threat_thread`, `scene_age`, `beat_streak`, `roll_starvation`, `threat_density`) are binary 0/1, threshold=3.
- **Root cause:** Equal weight for all components, but urgency should matter more. With 6 binary components, threshold 3 is a hard midpoint — easy to hit or miss.
- **Fix:** Weighted binary — `urgent_thread: 2`, rest: 1 each. Total: 7, threshold: 4. Smallest change, urgency gets double-weight matching system intent.

## 3. Inventory canonical ID resolution failing for pack-specific items
- **Runs affected:** All 3 runs
- **Issue:** `resolve_inventory_canonical_id no match` for LLM-extracted items that don't match canonical IDs.
- **Items:** case_dismissal_files, arrest_files, leather_bound_ledger (noir); small_arms_ammo/ammunition, heavy_pistol (allied); mandatory_decon/decontamination (zombie)
- **Impact:** `small_arms_ammo` and `small_arms_ammunition` both appear in allied final state as separate entries instead of merging into `pistol_rounds`.
- **Root cause:** LLM extracts items using natural language names that don't match canonical IDs. Aliases exist in code but are never populated by the LLM.
- **Fix:** Tighten state extraction prompt to require canonical inventory IDs (e.g., "Use canonical item IDs: pistol_rounds, not small_arms_ammo or small_arms_ammunition").

## 4. TV viewer JSON parse warnings from markdown code fences in ruling output
- **Runs affected:** allied-ww2 (turns 5, 6, 7, 10, 13, 15 — 8 occurrences)
- **Error:** `[WARNING] _extract_stream_output_lines JSON parse failed:`
- **Root cause:** LLM wraps ruling JSON in markdown code fences (` ```json\n{...}\n``` `) — `json.loads()` in `tv.py:86` can't parse that. Also occasional empty ruling outputs (`''`).
- **Fix:** Strip code fences before `json.loads()` in `_extract_stream_output_lines`:
  ```python
  text = raw_out.strip()
  if text.startswith("```"):
      text = re.sub(r"^```(?:json)?\s*", "", text).rsplit("\n```", 1)[0].strip()
  parsed = _json.loads(text)
  ```
