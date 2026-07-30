"""Explicit Dash page registration for standard and developer profiles."""

from __future__ import annotations

from functools import partial
from importlib import import_module
from types import ModuleType

import dash

from quantas_gui.profile import ApplicationProfile
from quantas_gui.services.backend_info import BackendCompatibility

_STANDARD_PAGE_MODULES = (
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
    "quantas_gui.pages.about",
)

_UI_KIT_PAGE_MODULES = (
    "quantas_gui.pages.ui_kit",
    "quantas_gui.pages.settings",
    "quantas_gui.pages.about",
)


def register_pages(
    backend: BackendCompatibility,
    *,
    profile: ApplicationProfile = ApplicationProfile.STANDARD,
) -> tuple[ModuleType, ...]:
    """Register only the pages exposed by the selected application profile."""
    module_names = (
        _UI_KIT_PAGE_MODULES if profile is ApplicationProfile.UI_KIT else _STANDARD_PAGE_MODULES
    )
    modules = tuple(import_module(name) for name in module_names)
    for module in modules:
        layout = module.layout
        if bool(getattr(module, "USES_BACKEND_STATUS", False)):
            layout = partial(layout, backend=backend)
        elif module.__name__ == "quantas_gui.pages.settings":
            layout = partial(
                layout,
                developer_mode=profile is ApplicationProfile.UI_KIT,
            )
        path = module.PATH
        order = module.ORDER
        if profile is ApplicationProfile.UI_KIT and module.__name__ == "quantas_gui.pages.ui_kit":
            path = "/"
            order = 0
        dash.register_page(
            module.__name__,
            path=path,
            name=module.NAME,
            title=module.TITLE,
            order=order,
            layout=layout,
        )
    return modules
