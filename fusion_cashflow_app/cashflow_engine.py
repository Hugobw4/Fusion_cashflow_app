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

import pandas as pd
import numpy as np
from scipy.special import expit
import numpy_financial as npf
import pandas_datareader.data as web
import datetime
import requests

# Try to import power_to_epc module, fall back to manual EPC if not available
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from power_to_epc import arpa_epc, get_regional_factor
    POWER_TO_EPC_AVAILABLE = True
except ImportError:
    POWER_TO_EPC_AVAILABLE = False

# Try to import Q model for dynamic engineering Q estimation
try:
    from q_model import estimate_q_eng
    Q_MODEL_AVAILABLE = True
except ImportError:
    Q_MODEL_AVAILABLE = False

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
    "Southen Africa": 27.00, # https://taxsummaries.pwc.com/south-africa/corporate/taxes-on-corporate-income#:~:text=For%20tax%20years%20ending%20before,or%20after%2031%20March%202023
    "Oceania": 24.38, #https://taxfoundation.org/data/all/global/corporate-tax-rates-by-country-2024/
    "MENA": 55.00, #https://taxsummaries.pwc.com/oman/corporate/taxes-on-corporate-income#:~:text=Petroleum%20income%20tax NO SPECIFIC ENERGY GENERATION TAX BUT PETROLEUM COMPANYS PAY 55% OMAN AND UAE
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
        df = web.DataReader(stooq_symbol, "stooq", start, end)
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
    """Debt drawdown during construction (S-curve), then amortization (interest only, then principal)."""
    total_years = years_construction + plant_lifetime
    drawdown_schedule = [0] * total_years
    amort_schedule = [(0,0)] * total_years
    
    # S-curve drawdown over construction years
    if years_construction > 0:
        x = np.linspace(-6, 6, years_construction)  # Adjust range for desired S-curve shape
        s_curve = expit(x)
        s_curve_diff = np.diff(s_curve, prepend=0)
        # Normalize to ensure total drawdown equals principal
        normalized_s_curve_drawdown = (s_curve_diff / s_curve_diff.sum()) * principal
        for y in range(years_construction):
            drawdown_schedule[y] = normalized_s_curve_drawdown[y]
    # Amortization schedule (interest-only during construction, then principal + interest)
    # Interest during construction is based on the cumulative S-curve drawdown
    cumulative_drawdown = np.cumsum(drawdown_schedule)
    for y in range(years_construction):
        # Interest-only during construction
        interest_payment = cumulative_drawdown[y] * loan_rate
        amort_schedule[y] = (0, interest_payment)  # No principal payment during construction

    # Principal + interest after construction
    remaining_principal = principal
    for y in range(years_construction, total_years):
        if remaining_principal <= 0:
            break
         # Simple amortization for now, can be improved with more complex methods
        interest_payment = remaining_principal * loan_rate
        principal_payment = min(remaining_principal, principal / repayment_term_years)  # Even principal repayment over repayment term
        amort_schedule[y] = (principal_payment, interest_payment)
        remaining_principal -= principal_payment
        
    return drawdown_schedule, amort_schedule


def lcoe_from_cost_vectors(capex_vec, opex_vec, fuel_vec, decom_vec, energy_vec, discount_rate):
    """
    Lazard LCOE:
    PV(all discounted cost streams) ÷ PV(discounted energy),
    both discounted at the project WACC.
    """
    cost_vec = (np.array(capex_vec) +
                np.array(opex_vec) +
                np.array(fuel_vec) +
                np.array(decom_vec))

    pv_costs  = npf.npv(discount_rate, cost_vec)
    pv_energy = npf.npv(discount_rate, energy_vec)

    return pv_costs / pv_energy if pv_energy > 0 else np.nan


def lcoe_from_cost_vectors_with_tax(capex_vec, opex_vec, fuel_vec, decom_vec, 
                                   energy_vec, discount_rate, tax_vec):
    """
    Enhanced LCOE with tax effects:
    PV(all costs + taxes paid) ÷ PV(discounted energy)
    
    Note: tax_vec contains actual cash taxes paid to government,
    which are additional costs, not savings.
    """
    # Calculate total costs including taxes
    total_costs = (np.array(capex_vec) + 
                   np.array(opex_vec) + 
                   np.array(fuel_vec) + 
                   np.array(decom_vec) +
                   np.array(tax_vec))  # Add taxes as costs, not subtract!
    
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
    return np.sum(cashflows) / equity_investment


