"""Application services and deployment-neutral contracts."""

from quantas_gui.services.backend_info import BackendInfo, detect_quantas_backend
from quantas_gui.services.backends import (
    ExecutionBackend,
    JobHandle,
    JobState,
    JobStatus,
    ResultStore,
)
from quantas_gui.services.workspaces import (
    InvalidWorkspaceIdentifier,
    LocalWorkspaceStore,
)

__all__ = [
    "BackendInfo",
    "ExecutionBackend",
    "InvalidWorkspaceIdentifier",
    "JobHandle",
    "JobState",
    "JobStatus",
    "LocalWorkspaceStore",
    "ResultStore",
    "detect_quantas_backend",
]
