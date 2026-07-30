# Interface settings

GUI preferences are stored in the browser. They change presentation only: they
are not part of a scientific request, are not passed to `quantas.api` and are
never written into native HDF5 results.

## Theme

- **System** follows the operating-system light or dark preference;
- **Quantas Dark** keeps the dark theme;
- **Quantas Light** keeps the light theme.

A small bootstrap script applies the theme before Dash finishes loading, which
avoids a visible flash between modes. Plotly uses the effective theme for text,
axes, hover labels and backgrounds without changing the data.

## Text size

Four scales are available: compact, standard, comfortable and large. The choice
changes the CSS variable `--q-ui-scale`; numeric precision, data formatting and
CSV exports remain unchanged.

## Motion

The default respects `prefers-reduced-motion`. The explicit reduced setting
further limits transitions and non-essential movement.

## Table density

Density changes AG Grid row and header heights. It does not remove data or
change filtering, pagination or exported files.

## Persistence

Preferences belong to the browser profile. A future authenticated server may
optionally synchronize them, but browser preference storage must never contain
scientific results, paths, credentials or private server state.

The UI Kit uses the same preferences, but it starts only with
`quantas-gui --ui-kit` and is not linked from the normal Settings page.
