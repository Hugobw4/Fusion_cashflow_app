"""CAS 10 (Pre-construction) input parameters."""
from dataclasses import dataclass

from ..units import M_USD


@dataclass
class CAS10Inputs:
    """Pre-construction costs."""
    
    # Land and site prep
    land_cost: M_USD = M_USD(10.0)           # Land acquisition [M$]
    site_prep_cost: M_USD = M_USD(50.0)      # Site preparation [M$]
    
    # Regulatory & permitting
    permits_cost: M_USD = M_USD(20.0)        # Permits and licenses [M$]
    environmental_cost: M_USD = M_USD(15.0)  # Environmental studies [M$]
    
    # Engineering & design
    conceptual_design_cost: M_USD = M_USD(30.0)   # Conceptual design [M$]
    preliminary_design_cost: M_USD = M_USD(50.0)  # Preliminary design [M$]
