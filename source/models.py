from __future__ import annotations

from dataclasses import dataclass
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
    alpha_deg: float
    ud1_vector: tuple[float, float, float]
    ud2_prime_vector: tuple[float, float, float]
    ub_vector: tuple[float, float, float]
    ndc_vector: tuple[float, float, float]
    c_vector: tuple[float, float, float]


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
    """
    beta_rad = radians(formation_dip_deg)
    az_rad = radians(dip_azimuth_deg)
    x = sin(beta_rad) * sin(az_rad)
    y = sin(beta_rad) * cos(az_rad)
    z = cos(beta_rad)
    norm = sqrt(x * x + y * y + z * z)
    return (x / norm, y / norm, z / norm)


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


def compute_one_dip(inputs: OneDipInputs) -> OneDipResult:
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
    beta2_prime_rad = atan(
        tan(radians(inputs.formation_dip2_deg))
        * cos(radians(inputs.dip_azimuth1_deg - inputs.dip_azimuth2_deg))
    )
    beta2_prime_deg = beta2_prime_rad * 180.0 / pi

    ud1 = _downward_dip_pole_vector(
        formation_dip_deg=inputs.formation_dip1_deg,
        dip_azimuth_deg=inputs.dip_azimuth1_deg,
    )
    ud2_prime = _downward_dip_pole_vector(
        formation_dip_deg=beta2_prime_deg,
        dip_azimuth_deg=inputs.dip_azimuth1_deg,
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
    alpha_rad = acos(_clip_unit(_dot(ud1, mb_prime_unit)))

    sin_alpha = sin(alpha_rad)
    if abs(sin_alpha) < 1e-12:
        raise ValueError("sin(alpha) is zero. T5 is undefined for this geometry.")

    t5 = m_prime * (sin(gamma_rad) / sin_alpha)

    return ConcentricFoldResult(
        true_stratigraphic_thickness=t5,
        beta2_prime_deg=beta2_prime_deg,
        m_prime=m_prime,
        gamma_deg=gamma_rad * 180.0 / pi,
        alpha_deg=alpha_rad * 180.0 / pi,
        ud1_vector=ud1,
        ud2_prime_vector=ud2_prime,
        ub_vector=ub,
        ndc_vector=ndc,
        c_vector=c,
    )


def compute_plunging_concentric_fold(
    inputs: PlungingConcentricFoldInputs,
) -> PlungingConcentricFoldResult:
    """
    Plunging concentric fold: no dip azimuth correction; use Ud1 and Ud2 directly.
    N_dp = (Ud1 x Ud2) / ||Ud1 x Ud2||; M'b and M' as for concentric fold with N_dp.
    """
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
    alpha_rad = acos(_clip_unit(_dot(ud1, mb_prime_unit)))

    sin_alpha = sin(alpha_rad)
    if abs(sin_alpha) < 1e-12:
        raise ValueError("sin(alpha) is zero. T6 is undefined for this geometry.")

    t6 = m_prime * (sin(gamma_rad) / sin_alpha)

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
    )
