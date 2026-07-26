# Deployment roadmap

## Stage 1 — local application

```text
browser → Dash on 127.0.0.1 → local execution backend → quantas.api
                                      ↓
                               local HDF5 workspace
```

The launcher opens a browser and does not expose the service to the network by
default. Debug mode is opt-in.

## Stage 2 — laboratory server

```text
browser → HTTPS reverse proxy → WSGI Dash app → Redis/Celery queue
                                                  ↓
                                             Quantas workers
                                                  ↓
                                         shared result storage
```

The application factory, URL-prefix support, WSGI entry point, health endpoint,
workspace identifiers, and execution protocols are already present.

## Stage 3 — public service

Before public access, add:

- authentication and user/session ownership;
- isolated workspaces and expiring results;
- upload type and size validation;
- CPU, memory, duration, and concurrency quotas;
- rate limits and audit logging;
- HTTPS, secure cookies, CSP, HSTS, and non-debug error handling;
- worker/container isolation appropriate to accepted input formats.

A public deployment is an operational security project, not merely a different
value for `host`.
