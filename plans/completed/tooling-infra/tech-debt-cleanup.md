# Tech Debt Cleanup

## Status
`completed`

## Phases

3 phases: Remove `follow_imports = "skip"` from mypy config, clean up duplicate entries in pyproject.toml, and remove nested .venv directory.

## Issue

The project has accumulated three categories of tech debt that reduce type safety, create configuration noise, and risk confusion about which virtualenv is active. The most impactful is `follow_imports = "skip"` in mypy config (pyproject.toml:48), which silently disables all import resolution for third-party packages — meaning no type checking on FastAPI, Jinja2, Pydantic, OpenAI client, httpx, sse-starlette, Faker, or pykakasi. The workaround is six separate `disable_error_code` override sections that mask real issues rather than fixing them. Additionally, mypy appears twice in the dependency declarations and a nested `.venv/` exists inside `ccya/.venv`.

## Solution

Phase 01 removes `follow_imports = "skip"` from `[tool.mypy]`, then systematically reduces or eliminates each `disable_error_code` override by either adding proper type annotations to route handlers or confirming the overrides are no longer needed. Phase 02 deduplicates the mypy entry in pyproject.toml. Phase 03 removes the nested `ccya/.venv/` directory that was accidentally created inside the package source tree.

## Firm decisions

1. Keep strict mode enabled — do not relax other mypy settings.
2. Route handlers may remain untyped if FastAPI decorator typing proves problematic; suppress only with targeted overrides, not blanket ones.
3. `types-PyYAML` stubs are already installed and sufficient for yaml imports.
4. The pydantic mypy plugin (`plugins = ["pydantic.mypy"]`) should be retained — it provides validation beyond what inline annotations give us.

## Non-goals

- Adding type hints to all route handler parameters (only return types where needed).
- Migrating from `Any` usage in existing code.
- Upgrading or downgrading any third-party dependencies.
- Running tests (tests are temporarily removed during refactor per AGENTS.md).

## Risks, Ambiguities, and Blockers

1. FastAPI v2.x decorators may surface `untyped-decorator` errors on `@app.get`/`@post`. If so, the override for those modules stays but with fewer disabled codes.
2. OpenAI client's `chat.completions.create(**kwargs)` pattern uses `dict[str, Any]` which mypy strict may flag as incompatible with the actual `ChatCompletion` return type. May need a cast or local variable annotation.
3. Faker dynamic attribute access (`hasattr(faker, 'first_name_male')`) may surface `call-arg` errors if not handled carefully.
4. Running `make check` after each phase is essential to catch regressions early.

## Implementation — Phase 01: Remove follow_imports = "skip" and clean up mypy overrides

### Context files to load
- `/Users/pwilson/Repos/ccya/pyproject.toml` (mypy config)
- `/Users/pwilson/repos/ccya/ccya/server/app.py` (FastAPI app, middleware)
- `/Users/pwilson/repos/ccya/ccya/server/routes.py` (route handlers)
- `/Users/pwilson/repos/ccya/ccya/llm_client.py` (OpenAI client usage)
- `/Users/pwilson/repos/ccya/ccya/engine/names.py` (Faker/Kakasi usage)

### Detailed steps

#### Step 01.1 — Remove `follow_imports = "skip"` from mypy config

**File:** `pyproject.toml`

**What:** Delete the line `follow_imports = "skip"` from `[tool.mypy]`. This is a single-line removal at pyproject.toml:48.

**Why:** With all third-party packages shipping `py.typed`, there is no reason to skip import resolution. The six `disable_error_code` override sections exist as workarounds for this setting and will become unnecessary or reducible once imports are resolved.

**Validation:** Run `make typecheck`. Note any new errors — they indicate which overrides can be removed.

#### Step 01.2 — Fix OpenAI client typing in llm_client.py

**File:** `ccya/llm_client.py`

**What:** Find the `chat.completions.create(**kwargs)` call and add a local variable annotation for its return type using `from openai.types.chat import ChatCompletion`. Change from implicit `Any` to explicit `ChatCompletion` assignment. If kwargs is typed as `dict[str, Any]`, cast it or annotate the local binding explicitly.

**Why:** OpenAI's client methods accept keyword arguments that mypy strict mode may flag when passed via `**kwargs` with `Any`. Explicit typing prevents `arg-type` and `return-value` errors.

**Validation:** Confirmed by `make typecheck` passing without new errors in `ccya/llm_client.py`.

