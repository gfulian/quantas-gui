"""Dash renderer for frontend-neutral Quantas GUI form schemas."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import dash_ag_grid as dag
from dash import dcc, html

from quantas_gui.components.controls import action_button

from .ids import FormIds
from .schema import (
    BooleanField,
    Choice,
    ChoiceField,
    FieldKind,
    FieldSpec,
    FileUploadField,
    FormSchema,
    FormSection,
    KeyValueField,
    MatrixField,
    NumericField,
    RangeTripletField,
    SliderField,
    TagsField,
    TextField,
    VectorField,
)
from .values import key_value_to_row_data, matrix_to_row_data


def render_form(schema: FormSchema, *, actions: bool = True) -> html.Div:
    """Render a complete declarative form.

    Parameters
    ----------
    schema
        Frontend-neutral form definition.
    actions
        Whether to append reset and submit actions.

    Returns
    -------
    dash.html.Div
        Rendered form shell.
    """
    children: list[Any] = [
        html.Div(
            [
                html.Div("Configuration", className="q-eyebrow"),
                html.H2(schema.title),
                html.P(schema.description) if schema.description else None,
            ],
            className="q-form-heading",
        ),
        html.Div(id=FormIds.summary(schema.key), className="q-form-summary"),
        *[render_section(schema.key, section) for section in schema.sections],
    ]
    if actions:
        children.append(
            html.Div(
                [
                    action_button(
                        schema.reset_label,
                        component_id=FormIds.reset(schema.key),
                    ),
                    action_button(
                        schema.submit_label,
                        component_id=FormIds.submit(schema.key),
                        primary=True,
                    ),
                ],
                className="q-form-actions",
            )
        )
    return html.Div(children, className="q-form", id=f"q-form-{schema.key}")


def render_section(form_key: str, section: FormSection) -> Any:
    """Render one logical form section."""
    body = html.Div(
        [render_field(form_key, field) for field in section.fields],
        className="q-form-grid",
    )
    heading = [
        html.Div(
            [
                html.H3(section.title),
                html.Span("Advanced", className="q-field-badge") if section.advanced else None,
            ],
            className="q-form-section-title",
        ),
        html.P(section.description, className="q-form-section-description")
        if section.description
        else None,
    ]
    class_name = "q-form-section q-panel"
    if section.advanced:
        class_name += " q-form-section--advanced"
    if section.presentation == "details":
        return html.Details(
            [html.Summary(heading), body],
            id=FormIds.section(form_key, section.key),
            className=class_name,
            open=not section.collapsed,
        )
    return html.Section(
        [*heading, body],
        id=FormIds.section(form_key, section.key),
        className=class_name,
    )


def render_field(form_key: str, field: FieldSpec) -> html.Div:
    """Render one field with label, help, unit, and validation slot."""
    control = _render_control(form_key, field)
    classes = ["q-field", f"q-field--{field.width}", f"q-field--{field.kind.value}"]
    if field.advanced:
        classes.append("q-field--advanced")
    label_children: list[Any] = [html.Span(field.label)]
    if field.required:
        label_children.append(html.Span("Required", className="q-field-required"))
    if field.advanced:
        label_children.append(html.Span("Advanced", className="q-field-badge"))
    if field.unit:
        label_children.append(html.Span(field.unit, className="q-field-unit"))

    return html.Div(
        [
            html.Div(label_children, className="q-field-label"),
            control,
            html.P(field.description, className="q-field-help") if field.description else None,
            html.Div(id=FormIds.error(form_key, field.key), className="q-field-error"),
        ],
        id=FormIds.wrapper(form_key, field.key),
        className=" ".join(classes),
        **{"data-field": field.key},
    )


def _render_control(form_key: str, field: FieldSpec) -> Any:
    if isinstance(field, TextField):
        return _text_control(form_key, field)
    if isinstance(field, NumericField):
        return _numeric_control(form_key, field)
    if isinstance(field, BooleanField):
        return _boolean_control(form_key, field)
    if isinstance(field, ChoiceField):
        return _choice_control(form_key, field)
    if isinstance(field, SliderField):
        return _slider_control(form_key, field)
    if isinstance(field, RangeTripletField):
        return _range_triplet_control(form_key, field)
    if isinstance(field, VectorField):
        return _vector_control(form_key, field)
    if isinstance(field, MatrixField):
        return _matrix_control(form_key, field)
    if isinstance(field, FileUploadField):
        return _upload_control(form_key, field)
    if isinstance(field, TagsField):
        return _tags_control(form_key, field)
    if isinstance(field, KeyValueField):
        return _key_value_control(form_key, field)
    raise TypeError(f"unsupported form field: {type(field).__name__}")


def _text_control(form_key: str, field: TextField) -> Any:
    common = {
        "id": FormIds.control(form_key, field.key),
        "value": field.default,
        "placeholder": field.placeholder,
        "disabled": field.disabled,
        "persistence": field.persistence,
        "persistence_type": field.persistence_type,
    }
    if field.multiline or field.kind is FieldKind.TEXTAREA:
        return dcc.Textarea(
            **common,
            rows=field.rows,
            maxLength=field.max_length,
            className="q-input q-textarea",
        )
    return dcc.Input(
        **common,
        type="text",
        debounce=field.debounce,
        maxLength=field.max_length,
        className="q-input",
    )


def _numeric_control(form_key: str, field: NumericField) -> dcc.Input:
    bounds = field.bounds
    kwargs: dict[str, Any] = {
        "id": FormIds.control(form_key, field.key),
        "value": field.default,
        "placeholder": field.placeholder,
        "disabled": field.disabled,
        "debounce": field.debounce,
        "className": "q-input q-number-input",
        "persistence": field.persistence,
        "persistence_type": field.persistence_type,
    }
    if field.scientific:
        kwargs.update(type="text", inputMode="verbatim")
    else:
        kwargs.update(
            type="number",
            min=bounds.minimum,
            max=bounds.maximum,
            step=(1 if field.kind is FieldKind.INTEGER and bounds.step is None else bounds.step),
        )
    return dcc.Input(**kwargs)


def _boolean_control(form_key: str, field: BooleanField) -> dcc.Checklist:
    selected = ["enabled"] if bool(field.default) else []
    class_name = "q-boolean q-boolean--switch" if field.presentation == "switch" else "q-boolean"
    return dcc.Checklist(
        id=FormIds.control(form_key, field.key),
        options=[
            {
                "label": field.true_label,
                "value": "enabled",
                "disabled": field.disabled,
            }
        ],
        value=selected,
        className=class_name,
        persistence=field.persistence,
        persistence_type=field.persistence_type,
    )


def _choice_control(form_key: str, field: ChoiceField) -> Any:
    value = (
        list(field.default or ())
        if field.kind in {FieldKind.MULTI_SELECT, FieldKind.CHECKLIST}
        else field.default
    )
    identity = {
        "id": FormIds.control(form_key, field.key),
        "value": value,
        "persistence": field.persistence,
        "persistence_type": field.persistence_type,
    }
    if field.kind is FieldKind.RADIO:
        return dcc.RadioItems(
            **identity,
            options=[
                _choice_option(choice, force_disabled=field.disabled)
                for choice in field.choices
            ],
            inline=field.inline,
            className="q-radio-group",
        )
    if field.kind is FieldKind.CHECKLIST:
        return dcc.Checklist(
            **identity,
            options=[
                _choice_option(choice, force_disabled=field.disabled)
                for choice in field.choices
            ],
            inline=field.inline,
            className="q-checklist",
        )
    return dcc.Dropdown(
        **identity,
        options=[_choice_option(choice) for choice in field.choices],
        disabled=field.disabled,
        multi=field.kind is FieldKind.MULTI_SELECT,
        clearable=field.clearable,
        searchable=field.searchable,
        placeholder=field.placeholder,
        className="q-dropdown",
    )


def _slider_control(form_key: str, field: SliderField) -> Any:
    marks = {value: label for value, label in field.marks} or None
    common = {
        "id": FormIds.control(form_key, field.key),
        "min": field.bounds.minimum,
        "max": field.bounds.maximum,
        "step": field.bounds.step,
        "value": list(field.default)
        if field.kind is FieldKind.RANGE_SLIDER and field.default is not None
        else field.default,
        "marks": marks,
        "disabled": field.disabled,
        "tooltip": {"placement": "bottom", "always_visible": False}
        if field.tooltip
        else None,
        "persistence": field.persistence,
        "persistence_type": field.persistence_type,
        "className": "q-slider",
    }
    if field.kind is FieldKind.RANGE_SLIDER:
        return dcc.RangeSlider(**common, allowCross=False)
    return dcc.Slider(**common)


def _range_triplet_control(form_key: str, field: RangeTripletField) -> html.Div:
    values = field.default or (None, None, None)
    parts = ("start", "stop", "step")
    return html.Div(
        [
            dcc.Store(
                id=FormIds.control(form_key, field.key, "triplet-store"),
                data=list(values),
                storage_type=field.persistence_type,
            ),
            *[
                html.Label(
                    [
                        html.Span(label, className="q-subfield-label"),
                        dcc.Input(
                            id={
                                "type": "q-form-part",
                                "form": form_key,
                                "field": field.key,
                                "part": part,
                            },
                            value=value,
                            type="text" if field.scientific else "number",
                            min=None if field.scientific else field.bounds.minimum,
                            max=None if field.scientific else field.bounds.maximum,
                            step=None if field.scientific else field.bounds.step,
                            inputMode="verbatim" if field.scientific else None,
                            disabled=field.disabled,
                            className="q-input q-number-input",
                        ),
                    ],
                    className="q-subfield",
                )
                for part, label, value in zip(parts, field.labels, values, strict=True)
            ],
        ],
        className="q-composite q-composite--triplet",
    )


def _vector_control(form_key: str, field: VectorField) -> html.Div:
    values = field.default or tuple(None for _ in range(field.length))
    labels = field.labels or tuple(str(index + 1) for index in range(field.length))
    return html.Div(
        [
            dcc.Store(
                id=FormIds.control(form_key, field.key, "vector-store"),
                data=list(values),
                storage_type=field.persistence_type,
            ),
            *[
                html.Label(
                    [
                        html.Span(label, className="q-subfield-label"),
                        dcc.Input(
                            id={
                                "type": "q-form-vector-part",
                                "form": form_key,
                                "field": field.key,
                                "index": index,
                            },
                            value=value,
                            type="text" if field.scientific else "number",
                            min=None if field.scientific else field.bounds.minimum,
                            max=None if field.scientific else field.bounds.maximum,
                            step=None if field.scientific else field.bounds.step,
                            inputMode="verbatim" if field.scientific else None,
                            disabled=field.disabled,
                            className="q-input q-number-input",
                        ),
                    ],
                    className="q-subfield",
                )
                for index, (label, value) in enumerate(zip(labels, values, strict=True))
            ],
        ],
        className="q-composite q-composite--vector",
    )


def _matrix_control(form_key: str, field: MatrixField) -> html.Div:
    columns: list[dict[str, Any]] = [
        {
            "field": "__row__",
            "headerName": "",
            "editable": False,
            "pinned": "left",
            "width": 66,
            "suppressMovable": True,
        }
    ]
    for index in range(field.columns):
        label = field.column_labels[index] if field.column_labels else str(index + 1)
        editor: dict[str, Any] = {
            "field": f"c{index}",
            "headerName": label,
            "editable": not field.disabled,
            "cellDataType": "number",
            "cellEditor": "agNumberCellEditor",
            "minWidth": 82,
        }
        params: dict[str, Any] = {"showStepperButtons": False}
        if field.bounds.minimum is not None:
            params["min"] = field.bounds.minimum
        if field.bounds.maximum is not None:
            params["max"] = field.bounds.maximum
        if field.bounds.step is not None:
            params["step"] = field.bounds.step
        if field.bounds.precision is not None:
            params["precision"] = field.bounds.precision
        editor["cellEditorParams"] = params
        columns.append(editor)
    grid = dag.AgGrid(
        id=FormIds.control(form_key, field.key),
        rowData=matrix_to_row_data(field),
        columnDefs=columns,
        defaultColDef={
            "resizable": True,
            "sortable": False,
            "filter": False,
            "suppressHeaderMenuButton": True,
        },
        dashGridOptions={
            "theme": "legacy",
            "singleClickEdit": True,
            "stopEditingWhenCellsLoseFocus": True,
            "undoRedoCellEditing": True,
            "undoRedoCellEditingLimit": 25,
            "suppressClipboardPaste": not field.allow_paste,
        },
        className="ag-theme-quartz-dark q-matrix-grid",
        style={"height": f"{max(210, 48 + field.rows * 42)}px"},
    )
    badges = [
        html.Span(f"{field.rows} × {field.columns}", className="q-matrix-badge"),
        html.Span("symmetric", className="q-matrix-badge") if field.symmetric else None,
        html.Span("paste enabled", className="q-matrix-badge") if field.allow_paste else None,
    ]
    return html.Div(
        [html.Div(badges, className="q-matrix-meta"), grid],
        className="q-matrix-editor",
    )


def _upload_control(form_key: str, field: FileUploadField) -> html.Div:
    accept = ",".join(field.accept) if field.accept else None
    return html.Div(
        [
            dcc.Upload(
                id={
                    "type": "q-form-upload",
                    "form": form_key,
                    "field": field.key,
                },
                children=html.Div(
                    [
                        html.Strong("Drop files here"),
                        html.Span("or choose from this device"),
                        html.Small(
                            " · ".join(field.accept)
                            if field.accept
                            else "Supported input file"
                        ),
                    ],
                    className="q-upload-copy",
                ),
                accept=accept,
                multiple=field.multiple,
                disabled=field.disabled,
                className="q-field-upload",
            ),
            html.Div(
                id={
                    "type": "q-form-upload-list",
                    "form": form_key,
                    "field": field.key,
                },
                className="q-upload-list",
            ),
        ]
    )


def _tags_control(form_key: str, field: TagsField) -> dag.AgGrid:
    rows = [{"value": item} for item in (field.default or ())]
    if not rows:
        rows = [{"value": ""}]
    editor = (
        "agNumberCellEditor"
        if field.value_type in {"integer", "float"}
        else "agTextCellEditor"
    )
    return dag.AgGrid(
        id=FormIds.control(form_key, field.key),
        rowData=rows,
        columnDefs=[
            {
                "field": "value",
                "headerName": field.label,
                "editable": not field.disabled,
                "cellEditor": editor,
                "cellDataType": "number" if field.value_type in {"integer", "float"} else "text",
            }
        ],
        defaultColDef={"resizable": True, "sortable": False, "filter": False},
        dashGridOptions={
            "theme": "legacy",
            "singleClickEdit": True,
            "stopEditingWhenCellsLoseFocus": True,
            "undoRedoCellEditing": True,
            "rowSelection": {"mode": "multiRow"},
        },
        className="ag-theme-quartz-dark q-list-grid",
        style={"height": "210px"},
    )


def _key_value_control(form_key: str, field: KeyValueField) -> html.Div:
    editor = (
        "agNumberCellEditor"
        if field.value_type in {"integer", "float"}
        else "agTextCellEditor"
    )
    grid = dag.AgGrid(
        id=FormIds.control(form_key, field.key),
        rowData=key_value_to_row_data(field),
        columnDefs=[
            {
                "field": "key",
                "headerName": field.key_label,
                "editable": not field.disabled,
                "cellEditor": "agTextCellEditor",
                "cellDataType": "text",
            },
            {
                "field": "value",
                "headerName": field.value_label,
                "editable": not field.disabled,
                "cellEditor": editor,
                "cellDataType": "number" if field.value_type in {"integer", "float"} else "text",
            },
        ],
        defaultColDef={"resizable": True, "sortable": False, "filter": False},
        dashGridOptions={
            "theme": "legacy",
            "singleClickEdit": True,
            "stopEditingWhenCellsLoseFocus": True,
            "undoRedoCellEditing": True,
            "rowSelection": {"mode": "multiRow"},
        },
        className="ag-theme-quartz-dark q-key-value-grid",
        style={"height": "240px"},
    )
    return html.Div(
        [
            grid,
            html.Div(
                [
                    html.Button(
                        "+ Add row",
                        id={
                            "type": "q-form-grid-add",
                            "form": form_key,
                            "field": field.key,
                        },
                        className="q-button q-button--small",
                        disabled=field.disabled,
                        type="button",
                    ),
                    html.Button(
                        "Remove selected",
                        id={
                            "type": "q-form-grid-remove",
                            "form": form_key,
                            "field": field.key,
                        },
                        className="q-button q-button--small",
                        disabled=field.disabled,
                        type="button",
                    ),
                ],
                className="q-grid-actions",
            ),
        ],
        className="q-key-value-editor",
    )


def _choice_option(
    choice: Choice,
    *,
    force_disabled: bool = False,
) -> dict[str, Any]:
    return {
        "label": choice.label,
        "value": choice.value,
        "disabled": force_disabled or choice.disabled,
    }


__all__ = ["render_field", "render_form", "render_section"]
