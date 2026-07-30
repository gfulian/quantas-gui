"""Compact mathematical formatting for native Dash selector labels.

Plotly figures use MathJax, but native dropdown option labels are plain text.
This module converts the small LaTeX subset emitted by Quantas plot titles and
property labels to readable Unicode without interpreting scientific meaning.
"""

from __future__ import annotations

import re

_SUBSCRIPT = str.maketrans(
    {
        "0": "₀",
        "1": "₁",
        "2": "₂",
        "3": "₃",
        "4": "₄",
        "5": "₅",
        "6": "₆",
        "7": "₇",
        "8": "₈",
        "9": "₉",
        "+": "₊",
        "-": "₋",
        "(": "₍",
        ")": "₎",
        "a": "ₐ",
        "e": "ₑ",
        "h": "ₕ",
        "i": "ᵢ",
        "j": "ⱼ",
        "k": "ₖ",
        "l": "ₗ",
        "m": "ₘ",
        "n": "ₙ",
        "o": "ₒ",
        "p": "ₚ",
        "r": "ᵣ",
        "s": "ₛ",
        "t": "ₜ",
        "u": "ᵤ",
        "v": "ᵥ",
        "x": "ₓ",
        "b": "ʙ",
        "c": "ᴄ",
        "d": "ᴅ",
        "f": "ꜰ",
        "g": "ɢ",
        "q": "Q",
        "w": "ᴡ",
        "y": "ʏ",
        "z": "ᴢ",
        "E": "ₑ",
        "G": "ɢ",
        "P": "ₚ",
        "Z": "ᴢ",
        "S": "ₛ",
        "T": "ₜ",
        "V": "ᵥ",
        "I": "ᵢ",
        "J": "ⱼ",
    }
)
_SUPERSCRIPT = str.maketrans(
    {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
        "+": "⁺",
        "-": "⁻",
        "(": "⁽",
        ")": "⁾",
        "a": "ᵃ",
        "b": "ᵇ",
        "c": "ᶜ",
        "d": "ᵈ",
        "e": "ᵉ",
        "f": "ᶠ",
        "g": "ᵍ",
        "h": "ʰ",
        "i": "ⁱ",
        "j": "ʲ",
        "k": "ᵏ",
        "l": "ˡ",
        "m": "ᵐ",
        "n": "ⁿ",
        "o": "ᵒ",
        "p": "ᵖ",
        "r": "ʳ",
        "s": "ˢ",
        "t": "ᵗ",
        "u": "ᵘ",
        "v": "ᵛ",
        "w": "ʷ",
        "x": "ˣ",
        "y": "ʸ",
        "z": "ᶻ",
        "A": "ᴬ",
        "B": "ᴮ",
        "D": "ᴰ",
        "E": "ᴱ",
        "G": "ᴳ",
        "H": "ᴴ",
        "I": "ᴵ",
        "J": "ᴶ",
        "K": "ᴷ",
        "L": "ᴸ",
        "M": "ᴹ",
        "N": "ᴺ",
        "O": "ᴼ",
        "P": "ᴾ",
        "R": "ᴿ",
        "S": "ˢ",
        "T": "ᵀ",
        "U": "ᵁ",
        "V": "ⱽ",
        "W": "ᵂ",
    }
)
_COMMANDS = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\Delta": "Δ",
    r"\epsilon": "ε",
    r"\eta": "η",
    r"\theta": "θ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "ν",
    r"\pi": "π",
    r"\rho": "ρ",
    r"\sigma": "σ",
    r"\tau": "τ",
    r"\phi": "φ",
    r"\psi": "ψ",
    r"\kappa": "κ",
    r"\xi": "ξ",
    r"\zeta": "ζ",
    r"\chi": "χ",
    r"\omega": "ω",
    r"\Gamma": "Γ",
    r"\Omega": "Ω",
    r"\pm": "±",
    r"\times": "×",
    r"\cdot": "·",
    r"\circ": "°",
    r"\prime": "′",
    r"\AA": "Å",
    r"\%": "%",
    r"\log": "log",
    r"\left": "",
    r"\right": "",
}
_SCRIPT_PATTERN = re.compile(r"([_^])(?:\{([^{}]+)\}|([A-Za-z0-9+\-()]))")
_PLAIN_NUMERIC_SCRIPT_PATTERN = re.compile(r"([_^])([+\-]?\d+)")
_TEXT_COMMAND_PATTERN = re.compile(r"\\(?:mathrm|text|mathit|mathbf)\{([^{}]+)\}")
_BRACKET_UNIT_PATTERN = re.compile(r"^(?P<quantity>.+?)\s*\[(?P<unit>[^\[\]]+)\]\s*$")
_SLASH_UNIT_PATTERN = re.compile(r"^(?P<quantity>.+?)\s+/\s+(?P<unit>\S.*)$")
_KNOWN_UNIT_PATTERN = re.compile(
    r"^(?:"
    r"(?:[kMGT]?Pa)|"
    r"K|"
    r"(?:[kMGT]?Hz)|"
    r"(?:cm|mm|m|km|Å|A|bohr)(?:\b|[\s·*/^⁻⁰¹²³⁴⁵⁶⁷⁸⁹-].*)|"
    r"(?:mg|g|kg)(?:\b|[\s·*/^⁻⁰¹²³⁴⁵⁶⁷⁸⁹-].*)|"
    r"(?:J|kJ|MJ|Ha|eV|meV)(?:\b|[\s·*/^⁻⁰¹²³⁴⁵⁶⁷⁸⁹-].*)|"
    r"(?:mol|rad|deg|°|%|1)(?:\b|[\s·*/^⁻⁰¹²³⁴⁵⁶⁷⁸⁹-].*)"
    r")$",
    re.IGNORECASE,
)

