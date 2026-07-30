"""Accessible components for backend compatibility and degraded operation."""

from __future__ import annotations

from dash import html

from quantas_gui.services.backend_info import BackendCompatibility


def backend_diagnostic(backend: BackendCompatibility) -> html.Section:
    """Render the complete public-backend compatibility diagnostic."""
    status = "Ready" if backend.ready else "Scientific functions disabled"
    version = backend.version or "Not detected"
    missing = (
        html.Ul([html.Li(item) for item in backend.missing_capabilities])
        if backend.missing_capabilities
        else html.P("No missing public capabilities were reported.")
    )
    return html.Section(
        [
            html.Div(status, className="q-backend-diagnostic-status"),
            html.H2("Quantas backend compatibility"),
            html.Dl(
                [
                    html.Dt("Required"),
                    html.Dd(backend.required_version),
                    html.Dt("Detected"),
                    html.Dd(version),
                    html.Dt("Available"),
                    html.Dd("Yes" if backend.available else "No"),
                    html.Dt("Compatible"),
                    html.Dd("Yes" if backend.compatible else "No"),
                ],
                className="q-backend-diagnostic-grid",
            ),
            html.H3("Public capabilities"),
            missing,
            html.P(backend.detail or "No additional detail is available."),
            html.P(backend.recovery_action, className="q-backend-recovery"),
        ],
        className=(
            "q-panel q-backend-diagnostic is-ready"
            if backend.ready
            else "q-panel q-backend-diagnostic is-blocked"
        ),
        role="status",
        **{"aria-live": "polite"},
    )


def backend_required_page(
    backend: BackendCompatibility,
    *,
    eyebrow: str,
    title: str,
    summary: str,
) -> html.Div:
    """Render a disabled scientific page while keeping the shell available."""
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
            backend_diagnostic(backend),
        ],
        className="q-content",
    )


__all__ = ["backend_diagnostic", "backend_required_page"]
