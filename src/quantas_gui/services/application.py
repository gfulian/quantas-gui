"""Application-service assembly for local and future server deployments."""

from __future__ import annotations

from dataclasses import dataclass

from quantas_gui.config import Settings
from quantas_gui.services.cache import LocalArtifactCache
from quantas_gui.services.result_backend import QuantasResultBackend
from quantas_gui.services.results import ResultExplorerService
from quantas_gui.services.workspaces import LocalWorkspaceStore


@dataclass(frozen=True, slots=True)
class AppServices:
    """Replaceable application services injected into Dash callbacks."""

    results: ResultExplorerService


def build_default_services(settings: Settings) -> AppServices:
    """Build the local service graph without changing page code."""
    workspace_store = LocalWorkspaceStore(settings.workspace_root)
    return AppServices(
        results=ResultExplorerService(
            workspace_store=workspace_store,
            backend=QuantasResultBackend(),
            max_upload_bytes=settings.max_upload_bytes,
            cache=LocalArtifactCache(max_entries=settings.result_cache_entries),
        )
    )
