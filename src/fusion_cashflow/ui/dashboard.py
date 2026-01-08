import sys
import os
import threading

# Add the src directory to Python path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "..", "..")
sys.path.insert(0, os.path.abspath(src_path))

print(f"Added to sys.path: {os.path.abspath(src_path)}")  # Debug print

import holoviews as hv
import nevergrad as ng

hv.extension("bokeh")
from bokeh.io import curdoc
from bokeh.layouts import row, column, Spacer
from bokeh.models import (
    TextInput,
    Select,
    Slider,
    Checkbox,
    Button,
    Div,
    NumberFormatter,
    DataTable,
    TableColumn,
    ColumnDataSource,
    Tabs,
    TabPanel,
)

# Import costing panel module
from fusion_cashflow.ui.costing_panel import create_costing_panel

# --- Highlight Facts & Figures ---
# This Div will be updated with key metrics (LCOE, IRR, NPV, Payback, etc.)
highlight_div = Div(
    text="",
    width=900,
    styles={
        "background": "#00375b",
        "border-radius": "16px",
        "padding": "18px 24px 12px 24px",
        "margin-bottom": "18px",
        "font-size": "18px",
        "font-weight": "800",
        "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
        "border": "1px solid #e0e0e0",
        "color": "#ffffff",
        "font-family": "Inter, Helvetica, Arial, sans-serif",
    },
)

# --- Financial Metrics Section ---
# This Div will show DSCR and Equity Multiple metrics
financial_metrics_div = Div(
    text="",
    width=900,
    styles={
        "background": "#2c5282",
        "border-radius": "16px",
        "padding": "18px 24px 12px 24px",
        "margin-bottom": "18px",
        "font-size": "18px",
        "font-weight": "800",
        "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
        "border": "1px solid #e0e0e0",
        "color": "#ffffff",
        "font-family": "Inter, Helvetica, Arial, sans-serif",
    },
)

# --- DSCR Metrics (for DSCR chart) ---
dscr_metrics_div = Div(
    text="",
    width=600,
    styles={
        "background": "#00375b",
        "border-radius": "12px",
        "padding": "12px 16px 8px 16px",
        "margin-bottom": "12px",
        "font-size": "16px",
        "font-weight": "800",
        "box-shadow": "0 1px 4px rgba(0,0,0,0.04)",
        "border": "1px solid #e0e0e0",
        "color": "#ffffff",
        "font-family": "Inter, Helvetica, Arial, sans-serif",
    },
)

# --- Equity Metrics (for cumulative cashflow chart) ---
equity_metrics_div = Div(
    text="",
    width=600,
    styles={
        "background": "#00375b",
        "border-radius": "12px",
        "padding": "12px 16px 8px 16px",
        "margin-bottom": "12px",
        "font-size": "16px",
        "font-weight": "800",
        "box-shadow": "0 1px 4px rgba(0,0,0,0.04)",
        "border": "1px solid #e0e0e0",
        "color": "#ffffff",
        "font-family": "Inter, Helvetica, Arial, sans-serif",
    },
)

# --- Funding/Sankey Chart Container ---
funding_div = Div(
    text="",
    width=800,
    height=500,
    styles={
        "background": "#ffffff",
        "border-radius": "12px",
        "padding": "12px",
        "margin-bottom": "12px",
        "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
        "border": "1px solid #e0e0e0",
    },
)


def render_highlight_facts(outputs):
    # Extract key metrics from outputs, fallback to 'N/A' if not present
    lcoe_val = outputs.get("lcoe_val", "N/A")
    irr = outputs.get("irr", "N/A") 
    npv = outputs.get("npv", "N/A")
    payback = outputs.get("payback", "N/A")  # Fixed: use "payback" not "payback_years"
    
    # Format values if numeric
    def fmt(val, style):
        if val == "N/A" or val is None:
            return "N/A"
        try:
            if style == "currency":
                return f"${val:,.0f}"
            elif style == "currency_detailed":
                return f"${val:,.2f}"
            elif style == "percent":
                return f"{val*100:.2f}%"
            elif style == "years":
                return f"{val:.1f} years"
            else:
                return f"{val:,.2f}"
        except (TypeError, ValueError):
            return "N/A"

    html = f"""
    <div style='display: flex; justify-content: space-between; align-items: center; font-size: 18px; font-weight: 800; white-space: nowrap; padding: 0 20px;'>
        <div style='margin-right: 30px;'>
            <span title='Levelized Cost of Energy - The cost per MWh to build and operate the power plant over its lifetime' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>LCOE<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> {fmt(lcoe_val, 'currency_detailed')} / MWh</span>
        </div>
        <div style='margin-right: 30px;'>
            <span title='Internal Rate of Return - The discount rate that makes the NPV of all cash flows equal to zero' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>IRR<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> {fmt(irr, 'percent')}</span>
        </div>
        <div style='margin-right: 30px;'>
            <span title='Net Present Value - The present value of all future cash flows minus the initial investment' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>NPV<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> {fmt(npv, 'currency')}</span>
        </div>
        <div>
            <span title='Total Project Payback Period - The time it takes for the cumulative unlevered cash flows to equal the total project investment (includes all costs, debt and equity)' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>Payback<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> {fmt(payback, 'years')}</span>
        </div>
    </div>
    """
    return html


def render_dscr_metrics(outputs):
    # Extract DSCR metrics from outputs, fallback to 'N/A' if not present
    min_dscr = outputs.get("min_dscr", "N/A")
    avg_dscr = outputs.get("avg_dscr", "N/A")

    # Format values if numeric
    def fmt(val, style):
        if isinstance(val, (int, float)):
            if style == "ratio":
                return f"{val:.2f}x"
            else:
                return str(val)
        return val

    html = f"""
    <div style='font-size: 14px; margin-bottom: 8px; color: #ffffff; font-weight: 600;'>DEBT SERVICE COVERAGE RATIO PROFILE</div>
    <div style='display: flex; gap: 24px;'>
        <div>
            <span title='Minimum Debt Service Coverage Ratio - The lowest ratio of Net Operating Income to debt service payments. Higher is better (>1.25 typically required)' 
                  style='cursor: help; background: rgba(0, 55, 91, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(0, 55, 91, 0.2)'" 
                  onmouseout="this.style.background='rgba(0, 55, 91, 0.1)'">
                <b>Min DSCR<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'>{fmt(min_dscr, 'ratio')}</span>
        </div>
        <div>
            <span title='Average Debt Service Coverage Ratio - The average ratio of Net Operating Income to debt service payments over the loan term' 
                  style='cursor: help; background: rgba(0, 55, 91, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(0, 55, 91, 0.2)'" 
                  onmouseout="this.style.background='rgba(0, 55, 91, 0.1)'">
                <b>Avg DSCR<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'>{fmt(avg_dscr, 'ratio')}</span>
        </div>
    </div>
    """
    return html


def render_equity_metrics(outputs):
    # Extract equity metrics from outputs, fallback to 'N/A' if not present
    equity_mult = outputs.get("equity_mult", "N/A")

    # Format values if numeric
    def fmt(val, style):
        if isinstance(val, (int, float)):
            if style == "mult":
                return f"{val:.2f}x"
            else:
                return str(val)
        return val

    html = f"""
    <div style='font-size: 14px; margin-bottom: 8px; color: #ffffff; font-weight: 600;'>CUMULATIVE CASHFLOW PERFORMANCE</div>
    <span title='Equity Multiple - The ratio of cumulative distributions to initial equity investment. Shows total return on equity over project life' 
          style='cursor: help; background: rgba(0, 55, 91, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
          onmouseover="this.style.background='rgba(0, 55, 91, 0.2)'" 
          onmouseout="this.style.background='rgba(0, 55, 91, 0.1)'">
        <b>Equity Multiple<sup>?</sup>:</b>
    </span> 
    <span style='color:#ffffff;font-weight:800'>{fmt(equity_mult, 'mult')}</span>
    """
    return html


import holoviews as hv

