from __future__ import annotations

from pathlib import Path

import pytest

dash = pytest.importorskip("dash")


def _application_types():
    """Import Dash-dependent objects after the module-level dependency gate."""
    from quantas_gui.app import create_app
    from quantas_gui.config import Settings

    return create_app, Settings


def test_app_factory_registers_pages_and_health_endpoint(tmp_path: Path) -> None:
    create_app, Settings = _application_types()
    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    app = create_app(settings)
    assert app.title == "Quantas GUI"
    assert app.server.config["MAX_CONTENT_LENGTH"] == settings.max_request_bytes
    paths = {page["path"] for page in dash.page_registry.values()}
    assert {
        "/",
        "/results",
        "/elasticity",
        "/seismic",
        "/qha",
        "/eos",
        "/settings",
    } <= paths
    assert "/ui-kit" not in paths

    client = app.server.test_client()
    response = client.get("/healthz")
    readiness = client.get("/readyz")
    assert response.status_code == 200
    assert readiness.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "local"
    assert payload["profile"] == "standard"
    assert payload["workspace_locking"] == "cross-process"
    assert payload["artifact_cache_scope"] == "process"


def test_dash_layout_endpoint_serializes_complete_shell(tmp_path: Path) -> None:
    """Catch invalid component properties before the browser sees the layout."""
    create_app, Settings = _application_types()
    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    app = create_app(settings)

    response = app.server.test_client().get("/_dash-layout")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["namespace"] == "dash_html_components"
    assert payload["type"] == "Div"


def test_prefixed_health_and_layout_endpoints(tmp_path: Path) -> None:
    create_app, Settings = _application_types()
    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        url_prefix="/quantas/",
        open_browser=False,
    )
    app = create_app(settings)
    client = app.server.test_client()

    health_response = client.get("/quantas/healthz")
    readiness_response = client.get("/quantas/readyz")
    layout_response = client.get("/quantas/_dash-layout")

    assert health_response.status_code == 200
    assert readiness_response.status_code == 200
    assert layout_response.status_code == 200


def test_ui_kit_profile_is_isolated_from_scientific_pages(tmp_path: Path) -> None:
    create_app, Settings = _application_types()
    from quantas_gui.profile import ApplicationProfile

    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    app = create_app(settings, profile=ApplicationProfile.UI_KIT)
    paths = {page["path"] for page in dash.page_registry.values()}
    assert paths == {"/", "/settings", "/about"}
    assert app.title == "Scientific UI Kit"

    client = app.server.test_client()
    payload = client.get("/healthz").get_json()
    assert client.get("/readyz").status_code == 200
    assert payload["profile"] == "ui-kit"
    assert payload["status"] == "ok"


def test_server_profile_applies_security_headers_and_proxy_configuration(tmp_path: Path) -> None:
    create_app, Settings = _application_types()
    settings = Settings.server_defaults().with_overrides(
        workspace_root=tmp_path,
        trusted_hosts=("localhost",),
        proxy_hops=1,
    )
    app = create_app(settings)
    response = app.server.test_client().get("/healthz", headers={"Host": "localhost"})
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert app.server.config["SESSION_COOKIE_SECURE"] is True


def test_degraded_backend_is_alive_but_not_ready(tmp_path: Path) -> None:
    create_app, Settings = _application_types()
    from quantas_gui.services.application import AppServices
    from quantas_gui.services.backend_info import REQUIRED_QUANTAS, BackendCompatibility
    from quantas_gui.services.backends import DisabledExecutionBackend
    from quantas_gui.services.cache import LocalArtifactCache
    from quantas_gui.services.result_backend import QuantasResultBackend
    from quantas_gui.services.results import ResultExplorerService
    from quantas_gui.services.workspaces import LocalWorkspaceStore

    settings = Settings.local_defaults().with_overrides(
        workspace_root=tmp_path,
        open_browser=False,
    )
    backend = BackendCompatibility(
        available=False,
        compatible=False,
        version=None,
        required_version=REQUIRED_QUANTAS,
        missing_capabilities=("quantas.api",),
        detail="Quantas is unavailable",
    )
    workspace = LocalWorkspaceStore(tmp_path)
    cache = LocalArtifactCache()
    results = ResultExplorerService(
        workspace_store=workspace,
        backend=QuantasResultBackend(),
        max_upload_bytes=settings.max_upload_bytes,
        compatibility=backend,
        cache=cache,
    )
    services = AppServices(
        backend=backend,
        workspace_store=workspace,
        artifact_cache=cache,
        execution=DisabledExecutionBackend(),
        results=results,
    )
    app = create_app(settings, services=services)
    client = app.server.test_client()

    assert client.get("/healthz").status_code == 200
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.get_json()["status"] == "degraded"
