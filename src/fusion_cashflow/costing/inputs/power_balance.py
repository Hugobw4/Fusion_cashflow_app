"""Power balance input parameters."""
from dataclasses import dataclass

from ..units import MW


@dataclass
class PowerBalanceInputs:
    """Inputs for computing power flow through the reactor."""
    
    # Plasma physics
    q_plasma: float = 10.0              # Plasma Q (fusion power / heating power)
    p_heating: MW = MW(50.0)            # External heating power [MW]
    
    # Neutron multiplication
    neutron_multiplication: float = 1.15  # Blanket neutron multiplication factor (mn)
    
    # Thermal efficiency
    eta_th: float = 0.40                # Gross thermal-to-electric efficiency
    
    # Recirculating power estimates (MFE)
    p_magnets: MW = MW(0.0)             # Magnet system power (computed from CAS 22.03)
    p_cryo: MW = MW(20.0)               # Cryogenic system power
    p_pumps: MW = MW(10.0)              # Coolant pumping power
    p_aux: MW = MW(15.0)                # Auxiliary systems power
    
    # IFE-specific
    driver_efficiency: float = 0.10      # Laser/driver efficiency (IFE only)
    target_yield_mj: float = 500.0       # Target fusion yield [MJ] (IFE only)
    rep_rate_hz: float = 10.0            # Repetition rate [Hz] (IFE only)
