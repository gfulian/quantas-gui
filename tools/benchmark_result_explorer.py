"""Measure native Explorer construction and Plotly conversion for one result."""

from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter

from quantas_gui.renderers.plotly import plot_inventory, render_collection_plot
from quantas_gui.services.result_backend import QuantasResultBackend


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    backend = QuantasResultBackend()
    path = args.result.expanduser().resolve()

    started = perf_counter()
    overview = backend.inspect(path)
    print(f"inspect: {perf_counter() - started:.4f}s · {overview.summary.module}")

    for family in backend.table_families(path):
        started = perf_counter()
        tables = backend.build_tables(path, family.key)
        print(f"tables/{family.key}: {perf_counter() - started:.4f}s · {len(tables)} tables")

    for family in backend.plot_families(path):
        started = perf_counter()
        collection = backend.build_plots(path, family.key)
        build_time = perf_counter() - started
        inventory = plot_inventory(collection, family_key=family.key)
        print(f"plots/{family.key}: {build_time:.4f}s · {len(inventory)} plots")
        if inventory:
            started = perf_counter()
            figure = render_collection_plot(collection, inventory[0].key)
            print(
                f"  first figure: {perf_counter() - started:.4f}s · "
                f"{len(figure.to_json()) / 1024.0:.1f} KiB JSON"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
