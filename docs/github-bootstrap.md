# Creating the GitHub repository

The source tree contains no authentication token or personal remote
configuration. A repository can therefore be created from a local checkout
without modifying the package.

## Create it with GitHub CLI

After installing and authenticating `gh`, run from the project root:

```bash
./scripts/bootstrap_github.sh
```

The script initializes Git with `main`, creates the first commit, creates the
remote repository and pushes the branch. Owner, repository name and visibility
can be changed through environment variables:

```bash
GITHUB_OWNER=my-account \
GITHUB_REPOSITORY_NAME=quantas-gui \
GITHUB_VISIBILITY=private \
./scripts/bootstrap_github.sh
```

## Recommended settings

After the first complete green CI run:

- protect `main` and require the aggregate `CI gate`;
- use pull requests and squash merges;
- delete merged branches automatically;
- enable Dependabot security updates and secret scanning;
- leave Pages, deployment and publishing secrets disabled until a real release
  process exists.

Detailed settings are described in
[repository-hardening.md](repository-hardening.md).
