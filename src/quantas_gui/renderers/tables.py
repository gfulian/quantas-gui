"""Dash AG Grid and CSV adapters for neutral Quantas report tables."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from io import StringIO
from math import isfinite
from numbers import Integral, Real
from typing import Any, Literal

from quantas_gui.presentation.scientific_labels import (
    quantity_unit_label,
    scientific_label_text,
)

_NUMERIC_FORMATS: dict[str, str] = {
    "general": ".8g",
    "integer": "d",
    "energy": ".12E",
    "energy_ha": ".12E",
    "energy_ev": ".10E",
    "volume": ".8f",
    "pressure": ".8f",
    "modulus": ".8f",
    "thermoelastic_modulus": ".4f",
    "thermoelastic_uncertainty": ".4f",
    "temperature": ".2f",
    "frequency": ".6f",
    "dimensionless": ".8f",
    "uncertainty": ".6E",
    "angle": ".6f",
    "eos_pressure": ".4f",
    "eos_temperature": ".2f",
    "eos_structural": ".6f",
    "eos_correlation": ".6f",
    "eos_covariance": ".6e",
}

ColumnKind = Literal["text", "number", "boolean"]


@dataclass(frozen=True, slots=True)
class NormalizedTable:
    """Browser-ready table data that preserves the source table separately."""

    title: str
    columns: tuple[str, ...]
    display_columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    display_rows: tuple[tuple[str, ...], ...]
    formats: tuple[Any, ...]
    alignments: tuple[str, ...]
    column_kinds: tuple[ColumnKind, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class GridPayload:
    """Dash AG Grid payload with raw sortable cells and display formatters."""

    records: tuple[dict[str, Any], ...]
    columns: tuple[dict[str, Any], ...]


def normalize_table(table: Any) -> NormalizedTable:
    """Normalize one public ``ReportTable`` through structural attributes."""
    columns = tuple(str(item) for item in table.columns)
    rows = tuple(tuple(_padded(row, len(columns))) for row in table.rows)
    metadata = dict(getattr(table, "metadata", {}) or {})
    formats = tuple(
        _metadata_list(
            metadata,
            "column_formats",
            len(columns),
            None,
        )
    )
    units = _metadata_list(
        metadata,
        "column_units",
        len(columns),
        None,
    )
    alignments = tuple(
        str(item).lower()
        for item in _metadata_list(
            metadata,
            "column_alignments",
            len(columns),
            "left",
        )
    )
    display_columns = tuple(
        scientific_label_text(quantity_unit_label(column, unit))
        for column, unit in zip(columns, units, strict=True)
    )
    display_rows = tuple(
        tuple(format_cell(value, formats[index]) for index, value in enumerate(row)) for row in rows
    )
    column_kinds = tuple(
        _column_kind(tuple(row[index] for row in rows)) for index in range(len(columns))
    )
    return NormalizedTable(
        title=str(table.title),
        columns=columns,
        display_columns=display_columns,
        rows=rows,
        display_rows=display_rows,
        formats=formats,
        alignments=alignments,
        column_kinds=column_kinds,
        metadata=metadata,
    )


def table_to_csv(table: Any) -> str:
    """Serialize the complete neutral table using raw values and unit headers."""
    normalized = normalize_table(table)
    stream = StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(normalized.display_columns)
    for row in normalized.rows:
        writer.writerow(_csv_cell(value) for value in row)
    return stream.getvalue()


def table_grid_payload(table: Any) -> GridPayload:
    """Build raw AG Grid records while preserving Quantas display formatting."""
    normalized = normalize_table(table)
    records: list[dict[str, Any]] = []
    for raw_row, display_row in zip(normalized.rows, normalized.display_rows, strict=True):
        record: dict[str, Any] = {}
        for index, (raw_value, display_value) in enumerate(zip(raw_row, display_row, strict=True)):
            record[f"c{index}"] = _grid_cell(raw_value)
            record[f"_display_c{index}"] = display_value
        records.append(record)

    columns: list[dict[str, Any]] = []
    for index, (label, alignment, kind) in enumerate(
        zip(
            normalized.display_columns,
            normalized.alignments,
            normalized.column_kinds,
            strict=True,
        )
    ):
        field = f"c{index}"
        display_field = f"_display_c{index}"
        columns.append(
            {
                "field": field,
                "headerName": label,
                "sortable": True,
                "filter": ("agNumberColumnFilter" if kind == "number" else "agTextColumnFilter"),
                "cellDataType": kind,
                "resizable": True,
                "minWidth": 110,
                "cellStyle": {"textAlign": _dash_alignment(alignment)},
                "valueFormatter": {
                    "function": (
                        f"params.data && params.data.{display_field} !== undefined "
                        f"? params.data.{display_field} : ''"
                    )
                },
                "tooltipField": display_field,
            }
        )
    return GridPayload(records=tuple(records), columns=tuple(columns))


def table_component(
    table: Any,
    *,
    component_id: str,
    page_size: int = 20,
) -> Any:
    """Create a virtualized AG Grid table with numeric sorting on raw values."""
    import dash_ag_grid as dag
    from dash import html

    normalized = normalize_table(table)
    payload = table_grid_payload(table)
    return html.Section(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H3(normalized.title),
                            html.P(
                                f"{len(normalized.rows)} rows · {len(normalized.columns)} columns"
                            ),
                        ]
                    ),
                    html.Span(
                        "Raw values retained",
                        className="q-table-precision-badge",
                    ),
                ],
                className="q-table-heading",
            ),
            dag.AgGrid(
                id=component_id,
                rowData=list(payload.records),
                columnDefs=list(payload.columns),
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
                className="ag-theme-quartz-dark q-report-grid",
                style={
                    "height": _grid_height(
                        row_count=len(normalized.rows),
                        page_size=max(5, int(page_size)),
                    ),
                    "width": "100%",
                },
            ),
        ],
        className="q-panel q-table-panel",
    )


def _grid_height(*, row_count: int, page_size: int) -> str:
    """Return a compact bounded height for one paginated report grid."""
    visible_rows = max(1, min(max(0, row_count), max(5, page_size)))
    pixels = 44 + visible_rows * 38 + 58
    return f"min(68vh, {min(max(pixels, 190), 780)}px)"


def format_cell(value: Any, format_name: Any = None) -> str:
    """Format a table cell for display while preserving the raw value elsewhere."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Integral):
        specification = _resolve_format(format_name)
        if specification == "d":
            return format(int(value), specification)
        return format(float(value), specification)
    if isinstance(value, Real):
        name = None if format_name is None else str(format_name)
        if name in {
            "eos_parameter",
            "eos_uncertainty",
            "eos_residual",
            "eos_statistic",
        }:
            return _adaptive_six(float(value))
        if name == "eos_pressure_uncertainty":
            number = float(value)
            if number != 0.0 and abs(number) < 5.0e-5:
                return f"{number:.6e}"
            return f"{number:.4f}"
        if name == "eos_temperature_uncertainty":
            number = float(value)
            if number != 0.0 and abs(number) < 5.0e-3:
                return f"{number:.6e}"
            return f"{number:.2f}"
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


def _metadata_list(
    metadata: dict[str, Any],
    key: str,
    length: int,
    default: Any,
) -> list[Any]:
    values = metadata.get(key, ())
    if not isinstance(values, Sequence) or isinstance(
        values,
        (str, bytes, bytearray),
    ):
        return [default] * length
    normalized = list(values)
    return normalized if len(normalized) == length else [default] * length


def _padded(row: Sequence[Any], length: int) -> tuple[Any, ...]:
    values = tuple(row[:length])
    return values + (None,) * (length - len(values))


def _column_kind(values: tuple[Any, ...]) -> ColumnKind:
    nonempty = tuple(value for value in values if value is not None)
    if nonempty and all(isinstance(value, bool) for value in nonempty):
        return "boolean"
    if nonempty and all(
        isinstance(value, Real) and not isinstance(value, bool) for value in nonempty
    ):
        return "number"
    return "text"


def _grid_cell(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, Integral)):
        return value
    if isinstance(value, Real):
        number = float(value)
        return number if isfinite(number) else None
    item = getattr(value, "item", None)
    shape = getattr(value, "shape", None)
    if callable(item) and shape == ():
        return _grid_cell(item())
    return _csv_cell(value)


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
