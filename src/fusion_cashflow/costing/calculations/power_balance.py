"""Power balance calculations for fusion reactors.

Dispatches to reactor-specific modules for detailed calculations.
Legacy compute_power_balance_mfe/ife retained for backward compatibility.
"""
from ..costing_data import CostingData
from ..units import MW
from ..enums_new import FuelType, ReactorType

# Import detailed calculation modules
try:
    from .mfe_power_balance import compute_power_balance_mfe_detailed
    from .ife_power_balance import compute_power_balance_ife_detailed
    USE_DETAILED_CALCULATIONS = True
except ImportError:
    USE_DETAILED_CALCULATIONS = False


# Fusion reaction energy fractions for DT fuel
DT_ALPHA_FRACTION = 3.52 / 17.58      # Alpha particle energy
DT_NEUTRON_FRACTION = 14.06 / 17.58   # Neutron energy

# Other fuel types (simplified - would need proper physics)
FUEL_FRACTIONS = {
    FuelType.DT: {'alpha': DT_ALPHA_FRACTION, 'neutron': DT_NEUTRON_FRACTION},
    FuelType.DD: {'alpha': 0.5, 'neutron': 0.5},  # Simplified
    FuelType.DHe3: {'alpha': 0.80, 'neutron': 0.20},  # Mainly charged products
    FuelType.pB11: {'alpha': 1.0, 'neutron': 0.0},  # Aneutronic
}


def compute_power_balance_mfe(data: CostingData) -> None:
    """Compute power balance for MFE reactor.
    
    Updates data.power_balance_out in place.
    
    Args:
        data: CostingData with power balance inputs
    """
    inp = data.power_balance_in
    fuel = data.basic.fuel_type
    
    out = data.power_balance_out
    
    # Fusion power from Q_plasma
    p_fusion = MW(inp.q_plasma * inp.p_heating)
    out.p_fusion = p_fusion
    
    # Split into alpha and neutron
    fractions = FUEL_FRACTIONS.get(fuel, FUEL_FRACTIONS[FuelType.DT])
    p_alpha = MW(p_fusion * fractions['alpha'])
    p_neutron = MW(p_fusion * fractions['neutron'])
    
    out.p_alpha = p_alpha
    out.p_neutron = p_neutron
    
    # Neutron multiplication in blanket
    p_neutron_wall = MW(p_neutron * inp.neutron_multiplication)
    
    # Total thermal power
    p_thermal = MW(p_neutron_wall + p_alpha + inp.p_heating)
    out.p_thermal = p_thermal
    
    # Update basic.p_et
    data.basic.p_et = p_thermal
    
    # Gross electric
    p_electric_gross = MW(p_thermal * inp.eta_th)
    out.p_electric_gross = p_electric_gross
    out.eta_th = inp.eta_th
    
    # Recirculating power
    p_recirc = MW(inp.p_magnets + inp.p_cryo + inp.p_heating + inp.p_pumps + inp.p_aux)
    out.p_recirculating = p_recirc
    
    # Net electric
    p_net = MW(p_electric_gross - p_recirc)
    out.p_net = p_net
    
    # Update basic.p_nrl
    data.basic.p_nrl = p_net
    
    # Engineering Q
    if p_recirc > 0:
        out.q_eng = p_net / p_recirc
    else:
        out.q_eng = 0.0


def compute_power_balance_ife(data: CostingData) -> None:
    """Compute power balance for IFE reactor.
    
    Updates data.power_balance_out in place.
    
    Args:
        data: CostingData with power balance inputs
    """
    inp = data.power_balance_in
    
    out = data.power_balance_out
    
    # Fusion power from target yield × rep rate
    p_fusion_mw = (inp.target_yield_mj * inp.rep_rate_hz) / 1.0  # MJ/s = MW
    out.p_fusion = MW(p_fusion_mw)
    
    # Thermal power (assume some multiplication)
    p_thermal = MW(p_fusion_mw * inp.neutron_multiplication)
    out.p_thermal = p_thermal
    data.basic.p_et = p_thermal
    
    # Gross electric
    p_electric_gross = MW(p_thermal * inp.eta_th)
    out.p_electric_gross = p_electric_gross
    out.eta_th = inp.eta_th
    
    # Driver power
    p_driver = MW(p_fusion_mw / inp.driver_efficiency)
    
    # Recirculating power
    p_recirc = MW(p_driver + inp.p_aux)
    out.p_recirculating = p_recirc
    
    # Net electric
    p_net = MW(p_electric_gross - p_recirc)
    out.p_net = p_net
    data.basic.p_nrl = p_net
    
    # Engineering Q
    if p_recirc > 0:
        out.q_eng = p_net / p_recirc
    else:
        out.q_eng = 0.0


def compute_power_balance(data: CostingData) -> None:
    """Compute power balance (dispatch to MFE or IFE).
    
    Uses detailed reactor-specific calculations when available.
    
    Args:
        data: CostingData
    """
    if data.basic.reactor_type in [ReactorType.MFE_TOKAMAK, ReactorType.MFE_MIRROR]:
        if USE_DETAILED_CALCULATIONS:
            compute_power_balance_mfe_detailed(data)
        else:
            compute_power_balance_mfe(data)
    elif data.basic.reactor_type == ReactorType.IFE_LASER:
        if USE_DETAILED_CALCULATIONS:
            compute_power_balance_ife_detailed(data)
        else:
            compute_power_balance_ife(data)
    else:
        raise ValueError(f"Unknown reactor type: {data.basic.reactor_type}")
