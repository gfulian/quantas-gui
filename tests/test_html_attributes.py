"""Static guards for literal HTML wildcard attributes used by Dash."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src" / "quantas_gui"


def test_aria_and_data_attributes_use_literal_hyphenated_names() -> None:
    """Reject ``aria_label=``/``data_testid=`` before Dash serializes layout."""
    violations: list[str] = []

    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg is None:
                    continue
                if keyword.arg.startswith(("aria_", "data_")):
                    relative = path.relative_to(SOURCE_ROOT.parent)
                    violations.append(f"{relative}:{node.lineno}: {keyword.arg}")

    assert not violations, (
        "Dash wildcard HTML attributes must be passed with literal hyphenated "
        "names, for example **{'aria-label': '...'}:\n" + "\n".join(violations)
    )
