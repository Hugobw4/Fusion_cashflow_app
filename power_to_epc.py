#!/usr/bin/env python3
"""
Power-to-EPC Cost Linkage Module

Implements physically-grounded relationships between net electric power (MW)
and Engineering-Procurement-Construction (EPC) costs for fusion energy systems.

Contains:
- ARPA-E MFE scaling relationships from PyCosting
- CATF cost distributions with percentile sampling
- Inverse functions for EPC-driven design optimization

"""

import numpy as np
from functools import lru_cache
from typing import Dict, Union, Optional
import warnings

# Import Q model with fallback for standalone execution
try:
    from .q_model import estimate_q_eng
except ImportError:
    from q_model import estimate_q_eng


# =============================
# ARPA-E MFE Cost Coefficients
# =============================

# Building cost coefficients (in thousands of dollars per MW gross)
# From pycosting_arpa_e_mfe.py Cost Category 21: Buildings
# Formula in ARPA-E: coefficient * thousands_to_millions * PET
# where thousands_to_millions = 1/1000, so final formula: coefficient * PET / 1000 (millions)
ARPA_BUILDING_COEFFS = {
    "site_improvements": 268 * 0.5,      # C210100: DD scaling factor 0.5
    "fusion_heat_island": 186.8 * 0.5,   # C210200: DD scaling factor 0.5
    "turbine_building": 54.0,            # C210300
    "heat_exchanger": 37.8,              # C210400
    "power_supply": 10.8,                # C210500
    "reactor_auxiliaries": 5.4,          # C210600
    "hot_cell": 93.4 * 0.5,              # C210700: DD scaling factor 0.5
    "reactor_services": 18.7,            # C210800
    "service_water": 0.3,                # C210900
    "fuel_storage": 1.1,                 # C211000
    "control_room": 0.9,                 # C211100
    "onsite_ac_power": 0.8,              # C211200
    "administration": 4.4,               # C211300
    "site_services": 1.6,                # C211400
    "cryogenics": 2.4,                   # C211500
    "security": 0.9,                     # C211600
    "ventilation_stack": 27.0,           # C211700
}

# Pre-construction costs (from Cost Category 10)
ARPA_PRECONSTRUCTION_COEFFS = {
    "land_rights": {"sqrt_nmod": True, "pneutron_coeff": 0.9/239, "pnrl_coeff": 0.9/239},  # C110000
    "site_permits": 10,        # C120000
    "plant_licensing": 210,    # C130000
    "plant_permits": 5,        # C140000
    "plant_studies": 5,        # C150000
    "plant_reports": 2,        # C160000
    "other_preconstruction": 1,# C170000
}

# Power balance parameters for fusion power calculation
FUSION_POWER_PARAMS = {
    "MFE": {
        "fuel_type": "DT",
        "PALPHA": 520,  # Alpha power for DT fuel
        "MN": 1.1,      # Neutron energy multiplier
        "ETATH": 0.5,   # Thermal conversion efficiency
        "ETADE": 0.85,  # Direct energy conversion efficiency
        "PINPUT": 50,   # Input power
        "FPCPPF": 0.06, # Primary Coolant Pumping Power Fraction
        "FSUB": 0.03,   # Subsystem and Control Fraction
    },
    "IFE": {
        "fuel_type": "DT",
        "PALPHA": 520,
        "MN": 1.1,
        "ETATH": 0.45,  # Slightly lower for IFE
        "ETADE": 0.80,  # Slightly lower for IFE
        "PINPUT": 75,   # Higher driver power for IFE
        "FPCPPF": 0.04,
        "FSUB": 0.03,
    }
}

# Regional cost adjustment factors
REGIONAL_FACTORS = {
    "North America": 1.0,
    "Europe": 1.15,
    "China": 0.65,
    "India": 0.45,
    "Oceania": 1.05,
    "Southern Africa": 0.55,
    "MENA": 0.70,
    "Latin America": 0.60,
    "Russia & CIS": 0.50,
    "Southeast Asia": 0.50,
    "Sub-Saharan Africa": 0.45,
}

# CATF Cost Distribution Parameters (P10, P50, P90 in $/kW)
CATF_COST_DISTRIBUTION = {
    "P10": 8500,   # Optimistic
    "P50": 12500,  # Median
    "P90": 18000,  # Conservative
}


# =============================
# Core Functions
# =============================

