"""Passive presentation contracts for module-aware result exploration.

The classes in this module contain no Dash components and no Quantas
implementation objects.  They describe which report and plot families a
scientific result exposes, so the Results Explorer can remain generic while
module-specific adapters retain scientific intent.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

ArtifactCost = Literal["low", "moderate", "high"]


@dataclass(frozen=True, slots=True)
class TableFamilyDescriptor:
    """Describe one lazily generated report-table family.

    Parameters
    ----------
    key
        Stable family identifier used in callbacks and cache keys.
    title
        Human-readable selector label.
    description
        Short explanation of the scientific content.
    default
        Whether this family should be selected initially.
    cost
        Qualitative construction cost displayed by the GUI.
    """

    key: str
    title: str
    description: str
    default: bool = False
    cost: ArtifactCost = "low"

    def as_option(self) -> dict[str, str]:
        """Return one Dash dropdown option."""
        return {"label": self.title, "value": self.key}

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PlotFamilyDescriptor:
    """Describe one lazily generated scientific plot family.

    Parameters
    ----------
    key
        Stable family identifier used by the module adapter.
    title
        Human-readable selector label.
    description
        Short scientific explanation.
    default
        Whether this family should be selected initially.
    cost
        Qualitative construction cost.  High-cost families are never built
        while merely opening the Results Explorer.
    icon
        Compact symbolic label used by responsive controls.
    """

    key: str
    title: str
    description: str
    default: bool = False
    cost: ArtifactCost = "low"
    icon: str = "◇"

    def as_option(self) -> dict[str, str]:
        """Return one Dash dropdown option."""
        suffix = " · compute" if self.cost == "high" else ""
        return {"label": f"{self.title}{suffix}", "value": self.key}

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return asdict(self)


def default_family_key(
    families: tuple[TableFamilyDescriptor, ...] | tuple[PlotFamilyDescriptor, ...],
) -> str | None:
    """Return the declared default family, or the first family when present."""
    for family in families:
        if family.default:
            return family.key
    return families[0].key if families else None
