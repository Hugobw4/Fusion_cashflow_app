# =============================
# Fusion Project Whole-Life Cash Flow Engine
#
# Pure finance logic for:
#   - NPV, IRR, LCOE, DSCR, Payback, Equity Multiple
#   - Debt drawdown and amortization
#   - Region and risk mapping
#   - Scenario runner
#
# No plotting or file I/O in this module.
# =============================

import time
import warnings
import pandas as pd
import numpy as np
from scipy.special import expit
import numpy_financial as npf
import pandas_datareader.data as web
import datetime
import requests

# Import compute_epc for EPC costing (Q_eng derived inside costing module)
try:
    from .power_to_epc import compute_epc
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from power_to_epc import compute_epc
    except ImportError:
        compute_epc = None


# =============================
# EPC Cache — skip expensive costing when only financial params change
# =============================
_epc_cache_key = None
_epc_cache_result = None

# Config keys that affect EPC costing (physics / geometry / materials)
_EPC_RELEVANT_KEYS = (
    "reactor_type_code", "fuel_type_code", "noak", "power_method",
    "capacity_factor", "plant_lifetime",
    "net_electric_power_mw", "fusion_power_mw", "auxiliary_power_mw",
    "q_plasma", "thermal_efficiency",
    # Geometry
    "major_radius_m", "plasma_t", "vacuum_t", "firstwall_t", "blanket_t",
    "reflector_t", "ht_shield_t", "structure_t", "gap_t", "vessel_t",
    "coil_t", "elongation",
    # Materials
    "first_wall_material", "blanket_type", "structure_material",
    # Magnets
    "magnet_technology", "toroidal_field_tesla", "n_tf_coils",
    "tape_width_m_actual", "coil_thickness_m",
    # IFE
    "chamber_radius_m", "driver_energy_mj", "repetition_rate_hz", "target_gain",
    # Expert overrides
    "use_expert_geometry",
    "expert_major_radius_m", "expert_plasma_t", "expert_elongation",
    "expert_vacuum_t", "expert_firstwall_t", "expert_blanket_t",
    "expert_reflector_t", "expert_ht_shield_t", "expert_structure_t",
    "expert_gap_t", "expert_vessel_t", "expert_gap2_t",
    "expert_lt_shield_t", "expert_coil_t", "expert_bio_shield_t",
)


def _epc_cache_hash(config):
    """Build a hashable key from physics-relevant config values."""
    return tuple(config.get(k) for k in _EPC_RELEVANT_KEYS)


def _compute_epc_cached(config):
    """Return cached EPC result if physics params unchanged, else recompute."""
    global _epc_cache_key, _epc_cache_result
    key = _epc_cache_hash(config)
    if key == _epc_cache_key and _epc_cache_result is not None:
        return _epc_cache_result
    result = compute_epc(config)
    _epc_cache_key = key
    _epc_cache_result = result
    return result

# =============================
# Dictionaries & Mappings (Do Not Edit)
# =============================
REGION_MAP = {
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": [
        "France",
        "Germany",
        "UK",
        "Italy",
        "Spain",
        "Netherlands",
        "Norway",
        "Sweden",
        "Finland",
        "Poland",
        "Ukraine",
    ],
    "MENA": [
        "Saudi Arabia",
        "UAE",
        "Egypt",
        "Algeria",
        "Morocco",
        "Iran",
        "Iraq",
        "Jordan",
        "Tunisia",
        "Libya",
    ],
    "Southern Africa": ["South Africa", "Namibia", "Botswana", "Zimbabwe", "Zambia"],
    "Sub-Saharan Africa": ["Nigeria", "Kenya", "Ghana", "Tanzania", "Ethiopia"],
    "China": ["China"],
    "India": ["India"],
    "Southeast Asia": ["Thailand", "Vietnam", "Indonesia", "Philippines", "Malaysia"],
    "Latin America": ["Brazil", "Argentina", "Chile", "Peru", "Colombia", "Mexico"],
    "Russia & CIS": ["Russia", "Kazakhstan", "Uzbekistan", "Turkmenistan", "Armenia"],
    "Oceania": ["Australia", "New Zealand", "Fiji", "Papua New Guinea"],
}

RISK_FREE_RATE_MAP = {
    "North America": 0.0440,  # U.S. 10-year Treasury Note (TradingEconomics)
    "Europe": 0.0251,  # German 10-year Bund (FT Markets)
    "MENA": 0.0606,  # Saudi Arabia 10-year Govt Bond (FTSE Russell)
    "Southern Africa": 0.1006,  # South Africa 10-year Govt Bond (TradingEconomics)
    "Sub-Saharan Africa": 0.1895,  # Nigeria 10-year Govt Bond (TradingEconomics)
    "China": 0.0164,  # China 10-year Govt Bond (TradingEconomics)
    "India": 0.0639,  # India 10-year Govt Bond (TradingEconomics)
    "Southeast Asia": 0.0228,  # Singapore 10-year Govt Bond (TradingEconomics)
    "Latin America": 0.1384,  # Brazil 10-year Govt Bond (TradingEconomics)
    "Russia & CIS": 0.1498,  # Russia 10-year Govt Bond (TradingEconomics)
    "Oceania": 0.0419,  # Australia 10-year Govt Bond (TradingEconomics)
}

UNLEVERED_BETA_SCENARIOS = {
    "conservative": 0.70,  # Slightly higher risk profile
    "base": 0.55,  # Aligns with nuclear utilities average
    "aggressive": 0.85,  # First‐of‐a‐kind, high‐tech risk
}

REGION_INDEX_TICKERS = {
    "North America": "SPX",  # S&P 500 ETF
    "Europe": "DAX",  # Euro Stoxx 50
    "China": "SHC",  # SSE COMP
    "India": "SNX",  # SENSEX
    "Oceania": "AOR",  # ALL ORDINARIES
    "Southern Africa": "TOP40",  # JSE TOP40
    "MENA": "TASI",  # TASI
    "Latin America": "BVP",  # Bovespa Index - Brazil
    "Russia & CIS": "RTS",  # RTS
    "Southeast Asia": "NKX",  # NIKKEI225
    "Sub-Saharan Africa": "TOP40",  # JSE TOP40
}

