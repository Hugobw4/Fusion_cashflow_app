"""Backward-compatible adapter for PyFECONS costing.

This module provides the `compute_total_epc_cost(config: dict) -> dict` function
that maintains compatibility with the existing application while using the new
PyFECONS-based costing system internally.
"""
from typing import Dict, Any

from .costing_data import CostingData
from .units import MW, Meters, M_USD
from .enums_new import (
    ReactorType, FuelType, LSALevel, BlanketPrimaryCoolant,
    BlanketNeutronMultiplier, MagnetType, MagnetMaterialType
)

# Calculation modules
from .calculations.power_balance import compute_power_balance
from .calculations.volume import compute_all_volumes
from .calculations.cas21 import compute_cas21
from .calculations.cas220101 import compute_cas220101
from .calculations.cas220103 import compute_cas220103  # Detailed magnet costing
from .calculations.cas_calcs import (
    compute_cas10, compute_cas2202,
    compute_cas2204, compute_cas2205, compute_cas2206, compute_cas2207,
    compute_cas23, compute_cas24, compute_cas25, compute_cas26,
    compute_cas27, compute_cas28, compute_cas29, compute_cas30,
    compute_cas40, compute_cas50, compute_cas60, compute_cas70,
    compute_cas80, compute_cas90,
)


