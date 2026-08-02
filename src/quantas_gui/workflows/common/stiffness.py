"""Shared structural parsing for editable Voigt stiffness matrices."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

_MATRIX_TOKEN = re.compile(r"[\s,;]+")


def parse_stiffness_text(text: str) -> tuple[tuple[float, ...], ...]:
    """Parse one full or triangular 6 × 6 numerical stiffness matrix.

    This helper performs only structural coercion. A complete matrix with both
    triangles populated is preserved exactly so final symmetry tolerances and
    scientific validation remain owned by Quantas.
    """
    rows: list[tuple[float, ...]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("[]()|")
        if not line:
            continue
        tokens = [token for token in _MATRIX_TOKEN.split(line) if token]
        try:
            row = tuple(float(token) for token in tokens)
        except ValueError as exc:
            raise ValueError(f"Matrix row {len(rows) + 1} contains a non-numerical value.") from exc
        if not all(math.isfinite(value) for value in row):
            raise ValueError(f"Matrix row {len(rows) + 1} must contain only finite values.")
        rows.append(row)
    if len(rows) != 6:
        raise ValueError(f"The stiffness matrix must contain exactly six rows; found {len(rows)}.")

    row_lengths = tuple(len(row) for row in rows)
    if row_lengths == (6, 6, 6, 6, 6, 6):
        return _expand_zero_padded_triangle(rows)
    if row_lengths == (6, 5, 4, 3, 2, 1):
        return _expand_compact_triangle(rows, upper=True)
    if row_lengths == (1, 2, 3, 4, 5, 6):
        return _expand_compact_triangle(rows, upper=False)
    raise ValueError(
        "The stiffness matrix must be a full 6 × 6 matrix, an upper triangle "
        "with 6, 5, …, 1 values per row, or a lower triangle with "
        "1, 2, …, 6 values per row."
    )


def format_stiffness(matrix: Sequence[Sequence[float]]) -> str:
    """Format one stiffness tensor for the canonical editable textarea."""
    rows = tuple(tuple(float(value) for value in row) for row in matrix)
    if len(rows) != 6 or any(len(row) != 6 for row in rows):
        raise ValueError("stiffness must have shape (6, 6)")
    return "\n".join(" ".join(f"{value:14.8g}" for value in row) for row in rows)


def _expand_compact_triangle(
    rows: Sequence[Sequence[float]],
    *,
    upper: bool,
) -> tuple[tuple[float, ...], ...]:
    matrix = [[0.0 for _ in range(6)] for _ in range(6)]
    for row_index, row in enumerate(rows):
        start_column = row_index if upper else 0
        for offset, value in enumerate(row):
            column_index = start_column + offset
            matrix[row_index][column_index] = float(value)
            matrix[column_index][row_index] = float(value)
    return tuple(tuple(row) for row in matrix)


def _expand_zero_padded_triangle(
    rows: Sequence[Sequence[float]],
) -> tuple[tuple[float, ...], ...]:
    matrix = tuple(tuple(float(value) for value in row) for row in rows)
    lower_is_padding = all(
        _is_structural_zero(matrix[row][column]) for row in range(6) for column in range(row)
    )
    upper_is_padding = all(
        _is_structural_zero(matrix[row][column]) for row in range(6) for column in range(row + 1, 6)
    )
    if lower_is_padding and not upper_is_padding:
        return _mirror_full_triangle(matrix, upper=True)
    if upper_is_padding and not lower_is_padding:
        return _mirror_full_triangle(matrix, upper=False)
    return matrix


def _mirror_full_triangle(
    matrix: Sequence[Sequence[float]],
    *,
    upper: bool,
) -> tuple[tuple[float, ...], ...]:
    expanded = [list(row) for row in matrix]
    for row in range(6):
        for column in range(row + 1, 6):
            if upper:
                expanded[column][row] = expanded[row][column]
            else:
                expanded[row][column] = expanded[column][row]
    return tuple(tuple(float(value) for value in row) for row in expanded)


def _is_structural_zero(value: float) -> bool:
    return math.isclose(value, 0.0, rel_tol=0.0, abs_tol=1.0e-12)


__all__ = ["format_stiffness", "parse_stiffness_text"]
