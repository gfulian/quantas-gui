from __future__ import annotations

from quantas_gui.presentation.scientific_labels import (
    quantity_unit_label,
    scientific_label_text,
    scientific_math_label,
)


def test_selector_labels_convert_quantas_math_to_readable_unicode() -> None:
    assert scientific_label_text(r"$V_P$") == "Vₚ"
    assert scientific_label_text(r"$V_{S1}$ (km s$^{-1}$)") == "Vₛ₁ (km s⁻¹)"
    assert scientific_label_text(r"$\alpha_V$ (K$^{-1}$)") == "αᵥ (K⁻¹)"


def test_selector_conversion_does_not_rewrite_plain_scientific_text() -> None:
    assert scientific_label_text("Pressure (GPa)") == "Pressure (GPa)"


def test_selector_labels_unwrap_nested_math_commands_and_functions() -> None:
    assert scientific_label_text(r"$\mathrm{km\,s^{-1}}$") == "km s⁻¹"
    assert scientific_label_text(r"$\log_{10}(A_{S1})$") == "log₁₀(Aₛ₁)"
    assert scientific_label_text(r"$\theta$ ($^\circ$)") == "θ (°)"
    assert scientific_label_text(r"$\psi_{S1}$") == "ψₛ₁"
    assert scientific_label_text(r"$K^{\prime}$") == "K′"
    assert scientific_label_text(r"$\AA^3$") == "Å³"
    assert scientific_label_text(r"Isothermal $C^T$") == "Isothermal Cᵀ"
    assert scientific_label_text(r"$\%$") == "%"


def test_quantity_unit_labels_use_parentheses_without_rewriting_ratios() -> None:
    assert quantity_unit_label("E / GPa") == "E (GPa)"
    assert quantity_unit_label("E", "GPa") == "E (GPa)"
    assert quantity_unit_label("E [GPa]") == "E (GPa)"
    assert quantity_unit_label("E (GPa)", "GPa") == "E (GPa)"
    assert quantity_unit_label(r"$V_P$ / km s$^{-1}$") == r"$V_P$ (km s$^{-1}$)"
    assert quantity_unit_label(r"$C_P$ / $C_V$") == r"$C_P$ / $C_V$"


def test_generic_tensor_indices_use_conventional_lowercase_notation() -> None:
    assert scientific_label_text("C_IJ") == "Cᵢⱼ"
    assert scientific_label_text("C_iJ") == "Cᵢⱼ"
    assert scientific_label_text(r"\Delta C_{IJ}/C_{IJ,ref}") == "Δ Cᵢⱼ/Cᵢⱼ,ref"
    assert scientific_math_label(r"Elastic stiffness $C_{IJ}$ (GPa)") == (
        r"Elastic stiffness $C_{ij}$ (GPa)"
    )
    assert scientific_math_label(r"$C^{T}_{IJ}$ and $C^S_{IJ}$") == (
        r"$C^{T}_{ij}$ and $C^{S}_{ij}$"
    )


def test_equivalent_angstrom_units_are_not_duplicated() -> None:
    assert quantity_unit_label(r"Equilibrium volume (Å$^3$)", "angstrom^3") == (
        "Equilibrium volume (Å³)"
    )
    assert quantity_unit_label("Volume", "A^3") == "Volume (Å³)"
