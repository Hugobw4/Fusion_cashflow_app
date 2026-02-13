import sys
import os
import threading

# Add the src directory to Python path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "..", "..", "..")
sys.path.insert(0, os.path.abspath(src_path))

print(f"Added to sys.path: {os.path.abspath(src_path)}")  # Debug print

import holoviews as hv

import pandas as pd

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
    RadioButtonGroup,
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
    sizing_mode="stretch_width",
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
        "overflow": "visible",
    },
)

# --- Equity Metrics (for cumulative cashflow chart) ---
equity_metrics_div = Div(
    text="",
    sizing_mode="stretch_width",
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
    <style>
      .main-kpi {{ position:relative; display:inline-block; margin-right:30px; }}
      .main-kpi .main-tip {{
        visibility:hidden; opacity:0; transition:opacity 0.2s;
        position:absolute; bottom:110%; left:50%; transform:translateX(-50%);
        background:#001e3c; color:#ffffff; font-size:11px; font-weight:400;
        padding:6px 10px; border-radius:6px; white-space:nowrap;
        box-shadow:0 2px 8px rgba(0,0,0,0.3); z-index:10;
        pointer-events:none;
      }}
      .main-kpi:hover .main-tip {{ visibility:visible; opacity:1; }}
      .main-kpi .kpi-lbl {{
        cursor:help; background:rgba(160,196,255,0.15); padding:2px 6px;
        border-radius:4px; transition:background 0.2s;
      }}
      .main-kpi:hover .kpi-lbl {{ background:rgba(160,196,255,0.3); }}
    </style>
    <div style='display: flex; justify-content: space-between; align-items: center; font-size: 18px; font-weight: 800; white-space: nowrap; padding: 0 20px;'>
        <div class='main-kpi'>
            <span class='kpi-lbl'><b>LCOE<sup>?</sup>:</b></span>
            <span style='color:#ffffff;font-weight:800'> {fmt(lcoe_val, 'currency_detailed')} / MWh</span>
            <div class='main-tip'>Levelized Cost of Energy &mdash; cost per MWh over plant lifetime</div>
        </div>
        <div class='main-kpi'>
            <span class='kpi-lbl'><b>IRR<sup>?</sup>:</b></span>
            <span style='color:#ffffff;font-weight:800'> {fmt(irr, 'percent')}</span>
            <div class='main-tip'>Internal Rate of Return &mdash; discount rate making NPV = 0</div>
        </div>
        <div class='main-kpi'>
            <span class='kpi-lbl'><b>NPV<sup>?</sup>:</b></span>
            <span style='color:#ffffff;font-weight:800'> {fmt(npv, 'currency')}</span>
            <div class='main-tip'>Net Present Value &mdash; present value of all future cash flows minus investment</div>
        </div>
        <div class='main-kpi' style='margin-right:0;'>
            <span class='kpi-lbl'><b>Payback<sup>?</sup>:</b></span>
            <span style='color:#ffffff;font-weight:800'> {fmt(payback, 'years')}</span>
            <div class='main-tip'>Total project payback period &mdash; time for cumulative cash flows to equal investment</div>
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
    <style>
      .dscr-kpi {{ position:relative; display:inline-block; }}
      .dscr-kpi .dscr-tip {{
        visibility:hidden; opacity:0; transition:opacity 0.2s;
        position:absolute; bottom:110%; left:50%; transform:translateX(-50%);
        background:#001e3c; color:#ffffff; font-size:11px; font-weight:400;
        padding:6px 10px; border-radius:6px; white-space:nowrap;
        box-shadow:0 2px 8px rgba(0,0,0,0.3); z-index:10;
        pointer-events:none;
      }}
      .dscr-kpi:hover .dscr-tip {{ visibility:visible; opacity:1; }}
      .dscr-kpi .dscr-lbl {{
        cursor:help; background:rgba(0,55,91,0.1); padding:2px 6px;
        border-radius:4px; transition:background 0.2s;
      }}
      .dscr-kpi:hover .dscr-lbl {{ background:rgba(0,55,91,0.2); }}
    </style>
    <div style='font-size: 14px; margin-bottom: 8px; color: #ffffff; font-weight: 600;'>DEBT SERVICE COVERAGE RATIO PROFILE</div>
    <div style='display: flex; gap: 24px;'>
        <div class='dscr-kpi'>
            <span class='dscr-lbl'><b>Min DSCR<sup>?</sup>:</b></span>
            <span style='color:#ffffff;font-weight:800'>{fmt(min_dscr, 'ratio')}</span>
            <div class='dscr-tip'>Minimum DSCR &mdash; lowest NOI-to-debt-service ratio (&gt;1.25 typically required)</div>
        </div>
        <div class='dscr-kpi'>
            <span class='dscr-lbl'><b>Avg DSCR<sup>?</sup>:</b></span>
            <span style='color:#ffffff;font-weight:800'>{fmt(avg_dscr, 'ratio')}</span>
            <div class='dscr-tip'>Average DSCR &mdash; mean NOI-to-debt-service ratio over loan term</div>
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
    <style>
      .eq-kpi {{ position:relative; display:inline-block; }}
      .eq-kpi .eq-tip {{
        visibility:hidden; opacity:0; transition:opacity 0.2s;
        position:absolute; bottom:110%; left:50%; transform:translateX(-50%);
        background:#001e3c; color:#ffffff; font-size:11px; font-weight:400;
        padding:6px 10px; border-radius:6px; white-space:nowrap;
        box-shadow:0 2px 8px rgba(0,0,0,0.3); z-index:10;
        pointer-events:none;
      }}
      .eq-kpi:hover .eq-tip {{ visibility:visible; opacity:1; }}
      .eq-kpi .eq-lbl {{
        cursor:help; background:rgba(0,55,91,0.1); padding:2px 6px;
        border-radius:4px; transition:background 0.2s;
      }}
      .eq-kpi:hover .eq-lbl {{ background:rgba(0,55,91,0.2); }}
    </style>
    <div style='font-size: 14px; margin-bottom: 8px; color: #ffffff; font-weight: 600;'>CUMULATIVE CASHFLOW PERFORMANCE</div>
    <div class='eq-kpi'>
        <span class='eq-lbl'><b>Equity Multiple<sup>?</sup>:</b></span>
        <span style='color:#ffffff;font-weight:800'>{fmt(equity_mult, 'mult')}</span>
        <div class='eq-tip'>Equity Multiple &mdash; cumulative distributions / initial equity investment</div>
    </div>
    """
    return html


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

OPTIMIZATION_AVAILABLE = True
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
    widgets["reactor_type"] = Select(
        title="Reactor Type",
        value=config.get("reactor_type", "MFE Tokamak"),
        options=["MFE Tokamak", "IFE Laser"]
    )
    widgets["net_electric_power_mw"] = Div(
        text="<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Net Electric Output (MW):</b> <span style='color:#4CAF50;'>Calculating...</span></div>",
        width=300,
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
        title="Fuel Type",
        value=config.get("fuel_type", "DT (Deuterium-Tritium)"),
        options=[
            "DT (Deuterium-Tritium)",
            "DD (Deuterium-Deuterium)",
            "DHe3 (Deuterium-Helium-3)",
            "pB11 (Proton-Boron-11)"
        ]
    )
    
    # NOAK/FOAK Selection
    widgets["noak"] = RadioButtonGroup(
        labels=["NOAK (Nth-of-a-kind)", "FOAK (First-of-a-kind)"],
        active=0 if config.get("noak", True) else 1,
        width=310
    )
    
    # Power Balance Parameters
    widgets["fusion_power_mw"] = Slider(
        title="Fusion Power Output (MW)",
        start=100,
        end=3000,
        value=config.get("fusion_power_mw", 500),
        step=10,
    )
    widgets["q_plasma"] = Slider(
        title="Plasma Q (Fusion Gain)",
        start=0.001,
        end=50,
        value=config.get("q_plasma", 10),
        step=0.001,
    )
    widgets["derived_heating_power"] = Div(
        text="<div style='color:#aaa; font-size:13px; margin:2px 0;'>Derived Heating Power: 50.0 MW</div>",
        width=300,
    )
    widgets["thermal_efficiency"] = Slider(
        title="Thermal-to-Electric Efficiency",
        start=0.35,
        end=0.55,
        value=config.get("thermal_efficiency", 0.46),
        step=0.01,
        format="0.0%",
    )
    widgets["power_balance_info"] = Div(
        text="<div style='color:#ffffff; font-size:14px; margin:10px 0; padding:8px; background:#004d73; border-radius:8px;'><b>Power Balance:</b> P_heating = P_fusion / Q<br>Q_eng = P_net / P_recirculating</div>",
        width=300,
    )
    
    widgets["input_debt_pct"] = Slider(
        title="Debt %", start=0.0, end=1.0, value=config["input_debt_pct"], step=0.01, format="0%"
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
    
    # ===== MATERIAL SELECTION SECTION =====
    widgets["materials_header"] = Div(
        text="<div style='font-size:16px; font-weight:bold; margin-top:20px; margin-bottom:10px; color:#ffffff;'>Material Selection</div>",
        width=320,
    )
    widgets["first_wall_material"] = Select(
        title="First Wall Material",
        value=config.get("first_wall_material", "Tungsten"),
        options=["Tungsten", "Beryllium", "Liquid Lithium", "FLiBe"]
    )
    widgets["blanket_type"] = Select(
        title="Blanket Type",
        value=config.get("blanket_type", "Solid Breeder (Li2TiO3)"),
        options=[
            "Solid Breeder (Li2TiO3)",
            "Solid Breeder (Li4SiO4)",
            "Flowing Liquid Breeder (PbLi)",
            "No Breeder (Aneutronic)"
        ]
    )
    widgets["structure_material"] = Select(
        title="Structure Material",
        value=config.get("structure_material", "Ferritic Steel (FMS)"),
        options=[
            "Stainless Steel (SS)",
            "Ferritic Steel (FMS)",
            "ODS Steel",
            "Vanadium"
        ]
    )
    widgets["material_cost_preview"] = Div(
        text="<div style='color:#aaa; font-size:12px; margin:5px 0;'>Material costs will be calculated...</div>",
        width=320,
    )
    
    # ===== MAGNET SECTION (MFE ONLY) =====
    widgets["magnet_header"] = Div(
        text="<div style='font-size:16px; font-weight:bold; margin-top:20px; margin-bottom:10px; color:#ffffff;'>Magnet System (MFE Only)</div>",
        width=320,
        visible=config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak"
    )
    widgets["magnet_technology"] = Select(
        title="Magnet Technology",
        value=config.get("magnet_technology", "HTS REBCO"),
        options=[
            "HTS REBCO",
            "HTS Cable-in-Conduit",
            "LTS NbTi",
            "LTS Nb3Sn",
            "Copper (resistive)"
        ],
        visible=config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak"
    )
    widgets["toroidal_field_tesla"] = Slider(
        title="Peak Toroidal Field (Tesla)",
        start=5,
        end=20,
        value=config.get("toroidal_field_tesla", 12),
        step=0.5,
        visible=config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak"
    )
    widgets["n_tf_coils"] = Slider(
        title="Number of TF Coils",
        start=8,
        end=24,
        value=config.get("n_tf_coils", 12),
        step=2,
        visible=config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak"
    )
    widgets["tape_width_m"] = Slider(
        title="HTS Tape Width (mm)",
        start=3,
        end=12,
        value=config.get("tape_width_m", 4),
        step=0.5,
        visible=config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak" and "HTS" in config.get("magnet_technology", "HTS REBCO")
    )
    widgets["coil_thickness_m"] = Slider(
        title="Coil Radial Thickness (m)",
        start=0.15,
        end=0.5,
        value=config.get("coil_thickness_m", 0.25),
        step=0.05,
        visible=config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak"
    )
    widgets["magnet_cost_preview"] = Div(
        text="<div style='color:#aaa; font-size:12px; margin:5px 0;'>Magnet costs will be calculated...</div>",
        width=320,
        visible=config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak"
    )
    
    # ===== IFE SECTION (IFE ONLY) =====
    widgets["ife_header"] = Div(
        text="<div style='font-size:16px; font-weight:bold; margin-top:20px; margin-bottom:10px; color:#ffffff;'>IFE Driver System</div>",
        width=320,
        visible=config.get("reactor_type", "MFE Tokamak") != "MFE Tokamak"
    )
    widgets["chamber_radius_m"] = Slider(
        title="Chamber Radius (m)",
        start=5,
        end=15,
        value=config.get("chamber_radius_m", 8),
        step=0.5,
        visible=config.get("reactor_type", "MFE Tokamak") != "MFE Tokamak"
    )
    widgets["driver_energy_mj"] = Slider(
        title="Driver Energy per Shot (MJ)",
        start=1,
        end=10,
        value=config.get("driver_energy_mj", 2),
        step=0.1,
        visible=config.get("reactor_type", "MFE Tokamak") != "MFE Tokamak"
    )
    widgets["repetition_rate_hz"] = Slider(
        title="Target Repetition Rate (Hz)",
        start=1,
        end=20,
        value=config.get("repetition_rate_hz", 10),
        step=1,
        visible=config.get("reactor_type", "MFE Tokamak") != "MFE Tokamak"
    )
    widgets["target_gain"] = Slider(
        title="Target Gain",
        start=10,
        end=100,
        value=config.get("target_gain", 50),
        step=5,
        visible=config.get("reactor_type", "MFE Tokamak") != "MFE Tokamak"
    )
    
    # ===== EPC OVERRIDE =====
    widgets["override_epc"] = Checkbox(
        label="Manual EPC Override", active=config.get("override_epc", False)
    )
    widgets["override_epc_value"] = TextInput(
        title="Override EPC Cost ($)",
        value=str(int(config.get("override_epc_value", 5000000000))),
        visible=config.get("override_epc", False),
    )
    
    # ===== Q ENGINEERING SECTION (Updated to Calculated/Manual mode) =====
    widgets["q_eng_mode"] = Select(
        title="Q Engineering Mode",
        value=config.get("q_eng_mode", "Calculated (from physics)"),
        options=["Calculated (from physics)", "Manual Override"]
    )
    widgets["calculated_q_eng_display"] = Div(
        text="<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Calculated Q_eng:</b> <span style='color:#4CAF50;'>Calculating...</span></div>",
        width=400,
    )
    widgets["manual_q_eng"] = Slider(
        title="Manual Q Engineering Value",
        start=1.0,
        end=15.0,
        value=config.get("manual_q_eng", 4.0),
        step=0.1,
        visible=config.get("q_eng_mode", "Calculated (from physics)") == "Manual Override"
    )
    
    # Display widgets for auto-calculated values (read-only)
    widgets["auto_epc_display"] = Div(
        text="<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Total EPC Cost:</b> Calculating...</div>",
        width=400,
    )
    # Removed auto_q_eng_display - replaced by calculated_q_eng_display above
    
    widgets["extra_capex_pct"] = Slider(
        title="Extra CapEx %",
        start=0.0,
        end=0.5,
        value=config["extra_capex_pct"],
        step=0.01,
        format="0%",
    )
    # NOTE: Contingency sliders removed - contingency is handled by CAS 29 in costing module
    # Keeping hidden widgets so get_config_from_widgets doesn't break
    widgets["project_contingency_pct"] = Slider(
        title="Project Contingency % (CAS 29)",
        start=0.0,
        end=0.5,
        value=0.0,
        step=0.01,
        format="0%",
        visible=False,
    )
    widgets["process_contingency_pct"] = Slider(
        title="Process Contingency % (CAS 29)",
        start=0.0,
        end=0.5,
        value=0.0,
        step=0.01,
        format="0%",
        visible=False,
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
    
    # ===== INDUSTRIAL HEAT SALES =====
    widgets["enable_heat_sales"] = Checkbox(
        label="Enable Industrial Heat Sales", active=config.get("enable_heat_sales", False)
    )
    widgets["heat_sales_fraction"] = Slider(
        title="Heat Sales Fraction",
        start=0.0,
        end=0.50,
        value=config.get("heat_sales_fraction", 0.10),
        step=0.01,
        format="0%",
        visible=config.get("enable_heat_sales", False),
    )
    widgets["heat_price_per_mwh_th"] = Slider(
        title="Heat Price ($/MWh_th)",
        start=5,
        end=100,
        value=config.get("heat_price_per_mwh_th", 30),
        step=1,
        visible=config.get("enable_heat_sales", False),
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
        disabled=not OPTIMIZATION_AVAILABLE,
        margin=(18, 0, 0, 0),
    )
    widgets["optimise_status"] = Div(
        text="<div style='padding:8px 12px;border-radius:8px;background:rgba(255,255,255,0.08);color:#ffffff;font-size:13px;font-weight:600;font-family:Inter,Helvetica,Arial,sans-serif;'>Ready to optimise</div>" if OPTIMIZATION_AVAILABLE else "<div style='padding:8px 12px;border-radius:8px;background:rgba(255,100,100,0.12);color:#ff6b6b;font-size:13px;font-weight:600;font-family:Inter,Helvetica,Arial,sans-serif;'>Optimisation not available</div>",
        width=280,
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
        elif isinstance(w, RadioButtonGroup):
            # Handle RadioButtonGroup (e.g., noak: 0=True, 1=False)
            if k == "noak":
                config[k] = (w.active == 0)  # 0 index = NOAK (True), 1 index = FOAK (False)
            else:
                config[k] = w.active
    
    # Map UI values to costing module enum codes
    if "fuel_type" in config:
        fuel_map = {
            "DT (Deuterium-Tritium)": "DT",
            "DD (Deuterium-Deuterium)": "DD",
            "DHe3 (Deuterium-Helium-3)": "DHE3",
            "pB11 (Proton-Boron-11)": "PB11"
        }
        config["fuel_type_code"] = fuel_map.get(config["fuel_type"], "DT")
    
    # Map reactor_type to MFE/IFE codes
    if "reactor_type" in config:
        reactor_map = {
            "MFE Tokamak": "MFE",
            "IFE Laser": "IFE"
        }
        config["reactor_type_code"] = reactor_map.get(config["reactor_type"], "MFE")
        
        # Set power_method using same canonical codes as reactor_type_code
        config["power_method"] = reactor_map.get(config["reactor_type"], "MFE")
    
    # Derive auxiliary_power_mw from fusion_power / q_plasma
    fusion_mw = config.get("fusion_power_mw", 500)
    q_plasma = config.get("q_plasma", 10)
    if q_plasma > 0:
        config["auxiliary_power_mw"] = fusion_mw / q_plasma
    else:
        config["auxiliary_power_mw"] = 50  # safety fallback
    
    # Convert tape_width from mm to m if present
    if "tape_width_m" in config:
        config["tape_width_m_actual"] = config["tape_width_m"] / 1000.0  # mm to m
    
    # Parse override_epc_value from TextInput string to float
    if "override_epc_value" in config and isinstance(config["override_epc_value"], str):
        try:
            config["override_epc_value"] = float(config["override_epc_value"])
        except ValueError:
            config["override_epc_value"] = 5_000_000_000
    
    return config


# --- Throttling/debouncing for widget updates ---

debounce_timer = None
DEBOUNCE_DELAY = 0.8  # seconds


def update_dashboard():
    config = get_config_from_widgets(widgets)
    
    # Calculate values using new costing system
    try:
        if config.get("override_epc", False):
            # Manual EPC override — skip costing, show override value
            override_val = config.get("override_epc_value", 5_000_000_000)
            widgets["auto_epc_display"].text = (
                f"<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>EPC Cost (Manual):</b> <span style='color:#FFC107;'>${override_val/1e9:.2f} B</span></div>")
            widgets["calculated_q_eng_display"].text = (
                f"<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>Q_eng:</b> <span style='color:#FFC107;'>Manual mode</span></div>")
            widgets["net_electric_power_mw"].text = (
                f"<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>Net Electric Output (MW):</b> <span style='color:#FFC107;'>Manual mode</span></div>")
        else:
            from fusion_cashflow.core.power_to_epc import compute_epc
            from fusion_cashflow.costing import compute_total_epc_cost
            
            # Get costing results
            epc_result = compute_epc(config)
        
            # Feed costing P_net back into config for cashflow engine
            p_net_from_costing = epc_result.get("power_balance", {}).get("p_net", 400)
            config["net_electric_power_mw"] = p_net_from_costing
            
            # Update Net Electric Output display
            p_net_color = "#4CAF50" if p_net_from_costing > 100 else "#FF5252"
            widgets["net_electric_power_mw"].text = (
                f"<div style='margin-bottom:10px; color:#ffffff; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>Net Electric Output (MW):</b> <span style='color:{p_net_color};'>{p_net_from_costing:.0f}</span></div>")
            
            # Update Q_eng display
            q_eng_value = epc_result.get("power_balance", {}).get("q_eng", 0)
            q_color = "#4CAF50" if q_eng_value > 1.5 else ("#FFC107" if q_eng_value > 1.0 else "#FF5252")
            widgets["calculated_q_eng_display"].text = (
                f"<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>Calculated Q_eng:</b> <span style='color:{q_color};'>{q_eng_value:.2f}</span></div>")
            
            # Update EPC display
            auto_epc_cost = epc_result.get("total_epc", 0)
            auto_epc_per_kw = epc_result.get("epc_per_kw", 0)
            widgets["auto_epc_display"].text = (
                f"<div style='margin-bottom:10px;color:#ffffff;font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'>"
                f"<b>Total EPC Cost:</b> ${auto_epc_cost/1e9:.2f} B "
                f"(${auto_epc_per_kw:,} / kW)</div>")
            
            # Update derived heating power display
            p_heating_derived = config.get("auxiliary_power_mw", 50)
            widgets["derived_heating_power"].text = (
                f"<div style='color:#aaa; font-size:13px; margin:2px 0;'>Derived Heating Power: {p_heating_derived:.1f} MW</div>")
            
            # Update material cost preview
            # Sum of firstwall + blanket + shield from detailed result
            detailed = epc_result.get("detailed_result", {})
            material_cost = (
                detailed.get("firstwall", 0) +
                detailed.get("blanket", 0) +
                detailed.get("shield", 0)
            )
            widgets["material_cost_preview"].text = (
                f"<div style='color:#aaa; font-size:12px; margin:5px 0;'>Estimated material cost: ${material_cost/1e6:.1f}M</div>")
            
            # Update magnet cost preview (MFE only)
            if config.get("reactor_type") == "MFE Tokamak":
                magnet_cost = detailed.get("cas_2203", 0)
                widgets["magnet_cost_preview"].text = (
                    f"<div style='color:#aaa; font-size:12px; margin:5px 0;'>Estimated magnet cost: ${magnet_cost/1e6:.1f}M</div>")
            
            # Update expert geometry displays
            if config.get("use_expert_geometry"):
                if config.get("reactor_type") == "MFE Tokamak":
                    total_r = (config.get("expert_major_radius_m", 3) + 
                              config.get("expert_plasma_t", 1.1) +
                              config.get("expert_vacuum_t", 0.1) +
                              config.get("expert_firstwall_t", 0.02) +
                              config.get("expert_blanket_t", 0.8) +
                              config.get("expert_reflector_t", 0.2) +
                              config.get("expert_ht_shield_t", 0.2) +
                              config.get("expert_structure_t", 0.2) +
                              config.get("expert_gap_t", 0.5) +
                              config.get("expert_vessel_t", 0.2) +
                              config.get("expert_gap2_t", 0.5) +
                              config.get("expert_lt_shield_t", 0.3) +
                              config.get("expert_coil_t", 1.0) +
                              config.get("expert_bio_shield_t", 1.0))
                    widgets["total_radius_display"].text = (
                        f"<div style='display:flex; justify-content:space-between; align-items:center; padding:12px 20px; "
                        f"font-family:Inter,Helvetica,Arial,sans-serif;'>"
                        f"<span style='font-size:14px; font-weight:700; color:#00375b;'>Total Machine Radius</span>"
                        f"<span style='font-size:20px; font-weight:800; color:#00375b;'>{total_r:.2f} m</span></div>")
                    # Update group subtotals
                    _g1_txt = f"Core: R\u2080 = {config.get('expert_major_radius_m',3):.1f} m, a = {config.get('expert_plasma_t',1.1):.1f} m"
                    widgets["mfe_group1_subtotal"].text = f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>{_g1_txt}</div>"
                    _g2 = config.get('expert_vacuum_t',0.1)+config.get('expert_firstwall_t',0.02)+config.get('expert_blanket_t',0.8)+config.get('expert_reflector_t',0.2)
                    widgets["mfe_group2_subtotal"].text = f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>Inner build: {_g2:.2f} m</div>"
                    _g3 = config.get('expert_ht_shield_t',0.2)+config.get('expert_structure_t',0.2)+config.get('expert_gap_t',0.5)
                    widgets["mfe_group3_subtotal"].text = f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>Shielding: {_g3:.2f} m</div>"
                    _g4 = config.get('expert_vessel_t',0.2)+config.get('expert_gap2_t',0.5)+config.get('expert_lt_shield_t',0.3)+config.get('expert_coil_t',1.0)+config.get('expert_bio_shield_t',1.0)
                    widgets["mfe_group4_subtotal"].text = f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>Outer: {_g4:.2f} m</div>"
                else:  # IFE
                    outer_r = (config.get("expert_chamber_radius_m", 8) +
                              config.get("expert_firstwall_t_ife", 0.005) +
                              config.get("expert_blanket_t_ife", 0.5) +
                              config.get("expert_reflector_t_ife", 0.1) +
                              config.get("expert_structure_t_ife", 0.2) +
                              config.get("expert_vessel_t_ife", 0.2))
                    widgets["outer_radius_display"].text = (
                        f"<div style='display:flex; justify-content:space-between; align-items:center; padding:12px 20px; "
                        f"font-family:Inter,Helvetica,Arial,sans-serif;'>"
                        f"<span style='font-size:14px; font-weight:700; color:#00375b;'>Outer Vessel Radius</span>"
                        f"<span style='font-size:20px; font-weight:800; color:#00375b;'>{outer_r:.2f} m</span></div>")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        widgets["calculated_q_eng_display"].text = f"<div style='margin-bottom:10px; color:#ff6b6b; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Calculated Q_eng:</b> Error: {str(e)[:50]}...</div>"
        widgets["auto_epc_display"].text = f"<div style='margin-bottom:10px; color:#ff6b6b; font-size:18px; font-weight:800; font-family:Inter, Helvetica, Arial, sans-serif;'><b>Total EPC Cost:</b> Error: {str(e)[:50]}...</div>"
    
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
        # Store region factor in config for driver analysis
        if not config.get('_region_factor'):
            from fusion_cashflow.core.power_to_epc import get_regional_factor
            config['_region_factor'] = get_regional_factor(config['project_location'])
        
        updated_costing_panel = create_costing_panel(epc_breakdown, config)
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
# Add new UI parameters to config
config["reactor_type"] = "MFE Tokamak"
config["power_method"] = "MFE"  # Canonical code: MFE, IFE, PWR
config["fuel_type"] = "DT (Deuterium-Tritium)"
config["noak"] = True
config["fusion_power_mw"] = 500
config["q_plasma"] = 10
config["auxiliary_power_mw"] = 50  # Derived from fusion_power / q_plasma
config["thermal_efficiency"] = 0.46
config["first_wall_material"] = "Tungsten"
config["blanket_type"] = "Solid Breeder (Li2TiO3)"
config["structure_material"] = "Ferritic Steel (FMS)"
config["magnet_technology"] = "HTS REBCO"
config["toroidal_field_tesla"] = 12
config["n_tf_coils"] = 12
config["tape_width_m"] = 4  # mm
config["coil_thickness_m"] = 0.25
config["chamber_radius_m"] = 8
config["driver_energy_mj"] = 2
config["q_eng_mode"] = "Calculated (from physics)"
config["use_expert_geometry"] = False
# No need for override_epc or total_epc_cost - always use embedded costing now
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
def update_fuel_type_based_on_reactor_type(attr, old, new):
    """Update fuel type options based on reactor type selection."""
    reactor_type = widgets["reactor_type"].value
    # No longer restrict fuel types - all fusion reactors can use any fuel
    # This function kept for potential future fuel type validation
    pass

def update_config_based_on_reactor_type(attr, old, new):
    """Update all configuration parameters when reactor type changes."""
    # Reactor type changes are now handled by toggle_reactor_type_visibility()
    # This function kept for potential future configuration updates
    pass

# Attach reactor_type callbacks (in addition to visibility callbacks below)
# Note: These are mostly placeholders now; main logic is in toggle_reactor_type_visibility()
widgets["reactor_type"].on_change("value", update_fuel_type_based_on_reactor_type)
widgets["reactor_type"].on_change("value", update_config_based_on_reactor_type)

# --- EPC and Q Engineering Visibility Toggle Functions ---
def toggle_epc_slider_visibility(attr, old, new):
    """Show/hide the manual EPC override text input based on checkbox."""
    widgets["override_epc_value"].visible = new

def toggle_heat_sales_visibility(attr, old, new):
    """Show/hide the heat sales sliders based on checkbox."""
    widgets["heat_sales_fraction"].visible = new
    widgets["heat_price_per_mwh_th"].visible = new

def toggle_q_eng_slider_visibility(attr, old, new):
    """Show/hide the manual Q Engineering slider based on q_eng_mode."""
    if new == "Manual Override":
        widgets["manual_q_eng"].visible = True
        widgets["calculated_q_eng_display"].visible = False
    else:
        widgets["manual_q_eng"].visible = False
        widgets["calculated_q_eng_display"].visible = True

def toggle_reactor_type_visibility(attr, old, new):
    """Show/hide sections based on reactor type (MFE vs IFE)."""
    is_mfe = (new == "MFE Tokamak")
    is_ife = (new == "IFE Laser")
    
    # Magnet section (MFE only)
    widgets["magnet_header"].visible = is_mfe
    widgets["magnet_technology"].visible = is_mfe
    widgets["toroidal_field_tesla"].visible = is_mfe
    widgets["n_tf_coils"].visible = is_mfe
    widgets["tape_width_m"].visible = is_mfe and "HTS" in widgets["magnet_technology"].value
    widgets["coil_thickness_m"].visible = is_mfe
    widgets["magnet_cost_preview"].visible = is_mfe
    
    # IFE section (IFE only)
    widgets["ife_header"].visible = is_ife
    widgets["chamber_radius_m"].visible = is_ife
    widgets["driver_energy_mj"].visible = is_ife
    widgets["repetition_rate_hz"].visible = is_ife
    widgets["target_gain"].visible = is_ife
    
    # Expert geometry sections
    use_expert = widgets["use_expert_geometry"].active
    widgets["mfe_geometry_header"].visible = is_mfe and use_expert
    widgets["mfe_group1_header"].visible = is_mfe and use_expert
    widgets["expert_major_radius_m"].visible = is_mfe and use_expert
    widgets["expert_plasma_t"].visible = is_mfe and use_expert
    widgets["expert_elongation"].visible = is_mfe and use_expert
    widgets["mfe_group1_subtotal"].visible = is_mfe and use_expert
    widgets["mfe_group2_header"].visible = is_mfe and use_expert
    widgets["expert_vacuum_t"].visible = is_mfe and use_expert
    widgets["expert_firstwall_t"].visible = is_mfe and use_expert
    widgets["expert_blanket_t"].visible = is_mfe and use_expert
    widgets["expert_reflector_t"].visible = is_mfe and use_expert
    widgets["mfe_group2_subtotal"].visible = is_mfe and use_expert
    widgets["mfe_group3_header"].visible = is_mfe and use_expert
    widgets["expert_ht_shield_t"].visible = is_mfe and use_expert
    widgets["expert_structure_t"].visible = is_mfe and use_expert
    widgets["expert_gap_t"].visible = is_mfe and use_expert
    widgets["mfe_group3_subtotal"].visible = is_mfe and use_expert
    widgets["mfe_group4_header"].visible = is_mfe and use_expert
    widgets["expert_vessel_t"].visible = is_mfe and use_expert
    widgets["expert_gap2_t"].visible = is_mfe and use_expert
    widgets["expert_lt_shield_t"].visible = is_mfe and use_expert
    widgets["expert_coil_t"].visible = is_mfe and use_expert
    widgets["expert_bio_shield_t"].visible = is_mfe and use_expert
    widgets["mfe_group4_subtotal"].visible = is_mfe and use_expert
    widgets["total_radius_display"].visible = is_mfe and use_expert
    
    widgets["ife_geometry_header"].visible = is_ife and use_expert
    widgets["ife_group_header"].visible = is_ife and use_expert
    widgets["expert_chamber_radius_m"].visible = is_ife and use_expert
    widgets["expert_firstwall_t_ife"].visible = is_ife and use_expert
    widgets["expert_blanket_t_ife"].visible = is_ife and use_expert
    widgets["expert_reflector_t_ife"].visible = is_ife and use_expert
    widgets["expert_structure_t_ife"].visible = is_ife and use_expert
    widgets["expert_vessel_t_ife"].visible = is_ife and use_expert
    widgets["outer_radius_display"].visible = is_ife and use_expert

def toggle_magnet_technology_visibility(attr, old, new):
    """Show/hide HTS tape width based on magnet technology."""
    widgets["tape_width_m"].visible = "HTS" in new and widgets["reactor_type"].value == "MFE Tokamak"

def toggle_expert_geometry_visibility(attr, old, new):
    """Enable/disable expert geometry sliders based on checkbox."""
    is_mfe = widgets["reactor_type"].value == "MFE Tokamak"
    is_ife = widgets["reactor_type"].value == "IFE Laser"
    
    # MFE geometry
    widgets["mfe_geometry_header"].visible = is_mfe and new
    widgets["mfe_group1_header"].visible = is_mfe and new
    widgets["expert_major_radius_m"].visible = is_mfe and new
    widgets["expert_plasma_t"].visible = is_mfe and new
    widgets["expert_elongation"].visible = is_mfe and new
    widgets["mfe_group1_subtotal"].visible = is_mfe and new
    widgets["mfe_group2_header"].visible = is_mfe and new
    widgets["expert_vacuum_t"].visible = is_mfe and new
    widgets["expert_firstwall_t"].visible = is_mfe and new
    widgets["expert_blanket_t"].visible = is_mfe and new
    widgets["expert_reflector_t"].visible = is_mfe and new
    widgets["mfe_group2_subtotal"].visible = is_mfe and new
    widgets["mfe_group3_header"].visible = is_mfe and new
    widgets["expert_ht_shield_t"].visible = is_mfe and new
    widgets["expert_structure_t"].visible = is_mfe and new
    widgets["expert_gap_t"].visible = is_mfe and new
    widgets["mfe_group3_subtotal"].visible = is_mfe and new
    widgets["mfe_group4_header"].visible = is_mfe and new
    widgets["expert_vessel_t"].visible = is_mfe and new
    widgets["expert_gap2_t"].visible = is_mfe and new
    widgets["expert_lt_shield_t"].visible = is_mfe and new
    widgets["expert_coil_t"].visible = is_mfe and new
    widgets["expert_bio_shield_t"].visible = is_mfe and new
    widgets["mfe_group4_subtotal"].visible = is_mfe and new
    widgets["total_radius_display"].visible = is_mfe and new
    
    # IFE geometry
    widgets["ife_geometry_header"].visible = is_ife and new
    widgets["ife_group_header"].visible = is_ife and new
    widgets["expert_chamber_radius_m"].visible = is_ife and new
    widgets["expert_firstwall_t_ife"].visible = is_ife and new
    widgets["expert_blanket_t_ife"].visible = is_ife and new
    widgets["expert_reflector_t_ife"].visible = is_ife and new
    widgets["expert_structure_t_ife"].visible = is_ife and new
    widgets["expert_vessel_t_ife"].visible = is_ife and new
    widgets["outer_radius_display"].visible = is_ife and new

# Set up visibility toggle callbacks
widgets["override_epc"].on_change("active", toggle_epc_slider_visibility)
widgets["enable_heat_sales"].on_change("active", toggle_heat_sales_visibility)
widgets["q_eng_mode"].on_change("value", toggle_q_eng_slider_visibility)
widgets["reactor_type"].on_change("value", toggle_reactor_type_visibility)
widgets["magnet_technology"].on_change("value", toggle_magnet_technology_visibility)

# Initial cashflow calculation with error handling
try:
    outputs = run_cashflow_scenario(config)
    print("Initial cashflow scenario completed successfully")
except Exception as e:
    import traceback
    print(f"ERROR during initial cashflow calculation: {e}")
    traceback.print_exc()
    # Provide fallback outputs to prevent dashboard from breaking
    outputs = {
        "year_labels_int": list(range(2028, 2088)),
        "unlevered_cf_vec": [0] * 60,
        "levered_cf_vec": [0] * 60,
        "revenue_vec": [0] * 60,
        "om_vec": [0] * 60,
        "fuel_vec": [0] * 60,
        "tax_vec": [0] * 60,
        "noi_vec": [0] * 60,
        "cumulative_unlevered_cf_vec": [0] * 60,
        "cumulative_levered_cf_vec": [0] * 60,
        "dscr_vec": [0] * 60,
        "principal_paid_vec": [0] * 60,
        "interest_paid_vec": [0] * 60,
        "npv": 0,
        "irr": 0,
        "lcoe_val": 0,
        "payback_period": 0,
        "avg_dscr": 0,
        "equity_multiple": 0,
    }

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
            outputs.get("total_epc_cost", 5_000_000_000),  # Get from outputs
            outputs.get("total_epc_cost", 5_000_000_000) * config["extra_capex_pct"],
            outputs.get("total_epc_cost", 5_000_000_000) * config["project_contingency_pct"],
            outputs.get("total_epc_cost", 5_000_000_000) * config["process_contingency_pct"],
            outputs.get("total_epc_cost", 5_000_000_000) * config["financing_fee"],
        ],
    }
)
funding_source = ColumnDataSource(funding_df)
# sens_source = ColumnDataSource(sensitivity_df)
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
def make_download_button(source, label, data_type, project_widget):
    button = Button(label=label, button_type="primary", width=160)
    
    # Create the download callback with the data source and project name
    download_callback = CustomJS(args=dict(source=source, data_type=data_type, project_widget=project_widget), code="""
        // Get project name and sanitize it
        var projectName = project_widget.value || 'Project';
        projectName = projectName.replace(/[^a-zA-Z0-9]/g, '_');
        
        // Generate timestamp (DD_MM_YYYY format)
        var now = new Date();
        var timestamp = now.getDate().toString().padStart(2, '0') + '_' +
                       (now.getMonth() + 1).toString().padStart(2, '0') + '_' +
                       now.getFullYear().toString();
        
        // Construct filename
        var filename = 'FAS_Cashflow_' + projectName + '_' + timestamp + '_' + data_type + '.csv';
        
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


annual_download = make_download_button(annual_source, " Download Annual Data", "annual", widgets["project_name"])
cum_download = make_download_button(cum_source, " Download Cumulative Data", "cumulative", widgets["project_name"])
dscr_download = make_download_button(dscr_source, " Download DSCR Data", "dscr", widgets["project_name"])
sens_download = make_download_button(sens_source, " Download Sensitivity Data", "sensitivity", widgets["project_name"])


# --- Layout ---
# Tooltip CSS for sidebar section headers (each Bokeh Div is isolated, so every tooltip needs its own style block)
_TIP_CSS = (
    "<style>"
    ".sb-tip-wrap{position:relative;display:inline-block}"
    ".sb-tip-wrap .sb-tip{visibility:hidden;opacity:0;transition:opacity .2s;position:absolute;bottom:110%;left:50%;transform:translateX(-50%);"
    "background:#001e3c;color:#fff;font-size:11px;font-weight:400;padding:6px 10px;border-radius:6px;white-space:nowrap;"
    "box-shadow:0 2px 8px rgba(0,0,0,.3);z-index:10;pointer-events:none}"
    ".sb-tip-wrap:hover .sb-tip{visibility:visible;opacity:1}"
    ".sb-tip-wrap .sb-lbl{cursor:help;background:rgba(160,196,255,.15);padding:2px 6px;border-radius:4px;transition:background .2s}"
    ".sb-tip-wrap:hover .sb-lbl{background:rgba(160,196,255,.3)}"
    "</style>"
)
_H3 = "margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;"

def _section_tip(label: str, tip: str) -> Div:
    """Return a sidebar section header Div with a hover tooltip."""
    return Div(text=f"<h3 style='{_H3}'>{_TIP_CSS}<span class='sb-tip-wrap'><span class='sb-lbl'>{label}<sup>?</sup></span><span class='sb-tip'>{tip}</span></span></h3>")

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
    widgets["reactor_type"],
    widgets["net_electric_power_mw"],
    widgets["capacity_factor"],
    widgets["fuel_type"],
    widgets["noak"],
    
    # Power Balance Parameters
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'>Power Balance</h3>"),
    widgets["fusion_power_mw"],
    widgets["q_plasma"],
    widgets["derived_heating_power"],
    widgets["thermal_efficiency"],
    widgets["power_balance_info"],
    
    # Material Selection
    widgets["materials_header"],
    widgets["first_wall_material"],
    widgets["blanket_type"],
    widgets["structure_material"],
    widgets["material_cost_preview"],
    
    # Magnet System (MFE Only)
    widgets["magnet_header"],
    widgets["magnet_technology"],
    widgets["toroidal_field_tesla"],
    widgets["n_tf_coils"],
    widgets["tape_width_m"],
    widgets["coil_thickness_m"],
    widgets["magnet_cost_preview"],
    
    # IFE Driver System
    widgets["ife_header"],
    widgets["chamber_radius_m"],
    widgets["driver_energy_mj"],
    widgets["repetition_rate_hz"],
    widgets["target_gain"],
    
    # EPC Cost Integration
    _section_tip("EPC Cost Integration", "Total cost to design, procure equipment, and build the plant"),
    widgets["auto_epc_display"],
    widgets["override_epc"],
    widgets["override_epc_value"],
    
    # Q Engineering Integration
    _section_tip("Q Engineering Integration", "Energy amplification factor (fusion power out / heating power in)"),
    widgets["q_eng_mode"],
    widgets["calculated_q_eng_display"],
    widgets["manual_q_eng"],
    
    # Financial parameters
    _section_tip("Financial Parameters", "Debt structure, interest rates, and loan terms"),
    widgets["input_debt_pct"],
    widgets["loan_rate"],
    widgets["financing_fee"],
    widgets["repayment_term_years"],
    widgets["grace_period_years"],
    
    # Cost parameters
    _section_tip("Cost Parameters", "CapEx, contingencies, O&amp;M costs, and electricity pricing"),
    widgets["extra_capex_pct"],
    widgets["project_contingency_pct"],
    widgets["process_contingency_pct"],
    widgets["fixed_om_per_mw"],
    widgets["variable_om"],
    widgets["electricity_price"],
    
    # Industrial heat sales
    _section_tip("Industrial Heat Sales", "Optional revenue from selling thermal energy to industrial customers"),
    widgets["enable_heat_sales"],
    widgets["heat_sales_fraction"],
    widgets["heat_price_per_mwh_th"],
    
    # Operations
    _section_tip("Operations", "Lifetime, depreciation, decommissioning, tax &amp; ramp-up"),
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
    Div(text="<h3 style='margin-top:20px;color:#ffffff; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'>Optimisation — Experimental</h3>"),
    row(widgets["optimise_target"], Spacer(width=10), widgets["optimise_button"]),
    widgets["optimise_status"],
    
    Spacer(height=16),
    annual_download,
    cum_download,
    dscr_download,
    sizing_mode="stretch_height",
)

