"""CAS 22 output (Reactor Plant Equipment)."""
from dataclasses import dataclass

from ..units import M_USD


@dataclass
class CAS220101Output:
    """CAS 22.01.01 - First wall, blanket, shield."""
    
    C22010101: M_USD = M_USD(0.0)  # First wall
    C22010102: M_USD = M_USD(0.0)  # Blanket
    C22010103: M_USD = M_USD(0.0)  # Shield
    C22010104: M_USD = M_USD(0.0)  # Divertor/Target
    C22010100: M_USD = M_USD(0.0)  # TOTAL 22.01.01
    
    def compute_total(self):
        self.C22010100 = M_USD(sum([
            self.C22010101, self.C22010102, self.C22010103, self.C22010104
        ]))


@dataclass
class CAS220102Output:
    """CAS 22.01.02 - High-temperature shield."""
    
    C22010200: M_USD = M_USD(0.0)  # TOTAL 22.01.02


@dataclass
class CAS220103Output:
    """CAS 22.01.03 - Support structure."""
    
    C22010300: M_USD = M_USD(0.0)  # TOTAL 22.01.03


@dataclass
class CAS220104Output:
    """CAS 22.01.04 - Penetrations and access."""
    
    C22010400: M_USD = M_USD(0.0)  # TOTAL 22.01.04


@dataclass
class CAS220105Output:
    """CAS 22.01.05 - Vessel."""
    
    C22010500: M_USD = M_USD(0.0)  # TOTAL 22.01.05


@dataclass
class CAS220106Output:
    """CAS 22.01.06 - Pressure suppression system."""
    
    C22010600: M_USD = M_USD(0.0)  # TOTAL 22.01.06


@dataclass
class CAS220107Output:
    """CAS 22.01.07 - Vacuum system auxiliary."""
    
    C22010700: M_USD = M_USD(0.0)  # TOTAL 22.01.07


@dataclass
class CAS2201Output:
    """CAS 22.01 - Blanket and first wall system (aggregate)."""
    
    cas220101: CAS220101Output = None
    cas220102: CAS220102Output = None
    cas220103: CAS220103Output = None
    cas220104: CAS220104Output = None
    cas220105: CAS220105Output = None
    cas220106: CAS220106Output = None
    cas220107: CAS220107Output = None
    C220100: M_USD = M_USD(0.0)  # TOTAL CAS 22.01
    
    def __post_init__(self):
        if self.cas220101 is None:
            self.cas220101 = CAS220101Output()
        if self.cas220102 is None:
            self.cas220102 = CAS220102Output()
        if self.cas220103 is None:
            self.cas220103 = CAS220103Output()
        if self.cas220104 is None:
            self.cas220104 = CAS220104Output()
        if self.cas220105 is None:
            self.cas220105 = CAS220105Output()
        if self.cas220106 is None:
            self.cas220106 = CAS220106Output()
        if self.cas220107 is None:
            self.cas220107 = CAS220107Output()
    
    def compute_total(self):
        self.C220100 = M_USD(sum([
            self.cas220101.C22010100,
            self.cas220102.C22010200,
            self.cas220103.C22010300,
            self.cas220104.C22010400,
            self.cas220105.C22010500,
            self.cas220106.C22010600,
            self.cas220107.C22010700,
        ]))


@dataclass
class CAS2202Output:
    """CAS 22.02 - Main heat transfer system."""
    
    C220200: M_USD = M_USD(0.0)  # TOTAL CAS 22.02


@dataclass
class CAS2203Output:
    """CAS 22.03 - Magnet systems."""
    
    C22030301: M_USD = M_USD(0.0)  # TF coils
    C22030302: M_USD = M_USD(0.0)  # PF coils
    C22030303: M_USD = M_USD(0.0)  # Central solenoid
    C22030304: M_USD = M_USD(0.0)  # Magnet structure
    C22030305: M_USD = M_USD(0.0)  # Cryostat
    C22030306: M_USD = M_USD(0.0)  # Cryogenic plant
    C220300: M_USD = M_USD(0.0)  # TOTAL CAS 22.03
    
    def compute_total(self):
        self.C220300 = M_USD(sum([
            self.C22030301, self.C22030302, self.C22030303,
            self.C22030304, self.C22030305, self.C22030306
        ]))


@dataclass
class CAS2204Output:
    """CAS 22.04 - Supplementary heating/Target factory."""
    
    C220400: M_USD = M_USD(0.0)  # TOTAL CAS 22.04


@dataclass
class CAS2205Output:
    """CAS 22.05 - Primary structure and support."""
    
    C220500: M_USD = M_USD(0.0)  # TOTAL CAS 22.05


@dataclass
class CAS2206Output:
    """CAS 22.06 - Vacuum pumping system."""
    
    C220600: M_USD = M_USD(0.0)  # TOTAL CAS 22.06


@dataclass
class CAS2207Output:
    """CAS 22.07 - Power supplies."""
    
    C220700: M_USD = M_USD(0.0)  # TOTAL CAS 22.07


@dataclass
class CAS22Output:
    """CAS 22 - Reactor Plant Equipment (aggregate)."""
    
    cas2201: CAS2201Output = None
    cas2202: CAS2202Output = None
    cas2203: CAS2203Output = None
    cas2204: CAS2204Output = None
    cas2205: CAS2205Output = None
    cas2206: CAS2206Output = None
    cas2207: CAS2207Output = None
    C220000: M_USD = M_USD(0.0)  # TOTAL CAS 22
    
    def __post_init__(self):
        if self.cas2201 is None:
            self.cas2201 = CAS2201Output()
        if self.cas2202 is None:
            self.cas2202 = CAS2202Output()
        if self.cas2203 is None:
            self.cas2203 = CAS2203Output()
        if self.cas2204 is None:
            self.cas2204 = CAS2204Output()
        if self.cas2205 is None:
            self.cas2205 = CAS2205Output()
        if self.cas2206 is None:
            self.cas2206 = CAS2206Output()
        if self.cas2207 is None:
            self.cas2207 = CAS2207Output()
    
    def compute_total(self):
        self.C220000 = M_USD(sum([
            self.cas2201.C220100,
            self.cas2202.C220200,
            self.cas2203.C220300,
            self.cas2204.C220400,
            self.cas2205.C220500,
            self.cas2206.C220600,
            self.cas2207.C220700,
        ]))
