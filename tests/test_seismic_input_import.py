from __future__ import annotations

from base64 import b64encode
from pathlib import Path

import pytest

from quantas_gui.services.backends import DisabledExecutionBackend
from quantas_gui.services.cache import LocalArtifactCache
from quantas_gui.services.result_backend import QuantasResultBackend
from quantas_gui.services.results import ResultExplorerService
from quantas_gui.services.workspaces import LocalWorkspaceStore
from quantas_gui.workflows.seismic.service import SeismicWorkflowService


def _contents(text: str) -> str:
    return "data:text/plain;base64," + b64encode(text.encode("utf-8")).decode("ascii")


def _service(tmp_path: Path) -> SeismicWorkflowService:
    from quantas_gui.services.backend_info import detect_quantas_backend

    store = LocalWorkspaceStore(tmp_path / "workspaces")
    compatibility = detect_quantas_backend()
    results = ResultExplorerService(
        workspace_store=store,
        backend=QuantasResultBackend(),
        max_upload_bytes=1024 * 1024,
        compatibility=compatibility,
        cache=LocalArtifactCache(max_entries=4),
    )
    return SeismicWorkflowService(store, DisabledExecutionBackend(), results)


def _quantas_input() -> str:
    return """Shared input
220 80 70 0 0 0
190 65 0 0 0
250 0 0 0
75 0 0
68 0
60
3178
"""


def _vasp_output(*, include_density: bool = True) -> str:
    lines: list[str] = []
    if include_density:
        lines.extend(
            [
                "POMASS = 24.305; ZVAL = 2.000",
                "ions per type = 2",
                "volume of cell : 80.000000",
            ]
        )
    lines.extend(
        [
            "SYMMETRIZED ELASTIC MODULI (kBar)",
            "separator",
            "separator",
            "1 2200 800 700 0 0 0",
            "2 800 1900 650 0 0 0",
            "3 700 650 2500 0 0 0",
            "4 0 0 0 750 0 0",
            "5 0 0 0 0 680 0",
            "6 0 0 0 0 0 600",
        ]
    )
    return "\n".join(lines) + "\n"


def test_shared_quantas_input_populates_density_and_tensor(tmp_path: Path) -> None:
    imported = _service(tmp_path).import_upload(
        mode="quantas",
        filename="shared.dat",
        contents=_contents(_quantas_input()),
    )

    assert imported.jobname == "Shared input"
    assert imported.density == pytest.approx(3178.0)
    assert imported.stiffness[0][0] == pytest.approx(220.0)
    assert imported.stiffness[1][0] == pytest.approx(80.0)


def test_crystal_output_populates_density_and_tensor(tmp_path: Path) -> None:
    rows = [
        "| 100 10 20 0 0 0 |",
        "| 110 30 0 0 0 |",
        "| 120 0 0 0 |",
        "| 40 0 0 |",
        "| 50 0 |",
        "| 60 |",
    ]
    text = "\n".join(
        [
            "ELASTCON OPTION",
            "GEOMETRY NOW FULLY CONSISTENT WITH THE GROUP",
            "PRIMITIVE CELL - TEST 3.178 g/cm3",
            "FINAL RESULTS START",
            "SYMMETRIZED ELASTIC CONSTANTS",
            "header",
            *rows,
        ]
    )

    imported = _service(tmp_path).import_upload(
        mode="crystal",
        filename="crystal.out",
        contents=_contents(text + "\n"),
        jobname="CRYSTAL run",
    )

    assert imported.jobname is None
    assert imported.density == pytest.approx(3178.0)
    assert imported.stiffness[0][2] == pytest.approx(20.0)
    assert imported.stiffness[2][0] == pytest.approx(20.0)


def test_vasp_output_populates_density_and_tensor(tmp_path: Path) -> None:
    imported = _service(tmp_path).import_upload(
        mode="vasp",
        filename="OUTCAR",
        contents=_contents(_vasp_output()),
        jobname="VASP run",
    )

    expected_density = 2.0 * 24.305 / 80.0 * 1660.53906660
    assert imported.jobname is None
    assert imported.density == pytest.approx(expected_density, rel=5.0e-7)
    assert imported.stiffness[0][0] == pytest.approx(220.0)


def test_vasp_output_without_density_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="finite positive density"):
        _service(tmp_path).import_upload(
            mode="vasp",
            filename="OUTCAR",
            contents=_contents(_vasp_output(include_density=False)),
        )
