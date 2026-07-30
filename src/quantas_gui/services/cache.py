"""Replaceable server-side cache for expensive Explorer artifacts.

The local implementation is bounded and process-local. It provides single-flight
construction within one process, so concurrent Dash callbacks requesting the
same report or PlotCollection share one factory execution. Namespace
invalidation detaches in-flight factories so their values cannot be reinserted
after a result has been closed.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from threading import Event, RLock
from typing import Any, Protocol, TypeVar, cast

ValueT = TypeVar("ValueT")
_MISSING = object()


class ArtifactCache(Protocol):
    """Cache operations required by application services."""

    def get_or_create(self, key: Hashable, factory: Callable[[], ValueT]) -> ValueT:
        """Return a cached value or create and retain it."""

    def invalidate_prefix(self, prefix: tuple[Hashable, ...]) -> None:
        """Remove entries whose tuple key starts with *prefix*."""

    def clear(self) -> None:
        """Remove every cached artifact."""

    def stats(self) -> dict[str, int]:
        """Return lightweight diagnostic counters."""


@dataclass(slots=True)
class _Flight:
    completed: Event = field(default_factory=Event)
    value: Any = _MISSING
    error: BaseException | None = None


@dataclass(slots=True)
class LocalArtifactCache:
    """Thread-safe bounded least-recently-used cache for local mode.

    The cache is safe for concurrent threads in one WSGI worker. Separate WSGI
    workers intentionally keep independent caches; the workspace lock prevents
    concurrent HDF5 access, while a future shared implementation may provide cross-process cache
    reuse through the same :class:`ArtifactCache` protocol.
    """

    max_entries: int = 48
    _values: OrderedDict[Hashable, Any] = field(default_factory=OrderedDict, init=False)
    _inflight: dict[Hashable, _Flight] = field(default_factory=dict, init=False)
    _lock: RLock = field(default_factory=RLock, init=False)
    hits: int = field(default=0, init=False)
    misses: int = field(default=0, init=False)
    coalesced: int = field(default=0, init=False)
    invalidations: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.max_entries < 1:
            raise ValueError("max_entries must be positive")

    def get_or_create(self, key: Hashable, factory: Callable[[], ValueT]) -> ValueT:
        """Return one value with single-flight construction per cache key."""
        with self._lock:
            if key in self._values:
                self.hits += 1
                value = self._values.pop(key)
                self._values[key] = value
                return cast(ValueT, value)

            flight = self._inflight.get(key)
            if flight is not None:
                self.coalesced += 1
                owner = False
            else:
                flight = _Flight()
                self._inflight[key] = flight
                self.misses += 1
                owner = True

        if not owner:
            flight.completed.wait()
            if flight.error is not None:
                raise flight.error
            if flight.value is _MISSING:
                raise RuntimeError("cache construction completed without a value")
            return cast(ValueT, flight.value)

        try:
            value = factory()
        except BaseException as exc:
            with self._lock:
                flight.error = exc
                if self._inflight.get(key) is flight:
                    self._inflight.pop(key, None)
                flight.completed.set()
            raise

        with self._lock:
            flight.value = value
            active = self._inflight.get(key) is flight
            if active:
                self._inflight.pop(key, None)
                self._values[key] = value
                while len(self._values) > self.max_entries:
                    self._values.popitem(last=False)
            flight.completed.set()
        return value

    def invalidate_prefix(self, prefix: tuple[Hashable, ...]) -> None:
        """Invalidate cached and in-flight values in one result namespace."""
        with self._lock:
            cached = {key for key in self._values if _matches_prefix(key, prefix)}
            in_flight = {key for key in self._inflight if _matches_prefix(key, prefix)}
            for key in cached:
                self._values.pop(key, None)
            for key in in_flight:
                # Existing callers may finish, but the detached owner can no
                # longer publish its value. A later request starts a new flight.
                self._inflight.pop(key, None)
            if cached or in_flight:
                self.invalidations += 1

    def clear(self) -> None:
        """Remove all retained values without resurrecting in-flight factories."""
        with self._lock:
            self._inflight.clear()
            self._values.clear()
            self.hits = 0
            self.misses = 0
            self.coalesced = 0
            self.invalidations = 0

    def stats(self) -> dict[str, int]:
        """Return lightweight diagnostic counters."""
        with self._lock:
            return {
                "entries": len(self._values),
                "inflight": len(self._inflight),
                "max_entries": self.max_entries,
                "hits": self.hits,
                "misses": self.misses,
                "coalesced": self.coalesced,
                "invalidations": self.invalidations,
            }


def _matches_prefix(key: Hashable, prefix: tuple[Hashable, ...]) -> bool:
    return isinstance(key, tuple) and key[: len(prefix)] == prefix