_GENERIC_TENSOR_REPLACEMENTS = (
    (r"C^{T}_{IJ}", r"C^{T}_{ij}"),
    (r"C^{S}_{IJ}", r"C^{S}_{ij}"),
    (r"C^{T}_IJ", r"C^{T}_{ij}"),
    (r"C^{S}_IJ", r"C^{S}_{ij}"),
    (r"C^T_{IJ}", r"C^{T}_{ij}"),
    (r"C^S_{IJ}", r"C^{S}_{ij}"),
    (r"C^T_IJ", r"C^{T}_{ij}"),
    (r"C^S_IJ", r"C^{S}_{ij}"),
    (r"C_{IJ,ref}", r"C_{ij,\mathrm{ref}}"),
    (r"C_{iJ,ref}", r"C_{ij,\mathrm{ref}}"),
    (r"C_{Ij,ref}", r"C_{ij,\mathrm{ref}}"),
    (r"C_IJ,ref", r"C_{ij,\mathrm{ref}}"),
    (r"C_iJ,ref", r"C_{ij,\mathrm{ref}}"),
    (r"C_Ij,ref", r"C_{ij,\mathrm{ref}}"),
    (r"C_{IJ}", r"C_{ij}"),
    (r"C_{iJ}", r"C_{ij}"),
    (r"C_{Ij}", r"C_{ij}"),
    (r"C_IJ", r"C_{ij}"),
    (r"C_iJ", r"C_{ij}"),
    (r"C_Ij", r"C_{ij}"),
    (r"C_ij", r"C_{ij}"),
)

_UNIT_ALIASES = {
    "angstrom": "Å",
    "angstroms": "Å",
    "a^3": "Å³",
    "a3": "Å³",
    "a³": "Å³",
    "angstrom^3": "Å³",
    "angstrom3": "Å³",
}


def scientific_label_text(value: object) -> str:
    """Return a readable native-control label for a Quantas mathematical string.

    The conversion is deliberately presentation-only. Plot axes and colorbars
    continue to receive the original public Quantas labels for MathJax.
    """
    text = scientific_math_label(value)
    text = text.replace(r"C_{ij,\mathrm{ref}}", "Cᵢⱼ,ref")
    text = text.replace(r"C_{ij,ref}", "Cᵢⱼ,ref")

    def replace_script(match: re.Match[str]) -> str:
        payload = match.group(2) or (match.group(3) if match.lastindex == 3 else "") or ""
        table = _SUBSCRIPT if match.group(1) == "_" else _SUPERSCRIPT
        converted = payload.translate(table)
        return converted if converted != payload else payload

    previous = None
    while previous != text:
        previous = text
        for command, replacement in _COMMANDS.items():
            text = text.replace(command, replacement)
        text = _PLAIN_NUMERIC_SCRIPT_PATTERN.sub(replace_script, text)
        text = _SCRIPT_PATTERN.sub(replace_script, text)
        text = _TEXT_COMMAND_PATTERN.sub(r"{\1}", text)

    text = (
        text.replace("$", "")
        .replace("{", "")
        .replace("}", "")
        .replace(r"\,", " ")
        .replace(r"\;", " ")
        .replace(r"\:", " ")
        .replace(r"\ ", " ")
        .replace("^-", "⁻")
        .replace("^°", "°")
    )
    return " ".join(text.split())


