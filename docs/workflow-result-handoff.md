# Handing a workflow result to the Explorer

Uploads and completed calculations use the same Result Explorer, but ownership
of their files is different.

## Browser upload

1. Check backend compatibility before decoding.
2. Create an isolated Explorer workspace.
3. Write the upload atomically.
4. Identify and open it through `quantas.api.registry`.
5. Store only the opaque active-result state in the browser.
6. On close, invalidate artifacts and remove the Explorer-owned workspace.

## Completed workflow

1. The execution backend writes native Quantas HDF5 in its controlled
   workspace.
2. The workflow registers `workspace_id`, `result_id` and a display filename
   with `ResultExplorerService.register_result()`.
3. The service validates the controlled path through the normal public backend.
4. The workflow writes the returned reference and summary to the global result
   session store.
5. The application navigates to `/results`.
6. Closing the Explorer invalidates its artifacts but leaves the workflow-owned
   workspace intact.

No filesystem path, HDF5 object, calculator, table, PlotSpec or large array is
placed in browser state.

`ElasticityWorkflowService.active_result()` performs the server-side
registration and returns an `ActiveResultState`. Since `0.3.0a4`, the handoff is
intentionally two-stage: the workflow callback first writes that state to the
global result session, then a separate callback observes the committed store
and navigates to `/results`. A one-shot page hydration trigger runs after the
Result Explorer layout is mounted, causing the shell, header and initial tab to
consume the existing global session. No scientific result is rebuilt or
serialised in the browser.

## Example

```python
from quantas_gui.models import ActiveResultState

reference, overview = result_service.register_result(
    workspace_id=workspace_id,
    result_id=result_id,
    filename="elasticity.hdf5",
)

session_payload = ActiveResultState(
    reference=reference,
    summary=overview.summary,
).as_dict()
```

The workflow callback writes `session_payload` to `ResultIds.SESSION`. A
separate navigation callback moves to `/results` only after the global store
reports that exact payload. The workflow does not import Explorer callback
helpers or duplicate the Explorer interface.

## Completion card

A workflow page should finish with a compact summary containing status, key
results, warnings, native HDF5 download, an **Open in Result Explorer** action
and any valid downstream interoperability actions. Detailed tables and figures
remain in the shared Explorer.