hv.extension("bokeh")
from bokeh.models import (
    Div,
)
from fusion_cashflow.core.cashflow_engine import (
    get_default_config,
    get_default_config_by_power_method,
    run_cashflow_scenario,
    run_sensitivity_analysis,
    get_avg_annual_return,
)
from fusion_cashflow.visualization.bokeh_plots import (
    plot_annual_cashflow_bokeh,
    plot_cumulative_cashflow_bokeh,
    plot_dscr_profile_bokeh,
    plot_cashflow_waterfall_bokeh,
    plot_sensitivity_heatmap,
)

# Import optimisation tools
try:
    scripts_path = os.path.join(current_dir, "..", "..", "..", "scripts")
    sys.path.insert(0, os.path.abspath(scripts_path))
    from optimization_tools import single_objective_fitness
    OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import optimisation_tools: {e}")
    OPTIMIZATION_AVAILABLE = False

import pandas as pd
from bokeh.events import ButtonClick

# --- Styling ---
APPLE_CSS = """
<link rel="icon" type="image/x-icon" href="assets/favicon.ico?v=20250807_2">
<style>
/* Hide Bokeh application header/toolbar and top-level elements */
.bk-root .bk-toolbar, .bk-toolbar-above, .bk-toolbar-below, .bk-toolbar-left, .bk-toolbar-right {
    display: none !important;
}
.bk-root .bk-toolbar-box {
    display: none !important;
}
/* Hide any top-level headers, nav elements, or application bars */
.bk-root .bk-header, .bk-root .bk-nav, .bk-root .bk-menu {
    display: none !important;
}
/* Target Bokeh's application-level elements */
.bk-root > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
/* Hide any blue bars or headers at document level */
body > div:first-child {
    display: none !important;
}
/* Remove any top margin/padding that might create blue space */
.bk-root {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
body {
    margin-top: 0 !important;
    padding-top: 0 !important;
    background: white !important;
}
/* Hide any potential Bokeh server elements */
.bk-logo, .bk-logo-small, .bk-logo-notebook {
    display: none !important;
}
/* Target potential application wrapper elements */
div[data-root-id] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.bk-root .bk-btn, .bk-root .bk-input, .bk-root .bk-slider, .bk-root .bk-select {
    border-radius: 16px !important;
    font-family: "Inter, Helvetica, Arial, sans-serif" !important;
    font-size: 18px !important;
    font-weight: 800 !important;
    background: #00375b !important;
    color: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}
.bk-root .bk-btn-primary {
    background: #00375b !important;
    color: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 16px !important;
    font-family: "Inter, Helvetica, Arial, sans-serif" !important;
    font-weight: 800 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
}
.bk-root .bk-panel {
    border-radius: 16px;
    background: #00375b;
    color: #ffffff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e0e0e0;
    font-family: "Inter, Helvetica, Arial, sans-serif";
}
.bk-root .bk-data-table {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #e0e0e0;
    background: #00375b;
    color: #ffffff;
    font-family: "Inter, Helvetica, Arial, sans-serif";
    font-weight: 800;
}
</style>
"""


# --- Widgets for all key inputs ---
def make_widgets(config):
    widgets = {}
    widgets["project_name"] = TextInput(
        title="Project Name", value=config["project_name"]
    )
    widgets["project_location"] = TextInput(
        title="Project Location", value=config["project_location"]
    )
    widgets["construction_start_year"] = Slider(
        title="Construction Start Year",
        start=1980,
        end=2150,
        value=config["construction_start_year"],
        step=1,
    )
    widgets["project_energy_start_year"] = Slider(
        title="Energy Start Year",
        start=1985,
        end=2200,
        value=config["project_energy_start_year"],
        step=1,
    )
    # Add a read-only Div to show years_construction
    years_construction_val = config["project_energy_start_year"] - config["construction_start_year"]
    widgets["years_construction_display"] = Div(
        text=f"<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Construction Duration (years):</b> {years_construction_val}</div>",
        width=300,
    )
    widgets["plant_lifetime"] = Slider(
        title="Plant Lifetime (years)",
        start=20,
        end=80,
        value=config["plant_lifetime"],
        step=1,
    )
    widgets["power_method"] = Select(
        title="Power Method", value=config["power_method"], options=["MFE", "IFE", "PWR"]
    )
    widgets["net_electric_power_mw"] = Slider(
        title="Net Electric Power (MW)",
        start=10,
        end=4000,
        value=config["net_electric_power_mw"],
        step=10,
    )
    widgets["capacity_factor"] = Slider(
        title="Capacity Factor",
        start=0.1,
        end=1.0,
        value=config["capacity_factor"],
        step=0.01,
        format="0%",
    )
    widgets["fuel_type"] = Select(
        title="Fuel Type", value=config["fuel_type"], options=[
            "Lithium-Solid", 
            "Lithium-Liquid", 
            "Tritium",
            "Fission Benchmark Enriched Uranium"
        ]
    )
    widgets["input_debt_pct"] = Slider(
        title="Debt %", start=0.0, end=1.0, value=config["input_debt_pct"], step=0.01, format="0%"
    )
    widgets["cost_of_debt"] = Slider(
        title="Cost of Debt",
        start=0.0,
        end=0.2,
        value=config["cost_of_debt"],
        step=0.001,
        format="0.0%",
    )
    widgets["loan_rate"] = Slider(
        title="Loan Rate", start=0.0, end=0.2, value=config["loan_rate"], step=0.001, format="0.0%"
    )
    widgets["financing_fee"] = Slider(
        title="Financing Fee",
        start=0.0,
        end=0.1,
        value=config["financing_fee"],
        step=0.001,
        format="0.0%",
    )
    widgets["repayment_term_years"] = Slider(
        title="Repayment Term (years)",
        start=1,
        end=40,
        value=config["repayment_term_years"],
        step=1,
    )
    widgets["grace_period_years"] = Slider(
        title="Grace Period (years)",
        start=0,
        end=10,
        value=config["grace_period_years"],
        step=1,
    )
    # EPC Cost Control Toggle
    widgets["override_epc"] = Checkbox(
        label="Manual EPC Cost Override", active=config.get("override_epc", False)
    )
    widgets["total_epc_cost"] = Slider(
        title="Total EPC Cost ($)",
        start=1e9,
        end=5e10,
        value=config["total_epc_cost"],
        step=1e8,
        format="0,0",
        visible=config.get("override_epc", False),  # Initially hidden unless override is active
    )
    # Q Engineering Control Toggle
    widgets["override_q_eng"] = Checkbox(
        label="Manual Q Engineering Override", active=config.get("override_q_eng", False)
    )
    widgets["manual_q_eng"] = Slider(
        title="Q Engineering Value",
        start=1.0,
        end=15.0,
        value=config.get("manual_q_eng", 4.0),
        step=0.1,
        visible=config.get("override_q_eng", False),  # Initially hidden unless override is active
    )
    
    # Display widgets for auto-calculated values (read-only)
    widgets["auto_epc_display"] = Div(
        text="<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Auto EPC Cost:</b> Calculating...</div>",
        width=400,
    )
    widgets["auto_q_eng_display"] = Div(
        text="<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Auto Q Engineering:</b> Calculating...</div>",
        width=400,
    )
    widgets["extra_capex_pct"] = Slider(
        title="Extra CapEx %",
        start=0.0,
        end=0.5,
        value=config["extra_capex_pct"],
        step=0.01,
        format="0%",
    )
    widgets["project_contingency_pct"] = Slider(
        title="Project Contingency %",
        start=0.0,
        end=0.5,
        value=config["project_contingency_pct"],
        step=0.01,
        format="0%",
    )
    widgets["process_contingency_pct"] = Slider(
        title="Process Contingency %",
        start=0.0,
        end=0.5,
        value=config["process_contingency_pct"],
        step=0.01,
        format="0%",
    )
    widgets["fixed_om_per_mw"] = Slider(
        title="Fixed O&M per MW ($)",
        start=10000,
        end=200000,
        value=config["fixed_om_per_mw"],
        step=1000,
    )
    widgets["variable_om"] = Slider(
        title="Variable O&M ($/MWh)",
        start=0.0,
        end=20.0,
        value=config["variable_om"],
        step=0.1,
    )
    widgets["electricity_price"] = Slider(
        title="Electricity Price ($/MWh)",
        start=10,
        end=500,
        value=config["electricity_price"],
        step=1,
    )
    widgets["dep_years"] = Slider(
        title="Depreciation Years", start=5, end=40, value=config["dep_years"], step=1
    )
    widgets["salvage_value"] = Slider(
        title="Salvage Value ($)",
        start=0,
        end=1e8,
        value=config["salvage_value"],
        step=1e6,
    )
    widgets["decommissioning_cost"] = Slider(
        title="Decommissioning Cost ($)",
        start=0,
        end=2e9,
        value=config["decommissioning_cost"],
        step=1e7,
    )
    widgets["use_real_dollars"] = Checkbox(
        label="Use Real Dollars", active=config["use_real_dollars"]
    )
    widgets["price_escalation_active"] = Checkbox(
        label="Price Escalation Active", active=config["price_escalation_active"]
    )
    widgets["escalation_rate"] = Slider(
        title="Escalation Rate",
        start=0.0,
        end=0.1,
        value=config["escalation_rate"],
        step=0.001,
    )
    widgets["include_fuel_cost"] = Checkbox(
        label="Include Fuel Cost", active=config["include_fuel_cost"]
    )
    widgets["apply_tax_model"] = Checkbox(
        label="Apply Tax Model", active=config["apply_tax_model"]
    )
    widgets["ramp_up"] = Checkbox(label="Ramp Up", active=config["ramp_up"])
    widgets["ramp_up_years"] = Slider(
        title="Ramp Up Years", start=0, end=10, value=config["ramp_up_years"], step=1
    )
    widgets["ramp_up_rate_per_year"] = Slider(
        title="Ramp Up Rate/Year",
        start=0.0,
        end=1.0,
        value=config["ramp_up_rate_per_year"],
        step=0.01,
    )
    
    # Optimization widgets
    widgets["optimise_target"] = Select(
        title="Target metric",
        value="Max IRR",
        options=["Max IRR", "Max NPV", "Min LCOE"]
    )
    widgets["optimise_button"] = Button(
        label="Optimise", 
        button_type="success",
        width=120,
        disabled=not OPTIMIZATION_AVAILABLE
    )
    widgets["optimise_status"] = Div(
        text="Ready to optimise" if OPTIMIZATION_AVAILABLE else "Optimisation not available",
        styles={"color": "#ffffff" if OPTIMIZATION_AVAILABLE else "#ff6b6b", "font-size": "18px", "font-weight": "800", "font-family": "Inter, Helvetica, Arial, sans-serif"}
    )
    
    return widgets


