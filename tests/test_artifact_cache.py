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


def test_concurrent_requests_share_one_factory_execution() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, Lock

    cache = LocalArtifactCache(max_entries=4)
    started = Event()
    release = Event()
    calls = 0
    calls_lock = Lock()
    value = object()

    def factory() -> object:
        nonlocal calls
        with calls_lock:
            calls += 1
        started.set()
        assert release.wait(timeout=2)
        return value

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(cache.get_or_create, ("w", "r", "plots"), factory) for _ in range(8)
        ]
        assert started.wait(timeout=2)
        release.set()
        results = [future.result(timeout=2) for future in futures]

    assert calls == 1
    assert all(result is value for result in results)
    assert cache.stats()["coalesced"] == 7


def test_invalidation_during_factory_prevents_stale_reinsertion() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    cache = LocalArtifactCache(max_entries=4)
    started = Event()
    release = Event()
    first = object()

    def slow_factory() -> object:
        started.set()
        assert release.wait(timeout=2)
        return first

    key = ("workspace", "result", "overview")
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(cache.get_or_create, key, slow_factory)
        assert started.wait(timeout=2)
        cache.invalidate_prefix(("workspace", "result"))
        release.set()
        assert future.result(timeout=2) is first

    assert cache.stats()["entries"] == 0
    second = object()
    assert cache.get_or_create(key, lambda: second) is second
    assert cache.stats()["entries"] == 1


def test_factory_exceptions_are_shared_and_retryable() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    cache = LocalArtifactCache(max_entries=4)
    started = Event()
    release = Event()

    def broken() -> object:
        started.set()
        assert release.wait(timeout=2)
        raise ValueError("broken")

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(cache.get_or_create, ("key",), broken)
        second = executor.submit(cache.get_or_create, ("key",), broken)
        assert started.wait(timeout=2)
        release.set()
        for future in (first, second):
            try:
                future.result(timeout=2)
            except ValueError as error:
                assert str(error) == "broken"
            else:
                raise AssertionError("expected shared factory error")

    recovered = object()
    assert cache.get_or_create(("key",), lambda: recovered) is recovered


def test_new_request_after_invalidation_does_not_join_stale_flight() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    cache = LocalArtifactCache(max_entries=4)
    first_started = Event()
    first_release = Event()
    second_started = Event()
    first_value = object()
    second_value = object()
    key = ("workspace", "result", "overview")

    def first_factory() -> object:
        first_started.set()
        assert first_release.wait(timeout=3)
        return first_value

    def second_factory() -> object:
        second_started.set()
        return second_value

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(cache.get_or_create, key, first_factory)
        assert first_started.wait(timeout=2)
        cache.invalidate_prefix(("workspace", "result"))
        second = executor.submit(cache.get_or_create, key, second_factory)
        assert second_started.wait(timeout=2)
        assert second.result(timeout=2) is second_value
        first_release.set()
        assert first.result(timeout=2) is first_value

    assert cache.get_or_create(key, lambda: object()) is second_value
    assert cache.stats()["entries"] == 1