def scientific_math_label(value: object) -> str:
    """Return a Plotly/MathJax label with canonical generic tensor indices.

    Quantas remains authoritative for the represented quantity. This helper
    only normalizes presentation spellings such as ``C_IJ`` to the conventional
    generic tensor notation ``C_{ij}``. Specific components such as ``C_11``
    or ``C_{11}`` are left unchanged.
    """
    text = str(value)
    for source, replacement in _GENERIC_TENSOR_REPLACEMENTS:
        text = text.replace(source, replacement)
    return text


def display_unit(value: object) -> str:
    """Return one compact display spelling for a public physical unit."""
    text = scientific_label_text(value).strip()
    normalized = text.casefold().replace(" ", "")
    return _UNIT_ALIASES.get(normalized, text.replace("angstrom", "Å"))


def quantity_unit_label(label: object, unit: object | None = None) -> str:
    """Return a presentation label in the canonical ``Quantity (unit)`` form.

    Quantas remains authoritative for the quantity and unit strings. This helper
    only normalizes common frontend spellings such as ``E / GPa`` and
    ``E [GPa]``. A slash is rewritten only when its right-hand side resembles a
    physical unit, so scientific ratios such as ``C_P / C_V`` remain unchanged.
    """
    label_text = " ".join(scientific_math_label(label).strip().split())
    unit_text = "" if unit is None else display_unit(unit)
    label_text = _normalize_trailing_unit(label_text)

    bracket_match = _BRACKET_UNIT_PATTERN.match(label_text)
    if bracket_match is not None:
        embedded_unit = bracket_match.group("unit").strip()
        if not unit_text:
            unit_text = embedded_unit
        if _unit_signature(embedded_unit) == _unit_signature(unit_text):
            label_text = bracket_match.group("quantity").strip()

    slash_match = _SLASH_UNIT_PATTERN.match(label_text)
    if slash_match is not None:
        embedded_unit = slash_match.group("unit").strip()
        signatures_match = bool(unit_text) and (
            _unit_signature(embedded_unit) == _unit_signature(unit_text)
        )
        if signatures_match:
            label_text = slash_match.group("quantity").strip()
        elif not unit_text and _looks_like_unit(embedded_unit):
            label_text = slash_match.group("quantity").strip()
            unit_text = embedded_unit

    if not unit_text:
        return label_text
    if _has_parenthesized_unit(label_text, unit_text):
        return label_text
    return f"{label_text} ({unit_text})"


def _normalize_trailing_unit(label: str) -> str:
    """Normalize a physical unit already embedded in trailing parentheses."""
    match = re.search(r"\(([^()]*)\)\s*$", label)
    if match is None or not _looks_like_unit(match.group(1)):
        return label
    normalized = display_unit(match.group(1))
    return f"{label[: match.start()].rstrip()} ({normalized})"


def _looks_like_unit(value: str) -> bool:
    """Return whether a slash suffix resembles a physical unit expression."""
    plain = scientific_label_text(value).strip()
    return _KNOWN_UNIT_PATTERN.fullmatch(plain) is not None


def _has_parenthesized_unit(label: str, unit: str) -> bool:
    """Return whether ``label`` already ends with the supplied unit in brackets."""
    match = re.search(r"\(([^()]*)\)\s*$", label)
    if match is None:
        return False
    embedded = match.group(1)
    return _looks_like_unit(embedded) or (_unit_signature(embedded) == _unit_signature(unit))


def _unit_signature(value: str) -> str:
    """Return a comparison-only signature for a unit string."""
    return re.sub(r"[^a-z0-9%°å]+", "", display_unit(value).casefold())


__all__ = [
    "display_unit",
    "quantity_unit_label",
    "scientific_label_text",
    "scientific_math_label",
]
