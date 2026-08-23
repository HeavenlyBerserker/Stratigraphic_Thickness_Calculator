"""Batch input/output column schema shared by desktop and web."""

from __future__ import annotations

from typing import Any

# Value column and matching Monte Carlo σ column (interleaved in the workbook).
INPUT_SIGMA_PAIRS: list[tuple[str, str]] = [
    ("M", "sigma_M"),
    ("delta_deg", "sigma_delta_deg"),
    ("phib_deg", "sigma_phib_deg"),
    ("beta1_deg", "sigma_beta1_deg"),
    ("phid1_deg", "sigma_phid1_deg"),
    ("beta2_deg", "sigma_beta2_deg"),
    ("phid2_deg", "sigma_phid2_deg"),
]

BATCH_HEADERS: list[str] = (
    ["well_id", "T"]
    + [col for pair in INPUT_SIGMA_PAIRS for col in pair]
)

# Map spreadsheet columns to ``source.models`` field names per model family.
T1_FIELD_MAP: dict[str, str] = {
    "M": "measured_thickness",
    "delta_deg": "wellbore_inclination_deg",
    "phib_deg": "wellbore_azimuth_deg",
    "beta1_deg": "formation_dip_deg",
    "phid1_deg": "dip_azimuth_deg",
}

TWO_BED_FIELD_MAP: dict[str, str] = {
    "M": "measured_thickness",
    "delta_deg": "wellbore_inclination_deg",
    "phib_deg": "wellbore_azimuth_deg",
    "beta1_deg": "formation_dip1_deg",
    "phid1_deg": "dip_azimuth1_deg",
    "beta2_deg": "formation_dip2_deg",
    "phid2_deg": "dip_azimuth2_deg",
}

MODEL_ID_BY_T: dict[int, str] = {
    1: "t1",
    2: "t2",
    3: "t3",
    4: "t4",
    5: "t5",
    6: "t6",
    7: "t7",
    8: "t8",
}

T1_REQUIRED = ["M", "delta_deg", "phib_deg", "beta1_deg", "phid1_deg"]
T1_UNUSED = ["beta2_deg", "phid2_deg"]
TWO_BED_REQUIRED = [col for col, _ in INPUT_SIGMA_PAIRS]

WRAP_AZIMUTH_FIELDS = frozenset(
    {
        "wellbore_azimuth_deg",
        "dip_azimuth_deg",
        "dip_azimuth1_deg",
        "dip_azimuth2_deg",
    }
)

FIELD_BOUNDS: dict[str, tuple[float, float]] = {
    "measured_thickness": (0.0, 1e9),
    "wellbore_inclination_deg": (0.0, 180.0),
    "wellbore_azimuth_deg": (0.0, 360.0),
    "formation_dip_deg": (0.0, 90.0),
    "dip_azimuth_deg": (0.0, 360.0),
    "formation_dip1_deg": (0.0, 90.0),
    "dip_azimuth1_deg": (0.0, 360.0),
    "formation_dip2_deg": (0.0, 90.0),
    "dip_azimuth2_deg": (0.0, 360.0),
}

# Defaults aligned with mobile/index.html.
DEFAULT_VALUES: dict[str, float] = {
    "M": 100.0,
    "delta_deg": 20.0,
    "phib_deg": 120.0,
    "beta1_deg": 15.0,
    "phid1_deg": 140.0,
    "beta2_deg": 18.0,
    "phid2_deg": 150.0,
}

DEFAULT_SIGMAS: dict[str, float] = {sigma: 0.0 for _, sigma in INPUT_SIGMA_PAIRS}

MC_SAMPLE_COUNT_DESKTOP = 10000
MC_SAMPLE_COUNT_WEB = 2500


def empty_input_row() -> dict[str, Any]:
    row: dict[str, Any] = {"well_id": "", "T": ""}
    for value_col, sigma_col in INPUT_SIGMA_PAIRS:
        row[value_col] = ""
        row[sigma_col] = 0.0
    return row


def example_rows() -> list[dict[str, Any]]:
    """Eight deterministic + eight Monte Carlo rows (one per T₁–T₈)."""
    rows: list[dict[str, Any]] = []
    for t in range(1, 9):
        row = empty_input_row()
        row["well_id"] = f"EX-DET-T{t}"
        row["T"] = t
        for col, val in DEFAULT_VALUES.items():
            row[col] = val
        for _, sigma_col in INPUT_SIGMA_PAIRS:
            row[sigma_col] = 0.0
        if t == 1:
            row["beta2_deg"] = ""
            row["phid2_deg"] = ""
        rows.append(row)

    for t in range(1, 9):
        row = empty_input_row()
        row["well_id"] = f"EX-MC-T{t}"
        row["T"] = t
        for col, val in DEFAULT_VALUES.items():
            row[col] = val
        for _, sigma_col in INPUT_SIGMA_PAIRS:
            row[sigma_col] = 0.0
        row["sigma_M"] = 1.0
        if t == 1:
            row["beta2_deg"] = ""
            row["phid2_deg"] = ""
        rows.append(row)
    return rows


def to_js_object() -> dict[str, Any]:
    return {
        "headers": BATCH_HEADERS,
        "inputSigmaPairs": [
            {"value": v, "sigma": s} for v, s in INPUT_SIGMA_PAIRS
        ],
        "modelIdByT": MODEL_ID_BY_T,
        "t1Required": T1_REQUIRED,
        "t1Unused": T1_UNUSED,
        "twoBedRequired": TWO_BED_REQUIRED,
        "wrapAzimuthFields": sorted(WRAP_AZIMUTH_FIELDS),
        "defaultValues": DEFAULT_VALUES,
        "defaultSigmas": DEFAULT_SIGMAS,
        "mcSampleCountWeb": MC_SAMPLE_COUNT_WEB,
        "exampleRows": example_rows(),
    }
