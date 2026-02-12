"""CAS 10 output (Pre-construction costs)."""
from dataclasses import dataclass

from ..units import M_USD


@dataclass
class CAS10Output:
    """CAS 10 - Pre-construction cost outputs."""
    
    C100100: M_USD = M_USD(0.0)  # Land acquisition
    C100200: M_USD = M_USD(0.0)  # Site preparation
    C100300: M_USD = M_USD(0.0)  # Permits and licenses
    C100400: M_USD = M_USD(0.0)  # Environmental studies
    C100500: M_USD = M_USD(0.0)  # Conceptual design
    C100600: M_USD = M_USD(0.0)  # Preliminary design
    C100000: M_USD = M_USD(0.0)  # TOTAL CAS 10
    
    def compute_total(self):
        """Sum all sub-accounts."""
        self.C100000 = M_USD(sum([
            self.C100100, self.C100200, self.C100300,
            self.C100400, self.C100500, self.C100600
        ]))
