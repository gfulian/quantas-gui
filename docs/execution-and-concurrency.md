# Execution and concurrency

This guide explains the safeguards added before the first executable workflow.
They matter on a desktop too: Dash can issue overlapping requests, and a server
may use several WSGI workers.

## Result access

Each workspace has a portable file lock and a small closing marker. Reads and
exports acquire a shared logical lease. Deletion first marks the workspace as
closing, which prevents new readers, and then waits for current readers to
finish.

This avoids several common failures:

- deleting an HDF5 file while another callback is reading it;
- opening a partially written upload;
- exporting into a path that appears complete before the write has finished;
- reopening a workspace after close has started.

## Artifact cache

The process-local cache is single-flight by key. If several callbacks request
the same report or PlotSpec at once, one builder performs the work and the
others receive its result.

Each result namespace has an invalidation generation. When the result is closed,
in-flight work may finish for the request that started it, but it cannot put a
stale artifact back into the cache.

A future server may replace this cache with a shared implementation without
changing callbacks or module adapters.

## Atomic publication

Uploads, exports and generated results are written to a temporary file in the
same workspace, flushed and then moved to the final name with an atomic replace.
On failure the temporary file is removed. Consumers therefore see either the
previous complete file or the new complete file, never a half-written result.

## Long workflows

A scientific calculation that may take seconds, minutes or hours must not run
inside a Dash callback. The callback submits a request to an
`ExecutionBackend` and immediately receives an opaque `JobHandle`.

The backend contract provides:

- queued, running, cancelling, succeeded, failed and cancelled states;
- bounded progress values;
- ordered events with a cursor;
- cancellation requests;
- a final opaque result identifier;
- a description of backend capabilities.

The browser stores only the handle and event cursor. Requests, logs and results
remain server-side.

## Local and server implementations

The first implementation in `0.3` will use a separate local process, allowing a
long Elasticity calculation to continue without occupying the HTTP request.

A multi-worker deployment will need a persistent queue and job store shared by
all WSGI workers. The project has not selected a product yet; Celery, Redis or
another stack will be evaluated when real workflow requirements are available.

## Cancellation

Cancellation is cooperative. The backend records the request and the worker
stops at a safe boundary exposed by the scientific operation. The interface
must not claim that a job is cancelled until the worker confirms it and any
partial output has been cleaned up or clearly quarantined.
