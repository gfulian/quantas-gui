"""Local command-line launcher for Quantas GUI."""

from __future__ import annotations

import argparse
import socket
from threading import Timer
import webbrowser

from quantas_gui.config import Settings


def build_parser() -> argparse.ArgumentParser:
    """Create the local launcher argument parser."""
    parser = argparse.ArgumentParser(
        prog="quantas-gui",
        description="Start the Quantas graphical interface.",
    )
    parser.add_argument("--host", help="Listening interface (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, help="Preferred TCP port (default: 8050).")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the default browser automatically.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Dash development tools. Never use this on a public server.",
    )
    parser.add_argument(
        "--url-prefix",
        help="Mount the app below a URL prefix, for example /quantas/.",
    )
    return parser


def find_available_port(host: str, preferred: int, *, attempts: int = 50) -> int:
    """Return the first available port at or above ``preferred``."""
    for port in range(preferred, preferred + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No available port found from {preferred} to {preferred + attempts - 1}")


def main(argv: list[str] | None = None) -> int:
    """Start the safe local server and optionally open a browser."""
    args = build_parser().parse_args(argv)
    settings = Settings.from_environment()
    changes: dict[str, object] = {}
    if args.host is not None:
        changes["host"] = args.host
    if args.port is not None:
        changes["port"] = args.port
    if args.url_prefix is not None:
        changes["url_prefix"] = args.url_prefix
    if args.no_browser:
        changes["open_browser"] = False
    if args.debug:
        changes["debug"] = True
    settings = settings.with_overrides(**changes)
    settings = settings.with_overrides(
        port=find_available_port(settings.host, settings.port)
    )

    from quantas_gui.app import create_app

    app = create_app(settings)
    url = f"http://{settings.host}:{settings.port}{settings.url_prefix}"
    if settings.open_browser:
        timer = Timer(0.8, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    print(f"Quantas GUI: {url}")
    print(f"Workspace: {settings.workspace_root}")
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        use_reloader=settings.debug,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
