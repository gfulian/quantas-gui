"""Pattern-matching identifiers for reusable Quantas GUI forms."""

from __future__ import annotations

from typing import Any


class FormIds:
    """Create aligned dictionary identifiers for a declarative form."""

    @staticmethod
    def control(form: str, field: str, part: str = "value") -> dict[str, Any]:
        """Return the identifier of one concrete input control."""
        return {"type": "q-form-control", "form": form, "field": field, "part": part}

    @staticmethod
    def wrapper(form: str, field: str) -> dict[str, Any]:
        """Return the identifier of one field wrapper."""
        return {"type": "q-form-wrapper", "form": form, "field": field}

    @staticmethod
    def error(form: str, field: str) -> dict[str, Any]:
        """Return the identifier of one field validation slot."""
        return {"type": "q-form-error", "form": form, "field": field}

    @staticmethod
    def section(form: str, section: str) -> dict[str, Any]:
        """Return the identifier of one form section."""
        return {"type": "q-form-section", "form": form, "section": section}

    @staticmethod
    def submit(form: str) -> dict[str, Any]:
        """Return the identifier of the form submit action."""
        return {"type": "q-form-submit", "form": form}

    @staticmethod
    def reset(form: str) -> dict[str, Any]:
        """Return the identifier of the form reset action."""
        return {"type": "q-form-reset", "form": form}

    @staticmethod
    def summary(form: str) -> dict[str, Any]:
        """Return the identifier of the form-level validation summary."""
        return {"type": "q-form-summary", "form": form}


__all__ = ["FormIds"]