REGIONAL_TAX_RATES = {
    "North America": 25.59, #https://taxfoundation.org/data/all/global/corporate-tax-rates-by-country-2024/
    "Europe": 20.18, #https://taxfoundation.org/data/all/global/corporate-tax-rates-by-country-2024/
    "China": 25.00, #https://taxsummaries.pwc.com/peoples-republic-of-china/corporate/taxes-on-corporate-income#:~:text=Under%20the%20CIT%20law%2C%20the,standard%20tax%20rate%20is%2025
    "India": 15.00, #https://taxsummaries.pwc.com/india/corporate/taxes-on-corporate-income#:~:text=Reduced%20rate%20of%20tax%20for,engaged%20in%20generation%20of%20electricity  ENERGY SECTOR SPECIFIC
    "Southern Africa": 27.00, # https://taxsummaries.pwc.com/south-africa/corporate/taxes-on-corporate-income#:~:text=For%20tax%20years%20ending%20before,or%20after%2031%20March%202023
    "Oceania": 24.38, #https://taxfoundation.org/data/all/global/corporate-tax-rates-by-country-2024/
    "MENA": 20.00, #https://taxsummaries.pwc.com/oman/corporate/taxes-on-corporate-income#:~:text=Petroleum%20income%20tax NO SPECIFIC ENERGY GENERATION TAX BUT PETROLEUM COMPANYS PAY 55% OMAN AND UAE
    "Sub-Saharan Africa": 27.28, #https://taxfoundation.org/data/all/global/corporate-tax-rates-by-country-2024/
    "Latin America": 27.36, #https://pages.stern.nyu.edu/~adamodar/pc/archives/countrytaxrates21.xls#:~:text=%5BXLS%5D%20https%3A%2F%2Fpages.stern.nyu.edu%2F,27.36
    "Russia & CIS": 25.00, #https://tass.com/economy/1816413#:~:text=MOSCOW%2C%20July%2012,of%20the%20corporate%20income%20tax
    "Southeast Asia": 23.00 # https://www.aseanbriefing.com/news/comparing-tax-rates-across-asean/#:~:text=Currently%2C%20most%20of%20the%20ASEAN,the%20overall%20cost%20of%20doing
}


# =============================
# Helper Functions
# =============================
def map_location_to_region(project_location):
    """Map a project location string to a region name."""
    project_location = project_location.lower().strip()
    for region, countries in REGION_MAP.items():
        for country in countries:
            if country.lower() in project_location:
                return region
    return "Unknown"


def get_risk_free_rate(region_name):
    """Retrieve the nominal risk-free rate for a given region."""
    # Falls back to a default of 3% if the region is not found.
    default_rate = 0.03
    return RISK_FREE_RATE_MAP.get(region_name, default_rate)


def get_unlevered_beta(scenario):
    """Retrieve the unlevered beta based on the chosen risk scenario."""
    # Falls back to 'base' if the scenario is not recognized.
    return UNLEVERED_BETA_SCENARIOS.get(scenario, UNLEVERED_BETA_SCENARIOS["base"])


def get_levered_beta(unlevered_beta, debt_pct, tax_rate):
    """Calculate the levered beta using the standard formula."""
    # beta_L = beta_U * [1 + (1 - tax_rate) * (debt/equity)]
    equity_pct = 1.0 - debt_pct
    if equity_pct == 0:
        raise ValueError("Equity percentage cannot be zero.")
    debt_to_equity = debt_pct / equity_pct
    return unlevered_beta * (1 + (1 - tax_rate) * debt_to_equity)


_stooq_cache = {}
_stooq_cache_date = None



HARDCODED_AVG_RETURNS = {
    'North America': 0.05862909229093205,
    'Europe': 0.051329545739963844,
    'China': 0.0363600914129143,
    'India': 0.11362815309866603,
    'Oceania': 0.04156668100625649,
    'Southern Africa': 0.09940116692389456,
    'MENA': 0.0661967927282765,
    'Latin America': 0.0861213404432597,
    'Russia & CIS': 0.07417993159300096,
    'Southeast Asia': 0.029292706115026546,
    'Sub-Saharan Africa': 0.09940116692389456,
}
#this was fetched on 09/07/2025

def stooq_ping():
    # Try a very lightweight request to Stooq to check if API is up
    try:
        resp = requests.get('https://stooq.com/q/d/l/?s=spx.us&i=d', timeout=2)
        if resp.status_code == 200:
            return True
    except Exception:
        pass
    return False

def get_avg_annual_return(region, start="2000-01-01", end=None):
    global _stooq_cache, _stooq_cache_date
    today = datetime.date.today()
    if _stooq_cache_date != today:
        _stooq_cache = {}
        _stooq_cache_date = today

    if region in _stooq_cache:
        return _stooq_cache[region]
    ticker = REGION_INDEX_TICKERS.get(region)
    if not ticker:
        return HARDCODED_AVG_RETURNS.get(region, 0.07)  # fallback

    # Ping Stooq once per process per day
    if not hasattr(get_avg_annual_return, '_stooq_available') or get_avg_annual_return._stooq_available_date != today:
        get_avg_annual_return._stooq_available = stooq_ping()
        get_avg_annual_return._stooq_available_date = today
    if not get_avg_annual_return._stooq_available:
        return HARDCODED_AVG_RETURNS.get(region, 0.07)

    stooq_symbol = f"^{ticker}"
    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")
    try:
        # Add timeout to prevent hanging on slow/blocked networks (e.g., AWS Lightsail)
        import socket
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(5)  # 5 second timeout
        try:
            df = web.DataReader(stooq_symbol, "stooq", start, end)
        finally:
            socket.setdefaulttimeout(original_timeout)
        
        if df.empty:
            # Final fallback: hardcoded value
            if region in HARDCODED_AVG_RETURNS:
                return HARDCODED_AVG_RETURNS[region]
            return 0.07
        df = df.sort_index()
        first_price = df["Close"].iloc[0]
        last_price = df["Close"].iloc[-1]
        cumulative_return = (last_price / first_price) - 1
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25
        ann_return = (1 + cumulative_return) ** (1 / years) - 1
        _stooq_cache[region] = ann_return
        return ann_return
    except Exception:
        # Final fallback: hardcoded value
        if region in HARDCODED_AVG_RETURNS:
            return HARDCODED_AVG_RETURNS[region]
        return 0.07


def get_tax_rate(region):
    """Get the corporate tax rate for the region."""
    # Tax rates are stored as percentages, convert to decimal
    return REGIONAL_TAX_RATES.get(region, 25.0) / 100.0


def straight_line_half_year(total_cost, dep_years, plant_lifetime):
    """Straight-Line Depreciation with Half-Year Convention."""
    half_year = 0.5 * (total_cost / dep_years)
    annual_sl = (total_cost - half_year) / (dep_years - 1)
    schedule = [half_year] + [annual_sl] * (dep_years - 2) + [half_year]
    if plant_lifetime > dep_years:
        schedule += [0] * (plant_lifetime - dep_years)
    return schedule