# =============================
# Main Calculation Flow
# =============================
def get_default_config():
    """Return a dict of all model configuration parameters."""
    construction_start_year = 2007
    project_energy_start_year = 2034
    years_construction = project_energy_start_year - construction_start_year  # Default: difference of years
    return {
        "project_name": "ITER",
        "project_location": "South of France",
        "construction_start_year": construction_start_year,
        "years_construction": years_construction,  # Always numeric, so included in sensitivity
        "project_energy_start_year": project_energy_start_year,
        "plant_lifetime": 30,
        "power_method": "MFE",
        "net_electric_power_mw": 500,  # Core driver
        "capacity_factor": 0.9,
        "fuel_type": "Lithium-Solid",
        "input_debt_pct": 0.70,
        "cost_of_debt": 0.055,
        "loan_rate": 0.055,
        "financing_fee": 0.015,
        "repayment_term_years": 20,
        "grace_period_years": 3,
        "total_epc_cost": 13000000000,  # Core driver - used only if override_epc=True
        "override_epc": False,  # NEW: If True, use manual total_epc_cost; if False, auto-generate from power
        "override_q_eng": False,  # NEW: If True, use manual Q_eng; if False, auto-generate from Q model
        "manual_q_eng": 4.0,  # Manual Q engineering value (used only if override_q_eng=True)
        "extra_capex_pct": 0.05,
        "project_contingency_pct": 0.15,
        "process_contingency_pct": 0.20,
        "fixed_om_per_mw": 60000,
        "variable_om": 2.7,
        "electricity_price": 100,  # Core driver
        "dep_years": 20,
        "salvage_value": 10000000,
        "decommissioning_cost": 843000000,
        "use_real_dollars": False,
        "price_escalation_active": True,
        "escalation_rate": 0.02,
        "include_fuel_cost": True,
        "apply_tax_model": True,
        "ramp_up": True,
        "ramp_up_years": 3,
        "ramp_up_rate_per_year": 0.33,
    }


def get_mfe_config():
    """Return default configuration for MFE (Magnetic Fusion Energy) - ITER-based."""
    return get_default_config()  # Uses ITER as the MFE baseline


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
        "cost_of_debt": 0.05,
        "loan_rate": 0.05,
        "financing_fee": 0.01,
        "repayment_term_years": 30,
        "grace_period_years": 3,
        "total_epc_cost": 35000000000,
        "override_epc": True,  # PWR uses historical actual cost
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
    }


def get_default_config_by_power_method(power_method):
    """Return appropriate default configuration based on power method."""
    if power_method == "MFE" or power_method == "IFE":
        return get_mfe_config()
    elif power_method == "PWR":
        return get_pwr_config()
    else:
        return get_default_config()  # Fallback to generic default