# --- Update logic ---
def get_config_from_widgets(widgets):
    config = {}
    for k, w in widgets.items():
        if isinstance(w, (Slider, TextInput, Select)):
            config[k] = w.value
        elif isinstance(w, Checkbox):
            config[k] = w.active
    # Force manual EPC when benchmarking PWR, but allow user to adjust the amount
    if config.get("power_method") == "PWR":
        config["override_epc"] = True
        # Use the widget value for total_epc_cost (don't hardcode it)
        # This allows users to adjust PWR EPC cost via the slider
    return config


# --- Throttling/debouncing for widget updates ---

debounce_timer = None
DEBOUNCE_DELAY = 0.8  # seconds


def update_dashboard():
    config = get_config_from_widgets(widgets)
    
    # Skip fusion auto-calcs when benchmarking a fixed PWR plant
    tech = config["power_method"]
    if tech == "PWR":
        widgets["auto_q_eng_display"].text = (
            "<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
            "<b>Auto Q Engineering:</b> N/A (fixed benchmark)</div>")
        # Show the actual EPC cost from the slider for PWR
        actual_epc_cost = config["total_epc_cost"]
        widgets["auto_epc_display"].text = (
            "<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
            f"<b>Auto EPC Cost:</b> ${actual_epc_cost/1e9:.1f} B (manual override)</div>")
    else:
        # Calculate auto-generated values for display
        try:
            from fusion_cashflow.core.power_to_epc import arpa_epc, get_regional_factor
            from fusion_cashflow.core.q_model import estimate_q_eng
            
            net_mw = config["net_electric_power_mw"]
            location = config["project_location"]
            years_construction = (
                config["project_energy_start_year"] - config["construction_start_year"]
            )
            
            # Auto Q (fusion only)
            auto_q_eng = estimate_q_eng(net_mw, tech)
            widgets["auto_q_eng_display"].text = (
                f"<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>Auto Q Engineering:</b> {auto_q_eng:.2f}</div>")
            
            # Auto EPC (fusion only)
            region_factor = get_regional_factor(location)
            epc_result = arpa_epc(
                net_mw=net_mw,
                years=years_construction,
                tech=tech,
                region_factor=region_factor,
                noak=True,
            )
            auto_epc_cost   = epc_result["total_epc_cost"]
            auto_epc_per_kw = epc_result["cost_per_kw"]
            widgets["auto_epc_display"].text = (
                f"<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>Auto EPC Cost:</b> ${auto_epc_cost/1e9:.2f} B "
                f"(${auto_epc_per_kw:,} / kW)</div>")
                
        except Exception as e:
            widgets["auto_q_eng_display"].text = f"<div style='margin-bottom:10px; color:#ff6b6b; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Auto Q Engineering:</b> Error: {str(e)[:50]}...</div>"
            widgets["auto_epc_display"].text = f"<div style='margin-bottom:10px; color:#ff6b6b; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Auto EPC Cost:</b> Error: {str(e)[:50]}...</div>"
    
    outputs = run_cashflow_scenario(config)
    highlight_div.text = render_highlight_facts(outputs)
    dscr_metrics_div.text = render_dscr_metrics(outputs)
    equity_metrics_div.text = render_equity_metrics(outputs)
    annual_fig = plot_annual_cashflow_bokeh(outputs, config)
    cum_fig = plot_cumulative_cashflow_bokeh(outputs, config)
    dscr_fig = plot_dscr_profile_bokeh(outputs, config)
    annual_df = pd.DataFrame({
        "Year": outputs["year_labels_int"],
        "Unlevered CF": outputs["unlevered_cf_vec"],
        "Levered CF": outputs["levered_cf_vec"],
        "Revenue": outputs["revenue_vec"],
        "O&M": outputs["om_vec"],
        "Fuel": outputs["fuel_vec"],
        "Tax": outputs["tax_vec"],
        "NOI": outputs["noi_vec"],
    })
    annual_source.data = dict(ColumnDataSource(annual_df).data)
    cum_df = pd.DataFrame({
        "Year": outputs["year_labels_int"],
        "Cumulative Unlevered CF": outputs["cumulative_unlevered_cf_vec"],
        "Cumulative Levered CF": outputs["cumulative_levered_cf_vec"],
    })
    cum_source.data = dict(ColumnDataSource(cum_df).data)
    dscr_df = pd.DataFrame({
        "Year": outputs["year_labels_int"],
        "DSCR": outputs["dscr_vec"],
        "NOI": outputs["noi_vec"],
        "Debt Service": [a + b for a, b in zip(outputs["principal_paid_vec"], outputs["interest_paid_vec"])]
    })
    dscr_source.data = dict(ColumnDataSource(dscr_df).data)
    
    # Update costing panel if EPC breakdown is available
    epc_breakdown = outputs.get("epc_breakdown", {})
    if epc_breakdown:
        updated_costing_panel = create_costing_panel(epc_breakdown)
        costing_col.children = [updated_costing_panel]
    
    # Replace plots in layout (main tab only)
    main_col.children = [
        highlight_div,
        annual_cf_explanation,
        annual_fig,
        annual_toggle_button,
        annual_table_explanation,
        annual_table,
        equity_metrics_div,
        cumulative_cf_explanation,
        cum_fig,
        cum_toggle_button,
        cum_table_explanation,
        cum_table,
        dscr_metrics_div,
        dscr_fig,
        dscr_toggle_button,
        dscr_table_explanation,
        dscr_table,
    ]


