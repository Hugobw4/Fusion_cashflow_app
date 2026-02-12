"""Calculation stubs for remaining CAS accounts.

These are simplified placeholders that use $/kW formulas.
Full implementations would follow PyFECONS detailed calculations.
"""
from ..costing_data import CostingData
from ..units import M_USD
from ..enums_new import ReactorType
from .conversions import compute_cost_from_factor, apply_fuel_scaling

# Import IFE-specific calculations
try:
    from .ife_power_balance import compute_ife_driver_cost, compute_ife_target_factory_cost
    IFE_MODULE_AVAILABLE = True
except ImportError:
    IFE_MODULE_AVAILABLE = False


def compute_cas10(data: CostingData) -> None:
    """CAS 10 - Pre-construction costs."""
    inp = data.cas10_in
    out = data.cas10_out
    
    out.C100100 = inp.land_cost
    out.C100200 = inp.site_prep_cost
    out.C100300 = inp.permits_cost
    out.C100400 = inp.environmental_cost
    out.C100500 = inp.conceptual_design_cost
    out.C100600 = inp.preliminary_design_cost
    
    out.compute_total()


def compute_cas2202(data: CostingData) -> None:
    """CAS 22.02 - Main heat transfer system (simplified).
    
    For IFE, this includes the driver cost (laser/ion beam).
    For MFE, this is coolant loops and heat exchangers.
    """
    p_et = data.basic.p_et
    
    # Check if IFE - use driver costing
    if data.basic.reactor_type == ReactorType.IFE_LASER and IFE_MODULE_AVAILABLE:
        cost = compute_ife_driver_cost(data)
    else:
        # MFE: standard heat transfer system
        cost = compute_cost_from_factor(50.0, p_et)  # ~50 $/kW estimate
    
    data.cas22_out.cas2202.C220200 = cost


# NOTE: compute_cas2203 moved to calculations/cas220103.py for detailed magnet costing


def compute_cas2204(data: CostingData) -> None:
    """CAS 22.04 - Supplementary heating or target factory.
    
    For IFE, this is the target factory (continuous target production).
    For MFE, this is auxiliary heating (NBI, ECRH, ICRH).
    """
    p_et = data.basic.p_et
    
    # Check if IFE - use target factory costing
    if data.basic.reactor_type == ReactorType.IFE_LASER and IFE_MODULE_AVAILABLE:
        cost = compute_ife_target_factory_cost(data)
    else:
        # MFE: auxiliary heating systems
        cost = compute_cost_from_factor(30.0, p_et)
    
    data.cas22_out.cas2204.C220400 = cost


def compute_cas2205(data: CostingData) -> None:
    """CAS 22.05 - Primary structure (simplified)."""
    p_et = data.basic.p_et
    cost = compute_cost_from_factor(20.0, p_et)
    data.cas22_out.cas2205.C220500 = cost


def compute_cas2206(data: CostingData) -> None:
    """CAS 22.06 - Vacuum system (simplified)."""
    p_et = data.basic.p_et
    cost = compute_cost_from_factor(15.0, p_et)
    data.cas22_out.cas2206.C220600 = cost


def compute_cas2207(data: CostingData) -> None:
    """CAS 22.07 - Power supplies (simplified)."""
    p_et = data.basic.p_et
    cost = compute_cost_from_factor(25.0, p_et)
    data.cas22_out.cas2207.C220700 = cost


def compute_cas23(data: CostingData) -> None:
    """CAS 23 - Turbine plant."""
    p_et = data.basic.p_et
    data.cas23_out.C230000 = compute_cost_from_factor(79.0, p_et)


def compute_cas24(data: CostingData) -> None:
    """CAS 24 - Electric plant."""
    p_et = data.basic.p_et
    data.cas24_out.C240000 = compute_cost_from_factor(47.0, p_et)


def compute_cas25(data: CostingData) -> None:
    """CAS 25 - Miscellaneous plant equipment."""
    p_et = data.basic.p_et
    data.cas25_out.C250000 = compute_cost_from_factor(30.0, p_et)


def compute_cas26(data: CostingData) -> None:
    """CAS 26 - Heat rejection."""
    p_et = data.basic.p_et
    data.cas26_out.C260000 = compute_cost_from_factor(29.0, p_et)


def compute_cas27(data: CostingData) -> None:
    """CAS 27 - Fuel handling."""
    p_et = data.basic.p_et
    fuel_type = data.basic.fuel_type.value
    cost = compute_cost_from_factor(46.0, p_et)
    cost = apply_fuel_scaling(cost, fuel_type)
    data.cas27_out.C270000 = cost


