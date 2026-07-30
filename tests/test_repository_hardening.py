"""Regression checks for repository governance and workflow hardening."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_every_external_action_is_pinned_to_a_full_sha() -> None:
    uses_lines = [
        line.strip() for line in _workflow_text().splitlines() if line.strip().startswith("uses:")
    ]
    assert uses_lines
    for line in uses_lines:
        reference = line.split("@", 1)[1].split(maxsplit=1)[0]
        assert FULL_SHA.fullmatch(reference), line


def test_workflow_is_read_only_and_does_not_use_pull_request_target() -> None:
    text = _workflow_text()
    assert "permissions:\n  contents: read" in text
    assert "pull_request_target" not in text
    assert "persist-credentials: false" in text


def test_workflow_exposes_one_aggregate_gate_and_dependency_review() -> None:
    text = _workflow_text()
    assert "name: CI gate" in text
    assert "name: Dependency review" in text
    assert "needs: [test, package, dependency-review]" in text
    assert "fail-on-severity: moderate" in text


def test_repository_routes_security_reports_privately() -> None:
    issue_config = (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
    policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    advisory_url = "https://github.com/gfulian/quantas-gui/security/advisories/new"
    assert advisory_url in issue_config
    assert advisory_url in policy
