"""
Comprehensive enumerations for fusion reactor costing.

This module provides all the enum types needed for PyFECONS-compatible
costing calculations, including reactor types, fuel types, materials,
coolants, and configuration options.
"""
from enum import Enum


class ReactorType(Enum):
    """Type of fusion reactor confinement."""
    MFE_TOKAMAK = "tokamak"
    MFE_MIRROR = "mirror"
    IFE_LASER = "laser"


class FuelType(Enum):
    """Fusion fuel cycle type."""
    DT = "DT"           # Deuterium-Tritium
    DD = "DD"           # Deuterium-Deuterium
    DHe3 = "DHe3"       # Deuterium-Helium-3
    pB11 = "pB11"       # Proton-Boron-11


class BlanketPrimaryCoolant(Enum):
    """Primary coolant for blanket system."""
    WATER = "H2O"
    HELIUM = "He"
    FLIBE = "FLiBe"
    PBLI = "PbLi"
    DUAL_COOLANT = "Dual"


class BlanketSecondaryCoolant(Enum):
    """Secondary coolant for blanket system (if applicable)."""
    WATER = "H2O"
    HELIUM = "He"
    NONE = "None"


class BlanketBreederMaterial(Enum):
    """Tritium breeding material."""
    LI4SIO4 = "Li4SiO4"           # Lithium orthosilicate (ceramic)
    LI2TIO3 = "Li2TiO3"           # Lithium metatitanate (ceramic)
    FLIBE = "FLiBe"               # Molten salt (2LiF-BeF2)
    PBLI = "PbLi"                 # Lead-lithium eutectic
    LI = "Li"                     # Liquid lithium


class BlanketNeutronMultiplier(Enum):
    """Neutron multiplication material."""
    BE = "Be"           # Beryllium
    PB = "Pb"           # Lead
    NONE = "None"


class MagnetType(Enum):
    """Type of magnet technology."""
    HTS = "HTS"                 # High-temperature superconductor
    LTS = "LTS"                 # Low-temperature superconductor
    COPPER = "Copper"           # Resistive copper
    RESISTIVE = "Resistive"     # Generic resistive


class MagnetMaterialType(Enum):
    """Specific superconductor or conductor material."""
    REBCO = "REBCO"             # RE-Ba-Cu-O (e.g., YBCO) - HTS
    NB3SN = "Nb3Sn"             # Niobium-tin - LTS
    NBTI = "NbTi"               # Niobium-titanium - LTS
    COPPER = "Copper"           # Copper conductor


class StructurePga(Enum):
    """Peak ground acceleration for seismic design."""
    LOW = "low"          # 0.1g
    MED = "medium"       # 0.3g
    HIGH = "high"        # 0.5g


class Region(Enum):
    """Geographic region for cost scaling."""
    US = "US"
    EU = "EU"
    ASIA = "Asia"


class LSALevel(Enum):
    """Level of Safety Assurance (regulatory classification)."""
    LSA1 = 1   # Least safety assurance (commercial-grade)
    LSA2 = 2   # Low safety assurance
    LSA3 = 3   # Medium safety assurance
    LSA4 = 4   # Highest safety assurance (experimental-grade)


class HeatingType(Enum):
    """Supplementary heating system type."""
    NBI = "NBI"                 # Neutral beam injection
    ECRH = "ECRH"               # Electron cyclotron resonance heating
    ICRH = "ICRH"               # Ion cyclotron resonance heating
    LHRH = "LHRH"               # Lower hybrid resonance heating
    COMBINED = "Combined"       # Multiple systems


class VacuumPumpType(Enum):
    """Type of vacuum pumping system."""
    CRYOPUMP = "Cryopump"
    TURBOMOLECULAR = "Turbomolecular"
    DIFFUSION = "Diffusion"
    COMBINED = "Combined"


class TurbineType(Enum):
    """Steam/gas turbine type."""
    STEAM_RANKINE = "Steam"
    GAS_BRAYTON = "Brayton"
    COMBINED_CYCLE = "Combined"


class CoolingTowerType(Enum):
    """Heat rejection system type."""
    WET = "Wet"
    DRY = "Dry"
    HYBRID = "Hybrid"


# Material codes enum (for type safety)
class MaterialCode(Enum):
    """Material identifier codes."""
    FS = "FS"               # Ferritic Steel
    W = "W"                 # Tungsten
    BE = "Be"               # Beryllium
    LI = "Li"               # Lithium
    LI4SIO4 = "Li4SiO4"     # Lithium orthosilicate
    LI2TIO3 = "Li2TiO3"     # Lithium metatitanate
    FLIBE = "FLiBe"         # FLiBe molten salt
    SIC = "SiC"             # Silicon carbide
    SS316 = "SS316"         # Stainless steel 316
    CU = "Cu"               # Copper
    YBCO = "YBCO"           # YBCO superconductor
    NB3SN = "Nb3Sn"         # Niobium-tin superconductor
    NBTI = "NbTi"           # Niobium-titanium superconductor
    CONCRETE = "Concrete"   # Concrete
    BFS = "BFS"             # Borated ferritic steel
    INCONEL = "Inconel"     # Inconel 718
    PB = "Pb"               # Lead
    PBLI = "PbLi"           # Lead-lithium
    V = "V"                 # Vanadium alloy