@lru_cache(maxsize=256)
def _calculate_fusion_power_balance(net_mw: float, tech: str = "MFE") -> Dict[str, float]:
    """
    Calculate fusion power balance from net electric power.
    
    Reverse-engineers fusion power (PNRL) and gross electric (PET) from net MW.
    Based on power balance equations from pycosting_arpa_e_mfe.py.
    """
    params = FUSION_POWER_PARAMS.get(tech, FUSION_POWER_PARAMS["MFE"])
    
    # Constants from power balance
    PALPHA = params["PALPHA"]
    MN = params["MN"]
    ETATH = params["ETATH"]
    ETADE = params["ETADE"]
    PINPUT = params["PINPUT"]
    FPCPPF = params["FPCPPF"]
    FSUB = params["FSUB"]
    
    # Fixed auxiliary loads (MW)
    PTRIT = 10.0    # Tritium systems
    PHOUSE = 4.0    # Housekeeping
    PTFCOOL = 12.7  # TF coil cooling
    PPFCOOL = 11.0  # PF coil cooling
    PTF = 1.0       # TF coil power
    PPF = 1.0       # PF coil power
    PCRYO = 0.5     # Cryogenics
    ETAPIN = 0.5    # Input power efficiency
    
    PAUX = PTRIT + PHOUSE
    PCOILS = PTF + PPF
    PCOOL = PTFCOOL + PPFCOOL
    
    # Solve for fusion power (PNRL) iteratively
    # Net power equation: PNET = (1 - 1/QENG) * PET
    # where QENG = (thermal_electric + direct_electric) / total_consumption
    
    # Use data-driven Q model instead of hard-coded estimates
    q_eng_estimate = estimate_q_eng(net_mw, tech)
    
    # Initial guess: PNRL ≈ net_mw * (1 + 1/Q_eng) * conversion_factor
    # Accounting for thermal efficiency losses and auxiliary power
    conversion_factor = 1.0 / (ETATH * 0.85)  # Account for gross-to-net losses
    pnrl_guess = net_mw * (1 + 1/q_eng_estimate) * conversion_factor
    
    for _ in range(10):  # Iterative solver
        PNEUTRON = pnrl_guess - PALPHA
        PTH = MN * PNEUTRON + PINPUT + ETATH * (FPCPPF + FSUB) * (MN * PNEUTRON)
        PTHE = ETATH * PTH
        PDEE = ETADE * PALPHA
        PET = PDEE + PTHE
        
        PPUMP = FPCPPF * PTHE
        PSUB = FSUB * PTHE
        
        total_consumption = PCOILS + PPUMP + PSUB + PAUX + PCOOL + PCRYO + PINPUT / ETAPIN
        QENG = (PTHE + PDEE) / total_consumption
        PNET_calc = (1 - 1/QENG) * PET
        
        # Adjust PNRL based on error
        error = PNET_calc - net_mw
        if abs(error) < 0.1:  # Converged
            break
        pnrl_guess -= error * 0.5  # Damped iteration
    
    return {
        "PNRL": pnrl_guess,
        "PET": PET,
        "PNET": PNET_calc,
        "PNEUTRON": PNEUTRON,
        "QENG": QENG,
        "PTH": PTH,
        "PTHE": PTHE,
        "PDEE": PDEE,
    }


