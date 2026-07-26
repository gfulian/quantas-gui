from __future__ import annotations

from quantas_gui.forms.schema import MatrixField
from quantas_gui.forms.values import matrix_to_row_data, row_data_to_matrix


def test_matrix_grid_round_trip_preserves_numeric_values() -> None:
    field = MatrixField(
        key="matrix",
        label="Matrix",
        rows=2,
        columns=2,
        default=((1.0, 2.0), (2.0, 4.0)),
        row_labels=("a", "b"),
        column_labels=("a", "b"),
        symmetric=True,
    )
    rows = matrix_to_row_data(field)
    assert rows[0]["__row__"] == "a"
    assert row_data_to_matrix(field, rows) == ((1.0, 2.0), (2.0, 4.0))
