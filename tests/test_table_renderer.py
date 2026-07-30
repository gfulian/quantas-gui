from __future__ import annotations

from quantas_gui.models.results import TableData
from quantas_gui.renderers.tables import (
    normalize_table,
    table_grid_payload,
    table_to_csv,
)


def test_table_renderer_applies_display_metadata_without_mutating_rows() -> None:
    table = TableData(
        title="Elastic moduli",
        columns=["Property", "Value"],
        rows=[["K_R", 42.123456789]],
        metadata={
            "column_formats": [None, "modulus"],
            "column_units": [None, "GPa"],
            "column_alignments": ["left", "right"],
        },
    )
    normalized = normalize_table(table)

    assert normalized.display_columns == ("Property", "Value (GPa)")
    assert normalized.display_rows == (("K_R", "42.12345679"),)
    assert table.rows[0][1] == 42.123456789


def test_csv_export_uses_raw_values_and_unit_headers() -> None:
    table = TableData(
        title="Data",
        columns=["P", "V"],
        rows=[[1.25, 100.125]],
        metadata={"column_units": ["GPa", "Å^3"]},
    )
    text = table_to_csv(table)
    assert "P (GPa),V (Å³)" in text
    assert "1.25,100.125" in text


def test_ag_grid_uses_raw_numbers_for_sorting_and_formatted_display() -> None:
    table = TableData(
        title="Numeric sorting",
        columns=["Value"],
        rows=[[1.0], [10.0], [2.0]],
        metadata={
            "column_formats": ["modulus"],
            "column_alignments": ["right"],
        },
    )

    payload = table_grid_payload(table)

    assert [row["c0"] for row in payload.records] == [1.0, 10.0, 2.0]
    assert [row["_display_c0"] for row in payload.records] == [
        "1.00000000",
        "10.00000000",
        "2.00000000",
    ]
    assert payload.columns[0]["cellDataType"] == "number"
    assert payload.columns[0]["filter"] == "agNumberColumnFilter"
    assert "_display_c0" in payload.columns[0]["valueFormatter"]["function"]


def test_report_grid_uses_a_dedicated_class_and_compact_height() -> None:
    from quantas_gui.renderers.tables import _grid_height

    assert _grid_height(row_count=3, page_size=50) == "min(68vh, 216px)"
    assert _grid_height(row_count=1000, page_size=50) == "min(68vh, 780px)"


def test_existing_slash_unit_headers_are_normalized_without_rewriting_ratios() -> None:
    table = TableData(
        title="Header normalization",
        columns=["E / GPa", "C_P / C_V"],
        rows=[[100.0, 1.2]],
    )

    normalized = normalize_table(table)

    assert normalized.display_columns == ("E (GPa)", "Cₚ / Cᵥ")
