"""CAS 22.01.01 (First Wall, Blanket, Shield) input parameters."""
from dataclasses import dataclass

from ..units import Meters
from ..enums_new import (
    BlanketPrimaryCoolant,
    BlanketSecondaryCoolant,
    BlanketBreederMaterial,
    BlanketNeutronMultiplier,
)


@dataclass
class CAS220101Inputs:
    """Reactor core component inputs (first wall, blanket, shield)."""
    
    # ===== Geometry =====
    # Plasma parameters
    r_plasma: Meters = Meters(2.0)          # Major radius (tokamak) or chamber radius [m]
    a_plasma: Meters = Meters(0.5)          # Minor radius (tokamak) [m]
    elon: float = 1.7                        # Elongation (tokamak only)
    chamber_length: Meters = Meters(10.0)   # Chamber length (mirror) [m]
    
    # Layer thicknesses (radial build)
    first_wall_thickness: Meters = Meters(0.02)      # First wall thickness [m]
    blanket_thickness: Meters = Meters(0.50)          # Blanket thickness [m]
    shield_thickness: Meters = Meters(0.50)           # Shield thickness [m]
    
    # ===== Materials =====
    # First wall
    first_wall_material: str = "W"                    # Material code (e.g., "W", "FS")
    first_wall_structure_material: str = "FS"         # Structural backing
    
    # Blanket
    blanket_structural_material: str = "FS"           # Structure (e.g., "FS", "SiC")
    blanket_breeder_material: str = "Li4SiO4"         # Breeder (or enum-driven)
    blanket_coolant: BlanketPrimaryCoolant = BlanketPrimaryCoolant.WATER
    blanket_secondary_coolant: BlanketSecondaryCoolant = BlanketSecondaryCoolant.NONE
    blanket_multiplier: BlanketNeutronMultiplier = BlanketNeutronMultiplier.BE
    
    # Shield
    shield_material: str = "BFS"                      # Shield material (e.g., "BFS", "Concrete")
    
    # ===== Volume fractions =====
    # First wall
    fw_armor_fraction: float = 0.70         # Fraction of FW volume that is armor (W)
    fw_structure_fraction: float = 0.30     # Fraction that is structure (FS)
    
    # Blanket
    blanket_structure_fraction: float = 0.15    # Structure (e.g., FS)
    blanket_breeder_fraction: float = 0.50      # Breeder (e.g., Li4SiO4)
    blanket_coolant_fraction: float = 0.20      # Coolant channels
    blanket_multiplier_fraction: float = 0.15   # Neutron multiplier (e.g., Be)
    
    # Shield
    shield_structure_fraction: float = 0.60     # Steel/structure
    shield_boron_fraction: float = 0.10         # Boron content (neutron absorber)
    shield_void_fraction: float = 0.30          # Cooling channels/voids
    
    # ===== Divertor / Target (MFE/IFE) =====
    divertor_area_m2: float = 50.0              # Divertor surface area [m²] (MFE)
    divertor_material: str = "W"                # Divertor armor material
    divertor_structure_material: str = "Cu"     # Divertor structure/heat sink
    
    # Target chamber (IFE)
    target_chamber_thickness: Meters = Meters(0.05)  # First wall thickness (IFE) [m]
    target_chamber_material: str = "FS"              # Chamber wall material
