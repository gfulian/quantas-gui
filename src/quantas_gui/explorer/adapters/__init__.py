"""Scientific module adapters used by the Results Explorer."""

from quantas_gui.explorer.adapters.base import GuiPlotCollection, ResultModuleAdapter
from quantas_gui.explorer.adapters.registry import adapter_for, registered_adapters

__all__ = [
    "GuiPlotCollection",
    "ResultModuleAdapter",
    "adapter_for",
    "registered_adapters",
]
