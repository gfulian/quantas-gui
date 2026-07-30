"""Reusable landing-page cards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import dash
from dash import dcc, html


@dataclass(frozen=True, slots=True)
class ModuleCardSpec:
    """Passive description of a scientific module card."""

    slug: str
    title: str
    kicker: str
    summary: str
    image: str


def module_card(
    spec: ModuleCardSpec,
    *,
    disabled: bool = False,
    disabled_reason: str | None = None,
) -> Any:
    """Create a module card with an accessible disabled state."""
    article = html.Article(
        [
            html.Img(
                src=dash.get_asset_url(f"images/{spec.image}"),
                className="q-module-image",
                alt=f"Representative {spec.title} result",
            ),
            html.Div(className="q-module-overlay"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(spec.kicker),
                            html.Span("—" if disabled else "↗", className="q-module-arrow"),
                        ],
                        className="q-module-kicker",
                    ),
                    html.H3(spec.title),
                    html.P(spec.summary),
                ],
                className="q-module-body",
            ),
        ],
        className="q-module-card",
    )
    if disabled:
        return html.Div(
            article,
            className="q-module-link is-disabled",
            title=disabled_reason,
            role="link",
            tabIndex=-1,
            **{"aria-disabled": "true"},
        )
    return dcc.Link(
        article,
        href=dash.get_relative_path(f"/{spec.slug}"),
        className="q-module-link",
    )
