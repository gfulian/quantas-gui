from __future__ import annotations

from pathlib import Path

from quantas_gui.config import Settings


def test_local_defaults_are_loopback_and_non_debug() -> None:
    settings = Settings.local_defaults()
    assert settings.host == "127.0.0.1"
    assert settings.debug is False
    assert settings.url_prefix == "/"
    assert settings.max_request_bytes > settings.max_upload_bytes


def test_environment_and_prefix_normalisation(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("QUANTAS_GUI_MODE", "server")
    monkeypatch.setenv("QUANTAS_GUI_URL_PREFIX", "quantas")
    monkeypatch.setenv("QUANTAS_GUI_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("QUANTAS_GUI_OPEN_BROWSER", "false")
    settings = Settings.from_environment()
    assert settings.mode == "server"
    assert settings.url_prefix == "/quantas/"
    assert settings.workspace_root == tmp_path
    assert settings.open_browser is False
