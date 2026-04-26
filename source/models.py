from __future__ import annotations

from dataclasses import dataclass, field
from math import acos, atan, cos, pi, radians, sin, sqrt, tan


@dataclass(slots=True)
class OneDipInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    formation_dip_deg: float
    wellbore_azimuth_deg: float
    dip_azimuth_deg: float


@dataclass(slots=True)
class OneDipResult:
    true_stratigraphic_thickness: float
    ud1_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]


@dataclass(slots=True)
class AverageVectorInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    wellbore_azimuth_deg: float
    formation_dip1_deg: float
    dip_azimuth1_deg: float
    formation_dip2_deg: float
    dip_azimuth2_deg: float


@dataclass(slots=True)
class AverageVectorResult:
    true_stratigraphic_thickness: float
    ud1_vector: tuple[float, float, float]
    ud2_vector: tuple[float, float, float]
    uav_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]


@dataclass(slots=True)
class AverageThicknessInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    wellbore_azimuth_deg: float
    formation_dip1_deg: float
    dip_azimuth1_deg: float
    formation_dip2_deg: float
    dip_azimuth2_deg: float


@dataclass(slots=True)
class AverageThicknessResult:
    true_stratigraphic_thickness: float
    ud1_dot_ub: float
    ud2_dot_ub: float
    ud1_vector: tuple[float, float, float]
    ud2_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]


@dataclass(slots=True)
class MixedAverageInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    wellbore_azimuth_deg: float
    formation_dip1_deg: float
    dip_azimuth1_deg: float
    formation_dip2_deg: float
    dip_azimuth2_deg: float


@dataclass(slots=True)
class MixedAverageResult:
    true_stratigraphic_thickness: float
    t2_value: float
    t3_value: float
    ud1_vector: tuple[float, float, float]
    ud2_vector: tuple[float, float, float]
    uav_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]


@dataclass(slots=True)
class ConcentricFoldInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    wellbore_azimuth_deg: float
    formation_dip1_deg: float
    dip_azimuth1_deg: float
    formation_dip2_deg: float
    dip_azimuth2_deg: float


@dataclass(slots=True)
class ConcentricFoldResult:
    true_stratigraphic_thickness: float
    beta2_prime_deg: float
    m_prime: float
    gamma_deg: float
    alpha_deg: float  # α = 90° − η/2 (degrees)
    eta_deg: float  # η = arccos(Ud1 · U'd2), degrees
    ud1_vector: tuple[float, float, float]
    ud2_prime_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]
    ndc_vector: tuple[float, float, float]
    c_vector: tuple[float, float, float]
    geometry_warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class PlungingConcentricFoldInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    wellbore_azimuth_deg: float
    formation_dip1_deg: float
    dip_azimuth1_deg: float
    formation_dip2_deg: float
    dip_azimuth2_deg: float


@dataclass(slots=True)
class PlungingConcentricFoldResult:
    true_stratigraphic_thickness: float
    m_prime: float
    gamma_deg: float
    alpha_deg: float
    ud1_vector: tuple[float, float, float]
    ud2_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]
    ndp_vector: tuple[float, float, float]
    c_vector: tuple[float, float, float]
    geometry_warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class TopNormalInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    wellbore_azimuth_deg: float
    formation_dip1_deg: float
    dip_azimuth1_deg: float
    formation_dip2_deg: float
    dip_azimuth2_deg: float


@dataclass(slots=True)
class TopNormalResult:
    true_stratigraphic_thickness: float
    m_prime: float
    alpha_deg: float
    eta_deg: float
    s_value: float
    uses_positive_s_branch: bool
    ud1_vector: tuple[float, float, float]
    ud2_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]
    ndp_vector: tuple[float, float, float]
    ub_prime_vector: tuple[float, float, float]
    geometry_warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class EqualAngleInputs:
    measured_thickness: float
    wellbore_inclination_deg: float
    wellbore_azimuth_deg: float
    formation_dip1_deg: float
    dip_azimuth1_deg: float
    formation_dip2_deg: float
    dip_azimuth2_deg: float


