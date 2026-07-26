"""Explicit Dash page registration.

Pages are registered after the :class:`dash.Dash` instance exists. This avoids
import-time coupling and lets the packaged application use an application
factory with an absolute assets directory.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

import dash

_PAGE_MODULES = (
    "quantas_gui.pages.home",
    "quantas_gui.pages.results",
    "quantas_gui.pages.workflows",
    "quantas_gui.pages.interop",
    "quantas_gui.pages.elasticity",
    "quantas_gui.pages.seismic",
    "quantas_gui.pages.ha",
    "quantas_gui.pages.qha",
    "quantas_gui.pages.eos",
    "quantas_gui.pages.thermoelasticity",
    "quantas_gui.pages.settings",
    "quantas_gui.pages.ui_kit",
    "quantas_gui.pages.about",
)


def register_pages() -> tuple[ModuleType, ...]:
    """Register all packaged pages and return their imported modules."""
    modules = tuple(import_module(name) for name in _PAGE_MODULES)
    for module in modules:
        dash.register_page(
            module.__name__,
            path=module.PATH,
            name=module.NAME,
            title=module.TITLE,
            order=module.ORDER,
            layout=module.layout,
        )
    return modules
