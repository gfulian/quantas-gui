"""Module-aware presentation for second-order elasticity results."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter
from quantas_gui.explorer.models import PlotFamilyDescriptor


class ElasticityAdapter(ResultModuleAdapter):
    """Expose stored polar data and on-demand 3D elasticity surfaces."""

    name = "elasticity"

    def plot_families(
        self,
        namespace: Any,
        result: Any,
    ) -> tuple[PlotFamilyDescriptor, ...]:
        payload = namespace.get_result(result)
        families: list[PlotFamilyDescriptor] = []
        if bool(getattr(payload, "properties_2d", {})):
            families.append(
                PlotFamilyDescriptor(
                    key="polar-2d",
                    title="Directional properties · 2D polar",
                    description=(
                        "Principal-plane polar diagrams for Young's modulus, "
                        "compressibility, shear modulus, and Poisson's ratio."
                    ),
                    default=True,
                    cost="low",
                    icon="◉",
                )
            )
        families.append(
            PlotFamilyDescriptor(
                key="surface-3d",
                title="Directional properties · 3D surfaces",
                description=(
                    "Interactive physical-radius surfaces calculated from the "
                    "stored stiffness tensor."
                ),
                default=not families,
                cost="high",
                icon="⬡",
            )
        )
        return tuple(families)

    def build_plots(self, namespace: Any, result: Any, family_key: str) -> Any:
        if family_key == "polar-2d":
            return namespace.build_2d_plots(result)
        if family_key == "surface-3d":
            return namespace.build_3d_plots(result)
        raise KeyError(f"unknown elasticity plot family {family_key!r}")

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        if family_key == "polar-2d":
            return f"{title}: directional variation in archived principal-plane sections."
        return (
            f"{title}: physical-radius directional surface computed from the "
            "stored stiffness tensor."
        )

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "stiffness" in normalized or "compliance" in normalized:
            return "Tensor"
        if "average" in normalized or "voigt" in normalized or "reuss" in normalized:
            return "Polycrystal"
        if "stability" in normalized:
            return "Stability"
        if "variation" in normalized:
            return "Directional"
        return "Elasticity"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return "2D polar" if family_key == "polar-2d" else "3D surface"
