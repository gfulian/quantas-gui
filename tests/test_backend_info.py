from __future__ import annotations

from quantas_gui.services.backend_info import detect_quantas_backend


def test_backend_discovery_is_non_fatal() -> None:
    info = detect_quantas_backend()
    assert isinstance(info.available, bool)
    assert info.detail
