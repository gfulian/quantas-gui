"""Dash graphical interface for the Quantas scientific library."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quantas_gui._version import __version__

if TYPE_CHECKING:
    from dash import Dash

    from quantas_gui.config import Settings
    from quantas_gui.services.application import AppServices


def create_app(
    settings: Settings | None = None,
    services: AppServices | None = None,
) -> Dash:
    """Create the Dash application through a lazy import.

    Keeping Dash out of the package import path lets lightweight utilities,
    configuration, and service contracts remain importable in worker and
    packaging contexts that do not instantiate the web application.
    """
    from quantas_gui.app import create_app as factory

    return factory(settings, services=services)


__all__ = ["__version__", "create_app"]
