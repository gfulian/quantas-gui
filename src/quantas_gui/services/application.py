"""Application-service assembly for local and future server deployments."""

from __future__ import annotations

from dataclasses import dataclass

from quantas_gui.config import Settings
from quantas_gui.services.backend_info import BackendCompatibility, detect_quantas_backend
from quantas_gui.services.backends import DisabledExecutionBackend, ExecutionBackend
from quantas_gui.services.cache import ArtifactCache, LocalArtifactCache
from quantas_gui.services.result_backend import QuantasResultBackend
from quantas_gui.services.results import ResultExplorerService
from quantas_gui.services.workspaces import LocalWorkspaceStore, WorkspaceStore


@dataclass(frozen=True, slots=True)
class AppServices:
    """Replaceable application services injected into Dash callbacks."""

    backend: BackendCompatibility
    workspace_store: WorkspaceStore
    artifact_cache: ArtifactCache
    execution: ExecutionBackend
    results: ResultExplorerService


def build_default_services(settings: Settings) -> AppServices:
    """Build the safe filesystem-backed service graph.

    The same graph is correct for the local launcher and for WSGI workers that
    share ``workspace_root``. The artifact cache remains process-local; a future shared cache can be
    injected without changing pages or Result Explorer code.
    Scientific execution is deliberately disabled until a workflow-specific
    background worker is connected in milestone ``0.3``.
    """
    workspace_store = LocalWorkspaceStore(
        settings.workspace_root,
        lock_timeout_seconds=settings.workspace_lock_timeout_seconds,
    )
    artifact_cache = LocalArtifactCache(max_entries=settings.result_cache_entries)
    compatibility = detect_quantas_backend()
    execution = DisabledExecutionBackend()
    results = ResultExplorerService(
        workspace_store=workspace_store,
        backend=QuantasResultBackend(),
        max_upload_bytes=settings.max_upload_bytes,
        cache=artifact_cache,
        compatibility=compatibility,
    )
    return AppServices(
        backend=compatibility,
        workspace_store=workspace_store,
        artifact_cache=artifact_cache,
        execution=execution,
        results=results,
    )
