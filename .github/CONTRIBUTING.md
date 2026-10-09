# Contributing

Thanks for your interest in Fablethread. This guide covers how to submit bugs, feature requests, and pull requests.

## License

Fablethread is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE). By contributing you agree your contributions are licensed under it and the project stays noncommercial. Commercial use requires a separate license from the copyright holder.

## Reporting bugs

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md). At minimum, include:

- **What you did** (steps to reproduce)
- **What happened** (actual behavior)
- **What you expected** (expected behavior)
- **Environment** (OS, Python version, LLM backend, model)
- **Logs** (relevant excerpts from `logs/game.log` or `logs/server.log`)

If you can reliably reproduce a bug, a minimal save directory (`saves/`) that triggers it is extremely helpful.

## Requesting features

Open an issue with a clear description of the problem you're trying to solve and your proposed solution.

## Pull requests

1. **Set up a dev environment:** `make install`
2. **Lint + typecheck:** `make check` (must pass)
3. **Write a clear PR title** — one line, imperative mood. Example: `fix: reject impossible inventory removals`
4. **Write a PR description** — use the [PR template](.github/PULL_REQUEST_TEMPLATE.md)
5. **Reference related issues** — `Closes #123` in the description

### Code standards

- Follow existing patterns. No new dependencies without discussion.
- Add docstrings to new public functions.
- No dead code. Delete unused fields, routes, config keys.
- If a change touches a module boundary, prompt, or config key, update the relevant `docs/architecture/` doc and `docs/repomap.md`.

### Workflow

1. Create a branch: `git worktree add -b <slug> ../fablethread-<slug> main`
2. Make changes, commit with a descriptive message.
3. Push and open a PR to `main`.
4. The PR title should be clear and descriptive (no ticket prefix — this repo doesn't use Linear).