def arpa_epc(net_mw: float, years: float, tech: str = "MFE", 
             region_factor: float = 1.0, noak: bool = True) -> Dict[str, float]:
    """
    Calculate EPC cost using ARPA-E MFE scaling relationships.
    
    Args:
        net_mw: Net electric power output in MW
        years: Construction time in years (affects contingency)
        tech: Technology type ("MFE", "IFE", or "PWR")
        region_factor: Regional cost adjustment factor
        noak: If True, use NOAK (Nth-of-a-kind) costing
        
    Returns:
        Dictionary with cost breakdown and total EPC cost
    """
    if net_mw <= 0:
        raise ValueError("Net power must be positive")
    if years <= 0:
        raise ValueError("Construction years must be positive")
        
    # Get power balance
    power_balance = _calculate_fusion_power_balance(net_mw, tech)
    PET = power_balance["PET"]  # Gross electric power for building scaling
    PNEUTRON = power_balance["PNEUTRON"]
    PNRL = power_balance["PNRL"]
    
    # Building costs (Cost Category 21) - scale with gross electric power
    building_costs = {}
    building_total = 0.0
    # Original ARPA-E formula: coefficient * thousands_to_millions * PET
    # where thousands_to_millions = 1/1000
    # So: coefficient * PET / 1000 gives millions of dollars
    
    for component, coeff in ARPA_BUILDING_COEFFS.items():
        cost = coeff * PET / 1000 * 1e6  # coeff * PET * thousands_to_millions * millions_to_dollars
        building_costs[component] = cost
        building_total += cost
    
    # Building contingency
    if noak:
        building_contingency_rate = 0.15  # 15% for NOAK
    else:
        building_contingency_rate = 0.25  # 25% for FOAK
    
    building_contingency = building_total * building_contingency_rate
    building_total_with_contingency = building_total + building_contingency
    
    # Pre-construction costs (Cost Category 10)
    preconstruction_costs = {}
    preconstruction_total = 0.0
    
    # Land rights (special scaling with power)
    NMOD = 1  # Number of modules (typically 1)
    land_cost = np.sqrt(NMOD) * (
        PNEUTRON / 239 * 0.9 + PNRL / 239 * 0.9
    )
    preconstruction_costs["land_rights"] = land_cost
    preconstruction_total += land_cost
    
    # Other pre-construction costs (fixed)
    for component, cost in ARPA_PRECONSTRUCTION_COEFFS.items():
        if component != "land_rights":
            preconstruction_costs[component] = cost
            preconstruction_total += cost
    
    # Pre-construction contingency
    preconstruction_contingency = preconstruction_total * building_contingency_rate
    preconstruction_total_with_contingency = preconstruction_total + preconstruction_contingency
    
    # Reactor equipment costs (placeholder - would need full radial build calculation)
    # For now, use empirical scaling: ~40% of building costs for fusion systems
    reactor_equipment_total = building_total * 0.40
    
    # Total direct costs
    total_direct = (building_total_with_contingency + 
                   preconstruction_total_with_contingency + 
                   reactor_equipment_total)
    
    # Indirect costs (engineering, construction management, etc.)
    # Typical 25-35% of direct costs
    indirect_rate = 0.30
    indirect_costs = total_direct * indirect_rate
    
    # Total construction cost
    total_construction = total_direct + indirect_costs
    
    # Interest during construction (IDC)
    # Simple approximation: construction_rate * years * total_construction / 2
    construction_interest_rate = 0.06  # 6% typical
    idc = construction_interest_rate * years * total_construction / 2
    
    # Owner's costs (development, permitting, etc.)
    owners_costs = total_construction * 0.10  # 10% typical
    
    # Total EPC cost
    total_epc = (total_construction + idc + owners_costs) * region_factor
    
    return {
        # Component breakdowns
        "building_costs": building_costs,
        "building_total": building_total,
        "building_contingency": building_contingency,
        "preconstruction_costs": preconstruction_costs,
        "preconstruction_total": preconstruction_total,
        "reactor_equipment": reactor_equipment_total,
        
        # Major categories
        "total_direct": total_direct,
        "indirect_costs": indirect_costs,
        "total_construction": total_construction,
        "idc": idc,
        "owners_costs": owners_costs,
        
        # Final result
        "total_epc_cost": total_epc,
        
        # Power balance for reference
        "power_balance": power_balance,
        
        # Scaling info
        "net_mw": net_mw,
        "gross_mw": PET,
        "tech": tech,
        "years": years,
        "region_factor": region_factor,
        "noak": noak,
        "cost_per_kw": total_epc / (net_mw * 1000),  # $/kW net (convert MW to kW)
    }


def catf_epc(net_mw: float, pctl: float = 50, region_factor: float = 1.0) -> float:
    """
    Calculate EPC cost using CATF cost distribution.
    
    Args:
        net_mw: Net electric power in MW
        pctl: Percentile of cost distribution (10, 50, or 90)
        region_factor: Regional cost adjustment factor
        
    Returns:
        Total EPC cost in USD
    """
    if net_mw <= 0:
        raise ValueError("Net power must be positive")
    if pctl not in [10, 50, 90]:
        raise ValueError("Percentile must be 10, 50, or 90")
    
    # Get cost per kW from distribution
    cost_per_kw = CATF_COST_DISTRIBUTION[f"P{int(pctl)}"]
    
    # Calculate total cost
    total_epc = cost_per_kw * net_mw * 1000 * region_factor  # Convert MW to kW
    
    return total_epc


