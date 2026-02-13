#!/usr/bin/env python3
"""
Power-to-EPC Cost Linkage Module

Integrates extracted fusion reactor costing code (from PyFECONS) directly into application.
Provides comprehensive costing with geometry-driven volumes, magnet calculations, 
Q_eng derivation, and complete CAS breakdown.

No external dependencies - all costing logic embedded.
"""

from typing import Dict, Any
from ..costing import compute_total_epc_cost


# =============================
# Regional Cost Factors
# =============================

# Regional cost adjustment factors
REGIONAL_FACTORS = {
    "North America": 1.0,      # dimensionless (cost multiplier relative to North America baseline)
    "Europe": 1.15,            # dimensionless (15% higher costs than North America)
    "China": 0.65,             # dimensionless (35% lower costs than North America)
    "India": 0.45,             # dimensionless (55% lower costs than North America)
    "Oceania": 1.05,           # dimensionless (5% higher costs than North America)
    "Southern Africa": 0.55,   # dimensionless (45% lower costs than North America)
    "MENA": 0.70,              # dimensionless (30% lower costs than North America)
    "Latin America": 0.60,     # dimensionless (40% lower costs than North America)
    "Russia & CIS": 0.50,      # dimensionless (50% lower costs than North America)
    "Southeast Asia": 0.50,    # dimensionless (50% lower costs than North America)
    "Sub-Saharan Africa": 0.45,# dimensionless (55% lower costs than North America)
}


def get_regional_factor(location: str) -> float:
    """
    Get regional cost factor from project location string.
    
    Args:
        location: Project location string (e.g., "USA", "France", "China")
        
    Returns:
        Regional cost multiplier (1.0 = North America baseline)
    """
    location_lower = location.lower()
    
    for region, countries in {
        "North America": ["united states", "canada", "mexico", "usa"],
        "Europe": ["france", "germany", "uk", "italy", "spain", "netherlands", 
                  "norway", "sweden", "finland", "poland", "ukraine", "europe"],
        "China": ["china", "chinese"],
        "India": ["india", "indian"],
        "Oceania": ["australia", "new zealand", "oceania"],
        "Southern Africa": ["south africa", "southern africa"],
        "MENA": ["saudi arabia", "uae", "egypt", "middle east", "mena"],
        "Latin America": ["brazil", "argentina", "chile", "latin america"],
        "Russia & CIS": ["russia", "russian", "cis"],
        "Southeast Asia": ["singapore", "thailand", "vietnam", "southeast asia"],
        "Sub-Saharan Africa": ["nigeria", "kenya", "sub-saharan africa"],
    }.items():
        if any(country in location_lower for country in countries):
            return REGIONAL_FACTORS.get(region, 1.0)
    
    return 1.0  # Default to North America factor


# =============================
# Main EPC Calculation Function
# =============================

