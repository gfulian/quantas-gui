from __future__ import annotations

from base64 import b64encode
from pathlib import Path
from types import SimpleNamespace

import pytest

from quantas_gui.models.results import ResultOverview, ResultSummary, TableData
from quantas_gui.services.results import ResultExplorerService, ResultUploadError
from quantas_gui.services.workspaces import LocalWorkspaceStore


class FakeResultBackend:
    def inspect(self, path: Path) -> ResultOverview:
        assert path.read_bytes() == b"native-hdf5"
        return ResultOverview(
            summary=ResultSummary(
                module="elasticity",
                module_title="Second-order elasticity",
                method="elasticity",
                program="quantas",
                quantas_version="2.0.0b6",
                schema_version="1.0",
                created_at=None,
                created_by=None,
            ),
            metadata={},
            input_data={},
            options={},
            inventory=(),
            warnings=(),
            events=(),
        )

    def build_tables(self, path: Path):
        return (TableData("Summary", ["A"], [[1.0]]),)

    def build_plots(self, path: Path):
        return SimpleNamespace(plots=[], warnings=[])

    def render_plain_report(self, path: Path) -> str:
        return "report"


def _contents(payload: bytes) -> str:
    return "data:application/x-hdf5;base64," + b64encode(payload).decode("ascii")


def test_upload_is_stored_under_opaque_workspace(tmp_path: Path) -> None:
    service = ResultExplorerService(
        workspace_store=LocalWorkspaceStore(tmp_path),
        backend=FakeResultBackend(),
        max_upload_bytes=1024,
    )
    reference, overview = service.ingest_upload(
        filename="../calcite.hdf5",
        contents=_contents(b"native-hdf5"),
    )

    assert reference.filename == "calcite.hdf5"
    assert overview.summary.module == "elasticity"
    path = service.path(reference)
    assert path.is_file()
    assert path.parent.parent.parent == tmp_path.resolve()

    service.close(reference)
    assert not path.exists()


def test_upload_rejects_non_hdf5_suffix(tmp_path: Path) -> None:
    service = ResultExplorerService(
        workspace_store=LocalWorkspaceStore(tmp_path),
        backend=FakeResultBackend(),
        max_upload_bytes=1024,
    )
    with pytest.raises(ResultUploadError):
        service.ingest_upload(filename="result.txt", contents=_contents(b"native-hdf5"))


def test_upload_rejects_oversized_payload(tmp_path: Path) -> None:
    service = ResultExplorerService(
        workspace_store=LocalWorkspaceStore(tmp_path),
        backend=FakeResultBackend(),
        max_upload_bytes=4,
    )
    with pytest.raises(ResultUploadError):
        service.ingest_upload(filename="result.h5", contents=_contents(b"too-large"))


def test_windows_style_browser_path_is_reduced_to_display_name(tmp_path: Path) -> None:
    service = ResultExplorerService(
        workspace_store=LocalWorkspaceStore(tmp_path),
        backend=FakeResultBackend(),
        max_upload_bytes=1024,
    )
    reference, _ = service.ingest_upload(
        filename=r"C:\Users\example\calcite.hdf5",
        contents=_contents(b"native-hdf5"),
    )
    assert reference.filename == "calcite.hdf5"


def test_result_service_caches_report_and_plot_construction(tmp_path: Path) -> None:
    class CountingBackend(FakeResultBackend):
        table_calls = 0
        plot_calls = 0

        def table_families(self, path: Path):
            from quantas_gui.explorer.models import TableFamilyDescriptor

            return (TableFamilyDescriptor("default", "Report", "Default", default=True),)

        def plot_families(self, path: Path):
            from quantas_gui.explorer.models import PlotFamilyDescriptor

            return (PlotFamilyDescriptor("default", "Plots", "Default", default=True),)

        def build_tables(self, path: Path, family_key=None):
            self.table_calls += 1
            return super().build_tables(path)

        def build_plots(self, path: Path, family_key=None):
            self.plot_calls += 1
            return super().build_plots(path)

    backend = CountingBackend()
    service = ResultExplorerService(
        workspace_store=LocalWorkspaceStore(tmp_path), backend=backend, max_upload_bytes=1024
    )
    reference, _ = service.ingest_upload(filename="result.h5", contents=_contents(b"native-hdf5"))
    assert service.build_tables(reference) is service.build_tables(reference)
    assert service.build_plots(reference) is service.build_plots(reference)
    assert backend.table_calls == 1
    assert backend.plot_calls == 1
