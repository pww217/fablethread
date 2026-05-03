# LLM Pipeline Accuracy — Checklist

Full implementation details: [llm-pipeline-accuracy.md](./llm-pipeline-accuracy.md)

> Plans B / C / D / E are complete and archived in `plans/completed/`. Plans A and F remain.

---

## A — Context Block Labeling
*Template changes only. Zero latency impact. Fixes narration continuity and stale-fact extraction.*

- [ ] Add `## PRIOR HISTORY` / `## END PRIOR HISTORY` wrapper to `_chronicle.j2`
- [ ] Add `## RECENT TURNS` / `## END RECENT TURNS` header to `_recent.j2`
- [ ] Add `## CURRENT TURN NARRATION` label in `extract_user.j2` around narration input

---

## F — Compaction Redesign
*New prompt files + Python logic. Fixes fixed-cadence compaction. See also `compaction-strategy.md`.*

- [ ] Replace fixed turn-count trigger with token-threshold check in Python engine
- [ ] Create `ccya/prompts/compact_system.j2` (preserve/discard rules + output schema)
- [ ] Create `ccya/prompts/compact_user.j2` (inventory + established_facts + recent turns input)
- [ ] Update Python engine: archive recent_turns to chronicle, clear recent_turns, merge new_facts
- [ ] Ensure `_chronicle.j2` renders chronicle entries with `PRIOR HISTORY` label (Plan A)
