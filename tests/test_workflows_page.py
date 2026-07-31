from __future__ import annotations

import pytest

pytest.importorskip("dash")

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


def test_workflow_catalogue_distinguishes_gui_and_backend_availability() -> None:
    payload = to_json(layout(backend=_backend()))

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
    assert '"href":"/elasticity"' in payload
    assert '"href":"/seismic"' not in payload
    assert "Next · 0.4" in payload
    assert "Elastic stiffness tensor in GPa and density" in payload
    assert "Native Quantas Elasticity HDF5" in payload
    assert "Native Quantas EOS archive" in payload


def test_elasticity_action_is_disabled_when_its_public_lifecycle_is_incomplete() -> None:
    payload = to_json(
        layout(
            backend=_backend(
                workflow_missing=(("elasticity", ("run", "write_result")),),
            )
        )
    )

    assert "Workflow unavailable" in payload
    assert "API incomplete" in payload
    assert "Missing public operations: run, write_result." in payload
    assert '"href":"/elasticity"' not in payload
