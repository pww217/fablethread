.PHONY: install run dev fmt lint test css clean new-game

install:
	uv sync

run:
	uv run ccya

dev:
	uv run uvicorn ccya.server:app --reload --host 127.0.0.1 --port 8765

fmt:
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest -q

css:
	./scripts/tailwindcss -i ccya/static/app.src.css -o ccya/static/app.css --minify

new-game:
	uv run python -m ccya --new-game

clean:
	rm -rf .venv dist build *.egg-info __pycache__ .pytest_cache
