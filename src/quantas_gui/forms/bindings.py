"""Dash callback dependencies generated from form schemas."""

from __future__ import annotations

from typing import Any

from dash import State

from .schema import FormSchema
from .values import normalize_component_value, value_component_id, value_property


def form_state_dependencies(schema: FormSchema) -> dict[str, State]:
    """Return keyword-grouped Dash ``State`` dependencies for a form.

    The returned mapping is intended for Dash flexible callback signatures::

        @callback(Output(...), Input(...), state=form_state_dependencies(schema))
        def submit(..., **raw_values):
            values = normalize_form_values(schema, raw_values)

    Parameters
    ----------
    schema
        Declarative form definition.

    Returns
    -------
    dict
        Mapping from stable field key to Dash ``State`` dependency.
    """
    return {
        field.key: State(value_component_id(schema.key, field), value_property(field))
        for field in schema.fields
    }


def normalize_form_values(
    schema: FormSchema,
    raw_values: dict[str, Any],
) -> dict[str, Any]:
    """Normalize widget-specific callback values by field specification."""
    return {
        field.key: normalize_component_value(field, raw_values.get(field.key))
        for field in schema.fields
    }


__all__ = ["form_state_dependencies", "normalize_form_values"]