@dataclass(slots=True)
class EqualAngleResult:
    true_stratigraphic_thickness: float
    top_normal_thickness: float
    m_prime: float
    alpha_deg: float
    eta_deg: float
    s_value: float
    uses_positive_s_branch: bool
    ud1_vector: tuple[float, float, float]
    ud2_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]
    ndp_vector: tuple[float, float, float]
    ub_prime_vector: tuple[float, float, float]
    geometry_warnings: tuple[str, ...] = field(default_factory=tuple)


def _unit_vector_from_inclination_azimuth(
    inclination_deg: float,
    azimuth_deg: float,
) -> tuple[float, float, float]:
    """
    Return a unit direction vector from inclination/azimuth.
    Coordinate convention: x=East, y=North, z=Down.
    Inclination is measured from vertical down.
    """
    inc_rad = radians(inclination_deg)
    azi_rad = radians(azimuth_deg)
    x = sin(inc_rad) * sin(azi_rad)
    y = sin(inc_rad) * cos(azi_rad)
    z = cos(inc_rad)
    norm = sqrt(x * x + y * y + z * z)
    return (x / norm, y / norm, z / norm)


def _downward_dip_pole_vector(
    formation_dip_deg: float,
    dip_azimuth_deg: float,
) -> tuple[float, float, float]:
    """
    Dip-pole direction represented as downward normal to the bedding plane.

    For the base contact vector U_d2, call this with (formation_dip2_deg, dip_azimuth2_deg),
    i.e., use beta2 with phi_d2 (never beta1 with phi_d2).
    """
    beta_rad = radians(formation_dip_deg)
    az_rad = radians(dip_azimuth_deg)
    x = sin(beta_rad) * sin(az_rad)
    y = sin(beta_rad) * cos(az_rad)
    z = cos(beta_rad)
    norm = sqrt(x * x + y * y + z * z)
    return (x / norm, y / norm, z / norm)


def _smallest_azimuth_separation_deg(phi1_deg: float, phi2_deg: float) -> float:
    """Smallest angle between two map azimuths, in [0, 180] degrees."""
    d = abs(phi1_deg - phi2_deg) % 360.0
    if d > 180.0:
        d = 360.0 - d
    return d


def _concentric_fold_dip_pole_unit(
    dip_azimuth_deg: float,
    formation_dip_deg: float,
) -> tuple[float, float, float]:
    """
    Dip-pole unit vector for the concentric-fold model (Xu et al., 2007, 2010):
    U = (-cos φd sin β, -sin φd sin β, cos β) with x=East, y=North, z=Down.
    U_d1 uses (φ_d1, β_1); U'_d2 uses (φ from the azimuth-branch rule, β'_2).
    """
    beta_rad = radians(formation_dip_deg)
    phi_rad = radians(dip_azimuth_deg)
    x = -cos(phi_rad) * sin(beta_rad)
    y = -sin(phi_rad) * sin(beta_rad)
    z = cos(beta_rad)
    return (x, y, z)


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(v: tuple[float, float, float]) -> float:
    return sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _normalize(v: tuple[float, float, float], error_message: str) -> tuple[float, float, float]:
    v_norm = _norm(v)
    if v_norm == 0:
        raise ValueError(error_message)
    return (v[0] / v_norm, v[1] / v_norm, v[2] / v_norm)


def _clip_unit(x: float) -> float:
    return max(-1.0, min(1.0, x))


_SURVEY_DEG_EPS = 1e-6
_INTERIOR_DEG_EPS = 1e-3  # strict inequalities for η, α, γ (degrees)


def _validate_survey_angles(
    *,
    wellbore_inclination_deg: float,
    wellbore_azimuth_deg: float,
    bed_dips_deg: list[float],
    bed_azimuths_deg: list[float],
) -> None:
    """Enforce documented input ranges: δ∈[0,180], φ∈[0,360], β∈[0,90]."""
    if not (-_SURVEY_DEG_EPS <= wellbore_inclination_deg <= 180.0 + _SURVEY_DEG_EPS):
        raise ValueError(
            "Wellbore inclination δ must be in [0°, 180°] (angle from vertical down)."
        )
    if not (-_SURVEY_DEG_EPS <= wellbore_azimuth_deg <= 360.0 + _SURVEY_DEG_EPS):
        raise ValueError(
            "Wellbore azimuth φ_b must be in [0°, 360°] (clockwise from north)."
        )
    for b in bed_dips_deg:
        if not (-_SURVEY_DEG_EPS <= b <= 90.0 + _SURVEY_DEG_EPS):
            raise ValueError(f"Bed dip β must be in [0°, 90°] (got {b:.6f}°).")
    for p in bed_azimuths_deg:
        if not (-_SURVEY_DEG_EPS <= p <= 360.0 + _SURVEY_DEG_EPS):
            raise ValueError(f"Dip azimuth φ must be in [0°, 360°] (got {p:.6f}°).")


