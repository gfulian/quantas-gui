"""Passive presentation contracts for module-aware result exploration.

The classes in this module contain no Dash components and no Quantas
implementation objects.  They describe which report and plot families a
scientific result exposes, so the Results Explorer can remain generic while
module-specific adapters retain scientific intent.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, TypeAlias

from quantas_gui.presentation.scientific_labels import scientific_label_text

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
        return {"label": scientific_label_text(self.title), "value": self.key}

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
    plot_kind: str = ""
    property_keys: tuple[str, ...] = ()
    supported_contexts: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    def as_option(self) -> dict[str, str]:
        """Return one Dash dropdown option."""
        suffix = " · compute" if self.cost == "high" else ""
        return {"label": scientific_label_text(f"{self.title}{suffix}"), "value": self.key}

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScientificExportDescriptor:
    """Describe one public Quantas export exposed in the Result Explorer.

    The descriptor contains only registry metadata and GUI presentation policy.
    Scientific parameters remain the responsibility of the module-specific
    adapter and the public Quantas operation.
    """

    key: str
    title: str
    description: str
    suffix: str
    enabled: bool = False
    unavailable_reason: str | None = None

    def as_option(self) -> dict[str, object]:
        """Return one Dash dropdown option."""
        label = self.title
        if not self.enabled and self.unavailable_reason:
            label = f"{label} · configuration required"
        return {"label": label, "value": self.key, "disabled": not self.enabled}

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return asdict(self)


ScientificScalar: TypeAlias = str | int | float | bool
ScientificSelectionValue: TypeAlias = ScientificScalar | tuple[ScientificScalar, ...] | None


@dataclass(frozen=True, slots=True)
class ScientificSelectionOption:
    """One exact value exposed by a public Quantas plot inventory."""

    value: ScientificScalar
    label: str
    description: str = ""

    def as_option(self) -> dict[str, Any]:
        """Return one Dash-compatible option without changing the source value."""
        option: dict[str, Any] = {"label": self.label, "value": self.value}
        if self.description:
            option["title"] = self.description
        return option


@dataclass(frozen=True, slots=True)
class ScientificSelectionField:
    """Describe one scientific property or context selector."""

    key: str
    label: str
    description: str
    options: tuple[ScientificSelectionOption, ...]
    value: ScientificSelectionValue
    role: Literal["property", "context"] = "context"
    multiple: bool = False
    required: bool = False
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class InformativeScientificContext:
    """Read-only context that explains the stored result without being editable."""

    key: str
    label: str
    values: tuple[str, ...]
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class PlotSelectionSchema:
    """Result-aware scientific controls for one public plot representation."""

    family_key: str
    title: str
    description: str
    property_field: ScientificSelectionField | None = None
    context_fields: tuple[ScientificSelectionField, ...] = ()
    informative_contexts: tuple[InformativeScientificContext, ...] = ()
    constraints: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PlotBuildSelection:
    """Lightweight scientific selection passed to a module-specific builder."""

    family_key: str
    property_keys: tuple[str, ...] = ()
    contexts: tuple[tuple[str, ScientificSelectionValue], ...] = ()

    def context(self, key: str, default: Any = None) -> Any:
        """Return one selected context value."""
        for context_key, value in self.contexts:
            if context_key == key:
                return value
        return default

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible browser representation."""
        return {
            "family_key": self.family_key,
            "property_keys": list(self.property_keys),
            "contexts": [
                [key, list(value) if isinstance(value, tuple) else value]
                for key, value in self.contexts
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> PlotBuildSelection | None:
        """Reconstruct one selection from lightweight browser state."""
        if not payload:
            return None
        contexts: list[tuple[str, ScientificSelectionValue]] = []
        for item in payload.get("contexts", ()):
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            key, value = item
            if isinstance(value, list):
                value = tuple(value)
            contexts.append((str(key), value))
        return cls(
            family_key=str(payload.get("family_key", "")),
            property_keys=tuple(str(item) for item in payload.get("property_keys", ())),
            contexts=tuple(contexts),
        )

    def cache_token(self) -> str:
        """Return a deterministic compact cache-key token."""
        context_text = ";".join(
            f"{key}={value!r}" for key, value in sorted(self.contexts, key=lambda item: item[0])
        )
        return f"{self.family_key}|{','.join(self.property_keys)}|{context_text}"


def default_family_key(
    families: tuple[TableFamilyDescriptor, ...] | tuple[PlotFamilyDescriptor, ...],
) -> str | None:
    """Return the declared default family, or the first family when present."""
    for family in families:
        if family.default:
            return family.key
    return families[0].key if families else None