def _config_to_costing_data(config: dict) -> CostingData:
    """Convert flat config dict to CostingData dataclass.
    
    Args:
        config: Legacy config dict with keys like 'thermal_power_mw', 'q_plasma', etc.
        
    Returns:
        Populated CostingData instance
    """
    data = CostingData()
    
    # ===== BasicInputs =====
    if 'net_electric_mw' in config:
        data.basic.p_nrl = MW(config['net_electric_mw'])
    if 'thermal_power_mw' in config:
        data.basic.p_et = MW(config['thermal_power_mw'])
    
    if 'reactor_type' in config:
        rt_map = {
            # Legacy/raw codes\n            'tokamak': ReactorType.MFE_TOKAMAK,
            'mirror': ReactorType.MFE_MIRROR,
            'laser': ReactorType.IFE_LASER,
            # Dashboard codes (from get_config_from_widgets reactor_type_code mapping)
            'MFE': ReactorType.MFE_TOKAMAK,
            'IFE': ReactorType.IFE_LASER,
        }
        data.basic.reactor_type = rt_map.get(config['reactor_type'], ReactorType.MFE_TOKAMAK)
    
    if 'fuel_type' in config:
        ft_map = {
            # Canonical codes
            'DT': FuelType.DT, 'DD': FuelType.DD, 'DHe3': FuelType.DHe3, 'pB11': FuelType.pB11,
            # Dashboard codes (uppercase from fuel_type_code mapping)
            'DHE3': FuelType.DHe3, 'PB11': FuelType.pB11,
        }
        data.basic.fuel_type = ft_map.get(config['fuel_type'], FuelType.DT)
    
    if 'lsa_level' in config:
        data.basic.lsa_level = LSALevel(config['lsa_level'])
    
    if 'is_foak' in config:
        data.basic.is_foak = config['is_foak']
    elif 'noak' in config:
        data.basic.is_foak = not config['noak']  # noak=True → is_foak=False
    
    if 'capacity_factor' in config:
        data.basic.capacity_factor = config['capacity_factor']
    elif 'availability' in config:  # Legacy fallback
        data.basic.capacity_factor = config['availability']
    
    if 'plant_lifetime_years' in config:
        data.basic.plant_lifetime_years = int(config['plant_lifetime_years'])
    
    # ===== PowerBalanceInputs =====
    # Derive Q_plasma from fusion power and heating if not explicitly provided
    if 'q_plasma' in config:
        data.power_balance_in.q_plasma = config['q_plasma']
    elif 'p_nrl_fusion_power_mw' in config and 'auxiliary_power_mw' in config:
        p_heat = config['auxiliary_power_mw']
        if p_heat > 0:
            data.power_balance_in.q_plasma = config['p_nrl_fusion_power_mw'] / p_heat
    if 'heating_power_mw' in config:
        data.power_balance_in.p_heating = MW(config['heating_power_mw'])
    # Also accept 'auxiliary_power_mw' from dashboard (derived from P_fusion / Q)
    elif 'auxiliary_power_mw' in config:
        data.power_balance_in.p_heating = MW(config['auxiliary_power_mw'])
    if 'neutron_multiplication' in config:
        data.power_balance_in.neutron_multiplication = config['neutron_multiplication']
    if 'thermal_efficiency' in config:
        data.power_balance_in.eta_th = config['thermal_efficiency']
    
    # IFE power balance inputs
    if 'repetition_rate_hz' in config:
        data.power_balance_in.rep_rate_hz = config['repetition_rate_hz']
    if 'target_gain' in config:
        # target_yield_mj = driver_energy_mj × target_gain
        driver_energy = config.get('driver_energy_mj', 2.0)
        data.power_balance_in.target_yield_mj = driver_energy * config['target_gain']
    
    # ===== CAS220101Inputs (geometry & materials) =====
    if 'major_radius' in config:
        data.cas220101_in.r_plasma = Meters(config['major_radius'])
    if 'minor_radius' in config:
        data.cas220101_in.a_plasma = Meters(config['minor_radius'])
    if 'elongation' in config:
        data.cas220101_in.elon = config['elongation']
    if 'chamber_length' in config:
        data.cas220101_in.chamber_length = Meters(config['chamber_length'])
    
    if 'first_wall_thickness' in config:
        data.cas220101_in.first_wall_thickness = Meters(config['first_wall_thickness'])
    if 'blanket_thickness' in config:
        data.cas220101_in.blanket_thickness = Meters(config['blanket_thickness'])
    if 'shield_thickness' in config:
        data.cas220101_in.shield_thickness = Meters(config['shield_thickness'])
    
    # Map first_wall_material (handle all known formats)
    if 'first_wall_material' in config:
        fw_map = {
            # Dashboard format
            'Tungsten': 'W',
            'Beryllium': 'Be',
            'Liquid Lithium': 'Li',
            'FLiBe': 'FLiBe',
            # Legacy format with codes
            'Tungsten (W)': 'W',
            'Beryllium (Be)': 'Be',
            'Stainless Steel (SS316)': 'SS316',
            'Ferritic Steel (FMS)': 'FS',
            # Raw codes
            'W': 'W',
            'Be': 'Be',
            'Li': 'Li',
            'FS': 'FS',
            'SS316': 'SS316',
        }
        data.cas220101_in.first_wall_material = fw_map.get(
            config['first_wall_material'], 
            config['first_wall_material']  # Pass through if not in map
        )
    
    # Map blanket_type to blanket_breeder_material
    if 'blanket_type' in config:
        blanket_map = {
            # Dashboard format
            'Solid Breeder (Li2TiO3)': 'Li2TiO3',
            'Solid Breeder (Li4SiO4)': 'Li4SiO4',
            'Flowing Liquid Breeder (PbLi)': 'PbLi',
            'No Breeder (Aneutronic)': 'Li4SiO4',  # Default fallback
            # Raw codes
            'Li2TiO3': 'Li2TiO3',
            'Li4SiO4': 'Li4SiO4',
            'PbLi': 'PbLi',
            'FLiBe': 'FLiBe',
        }
        data.cas220101_in.blanket_breeder_material = blanket_map.get(
            config['blanket_type'], 'Li4SiO4'
        )
    
    # Map structure_material to blanket/shield structural materials
    if 'structure_material' in config:
        structure_map = {
            # Dashboard format
            'Stainless Steel (SS)': 'SS316',
            'Ferritic Steel (FMS)': 'FS',
            'ODS Steel': 'FS',  # Approximate as ferritic steel
            'Vanadium': 'V',
            # Raw codes
            'SS316': 'SS316',
            'FS': 'FS',
            'V': 'V',
        }
        struct_code = structure_map.get(config['structure_material'], 'FS')
        data.cas220101_in.blanket_structural_material = struct_code
        data.cas220101_in.shield_material = struct_code
    
    if 'blanket_structural_material' in config:
        data.cas220101_in.blanket_structural_material = config['blanket_structural_material']
    if 'shield_material' in config:
        data.cas220101_in.shield_material = config['shield_material']
    if 'blanket_coolant' in config:
        coolant_map = {
            'H2O': BlanketPrimaryCoolant.WATER,
            'He': BlanketPrimaryCoolant.HELIUM,
            'FLiBe': BlanketPrimaryCoolant.FLIBE,
            'PbLi': BlanketPrimaryCoolant.PBLI
        }
        data.cas220101_in.blanket_coolant = coolant_map.get(config['blanket_coolant'],
                                                             BlanketPrimaryCoolant.WATER)
    if 'blanket_multiplier' in config:
        mult_map = {
            'Be': BlanketNeutronMultiplier.BE,
            'Pb': BlanketNeutronMultiplier.PB,
            'None': BlanketNeutronMultiplier.NONE
        }
        data.cas220101_in.blanket_multiplier = mult_map.get(config['blanket_multiplier'],
                                                             BlanketNeutronMultiplier.BE)
    
    # ===== CAS2203Inputs (magnets) =====
    # Accept both 'magnet_type' (legacy) and 'magnet_technology' (dashboard) keys
    magnet_tech = config.get('magnet_type') or config.get('magnet_technology')
    if magnet_tech:
        mag_map = {
            # Dashboard format
            'HTS REBCO': MagnetType.HTS,
            'HTS Cable-in-Conduit': MagnetType.HTS,
            'LTS NbTi': MagnetType.LTS,
            'LTS Nb3Sn': MagnetType.LTS,
            'Copper (resistive)': MagnetType.COPPER,
            # Legacy/raw format
            'HTS': MagnetType.HTS,
            'LTS': MagnetType.LTS,
            'Copper': MagnetType.COPPER,
        }
        data.cas2203_in.magnet_type = mag_map.get(magnet_tech, MagnetType.HTS)
    
    if 'n_tf_coils' in config:
        data.cas2203_in.n_tf_coils = int(config['n_tf_coils'])
    
    return data


