# Interface settings

Quantas GUI stores presentation preferences in the browser through a local
`dcc.Store`. They are not part of the scientific request, are not passed to
`quantas.api`, and are never written to native HDF5 results.

## Available preferences

### Theme

- **Quantas Dark** — default theme;
- **Quantas Light** — light surfaces with the same blue and orange scientific
  accents;
- **System** — follows the operating-system colour preference.

The effective theme is applied client-side to avoid a server round trip and is
also made available to the Result Explorer so Plotly figures use a compatible
background and text palette.

### Text size

The typography scale is applied through the inherited `--q-ui-scale` CSS
variable:

- compact: `0.90`;
- standard: `1.00`;
- comfortable: `1.12`;
- large: `1.25`.

Display scaling does not change numerical formatting, stored precision, or CSV
exports.

### Motion

The default respects `prefers-reduced-motion`. The explicit reduced setting
minimises transitions and non-essential movement regardless of the browser
profile.

### Table density

The density preference changes shared AG Grid row and header heights. It does
not remove rows or alter pagination, filtering, or exported data.

## Persistence and server deployment

Preferences are stored per browser profile. A future authenticated server may
optionally synchronize user preferences, but the current local-storage contract
should remain the fallback and must never contain scientific results, paths,
credentials, or private server state.
