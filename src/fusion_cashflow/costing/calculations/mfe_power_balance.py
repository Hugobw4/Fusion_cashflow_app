"""MFE-specific power balance calculations with detailed recirculating power.

Calculates magnet power, cryogenic load, heating power, pumping power, and auxiliary
loads based on reactor configuration and magnetic field strength.
"""
from ..costing_data import CostingData
from ..units import MW
from ..enums_new import FuelType, MagnetType, ReactorType
import math


# Fusion reaction energy fractions
FUEL_FRACTIONS = {
    FuelType.DT: {'alpha': 3.52 / 17.58, 'neutron': 14.06 / 17.58},
    FuelType.DD: {'alpha': 0.5, 'neutron': 0.5},
    FuelType.DHe3: {'alpha': 0.80, 'neutron': 0.20},
    FuelType.pB11: {'alpha': 1.0, 'neutron': 0.0},
}


def estimate_magnet_power(data: CostingData) -> MW:
    """Estimate power consumption for magnets.
    
    For superconducting magnets, this is primarily charging/control losses.
    For resistive magnets, this is steady-state Joule heating.
    
    Args:
        data: CostingData with magnet configuration
        
    Returns:
        Magnet power consumption [MW]
    """
    mag_type = data.cas2203_in.magnet_type
    p_thermal = data.basic.p_et
    
    if mag_type == MagnetType.HTS:
        # HTS: very low losses, ~0.1-0.2% of thermal power for control
        return MW(p_thermal * 0.002)
    elif mag_type == MagnetType.LTS:
        # LTS: slightly higher than HTS due to more active cooling
        return MW(p_thermal * 0.003)
    elif mag_type == MagnetType.COPPER:
        # Resistive copper: substantial Joule heating, ~5-10% of thermal power
        return MW(p_thermal * 0.08)
    else:
        # Default estimate
        return MW(p_thermal * 0.005)


def estimate_cryogenic_power(data: CostingData) -> MW:
    """Estimate cryogenic system power consumption.
    
    For superconducting magnets, cryogenic cooling is significant.
    Uses Carnot efficiency to estimate compressor power.
    
    Args:
        data: CostingData with magnet configuration
        
    Returns:
        Cryogenic system power [MW]
    """
    mag_type = data.cas2203_in.magnet_type
    p_thermal = data.basic.p_et
    
    if mag_type in [MagnetType.HTS, MagnetType.LTS]:
        # Superconducting: need cryogenic cooling
        # Assume ~300W/W cooling load at 4-77K
        # Heat load scales with magnet volume/surface
        # Rough estimate: 1-2% of thermal power
        if mag_type == MagnetType.HTS:
            return MW(p_thermal * 0.01)  # HTS at 77K is less demanding
        else:
            return MW(p_thermal * 0.015)  # LTS at 4K requires more power
    else:
        # No cryogenics for resistive magnets
        return MW(0.0)


def estimate_heating_power(data: CostingData) -> MW:
    """Estimate auxiliary heating power (NBI, ECRH, ICRH).
    
    Args:
        data: CostingData with power balance inputs
        
    Returns:
        Heating power delivered to plasma [MW]
    """
    # Already specified in power_balance_in
    return data.power_balance_in.p_heating


def estimate_pumping_power(data: CostingData) -> MW:
    """Estimate coolant pumping power.
    
    Scales with thermal power and coolant system complexity.
    
    Args:
        data: CostingData
        
    Returns:
        Pumping power [MW]
    """
    p_thermal = data.basic.p_et
    
    # Primary coolant pumps: ~0.5-1% of thermal power
    # Secondary coolant pumps: ~0.3-0.5%
    # Total: ~1-1.5% of thermal power
    return MW(p_thermal * 0.012)


def estimate_auxiliary_power(data: CostingData) -> MW:
    """Estimate auxiliary loads (control, diagnostics, tritium).
    
    Args:
        data: CostingData
        
    Returns:
        Auxiliary power [MW]
    """
    p_thermal = data.basic.p_et
    
    # Control systems, diagnostics, tritium breeding, vacuum, etc.
    # Typically 2-3% of thermal power
    return MW(p_thermal * 0.025)


def compute_mfe_recirculating_power(data: CostingData) -> MW:
    """Compute total MFE recirculating power from components.
    
    Args:
        data: CostingData
        
    Returns:
        Total recirculating power [MW]
    """
    p_magnets = estimate_magnet_power(data)
    p_cryo = estimate_cryogenic_power(data)
    p_heating = estimate_heating_power(data)
    p_pumps = estimate_pumping_power(data)
    p_aux = estimate_auxiliary_power(data)
    
    # Store components in power_balance_in for reference
    data.power_balance_in.p_magnets = p_magnets
    data.power_balance_in.p_cryo = p_cryo
    data.power_balance_in.p_pumps = p_pumps
    data.power_balance_in.p_aux = p_aux
    
    total = MW(p_magnets + p_cryo + p_heating + p_pumps + p_aux)
    
    return total


def compute_power_balance_mfe_detailed(data: CostingData) -> None:
    """Compute detailed MFE power balance with component-level recirculating power.
    
    Updates data.power_balance_out in place.
    
    Args:
        data: CostingData with power balance inputs
    """
    inp = data.power_balance_in
    fuel = data.basic.fuel_type
    out = data.power_balance_out
    
    # === Fusion Power ===
    p_fusion = MW(inp.q_plasma * inp.p_heating)
    out.p_fusion = p_fusion
    
    # Split into alpha and neutron
    fractions = FUEL_FRACTIONS.get(fuel, FUEL_FRACTIONS[FuelType.DT])
    p_alpha = MW(p_fusion * fractions['alpha'])
    p_neutron = MW(p_fusion * fractions['neutron'])
    
    out.p_alpha = p_alpha
    out.p_neutron = p_neutron
    
    # === Neutron Multiplication ===
    p_neutron_wall = MW(p_neutron * inp.neutron_multiplication)
    
    # === Total Thermal Power ===
    p_thermal = MW(p_neutron_wall + p_alpha + inp.p_heating)
    out.p_thermal = p_thermal
    data.basic.p_et = p_thermal
    
    # === Gross Electric Power ===
    p_electric_gross = MW(p_thermal * inp.eta_th)
    out.p_electric_gross = p_electric_gross
    out.eta_th = inp.eta_th
    
    # === Detailed Recirculating Power ===
    p_recirc = compute_mfe_recirculating_power(data)
    out.p_recirculating = p_recirc
    
    # === Net Electric Power ===
    p_net = MW(p_electric_gross - p_recirc)
    out.p_net = p_net
    data.basic.p_nrl = p_net
    
    # === Engineering Q ===
    if p_recirc > 0:
        out.q_eng = p_net / p_recirc
    else:
        out.q_eng = 0.0