def build_debt_drawdown_and_amortization(
    principal, loan_rate, repayment_term_years, grace, plant_lifetime, years_construction
):
    """
    Debt drawdown during construction (S-curve), then amortization with grace period.
    
    Schedule structure:
    1. Construction years: Interest-only on cumulative S-curve drawdown
    2. Grace period: Interest-only on full principal (no principal payments)
    3. Amortization period: Standard annuity (constant total payment)
    
    Args:
        principal: Total loan amount ($)
        loan_rate: Annual interest rate (decimal)
        repayment_term_years: Loan repayment period (years)
        grace: Grace period duration (years)
        plant_lifetime: Plant operational lifetime (years)
        years_construction: Construction duration (years)
        
    Returns:
        drawdown_schedule: List of annual debt drawdowns ($)
        amort_schedule: List of (principal_payment, interest_payment) tuples ($)
    """
    total_years = years_construction + plant_lifetime
    drawdown_schedule = [0] * total_years
    amort_schedule = [(0, 0)] * total_years
    
    # S-curve drawdown over construction years
    if years_construction > 0:
        x = np.linspace(-6, 6, years_construction)
        s_curve = expit(x)
        s_curve_diff = np.diff(s_curve, prepend=0)
        # Normalize to ensure total drawdown equals principal
        normalized_s_curve_drawdown = (s_curve_diff / s_curve_diff.sum()) * principal
        for y in range(years_construction):
            drawdown_schedule[y] = normalized_s_curve_drawdown[y]
    
    # Interest during construction (based on cumulative S-curve drawdown)
    cumulative_drawdown = np.cumsum(drawdown_schedule)
    for y in range(years_construction):
        interest_payment = cumulative_drawdown[y] * loan_rate
        amort_schedule[y] = (0, interest_payment)
    
    # Grace period: Interest-only on full principal
    remaining_principal = principal
    grace_end_year = years_construction + grace
    
    for y in range(years_construction, min(grace_end_year, total_years)):
        interest_payment = remaining_principal * loan_rate
        amort_schedule[y] = (0, interest_payment)
    
    # Amortization period: Standard annuity formula (constant payment)
    amortization_start_year = grace_end_year
    
    if remaining_principal > 0 and repayment_term_years > 0 and amortization_start_year < total_years:
        # Calculate constant payment using annuity formula
        # PMT = P × [r(1+r)^n] / [(1+r)^n - 1]
        if loan_rate > 0:
            constant_payment = remaining_principal * (
                loan_rate * (1 + loan_rate) ** repayment_term_years
            ) / (
                (1 + loan_rate) ** repayment_term_years - 1
            )
        else:
            # Zero interest rate: divide principal evenly
            constant_payment = remaining_principal / repayment_term_years
        
        # Build amortization schedule with constant payment
        for y in range(amortization_start_year, total_years):
            if remaining_principal <= 0.01:  # Allow small rounding error
                break
            
            # Interest on remaining balance
            interest_payment = remaining_principal * loan_rate
            
            # Principal is constant payment minus interest
            principal_payment = constant_payment - interest_payment
            
            # Handle final payment (remaining principal might be less than calculated)
            if principal_payment > remaining_principal:
                principal_payment = remaining_principal
                # Recalculate interest for final payment
                interest_payment = remaining_principal * loan_rate
            
            amort_schedule[y] = (principal_payment, interest_payment)
            remaining_principal -= principal_payment
            
            # Stop after repayment term
            if y - amortization_start_year + 1 >= repayment_term_years:
                break
    
    return drawdown_schedule, amort_schedule


def lcoe_from_cost_vectors_with_tax(capex_vec, opex_vec, fuel_vec, decom_vec, 
                                   energy_vec, discount_rate, tax_vec):
    """
    Calculate post-tax LCOE including all cash costs to project.
    
    This is an "all-in" LCOE that includes:
    - Capital costs (CAPEX)
    - Operating costs (OPEX)  
    - Fuel costs
    - Decommissioning costs
    - Cash taxes paid to government
    
    Post-tax LCOE enables fair comparison across regions with different
    tax regimes by showing the true all-in cost per MWh including tax burden.
    
    For technology-only comparison (ignoring tax policy differences),
    consider using pre-tax LCOE by excluding tax_vec.
    
    Args:
        capex_vec: Capital expenditure vector ($/year)
        opex_vec: Operating expenditure vector ($/year)
        fuel_vec: Fuel cost vector ($/year)
        decom_vec: Decommissioning cost vector ($/year)
        energy_vec: Energy production vector (MWh/year)
        discount_rate: Discount rate for NPV calculation (decimal)
        tax_vec: Cash taxes paid vector ($/year)
        
    Returns:
        LCOE in $/MWh (post-tax, all-in basis)
    """
    # Calculate total costs including taxes (real cash costs to project)
    total_costs = (np.array(capex_vec) + 
                   np.array(opex_vec) + 
                   np.array(fuel_vec) + 
                   np.array(decom_vec) +
                   np.array(tax_vec))  # Taxes are real cash costs to project
    
    pv_costs = npf.npv(discount_rate, total_costs)
    pv_energy = npf.npv(discount_rate, energy_vec)
    
    return pv_costs / pv_energy if pv_energy > 0 else np.nan


def payback_period(cumulative_cf):
    """Payback period: first year cumulative CF >= 0."""
    for i, cf in enumerate(cumulative_cf):
        if cf >= 0:
            return i
    return None


def dscr(cashflows, debt_service):
    """Debt Service Coverage Ratio: (Net Operating Income) / (Debt Service)."""
    dscrs = []
    for cf, ds in zip(cashflows, debt_service):
        if ds > 0:
            dscrs.append(cf / ds)
        else:
            dscrs.append(np.nan)
    return dscrs


def equity_multiple(cashflows, equity_investment):
    """Equity multiple: total cash returned to equity / equity invested."""
    if equity_investment == 0:
        return np.nan
    return np.sum(cashflows) / abs(equity_investment)