#### Step 01.3 — Fix Faker dynamic access in names.py

**File:** `ccya/engine/names.py`

**What:** Find any `hasattr(faker, name)` or `getattr(faker, name)` patterns and add a `# type: ignore[attr-defined]` comment inline where needed. Do not change the runtime behavior — this is purely to satisfy mypy strict mode on dynamic attribute access.

**Why:** Faker's methods are accessed dynamically by string name (e.g., `first_name_male`, `last_name_female`). Mypy cannot verify these exist at static analysis time. Inline `type: ignore` is appropriate here since the runtime behavior is correct and intentional.

**Validation:** Confirmed by `make typecheck` passing without new errors in `ccya/engine/names.py`.

#### Step 01.4 — Reduce or remove mypy override sections based on step 01.1 results

**File:** `pyproject.toml`

**What:** After running `make typecheck`, evaluate each disable_error_code section:
- If a module now passes without any disabled codes, delete that entire `[[tool.mypy.override]]` block.
- If only some codes are still needed (e.g., `untyped-decorator` remains but `no-untyped-def` no longer is), reduce the `disable_error_code` list to only what's actually needed.
- For `ccya.server`: if route handler return types cause errors, add explicit `-> ResponseType` annotations where practical; otherwise keep `untyped-decorator`, `no-untyped-def`, `return-value` suppressed but remove `attr-defined` and `no-any-return` if no longer triggered.
- For `ccya.models` and `ccya.pack`: these are well-typed Pydantic models — the `untyped-decorator` disable should be removable since pydantic v2 decorators are typed.

**Why:** The override sections exist solely because `follow_imports = "skip"` made imports opaque. Once imports resolve, most overrides become unnecessary noise that hides real issues.

**Validation:** Run `make typecheck`. Zero new errors compared to the baseline after step 01.1. Then run `make check` for full lint+typecheck pass.

### Tests to write or update
None — tests are temporarily removed during refactor per AGENTS.md.

### REPOMAP updates required
- If any module gains type annotations that change its public API surface, note in the repomap. Otherwise no changes needed since this is purely config cleanup.

## Implementation — Phase 02: Deduplicate mypy entry in pyproject.toml

### Context files to load
- `/Users/pwilson/Repos/ccya/pyproject.toml`

### Detailed steps

#### Step 02.1 — Remove duplicate `mypy` from `[dependency-groups.dev]`

**File:** `pyproject.toml`

**What:** Find the `mypy>=1.20.2` entry in `[dependency-groups.dev]` (line ~76) and remove it. The same package already exists in `[project.optional-dependencies.dev]` at line 27 as just `"mypy"`. Keep only the one in optional-dependencies.

**Why:** Duplicate entries create confusion about which is authoritative, may cause lock file conflicts between `pip install -e .[dev]` and `uv sync --group dev`, and violate the "one source of truth per concept" rule from AGENTS.md.

**Validation:** Run `make typecheck` to confirm mypy still works after removing the duplicate. Also run `grep -n "mypy" pyproject.toml` to verify only one entry remains.

### Tests to write or update
None — tests are temporarily removed during refactor per AGENTS.md.

### REPOMAP updates required
No changes needed. This is a config-only change with no impact on module boundaries or public APIs.

## Implementation — Phase 03: Remove nested .venv directory

### Context files to load
- `/Users/pwilson/Repos/ccya/.gitignore` (to confirm `.venv/` is already ignored at root level)

### Detailed steps

#### Step 03.1 — Delete `ccya/.venv/` directory

**File:** `ccya/.venv/` (entire directory)

**What:** Remove the nested virtualenv at `/Users/pwilson/repos/ccya/ccya/.venv/`. The root-level `.gitignore` already ignores all `.venv/` directories, so this nested one was never tracked in git. It is an accidental artifact from running `uv venv` or similar inside the package directory.

**Why:** Having two virtualenvs (one at project root, one nested) causes confusion about which Python environment tools use. The nested one serves no purpose — all tooling runs from the project-level `.venv/`. Removing it also cleans up ~256 bytes of filesystem noise and prevents future developers from accidentally activating the wrong env.

**Validation:** Run `which python` and `python -c "import sys; print(sys.prefix)"` to confirm the active venv is still at the root level after removal. Also run `make check` to verify tooling works with the remaining .venv.

### Tests to write or update
None — tests are temporarily removed during refactor per AGENTS.md.

### REPOMAP updates required
No changes needed. This is a filesystem cleanup operation only.
