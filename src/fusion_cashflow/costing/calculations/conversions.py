"""Unit conversion helpers for costing calculations."""
from ..units import M_USD, MW


def k_to_m_usd(k_factor: float) -> float:
    """Convert $/kW factor to M$/MW (equiv: divide by 1000).
    
    PyFECONS uses $/kW factors that need to be converted to M$ when
    multiplied by thermal power in MW.
    
    Args:
        k_factor: Cost factor in $/kW
        
    Returns:
        Factor to multiply by MW to get M$
        
    Example:
        >>> # Building cost: 268 $/kW × 2000 MW = 536 M$
        >>> k_to_m_usd(268.0) * 2000
        536.0
    """
    return k_factor / 1000.0


def compute_cost_from_factor(k_factor: float, power_mw: MW) -> M_USD:
    """Compute cost from $/kW factor and power.
    
    Args:
        k_factor: Cost factor in $/kW
        power_mw: Power in MW
        
    Returns:
        Cost in M$
    """
    return M_USD(k_to_m_usd(k_factor) * power_mw)


def apply_fuel_scaling(cost: M_USD, fuel_type: str) -> M_USD:
    """Apply fuel scaling factor to cost.
    
    Non-DT fuels (DD, DHe3, pB11) have reduced tritium handling needs,
    so certain buildings (reactor, turbine, hot cell) get 0.5× scaling.
    
    Args:
        cost: Base cost [M$]
        fuel_type: Fuel type ("DT", "DD", "DHe3", "pB11")
        
    Returns:
        Scaled cost [M$]
    """
    if fuel_type == "DT":
        return cost
    else:
        # Non-DT fuels: 0.5× scaling
        return M_USD(cost * 0.5)
