"""Replaceable server-side cache for expensive Explorer artifacts.

The local implementation is intentionally process-local and bounded.  The
protocol keeps callers independent from the storage mechanism so a future
server deployment can replace it with Redis or a filesystem cache without
changing Dash pages or scientific adapters.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Protocol, TypeVar, cast

ValueT = TypeVar("ValueT")


class ArtifactCache(Protocol):
    """Cache operations required by application services."""

    def get_or_create(self, key: Hashable, factory: Callable[[], ValueT]) -> ValueT:
        """Return a cached value or create and retain it."""

    def invalidate_prefix(self, prefix: tuple[Hashable, ...]) -> None:
        """Remove entries whose tuple key starts with *prefix*."""

    def clear(self) -> None:
        """Remove every cached artifact."""


@dataclass(slots=True)
class LocalArtifactCache:
    """Thread-safe bounded least-recently-used cache for local mode.

    Parameters
    ----------
    max_entries
        Maximum number of overview, table, plot, and rendered-figure artifacts
        retained by one application process.
    """

    max_entries: int = 48
    _values: OrderedDict[Hashable, Any] = field(default_factory=OrderedDict, init=False)
    _lock: RLock = field(default_factory=RLock, init=False)
    hits: int = field(default=0, init=False)
    misses: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.max_entries < 1:
            raise ValueError("max_entries must be positive")

    def get_or_create(self, key: Hashable, factory: Callable[[], ValueT]) -> ValueT:
        """Return one value while avoiding duplicate local construction."""
        with self._lock:
            if key in self._values:
                self.hits += 1
                value = self._values.pop(key)
                self._values[key] = value
                return cast(ValueT, value)
        value = factory()
        with self._lock:
            # Another thread may have completed the same artifact meanwhile.
            if key in self._values:
                self.hits += 1
                cached = self._values.pop(key)
                self._values[key] = cached
                return cast(ValueT, cached)
            self.misses += 1
            self._values[key] = value
            while len(self._values) > self.max_entries:
                self._values.popitem(last=False)
        return value

    def invalidate_prefix(self, prefix: tuple[Hashable, ...]) -> None:
        """Remove all tuple-keyed artifacts in one result namespace."""
        with self._lock:
            doomed = [
                key
                for key in self._values
                if isinstance(key, tuple) and key[: len(prefix)] == prefix
            ]
            for key in doomed:
                self._values.pop(key, None)

    def clear(self) -> None:
        """Remove all cached artifacts and reset counters."""
        with self._lock:
            self._values.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> dict[str, int]:
        """Return lightweight diagnostic counters."""
        with self._lock:
            return {
                "entries": len(self._values),
                "max_entries": self.max_entries,
                "hits": self.hits,
                "misses": self.misses,
            }
