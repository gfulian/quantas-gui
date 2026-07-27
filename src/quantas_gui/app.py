"""Application factory for Quantas GUI."""

from __future__ import annotations

from pathlib import Path

import dash
from dash import Dash
from flask import jsonify

from quantas_gui.callbacks.navigation import register_navigation_callbacks
from quantas_gui.callbacks.results import register_result_callbacks
from quantas_gui.callbacks.settings import register_settings_callbacks
from quantas_gui.components.shell import build_shell
from quantas_gui.config import Settings
from quantas_gui.forms.callbacks import register_form_component_callbacks
from quantas_gui.pages import register_pages
from quantas_gui.services.application import AppServices, build_default_services
from quantas_gui.services.backend_info import detect_quantas_backend

_PACKAGE_ROOT = Path(__file__).resolve().parent


def create_app(
    settings: Settings | None = None,
    services: AppServices | None = None,
) -> Dash:
    """Create Quantas GUI without binding pages to a deployment backend.

    Parameters
    ----------
    settings
        Runtime settings. When omitted they are loaded from environment
        variables and safe local defaults.
    services
        Optional application-service graph. Tests and future server deployments
        may inject alternative result stores and execution backends.

    Returns
    -------
    dash.Dash
        Configured multipage application. Its Flask server is available as
        ``app.server`` for WSGI deployment.
    """
    resolved = settings or Settings.from_environment()
    resolved.prepare_workspace()
    app_services = services or build_default_services(resolved)

    # Dash keeps a process-global page registry. Clear only when constructing
    # the single application instance used by this process or by tests.
    dash.page_registry.clear()

    app = Dash(
        __name__,
        use_pages=True,
        pages_folder="",
        assets_folder=str(_PACKAGE_ROOT / "assets"),
        title="Quantas GUI",
        update_title="Quantas · working…",
        suppress_callback_exceptions=True,
        url_base_pathname=resolved.url_prefix,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
            {"name": "theme-color", "content": "#071522"},
            {
                "name": "description",
                "content": "Graphical interface for the Quantas scientific library",
            },
        ],
    )
    app.server.config["MAX_CONTENT_LENGTH"] = resolved.max_request_bytes
    app.server.config["QUANTAS_GUI_SETTINGS"] = resolved
    app.server.config["QUANTAS_GUI_SERVICES"] = app_services

    register_pages()

    def serve_layout():
        return build_shell(backend=detect_quantas_backend())

    app.layout = serve_layout
    register_navigation_callbacks(app)
    register_form_component_callbacks(app)
    register_result_callbacks(app, app_services.results)
    register_settings_callbacks(app)
    _register_health_endpoint(app, resolved)
    return app


def _register_health_endpoint(app: Dash, settings: Settings) -> None:
    prefix = settings.url_prefix.rstrip("/")
    route = f"{prefix}/healthz" if prefix else "/healthz"
    endpoint = f"quantas_gui_health_{abs(hash(route))}"

    @app.server.get(route, endpoint=endpoint)
    def health() -> tuple[object, int]:
        backend = detect_quantas_backend()
        payload = {
            "status": "ok",
            "mode": settings.mode,
            "backend_available": backend.available,
            "backend_version": backend.version,
        }
        return jsonify(payload), 200
