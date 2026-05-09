# ccya eval harness

## Adding a custom eval pack

The eval harness searches for packs in the directories listed under `pack_dirs:`
in `evals/config.yaml`. Default order:

1. `evals/packs/`
2. `packs/default/`
3. `packs/custom/`

To add a custom pack:

1. Create a folder under any search dir, e.g. `packs/custom/grimdark-noir/`.
2. Populate it with `pack.yaml`, `seed_state.yaml` (REQUIRED — eval only supports
   static packs), `style.md`, `scenario.yaml` (optional — for narrator_rules /
   factions / locations), and `extract_examples.yaml` (optional).
3. Reference it in a scenario: set `pack="grimdark-noir"` on the `Scenario(...)`
   call in `evals/scenarios/<your_scenario>.py`. The harness picks up the first
   match in the search order.

To run only that scenario: `make eval` after setting `default_scenario:` in
`evals/config.yaml`, OR `uv run python -m ccya.eval run <your_scenario>`.

To run every discovered scenario: `make eval-all` (see below).