# =============================
# Main Calculation Flow
# =============================
def get_default_config():
    """Return a dict of all model configuration parameters."""
    construction_start_year = 2028
    project_energy_start_year = 2031
    years_construction = project_energy_start_year - construction_start_year  # Default: difference of years
    return {
        "project_name": "NOAK ARC",
        "project_location": "USA",
        "construction_start_year": construction_start_year,
        "years_construction": years_construction,  # Always numeric, so included in sensitivity
        "project_energy_start_year": project_energy_start_year,
        "plant_lifetime": 32,
        
        # Reactor configuration (canonical codes: MFE, IFE, PWR)
        "reactor_type": "MFE",
        "power_method": "MFE",
        "fuel_type": "DT",  # Canonical fuel codes: DT, DD, DHE3, PB11
        
        # Core power parameters
        "net_electric_power_mw": 400,  # Core driver
        "capacity_factor": 0.92,
        
        # PyFECONS material selections (MFE)
        "first_wall_material": "BERYLLIUM",  # Options: BERYLLIUM, TUNGSTEN, LIQUID_LITHIUM
        "blanket_type": "SOLID_BREEDER_LI2TIO3",  # Options: SOLID_BREEDER_LI2TIO3, LIQUID_BREEDER_FLIBE, LIQUID_BREEDER_PBLI
        "structure_material": "FERRITIC_STEEL",  # Options: FERRITIC_STEEL, STAINLESS_STEEL_316, INCOLOY
        
        # PyFECONS magnet configuration (MFE only)
        "magnet_technology": "HTS_REBCO",  # Options: HTS_REBCO, HTS_YBCO, LTS_NB3SN, LTS_NBTI
        "toroidal_field_tesla": 5.0,  # Toroidal field strength (T)
        
        # Q_eng is calculated by the costing power balance module (no manual override in cashflow)
        
        # Expert geometry overrides
        "use_expert_geometry": False,  # If True, use expert_* parameters; if False, scale from template
        
        # Expert MFE radial build parameters (meters) - names match dashboard widgets
        "expert_major_radius_m": 3.0,
        "expert_plasma_t": 1.1,
        "expert_elongation": 3.0,
        "expert_vacuum_t": 0.1,
        "expert_firstwall_t": 0.02,
        "expert_blanket_t": 0.8,
        "expert_reflector_t": 0.2,
        "expert_ht_shield_t": 0.2,
        "expert_structure_t": 0.2,
        "expert_gap_t": 0.5,
        "expert_vessel_t": 0.2,
        "expert_gap2_t": 0.5,
        "expert_lt_shield_t": 0.3,
        "expert_coil_t": 1.0,
        "expert_bio_shield_t": 1.0,
        
        # Financial parameters
        "input_debt_pct": 0.50,
        "loan_rate": 0.05,
        "financing_fee": 0.015,
        "repayment_term_years": 20,
        "grace_period_years": 3,
        "extra_capex_pct": 0.05,
        # Contingency handled by CAS 29 in costing module (no double-counting)
        "project_contingency_pct": 0.0,
        "process_contingency_pct": 0.0,
        
        # O&M parameters
        "fixed_om_per_mw": 60000,
        "variable_om": 2.7,
        "electricity_price": 81,  # Core driver
        
        # Depreciation & end-of-life
        "dep_years": 20,
        "salvage_value": 10000000,
        "decommissioning_cost": 843000000,
        
        # Economic parameters
        "use_real_dollars": False,
        "price_escalation_active": True,
        "escalation_rate": 0.02,
        "include_fuel_cost": True,
        "apply_tax_model": True,
        
        # Ramp-up parameters
        "ramp_up": True,
        "ramp_up_years": 3,
        "ramp_up_rate_per_year": 0.33,
        
        # Industrial heat sales
        "enable_heat_sales": False,
        "heat_sales_fraction": 0.10,
        "heat_price_per_mwh_th": 30,
        
        # EPC override
        "override_epc": False,
        "override_epc_value": 5000000000,
    }


def get_mfe_config():
    """Return default configuration for MFE (Magnetic Fusion Energy) - NOAK ARC-based."""
    return get_default_config()  # Uses NOAK ARC as the MFE baseline


def get_pwr_config():
    """Return default configuration for PWR (Pressurized Water Reactor) - Vogtle-based."""
    return {
        "project_name": "Plant Vogtle Units 3 & 4",
        "project_location": "Waynesboro, Georgia, USA",
        "construction_start_year": 2013,
        "years_construction": 11,
        "project_energy_start_year": 2024,
        "plant_lifetime": 60,
        "power_method": "PWR",
        "net_electric_power_mw": 2231,
        "capacity_factor": 0.90,
        "fuel_type": "Fission Benchmark Enriched Uranium",
        "input_debt_pct": 0.70,
        "loan_rate": 0.05,
        "financing_fee": 0.01,
        "repayment_term_years": 30,
        "grace_period_years": 3,
        "extra_capex_pct": 0.0,
        "project_contingency_pct": 0.0,
        "process_contingency_pct": 0.0,
        "fixed_om_per_mw": 158610,
        "variable_om": 2.54,
        "electricity_price": 70,
        "dep_years": 20,
        "salvage_value": 0,
        "decommissioning_cost": 1000000000,
        "use_real_dollars": False,
        "price_escalation_active": True,
        "escalation_rate": 0.02,
        "include_fuel_cost": True,
        "apply_tax_model": True,
        "ramp_up": True,
        "ramp_up_years": 3,
        "ramp_up_rate_per_year": 0.33,
        
        # Industrial heat sales
        "enable_heat_sales": False,
        "heat_sales_fraction": 0.10,
        "heat_price_per_mwh_th": 30,
        
        # EPC override
        "override_epc": False,
        "override_epc_value": 35000000000,
    }


def get_ife_config():
    """Return default configuration for IFE (Inertial Fusion Energy) - NIF-inspired baseline."""
    construction_start_year = 2025
    project_energy_start_year = 2038
    years_construction = project_energy_start_year - construction_start_year  
    return {
        "project_name": "IFE Commercial Plant",
        "project_location": "United States",
        "construction_start_year": construction_start_year,
        "years_construction": years_construction,  # Always numeric, so included in sensitivity
        "project_energy_start_year": project_energy_start_year,
        "plant_lifetime": 30,
        "power_method": "IFE",
        "net_electric_power_mw": 1000,
        "capacity_factor": 0.85,  # Slightly lower than MFE due to laser maintenance
        "fuel_type": "Tritium",
        "input_debt_pct": 0.70,
        "loan_rate": 0.06,
        "financing_fee": 0.02,
        "repayment_term_years": 20,
        "grace_period_years": 3,
        # No total_epc_cost or override_epc - always use embedded costing system
        # Q_eng is calculated by costing power balance module
        "extra_capex_pct": 0.08,  # Higher contingency for laser systems
        # Contingency handled by CAS 29 in costing module (no double-counting)
        "project_contingency_pct": 0.0,
        "process_contingency_pct": 0.0,
        "fixed_om_per_mw": 75000,  # Higher O&M due to laser maintenance
        "variable_om": 3.2,
        "electricity_price": 100,
        "dep_years": 20,
        "salvage_value": 8000000,
        "decommissioning_cost": 950000000,
        "use_real_dollars": False,
        "price_escalation_active": True,
        "escalation_rate": 0.02,
        "include_fuel_cost": True,
        "apply_tax_model": True,
        "ramp_up": True,
        "ramp_up_years": 2,
        "ramp_up_rate_per_year": 0.5,
        
        # Industrial heat sales
        "enable_heat_sales": False,
        "heat_sales_fraction": 0.10,
        "heat_price_per_mwh_th": 30,
        
        # EPC override
        "override_epc": False,
        "override_epc_value": 5000000000,
        
        # IFE-specific parameters
        "impfreq": 1.0,  # Implosion frequency in Hz
    }


def get_default_config_by_power_method(power_method):
    """Return appropriate default configuration based on power method."""
    if power_method == "MFE":
        return get_mfe_config()
    elif power_method == "IFE":
        return get_ife_config()
    elif power_method == "PWR":
        return get_pwr_config()
    else:
        return get_default_config()  # Fallback to generic default


