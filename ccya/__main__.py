"""CLI entry point for ccya."""

import argparse
import webbrowser

import uvicorn

from ccya.server import app, config, SAVE_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="ccya — LLM text adventure")
    parser.add_argument("--new-game", action="store_true", help="Start a new game from seed")
    parser.add_argument("--host", default=None, help="Bind host (overrides config)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (overrides config)")
    args = parser.parse_args()

    host = args.host or config["server"]["bind_host"]
    port = args.port or config["server"]["bind_port"]

    if args.new_game:
        import yaml
        from ccya.state import init_save_dir
        pack = config.get("game", {}).get("setting_pack", "hard-scifi-demo")
        seed_path = f"packs/{pack}/seed_state.yaml"
        with open(seed_path) as f:
            seed = yaml.safe_load(f) or {}
        init_save_dir(SAVE_DIR, seed)
        print(f"New game started in {SAVE_DIR}")

    # Start server and open browser
    import threading
    import time

    def open_browser() -> None:
        time.sleep(1.5)
        url = f"http://{host}:{port}/"
        print(f"\nOpening {url} in browser...")
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
