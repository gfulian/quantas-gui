# Quantas GUI design system

Quantas Dark remains the default scientific theme and stable product identity.
Quantas Light provides an alternative high-legibility presentation using the
same structural blue and scientific orange accents. A System option resolves to
the browser operating-system preference.

## Palette

- background: `#071522`;
- deep background: `#04101a`;
- structural blue: `#69bce8`;
- strong blue: `#2994d1`;
- scientific accent orange: `#ed8a28`;
- success: `#50c6a9`;
- warning: `#f0b75a`;
- error: `#f06c75`.

Base tokens live in `assets/00_tokens.css`. Theme, typography-scale, motion,
and density overrides live in `assets/60_settings.css`. Layout, components,
and responsive rules consume variables rather than changing scientific data.
Results Explorer rules are isolated in `assets/40_results.css`.

## Visual priorities

1. scientific figures and tables remain visually dominant;
2. warnings and errors are unambiguous but not theatrical;
3. controls use stable spacing and hierarchy across workflows;
4. mobile layouts remain usable for inspection, while large scientific editing
   tasks may still recommend a larger display;
5. motion respects `prefers-reduced-motion`;
6. renderer toolbars collapse cleanly without hiding scientific context.

## Reusable renderer controls

Renderer controls are components, not page-specific markup. The initial set
contains table/plot selectors, page size, colormap, hover mode, spherical
projection, message filtering, and visibility toggles. Controls should be added
only when they can be applied without altering scientific data.

## Scientific images

Landing cards use representative Quantas-generated figures, not generic stock
photography. These images are static previews; workflow pages use interactive
Plotly figures generated from neutral Quantas plot specifications.

## Browser-local preferences

The Settings page writes only presentation values to a local `dcc.Store`. The
client-side preference callback sets theme and accessibility attributes on the
document root. Scientific inputs, raw table values, PlotCollection data, and
HDF5 content remain independent. See [Interface settings](settings.md).
