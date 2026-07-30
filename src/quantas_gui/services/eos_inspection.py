"""Read-only EOS archive inventories and report-table presentation.

This module consumes only public :mod:`quantas.api.eos` archive objects. It
keeps the generic result gateway focused on lifecycle dispatch while EOS
retains its session-oriented structure.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import Any

from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor
from quantas_gui.models.results import TableData
from quantas_gui.presentation.scientific_labels import scientific_label_text


def eos_table_families(inventory: Any) -> tuple[TableFamilyDescriptor, ...]:
    """Return archive and immutable-record report families."""
    families: list[TableFamilyDescriptor] = [
        TableFamilyDescriptor(
            key="summary",
            title="Archive summary",
            description="Read-only EOS archive identity and selection state.",
            default=True,
        ),
        TableFamilyDescriptor(
            key="datasets",
            title="Datasets",
            description="Embedded dataset metadata and scientific coordinate coverage.",
        ),
        TableFamilyDescriptor(
            key="slots",
            title="Result slots",
            description="Persistent domain/target slots and accepted-record state.",
        ),
        TableFamilyDescriptor(
            key="records",
            title="Fit history",
            description="Immutable accepted, rejected, superseded, and failed records.",
        ),
    ]
    for record in inventory.records:
        status = "accepted" if record.current_accepted else enum_text(record.disposition)
        families.append(
            TableFamilyDescriptor(
                key=encode_eos_record_family(record.record_id),
                title=(
                    f"Fit record #{record.record_id} · {record.model_tag} · "
                    f"{scientific_label_text(record.target)}"
                ),
                description=(
                    f"Read-only {record.domain.value.upper()} fit details for "
                    f"{record.slot_key} ({status}), including parameters, covariance, "
                    "quality metrics, and solver diagnostics."
                ),
                cost="low",
            )
        )
    return tuple(families)


def build_eos_tables(
    eos: Any,
    path: Path,
    inventory: Any,
    family_key: str | None,
) -> tuple[TableData, ...]:
    """Build one read-only EOS archive or immutable-record report family."""
    selected = family_key or "summary"
    if selected == "summary":
        return (
            TableData(
                title="EOS archive summary",
                columns=["Property", "Value"],
                rows=[
                    ["Schema version", inventory.schema_version],
                    ["Datasets", len(inventory.datasets)],
                    ["Result slots", len(inventory.slots)],
                    ["Fit records", len(inventory.records)],
                    ["Events", inventory.event_count],
                    ["Selected record", inventory.selected_record_id],
                    ["Warnings", len(inventory.warnings)],
                ],
                metadata={"kind": "eos-archive-summary", "read_only": True},
            ),
        )
    if selected == "datasets":
        return (
            TableData(
                title="EOS datasets",
                columns=[
                    "ID",
                    "Job name",
                    "Points",
                    "Selected",
                    "Excluded",
                    "Variables",
                    "Constants",
                    "Supported slots",
                ],
                rows=[
                    [
                        item.dataset_id,
                        item.jobname,
                        item.npoints,
                        item.selected_npoints,
                        item.excluded_npoints,
                        ", ".join(item.variable_coordinates),
                        ", ".join(item.constant_coordinates),
                        ", ".join(item.slot_keys),
                    ]
                    for item in inventory.datasets
                ],
                metadata={"kind": "eos-datasets", "read_only": True},
            ),
        )
    if selected == "slots":
        return (
            TableData(
                title="EOS result slots",
                columns=[
                    "Slot",
                    "Domain",
                    "Target",
                    "Status",
                    "Accepted record",
                    "Last record",
                    "History",
                    "Plottable records",
                ],
                rows=[
                    [
                        item.key,
                        enum_text(item.domain),
                        scientific_label_text(item.target),
                        enum_text(item.status),
                        item.accepted_record_id,
                        item.last_record_id,
                        ", ".join(str(value) for value in item.record_ids),
                        ", ".join(str(value) for value in item.plottable_record_ids),
                    ]
                    for item in inventory.slots
                ],
                metadata={"kind": "eos-slots", "read_only": True},
            ),
        )
    if selected == "records":
        return (
            TableData(
                title="EOS fit history",
                columns=[
                    "Record",
                    "Dataset",
                    "Slot",
                    "Model",
                    "Fit status",
                    "Disposition",
                    "Accepted",
                    "Representations",
                ],
                rows=[
                    [
                        item.record_id,
                        item.dataset_id,
                        item.slot_key,
                        item.model_tag,
                        item.fit_status,
                        enum_text(item.disposition),
                        item.current_accepted,
                        ", ".join(item.representation_keys),
                    ]
                    for item in inventory.records
                ],
                metadata={"kind": "eos-records", "read_only": True},
            ),
        )
    if selected.startswith("fit_record_"):
        record_id = decode_eos_record_family(selected)
        known_ids = {int(item.record_id) for item in inventory.records}
        if record_id not in known_ids:
            raise KeyError(f"unknown EOS fit record {record_id}")
        with eos.open_archive(path, writable=False) as archive:
            inspection = archive.inspect_record(record_id)
            dataset = archive.dataset(inspection.record.dataset_id)
        return eos_record_tables(inspection, dataset)
    raise KeyError(f"unknown EOS report family {selected!r}")


def eos_record_tables(inspection: Any, dataset: Any) -> tuple[TableData, ...]:
    """Translate one public immutable EOS record into GUI report tables."""
    record = inspection.record
    request = record.request
    result = record.result
    fit = result.fit
    request_data = request.as_dict()
    model_data = dict(request_data.get("model", {}))
    options_data = dict(request_data.get("options", {}))
    solver_data = dict(options_data.get("solver_options", {}))
    metadata = dict(result.metadata)
    relationship = metadata.get("relationship")
    target_unit = eos_target_unit(dataset, request.target, metadata)
    model_name = model_data.get("name") or model_data.get("tag") or str(request.model)

    identity_rows: list[list[Any]] = [
        ["Record", record.record_id],
        ["Disposition", enum_text(inspection.disposition)],
        ["Current accepted result", inspection.is_current_accepted],
        ["Dataset", record.dataset_id],
        ["Dataset job name", str(dataset.jobname)],
        ["Result slot", record.slot.key],
        ["Fit domain", request.domain.value],
        ["Fitted target", scientific_label_text(request.target)],
        ["Target unit", scientific_label_text(target_unit) if target_unit else None],
        ["Relationship", relationship],
        ["EOS model", model_name],
        ["Model tag", model_data.get("tag")],
        ["Model family", model_data.get("family")],
        ["EOS order", model_data.get("order")],
        ["Fit method", None if fit.method is None else fit.method.value],
        ["Solver", solver_data.get("type")],
        ["Allow extrapolation", options_data.get("allow_extrapolation")],
        ["Parent record", record.parent_record_id],
        ["Created at", record.created_at.isoformat()],
    ]
    identity = TableData(
        title=f"EOS fit record #{record.record_id}",
        columns=["Property", "Value"],
        rows=[row for row in identity_rows if row[1] is not None],
        metadata={"kind": "eos-fit-identity", "read_only": True},
    )

    parameter_definitions = eos_parameter_definitions(result)
    parameters = tuple(fit.parameter_names)
    values = () if fit.parameters is None else tuple(float(item) for item in fit.parameters)
    errors = () if fit.errors is None else tuple(float(item) for item in fit.errors)
    states = tuple(enum_text(item) for item in fit.parameter_states)
    parameter_rows: list[list[Any]] = []
    for index, name in enumerate(parameters):
        definition = parameter_definitions.get(str(name), {})
        parameter_rows.append(
            [
                eos_parameter_label(str(name)),
                values[index] if index < len(values) else None,
                errors[index] if index < len(errors) else None,
                states[index] if index < len(states) else definition.get("state"),
                scientific_label_text(definition.get("unit", "")),
                definition.get("description"),
                finite_or_text(definition.get("initial_value")),
                finite_or_text(definition.get("lower_bound")),
                finite_or_text(definition.get("upper_bound")),
            ]
        )
    parameter_table = TableData(
        title="EOS fitted parameters",
        columns=[
            "Parameter",
            "Value",
            "Uncertainty",
            "State",
            "Unit",
            "Description",
            "Initial value",
            "Lower bound",
            "Upper bound",
        ],
        rows=parameter_rows,
        metadata={
            "kind": "eos-fit-parameters",
            "read_only": True,
            "column_formats": [
                None,
                "general",
                "uncertainty",
                None,
                None,
                None,
                "general",
                "general",
                "general",
            ],
        },
    )

    diagnostics = fit.diagnostics
    quality_rows: list[list[Any]] = [
        ["Successful", fit.success],
        ["Status", fit.status.value],
        ["Quality", fit.quality.value],
        ["Message", fit.message],
        ["Number of observations", fit.n_points],
        ["Number of fitted parameters", fit.n_parameters],
        ["Degrees of freedom", fit.dof],
        ["RMSE", fit.rmse],
        ["MAE", fit.mae],
        ["Maximum absolute error", fit.max_abs_error],
        ["R²", fit.r_squared],
        ["Condition number", fit.condition_number],
    ]
    if diagnostics is not None:
        quality_rows.extend(
            [
                ["Objective", diagnostics.objective],
                ["Weighted fit", diagnostics.weighted],
                ["χ²", diagnostics.chi_square],
                ["Reduced χ²", diagnostics.reduced_chi_square],
                ["Jacobian rank", diagnostics.jacobian_rank],
                ["Diagnostic condition number", diagnostics.condition_number],
                ["Iterations", diagnostics.n_iterations],
                ["Function evaluations", diagnostics.n_evaluations],
                ["Stop reason", diagnostics.stop_reason],
            ]
        )
    quality = TableData(
        title="EOS fit quality and diagnostics",
        columns=["Metric", "Value"],
        rows=[row for row in quality_rows if row[1] not in (None, "")],
        metadata={"kind": "eos-fit-quality", "read_only": True},
    )

    tables: list[TableData] = [identity, parameter_table, quality]
    if fit.covariance is not None and parameters:
        tables.append(
            eos_matrix_table(
                "EOS parameter covariance",
                parameters,
                fit.covariance,
                kind="eos-fit-covariance",
                number_format="eos_covariance",
            )
        )
    if diagnostics is not None and diagnostics.correlation is not None and parameters:
        tables.append(
            eos_matrix_table(
                "EOS parameter correlation",
                parameters,
                diagnostics.correlation,
                kind="eos-fit-correlation",
                number_format="eos_correlation",
            )
        )
    if result.derived:
        tables.append(
            TableData(
                title="EOS derived quantities",
                columns=["Quantity", "Value"],
                rows=[
                    [scientific_label_text(name), float(value)]
                    for name, value in result.derived.items()
                ],
                metadata={"kind": "eos-fit-derived", "read_only": True},
            )
        )
    warnings = [*result.warnings, *fit.warnings]
    if diagnostics is not None:
        warnings.extend(diagnostics.warnings)
    unique_warnings = tuple(dict.fromkeys(str(item) for item in warnings if str(item)))
    if unique_warnings:
        tables.append(
            TableData(
                title="EOS fit warnings",
                columns=["Warning"],
                rows=[[item] for item in unique_warnings],
                metadata={"kind": "eos-fit-warnings", "read_only": True},
            )
        )
    return tuple(tables)


def eos_parameter_definitions(result: Any) -> dict[str, dict[str, Any]]:
    """Return public parameter metadata keyed by stable parameter name."""
    parameter_map = dict(getattr(result, "metadata", {}) or {}).get("parameter_map", {})
    definitions = dict(parameter_map).get("definitions", ()) if parameter_map else ()
    return {
        str(item.get("name")): dict(item)
        for item in definitions
        if isinstance(item, dict) and item.get("name") is not None
    }


def eos_parameter_label(name: str) -> str:
    """Return a compact mathematical label for one public EOS parameter name."""
    special = {
        "KP": "K′",
        "KPP": "K″",
        "temperature_ref": "Tᵣₑꜰ",
        "dK0_dT": "dK₀/dT",
    }
    if name in special:
        return special[name]
    greek = {"alpha": r"\alpha", "gamma": r"\gamma", "theta": r"\theta"}
    match = re.fullmatch(r"(?P<base>[A-Za-z]+)(?P<index>\d+)", name)
    if match is not None:
        base = greek.get(match.group("base"), match.group("base"))
        return scientific_label_text(f"{base}_{{{match.group('index')}}}")
    return scientific_label_text(name)


def eos_target_unit(dataset: Any, target: str, metadata: dict[str, Any]) -> str | None:
    """Return the archived target unit without inferring a scientific conversion."""
    units = dict(getattr(dataset, "units", {}) or {})
    if target in units:
        return str(units[target])
    if target == "volume" and metadata.get("volume_unit") is not None:
        return str(metadata["volume_unit"])
    if target == "energy" and metadata.get("energy_unit") is not None:
        return str(metadata["energy_unit"])
    return None


def eos_matrix_table(
    title: str,
    parameter_names: tuple[str, ...],
    values: Any,
    *,
    kind: str,
    number_format: str,
) -> TableData:
    """Return one square parameter matrix with explicit row and column labels."""
    matrix = values.tolist() if hasattr(values, "tolist") else values
    labels = [eos_parameter_label(name) for name in parameter_names]
    return TableData(
        title=title,
        columns=["Parameter", *labels],
        rows=[
            [labels[index], *[float(value) for value in row]] for index, row in enumerate(matrix)
        ],
        metadata={
            "kind": kind,
            "read_only": True,
            "column_formats": [None, *[number_format for _ in labels]],
        },
    )


def finite_or_text(value: Any) -> Any:
    """Keep finite numbers numeric and represent open bounds explicitly."""
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return value
    if isfinite(numeric):
        return numeric
    return "+∞" if numeric > 0.0 else "−∞"


def encode_eos_record_family(record_id: int) -> str:
    return f"fit_record_{int(record_id)}"


def decode_eos_record_family(value: str) -> int:
    prefix = "fit_record_"
    if not str(value).startswith(prefix):
        raise KeyError(f"invalid EOS report family {value!r}")
    try:
        record_id = int(str(value).removeprefix(prefix))
    except ValueError as exc:
        raise KeyError(f"invalid EOS report family {value!r}") from exc
    if record_id <= 0:
        raise KeyError(f"invalid EOS report family {value!r}")
    return record_id


def eos_plot_families(inventory: Any) -> tuple[PlotFamilyDescriptor, ...]:
    families: list[PlotFamilyDescriptor] = []
    selected_record_id = inventory.selected_record_id
    if selected_record_id is None and any(item.plottable for item in inventory.records):
        families.append(
            PlotFamilyDescriptor(
                key="eos_select_record",
                title="Select record and representation",
                description=(
                    "This archive has no unique accepted record. Choose one immutable "
                    "record explicitly before building a diagnostic."
                ),
                default=True,
                cost="low",
                icon="…",
                constraints=("Explicit EOS record selection is required.",),
            )
        )
    for record in inventory.records:
        if not record.plottable:
            continue
        for representation_key in record.representation_keys:
            default = record.record_id == selected_record_id and not any(
                item.default for item in families
            )
            families.append(
                PlotFamilyDescriptor(
                    key=encode_eos_plot_family(record.record_id, representation_key),
                    title=(
                        f"Record #{record.record_id} · "
                        f"{representation_key.replace('_', ' ').title()}"
                    ),
                    description=(
                        f"Read-only {record.slot_key} {record.model_tag} representation "
                        f"from immutable record #{record.record_id}."
                    ),
                    default=default,
                    cost="moderate",
                    icon="◇",
                    constraints=(
                        "EOS archive inspection is read-only.",
                        "The selected immutable record is passed explicitly to Quantas.",
                    ),
                )
            )
    return tuple(families)


def encode_eos_plot_family(record_id: int, representation_key: str) -> str:
    return f"record_{int(record_id)}__{representation_key}"


def decode_eos_plot_family(value: str) -> tuple[int, str]:
    prefix, separator, representation_key = str(value).partition("__")
    if not separator or not prefix.startswith("record_") or not representation_key:
        raise KeyError(f"invalid EOS plot family {value!r}")
    try:
        record_id = int(prefix.removeprefix("record_"))
    except ValueError as exc:
        raise KeyError(f"invalid EOS plot family {value!r}") from exc
    if record_id <= 0:
        raise KeyError(f"invalid EOS plot family {value!r}")
    return record_id, representation_key


def enum_text(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def render_structural_tables(tables: Sequence[Any]) -> str:
    """Render GUI-owned structural tables for archive-only workflows."""
    blocks: list[str] = []
    for table in tables:
        columns = [str(item) for item in table.columns]
        rows = [["" if value is None else str(value) for value in row] for row in table.rows]
        widths = [len(column) for column in columns]
        for row in rows:
            for index, value in enumerate(row[: len(widths)]):
                widths[index] = max(widths[index], len(value))
        heading = " ".join(value.ljust(widths[index]) for index, value in enumerate(columns))
        lines = [str(table.title), heading]
        lines.append(" ".join("-" * width for width in widths))
        for row in rows:
            padded = row + [""] * (len(widths) - len(row))
            lines.append(
                " ".join(
                    value.ljust(widths[index]) for index, value in enumerate(padded[: len(widths)])
                )
            )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
