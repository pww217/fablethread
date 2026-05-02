# Plan: Context Compaction Strategy

## Current State

Context is currently compacted on a fixed cadence (approx. every 4–6 turns via `window_turns`).
This works but has two problems:
1. Compaction may fire when context is still lean (wasted inference time)
2. Compaction may not fire when context is dense (accuracy degrades before the trigger)

---

## Proposed: Token-Threshold Compaction

### Trigger condition

After each turn, count the total tokens in the narrative history window being passed to
the narrator. If the count exceeds a configurable threshold, queue a compaction before the
next turn.

```python
COMPACTION_THRESHOLD_TOKENS = 3000  # tune empirically

def should_compact(recent_turns: list[dict], tokenizer) -> bool:
    total = sum(
        len(tokenizer.encode(t["narrative"])) + len(tokenizer.encode(t["input"]))
        for t in recent_turns
    )
    return total > COMPACTION_THRESHOLD_TOKENS
```

For MLX/local use, a rough character-based proxy avoids loading a separate tokenizer:
`total_chars = sum(len(t["narrative"]) + len(t["input"]) for t in recent_turns)`
with a chars-to-tokens ratio of ~3.5 for English prose. Threshold ~10,500 chars ≈ 3,000 tokens.

### When to compact

Compact **after** the current turn completes (state applied, narration shown) and **before**
the next turn's narrator call. Never compact mid-turn — the player should not notice latency
from compaction during a live turn.

A subtle "Compacting context..." indicator in the UI during the inter-turn window is acceptable.

### What compaction produces

The compaction call produces a structured summary replacing the turn window:
- Key events (3-5 bullet points)
- Active NPC attitudes at end of window
- Location at end of window
- Any unresolved threads or pending consequences

This summary is stored as a single synthetic "prior context" entry, distinct from live turns,
so the labeling scheme (`[PRIOR TURN SUMMARY]` vs `[CURRENT TURN NARRATION]`) still works.

---

## Context Block Labeling (Low-Effort, Ship First)

Regardless of compaction strategy, label context blocks explicitly in Python before building
the extract user message. The narrator already receives `recent_turns` with turn numbers;
the extractor should receive explicitly labeled sections.

In the Python code that builds the extract user context:

```python
def format_recent_turns(recent_turns: list[dict]) -> str:
    if not recent_turns:
        return ""
    parts = ["[PRIOR TURN CONTEXT]"]
    for t in recent_turns[:-1]:  # all but the most recent
        parts.append(f"Turn {t['turn']}: {t['input']}\n{t['narrative'][:400]}")
    parts.append("[CURRENT TURN NARRATION]")
    parts.append(recent_turns[-1]["narrative"])
    return "\n\n".join(parts)
```

This is a 10-line change with no prompt template edits required — the labels appear in the
rendered output naturally.

---

## Configuration

Add to `config.yaml`:

```yaml
context:
  compaction_threshold_tokens: 3000   # trigger compaction above this
  compaction_min_turns: 3             # never compact fewer than N turns (avoid thrashing)
  window_turns: 6                     # keep unchanged — used as max before forced compact
```

---

## Rollout Order

1. **Context block labeling** — pure Python change, no prompt edits, ship immediately
2. **Token-threshold check** — add `should_compact()` utility and wire into turn loop
3. **Compaction call** — if not already implemented, build the summarization prompt
4. **Config knobs** — expose threshold in `config.yaml`