def _warn_intermediate_closed_deg(
    label: str, value_deg: float, lo: float, hi: float
) -> str | None:
    if lo - _SURVEY_DEG_EPS <= value_deg <= hi + _SURVEY_DEG_EPS:
        return None
    return (
        f"{label} is outside the expected closed range [{lo}°, {hi}°] "
        f"(computed {value_deg:.4f}°). The thickness above may be non-physical or unreliable."
    )


def _warn_interior_open_deg(label: str, value_deg: float, lo: float, hi: float) -> str | None:
    if lo + _INTERIOR_DEG_EPS < value_deg < hi - _INTERIOR_DEG_EPS:
        return None
    return (
        f"{label} is outside the expected open range ({lo}°, {hi}°) "
        f"(computed {value_deg:.4f}°). The thickness above may be non-physical or unreliable."
    )


def compute_one_dip(inputs: OneDipInputs) -> OneDipResult:
    _validate_survey_angles(
        wellbore_inclination_deg=inputs.wellbore_inclination_deg,
        wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
        bed_dips_deg=[inputs.formation_dip_deg],
        bed_azimuths_deg=[inputs.dip_azimuth_deg],
    )
    delta = radians(inputs.wellbore_inclination_deg)
    beta1 = radians(inputs.formation_dip_deg)
    azimuth_diff = radians(inputs.dip_azimuth_deg - inputs.wellbore_azimuth_deg)

    thickness = (
        inputs.measured_thickness
        * (
            cos(delta)
            - sin(delta) * cos(azimuth_diff) * tan(beta1)
        )
        * cos(beta1)
    )

    ud1 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip_deg,
        dip_azimuth_deg=inputs.dip_azimuth_deg,
    )
    ub = _unit_vector_from_inclination_azimuth(
        inclination_deg=inputs.wellbore_inclination_deg,
        azimuth_deg=inputs.wellbore_azimuth_deg,
    )

    return OneDipResult(
        true_stratigraphic_thickness=thickness,
        ud1_vector=ud1,
        ub_vector=ub,
    )


def compute_average_vector(inputs: AverageVectorInputs) -> AverageVectorResult:
    _validate_survey_angles(
        wellbore_inclination_deg=inputs.wellbore_inclination_deg,
        wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
        bed_dips_deg=[inputs.formation_dip1_deg, inputs.formation_dip2_deg],
        bed_azimuths_deg=[inputs.dip_azimuth1_deg, inputs.dip_azimuth2_deg],
    )
    ud1 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip1_deg,
        dip_azimuth_deg=inputs.dip_azimuth1_deg,
    )
    ud2 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip2_deg,
        dip_azimuth_deg=inputs.dip_azimuth2_deg,
    )
    ub = _unit_vector_from_inclination_azimuth(
        inclination_deg=inputs.wellbore_inclination_deg,
        azimuth_deg=inputs.wellbore_azimuth_deg,
    )

    ud_sum = (
        ud1[0] + ud2[0],
        ud1[1] + ud2[1],
        ud1[2] + ud2[2],
    )
    ud_sum_norm = sqrt(
        ud_sum[0] * ud_sum[0] + ud_sum[1] * ud_sum[1] + ud_sum[2] * ud_sum[2]
    )
    if ud_sum_norm == 0:
        raise ValueError("U_d1 + U_d2 is zero. Average vector is undefined.")

    uav = (
        ud_sum[0] / ud_sum_norm,
        ud_sum[1] / ud_sum_norm,
        ud_sum[2] / ud_sum_norm,
    )

    dot_uav_ub = uav[0] * ub[0] + uav[1] * ub[1] + uav[2] * ub[2]
    thickness = inputs.measured_thickness * dot_uav_ub

    return AverageVectorResult(
        true_stratigraphic_thickness=thickness,
        ud1_vector=ud1,
        ud2_vector=ud2,
        uav_vector=uav,
        ub_vector=ub,
    )