# --- Chart Explanation Divs ---
annual_cf_explanation = Div(
    text="""<style>.cf-tip-wrap{position:relative;display:inline-block}.cf-tip-wrap .cf-tip{visibility:hidden;opacity:0;transition:opacity .2s;position:absolute;bottom:110%;left:50%;transform:translateX(-50%);background:#001e3c;color:#fff;font-size:11px;font-weight:400;padding:6px 10px;border-radius:6px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.3);z-index:10;pointer-events:none}.cf-tip-wrap:hover .cf-tip{visibility:visible;opacity:1}.cf-tip-wrap .cf-lbl{cursor:help;background:rgba(160,196,255,.15);padding:2px 6px;border-radius:4px;transition:background .2s}.cf-tip-wrap:hover .cf-lbl{background:rgba(160,196,255,.3)}</style>
    <div style='color: #a0c4ff; font-size: 14px; margin: 10px 0 5px 0; font-weight: 600; font-family: Inter, Helvetica, Arial, sans-serif;'>
    <span class='cf-tip-wrap'>
        <span class='cf-lbl'>ANNUAL CASH FLOWS<sup>?</sup></span>
        <span class='cf-tip'>Unlevered = project-level before debt. Levered = equity-level after debt payments</span>
    </span>
    </div>""",
    width=900
)