def _run_calculations(data: CostingData) -> None:
    """Execute all costing calculations in proper order.
    
    Args:
        data: CostingData instance (modified in place)
    """
    # 1. Power balance (sets p_et and p_nrl)
    compute_power_balance(data)
    
    # 2. Geometry (volumes)
    compute_all_volumes(data)
    
    # 3. CAS 10 - Pre-construction
    compute_cas10(data)
    
    # 4. CAS 21 - Buildings
    compute_cas21(data)
    
    # 5. CAS 22 - Reactor Plant Equipment
    compute_cas220101(data)  # First wall/blanket/shield
    compute_cas2202(data)    # Heat transfer
    compute_cas220103(data)  # Magnets (detailed material-based)
    compute_cas2204(data)    # Heating
    compute_cas2205(data)    # Structure
    compute_cas2206(data)    # Vacuum
    compute_cas2207(data)    # Power supplies
    
    # Aggregate CAS 22.01
    data.cas22_out.cas2201.compute_total()
    
    # Aggregate CAS 22
    data.cas22_out.compute_total()
    
    # 6. CAS 23-28 - Balance of plant
    compute_cas23(data)
    compute_cas24(data)
    compute_cas25(data)
    compute_cas26(data)
    compute_cas27(data)
    compute_cas28(data)
    
    # 7. CAS 29 - Contingency
    compute_cas29(data)
    
    # 8. Compute direct capital (C200000)
    data.compute_summary_totals()
    
    # 9. CAS 30 - Indirect
    compute_cas30(data)
    
    # 10. CAS 40 - Owner costs
    compute_cas40(data)
    
    # 11. CAS 50, 60 - Capitalized supplementary & O&M
    compute_cas50(data)
    compute_cas60(data)
    
    # 12. Recompute TCC/EPC
    data.compute_summary_totals()
    
    # 13. CAS 70, 80, 90 - Annualized costs
    compute_cas70(data)
    compute_cas80(data)
    compute_cas90(data)
    
    # NOTE: Costing LCOE removed. The cashflow engine computes the authoritative
    # post-tax NPV-based LCOE which is displayed on the dashboard.


