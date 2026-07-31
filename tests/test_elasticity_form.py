from __future__ import annotations

from quantas_gui.forms.schema import FieldKind, FileUploadField, TextField
from quantas_gui.workflows.elasticity.schema import (
    build_request,
    elasticity_form,
    format_stiffness,
    parse_stiffness_text,
)


def _values() -> dict[str, object]:
    schema = elasticity_form()
    return {field.key: field.default for field in schema.fields}


def test_elasticity_form_exposes_only_supported_scientific_inputs() -> None:
    schema = elasticity_form()
    keys = {field.key for field in schema.fields}

    assert "density" not in keys
    assert "symmetry" not in keys
    assert "pressure_unit" not in keys
    assert "plot" not in keys
    assert {"jobname", "stiffness_text", "calculate_2d", "calculate_3d"} <= keys

    stiffness = schema.field("stiffness_text")
    assert isinstance(stiffness, TextField)
    assert stiffness.kind is FieldKind.TEXTAREA
    assert stiffness.unit == "GPa"
    assert "upper triangle" in stiffness.description.lower()
    assert "lower triangle" in stiffness.description.lower()

    upload = schema.field("source_upload")
    assert isinstance(upload, FileUploadField)
    assert upload.accept == ()  # OUTCAR may be extensionless.


def test_pasted_matrix_accepts_common_separators_and_round_trips() -> None:
    text = "\n".join(
        [
            "100, 10, 10, 0, 0, 0",
            "10 100 10 0 0 0",
            "10;100;120;0;0;0",
            "0 0 0 40 0 0",
            "0 0 0 0 50 0",
            "0 0 0 0 0 60",
        ]
    )
    matrix = parse_stiffness_text(text)

    assert matrix[0][0] == 100.0
    assert matrix[2][1] == 100.0
    assert parse_stiffness_text(format_stiffness(matrix)) == matrix


def _distinct_stiffness() -> tuple[tuple[float, ...], ...]:
    return (
        (100.0, 11.0, 12.0, 13.0, 14.0, 15.0),
        (11.0, 110.0, 22.0, 23.0, 24.0, 25.0),
        (12.0, 22.0, 120.0, 33.0, 34.0, 35.0),
        (13.0, 23.0, 33.0, 130.0, 44.0, 45.0),
        (14.0, 24.0, 34.0, 44.0, 140.0, 55.0),
        (15.0, 25.0, 35.0, 45.0, 55.0, 150.0),
    )


def test_pasted_compact_upper_triangle_is_mirrored() -> None:
    text = """100 11 12 13 14 15
110 22 23 24 25
120 33 34 35
130 44 45
140 55
150"""

    assert parse_stiffness_text(text) == _distinct_stiffness()


def test_pasted_compact_lower_triangle_is_mirrored() -> None:
    text = """100
11 110
12 22 120
13 23 33 130
14 24 34 44 140
15 25 35 45 55 150"""

    assert parse_stiffness_text(text) == _distinct_stiffness()


def test_pasted_zero_padded_triangles_are_mirrored() -> None:
    upper = """100 11 12 13 14 15
0 110 22 23 24 25
0 0 120 33 34 35
0 0 0 130 44 45
0 0 0 0 140 55
0 0 0 0 0 150"""
    lower = """100 0 0 0 0 0
11 110 0 0 0 0
12 22 120 0 0 0
13 23 33 130 0 0
14 24 34 44 140 0
15 25 35 45 55 150"""

    assert parse_stiffness_text(upper) == _distinct_stiffness()
    assert parse_stiffness_text(lower) == _distinct_stiffness()


def test_full_asymmetric_matrix_is_not_silently_modified() -> None:
    text = """100 11 12 13 14 15
99 110 22 23 24 25
12 22 120 33 34 35
13 23 33 130 44 45
14 24 34 44 140 55
15 25 35 45 55 150"""

    matrix = parse_stiffness_text(text)

    assert matrix[0][1] == 11.0
    assert matrix[1][0] == 99.0


def test_mixed_triangular_row_shape_is_rejected() -> None:
    text = """100 11 12 13 14 15
110 22 23 24 25
120 33 34 35
130 44 45 46
140 55
150"""

    try:
        parse_stiffness_text(text)
    except ValueError as exc:
        assert "upper triangle" in str(exc)
        assert "lower triangle" in str(exc)
    else:
        raise AssertionError("mixed triangular row lengths must be rejected")


def test_build_request_expands_compact_triangle_before_adapter_construction() -> None:
    values = _values()
    values["stiffness_text"] = """100 11 12 13 14 15
110 22 23 24 25
120 33 34 35
130 44 45
140 55
150"""

    checked = build_request(values)

    assert checked.valid
    assert checked.request is not None
    assert checked.request.stiffness == _distinct_stiffness()


def test_build_request_keeps_hidden_sampling_defaults_and_source_provenance() -> None:
    values = _values()
    values["calculate_2d"] = False
    values["ntheta_2d"] = None
    values["calculate_3d"] = False
    values["ntheta_3d"] = None
    values["nphi_3d"] = None
    values["properties_3d"] = None

    checked = build_request(values, source_filename="calcite.out")

    assert checked.valid
    assert checked.request is not None
    assert checked.request.source_filename == "calcite.out"
    assert checked.request.ntheta_2d == 361
    assert checked.request.ntheta_3d == 61
    assert checked.request.nphi_3d == 121


def test_build_request_reports_matrix_shape_at_the_text_field() -> None:
    values = _values()
    values["stiffness_text"] = "1 2 3\n"

    checked = build_request(values)

    assert checked.valid is False
    assert checked.request is None
    assert any(issue.field == "stiffness_text" for issue in checked.issues)


def test_selected_file_mode_requires_matching_import_provenance() -> None:
    values = _values()
    values["input_mode"] = "vasp"

    missing = build_request(values)
    imported = build_request(values, source_filename="OUTCAR")

    assert missing.valid is False
    assert any(issue.code == "source-required" for issue in missing.issues)
    assert imported.valid is True
    assert imported.request is not None
    assert imported.request.source_filename == "OUTCAR"


def test_3d_form_request_uses_internal_batches_for_visible_progress() -> None:
    values = _values()
    values["calculate_3d"] = True
    values["ntheta_3d"] = 31
    values["nphi_3d"] = 61

    checked = build_request(values)

    assert checked.valid
    assert checked.request is not None
    assert checked.request.batch_size == 256