def run_cashflow_scenario(config):
    t0 = time.time()
    # --- Input/config setup ---
    construction_start_year = config["construction_start_year"]
    years_construction = config.get("years_construction")
    if years_construction is not None:
        years_construction = int(round(years_construction))
        project_energy_start_year = construction_start_year + years_construction
    else:
        project_energy_start_year = config["project_energy_start_year"]
        years_construction = int(round(project_energy_start_year - construction_start_year))
    plant_lifetime = config["plant_lifetime"]
    plant_lifetime = int(round(plant_lifetime))
    power_method = config["power_method"]
    
    # --- Fuel Type Resolution ---
    # Use canonical fuel_type_code (DT, DD, DHE3, PB11) from dashboard mapping
    # Fall back to fuel_type for backward compatibility with PWR configs
    fuel_code = config.get("fuel_type_code", "")
    raw_fuel = config.get("fuel_type", "")
    
    if power_method == "PWR":
        fuel_type = "Fission Benchmark Enriched Uranium"
    elif fuel_code in ("DT", "DD"):
        fuel_type = "Lithium-Solid"  # DT/DD fusion uses lithium breeding
    elif fuel_code == "DHE3":
        fuel_type = "Tritium"  # DHe3 still needs some tritium
    elif fuel_code == "PB11":
        fuel_type = "Tritium"  # pB11 aneutronic, minimal fuel cost
    elif raw_fuel in ("Lithium-Solid", "Lithium-Liquid", "Tritium", "Fission Benchmark Enriched Uranium"):
        fuel_type = raw_fuel  # Legacy format, pass through
    else:
        fuel_type = "Lithium-Solid"  # Default fallback
    
    # Apply power method adjustments to key variables
    net_electric_power_mw = config.get("net_electric_power_mw", 400)
    capacity_factor = config["capacity_factor"]  # Use config value directly
    input_debt_pct = config["input_debt_pct"]
    input_equity_pct = 1.0 - input_debt_pct
    loan_rate = config["loan_rate"]
    financing_fee = config["financing_fee"]
    repayment_term_years = config["repayment_term_years"]
    repayment_term_years = int(round(repayment_term_years))
    grace_period_years = config["grace_period_years"]
    grace_period_years = int(round(grace_period_years))
    
    # --- Power-to-EPC Integration (cached when only financial params change) ---
    p_thermal_mw = 0.0  # Will be set from costing if available
    
    if config.get("override_epc", False):
        # Manual EPC override — skip costing entirely, use slider values for P_net/O&M
        total_epc_cost = config.get("override_epc_value", 5_000_000_000)
        config["_epc_breakdown"] = {}
        config["_q_eng"] = config.get("manual_q_eng", 4.0)
    else:
        try:
            epc_result = _compute_epc_cached(config)
            total_epc_cost = epc_result["total_epc"]
            
            config["_epc_breakdown"] = epc_result
            config["_q_eng"] = epc_result.get("power_balance", {}).get("q_eng", 0)
            
            # Use physics-derived P_net for revenue/energy/O&M consistency
            p_net_from_costing = epc_result.get("power_balance", {}).get("p_net", None)
            if p_net_from_costing is not None and p_net_from_costing > 0:
                net_electric_power_mw = p_net_from_costing
                config["net_electric_power_mw"] = p_net_from_costing
            
            # Extract p_thermal for industrial heat sales
            p_thermal_from_costing = epc_result.get("power_balance", {}).get("p_thermal", 0)
            if p_thermal_from_costing and p_thermal_from_costing > 0:
                p_thermal_mw = p_thermal_from_costing
            
            # Use costing-derived O&M if available (physics-based, CAS 70)
            costing_fixed_om = epc_result.get("costing_fixed_om_per_mw", None)
            if costing_fixed_om is not None and costing_fixed_om > 0:
                config["fixed_om_per_mw"] = costing_fixed_om
            
            # Use costing-derived annual fuel cost if available (physics-based, CAS 80)
            costing_fuel = epc_result.get("costing_annual_fuel_cost", None)
            if costing_fuel is not None:
                config["_costing_annual_fuel_cost"] = costing_fuel
            
        except Exception as e:
            warnings.warn(f"Embedded costing system failed: {e}. Using default $5B EPC cost.")
            total_epc_cost = 5_000_000_000
            config["_epc_breakdown"] = {}
            config["_q_eng"] = 1.0
    
    extra_capex = total_epc_cost * config["extra_capex_pct"]
    # NOTE: Contingency is handled by CAS 29 in the costing module.
    # project_contingency_pct and process_contingency_pct removed to avoid double-counting.
    project_contingency_cost = 0
    process_contingency_cost = 0
    fixed_om = config["fixed_om_per_mw"] * net_electric_power_mw  # Use config values directly
    variable_om = config["variable_om"]  # Use config value directly
    electricity_price = config["electricity_price"]
    dep_years = config["dep_years"]
    dep_years = int(round(dep_years))
    salvage_value = config["salvage_value"]
    decommissioning_cost = config["decommissioning_cost"]
    use_real_dollars = config["use_real_dollars"]
    price_escalation_active = config["price_escalation_active"]
    escalation_rate = config["escalation_rate"]
    include_fuel_cost = config["include_fuel_cost"]
    apply_tax_model = config["apply_tax_model"]
    ramp_up = config["ramp_up"]
    ramp_up_years = config["ramp_up_years"]
    ramp_up_years = int(round(ramp_up_years))
    ramp_up_rate_per_year = config["ramp_up_rate_per_year"]
    # t1 = time.time(); print(f'[PROFILE] after input/config setup: {t1-t0:.2f}s')
    # --- Region/risk-free/tax calculations ---
    annual_energy_output_mwh = (net_electric_power_mw * 8760) * capacity_factor
    
    # Fuel cost: prefer costing-derived CAS 80 (physics-based) over hardcoded models
    costing_annual_fuel = config.get("_costing_annual_fuel_cost", None)
    if costing_annual_fuel is not None and costing_annual_fuel > 0 and power_method != "PWR":
        # Use costing module's annual fuel cost (CAS 80) as base
        total_fuel_cost = costing_annual_fuel
        # Derive per-MWh rate for operation loop (escalation applied there)
        fuel_cost_per_mwh_base = total_fuel_cost / annual_energy_output_mwh if annual_energy_output_mwh > 0 else 0
        use_costing_fuel = True
    else:
        # Fallback to legacy fuel cost model
        use_costing_fuel = False
        if fuel_type == "Lithium-Solid":
            fuel_price_per_g = 152.928
            burn_kg_per_year_per_gw = 100
            burn_g_per_year = burn_kg_per_year_per_gw * 1000 * (net_electric_power_mw / 1000)
            fuel_grams_per_mwh = burn_g_per_year / annual_energy_output_mwh
        elif fuel_type == "Tritium":
            fuel_price_per_g = 300
            fuel_grams_per_mwh = 0.00947
        elif fuel_type == "Lithium-Liquid":
            fuel_price_per_g = 152.928
            burn_kg_per_year_per_gw = 100
            burn_g_per_year = burn_kg_per_year_per_gw * 1000 * (net_electric_power_mw / 1000)
            fuel_grams_per_mwh = burn_g_per_year / annual_energy_output_mwh
        elif fuel_type == "Fission Benchmark Enriched Uranium":
            fuel_price_per_g = 1.663
            fuel_grams_per_mwh = 2.78  # https://world-nuclear.org/information-library/economic-aspects/economics-of-nuclear-power
        else:
            raise ValueError("Invalid fuel type. Choose 'Lithium' or 'Tritium'.")
        total_fuel_cost = annual_energy_output_mwh * fuel_grams_per_mwh * fuel_price_per_g
    region = map_location_to_region(config["project_location"])
    risk_free_rate = get_risk_free_rate(region)
    scenario = "base"
    unlevered_beta = get_unlevered_beta(scenario)
    tax_rate = get_tax_rate(region)
    levered_beta = get_levered_beta(unlevered_beta, input_debt_pct, tax_rate)
    avg_annual_return = get_avg_annual_return(region, start="2000-01-01")
    if avg_annual_return is None:
        avg_annual_return = 0.07
    market_risk_premium = avg_annual_return - risk_free_rate
    cost_of_equity = risk_free_rate + levered_beta * market_risk_premium
    cost_of_debt = loan_rate  # Pre-tax cost of debt = nominal loan rate
    cost_of_debt_posttax = loan_rate * (1 - tax_rate)  # After-tax cost of debt
    wacc = input_equity_pct * cost_of_equity + input_debt_pct * cost_of_debt_posttax
    discount_rate = wacc
    financing_charges = total_epc_cost * financing_fee
    toc = (
        total_epc_cost
        + extra_capex
        + project_contingency_cost
        + process_contingency_cost
        + financing_charges
    )
    depreciable_base = toc
    decommissioning_year = (
        construction_start_year + years_construction + plant_lifetime - 1
    )
    total_years = years_construction + plant_lifetime
    years = list(range(total_years))
    year_labels = [construction_start_year + y for y in years]
    # t2 = time.time(); print(f'[PROFILE] after region/risk-free/tax: {t2-t0:.2f}s')
    # --- Debt/amortization/depreciation setup ---
    cashflow_type = []
    revenue_vec = []
    heat_revenue_vec = []
    fuel_vec = []
    om_vec = []
    depreciation_vec = []
    tax_vec = []
    debt_service_vec = []
    principal_paid_vec = []
    interest_paid_vec = []
    energy_vec = []
    noi_vec = []
    unlevered_cf_vec = []
    levered_cf_vec = []
    equity_cf_vec = []
    cumulative_unlevered_cf_vec = []
    cumulative_levered_cf_vec = []
    dscr_vec = []
    # --- Cost vectors for LCOE calculation ---
    capex_vec = []
    opex_vec = []
    fuel_cost_vec = []
    decom_vec = []
    escalation_factors = [1.0]
    for y in range(1, total_years):
        if price_escalation_active:
            escalation_factors.append(escalation_factors[-1] * (1 + escalation_rate))
        else:
            escalation_factors.append(1.0)
    debt_principal = toc * input_debt_pct
    drawdown_schedule, amort_schedule = build_debt_drawdown_and_amortization(
        debt_principal,
        loan_rate,
        repayment_term_years,
        grace_period_years,
        plant_lifetime,
        years_construction,
    )
    depreciation_schedule = straight_line_half_year(
        depreciable_base, dep_years, plant_lifetime
    )
    full_depreciation_schedule = [0] * years_construction + depreciation_schedule
    # t3 = time.time(); print(f'[PROFILE] after debt/amortization/depreciation: {t3-t0:.2f}s')
    # --- Construction loop ---
    for y in range(years_construction):
        esc = escalation_factors[y]
        capex_outflow = drawdown_schedule[y] * esc
        financing_outflow = financing_charges / years_construction * esc
        
        # Use pre-calculated interest from amortization schedule (prevents double-counting)
        # amort_schedule[y] = (principal_payment, interest_payment)
        # During construction: principal=0, interest based on cumulative drawdown
        interest_during_construction = amort_schedule[y][1] * esc
        
        net_cf = -(
            capex_outflow + financing_outflow + interest_during_construction
        )
        cashflow_type.append("Construction")
        revenue_vec.append(0)
        heat_revenue_vec.append(0)
        fuel_vec.append(0)
        om_vec.append(0)
        depreciation_vec.append(0)
        tax_vec.append(0)
        debt_service_vec.append(0)
        principal_paid_vec.append(0)
        interest_paid_vec.append(interest_during_construction)
        energy_vec.append(0)
        noi_vec.append(0)
        unlevered_cf_vec.append(net_cf)
        levered_cf_vec.append(net_cf)
        dscr_vec.append(np.nan)
        if y == 0:
            equity_cf_vec.append(-toc * input_equity_pct)
        else:
            equity_cf_vec.append(0)
        # --- Cost vectors for LCOE calculation ---
        capex_vec.append(capex_outflow + financing_outflow + interest_during_construction)
        opex_vec.append(0)
        fuel_cost_vec.append(0)
        decom_vec.append(0)
    # t4 = time.time(); print(f'[PROFILE] after construction loop: {t4-t0:.2f}s')
    # --- Operation loop ---
    for y in range(plant_lifetime):
        op_year = y + years_construction
        esc = escalation_factors[op_year]
        if ramp_up and y < ramp_up_years:
            ramp_mult = (y + 1) * ramp_up_rate_per_year
            ramp_mult = min(ramp_mult, 1.0)
        else:
            ramp_mult = 1.0
        price = electricity_price * esc
        annual_energy = annual_energy_output_mwh * ramp_mult
        
        # --- Industrial heat sales ---
        heat_rev = 0.0
        enable_heat_sales = config.get("enable_heat_sales", False)
        if enable_heat_sales and p_thermal_mw > 0:
            heat_frac = config.get("heat_sales_fraction", 0.10)
            heat_price = config.get("heat_price_per_mwh_th", 30) * esc
            # Thermal energy sold as heat (MWh_th)
            heat_energy_mwh_th = p_thermal_mw * 8760 * capacity_factor * heat_frac * ramp_mult
            heat_rev = heat_energy_mwh_th * heat_price
            # Reduce electricity output — diverted thermal energy doesn't reach turbine
            annual_energy *= (1.0 - heat_frac)
        
        energy_vec.append(annual_energy)
        revenue = annual_energy * price + heat_rev
        heat_revenue_vec.append(heat_rev)
        revenue_vec.append(revenue)
        if use_costing_fuel:
            # Costing-derived fuel: scale by ramp and escalation
            fuel = (
                fuel_cost_per_mwh_base * annual_energy * esc
                if include_fuel_cost
                else 0
            )
        else:
            # Legacy fuel model
            fuel_price = fuel_price_per_g * esc
            fuel = (
                (fuel_grams_per_mwh * annual_energy) * fuel_price
                if include_fuel_cost
                else 0
            )
        fuel_vec.append(fuel)
        variable_om_cost = variable_om * annual_energy * esc
        fixed_om_cost = fixed_om * esc
        om = variable_om_cost + fixed_om_cost
        om_vec.append(om)
        noi = revenue - fuel - om
        noi_vec.append(noi)
        depreciation = full_depreciation_schedule[op_year]
        depreciation_vec.append(depreciation)
        op_profit = revenue - fuel - om
        cash_tax = max(0, op_profit - depreciation) * tax_rate
        tax_vec.append(cash_tax)
        # Debt service from pre-calculated amortization schedule
        # Schedule already accounts for:
        # - Construction years: Interest on cumulative drawdown
        # - Grace period: Interest-only on full principal  
        # - Amortization period: Principal + interest (constant payment annuity)
        if op_year < len(amort_schedule):
            principal_payment, interest_payment = amort_schedule[op_year]
            # Apply escalation to debt service
            principal_payment *= esc
            interest_payment *= esc
        else:
            # Beyond schedule (loan fully repaid or past plant life)
            principal_payment, interest_payment = 0, 0
        
        principal_paid_vec.append(principal_payment)
        interest_paid_vec.append(interest_payment)
        debt_service = principal_payment + interest_payment
        debt_service_vec.append(debt_service)
        unlevered_cf = revenue - fuel - om - cash_tax + depreciation
        levered_cf = unlevered_cf - debt_service
        if (construction_start_year + op_year) == decommissioning_year:
            unlevered_cf -= decommissioning_cost
            unlevered_cf += salvage_value
            levered_cf -= decommissioning_cost
            levered_cf += salvage_value
        unlevered_cf_vec.append(unlevered_cf)
        levered_cf_vec.append(levered_cf)
        equity_cf_vec.append(levered_cf)
        # --- Cost vectors for LCOE calculation ---
        capex_vec.append(0)  # No capex during operation
        opex_vec.append(om)  # O&M costs
        fuel_cost_vec.append(fuel)  # Fuel costs
        # Decommissioning costs in the final year
        if (construction_start_year + op_year) == decommissioning_year:
            decom_vec.append(decommissioning_cost)
        else:
            decom_vec.append(0)
    # t5 = time.time(); print(f'[PROFILE] after operation loop: {t5-t0:.2f}s')
    if use_real_dollars:
        for y in range(len(unlevered_cf_vec)):
            deflator = (1 + escalation_rate) ** y
            unlevered_cf_vec[y] /= deflator
            levered_cf_vec[y] /= deflator
            equity_cf_vec[y] /= deflator
            revenue_vec[y] /= deflator
            fuel_vec[y] /= deflator
            om_vec[y] /= deflator
            depreciation_vec[y] /= deflator
            tax_vec[y] /= deflator
            debt_service_vec[y] /= deflator
            principal_paid_vec[y] /= deflator
            interest_paid_vec[y] /= deflator
            energy_vec[y] /= deflator
            noi_vec[y] /= deflator
            # Also deflate cost vectors for LCOE calculation
            capex_vec[y] /= deflator
            opex_vec[y] /= deflator
            fuel_cost_vec[y] /= deflator
            decom_vec[y] /= deflator
        cumulative_unlevered_cf_vec = np.cumsum(unlevered_cf_vec).tolist()
        cumulative_levered_cf_vec = np.cumsum(levered_cf_vec).tolist()
        cumulative_equity_cf_vec = np.cumsum(equity_cf_vec).tolist()
    else:
        cumulative_unlevered_cf_vec = np.cumsum(unlevered_cf_vec).tolist()
        cumulative_levered_cf_vec = np.cumsum(levered_cf_vec).tolist()
        cumulative_equity_cf_vec = np.cumsum(equity_cf_vec).tolist()
    # treat years with zero scheduled debt service as "not applicable"
    # Suppress divide by zero warnings for DSCR calculation
    with np.errstate(divide='ignore', invalid='ignore'):
        dscr_vec = np.where(
            np.array(debt_service_vec) > 0,
            np.array(noi_vec) / np.array(debt_service_vec),
            np.nan,  # NaN suppresses plotting in Bokeh
        ).tolist()
    debt_drawdown_vec = drawdown_schedule
    all_vectors = [
        year_labels,
        cashflow_type,
        revenue_vec,
        fuel_vec,
        om_vec,
        depreciation_vec,
        interest_paid_vec,
        principal_paid_vec,
        tax_vec,
        unlevered_cf_vec,
        cumulative_unlevered_cf_vec,
        noi_vec,
        dscr_vec,
        levered_cf_vec,
        cumulative_levered_cf_vec,
        equity_cf_vec,
        cumulative_equity_cf_vec,
        debt_drawdown_vec,
    ]
    max_len = max(len(v) for v in all_vectors)

    def pad_or_truncate(vec, fill):
        if len(vec) < max_len:
            return vec + [fill] * (max_len - len(vec))
        else:
            return vec[:max_len]

    year_labels = pad_or_truncate(year_labels, "")
    cashflow_type = pad_or_truncate(cashflow_type, "")
    revenue_vec = pad_or_truncate(revenue_vec, 0)
    fuel_vec = pad_or_truncate(fuel_vec, 0)
    om_vec = pad_or_truncate(om_vec, 0)
    depreciation_vec = pad_or_truncate(depreciation_vec, 0)
    interest_paid_vec = pad_or_truncate(interest_paid_vec, 0)
    principal_paid_vec = pad_or_truncate(principal_paid_vec, 0)
    tax_vec = pad_or_truncate(tax_vec, 0)
    unlevered_cf_vec = pad_or_truncate(unlevered_cf_vec, 0)
    cumulative_unlevered_cf_vec = pad_or_truncate(cumulative_unlevered_cf_vec, 0)
    noi_vec = pad_or_truncate(noi_vec, 0)
    dscr_vec = pad_or_truncate(dscr_vec, np.nan)
    levered_cf_vec = pad_or_truncate(levered_cf_vec, 0)
    cumulative_levered_cf_vec = pad_or_truncate(cumulative_levered_cf_vec, 0)
    equity_cf_vec = pad_or_truncate(equity_cf_vec, 0)
    cumulative_equity_cf_vec = pad_or_truncate(cumulative_equity_cf_vec, 0)
    debt_drawdown_vec = pad_or_truncate(debt_drawdown_vec, 0)
    df = pd.DataFrame(
        {
            "Year": year_labels,
            "Phase": cashflow_type,
            "Revenue": revenue_vec,
            "FuelCost": fuel_vec,
            "O&M": om_vec,
            "Depreciation": depreciation_vec,
            "Interest": interest_paid_vec,
            "Principal": principal_paid_vec,
            "Tax": tax_vec,
            "UnleveredCF": unlevered_cf_vec,
            "CumUnleveredCF": cumulative_unlevered_cf_vec,
            "NOI": noi_vec,
            "DSCR": dscr_vec,
            "LeveredCF": levered_cf_vec,
            "CumLeveredCF": cumulative_levered_cf_vec,
            "EquityCF": equity_cf_vec,
            "CumEquityCF": cumulative_equity_cf_vec,
            "DebtDrawdown": debt_drawdown_vec,
        }
    )
    equity_df = df[["Year", "Phase", "EquityCF", "CumEquityCF"]].copy()
    npv = npf.npv(discount_rate, unlevered_cf_vec)
    irr = npf.irr(unlevered_cf_vec)
    payback = payback_period(cumulative_unlevered_cf_vec)
    # Use tax-adjusted LCOE for more accurate calculation
    lcoe_val = lcoe_from_cost_vectors_with_tax(capex_vec, opex_vec, fuel_cost_vec, decom_vec, energy_vec, discount_rate, tax_vec)
    equity_npv = npf.npv(discount_rate, equity_cf_vec)
    equity_irr = npf.irr(equity_cf_vec)
    equity_payback = payback_period(cumulative_equity_cf_vec)
    
    # Calculate equity multiple using the proper function
    equity_mult = equity_multiple(equity_cf_vec, toc * input_equity_pct)
    
    # Calculate DSCR statistics for operational years
    operational_dscr = [d for d in dscr_vec if not np.isnan(d)]
    min_dscr = min(operational_dscr) if operational_dscr else np.nan
    avg_dscr = np.mean(operational_dscr) if operational_dscr else np.nan
    
    # tN = time.time(); print(f'[PROFILE] before return: {tN-t0:.2f}s')
    # print('[PROFILE] run_cashflow_scenario: end, total time:', time.time() - t0)
    return {
        "df": df,
        "equity_df": equity_df,
        "npv": npv,
        "irr": irr,
        "equity_npv": equity_npv,
        "equity_irr": equity_irr,
        "payback": payback,
        "equity_payback": equity_payback,
        "lcoe_val": lcoe_val,
        "equity_mult": equity_mult,
        "min_dscr": min_dscr,
        "avg_dscr": avg_dscr,
        "dscr_vec": dscr_vec,
        "year_labels": year_labels,
        "cashflow_type": cashflow_type,
        "revenue_vec": revenue_vec,
        "fuel_vec": fuel_vec,
        "om_vec": om_vec,
        "depreciation_vec": depreciation_vec,
        "interest_paid_vec": interest_paid_vec,
        "principal_paid_vec": principal_paid_vec,
        "tax_vec": tax_vec,
        "unlevered_cf_vec": unlevered_cf_vec,
        "cumulative_unlevered_cf_vec": cumulative_unlevered_cf_vec,
        "noi_vec": noi_vec,
        "levered_cf_vec": levered_cf_vec,
        "cumulative_levered_cf_vec": cumulative_levered_cf_vec,
        "equity_cf_vec": equity_cf_vec,
        "cumulative_equity_cf_vec": cumulative_equity_cf_vec,
        "energy_vec": energy_vec,
        "heat_revenue_vec": heat_revenue_vec,
        "toc": toc,
        "total_epc_cost": total_epc_cost,
        "input_equity_pct": input_equity_pct,
        "discount_rate": discount_rate,
        "wacc": wacc,
        "cost_of_equity": cost_of_equity,
        "cost_of_debt": cost_of_debt,
        "region": region,
        "tax_rate": tax_rate,
        "decommissioning_year": decommissioning_year,
        "years_construction": years_construction,
        "plant_lifetime": plant_lifetime,
        "construction_start_year": construction_start_year,
        "project_energy_start_year": project_energy_start_year,
        "year_labels_int": [int(y) if str(y).isdigit() else y for y in year_labels],
        "debt_drawdown_vec": debt_drawdown_vec,
        "epc_breakdown": config.get("_epc_breakdown", {}),
    }


