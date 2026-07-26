# Changelog

All notable changes to Quantas GUI will be documented in this file.

The project follows Semantic Versioning while the public interface remains under
active alpha development.

## 0.2.1a1 — 2026-07-26

First repository-ready alpha for the public `gfulian/quantas-gui` project.

### Added

- browser-local **Settings** page;
- Quantas Dark, Quantas Light, and operating-system theme selection;
- compact, standard, comfortable, and large typography scales;
- reduced-motion and table-density preferences;
- local browser persistence that never modifies Quantas inputs or HDF5 files;
- theme synchronization for the application shell, Dash AG Grid, and Result
  Explorer Plotly figures;
- direct Settings access from the sidebar, top bar, and responsive navigation;
- Windows and GitHub Desktop bootstrap instructions for the existing remote
  repository.

### Changed

- rewrote the repository README as a concise introduction, installation, and current-status guide;
- replaced the internal incremental roadmap with capability milestones from `0.1` through the stable `1.0` release;
- expanded CONTRIBUTING with development, architecture, scientific, testing, and pull-request guidance;
- rewrote the landing-page copy in a technical, scientific style;
- removed fabricated recent-workspace entries from the landing page;
- replaced promotional capability wording with explicit implementation and
  architecture descriptions;
- retained Quantas Dark as the default theme;
- kept the Scientific UI Kit accessible from both navigation and Settings.

### Fixed

- replaced the incomplete component-probe exception list with a reusable Dash
  generated-component probe that discovers required explicit properties at
  runtime;
- added the required probe identifier for `dcc.Store`;
- applied the same probe implementation to pytest and the standalone Dash
  component audit, preventing the two checks from diverging.

### Existing foundation included in this alpha

- responsive Dash application shell;
- Scientific UI Kit and declarative form system;
- controlled native-HDF5 Result Explorer;
- module-aware adapters for Elasticity, SEISMIC, HA, QHA,
  Thermoelasticity, and the structurally separate EOS archive;
- lazy server-side report and plot construction with bounded artifact caching;
- Plotly renderers for Cartesian, polar, contour, surface, spherical, and panel
  specifications;
- replaceable workspace, result-store, and execution-backend seams for future
  server deployment.

## Unreleased

### Planned

- systematic scientific review of every module-specific Plotly view;
- improved Plotly export, camera, annotation, comparison, and unit controls;
- first complete executable workflow, beginning with Elasticity;
- local background-job execution with Quantas progress events;
- server-side worker and shared-cache implementations without changing page
  contracts.
