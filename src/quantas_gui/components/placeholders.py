"""Shared components for pages not yet connected to Quantas calculations."""

from __future__ import annotations

from dash import html


def development_page(
    *,
    eyebrow: str,
    title: str,
    summary: str,
    next_step: str,
) -> html.Div:
    """Create a polished placeholder that documents the next implementation step."""
    return html.Div(
        [
            html.Section(
                [
                    html.Div(eyebrow, className="q-eyebrow"),
                    html.H1(title),
                    html.P(summary),
                ],
                className="q-page-intro",
            ),
            html.Section(
                [
                    html.Div("In development", className="q-empty-state-badge"),
                    html.H2("The interface boundary is ready"),
                    html.P(next_step),
                ],
                className="q-empty-state q-panel",
            ),
        ],
        className="q-content",
    )
