"""Module-aware presentation for directional seismic results."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import GuiPlotCollection, ResultModuleAdapter
from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor


class SeismicAdapter(ResultModuleAdapter):
    """Separate spherical maps, compact summaries, and 3D surfaces."""

    name = "seismic"

    def table_families(self, namespace: Any, result: Any) -> tuple[TableFamilyDescriptor, ...]:
        del namespace, result
        return (
            TableFamilyDescriptor(
                "standard",
                "Standard report",
                "Compact isotropic values, extrema, and anisotropy summaries.",
            ),
            TableFamilyDescriptor(
                "extended",
                "Extended report",
                "Wave-property tables and detailed directional extrema.",
                default=True,
                cost="moderate",
            ),
            TableFamilyDescriptor(
                "debug",
                "Debug report",
                "Numerical diagnostics, degeneracies, and enhancement details.",
                cost="moderate",
            ),
        )

    def build_tables(self, namespace: Any, result: Any, family_key: str) -> tuple[Any, ...]:
        if family_key not in {"standard", "extended", "debug"}:
            raise KeyError(f"unknown SEISMIC report family {family_key!r}")
        return tuple(namespace.build_report(result, level=family_key))

    def plot_families(self, namespace: Any, result: Any) -> tuple[PlotFamilyDescriptor, ...]:
        del namespace, result
        return (
            PlotFamilyDescriptor(
                "maps",
                "Spherical maps",
                "Interactive equal-area maps of phase, group, enhancement, and anisotropy fields.",
                default=True,
                cost="moderate",
                icon="◉",
            ),
            PlotFamilyDescriptor(
                "summary",
                "Extrema and anisotropy summary",
                "Faceted directional summary with extrema markers and anisotropy metadata.",
                cost="moderate",
                icon="⌖",
            ),
            PlotFamilyDescriptor(
                "surfaces",
                "3D wave surfaces",
                "Rotatable phase/group velocity and enhancement surfaces.",
                cost="high",
                icon="⬡",
            ),
        )

    def build_plots(self, namespace: Any, result: Any, family_key: str) -> Any:
        if family_key == "maps":
            return namespace.build_plots(result)
        if family_key == "summary":
            return GuiPlotCollection(plots=[namespace.build_summary(result)], warnings=[])
        if family_key == "surfaces":
            return namespace.build_surfaces(result)
        raise KeyError(f"unknown SEISMIC plot family {family_key!r}")

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        descriptions = {
            "maps": "directional wave field projected onto an interactive hemisphere",
            "summary": "extrema, directions, and anisotropy collected in a faceted summary",
            "surfaces": "rotatable physical-radius wave surface with optional vector fields",
        }
        return f"{title}: {descriptions[family_key]}."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "isotropic" in normalized:
            return "Reference"
        if "extrem" in normalized or "anisotrop" in normalized:
            return "Directional"
        if "degener" in normalized or "caustic" in normalized or "enhancement" in normalized:
            return "Diagnostics"
        return "Wave field"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return {"maps": "Spherical map", "summary": "Summary", "surfaces": "3D surface"}[family_key]