cumulative_cf_explanation = Div(
    text="""<style>.cf-tip-wrap{position:relative;display:inline-block}.cf-tip-wrap .cf-tip{visibility:hidden;opacity:0;transition:opacity .2s;position:absolute;bottom:110%;left:50%;transform:translateX(-50%);background:#001e3c;color:#fff;font-size:11px;font-weight:400;padding:6px 10px;border-radius:6px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.3);z-index:10;pointer-events:none}.cf-tip-wrap:hover .cf-tip{visibility:visible;opacity:1}.cf-tip-wrap .cf-lbl{cursor:help;background:rgba(160,196,255,.15);padding:2px 6px;border-radius:4px;transition:background .2s}.cf-tip-wrap:hover .cf-lbl{background:rgba(160,196,255,.3)}</style>
    <div style='color: #a0c4ff; font-size: 14px; margin: 20px 0 5px 0; font-weight: 600; font-family: Inter, Helvetica, Arial, sans-serif;'>
    <span class='cf-tip-wrap'>
        <span class='cf-lbl'>CUMULATIVE CASH FLOWS<sup>?</sup></span>
        <span class='cf-tip'>Total money flow over time &mdash; zero-crossing = payback point</span>
    </span>
    </div>""",
    width=900
)

# --- Main Results Tab ---
# Create empty main_col - will be populated by update_dashboard()
main_col = column()

