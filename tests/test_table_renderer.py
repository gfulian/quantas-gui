from __future__ import annotations

from quantas_gui.models.results import TableData
from quantas_gui.renderers.tables import normalize_table, table_to_csv


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

    assert normalized.display_columns == ("Property", "Value [GPa]")
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
    assert "P [GPa],V [Å^3]" in text
    assert "1.25,100.125" in text
