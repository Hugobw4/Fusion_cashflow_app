"""CAS 22.03 - Magnet Systems (Material-Based Costing).

Comprehensive magnet costing based on conductor material, field strength, and geometry.
Replaces simplified $/kW estimate with physics-based material quantities.
"""
from ..costing_data import CostingData
from ..units import M_USD, MW, Meters
from ..materials_new import get_material
from ..enums_new import MagnetType, ReactorType
import math


def compute_magnet_volume_tokamak(data: CostingData) -> dict:
    """Compute magnet conductor volumes for tokamak.
    
    Args:
        data: CostingData with geometry and magnet config
        
    Returns:
        Dict with TF, PF, CS conductor volumes [m³]
    """
    geom = data.cas220101_in
    mag_in = data.cas2203_in
    
    # Get radii from volume calculation
    r_plasma = geom.r_plasma
    a_plasma = geom.a_plasma
    
    # Outer radius of vacuum vessel + gap (approximate coil inner bore)
    r_inner_coil = data.radii.get('vessel_outer', r_plasma + a_plasma + 3.0)
    
    # TF coil parameters
    n_tf = mag_in.n_tf_coils
    r_outer_coil = r_inner_coil + mag_in.coil_radial_thickness
    
    # TF coil D-shape approximation
    # Use toroidal length formula: L = 2π × (R + a_coil) for one coil
    # Height: ~2 × plasma_height × 1.2 (margin)
    plasma_height = a_plasma * geom.elon
    coil_height = plasma_height * 1.4  # 40% margin
    
    # Cross-section area of one TF coil
    coil_cross_section = mag_in.coil_radial_thickness * coil_height
    
    # Toroidal circumference at average radius
    r_avg = (r_inner_coil + r_outer_coil) / 2.0
    toroidal_length = 2 * math.pi * r_avg
    
    # Total conductor volume per coil (assuming conductor is ~40% of coil volume)
    conductor_fraction = 0.40  # Rest is insulation, structure, cooling
    vol_per_coil = coil_cross_section * toroidal_length * conductor_fraction
    vol_tf_total = vol_per_coil * n_tf
    
    # PF coils (approximate as ~30% of TF volume)
    vol_pf = vol_tf_total * 0.30
    
    # Central solenoid (approximate as ~15% of TF volume)
    vol_cs = vol_tf_total * 0.15
    
    return {
        'tf': vol_tf_total,
        'pf': vol_pf,
        'cs': vol_cs,
        'total': vol_tf_total + vol_pf + vol_cs
    }


def compute_magnet_volume_mirror(data: CostingData) -> dict:
    """Compute magnet conductor volumes for mirror reactor.
    
    Args:
        data: CostingData with geometry and magnet config
        
    Returns:
        Dict with solenoid and mirror coil conductor volumes [m³]
    """
    geom = data.cas220101_in
    mag_in = data.cas2203_in
    
    # Mirror uses solenoidal coils + mirror throat coils
    chamber_length = geom.chamber_length
    r_chamber = geom.r_plasma  # Reuse as chamber radius
    
    # Solenoid coils (cylindrical)
    n_solenoid = 20  # Typical number of solenoidal coils
    coil_thickness = mag_in.coil_radial_thickness
    r_coil = r_chamber + 1.0  # 1m gap
    coil_spacing = chamber_length / n_solenoid
    conductor_fraction = 0.40
    
    # Volume per solenoid coil (toroidal ring)
    vol_per_solenoid = 2 * math.pi * r_coil * coil_thickness * 0.3 * conductor_fraction
    vol_solenoid = vol_per_solenoid * n_solenoid
    
    # Mirror throat coils (2 high-field coils at ends)
    vol_mirror = vol_solenoid * 0.5
    
    return {
        'solenoid': vol_solenoid,
        'mirror': vol_mirror,
        'total': vol_solenoid + vol_mirror
    }


def compute_magnet_material_cost(volume_m3: float, magnet_type: MagnetType) -> M_USD:
    """Compute magnet conductor cost from volume and type.
    
    Args:
        volume_m3: Conductor volume [m³]
        magnet_type: HTS, LTS, or Copper
        
    Returns:
        Material cost [M$]
    """
    if magnet_type == MagnetType.HTS:
        # YBCO tape cost
        mat = get_material('YBCO')
        # HTS is tape-based, more expensive per volume
        cost = mat.volume_cost_m_usd(volume_m3) * 5.0  # 5x multiplier for tape form factor
    elif magnet_type == MagnetType.LTS:
        # Nb3Sn or NbTi
        mat = get_material('Nb3Sn')
        cost = mat.volume_cost_m_usd(volume_m3) * 2.0  # 2x multiplier for cable
    elif magnet_type == MagnetType.COPPER:
        # Pure copper resistive magnets
        mat = get_material('Cu')
        cost = mat.volume_cost_m_usd(volume_m3) * 1.5  # 1.5x for large conductor
    else:
        # Fallback
        cost = M_USD(volume_m3 * 100.0)  # $100M per m³ assumption
    
    return cost


