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

    response = app.server.test_client().get("/healthz")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "local"


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
    layout_response = client.get("/quantas/_dash-layout")

    assert health_response.status_code == 200
    assert layout_response.status_code == 200
