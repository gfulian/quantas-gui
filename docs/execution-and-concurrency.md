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

`0.3.0a2` provides `LocalProcessExecutionBackend`. It uses Python's `spawn`
context on every supported platform, so Windows and Unix systems exercise the
same process boundary. A submitted request is already persisted in its
workspace before the process starts. Status is stored atomically as JSON,
events are appended as ordered JSON lines under a file lock, and the final
native result is published through the workspace's atomic-output contract.

The application process owns only a small process registry used to detect an
unhandled worker exit. Scientific requests, events and outputs are filesystem
state, so closing or refreshing the browser does not terminate the job. This
implementation is deliberately enabled only in local mode and reports
`process_shared=False`.

A multi-worker deployment still needs a persistent queue and process ownership
shared by all WSGI workers. The project has not selected a product; Celery,
Redis or another stack will be evaluated only when server requirements justify
it. Server mode therefore keeps workflow execution disabled unless another
`ExecutionBackend` is injected.

## Cancellation

Cancellation is cooperative. The local backend writes a cancellation marker and
moves the visible state to `cancelling`. The Elasticity observer checks that
marker at structured Quantas event and progress boundaries; the worker also
checks before calculation, before HDF5 writing and before final publication.
Only the worker can confirm `cancelled`, after the atomic-output context has
removed its temporary file and any unpublished destination has been deleted.

The current public Elasticity API accepts an observer but does not expose a
separate cancellation token inside every numerical kernel. Cancellation latency
therefore depends on the next emitted event or explicit worker checkpoint. This
is a recorded backend-contract limitation, not a reason for the GUI to
terminate the process unsafely or to report cancellation early.

## Elasticity callback boundary

`0.3.0a2` connects the local backend without moving calculation into Dash. The
submit callback performs only structural coercion, request persistence and
`ExecutionBackend.submit()`. A 750 ms interval polls persistent status and
ordered events by cursor. Cancellation writes a cooperative request; it does
not terminate the process from the HTTP callback.

The visible activity stream is bounded in browser session state. Scientific
arrays, result objects, file paths and HDF5 resources are removed from events
before persistence. For 3D Elasticity, the form adapter chooses an internal
bounded batch size from the requested grid so progress remains observable on
larger samples. This parameter is operational, is not presented as a scientific
choice and does not change the calculated grid or property values.

When execution is disabled, as in the default multi-worker server profile, the
page renders an explicit unavailable state rather than presenting a form that
cannot submit.
