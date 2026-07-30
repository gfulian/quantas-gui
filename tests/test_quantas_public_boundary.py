from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "quantas_gui"
_FORBIDDEN_PREFIXES = (
    "quantas.cli",
    "quantas.modules",
    "quantas.core",
    "quantas.models",
    "quantas.renderers",
    "h5py",
)


def test_scientific_integration_imports_only_quantas_api() -> None:
    offenders: list[str] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(_FORBIDDEN_PREFIXES):
                    offenders.append(f"{path.relative_to(SOURCE_ROOT)}:{node.lineno}:{node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(_FORBIDDEN_PREFIXES):
                        offenders.append(
                            f"{path.relative_to(SOURCE_ROOT)}:{node.lineno}:{alias.name}"
                        )
    assert not offenders, "forbidden backend imports:\n" + "\n".join(offenders)


def test_result_backend_does_not_depend_on_hdf5_implementation() -> None:
    source = (SOURCE_ROOT / "services" / "result_backend.py").read_text(encoding="utf-8")
    assert "h5py" not in source
    assert "registry.module_from_result" in source
    assert "registry.open_result" in source
    assert ".describe_plots(" in source


def test_plotly_dispatch_uses_public_plot_classes() -> None:
    source = (SOURCE_ROOT / "renderers" / "plotly" / "renderer.py").read_text(encoding="utf-8")
    assert 'import_module("quantas.api.plotting")' in source
    assert "isinstance(spec, spec_type)" in source
    assert "type(spec).__name__" not in source
