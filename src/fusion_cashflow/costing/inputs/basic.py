"""Basic input parameters for costing calculations."""
from dataclasses import dataclass, field

from ..units import MW
from ..enums_new import ReactorType, FuelType, LSALevel, Region


@dataclass
class BasicInputs:
    """Core reactor parameters for costing."""
    
    # Power parameters
    p_nrl: MW = MW(500.0)              # Net rated load (electrical output) [MWe]
    p_et: MW = MW(0.0)                 # Total thermal power (computed from power balance) [MWth]
    
    # Configuration
    n_mod: int = 1                      # Number of power core modules
    reactor_type: ReactorType = ReactorType.MFE_TOKAMAK
    fuel_type: FuelType = FuelType.DT
    
    # Regulatory & economics
    lsa_level: LSALevel = LSALevel.LSA1  # Level of Safety Assurance
    region: Region = Region.US           # Geographic region for cost scaling
    is_foak: bool = False                # First-of-a-kind (adds contingency)
    
    # Plant characteristics
    capacity_factor: float = 0.92         # Plant capacity factor (0-1)
    construction_time_years: int = 6     # Construction duration
    plant_lifetime_years: int = 40       # Design lifetime
    
    # Financial
    discount_rate: float = 0.05          # Real discount rate for LCOE
    capital_recovery_factor: float = 0.09  # CRF for annualized costs (CAS 90)
