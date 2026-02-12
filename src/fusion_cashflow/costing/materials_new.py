"""
Material properties database for fusion reactor costing.

This module provides the comprehensive material database from PyFECONS,
including density, raw cost, manufacturing multipliers, and thermal properties.
"""
from dataclasses import dataclass
from typing import Dict, Optional

from .units import KgM3, Kelvin, M_USD


@dataclass
class Material:
    """Material properties for costing calculations."""
    
    name: str               # Full material name
    code: str               # Short identifier code
    rho: KgM3              # Density in kg/m³
    c_raw: float           # Raw material cost in $/kg
    m: float               # Manufacturing multiplier
    t_max: Kelvin = Kelvin(0.0)  # Maximum operating temperature (K)
    
    @property
    def unit_cost(self) -> float:
        """Manufactured cost per kg ($/kg)."""
        return self.c_raw * self.m
    
    def volume_cost_m_usd(self, volume_m3: float) -> M_USD:
        """Calculate cost for given volume in M$.
        
        Args:
            volume_m3: Volume in cubic meters
            
        Returns:
            Cost in millions of USD
        """
        return M_USD(volume_m3 * self.rho * self.c_raw * self.m / 1e6)
    
    def mass_cost_m_usd(self, mass_kg: float) -> M_USD:
        """Calculate cost for given mass in M$.
        
        Args:
            mass_kg: Mass in kilograms
            
        Returns:
            Cost in millions of USD
        """
        return M_USD(mass_kg * self.c_raw * self.m / 1e6)


# Material database - PyFECONS values
MATERIALS: Dict[str, Material] = {
    "FS": Material(
        name="Ferritic Steel",
        code="FS",
        rho=KgM3(7470),
        c_raw=10.0,
        m=3.0,
        t_max=Kelvin(823)  # ~550°C
    ),
    "W": Material(
        name="Tungsten",
        code="W",
        rho=KgM3(19300),
        c_raw=100.0,
        m=3.0,
        t_max=Kelvin(3695)  # Very high temp capability
    ),
    "Be": Material(
        name="Beryllium",
        code="Be",
        rho=KgM3(1850),
        c_raw=5750.0,
        m=3.0,
        t_max=Kelvin(923)  # ~650°C
    ),
    "Li": Material(
        name="Lithium",
        code="Li",
        rho=KgM3(534),
        c_raw=70.0,
        m=1.5,
        t_max=Kelvin(1615)  # Boiling point
    ),
    "Li4SiO4": Material(
        name="Lithium Orthosilicate",
        code="Li4SiO4",
        rho=KgM3(2390),
        c_raw=1.0,
        m=2.0,
        t_max=Kelvin(1528)  # Melting point
    ),
    "Li2TiO3": Material(
        name="Lithium Metatitanate",
        code="Li2TiO3",
        rho=KgM3(3430),
        c_raw=1297.05,
        m=3.0,
        t_max=Kelvin(1800)
    ),
    "FLiBe": Material(
        name="FLiBe Molten Salt",
        code="FLiBe",
        rho=KgM3(1900),
        c_raw=1000.0,
        m=1.0,
        t_max=Kelvin(1703)  # Boiling point
    ),
    "SiC": Material(
        name="Silicon Carbide",
        code="SiC",
        rho=KgM3(3200),
        c_raw=14.49,
        m=3.0,
        t_max=Kelvin(3003)  # Very high temp
    ),
    "SS316": Material(
        name="Stainless Steel 316",
        code="SS316",
        rho=KgM3(7860),
        c_raw=2.0,
        m=2.0,
        t_max=Kelvin(923)  # ~650°C
    ),
    "Cu": Material(
        name="Copper",
        code="Cu",
        rho=KgM3(8960),
        c_raw=10.2,
        m=3.0,
        t_max=Kelvin(1358)  # Melting point
    ),
    "YBCO": Material(
        name="YBCO HTS",
        code="YBCO",
        rho=KgM3(6200),
        c_raw=55.0,
        m=1.0,
        t_max=Kelvin(92)  # Critical temp
    ),
    "Nb3Sn": Material(
        name="Niobium-Tin LTS",
        code="Nb3Sn",
        rho=KgM3(8900),  # Approximate
        c_raw=5.0,
        m=1.0,
        t_max=Kelvin(18)  # Critical temp
    ),
    "NbTi": Material(
        name="Niobium-Titanium LTS",
        code="NbTi",
        rho=KgM3(6000),  # Approximate
        c_raw=2.5,
        m=1.0,
        t_max=Kelvin(10)  # Critical temp
    ),
    "Concrete": Material(
        name="Concrete",
        code="Concrete",
        rho=KgM3(2300),
        c_raw=0.013,  # 13/1000 from PyFECONS
        m=2.0,
        t_max=Kelvin(573)  # ~300°C
    ),
    "BFS": Material(
        name="Borated Ferritic Steel",
        code="BFS",
        rho=KgM3(7800),
        c_raw=30.0,
        m=2.0,
        t_max=Kelvin(823)  # ~550°C
    ),
    "Inconel": Material(
        name="Inconel 718",
        code="Inconel",
        rho=KgM3(8440),
        c_raw=46.0,
        m=3.0,
        t_max=Kelvin(980)  # ~700°C
    ),
    "Pb": Material(
        name="Lead",
        code="Pb",
        rho=KgM3(11340),
        c_raw=2.4,
        m=1.5,
        t_max=Kelvin(2022)  # Boiling point
    ),
    "PbLi": Material(
        name="Lead-Lithium Eutectic",
        code="PbLi",
        rho=KgM3(9700),  # Blended density (Pb:Li ~10:1 molar)
        c_raw=5.0,  # Blended cost
        m=1.5,
        t_max=Kelvin(1943)
    ),
    "V": Material(
        name="Vanadium Alloy",
        code="V",
        rho=KgM3(6100),
        c_raw=220.0,
        m=3.0,
        t_max=Kelvin(2183)  # Boiling point
    ),
}


