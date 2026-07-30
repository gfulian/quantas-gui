"""Callbacks for browser-local interface preferences."""

from __future__ import annotations

from typing import Any

import dash
from dash import Input, Output, State, ctx

from quantas_gui.models.preferences import UserPreferences

_STORE_ID = "q-user-preferences"
_EFFECTIVE_THEME_ID = "q-effective-theme"


def register_settings_callbacks(app: dash.Dash) -> None:
    """Register preference persistence and browser-side theme application."""

    @app.callback(
        Output("q-setting-theme", "value"),
        Output("q-setting-text-size", "value"),
        Output("q-setting-motion", "value"),
        Output("q-setting-table-density", "value"),
        Input("q-settings-hydrate", "n_intervals"),
        Input("q-settings-reset", "n_clicks"),
        State(_STORE_ID, "data"),
        prevent_initial_call=True,
    )
    def hydrate_settings_page(
        _n_intervals: int,
        _reset_clicks: int | None,
        stored: dict[str, Any] | None,
    ) -> tuple[str, str, str, str]:
        preferences = (
            UserPreferences.defaults()
            if ctx.triggered_id == "q-settings-reset"
            else UserPreferences.from_mapping(stored)
        )
        return (
            preferences.theme,
            preferences.text_size,
            preferences.motion,
            preferences.table_density,
        )

    @app.callback(
        Output(_STORE_ID, "data"),
        Input("q-setting-theme", "value"),
        Input("q-setting-text-size", "value"),
        Input("q-setting-motion", "value"),
        Input("q-setting-table-density", "value"),
        Input("q-settings-reset", "n_clicks"),
        prevent_initial_call=True,
    )
    def save_preferences(
        theme: str | None,
        text_size: str | None,
        motion: str | None,
        table_density: str | None,
        _reset_clicks: int | None,
    ) -> dict[str, str]:
        if ctx.triggered_id == "q-settings-reset":
            return UserPreferences.defaults().as_dict()
        return UserPreferences.from_mapping(
            {
                "theme": theme,
                "text_size": text_size,
                "motion": motion,
                "table_density": table_density,
            }
        ).as_dict()

    app.clientside_callback(
        """
        function(data, _nIntervals, currentEffectiveTheme) {
            const defaults = {
                theme: "system",
                text_size: "standard",
                motion: "system",
                table_density: "comfortable"
            };
            const raw = Object.assign({}, defaults, data || {});
            const preferences = {
                theme: ["dark", "light", "system"].includes(raw.theme) ? raw.theme : defaults.theme,
                text_size: ["compact", "standard", "comfortable", "large"].includes(raw.text_size)
                    ? raw.text_size : defaults.text_size,
                motion: ["system", "reduced"].includes(raw.motion) ? raw.motion : defaults.motion,
                table_density: ["comfortable", "compact"].includes(raw.table_density)
                    ? raw.table_density : defaults.table_density
            };
            const scale = {
                compact: "0.90",
                standard: "1.00",
                comfortable: "1.12",
                large: "1.25"
            }[preferences.text_size] || "1.00";
            const media = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)");
            const effectiveTheme = preferences.theme === "system"
                ? ((media && media.matches) ? "light" : "dark")
                : preferences.theme;
            const root = document.documentElement;
            root.setAttribute("data-q-theme", preferences.theme);
            root.setAttribute("data-q-effective-theme", effectiveTheme);
            root.setAttribute("data-q-motion", preferences.motion);
            root.setAttribute("data-q-density", preferences.table_density);
            root.style.setProperty("--q-ui-scale", scale);
            const themeMeta = document.querySelector('meta[name="theme-color"]');
            if (themeMeta) {
                const themeColor = effectiveTheme === "light" ? "#f3f7fa" : "#071522";
                themeMeta.setAttribute("content", themeColor);
            }
            const effectiveOutput = effectiveTheme === currentEffectiveTheme
                ? window.dash_clientside.no_update
                : effectiveTheme;
            return [JSON.stringify(preferences), effectiveOutput];
        }
        """,
        Output("q-settings-applied", "children"),
        Output(_EFFECTIVE_THEME_ID, "data"),
        Input(_STORE_ID, "data"),
        Input("q-system-theme-watch", "n_intervals"),
        State(_EFFECTIVE_THEME_ID, "data"),
    )