def run_sensitivity_analysis(base_config):
    """Run a dense sensitivity analysis on key variables and return a DataFrame of results."""
    import copy

    bands = [
        -0.14,
        -0.12,
        -0.10,
        -0.08,
        -0.06,
        -0.04,
        -0.02,
        0.0,
        0.02,
        0.04,
        0.06,
        0.08,
        0.10,
        0.12,
        0.14,
    ]
    drivers = [
        ("Construction Years", ["years_construction"]),
        ("Electricity Price", ["electricity_price"]),
        ("Plasma Q", ["q_plasma"]),
        ("Capacity Factor", ["capacity_factor"]),
        ("Debt Percentage", ["input_debt_pct"]),
    ]
    metrics = []
    # For each driver and band
    for driver, keys in drivers:
        # Note: EPC Cost sensitivity now uses embedded costing system
        # The costing will be recalculated for each scenario automatically
        if driver == "EPC Cost":
            base_config_for_driver = copy.deepcopy(base_config)
            base_outputs = run_cashflow_scenario(base_config_for_driver)
        else:
            base_outputs = run_cashflow_scenario(base_config)
        
        base_metrics = {
            "Scenario": f"{driver} 0%",
            "Driver": driver,
            "Band": "0%",
            "NPV": base_outputs["npv"],
            "IRR": base_outputs["irr"],
            "LCOE": base_outputs["lcoe_val"],
            "Payback Period": base_outputs.get("payback_period", 0),
        }
        metrics.append(base_metrics)
        for band in bands:
            if band == 0.0:
                continue  # Already did base
            config_mod = copy.deepcopy(base_config)
            for key in keys:
                if key not in config_mod:
                    # Try to compute years_construction if possible
                    if key == "years_construction":
                        if "project_energy_start_year" in config_mod and "construction_start_year" in config_mod:
                            config_mod[key] = int(round(config_mod["project_energy_start_year"] - config_mod["construction_start_year"]))
                        else:
                            continue  # Cannot compute, skip this band
                    else:
                        continue  # Key missing, skip this band
                config_mod[key] *= 1 + band
                
                # Note: When modifying parameters, embedded costing will recalculate automatically
                # No need to override - the new system handles parameter changes dynamically
                
                # Apply constraints to keep parameters within reasonable bounds
                if key == "capacity_factor":
                    config_mod[key] = max(0.1, min(1.0, config_mod[key]))  # Keep between 10% and 100%
                elif key == "input_debt_pct":
                    config_mod[key] = max(0.0, min(0.95, config_mod[key]))  # Keep between 0% and 95%
                
                # If the key is one of the integer parameters, cast it back to int
                if key in ["years_construction", "plant_lifetime", "dep_years", "repayment_term_years", "grace_period_years", "ramp_up_years"]:
                    config_mod[key] = int(round(config_mod[key]))
            outputs = run_cashflow_scenario(config_mod)
            percent = f"{int(band*100):+d}%"
            metrics.append(
                {
                    "Scenario": f"{driver} {percent}",
                    "Driver": driver,
                    "Band": percent,
                    "NPV": outputs["npv"],
                    "IRR": outputs["irr"],
                    "LCOE": outputs["lcoe_val"],
                    "Payback Period": outputs.get("payback_period", 0),
                }
            )
    df = pd.DataFrame(metrics)
    return df
