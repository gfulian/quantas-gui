"""Production WSGI entry point for laboratory and server deployments."""

from __future__ import annotations

from quantas_gui.app import create_app
from quantas_gui.config import Settings
from quantas_gui.profile import ApplicationProfile

settings = Settings.from_environment(defaults=Settings.server_defaults()).with_overrides(
    mode="server",
    open_browser=False,
    debug=False,
)
app = create_app(settings, profile=ApplicationProfile.STANDARD)
server = app.server