debounce_callback_id = None


def debounced_update():
    global debounce_callback_id
    doc = curdoc()
    if debounce_callback_id is not None:
        doc.remove_timeout_callback(debounce_callback_id)
        debounce_callback_id = None

    def run_update():
        global debounce_callback_id
        debounce_callback_id = None
        update_dashboard()

    # Schedule update_dashboard to run after DEBOUNCE_DELAY seconds
    debounce_callback_id = doc.add_timeout_callback(
        run_update, int(DEBOUNCE_DELAY * 1000)
    )


def download_csv_callback(source, filename):
    """Generate CSV data from ColumnDataSource."""
    df = pd.DataFrame(source.data)
    csv = df.to_csv(index=False)
    return csv


# --- Initial setup ---
config = get_default_config()
widgets = make_widgets(config)

# --- Make years_construction_display reactive ---
def update_years_construction_display(attr, old, new):
    years = widgets["project_energy_start_year"].value - widgets["construction_start_year"].value
    widgets["years_construction_display"].text = (
        f"<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Construction Duration (years):</b> {years}</div>"
    )
widgets["construction_start_year"].on_change("value", update_years_construction_display)
widgets["project_energy_start_year"].on_change("value", update_years_construction_display)

# --- Make power method and fuel type reactive ---
def update_fuel_type_based_on_power_method(attr, old, new):
    power_method = widgets["power_method"].value
    if power_method == "PWR":
        # For PWR, force fission fuel
        widgets["fuel_type"].value = "Fission Benchmark Enriched Uranium"
        widgets["fuel_type"].options = ["Fission Benchmark Enriched Uranium"]
    elif power_method in ["MFE", "IFE"]:
        # For fusion methods, provide fusion fuel options
        widgets["fuel_type"].options = ["Lithium-Solid", "Lithium-Liquid", "Tritium"]
        if widgets["fuel_type"].value == "Fission Benchmark Enriched Uranium":
            widgets["fuel_type"].value = "Lithium-Solid"
    else:
        # Default case - all options available
        widgets["fuel_type"].options = [
            "Lithium-Solid", 
            "Lithium-Liquid", 
            "Tritium", 
            "Fission Benchmark Enriched Uranium"
        ]

def update_config_based_on_power_method(attr, old, new):
    """Update all configuration parameters when power method changes."""
    from fusion_cashflow.core.cashflow_engine import get_default_config_by_power_method
    
    power_method = widgets["power_method"].value
    new_config = get_default_config_by_power_method(power_method)
    
    # Update all widgets with new configuration values
    # Skip power_method itself to avoid recursion
    for key, value in new_config.items():
        if key in widgets and key != "power_method":
            widget = widgets[key]
            if isinstance(widget, (Slider, TextInput, Select)):
                # For sliders, make sure the value is within range
                if isinstance(widget, Slider):
                    if value < widget.start:
                        widget.start = value
                    if value > widget.end:
                        widget.end = value
                widget.value = value
            elif isinstance(widget, Checkbox):
                widget.active = value
    
    # Special handling for PWR: force manual EPC override and make slider visible
    if power_method == "PWR":
        widgets["override_epc"].active = True
        widgets["total_epc_cost"].visible = True
    else:
        # For fusion methods, respect the config's override_epc setting
        widgets["total_epc_cost"].visible = widgets["override_epc"].active
    
    # Update years construction display
    years = widgets["project_energy_start_year"].value - widgets["construction_start_year"].value
    widgets["years_construction_display"].text = (
        f"<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Construction Duration (years):</b> {years}</div>"
    )
    
    # Update fuel type options based on new power method
    update_fuel_type_based_on_power_method(attr, old, new)

widgets["power_method"].on_change("value", update_fuel_type_based_on_power_method)
widgets["power_method"].on_change("value", update_config_based_on_power_method)

# --- EPC and Q Engineering Visibility Toggle Functions ---
def toggle_epc_slider_visibility(attr, old, new):
    """Show/hide the manual EPC cost slider based on override checkbox."""
    widgets["total_epc_cost"].visible = new

def toggle_q_eng_slider_visibility(attr, old, new):
    """Show/hide the manual Q Engineering slider based on override checkbox."""
    widgets["manual_q_eng"].visible = new

# Set up visibility toggle callbacks
widgets["override_epc"].on_change("active", toggle_epc_slider_visibility)
widgets["override_q_eng"].on_change("active", toggle_q_eng_slider_visibility)

outputs = run_cashflow_scenario(config)

# Do NOT run sensitivity analysis at startup
# print('[DEBUG] Calling run_sensitivity_analysis(config)')
# sensitivity_df = run_sensitivity_analysis(config)
# print('[DEBUG] Finished run_sensitivity_analysis(config)')

# Placeholder for sensitivity tab at startup
from bokeh.plotting import figure
placeholder_fig = figure(height=400, width=700, title="Click 'Run Sensitivity Analysis' to compute results.")
placeholder_fig.text(x=[0.5], y=[0.5], text=["No sensitivity data yet."], text_align="center", text_baseline="middle", text_font_size="16pt")


annual_df = pd.DataFrame(
    {
        "Year": outputs["year_labels_int"],
        "Unlevered CF": outputs["unlevered_cf_vec"],
        "Levered CF": outputs["levered_cf_vec"],
        "Revenue": outputs["revenue_vec"],
        "O&M": outputs["om_vec"],
        "Fuel": outputs["fuel_vec"],
        "Tax": outputs["tax_vec"],
        "NOI": outputs["noi_vec"],
    }
)
annual_source = ColumnDataSource(annual_df)

cum_df = pd.DataFrame(
    {
        "Year": outputs["year_labels_int"],
        "Cumulative Unlevered CF": outputs["cumulative_unlevered_cf_vec"],
        "Cumulative Levered CF": outputs["cumulative_levered_cf_vec"],
    }
)
cum_source = ColumnDataSource(cum_df)

dscr_df = pd.DataFrame(
    {
        "Year": outputs["year_labels_int"],
        "DSCR": outputs["dscr_vec"],
        "NOI": outputs["noi_vec"],
        "Debt Service": [
            a + b
            for a, b in zip(outputs["principal_paid_vec"], outputs["interest_paid_vec"])
        ],
    }
)
dscr_source = ColumnDataSource(dscr_df)

funding_df = pd.DataFrame(
    {
        "Label": [
            "Debt",
            "Equity",
            "EPC",
            "Extra CapEx",
            "Project Contingency",
            "Process Contingency",
            "Financing Fees",
        ],
        "Amount": [
            sum(outputs["debt_drawdown_vec"][: outputs["years_construction"]]),
            outputs["toc"]
            - sum(outputs["debt_drawdown_vec"][: outputs["years_construction"]]),
            config["total_epc_cost"],
            config["total_epc_cost"] * config["extra_capex_pct"],
            config["total_epc_cost"] * config["project_contingency_pct"],
            config["total_epc_cost"] * config["process_contingency_pct"],
            config["total_epc_cost"] * config["financing_fee"],
        ],
    }
)
funding_source = ColumnDataSource(funding_df)
# sens_source = ColumnDataSource(sensitivity_df)
import pandas as pd
sens_source = ColumnDataSource(pd.DataFrame())


# --- Plots ---
annual_fig = plot_annual_cashflow_bokeh(outputs, config)
cum_fig = plot_cumulative_cashflow_bokeh(outputs, config)
dscr_fig = plot_dscr_profile_bokeh(outputs, config)
# Sensitivity plot will be created on demand in its tab

# --- Tables ---
from bokeh.models import CustomJS

# Create toggle buttons for table explanations
annual_toggle_button = Button(label="Table Column Explanations ▼", button_type="default", width=300, 
                            styles={"background": "#FFFFFF", "color": "#00375b"})

