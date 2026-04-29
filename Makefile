.PHONY: install run dev fmt lint test css clean new-game vendor ollama-launch ollama-env

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
	npx --yes @tailwindcss/cli -i ccya/static/app.src.css -o ccya/static/app.css --minify

new-game:
	uv run python -m ccya --new-game

vendor:
	mkdir -p ccya/static/vendor
	curl -sL "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js" -o ccya/static/vendor/htmx.min.js
	curl -sL "https://unpkg.com/alpinejs@3.14.8/dist/cdn.min.js" -o ccya/static/vendor/alpine.min.js

ollama-launch:
	bash scripts/ollama-launch.sh

ollama-env:
	@echo "# Paste into a shell or use launchctl setenv (see README), then restart Ollama.app if using the GUI."
	@echo "export OLLAMA_FLASH_ATTENTION=1"
	@echo "export OLLAMA_KV_CACHE_TYPE=q8_0"
	@echo "export OLLAMA_NUM_PARALLEL=1"
	@echo "export OLLAMA_MAX_LOADED_MODELS=1"
	@echo "export OLLAMA_KEEP_ALIVE=10m"
	@echo "export OLLAMA_MLX=1"
	@echo "# launchctl setenv OLLAMA_FLASH_ATTENTION 1"
	@echo "# launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0"
	@echo "# launchctl setenv OLLAMA_NUM_PARALLEL 1"
	@echo "# launchctl setenv OLLAMA_MAX_LOADED_MODELS 1"
	@echo "# launchctl setenv OLLAMA_KEEP_ALIVE 10m"
	@echo "# launchctl setenv OLLAMA_MLX 1"

clean:
	rm -rf .venv dist build *.egg-info __pycache__ .pytest_cache
