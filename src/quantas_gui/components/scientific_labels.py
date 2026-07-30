"""Compatibility facade for scientific label presentation helpers.

New code should import these renderer-neutral helpers from
:mod:`quantas_gui.presentation.scientific_labels`.
"""

from quantas_gui.presentation.scientific_labels import (
    display_unit,
    quantity_unit_label,
    scientific_label_text,
    scientific_math_label,
)

__all__ = [
    "display_unit",
    "quantity_unit_label",
    "scientific_label_text",
    "scientific_math_label",
]