annual_table_explanation = Div(
    text="""<div style='background: rgba(0, 55, 91); padding: 12px; border-radius: 6px; border-left: 3px solid #00375b; display: none;' id='annual-explanation'>
        <div style='font-size: 12px; color: #FFFFFF; font-family: Inter, Helvetica, Arial, sans-serif; line-height: 1.4;'>
            <strong style='color: #FFFFFF;'>Unlevered CF:</strong> <span style='color: #FFFFFF;'>Project-level cash flow before debt payments</span><br>
            <strong style='color: #FFFFFF;'>Levered CF:</strong> <span style='color: #FFFFFF;'>Equity-level cash flow after debt service</span><br>
            <strong style='color: #FFFFFF;'>Revenue:</strong> <span style='color: #FFFFFF;'>Income from electricity sales</span><br>
            <strong style='color: #FFFFFF;'>O&M:</strong> <span style='color: #FFFFFF;'>Operations & Maintenance costs</span><br>
            <strong style='color: #FFFFFF;'>NOI:</strong> <span style='color: #FFFFFF;'>Net Operating Income (Revenue - Operating Costs)</span>
        </div>
    </div>""",
    width=900
)

# JavaScript callback for annual table toggle
annual_toggle_callback = CustomJS(args=dict(explanation=annual_table_explanation, button=annual_toggle_button), code="""
    const explanationDiv = explanation.text;
    if (explanationDiv.includes('display: none')) {
        explanation.text = explanationDiv.replace('display: none', 'display: block');
        button.label = 'Table Column Explanations ▲';
    } else {
        explanation.text = explanationDiv.replace('display: block', 'display: none');
        button.label = 'Table Column Explanations ▼';
    }
""")

annual_toggle_button.js_on_click(annual_toggle_callback)

annual_columns = [
    TableColumn(field="Year", title="Year"),
    TableColumn(field="Unlevered CF", title="Unlevered CF", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="Levered CF", title="Levered CF", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="Revenue", title="Revenue", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="O&M", title="O&M", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="Fuel", title="Fuel", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="Tax", title="Tax", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="NOI", title="NOI", formatter=NumberFormatter(format="$0,0")),
]
annual_table = DataTable(source=annual_source, columns=annual_columns, width=900, height=220, index_position=None)

# Cumulative table toggle
cum_toggle_button = Button(label="Cumulative Cash Flow Explanations ▼", button_type="default", width=300,
                          styles={"background": "#FFFFFF", "color": "#00375b"})

cum_table_explanation = Div(
    text="""<div style='background: rgba(0, 55, 91); padding: 12px; border-radius: 6px; border-left: 3px solid #00375b; display: none;' id='cum-explanation'>
        <div style='font-size: 12px; color: #FFFFFF; font-family: Inter, Helvetica, Arial, sans-serif; line-height: 1.4;'>
            <strong style='color: #FFFFFF;'>Cumulative Unlevered CF:</strong> <span style='color: #FFFFFF;'>Running total of project cash flows (payback timing)</span><br>
            <strong style='color: #FFFFFF;'>Cumulative Levered CF:</strong> <span style='color: #FFFFFF;'>Running total of equity returns after debt service</span>
        </div>
    </div>""",
    width=600
)

# JavaScript callback for cumulative table toggle
cum_toggle_callback = CustomJS(args=dict(explanation=cum_table_explanation, button=cum_toggle_button), code="""
    const explanationDiv = explanation.text;
    if (explanationDiv.includes('display: none')) {
        explanation.text = explanationDiv.replace('display: none', 'display: block');
        button.label = 'Cumulative Cash Flow Explanations ▲';
    } else {
        explanation.text = explanationDiv.replace('display: block', 'display: none');
        button.label = 'Cumulative Cash Flow Explanations ▼';
    }
""")

cum_toggle_button.js_on_click(cum_toggle_callback)

cum_columns = [
    TableColumn(field="Year", title="Year"),
    TableColumn(field="Cumulative Unlevered CF", title="Cumulative Unlevered CF", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="Cumulative Levered CF", title="Cumulative Levered CF", formatter=NumberFormatter(format="$0,0")),
]
cum_table = DataTable(source=cum_source, columns=cum_columns, width=600, height=220, index_position=None)

# DSCR table toggle  
dscr_toggle_button = Button(label="Debt Service Coverage Explanations ▼", button_type="default", width=300,
                           styles={"background": "#FFFFFF", "color": "#00375b"})

dscr_table_explanation = Div(
    text="""<div style='background: rgba(0, 55, 91); padding: 12px; border-radius: 6px; border-left: 3px solid #00375b; display: none;' id='dscr-explanation'>
        <div style='font-size: 12px; color: #FFFFFF; font-family: Inter, Helvetica, Arial, sans-serif; line-height: 1.4;'>
            <strong style='color: #FFFFFF;'>DSCR:</strong> <span style='color: #FFFFFF;'>Debt Service Coverage Ratio (NOI ÷ Debt Service). >1.25 typically required</span><br>
            <strong style='color: #FFFFFF;'>NOI:</strong> <span style='color: #FFFFFF;'>Net Operating Income available for debt service</span><br>
            <strong style='color: #FFFFFF;'>Debt Service:</strong> <span style='color: #FFFFFF;'>Annual principal + interest payments</span>
        </div>
    </div>""",
    width=600
)

# JavaScript callback for DSCR table toggle
dscr_toggle_callback = CustomJS(args=dict(explanation=dscr_table_explanation, button=dscr_toggle_button), code="""
    const explanationDiv = explanation.text;
    if (explanationDiv.includes('display: none')) {
        explanation.text = explanationDiv.replace('display: none', 'display: block');
        button.label = 'Debt Service Coverage Explanations ▲';
    } else {
        explanation.text = explanationDiv.replace('display: block', 'display: none');
        button.label = 'Debt Service Coverage Explanations ▼';
    }
""")

dscr_toggle_button.js_on_click(dscr_toggle_callback)

dscr_columns = [
    TableColumn(field="Year", title="Year"),
    TableColumn(field="DSCR", title="DSCR", formatter=NumberFormatter(format="0.00")),
    TableColumn(field="NOI", title="NOI", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="Debt Service", title="Debt Service", formatter=NumberFormatter(format="$0,0")),
]
dscr_table = DataTable(source=dscr_source, columns=dscr_columns, width=600, height=220, index_position=None)


# --- Download buttons ---
def make_download_button(source, label, filename):
    button = Button(label=label, button_type="primary", width=160)
    
    # Create the download callback with the data source
    download_callback = CustomJS(args=dict(source=source, filename=filename), code="""
        // Convert ColumnDataSource data to CSV
        var data = source.data;
        var columns = Object.keys(data);
        var nrows = data[columns[0]].length;
        
        // Create CSV header
        var csv = columns.join(',') + '\\n';
        
        // Add data rows
        for (var i = 0; i < nrows; i++) {
            var row = [];
            for (var j = 0; j < columns.length; j++) {
                var value = data[columns[j]][i];
                // Handle null/undefined values
                if (value === null || value === undefined) {
                    value = '';
                } else if (typeof value === 'string' && value.includes(',')) {
                    // Escape commas in string values
                    value = '"' + value + '"';
                }
                row.push(value);
            }
            csv += row.join(',') + '\\n';
        }
        
        // Create and trigger download
        var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        var link = document.createElement('a');
        if (link.download !== undefined) {
            var url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    """)
    
    button.js_on_click(download_callback)
    return button


annual_download = make_download_button(annual_source, " Download Annual Data", "annual.csv")
cum_download = make_download_button(cum_source, " Download Cumulative Data", "cumulative.csv")
dscr_download = make_download_button(dscr_source, " Download DSCR Data", "dscr.csv")
sens_download = make_download_button(sens_source, " Download Sensitivity Data", "sensitivity.csv")


