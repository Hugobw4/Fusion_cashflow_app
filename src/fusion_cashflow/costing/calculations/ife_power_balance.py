"""IFE-specific power balance calculations.

Handles laser/ion beam driver efficiency, target yield, and repetition rate.
Includes driver costing for laser amplifiers and target factory costing.
"""
from ..costing_data import CostingData
from ..units import MW, M_USD
from ..enums_new import FuelType
import math


# Fusion reaction energy fractions (same as MFE)
FUEL_FRACTIONS = {
    FuelType.DT: {'alpha': 3.52 / 17.58, 'neutron': 14.06 / 17.58},
    FuelType.DD: {'alpha': 0.5, 'neutron': 0.5},
    FuelType.DHe3: {'alpha': 0.80, 'neutron': 0.20},
    FuelType.pB11: {'alpha': 1.0, 'neutron': 0.0},
}


def compute_power_balance_ife_detailed(data: CostingData) -> None:
    """Compute detailed IFE power balance.
    
    IFE uses target_yield_mj [MJ/shot], rep_rate_hz [Hz], and driver_efficiency.
    Driver power = p_fusion / (driver_efficiency * G)
    where G = target_yield / driver_energy
    
    Updates data.power_balance_out in place.
    
    Args:
        data: CostingData with IFE-specific inputs
    """
    inp = data.power_balance_in
    fuel = data.basic.fuel_type
    out = data.power_balance_out
    
    # === Target Yield ===
    # target_yield_mj [MJ/shot] × rep_rate_hz [Hz] = fusion power [MW]
    p_fusion = MW(inp.target_yield_mj * inp.rep_rate_hz)
    out.p_fusion = p_fusion
    
    # Split into alpha and neutron
    fractions = FUEL_FRACTIONS.get(fuel, FUEL_FRACTIONS[FuelType.DT])
    p_alpha = MW(p_fusion * fractions['alpha'])
    p_neutron = MW(p_fusion * fractions['neutron'])
    
    out.p_alpha = p_alpha
    out.p_neutron = p_neutron
    
    # === Neutron Multiplication ===
    p_neutron_wall = MW(p_neutron * inp.neutron_multiplication)
    
    # === Driver Power ===
    # Target gain G = target_yield / driver_energy
    # For typical IFE: G ~ 50-100, driver_efficiency ~ 5-15%
    # driver_energy [MJ] = target_yield / G
    # p_driver = driver_energy × rep_rate / driver_efficiency
    
    # Simple model: p_driver scales inversely with driver_efficiency
    # Assume target gain G embedded in p_heating specification
    p_driver = MW(inp.p_heating / inp.driver_efficiency)
    
    # === Total Thermal Power ===
    # IFE: neutrons deposit in blanket, alphas absorbed in chamber
    p_thermal = MW(p_neutron_wall + p_alpha)
    out.p_thermal = p_thermal
    data.basic.p_et = p_thermal
    
    # === Gross Electric Power ===
    p_electric_gross = MW(p_thermal * inp.eta_th)
    out.p_electric_gross = p_electric_gross
    out.eta_th = inp.eta_th
    
    # === Recirculating Power ===
    # IFE: driver power + pumps + aux
    p_pumps = MW(p_thermal * 0.012)  # 1.2% for coolant pumps
    p_aux = MW(p_thermal * 0.025)    # 2.5% for auxiliary systems
    
    p_recirc = MW(p_driver + p_pumps + p_aux)
    out.p_recirculating = p_recirc
    
    # Store components
    inp.p_magnets = MW(0.0)  # No magnets in IFE
    inp.p_cryo = MW(0.0)     # No cryogenics
    inp.p_heating = p_driver
    inp.p_pumps = p_pumps
    inp.p_aux = p_aux
    
    # === Net Electric Power ===
    p_net = MW(p_electric_gross - p_recirc)
    out.p_net = p_net
    data.basic.p_nrl = p_net
    
    # === Engineering Q ===
    if p_recirc > 0:
        out.q_eng = p_net / p_recirc
    else:
        out.q_eng = 0.0


def compute_ife_driver_cost(data: CostingData) -> M_USD:
    """Compute IFE driver system cost (CAS 22.02).
    
    Laser drivers: amplifiers, optics, beam transport
    Ion drivers: accelerator stages, beam transport
    
    Args:
        data: CostingData with driver parameters
        
    Returns:
        Driver cost [M$]
    """
    inp = data.power_balance_in
    
    # Driver energy [MJ] = target_yield / target_gain
    # Assume target_gain encoded in p_heating
    driver_energy_mj = inp.p_heating  # Rough proxy
    
    # Laser driver cost scaling: ~$1000/J delivered
    # Includes amplifiers, optics, beam control
    cost_per_joule = 0.001  # M$/J = $1000/J
    driver_cost = M_USD(driver_energy_mj * 1e6 * cost_per_joule * inp.rep_rate_hz**0.3)
    
    # Scale with driver efficiency (less efficient = bigger driver = more cost)
    efficiency_factor = 0.1 / inp.driver_efficiency  # Normalized to 10%
    driver_cost = M_USD(driver_cost * efficiency_factor)
    
    return driver_cost


def compute_ife_target_factory_cost(data: CostingData) -> M_USD:
    """Compute IFE target factory cost (CAS 22.04 override).
    
    IFE requires continuous target production at rep_rate_hz.
    
    Args:
        data: CostingData with rep_rate_hz
        
    Returns:
        Target factory cost [M$]
    """
    inp = data.power_balance_in
    
    # Target production scales with rep_rate_hz
    # Baseline: $100M for 10 Hz facility
    baseline_cost = 100.0  # M$
    baseline_rate = 10.0   # Hz
    
    cost = M_USD(baseline_cost * (inp.rep_rate_hz / baseline_rate)**0.7)
    
    return cost
