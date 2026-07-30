# Repository protection

These settings protect the source, CI pipeline and future releases. They do not
replace application security and do not mean that the alpha is ready for an
untrusted public deployment.

## Safeguards already stored in the repository

The project includes a cross-platform CI matrix, one aggregate `CI gate`,
dependency review, reduced GitHub Actions permissions, actions pinned to
immutable SHAs, timeouts, cancellation of superseded runs, short artifact
retention, CODEOWNERS, templates and grouped Dependabot updates.

## Protecting `main`

Apply the ruleset only after a complete CI run is green. In **Settings → Rules
→ Rulesets**, create a rule for the default branch that requires:

- a pull request;
- resolved conversations;
- linear history;
- an up-to-date branch before merge;
- the `CI gate` status check;
- blocked deletion and force pushes.

With one maintainer, required approvals may remain at zero. A limited
administrator bypass is useful only for recovering from a broken ruleset or CI
configuration, not for normal development.

## Pull requests and merges

Enable squash merging, disable merge commits and delete merged branches
automatically. Day-to-day work should use short branches such as `feature/...`,
`fix/...`, `docs/...` or `chore/...`.

## GitHub Actions

In the Actions settings:

- allow only GitHub-owned or explicitly approved actions;
- keep default permissions read-only;
- prevent actions from approving pull requests;
- require approval for outside contributors;
- use short retention while the project is in alpha.

## Repository security

Enable the dependency graph, Dependabot alerts and security updates, secret
scanning with push protection, private vulnerability reporting and CodeQL for
Python.

The maintainer account also needs two-factor authentication, recovery codes and
regular review of SSH keys, tokens and authorized applications.

## Before a public release

Before the first stable distribution, protect tags matching `v*`, publish with
PyPI Trusted Publishing, generate artifact attestations and document the release
and rollback procedure.
