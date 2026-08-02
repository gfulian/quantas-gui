"""Declarative SEISMIC form and pure value coercion helpers."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

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
from quantas_gui.workflows.common import (
    RotationRequest,
    format_stiffness,
    parse_stiffness_text,
)
from quantas_gui.workflows.seismic.request import (
    HemisphereRequest,
    SamplingLevelRequest,
    SeismicRequest,
)

FORM_KEY = "seismic"
_INPUT_MODES = frozenset({"manual", "quantas", "crystal", "vasp"})
_HEMISPHERES = frozenset({"upper", "lower", "full"})
_LEVELS = frozenset({"phase", "group", "enhancement"})
_ROTATION_KINDS = frozenset({"xyz", "matrix"})

_DEFAULT_STIFFNESS = """100.0  10.0  10.0   0.0   0.0   0.0
 10.0 100.0  10.0   0.0   0.0   0.0
 10.0  10.0 100.0   0.0   0.0   0.0
  0.0   0.0   0.0  45.0   0.0   0.0
  0.0   0.0   0.0   0.0  45.0   0.0
  0.0   0.0   0.0   0.0   0.0  45.0"""


def seismic_form() -> FormSchema:
    """Return the complete user-facing SEISMIC workflow schema."""
    rotation_enabled = Condition("rotation_enabled", ConditionOperator.TRUTHY)
    xyz_rotation = Condition("rotation_kind", ConditionOperator.EQUALS, "xyz")
    matrix_rotation = Condition("rotation_kind", ConditionOperator.EQUALS, "matrix")

    return FormSchema(
        key=FORM_KEY,
        title="SEISMIC calculation",
        description=(
            "Enter a 6 × 6 elastic stiffness tensor in Voigt notation and the material "
            "density. Quantas validates the physical medium and samples the selected "
            "Christoffel-wave fields into a native HDF5 result."
        ),
        submit_label="Run SEISMIC",
        reset_label="Clear form",
        sections=(
            FormSection(
                key="input",
                title="Input",
                description=(
                    "Use a Quantas input, import a CRYSTAL or VASP output, or paste the "
                    "stiffness tensor and density directly. Imported values remain editable."
                ),
                fields=(
                    ChoiceField(
                        key="input_mode",
                        label="Input source",
                        kind=FieldKind.RADIO,
                        default="manual",
                        choices=(
                            Choice("manual", "Paste tensor and density"),
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
                            "The file is parsed server-side through quantas.api.seismic. "
                            "CRYSTAL and VASP outputs populate stiffness and density."
                        ),
                        accept=(),
                        multiple=False,
                        width="full",
                        visible_when=(
                            Condition("input_mode", ConditionOperator.NOT_EQUALS, "manual"),
                        ),
                    ),
                    TextField(
                        key="jobname",
                        label="Job name",
                        default="SEISMIC calculation",
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
                            "Paste a full 6 × 6 Voigt matrix, a compact upper or lower "
                            "triangle, or a zero-padded triangular 6 × 6 matrix. Complete "
                            "asymmetric matrices are not silently modified."
                        ),
                        width="full",
                    ),
                    NumericField(
                        key="density",
                        label="Density",
                        default=3000.0,
                        required=True,
                        unit="kg m⁻³",
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0, minimum_open=True, precision=10),
                        description=(
                            "Finite positive material density used by the Christoffel solver."
                        ),
                        width="half",
                    ),
                ),
            ),
            FormSection(
                key="sampling",
                title="Sampling and calculated fields",
                description=(
                    "These settings determine the scientific data calculated and stored. "
                    "Plot rendering is handled by the Result Explorer."
                ),
                fields=(
                    NumericField(
                        key="ntheta",
                        label="Polar angular points",
                        kind=FieldKind.INTEGER,
                        default=91,
                        bounds=NumericBounds(minimum=2, maximum=10000, step=1),
                        description="Number of polar samples.",
                    ),
                    NumericField(
                        key="nphi",
                        label="Azimuthal angular points",
                        kind=FieldKind.INTEGER,
                        default=181,
                        bounds=NumericBounds(minimum=3, maximum=20000, step=1),
                        description="The azimuthal seam is not duplicated.",
                    ),
                    ChoiceField(
                        key="hemisphere",
                        label="Sampling domain",
                        kind=FieldKind.RADIO,
                        default="upper",
                        choices=(
                            Choice("upper", "Upper hemisphere"),
                            Choice("lower", "Lower hemisphere"),
                            Choice("full", "Full sphere"),
                        ),
                        inline=True,
                        width="full",
                    ),
                    ChoiceField(
                        key="level",
                        label="Highest calculated level",
                        kind=FieldKind.RADIO,
                        default="enhancement",
                        choices=(
                            Choice("phase", "Phase velocity", "Phase speeds and polarizations."),
                            Choice(
                                "group",
                                "Group velocity",
                                "Add ray directions and group speeds.",
                            ),
                            Choice(
                                "enhancement",
                                "Enhancement",
                                "Add focusing, caustic and enhancement diagnostics.",
                            ),
                        ),
                        inline=False,
                        width="full",
                    ),
                    BooleanField(
                        key="track_polarization_axes",
                        label="Polarization continuity",
                        default=True,
                        true_label="Track shear-wave polarization axes across the sampled grid",
                        description=(
                            "Disable only when deterministic continuity of axial polarization "
                            "directions is not required."
                        ),
                        width="full",
                    ),
                ),
            ),
            FormSection(
                key="numerical",
                title="Advanced numerical tolerances",
                description=(
                    "Defaults match the public Quantas SEISMIC contract. Change them only for "
                    "a documented numerical reason."
                ),
                presentation="details",
                collapsed=True,
                advanced=True,
                fields=(
                    NumericField(
                        key="eigenvalue_rtol",
                        label="Eigenvalue relative tolerance",
                        default=1.0e-10,
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0, precision=14),
                        advanced=True,
                    ),
                    NumericField(
                        key="eigenvalue_atol",
                        label="Eigenvalue absolute tolerance",
                        default=1.0e-12,
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0, precision=14),
                        advanced=True,
                    ),
                    NumericField(
                        key="degeneracy_rtol",
                        label="Degeneracy relative tolerance",
                        default=1.0e-8,
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0, precision=14),
                        advanced=True,
                    ),
                    NumericField(
                        key="degeneracy_atol",
                        label="Degeneracy absolute tolerance",
                        default=1.0e-10,
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0, precision=14),
                        advanced=True,
                    ),
                    NumericField(
                        key="pseudoinverse_rcond",
                        label="Pseudoinverse relative cutoff",
                        default=1.0e-10,
                        scientific=True,
                        bounds=NumericBounds(
                            minimum=0.0,
                            maximum=1.0,
                            maximum_open=True,
                            precision=14,
                        ),
                        advanced=True,
                    ),
                    NumericField(
                        key="caustic_rtol",
                        label="Caustic relative tolerance",
                        default=1.0e-10,
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0, precision=14),
                        advanced=True,
                    ),
                    NumericField(
                        key="caustic_atol",
                        label="Caustic absolute tolerance",
                        default=1.0e-12,
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0, precision=14),
                        advanced=True,
                    ),
                ),
            ),
            FormSection(
                key="rotation",
                title="Physical tensor transformation",
                description=(
                    "This rotates the elastic tensor or its basis before wave analysis. It is "
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

    request: SeismicRequest | None
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
    validation = validate_form(seismic_form(), values)
    issues = list(validation.issues)
    normalized = validation.values

    mode = input_mode(normalized.get("input_mode", "manual"))
    if mode != "manual" and source_filename is None:
        issues.append(
            ValidationIssue(
                "input_mode",
                "Upload the selected source file before running SEISMIC.",
                "source-required",
            )
        )

    stiffness: tuple[tuple[float, ...], ...] | None = None
    try:
        stiffness = parse_stiffness_text(str(normalized.get("stiffness_text", "")))
    except ValueError as exc:
        issues.append(ValidationIssue("stiffness_text", str(exc), "matrix-text"))

    rotation: RotationRequest | None = None
    if bool(normalized.get("rotation_enabled")):
        try:
            kind = rotation_kind(normalized.get("rotation_kind"))
            if kind == "xyz":
                raw_xyz = normalized.get("rotation_xyz", ())
                rotation = RotationRequest(
                    kind="xyz",
                    values=tuple(float(item) for item in raw_xyz),
                    description=_optional_text(normalized.get("rotation_description")),
                )
            else:
                raw_matrix = normalized.get("rotation_matrix", ())
                rotation = RotationRequest(
                    kind="matrix",
                    values=tuple(float(item) for row in raw_matrix for item in row),
                    description=_optional_text(normalized.get("rotation_description")),
                )
        except (TypeError, ValueError) as exc:
            issues.append(ValidationIssue("rotation_kind", str(exc), "rotation"))

    if issues or stiffness is None:
        return RequestValidation(request=None, issues=tuple(issues))

    ntheta = int(normalized.get("ntheta") or 91)
    nphi = int(normalized.get("nphi") or 181)
    try:
        request = SeismicRequest(
            jobname=str(normalized.get("jobname", "")),
            stiffness=stiffness,
            density=_required_float(normalized, "density"),
            source_filename=source_filename,
            ntheta=ntheta,
            nphi=nphi,
            hemisphere=hemisphere(normalized.get("hemisphere")),
            level=sampling_level(normalized.get("level")),
            batch_size=_progress_batch_size(ntheta, nphi),
            track_polarization_axes=bool(normalized.get("track_polarization_axes")),
            eigenvalue_rtol=_required_float(normalized, "eigenvalue_rtol"),
            eigenvalue_atol=_required_float(normalized, "eigenvalue_atol"),
            degeneracy_rtol=_required_float(normalized, "degeneracy_rtol"),
            degeneracy_atol=_required_float(normalized, "degeneracy_atol"),
            pseudoinverse_rcond=_required_float(normalized, "pseudoinverse_rcond"),
            caustic_rtol=_required_float(normalized, "caustic_rtol"),
            caustic_atol=_required_float(normalized, "caustic_atol"),
            rotation=rotation,
        )
    except (TypeError, ValueError) as exc:
        return RequestValidation(
            request=None,
            issues=(*issues, ValidationIssue(None, str(exc), "request")),
        )
    return RequestValidation(request=request, issues=())


def input_mode(value: object) -> Literal["manual", "quantas", "crystal", "vasp"]:
    mode = str(value)
    if mode not in _INPUT_MODES:
        raise ValueError("Choose a supported SEISMIC input source.")
    return cast(Literal["manual", "quantas", "crystal", "vasp"], mode)


def hemisphere(value: object) -> HemisphereRequest:
    selected = str(value)
    if selected not in _HEMISPHERES:
        raise ValueError("Choose upper, lower, or full sampling.")
    return cast(HemisphereRequest, selected)


def sampling_level(value: object) -> SamplingLevelRequest:
    selected = str(value)
    if selected not in _LEVELS:
        raise ValueError("Choose phase, group, or enhancement calculation level.")
    return cast(SamplingLevelRequest, selected)


def rotation_kind(value: object) -> Literal["xyz", "matrix"]:
    selected = str(value)
    if selected not in _ROTATION_KINDS:
        raise ValueError("Choose a supported rotation representation.")
    return cast(Literal["xyz", "matrix"], selected)


def _required_float(values: Mapping[str, Any], key: str) -> float:
    value = values.get(key)
    if value is None:
        raise ValueError(f"{key} is required")
    return float(value)


def _progress_batch_size(ntheta: int, nphi: int) -> int:
    points = max(1, ntheta * nphi)
    return max(128, min(4096, math.ceil(points / 20)))


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "FORM_KEY",
    "RequestValidation",
    "build_request",
    "format_stiffness",
    "hemisphere",
    "input_mode",
    "parse_stiffness_text",
    "rotation_kind",
    "sampling_level",
    "seismic_form",
]
