#!/usr/bin/env bash
set -euo pipefail

OWNER="${GITHUB_OWNER:-gfulian}"
REPOSITORY="${GITHUB_REPOSITORY_NAME:-quantas-gui}"
VISIBILITY="${GITHUB_VISIBILITY:-public}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required: https://cli.github.com/" >&2
  exit 1
fi

gh auth status

if [[ ! -d .git ]]; then
  git init -b main
fi

git add .
if ! git diff --cached --quiet; then
  git commit -m "Initial Quantas GUI scaffold"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "Remote origin already exists: $(git remote get-url origin)"
else
  gh repo create "${OWNER}/${REPOSITORY}" \
    "--${VISIBILITY}" \
    --source=. \
    --remote=origin \
    --push \
    --description "Modern Dash and Plotly graphical interface for Quantas"
fi
