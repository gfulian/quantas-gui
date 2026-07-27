"""Module-aware presentation for harmonic thermodynamics."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter
from quantas_gui.explorer.models import PlotFamilyDescriptor


class HAAdapter(ResultModuleAdapter):
    """Expose harmonic thermodynamic curves as one coherent family."""

    name = "ha"

    def plot_families(self, namespace: Any, result: Any) -> tuple[PlotFamilyDescriptor, ...]:
        del namespace, result
        return (
            PlotFamilyDescriptor(
                "thermodynamics",
                "Thermodynamic functions",
                (
                    "Temperature-dependent vibrational energy, free energy, "
                    "entropy, and heat capacity."
                ),
                default=True,
                cost="low",
                icon="∿",
            ),
        )

    def build_plots(self, namespace: Any, result: Any, family_key: str) -> Any:
        if family_key != "thermodynamics":
            raise KeyError(f"unknown HA plot family {family_key!r}")
        return namespace.build_plots(result)

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind, family_key
        return f"{title}: temperature-dependent harmonic vibrational thermodynamics."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "thermo" in normalized or "heat" in normalized or "entropy" in normalized:
            return "Thermodynamics"
        if "frequency" in normalized or "mode" in normalized:
            return "Vibrations"
        return "HA"