def compute_average_thickness(
    inputs: AverageThicknessInputs,
) -> AverageThicknessResult:
    _validate_survey_angles(
        wellbore_inclination_deg=inputs.wellbore_inclination_deg,
        wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
        bed_dips_deg=[inputs.formation_dip1_deg, inputs.formation_dip2_deg],
        bed_azimuths_deg=[inputs.dip_azimuth1_deg, inputs.dip_azimuth2_deg],
    )
    ud1 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip1_deg,
        dip_azimuth_deg=inputs.dip_azimuth1_deg,
    )
    ud2 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip2_deg,
        dip_azimuth_deg=inputs.dip_azimuth2_deg,
    )
    ub = _unit_vector_from_inclination_azimuth(
        inclination_deg=inputs.wellbore_inclination_deg,
        azimuth_deg=inputs.wellbore_azimuth_deg,
    )

    ud1_dot_ub = ud1[0] * ub[0] + ud1[1] * ub[1] + ud1[2] * ub[2]
    ud2_dot_ub = ud2[0] * ub[0] + ud2[1] * ub[1] + ud2[2] * ub[2]
    thickness = inputs.measured_thickness * (ud1_dot_ub + ud2_dot_ub) / 2.0

    return AverageThicknessResult(
        true_stratigraphic_thickness=thickness,
        ud1_dot_ub=ud1_dot_ub,
        ud2_dot_ub=ud2_dot_ub,
        ud1_vector=ud1,
        ud2_vector=ud2,
        ub_vector=ub,
    )


def compute_mixed_average(inputs: MixedAverageInputs) -> MixedAverageResult:
    avg_vector_result = compute_average_vector(
        AverageVectorInputs(
            measured_thickness=inputs.measured_thickness,
            wellbore_inclination_deg=inputs.wellbore_inclination_deg,
            wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
            formation_dip1_deg=inputs.formation_dip1_deg,
            dip_azimuth1_deg=inputs.dip_azimuth1_deg,
            formation_dip2_deg=inputs.formation_dip2_deg,
            dip_azimuth2_deg=inputs.dip_azimuth2_deg,
        )
    )
    avg_thickness_result = compute_average_thickness(
        AverageThicknessInputs(
            measured_thickness=inputs.measured_thickness,
            wellbore_inclination_deg=inputs.wellbore_inclination_deg,
            wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
            formation_dip1_deg=inputs.formation_dip1_deg,
            dip_azimuth1_deg=inputs.dip_azimuth1_deg,
            formation_dip2_deg=inputs.formation_dip2_deg,
            dip_azimuth2_deg=inputs.dip_azimuth2_deg,
        )
    )

    t2_value = avg_vector_result.true_stratigraphic_thickness
    t3_value = avg_thickness_result.true_stratigraphic_thickness
    t4_value = (t2_value + t3_value) / 2.0

    return MixedAverageResult(
        true_stratigraphic_thickness=t4_value,
        t2_value=t2_value,
        t3_value=t3_value,
        ud1_vector=avg_vector_result.ud1_vector,
        ud2_vector=avg_vector_result.ud2_vector,
        uav_vector=avg_vector_result.uav_vector,
        ub_vector=avg_vector_result.ub_vector,
    )


