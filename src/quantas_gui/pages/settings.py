"""Browser-local appearance and interface settings."""

from __future__ import annotations

from dash import dcc, html

from quantas_gui.components.settings import (
    developer_tools_link,
    option_cards,
    preference_group,
    settings_preview,
)
from quantas_gui.models.preferences import UserPreferences

PATH = "/settings"
NAME = "Settings"
TITLE = "Settings · Quantas GUI"
ORDER = 90


_THEME_OPTIONS = (
    ("Quantas Dark", "dark", "Current dark interface and default theme."),
    ("Quantas Light", "light", "Light surfaces with the same scientific colour accents."),
    ("System", "system", "Follow the operating-system light or dark preference."),
)

_TEXT_OPTIONS = (
    ("Compact", "compact", "90% typography for dense desktop layouts."),
    ("Standard", "standard", "Default typography and information density."),
    ("Comfortable", "comfortable", "112% typography for improved readability."),
    ("Large", "large", "125% typography for presentations and accessibility."),
)

_MOTION_OPTIONS = (
    ("System", "system", "Respect the operating-system reduced-motion setting."),
    ("Reduced", "reduced", "Minimise transitions and non-essential movement."),
)

_DENSITY_OPTIONS = (
    ("Comfortable", "comfortable", "Default row heights and editing space."),
    ("Compact", "compact", "More table rows within the available viewport."),
)


def layout() -> html.Div:
    """Return the application-settings page."""
    defaults = UserPreferences.defaults()
    return html.Div(
        [
            dcc.Interval(id="q-settings-hydrate", interval=50, max_intervals=1),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Application preferences", className="q-eyebrow"),
                            html.H1("Interface settings"),
                            html.P(
                                "Configure browser-local presentation preferences. These "
                                "settings affect only the graphical interface; scientific "
                                "methods, units, precision, and stored results are unchanged."
                            ),
                        ],
                        className="q-page-intro",
                    ),
                    html.Button(
                        "Restore defaults",
                        id="q-settings-reset",
                        n_clicks=0,
                        className="q-button",
                    ),
                ],
                className="q-settings-page-header",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            preference_group(
                                title="Theme",
                                description=(
                                    "Select the colour scheme used by the "
                                    "application shell and scientific views."
                                ),
                                control=option_cards(
                                    "q-setting-theme", _THEME_OPTIONS, value=defaults.theme
                                ),
                            ),
                            preference_group(
                                title="Text size",
                                description=(
                                    "Scale interface typography while preserving "
                                    "numerical display precision."
                                ),
                                control=option_cards(
                                    "q-setting-text-size",
                                    _TEXT_OPTIONS,
                                    value=defaults.text_size,
                                ),
                            ),
                            preference_group(
                                title="Motion",
                                description=(
                                    "Control decorative transitions and interface movement."
                                ),
                                control=option_cards(
                                    "q-setting-motion",
                                    _MOTION_OPTIONS,
                                    value=defaults.motion,
                                ),
                            ),
                            preference_group(
                                title="Table density",
                                description=(
                                    "Choose the default row density for result "
                                    "tables and structured editors."
                                ),
                                control=option_cards(
                                    "q-setting-table-density",
                                    _DENSITY_OPTIONS,
                                    value=defaults.table_density,
                                ),
                                note=(
                                    "Individual scientific views may later expose "
                                    "a temporary per-table override."
                                ),
                            ),
                        ],
                        className="q-settings-list",
                    ),
                    html.Div(
                        [
                            settings_preview(),
                            developer_tools_link(),
                            html.Div(
                                [
                                    html.Strong("Storage policy"),
                                    html.P(
                                        "Preferences are stored in this browser only. They are "
                                        "not written to Quantas HDF5 files and are not shared "
                                        "with a future server deployment."
                                    ),
                                ],
                                className="q-panel q-settings-policy",
                            ),
                        ],
                        className="q-settings-aside",
                    ),
                ],
                className="q-settings-layout",
            ),
        ],
        className="q-content",
    )