# --- Layout ---
# --- Layout ---
sidebar = column(
    Div(text=APPLE_CSS),
    # Logo - Using static file serving
    Div(text="""
        <div style='text-align:center; margin-bottom:20px;'>
            <img src='assets/logo.png' alt='Company Logo' style='max-width:200px; height:auto; border-radius:8px;'/>
        </div>
    """),
    Div(text="<h2 style='margin-bottom:8px; color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'>Fusion Cashflow App</h2><p style='color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif;'>Adjust inputs and see results instantly.</p>"),
    
    # Help guide for physicists
    Div(text="""
        <div style='background: rgba(160, 196, 255, 0.1); border-left: 4px solid #A0C4FF; padding: 15px; margin: 15px 0; border-radius: 6px;'>
            <p style='color: #ffffff; margin: 0; font-size: 13px; line-height: 1.4; font-family: Inter, Helvetica, Arial, sans-serif;'>
                Hover over items with <sup style='color: #A0C4FF;'>?</sup> symbols for financial term explanations. 
            </p>
        </div>
    """),
    
    # Basic project settings
    widgets["project_name"],
    widgets["project_location"],
    widgets["construction_start_year"],
    widgets["project_energy_start_year"],
    widgets["years_construction_display"],
    widgets["plant_lifetime"],
    
    # Power and technology
    widgets["power_method"],
    widgets["net_electric_power_mw"],
    widgets["capacity_factor"],
    widgets["fuel_type"],
    
    # EPC Cost Integration
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'><span title='Engineering, Procurement & Construction - The total cost to design, procure equipment, and build the power plant' style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;' onmouseover=\"this.style.background='rgba(160, 196, 255, 0.2)'\" onmouseout=\"this.style.background='rgba(160, 196, 255, 0.1)'\">EPC Cost Integration<sup>?</sup></span></h3>"),
    widgets["auto_epc_display"],
    widgets["override_epc"],
    widgets["total_epc_cost"],
    
    # Q Engineering Integration
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'><span title='Q Engineering - The energy amplification factor (fusion power out / heating power in). Higher Q means more efficient fusion reactions' style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;' onmouseover=\"this.style.background='rgba(160, 196, 255, 0.2)'\" onmouseout=\"this.style.background='rgba(160, 196, 255, 0.1)'\">Q Engineering Integration<sup>?</sup></span></h3>"),
    widgets["auto_q_eng_display"],
    widgets["override_q_eng"],
    widgets["manual_q_eng"],
    
    # Financial parameters
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'><span title='Financial Parameters - Debt structure, interest rates, and loan terms that determine how the project is financed' style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;' onmouseover=\"this.style.background='rgba(160, 196, 255, 0.2)'\" onmouseout=\"this.style.background='rgba(160, 196, 255, 0.1)'\">Financial Parameters<sup>?</sup></span></h3>"),
    widgets["input_debt_pct"],
    widgets["cost_of_debt"],
    widgets["loan_rate"],
    widgets["financing_fee"],
    widgets["repayment_term_years"],
    widgets["grace_period_years"],
    
    # Cost parameters
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'><span title='Cost Parameters - Additional capital expenses, contingencies, operations & maintenance costs, and electricity pricing' style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;' onmouseover=\"this.style.background='rgba(160, 196, 255, 0.2)'\" onmouseout=\"this.style.background='rgba(160, 196, 255, 0.1)'\">Cost Parameters<sup>?</sup></span></h3>"),
    widgets["extra_capex_pct"],
    widgets["project_contingency_pct"],
    widgets["process_contingency_pct"],
    widgets["fixed_om_per_mw"],
    widgets["variable_om"],
    widgets["electricity_price"],
    
    # Operations
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'><span title='Operations - Plant lifetime, depreciation, end-of-life costs, tax modeling, and operational ramp-up parameters' style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;' onmouseover=\"this.style.background='rgba(160, 196, 255, 0.2)'\" onmouseout=\"this.style.background='rgba(160, 196, 255, 0.1)'\">Operations<sup>?</sup></span></h3>"),
    widgets["dep_years"],
    widgets["salvage_value"],
    widgets["decommissioning_cost"],
    widgets["use_real_dollars"],
    widgets["price_escalation_active"],
    widgets["escalation_rate"],
    widgets["include_fuel_cost"],
    widgets["apply_tax_model"],
    widgets["ramp_up"],
    widgets["ramp_up_years"],
    widgets["ramp_up_rate_per_year"],
    
    # Optimization
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'>Optimisation- Experimental</h3>"),
    widgets["optimise_target"],
    row(widgets["optimise_button"], Spacer(width=10), widgets["optimise_status"]),
    
    Spacer(height=16),
    annual_download,
    cum_download,
    dscr_download,
    sizing_mode="stretch_height",
)

# --- Chart Explanation Divs ---
annual_cf_explanation = Div(
    text="""<div style='color: #a0c4ff; font-size: 14px; margin: 10px 0 5px 0; font-weight: 600; font-family: Inter, Helvetica, Arial, sans-serif;'>
    <span title='Annual Cash Flow shows yearly money in and out. Unlevered = project-level before debt service. Levered = equity-level after debt payments' 
          style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
          onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
          onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
        ANNUAL CASH FLOWS<sup>?</sup>
    </span>
    </div>""",
    width=900
)

cumulative_cf_explanation = Div(
    text="""<div style='color: #a0c4ff; font-size: 14px; margin: 20px 0 5px 0; font-weight: 600; font-family: Inter, Helvetica, Arial, sans-serif;'>
    <span title='Cumulative Cash Flow tracks total money flow over time. When it crosses zero, the project has paid back its investment (payback point)' 
          style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
          onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
          onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
        CUMULATIVE CASH FLOWS<sup>?</sup>
    </span>
    </div>""",
    width=900
)

# --- Main Results Tab ---
main_col = column(
    highlight_div,
    annual_cf_explanation,
    annual_fig,
    annual_toggle_button,
    annual_table_explanation,
    annual_table,
    equity_metrics_div,
    cumulative_cf_explanation,
    cum_fig,
    cum_toggle_button,
    cum_table_explanation,
    cum_table,
    dscr_metrics_div,
    dscr_fig,
    dscr_toggle_button,
    dscr_table_explanation,
    dscr_table,
    sizing_mode="stretch_both",
)


# --- Main Results Tab ---
main_tab = TabPanel(child=main_col, title="Main Results")

# --- Sensitivity Analysis Tab ---
from bokeh.models import Div
grey_container_style = {
    "background": "#00375b",
    "border-radius": "16px",
    "padding": "18px 24px 18px 24px",  # Reduced bottom padding
    "margin": "16px 0 16px 0",
    "font-size": "18px",
    "font-weight": "800",
    "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
    "overflow-x": "auto",
    "width": "100%",
    "border": "1px solid #e0e0e0",
    "color": "#ffffff",
    "font-family": "Inter, Helvetica, Arial, sans-serif",
}
# Create a container for the plot
sens_fig = placeholder_fig
sens_plot_container = column(sens_fig, sizing_mode="stretch_width", styles=grey_container_style)
sens_col = column(
    Div(
        text="<h3 style='color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'>Sensitivity Analysis</h3><p style='color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif;'>Click the button to recompute sensitivity analysis with current inputs.</p>"
    ),
    row(
        Button(
            label="Run Sensitivity Analysis",
            button_type="primary",
            width=220,
            name="run_sens_btn",
        ),
        sens_download,
        Spacer(width=20),  # Add some spacing between buttons
    ),
    sens_plot_container,
    sizing_mode="stretch_both",
)
sens_tab = TabPanel(child=sens_col, title="Sensitivity Analysis")

# --- Costing Breakdown Tab ---
# Create initial costing panel with current outputs
epc_breakdown = outputs.get("epc_breakdown", {})
if epc_breakdown:
    # Create costing panel with full EPC results
    costing_panel = create_costing_panel(epc_breakdown)
else:
    # Show placeholder if no EPC breakdown available
    costing_panel = column(
        Div(
            text="""
            <h3 style='color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'>
                EPC Cost Breakdown
            </h3>
            <p style='color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif;'>
                Enable "Auto-Generate EPC" to view detailed cost breakdown.
            </p>
            """,
            styles=grey_container_style
        ),
        sizing_mode="stretch_both"
    )

costing_col = column(costing_panel, sizing_mode="stretch_both")
costing_tab = TabPanel(child=costing_col, title="Cost Breakdown")


# --- Optimization Function ---
# Global variables to track optimization state
_optimization_running = False
_optimization_result = None  # Store optimization results

