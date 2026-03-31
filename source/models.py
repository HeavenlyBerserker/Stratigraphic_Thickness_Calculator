from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin, sqrt, tan


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
