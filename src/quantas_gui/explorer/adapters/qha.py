"""Module-aware presentation for quasi-harmonic thermodynamics."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import GuiPlotCollection, ResultModuleAdapter
from quantas_gui.explorer.models import PlotFamilyDescriptor


class QHAAdapter(ResultModuleAdapter):
    """Separate one-dimensional thermodynamic curves from P-T contours."""

    name = "qha"

    def plot_families(self, namespace: Any, result: Any) -> tuple[PlotFamilyDescriptor, ...]:
        payload = namespace.get_result(result)
        pressure = getattr(payload, "pressure", ())
        temperature = getattr(payload, "temperature", ())
        families = [
            PlotFamilyDescriptor(
                "curves",
                "Thermodynamic curves",
                "One-dimensional pressure or temperature sections for available QHA properties.",
                default=True,
                cost="moderate",
                icon="∿",
            )
        ]
        if (
            getattr(pressure, "size", len(pressure)) > 1
            and getattr(temperature, "size", len(temperature)) > 1
        ):
            families.append(
                PlotFamilyDescriptor(
                    "contours",
                    "Pressure–temperature contours",
                    "Interactive two-dimensional maps over the archived P-T domain.",
                    cost="moderate",
                    icon="▦",
                )
            )
        return tuple(families)

    def build_plots(self, namespace: Any, result: Any, family_key: str) -> Any:
        if family_key == "curves":
            collection = namespace.build_plots(
                result,
                options=namespace.PlotOptions(include_contours=False),
            )
            return _filtered_collection(collection, exclude={"ContourPlotSpec"})
        if family_key == "contours":
            collection = namespace.build_plots(
                result,
                options=namespace.PlotOptions(include_contours=True),
            )
            return _filtered_collection(collection, include={"ContourPlotSpec"})
        raise KeyError(f"unknown QHA plot family {family_key!r}")

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        if family_key == "contours":
            return f"{title}: property variation over the archived pressure-temperature domain."
        return f"{title}: one-dimensional QHA section built from the archived equilibrium state."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "equilibrium" in normalized or "volume" in normalized or "density" in normalized:
            return "Equilibrium"
        if "fit" in normalized or "residual" in normalized or "diagnostic" in normalized:
            return "Fit diagnostics"
        if "grüneisen" in normalized or "gruneisen" in normalized:
            return "Grüneisen"
        return "Thermodynamics"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return "P-T contour" if family_key == "contours" else "Thermodynamic curve"


def _filtered_collection(
    collection: Any,
    *,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> GuiPlotCollection:
    selected = []
    for plot in getattr(collection, "plots", ()):
        kind = type(plot).__name__
        if include is not None and kind not in include:
            continue
        if exclude is not None and kind in exclude:
            continue
        selected.append(plot)
    return GuiPlotCollection(
        plots=selected,
        warnings=[str(item) for item in getattr(collection, "warnings", ())],
    )
