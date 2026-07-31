"""Application services and deployment-neutral contracts."""

from quantas_gui.services.backend_info import (
    REQUIRED_QUANTAS,
    BackendCompatibility,
    BackendInfo,
    detect_quantas_backend,
)
from quantas_gui.services.backends import (
    DisabledExecutionBackend,
    ExecutionBackend,
    ExecutionBackendDescriptor,
    JobEvent,
    JobHandle,
    JobState,
    JobStatus,
    ResultStore,
)
from quantas_gui.services.local_execution import (
    LocalProcessExecutionBackend,
    WorkflowCancelled,
    WorkflowExecutionContext,
)
from quantas_gui.services.workspaces import (
    InvalidWorkspaceIdentifier,
    LocalWorkspaceStore,
    WorkspaceBusyError,
    WorkspaceClosingError,
    WorkspaceStore,
)

__all__ = [
    "BackendCompatibility",
    "BackendInfo",
    "REQUIRED_QUANTAS",
    "DisabledExecutionBackend",
    "ExecutionBackend",
    "ExecutionBackendDescriptor",
    "InvalidWorkspaceIdentifier",
    "JobEvent",
    "JobHandle",
    "JobState",
    "JobStatus",
    "LocalProcessExecutionBackend",
    "LocalWorkspaceStore",
    "ResultStore",
    "WorkspaceBusyError",
    "WorkspaceClosingError",
    "WorkflowCancelled",
    "WorkflowExecutionContext",
    "WorkspaceStore",
    "detect_quantas_backend",
]
