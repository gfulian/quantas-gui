from __future__ import annotations

from base64 import b64encode
from pathlib import Path
from types import SimpleNamespace

import pytest

from quantas_gui.explorer.models import (
    PlotBuildSelection,
    PlotSelectionSchema,
    ScientificExportDescriptor,
)
from quantas_gui.models.results import (
    ActiveResultState,
    ResultOverview,
    ResultSummary,
    TableData,
)
from quantas_gui.services.backend_info import REQUIRED_QUANTAS, BackendCompatibility
from quantas_gui.services.result_backend import ResultBackendUnavailable
from quantas_gui.services.results import ResultExplorerService, ResultUploadError
from quantas_gui.services.workspaces import LocalWorkspaceStore

READY = BackendCompatibility(
    available=True,
    compatible=True,
    version="2.0.0b7",
    required_version=REQUIRED_QUANTAS,
    missing_capabilities=(),
    detail="Public lifecycle API validated",
)
UNAVAILABLE = BackendCompatibility(
    available=False,
    compatible=False,
    version=None,
    required_version=REQUIRED_QUANTAS,
    missing_capabilities=("quantas.api",),
    detail="Quantas is not installed",
)


class FakeResultBackend:
    def inspect(self, path: Path) -> ResultOverview:
        assert path.read_bytes() == b"native-hdf5"
        return ResultOverview(
            summary=ResultSummary(
                module="elasticity",
                module_title="Second-order elasticity",
                method="elasticity",
                program="quantas",
                quantas_version="2.0.0b7",
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

    def build_tables(self, path: Path, family_key: str | None = None):
        del path, family_key
        return (TableData("Summary", ["A"], [[1.0]]),)

    def plot_selection_schema(self, path: Path, family_key: str) -> PlotSelectionSchema:
        del path
        return PlotSelectionSchema(
            family_key=family_key,
            title="Plots",
            description="Scientific selection schema.",
        )

    def build_plots(
        self,
        path: Path,
        family_key: str | None = None,
        selection: PlotBuildSelection | None = None,
    ):
        del path, family_key, selection
        return SimpleNamespace(plots=[], warnings=[])

    def render_plain_report(self, path: Path, family_key: str | None = None) -> str:
        del path, family_key
        return "report"

    def scientific_exports(self, path: Path):
        del path
        return (
            ScientificExportDescriptor(
                key="export_table",
                title="Export table",
                description="Write a public scientific table.",
                suffix=".dat",
                enabled=True,
            ),
        )

    def write_scientific_export(
        self,
        path: Path,
        operation_key: str,
        destination: Path,
    ) -> Path:
        assert path.read_bytes() == b"native-hdf5"
        assert operation_key == "export_table"
        destination.write_text("scientific export\n", encoding="utf-8")
        return destination

    def table_group(self, path: Path, title: str) -> str:
        del path
        return f"Table · {title}"

    def plot_group(self, path: Path, title: str, kind: str, family_key: str) -> str:
        del path, kind, family_key
        return f"Plot · {title}"

    def plot_description(
        self,
        path: Path,
        title: str,
        kind: str,
        family_key: str,
    ) -> str:
        del path, kind, family_key
        return f"Description for {title}"


def _service(
    tmp_path: Path,
    *,
    backend: FakeResultBackend | None = None,
    compatibility: BackendCompatibility = READY,
    max_upload_bytes: int = 1024,
) -> ResultExplorerService:
    return ResultExplorerService(
        workspace_store=LocalWorkspaceStore(tmp_path),
        backend=backend or FakeResultBackend(),
        max_upload_bytes=max_upload_bytes,
        compatibility=compatibility,
    )


def _contents(payload: bytes) -> str:
    return "data:application/x-hdf5;base64," + b64encode(payload).decode("ascii")


def test_upload_is_stored_under_opaque_workspace(tmp_path: Path) -> None:
    service = _service(tmp_path)
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
    service = _service(tmp_path)
    with pytest.raises(ResultUploadError):
        service.ingest_upload(filename="result.txt", contents=_contents(b"native-hdf5"))


def test_upload_rejects_oversized_payload(tmp_path: Path) -> None:
    service = _service(tmp_path, max_upload_bytes=4)
    with pytest.raises(ResultUploadError):
        service.ingest_upload(filename="result.h5", contents=_contents(b"too-large"))


def test_windows_style_browser_path_is_reduced_to_display_name(tmp_path: Path) -> None:
    service = _service(tmp_path)
    reference, _ = service.ingest_upload(
        filename=r"C:\Users\example\calcite.hdf5",
        contents=_contents(b"native-hdf5"),
    )
    assert reference.filename == "calcite.hdf5"


def test_unavailable_backend_blocks_before_decoding_or_workspace_write(tmp_path: Path) -> None:
    class ExplodingBackend(FakeResultBackend):
        def inspect(self, path: Path) -> ResultOverview:
            raise AssertionError("backend inspection must not start")

    service = _service(
        tmp_path,
        backend=ExplodingBackend(),
        compatibility=UNAVAILABLE,
    )
    with pytest.raises(ResultBackendUnavailable, match="Required Quantas version"):
        service.ingest_upload(
            filename="result.h5",
            contents="not-even-a-data-url",
        )
    assert list(tmp_path.iterdir()) == []


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

        def build_tables(self, path: Path, family_key: str | None = None):
            self.table_calls += 1
            return super().build_tables(path, family_key)

        def build_plots(
            self,
            path: Path,
            family_key: str | None = None,
            selection: PlotBuildSelection | None = None,
        ):
            self.plot_calls += 1
            return super().build_plots(path, family_key, selection)

    backend = CountingBackend()
    service = _service(tmp_path, backend=backend)
    reference, _ = service.ingest_upload(
        filename="result.h5",
        contents=_contents(b"native-hdf5"),
    )
    assert service.build_tables(reference) is service.build_tables(reference)
    assert service.build_plots(reference) is service.build_plots(reference)
    assert backend.table_calls == 1
    assert backend.plot_calls == 1


def test_scientific_export_uses_controlled_workspace_and_cache(tmp_path: Path) -> None:
    service = _service(tmp_path)
    reference, _ = service.ingest_upload(
        filename="calcite.hdf5",
        contents=_contents(b"native-hdf5"),
    )

    descriptors = service.scientific_exports(reference)
    assert descriptors[0].enabled

    first = service.build_scientific_export(reference, "export_table")
    second = service.build_scientific_export(reference, "export_table")

    assert first == second
    assert first.read_text(encoding="utf-8") == "scientific export\n"
    assert first.parent.name == reference.result_id
    assert first.parent.parent.name == "exports"


def test_result_service_caches_scientific_selections_independently(tmp_path: Path) -> None:
    class CountingBackend(FakeResultBackend):
        plot_calls = 0

        def plot_families(self, path: Path):
            del path
            from quantas_gui.explorer.models import PlotFamilyDescriptor

            return (
                PlotFamilyDescriptor(
                    "temperature_curves",
                    "Temperature curves",
                    "Selected sections.",
                    default=True,
                ),
            )

        def build_plots(
            self,
            path: Path,
            family_key: str | None = None,
            selection: PlotBuildSelection | None = None,
        ):
            self.plot_calls += 1
            return super().build_plots(path, family_key, selection)

    backend = CountingBackend()
    service = _service(tmp_path, backend=backend)
    reference, _ = service.ingest_upload(
        filename="result.h5",
        contents=_contents(b"native-hdf5"),
    )
    first = PlotBuildSelection(
        "temperature_curves",
        ("free_energy",),
        (("sampled_volume", (10.0,)),),
    )
    second = PlotBuildSelection(
        "temperature_curves",
        ("free_energy",),
        (("sampled_volume", (11.0,)),),
    )

    assert service.build_plots(reference, selection=first) is service.build_plots(
        reference, selection=first
    )
    service.build_plots(reference, selection=second)

    assert backend.plot_calls == 2


def test_result_service_reuses_multi_property_surface_selection(tmp_path: Path) -> None:
    class CountingBackend(FakeResultBackend):
        plot_calls = 0

        def plot_families(self, path: Path):
            del path
            from quantas_gui.explorer.models import PlotFamilyDescriptor

            return (
                PlotFamilyDescriptor(
                    "property_surface_3d",
                    "General scalar-field surface",
                    "Selected scalar fields.",
                    default=True,
                ),
            )

        def build_plots(
            self,
            path: Path,
            family_key: str | None = None,
            selection: PlotBuildSelection | None = None,
        ):
            self.plot_calls += 1
            return super().build_plots(path, family_key, selection)

    backend = CountingBackend()
    service = _service(tmp_path, backend=backend)
    reference, _ = service.ingest_upload(
        filename="seismic.h5",
        contents=_contents(b"native-hdf5"),
    )
    selection = PlotBuildSelection(
        "property_surface_3d",
        ("phase_v_p", "shear_anisotropy"),
        (("surface_geometry", "unit_sphere"),),
    )

    first = service.build_plots(reference, "property_surface_3d", selection=selection)
    second = service.build_plots(reference, "property_surface_3d", selection=selection)

    assert first is second
    assert backend.plot_calls == 1


def test_workflow_result_registration_uses_existing_controlled_file(tmp_path: Path) -> None:
    service = _service(tmp_path)
    workspace_id = service.workspace_store.create_workspace()
    result_id = "elasticity-result"
    path = service.workspace_store.write_result_bytes(
        workspace_id=workspace_id,
        result_id=result_id,
        payload=b"native-hdf5",
    )

    reference, overview = service.register_result(
        workspace_id=workspace_id,
        result_id=result_id,
        filename="elasticity.hdf5",
    )

    assert reference.disposable_workspace is False
    assert reference.size_bytes == path.stat().st_size
    assert overview.summary.module == "elasticity"
    service.close(reference)
    assert path.is_file()


def test_uploaded_result_keeps_disposable_workspace_lifecycle(tmp_path: Path) -> None:
    service = _service(tmp_path)
    reference, _ = service.ingest_upload(
        filename="uploaded.hdf5",
        contents=_contents(b"native-hdf5"),
    )
    path = service.path(reference)
    assert reference.disposable_workspace is True

    service.close(reference)

    assert not path.exists()


def test_active_result_state_round_trips_workflow_handoff(tmp_path: Path) -> None:
    service = _service(tmp_path)
    reference, overview = service.ingest_upload(
        filename="active.hdf5",
        contents=_contents(b"native-hdf5"),
    )

    state = ActiveResultState(reference=reference, summary=overview.summary)
    restored = ActiveResultState.from_dict(state.as_dict())

    assert restored == state
    assert restored.reference.workspace_id == reference.workspace_id
    assert restored.summary.module == "elasticity"


def test_result_service_delegates_presentation_grouping_to_backend(tmp_path: Path) -> None:
    service = _service(tmp_path)
    reference, _ = service.ingest_upload(
        filename="grouped.hdf5",
        contents=_contents(b"native-hdf5"),
    )

    assert service.table_group(reference, "Summary") == "Table · Summary"
    assert service.plot_group(reference, "Surface", "SurfacePlotSpec", "surface") == (
        "Plot · Surface"
    )
    assert (
        service.plot_description(
            reference,
            "Surface",
            "SurfacePlotSpec",
            "surface",
        )
        == "Description for Surface"
    )


def test_close_during_table_build_does_not_resurrect_cache_or_workspace(
    tmp_path: Path,
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import sleep

    class BlockingBackend(FakeResultBackend):
        def __init__(self) -> None:
            self.started = Event()
            self.release = Event()

        def table_families(self, path: Path):
            del path
            from quantas_gui.explorer.models import TableFamilyDescriptor

            return (TableFamilyDescriptor("default", "Report", "Default", default=True),)

        def build_tables(self, path: Path, family_key: str | None = None):
            self.started.set()
            assert self.release.wait(timeout=5)
            return super().build_tables(path, family_key)

    backend = BlockingBackend()
    service = _service(tmp_path, backend=backend)
    reference, _ = service.ingest_upload(
        filename="closing.hdf5",
        contents=_contents(b"native-hdf5"),
    )
    service.table_families(reference)
    path = service.path(reference)

    with ThreadPoolExecutor(max_workers=2) as executor:
        build = executor.submit(service.build_tables, reference)
        assert backend.started.wait(timeout=2)
        close = executor.submit(service.close, reference)
        sleep(0.05)
        assert path.is_file()
        assert not close.done()
        backend.release.set()
        assert build.result(timeout=3)[0].title == "Summary"
        assert close.result(timeout=3) is None

    assert not path.exists()
    assert service.cache.stats()["entries"] == 0
    assert service.cache.stats()["inflight"] == 0