# --- Main Results Tab ---
main_tab = TabPanel(child=main_col, title="Main Results")

# --- Sensitivity Analysis Tab ---
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
        text="<h3 style='color:#00375b; font-family:Inter, Helvetica, Arial, sans-serif; font-weight:800;'>Sensitivity Analysis</h3><p style='color:#333333; font-family:Inter, Helvetica, Arial, sans-serif;'>Click the button to recompute sensitivity analysis with current inputs.</p>"
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
    styles={'max-width': '92%'},
)
sens_tab = TabPanel(child=sens_col, title="Sensitivity Analysis")

# --- Costing Breakdown Tab ---
# Create initial costing panel with current outputs
epc_breakdown = outputs.get("epc_breakdown", {})
if epc_breakdown:
    # Store region factor in config for driver analysis
    if not config.get('_region_factor'):
        from fusion_cashflow.core.power_to_epc import get_regional_factor
        config['_region_factor'] = get_regional_factor(config['project_location'])
    
    # Create costing panel with full EPC results and config
    costing_panel = create_costing_panel(epc_breakdown, config)
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
        )
    )

costing_col = column(costing_panel, styles={'background': '#f5f5f5', 'border-radius': '16px', 'padding': '12px'})
costing_tab = TabPanel(child=costing_col, title="Cost Breakdown")


