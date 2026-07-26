"""Registry of scientific presentation adapters."""

from __future__ import annotations

from quantas_gui.explorer.adapters.base import ResultModuleAdapter
from quantas_gui.explorer.adapters.elasticity import ElasticityAdapter
from quantas_gui.explorer.adapters.eos import EOSAdapter
from quantas_gui.explorer.adapters.ha import HAAdapter
from quantas_gui.explorer.adapters.qha import QHAAdapter
from quantas_gui.explorer.adapters.seismic import SeismicAdapter
from quantas_gui.explorer.adapters.thermoelasticity import ThermoelasticityAdapter


_ADAPTERS: dict[str, ResultModuleAdapter] = {
    adapter.name: adapter
    for adapter in (
        ElasticityAdapter(),
        SeismicAdapter(),
        HAAdapter(),
        QHAAdapter(),
        ThermoelasticityAdapter(),
        EOSAdapter(),
    )
}
_GENERIC = ResultModuleAdapter()


def adapter_for(module_name: str) -> ResultModuleAdapter:
    """Return the registered adapter or the generic public-API adapter."""
    return _ADAPTERS.get(str(module_name), _GENERIC)


def registered_adapters() -> tuple[str, ...]:
    """Return stable registered module names."""
    return tuple(_ADAPTERS)
