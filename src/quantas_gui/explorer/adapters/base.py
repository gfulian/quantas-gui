"""Base module adapter for the Results Explorer.

Adapters may call only functions exposed by a public ``quantas.api``
namespace.  They never import ``quantas.modules`` or renderer implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor


@dataclass(slots=True)
class GuiPlotCollection:
    """Small structural PlotCollection used when a public API returns one spec."""

    plots: list[Any]
    warnings: list[str]


class ResultModuleAdapter:
    """Generic adapter used when a module does not need special presentation."""

    name = "generic"

    def table_families(
        self,
        namespace: Any,
        result: Any,
    ) -> tuple[TableFamilyDescriptor, ...]:
        """Return report families supported by this result."""
        del namespace, result
        return (
            TableFamilyDescriptor(
                key="default",
                title="Report",
                description="Frontend-neutral report tables exposed by Quantas.",
                default=True,
            ),
        )

    def build_tables(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
    ) -> tuple[Any, ...]:
        """Build one report family."""
        if family_key != "default":
            raise KeyError(f"unknown report family {family_key!r}")
        return tuple(namespace.build_report(result))

    def plot_families(
        self,
        namespace: Any,
        result: Any,
    ) -> tuple[PlotFamilyDescriptor, ...]:
        """Return the default plot family exposed by a public namespace."""
        del result
        if not hasattr(namespace, "build_plots"):
            return ()
        return (
            PlotFamilyDescriptor(
                key="default",
                title="Available plots",
                description="Default plot specifications exposed by Quantas.",
                default=True,
                cost="moderate",
            ),
        )

    def build_plots(
        self,
        namespace: Any,
        result: Any,
        family_key: str,
    ) -> Any:
        """Build one plot family."""
        if family_key != "default":
            raise KeyError(f"unknown plot family {family_key!r}")
        return namespace.build_plots(result)

    def table_group(self, title: str) -> str:
        """Return a compact table-group label."""
        del title
        return "Report"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        """Return a compact plot-group label."""
        del title, family_key
        return _kind_label(kind)

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        """Return a short plot explanation."""
        del family_key
        return f"{title} rendered from a frontend-neutral {kind}."


def _kind_label(kind: str) -> str:
    return {
        "LinePlotSpec": "Line",
        "ContourPlotSpec": "Contour",
        "PolarPlotSpec": "Polar",
        "SurfacePlotSpec": "3D surface",
        "SphericalMapSpec": "Spherical map",
        "SphericalSummarySpec": "Spherical summary",
        "PanelPlotSpec": "Panels",
    }.get(kind, kind.removesuffix("PlotSpec") or "Plot")
