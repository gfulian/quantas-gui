from __future__ import annotations

from pathlib import Path

import numpy as np
from quantas.api import common, eos, ha

from quantas_gui.explorer.models import PlotBuildSelection
from quantas_gui.services.result_backend import QuantasResultBackend


def _write_ha_result(path: Path) -> Path:
    payload = ha.Result(
        jobname="GUI public lifecycle",
        temperature=np.asarray([0.0, 100.0, 200.0], dtype=np.float64),
        volume=np.asarray([10.0, 11.0], dtype=np.float64),
        static_energy=np.asarray([-1.0, -0.9], dtype=np.float64),
        zero_point_energy=np.asarray([[0.1, 0.2]], dtype=np.float64),
        free_energy=np.asarray(
            [[-0.9, -0.7], [-0.8, -0.6], [-0.7, -0.5]],
            dtype=np.float64,
        ),
        entropy=np.asarray(
            [[0.0, 0.0], [0.01, 0.02], [0.02, 0.03]],
            dtype=np.float64,
        ),
        isochoric_heat_capacity=np.asarray(
            [[0.0, 0.0], [0.1, 0.2], [0.2, 0.3]],
            dtype=np.float64,
        ),
        metadata={
            "units": {
                "energy": "Ha",
                "entropy": "Ha cell^-1 K^-1",
                "heat_capacity": "Ha cell^-1 K^-1",
                "volume": "A^3",
                "temperature": "K",
            }
        },
    )
    result = common.ResultData(
        metadata=common.ResultMetadata(module="ha", method="harmonic"),
        results={"ha": payload},
    )
    return ha.write_result(result, path)


def test_public_result_backend_uses_registry_inventory_report_and_builders(
    tmp_path: Path,
) -> None:
    result_path = _write_ha_result(tmp_path / "ha-result")
    backend = QuantasResultBackend()

    overview = backend.inspect(result_path)
    assert overview.summary.module == "ha"
    assert not overview.summary.archive

    table_families = backend.table_families(result_path)
    assert table_families[0].key == "default"
    assert backend.build_tables(result_path, "default")

    plot_families = backend.plot_families(result_path)
    assert {item.key for item in plot_families} == {
        "temperature_curves",
        "volume_curves",
        "volume_temperature_contour",
    }
    assert all(item.property_keys for item in plot_families)
    for family in plot_families:
        collection = backend.build_plots(result_path, family.key)
        assert collection.plots


def test_public_ha_selection_schema_and_selected_builder_use_exact_coordinates(
    tmp_path: Path,
) -> None:
    result_path = _write_ha_result(tmp_path / "ha-selection")
    backend = QuantasResultBackend()

    schema = backend.plot_selection_schema(result_path, "temperature_curves")
    assert schema.property_field is not None
    assert {item.value for item in schema.property_field.options} >= {
        "free_energy",
        "entropy",
    }
    volumes = next(field for field in schema.context_fields if field.key == "sampled_volume")
    assert tuple(item.value for item in volumes.options) == (10.0, 11.0)

    selection = PlotBuildSelection(
        family_key="temperature_curves",
        property_keys=("free_energy",),
        contexts=(("sampled_volume", (10.0,)),),
    )
    collection = backend.build_plots(
        result_path,
        "temperature_curves",
        selection=selection,
    )

    assert len(collection.plots) == 1
    plot = collection.plots[0]
    assert plot.key == "free_energy"
    assert len(plot.series) == 1
    assert plot.x_axis.label == "Temperature (K)"
    assert plot.y_axis.label == "$F$ (Ha)"


def test_eos_archive_inspection_is_public_read_only_and_structural(tmp_path: Path) -> None:
    dataset = eos.Dataset(
        jobname="GUI EOS archive",
        columns={
            "pressure": np.asarray([0.0, 1.0, 2.0], dtype=np.float64),
            "volume": np.asarray([10.0, 9.8, 9.6], dtype=np.float64),
        },
        units={"pressure": "GPa", "volume": "A^3"},
    )
    archive_path = tmp_path / "eos.hdf5"
    with eos.Archive.create(archive_path, dataset=dataset, creator="GUI test"):
        pass
    before = archive_path.read_bytes()

    backend = QuantasResultBackend()
    overview = backend.inspect(archive_path)
    assert overview.summary.module == "eos"
    assert overview.summary.archive
    assert overview.summary.result_keys == ("pv/volume",)
    assert overview.warnings

    families = backend.table_families(archive_path)
    assert {item.key for item in families} == {"summary", "datasets", "slots", "records"}
    assert backend.build_tables(archive_path, "datasets")[0].rows[0][1] == "GUI EOS archive"
    assert backend.plot_families(archive_path) == ()
    assert archive_path.read_bytes() == before


def test_eos_fit_record_tables_expose_model_parameters_and_covariance(tmp_path: Path) -> None:
    dataset = eos.Dataset(
        jobname="GUI EOS fitted archive",
        columns={
            "pressure": np.asarray([0.0, 0.8, 1.8, 3.0, 4.5, 6.3, 8.5, 11.2]),
            "volume": np.asarray([112.0, 110.0, 108.0, 106.0, 104.0, 102.0, 100.0, 98.0]),
        },
        units={"pressure": "GPa", "volume": "angstrom^3"},
    )
    request = eos.FitRequest(
        model="BM3",
        options=eos.FitOptions(solver_options=eos.OLSOptions()),
    )
    result = eos.fit(dataset, request)
    assert result.fit.success

    archive_path = tmp_path / "eos-fitted.hdf5"
    with eos.Archive.create(archive_path, dataset=dataset, creator="GUI test") as archive:
        archive.append_fit(1, request, result, accept=True)
    before = archive_path.read_bytes()

    backend = QuantasResultBackend()
    families = backend.table_families(archive_path)
    fit_family = next(item for item in families if item.key == "fit_record_1")
    assert "BM3" in fit_family.title
    assert "volume" in fit_family.title

    tables = backend.build_tables(archive_path, fit_family.key)
    titles = {table.title for table in tables}
    assert {
        "EOS fit record #1",
        "EOS fitted parameters",
        "EOS fit quality and diagnostics",
        "EOS parameter covariance",
    } <= titles

    identity = next(table for table in tables if table.title == "EOS fit record #1")
    identity_values = {row[0]: row[1] for row in identity.rows}
    assert identity_values["EOS model"] == "Birch-Murnaghan, order 3"
    assert identity_values["Fitted target"] == "volume"
    assert identity_values["Target unit"] == "angstrom³"

    parameters = next(table for table in tables if table.title == "EOS fitted parameters")
    assert parameters.columns[:6] == [
        "Parameter",
        "Value",
        "Uncertainty",
        "State",
        "Unit",
        "Description",
    ]
    assert [row[0] for row in parameters.rows] == ["K₀", "K′", "K″", "V₀"]

    covariance = next(table for table in tables if table.title == "EOS parameter covariance")
    assert len(covariance.rows) == 4
    assert len(covariance.columns) == 5
    assert archive_path.read_bytes() == before
