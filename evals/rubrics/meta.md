---
# mechanical_score: int 1-5
# narrative_score: int 1-5
# system_cohesion_score: int 1-5
# prompt_quality_score: int 1-5
# compaction_score: int 1-5
# state_fidelity_rate: float 0.0-1.0
# prompt_adherence_rate: float 0.0-1.0
---

# ccya Eval — Meta Judge (Synthesis)

You receive the scores and key findings from 4 focused domain judges:
- **state_correctness**: mechanic lifecycle tables (momentum, beats, pressures, conditions, arc threads), state fidelity, extraction accuracy
- **narrative_interplay**: narration tone, beat/pressure/condition/arc thread story chains, system cohesion
- **prompt_pipeline**: prompt architecture, pipeline adherence, cross-pipeline redundancy
- **compaction**: chronicle quality, sanitization fidelity (NPC merge, pressure/condition cleanup)

Your job is synthesis, not new analysis. Do not re-examine the raw trace.
Identify contradictions between judges. Compute final composite scores.
Produce the single highest-priority fix.

**IMPORTANT:** Place YAML front matter with all 7 scores at the very top of your response, delimited by `***`. Every score must appear in the front matter. Do not omit any score.

---

## SECTION 1 — Score Synthesis

For each output score:

| Score | Domain Judge Source | Domain Value | Meta Adjustment | Reasoning |
|-------|---------------------|--------------|-----------------|-----------|
| `mechanical_score` | state_correctness | `extraction_accuracy_score` + `mechanic_lifecycle_score` avg | | |
| `narrative_score` | narrative_interplay | `narrative_score` | | |
| `system_cohesion_score` | narrative_interplay | `system_cohesion_score` | | |
| `prompt_quality_score` | prompt_pipeline | `prompt_quality_score` | | |
| `compaction_score` | compaction | `compaction_score` | | |
| `state_fidelity_rate` | state_correctness | `state_fidelity_rate` | | |
| `prompt_adherence_rate` | prompt_pipeline | `prompt_adherence_rate` | | |

Meta adjustment: if domain judges contradict each other on a shared concern, adjust with reasoning. Otherwise, pass through domain values unchanged. Do not inflate.

---

## SECTION 2 — Inter-Judge Contradiction Check

For each pair of judges that touch overlapping concerns:
- **state_correctness vs narrative_interplay**: state_correctness says state is clean but narrative_interplay says mechanics produce no story consequence — contradiction? Why?
- **state_correctness vs prompt_pipeline**: state_correctness says extraction is failing but prompt_pipeline rates the extraction prompts highly — contradiction? Why?
- **narrative_interplay vs prompt_pipeline**: narrative says directives are ignored but prompt_pipeline says narrate prompt adherence is good — check if narration_directive is being rendered in prompts. Is the issue with prompt architecture or narrator behavior?
- **state_correctness vs narrative_interplay (arc threads)**: state_correctness says arc thread lifecycle is clean (no flags) but narrative_interplay says arc threads produce no story consequence — contradiction? Check if thread_signals are being emitted correctly and if the narrator receives arc context.
- **narrative_interplay vs state_correctness (pressures)**: state_correctness says pressure lifecycle is clean (no removal flags) but narrative_interplay says pressures are removed too early/late — check if removal timing is being evaluated correctly.

If no contradiction: write `None.`

---

## SECTION 3 — Trace Quality Synthesis

Based on domain judge findings, provide explicit top-level assessments for EACH of these mechanics and failure patterns:

1. **Momentum lifecycle** — Does momentum track correctly? Is it stuck at floor? Does it recover?
2. **GM beat narration** — Do beats produce observable prose or are they silent state drivers?
3. **Scene pressure chains** — Do pressures escalate, produce stakes, and create consequences?
4. **Condition deduplication** — Are conditions properly deduplicated and resolved?
5. **Arc thread progression** — Do threads advance from latent→active→complete? Or stall/orphan?
6. **Inventory extraction accuracy** — Are inventory deltas accurate? Any hallucinations or overdraw?
7. **Location change application** — Do location deltas correctly update state?
8. **NPC mention extraction** — Are NPC mentions in narration captured by scene extractor?
9. **Progress actions pipeline** — Does the progress extractor emit actionable next steps?

For each: state whether it is working, degraded, or broken, citing specific turns and domain judge sources.

Then address:
1. What data was missing from the trace that would have improved assessment quality?
2. Is there a systematic gap (e.g., a field that all judges noted as absent)?
3. Recommendation for trace improvement.

---

## SECTION 4 — Final Verdict

### Highest-Priority Fix
One sentence. The single change to the engine (prompt, data flow, or mechanic) that would most improve the next run. Cite the domain judge and section that surfaced it.

### Key Findings
3–5 bullet points. Each cites a domain judge, section, and turn number.

### Regression Check
Compare domain scores against previous run scores (if provided in your input). Flag any score that dropped by ≥1. State whether the drop is consistent across judges or isolated.