def compute_concentric_fold(inputs: ConcentricFoldInputs) -> ConcentricFoldResult:
    """
    Concentric fold (Xu et al., 2007, 2010): corrected β'₂ and U'_d2, N_dc, Berg (2011)
    M' and U'_b, T₅ = M' sin γ / cos(η/2), with γ, U_c, and η from dip-pole geometry.
    """
    _validate_survey_angles(
        wellbore_inclination_deg=inputs.wellbore_inclination_deg,
        wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
        bed_dips_deg=[inputs.formation_dip1_deg, inputs.formation_dip2_deg],
        bed_azimuths_deg=[inputs.dip_azimuth1_deg, inputs.dip_azimuth2_deg],
    )
    phi_d1 = inputs.dip_azimuth1_deg
    phi_d2 = inputs.dip_azimuth2_deg
    az_sep = _smallest_azimuth_separation_deg(phi_d1, phi_d2)

    beta2_prime_rad = atan(
        tan(radians(inputs.formation_dip2_deg))
        * abs(cos(radians(phi_d1 - phi_d2)))
    )
    beta2_prime_deg = beta2_prime_rad * 180.0 / pi

    phi_for_ud2 = phi_d1 if az_sep <= 90.0 else (phi_d1 + 180.0) % 360.0

    ud1 = _concentric_fold_dip_pole_unit(
        dip_azimuth_deg=phi_d1,
        formation_dip_deg=inputs.formation_dip1_deg,
    )
    ud2_prime = _concentric_fold_dip_pole_unit(
        dip_azimuth_deg=phi_for_ud2,
        formation_dip_deg=beta2_prime_deg,
    )
    ub = _unit_vector_from_inclination_azimuth(
        inclination_deg=inputs.wellbore_inclination_deg,
        azimuth_deg=inputs.wellbore_azimuth_deg,
    )

    ndc = _normalize(
        _cross(ud1, ud2_prime),
        "U_d1 x U'_d2 is zero. N_dc is undefined.",
    )
    mb = (
        inputs.measured_thickness * ub[0],
        inputs.measured_thickness * ub[1],
        inputs.measured_thickness * ub[2],
    )
    ndc_dot_mb = _dot(ndc, mb)
    mb_prime = (
        mb[0] - ndc[0] * ndc_dot_mb,
        mb[1] - ndc[1] * ndc_dot_mb,
        mb[2] - ndc[2] * ndc_dot_mb,
    )
    m_prime = _norm(mb_prime)
    if m_prime == 0:
        raise ValueError("M' is zero. Projection onto dip-normal plane is zero.")

    c = _normalize(
        (
            ud1[0] - ud2_prime[0],
            ud1[1] - ud2_prime[1],
            ud1[2] - ud2_prime[2],
        ),
        "U_d1 - U'_d2 is zero. Vector C is undefined.",
    )
    mb_prime_unit = (mb_prime[0] / m_prime, mb_prime[1] / m_prime, mb_prime[2] / m_prime)
    gamma_rad = acos(_clip_unit(_dot(c, mb_prime_unit)))
    eta_rad = acos(_clip_unit(_dot(ud1, ud2_prime)))
    cos_half_eta = cos(eta_rad / 2.0)
    if abs(cos_half_eta) < 1e-12:
        raise ValueError("cos(η/2) is zero. T5 is undefined for this geometry.")

    t5 = m_prime * (sin(gamma_rad) / cos_half_eta)
    alpha_paper_rad = pi / 2.0 - eta_rad / 2.0

    eta_deg_check = eta_rad * 180.0 / pi
    gamma_deg_check = gamma_rad * 180.0 / pi
    alpha_deg_check = alpha_paper_rad * 180.0 / pi
    geom_warn: list[str] = []
    for w in (
        _warn_intermediate_closed_deg("β′₂ (corrected base dip)", beta2_prime_deg, 0.0, 90.0),
        _warn_interior_open_deg("η (angle between U_d1 and U′d2)", eta_deg_check, 0.0, 180.0),
        _warn_interior_open_deg("γ", gamma_deg_check, 0.0, 180.0),
        _warn_interior_open_deg("α (90° − η/2)", alpha_deg_check, 0.0, 180.0),
    ):
        if w is not None:
            geom_warn.append(w)

    return ConcentricFoldResult(
        true_stratigraphic_thickness=t5,
        beta2_prime_deg=beta2_prime_deg,
        m_prime=m_prime,
        gamma_deg=gamma_rad * 180.0 / pi,
        alpha_deg=alpha_paper_rad * 180.0 / pi,
        eta_deg=eta_rad * 180.0 / pi,
        ud1_vector=ud1,
        ud2_prime_vector=ud2_prime,
        ub_vector=ub,
        ndc_vector=ndc,
        c_vector=c,
        geometry_warnings=tuple(geom_warn),
    )


