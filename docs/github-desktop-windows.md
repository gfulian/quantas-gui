# Populate the GitHub repository from Windows

The remote repository already exists at `gfulian/quantas-gui`. The safest
GitHub Desktop workflow is to clone that repository first and then copy the
prepared source tree into the clone. This preserves the hidden `.git`
directory and avoids publishing a nested repository.

## 1. Clone with GitHub Desktop

1. Open **GitHub Desktop**.
2. Choose **File → Clone repository**.
3. Select `gfulian/quantas-gui`.
4. Choose a local path, for example:

   ```text
   C:\Users\<name>\Documents\GitHub\quantas-gui
   ```

5. Complete the clone.

The remote currently contains an initial README. It is expected to be replaced
by the repository-ready README supplied with this source tree.

## 2. Copy the prepared repository content

Extract the Quantas GUI source archive to a temporary directory. Copy **the
contents** of that directory into the GitHub Desktop clone, including:

```text
.github
constraints
docs
scripts
src
tests
tools
.editorconfig
.env.example
.gitignore
CITATION.cff
CHANGELOG.md
CODE_OF_CONDUCT.md
CONTRIBUTING.md
LICENSE
MANIFEST.in
README.md
ROADMAP.md
SECURITY.md
pyproject.toml
```

Do not copy a `.git` directory from another location and do not delete the
`.git` directory created by GitHub Desktop.

## 3. Validate in PowerShell

From the cloned repository:

```powershell
cd C:\Users\<name>\Documents\GitHub\quantas-gui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,performance]"
python -m pip install -e "C:\path\to\quantas"
python tools\audit_dash_components.py
python -m pytest -q
quantas-gui

# Or run the repository helper:
.\scripts\validate_windows.ps1 -QuantasPath "C:\\path\\to\\quantas"
```

The `.venv` directory is ignored by Git and must not be committed.

## 4. Commit and publish

In GitHub Desktop:

1. Review the complete change list.
2. Use a commit message such as:

   ```text
   Initialize Quantas GUI 0.2.1a1
   ```

3. Commit to `main`.
4. Choose **Push origin**.

After the first CI run succeeds, enable branch protection for `main` and
require the CI check before merging future pull requests.
