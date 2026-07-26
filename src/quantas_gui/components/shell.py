"""Persistent application shell and navigation."""

from __future__ import annotations

from dataclasses import dataclass

import dash
from dash import dcc, html

from quantas_gui.models.preferences import UserPreferences
from quantas_gui.services.backend_info import BackendInfo


@dataclass(frozen=True, slots=True)
class NavigationItem:
    """Passive navigation entry."""

    icon: str
    label: str
    path: str


WORKSPACE_NAV = (
    NavigationItem("⌂", "Overview", "/"),
    NavigationItem("▣", "Results", "/results"),
    NavigationItem("◇", "Workflows", "/workflows"),
    NavigationItem("↔", "Interoperability", "/interop"),
)

SYSTEM_NAV = (
    NavigationItem("⚙", "Settings", "/settings"),
    NavigationItem("◆", "UI Kit", "/ui-kit"),
)

MOBILE_NAV = (*WORKSPACE_NAV, *SYSTEM_NAV)


MODULE_NAV = (
    NavigationItem("E", "Elasticity", "/elasticity"),
    NavigationItem("S", "SEISMIC", "/seismic"),
    NavigationItem("H", "HA / QHA", "/qha"),
    NavigationItem("P", "Equation of state", "/eos"),
    NavigationItem("T", "Thermoelasticity", "/thermoelasticity"),
)


def build_shell(*, backend: BackendInfo) -> html.Div:
    """Create the application shell around the Dash page container."""
    return html.Div(
        [
            dcc.Location(id="q-location", refresh=False),
            dcc.Store(
                id="q-user-preferences",
                storage_type="local",
                data=UserPreferences.defaults().as_dict(),
            ),
            dcc.Store(id="q-effective-theme", storage_type="memory", data="dark"),
            html.Div(id="q-settings-applied", hidden=True),
            _sidebar(backend),
            html.Header(
                [
                    html.Div(
                        [
                            html.Span("Workspace"),
                            html.Span("/"),
                            html.Strong("Overview", id="q-breadcrumb-current"),
                        ],
                        className="q-breadcrumb",
                    ),
                    html.Div(
                        [
                            dcc.Link(
                                "⚙",
                                href=dash.get_relative_path("/settings"),
                                className="q-button q-button--icon q-button--settings",
                                title="Interface settings",
                            ),
                            dcc.Link(
                                "?",
                                href=dash.get_relative_path("/about"),
                                className="q-button q-button--icon q-button--about",
                                title="About Quantas GUI",
                            ),
                            dcc.Link(
                                "Open result",
                                href=dash.get_relative_path("/results"),
                                className="q-button q-button--primary",
                            ),
                        ],
                        className="q-top-actions",
                    ),
                ],
                className="q-topbar",
            ),
            html.Main(dash.page_container, className="q-main"),
            _mobile_navigation(),
        ],
        className="q-app-shell",
    )


def _sidebar(backend: BackendInfo) -> html.Aside:
    status_class = "is-ready" if backend.available else "is-offline"
    version = f"Quantas {backend.version}" if backend.version else "Quantas backend"
    return html.Aside(
        [
            dcc.Link(
                [
                    html.Img(
                        src=dash.get_asset_url("quantas-logo.png"),
                        className="q-brand-logo",
                        alt="Quantas logo",
                    ),
                    html.Div(
                        [
                            html.P("QUANTAS", className="q-brand-name"),
                            html.P("Graphical interface", className="q-brand-edition"),
                        ],
                        className="q-brand-copy",
                    ),
                ],
                href=dash.get_relative_path("/"),
                className="q-brand",
            ),
            html.Nav(
                [
                    html.Div("Workspace", className="q-nav-label"),
                    *[_nav_link(item) for item in WORKSPACE_NAV],
                    html.Div("Scientific modules", className="q-nav-label"),
                    *[_nav_link(item) for item in MODULE_NAV],
                    html.Div("System", className="q-nav-label"),
                    *[_nav_link(item) for item in SYSTEM_NAV],
                ],
                className="q-nav",
            ),
            html.Div(
                [
                    html.Strong(version),
                    html.Span(backend.detail),
                    html.Span("Local workspace · float64", className="q-backend-mode"),
                ],
                className=f"q-sidebar-footer {status_class}",
            ),
        ],
        className="q-sidebar",
    )


def _nav_link(item: NavigationItem, *, mobile: bool = False) -> dcc.Link:
    class_name = "q-mobile-nav-item" if mobile else "q-nav-item"
    return dcc.Link(
        [
            html.Span(item.icon, className="q-nav-icon"),
            html.Span(item.label),
        ],
        href=dash.get_relative_path(item.path),
        id={"type": "q-mobile-nav-link" if mobile else "q-nav-link", "path": item.path},
        className=class_name,
    )


def _mobile_navigation() -> html.Nav:
    return html.Nav(
        [_nav_link(item, mobile=True) for item in MOBILE_NAV],
        className="q-mobile-nav",
        **{"aria-label": "Primary navigation"},
    )
