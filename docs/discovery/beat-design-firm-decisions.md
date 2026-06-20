## Firm Decisions

**Beat generation stays inside storytell** — no new pipeline step now. Future split is anticipated but not designed for yet.

**`surface_as` is removed** — inferred from `intent`. The field and its validation, checker logic, and prompt warnings go away entirely.

**`intent` is a required field on every non-null beat** — a single concrete sentence describing what is about to happen. Not a category label. Must be tied to something ongoing (active thread or present NPC state) — no free-floating environmental events.

**NPC action is the primary beat driver** — present NPCs with motivation/fear/leverage are checked first. If an NPC has an obvious move given the current situation, that becomes the beat. Environmental/atmospheric beats are fallbacks only, and even then must be anchored to an active thread or NPC situation.

**`npc_id` + `driver` fields on the beat** — optional, but required when an NPC is the source. `driver` is one of `motivation | fear | leverage`. When set, tells the narrator exactly whose psychology is driving the action.

**No thread ID anchor required** — the connection to threads should be inferrable from `intent`. No mechanical coupling.

**Dice outcome does not gate beats** — the beat fires independent of this turn's outcome. Narrator handles feel.

**Null beats are allowed** — the storyteller should not be forced to emit a beat every turn. However, given LLM tendencies to always comply, the prompt needs explicit permission plus a meaningful bar: *only emit null if no NPC has a motivated move and no thread has a natural next action*.

**Two-section storytell prompt with two separate output fields** — `record` (thread/arc updates) and `beat` (world beat). Emitting two distinct JSON objects is acceptable and may ease future split. No other extractor does this currently — it's a deliberate structural choice to reduce cognitive conflation between record-keeper and game-master modes.

**NPC context passed to storytell for beat generation** — only present NPCs, only motivation/fear/leverage + name. Not full bio, personality archetype, or presence metadata. Keeps token cost minimal.

**Beat still has 2-turn TTL** — unchanged from current lifecycle.

***

## Open Questions

- **Null beat frequency in practice** — will the LLM actually emit null with reasonable frequency, or will prompt instruction alone be insufficient? May need recent-beat history as a nudge ("you have emitted a beat for 4 consecutive turns").
- **Does the narrator receive `npc_id` + `driver` explicitly, or just `intent`?** `intent` may be sufficient for narration; the structured fields are more useful for evals and future tooling. Worth deciding before implementation.
- **Temperature for beat section** — the record-keeper pass is analytic; the beat pass is generative. Should they run at different temperatures, or is a single temperature acceptable given they're in the same call?
- **How does the beat section handle scenes with no present NPCs at all?** Pure environmental fallback — what anchors it if there are no present NPCs and threads are all background urgency?

***

## Constraints

- Storytell context must not grow meaningfully — NPC fields for beat generation must replace or be additive to something already present, not pure addition
- Prompt must not conflate the two cognitive modes — structural separation in both input framing and output fields is the primary mitigation
- No new pipeline steps, no async work, no background execution in this phase
- No beat type → thread ID mechanical coupling
- `surface_as` removal must be clean — checker, validator, and prompt warnings all go

***

## Non-Goals

- Async / background beat generation
- Separate pipeline step for beat generation
- Per-NPC beat emission (one beat per turn, as now)
- Dice-outcome-gated beats
- Beat anchored to specific thread ID
- Changes to beat TTL or lifecycle mechanics
- Changes to narrator prompt structure (narrator receives `intent` the same way it currently receives beat type)
- Full NPC context in storytell (bio, archetype, full presence model)