def compute_magnet_structure_cost(conductor_cost: M_USD) -> M_USD:
    """Compute magnet structure, casing, and support cost.
    
    Structure cost scales with conductor cost.
    
    Args:
        conductor_cost: Conductor material cost [M$]
        
    Returns:
        Structure cost [M$]
    """
    # Structure, dewars, supports: ~50% of conductor cost
    return M_USD(conductor_cost * 0.50)


def compute_cryogenic_cost(data: CostingData, is_superconducting: bool) -> M_USD:
    """Compute cryogenic system cost.
    
    Args:
        data: CostingData
        is_superconducting: True for HTS/LTS, False for copper
        
    Returns:
        Cryogenic plant cost [M$]
    """
    if not is_superconducting:
        return M_USD(0.0)  # No cryo for resistive magnets
    
    p_et = data.basic.p_et
    
    # Cryo plant scales with thermal power (proxy for magnet power/cooling load)
    # Typical: $10-20M per 100 MW thermal
    cost = M_USD(p_et / 100.0 * 15.0)
    
    return cost


def compute_cas220103(data: CostingData) -> None:
    """CAS 22.03 - Magnet systems (material-based).
    
    Computes magnet costs based on:
    - Reactor type (tokamak, mirror, IFE)
    - Magnet type (HTS, LTS, Copper)
    - Geometry-derived conductor volumes
    - Material costs from database
    
    Updates data.cas22_out.cas2203 in place.
    
    Args:
        data: CostingData with magnet configuration
    """
    mag_in = data.cas2203_in
    reactor_type = data.basic.reactor_type
    magnet_type = mag_in.magnet_type
    out = data.cas22_out.cas2203
    
    # IFE has no magnets
    if reactor_type == ReactorType.IFE_LASER:
        out.C220300 = M_USD(0.0)
        out.C22030301 = M_USD(0.0)  # TF coils
        out.C22030302 = M_USD(0.0)  # PF coils  
        out.C22030303 = M_USD(0.0)  # CS
        out.C22030304 = M_USD(0.0)  # Structure
        out.C22030305 = M_USD(0.0)  # Cryostat
        out.C22030306 = M_USD(0.0)  # Cryo plant
        return
    
    # Compute conductor volumes based on reactor type
    if reactor_type == ReactorType.MFE_TOKAMAK:
        volumes = compute_magnet_volume_tokamak(data)
        vol_tf = volumes['tf']
        vol_pf = volumes['pf']
        vol_cs = volumes['cs']
    elif reactor_type == ReactorType.MFE_MIRROR:
        volumes = compute_magnet_volume_mirror(data)
        vol_tf = volumes['solenoid']
        vol_pf = volumes['mirror'] 
        vol_cs = 0.0  # No central solenoid in mirror
    else:
        # Fallback
        vol_tf = 50.0  # m³
        vol_pf = 15.0
        vol_cs = 7.5
    
    # Compute material costs
    cost_tf = compute_magnet_material_cost(vol_tf, magnet_type)
    cost_pf = compute_magnet_material_cost(vol_pf, magnet_type)
    cost_cs = compute_magnet_material_cost(vol_cs, magnet_type)
    
    # Structure cost (casing, supports)
    cost_conductor_total = cost_tf + cost_pf + cost_cs
    cost_structure = compute_magnet_structure_cost(cost_conductor_total)
    
    # Cryogenic system
    is_superconducting = magnet_type in [MagnetType.HTS, MagnetType.LTS]
    cost_cryo_plant = compute_cryogenic_cost(data, is_superconducting)
    cost_cryostat = M_USD(cost_cryo_plant * 0.30) if is_superconducting else M_USD(0.0)
    
    # Assign to output
    out.C22030301 = cost_tf
    out.C22030302 = cost_pf
    out.C22030303 = cost_cs
    out.C22030304 = cost_structure
    out.C22030305 = cost_cryostat
    out.C22030306 = cost_cryo_plant
    
    # Total
    out.C220300 = M_USD(
        cost_tf + cost_pf + cost_cs + cost_structure + cost_cryostat + cost_cryo_plant
    )
