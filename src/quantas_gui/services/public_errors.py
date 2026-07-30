"""Browser-safe error presentation helpers."""

from __future__ import annotations

import re
from typing import Final

_MAX_PUBLIC_MESSAGE: Final = 1200
_WINDOWS_PATH = re.compile(r"(?i)(?<![\w])(?:[a-z]:[\\/]|\\\\[^\\/\s]+[\\/][^\\/\s]+)[^\s'\"<>]*")
_POSIX_PATH = re.compile(r"(?<![\w:])/(?:[^/\s'\"<>]+/)*[^/\s'\"<>]+")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def public_error_message(
    error: BaseException,
    *,
    fallback: str = "The operation could not be completed.",
) -> str:
    """Return a bounded message that does not disclose server paths.

    Full exception details belong in server logs. Browser alerts may retain the
    scientific or validation explanation, but absolute Windows, UNC, and POSIX
    paths are replaced and control characters are removed.
    """
    message = str(error).strip() or fallback
    message = _CONTROL.sub("", message)
    message = _WINDOWS_PATH.sub("<server path>", message)
    message = _POSIX_PATH.sub("<server path>", message)
    lines = [line.strip() for line in message.splitlines() if line.strip()]
    compact = " · ".join(lines[:6]) or fallback
    if len(compact) <= _MAX_PUBLIC_MESSAGE:
        return compact
    return compact[: _MAX_PUBLIC_MESSAGE - 1].rstrip() + "…"
