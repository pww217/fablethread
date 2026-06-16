# EV Tooling Issues & Frustrations

**Date:** 2026-06-16 | **Context:** 5 evals, 100 turns, sequential execution

---

## 1. No parallel execution — no warning

Fired 5 `play --llm --turns 20` in parallel. All 5 returned immediately with `"(no output)"` and `"User aborted the command."` No error message, no indication of why. Had to edit `SKILL.md` to add the sequential constraint.

---

## 2. Logging `TypeError` crashes the formatter mid-run

`thread_same_turn_conflict` uses `%d` for `trace_id` which is a string. Spams `--- Logging error ---` tracebacks into the output stream, making it harder to parse what's actually happening.

---

## 3. Failures are silent

`extraction.state.empty` appears in the output but the turn continues normally — no `Errors:` line. `Fallback narrative` appears on turns 17-20 of Zombie but the turn header still says `Errors: none`. You have to read every line to spot the failures.

---

## 4. No progress indicator during a 20-turn run

Each turn takes ~30 seconds, so a 20-turn run is ~10 minutes with `--no-sanitize`. No ETA, no `"Turn 7/20"` counter in the output. You just wait.

---

## 5. `--eval` adds significant time at the end

After all 20 turns complete, checkers run on all turns before returning control. No progress indicator during this phase either.

---

## 6. Soft-check warnings have no severity signal

`generate_seed soft-check: Opening narrative 422 words (expected 530-930)` — is this a warning? A failure? The run continues regardless. No way to make it a hard failure.

---

## 7. Retry messages are interleaved with turn output

`extract_state parse failed (attempt 1/2)` and `extract_state parse failed (attempt 2/2)` appear in the stream but it's not immediately clear which turn they belong to — you have to correlate `trace_id` values.

---

## 8. No structured output

Everything is stdout/stderr mixed — turn output, checker output, logging errors, soft-checks, warnings. Hard to parse programmatically or filter.

---

## 9. No way to see prompts during the run

To debug what the LLM saw, you need to run `ev.py prompt N stream` commands afterward. No `--verbose-prompts` flag during `play`.

---

## 10. `--until-error` exists but errors are silent

Since `extraction.state.empty` and `Fallback narrative` don't set `Errors:` status, `--until-error` wouldn't catch them. The only things that trigger `--until-error` are actual Python exceptions.

---

## 11. `latest` symlink management is a known pitfall

Documented in README but worth noting — if `saves/ev/latest` breaks, `--resume` fails silently or with a confusing error.

---

## 12. No checkpoint/resume

If a 20-turn run crashes at turn 15, you lose everything. No `--resume-from N` flag.

---

## 13. `--no-sanitize` is necessary for speed but unsafe

Without it, turns take 5-10s longer each. But skipping sanitizer means thread state can drift. No middle ground.

---

## 14. `Fallback message stripped from narration` doesn't explain what was stripped

No indication of what the fallback narrative contains or why the original was rejected.

---
