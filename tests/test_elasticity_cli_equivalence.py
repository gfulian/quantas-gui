from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from quantas_gui.workflows.elasticity.adapter import build_public_contracts
from quantas_gui.workflows.elasticity.request import ElasticityRequest, RotationRequest


def _stiffness() -> tuple[tuple[float, ...], ...]:
    return (
        (220.0, 80.0, 70.0, 0.0, 0.0, 0.0),
        (80.0, 190.0, 65.0, 0.0, 0.0, 0.0),
        (70.0, 65.0, 250.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 75.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 68.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 60.0),
    )


def test_equivalent_cli_and_public_api_results_match(tmp_path: Path) -> None:
    from quantas.api import elasticity

    executable = shutil.which("quantas")
    if executable is None:
        pytest.skip("the Quantas console script is unavailable")

    request = ElasticityRequest(
        jobname="CLI equivalence",
        stiffness=_stiffness(),
        calculate_2d=True,
        ntheta_2d=7,
        calculate_3d=True,
        ntheta_3d=7,
        nphi_3d=13,
        properties_3d=("young",),
        rotation=RotationRequest(kind="xyz", values=(10.0, 20.0, 30.0)),
    )
    input_file = tmp_path / "elasticity.dat"
    input_file.write_text(
        request.jobname
        + "\n"
        + "\n".join(" ".join(str(value) for value in row) for row in _stiffness())
        + "\n",
        encoding="utf-8",
    )
    cli_result = tmp_path / "cli.hdf5"
    cli_report = tmp_path / "cli.log"
    completed = subprocess.run(
        [
            executable,
            "elasticity",
            "run",
            str(input_file),
            "--2d",
            "--3d",
            "--ntheta",
            "7",
            "--nphi",
            "13",
            "--property",
            "young",
            "--rotate-xyz",
            "10",
            "20",
            "30",
            "--output",
            str(cli_result),
            "--report",
            str(cli_report),
            "--quiet",
            "--force",
            "--no-progress",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    assert cli_report.is_file()

    direct_input, direct_options = build_public_contracts(request, workspace_path=tmp_path)
    direct = elasticity.get_result(elasticity.run(direct_input, direct_options))
    cli = elasticity.get_result(elasticity.read_result(cli_result))

    np.testing.assert_allclose(cli.stiffness, direct.stiffness, rtol=0.0, atol=0.0)
    np.testing.assert_allclose(
        cli.compliance,
        direct.compliance,
        rtol=1.0e-14,
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        cli.averages.as_array(),
        direct.averages.as_array(),
        rtol=1.0e-14,
        atol=1.0e-14,
    )
    assert cli.crystal_system == direct.crystal_system
    assert cli.stability.is_stable is direct.stability.is_stable
    assert cli.properties_2d.keys() == direct.properties_2d.keys()
    assert cli.properties_3d is not None
    assert direct.properties_3d is not None
    np.testing.assert_allclose(
        cli.properties_3d.surfaces["young"].values,
        direct.properties_3d.surfaces["young"].values,
        rtol=1.0e-12,
        atol=1.0e-12,
    )
