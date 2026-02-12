"""Volume calculations for reactor components.

This module computes component volumes based on radial build parameters
and reactor geometry (tokamak, mirror, or IFE chamber).
"""
import math
from typing import Dict

from ..costing_data import CostingData
from ..enums_new import ReactorType
from ..units import Meters, Meters3


def compute_inner_radii(data: CostingData) -> Dict[str, float]:
    """Compute inner radii of all layers from radial build.
    
    Stacks layer thicknesses outward from plasma edge.
    
    Args:
        data: CostingData with geometry inputs
        
    Returns:
        Dict of component inner radii [m]
    """
    inp = data.cas220101_in
    
    # Starting radius (outer edge of plasma)
    if data.basic.reactor_type == ReactorType.MFE_TOKAMAK:
        r0 = inp.r_plasma + inp.a_plasma  # Major radius + minor radius
    else:
        r0 = inp.r_plasma  # Chamber radius for mirror/IFE
    
    radii = {}
    radii['plasma_outer'] = r0
    radii['first_wall_inner'] = r0
    radii['blanket_inner'] = r0 + inp.first_wall_thickness
    radii['shield_inner'] = radii['blanket_inner'] + inp.blanket_thickness
    radii['magnet_inner'] = radii['shield_inner'] + inp.shield_thickness
    
    return radii


def compute_outer_radii(data: CostingData, inner_radii: Dict[str, float]) -> Dict[str, float]:
    """Compute outer radii by adding thicknesses to inner radii.
    
    Args:
        data: CostingData with geometry inputs
        inner_radii: Dict of inner radii from compute_inner_radii
        
    Returns:
        Dict of component outer radii [m]
    """
    inp = data.cas220101_in
    
    radii = {}
    radii['first_wall_outer'] = inner_radii['first_wall_inner'] + inp.first_wall_thickness
    radii['blanket_outer'] = inner_radii['blanket_inner'] + inp.blanket_thickness
    radii['shield_outer'] = inner_radii['shield_inner'] + inp.shield_thickness
    
    return radii


def calc_volume_outer_hollow_torus(R: float, r_outer: float, r_inner: float) -> float:
    """Calculate volume of hollow torus (tokamak geometry).
    
    V = 2π²R(r_outer² - r_inner²)
    
    Args:
        R: Major radius [m]
        r_outer: Outer minor radius [m]
        r_inner: Inner minor radius [m]
        
    Returns:
        Volume [m³]
    """
    return 2.0 * math.pi**2 * R * (r_outer**2 - r_inner**2)


def calc_volume_ring(length: float, r_inner: float, r_outer: float) -> float:
    """Calculate volume of cylindrical ring (mirror geometry).
    
    V = πL(r_outer² - r_inner²)
    
    Args:
        length: Cylinder length [m]
        r_outer: Outer radius [m]
        r_inner: Inner radius [m]
        
    Returns:
        Volume [m³]
    """
    return math.pi * length * (r_outer**2 - r_inner**2)


def calc_volume_sphere(r_inner: float, r_outer: float) -> float:
    """Calculate volume of spherical shell (IFE geometry).
    
    V = 4/3 π (r_outer³ - r_inner³)
    
    Args:
        r_outer: Outer radius [m]
        r_inner: Inner radius [m]
        
    Returns:
        Volume [m³]
    """
    return (4.0/3.0) * math.pi * (r_outer**3 - r_inner**3)


