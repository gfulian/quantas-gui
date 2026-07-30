## What changes

Describe the problem and the behaviour visible to users.

## Architectural boundary

- [ ] Scientific work uses only `quantas.api`.
- [ ] Large scientific data remain server-side.
- [ ] The GUI does not introduce its own formulas or conventions.
- [ ] Browser state contains only identifiers and lightweight state.

## Security and repository hygiene

- [ ] No credentials, private data, local paths or generated files are included.
- [ ] Dependency changes are intentional and respect the declared baselines.
- [ ] GitHub Actions keep minimal permissions and immutable SHA pins.

## Validation performed

- [ ] `python tools/run_checks.py`
- [ ] desktop review, when visual behaviour changes
- [ ] mobile review, when visual behaviour changes
- [ ] Quantas Dark and Quantas Light review
- [ ] scientific comparison with API/CLI, when applicable
- [ ] `CHANGELOG.md` and `PROJECT_STATE.md` updated, when needed
