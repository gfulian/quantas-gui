"""Environment-driven application settings.

The configuration object deliberately describes deployment policy without
binding the Dash pages to a particular execution backend or storage system.
"""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
from pathlib import Path

from platformdirs import user_data_path


def _as_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalise_prefix(value: str) -> str:
    stripped = value.strip()
    if not stripped or stripped == "/":
        return "/"
    return f"/{stripped.strip('/')}/"


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings shared by local and future server deployments.

    Parameters
    ----------
    mode
        Deployment mode label. The initial implementation supports ``local``;
        future implementations may use ``server`` without changing page code.
    host
        Interface on which the local development server listens.
    port
        Preferred TCP port. The local launcher finds the next available port
        when this value is already in use.
    open_browser
        Whether the local launcher opens the default web browser.
    debug
        Enable Dash development tools. This must remain disabled in server
        deployments.
    workspace_root
        Server-side root for uploads, requests, jobs, and HDF5 results.
    max_upload_bytes
        Maximum decoded native-result file size accepted by the Explorer.
    url_prefix
        URL prefix used when the app is mounted below a reverse-proxy path.
    redis_url
        Optional Redis connection used by a future distributed job backend.
    result_cache_entries
        Maximum number of prepared Explorer artifacts retained by the local
        in-process least-recently-used cache.
    """

    mode: str
    host: str
    port: int
    open_browser: bool
    debug: bool
    workspace_root: Path
    max_upload_bytes: int
    url_prefix: str
    redis_url: str | None
    result_cache_entries: int

    @classmethod
    def local_defaults(cls) -> Settings:
        """Return safe defaults for a single-user local installation."""
        return cls(
            mode="local",
            host="127.0.0.1",
            port=8050,
            open_browser=True,
            debug=False,
            workspace_root=user_data_path("quantas-gui", "Quantas") / "workspaces",
            max_upload_bytes=256 * 1024 * 1024,
            url_prefix="/",
            redis_url=None,
            result_cache_entries=48,
        )

    @classmethod
    def from_environment(cls) -> Settings:
        """Build settings from ``QUANTAS_GUI_*`` environment variables."""
        defaults = cls.local_defaults()
        return cls(
            mode=environ.get("QUANTAS_GUI_MODE", defaults.mode),
            host=environ.get("QUANTAS_GUI_HOST", defaults.host),
            port=int(environ.get("QUANTAS_GUI_PORT", str(defaults.port))),
            open_browser=_as_bool(
                environ.get("QUANTAS_GUI_OPEN_BROWSER"), default=defaults.open_browser
            ),
            debug=_as_bool(environ.get("QUANTAS_GUI_DEBUG"), default=defaults.debug),
            workspace_root=Path(
                environ.get("QUANTAS_GUI_WORKSPACE", str(defaults.workspace_root))
            ).expanduser(),
            max_upload_bytes=int(
                environ.get("QUANTAS_GUI_MAX_UPLOAD", str(defaults.max_upload_bytes))
            ),
            url_prefix=_normalise_prefix(
                environ.get("QUANTAS_GUI_URL_PREFIX", defaults.url_prefix)
            ),
            redis_url=environ.get("REDIS_URL"),
            result_cache_entries=max(
                8,
                int(
                    environ.get(
                        "QUANTAS_GUI_RESULT_CACHE_ENTRIES",
                        str(defaults.result_cache_entries),
                    )
                ),
            ),
        )

    @property
    def max_request_bytes(self) -> int:
        """Return an HTTP-body limit that includes base64 and JSON overhead."""
        encoded = (self.max_upload_bytes * 4 + 2) // 3
        return encoded + 2 * 1024 * 1024

    def with_overrides(
        self,
        *,
        mode: str | None = None,
        host: str | None = None,
        port: int | None = None,
        open_browser: bool | None = None,
        debug: bool | None = None,
        workspace_root: Path | None = None,
        max_upload_bytes: int | None = None,
        url_prefix: str | None = None,
        result_cache_entries: int | None = None,
    ) -> Settings:
        """Return a copy containing validated application overrides."""
        return Settings(
            mode=self.mode if mode is None else mode,
            host=self.host if host is None else host,
            port=self.port if port is None else port,
            open_browser=self.open_browser if open_browser is None else open_browser,
            debug=self.debug if debug is None else debug,
            workspace_root=self.workspace_root if workspace_root is None else workspace_root,
            max_upload_bytes=(
                self.max_upload_bytes if max_upload_bytes is None else max_upload_bytes
            ),
            url_prefix=self.url_prefix if url_prefix is None else _normalise_prefix(url_prefix),
            redis_url=self.redis_url,
            result_cache_entries=(
                self.result_cache_entries if result_cache_entries is None else result_cache_entries
            ),
        )

    def prepare_workspace(self) -> Path:
        """Create and return the controlled workspace root."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        return self.workspace_root
