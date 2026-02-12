"""CAS 22.01.01 (First wall, blanket, shield) calculations.

Component cost = volume × material cost
Material cost = volume × rho × c_raw × m / 1e6  [M$]
"""
from ..costing_data import CostingData
from ..units import M_USD
from ..materials_new import get_material
from ..enums_new import BlanketPrimaryCoolant


def get_blanket_materials(data: CostingData) -> dict:
    """Determine blanket materials based on coolant type.
    
    Args:
        data: CostingData with blanket config
        
    Returns:
        Dict with 'structure', 'breeder', 'multiplier' material codes
    """
    coolant = data.cas220101_in.blanket_coolant
    
    # Dispatch based on coolant type (PyFECONS logic)
    if coolant == BlanketPrimaryCoolant.WATER:
        return {
            'structure': data.cas220101_in.blanket_structural_material or 'FS',
            'breeder': data.cas220101_in.blanket_breeder_material or 'Li4SiO4',
            'multiplier': 'Be'
        }
    elif coolant == BlanketPrimaryCoolant.HELIUM:
        return {
            'structure': 'FS',
            'breeder': data.cas220101_in.blanket_breeder_material or 'Li4SiO4',
            'multiplier': 'Be'
        }
    elif coolant == BlanketPrimaryCoolant.FLIBE:
        return {
            'structure': 'SiC',  # or FS
            'breeder': 'FLiBe',  # Self-breeding (coolant IS breeder)
            'multiplier': None    # Not needed
        }
    elif coolant == BlanketPrimaryCoolant.PBLI:
        return {
            'structure': 'FS',
            'breeder': 'PbLi',   # Self-breeding (coolant IS breeder)
            'multiplier': None    # Pb inherent
        }
    else:
        # Default
        return {
            'structure': 'FS',
            'breeder': data.cas220101_in.blanket_breeder_material or 'Li4SiO4',
            'multiplier': 'Be'
        }


def compute_first_wall_cost(data: CostingData) -> M_USD:
    """Compute first wall cost.
    
    FW typically has armor (W) + structure (FS).
    
    Args:
        data: CostingData with volumes and materials
        
    Returns:
        First wall cost [M$]
    """
    inp = data.cas220101_in
    vol_fw = data.volumes.get('first_wall', 0.0)
    
    # Armor material (e.g., W)
    mat_armor = get_material(inp.first_wall_material)
    vol_armor = vol_fw * inp.fw_armor_fraction
    cost_armor = mat_armor.volume_cost_m_usd(vol_armor)
    
    # Structure material (e.g., FS)
    mat_structure = get_material(inp.first_wall_structure_material)
    vol_structure = vol_fw * inp.fw_structure_fraction
    cost_structure = mat_structure.volume_cost_m_usd(vol_structure)
    
    return M_USD(cost_armor + cost_structure)


def compute_blanket_cost(data: CostingData) -> M_USD:
    """Compute blanket cost.
    
    Blanket has structure + breeder + coolant(ignored) + multiplier.
    
    Args:
        data: CostingData with volumes and materials
        
    Returns:
        Blanket cost [M$]
    """
    inp = data.cas220101_in
    vol_blanket = data.volumes.get('blanket', 0.0)
    
    # Get material dispatch
    mats = get_blanket_materials(data)
    
    # Structure
    mat_structure = get_material(mats['structure'])
    vol_structure = vol_blanket * inp.blanket_structure_fraction
    cost_structure = mat_structure.volume_cost_m_usd(vol_structure)
    
    # Breeder
    mat_breeder = get_material(mats['breeder'])
    vol_breeder = vol_blanket * inp.blanket_breeder_fraction
    cost_breeder = mat_breeder.volume_cost_m_usd(vol_breeder)
    
    # Multiplier (if applicable)
    cost_multiplier = M_USD(0.0)
    if mats['multiplier']:
        mat_multiplier = get_material(mats['multiplier'])
        vol_multiplier = vol_blanket * inp.blanket_multiplier_fraction
        cost_multiplier = mat_multiplier.volume_cost_m_usd(vol_multiplier)
    
    return M_USD(cost_structure + cost_breeder + cost_multiplier)


def compute_shield_cost(data: CostingData) -> M_USD:
    """Compute shield cost.
    
    Shield is typically borated ferritic steel (BFS) or concrete.
    
    Args:
        data: CostingData with volumes and materials
        
    Returns:
        Shield cost [M$]
    """
    inp = data.cas220101_in
    vol_shield = data.volumes.get('shield', 0.0)
    
    # Shield material
    mat_shield = get_material(inp.shield_material)
    
    # Apply structure fraction (rest is void/cooling)
    vol_effective = vol_shield * inp.shield_structure_fraction
    cost_shield = mat_shield.volume_cost_m_usd(vol_effective)
    
    return cost_shield


def compute_divertor_cost(data: CostingData) -> M_USD:
    """Compute divertor/target cost (placeholder).
    
    For now, simple area-based estimate.
    
    Args:
        data: CostingData with divertor area
        
    Returns:
        Divertor cost [M$]
    """
    inp = data.cas220101_in
    area_m2 = inp.divertor_area_m2
    
    # Simplified: W armor @ 10 kg/m² × cost
    mat_armor = get_material(inp.divertor_material)
    mass_kg = area_m2 * 10.0  # 10 kg/m² armor
    cost_armor = mat_armor.mass_cost_m_usd(mass_kg)
    
    # Structure (Cu heat sink) @ 50 kg/m²
    mat_structure = get_material(inp.divertor_structure_material)
    mass_structure_kg = area_m2 * 50.0
    cost_structure = mat_structure.mass_cost_m_usd(mass_structure_kg)
    
    return M_USD(cost_armor + cost_structure)


def compute_cas220101(data: CostingData) -> None:
    """Compute CAS 22.01.01 (First wall, blanket, shield) costs.
    
    Updates data.cas22_out.cas2201.cas220101 in place.
    
    Args:
        data: CostingData with volumes and material inputs
    """
    out = data.cas22_out.cas2201.cas220101
    
    # Compute each component
    out.C22010101 = compute_first_wall_cost(data)
    out.C22010102 = compute_blanket_cost(data)
    out.C22010103 = compute_shield_cost(data)
    out.C22010104 = compute_divertor_cost(data)
    
    # Total
    out.compute_total()
