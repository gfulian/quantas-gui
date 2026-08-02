"""Adapter from GUI SEISMIC requests to the public Quantas API."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from quantas.api import seismic

from quantas_gui.workflows.common import RotationRequest
from quantas_gui.workflows.seismic.request import SeismicRequest


def build_public_contracts(
    request: SeismicRequest,
    *,
    workspace_path: Path,
) -> tuple[seismic.Input, seismic.Options]:
    """Construct validated public Quantas input and option dataclasses."""
    input_data = _build_input(request, workspace_path=workspace_path)
    options = seismic.Options(
        ntheta=request.ntheta,
        nphi=request.nphi,
        hemisphere=seismic.Hemisphere(request.hemisphere),
        level=seismic.SamplingLevel(request.level),
        batch_size=request.batch_size,
        track_polarization_axes=request.track_polarization_axes,
        eigenvalue_rtol=request.eigenvalue_rtol,
        eigenvalue_atol=request.eigenvalue_atol,
        degeneracy_rtol=request.degeneracy_rtol,
        degeneracy_atol=request.degeneracy_atol,
        pseudoinverse_rcond=request.pseudoinverse_rcond,
        caustic_rtol=request.caustic_rtol,
        caustic_atol=request.caustic_atol,
        rotation=_build_rotation(request.rotation),
    )
    return seismic.normalize_input(input_data), options


def _build_input(
    request: SeismicRequest,
    *,
    workspace_path: Path,
) -> seismic.Input:
    if request.stiffness is not None:
        assert request.density is not None
        source = None
        if request.source_filename is not None:
            candidate = workspace_path / "inputs" / request.source_filename
            if candidate.is_file():
                source = candidate
        return seismic.Input(
            jobname=request.jobname,
            stiffness=np.asarray(request.stiffness, dtype=float),
            density=request.density,
            source=source,
        )

    assert request.input_filename is not None
    source = workspace_path / "inputs" / request.input_filename
    parsed = seismic.read_input(source)
    return seismic.Input(
        jobname=request.jobname,
        stiffness=parsed.stiffness,
        density=parsed.density,
        source=source,
        raw=parsed.raw,
    )


def _build_rotation(rotation: RotationRequest | None) -> seismic.TensorRotation | None:
    if rotation is None:
        return None
    if rotation.kind == "xyz":
        x, y, z = rotation.values
        return seismic.TensorRotation.from_xyz(
            x,
            y,
            z,
            degrees=True,
            description=rotation.description,
        )
    matrix = np.asarray(rotation.values, dtype=float).reshape((3, 3))
    return seismic.TensorRotation.from_matrix(
        matrix,
        description=rotation.description,
    )


__all__ = ["build_public_contracts"]
