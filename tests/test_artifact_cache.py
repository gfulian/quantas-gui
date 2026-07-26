from __future__ import annotations

from quantas_gui.services.cache import LocalArtifactCache


def test_local_artifact_cache_reuses_and_invalidates_namespaces() -> None:
    cache = LocalArtifactCache(max_entries=4)
    calls = 0

    def factory() -> object:
        nonlocal calls
        calls += 1
        return object()

    first = cache.get_or_create(("workspace", "result", "plots", "surface"), factory)
    second = cache.get_or_create(("workspace", "result", "plots", "surface"), factory)
    assert first is second
    assert calls == 1
    assert cache.stats()["hits"] == 1

    cache.invalidate_prefix(("workspace", "result"))
    third = cache.get_or_create(("workspace", "result", "plots", "surface"), factory)
    assert third is not first
    assert calls == 2
