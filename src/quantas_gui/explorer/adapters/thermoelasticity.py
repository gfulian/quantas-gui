"""Module-aware presentation for quasi-static thermoelasticity."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter
from quantas_gui.explorer.models import PlotFamilyDescriptor, TableFamilyDescriptor


class ThermoelasticityAdapter(ResultModuleAdapter):
    """Expose only the plot families supported by the archived workflow stage."""

    name = "thermoelasticity"

    def table_families(self, namespace: Any, result: Any) -> tuple[TableFamilyDescriptor, ...]:
        del namespace, result
        return (
            TableFamilyDescriptor(
                "standard",
                "Standard report",
                "Fit, reconstruction, stability, and provenance summaries.",
                default=True,
            ),
            TableFamilyDescriptor(
                "extended",
                "Extended report",
                "Additional uncertainty and reconstruction details.",
                cost="moderate",
            ),
            TableFamilyDescriptor(
                "debug",
                "Debug report",
                "Detailed fit diagnostics and policy decisions.",
                cost="moderate",
            ),
        )

    def build_tables(self, namespace: Any, result: Any, family_key: str) -> tuple[Any, ...]:
        if family_key not in {"standard", "extended", "debug"}:
            raise KeyError(f"unknown thermoelastic report family {family_key!r}")
        return tuple(namespace.build_report(result, level=family_key))

    def plot_families(self, namespace: Any, result: Any) -> tuple[PlotFamilyDescriptor, ...]:
        payload = namespace.get_result(result)
        families: list[PlotFamilyDescriptor] = []
        if bool(getattr(payload, "component_fits", {})):
            families.append(
                PlotFamilyDescriptor(
                    "fits",
                    "Elastic-volume fits",
                    "Observed stiffness values, fitted curves, confidence bands, and residuals.",
                    default=True,
                    cost="moderate",
                    icon="∿",
                )
            )
        temperature = getattr(payload, "temperature", ())
        pressure = getattr(payload, "pressure", ())
        has_grid = (
            getattr(temperature, "size", len(temperature)) > 1
            and getattr(pressure, "size", len(pressure)) > 1
            and getattr(payload, "stiffness_isothermal", None) is not None
        )
        if has_grid:
            families.extend(
                [
                    PlotFamilyDescriptor(
                        "pt",
                        "Pressure–temperature stiffness",
                        "P-T contour maps for selected elastic components.",
                        default=not families,
                        cost="moderate",
                        icon="▦",
                    ),
                    PlotFamilyDescriptor(
                        "domain",
                        "Calibration and analysis domain",
                        "QHA volume coverage, extrapolation masks, and archived profiles.",
                        cost="moderate",
                        icon="⌗",
                    ),
                ]
            )
        if bool(getattr(payload, "profiles", {})):
            families.append(
                PlotFamilyDescriptor(
                    "profiles",
                    "Depth profiles",
                    "Elastic properties along archived geothermobarometric paths.",
                    default=not families,
                    cost="moderate",
                    icon="↘",
                )
            )
        if not families:
            families.append(
                PlotFamilyDescriptor(
                    "auto",
                    "Available plots",
                    "Plots selected automatically from the archived workflow stage.",
                    default=True,
                    cost="moderate",
                )
            )
        return tuple(families)

    def build_plots(self, namespace: Any, result: Any, family_key: str) -> Any:
        if family_key == "fits":
            return namespace.build_fit_plots(result)
        if family_key == "pt":
            return namespace.build_pt_plots(result)
        if family_key == "domain":
            return namespace.build_domain_plot(result)
        if family_key == "profiles":
            payload = namespace.get_result(result)
            names = tuple(getattr(payload, "profiles", {}))
            profile_name = names[0] if names else None
            return namespace.build_profile_plots(result, profile_name=profile_name)
        if family_key == "auto":
            return namespace.build_plots(result)
        raise KeyError(f"unknown thermoelastic plot family {family_key!r}")

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind
        descriptions = {
            "fits": "elastic-volume calibration and residual diagnostics",
            "pt": "thermoelastic property over the pressure-temperature grid",
            "domain": "calibration coverage, analysis domain, and extrapolation policy",
            "profiles": "property evolution along an archived geothermobarometric path",
            "auto": "available plot selected from the archived workflow stage",
        }
        return f"{title}: {descriptions[family_key]}."

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "fit" in normalized or "residual" in normalized:
            return "Calibration"
        if "stability" in normalized:
            return "Stability"
        if "profile" in normalized or "depth" in normalized:
            return "Profile"
        if "provenance" in normalized or "metadata" in normalized:
            return "Provenance"
        return "Reconstruction"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind
        return {
            "fits": "Calibration",
            "pt": "P-T map",
            "domain": "Domain",
            "profiles": "Profile",
            "auto": "Available",
        }[family_key]
