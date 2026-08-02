from __future__ import annotations

import pytest

pytest.importorskip("dash")

from dash import dcc, html
from dash._utils import to_json

from quantas_gui.pages.workflows import WORKFLOWS, layout
from quantas_gui.services.backend_info import REQUIRED_QUANTAS, BackendCompatibility


@pytest.fixture(autouse=True)
def _prefix_aware_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "quantas_gui.pages.workflows.dash.get_relative_path",
        lambda path: f"/quantas{path}",
    )


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


def _child_text(component: object) -> tuple[str, ...]:
    if isinstance(component, str):
        return (component,)

    values: list[str] = []
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            values.extend(_child_text(child))
    elif children is not None:
        values.extend(_child_text(children))
    return tuple(values)


def _card_by_title(component: object, title: str) -> html.Article:
    if isinstance(component, html.Article) and title in _child_text(component):
        return component

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            try:
                return _card_by_title(child, title)
            except LookupError:
                continue
    elif children is not None:
        return _card_by_title(children, title)
    raise LookupError(f"workflow card not found: {title}")


def test_workflow_catalogue_distinguishes_gui_and_backend_availability() -> None:
    page = layout(backend=_backend())
    hrefs = _link_hrefs(page)
    text_values = _child_text(page)

    assert len(WORKFLOWS) == 6
    for title in (
        "Elasticity",
        "SEISMIC",
        "Harmonic thermodynamics",
        "Quasi-harmonic approximation",
        "Thermoelasticity",
        "Equation of state",
    ):
        assert title in text_values

    assert "Start workflow" in text_values
    assert "/quantas/elasticity" in hrefs
    assert "/quantas/seismic" in hrefs

    seismic_text = _child_text(_card_by_title(page, "SEISMIC"))
    assert "Available" in seismic_text
    assert "Milestone 0.4" in seismic_text
    assert "Elastic stiffness tensor in GPa and density" in seismic_text

    ha_text = _child_text(_card_by_title(page, "Harmonic thermodynamics"))
    assert "Next · 0.5" in ha_text
    assert "Milestone 0.5" in ha_text

    qha_text = _child_text(_card_by_title(page, "Quasi-harmonic approximation"))
    assert "Next · 0.5" in qha_text
    assert "Milestone 0.5" in qha_text

    elasticity_text = _child_text(_card_by_title(page, "Elasticity"))
    assert "Native Quantas Elasticity HDF5" in elasticity_text

    eos_text = _child_text(_card_by_title(page, "Equation of state"))
    assert "Native Quantas EOS archive" in eos_text


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


def test_seismic_action_is_disabled_when_input_generation_is_incomplete() -> None:
    page = layout(
        backend=_backend(
            workflow_missing=(("seismic", ("create_input",)),),
        )
    )
    payload = to_json(page)
    hrefs = _link_hrefs(page)

    assert "Workflow unavailable" in payload
    assert "Missing public operations: create_input." in payload
    assert not any(href.rstrip("/").endswith("/seismic") for href in hrefs)
    assert any(href.rstrip("/").endswith("/elasticity") for href in hrefs)
