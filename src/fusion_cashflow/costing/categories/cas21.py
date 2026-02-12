"""CAS 21 output (Buildings and structures)."""
from dataclasses import dataclass

from ..units import M_USD


@dataclass
class CAS21Output:
    """CAS 21 - Buildings and structures cost outputs."""
    
    # All 17 building sub-accounts from PyFECONS
    C210100: M_USD = M_USD(0.0)   # Reactor building
    C210200: M_USD = M_USD(0.0)   # Turbine building
    C210300: M_USD = M_USD(0.0)   # Reactor maintenance building
    C210400: M_USD = M_USD(0.0)   # Warm shop
    C210500: M_USD = M_USD(0.0)   # Tritium building
    C210600: M_USD = M_USD(0.0)   # Electrical equipment building
    C210700: M_USD = M_USD(0.0)   # Hot cell building
    C210800: M_USD = M_USD(0.0)   # Reactor service building
    C210900: M_USD = M_USD(0.0)   # Service water building
    C211000: M_USD = M_USD(0.0)   # Fuel storage building
    C211100: M_USD = M_USD(0.0)   # Control room building
    C211200: M_USD = M_USD(0.0)   # On-site AC power building
    C211300: M_USD = M_USD(0.0)   # Admin building
    C211400: M_USD = M_USD(0.0)   # Site services building
    C211500: M_USD = M_USD(0.0)   # Cryogenics building
    C211600: M_USD = M_USD(0.0)   # Security building
    C211700: M_USD = M_USD(0.0)   # Ventilation stack
    C211800: M_USD = M_USD(0.0)   # Spare (not used)
    C211900: M_USD = M_USD(0.0)   # Contingency (FOAK only)
    C210000: M_USD = M_USD(0.0)   # TOTAL CAS 21
    
    def compute_total(self):
        """Sum all sub-accounts."""
        self.C210000 = M_USD(sum([
            self.C210100, self.C210200, self.C210300, self.C210400,
            self.C210500, self.C210600, self.C210700, self.C210800,
            self.C210900, self.C211000, self.C211100, self.C211200,
            self.C211300, self.C211400, self.C211500, self.C211600,
            self.C211700, self.C211800, self.C211900
        ]))