# --- Optimization Function (multi-variable, no nevergrad) ---
# Global variables to track optimization state
_optimization_running = False
_optimization_result = None  # Store optimization results

def _opt_status_html(text, color="#ffffff", bg="rgba(255,255,255,0.08)"):
    """Wrap optimiser status text in a styled card."""
    return (
        f"<div style='padding:8px 12px;border-radius:8px;background:{bg};"
        f"color:{color};font-size:13px;font-weight:600;"
        f"font-family:Inter,Helvetica,Arial,sans-serif;line-height:1.5;'>"
        f"{text}</div>"
    )

# Optimisation search space — matches slider bounds
_OPT_VARS = {
    "input_debt_pct":   {"low": 0.10, "high": 0.90, "step": 0.01},
    "capacity_factor":  {"low": 0.50, "high": 0.95, "step": 0.01},
    "electricity_price":{"low": 30,   "high": 400,  "step": 1},
    "plant_lifetime":   {"low": 25,   "high": 60,   "step": 1},
}

def _latin_hypercube(n, rng):
    """Return n quasi-random samples in [0,1)^d via Latin Hypercube Sampling."""
    import numpy as np
    d = len(_OPT_VARS)
    result = np.zeros((n, d))
    for j in range(d):
        perm = rng.permutation(n)
        for i in range(n):
            result[i, j] = (perm[i] + rng.random()) / n
    return result