def run_cashflow_scenario(config):
    import time
    # print('[PROFILE] run_cashflow_scenario: start')
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
    
    # --- Power Method Specific Adjustments ---
    # Only apply fuel type logic based on power method
    if power_method == "MFE":  # Magnetic Fusion Energy (Tokamak)
        # MFE should use fusion-compatible fuels
        if config["fuel_type"] not in ["Lithium-Solid", "Lithium-Liquid", "Tritium"]:
            fuel_type = "Lithium-Solid"  # Default for MFE
        else:
            fuel_type = config["fuel_type"]
        
    elif power_method == "IFE":  # Inertial Fusion Energy (Laser-driven)
        # IFE should use fusion-compatible fuels
        if config["fuel_type"] not in ["Lithium-Solid", "Lithium-Liquid", "Tritium"]:
            fuel_type = "Tritium"  # Default for IFE
        else:
            fuel_type = config["fuel_type"]
        
    elif power_method == "PWR":  # Pressurized Water Reactor (Fission)
        # PWR must use enriched uranium fuel
        fuel_type = "Fission Benchmark Enriched Uranium"
            
    else:
        # Default case - use config fuel type
        fuel_type = config["fuel_type"]
        if fuel_type not in ["Lithium-Solid", "Lithium-Liquid", "Tritium", "Fission Benchmark Enriched Uranium"]:
            fuel_type = "Lithium-Solid"
    
    # Apply power method adjustments to key variables
    net_electric_power_mw = config["net_electric_power_mw"]
    capacity_factor = config["capacity_factor"]  # Use config value directly
    input_debt_pct = config["input_debt_pct"]
    input_equity_pct = 1.0 - input_debt_pct
    cost_of_debt = config["cost_of_debt"]
    loan_rate = config["loan_rate"]
    financing_fee = config["financing_fee"]
    repayment_term_years = config["repayment_term_years"]
    repayment_term_years = int(round(repayment_term_years))
    grace_period_years = config["grace_period_years"]
    grace_period_years = int(round(grace_period_years))
    
    # --- Power-to-EPC Integration ---
    override_epc = config.get("override_epc", False)
    if override_epc or not POWER_TO_EPC_AVAILABLE:
        # Use manual EPC cost from config
        total_epc_cost = config["total_epc_cost"]
    else:
        # Auto-generate EPC cost from power using ARPA-E scaling
        try:
            region_factor = get_regional_factor(config["project_location"])
            epc_result = arpa_epc(
                net_mw=net_electric_power_mw,
                years=years_construction,
                tech=power_method,
                region_factor=region_factor,
                noak=True  # Assume NOAK for cost optimization
            )
            total_epc_cost = epc_result["total_epc_cost"]
            
            # Store EPC breakdown for analysis
            config["_epc_breakdown"] = epc_result
            
        except Exception as e:
            # Fallback to manual EPC if auto-generation fails
            total_epc_cost = config["total_epc_cost"]
            import warnings
            warnings.warn(f"Power-to-EPC auto-generation failed: {e}. Using manual EPC cost.")
    
    extra_capex = total_epc_cost * config["extra_capex_pct"]
    project_contingency_cost = total_epc_cost * config["project_contingency_pct"]
    process_contingency_cost = total_epc_cost * config["process_contingency_pct"]
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
        fuel_grams_per_mwh = 2.78 #https://world-nuclear.org/information-library/economic-aspects/economics-of-nuclear-power
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
    cost_of_debt_posttax = cost_of_debt * (1 - tax_rate)
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
        interest_during_construction = (
            sum(drawdown_schedule[:y]) * loan_rate * esc if y > 0 else 0
        )
        net_cf = -(
            capex_outflow + financing_outflow + interest_during_construction
        )
        cashflow_type.append("Construction")
        revenue_vec.append(0)
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
        energy_vec.append(annual_energy)
        revenue = annual_energy * price
        revenue_vec.append(revenue)
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
        if op_year < (
            project_energy_start_year + grace_period_years - construction_start_year
        ):
            principal_payment, interest_payment = 0, 0
        else:
            idx = op_year - (
                project_energy_start_year + grace_period_years - construction_start_year
            )
            if 0 <= idx < grace_period_years:
                principal_payment, interest_payment = 0, amort_schedule[idx][1]
            elif (
                grace_period_years <= idx < (grace_period_years + repayment_term_years)
            ):
                principal_payment, interest_payment = amort_schedule[idx]
            else:
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
    equity_mult = sum(equity_cf_vec) / abs(toc * input_equity_pct)
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
    }


def run_sensitivity_analysis(base_config):
    """Run a dense sensitivity analysis on key variables and return a DataFrame of results."""
    import copy
    import pandas as pd

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
        ("WACC", ["cost_of_debt"]),
        ("Electricity Price", ["electricity_price"]),
        ("EPC Cost", ["total_epc_cost"]),
        ("Net Electric Power (MW)", ["net_electric_power_mw"]),
    ]
    metrics = []
    # For each driver and band
    for driver, keys in drivers:
        base_outputs = run_cashflow_scenario(base_config)
        base_metrics = {
            "Scenario": f"{driver} 0%",
            "Driver": driver,
            "Band": "0%",
            "NPV": base_outputs["npv"],
            "IRR": base_outputs["irr"],
            "Equity NPV": base_outputs["equity_npv"],
            "Equity IRR": base_outputs["equity_irr"],
            "LCOE": base_outputs["lcoe_val"],
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
                    "Equity NPV": outputs["equity_npv"],
                    "Equity IRR": outputs["equity_irr"],
                    "LCOE": outputs["lcoe_val"],
                }
            )
    df = pd.DataFrame(metrics)
    return df

def get_estimated_q_eng(config):
    """
    Get estimated engineering Q for the given configuration.
    
    Args:
        config: Configuration dictionary with power and technology parameters
        
    Returns:
        Float: Engineering Q estimate, either from Q model or manual override
    """
    override_q_eng = config.get("override_q_eng", False)
    
    if override_q_eng:
        # Use manual Q_eng value
        return config.get("manual_q_eng", 4.0)
    elif Q_MODEL_AVAILABLE:
        # Use dynamic Q model
        try:
            net_mw = config["net_electric_power_mw"]
            power_method = config.get("power_method", "MFE")
            return estimate_q_eng(net_mw, power_method)
        except Exception as e:
            import warnings
            warnings.warn(f"Q model estimation failed: {e}. Using default Q=4.0")
            return 4.0
    else:
        # Fallback to default Q value
        return 4.0
