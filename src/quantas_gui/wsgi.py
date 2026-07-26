"""WSGI entry point for future server deployments."""

from __future__ import annotations

from quantas_gui.app import create_app
from quantas_gui.config import Settings

app = create_app(Settings.from_environment())
server = app.server
