"""Presentation adapter for the session-oriented EOS archive."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter


class EOSAdapter(ResultModuleAdapter):
    """Keep EOS structural inspection separate from fit-session visualization."""

    name = "eos"

    def plot_families(self, namespace: Any, result: Any):
        del namespace, result
        return ()
