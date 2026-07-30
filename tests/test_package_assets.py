from __future__ import annotations

from importlib.resources import files


def test_design_assets_are_packaged() -> None:
    assets = files("quantas_gui") / "assets"
    assert (assets / "00_tokens.css").is_file()
    assert (assets / "05_theme_bootstrap.js").is_file()
    assert (assets / "30_responsive.css").is_file()
    assert (assets / "40_results.css").is_file()
    assert (assets / "60_settings.css").is_file()
    assert (assets / "quantas-logo.png").is_file()
    assert (assets / "images" / "seismic.png").is_file()
