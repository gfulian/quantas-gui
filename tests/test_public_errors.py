from __future__ import annotations

from quantas_gui.services.public_errors import public_error_message


def test_public_error_message_redacts_windows_and_posix_paths() -> None:
    error = RuntimeError(
        r"Could not open C:\Users\scientist\secret\result.h5 or /srv/private/result.h5"
    )
    message = public_error_message(error)
    assert "C:\\Users" not in message
    assert "/srv/private" not in message
    assert message.count("<server path>") == 2


def test_public_error_message_is_bounded_and_removes_controls() -> None:
    message = public_error_message(RuntimeError("bad\x00value\n" + "x" * 2000))
    assert "\x00" not in message
    assert "\n" not in message
    assert len(message) == 1200
    assert message.endswith("…")


def test_public_error_message_uses_fallback_for_empty_exception() -> None:
    assert public_error_message(RuntimeError(""), fallback="Unavailable") == "Unavailable"