def _costing_data_to_result_dict(data: CostingData) -> Dict[str, Any]:
    """Convert CostingData outputs to flat result dict (legacy format).
    
    Args:
        data: CostingData with computed outputs
        
    Returns:
        Dict matching legacy output format
    """
    def _real(v):
        """Coerce complex values to float (guards against negative-base exponents)."""
        return float(v.real) if isinstance(v, complex) else float(v)

    result = {}
    
    # ===== Power balance =====
    pb = data.power_balance_out
    result['power_balance'] = {
        'p_fusion': _real(pb.p_fusion),
        'p_thermal': _real(pb.p_thermal),
        'p_electric_gross': _real(pb.p_electric_gross),
        'p_net': _real(pb.p_net),
        'p_electric_net': _real(pb.p_net),  # Alias for backward compatibility
        'p_recirculating': _real(pb.p_recirculating),
        'eta_th': pb.eta_th,
    }
    result['q_eng'] = pb.q_eng
    
    # ===== Volumes =====
    result['volumes'] = {k: _real(v) for k, v in data.volumes.items()}
    
    # ===== CAS costs =====
    # CAS 10
    result['cas_10_preconstruction'] = _real(data.cas10_out.C100000)
    
    # CAS 21
    result['cas_21_total'] = _real(data.cas21_out.C210000)
    
    # CAS 21 sub-accounts (for dashboard display)
    result['building_reactor_building'] = _real(data.cas21_out.C210100)
    result['building_turbine_building'] = _real(data.cas21_out.C210200)
    result['building_auxiliary_buildings'] = _real(
        data.cas21_out.C210300 + data.cas21_out.C210400 + data.cas21_out.C210500 +
        data.cas21_out.C210600 + data.cas21_out.C210700 + data.cas21_out.C210800 +
        data.cas21_out.C210900 + data.cas21_out.C211000 + data.cas21_out.C211100 +
        data.cas21_out.C211200 + data.cas21_out.C211300 + data.cas21_out.C211400 +
        data.cas21_out.C211500 + data.cas21_out.C211600 + data.cas21_out.C211700
    )
    
    # CAS 22 (reactor equipment)
    result['cas_22_total'] = _real(data.cas22_out.C220000)
    result['cas_2201'] = _real(data.cas22_out.cas2201.C220100)
    result['cas_2202'] = _real(data.cas22_out.cas2202.C220200)
    result['cas_2203'] = _real(data.cas22_out.cas2203.C220300)
    result['cas_2204'] = _real(data.cas22_out.cas2204.C220400)
    result['cas_2205'] = _real(data.cas22_out.cas2205.C220500)
    result['cas_2206'] = _real(data.cas22_out.cas2206.C220600)
    result['cas_2207'] = _real(data.cas22_out.cas2207.C220700)
    
    # CAS 22.01.01 sub-components (for dashboard display)
    cas220101 = data.cas22_out.cas2201.cas220101
    result['firstwall'] = _real(cas220101.C22010101)
    result['blanket'] = _real(cas220101.C22010102)
    result['shield'] = _real(cas220101.C22010103)
    result['divertor'] = _real(cas220101.C22010104)
    
    # Legacy names (for backward compat)
    result['heating_systems'] = result['cas_2204']
    result['coolant_system'] = result['cas_2202']
    result['tritium_systems'] = _real(data.cas27_out.C270000)
    result['instrumentation'] = _real(data.cas28_out.C280000)
    result['vacuum_system'] = result['cas_2205']
    
    # CAS 23-28
    result['cas_23_turbine'] = _real(data.cas23_out.C230000)
    result['cas_24_electrical'] = _real(data.cas24_out.C240000)
    result['cas_25_misc'] = _real(data.cas25_out.C250000)
    result['cas_26_cooling'] = _real(data.cas26_out.C260000)
    result['cas_27_materials'] = _real(data.cas27_out.C270000)
    result['cas_28_instrumentation'] = _real(data.cas28_out.C280000)
    
    # CAS 29-40
    result['cas_29_contingency'] = _real(data.cas29_out.C290000)
    result['cas_30_indirect'] = _real(data.cas30_out.C300000)
    result['cas_40_owner_costs'] = _real(data.cas40_out.C400000)
    
    # Totals
    result['total_capital_cost'] = _real(data.total_capital_cost)
    result['total_epc_cost'] = _real(data.total_epc_cost)
    
    # Annualized costs from costing module (CAS 70/80/90) [M$/yr]
    result['cas_70_annual_om'] = _real(data.cas70_out.C700000)       # M$/yr
    result['cas_80_annual_fuel'] = _real(data.cas80_out.C800000)     # M$/yr
    result['cas_90_annual_capital'] = _real(data.cas90_out.C900000)  # M$/yr
    
    # Net electric power from power balance (MW) — used for per-kW and per-MW metrics
    p_net = _real(pb.p_net)
    
    # Derived O&M parameters for cashflow engine (so it uses physics-based values)
    if p_net > 0:
        # fixed_om_per_mw = CAS 70 annual O&M / P_net ($/MW/yr)
        result['costing_fixed_om_per_mw'] = (_real(data.cas70_out.C700000) * 1e6) / p_net
        # Annual fuel cost ($)
        result['costing_annual_fuel_cost'] = _real(data.cas80_out.C800000) * 1e6
    else:
        result['costing_fixed_om_per_mw'] = 60000.0
        result['costing_annual_fuel_cost'] = 0.0
    
    # Per-kW metrics
    if p_net > 0:
        result['cost_per_kw_net'] = _real(data.total_capital_cost) / (p_net * 1000.0)
        result['epc_per_kw_net'] = _real(data.total_epc_cost) / (p_net * 1000.0)
    else:
        result['cost_per_kw_net'] = 0.0
        result['epc_per_kw_net'] = 0.0
    
    # NOTE: Costing LCOE removed — cashflow engine computes the authoritative LCOE.
    # Returning 0 to avoid KeyError from any legacy code that accesses these keys.
    result['lcoe_usd_per_mwh'] = 0.0
    result['lcoe'] = 0.0
    
    # Additional aliases for test compatibility
    result['cas_30_indirect_costs'] = result['cas_30_indirect']
    
    return result


