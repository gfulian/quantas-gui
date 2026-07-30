# Deployment roadmap

Quantas GUI starts as a local application, but the code avoids shortcuts that
would force the pages to be rewritten for server use. Deployment will mature in
stages.

## Stage 1 — local application

```text
browser → Dash on 127.0.0.1 → local backend → quantas.api
                                      ↓
                               local HDF5 workspace
```

The launcher opens the browser and does not expose the service to the network by
default. This remains the simplest way to use the GUI on one workstation.

## Stage 2 — laboratory server

```text
browser → HTTPS reverse proxy → WSGI application → shared queue
                                                      ↓
                                                 Quantas workers
                                                      ↓
                                           shared result storage
```

The application factory, URL prefix, WSGI entry point, health endpoints, opaque
workspace identifiers, cross-process locks and atomic publication are already
in place. Result Explorer requests can be served by several workers sharing the
same filesystem.

Long scientific calculations will be connected as workflows are introduced.
They must not remain inside an HTTP request, and the server will not claim to
support them until a real job backend has been implemented and tested.

## Stage 3 — public service

Opening the application to untrusted users requires additional operational
work:

- authentication and workspace ownership;
- result expiry and deletion;
- limits on uploads, CPU, memory, duration and concurrency;
- rate limiting and audit logs;
- HTTPS, secure cookies, CSP, HSTS and non-debug error handling;
- suitable isolation for workers and accepted input files.

Changing only the `host` value does not turn a local application into a secure
public service.