def run_optimiser():
    """Run optimisation with the selected objective."""
    global _optimization_running, _optimization_result
    
    print("Optimise button clicked!")  # Debug print
    
    # Prevent multiple simultaneous optimizations
    if _optimization_running:
        print("Optimisation already running, ignoring click")
        widgets["optimise_status"].text = "Optimisation already running..."
        widgets["optimise_status"].styles = {"color": "#ffcc00", "font-size": "18px", "font-weight": "800", "font-family": "Inter, Helvetica, Arial, sans-serif"}
        return
    
    if not OPTIMIZATION_AVAILABLE:
        widgets["optimise_status"].text = "Optimisation not available"
        print("Optimisation not available")
        return
    
    # Set running flag and disable button
    _optimization_running = True
    _optimization_result = None  # Clear previous result
    widgets["optimise_button"].disabled = True
    widgets["optimise_status"].text = "Optimising... (3 attempts × 50 iterations)"
    widgets["optimise_status"].styles = {"color": "#ffcc00", "font-size": "18px", "font-weight": "800", "font-family": "Inter, Helvetica, Arial, sans-serif"}
    print("Starting optimisation...")
    
    cfg0 = get_config_from_widgets(widgets)
    
    def worker():
        global _optimization_running, _optimization_result
        try:
            print("Worker thread started")
            # Map UI labels to internal objective names
            metric_map = {
                "Max IRR": "IRR",
                "Max NPV": "NPV", 
                "Min LCOE": "LCOE"
            }
            objective = metric_map[widgets["optimise_target"].value]
            print(f"Objective: {objective}")
            
            # Get the region from project location
            from fusion_cashflow.core.cashflow_engine import map_location_to_region
            region = map_location_to_region(cfg0["project_location"])
            print(f"Region: {region}")
            
            # Create Nevergrad instrumentation for debt ratio only
            instr = ng.p.Instrumentation(
                input_debt_pct=ng.p.Scalar(lower=0.30, upper=0.90)
            )
            
            # Run multiple optimization attempts to find the absolute best
            num_attempts = 3  # Run 3 independent optimizations
            budget_per_attempt = 50  # More iterations per attempt
            
            all_results = []
            
            print(f"Running {num_attempts} optimisation attempts with {budget_per_attempt} iterations each...")
            
            for attempt in range(num_attempts):
                print(f"Starting optimisation attempt {attempt + 1}/{num_attempts}")
                
                # Use OnePlusOne optimizer with more iterations
                opt = ng.optimizers.OnePlusOne(parametrization=instr, budget=budget_per_attempt)
                attempt_best = None
                attempt_best_val = float("inf") if objective == "LCOE" else float("-inf")
                
                for i in range(opt.budget):
                    try:
                        x = opt.ask()
                        
                        # Extract debt percentage parameter - handle both dict and tuple formats
                        if hasattr(x.value, 'items') and isinstance(x.value, dict):
                            # Dictionary format
                            debt_pct = x.value["input_debt_pct"]
                        elif isinstance(x.value, tuple) and len(x.value) == 2:
                            # Tuple format (args, kwargs)
                            args, kwargs = x.value
                            debt_pct = kwargs.get("input_debt_pct", args[0] if args else 0.5)
                        elif isinstance(x.value, (list, tuple)) and len(x.value) > 0:
                            # Simple array/tuple format
                            debt_pct = x.value[0]
                        elif hasattr(x.value, '__getitem__'):
                            # Other indexable format 
                            debt_pct = x.value[0]
                        else:
                            # Single scalar value
                            debt_pct = float(x.value)
                        
                        # Create modified config with new debt ratio
                        cfg = cfg0.copy()
                        cfg["input_debt_pct"] = debt_pct
                        
                        # Run cashflow scenario
                        from fusion_cashflow.core import cashflow_engine
                        out = cashflow_engine.run_cashflow_scenario(cfg)
                        
                        # Extract objective value
                        val = {
                            "IRR": out.get("irr", -0.5),
                            "NPV": out.get("npv", -1e10), 
                            "LCOE": out.get("lcoe_val", 1000.0)
                        }[objective]
                        
                        # Calculate fitness (nevergrad minimizes, so negate for maximization)
                        fitness = -val if objective in ["IRR", "NPV"] else val
                        opt.tell(x, fitness)
                        
                        # Track best result for this attempt
                        if ((objective == "LCOE" and val < attempt_best_val) or
                            (objective != "LCOE" and val > attempt_best_val)):
                            attempt_best_val = val
                            attempt_best = (debt_pct, out)
                            
                    except Exception as e:
                        # Handle errors in individual iterations
                        print(f"Error in optimisation attempt {attempt + 1}, iteration {i}: {e}")
                        continue
                
                # Store this attempt's result
                if attempt_best is not None:
                    all_results.append((attempt_best_val, attempt_best))
                    print(f"Attempt {attempt + 1} completed: {objective}={attempt_best_val:.4f} @ debt={attempt_best[0]:.1%}")
                else:
                    print(f"Attempt {attempt + 1} failed to find valid results")
            
            # Find the absolute best result across all attempts
            if all_results:
                # Sort results: ascending for LCOE (minimize), descending for IRR/NPV (maximize)
                if objective == "LCOE":
                    all_results.sort(key=lambda x: x[0])  # Sort ascending (lower is better)
                    best_val, best = all_results[0]  # Take the lowest LCOE
                    print(f"BEST RESULT: Lowest {objective} = ${best_val:,.2f} @ debt {best[0]:.1%}")
                else:
                    all_results.sort(key=lambda x: x[0], reverse=True)  # Sort descending (higher is better)
                    best_val, best = all_results[0]  # Take the highest IRR/NPV
                    if objective == "IRR":
                        print(f"BEST RESULT: Highest {objective} = {best_val*100:.2f}% @ debt {best[0]:.1%}")
                    else:
                        print(f"BEST RESULT: Highest {objective} = ${best_val:,.0f} @ debt {best[0]:.1%}")
                
                # Show comparison of all attempts
                print("All attempts comparison:")
                for i, (val, result) in enumerate(all_results):
                    debt_pct = result[0]
                    if objective == "LCOE":
                        print(f"  Attempt {i+1}: LCOE=${val:,.2f} @ debt={debt_pct:.1%}")
                    elif objective == "IRR":
                        print(f"  Attempt {i+1}: IRR={val*100:.2f}% @ debt={debt_pct:.1%}")
                    else:
                        print(f"  Attempt {i+1}: NPV=${val:,.0f} @ debt={debt_pct:.1%}")
                        
            else:
                best = None
                best_val = None
                print("All optimisation attempts failed")
            
            print(f"Optimisation complete. Best result: {best is not None}")
            
            # Store result for periodic callback to pick up
            _optimization_result = {
                'best': best,
                'best_val': best_val,
                'objective': objective,
                'success': best is not None
            }
            if best:
                print(f"Optimisation result stored: debt={best[0]:.3f}")
            else:
                print("Optimisation result stored: debt=None")
            
        except Exception as e:
            print(f"Worker thread error: {e}")
            import traceback
            traceback.print_exc()
            _optimization_result = {
                'best': None,
                'error': str(e),
                'success': False
            }
    
    # Run optimization in background thread
    print("Starting worker thread...")
    threading.Thread(target=worker, daemon=True).start()


