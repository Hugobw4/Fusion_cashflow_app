"""CAS 21 (Buildings) calculations.

This module implements the 17 building cost calculations from PyFECONS,
each using the formula: Cost = k_to_m_usd(factor) × p_et × fuel_scaling
"""
from ..costing_data import CostingData
from ..units import M_USD
from .conversions import compute_cost_from_factor, apply_fuel_scaling


# Building cost factors [$/kW] from PyFECONS
BUILDING_FACTORS = {
    'C210100': 268.0,   # Reactor building
    'C210200': 186.8,   # Turbine building
    'C210300': 54.0,    # Reactor maintenance building
    'C210400': 37.8,    # Warm shop
    'C210500': 10.8,    # Tritium building
    'C210600': 5.4,     # Electrical equipment building
    'C210700': 93.4,    # Hot cell building
    'C210800': 18.7,    # Reactor service building
    'C210900': 0.3,     # Service water building
    'C211000': 1.1,     # Fuel storage building
    'C211100': 0.9,     # Control room building
    'C211200': 0.8,     # On-site AC power building
    'C211300': 4.4,     # Admin building
    'C211400': 1.6,     # Site services building
    'C211500': 2.4,     # Cryogenics building
    'C211600': 0.9,     # Security building
    'C211700': 27.0,    # Ventilation stack
}

# Buildings that get fuel scaling (0.5× for non-DT)
FUEL_SCALED_BUILDINGS = ['C210100', 'C210200', 'C210700']


def compute_cas21(data: CostingData) -> None:
    """Compute CAS 21 (Buildings and structures) costs.
    
    Updates data.cas21_out in place.
    
    Args:
        data: CostingData with basic inputs
    """
    p_et = data.basic.p_et
    fuel_type = data.basic.fuel_type.value
    is_foak = data.basic.is_foak
    
    out = data.cas21_out
    
    # Compute each building
    for code, factor in BUILDING_FACTORS.items():
        cost = compute_cost_from_factor(factor, p_et)
        
        # Apply fuel scaling if applicable
        if code in FUEL_SCALED_BUILDINGS:
            cost = apply_fuel_scaling(cost, fuel_type)
        
        # Apply user-defined scaling factors (from CAS21Inputs)
        if code == 'C210100':
            cost = M_USD(cost * data.cas21_in.reactor_building_factor)
            if data.cas21_in.reactor_building_override_musd > 0:
                cost = M_USD(data.cas21_in.reactor_building_override_musd)
        elif code == 'C210200':
            cost = M_USD(cost * data.cas21_in.turbine_building_factor)
            if data.cas21_in.turbine_building_override_musd > 0:
                cost = M_USD(data.cas21_in.turbine_building_override_musd)
        elif code == 'C210700':
            cost = M_USD(cost * data.cas21_in.hot_cell_building_factor)
        
        # Assign to output
        setattr(out, code, cost)
    
    # FOAK contingency: 10% of sum(C210100..C211700)
    if is_foak:
        subtotal = sum([getattr(out, f'C{i}') for i in range(210100, 211800, 100)])
        out.C211900 = M_USD(subtotal * 0.10)
    else:
        out.C211900 = M_USD(0.0)
    
    # Compute total
    out.compute_total()
