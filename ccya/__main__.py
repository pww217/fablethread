import argparse
import sys

import uvicorn

from ccya.cli import print_banner
from ccya.logging_setup import setup_logging
from ccya.server import app, config
from ccya.server.app import SAVE_DIR

setup_logging()


def main() -> None:
    parser = argparse.ArgumentParser(description="ccya — LLM text adventure")
    parser.add_argument(
        "--new-game", action="store_true", help="Start a new game from seed"
    )
    parser.add_argument("--host", default=None, help="Bind host (overrides config)")
    parser.add_argument(
        "--port", type=int, default=None, help="Bind port (overrides config)"
    )
    args = parser.parse_args()

    host = args.host or config["server"]["bind_host"]
    port = args.port or config["server"]["bind_port"]

    if args.new_game:
        import yaml
        from ccya.state import init_save_dir

        if SAVE_DIR is None:
            print("Error: save directory not configured", file=sys.stderr)
            sys.exit(1)
        pack = config.get("game", {}).get("setting_pack", "zombie-survival")
        seed_path = f"packs/{pack}/seed_state.yaml"
        with open(seed_path) as f:
            seed = yaml.safe_load(f) or {}
        init_save_dir(SAVE_DIR, seed)
        print(f"New game started in {SAVE_DIR}")

    print_banner(host, port)

    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
