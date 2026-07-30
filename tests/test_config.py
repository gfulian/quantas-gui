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


def test_server_defaults_disable_browser_debug_and_enable_secure_cookies() -> None:
    settings = Settings.server_defaults()
    assert settings.mode == "server"
    assert settings.open_browser is False
    assert settings.debug is False
    assert settings.secure_cookies is True
    assert settings.host == "0.0.0.0"


def test_server_environment_rejects_explicit_debug(monkeypatch) -> None:
    import pytest

    monkeypatch.setenv("QUANTAS_GUI_MODE", "server")
    monkeypatch.setenv("QUANTAS_GUI_DEBUG", "true")
    with pytest.raises(ValueError, match="server mode cannot enable Dash debug tools"):
        Settings.from_environment(defaults=Settings.server_defaults())


def test_wsgi_entry_point_forces_server_mode() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "quantas_gui" / "wsgi.py").read_text(
        encoding="utf-8"
    )
    assert ".with_overrides(" in source
    assert 'mode="server"' in source
    assert "open_browser=False" in source
    assert "debug=False" in source


def test_environment_rejects_ambiguous_boolean(monkeypatch) -> None:
    import pytest

    monkeypatch.setenv("QUANTAS_GUI_OPEN_BROWSER", "sometimes")
    with pytest.raises(ValueError, match="invalid boolean value"):
        Settings.from_environment()


def test_environment_rejects_invalid_prefix_and_cache_size(monkeypatch) -> None:
    import pytest

    monkeypatch.setenv("QUANTAS_GUI_URL_PREFIX", "../unsafe")
    with pytest.raises(ValueError, match="invalid path segment"):
        Settings.from_environment()

    monkeypatch.delenv("QUANTAS_GUI_URL_PREFIX")
    monkeypatch.setenv("QUANTAS_GUI_RESULT_CACHE_ENTRIES", "0")
    with pytest.raises(ValueError, match="result_cache_entries must be positive"):
        Settings.from_environment()


def test_settings_reject_trusted_host_urls() -> None:
    import pytest

    with pytest.raises(ValueError, match="invalid trusted host"):
        Settings.server_defaults().with_overrides(trusted_hosts=("https://quantas.example.org",))
