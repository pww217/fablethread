.PHONY: install run dev fmt lint test test-v test-x typecheck check deadcode css clean new-game roadmap vendor kill eval eval-fast eval-judge-only eval-pack eval-all full-eval clean-pycache

install:
	uv sync

kill:
	@lsof -ti:8765 2>/dev/null | xargs -r kill -9 && echo "killed server on 8765" || echo "no server on 8765"

clean-pycache:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

run:
	uv run ccya --host 0.0.0.0

dev:
	uv run python -m ccya.cli --host 0.0.0.0

fmt:
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest -q

test-v:
	uv run pytest

test-x:
	uv run pytest -x -v

test-integration:
	uv run pytest tests/integration -q

test-all: test test-integration

typecheck:
	uv run mypy ccya

lint-scripts:
	uv run ruff check scripts/

validate-packs:
	uv run python scripts/validate_pack_yamls.py

deadcode:
	uv run vulture ccya/ scripts/ --min-confidence 80

check: lint typecheck validate-packs deadcode

css:
	npx --yes @tailwindcss/cli -i ccya/static/app.src.css -o ccya/static/app.css --minify

new-game:
	uv run python -m ccya --new-game

roadmap:
	uv run python scripts/generate-roadmap.py $(ARGS)

vendor:
	mkdir -p ccya/static/vendor
	curl -sL "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js" -o ccya/static/vendor/htmx.min.js
	curl -sL "https://unpkg.com/alpinejs@3.14.8/dist/cdn.min.js" -o ccya/static/vendor/alpine.min.js

clean:
	rm -rf .venv dist build *.egg-info __pycache__ .pytest_cache

full-eval:
	bash scripts/eval/run-cycle.sh
