from __future__ import annotations

import socket

from quantas_gui.cli import build_parser, find_available_port


def test_parser_accepts_server_safe_options() -> None:
    args = build_parser().parse_args(
        ["--no-browser", "--port", "9000", "--url-prefix", "/quantas/"]
    )
    assert args.no_browser is True
    assert args.port == 9000
    assert args.url_prefix == "/quantas/"


def test_find_available_port_skips_occupied_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        occupied = sock.getsockname()[1]
        selected = find_available_port("127.0.0.1", occupied, attempts=2)
    assert selected == occupied + 1
