.PHONY: install run dev fmt lint test test-v test-x typecheck check css clean new-game vendor llama-swap eval eval-fast eval-judge-only eval-pack eval-all full-eval

install:
	uv sync

llama-swap:
	@bash scripts/infra/llama-swap.sh

run: llama-swap
	uv run ccya --host 0.0.0.0

dev: llama-swap
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

check: lint typecheck validate-packs

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
	@if [ -n "$(JUDGE)" ]; then \
		JUDGE_ARGS=""; \
		for j in $(JUDGE); do JUDGE_ARGS="$$JUDGE_ARGS --judge $$j"; done; \
		uv run python -m ccya.eval run $$JUDGE_ARGS; \
	else \
		uv run python -m ccya.eval run; \
	fi

eval-fast: llama-swap
	@if [ -n "$(JUDGE)" ]; then \
		JUDGE_ARGS=""; \
		for j in $(JUDGE); do JUDGE_ARGS="$$JUDGE_ARGS --judge $$j"; done; \
		uv run python -m ccya.eval run --temp 0 $$JUDGE_ARGS; \
	else \
		uv run python -m ccya.eval run --temp 0; \
	fi

eval-judge-only:
	@if [ -z "$(RUN)" ]; then echo 'Usage: make eval-judge-only RUN=evals/runs/<ts>'; exit 2; fi
	@if [ -n "$(JUDGE)" ]; then \
		JUDGE_ARGS=""; \
		for j in $(JUDGE); do JUDGE_ARGS="$$JUDGE_ARGS --judge $$j"; done; \
		uv run python -m ccya.eval judge-only $(RUN) $$JUDGE_ARGS; \
	else \
		uv run python -m ccya.eval judge-only $(RUN); \
	fi

eval-pack:
	uv run python -m ccya.eval pack

eval-all: llama-swap
	uv run python -m ccya.eval run --all

full-eval: llama-swap
	bash scripts/eval/run-cycle.sh
