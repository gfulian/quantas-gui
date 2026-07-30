"""Application-shell navigation callbacks."""

from __future__ import annotations

from collections.abc import Sequence

import dash
from dash import ALL, Input, Output, State

from quantas_gui.profile import ApplicationProfile

_STANDARD_BREADCRUMBS = {
    "": "Overview",
    "results": "Results Explorer",
    "workflows": "Workflows",
    "interop": "Interoperability",
    "elasticity": "Elasticity",
    "seismic": "SEISMIC",
    "ha": "Harmonic thermodynamics",
    "qha": "Quasi-harmonic approximation",
    "eos": "Equation of state",
    "thermoelasticity": "Thermoelasticity",
    "settings": "Settings",
    "about": "About",
}

_UI_KIT_BREADCRUMBS = {
    "": "Scientific UI Kit",
    "settings": "Settings",
    "about": "About",
}


def register_navigation_callbacks(
    app: dash.Dash,
    *,
    profile: ApplicationProfile = ApplicationProfile.STANDARD,
) -> None:
    """Register active-link and breadcrumb callbacks on an app instance."""
    breadcrumbs = (
        _UI_KIT_BREADCRUMBS if profile is ApplicationProfile.UI_KIT else _STANDARD_BREADCRUMBS
    )

    @app.callback(
        Output({"type": "q-nav-link", "path": ALL}, "className"),
        Output({"type": "q-mobile-nav-link", "path": ALL}, "className"),
        Output("q-breadcrumb-current", "children"),
        Input("q-location", "pathname"),
        State({"type": "q-nav-link", "path": ALL}, "id"),
        State({"type": "q-mobile-nav-link", "path": ALL}, "id"),
    )
    def update_navigation(
        pathname: str | None,
        desktop_ids: Sequence[dict[str, str]],
        mobile_ids: Sequence[dict[str, str]],
    ) -> tuple[list[str], list[str], str]:
        stripped = dash.strip_relative_path(pathname) or ""
        normalised = f"/{stripped}" if stripped else "/"
        desktop = _classes(desktop_ids, normalised, "q-nav-item")
        mobile = _classes(mobile_ids, normalised, "q-mobile-nav-item")
        breadcrumb = breadcrumbs.get(stripped, profile.root_breadcrumb)
        return desktop, mobile, breadcrumb


def _classes(
    identifiers: Sequence[dict[str, str]],
    current_path: str,
    base_class: str,
) -> list[str]:
    return [
        f"{base_class} is-active" if item["path"] == current_path else base_class
        for item in identifiers
    ]
