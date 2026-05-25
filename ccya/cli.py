"""Shared CLI utilities: hyperlink helper, startup banner."""

from __future__ import annotations

import sys

import uvicorn

from ccya.logging_setup import setup_logging

setup_logging()


def hyperlink(url: str, label: str | None = None) -> str:
    """Return a terminal hyperlink (OSC 8) or plain URL if not a TTY."""
    label = label or url
    if not sys.stdout.isatty():
        return url
    return f"\x1b]8;;{url}\x1b\\{label}\x1b]8;;\x1b\\"


def print_banner(host: str, port: int, extra: list[str] | None = None) -> None:
    """Print a clean startup banner with clickable link."""
    url = f"http://{host}:{port}/"
    link = hyperlink(url)
    print()
    print("  ccya \u2014 Choose Your Own Adventure")
    print(f"  {link}")
    if extra:
        for line in extra:
            print(f"  {line}")
    print()


def dev() -> None:
    """Run the server with hot-reload for development."""
    import argparse

    from ccya.server import config

    parser = argparse.ArgumentParser(description="ccya — LLM text adventure (dev)")
    parser.add_argument("--host", default=None, help="Bind host (overrides config)")
    parser.add_argument(
        "--port", type=int, default=None, help="Bind port (overrides config)"
    )
    args = parser.parse_args()

    host = args.host or config["server"]["bind_host"]
    port = args.port or config["server"]["bind_port"]
    print_banner(host, port, ["  hot-reload enabled"])
    uvicorn.run(
        "ccya.server:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["ccya"],
    )


if __name__ == "__main__":
    dev()
