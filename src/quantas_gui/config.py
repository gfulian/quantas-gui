"""Environment-driven application settings.

The configuration object describes deployment policy without coupling Dash
pages to a concrete cache, workspace, or execution implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from os import environ
from pathlib import Path

from platformdirs import user_data_path

_VALID_MODES = frozenset({"local", "server"})


def _as_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean value {value!r}")


def _normalise_prefix(value: str) -> str:
    stripped = value.strip()
    if not stripped or stripped == "/":
        return "/"
    if "://" in stripped or any(character in stripped for character in ("\\", "?", "#")):
        raise ValueError("url_prefix must be a URL path without query or fragment")
    parts = tuple(part for part in stripped.strip("/").split("/") if part)
    if not parts or any(
        part in {".", ".."} or not part.isprintable() or any(char.isspace() for char in part)
        for part in parts
    ):
        raise ValueError("url_prefix contains an invalid path segment")
    return f"/{'/'.join(parts)}/"


def _csv_tuple(value: str | None, *, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings shared by local and WSGI deployments.

    ``local`` mode is a single-user loopback application. ``server`` mode is a
    WSGI deployment profile: browser launch and Dash debug tools are forbidden,
    forwarded proxy headers are trusted only when ``proxy_hops`` is explicitly
    positive, and the workspace root must be shared by every WSGI worker that
    serves the same application instance.
    """

    mode: str
    host: str
    port: int
    open_browser: bool
    debug: bool
    workspace_root: Path
    max_upload_bytes: int
    url_prefix: str
    result_cache_entries: int
    workspace_lock_timeout_seconds: float
    proxy_hops: int
    secure_cookies: bool
    trusted_hosts: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(_VALID_MODES)!r}")
        if not self.host.strip():
            raise ValueError("host must not be empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if self.max_upload_bytes < 1:
            raise ValueError("max_upload_bytes must be positive")
        if self.result_cache_entries < 1:
            raise ValueError("result_cache_entries must be positive")
        if self.workspace_lock_timeout_seconds <= 0:
            raise ValueError("workspace_lock_timeout_seconds must be positive")
        if self.proxy_hops < 0:
            raise ValueError("proxy_hops must not be negative")
        if self.mode == "server" and self.open_browser:
            raise ValueError("server mode cannot open a browser")
        if self.mode == "server" and self.debug:
            raise ValueError("server mode cannot enable Dash debug tools")
        for trusted_host in self.trusted_hosts:
            if (
                not trusted_host
                or "://" in trusted_host
                or "/" in trusted_host
                or any(character.isspace() for character in trusted_host)
            ):
                raise ValueError(f"invalid trusted host {trusted_host!r}")

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
            result_cache_entries=48,
            workspace_lock_timeout_seconds=300.0,
            proxy_hops=0,
            secure_cookies=False,
            trusted_hosts=("127.0.0.1", "localhost"),
        )

    @classmethod
    def server_defaults(cls) -> Settings:
        """Return conservative defaults for a WSGI laboratory deployment."""
        local = cls.local_defaults()
        return cls(
            mode="server",
            host="0.0.0.0",
            port=8050,
            open_browser=False,
            debug=False,
            workspace_root=local.workspace_root,
            max_upload_bytes=local.max_upload_bytes,
            url_prefix="/",
            result_cache_entries=local.result_cache_entries,
            workspace_lock_timeout_seconds=local.workspace_lock_timeout_seconds,
            proxy_hops=0,
            secure_cookies=True,
            trusted_hosts=(),
        )

    @classmethod
    def from_environment(cls, *, defaults: Settings | None = None) -> Settings:
        """Build settings from ``QUANTAS_GUI_*`` environment variables.

        Parameters
        ----------
        defaults
            Baseline profile. The local launcher uses :meth:`local_defaults`,
            while the WSGI entry point passes :meth:`server_defaults`.
        """
        baseline = defaults or cls.local_defaults()
        mode = environ.get("QUANTAS_GUI_MODE", baseline.mode).strip().lower()
        server_mode = mode == "server"
        open_browser_default = False if server_mode else baseline.open_browser
        debug_default = False if server_mode else baseline.debug
        secure_cookie_default = True if server_mode else baseline.secure_cookies
        return cls(
            mode=mode,
            host=environ.get("QUANTAS_GUI_HOST", baseline.host),
            port=int(environ.get("QUANTAS_GUI_PORT", str(baseline.port))),
            open_browser=_as_bool(
                environ.get("QUANTAS_GUI_OPEN_BROWSER"),
                default=open_browser_default,
            ),
            debug=_as_bool(
                environ.get("QUANTAS_GUI_DEBUG"),
                default=debug_default,
            ),
            workspace_root=Path(
                environ.get("QUANTAS_GUI_WORKSPACE", str(baseline.workspace_root))
            ).expanduser(),
            max_upload_bytes=int(
                environ.get("QUANTAS_GUI_MAX_UPLOAD", str(baseline.max_upload_bytes))
            ),
            url_prefix=_normalise_prefix(
                environ.get("QUANTAS_GUI_URL_PREFIX", baseline.url_prefix)
            ),
            result_cache_entries=int(
                environ.get(
                    "QUANTAS_GUI_RESULT_CACHE_ENTRIES",
                    str(baseline.result_cache_entries),
                )
            ),
            workspace_lock_timeout_seconds=float(
                environ.get(
                    "QUANTAS_GUI_WORKSPACE_LOCK_TIMEOUT",
                    str(baseline.workspace_lock_timeout_seconds),
                )
            ),
            proxy_hops=int(environ.get("QUANTAS_GUI_PROXY_HOPS", str(baseline.proxy_hops))),
            secure_cookies=_as_bool(
                environ.get("QUANTAS_GUI_SECURE_COOKIES"),
                default=secure_cookie_default,
            ),
            trusted_hosts=_csv_tuple(
                environ.get("QUANTAS_GUI_TRUSTED_HOSTS"),
                default=baseline.trusted_hosts,
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
        workspace_lock_timeout_seconds: float | None = None,
        proxy_hops: int | None = None,
        secure_cookies: bool | None = None,
        trusted_hosts: tuple[str, ...] | None = None,
    ) -> Settings:
        """Return a copy containing validated application overrides."""
        resolved_mode = self.mode if mode is None else mode
        resolved_open_browser = self.open_browser if open_browser is None else open_browser
        resolved_debug = self.debug if debug is None else debug
        if resolved_mode == "server":
            if open_browser is None:
                resolved_open_browser = False
            if debug is None:
                resolved_debug = False
        return Settings(
            mode=resolved_mode,
            host=self.host if host is None else host,
            port=self.port if port is None else port,
            open_browser=resolved_open_browser,
            debug=resolved_debug,
            workspace_root=self.workspace_root if workspace_root is None else workspace_root,
            max_upload_bytes=(
                self.max_upload_bytes if max_upload_bytes is None else max_upload_bytes
            ),
            url_prefix=self.url_prefix if url_prefix is None else _normalise_prefix(url_prefix),
            result_cache_entries=(
                self.result_cache_entries if result_cache_entries is None else result_cache_entries
            ),
            workspace_lock_timeout_seconds=(
                self.workspace_lock_timeout_seconds
                if workspace_lock_timeout_seconds is None
                else workspace_lock_timeout_seconds
            ),
            proxy_hops=self.proxy_hops if proxy_hops is None else proxy_hops,
            secure_cookies=(self.secure_cookies if secure_cookies is None else secure_cookies),
            trusted_hosts=self.trusted_hosts if trusted_hosts is None else trusted_hosts,
        )

    def prepare_workspace(self) -> Path:
        """Create and return the controlled workspace root."""
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        return self.workspace_root.resolve()
