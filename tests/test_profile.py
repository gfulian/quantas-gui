"""Regression tests for application profile labels."""

from __future__ import annotations

from quantas_gui.profile import ApplicationProfile


def test_application_profiles_expose_titles_without_shadowing_str_title() -> None:
    assert ApplicationProfile.STANDARD.application_title == "Quantas GUI"
    assert ApplicationProfile.UI_KIT.application_title == "Scientific UI Kit"
    assert ApplicationProfile.STANDARD.title() == "Standard"
