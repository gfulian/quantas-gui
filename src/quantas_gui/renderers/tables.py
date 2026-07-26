"""Dash AG Grid and CSV adapters for neutral Quantas report tables."""

from __future__ import annotations

from dataclasses import dataclass
import csv
from io import StringIO
from numbers import Integral, Real
from typing import Any, Sequence


_NUMERIC_FORMATS: dict[str, str] = {
    "general": ".8g", "integer": "d", "energy": ".12E", "energy_ha": ".12E",
    "energy_ev": ".10E", "volume": ".8f", "pressure": ".8f", "modulus": ".8f",
    "thermoelastic_modulus": ".4f", "thermoelastic_uncertainty": ".4f",
    "temperature": ".2f", "frequency": ".6f", "dimensionless": ".8f",
    "uncertainty": ".6E", "angle": ".6f", "eos_pressure": ".4f",
    "eos_temperature": ".2f", "eos_structural": ".6f", "eos_correlation": ".6f",
    "eos_covariance": ".6e",
}


@dataclass(frozen=True, slots=True)
class NormalizedTable:
    """Browser-ready table data that preserves the source table separately."""

    title: str
    columns: tuple[str, ...]
    display_columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    display_rows: tuple[tuple[str, ...], ...]
    alignments: tuple[str, ...]
    metadata: dict[str, Any]


def normalize_table(table: Any) -> NormalizedTable:
    """Normalize one public ``ReportTable`` through structural attributes."""
    columns = tuple(str(item) for item in table.columns)
    rows = tuple(tuple(row) for row in table.rows)
    metadata = dict(getattr(table, "metadata", {}) or {})
    formats = _metadata_list(metadata, "column_formats", len(columns), None)
    units = _metadata_list(metadata, "column_units", len(columns), None)
    alignments = tuple(
        str(item).lower()
        for item in _metadata_list(metadata, "column_alignments", len(columns), "left")
    )
    display_columns = tuple(
        f"{column} [{unit}]" if unit not in (None, "") else column
        for column, unit in zip(columns, units, strict=True)
    )
    display_rows = tuple(
        tuple(format_cell(value, formats[index]) for index, value in enumerate(_padded(row, len(columns))))
        for row in rows
    )
    return NormalizedTable(
        title=str(table.title), columns=columns, display_columns=display_columns,
        rows=rows, display_rows=display_rows, alignments=alignments, metadata=metadata,
    )


def table_to_csv(table: Any) -> str:
    """Serialize one neutral table to CSV using raw values and unit headers."""
    normalized = normalize_table(table)
    stream = StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(normalized.display_columns)
    for row in normalized.rows:
        writer.writerow(_csv_cell(value) for value in _padded(row, len(normalized.columns)))
    return stream.getvalue()


def table_component(table: Any, *, component_id: str, page_size: int = 20):
    """Create a virtualized AG Grid table without changing source values."""
    import dash_ag_grid as dag
    from dash import html

    normalized = normalize_table(table)
    records = [
        {f"c{index}": value for index, value in enumerate(row)}
        for row in normalized.display_rows
    ]
    columns = []
    for index, (label, alignment) in enumerate(
        zip(normalized.display_columns, normalized.alignments, strict=True)
    ):
        columns.append(
            {
                "field": f"c{index}",
                "headerName": label,
                "sortable": True,
                "filter": True,
                "resizable": True,
                "minWidth": 110,
                "cellStyle": {"textAlign": _dash_alignment(alignment)},
                "tooltipField": f"c{index}",
            }
        )
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [html.H3(normalized.title), html.P(
                            f"{len(normalized.rows)} rows · {len(normalized.columns)} columns"
                        )]
                    ),
                    html.Span("Raw values retained", className="q-table-precision-badge"),
                ],
                className="q-table-heading",
            ),
            dag.AgGrid(
                id=component_id,
                rowData=records,
                columnDefs=columns,
                defaultColDef={
                    "resizable": True,
                    "sortable": True,
                    "filter": True,
                    "suppressHeaderMenuButton": False,
                },
                dashGridOptions={
                    "theme": "legacy",
                    "pagination": True,
                    "paginationPageSize": max(5, int(page_size)),
                    "paginationPageSizeSelector": False,
                    "animateRows": False,
                    "enableCellTextSelection": True,
                    "ensureDomOrder": False,
                    "rowBuffer": 12,
                    "tooltipShowDelay": 300,
                },
                className="ag-theme-quartz-dark q-results-grid",
                style={"height": "min(68vh, 780px)", "width": "100%"},
            ),
        ],
        className="q-panel q-table-panel",
    )


def format_cell(value: Any, format_name: Any = None) -> str:
    """Format a table cell for display while preserving the raw value elsewhere."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Integral):
        specification = _resolve_format(format_name)
        return format(int(value), specification) if specification == "d" else format(float(value), specification)
    if isinstance(value, Real):
        name = None if format_name is None else str(format_name)
        if name in {"eos_parameter", "eos_uncertainty", "eos_residual", "eos_statistic"}:
            return _adaptive_six(float(value))
        if name == "eos_pressure_uncertainty":
            number = float(value)
            return f"{number:.6e}" if number != 0.0 and abs(number) < 5.0e-5 else f"{number:.4f}"
        if name == "eos_temperature_uncertainty":
            number = float(value)
            return f"{number:.6e}" if number != 0.0 and abs(number) < 5.0e-3 else f"{number:.2f}"
        return format(float(value), _resolve_format(format_name))
    return str(value)


def _resolve_format(format_name: Any) -> str:
    if format_name is None:
        return _NUMERIC_FORMATS["general"]
    name = str(format_name)
    return _NUMERIC_FORMATS.get(name, name)


def _adaptive_six(value: float) -> str:
    magnitude = abs(value)
    if value != 0.0 and (magnitude < 1.0e-4 or magnitude >= 1.0e6):
        return f"{value:.6e}"
    return f"{value:.6f}"


def _metadata_list(metadata: dict[str, Any], key: str, length: int, default: Any) -> list[Any]:
    values = metadata.get(key, ())
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return [default] * length
    normalized = list(values)
    return normalized if len(normalized) == length else [default] * length


def _padded(row: Sequence[Any], length: int) -> tuple[Any, ...]:
    values = tuple(row[:length])
    return values + (None,) * (length - len(values))


def _dash_alignment(value: str) -> str:
    return {"right": "right", "center": "center"}.get(value, "left")


def _csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    if shape is not None and dtype is not None:
        return f"{type(value).__name__}(shape={tuple(shape)}, dtype={dtype})"
    return value
