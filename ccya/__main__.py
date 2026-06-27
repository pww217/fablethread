import argparse
import sys

import uvicorn

from ccya.cli import print_banner
from ccya.logging_setup import setup_logging
from ccya.server import app, config

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
        print("Error: --new-game requires a scenario.yaml pack. Static packs are no longer supported.", file=sys.stderr)
        sys.exit(1)

    print_banner(host, port)

    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
