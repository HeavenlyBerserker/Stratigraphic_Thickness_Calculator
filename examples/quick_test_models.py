"""
Quick regression check for all thickness models (T1-T8) and Monte Carlo sampling.

Uses the same default inputs as the web app (``mobile/index.html``). Run from the repository root:

    python examples/quick_test_models.py

Exit code 0 means all checks passed.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.models import (  # noqa: E402
    AverageThicknessInputs,
    AverageVectorInputs,
    ConcentricFoldInputs,
    EqualAngleInputs,
    MixedAverageInputs,
    OneDipInputs,
    PlungingConcentricFoldInputs,
    TopNormalInputs,
    compute_average_thickness,
    compute_average_vector,
    compute_concentric_fold,
    compute_equal_angle,
    compute_mixed_average,
    compute_one_dip,
    compute_plunging_concentric_fold,
    compute_top_normal,
)

# Defaults in mobile/index.html (shared two-bed fields where applicable).
TWO_BED = {
    "measured_thickness": 100.0,
    "wellbore_inclination_deg": 20.0,
    "wellbore_azimuth_deg": 120.0,
    "formation_dip1_deg": 15.0,
    "dip_azimuth1_deg": 140.0,
    "formation_dip2_deg": 18.0,
    "dip_azimuth2_deg": 150.0,
}

WRAP_AZIMUTH_KEYS = frozenset(
    {
        "wellbore_azimuth_deg",
        "dip_azimuth_deg",
        "dip_azimuth1_deg",
        "dip_azimuth2_deg",
    }
)

MC_SAMPLE_COUNT = 5000
MC_SEED = 42

# Deterministic T at defaults (web / desktop / source.models).
EXPECTED_T = {
    "t1": 82.44905335189677,
    "t2": 98.8682902764527,
    "t3": 98.80436279445732,
    "t4": 98.83632653545502,
    "t5": 99.68169400792584,
    "t6": 98.9322591202143,
    "t7": 99.39274196793524,
    "t8": 99.3284753794784,
}

# Monte Carlo with sigma(M)=1 only, seed=42, n=5000 (matches in-app / Pyodide logic).
MC_T1_REF = {
    "mean": 82.44505321455188,
    "p10": 81.38245573630984,
    "p50": 82.43588061122054,
    "p90": 83.51300534750663,
}
MC_T2_REF = {
    "mean": 98.86349353562812,
    "p10": 97.58928611110535,
    "p50": 98.85249426308484,
    "p90": 100.14412196239343,
}
MC_STAT_RTOL = 0.02  # 2% on mean / percentiles vs fixed-seed reference


@dataclass(frozen=True)
class ModelCase:
    model_id: str
    label: str
    build_inputs: Callable[[dict[str, float]], Any]
    compute: Callable[[Any], Any]


def _bounds(field: str) -> tuple[float, float]:
    if "azimuth" in field:
        return (0.0, 360.0)
    if "inclination" in field:
        return (0.0, 180.0)
    if "dip" in field:
        return (0.0, 90.0)
    return (-1e9, 1e9)


def _sample(mu: float, sigma: float, lo: float, hi: float, wrap: bool) -> float:
    if sigma <= 0.0:
        return mu
    raw = random.gauss(mu, sigma)
    if wrap:
        width = hi - lo
        return ((raw - lo) % width) + lo
    return min(max(raw, lo), hi)


def _percentile(values: list[float], p: float) -> float:
    sv = sorted(values)
    if len(sv) == 1:
        return sv[0]
    index = (len(sv) - 1) * p
    low = int(index)
    high = min(low + 1, len(sv) - 1)
    frac = index - low
    return sv[low] * (1.0 - frac) + sv[high] * frac


def _close(a: float, b: float, rtol: float = 1e-9) -> bool:
    return abs(a - b) <= rtol * max(1.0, abs(b))


def _close_stat(a: float, b: float, rtol: float = MC_STAT_RTOL) -> bool:
    return abs(a - b) <= rtol * max(1.0, abs(b))


def run_monte_carlo(
    case: ModelCase,
    values: dict[str, float],
    stds: dict[str, float],
    *,
    sample_count: int = MC_SAMPLE_COUNT,
    seed: int = MC_SEED,
) -> dict[str, float]:
    random.seed(seed)
    thicknesses: list[float] = []
    keys = list(values.keys())
    for _ in range(sample_count):
        cur: dict[str, float] = {}
        for key in keys:
            lo, hi = _bounds(key)
            cur[key] = _sample(
                values[key],
                stds.get(key, 0.0),
                lo,
                hi,
                key in WRAP_AZIMUTH_KEYS,
            )
        result = case.compute(case.build_inputs(cur))
        thicknesses.append(float(result.true_stratigraphic_thickness))
    return {
        "mean": mean(thicknesses),
        "std": pstdev(thicknesses),
        "p10": _percentile(thicknesses, 0.10),
        "p50": _percentile(thicknesses, 0.50),
        "p90": _percentile(thicknesses, 0.90),
    }


def _model_cases() -> list[ModelCase]:
    t1_vals = {
        "measured_thickness": 100.0,
        "wellbore_inclination_deg": 20.0,
        "formation_dip_deg": 15.0,
        "wellbore_azimuth_deg": 120.0,
        "dip_azimuth_deg": 140.0,
    }
    return [
        ModelCase(
            "t1",
            "One-dip (T1)",
            lambda v: OneDipInputs(
                v["measured_thickness"],
                v["wellbore_inclination_deg"],
                v["formation_dip_deg"],
                v["wellbore_azimuth_deg"],
                v["dip_azimuth_deg"],
            ),
            compute_one_dip,
        ),
        ModelCase(
            "t2",
            "Average-vector (T2)",
            lambda v: AverageVectorInputs(**v),
            compute_average_vector,
        ),
        ModelCase(
            "t3",
            "Average-thickness (T3)",
            lambda v: AverageThicknessInputs(**v),
            compute_average_thickness,
        ),
        ModelCase(
            "t4",
            "Mixed-average (T4)",
            lambda v: MixedAverageInputs(**v),
            compute_mixed_average,
        ),
        ModelCase(
            "t5",
            "Concentric fold (T5)",
            lambda v: ConcentricFoldInputs(**v),
            compute_concentric_fold,
        ),
        ModelCase(
            "t6",
            "Plunging fold (T6)",
            lambda v: PlungingConcentricFoldInputs(**v),
            compute_plunging_concentric_fold,
        ),
        ModelCase(
            "t7",
            "Top-normal (T7)",
            lambda v: TopNormalInputs(**v),
            compute_top_normal,
        ),
        ModelCase(
            "t8",
            "Equal-angle (T8)",
            lambda v: EqualAngleInputs(**v),
            compute_equal_angle,
        ),
    ]


def test_deterministic(cases: list[ModelCase]) -> list[str]:
    errors: list[str] = []
    t1_vals = {
        "measured_thickness": 100.0,
        "wellbore_inclination_deg": 20.0,
        "formation_dip_deg": 15.0,
        "wellbore_azimuth_deg": 120.0,
        "dip_azimuth_deg": 140.0,
    }
    for case in cases:
        values = dict(TWO_BED) if case.model_id != "t1" else t1_vals
        try:
            t = float(case.compute(case.build_inputs(values)).true_stratigraphic_thickness)
        except Exception as exc:
            errors.append(f"{case.label}: raised {exc!r}")
            continue
        expected = EXPECTED_T[case.model_id]
        if not _close(t, expected):
            errors.append(f"{case.label}: T={t}, expected {expected}")
        elif t <= 0.0:
            errors.append(f"{case.label}: T should be positive, got {t}")
        else:
            print(f"OK: {case.label} T = {t:.6f}")
    return errors


def test_monte_carlo(
    case: ModelCase,
    values: dict[str, float],
    reference: dict[str, float],
    label: str,
) -> list[str]:
    errors: list[str] = []
    stds = {k: 0.0 for k in values}
    stds["measured_thickness"] = 1.0
    stats = run_monte_carlo(case, values, stds)
    for key in ("mean", "p10", "p50", "p90"):
        got = stats[key]
        ref = reference[key]
        if not _close_stat(got, ref):
            errors.append(f"{label} MC {key}: got {got}, expected ~{ref} (rtol {MC_STAT_RTOL})")
    if not errors:
        print(
            f"OK: {label} Monte Carlo (sigma M=1, n={MC_SAMPLE_COUNT}, seed={MC_SEED}) "
            f"mean={stats['mean']:.4f} p10={stats['p10']:.4f} "
            f"p50={stats['p50']:.4f} p90={stats['p90']:.4f}"
        )
    return errors


def main() -> int:
    cases = _model_cases()
    errors = test_deterministic(cases)

    t1_vals = {
        "measured_thickness": 100.0,
        "wellbore_inclination_deg": 20.0,
        "formation_dip_deg": 15.0,
        "wellbore_azimuth_deg": 120.0,
        "dip_azimuth_deg": 140.0,
    }
    errors.extend(test_monte_carlo(cases[0], t1_vals, MC_T1_REF, "T1"))
    errors.extend(test_monte_carlo(cases[1], dict(TWO_BED), MC_T2_REF, "T2"))

    if errors:
        print("\nFAILED:")
        for msg in errors:
            print(" ", msg)
        return 1
    print("\nAll deterministic and Monte Carlo checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
