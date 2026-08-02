"""Declarative Elasticity form and pure value coercion helpers."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from quantas_gui.forms.schema import (
    BooleanField,
    Choice,
    ChoiceField,
    Condition,
    ConditionOperator,
    FieldKind,
    FileUploadField,
    FormSchema,
    FormSection,
    MatrixField,
    NumericBounds,
    NumericField,
    TextField,
    VectorField,
)
from quantas_gui.forms.validation import ValidationIssue, validate_form
from quantas_gui.workflows.common.stiffness import format_stiffness, parse_stiffness_text
from quantas_gui.workflows.elasticity.request import ElasticityRequest, RotationRequest

FORM_KEY = "elasticity"
_INPUT_MODES = frozenset({"manual", "quantas", "crystal", "vasp"})
_ROTATION_KINDS = frozenset({"xyz", "matrix"})
_PROPERTY_KEYS = ("young", "compressibility", "shear", "poisson")
_DEFAULT_STIFFNESS = """100.0  10.0  10.0   0.0   0.0   0.0
 10.0 100.0  10.0   0.0   0.0   0.0
 10.0  10.0 100.0   0.0   0.0   0.0
  0.0   0.0   0.0  45.0   0.0   0.0
  0.0   0.0   0.0   0.0  45.0   0.0
  0.0   0.0   0.0   0.0   0.0  45.0"""


def elasticity_form() -> FormSchema:
    """Return the complete user-facing Elasticity workflow schema."""
    calculate_2d = Condition("calculate_2d", ConditionOperator.TRUTHY)
    calculate_3d = Condition("calculate_3d", ConditionOperator.TRUTHY)
    rotation_enabled = Condition("rotation_enabled", ConditionOperator.TRUTHY)
    xyz_rotation = Condition("rotation_kind", ConditionOperator.EQUALS, "xyz")
    matrix_rotation = Condition("rotation_kind", ConditionOperator.EQUALS, "matrix")

    return FormSchema(
        key=FORM_KEY,
        title="Elasticity calculation",
        description=(
            "Enter a 6 × 6 elastic stiffness tensor in Voigt notation. Quantas "
            "performs the scientific validation, infers crystal symmetry, and writes "
            "the native HDF5 result."
        ),
        submit_label="Run Elasticity",
        reset_label="Clear form",
        sections=(
            FormSection(
                key="input",
                title="Input",
                description=(
                    "Use a Quantas input, import a CRYSTAL or VASP output, or paste "
                    "the stiffness tensor directly. Imported data populate the editable fields."
                ),
                fields=(
                    ChoiceField(
                        key="input_mode",
                        label="Input source",
                        kind=FieldKind.RADIO,
                        default="manual",
                        choices=(
                            Choice("manual", "Paste matrix"),
                            Choice("quantas", "Quantas input"),
                            Choice("crystal", "CRYSTAL output"),
                            Choice("vasp", "VASP OUTCAR"),
                        ),
                        inline=True,
                        width="full",
                    ),
                    FileUploadField(
                        key="source_upload",
                        label="Source file",
                        description=(
                            "The upload is parsed server-side through the public Quantas API. "
                            "External outputs populate the tensor only."
                        ),
                        accept=(),
                        multiple=False,
                        width="full",
                        visible_when=(
                            Condition(
                                "input_mode",
                                ConditionOperator.NOT_EQUALS,
                                "manual",
                            ),
                        ),
                    ),
                    TextField(
                        key="jobname",
                        label="Job name",
                        default="Elasticity calculation",
                        required=True,
                        max_length=240,
                        placeholder="Short description of the calculation",
                        width="full",
                    ),
                    TextField(
                        key="stiffness_text",
                        label="Elastic stiffness matrix",
                        kind=FieldKind.TEXTAREA,
                        multiline=True,
                        rows=8,
                        default=_DEFAULT_STIFFNESS,
                        required=True,
                        unit="GPa",
                        placeholder="Full 6 × 6 matrix, or upper/lower triangular rows",
                        description=(
                            "Paste a full 6 × 6 Voigt matrix, a compact upper triangle "
                            "with 6, 5, …, 1 values per row, or a compact lower triangle "
                            "with 1, 2, …, 6 values per row. Zero-padded triangular 6 × 6 "
                            "matrices are also expanded. Spaces, tabs, commas, semicolons, "
                            "and scientific notation are accepted."
                        ),
                        width="full",
                    ),
                ),
            ),
            FormSection(
                key="directional",
                title="Directional data",
                description=(
                    "These options calculate and store scientific directional samples. "
                    "Plot rendering is handled later by the Result Explorer."
                ),
                fields=(
                    BooleanField(
                        key="calculate_2d",
                        label="Principal-plane data",
                        default=False,
                        true_label="Calculate and store 2D directional data",
                        width="full",
                    ),
                    NumericField(
                        key="ntheta_2d",
                        label="2D angular points",
                        kind=FieldKind.INTEGER,
                        default=361,
                        bounds=NumericBounds(minimum=2, maximum=100000, step=1),
                        description="Points sampled on each principal plane.",
                        visible_when=(calculate_2d,),
                        enabled_when=(calculate_2d,),
                    ),
                    BooleanField(
                        key="calculate_3d",
                        label="Three-dimensional data",
                        default=False,
                        true_label="Calculate and store 3D directional surfaces",
                        width="full",
                    ),
                    NumericField(
                        key="ntheta_3d",
                        label="Polar angular points",
                        kind=FieldKind.INTEGER,
                        default=61,
                        bounds=NumericBounds(minimum=2, maximum=10000, step=1),
                        visible_when=(calculate_3d,),
                        enabled_when=(calculate_3d,),
                    ),
                    NumericField(
                        key="nphi_3d",
                        label="Azimuthal angular points",
                        kind=FieldKind.INTEGER,
                        default=121,
                        bounds=NumericBounds(minimum=3, maximum=20000, step=1),
                        description="A value near 2 × nθ − 1 gives balanced sampling.",
                        visible_when=(calculate_3d,),
                        enabled_when=(calculate_3d,),
                    ),
                    ChoiceField(
                        key="properties_3d",
                        label="Stored 3D properties",
                        kind=FieldKind.CHECKLIST,
                        default=_PROPERTY_KEYS,
                        choices=(
                            Choice("young", "Young modulus"),
                            Choice("compressibility", "Linear compressibility"),
                            Choice("shear", "Shear modulus"),
                            Choice("poisson", "Poisson ratio"),
                        ),
                        inline=False,
                        width="full",
                        visible_when=(calculate_3d,),
                        enabled_when=(calculate_3d,),
                    ),
                ),
            ),
            FormSection(
                key="rotation",
                title="Physical tensor transformation",
                description=(
                    "This rotates the elastic tensor or its basis before analysis. It is "
                    "scientifically different from rotating the Plotly camera."
                ),
                presentation="details",
                collapsed=True,
                advanced=True,
                fields=(
                    BooleanField(
                        key="rotation_enabled",
                        label="Apply tensor rotation",
                        default=False,
                        true_label="Transform the physical elastic tensor",
                        width="full",
                    ),
                    ChoiceField(
                        key="rotation_kind",
                        label="Rotation representation",
                        kind=FieldKind.RADIO,
                        default="xyz",
                        choices=(
                            Choice("xyz", "XYZ angles"),
                            Choice("matrix", "3 × 3 matrix"),
                        ),
                        inline=True,
                        visible_when=(rotation_enabled,),
                        enabled_when=(rotation_enabled,),
                        width="full",
                    ),
                    VectorField(
                        key="rotation_xyz",
                        label="XYZ rotation angles",
                        default=(0.0, 0.0, 0.0),
                        labels=("X", "Y", "Z"),
                        length=3,
                        bounds=NumericBounds(precision=8),
                        unit="degrees",
                        visible_when=(rotation_enabled, xyz_rotation),
                        enabled_when=(rotation_enabled, xyz_rotation),
                        width="full",
                    ),
                    MatrixField(
                        key="rotation_matrix",
                        label="Rotation matrix",
                        rows=3,
                        columns=3,
                        default=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                        bounds=NumericBounds(precision=10),
                        visible_when=(rotation_enabled, matrix_rotation),
                        enabled_when=(rotation_enabled, matrix_rotation),
                        width="full",
                    ),
                    TextField(
                        key="rotation_description",
                        label="Transformation note",
                        placeholder="Optional provenance or frame description",
                        max_length=240,
                        visible_when=(rotation_enabled,),
                        enabled_when=(rotation_enabled,),
                        width="full",
                    ),
                ),
            ),
        ),
    )


@dataclass(frozen=True, slots=True)
class RequestValidation:
    """Result of GUI structural validation and request construction."""

    request: ElasticityRequest | None
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return self.request is not None and not self.issues

    def for_field(self, field: str) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.field == field)


def build_request(
    values: Mapping[str, Any],
    *,
    source_filename: str | None = None,
) -> RequestValidation:
    """Validate form values and construct one serializable worker request."""
    schema = elasticity_form()
    validation = validate_form(schema, values)
    issues = list(validation.issues)
    normalized = validation.values

    mode = input_mode(normalized.get("input_mode", "manual"))
    if mode != "manual" and source_filename is None:
        issues.append(
            ValidationIssue(
                "input_mode",
                "Upload the selected source file before running Elasticity.",
                "source-required",
            )
        )

    stiffness: tuple[tuple[float, ...], ...] | None = None
    try:
        stiffness = parse_stiffness_text(str(normalized.get("stiffness_text", "")))
    except ValueError as exc:
        issues.append(ValidationIssue("stiffness_text", str(exc), "matrix-text"))

    raw_properties = normalized.get("properties_3d") or _PROPERTY_KEYS
    properties = tuple(str(item) for item in raw_properties)
    if bool(normalized.get("calculate_3d")) and not properties:
        issues.append(
            ValidationIssue(
                "properties_3d",
                "Select at least one 3D elasticity property.",
                "required-selection",
            )
        )

    rotation: RotationRequest | None = None
    if bool(normalized.get("rotation_enabled")):
        kind = str(normalized.get("rotation_kind", ""))
        try:
            if kind == "xyz":
                raw_xyz = normalized.get("rotation_xyz", ())
                rotation = RotationRequest(
                    kind="xyz",
                    values=tuple(float(item) for item in raw_xyz),
                    description=_optional_text(normalized.get("rotation_description")),
                )
            elif kind == "matrix":
                raw_matrix = normalized.get("rotation_matrix", ())
                flat = tuple(float(item) for row in raw_matrix for item in row)
                rotation = RotationRequest(
                    kind="matrix",
                    values=flat,
                    description=_optional_text(normalized.get("rotation_description")),
                )
            else:
                raise ValueError("Choose a supported tensor rotation representation.")
        except (TypeError, ValueError) as exc:
            issues.append(ValidationIssue("rotation_kind", str(exc), "rotation"))

    if issues or stiffness is None:
        return RequestValidation(request=None, issues=tuple(issues))

    calculate_3d = bool(normalized.get("calculate_3d"))
    ntheta_3d = int(normalized.get("ntheta_3d") or 61)
    nphi_3d = int(normalized.get("nphi_3d") or 121)
    try:
        request = ElasticityRequest(
            jobname=str(normalized.get("jobname", "")),
            stiffness=stiffness,
            source_filename=source_filename,
            calculate_2d=bool(normalized.get("calculate_2d")),
            ntheta_2d=int(normalized.get("ntheta_2d") or 361),
            calculate_3d=calculate_3d,
            ntheta_3d=ntheta_3d,
            nphi_3d=nphi_3d,
            properties_3d=properties,
            batch_size=(_progress_batch_size(ntheta_3d, nphi_3d) if calculate_3d else 65536),
            rotation=rotation,
        )
    except (TypeError, ValueError) as exc:
        return RequestValidation(
            request=None,
            issues=(*issues, ValidationIssue(None, str(exc), "request")),
        )
    return RequestValidation(request=request, issues=())


def input_mode(value: object) -> Literal["manual", "quantas", "crystal", "vasp"]:
    """Return one validated input-mode value."""
    mode = str(value)
    if mode not in _INPUT_MODES:
        raise ValueError("Choose a supported Elasticity input source.")
    return mode  # type: ignore[return-value]


def rotation_kind(value: object) -> Literal["xyz", "matrix"]:
    """Return one validated rotation representation."""
    kind = str(value)
    if kind not in _ROTATION_KINDS:
        raise ValueError("Choose a supported rotation representation.")
    return kind  # type: ignore[return-value]


def _progress_batch_size(ntheta: int, nphi: int) -> int:
    """Choose bounded process batches that yield useful progress events."""
    points = max(1, ntheta * nphi)
    return max(256, min(65536, math.ceil(points / 20)))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "FORM_KEY",
    "RequestValidation",
    "build_request",
    "elasticity_form",
    "format_stiffness",
    "input_mode",
    "parse_stiffness_text",
    "rotation_kind",
]