def compute_plunging_concentric_fold(
    inputs: PlungingConcentricFoldInputs,
) -> PlungingConcentricFoldResult:
    """
    Plunging fold: bed azimuths at top and base may differ; no azimuth correction.
    N_dp = (Ud1 x Ud2) / ||Ud1 x Ud2||; M' = ||M'b|| with M'b = Mb - N_dp(N_dp . Mb).
    Uc = (Ud1 - Ud2) / ||Ud1 - Ud2||; gamma = arccos(Uc . U'b), alpha = arccos(Ud1 . Uc).
    """
    _validate_survey_angles(
        wellbore_inclination_deg=inputs.wellbore_inclination_deg,
        wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
        bed_dips_deg=[inputs.formation_dip1_deg, inputs.formation_dip2_deg],
        bed_azimuths_deg=[inputs.dip_azimuth1_deg, inputs.dip_azimuth2_deg],
    )
    ud1 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip1_deg,
        dip_azimuth_deg=inputs.dip_azimuth1_deg,
    )
    ud2 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip2_deg,
        dip_azimuth_deg=inputs.dip_azimuth2_deg,
    )
    ub = _unit_vector_from_inclination_azimuth(
        inclination_deg=inputs.wellbore_inclination_deg,
        azimuth_deg=inputs.wellbore_azimuth_deg,
    )

    ndp = _normalize(
        _cross(ud1, ud2),
        "U_d1 x U_d2 is zero. N_dp is undefined.",
    )
    mb = (
        inputs.measured_thickness * ub[0],
        inputs.measured_thickness * ub[1],
        inputs.measured_thickness * ub[2],
    )
    ndp_dot_mb = _dot(ndp, mb)
    mb_prime = (
        mb[0] - ndp[0] * ndp_dot_mb,
        mb[1] - ndp[1] * ndp_dot_mb,
        mb[2] - ndp[2] * ndp_dot_mb,
    )
    m_prime = _norm(mb_prime)
    if m_prime == 0:
        raise ValueError("M' is zero. Projection onto dip-normal plane is zero.")

    c = _normalize(
        (ud1[0] - ud2[0], ud1[1] - ud2[1], ud1[2] - ud2[2]),
        "U_d1 - U_d2 is zero. Vector C is undefined.",
    )
    mb_prime_unit = (
        mb_prime[0] / m_prime,
        mb_prime[1] / m_prime,
        mb_prime[2] / m_prime,
    )
    gamma_rad = acos(_clip_unit(_dot(c, mb_prime_unit)))
    alpha_rad = acos(_clip_unit(_dot(ud1, c)))

    sin_alpha = sin(alpha_rad)
    if abs(sin_alpha) < 1e-12:
        raise ValueError("sin(alpha) is zero. T6 is undefined for this geometry.")

    t6 = m_prime * (sin(gamma_rad) / sin_alpha)
    gamma_deg_check = gamma_rad * 180.0 / pi
    alpha_deg_check = alpha_rad * 180.0 / pi
    geom_warn: list[str] = []
    for w in (
        _warn_interior_open_deg("γ", gamma_deg_check, 0.0, 180.0),
        _warn_interior_open_deg("α", alpha_deg_check, 0.0, 180.0),
    ):
        if w is not None:
            geom_warn.append(w)

    return PlungingConcentricFoldResult(
        true_stratigraphic_thickness=t6,
        m_prime=m_prime,
        gamma_deg=gamma_rad * 180.0 / pi,
        alpha_deg=alpha_rad * 180.0 / pi,
        ud1_vector=ud1,
        ud2_vector=ud2,
        ub_vector=ub,
        ndp_vector=ndp,
        c_vector=c,
        geometry_warnings=tuple(geom_warn),
    )


