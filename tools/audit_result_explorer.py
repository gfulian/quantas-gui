"""Audit Result Explorer report and plot construction against native HDF5 files.

The audit uses the same public Quantas gateway and Plotly translation used by
Quantas GUI. It builds one family at a time, releases large artifacts between
families, and verifies that read-only inspection leaves each HDF5 file unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
from collections.abc import Iterable
from pathlib import Path

from quantas_gui.renderers.plotly import plot_inventory, render_collection_plot
from quantas_gui.services.result_backend import QuantasResultBackend


def main() -> int:
    """Run the requested audits and return a process-style status code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", nargs="+", type=Path, help="native Quantas HDF5 files")
    parser.add_argument(
        "--first-plot-only",
        action="store_true",
        help="render only the first PlotSpec in each advertised family",
    )
    parser.add_argument(
        "--skip-tables",
        action="store_true",
        help="skip report-family construction",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="skip PlotSpec construction and Plotly translation",
    )
    args = parser.parse_args()

    backend = QuantasResultBackend()
    failures = 0
    for path in _resolved_paths(args.results):
        failures += _audit_result(
            backend,
            path,
            first_plot_only=bool(args.first_plot_only),
            skip_tables=bool(args.skip_tables),
            skip_plots=bool(args.skip_plots),
        )
    return 1 if failures else 0


def _audit_result(
    backend: QuantasResultBackend,
    path: Path,
    *,
    first_plot_only: bool,
    skip_tables: bool,
    skip_plots: bool,
) -> int:
    before = _sha256(path)
    failures: list[str] = []
    print(f"\n== {path.name} ==")
    try:
        overview = backend.inspect(path)
        print(f"module: {overview.summary.module}")

        table_count = 0
        row_count = 0
        if not skip_tables:
            for family in backend.table_families(path):
                tables = None
                try:
                    tables = tuple(backend.build_tables(path, family.key))
                    rows = sum(len(table.rows) for table in tables)
                    table_count += len(tables)
                    row_count += rows
                    print(f"tables/{family.key}: {len(tables)} tables · {rows} rows")
                except Exception as exc:  # pragma: no cover - exercised by real audits
                    failures.append(f"tables/{family.key}: {exc}")
                finally:
                    tables = None

        plot_count = 0
        if not skip_plots:
            for family in backend.plot_families(path):
                collection = None
                inventory = None
                try:
                    collection = backend.build_plots(path, family.key)
                    inventory = plot_inventory(collection, family_key=family.key)
                    selected = inventory[:1] if first_plot_only else inventory
                    for descriptor in selected:
                        figure = render_collection_plot(collection, descriptor.key)
                        plot_count += 1
                        print(
                            f"plots/{family.key}/{descriptor.key}: {len(figure.data)} Plotly traces"
                        )
                        del figure
                    if not inventory:
                        print(f"plots/{family.key}: no constructible PlotSpecs")
                except Exception as exc:  # pragma: no cover - exercised by real audits
                    failures.append(f"plots/{family.key}: {exc}")
                finally:
                    inventory = None
                    collection = None

        print(f"summary: {table_count} tables · {row_count} rows · {plot_count} figures")
    except Exception as exc:  # pragma: no cover - exercised by real audits
        failures.append(f"open/inspect: {exc}")

    unchanged = before == _sha256(path)
    print(f"read-only checksum: {'PASS' if unchanged else 'FAIL'}")
    if not unchanged:
        failures.append("native HDF5 checksum changed during read-only inspection")
    for failure in failures:
        print(f"FAIL: {failure}")
    return len(failures)


def _resolved_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    resolved: list[Path] = []
    for path in paths:
        candidate = path.expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        resolved.append(candidate)
    return tuple(resolved)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
