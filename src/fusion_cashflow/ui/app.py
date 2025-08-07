import holoviews as hv

hv.extension("bokeh")
from fusion_cashflow.core.cashflow_engine import (
    get_default_config,
    run_cashflow_scenario,
    run_sensitivity_analysis,
)
from fusion_cashflow.visualization.bokeh_plots import (
    plot_annual_cashflow_bokeh,
    plot_cumulative_cashflow_bokeh,
    plot_dscr_profile_bokeh,
    plot_cashflow_waterfall_bokeh,
    plot_sensitivity_heatmap,
)
from fusion_cashflow.reporting.report_builder import save_bokeh_report
from bokeh.models import DataTable, TableColumn, NumberFormatter, ColumnDataSource
import pandas as pd
from bokeh.models import Div
from bokeh.themes import Theme
from bokeh.models import GlobalInlineStyleSheet, GlobalImportedStyleSheet
from bokeh.io import curdoc
import os

# --- Apply Fusion Fintech Theme ---
theme_path = os.path.join(os.path.dirname(__file__), "themes", "fusion_theme.yaml")
if os.path.exists(theme_path):
    curdoc().theme = Theme(filename=theme_path)
else:
    print(f"Warning: Theme file not found at {theme_path}")
    
# Note: template_stylesheets may not be available in all Bokeh versions
try:
    curdoc().template_stylesheets.append(
        GlobalImportedStyleSheet(
            url="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap"
        )
    )
except AttributeError:
    # Fallback for older Bokeh versions
    pass
fintech_css = GlobalInlineStyleSheet(
    css="""
:host, body {background:#F8FAFC;font-family:'Inter',sans-serif;color:#0F172A;}
.bk, .bk-input, .bk-btn {border-radius:8px!important;box-shadow:0 2px 6px #0001;}
.bk-btn-primary{background:#1E3A8A;color:#fff;border:none;}
.bk-btn-primary:hover{background:#0891B2;}
.noUi-target{background:#E5E7EB;border-radius:6px;}
.noUi-connect{background:#1E3A8A;}
.noUi-handle{border:3px solid #0891B2;border-radius:50%;}
.bk-tab{padding:8px 16px;border-radius:8px 8px 0 0;}
.bk-tab.bk-active{background:#1E3A8A;color:#fff;}
"""
)
# Apply stylesheet if available
try:
    curdoc().template_stylesheets.append(fintech_css)
except AttributeError:
    pass


