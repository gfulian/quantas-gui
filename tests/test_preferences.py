"""Tests for browser-local interface preferences."""

from __future__ import annotations

from quantas_gui.models.preferences import UserPreferences


def test_preference_defaults_follow_the_operating_system() -> None:
    preferences = UserPreferences.defaults()
    assert preferences.theme == "system"
    assert preferences.text_size == "standard"
    assert preferences.motion == "system"
    assert preferences.table_density == "comfortable"


def test_invalid_browser_preferences_fall_back_independently() -> None:
    preferences = UserPreferences.from_mapping(
        {
            "theme": "unsupported",
            "text_size": "comfortable",
            "motion": "animated",
            "table_density": "compact",
            "unknown": "ignored",
        }
    )
    assert preferences.theme == "system"
    assert preferences.text_size == "comfortable"
    assert preferences.motion == "system"
    assert preferences.table_density == "compact"


def test_preferences_round_trip_as_json_mapping() -> None:
    original = UserPreferences(
        theme="light",
        text_size="large",
        motion="reduced",
        table_density="compact",
    )
    assert UserPreferences.from_mapping(original.as_dict()) == original
