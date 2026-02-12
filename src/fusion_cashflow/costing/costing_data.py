"""Master costing data container.

This module provides the CostingData dataclass that holds all inputs and outputs
for a complete PyFECONS costing calculation.
"""
from dataclasses import dataclass, field
from typing import Dict

from .units import M_USD, Meters3
from .inputs.basic import BasicInputs
from .inputs.power_balance import PowerBalanceInputs
from .inputs.cas10 import CAS10Inputs
from .inputs.cas21 import CAS21Inputs
from .inputs.cas220101 import CAS220101Inputs
from .inputs.cas2203 import CAS2203Inputs
from .inputs.cas2202 import CAS2202Inputs
from .inputs.cas_misc import (
    CAS23Inputs, CAS24Inputs, CAS25Inputs, CAS26Inputs,
    CAS27Inputs, CAS28Inputs, CAS29Inputs, CAS30Inputs,
    CAS40Inputs, CAS50Inputs, CAS60Inputs, CAS70Inputs,
    CAS80Inputs, CAS90Inputs
)
from .categories.cas10 import CAS10Output
from .categories.cas21 import CAS21Output
from .categories.cas22 import CAS22Output
from .categories.cas_outputs import (
    CAS23Output, CAS24Output, CAS25Output, CAS26Output,
    CAS27Output, CAS28Output, CAS29Output, CAS30Output,
    CAS40Output, CAS50Output, CAS60Output, CAS70Output,
    CAS80Output, CAS90Output, LCOEOutput, PowerBalanceOutput
)


@dataclass
class CostingData:
    """Master container for all costing inputs and outputs.
    
    This dataclass holds:
    - All input parameters (basic, power balance, and per-CAS inputs)
    - All output results (per-CAS costs, power balance, LCOE)
    - Intermediate calculations (volumes, radii, etc.)
    """
    
    # ========== INPUTS ==========
    basic: BasicInputs = field(default_factory=BasicInputs)
    power_balance_in: PowerBalanceInputs = field(default_factory=PowerBalanceInputs)
    
    # CAS-specific inputs
    cas10_in: CAS10Inputs = field(default_factory=CAS10Inputs)
    cas21_in: CAS21Inputs = field(default_factory=CAS21Inputs)
    cas220101_in: CAS220101Inputs = field(default_factory=CAS220101Inputs)
    cas2202_in: CAS2202Inputs = field(default_factory=CAS2202Inputs)
    cas2203_in: CAS2203Inputs = field(default_factory=CAS2203Inputs)
    cas23_in: CAS23Inputs = field(default_factory=CAS23Inputs)
    cas24_in: CAS24Inputs = field(default_factory=CAS24Inputs)
    cas25_in: CAS25Inputs = field(default_factory=CAS25Inputs)
    cas26_in: CAS26Inputs = field(default_factory=CAS26Inputs)
    cas27_in: CAS27Inputs = field(default_factory=CAS27Inputs)
    cas28_in: CAS28Inputs = field(default_factory=CAS28Inputs)
    cas29_in: CAS29Inputs = field(default_factory=CAS29Inputs)
    cas30_in: CAS30Inputs = field(default_factory=CAS30Inputs)
    cas40_in: CAS40Inputs = field(default_factory=CAS40Inputs)
    cas50_in: CAS50Inputs = field(default_factory=CAS50Inputs)
    cas60_in: CAS60Inputs = field(default_factory=CAS60Inputs)
    cas70_in: CAS70Inputs = field(default_factory=CAS70Inputs)
    cas80_in: CAS80Inputs = field(default_factory=CAS80Inputs)
    cas90_in: CAS90Inputs = field(default_factory=CAS90Inputs)
    
    # ========== INTERMEDIATE CALCULATIONS ==========
    # Geometry (computed by volume.py)
    volumes: Dict[str, Meters3] = field(default_factory=dict)
    radii: Dict[str, float] = field(default_factory=dict)
    
    # Power balance (computed by power_balance.py)
    power_balance_out: PowerBalanceOutput = field(default_factory=PowerBalanceOutput)
    
    # ========== OUTPUTS ==========
    cas10_out: CAS10Output = field(default_factory=CAS10Output)
    cas21_out: CAS21Output = field(default_factory=CAS21Output)
    cas22_out: CAS22Output = field(default_factory=CAS22Output)
    cas23_out: CAS23Output = field(default_factory=CAS23Output)
    cas24_out: CAS24Output = field(default_factory=CAS24Output)
    cas25_out: CAS25Output = field(default_factory=CAS25Output)
    cas26_out: CAS26Output = field(default_factory=CAS26Output)
    cas27_out: CAS27Output = field(default_factory=CAS27Output)
    cas28_out: CAS28Output = field(default_factory=CAS28Output)
    cas29_out: CAS29Output = field(default_factory=CAS29Output)
    cas30_out: CAS30Output = field(default_factory=CAS30Output)
    cas40_out: CAS40Output = field(default_factory=CAS40Output)
    cas50_out: CAS50Output = field(default_factory=CAS50Output)
    cas60_out: CAS60Output = field(default_factory=CAS60Output)
    cas70_out: CAS70Output = field(default_factory=CAS70Output)
    cas80_out: CAS80Output = field(default_factory=CAS80Output)
    cas90_out: CAS90Output = field(default_factory=CAS90Output)
    lcoe_out: LCOEOutput = field(default_factory=LCOEOutput)
    
    # ========== SUMMARY TOTALS ==========
    c200000: M_USD = M_USD(0.0)  # Direct capital (sum CAS 21-29)
    total_capital_cost: M_USD = M_USD(0.0)  # TCC (includes indirect & owner)
    total_epc_cost: M_USD = M_USD(0.0)  # Same as TCC (legacy name)
    
    def compute_summary_totals(self):
        """Compute summary cost totals."""
        # C200000: Direct capital (CAS 21-29)
        direct_capital_components = [
            self.cas21_out.C210000,
            self.cas22_out.C220000,
            self.cas23_out.C230000,
            self.cas24_out.C240000,
            self.cas25_out.C250000,
            self.cas26_out.C260000,
            self.cas27_out.C270000,
            self.cas28_out.C280000,
            self.cas29_out.C290000,
        ]
        self.c200000 = M_USD(sum(direct_capital_components))
        
        # Total Capital Cost (TCC): CAS 10 + CAS 20 + CAS 30 + CAS 40 + CAS 50 + CAS 60
        self.total_capital_cost = M_USD(sum([
            self.cas10_out.C100000,  # Pre-construction
            self.c200000,             # Direct capital
            self.cas30_out.C300000,  # Indirect (construction)
            self.cas40_out.C400000,  # Owner costs
            self.cas50_out.C500000,  # Capitalized supplementary
            self.cas60_out.C600000,  # Capitalized O&M (spares)
        ]))
        
        # Legacy name (backward compat)
        self.total_epc_cost = self.total_capital_cost
