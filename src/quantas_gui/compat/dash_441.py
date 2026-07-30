"""Dash 4.4.1 component-property baseline used by Quantas GUI.

The generated Dash component classes reject unknown keyword arguments at
construction time.  Keeping the subset used by Quantas GUI in one explicit
contract makes source-level auditing possible even in environments where Dash
cannot be installed.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

DASH_BASELINE = "4.4.1"
DASH_AG_GRID_BASELINE = "35.2.0"
PLOTLY_BASELINE = "6.9.0"

# Minimal constructor arguments used only to inspect generated component
# metadata in compatibility tests and runtime audits. Some Dash components
# expose required React properties and cannot be instantiated empty even
# though the audit only needs ``available_properties``.
DASH_CORE_PROBE_ARGUMENTS: dict[str, dict[str, object]] = {
    "Link": {"href": "/"},
    "Location": {"id": "quantas-gui-compat-location"},
    "Store": {"id": "quantas-gui-compat-store"},
}

DASH_AG_GRID_PROBE_ARGUMENTS: dict[str, dict[str, object]] = {}


_REQUIRED_ARGUMENT = re.compile(r"Required argument `(?P<name>[^`]+)` was not specified\.")


def instantiate_component_probe(
    component_type: type[Any],
    explicit_arguments: Mapping[str, object] | None = None,
) -> Any:
    """Instantiate a generated Dash component for property introspection.

    Dash generated classes sometimes treat a property as required even when its
    Python signature gives it a default of ``None``.  The requirement is
    enforced through the private ``_explicit_args`` marker, so normal signature
    inspection is insufficient.  This helper starts from the project-specific
    probe arguments and, when the generated class reports another required
    property, retries with a harmless explicit value.

    Parameters
    ----------
    component_type
        Generated Dash, Dash Table, or Dash AG Grid component class.
    explicit_arguments
        Known minimal values for components such as ``Link`` and ``Location``.

    Returns
    -------
    object
        Constructed component instance exposing ``available_properties``.

    Raises
    ------
    TypeError
        If construction fails for a reason other than a missing required
        generated property, or if the same requirement is reported repeatedly.
    """
    arguments = dict(explicit_arguments or {})
    for _ in range(16):
        try:
            return component_type(**arguments)
        except TypeError as error:
            match = _REQUIRED_ARGUMENT.search(str(error))
            if match is None:
                raise
            name = match.group("name")
            if name in arguments:
                raise
            arguments[name] = _probe_value(name)
    raise TypeError(f"Unable to satisfy required arguments for {component_type!r}")


def _probe_value(name: str) -> object:
    """Return a harmless explicit value for a generated required property."""
    if name == "id":
        return "quantas-gui-component-probe"
    if name == "href":
        return "/"
    if name in {"options", "data", "rowData", "columnDefs"}:
        return []
    if name == "children":
        return ""
    return None


# Only properties intentionally used by this package are listed.  Every entry
# has been checked against the generated Python component classes shipped by
# Dash 4.4.1.  A smaller project-specific surface is easier to audit than
# copying the complete upstream API.
DASH_CORE_USED_PROPERTIES: dict[str, frozenset[str]] = {
    "Checklist": frozenset(
        {
            "id",
            "options",
            "value",
            "inline",
            "className",
            "persistence",
            "persistence_type",
        }
    ),
    "Download": frozenset({"id"}),
    "Dropdown": frozenset(
        {
            "id",
            "options",
            "value",
            "multi",
            "clearable",
            "searchable",
            "placeholder",
            "disabled",
            "className",
            "persistence",
            "persistence_type",
        }
    ),
    "Graph": frozenset({"id", "figure", "config", "className", "responsive", "mathjax"}),
    "Interval": frozenset({"id", "interval", "max_intervals", "n_intervals"}),
    "Input": frozenset(
        {
            "id",
            "value",
            "type",
            "debounce",
            "placeholder",
            "inputMode",
            "disabled",
            "min",
            "max",
            "step",
            "maxLength",
            "className",
            "persistence",
            "persistence_type",
        }
    ),
    "Link": frozenset({"id", "children", "href", "className", "title"}),
    "Loading": frozenset({"id", "children", "type", "color", "className"}),
    "Location": frozenset({"id", "refresh"}),
    "RadioItems": frozenset(
        {
            "id",
            "options",
            "value",
            "inline",
            "className",
            "inputClassName",
            "labelClassName",
            "persistence",
            "persistence_type",
        }
    ),
    "RangeSlider": frozenset(
        {
            "id",
            "min",
            "max",
            "step",
            "marks",
            "value",
            "allowCross",
            "disabled",
            "tooltip",
            "className",
            "persistence",
            "persistence_type",
        }
    ),
    "Slider": frozenset(
        {
            "id",
            "min",
            "max",
            "step",
            "marks",
            "value",
            "disabled",
            "tooltip",
            "className",
            "persistence",
            "persistence_type",
        }
    ),
    "Store": frozenset({"id", "data", "storage_type"}),
    "Tab": frozenset({"label", "value", "className", "selected_className"}),
    "Tabs": frozenset({"id", "value", "children", "className", "parent_className"}),
    "Textarea": frozenset(
        {
            "id",
            "value",
            "placeholder",
            "disabled",
            "rows",
            "maxLength",
            "className",
            "persistence",
            "persistence_type",
        }
    ),
    "Upload": frozenset({"id", "children", "accept", "multiple", "disabled", "className"}),
}

# Properties used by callbacks but not necessarily passed by constructors.
DASH_CORE_CALLBACK_PROPERTIES: dict[str, frozenset[str]] = {
    "Checklist": frozenset({"value"}),
    "Download": frozenset({"data"}),
    "Dropdown": frozenset({"value"}),
    "Graph": frozenset({"figure"}),
    "Input": frozenset({"id", "value"}),
    "Interval": frozenset({"n_intervals"}),
    "Location": frozenset({"pathname"}),
    "Store": frozenset({"data"}),
    "Tabs": frozenset({"value"}),
    "Upload": frozenset({"contents", "filename"}),
}

DASH_AG_GRID_CALLBACK_PROPERTIES: dict[str, frozenset[str]] = {
    "AgGrid": frozenset({"rowData", "selectedRows"})
}

DASH_AG_GRID_USED_PROPERTIES: dict[str, frozenset[str]] = {
    "AgGrid": frozenset(
        {
            "id",
            "rowData",
            "columnDefs",
            "defaultColDef",
            "dashGridOptions",
            "className",
            "style",
        }
    )
}

__all__ = [
    "DASH_AG_GRID_BASELINE",
    "DASH_AG_GRID_CALLBACK_PROPERTIES",
    "DASH_AG_GRID_PROBE_ARGUMENTS",
    "DASH_AG_GRID_USED_PROPERTIES",
    "DASH_BASELINE",
    "PLOTLY_BASELINE",
    "DASH_CORE_CALLBACK_PROPERTIES",
    "DASH_CORE_PROBE_ARGUMENTS",
    "DASH_CORE_USED_PROPERTIES",
    "instantiate_component_probe",
]
