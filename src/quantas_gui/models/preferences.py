"""Passive user-interface preferences stored in the browser."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Mapping


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """Browser-local presentation preferences for Quantas GUI.

    These values affect only presentation. They never modify Quantas inputs,
    numerical precision, scientific results, or native HDF5 content.

    Parameters
    ----------
    theme
        Interface theme: ``dark``, ``light``, or ``system``.
    text_size
        Global typography scale: ``compact``, ``standard``, ``comfortable``,
        or ``large``.
    motion
        Motion policy: ``system`` or ``reduced``.
    table_density
        Default visual density for reusable data grids.
    """

    THEMES: ClassVar[frozenset[str]] = frozenset({"dark", "light", "system"})
    TEXT_SIZES: ClassVar[frozenset[str]] = frozenset(
        {"compact", "standard", "comfortable", "large"}
    )
    MOTION_POLICIES: ClassVar[frozenset[str]] = frozenset({"system", "reduced"})
    TABLE_DENSITIES: ClassVar[frozenset[str]] = frozenset(
        {"comfortable", "compact"}
    )

    theme: str = "dark"
    text_size: str = "standard"
    motion: str = "system"
    table_density: str = "comfortable"

    @classmethod
    def defaults(cls) -> "UserPreferences":
        """Return the presentation defaults used by a new browser profile."""
        return cls()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "UserPreferences":
        """Create validated preferences from browser-provided data.

        Unknown or invalid values fall back independently to safe defaults so a
        stale local-storage record cannot prevent the application from loading.
        """
        defaults = cls.defaults()
        data = dict(value or {})
        return cls(
            theme=_member(data.get("theme"), cls.THEMES, defaults.theme),
            text_size=_member(
                data.get("text_size"), cls.TEXT_SIZES, defaults.text_size
            ),
            motion=_member(data.get("motion"), cls.MOTION_POLICIES, defaults.motion),
            table_density=_member(
                data.get("table_density"),
                cls.TABLE_DENSITIES,
                defaults.table_density,
            ),
        )

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-compatible representation for :class:`dcc.Store`."""
        return {key: str(value) for key, value in asdict(self).items()}


def _member(value: Any, allowed: frozenset[str], default: str) -> str:
    candidate = str(value) if value is not None else default
    return candidate if candidate in allowed else default
