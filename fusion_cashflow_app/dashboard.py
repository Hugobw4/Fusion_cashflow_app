import holoviews as hv

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
)

# --- Highlight Facts & Figures ---
# This Div will be updated with key metrics (LCOE, IRR, NPV, Payback, etc.)
highlight_div = Div(
    text="",
    width=900,
    styles={
        "background": "#f8f8fa",
        "border-radius": "16px",
        "padding": "18px 24px 12px 24px",
        "margin-bottom": "18px",
        "font-size": "18px",
        "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
        "border": "1px solid #e0e0e0",
        "color": "#222",
        "font-family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
    },
)


def render_highlight_facts(outputs):
    # Extract key metrics from outputs, fallback to 'N/A' if not present
    lcoe = outputs.get("lcoe_val", "N/A")
    irr = outputs.get("irr", "N/A")
    npv = outputs.get("npv", "N/A")
    payback = outputs.get("payback", "N/A")

    # Format values if numeric
    def fmt(val, style):
        if isinstance(val, (int, float)):
            if style == "pct":
                return f"{val*100:.2f}%"
            elif style == "usd":
                return f"${val:,.0f}"
            elif style == "usd0":
                return f"${val:,.2f}"
            else:
                return str(val)
        return val

    html = f"""
    <b>LCOE per MWh:</b> <span style='color:#007aff;font-weight:600'>{fmt(lcoe, 'usd0')}</span> &nbsp; &nbsp;
    <b>Project IRR:</b> <span style='color:#007aff;font-weight:600'>{fmt(irr, 'pct')}</span> &nbsp; &nbsp;
    <b>NPV:</b> <span style='color:#007aff;font-weight:600'>{fmt(npv, 'usd')}</span> &nbsp; &nbsp;
    <b>Payback:</b> <span style='color:#007aff;font-weight:600'>{'∞' if payback is None else payback if payback=='N/A' else int(payback)} years</span>
    """
    return html


import holoviews as hv

hv.extension("bokeh")
from bokeh.models import (
    Div,
)
from fusion_cashflow_app.cashflow_engine import (
    get_default_config,
    get_default_config_by_power_method,
    run_cashflow_scenario,
    run_sensitivity_analysis,
    get_avg_annual_return,
)
from fusion_cashflow_app.visuals.bokeh_plots import (
    plot_annual_cashflow_bokeh,
    plot_cumulative_cashflow_bokeh,
    plot_dscr_profile_bokeh,
    plot_cashflow_waterfall_bokeh,
    plot_sensitivity_heatmap,
)
import pandas as pd
from bokeh.events import ButtonClick

