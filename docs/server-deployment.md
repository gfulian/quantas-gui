# Server deployment

Quantas GUI is a WSGI Dash application. The current alpha supports local use
and controlled laboratory deployment. It is not yet a hardened public
multi-user service.

## Supported boundary

A laboratory deployment may use several WSGI workers on one host or on hosts
that share a filesystem with reliable locks and atomic rename behaviour.
Workspaces must use the same configured root. Artifact caches are currently
local to each worker.

The production entry point is:

```text
quantas_gui.wsgi:server
```

## Configuration

Important environment variables include:

```text
QUANTAS_GUI_MODE=server
QUANTAS_GUI_WORKSPACE_ROOT=<controlled directory>
QUANTAS_GUI_URL_PREFIX=/quantas/
QUANTAS_GUI_TRUSTED_HOSTS=host1,host2
QUANTAS_GUI_PROXY_HOPS=<number of trusted proxies>
QUANTAS_GUI_SECURE_COOKIES=true
QUANTAS_GUI_MAX_UPLOAD_BYTES=<limit>
QUANTAS_GUI_RESULT_CACHE_ENTRIES=<per-process cache size>
QUANTAS_GUI_WORKSPACE_LOCK_TIMEOUT=<seconds>
```

Server mode disables browser opening and Dash debug tools. Proxy headers are
trusted only when the number of proxy hops is configured explicitly.

## Windows laboratory server

Install the server extra and run Waitress:

```powershell
python -m pip install -e ".[server,performance]"
waitress-serve --listen=127.0.0.1:8050 quantas_gui.wsgi:server
```

Waitress is the supported production WSGI option on Windows. The built-in Dash
server remains a development tool.

## Linux laboratory server

Install the same extra and run Gunicorn:

```bash
python -m pip install -e ".[server,performance]"
gunicorn --workers 4 --bind 127.0.0.1:8050 quantas_gui.wsgi:server
```

Choose worker count according to memory and expected traffic. Scientific jobs
will eventually run in separate worker processes or a queue rather than inside
these WSGI workers.

## Reverse proxy and URL prefix

When the application sits behind Nginx, Apache or another proxy, set a URL
prefix and configure the proxy to preserve it. Configure trusted hosts and the
exact number of proxy hops; do not accept forwarded headers from arbitrary
clients.

TLS should normally terminate at the reverse proxy. Enable secure cookies when
the user-facing connection is HTTPS.

## Health endpoints

- `/healthz` reports that the web process is alive.
- `/readyz` reports whether the required Quantas backend and public contracts
  are ready. It returns HTTP `503` when scientific features cannot be served.

Monitoring should use both. A live process is not necessarily ready for
scientific work.

## Before public exposure

A public service still needs:

- authentication and authorization;
- per-user workspace ownership;
- upload quotas and file-content validation;
- CPU, memory, time and concurrency limits;
- isolated scientific workers;
- a persistent shared queue and job store;
- rate limiting;
- retention and secure deletion policies;
- operational logging, metrics and alerting;
- backup and recovery procedures.

Until these are implemented and tested, keep the deployment on a trusted
machine or laboratory network.
