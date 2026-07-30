# Publishing the repository from Windows

When the remote repository already exists, the safest GitHub Desktop workflow
is to clone it first and copy the prepared source into that clone. This keeps
the `.git` directory created by GitHub Desktop intact.

## 1. Clone the repository

In GitHub Desktop choose **File → Clone repository**, select
`gfulian/quantas-gui` and choose a local directory, for example:

```text
C:\Users\<name>\Documents\GitHub\quantas-gui
```

## 2. Copy the source

Extract the Quantas GUI archive to a temporary directory and copy **its
contents** into the new clone. Do not copy another `.git` directory and do not
delete the one created by GitHub Desktop.

The copy should include source, tests, documentation, `.github` files,
constraints, scripts and packaging metadata. Do not include `.venv`, caches,
build directories or local output.

## 3. Validate the checkout

The recommended validator does not depend on PowerShell execution policy:

```powershell
.\scripts\validate_windows.cmd "C:\path\to\quantas"
```

It creates or updates `.venv`, reinstalls Quantas GUI with the current
dependencies — including `filelock` — and runs the full quality gate.

The PowerShell version remains available. On a machine that blocks unsigned
scripts, invoke it with a policy limited to that process:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
    .\scripts\validate_windows.ps1 `
    -QuantasPath "C:\path\to\quantas"
```

There is no need to weaken the machine-wide policy.

After the automated gate, open both application profiles:

```powershell
quantas-gui
quantas-gui --ui-kit
```

## 4. Commit and push

Review the changed files in GitHub Desktop, create a descriptive commit and
choose **Push origin**. Once CI is green, enable the protection rules described
in [repository-hardening.md](repository-hardening.md).
