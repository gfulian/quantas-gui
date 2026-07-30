"""Application profiles for the user interface and developer component gallery."""

from __future__ import annotations

from enum import Enum


class ApplicationProfile(str, Enum):
    """Packaged UI surfaces selected at application construction time."""

    STANDARD = "standard"
    UI_KIT = "ui-kit"

    @property
    def application_title(self) -> str:
        if self is ApplicationProfile.UI_KIT:
            return "Scientific UI Kit"
        return "Quantas GUI"

    @property
    def root_breadcrumb(self) -> str:
        if self is ApplicationProfile.UI_KIT:
            return "Scientific UI Kit"
        return "Overview"
