from __future__ import annotations

from base64 import b64encode
from typing import cast

from quantas_gui.services.backends import DisabledExecutionBackend
from quantas_gui.services.results import ResultExplorerService
from quantas_gui.services.workspaces import LocalWorkspaceStore
from quantas_gui.workflows.elasticity.service import ElasticityWorkflowService


def _data_url(text: str) -> str:
    encoded = b64encode(text.encode("utf-8")).decode("ascii")
    return f"data:text/plain;base64,{encoded}"


def _service(tmp_path) -> ElasticityWorkflowService:
    return ElasticityWorkflowService(
        workspace_store=LocalWorkspaceStore(tmp_path),
        execution=DisabledExecutionBackend(),
        results=cast(ResultExplorerService, object()),
        max_upload_bytes=1024 * 1024,
    )


def test_quantas_input_import_uses_jobname_and_ignores_shared_density_line(tmp_path) -> None:
    matrix = "\n".join(
        [
            "100 10 10 0 0 0",
            "10 100 10 0 0 0",
            "10 10 100 0 0 0",
            "0 0 0 40 0 0",
            "0 0 0 0 40 0",
            "0 0 0 0 0 40",
        ]
    )
    imported = _service(tmp_path).import_upload(
        mode="quantas",
        filename="shared-elasticity-seismic.dat",
        contents=_data_url(f"Calcite\n{matrix}\n2710.0\n"),
    )

    assert imported.jobname == "Calcite"
    assert imported.stiffness[0][0] == 100.0
    assert imported.stiffness[5][5] == 40.0
    assert not hasattr(imported, "density")


def test_crystal_output_import_uses_public_input_generator_and_populates_tensor_only(
    tmp_path,
) -> None:
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
        filename="calcite.out",
        contents=_data_url(text + "\n"),
        jobname="Existing GUI title",
    )

    assert imported.jobname is None
    assert imported.stiffness[0][2] == imported.stiffness[2][0] == 20.0
    assert imported.source_filename == "calcite.out"


def test_vasp_outcar_without_extension_is_accepted(tmp_path) -> None:
    clamped = [1000.0, 1100.0, 1200.0, 400.0, 500.0, 600.0]
    relaxed = [2000.0, 2100.0, 2200.0, 700.0, 800.0, 900.0]

    def block(header: str, diagonal: list[float]) -> list[str]:
        result = [header, "separator", "separator"]
        for index, value in enumerate(diagonal, start=1):
            row = [0.0] * 6
            row[index - 1] = value
            result.append(f"{index} " + " ".join(str(item) for item in row))
        return result

    lines = [
        *block("SYMMETRIZED ELASTIC MODULI (kBar)", clamped),
        *block("TOTAL ELASTIC MODULI (kBar)", relaxed),
    ]

    imported = _service(tmp_path).import_upload(
        mode="vasp",
        filename="OUTCAR",
        contents=_data_url("\n".join(lines) + "\n"),
    )

    assert imported.source_filename == "OUTCAR"
    assert imported.jobname is None
    assert imported.stiffness[0][0] == 200.0
