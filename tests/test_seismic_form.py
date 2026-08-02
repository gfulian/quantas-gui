from __future__ import annotations

from quantas_gui.forms.schema import FieldKind, FileUploadField, NumericField, TextField
from quantas_gui.workflows.seismic.schema import build_request, seismic_form


def _values() -> dict[str, object]:
    schema = seismic_form()
    return {field.key: field.default for field in schema.fields}


def test_seismic_form_exposes_supported_scientific_inputs() -> None:
    schema = seismic_form()
    keys = {field.key for field in schema.fields}

    assert {
        "jobname",
        "stiffness_text",
        "density",
        "ntheta",
        "nphi",
        "hemisphere",
        "level",
        "track_polarization_axes",
    } <= keys
    assert "pressure_unit" not in keys
    assert "plot" not in keys
    assert "batch_size" not in keys
    assert "crystal_symmetry" not in keys

    stiffness = schema.field("stiffness_text")
    assert isinstance(stiffness, TextField)
    assert stiffness.kind is FieldKind.TEXTAREA
    assert stiffness.unit == "GPa"

    density = schema.field("density")
    assert isinstance(density, NumericField)
    assert density.unit == "kg m⁻³"
    assert density.bounds.minimum == 0.0
    assert density.bounds.minimum_open

    upload = schema.field("source_upload")
    assert isinstance(upload, FileUploadField)
    assert upload.accept == ()


def test_build_request_accepts_triangular_stiffness_and_density() -> None:
    values = _values()
    values["stiffness_text"] = """100 10 10 0 0 0
100 10 0 0 0
100 0 0 0
45 0 0
45 0
45"""
    values["density"] = 3178.0
    values["hemisphere"] = "full"
    values["level"] = "group"

    checked = build_request(values)

    assert checked.valid
    assert checked.request is not None
    assert checked.request.density == 3178.0
    assert checked.request.stiffness is not None
    assert checked.request.stiffness[1][0] == 10.0
    assert checked.request.hemisphere == "full"
    assert checked.request.level == "group"


def test_build_request_rejects_non_positive_density() -> None:
    values = _values()
    values["density"] = 0.0

    checked = build_request(values)

    assert not checked.valid
    assert checked.request is None
    assert any(issue.field == "density" for issue in checked.issues)


def test_selected_file_mode_requires_matching_import_provenance() -> None:
    values = _values()
    values["input_mode"] = "vasp"

    missing = build_request(values)
    imported = build_request(values, source_filename="OUTCAR")

    assert not missing.valid
    assert any(issue.code == "source-required" for issue in missing.issues)
    assert imported.valid
    assert imported.request is not None
    assert imported.request.source_filename == "OUTCAR"


def test_sampling_form_uses_internal_batches_for_visible_progress() -> None:
    values = _values()
    values["ntheta"] = 31
    values["nphi"] = 61

    checked = build_request(values)

    assert checked.valid
    assert checked.request is not None
    assert checked.request.batch_size == 128


def test_advanced_numerical_values_and_rotation_are_preserved() -> None:
    values = _values()
    values.update(
        {
            "eigenvalue_rtol": 2.0e-10,
            "degeneracy_atol": 3.0e-10,
            "pseudoinverse_rcond": 4.0e-10,
            "rotation_enabled": True,
            "rotation_kind": "xyz",
            "rotation_xyz": (10.0, 20.0, 30.0),
        }
    )

    checked = build_request(values)

    assert checked.valid
    assert checked.request is not None
    assert checked.request.eigenvalue_rtol == 2.0e-10
    assert checked.request.degeneracy_atol == 3.0e-10
    assert checked.request.pseudoinverse_rcond == 4.0e-10
    assert checked.request.rotation is not None
    assert checked.request.rotation.values == (10.0, 20.0, 30.0)