# --- Styling ---
APPLE_CSS = """
<style>
.bk-root .bk-btn, .bk-root .bk-input, .bk-root .bk-slider, .bk-root .bk-select {
    border-radius: 12px !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 15px;
    background: #f8f8fa;
    color: #222;
    border: 1px solid #e0e0e0;
    box-shadow: none;
}
.bk-root .bk-btn-primary {
    background: #007aff !important;
    color: #fff !important;
    border: none !important;
}
.bk-root .bk-panel {
    border-radius: 18px;
    background: #fff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #eee;
}
.bk-root .bk-data-table {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #eee;
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
        start=1990,
        end=2050,
        value=config["construction_start_year"],
        step=1,
    )
    widgets["project_energy_start_year"] = Slider(
        title="Energy Start Year",
        start=1990,
        end=2100,
        value=config["project_energy_start_year"],
        step=1,
    )
    # Add a read-only Div to show years_construction
    years_construction_val = config["project_energy_start_year"] - config["construction_start_year"]
    widgets["years_construction_display"] = Div(
        text=f"<div style='margin-bottom:10px; color:#007aff; font-size:16px;'><b>Construction Duration (years):</b> {years_construction_val}</div>",
        width=300,
    )
    widgets["plant_lifetime"] = Slider(
        title="Plant Lifetime (years)",
        start=5,
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
        title="Debt %", start=0.0, end=1.0, value=config["input_debt_pct"], step=0.01
    )
    widgets["cost_of_debt"] = Slider(
        title="Cost of Debt",
        start=0.0,
        end=0.2,
        value=config["cost_of_debt"],
        step=0.001,
    )
    widgets["loan_rate"] = Slider(
        title="Loan Rate", start=0.0, end=0.2, value=config["loan_rate"], step=0.001
    )
    widgets["financing_fee"] = Slider(
        title="Financing Fee",
        start=0.0,
        end=0.1,
        value=config["financing_fee"],
        step=0.001,
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
    widgets["total_epc_cost"] = Slider(
        title="Total EPC Cost ($)",
        start=1e9,
        end=5e10,
        value=config["total_epc_cost"],
        step=1e8,
        format="0,0",
    )
    widgets["extra_capex_pct"] = Slider(
        title="Extra CapEx %",
        start=0.0,
        end=0.5,
        value=config["extra_capex_pct"],
        step=0.01,
    )
    widgets["project_contingency_pct"] = Slider(
        title="Project Contingency %",
        start=0.0,
        end=0.5,
        value=config["project_contingency_pct"],
        step=0.01,
    )
    widgets["process_contingency_pct"] = Slider(
        title="Process Contingency %",
        start=0.0,
        end=0.5,
        value=config["process_contingency_pct"],
        step=0.01,
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
    return widgets


# --- Update logic ---
def get_config_from_widgets(widgets):
    config = {}
    for k, w in widgets.items():
        if isinstance(w, (Slider, TextInput, Select)):
            config[k] = w.value
        elif isinstance(w, Checkbox):
            config[k] = w.active
    return config


# --- Throttling/debouncing for widget updates ---

debounce_timer = None
DEBOUNCE_DELAY = 0.35  # seconds


def update_dashboard():
    config = get_config_from_widgets(widgets)
    outputs = run_cashflow_scenario(config)
    highlight_div.text = render_highlight_facts(outputs)
    annual_fig = plot_annual_cashflow_bokeh(outputs, config)
    cum_fig = plot_cumulative_cashflow_bokeh(outputs, config)
    dscr_fig = plot_dscr_profile_bokeh(outputs, config)
    funding_fig = plot_cashflow_waterfall_bokeh(outputs, config)
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
    # Replace plots in layout (main tab only)
    main_col.children = [
        highlight_div,
        annual_fig,
        annual_table,
        cum_fig,
        cum_table,
        dscr_fig,
        dscr_table,
        funding_fig,
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
        f"<div style='margin-bottom:10px; color:#007aff; font-size:16px;'><b>Construction Duration (years):</b> {years}</div>"
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
    from fusion_cashflow_app.cashflow_engine import get_default_config_by_power_method
    
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
    
    # Update years construction display
    years = widgets["project_energy_start_year"].value - widgets["construction_start_year"].value
    widgets["years_construction_display"].text = (
        f"<div style='margin-bottom:10px; color:#007aff; font-size:16px;'><b>Construction Duration (years):</b> {years}</div>"
    )
    
    # Update fuel type options based on new power method
    update_fuel_type_based_on_power_method(attr, old, new)

widgets["power_method"].on_change("value", update_fuel_type_based_on_power_method)
widgets["power_method"].on_change("value", update_config_based_on_power_method)

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
funding_fig = plot_cashflow_waterfall_bokeh(outputs, config)
# Sensitivity plot will be created on demand in its tab

# --- Tables ---
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
cum_columns = [
    TableColumn(field="Year", title="Year"),
    TableColumn(field="Cumulative Unlevered CF", title="Cumulative Unlevered CF", formatter=NumberFormatter(format="$0,0")),
    TableColumn(field="Cumulative Levered CF", title="Cumulative Levered CF", formatter=NumberFormatter(format="$0,0")),
]
cum_table = DataTable(source=cum_source, columns=cum_columns, width=600, height=220, index_position=None)
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

    def cb():
        csv = download_csv_callback(source, filename)
        button.js_on_click(None)  # Remove previous
        button.js_on_click(
            """
            var blob = new Blob([atob('%s')], {type: 'text/csv'});
            var link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = '%s';
            link.click();
        """
            % (csv.encode("utf-8").hex(), filename)
        )

    button.on_event(ButtonClick, lambda event: cb())
    return button


annual_download = make_download_button(annual_source, "Download Annual Table", "annual.csv")
cum_download = make_download_button(cum_source, "Download Cumulative Table", "cumulative.csv")
dscr_download = make_download_button(dscr_source, "Download DSCR Table", "dscr.csv")


# --- Layout ---
sidebar = column(
    Div(text=APPLE_CSS),
    Div(text="<h2 style='margin-bottom:8px;'>Fusion Cashflow App</h2><p style='color:#888;'>Adjust inputs and see results instantly.</p>"),
    *[w for w in widgets.values()],
    Spacer(height=16),
    annual_download,
    cum_download,
    dscr_download,
    sizing_mode="stretch_height",
)

# --- Main Results Tab ---
main_col = column(
    highlight_div,
    annual_fig,
    annual_table,
    cum_fig,
    cum_table,
    dscr_fig,
    dscr_table,
    funding_fig,
    sizing_mode="stretch_both",
)


# --- Main Results Tab ---

# Use TabPanel for Bokeh 3.x compatibility
from bokeh.models import TabPanel

main_tab = TabPanel(child=main_col, title="Main Results")

# --- Sensitivity Analysis Tab ---
from bokeh.models import Div
grey_container_style = {
    "background": "#f5f6fa",
    "border-radius": "12px",
    "padding": "24px 16px 24px 16px",
    "margin": "16px 0 16px 0",
    "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
    "overflow-x": "auto",
    "width": "100%"
}
# Create a container for the plot
sens_fig = placeholder_fig
sens_plot_container = column(sens_fig, sizing_mode="stretch_width", styles=grey_container_style)
sens_col = column(
    Div(
        text="<h3>Sensitivity Analysis</h3><p>Click the button to recompute sensitivity analysis with current inputs.</p>"
    ),
    Button(
        label="Run Sensitivity Analysis",
        button_type="primary",
        width=220,
        name="run_sens_btn",
    ),
    sens_plot_container,
    sizing_mode="stretch_both",
)
sens_tab = TabPanel(child=sens_col, title="Sensitivity Analysis")


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


# Find the button in sens_col and attach callback
for child in sens_col.children:
    if isinstance(child, Button) and getattr(child, "name", None) == "run_sens_btn":
        child.on_click(run_sensitivity_callback)
        break

# --- Tabs Layout ---



# Set initial highlight facts
highlight_div.text = render_highlight_facts(outputs)
get_avg_annual_return("Europe")
tabs = Tabs(tabs=[main_tab, sens_tab], sizing_mode="stretch_both")



# --- Modern container styles ---
outer_container_style = {
    "background": "#f5f6fa",
    "border-radius": "24px",
    "box-shadow": "0 4px 24px rgba(0,0,0,0.06)",
    "border": "1px solid #e0e0e0",
    "padding": "32px 0 32px 0",
    "margin": "32px auto",
    "display": "flex",
    "justify-content": "center",
    "align-items": "flex-start",
    "width": "100%",
    # Remove max-width to allow full width
}
main_col_style = {
    "background": "#fff",
    "border-radius": "18px",
    "box-shadow": "0 2px 12px rgba(0,0,0,0.07)",
    "border": "1px solid #e0e0e0",
    "padding": "32px 32px 32px 32px",
    "margin": "0 0 0 0",
    "width": "100%",
}
sidebar_style = {
    "background": "#f8f8fa",
    "border-radius": "18px",
    "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
    "border": "1px solid #e0e0e0",
    "padding": "24px 18px 24px 18px",
    "margin": "0 24px 0 0",
}




# --- Wrap sidebar in styled container, use tabs directly ---
styled_sidebar = column(sidebar, width=360, sizing_mode="stretch_height", styles=sidebar_style)
# For main results, make sure the main_col stretches full width
main_col.sizing_mode = "stretch_width"
main_col.width = None
styled_tabs = tabs  # Do not wrap Tabs in a column

# --- Center everything in a wide, light-grey container ---
try:
    from bokeh.layouts import grid
    # Use a responsive grid: sidebar in first column, main content in second column
    outer_grid = grid([
        [styled_sidebar, styled_tabs]
    ], sizing_mode="stretch_both")
    from bokeh.models import Div
    outer = column(
        Div(styles=outer_container_style),
        outer_grid,
        sizing_mode="stretch_both"
    )

    curdoc().add_root(outer)
    curdoc().title = "Fusion Cashflow Dashboard"
    update_dashboard()
except Exception as e:
    import traceback
    traceback.print_exc()


# --- Make all plots/tables fill width ---
for fig in [annual_fig, cum_fig, dscr_fig, funding_fig]:
    if hasattr(fig, 'sizing_mode'):
        fig.sizing_mode = "stretch_width"
        fig.width = None
for tbl in [annual_table, cum_table, dscr_table]:
    if hasattr(tbl, 'sizing_mode'):
        tbl.sizing_mode = "stretch_width"
        tbl.width = None
