"""Adapter from GUI Elasticity requests to the public Quantas API."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import numpy as np
from quantas.api import elasticity

from quantas_gui.workflows.elasticity.request import ElasticityRequest, RotationRequest


def build_public_contracts(
    request: ElasticityRequest,
    *,
    workspace_path: Path,
) -> tuple[elasticity.Input, elasticity.Options]:
    """Construct validated public Quantas input and option dataclasses."""
    input_data = _build_input(request, workspace_path=workspace_path)
    rotation = _build_rotation(request.rotation)
    surface_options = None
    if request.calculate_3d:
        surface_options = elasticity.SurfaceOptions(
            ntheta=request.ntheta_3d,
            nphi=request.nphi_3d,
            properties=cast(
                tuple[elasticity.SurfaceProperty, ...],
                request.properties_3d,
            ),
            batch_size=request.batch_size,
        )
    options = elasticity.Options(
        pressure_unit="GPa",
        calculate_2d=request.calculate_2d,
        ntheta=request.ntheta_2d,
        calculate_3d=request.calculate_3d,
        surface_options=surface_options,
        rotation=rotation,
    )
    return elasticity.normalize_input(input_data), options


def _build_input(
    request: ElasticityRequest,
    *,
    workspace_path: Path,
) -> elasticity.Input:
    if request.stiffness is not None:
        source = None
        if request.source_filename is not None:
            candidate = workspace_path / "inputs" / request.source_filename
            if candidate.is_file():
                source = candidate
        return elasticity.Input(
            jobname=request.jobname,
            stiffness=np.asarray(request.stiffness, dtype=float),
            source=source,
        )
    assert request.input_filename is not None
    source = workspace_path / "inputs" / request.input_filename
    parsed = elasticity.read_input(source)
    return elasticity.Input(
        jobname=request.jobname,
        stiffness=parsed.stiffness,
        source=source,
    )


def _build_rotation(
    rotation: RotationRequest | None,
) -> elasticity.TensorRotation | None:
    if rotation is None:
        return None
    if rotation.kind == "xyz":
        x, y, z = rotation.values
        return elasticity.TensorRotation.from_xyz(
            x,
            y,
            z,
            degrees=True,
            description=rotation.description,
        )
    matrix = np.asarray(rotation.values, dtype=float).reshape((3, 3))
    return elasticity.TensorRotation.from_matrix(
        matrix,
        description=rotation.description,
    )


__all__ = ["build_public_contracts"]
