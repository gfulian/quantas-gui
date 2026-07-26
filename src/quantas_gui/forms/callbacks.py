"""Generic callbacks used by composite Quantas GUI form controls."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import dash
from dash import ALL, MATCH, Input, Output, State, ctx, html, no_update


def register_form_component_callbacks(app: dash.Dash) -> None:
    """Register callbacks shared by all rendered declarative forms."""

    @app.callback(
        Output(
            {
                "type": "q-form-control",
                "form": MATCH,
                "field": MATCH,
                "part": "triplet-store",
            },
            "data",
        ),
        Input(
            {
                "type": "q-form-part",
                "form": MATCH,
                "field": MATCH,
                "part": ALL,
            },
            "value",
        ),
        State(
            {
                "type": "q-form-part",
                "form": MATCH,
                "field": MATCH,
                "part": ALL,
            },
            "id",
        ),
    )
    def collect_range_triplet(
        values: Sequence[Any],
        identifiers: Sequence[dict[str, Any]],
    ) -> list[Any]:
        order = {"start": 0, "stop": 1, "step": 2}
        result: list[Any] = [None, None, None]
        for value, identifier in zip(values, identifiers, strict=True):
            result[order[str(identifier["part"])]] = value
        return result

    @app.callback(
        Output(
            {
                "type": "q-form-control",
                "form": MATCH,
                "field": MATCH,
                "part": "vector-store",
            },
            "data",
        ),
        Input(
            {
                "type": "q-form-vector-part",
                "form": MATCH,
                "field": MATCH,
                "index": ALL,
            },
            "value",
        ),
        State(
            {
                "type": "q-form-vector-part",
                "form": MATCH,
                "field": MATCH,
                "index": ALL,
            },
            "id",
        ),
    )
    def collect_vector(
        values: Sequence[Any],
        identifiers: Sequence[dict[str, Any]],
    ) -> list[Any]:
        pairs = sorted(
            zip(identifiers, values, strict=True),
            key=lambda item: int(item[0]["index"]),
        )
        return [value for _, value in pairs]

    @app.callback(
        Output(
            {"type": "q-form-upload-list", "form": MATCH, "field": MATCH},
            "children",
        ),
        Input(
            {"type": "q-form-upload", "form": MATCH, "field": MATCH},
            "filename",
        ),
    )
    def display_upload_names(filename: str | Sequence[str] | None) -> Any:
        if not filename:
            return None
        names = [filename] if isinstance(filename, str) else list(filename)
        return [html.Span(name, className="q-upload-file") for name in names]

    @app.callback(
        Output(
            {"type": "q-form-control", "form": MATCH, "field": MATCH, "part": "value"},
            "rowData",
            allow_duplicate=True,
        ),
        Input({"type": "q-form-grid-add", "form": MATCH, "field": MATCH}, "n_clicks"),
        Input(
            {"type": "q-form-grid-remove", "form": MATCH, "field": MATCH},
            "n_clicks",
        ),
        State(
            {"type": "q-form-control", "form": MATCH, "field": MATCH, "part": "value"},
            "rowData",
        ),
        State(
            {"type": "q-form-control", "form": MATCH, "field": MATCH, "part": "value"},
            "selectedRows",
        ),
        prevent_initial_call=True,
    )
    def edit_key_value_rows(
        add_clicks: int | None,
        remove_clicks: int | None,
        rows: Sequence[dict[str, Any]] | None,
        selected: Sequence[dict[str, Any]] | None,
    ) -> list[dict[str, Any]] | Any:
        del add_clicks, remove_clicks
        current = [dict(item) for item in (rows or ())]
        triggered = ctx.triggered_id
        if not isinstance(triggered, dict):
            return no_update
        if triggered.get("type") == "q-form-grid-add":
            return [*current, {"key": "", "value": ""}]
        if triggered.get("type") == "q-form-grid-remove":
            selected_rows = [dict(item) for item in (selected or ())]
            if not selected_rows:
                return current
            return [item for item in current if item not in selected_rows]
        return no_update


__all__ = ["register_form_component_callbacks"]