def compute_volumes_mfe_tokamak(data: CostingData, 
                                 inner_radii: Dict[str, float],
                                 outer_radii: Dict[str, float]) -> Dict[str, Meters3]:
    """Compute volumes for MFE tokamak configuration.
    
    Args:
        data: CostingData
        inner_radii: Inner radii dict
        outer_radii: Outer radii dict
        
    Returns:
        Dict of component volumes [m³]
    """
    inp = data.cas220101_in
    R = inp.r_plasma  # Major radius
    elon = inp.elon   # Elongation
    
    volumes = {}
    
    # First wall
    r_fw_inner = inner_radii['first_wall_inner'] - R  # Convert to minor radius
    r_fw_outer = outer_radii['first_wall_outer'] - R
    vol_fw_base = calc_volume_outer_hollow_torus(R, r_fw_outer, r_fw_inner)
    volumes['first_wall'] = Meters3(vol_fw_base * elon)
    
    # Blanket
    r_blanket_inner = inner_radii['blanket_inner'] - R
    r_blanket_outer = outer_radii['blanket_outer'] - R
    vol_blanket_base = calc_volume_outer_hollow_torus(R, r_blanket_outer, r_blanket_inner)
    volumes['blanket'] = Meters3(vol_blanket_base * elon)
    
    # Shield
    r_shield_inner = inner_radii['shield_inner'] - R
    r_shield_outer = outer_radii['shield_outer'] - R
    vol_shield_base = calc_volume_outer_hollow_torus(R, r_shield_outer, r_shield_inner)
    volumes['shield'] = Meters3(vol_shield_base * elon)
    
    return volumes


def compute_volumes_mfe_mirror(data: CostingData,
                                inner_radii: Dict[str, float],
                                outer_radii: Dict[str, float]) -> Dict[str, Meters3]:
    """Compute volumes for MFE mirror configuration.
    
    Args:
        data: CostingData
        inner_radii: Inner radii dict
        outer_radii: Outer radii dict
        
    Returns:
        Dict of component volumes [m³]
    """
    inp = data.cas220101_in
    length = inp.chamber_length
    
    volumes = {}
    
    # First wall
    volumes['first_wall'] = Meters3(calc_volume_ring(
        length,
        inner_radii['first_wall_inner'],
        outer_radii['first_wall_outer']
    ))
    
    # Blanket
    volumes['blanket'] = Meters3(calc_volume_ring(
        length,
        inner_radii['blanket_inner'],
        outer_radii['blanket_outer']
    ))
    
    # Shield
    volumes['shield'] = Meters3(calc_volume_ring(
        length,
        inner_radii['shield_inner'],
        outer_radii['shield_outer']
    ))
    
    return volumes


def compute_volumes_ife(data: CostingData,
                        inner_radii: Dict[str, float],
                        outer_radii: Dict[str, float]) -> Dict[str, Meters3]:
    """Compute volumes for IFE configuration (spherical chamber).
    
    Args:
        data: CostingData
        inner_radii: Inner radii dict
        outer_radii: Outer radii dict
        
    Returns:
        Dict of component volumes [m³]
    """
    volumes = {}
    
    # First wall (target chamber)
    volumes['first_wall'] = Meters3(calc_volume_sphere(
        inner_radii['first_wall_inner'],
        outer_radii['first_wall_outer']
    ))
    
    # Blanket
    volumes['blanket'] = Meters3(calc_volume_sphere(
        inner_radii['blanket_inner'],
        outer_radii['blanket_outer']
    ))
    
    # Shield
    volumes['shield'] = Meters3(calc_volume_sphere(
        inner_radii['shield_inner'],
        outer_radii['shield_outer']
    ))
    
    return volumes


def compute_all_volumes(data: CostingData) -> None:
    """Compute all component volumes and store in data.volumes.
    
    Dispatches to correct geometry function based on reactor_type.
    
    Args:
        data: CostingData (modified in place)
    """
    # Compute radii
    inner_radii = compute_inner_radii(data)
    outer_radii = compute_outer_radii(data, inner_radii)
    
    # Store radii
    data.radii = {**inner_radii, **outer_radii}
    
    # Compute volumes based on reactor type
    if data.basic.reactor_type == ReactorType.MFE_TOKAMAK:
        volumes = compute_volumes_mfe_tokamak(data, inner_radii, outer_radii)
    elif data.basic.reactor_type == ReactorType.MFE_MIRROR:
        volumes = compute_volumes_mfe_mirror(data, inner_radii, outer_radii)
    elif data.basic.reactor_type == ReactorType.IFE_LASER:
        volumes = compute_volumes_ife(data, inner_radii, outer_radii)
    else:
        raise ValueError(f"Unknown reactor type: {data.basic.reactor_type}")
    
    # Store volumes
    data.volumes = volumes
