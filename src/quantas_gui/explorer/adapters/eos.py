"""Presentation adapter for the session-oriented EOS archive."""

from __future__ import annotations

from typing import Any

from quantas_gui.explorer.adapters.base import ResultModuleAdapter


class EOSAdapter(ResultModuleAdapter):
    """Provide presentation labels while archive discovery remains specialized."""

    name = "eos"

    def plot_families(
        self,
        namespace: Any,
        result: Any,
        inventory: Any,
    ) -> tuple[Any, ...]:
        del namespace, result, inventory
        return ()

    def table_group(self, title: str) -> str:
        normalized = title.lower()
        if "dataset" in normalized:
            return "Datasets"
        if "slot" in normalized:
            return "Result slots"
        if "history" in normalized or "record" in normalized:
            return "Fit history"
        return "EOS archive"

    def plot_group(self, title: str, kind: str, family_key: str) -> str:
        del title, kind, family_key
        return "EOS diagnostics"

    def plot_description(self, title: str, kind: str, family_key: str) -> str:
        del kind, family_key
        return f"{title}: read-only public EOS archive representation."
