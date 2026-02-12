"""CAS 22.03 (Magnet Systems) input parameters."""
from dataclasses import dataclass

from ..units import Meters
from ..enums_new import MagnetType, MagnetMaterialType


@dataclass
class CAS2203Inputs:
    """Magnet system inputs (TF, PF, CS coils for MFE)."""
    
    # ===== Configuration =====
    magnet_type: MagnetType = MagnetType.HTS
    magnet_material: MagnetMaterialType = MagnetMaterialType.REBCO
    
    # ===== TF coils (toroidal field - tokamak/mirror) =====
    n_tf_coils: int = 18                        # Number of TF coils
    coil_radial_thickness: Meters = Meters(1.0) # Radial thickness of coil pack [m]
    tf_coil_cross_section_m2: float = 0.5       # Cross-section area per coil [m²]
    tf_coil_perimeter: Meters = Meters(30.0)    # Perimeter of one TF coil [m]
    
    # TF coil material fractions
    tf_conductor_fraction: float = 0.30         # Superconductor (or copper)
    tf_stabilizer_fraction: float = 0.20        # Copper stabilizer (LTS) or none (HTS)
    tf_structure_fraction: float = 0.40         # Structure (Inconel/SS316)
    tf_insulation_fraction: float = 0.10        # Insulation
    
    # ===== PF coils (poloidal field - tokamak) =====
    n_pf_coils: int = 6                         # Number of PF coils
    pf_coil_total_volume_m3: float = 20.0       # Total PF coil volume [m³]
    
    pf_conductor_fraction: float = 0.30
    pf_stabilizer_fraction: float = 0.20
    pf_structure_fraction: float = 0.40
    pf_insulation_fraction: float = 0.10
    
    # ===== Central solenoid (tokamak only) =====
    has_central_solenoid: bool = True
    cs_volume_m3: float = 10.0                  # CS volume [m³]
    
    cs_conductor_fraction: float = 0.35
    cs_stabilizer_fraction: float = 0.20
    cs_structure_fraction: float = 0.35
    cs_insulation_fraction: float = 0.10
    
    # ===== Cryostat & structure =====
    cryostat_volume_m3: float = 5000.0          # Cryostat volume [m³]
    cryostat_material: str = "SS316"            # Cryostat material
    
    magnet_structure_mass_kg: float = 500000.0  # Magnet support structure mass [kg]
    magnet_structure_material: str = "Inconel"  # Support structure material
    
    # ===== Cryogenic system =====
    cryo_plant_capacity_kw: float = 50.0        # Cryo plant capacity [kW]
    cryo_plant_cost_factor: float = 100.0       # Cost factor [$/W]