def compute_cas28(data: CostingData) -> None:
    """CAS 28 - Instrumentation and control."""
    p_et = data.basic.p_et
    data.cas28_out.C280000 = compute_cost_from_factor(19.0, p_et)


def compute_cas29(data: CostingData) -> None:
    """CAS 29 - Contingency."""
    if data.basic.is_foak:
        # 10% of CAS 21-28
        subtotal = sum([
            data.cas21_out.C210000,
            data.cas22_out.C220000,
            data.cas23_out.C230000,
            data.cas24_out.C240000,
            data.cas25_out.C250000,
            data.cas26_out.C260000,
            data.cas27_out.C270000,
            data.cas28_out.C280000,
        ])
        data.cas29_out.C290000 = M_USD(subtotal * 0.10)
    else:
        data.cas29_out.C290000 = M_USD(0.0)


def compute_cas30(data: CostingData) -> None:
    """CAS 30 - Indirect costs (construction services)."""
    p_net = data.basic.p_nrl
    construction_time = data.basic.construction_time_years
    factor = data.cas30_in.construction_services_factor  # 0.22 default
    
    # Formula: (p_net/150)^-0.5 × p_net × factor × construction_time
    # Guard: if p_net <= 0 the power balance is invalid; return zero cost
    if p_net <= 0:
        data.cas30_out.C300000 = M_USD(0.0)
        return
    cost = ((p_net / 150.0) ** -0.5) * p_net * factor * construction_time
    data.cas30_out.C300000 = M_USD(cost)


def compute_cas40(data: CostingData) -> None:
    """CAS 40 - Owner costs."""
    # Factor based on LSA level
    LSA_FACTORS = {1: 0.07, 2: 0.10, 3: 0.14, 4: 0.18}
    lsa = data.basic.lsa_level.value
    factor = LSA_FACTORS.get(lsa, 0.07)
    
    # Apply to C200000 (direct capital)
    c200000 = data.c200000
    data.cas40_out.C400000 = M_USD(c200000 * factor)


def compute_cas50(data: CostingData) -> None:
    """CAS 50 - Capitalized supplementary."""
    data.cas50_out.C500000 = M_USD(data.cas50_in.supplementary_cost_musd)


def compute_cas60(data: CostingData) -> None:
    """CAS 60 - Capitalized O&M (spares, initial inventory)."""
    data.cas60_out.C600000 = M_USD(data.cas60_in.spares_cost_musd)


def compute_cas70(data: CostingData) -> None:
    """CAS 70 - Annualized O&M."""
    p_net = data.basic.p_nrl
    # Formula: 60 × p_net × 1000 / 1e6 = 0.060 × p_net [M$/yr]
    data.cas70_out.C700000 = M_USD(60.0 * p_net * 1000.0 / 1e6)


def compute_cas80(data: CostingData) -> None:
    """CAS 80 - Annualized fuel costs."""
    cost_per_kg = data.cas80_in.dt_fuel_cost_per_kg
    annual_burn_kg = data.cas80_in.annual_fuel_burn_kg
    data.cas80_out.C800000 = M_USD(cost_per_kg * annual_burn_kg / 1e6)


def compute_cas90(data: CostingData) -> None:
    """CAS 90 - Annualized financial costs."""
    crf = data.basic.capital_recovery_factor
    tcc = data.total_capital_cost
    data.cas90_out.C900000 = M_USD(crf * tcc)


def compute_lcoe(data: CostingData) -> None:
    """Compute Levelized Cost of Electricity."""
    p_net = data.basic.p_nrl
    n_mod = data.basic.n_mod
    capacity_factor = data.basic.capacity_factor
    discount_rate = data.basic.discount_rate
    lifetime = data.basic.plant_lifetime_years
    
    # Annual costs
    c90 = data.cas90_out.C900000  # M$/yr
    c70 = data.cas70_out.C700000  # M$/yr
    c80 = data.cas80_out.C800000  # M$/yr
    
    # Annual energy
    annual_energy_mwh = 8760 * p_net * n_mod * capacity_factor
    
    if annual_energy_mwh > 0:
        # Capital component (annualized via CRF in CAS 90)
        capital_component = (c90 * 1e6) / annual_energy_mwh
        
        # O&M component (already annualized in CAS 70/80)
        om_component = ((c70 + c80) * 1e6) / annual_energy_mwh
        
        # Total LCOE (simple pre-tax, all costs already annualized)
        lcoe = capital_component + om_component
        
        data.lcoe_out.lcoe_usd_per_mwh = lcoe
        data.lcoe_out.capital_component = capital_component
        data.lcoe_out.om_component = om_component
        data.lcoe_out.fuel_component = (c80 * 1e6) / annual_energy_mwh
    else:
        data.lcoe_out.lcoe_usd_per_mwh = 0.0
