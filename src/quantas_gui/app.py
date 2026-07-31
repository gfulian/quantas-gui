"""Application factory for Quantas GUI."""

from __future__ import annotations

from pathlib import Path

import dash
import dash_ag_grid as dag
from dash import Dash
from flask import jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from quantas_gui.callbacks.navigation import register_navigation_callbacks
from quantas_gui.callbacks.results import register_result_callbacks
from quantas_gui.callbacks.settings import register_settings_callbacks
from quantas_gui.components.shell import build_shell
from quantas_gui.config import Settings
from quantas_gui.forms.callbacks import register_form_component_callbacks
from quantas_gui.pages import register_pages
from quantas_gui.profile import ApplicationProfile
from quantas_gui.services.application import AppServices, build_default_services
from quantas_gui.workflows.elasticity.callbacks import register_elasticity_callbacks
from quantas_gui.workflows.elasticity.service import ElasticityWorkflowService

_PACKAGE_ROOT = Path(__file__).resolve().parent


def create_app(
    settings: Settings | None = None,
    services: AppServices | None = None,
    *,
    profile: ApplicationProfile = ApplicationProfile.STANDARD,
) -> Dash:
    """Create a profile-specific Dash application without starting a server.

    The standard profile exposes Quantas GUI. The ``ui-kit`` profile exposes
    only the developer component gallery, Settings, and About; it is selected by
    ``quantas-gui --ui-kit`` and is absent from normal navigation and WSGI
    deployments.
    """
    resolved = settings or Settings.from_environment()
    resolved.prepare_workspace()
    app_services = services or build_default_services(resolved)

    # Dash keeps a process-global page registry. Clear it before registering the
    # one application profile hosted by this process.
    dash.page_registry.clear()

    app = Dash(
        __name__,
        use_pages=True,
        pages_folder="",
        assets_folder=str(_PACKAGE_ROOT / "assets"),
        external_stylesheets=[dag.themes.BASE, dag.themes.QUARTZ],
        title=profile.application_title,
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
    _configure_flask(app, resolved)
    app.server.config["QUANTAS_GUI_SETTINGS"] = resolved
    app.server.config["QUANTAS_GUI_SERVICES"] = app_services
    app.server.config["QUANTAS_GUI_PROFILE"] = profile.value

    register_pages(
        app_services.backend,
        execution=app_services.execution.descriptor,
        profile=profile,
    )

    def serve_layout():
        return build_shell(backend=app_services.backend, profile=profile)

    app.layout = serve_layout
    register_navigation_callbacks(app, profile=profile)
    register_form_component_callbacks(app)
    if profile is ApplicationProfile.STANDARD:
        register_result_callbacks(app, app_services.results)
        register_elasticity_callbacks(
            app,
            ElasticityWorkflowService(
                workspace_store=app_services.workspace_store,
                execution=app_services.execution,
                results=app_services.results,
                max_upload_bytes=resolved.max_upload_bytes,
            ),
        )
    register_settings_callbacks(app)
    _register_health_endpoints(app, resolved, app_services, profile=profile)
    _register_security_headers(app)
    return app


def _configure_flask(app: Dash, settings: Settings) -> None:
    app.server.config["MAX_CONTENT_LENGTH"] = settings.max_request_bytes
    app.server.config["SESSION_COOKIE_HTTPONLY"] = True
    app.server.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.server.config["SESSION_COOKIE_SECURE"] = settings.secure_cookies
    if settings.trusted_hosts:
        app.server.config["TRUSTED_HOSTS"] = list(settings.trusted_hosts)
    if settings.proxy_hops:
        app.server.wsgi_app = ProxyFix(
            app.server.wsgi_app,
            x_for=settings.proxy_hops,
            x_proto=settings.proxy_hops,
            x_host=settings.proxy_hops,
            x_port=settings.proxy_hops,
            x_prefix=settings.proxy_hops,
        )


def _register_health_endpoints(
    app: Dash,
    settings: Settings,
    services: AppServices,
    *,
    profile: ApplicationProfile,
) -> None:
    prefix = settings.url_prefix.rstrip("/")
    health_route = f"{prefix}/healthz" if prefix else "/healthz"
    ready_route = f"{prefix}/readyz" if prefix else "/readyz"
    endpoint_seed = abs(hash((health_route, profile.value)))

    def payload() -> tuple[dict[str, object], bool]:
        backend = services.backend
        execution = services.execution.descriptor
        application_ready = profile is ApplicationProfile.UI_KIT or backend.ready
        body: dict[str, object] = {
            "status": "ok" if application_ready else "degraded",
            "mode": settings.mode,
            "profile": profile.value,
            "backend_available": backend.available,
            "backend_version": backend.version,
            "backend_compatible": backend.compatible,
            "backend_required": backend.required_version,
            "missing_capabilities": list(backend.missing_capabilities),
            "workflow_readiness": {
                module: backend.workflow_ready(module)
                for module in (
                    "elasticity",
                    "seismic",
                    "ha",
                    "qha",
                    "thermoelasticity",
                )
            },
            "workspace_store": type(services.workspace_store).__name__,
            "workspace_locking": "cross-process",
            "artifact_cache": type(services.artifact_cache).__name__,
            "artifact_cache_scope": "process",
            "execution_backend": execution.kind,
            "execution_available": execution.available,
            "execution_process_shared": execution.process_shared,
        }
        return body, application_ready

    @app.server.get(health_route, endpoint=f"quantas_gui_health_{endpoint_seed}")
    def health() -> tuple[object, int]:
        body, _ = payload()
        return jsonify(body), 200

    @app.server.get(ready_route, endpoint=f"quantas_gui_ready_{endpoint_seed}")
    def readiness() -> tuple[object, int]:
        body, application_ready = payload()
        return jsonify(body), 200 if application_ready else 503


def _register_security_headers(app: Dash) -> None:
    @app.server.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        )
        return response