# Periodic callback to check for optimization results
def check_optimization_results():
    """Check if optimisation has completed and apply results."""
    global _optimization_running, _optimization_result
    
    if _optimization_result is not None:
        print("Processing optimisation result...")
        result = _optimization_result
        _optimization_result = None  # Clear the result
        
        try:
            if result['success'] and result['best'] is not None:
                debt, outputs_updated = result['best']
                objective = result['objective']
                best_val = result['best_val']
                
                print(f"Applying successful optimisation: debt={debt:.3f}")
                
                # Update the debt percentage widget
                old_value = widgets["input_debt_pct"].value
                widgets["input_debt_pct"].value = debt
                print(f"Debt widget changed from {old_value} to {widgets['input_debt_pct'].value}")
                
                # Update dashboard with optimized configuration
                config_updated = get_config_from_widgets(widgets)
                outputs_updated = run_cashflow_scenario(config_updated)
                
                # Update the highlight div with new metrics
                highlight_div.text = render_highlight_facts(outputs_updated)
                dscr_metrics_div.text = render_dscr_metrics(outputs_updated)
                equity_metrics_div.text = render_equity_metrics(outputs_updated)
                print("Highlight div and contextual financial metrics updated")
                
                # Update all plot data sources
                annual_df = pd.DataFrame({
                    "Year": outputs_updated["year_labels_int"],
                    "Unlevered CF": outputs_updated["unlevered_cf_vec"],
                    "Levered CF": outputs_updated["levered_cf_vec"],
                    "Revenue": outputs_updated["revenue_vec"],
                    "O&M": outputs_updated["om_vec"],
                    "Fuel": outputs_updated["fuel_vec"],
                    "Tax": outputs_updated["tax_vec"],
                    "NOI": outputs_updated["noi_vec"],
                })
                annual_source.data = dict(ColumnDataSource(annual_df).data)
                
                cum_df = pd.DataFrame({
                    "Year": outputs_updated["year_labels_int"],
                    "Cumulative Unlevered CF": outputs_updated["cumulative_unlevered_cf_vec"],
                    "Cumulative Levered CF": outputs_updated["cumulative_levered_cf_vec"],
                })
                cum_source.data = dict(ColumnDataSource(cum_df).data)
                
                dscr_df = pd.DataFrame({
                    "Year": outputs_updated["year_labels_int"],
                    "DSCR": outputs_updated["dscr_vec"],
                    "NOI": outputs_updated["noi_vec"],
                    "Debt Service": [a + b for a, b in zip(outputs_updated["principal_paid_vec"], outputs_updated["interest_paid_vec"])]
                })
                dscr_source.data = dict(ColumnDataSource(dscr_df).data)
                print("All data sources updated")
                
                # Format improvement message
                delta = "↓" if objective == "LCOE" else "↑"
                if objective == "LCOE":
                    best_val_formatted = f"${best_val:,.2f}"
                elif objective == "IRR":
                    best_val_formatted = f"{best_val*100:.2f}%"
                else:  # NPV
                    best_val_formatted = f"${best_val:,.0f}"
                    
                status_text = (
                    f"Optimised: {objective} {delta} to "
                    f"{best_val_formatted} @ debt {debt:.0%}"
                )
                widgets["optimise_status"].text = status_text
                widgets["optimise_status"].styles = {"color": "#00cc66", "font-size": "18px", "font-weight": "800", "font-family": "Inter, Helvetica, Arial, sans-serif"}
                print(f"Status updated: {status_text}")
                
            else:
                # Handle optimization failure
                error_msg = result.get('error', 'Unknown error')
                print(f"Optimisation failed: {error_msg}")
                widgets["optimise_status"].text = f"Optimisation failed: {error_msg[:30]}..."
                widgets["optimise_status"].styles = {"color": "#ff6b6b", "font-size": "18px", "font-weight": "800", "font-family": "Inter, Helvetica, Arial, sans-serif"}
                
        except Exception as apply_error:
            print(f"Error applying optimisation results: {apply_error}")
            import traceback
            traceback.print_exc()
            widgets["optimise_status"].text = f"Apply error: {str(apply_error)[:30]}..."
            widgets["optimise_status"].styles = {"color": "#ff6b6b", "font-size": "18px", "font-weight": "800", "font-family": "Inter, Helvetica, Arial, sans-serif"}
        
        finally:
            # Always re-enable button and reset running flag
            widgets["optimise_button"].disabled = False
            _optimization_running = False
            print("Optimisation completed and button re-enabled")


# --- Proper widget callback binding to avoid closure issues and use debouncing ---
def make_callback(widget):
    def callback(attr, old, new):
        debounced_update()

    return callback


for w in widgets.values():
    if hasattr(w, "on_change"):
        if isinstance(w, (Slider, Select, TextInput, Checkbox)):
            w.on_change(
                "value" if not isinstance(w, Checkbox) else "active", make_callback(w)
            )


# --- Sensitivity Analysis Button Callback ---
def run_sensitivity_callback():
    config = get_config_from_widgets(widgets)
    outputs = run_cashflow_scenario(config)
    sensitivity_df = run_sensitivity_analysis(config)
    sens_fig_new = plot_sensitivity_heatmap(outputs, config, sensitivity_df)
    sens_plot_container.children[0] = sens_fig_new
    
    # Update the sensitivity data source for download
    sens_source.data = ColumnDataSource.from_df(sensitivity_df)


# Find the button in sens_col and attach callback
def find_sensitivity_button(layout):
    """Recursively find the sensitivity analysis button."""
    if hasattr(layout, 'children'):
        for child in layout.children:
            if isinstance(child, Button) and getattr(child, "name", None) == "run_sens_btn":
                return child
            elif hasattr(child, 'children'):
                result = find_sensitivity_button(child)
                if result:
                    return result
    return None

sens_button = find_sensitivity_button(sens_col)
if sens_button:
    sens_button.on_click(run_sensitivity_callback)

# --- Optimization Button Callback ---
widgets["optimise_button"].on_click(run_optimiser)

# --- Tabs Layout ---



# Set initial highlight facts
highlight_div.text = render_highlight_facts(outputs)
dscr_metrics_div.text = render_dscr_metrics(outputs)
equity_metrics_div.text = render_equity_metrics(outputs)
get_avg_annual_return("Europe")
tabs = Tabs(tabs=[main_tab, sens_tab, costing_tab])



# --- Modern container styles ---
outer_container_style = {
    "background": "#00375b",
    "border-radius": "16px",
    "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
    "border": "1px solid #e0e0e0",
    "padding": "18px 24px 12px 24px",
    "margin": "32px auto",
    "display": "flex",
    "justify-content": "center",
    "align-items": "flex-start",
    "width": "100%",
    "font-family": "Inter, Helvetica, Arial, sans-serif",
    "font-weight": "800",
    "color": "#ffffff",
    # Remove max-width to allow full width
}
main_col_style = {
    "background": "#00375b",
    "border-radius": "16px",
    "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
    "border": "1px solid #e0e0e0",
    "padding": "18px 24px 12px 24px",
    "margin": "0 0 0 0",
    "width": "100%",
    "font-family": "Inter, Helvetica, Arial, sans-serif",
    "font-weight": "800",
    "color": "#ffffff",
}
sidebar_style = {
    "background": "#00375b",
    "border-radius": "16px",
    "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
    "border": "1px solid #e0e0e0",
    "padding": "18px 24px 12px 24px",
    "margin": "0 24px 0 0",
    "font-family": "Inter, Helvetica, Arial, sans-serif",
    "font-weight": "800",
    "color": "#ffffff",
}




# --- Wrap sidebar in styled container, use tabs directly ---
styled_sidebar = column(sidebar, width=360, styles=sidebar_style)
styled_tabs = tabs

# --- Layout: sidebar on left, tabs on right ---
try:
    outer_container = row(styled_sidebar, styled_tabs, width=1800)
    
    curdoc().add_root(outer_container)
    curdoc().title = "Fusion Cashflow Dashboard"
    
    # Add favicon to the document
    curdoc().template_variables["favicon"] = "assets/favicon.ico?v=20250807"
    
    update_dashboard()
    
    # Add periodic callback to check for optimization results (runs every 500ms)
    curdoc().add_periodic_callback(check_optimization_results, 500)
    
except Exception as e:
    import traceback
    traceback.print_exc()


# --- Make all plots/tables fill width ---
for fig in [annual_fig, cum_fig, dscr_fig]:
    if hasattr(fig, 'sizing_mode'):
        fig.sizing_mode = "stretch_width"
        fig.width = None
for tbl in [annual_table, cum_table, dscr_table]:
    if hasattr(tbl, 'sizing_mode'):
        tbl.sizing_mode = "stretch_width"
        tbl.width = None
