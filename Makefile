.PHONY: install run dev fmt lint test test-v test-x typecheck check css clean new-game vendor llama-swap eval eval-fast eval-judge-only eval-pack

install:
	uv sync

llama-swap:
	@bash scripts/infra/llama-swap.sh

run: llama-swap
	uv run ccya

dev: llama-swap
	.venv/bin/python -m uvicorn ccya.server:app --reload --host 0.0.0.0 --port 8765

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

typecheck:
	uv run mypy ccya

check: lint typecheck

css:
	npx --yes @tailwindcss/cli -i ccya/static/app.src.css -o ccya/static/app.css --minify

new-game:
	uv run python -m ccya --new-game

vendor:
	mkdir -p ccya/static/vendor
	curl -sL "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js" -o ccya/static/vendor/htmx.min.js
	curl -sL "https://unpkg.com/alpinejs@3.14.8/dist/cdn.min.js" -o ccya/static/vendor/alpine.min.js

clean:
	rm -rf .venv dist build *.egg-info __pycache__ .pytest_cache

eval: llama-swap
	uv run python -m ccya.eval run

eval-fast: llama-swap
	uv run python -m ccya.eval run --temp 0

eval-judge-only:
	@if [ -z "$(RUN)" ]; then echo 'Usage: make eval-judge-only RUN=evals/runs/<ts>'; exit 2; fi
	uv run python -m ccya.eval judge-only $(RUN)

eval-pack:
	uv run python -m ccya.eval pack
