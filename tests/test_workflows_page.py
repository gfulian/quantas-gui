from __future__ import annotations

import pytest

pytest.importorskip("dash")

from dash import dcc
from dash._utils import to_json

from quantas_gui.pages.workflows import WORKFLOWS, layout
from quantas_gui.services.backend_info import REQUIRED_QUANTAS, BackendCompatibility


def _backend(
    *,
    workflow_missing: tuple[tuple[str, tuple[str, ...]], ...] = (),
) -> BackendCompatibility:
    return BackendCompatibility(
        available=True,
        compatible=True,
        version="2.0.0b7",
        required_version=REQUIRED_QUANTAS,
        missing_capabilities=(),
        detail="Public lifecycle API validated",
        workflow_missing=workflow_missing,
    )


def _link_hrefs(component: object) -> tuple[str, ...]:
    hrefs: list[str] = []
    if isinstance(component, dcc.Link):
        href = getattr(component, "href", None)
        if isinstance(href, str):
            hrefs.append(href)

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            hrefs.extend(_link_hrefs(child))
    elif children is not None:
        hrefs.extend(_link_hrefs(children))
    return tuple(hrefs)


def test_workflow_catalogue_distinguishes_gui_and_backend_availability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "quantas_gui.pages.workflows.dash.get_relative_path",
        lambda path: f"/quantas{path}",
    )
    page = layout(backend=_backend())
    payload = to_json(page)
    hrefs = _link_hrefs(page)

    assert len(WORKFLOWS) == 6
    for title in (
        "Elasticity",
        "SEISMIC",
        "Harmonic thermodynamics",
        "Quasi-harmonic approximation",
        "Thermoelasticity",
        "Equation of state",
    ):
        assert title in payload

    assert "Start workflow" in payload
    assert "/quantas/elasticity" in hrefs
    assert not any(href.rstrip("/").endswith("/seismic") for href in hrefs)
    assert "Next · 0.4" in payload
    assert "Elastic stiffness tensor in GPa and density" in payload
    assert "Native Quantas Elasticity HDF5" in payload
    assert "Native Quantas EOS archive" in payload


def test_elasticity_action_is_disabled_when_its_public_lifecycle_is_incomplete() -> None:
    page = layout(
        backend=_backend(
            workflow_missing=(("elasticity", ("run", "write_result")),),
        )
    )
    payload = to_json(page)
    hrefs = _link_hrefs(page)

    assert "Workflow unavailable" in payload
    assert "API incomplete" in payload
    assert "Missing public operations: run, write_result." in payload
    assert not any(href.rstrip("/").endswith("/elasticity") for href in hrefs)