def inverse_mw_from_epc(target_epc: float, years: float, 
                       region_factor: float = 1.0, tech: str = "MFE",
                       method: str = "arpa") -> float:
    """
    Back-solve net electric power from target EPC cost.
    
    Uses bisection method to find MW that gives target EPC cost.
    
    Args:
        target_epc: Target EPC cost in USD
        years: Construction time in years
        region_factor: Regional cost adjustment factor
        tech: Technology type for ARPA method
        method: Cost method ("arpa" or "catf")
        
    Returns:
        Net electric power in MW
    """
    if target_epc <= 0:
        raise ValueError("Target EPC must be positive")
    
    def cost_function(mw):
        """Cost function for root finding."""
        if method == "arpa":
            result = arpa_epc(mw, years, tech, region_factor)
            return result["total_epc_cost"]
        elif method == "catf":
            return catf_epc(mw, 50, region_factor)  # Use P50 for inverse
        else:
            raise ValueError("Method must be 'arpa' or 'catf'")
    
    # Bisection search bounds
    mw_low = 10.0     # 10 MW minimum
    mw_high = 5000.0  # 5 GW maximum
    
    # Check bounds
    cost_low = cost_function(mw_low)
    cost_high = cost_function(mw_high)
    
    if target_epc < cost_low:
        warnings.warn(f"Target EPC ${target_epc/1e9:.1f}B below minimum feasible cost")
        return mw_low
    if target_epc > cost_high:
        warnings.warn(f"Target EPC ${target_epc/1e9:.1f}B above maximum feasible cost")
        return mw_high
    
    # Bisection method
    tolerance = 1e6  # $1M tolerance
    max_iterations = 50
    
    for _ in range(max_iterations):
        mw_mid = (mw_low + mw_high) / 2
        cost_mid = cost_function(mw_mid)
        
        if abs(cost_mid - target_epc) < tolerance:
            return mw_mid
        
        if cost_mid < target_epc:
            mw_low = mw_mid
        else:
            mw_high = mw_mid
    
    # Return best estimate if not converged
    return (mw_low + mw_high) / 2


# =============================
# Utility Functions
# =============================

def get_regional_factor(location: str) -> float:
    """Get regional cost factor from project location string."""
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


def cost_summary(net_mw: float, years: float = 6, tech: str = "MFE", 
                location: str = "USA") -> Dict[str, Union[float, str]]:
    """
    Generate comprehensive cost summary comparing ARPA and CATF methods.
    
    Args:
        net_mw: Net electric power in MW
        years: Construction years
        tech: Technology type
        location: Project location for regional factors
        
    Returns:
        Dictionary with cost comparison
    """
    region_factor = get_regional_factor(location)
    
    # ARPA-E costs
    arpa_result = arpa_epc(net_mw, years, tech, region_factor)
    arpa_cost = arpa_result["total_epc_cost"]
    arpa_cost_per_kw = arpa_result["cost_per_kw"]
    
    # CATF costs
    catf_p10 = catf_epc(net_mw, 10, region_factor)
    catf_p50 = catf_epc(net_mw, 50, region_factor)
    catf_p90 = catf_epc(net_mw, 90, region_factor)
    
    return {
        "net_mw": net_mw,
        "gross_mw": arpa_result["gross_mw"],
        "tech": tech,
        "location": location,
        "region_factor": region_factor,
        "years": years,
        
        # ARPA-E results
        "arpa_epc_total": arpa_cost,
        "arpa_cost_per_kw": arpa_cost_per_kw,
        "arpa_building_total": arpa_result["building_total"],
        "arpa_reactor_equipment": arpa_result["reactor_equipment"],
        "arpa_idc": arpa_result["idc"],
        
        # CATF results
        "catf_p10": catf_p10,
        "catf_p50": catf_p50,
        "catf_p90": catf_p90,
        "catf_p10_per_kw": catf_p10 / (net_mw * 1000),
        "catf_p50_per_kw": catf_p50 / (net_mw * 1000),
        "catf_p90_per_kw": catf_p90 / (net_mw * 1000),
        
        # Comparison
        "arpa_vs_catf_p50_ratio": arpa_cost / catf_p50,
        "cost_range_billion": (catf_p10 / 1e9, catf_p90 / 1e9),
    }


if __name__ == "__main__":
    # Example usage and testing
    print("Power-to-EPC Cost Module")
    print("=" * 40)
    
    # Test cases
    test_cases = [
        (500, "MFE", "ITER baseline"),
        (2231, "PWR", "Vogtle reference"),
        (1000, "IFE", "1 GW IFE plant"),
    ]
    
    for net_mw, tech, description in test_cases:
        print(f"\n{description}: {net_mw} MW {tech}")
        print("-" * 30)
        
        summary = cost_summary(net_mw, tech=tech)
        print(f"ARPA EPC: ${summary['arpa_epc_total']/1e9:.1f}B (${summary['arpa_cost_per_kw']:,.0f}/kW)")
        print(f"CATF P50: ${summary['catf_p50']/1e9:.1f}B (${summary['catf_p50_per_kw']:,.0f}/kW)")
        print(f"Gross/Net: {summary['gross_mw']:.0f}/{summary['net_mw']:.0f} MW")