def compute_top_normal(inputs: TopNormalInputs) -> TopNormalResult:
    """
    Top-normal (wedging) bed: M is measured normal to the top bed.
    M' from Berg (2011) projection onto the plane of Ud1 and Ud2 with N_dp.
    Thickness = M' cos(α ∓ η)/cos(η) (paper T7) with S = N_dp · U'b selecting the branch.
    """
    _validate_survey_angles(
        wellbore_inclination_deg=inputs.wellbore_inclination_deg,
        wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
        bed_dips_deg=[inputs.formation_dip1_deg, inputs.formation_dip2_deg],
        bed_azimuths_deg=[inputs.dip_azimuth1_deg, inputs.dip_azimuth2_deg],
    )
    ud1 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip1_deg,
        dip_azimuth_deg=inputs.dip_azimuth1_deg,
    )
    ud2 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip2_deg,
        dip_azimuth_deg=inputs.dip_azimuth2_deg,
    )
    ub = _unit_vector_from_inclination_azimuth(
        inclination_deg=inputs.wellbore_inclination_deg,
        azimuth_deg=inputs.wellbore_azimuth_deg,
    )

    ndp = _normalize(
        _cross(ud1, ud2),
        "U_d1 x U_d2 is zero. N_dp is undefined.",
    )
    mb = (
        inputs.measured_thickness * ub[0],
        inputs.measured_thickness * ub[1],
        inputs.measured_thickness * ub[2],
    )
    ndp_dot_mb = _dot(ndp, mb)
    mb_prime = (
        mb[0] - ndp[0] * ndp_dot_mb,
        mb[1] - ndp[1] * ndp_dot_mb,
        mb[2] - ndp[2] * ndp_dot_mb,
    )
    m_prime = _norm(mb_prime)
    if m_prime == 0:
        raise ValueError("M' is zero. Projection onto dip-normal plane is zero.")

    ub_prime = (
        mb_prime[0] / m_prime,
        mb_prime[1] / m_prime,
        mb_prime[2] / m_prime,
    )

    alpha_rad = acos(_clip_unit(_dot(ud1, ub_prime)))
    eta_rad = acos(_clip_unit(_dot(ud1, ud2)))

    cos_eta = cos(eta_rad)
    if abs(cos_eta) < 1e-12:
        raise ValueError("cos(η) is zero. Top-normal thickness is undefined for this geometry.")

    s_val = _dot(ndp, ub_prime)
    if s_val >= 0.0:
        t_top_normal = m_prime * cos(alpha_rad + eta_rad) / cos_eta
        uses_positive = True
    else:
        t_top_normal = m_prime * cos(alpha_rad - eta_rad) / cos_eta
        uses_positive = False

    eta_deg_check = eta_rad * 180.0 / pi
    gw = _warn_interior_open_deg("η (angle between U_d1 and U_d2)", eta_deg_check, 0.0, 180.0)
    geom_warn: tuple[str, ...] = (gw,) if gw is not None else ()

    return TopNormalResult(
        true_stratigraphic_thickness=t_top_normal,
        m_prime=m_prime,
        alpha_deg=alpha_rad * 180.0 / pi,
        eta_deg=eta_rad * 180.0 / pi,
        s_value=s_val,
        uses_positive_s_branch=uses_positive,
        ud1_vector=ud1,
        ud2_vector=ud2,
        ub_vector=ub,
        ndp_vector=ndp,
        ub_prime_vector=ub_prime,
        geometry_warnings=geom_warn,
    )


def compute_equal_angle(inputs: EqualAngleInputs) -> EqualAngleResult:
    """
    Equal-angle method: T8 = T_top cos(η/2) where T_top is the top-normal thickness
    and η = arccos(Ud1 · Ud2) as in the top-normal geometry.
    """
    tn = compute_top_normal(
        TopNormalInputs(
            measured_thickness=inputs.measured_thickness,
            wellbore_inclination_deg=inputs.wellbore_inclination_deg,
            wellbore_azimuth_deg=inputs.wellbore_azimuth_deg,
            formation_dip1_deg=inputs.formation_dip1_deg,
            dip_azimuth1_deg=inputs.dip_azimuth1_deg,
            formation_dip2_deg=inputs.formation_dip2_deg,
            dip_azimuth2_deg=inputs.dip_azimuth2_deg,
        )
    )
    eta_rad = radians(tn.eta_deg)
    t8 = tn.true_stratigraphic_thickness * cos(eta_rad / 2.0)
    return EqualAngleResult(
        true_stratigraphic_thickness=t8,
        top_normal_thickness=tn.true_stratigraphic_thickness,
        m_prime=tn.m_prime,
        alpha_deg=tn.alpha_deg,
        eta_deg=tn.eta_deg,
        s_value=tn.s_value,
        uses_positive_s_branch=tn.uses_positive_s_branch,
        ud1_vector=tn.ud1_vector,
        ud2_vector=tn.ud2_vector,
        ub_vector=tn.ub_vector,
        ndp_vector=tn.ndp_vector,
        ub_prime_vector=tn.ub_prime_vector,
        geometry_warnings=tn.geometry_warnings,
    )
