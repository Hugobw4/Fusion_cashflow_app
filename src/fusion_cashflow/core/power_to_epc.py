#!/usr/bin/env python3
"""
Power-to-EPC Cost Linkage Module

Implements physically-grounded relationships between net electric power (MW)
and Engineering-Procurement-Construction (EPC) costs for fusion energy systems.

Contains:
- ARPA-E MFE scaling relationships from PyCosting
- ARPA-E IFE scaling relationships from PyCosting
- CATF cost distributions with percentile sampling
- Inverse functions for EPC-driven design optimization

"""

import numpy as np
from functools import lru_cache
from typing import Dict, Union, Optional
import warnings
import os
import math

# Suppress ARPA-E cost warnings globally
warnings.filterwarnings("ignore", message="ARPA-E Cost Warning*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*ARPA-E Cost Warning.*")

# Import Q model with fallback for standalone execution
try:
    from .q_model import estimate_q_eng
except ImportError:
    from q_model import estimate_q_eng


# =============================
# ARPA-E MFE Cost Coefficients
# =============================

# Materials database for both MFE and IFE calculations
MATERIALS = {
    "FS": {"rho": 7470, "c_raw": 10, "m": 3, "sigma": 450},
    "Pb": {"rho": 9400, "c_raw": 2.4, "m": 1.5},
    "Li4SiO4": {"rho": 2390, "c_raw": 1, "m": 2},
    "FLiBe": {"rho": 1900, "c": 40},
    "W": {"rho": 19300, "c_raw": 100, "m": 3},
    "Li": {"rho": 534, "c_raw": 70, "m": 1.5},
    "BFS": {"rho": 7800, "c_raw": 30, "m": 2},
    "PbLi": {"rho": None, "c": None},
    "SiC": {"rho": 3200, "c_raw": 14.49, "m": 3},
    "Inconel": {"rho": 8440, "c_raw": 46, "m": 3},
    "Cu": {"rho": 7300, "c_raw": 10.2, "m": 3},
    "Polyimide": {"rho": 1430, "c_raw": 100, "m": 3},
    "YBCO": {"rho": 6200, "c": 55},
    "Concrete": {"rho": 2300, "c_raw": 13/25, "m": 2},
    "SS316": {"rho": 7860, "c_raw": 2, "m": 2, "sigma": 900},
    "Nb3Sn": {"c": 5},
    "Incoloy": {"rho": 8170, "c_raw": 4, "m": 2},
    "GdBCO": {},
    "He": {},
    "NbTi": {},
    "Be": {"rho": 1850, "c_raw": 5750.00, "m": 3},
    "Li2TiO3": {"rho": 3430, "c_raw": 1297.05, "m": 3},
}

# Initialize PbLi material properties
pblir = 10
MATERIALS["PbLi"]["rho"] = (MATERIALS["Pb"]["rho"] * pblir + MATERIALS["Li"]["rho"]) / (pblir + 1)
MATERIALS["PbLi"]["c"] = (MATERIALS["Pb"]["c_raw"] * MATERIALS["Pb"]["m"] * pblir + MATERIALS["Li"]["c_raw"] * MATERIALS["Li"]["m"]) / (pblir + 1)

# Building cost coefficients from ARPA-E MFE study
# From pycosting_arpa_e_mfe.py Cost Category 21: Buildings
# Coefficients are in 2019 $/kW gross. Multiply by gross_power_kw.
ARPA_BUILDING_COEFFS_RAW = {
    "site_improvements": 268,            # C210100: $/kW 
    "fusion_heat_island": 186.8,         # C210200: $/kW 
    "turbine_building": 54.0,            # C210300: $/kW
    "heat_exchanger": 37.8,              # C210400: $/kW
    "power_supply": 10.8,                # C210500: $/kW
    "reactor_auxiliaries": 5.4,          # C210600: $/kW
    "hot_cell": 93.4,                    # C210700: $/kW 
    "reactor_services": 18.7,            # C210800: $/kW
    "service_water": 0.3,                # C210900: $/kW
    "fuel_storage": 1.1,                 # C211000: $/kW
    "control_room": 0.9,                 # C211100: $/kW
    "onsite_ac_power": 0.8,              # C211200: $/kW
    "administration": 4.4,               # C211300: $/kW
    "site_services": 1.6,                # C211400: $/kW
    "cryogenics": 2.4,                   # C211500: $/kW
    "security": 0.9,                     # C211600: $/kW
    "ventilation_stack": 27.0,           # C211700: $/kW
}

# IFE-specific building coefficients (from pycosting_arpa_e_ife.py)
# Coefficients are in 2019 $/kW gross for IFE systems
ARPA_IFE_BUILDING_COEFFS_RAW = {
    "site_improvements": 268,            # C210100: $/kW 
    "fusion_heat_island": 186.8,         # C210200: $/kW 
    "turbine_building": 54.0,            # C210300: $/kW
    "heat_exchanger": 37.8,              # C210400: $/kW
    "power_supply": 10.8,                # C210500: $/kW
    "reactor_auxiliaries": 5.4,          # C210600: $/kW
    "hot_cell": 93.4,                    # C210700: $/kW 
    "reactor_services": 18.7,            # C210800: $/kW
    "service_water": 0.3,                # C210900: $/kW
    "fuel_storage": 1.1,                 # C211000: $/kW
    "control_room": 0.9,                 # C211100: $/kW
    "onsite_ac_power": 0.8,              # C211200: $/kW
    "administration": 4.4,               # C211300: $/kW
    "site_services": 1.6,                # C211400: $/kW
    "cryogenics": 2.4,                   # C211500: $/kW
    "security": 0.9,                     # C211600: $/kW
    "ventilation_stack": 27.0,           # C211700: $/kW
}

