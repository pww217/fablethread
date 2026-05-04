.PHONY: install run dev fmt lint test test-v test-x typecheck check css clean new-game vendor llama-swap

install:
	uv sync

llama-swap:
	@bash scripts/llama-swap.sh

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