def _sample_to_config(unit_vec):
    """Map a [0,1]^d vector to actual config values (respecting step)."""
    import numpy as np
    out = {}
    for idx, (key, spec) in enumerate(_OPT_VARS.items()):
        raw = spec["low"] + unit_vec[idx] * (spec["high"] - spec["low"])
        # Snap to step
        raw = round(raw / spec["step"]) * spec["step"]
        raw = max(spec["low"], min(spec["high"], raw))
        out[key] = raw
    return out

def run_optimiser():
    """Multi-variable optimiser: LHS exploration + local refinement (~48 evals)."""
    global _optimization_running, _optimization_result
    import numpy as np

    if _optimization_running:
        widgets["optimise_status"].text = _opt_status_html("Optimisation already running...", "#ffcc00", "rgba(255,204,0,0.10)")
        return

    _optimization_running = True
    _optimization_result = None
    widgets["optimise_button"].disabled = True
    widgets["optimise_status"].text = _opt_status_html("Optimising… ~48 evaluations", "#ffcc00", "rgba(255,204,0,0.10)")

    cfg0 = get_config_from_widgets(widgets)

    def worker():
        global _optimization_running, _optimization_result
        try:
            metric_map = {"Max IRR": "IRR", "Max NPV": "NPV", "Min LCOE": "LCOE"}
            objective = metric_map[widgets["optimise_target"].value]
            minimise = (objective == "LCOE")

            rng = np.random.default_rng(42)

            def evaluate(overrides):
                """Run one cashflow scenario and return the objective value."""
                cfg = cfg0.copy()
                cfg.update(overrides)
                out = run_cashflow_scenario(cfg)
                val = {
                    "IRR":  out.get("irr", -0.5),
                    "NPV":  out.get("npv", -1e10),
                    "LCOE": out.get("lcoe_val", 1000.0),
                }[objective]
                return val, overrides, out

            # --- Phase 1: Latin Hypercube exploration (24 samples) ---
            lhs = _latin_hypercube(24, rng)
            results = []
            for row in lhs:
                try:
                    overrides = _sample_to_config(row)
                    val, ov, out = evaluate(overrides)
                    results.append((val, ov, out))
                except Exception:
                    continue

            if not results:
                _optimization_result = {"success": False, "error": "All evaluations failed"}
                return

            # Sort: ascending for LCOE, descending for IRR/NPV
            results.sort(key=lambda x: x[0], reverse=not minimise)

            # --- Phase 2: Local refinement around top-3 (8 perturbations each) ---
            top3 = results[:3]
            var_keys = list(_OPT_VARS.keys())
            for best_val, best_ov, best_out in top3:
                for _ in range(8):
                    try:
                        perturbed = {}
                        for key in var_keys:
                            spec = _OPT_VARS[key]
                            # ±10% of range, Gaussian
                            delta = rng.normal(0, 0.10) * (spec["high"] - spec["low"])
                            raw = best_ov[key] + delta
                            raw = round(raw / spec["step"]) * spec["step"]
                            raw = max(spec["low"], min(spec["high"], raw))
                            perturbed[key] = raw
                        val, ov, out = evaluate(perturbed)
                        results.append((val, ov, out))
                    except Exception:
                        continue

            # Final sort and pick best
            results.sort(key=lambda x: x[0], reverse=not minimise)
            best_val, best_ov, best_out = results[0]

            _optimization_result = {
                "success": True,
                "best_overrides": best_ov,
                "best_val": best_val,
                "best_outputs": best_out,
                "objective": objective,
                "n_evals": len(results),
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            _optimization_result = {"success": False, "error": str(e)}

    threading.Thread(target=worker, daemon=True).start()


# Periodic callback to check for optimization results
def check_optimization_results():
    """Check if optimisation has completed and apply results."""
    global _optimization_running, _optimization_result

    if _optimization_result is not None:
        result = _optimization_result
        _optimization_result = None

        try:
            if result["success"]:
                best_ov = result["best_overrides"]
                best_val = result["best_val"]
                objective = result["objective"]
                n_evals = result.get("n_evals", "?")

                # Apply optimised values to sliders
                for key, val in best_ov.items():
                    if key in widgets:
                        widgets[key].value = val

                # Re-run scenario with updated widgets and refresh dashboard
                config_updated = get_config_from_widgets(widgets)
                outputs_updated = run_cashflow_scenario(config_updated)

                highlight_div.text = render_highlight_facts(outputs_updated)
                dscr_metrics_div.text = render_dscr_metrics(outputs_updated)
                equity_metrics_div.text = render_equity_metrics(outputs_updated)

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

                # Format status message
                delta = "↓" if objective == "LCOE" else "↑"
                if objective == "LCOE":
                    fmt_val = f"${best_val:,.2f}"
                elif objective == "IRR":
                    fmt_val = f"{best_val*100:.2f}%"
                else:
                    fmt_val = f"${best_val:,.0f}"

                parts = []
                _short = {"input_debt_pct": "Debt", "capacity_factor": "CF",
                           "electricity_price": "Price", "plant_lifetime": "Life"}
                for k, v in best_ov.items():
                    lbl = _short.get(k, k)
                    if k in ("input_debt_pct", "capacity_factor"):
                        parts.append(f"{lbl} {v:.0%}")
                    elif k == "electricity_price":
                        parts.append(f"{lbl} ${v:.0f}/MWh")
                    elif k == "plant_lifetime":
                        parts.append(f"{lbl} {int(v)}yr")
                summary = " &middot; ".join(parts)

                status_text = (
                    f"<b>{objective} {delta} {fmt_val}</b><br>"
                    f"<span style='font-size:12px;font-weight:400;opacity:0.85;'>{summary} &nbsp;·&nbsp; {n_evals} evals</span>"
                )
                widgets["optimise_status"].text = _opt_status_html(status_text, "#00cc66", "rgba(0,204,102,0.10)")

            else:
                error_msg = result.get("error", "Unknown error")
                widgets["optimise_status"].text = _opt_status_html(f"Optimisation failed: {error_msg[:40]}", "#ff6b6b", "rgba(255,100,100,0.10)")

        except Exception as apply_error:
            import traceback
            traceback.print_exc()
            widgets["optimise_status"].text = _opt_status_html(f"Apply error: {str(apply_error)[:40]}", "#ff6b6b", "rgba(255,100,100,0.10)")

        finally:
            widgets["optimise_button"].disabled = False
            _optimization_running = False


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
        elif isinstance(w, RadioButtonGroup):
            w.on_change("active", make_callback(w))


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

# --- Expert Config Tab Creation ---
# Create expert geometry widgets
widgets["expert_header"] = Div(
    text="""
    <div style='font-family:Inter,Helvetica,Arial,sans-serif;'>
        <h3 style='margin:0 0 8px 0; color:#ffffff; font-size:18px; font-weight:700;'>Expert Configuration</h3>
        <p style='margin:0; color:rgba(255,255,255,0.8); font-size:13px; line-height:1.5;'>
            Override template-based geometry with custom radial build.
            <b style="color:#ffffff;">All parameters must be specified together</b> — partial overrides not supported.
        </p>
    </div>""",
    styles={"background": "#00375b", "padding": "18px 24px", "border-radius": "16px", "color": "#ffffff",
            "font-family": "Inter, Helvetica, Arial, sans-serif", "margin-bottom": "16px"},
)

widgets["use_expert_geometry"] = Checkbox(
    label="Enable Expert Geometry Override (unchecked = use template defaults)",
    active=config.get("use_expert_geometry", False)
)

widgets["geometry_mode_info"] = Div(
    text="<div style='color:#6b7280; font-size:12px; margin:8px 0 16px 0;'>When disabled, geometry auto-scales from reactor type and power level using proven templates.</div>",
)

# --- MFE Card Styles ---
_card_style = ("background:#fafafa; border:1px solid rgba(0,0,0,0.08); border-radius:12px; "
               "padding:14px 20px; margin-bottom:12px; font-family:Inter,Helvetica,Arial,sans-serif;")
_card_hdr = lambda title, subtitle: (
    f"<div style='{_card_style}'>"
    f"<div style='font-size:14px; font-weight:700; color:#00375b; margin-bottom:2px;'>{title}</div>"
    f"<div style='font-size:11px; color:#6b7280;'>{subtitle}</div></div>"
)

# MFE Section Header
_mfe_vis = config.get("reactor_type", "MFE Tokamak") == "MFE Tokamak" and config.get("use_expert_geometry", False)
widgets["mfe_geometry_header"] = Div(
    text="<div style='font-size:16px; font-weight:700; color:#00375b; margin:8px 0 4px 0; font-family:Inter,Helvetica,Arial,sans-serif;'>MFE Tokamak Radial Build</div>",
    visible=_mfe_vis,
)

# --- Group 1: Core Plasma ---
widgets["mfe_group1_header"] = Div(
    text=_card_hdr("Core Plasma", "Plasma shape and major geometry"),
    visible=_mfe_vis,
)
widgets["expert_major_radius_m"] = Slider(title="Major Radius R\u2080 (m)", start=2, end=10, value=config.get("expert_major_radius_m", 3), step=0.1, visible=_mfe_vis)
widgets["expert_plasma_t"] = Slider(title="Plasma Thickness / Minor Radius (m)", start=0.5, end=3, value=config.get("expert_plasma_t", 1.1), step=0.1, visible=_mfe_vis)
widgets["expert_elongation"] = Slider(title="Plasma Elongation \u03ba", start=1.0, end=4.0, value=config.get("expert_elongation", 3.0), step=0.1, visible=_mfe_vis)
widgets["mfe_group1_subtotal"] = Div(
    text=f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>Core: R\u2080 = {config.get('expert_major_radius_m',3):.1f} m, a = {config.get('expert_plasma_t',1.1):.1f} m</div>",
    visible=_mfe_vis,
)

# --- Group 2: Inner Components ---
widgets["mfe_group2_header"] = Div(
    text=_card_hdr("Inner Components", "First wall through reflector"),
    visible=_mfe_vis,
)
widgets["expert_vacuum_t"] = Slider(title="Vacuum Gap (m)", start=0.05, end=0.5, value=config.get("expert_vacuum_t", 0.1), step=0.01, visible=_mfe_vis)
widgets["expert_firstwall_t"] = Slider(title="First Wall (m)", start=0.005, end=0.05, value=config.get("expert_firstwall_t", 0.02), step=0.005, visible=_mfe_vis)
widgets["expert_blanket_t"] = Slider(title="Blanket (m)", start=0.3, end=1.5, value=config.get("expert_blanket_t", 0.8), step=0.05, visible=_mfe_vis)
widgets["expert_reflector_t"] = Slider(title="Reflector (m)", start=0.1, end=0.5, value=config.get("expert_reflector_t", 0.2), step=0.05, visible=_mfe_vis)
_g2_sum = sum(config.get(k, d) for k, d in [("expert_vacuum_t",0.1),("expert_firstwall_t",0.02),("expert_blanket_t",0.8),("expert_reflector_t",0.2)])
widgets["mfe_group2_subtotal"] = Div(
    text=f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>Inner build: {_g2_sum:.2f} m</div>",
    visible=_mfe_vis,
)

# --- Group 3: Shielding & Structure ---
widgets["mfe_group3_header"] = Div(
    text=_card_hdr("Shielding & Structure", "Shields, structural support, maintenance gap"),
    visible=_mfe_vis,
)
widgets["expert_ht_shield_t"] = Slider(title="High-Temp Shield (m)", start=0.1, end=0.5, value=config.get("expert_ht_shield_t", 0.2), step=0.05, visible=_mfe_vis)
widgets["expert_structure_t"] = Slider(title="Structure (m)", start=0.1, end=0.5, value=config.get("expert_structure_t", 0.2), step=0.05, visible=_mfe_vis)
widgets["expert_gap_t"] = Slider(title="Maintenance Gap (m)", start=0.2, end=1.0, value=config.get("expert_gap_t", 0.5), step=0.05, visible=_mfe_vis)
_g3_sum = sum(config.get(k, d) for k, d in [("expert_ht_shield_t",0.2),("expert_structure_t",0.2),("expert_gap_t",0.5)])
widgets["mfe_group3_subtotal"] = Div(
    text=f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>Shielding: {_g3_sum:.2f} m</div>",
    visible=_mfe_vis,
)

# --- Group 4: Outer Shell ---
widgets["mfe_group4_header"] = Div(
    text=_card_hdr("Outer Shell", "Vessel, coil, and biological shield"),
    visible=_mfe_vis,
)
widgets["expert_vessel_t"] = Slider(title="Vacuum Vessel (m)", start=0.05, end=0.5, value=config.get("expert_vessel_t", 0.2), step=0.05, visible=_mfe_vis)
widgets["expert_gap2_t"] = Slider(title="Secondary Gap (m)", start=0.2, end=1.0, value=config.get("expert_gap2_t", 0.5), step=0.05, visible=_mfe_vis)
widgets["expert_lt_shield_t"] = Slider(title="Low-Temp Shield (m)", start=0.2, end=0.5, value=config.get("expert_lt_shield_t", 0.3), step=0.05, visible=_mfe_vis)
widgets["expert_coil_t"] = Slider(title="TF Coil (m)", start=0.5, end=2.0, value=config.get("expert_coil_t", 1.0), step=0.1, visible=_mfe_vis)
widgets["expert_bio_shield_t"] = Slider(title="Biological Shield (m)", start=0.5, end=2.0, value=config.get("expert_bio_shield_t", 1.0), step=0.1, visible=_mfe_vis)
_g4_sum = sum(config.get(k, d) for k, d in [("expert_vessel_t",0.2),("expert_gap2_t",0.5),("expert_lt_shield_t",0.3),("expert_coil_t",1.0),("expert_bio_shield_t",1.0)])
widgets["mfe_group4_subtotal"] = Div(
    text=f"<div style='font-size:11px; color:#6b7280; text-align:right; margin:-4px 0 8px 0;'>Outer: {_g4_sum:.2f} m</div>",
    visible=_mfe_vis,
)

# Total radius KPI
_total_r = config.get("expert_major_radius_m", 3) + config.get("expert_plasma_t", 1.1) + _g2_sum + _g3_sum + _g4_sum
widgets["total_radius_display"] = Div(
    text=f"""<div style='display:flex; justify-content:space-between; align-items:center; padding:12px 20px;
                font-family:Inter,Helvetica,Arial,sans-serif;'>
        <span style='font-size:14px; font-weight:700; color:#00375b;'>Total Machine Radius</span>
        <span style='font-size:20px; font-weight:800; color:#00375b;'>{_total_r:.2f} m</span>
    </div>""",
    styles={"background": "#e0f2fe", "border-radius": "12px", "border": "1px solid #bae6fd", "margin-top": "4px"},
    visible=_mfe_vis,
)

# --- IFE Geometry Section ---
_ife_vis = config.get("reactor_type", "MFE Tokamak") != "MFE Tokamak" and config.get("use_expert_geometry", False)
widgets["ife_geometry_header"] = Div(
    text="<div style='font-size:16px; font-weight:700; color:#00375b; margin:8px 0 4px 0; font-family:Inter,Helvetica,Arial,sans-serif;'>IFE Spherical Chamber Build</div>",
    visible=_ife_vis,
)

widgets["ife_group_header"] = Div(
    text=_card_hdr("Chamber Components", "Inner chamber through vessel wall"),
    visible=_ife_vis,
)
widgets["expert_chamber_radius_m"] = Slider(title="Inner Chamber Radius (m)", start=5, end=15, value=config.get("expert_chamber_radius_m", 8), step=0.5, visible=_ife_vis)
widgets["expert_firstwall_t_ife"] = Slider(title="First Wall (m)", start=0.002, end=0.01, value=config.get("expert_firstwall_t_ife", 0.005), step=0.001, visible=_ife_vis)
widgets["expert_blanket_t_ife"] = Slider(title="Blanket (m)", start=0.3, end=1.0, value=config.get("expert_blanket_t_ife", 0.5), step=0.05, visible=_ife_vis)
widgets["expert_reflector_t_ife"] = Slider(title="Reflector (m)", start=0.05, end=0.2, value=config.get("expert_reflector_t_ife", 0.1), step=0.01, visible=_ife_vis)
widgets["expert_structure_t_ife"] = Slider(title="Structure (m)", start=0.1, end=0.3, value=config.get("expert_structure_t_ife", 0.2), step=0.05, visible=_ife_vis)
widgets["expert_vessel_t_ife"] = Slider(title="Vessel (m)", start=0.1, end=0.3, value=config.get("expert_vessel_t_ife", 0.2), step=0.05, visible=_ife_vis)

_ife_outer = sum(config.get(k, d) for k, d in [("expert_chamber_radius_m",8),("expert_firstwall_t_ife",0.005),("expert_blanket_t_ife",0.5),("expert_reflector_t_ife",0.1),("expert_structure_t_ife",0.2),("expert_vessel_t_ife",0.2)])
widgets["outer_radius_display"] = Div(
    text=f"""<div style='display:flex; justify-content:space-between; align-items:center; padding:12px 20px;
                font-family:Inter,Helvetica,Arial,sans-serif;'>
        <span style='font-size:14px; font-weight:700; color:#00375b;'>Outer Vessel Radius</span>
        <span style='font-size:20px; font-weight:800; color:#00375b;'>{_ife_outer:.2f} m</span>
    </div>""",
    styles={"background": "#e0f2fe", "border-radius": "12px", "border": "1px solid #bae6fd", "margin-top": "4px"},
    visible=_ife_vis,
)

# Create Expert Config column layout
expert_col = column(
    widgets["expert_header"],
    widgets["use_expert_geometry"],
    widgets["geometry_mode_info"],
    # MFE Geometry — grouped cards
    widgets["mfe_geometry_header"],
    widgets["mfe_group1_header"],
    widgets["expert_major_radius_m"],
    widgets["expert_plasma_t"],
    widgets["expert_elongation"],
    widgets["mfe_group1_subtotal"],
    widgets["mfe_group2_header"],
    widgets["expert_vacuum_t"],
    widgets["expert_firstwall_t"],
    widgets["expert_blanket_t"],
    widgets["expert_reflector_t"],
    widgets["mfe_group2_subtotal"],
    widgets["mfe_group3_header"],
    widgets["expert_ht_shield_t"],
    widgets["expert_structure_t"],
    widgets["expert_gap_t"],
    widgets["mfe_group3_subtotal"],
    widgets["mfe_group4_header"],
    widgets["expert_vessel_t"],
    widgets["expert_gap2_t"],
    widgets["expert_lt_shield_t"],
    widgets["expert_coil_t"],
    widgets["expert_bio_shield_t"],
    widgets["mfe_group4_subtotal"],
    widgets["total_radius_display"],
    # IFE Geometry
    widgets["ife_geometry_header"],
    widgets["ife_group_header"],
    widgets["expert_chamber_radius_m"],
    widgets["expert_firstwall_t_ife"],
    widgets["expert_blanket_t_ife"],
    widgets["expert_reflector_t_ife"],
    widgets["expert_structure_t_ife"],
    widgets["expert_vessel_t_ife"],
    widgets["outer_radius_display"],
    styles={'background': '#ffffff', 'border-radius': '16px', 'padding': '24px',
            'max-width': '92%',
            'font-family': 'Inter, Helvetica, Arial, sans-serif'},
)

# Create Expert Config Tab
expert_tab = TabPanel(child=expert_col, title="Expert Config")

# Attach expert geometry callback AFTER widget is created
widgets["use_expert_geometry"].on_change("active", toggle_expert_geometry_visibility)

# --- Tabs Layout ---



# Set initial highlight facts
highlight_div.text = render_highlight_facts(outputs)
dscr_metrics_div.text = render_dscr_metrics(outputs)
equity_metrics_div.text = render_equity_metrics(outputs)
get_avg_annual_return("Europe")
tabs = Tabs(tabs=[main_tab, sens_tab, costing_tab, expert_tab])

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
    # Clear any existing roots to prevent duplicate dashboards on reload
    doc = curdoc()
    doc.clear()
    
    outer_container = row(styled_sidebar, styled_tabs)
    
    doc.add_root(outer_container)
    doc.title = "Fusion Cashflow Dashboard"
    
    # Add favicon to the document
    doc.template_variables["favicon"] = "assets/favicon.ico?v=20250807"
    
    print("Dashboard layout created, starting initial update...")
    update_dashboard()
    print("Initial dashboard update completed")
    
    # Add periodic callback to check for optimization results (runs every 500ms)
    doc.add_periodic_callback(check_optimization_results, 500)
    
    print("Dashboard module imported successfully")
    
except Exception as e:
    import traceback
    print(f"CRITICAL ERROR during dashboard initialization: {e}")
    traceback.print_exc()
    raise
