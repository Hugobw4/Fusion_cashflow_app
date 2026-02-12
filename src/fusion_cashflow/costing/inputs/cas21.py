"""CAS 21 (Buildings) input parameters."""
from dataclasses import dataclass


@dataclass
class CAS21Inputs:
    """Buildings and structures inputs.
    
    Most CAS 21 costs are computed via $/kW factors × p_et,
    but this dataclass allows for overrides if needed.
    """
    
    # Scaling factors (default = 1.0, no override)
    reactor_building_factor: float = 1.0     # Multiplier for C210100
    turbine_building_factor: float = 1.0     # Multiplier for C210200
    hot_cell_building_factor: float = 1.0    # Multiplier for C210700
    
    # Custom overrides (if not None, bypasses $/kW formula)
    reactor_building_override_musd: float = 0.0  # If > 0, use this instead
    turbine_building_override_musd: float = 0.0
