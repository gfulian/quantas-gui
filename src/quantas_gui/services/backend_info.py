"""Runtime discovery of the optional Quantas scientific backend."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version


@dataclass(frozen=True, slots=True)
class BackendInfo:
    """Lightweight backend status displayed by the application shell."""

    available: bool
    version: str | None
    detail: str


def detect_quantas_backend() -> BackendInfo:
    """Detect Quantas without importing private implementation modules."""
    try:
        backend_version = version("quantas")
        import_module("quantas.api")
    except (PackageNotFoundError, ImportError) as exc:
        return BackendInfo(
            available=False,
            version=None,
            detail=f"Backend not connected ({exc.__class__.__name__})",
        )
    return BackendInfo(
        available=True,
        version=backend_version,
        detail=f"Quantas {backend_version} backend",
    )