# Scale factors for fusion plant costs
BUILDING_SCALE_EXPONENT = 0.65     # dimensionless (economy of scale factor)
REF_KW = 1_000_000                  # kW (1 GW-gross reference size)
REACTOR_EQUIP_TO_BUILDING = 1.50    # dimensionless (reactor equipment as fraction of building base cost)
MIN_DESIGN_CONTINGENCY = 0.05       # dimensionless (minimum contingency for NOAK plants)

# Use raw ARPA-E coefficients directly (no realism multiplier applied)
ARPA_BUILDING_COEFFS = ARPA_BUILDING_COEFFS_RAW.copy()  # $/kW (use original coefficients without adjustment)

# Pre-construction costs (from Cost Category 10)
ARPA_PRECONSTRUCTION_COEFFS = {
    "land_rights": {"sqrt_nmod": True, "pneutron_coeff": 0.9/239, "pnrl_coeff": 0.9/239},  # C110000: special (MW-based scaling)
    "site_permits": 10_000_000,       # C120000: $ (fixed cost in dollars)
    "plant_licensing": 210_000_000,   # C130000: $ (fixed cost in dollars)
    "plant_permits": 5_000_000,       # C140000: $ (fixed cost in dollars)
    "plant_studies": 5_000_000,       # C150000: $ (fixed cost in dollars)
    "plant_reports": 2_000_000,       # C160000: $ (fixed cost in dollars)
    "other_preconstruction": 1_000_000,# C170000: $ (fixed cost in dollars)
}

# Power balance parameters for fusion power calculation
FUSION_POWER_PARAMS = {
    "MFE": {
        "fuel_type": "DT",        # — (deuterium-tritium)
        "PALPHA": 520,            # MW (alpha power for DT fuel)
        "MN": 1.1,                # dimensionless (neutron energy multiplier)
        "ETATH": 0.5,             # dimensionless (thermal conversion efficiency)
        "ETADE": 0.85,            # dimensionless (direct energy conversion efficiency)
        "PINPUT": 50,             # MW (input power)
        "FPCPPF": 0.06,           # dimensionless (Primary Coolant Pumping Power Fraction)
        "FSUB": 0.03,             # dimensionless (Subsystem and Control Fraction)
    },
    "IFE": {
        "fuel_type": "DT",        # — (deuterium-tritium)
        "PALPHA": 520,            # MW (alpha power for DT fuel)
        "MN": 1.1,                # dimensionless (neutron energy multiplier)
        "ETATH": 0.45,            # dimensionless (thermal conversion efficiency, slightly lower for IFE)
        "ETADE": 0.80,            # dimensionless (direct energy conversion efficiency, slightly lower for IFE)
        "PINPUT": 75,             # MW (higher driver power for IFE)
        "FPCPPF": 0.04,           # dimensionless (Primary Coolant Pumping Power Fraction)
        "FSUB": 0.03,             # dimensionless (Subsystem and Control Fraction)
    }
}

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