def main():
    config = get_default_config()
    outputs = run_cashflow_scenario(config)
    sensitivity_df = run_sensitivity_analysis(config)

    # Generate all plots
    figs = []
    # 1. Annual Cash Flow
    figs.append(plot_annual_cashflow_bokeh(outputs, config))
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
    annual_columns = [
        TableColumn(field="Year", title="Year"),
        TableColumn(
            field="Unlevered CF",
            title="Unlevered CF",
            formatter=NumberFormatter(format="$0,0"),
        ),
        TableColumn(
            field="Levered CF",
            title="Levered CF",
            formatter=NumberFormatter(format="$0,0"),
        ),
        TableColumn(
            field="Revenue", title="Revenue", formatter=NumberFormatter(format="$0,0")
        ),
        TableColumn(field="O&M", title="O&M", formatter=NumberFormatter(format="$0,0")),
        TableColumn(
            field="Fuel", title="Fuel", formatter=NumberFormatter(format="$0,0")
        ),
        TableColumn(field="Tax", title="Tax", formatter=NumberFormatter(format="$0,0")),
        TableColumn(field="NOI", title="NOI", formatter=NumberFormatter(format="$0,0")),
    ]
    annual_table = DataTable(
        source=annual_source,
        columns=annual_columns,
        width=900,
        height=220,
        index_position=None,
    )
    figs.append(annual_table)
    # 2. Cumulative Cash Flow
    figs.append(plot_cumulative_cashflow_bokeh(outputs, config))
    cum_df = pd.DataFrame(
        {
            "Year": outputs["year_labels_int"],
            "Cumulative Unlevered CF": outputs["cumulative_unlevered_cf_vec"],
            "Cumulative Levered CF": outputs["cumulative_levered_cf_vec"],
        }
    )
    cum_source = ColumnDataSource(cum_df)
    cum_columns = [
        TableColumn(field="Year", title="Year"),
        TableColumn(
            field="Cumulative Unlevered CF",
            title="Cumulative Unlevered CF",
            formatter=NumberFormatter(format="$0,0"),
        ),
        TableColumn(
            field="Cumulative Levered CF",
            title="Cumulative Levered CF",
            formatter=NumberFormatter(format="$0,0"),
        ),
    ]
    cum_table = DataTable(
        source=cum_source,
        columns=cum_columns,
        width=600,
        height=220,
        index_position=None,
    )
    figs.append(cum_table)
    # 3. DSCR Profile
    figs.append(plot_dscr_profile_bokeh(outputs, config))
    dscr_df = pd.DataFrame(
        {
            "Year": outputs["year_labels_int"],
            "DSCR": outputs["dscr_vec"],
            "NOI": outputs["noi_vec"],
            "Debt Service": [
                a + b
                for a, b in zip(
                    outputs["principal_paid_vec"], outputs["interest_paid_vec"]
                )
            ],
        }
    )
    dscr_source = ColumnDataSource(dscr_df)
    dscr_columns = [
        TableColumn(field="Year", title="Year"),
        TableColumn(
            field="DSCR", title="DSCR", formatter=NumberFormatter(format="0.00")
        ),
        TableColumn(field="NOI", title="NOI", formatter=NumberFormatter(format="$0,0")),
        TableColumn(
            field="Debt Service",
            title="Debt Service",
            formatter=NumberFormatter(format="$0,0"),
        ),
    ]
    dscr_table = DataTable(
        source=dscr_source,
        columns=dscr_columns,
        width=600,
        height=220,
        index_position=None,
    )
    figs.append(dscr_table)
    # 4. Funding & Uses
    figs.append(plot_cashflow_waterfall_bokeh(outputs, config))
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
    funding_columns = [
        TableColumn(field="Label", title="Label"),
        TableColumn(
            field="Amount", title="Amount", formatter=NumberFormatter(format="$0,0")
        ),
    ]
    funding_table = DataTable(
        source=funding_source,
        columns=funding_columns,
        width=400,
        height=220,
        index_position=None,
    )
    figs.append(funding_table)
    # 5. Sensitivity Heatmap
    figs.append(plot_sensitivity_heatmap(outputs, config, sensitivity_df))
    sensitivity_table_source = ColumnDataSource(sensitivity_df)
    sensitivity_columns = [
        TableColumn(field="Driver", title="Driver"),
        TableColumn(field="Band", title="Band"),
        TableColumn(field="NPV", title="NPV", formatter=NumberFormatter(format="$0,0")),
        TableColumn(
            field="IRR", title="IRR", formatter=NumberFormatter(format="0.000%")
        ),
        TableColumn(
            field="Equity NPV",
            title="Equity NPV",
            formatter=NumberFormatter(format="$0,0"),
        ),
        TableColumn(
            field="Equity IRR",
            title="Equity IRR",
            formatter=NumberFormatter(format="0.000%"),
        ),
        TableColumn(
            field="LCOE", title="LCOE", formatter=NumberFormatter(format="$0,0")
        ),
        TableColumn(
            field="ΔNPV", title="ΔNPV", formatter=NumberFormatter(format="$0,0")
        ),
        TableColumn(
            field="ΔIRR", title="ΔIRR", formatter=NumberFormatter(format="0.000%")
        ),
    ]
    sensitivity_table = DataTable(
        source=sensitivity_table_source,
        columns=sensitivity_columns,
        width=1000,
        height=350,
        index_position=None,
    )
    figs.append(sensitivity_table)
    # Export sensitivity_df to CSV
    csv_filename = "sensitivity_analysis.csv"
    sensitivity_df.to_csv(csv_filename, index=False)
    csv_download_div = Div(
        text=f'<a href="{csv_filename}" download style="font-size:14px;">Download full sensitivity analysis as CSV</a>'
    )
    figs.append(csv_download_div)
    # Prepare summary metrics (as dict or DataFrame)
    metrics = {
        "Project NPV": outputs["npv"],
        "Project IRR": outputs["irr"],
        "Equity NPV": outputs["equity_npv"],
        "Equity IRR": outputs["equity_irr"],
        "Payback Year": outputs["payback"],
        "LCOE": outputs["lcoe_val"],
        "Equity Multiple": outputs["equity_mult"],
    }
    # Use new premium Sankey
    project_name = config.get("project_name", "Fusion Project")
    scenario_name = config.get("scenario_name", "Base Case")
    save_bokeh_report(
        figs,
        metrics,
        filename="whole_life_cashflow_report.html",
        project_name=project_name,
        scenario_name=scenario_name,
    )


# --- Outermost layout as card ---
# Replace/add this at the end where you add the layout to curdoc:
# root = row(sidebar, tabs, styles=Styles(
#     gap="24px", padding="24px", background="#FFFFFF",
#     border_radius="12px", box_shadow="0 6px 24px #0002"))
# curdoc().add_root(root)

# --- Import and Setup Dashboard ---
# Import the dashboard layout from dashboard.py
try:
    import dashboard
    print("Dashboard module imported successfully")
except ImportError as e:
    print(f"Error importing dashboard: {e}")
    # Create a simple error message if dashboard import fails
    from bokeh.models import Div
    error_div = Div(text=f"<h1>Error Loading Dashboard</h1><p>Import error: {e}</p>")
    curdoc().add_root(error_div)

if __name__ == "__main__":
    main()