# Material name aliases for backward compatibility
MATERIAL_ALIASES = {
    # Legacy full names → new codes
    'tungsten': 'W',
    'beryllium': 'Be',
    'lithium': 'Li',
    'liquid lithium': 'Li',
    'liquid_lithium': 'Li',
    'copper': 'Cu',
    'concrete': 'Concrete',
    'lead': 'Pb',
    'vanadium': 'V',
    'ferritic_steel': 'FS',
    'ferritic steel': 'FS',
    'stainless_steel': 'SS316',
    'stainless steel': 'SS316',
    'ss': 'SS316',
    'steel': 'SS316',
    'silicon_carbide': 'SiC',
    'silicon carbide': 'SiC',
    'borated_steel': 'BFS',
    'borated steel': 'BFS',
    'borated ferritic steel': 'BFS',
    'borated_ferritic_steel': 'BFS',
    'inconel': 'Inconel',
    'flibe': 'FLiBe',
    'pbli': 'PbLi',
    'lead_lithium': 'PbLi',
    'lead lithium': 'PbLi',
    'pb-li': 'PbLi',
    'ybco': 'YBCO',
    'nbti': 'NbTi',
    'nb3sn': 'Nb3Sn',
    'nb-ti': 'NbTi',
    'nb-sn': 'Nb3Sn',
    'niobium_tin': 'Nb3Sn',
    'niobium tin': 'Nb3Sn',
    'niobium-tin': 'Nb3Sn',
    'niobium_titanium': 'NbTi',
    'niobium titanium': 'NbTi',
    'niobium-titanium': 'NbTi',
    'lithium_orthosilicate': 'Li4SiO4',
    'lithium orthosilicate': 'Li4SiO4',
    'li4sio4': 'Li4SiO4',
    'lithium_metatitanate': 'Li2TiO3',
    'lithium metatitanate': 'Li2TiO3',
    'li2tio3': 'Li2TiO3',
    # Common variations (lowercase)
    'w': 'W',
    'be': 'Be',
    'li': 'Li',
    'cu': 'Cu',
    'pb': 'Pb',
    'v': 'V',
    'fs': 'FS',
    'ss316': 'SS316',
    'sic': 'SiC',
    'bfs': 'BFS',
}


def normalize_material_code(code: str) -> str:
    """Normalize material code, handling aliases and case variations.
    
    Args:
        code: Material code or alias (e.g., "tungsten", "W", "w")
        
    Returns:
        Normalized material code (e.g., "W")
        
    Raises:
        KeyError: If material code/alias not recognized
    """
    # Try as-is first
    if code in MATERIALS:
        return code
    
    # Try lowercase lookup in aliases
    code_lower = code.lower()
    if code_lower in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[code_lower]
    
    # Try exact match in aliases
    if code in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[code]
    
    # Not found
    raise KeyError(
        f"Material code '{code}' not recognized. "
        f"Available codes: {list(MATERIALS.keys())}. "
        f"Available aliases: {list(set(MATERIAL_ALIASES.keys()))[:10]}..."
    )


def get_material(code: str) -> Material:
    """Retrieve material by code or alias.
    
    Args:
        code: Material code or alias (e.g., "W", "tungsten", "FS")
        
    Returns:
        Material object
        
    Raises:
        KeyError: If material code not found
    """
    normalized = normalize_material_code(code)
    return MATERIALS[normalized]


def get_material_cost(code: str, volume_m3: float) -> M_USD:
    """Calculate material cost for given volume.
    
    Args:
        code: Material code
        volume_m3: Volume in cubic meters
        
    Returns:
        Cost in millions of USD
    """
    material = get_material(code)
    return material.volume_cost_m_usd(volume_m3)


def list_materials() -> Dict[str, str]:
    """Get dict of all material codes and names.
    
    Returns:
        Dict mapping code to full name
    """
    return {code: mat.name for code, mat in MATERIALS.items()}
