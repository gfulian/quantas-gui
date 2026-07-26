"""GUI renderers for frontend-neutral Quantas report and plot contracts."""

from quantas_gui.renderers.plotly import (
    COLORMAP_OPTIONS,
    PlotDescriptor,
    PlotlyRenderOptions,
    plot_inventory,
    render_collection_plot,
    render_plot,
)
from quantas_gui.renderers.tables import NormalizedTable, normalize_table, table_to_csv

__all__ = [
    "COLORMAP_OPTIONS",
    "NormalizedTable",
    "PlotDescriptor",
    "PlotlyRenderOptions",
    "normalize_table",
    "plot_inventory",
    "render_collection_plot",
    "render_plot",
    "table_to_csv",
]
