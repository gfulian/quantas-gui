"""Representative form schemas derived from the current Quantas option space."""

from __future__ import annotations

from .schema import (
    BooleanField,
    Choice,
    ChoiceField,
    Condition,
    ConditionOperator,
    FieldKind,
    FileUploadField,
    FormRule,
    FormRuleKind,
    FormSchema,
    FormSection,
    KeyValueField,
    MatrixField,
    NumericBounds,
    NumericField,
    RangeTripletField,
    SliderField,
    TagsField,
    TextField,
    VectorField,
)


def ui_kit_form() -> FormSchema:
    """Return a form exercising the reusable control families.

    The example values mirror real Quantas concepts without acting as an
    executable scientific workflow.
    """
    stiffness = (
        (165.0, 64.0, 64.0, 0.0, 0.0, 0.0),
        (64.0, 165.0, 64.0, 0.0, 0.0, 0.0),
        (64.0, 64.0, 165.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 80.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 80.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 80.0),
    )
    return FormSchema(
        key="ui-kit",
        title="Reusable scientific controls",
        description=(
            "A developer-facing gallery of the controls used to compose Quantas "
            "workflows. Values are illustrative and are not submitted to Quantas."
        ),
        submit_label="Validate example",
        sections=(
            FormSection(
                key="input",
                title="Input and metadata",
                description="Files, short labels, and free-form scientific notes.",
                fields=(
                    FileUploadField(
                        key="input_file",
                        label="Input file",
                        description="Browser upload replaces an unsafe server-path text field.",
                        accept=(".yaml", ".yml", ".txt", ".h5", ".hdf5"),
                        width="full",
                    ),
                    TextField(
                        key="jobname",
                        label="Job name",
                        default="Calcite elasticity",
                        placeholder="Short calculation title",
                        required=True,
                    ),
                    TextField(
                        key="notes",
                        label="Notes",
                        kind=FieldKind.TEXTAREA,
                        multiline=True,
                        rows=4,
                        placeholder="Optional assumptions, provenance, or comments…",
                        width="full",
                    ),
                ),
            ),
            FormSection(
                key="selection",
                title="Scientific selection",
                description="Compact single and multiple choices plus explicit toggles.",
                fields=(
                    ChoiceField(
                        key="hemisphere",
                        label="Hemisphere",
                        kind=FieldKind.RADIO,
                        default="upper",
                        inline=True,
                        choices=(
                            Choice("upper", "Upper"),
                            Choice("lower", "Lower"),
                            Choice("full", "Full"),
                        ),
                    ),
                    ChoiceField(
                        key="verbosity",
                        label="Verbosity",
                        kind=FieldKind.SELECT,
                        default="extended",
                        choices=(
                            Choice("standard", "Standard"),
                            Choice("extended", "Extended"),
                            Choice("debug", "Debug"),
                        ),
                    ),
                    ChoiceField(
                        key="properties",
                        label="Elastic properties",
                        kind=FieldKind.CHECKLIST,
                        default=("young", "compressibility"),
                        inline=True,
                        width="full",
                        choices=(
                            Choice("young", "Young modulus"),
                            Choice("compressibility", "Compressibility"),
                            Choice("shear", "Shear modulus"),
                            Choice("poisson", "Poisson ratio"),
                        ),
                    ),
                    ChoiceField(
                        key="plot_types",
                        label="Plot families",
                        kind=FieldKind.MULTI_SELECT,
                        default=("fit", "residuals"),
                        width="full",
                        choices=tuple(
                            Choice(value, label)
                            for value, label in (
                                ("fit", "Fit"),
                                ("residuals", "Residuals"),
                                ("normalized-pressure", "Normalized pressure"),
                                ("coverage", "Coverage"),
                                ("isotherms", "Isotherms"),
                                ("isobars", "Isobars"),
                            )
                        ),
                    ),
                    BooleanField(
                        key="calculate_3d",
                        label="Three-dimensional sampling",
                        default=True,
                        true_label="Calculate and persist 3D surfaces",
                        description="A semantic switch is clearer than a bare flag.",
                    ),
                    BooleanField(
                        key="overwrite",
                        label="Replace existing result",
                        default=False,
                        presentation="checkbox",
                        true_label="I understand that the existing output will be replaced",
                        description="Destructive acknowledgements use a checkbox, not a switch.",
                    ),
                ),
            ),
            FormSection(
                key="domain",
                title="Domain and numerical values",
                description=(
                    "Exact state coordinates use number fields and start–stop–step composites; "
                    "sliders are reserved for bounded exploratory or presentation values."
                ),
                fields=(
                    NumericField(
                        key="ntheta",
                        label="Polar samples",
                        kind=FieldKind.INTEGER,
                        default=91,
                        bounds=NumericBounds(minimum=2, step=1),
                    ),
                    NumericField(
                        key="eigenvalue_rtol",
                        label="Eigenvalue relative tolerance",
                        default=1.0e-10,
                        scientific=True,
                        bounds=NumericBounds(minimum=0.0),
                        advanced=True,
                    ),
                    RangeTripletField(
                        key="temperature",
                        label="Temperature domain",
                        default=(298.15, 1200.0, 50.0),
                        unit="K",
                        width="full",
                    ),
                    VectorField(
                        key="rotate_xyz",
                        label="Euler rotation",
                        default=(0.0, 0.0, 0.0),
                        labels=("X", "Y", "Z"),
                        length=3,
                        unit="deg",
                        width="full",
                    ),
                    SliderField(
                        key="confidence",
                        label="Confidence level",
                        default=0.95,
                        bounds=NumericBounds(
                            minimum=0.50,
                            maximum=0.999,
                            step=0.001,
                            precision=3,
                        ),
                        marks=((0.50, "50%"), (0.95, "95%"), (0.999, "99.9%")),
                        description=(
                            "A bounded statistical presentation control is slider-friendly."
                        ),
                        width="full",
                    ),
                    SliderField(
                        key="display_window",
                        label="Displayed data window",
                        kind=FieldKind.RANGE_SLIDER,
                        default=(10.0, 90.0),
                        bounds=NumericBounds(minimum=0.0, maximum=100.0, step=1.0),
                        marks=((0.0, "0"), (50.0, "50"), (100.0, "100")),
                        unit="%",
                        width="full",
                    ),
                ),
            ),
            FormSection(
                key="structured",
                title="Structured numerical input",
                description=(
                    "Matrices and repeatable records use editable grids with raw numeric values."
                ),
                fields=(
                    MatrixField(
                        key="stiffness",
                        label="Elastic stiffness matrix",
                        default=stiffness,
                        row_labels=("1", "2", "3", "4", "5", "6"),
                        column_labels=("1", "2", "3", "4", "5", "6"),
                        symmetric=True,
                        bounds=NumericBounds(precision=8),
                        unit="GPa",
                        width="full",
                    ),
                    TagsField(
                        key="isotherms",
                        label="Requested isotherms",
                        default=(300.0, 600.0, 900.0),
                        value_type="float",
                        unit="K",
                        width="half",
                    ),
                    KeyValueField(
                        key="parameter_constraints",
                        label="Parameter constraints",
                        default=(
                            {"key": "K0", "value": 40.0},
                            {"key": "Kp", "value": 4.0},
                        ),
                        key_label="Parameter",
                        value_label="Initial value",
                        value_type="float",
                        width="half",
                    ),
                ),
            ),
            FormSection(
                key="conditional",
                title="Conditional and cross-field behavior",
                description=(
                    "Dependencies are declared in the schema rather than hard-coded "
                    "in page layouts."
                ),
                presentation="details",
                collapsed=True,
                advanced=True,
                fields=(
                    ChoiceField(
                        key="adiabatic_mode",
                        label="Adiabatic conversion",
                        default="auto",
                        choices=(
                            Choice("auto", "Automatic"),
                            Choice("off", "Disabled"),
                            Choice("require", "Required"),
                        ),
                    ),
                    NumericField(
                        key="adiabatic_reference_temperature",
                        label="Reference temperature",
                        default=298.15,
                        unit="K",
                        visible_when=(
                            Condition(
                                "adiabatic_mode",
                                ConditionOperator.NOT_EQUALS,
                                "off",
                            ),
                        ),
                    ),
                    NumericField(
                        key="fixed_pressure",
                        label="Fixed pressure",
                        unit="GPa",
                        width="half",
                    ),
                    NumericField(
                        key="fixed_temperature",
                        label="Fixed temperature",
                        unit="K",
                        width="half",
                    ),
                ),
            ),
        ),
        rules=(
            FormRule(
                kind=FormRuleKind.EXACTLY_ONE,
                fields=("fixed_pressure", "fixed_temperature"),
                message="Set exactly one fixed thermodynamic coordinate.",
            ),
        ),
    )


__all__ = ["ui_kit_form"]