def compute_total_epc_cost(config: dict) -> dict:
    """Compute total EPC cost from configuration dict.
    
    This is the main entry point for backward compatibility with the existing
    application. It maintains the exact same signature as the old implementation.
    
    Args:
        config: Configuration dict with keys:
            - thermal_power_mw: Thermal power [MW]
            - net_electric_mw: Net electric power [MW]
            - q_plasma: Plasma Q
            - reactor_type: 'tokamak', 'mirror', or 'laser'
            - fuel_type: 'DT', 'DD', 'DHe3', 'pB11'
            - major_radius: Major radius [m] (tokamak)
            - minor_radius: Minor radius [m] (tokamak)
            - elongation: Elongation (tokamak)
            - blanket_thickness: Blanket thickness [m]
            - shield_thickness: Shield thickness [m]
            - first_wall_material: Material code (e.g., 'W')
            - magnet_type: 'HTS', 'LTS', 'Copper'
            ... and many more
            
    Returns:
        Result dict with keys:
            - power_balance: Dict of power flow
            - q_eng: Engineering Q
            - volumes: Dict of component volumes [m³]
            - cas_21_total: Buildings cost [M$]
            - cas_22_total: Reactor equipment cost [M$]
            - cas_2201: First wall/blanket/shield [M$]
            - cas_2203: Magnets [M$]
            - total_capital_cost: TCC [M$]
            - total_epc_cost: EPC [M$]
            - cost_per_kw_net: $/kW
            - epc_per_kw_net: $/kW
            - lcoe_usd_per_mwh: LCOE [$/MWh]
            ... and more
    """
    # 1. Convert config → CostingData
    data = _config_to_costing_data(config)
    
    # 2. Run all calculations
    _run_calculations(data)
    
    # 3. Convert CostingData → result dict
    result = _costing_data_to_result_dict(data)
    
    return result


# Legacy helper
def format_cost_summary(results: dict) -> str:
    """Format cost results as human-readable summary (legacy).
    
    Args:
        results: Result dict from compute_total_epc_cost
        
    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("FUSION REACTOR COST SUMMARY")
    lines.append("=" * 60)
    
    lines.append(f"\nPower Balance:")
    if 'power_balance' in results:
        pb = results['power_balance']
        lines.append(f"  Thermal Power:     {pb.get('p_thermal', 0):.1f} MW")
        lines.append(f"  Gross Electric:    {pb.get('p_electric_gross', 0):.1f} MW")
        lines.append(f"  Net Electric:      {pb.get('p_net', 0):.1f} MW")
        lines.append(f"  Engineering Q:     {results.get('q_eng', 0):.2f}")
    
    lines.append(f"\nCapital Costs:")
    lines.append(f"  CAS 21 (Buildings):        ${results.get('cas_21_total', 0):.1f} M")
    lines.append(f"  CAS 22 (Reactor):          ${results.get('cas_22_total', 0):.1f} M")
    lines.append(f"  CAS 23-28 (Balance):       ${sum([results.get(f'cas_2{i}_*', 0) for i in range(3, 9)]):.1f} M")
    lines.append(f"  CAS 29 (Contingency):      ${results.get('cas_29_contingency', 0):.1f} M")
    lines.append(f"  CAS 30 (Indirect):         ${results.get('cas_30_indirect', 0):.1f} M")
    lines.append(f"  CAS 40 (Owner):            ${results.get('cas_40_owner_costs', 0):.1f} M")
    lines.append(f"  ---")
    lines.append(f"  Total Capital Cost:        ${results.get('total_capital_cost', 0):.1f} M")
    lines.append(f"  Cost per kW:               ${results.get('cost_per_kw_net', 0):.0f}/kW")
    
    if 'lcoe_usd_per_mwh' in results:
        lines.append(f"\nLCOE:                        ${results['lcoe_usd_per_mwh']:.1f}/MWh")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)
