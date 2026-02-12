"""CAS 23-90 output dataclasses."""
from dataclasses import dataclass

from ..units import M_USD, MW


@dataclass
class CAS23Output:
    """CAS 23 - Turbine plant equipment."""
    C230000: M_USD = M_USD(0.0)  # TOTAL CAS 23


@dataclass
class CAS24Output:
    """CAS 24 - Electric plant equipment."""
    C240000: M_USD = M_USD(0.0)  # TOTAL CAS 24


@dataclass
class CAS25Output:
    """CAS 25 - Miscellaneous plant equipment."""
    C250000: M_USD = M_USD(0.0)  # TOTAL CAS 25


@dataclass
class CAS26Output:
    """CAS 26 - Heat rejection system."""
    C260000: M_USD = M_USD(0.0)  # TOTAL CAS 26


@dataclass
class CAS27Output:
    """CAS 27 - Fuel handling and storage."""
    C270000: M_USD = M_USD(0.0)  # TOTAL CAS 27


@dataclass
class CAS28Output:
    """CAS 28 - Instrumentation and control."""
    C280000: M_USD = M_USD(0.0)  # TOTAL CAS 28


@dataclass
class CAS29Output:
    """CAS 29 - Contingency."""
    C290000: M_USD = M_USD(0.0)  # TOTAL CAS 29


@dataclass
class CAS30Output:
    """CAS 30 - Indirect costs (construction services)."""
    C300000: M_USD = M_USD(0.0)  # TOTAL CAS 30


@dataclass
class CAS40Output:
    """CAS 40 - Owner costs."""
    C400000: M_USD = M_USD(0.0)  # TOTAL CAS 40


@dataclass
class CAS50Output:
    """CAS 50 - Capitalized supplementary costs."""
    C500000: M_USD = M_USD(0.0)  # TOTAL CAS 50


@dataclass
class CAS60Output:
    """CAS 60 - Capitalized O&M (spares, initial inventory)."""
    C600000: M_USD = M_USD(0.0)  # TOTAL CAS 60


@dataclass
class CAS70Output:
    """CAS 70 - Annualized O&M costs."""
    C700000: M_USD = M_USD(0.0)  # Annual O&M [M$/yr]


@dataclass
class CAS80Output:
    """CAS 80 - Annualized fuel costs."""
    C800000: M_USD = M_USD(0.0)  # Annual fuel [M$/yr]


@dataclass
class CAS90Output:
    """CAS 90 - Annualized financial costs."""
    C900000: M_USD = M_USD(0.0)  # Annual financial [M$/yr]


@dataclass
class LCOEOutput:
    """Levelized Cost of Electricity."""
    lcoe_usd_per_mwh: float = 0.0  # LCOE [$/MWh]
    
    # Breakdown
    capital_component: float = 0.0   # Capital contribution to LCOE [$/MWh]
    om_component: float = 0.0        # O&M contribution to LCOE [$/MWh]
    fuel_component: float = 0.0      # Fuel contribution to LCOE [$/MWh]


@dataclass
class PowerBalanceOutput:
    """Power balance outputs."""
    
    p_fusion: MW = MW(0.0)          # Fusion power [MW]
    p_neutron: MW = MW(0.0)         # Neutron power [MW]
    p_alpha: MW = MW(0.0)           # Alpha power [MW]
    p_thermal: MW = MW(0.0)         # Total thermal power [MW]
    p_electric_gross: MW = MW(0.0)  # Gross electric [MW]
    p_recirculating: MW = MW(0.0)   # Recirculating power [MW]
    p_net: MW = MW(0.0)             # Net electric [MW]
    q_eng: float = 0.0              # Engineering Q
    eta_th: float = 0.0             # Thermal efficiency
