# GitHub repository bootstrap

The source tree is ready to become the public `gfulian/quantas-gui` repository.
No remote repository or authentication token is embedded in the package.

## One-command creation

Install and authenticate the GitHub CLI, then run from the repository root:

```bash
./scripts/bootstrap_github.sh
```

The script:

1. initializes Git with `main` as the default branch;
2. creates the initial commit;
3. creates `gfulian/quantas-gui` as a public repository;
4. configures `origin` and pushes `main`.

The owner, repository name, and visibility can be overridden:

```bash
GITHUB_OWNER=my-account \
GITHUB_REPOSITORY_NAME=quantas-gui \
GITHUB_VISIBILITY=private \
./scripts/bootstrap_github.sh
```

## Recommended repository settings

After the first successful CI run:

- protect `main` and require the `test` and `package` jobs;
- require pull requests before merging;
- prefer squash merges and automatically delete merged branches;
- enable Dependabot security updates and secret scanning;
- keep GitHub Pages disabled until a documentation site exists;
- do not add deployment or package-publishing secrets during the visual-alpha phase.

## First milestone

Create a milestone named `0.1.0a1 — Results Explorer foundation` and add issues for:

- Quantas HDF5 identification through `quantas.api.registry`;
- result metadata and event rendering;
- neutral `ReportTable` renderer;
- Plotly renderer dispatcher;
- shared plot controls, beginning with `cmap_selector`;
- first complete Elasticity workflow.
