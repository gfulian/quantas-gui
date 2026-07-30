"""Persistent application shell and profile-aware navigation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import dash
from dash import dcc, html

from quantas_gui.components.result_ids import ResultIds
from quantas_gui.models.preferences import UserPreferences
from quantas_gui.profile import ApplicationProfile
from quantas_gui.services.backend_info import BackendCompatibility


@dataclass(frozen=True, slots=True)
class NavigationItem:
    """Passive navigation entry."""

    icon: str
    label: str
    path: str
    requires_backend: bool = False


WORKSPACE_NAV = (
    NavigationItem("⌂", "Overview", "/"),
    NavigationItem("▣", "Results", "/results", True),
    NavigationItem("◇", "Workflows", "/workflows", True),
    NavigationItem("↔", "Interoperability", "/interop", True),
)

SYSTEM_NAV = (NavigationItem("⚙", "Settings", "/settings"),)

MODULE_NAV = (
    NavigationItem("E", "Elasticity", "/elasticity", True),
    NavigationItem("S", "SEISMIC", "/seismic", True),
    NavigationItem("H", "HA / QHA", "/qha", True),
    NavigationItem("P", "Equation of state", "/eos", True),
    NavigationItem("T", "Thermoelasticity", "/thermoelasticity", True),
)

UI_KIT_NAV = (
    NavigationItem("◆", "UI Kit", "/"),
    NavigationItem("⚙", "Settings", "/settings"),
)


def build_shell(
    *,
    backend: BackendCompatibility,
    profile: ApplicationProfile = ApplicationProfile.STANDARD,
) -> html.Div:
    """Create the application shell around the selected Dash page profile."""
    top_actions: list[Any] = [
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
    ]
    if profile is ApplicationProfile.STANDARD:
        top_actions.append(_open_result_action(backend))

    return html.Div(
        [
            dcc.Location(id="q-location", refresh=False),
            dcc.Store(
                id="q-user-preferences",
                storage_type="local",
                data=UserPreferences.defaults().as_dict(),
            ),
            dcc.Store(id="q-effective-theme", storage_type="memory", data="dark"),
            dcc.Store(id=ResultIds.SESSION, storage_type="session"),
            dcc.Store(
                id="q-backend-compatibility",
                storage_type="memory",
                data=backend.as_dict(),
            ),
            dcc.Interval(id="q-system-theme-watch", interval=5_000, n_intervals=0),
            html.Div(id="q-settings-applied", hidden=True),
            _sidebar(backend, profile=profile),
            html.Header(
                [
                    html.Div(
                        [
                            html.Span(
                                "Workspace"
                                if profile is ApplicationProfile.STANDARD
                                else "Developer"
                            ),
                            html.Span("/"),
                            html.Strong(profile.root_breadcrumb, id="q-breadcrumb-current"),
                        ],
                        className="q-breadcrumb",
                    ),
                    html.Div(top_actions, className="q-top-actions"),
                ],
                className="q-topbar",
            ),
            html.Main(dash.page_container, className="q-main"),
            _mobile_navigation(backend, profile=profile),
        ],
        className="q-app-shell",
    )


def _open_result_action(backend: BackendCompatibility) -> Any:
    if backend.ready:
        return dcc.Link(
            "Open result",
            href=dash.get_relative_path("/results"),
            className="q-button q-button--primary",
        )
    return html.Span(
        "Open result",
        className="q-button q-button--primary is-disabled",
        title=backend.diagnostic_message(),
        **{"aria-disabled": "true"},
    )


def _sidebar(
    backend: BackendCompatibility,
    *,
    profile: ApplicationProfile,
) -> html.Aside:
    if backend.ready:
        status_class = "is-ready"
    elif backend.available:
        status_class = "is-incompatible"
    else:
        status_class = "is-offline"
    version = f"Quantas {backend.version}" if backend.version else "Quantas backend"
    edition = (
        "Developer component gallery"
        if profile is ApplicationProfile.UI_KIT
        else "Graphical interface"
    )

    navigation: list[Any] = []
    if profile is ApplicationProfile.UI_KIT:
        navigation.extend(
            [
                html.Div("Developer tools", className="q-nav-label"),
                *[_nav_link(item, backend=backend) for item in UI_KIT_NAV],
            ]
        )
    else:
        navigation.extend(
            [
                html.Div("Workspace", className="q-nav-label"),
                *[_nav_link(item, backend=backend) for item in WORKSPACE_NAV],
                html.Div("Scientific modules", className="q-nav-label"),
                *[_nav_link(item, backend=backend) for item in MODULE_NAV],
                html.Div("System", className="q-nav-label"),
                *[_nav_link(item, backend=backend) for item in SYSTEM_NAV],
            ]
        )

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
                            html.P(edition, className="q-brand-edition"),
                        ],
                        className="q-brand-copy",
                    ),
                ],
                href=dash.get_relative_path("/"),
                className="q-brand",
            ),
            html.Nav(navigation, className="q-nav"),
            html.Div(
                [
                    html.Strong(version),
                    html.Span(backend.status_label),
                    html.Span(backend.detail or "No backend detail", className="q-backend-mode"),
                ],
                className=f"q-sidebar-footer {status_class}",
                title=backend.diagnostic_message(),
            ),
        ],
        className="q-sidebar",
    )


def _nav_link(
    item: NavigationItem,
    *,
    backend: BackendCompatibility,
    mobile: bool = False,
) -> Any:
    class_name = "q-mobile-nav-item" if mobile else "q-nav-item"
    children = [
        html.Span(item.icon, className="q-nav-icon"),
        html.Span(item.label),
    ]
    enabled = backend.ready or not item.requires_backend
    if not enabled:
        return html.Div(
            children,
            className=f"{class_name} is-disabled",
            title=backend.diagnostic_message(),
            **{"aria-disabled": "true"},
        )
    return dcc.Link(
        children,
        href=dash.get_relative_path(item.path),
        id={"type": "q-mobile-nav-link" if mobile else "q-nav-link", "path": item.path},
        className=class_name,
    )


def _mobile_navigation(
    backend: BackendCompatibility,
    *,
    profile: ApplicationProfile,
) -> html.Nav:
    items = UI_KIT_NAV if profile is ApplicationProfile.UI_KIT else (*WORKSPACE_NAV, *SYSTEM_NAV)
    return html.Nav(
        [_nav_link(item, backend=backend, mobile=True) for item in items],
        className="q-mobile-nav",
        **{"aria-label": "Primary navigation"},
    )
