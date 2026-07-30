from __future__ import annotations

import numpy as np
from quantas.api import seismic

from quantas_gui.explorer.adapters import adapter_for


def test_public_seismic_tracking_reaches_2d_and_3d_plot_specs() -> None:
    stiffness = np.array(
        [
            [200.0, 120.0, 120.0, 0.0, 0.0, 0.0],
            [120.0, 200.0, 120.0, 0.0, 0.0, 0.0],
            [120.0, 120.0, 200.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 80.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 80.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 80.0],
        ]
    )
    result = seismic.run(
        seismic.Input(jobname="GUI polarization probe", stiffness=stiffness, density=3000.0),
        options=seismic.Options(
            ntheta=4,
            nphi=7,
            level="phase",
            track_polarization_axes=True,
        ),
    )
    inventory = seismic.describe_plots(result)
    adapter = adapter_for("seismic")

    maps = adapter.build_plots(seismic, result, "spherical_map", inventory)
    surfaces = adapter.build_plots(seismic, result, "property_surface_3d", inventory)

    assert any(spec.axis_layers for spec in maps.plots)
    assert any(spec.vector_layers for spec in surfaces.plots)
