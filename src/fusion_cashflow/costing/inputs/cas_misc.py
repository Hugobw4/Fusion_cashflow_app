"""CAS 23-90 (misc systems) input parameters."""
from dataclasses import dataclass


@dataclass
class CAS23Inputs:
    """CAS 23 - Turbine plant equipment."""
    pass  # Computed via $/kW × p_et formula


@dataclass
class CAS24Inputs:
    """CAS 24 - Electric plant equipment."""
    pass  # Computed via $/kW × p_et formula


@dataclass
class CAS25Inputs:
    """CAS 25 - Miscellaneous plant equipment."""
    pass  # Computed via $/kW × p_et formula


@dataclass
class CAS26Inputs:
    """CAS 26 - Heat rejection system."""
    pass  # Computed via $/kW × p_et formula


@dataclass
class CAS27Inputs:
    """CAS 27 - Fuel handling and storage."""  
    pass  # Computed via $/kW × p_et formula with fuel scaling


@dataclass
class CAS28Inputs:
    """CAS 28 - Instrumentation and control."""
    pass  # Computed via $/kW × p_et formula


@dataclass
class CAS29Inputs:
    """CAS 29 - Contingency."""
    pass  # Computed as percentage of CAS 21-28


@dataclass
class CAS30Inputs:
    """CAS 30 - Indirect costs (construction services)."""
    construction_services_factor: float = 0.22  # Factor 92 for indirect


@dataclass
class CAS40Inputs:
    """CAS 40 - Owner costs."""
    pass  # Computed from LSA level


@dataclass
class CAS50Inputs:
    """CAS 50 - Capitalized supplementary costs."""
    supplementary_cost_musd: float = 0.0  # Additional capitalized costs [M$]


@dataclass
class CAS60Inputs:
    """CAS 60 - Capitalized O&M (spares, initial inventory)."""
    spares_cost_musd: float = 50.0  # Cost of spare parts [M$]


@dataclass
class CAS70Inputs:
    """CAS 70 - Annualized O&M costs."""
    pass  # Computed via 60 × p_net × 1000 / 1e6


@dataclass
class CAS80Inputs:
    """CAS 80 - Annualized fuel costs."""
    dt_fuel_cost_per_kg: float = 10000.0  # Tritium cost [$/kg]
    annual_fuel_burn_kg: float = 150.0     # Annual fuel consumption [kg]


@dataclass
class CAS90Inputs:
    """CAS 90 - Annualized financial costs."""
    pass  # Computed via CRF × TCC