def compute_epc(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main dispatcher for EPC cost calculation using integrated costing.
    
    Uses extracted fusion costing algorithms embedded directly in application.
    Provides physics-based geometry scaling and comprehensive cost breakdown.
    
    Args:
        cfg: Configuration dictionary from dashboard with keys:
            - reactor_type: "MFE Tokamak" or "IFE Laser"
            - reactor_type_code: "MFE" or "IFE" (mapped from reactor_type)
            - fuel_type_code: "DT", "DD", "DHE3", or "PB11" (mapped from fuel_type)
            - noak: Boolean for NOAK vs FOAK
            - fusion_power_mw: Fusion power (MW)
            - auxiliary_power_mw: Auxiliary heating power (MW)
            - thermal_efficiency: Thermal-to-electric efficiency
            - first_wall_material, blanket_type, structure_material: Material selections
            - magnet_technology, toroidal_field_tesla, n_tf_coils, etc.: Magnet parameters
            - chamber_radius_m, driver_energy_mj: IFE parameters
            - use_expert_geometry: If True, use expert geometry overrides
            - expert_*: Expert geometry parameters
            
    Returns:
        Dictionary with EPC cost breakdown matching dashboard expectations
    """
    # Map dashboard config to costing module format
    costing_config = {
        # Basic parameters
        "reactor_type": cfg.get("reactor_type_code", "MFE"),
        "fuel_type": cfg.get("fuel_type_code", "DT"),
        "noak": cfg.get("noak", True),
        "capacity_factor": cfg.get("capacity_factor", 0.92),
        
        # Plant lifetime for LCOE calculation
        "plant_lifetime_years": cfg.get("plant_lifetime", 32),
        
        # Power parameters
        "p_nrl_fusion_power_mw": cfg.get("fusion_power_mw", 500),
        "auxiliary_power_mw": cfg.get("auxiliary_power_mw", 50),
        "q_plasma": cfg.get("q_plasma", 10),
        "thermal_efficiency": cfg.get("thermal_efficiency", 0.46),
        
        # Geometry parameters (defaults for non-expert mode)
        "major_radius_m": cfg.get("major_radius_m", 3.0),
        "plasma_t": cfg.get("plasma_t", 1.1),
        "vacuum_t": cfg.get("vacuum_t", 0.1),
        "firstwall_t": cfg.get("firstwall_t", 0.02),
        "blanket_t": cfg.get("blanket_t", 0.8),
        "reflector_t": cfg.get("reflector_t", 0.2),
        "ht_shield_t": cfg.get("ht_shield_t", 0.2),
        "structure_t": cfg.get("structure_t", 0.2),
        "gap_t": cfg.get("gap_t", 0.5),
        "vessel_t": cfg.get("vessel_t", 0.2),
        "coil_t": cfg.get("coil_t", 1.0),
        "elongation": cfg.get("elongation", 3.0),
        
        # Material selections - pass through as-is, adapter handles mapping
        "first_wall_material": cfg.get("first_wall_material", "Tungsten"),
        "blanket_type": cfg.get("blanket_type", "Solid Breeder (Li2TiO3)"),
        "structure_material": cfg.get("structure_material", "Ferritic Steel (FMS)"),
        
        # Magnet parameters - pass through as-is, adapter handles mapping
        "magnet_technology": cfg.get("magnet_technology", "HTS REBCO"),
        "toroidal_field_tesla": cfg.get("toroidal_field_tesla", 12.0),
        "n_tf_coils": int(cfg.get("n_tf_coils", 12)),
        "tape_width_m": cfg.get("tape_width_m_actual", 0.004),  # Already converted from mm to m
        "coil_thickness_m": cfg.get("coil_thickness_m", 0.25),
        
        # IFE parameters
        "chamber_radius_m": cfg.get("chamber_radius_m", 8.0),
        "driver_energy_mj": cfg.get("driver_energy_mj", 2.0),
        "repetition_rate_hz": cfg.get("repetition_rate_hz", 10.0),
        "target_gain": cfg.get("target_gain", 50),
    }
    
    # Use expert geometry if provided
    if cfg.get("use_expert_geometry", False):
        if cfg.get("reactor_type_code", "MFE") == "MFE":
            # MFE expert parameters (15 total)
            costing_config.update({
                "major_radius_m": cfg.get("expert_major_radius_m", 3.0),
                "plasma_t": cfg.get("expert_plasma_t", 1.1),
                "elongation": cfg.get("expert_elongation", 3.0),
                "vacuum_t": cfg.get("expert_vacuum_t", 0.1),
                "firstwall_t": cfg.get("expert_firstwall_t", 0.02),
                "blanket_t": cfg.get("expert_blanket_t", 0.8),
                "reflector_t": cfg.get("expert_reflector_t", 0.2),
                "ht_shield_t": cfg.get("expert_ht_shield_t", 0.2),
                "structure_t": cfg.get("expert_structure_t", 0.2),
                "gap_t": cfg.get("expert_gap_t", 0.5),
                "vessel_t": cfg.get("expert_vessel_t", 0.2),
                "gap2_t": cfg.get("expert_gap2_t", 0.5),
                "lt_shield_t": cfg.get("expert_lt_shield_t", 0.3),
                "coil_t": cfg.get("expert_coil_t", 1.0),
                "bio_shield_t": cfg.get("expert_bio_shield_t", 1.0),
            })
        else:  # IFE
            # IFE expert parameters (6 total)
            costing_config.update({
                "chamber_radius_m": cfg.get("expert_chamber_radius_m", 8.0),
                "firstwall_t": cfg.get("expert_firstwall_t_ife", 0.005),
                "blanket_t": cfg.get("expert_blanket_t_ife", 0.5),
                "reflector_t": cfg.get("expert_reflector_t_ife", 0.1),
                "structure_t": cfg.get("expert_structure_t_ife", 0.2),
                "vessel_t": cfg.get("expert_vessel_t_ife", 0.2),
            })
    
    # Call integrated costing module
    costing_results = compute_total_epc_cost(costing_config)
    
    # Apply regional cost factor
    region_factor = cfg.get("region_factor", 1.0)
    
    # Format results to match dashboard expectations
    result = {
        "total_epc": costing_results["total_epc_cost"] * 1e6 * region_factor,  # Convert M$ to $
        "epc_per_kw": costing_results["epc_per_kw_net"] * 1e6 * region_factor,  # Convert M$/kW to $/kW
        
        "breakdown": {
            "building_total": costing_results["cas_21_total"] * 1e6 * region_factor,
            "preconstruction_total": costing_results["cas_10_preconstruction"] * 1e6 * region_factor,
            "reactor_equipment": costing_results["cas_22_total"] * 1e6 * region_factor,
            "indirect_costs": costing_results["cas_30_indirect"] * 1e6 * region_factor,
            "idc": costing_results.get("cas_29_contingency", 0) * 1e6 * region_factor,
            "owners_costs": costing_results["cas_40_owner_costs"] * 1e6 * region_factor,
            "cas_27_materials": costing_results.get("cas_27_materials", 0) * 1e6 * region_factor,
        },
        
        "detailed_result": {
            # All CAS totals (in $)
            "cas_10_preconstruction": costing_results.get("cas_10_preconstruction", 0) * 1e6,
            "cas_21_total": costing_results.get("cas_21_total", 0) * 1e6,
            "cas_22_total": costing_results.get("cas_22_total", 0) * 1e6,
            "cas_23_turbine": costing_results.get("cas_23_turbine", 0) * 1e6,
            "cas_24_electrical": costing_results.get("cas_24_electrical", 0) * 1e6,
            "cas_25_misc": costing_results.get("cas_25_misc", 0) * 1e6,
            "cas_26_cooling": costing_results.get("cas_26_cooling", 0) * 1e6,
            "cas_27_materials": costing_results.get("cas_27_materials", 0) * 1e6,
            "cas_28_instrumentation": costing_results.get("cas_28_instrumentation", 0) * 1e6,
            "cas_29_contingency": costing_results.get("cas_29_contingency", 0) * 1e6,
            "cas_30_indirect": costing_results.get("cas_30_indirect", 0) * 1e6,
            "cas_40_owner_costs": costing_results.get("cas_40_owner_costs", 0) * 1e6,
            
            # CAS 21 sub-accounts (buildings)
            "building_reactor_building": costing_results.get("building_reactor_building", 0) * 1e6,
            "building_turbine_building": costing_results.get("building_turbine_building", 0) * 1e6,
            "building_auxiliary_buildings": costing_results.get("building_auxiliary_buildings", 0) * 1e6,
            
            # CAS 22 sub-accounts (reactor equipment)
            "cas_2201": costing_results.get("cas_2201", 0) * 1e6,
            "cas_2202": costing_results.get("cas_2202", 0) * 1e6,
            "cas_2203": costing_results.get("cas_2203", 0) * 1e6,
            "cas_2204": costing_results.get("cas_2204", 0) * 1e6,
            "cas_2205": costing_results.get("cas_2205", 0) * 1e6,
            "cas_2206": costing_results.get("cas_2206", 0) * 1e6,
            "cas_2207": costing_results.get("cas_2207", 0) * 1e6,
            
            # CAS 22.01.01 sub-components (reactor internals)
            "firstwall": costing_results.get("firstwall", 0) * 1e6,
            "blanket": costing_results.get("blanket", 0) * 1e6,
            "shield": costing_results.get("shield", 0) * 1e6,
            "divertor": costing_results.get("divertor", 0) * 1e6,
        },
        
        "power_balance": {
            "q_eng": costing_results["q_eng"],
            "p_net": costing_results["power_balance"]["p_electric_net"],
            "p_fusion": costing_results["power_balance"]["p_fusion"],
            "p_thermal": costing_results["power_balance"]["p_thermal"],
            "p_electric_gross": costing_results["power_balance"]["p_electric_gross"],
        },
        
        # Annualized cost parameters from costing module for cashflow engine
        "costing_fixed_om_per_mw": costing_results.get("costing_fixed_om_per_mw", 60000.0),
        "costing_annual_fuel_cost": costing_results.get("costing_annual_fuel_cost", 0.0),
        
        # Include volumes for reference
        "volumes": costing_results.get("volumes", {}),
    }
    
    return result
