#!/usr/bin/env python3
"""Audit the installed Quantas Click surface for GUI-control planning.

This development tool is intentionally outside the runtime package. Quantas
GUI must never import ``quantas.cli`` while serving the application; the CLI is
used only as a migration inventory and comparison reference.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import click


def _type_record(parameter_type: click.ParamType) -> dict[str, Any]:
    record: dict[str, Any] = {
        "class": type(parameter_type).__name__,
        "name": getattr(parameter_type, "name", None),
    }
    if isinstance(parameter_type, click.Choice):
        record["choices"] = list(parameter_type.choices)
        record["case_sensitive"] = parameter_type.case_sensitive
    for attribute in ("min", "max", "min_open", "max_open", "clamp"):
        if hasattr(parameter_type, attribute):
            record[attribute] = getattr(parameter_type, attribute)
    if isinstance(parameter_type, click.Path):
        for attribute in (
            "exists",
            "file_okay",
            "dir_okay",
            "writable",
            "readable",
            "resolve_path",
        ):
            record[attribute] = getattr(parameter_type, attribute)
    return record


def _parameter_record(parameter: click.Parameter) -> dict[str, Any]:
    return {
        "kind": type(parameter).__name__,
        "name": parameter.name,
        "opts": list(getattr(parameter, "opts", ())),
        "required": parameter.required,
        "default": parameter.default,
        "nargs": parameter.nargs,
        "multiple": parameter.multiple,
        "is_flag": bool(getattr(parameter, "is_flag", False)),
        "help_group": getattr(parameter, "help_group", None),
        "help": getattr(parameter, "help", None),
        "type": _type_record(parameter.type),
        "recommended_control": _recommended_control(parameter),
    }


def _recommended_control(parameter: click.Parameter) -> str:
    name = str(parameter.name or "")
    parameter_type = parameter.type
    if isinstance(parameter, click.Argument) and isinstance(parameter_type, click.Path):
        return "file-upload-or-result-reference"
    if isinstance(parameter_type, click.Path):
        if any(token in name for token in ("output", "outfile", "report", "archive")):
            return "download-name-or-workspace-reference"
        return "file-upload-or-workspace-reference"
    if bool(getattr(parameter, "is_flag", False)):
        if name in {"force", "overwrite"}:
            return "confirmation-checkbox"
        return "boolean-switch"
    if parameter.nargs == 3:
        if "rotate" in name:
            return "vector-3"
        return "range-triplet"
    if parameter.nargs > 1:
        return f"vector-{parameter.nargs}"
    if parameter.multiple:
        if isinstance(parameter_type, click.Choice):
            choices = list(parameter_type.choices)
            return "checklist" if len(choices) <= 6 else "multi-select"
        if name in {"fixed_parameters", "initial_parameters", "parameter_bounds"}:
            return "key-value-editor"
        return "repeatable-list"
    if isinstance(parameter_type, click.Choice):
        return "radio" if len(parameter_type.choices) <= 4 else "select"
    if isinstance(parameter_type, click.IntRange):
        return "integer-input"
    if isinstance(parameter_type, (click.FloatRange, click.types.FloatParamType)):
        if name in {
            "confidence",
            "opacity",
            "line_width",
            "marker_size",
            "marker_edge_width",
            "errorbar_width",
            "errorbar_capsize",
        }:
            return "bounded-slider-or-number"
        return "float-input"
    if isinstance(parameter_type, click.types.IntParamType):
        return "integer-input"
    return "text-input"


def _walk(command: click.Command, path: tuple[str, ...]) -> list[dict[str, Any]]:
    records = [
        {
            "path": " ".join(path),
            "help": command.help,
            "parameters": [
                _parameter_record(parameter)
                for parameter in command.params
                if getattr(parameter, "expose_value", True)
            ],
        }
    ]
    if isinstance(command, click.Group):
        for name, child in sorted(command.commands.items()):
            records.extend(_walk(child, (*path, name)))
    return records


def main() -> int:
    """Run the CLI audit and write a JSON inventory."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("quantas-cli-controls.json"))
    arguments = parser.parse_args()

    from quantas.cli.main import main as quantas_cli

    records = _walk(quantas_cli, ("quantas",))
    arguments.output.write_text(json.dumps(records, indent=2, default=str) + "\n")
    controls = Counter(
        parameter["recommended_control"]
        for command in records
        for parameter in command["parameters"]
    )
    print(f"commands: {len(records)}")
    print(f"parameters: {sum(len(item['parameters']) for item in records)}")
    for control, count in controls.most_common():
        print(f"{control}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