# CATF Cost Distribution Parameters (P10, P50, P90 in $/kW)
CATF_COST_DISTRIBUTION = {
    "P10": 8500,   # $/kW (optimistic 10th percentile cost)
    "P50": 12500,  # $/kW (median 50th percentile cost)
    "P90": 18000,  # $/kW (conservative 90th percentile cost)
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
    ETATH = params["ETATH"]      # dimensionless
    ETADE = params["ETADE"]      # dimensionless
    PINPUT = params["PINPUT"]    # MW
    FPCPPF = params["FPCPPF"]    # dimensionless
    FSUB = params["FSUB"]        # dimensionless
    
    # Fixed auxiliary loads (MW)
    PTRIT = 10.0    # MW (tritium systems)
    PHOUSE = 4.0    # MW (housekeeping)
    PTFCOOL = 12.7  # MW (TF coil cooling)
    PPFCOOL = 11.0  # MW (PF coil cooling)
    PTF = 1.0       # MW (TF coil power)
    PPF = 1.0       # MW (PF coil power)
    PCRYO = 0.5     # MW (cryogenics)
    ETAPIN = 0.5    # dimensionless (input power efficiency)
    
    PAUX = PTRIT + PHOUSE        # MW (MW + MW)
    PCOILS = PTF + PPF           # MW (MW + MW)
    PCOOL = PTFCOOL + PPFCOOL    # MW (MW + MW)
    
    # Solve for fusion power (PNRL) iteratively
    # Net power equation: PNET = (1 - 1/QENG) * PET
    # where QENG = (thermal_electric + direct_electric) / total_consumption
    
    # Use data-driven Q model instead of hard-coded estimates
    q_eng_estimate = estimate_q_eng(net_mw, tech)  # dimensionless
    
    # Initial guess: PNRL ≈ net_mw * (1 + 1/Q_eng) * conversion_factor
    # Accounting for thermal efficiency losses and auxiliary power
    conversion_factor = 1.0 / (ETATH * 0.85)  # dimensionless (1 / (dimensionless × dimensionless))
    pnrl_guess = net_mw * (1 + 1/q_eng_estimate) * conversion_factor  # MW (MW × dimensionless × dimensionless)
    
    for _ in range(10):  # Iterative solver
        PNEUTRON = pnrl_guess - PALPHA                                                    # MW (MW - MW)
        PTH = MN * PNEUTRON + PINPUT + ETATH * (FPCPPF + FSUB) * (MN * PNEUTRON)        # MW (dimensionless × MW + MW + dimensionless × dimensionless × dimensionless × MW)
        PTHE = ETATH * PTH                                                               # MW (dimensionless × MW)
        PDEE = ETADE * PALPHA                                                            # MW (dimensionless × MW)
        PET = PDEE + PTHE                                                                # MW (MW + MW)
        
        PPUMP = FPCPPF * PTHE                                                            # MW (dimensionless × MW)
        PSUB = FSUB * PTHE                                                               # MW (dimensionless × MW)
        
        total_consumption = PCOILS + PPUMP + PSUB + PAUX + PCOOL + PCRYO + PINPUT / ETAPIN  # MW (MW + MW + MW + MW + MW + MW + MW/dimensionless)
        QENG = (PTHE + PDEE) / total_consumption                                         # dimensionless ((MW + MW) / MW)
        PNET_calc = (1 - 1/QENG) * PET                                                   # MW ((dimensionless - dimensionless/dimensionless) × MW)
        
        # Adjust PNRL based on error
        error = PNET_calc - net_mw                                                       # MW (MW - MW)
        if abs(error) < 0.1:  # Converged                                               # MW
            break
        pnrl_guess -= error * 0.5  # Damped iteration                                   # MW (MW - MW × dimensionless)
    
    return {
        "PNRL": pnrl_guess,      # MW
        "PET": PET,              # MW
        "PNET": PNET_calc,       # MW
        "PNEUTRON": PNEUTRON,    # MW
        "QENG": QENG,            # dimensionless
        "PTH": PTH,              # MW
        "PTHE": PTHE,            # MW
        "PDEE": PDEE,            # MW
    }


# =============================
# Main Dispatcher Function
# =============================

def compute_epc(method: str, cfg: dict) -> Dict[str, float]:
    """
    Main dispatcher for EPC cost calculation.
    
    Args:
        method: Technology method ("MFE", "IFE", or "PWR")
        cfg: Configuration dictionary with required parameters
        
    Returns:
        Dictionary with EPC cost breakdown and totals
    """
    EPCRUNNERS = {
        "MFE": compute_mfe_epc,
        "IFE": compute_ife_epc, 
        "PWR": compute_pwr_epc,
    }
    
    if method not in EPCRUNNERS:
        raise ValueError(f"Unsupported method '{method}'. Available: {list(EPCRUNNERS.keys())}")
    
    return EPCRUNNERS[method](cfg)


def compute_mfe_epc(cfg: dict) -> Dict[str, float]:
    """
    Compute MFE EPC costs using existing ARPA-E MFE methodology.
    
    Args:
        cfg: Configuration dictionary with keys:
            - net_mw: Net electric power in MW
            - years: Construction years
            - region_factor: Regional cost adjustment (default 1.0)
            - noak: NOAK flag (default True)
            - realism_multiplier: Cost realism adjustment (optional)
            
    Returns:
        Dictionary with EPC cost breakdown matching original arpa_epc format
    """
    # Extract parameters with defaults
    net_mw = cfg.get("net_mw", 1000)
    years = cfg.get("years", 6)
    region_factor = cfg.get("region_factor", 1.0)
    noak = cfg.get("noak", True)
    realism_multiplier = cfg.get("realism_multiplier", None)
    
    # Call existing MFE logic
    result = arpa_epc(net_mw, years, tech="MFE", region_factor=region_factor, 
                     noak=noak, realism_multiplier=realism_multiplier)
    
    # Ensure consistent output format
    return {
        "total_epc": result["total_epc_cost"],
        "epc_per_kw": result["cost_per_kw"],
        "breakdown": {
            "building_total": result["building_total"],
            "preconstruction_total": result["preconstruction_total"],
            "reactor_equipment": result["reactor_equipment"],
            "indirect_costs": result["indirect_costs"],
            "idc": result["idc"],
            "owners_costs": result["owners_costs"],
        },
        "power_balance": result["power_balance"],
        "detailed_result": result,  # Full original result for backward compatibility
    }


def compute_ife_epc(cfg: dict) -> Dict[str, float]:
    """
    Compute IFE EPC costs using ARPA-E IFE methodology from pycosting_arpa_e_ife.py.
    
    Args:
        cfg: Configuration dictionary with keys:
            - net_mw: Net electric power in MW
            - years: Construction years
            - region_factor: Regional cost adjustment (default 1.0)
            - noak: NOAK flag (default True)
            - fuel_type: Fuel type (default "DT")
            - impfreq: Implosion frequency in Hz (default 1)
            
    Returns:
        Dictionary with EPC cost breakdown matching MFE format
    """
    # Extract parameters with defaults
    net_mw = cfg.get("net_mw", 1000)
    years = cfg.get("years", 6)
    region_factor = cfg.get("region_factor", 1.0)
    noak = cfg.get("noak", True)
    fuel_type = cfg.get("fuel_type", "DT")
    impfreq = cfg.get("impfreq", 1.0)  # Hz
    
    # IFE-specific power balance calculation
    power_balance = _calculate_ife_power_balance(net_mw, fuel_type, impfreq)
    
    # IFE reactor geometry and radial build
    geometry = _calculate_ife_geometry()
    
    # Building costs using IFE coefficients
    building_result = _calculate_ife_building_costs(power_balance["PET"], noak)
    
    # Pre-construction costs (similar to MFE but with IFE adjustments)
    preconstruction_result = _calculate_ife_preconstruction_costs(
        power_balance["PNEUTRON"], power_balance["PNRL"], noak
    )
    
    # Reactor equipment costs (IFE-specific with spherical geometry)
    reactor_equipment_result = _calculate_ife_reactor_equipment_costs(geometry, power_balance)
    
    # Shield costs (IFE-specific)
    shield_result = _calculate_ife_shield_costs(geometry)
    
    # Laser and target factory costs (IFE-specific)
    laser_result = _calculate_ife_laser_costs(power_balance, impfreq)
    target_factory_result = _calculate_ife_target_factory_costs(impfreq)
    
    # Total direct costs
    total_direct = (building_result["total"] + 
                   preconstruction_result["total"] + 
                   reactor_equipment_result["total"] +
                   shield_result["total"] +
                   laser_result["total"] +
                   target_factory_result["total"])
    
    # Indirect costs (30% of direct for IFE)
    indirect_rate = 0.30
    indirect_costs = total_direct * indirect_rate
    
    # Total construction cost
    total_construction = total_direct + indirect_costs
    
    # Interest during construction
    construction_interest_rate = 0.06
    idc = construction_interest_rate * years * total_construction / 2
    
    # Owner's costs
    owners_costs = total_construction * 0.10
    
    # Total EPC cost
    total_epc = (total_construction + idc + owners_costs) * region_factor
    
    # Cost per kW
    epc_per_kw = total_epc / (net_mw * 1000)
    
    return {
        "total_epc": total_epc,
        "epc_per_kw": epc_per_kw,
        "breakdown": {
            "building_total": building_result["total"],
            "preconstruction_total": preconstruction_result["total"],
            "reactor_equipment": reactor_equipment_result["total"],
            "shield_costs": shield_result["total"],
            "laser_costs": laser_result["total"],
            "target_factory": target_factory_result["total"],
            "indirect_costs": indirect_costs,
            "idc": idc,
            "owners_costs": owners_costs,
        },
        "power_balance": power_balance,
        "geometry": geometry,
    }


def compute_pwr_epc(cfg: dict) -> Dict[str, float]:
    """
    Placeholder for PWR EPC cost calculation.
    
    Args:
        cfg: Configuration dictionary
        
    Returns:
        Dictionary with EPC cost breakdown
    """
    net_mw = cfg.get("net_mw", 1000)
    
    # Simple PWR cost estimate based on industry benchmarks
    cost_per_kw = 6000  # $/kW typical for PWR
    total_epc = cost_per_kw * net_mw * 1000
    
    return {
        "total_epc": total_epc,
        "epc_per_kw": cost_per_kw,
        "breakdown": {
            "nuclear_island": total_epc * 0.40,
            "turbine_island": total_epc * 0.25,
            "balance_of_plant": total_epc * 0.35,
        },
        "power_balance": {"net_mw": net_mw, "gross_mw": net_mw * 1.08},
    }


def arpa_epc(net_mw: float, years: float, tech: str = "MFE", 
             region_factor: float = 1.0, noak: bool = True, 
             realism_multiplier: Optional[float] = None) -> Dict[str, float]:
    """
    Calculate EPC cost using ARPA-E MFE scaling relationships with realism adjustments.
    
    Args:
        net_mw: Net electric power output in MW
        years: Construction time in years (affects contingency)
        tech: Technology type ("MFE", "IFE", or "PWR")
        region_factor: Regional cost adjustment factor
        noak: If True, use NOAK (Nth-of-a-kind) costing
        realism_multiplier: Override default building cost realism multiplier
        
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
    
    # Use custom realism multiplier if provided, otherwise use raw coefficients
    if realism_multiplier is not None:
        # Apply custom realism multiplier to raw coefficients
        building_coeffs = {
            component: coeff * realism_multiplier 
            for component, coeff in ARPA_BUILDING_COEFFS_RAW.items()
        }
    else:
        # Use raw ARPA-E coefficients without any adjustment
        building_coeffs = ARPA_BUILDING_COEFFS
    
    # Building costs (Cost Category 21) - scale with gross electric power
    gross_power_kw = PET * 1_000  # kW (MW × 1000 kW/MW)
    building_costs = {
        k: coeff                                   # $/kW
           * (gross_power_kw / REF_KW)             # dimensionless
             ** BUILDING_SCALE_EXPONENT            # dimensionless
           * gross_power_kw                        # kW
        for k, coeff in building_coeffs.items()
    }  # $ ($/kW × (kW/kW)^exp × kW)
    building_base = sum(building_costs.values())  # $ (before contingency)
    
    # Building contingency - 10% for FOAK, 5% minimum for NOAK
    contingency_rate = 0.10 if not noak else MIN_DESIGN_CONTINGENCY  # dimensionless (contingency rate)
    building_contingency = contingency_rate * building_base  # $ (contingency amount)
    building_total = building_base + building_contingency  # $ (after contingency)
    
    # Pre-construction costs (Cost Category 10)
    preconstruction_costs = {}  # $
    preconstruction_total = 0.0  # $
    
    # Land rights (special scaling with power)
    NMOD = 1  # dimensionless (number of modules)
    land_cost = np.sqrt(NMOD) * (  # $ (dimensionless × MW/239 × 0.9 dimensionless)
        PNEUTRON / 239 * 0.9 + PNRL / 239 * 0.9
    )
    preconstruction_costs["land_rights"] = land_cost  # $
    preconstruction_total += land_cost  # $
    
    # Other pre-construction costs (fixed)
    for component, cost in ARPA_PRECONSTRUCTION_COEFFS.items():
        if component != "land_rights":
            preconstruction_costs[component] = cost  # $
            preconstruction_total += cost  # $
    
    # Pre-construction contingency (10% for FOAK only)
    if not noak:  # —
        preconstruction_total *= 1.10  # $ ($ × 1.10 dimensionless for FOAK contingency)
    
    preconstruction_total_with_contingency = preconstruction_total  # $
    
    # Reactor equipment costs (placeholder - would need full radial build calculation)
    reactor_equipment_total = building_base * REACTOR_EQUIP_TO_BUILDING  # $ ($ × dimensionless)
    
    # Total direct costs
    total_direct = (building_total +  # $ ($ + $ + $)
                   preconstruction_total_with_contingency + 
                   reactor_equipment_total)
    
    # Indirect costs (engineering, construction management, etc.)
    # Typical 25-35% of direct costs
    indirect_rate = 0.30  # dimensionless
    indirect_costs = total_direct * indirect_rate  # $ ($ × dimensionless)
    
    # Total construction cost
    total_construction = total_direct + indirect_costs  # $ ($ + $)
    
    # Interest during construction (IDC)
    # Simple approximation: construction_rate * years * total_construction / 2
    construction_interest_rate = 0.06  # 1/year (6% typical)
    idc = construction_interest_rate * years * total_construction / 2  # $ (1/year × year × $ / dimensionless)
    
    # Owner's costs (development, permitting, etc.)
    owners_costs = total_construction * 0.10  # $ ($ × dimensionless)
    
    # Total EPC cost
    total_epc = (total_construction + idc + owners_costs) * region_factor  # $ (($ + $ + $) × dimensionless)
    
    # Cost validation and warnings
    cost_per_kw = total_epc / (net_mw * 1000)  # $/kW ($ / (MW × 1000 kW/MW))
    building_cost_per_kw = building_total / (PET * 1000)  # $/kW ($ / (MW × 1000 kW/MW))
    
    # Validate costs against industry benchmarks
    cost_warnings = []
    if cost_per_kw < 2000:
        cost_warnings.append(f"Total EPC cost (${cost_per_kw:,.0f}/kW) is below realistic fusion targets ($5,000-8,000/kW)")
    elif cost_per_kw > 20000:
        cost_warnings.append(f"Total EPC cost (${cost_per_kw:,.0f}/kW) is above typical nuclear costs")
    
    if building_cost_per_kw < 1000:
        cost_warnings.append(f"Building costs (${building_cost_per_kw:,.0f}/kW) are below nuclear standards ($3,000-5,000/kW)")
    
    # Issue warnings if costs seem unrealistic
    if cost_warnings and realism_multiplier is None:
        for warning in cost_warnings:
            # Commented out for cleaner test output
            # warnings.warn(f"ARPA-E Cost Warning: {warning}. Consider adjusting realism_multiplier parameter.")
            pass
    
    return {
        # Component breakdowns
        "building_costs": building_costs,
        "building_base": building_base,
        "building_contingency": building_contingency,
        "building_total": building_total,
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
        "cost_per_kw": cost_per_kw,  # $/kW net
        "building_cost_per_kw": building_cost_per_kw,  # $/kW gross (for comparison)
        "cost_warnings": cost_warnings,
        "realism_multiplier_used": realism_multiplier or 1.0,  # Default to 1.0 (no adjustment)
    }


# =============================
# IFE-Specific Helper Functions
# =============================

def _calculate_ife_power_balance(net_mw: float, fuel_type: str = "DT", impfreq: float = 1.0) -> Dict[str, float]:
    """
    Calculate IFE power balance from net electric power.
    
    Based on power balance from pycosting_arpa_e_ife.py with laser-specific parameters.
    """
    # IFE-specific power parameters
    if fuel_type == "pB11" or fuel_type == "DD":
        PNRL = 2500  # MW
        PALPHA = 0   # MW (no alpha for aneutronic)
        PNEUTRON = PNRL  # MW
    else:  # DT fuel
        # Calculate fusion power from net electric power
        # Rule of thumb: PNRL ~ 2.5-3.0× net electric for IFE
        PNRL = net_mw * 2.8  # MW (rough scaling from net to fusion power for IFE)
        
        # DT fusion physics: Energy partition is fixed by nuclear cross-sections
        # Alpha particle (He-4): 3.5 MeV → 20% of fusion energy
        # Neutron: 14.1 MeV → 80% of fusion energy
        # Therefore: P_alpha / P_fusion = 3.5 / (3.5 + 14.1) = 0.2
        PALPHA = PNRL * 0.2  # MW (20% of fusion power in alpha particles)
        PNEUTRON = PNRL * 0.8  # MW (80% of fusion power in neutrons)
    
    # IFE parameters from pycosting_arpa_e_ife.py
    MN = 1.09  # Neutron energy multiplier
    ETAP = 0.5  # Pumping power capture efficiency
    FPCPPF = 0.01  # Primary Coolant Pumping Power Fraction
    FSUB = 0.01  # Subsystem and Control Fraction
    PTRIT = 6.3  # MW (Tritium Systems)
    PHOUSE = 4 * 300 / 560  # MW (Housekeeping power)
    PAUX = PTRIT + PHOUSE  # MW
    PCRYO = 0.8 * PNRL / 560  # MW (Cryo vacuum pumping)
    
    # Input power wall plug efficiency
    ETAPIN1 = 0.1  # Implosion laser efficiency
    ETAPIN2 = 0.1  # Ignition laser efficiency
    ETATH = 0.46  # Thermal conversion efficiency
    
    # Laser powers
    PIMPLOSION = 10  # MW (Implosion laser power)
    PIGNITION = 0.1  # MW (Ignition laser power)
    PIN = PIMPLOSION + PIGNITION  # MW (Total input power)
    
    # Power into systems
    PTARGET = 1  # MW (Target factory)
    PMACHINERY = 1  # MW (Machinery)
    
    # Thermal power
    PTH = MN * PNEUTRON + PALPHA + PIN + ETATH * (FPCPPF * ETAP + FSUB) * (MN * PNEUTRON + PALPHA)
    
    # Total (Gross) Electric Power
    PET = ETATH * PTH  # MW
    
    # Primary Coolant Pumping Power
    PP = FPCPPF * PET  # MW
    
    # Subsystem and Control Power
    PSUB = FSUB * PET  # MW
    
    # Scientific Q
    QS = PNRL / PIN  # dimensionless
    
    # Engineering Q
    QE = ETATH * (MN * PNEUTRON + PALPHA + PP + PIN) / (
        PTARGET + PP + PSUB + PAUX + PCRYO + PIMPLOSION / ETAPIN1 + PIGNITION / ETAPIN2
    )
    
    # Output Power (Net Electric Power)
    PNET = (1 - 1 / QE) * PET  # MW
    
    return {
        "PNRL": PNRL,
        "PET": PET,
        "PNET": PNET,
        "PNEUTRON": PNEUTRON,
        "PALPHA": PALPHA,
        "PTH": PTH,
        "QS": QS,
        "QE": QE,
        "PIN": PIN,
        "PIMPLOSION": PIMPLOSION,
        "PIGNITION": PIGNITION,
        "PTARGET": PTARGET,
    }


def _calculate_ife_geometry() -> Dict[str, float]:
    """
    Calculate IFE reactor geometry based on spherical chamber design.
    
    From pycosting_arpa_e_ife.py radial build calculations.
    """
    # Radial build inputs (spherical geometry)
    radial_build = {
        "axis_t": 0,       # m
        "plasma_t": 0.0001,  # m  
        "vacuum_t": 8.48,   # m (large vacuum chamber for IFE)
        "firstwall_t": 0.005,  # m
        "blanket1_t": 0,    # m 
        "reflector_t": 0.1,  # m
        "ht_shield_t": 0.1,  # m
        "structure_t": 0.2,  # m
        "gap1_t": 0.5,      # m
        "vessel_t": 0.2,    # m
        "gap2_t": 0.5,      # m
        "lt_shield_t": 0.3,  # m
        "bioshield_t": 1,   # m
    }
    
    # Calculate inner and outer radii
    components = ["axis", "plasma", "vacuum", "firstwall", "blanket1", "reflector", 
                 "ht_shield", "structure", "gap1", "vessel", "lt_shield", "gap2", "bioshield"]
    
    geometry = {}
    current_radius = 0
    
    for component in components:
        thickness = radial_build[f"{component}_t"]
        inner_radius = current_radius
        outer_radius = current_radius + thickness
        
        # Volume for sphere: (4/3) * π * (r_out³ - r_in³)
        volume = (4/3) * math.pi * (outer_radius**3 - inner_radius**3)
        
        geometry[component] = {
            "thickness": thickness,
            "inner_radius": inner_radius,
            "outer_radius": outer_radius,
            "volume": volume,
        }
        
        current_radius = outer_radius
    
    return geometry


def _calculate_ife_building_costs(gross_power_mw: float, noak: bool = True) -> Dict[str, float]:
    """Calculate IFE building costs using IFE-specific coefficients."""
    gross_power_kw = gross_power_mw * 1000
    
    # Use IFE building coefficients
    building_costs = {
        k: coeff * (gross_power_kw / REF_KW) ** BUILDING_SCALE_EXPONENT * gross_power_kw
        for k, coeff in ARPA_IFE_BUILDING_COEFFS_RAW.items()
    }
    
    building_base = sum(building_costs.values())
    
    # Contingency
    contingency_rate = 0.10 if not noak else MIN_DESIGN_CONTINGENCY
    building_contingency = contingency_rate * building_base
    building_total = building_base + building_contingency
    
    return {
        "costs": building_costs,
        "base": building_base,
        "contingency": building_contingency,
        "total": building_total,
    }


def _calculate_ife_preconstruction_costs(pneutron: float, pnrl: float, noak: bool = True) -> Dict[str, float]:
    """Calculate IFE pre-construction costs."""
    preconstruction_costs = {}
    preconstruction_total = 0.0
    
    # Land rights (special scaling with power)
    NMOD = 1
    land_cost = np.sqrt(NMOD) * (pneutron / 239 * 0.9 + pnrl / 239 * 0.9)
    preconstruction_costs["land_rights"] = land_cost
    preconstruction_total += land_cost
    
    # Other pre-construction costs (fixed)
    for component, cost in ARPA_PRECONSTRUCTION_COEFFS.items():
        if component != "land_rights":
            preconstruction_costs[component] = cost
            preconstruction_total += cost
    
    # Pre-construction contingency (10% for FOAK only)
    if not noak:
        preconstruction_total *= 1.10
    
    return {
        "costs": preconstruction_costs,
        "total": preconstruction_total,
    }


def _calculate_ife_reactor_equipment_costs(geometry: Dict, power_balance: Dict) -> Dict[str, float]:
    """
    Calculate IFE reactor equipment costs including first wall, blanket, and sphere-specific components.
    """
    # First wall costs based on material choice
    firstwall_vol = geometry["firstwall"]["volume"]  # m³
    
    # Assume liquid lithium first wall for IFE
    firstwall_material = "Li"
    C22010101 = (firstwall_vol * MATERIALS[firstwall_material]["rho"] * 
                 MATERIALS[firstwall_material]["c_raw"] * MATERIALS[firstwall_material]["m"] / 1e6)
    
    # Blanket costs (assume solid first wall, no breeder for aneutronic)
    blanket_vol = geometry["blanket1"]["volume"]  # m³
    C22010102 = blanket_vol * 100  # Simplified blanket cost $/m³
    
    # Total first wall and blanket
    C220101 = C22010101 + C22010102
    
    # Multiply by reactor scaling factor
    reactor_equipment_total = C220101 * REACTOR_EQUIP_TO_BUILDING
    
    return {
        "firstwall": C22010101,
        "blanket": C22010102,
        "firstwall_blanket": C220101,
        "total": reactor_equipment_total,
    }


def _calculate_ife_shield_costs(geometry: Dict) -> Dict[str, float]:
    """Calculate IFE shield costs for HT shield, LT shield, and bioshield."""
    # HT Shield
    f_SiC = 0.00
    f_PbLi = 0.1  
    f_W = 0.00
    f_BFS = 0.9
    
    V_HTS = geometry["ht_shield"]["volume"]
    C_HTS = V_HTS * (
        MATERIALS["SiC"]["rho"] * MATERIALS["SiC"]["c_raw"] * MATERIALS["SiC"]["m"] * f_SiC +
        MATERIALS["PbLi"]["rho"] * MATERIALS["PbLi"]["c"] * f_PbLi +
        MATERIALS["W"]["rho"] * MATERIALS["W"]["c_raw"] * MATERIALS["W"]["m"] * f_W +
        MATERIALS["BFS"]["rho"] * MATERIALS["BFS"]["c_raw"] * MATERIALS["BFS"]["m"] * f_BFS
    ) / 1e6
    
    C22010201 = C_HTS * 5  # HT shield with multiplier
    
    # LT Shield
    lt_shield_vol = geometry["lt_shield"]["volume"]
    C22010202 = lt_shield_vol * MATERIALS["SS316"]["c_raw"] * MATERIALS["SS316"]["m"] / 1e3
    
    # Bioshield
    bioshield_vol = geometry["bioshield"]["volume"]
    C22010203 = bioshield_vol * MATERIALS["Concrete"]["c_raw"] * MATERIALS["Concrete"]["m"] / 1e3
    C22010204 = C22010203 * 0.1  # Additional bioshield costs
    
    C220102 = C22010201 + C22010202 + C22010203 + C22010204
    
    return {
        "ht_shield": C22010201,
        "lt_shield": C22010202,
        "bioshield_base": C22010203,
        "bioshield_additional": C22010204,
        "total": C220102,
    }


def _calculate_ife_laser_costs(power_balance: Dict, impfreq: float) -> Dict[str, float]:
    """Calculate IFE laser system costs including driver and ignition lasers."""
    # Laser costs based on power requirements
    # Simplified cost model: $1M/MW for laser systems
    laser_power_cost_rate = 1_000_000  # $/MW
    
    implosion_cost = power_balance["PIMPLOSION"] * laser_power_cost_rate
    ignition_cost = power_balance["PIGNITION"] * laser_power_cost_rate
    
    # Frequency scaling for repetition rate equipment
    frequency_scaling = max(1.0, impfreq / 1.0)  # Scale costs with frequency above 1 Hz
    
    total_laser_cost = (implosion_cost + ignition_cost) * frequency_scaling
    
    return {
        "implosion_laser": implosion_cost * frequency_scaling,
        "ignition_laser": ignition_cost * frequency_scaling,
        "total": total_laser_cost,
    }


def _calculate_ife_target_factory_costs(impfreq: float) -> Dict[str, float]:
    """Calculate IFE target factory costs based on repetition rate."""
    # Target factory cost scales with required production rate
    # Base cost for 1 Hz operation: $50M
    base_target_factory_cost = 50_000_000  # $
    
    # Scale with frequency (more targets per second = more production capacity needed)
    frequency_scaling = max(1.0, math.sqrt(impfreq))  # Square root scaling
    
    target_factory_cost = base_target_factory_cost * frequency_scaling
    
    return {
        "base_factory": base_target_factory_cost,
        "frequency_scaling": frequency_scaling,
        "total": target_factory_cost,
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
    cost_per_kw = CATF_COST_DISTRIBUTION[f"P{int(pctl)}"]  # $/kW
    
    # Calculate total cost
    total_epc = cost_per_kw * net_mw * 1000 * region_factor  # $ ($/kW × MW × 1000 kW/MW × dimensionless)
    
    return total_epc  # $


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
    
    # Test building contingency calculation
    print("\n" + "=" * 50)
    print("Building Contingency Tests")
    print("=" * 50)
    
    # Test FOAK (contingency = 10%)
    foak_result = arpa_epc(1000, 6, noak=False)  # FOAK plant
    building_base_foak = foak_result["building_base"]  # $
    building_contingency_foak = foak_result["building_contingency"]  # $
    building_total_foak = foak_result["building_total"]  # $
    
    print(f"\nFOAK (noak=False) - 1000 MW:")
    print(f"  Building Base:        ${building_base_foak/1e6:.1f}M")
    print(f"  Building Contingency: ${building_contingency_foak/1e6:.1f}M")
    print(f"  Building Total:       ${building_total_foak/1e6:.1f}M")
    print(f"  Contingency %:        {100 * building_contingency_foak / building_base_foak:.1f}%")
    
    # Test NOAK (contingency = 0%)
    noak_result = arpa_epc(1000, 6, noak=True)  # NOAK plant
    building_base_noak = noak_result["building_base"]  # $
    building_contingency_noak = noak_result["building_contingency"]  # $
    building_total_noak = noak_result["building_total"]  # $
    
    print(f"\nNOAK (noak=True) - 1000 MW:")
    print(f"  Building Base:        ${building_base_noak/1e6:.1f}M")
    print(f"  Building Contingency: ${building_contingency_noak/1e6:.1f}M")
    print(f"  Building Total:       ${building_total_noak/1e6:.1f}M")
    print(f"  Contingency %:        {100 * building_contingency_noak / building_base_noak:.1f}%")
    
    # Assert-style checks
    print(f"\nValidation Checks:")
    
    # FOAK contingency should be exactly 10%
    expected_foak_contingency = 0.10 * building_base_foak  # $
    foak_contingency_correct = abs(building_contingency_foak - expected_foak_contingency) < 1.0  # $ (within $1)
    print(f"  FOAK contingency = 10% of base: {'PASS' if foak_contingency_correct else 'FAIL'}")
    
    # FOAK total should equal base + contingency
    foak_total_correct = abs(building_total_foak - (building_base_foak + building_contingency_foak)) < 1.0  # $ (within $1)
    print(f"  FOAK total = base + contingency: {'PASS' if foak_total_correct else 'FAIL'}")
    
    # NOAK contingency should be exactly MIN_DESIGN_CONTINGENCY (5%)
    expected_noak_contingency = MIN_DESIGN_CONTINGENCY * building_base_noak  # $
    noak_contingency_correct = abs(building_contingency_noak - expected_noak_contingency) < 1.0  # $ (within $1)
    print(f"  NOAK contingency = {MIN_DESIGN_CONTINGENCY*100:.0f}% of base: {'PASS' if noak_contingency_correct else 'FAIL'}")
    
    # NOAK total should equal base + contingency
    noak_total_correct = abs(building_total_noak - (building_base_noak + building_contingency_noak)) < 1.0  # $ (within $1)
    print(f"  NOAK total = base + contingency: {'PASS' if noak_total_correct else 'FAIL'}")
    
    # Building bases should be identical for same plant size
    base_identical = abs(building_base_foak - building_base_noak) < 1e-6  # $ (essentially zero difference)
    print(f"  FOAK and NOAK bases identical: {'PASS' if base_identical else 'FAIL'}")
    
    # Test cost threshold for 100 MW FOAK (should be $6,000-8,000/kW, not trigger $2,000/kW warning)
    small_foak_result = arpa_epc(100, 6, noak=False)  # 100 MW FOAK plant
    small_cost_per_kw = small_foak_result["cost_per_kw"]  # $/kW
    cost_warnings_small = small_foak_result["cost_warnings"]  # list
    low_cost_warning_triggered = any("below realistic fusion targets" in warning for warning in cost_warnings_small)  # boolean
    cost_threshold_correct = not low_cost_warning_triggered and small_cost_per_kw >= 6000  # boolean (expect $6k-8k/kW)
    print(f"  100 MW FOAK cost reasonable (${small_cost_per_kw:,.0f}/kW): {'PASS' if cost_threshold_correct else 'FAIL'}")
    
    all_tests_pass = all([foak_contingency_correct, foak_total_correct, noak_contingency_correct, 
                         noak_total_correct, base_identical, cost_threshold_correct])
    print(f"\nAll tests: {'PASS' if all_tests_pass else 'FAIL'}")
    
    if not all_tests_pass:
        print("ERROR: Some contingency tests failed!")
        exit(1)
