"""
Detailed costing panel showing ARPA-E CAS cost hierarchy.

Layout:
- KPI banner with CATF benchmark bands
- Top reduction levers card for decision support
- Waterfall chart showing cost buildup from CAS 10 → Total
- Summary table with inline bars and CAS 21/22 sub-rows
"""

import numpy as np
from bokeh.models import (
    ColumnDataSource,
    Div,
    Column as BokehColumn,
    HoverTool,
)
from bokeh.plotting import figure


# =============================
# ARPA-E CAS Category Definitions
# =============================

CAS_CATEGORIES = [
    {"cas": "10", "key": "cas_10_preconstruction", "name": "Pre-Construction Costs", "group": "preconstruction"},
    {"cas": "21", "key": "cas_21_total", "name": "Buildings & Site", "group": "direct",
     "children": [
         {"cas": "21.01", "key": "building_reactor_building", "name": "Reactor Building"},
         {"cas": "21.02", "key": "building_turbine_building", "name": "Turbine Building"},
         {"cas": "21.03", "key": "building_auxiliary_buildings", "name": "Auxiliary Buildings"},
     ]},
    {"cas": "22", "key": "cas_22_total", "name": "Reactor Plant Equipment", "group": "direct",
     "children": [
         {"cas": "22.01", "key": "cas_2201", "name": "First Wall / Blanket / Shield"},
         {"cas": "22.02", "key": "cas_2202", "name": "Heat Transfer & Transport"},
         {"cas": "22.03", "key": "cas_2203", "name": "Magnets"},
         {"cas": "22.04", "key": "cas_2204", "name": "Heating / Current Drive"},
         {"cas": "22.05", "key": "cas_2205", "name": "Vacuum Systems"},
         {"cas": "22.06", "key": "cas_2206", "name": "Power Core Structure"},
         {"cas": "22.07", "key": "cas_2207", "name": "Power Supplies"},
     ]},
    {"cas": "23", "key": "cas_23_turbine", "name": "Turbine Plant Equipment", "group": "direct"},
    {"cas": "24", "key": "cas_24_electrical", "name": "Electrical Equipment", "group": "direct"},
    {"cas": "25", "key": "cas_25_misc", "name": "Misc. Plant Equipment", "group": "direct"},
    {"cas": "26", "key": "cas_26_cooling", "name": "Heat Rejection", "group": "direct"},
    {"cas": "27", "key": "cas_27_materials", "name": "Special Materials", "group": "direct"},
    {"cas": "28", "key": "cas_28_instrumentation", "name": "Instrumentation & Control", "group": "direct"},
    {"cas": "29", "key": "cas_29_contingency", "name": "Contingency", "group": "contingency"},
    {"cas": "30", "key": "cas_30_indirect", "name": "Indirect Costs", "group": "indirect"},
    {"cas": "40", "key": "cas_40_owner_costs", "name": "Owner's Costs", "group": "indirect"},
]

GROUP_COLORS = {
    "preconstruction": "#8B5CF6",
    "direct": "#60A5FA",
    "contingency": "#F59E0B",
    "indirect": "#A78BFA",
    "total": "#10B981",
}


def create_costing_panel(epc_results, config=None):
    """
    Create costing panel with waterfall chart and summary table.

    Args:
        epc_results: Dictionary from power_to_epc.compute_epc()
        config: Configuration dictionary with project parameters

    Returns:
        bokeh.models.Column: Panel layout
    """
    total_epc = epc_results.get("total_epc", 0)
    cost_per_kw = epc_results.get("epc_per_kw", 0)
    detailed = epc_results.get("detailed_result", {})

    power_balance = epc_results.get("power_balance", {})
    net_mw = power_balance.get("p_net", 0) or power_balance.get("PNET", 0)
    gross_mw = power_balance.get("p_electric_gross", 0) or power_balance.get("PET", 0)
    tech = config.get("power_method", "MFE") if config else "MFE"

    categories = _extract_categories(detailed, total_epc, net_mw)
    benchmark_info = _get_benchmark_bands(net_mw, cost_per_kw, tech)

    kpi_banner = _create_kpi_banner(total_epc, cost_per_kw, net_mw, gross_mw, benchmark_info)
    waterfall = _create_waterfall_chart(categories, total_epc)
    summary_table = _create_summary_table(categories, total_epc, net_mw)

    content_column = BokehColumn(
        kpi_banner,
        waterfall,
        summary_table,
        sizing_mode="stretch_width",
        styles={
            "padding": "20px 40px",
            "max-width": "92%",
            "margin": "0 auto",
            "background": "#ffffff",
            "border-radius": "16px",
            "color": "#111111",
        },
    )
    return content_column


# =============================
# Data Extraction
# =============================

def _extract_categories(detailed, total_epc, net_mw):
    """Extract ordered cost categories from detailed_result dict."""
    cats = []
    for defn in CAS_CATEGORIES:
        cost = detailed.get(defn["key"], 0)
        if cost <= 0:
            continue
        pct = (cost / total_epc * 100) if total_epc > 0 else 0
        per_kw = (cost / (net_mw * 1000)) if net_mw > 0 else 0

        children = []
        for child_defn in defn.get("children", []):
            child_cost = detailed.get(child_defn["key"], 0)
            if child_cost > 0:
                children.append({
                    "cas": child_defn["cas"],
                    "name": child_defn["name"],
                    "cost": child_cost,
                    "pct": (child_cost / total_epc * 100) if total_epc > 0 else 0,
                    "per_kw": (child_cost / (net_mw * 1000)) if net_mw > 0 else 0,
                })

        cats.append({
            "cas": defn["cas"],
            "name": defn["name"],
            "group": defn["group"],
            "cost": cost,
            "pct": pct,
            "per_kw": per_kw,
            "children": children,
        })
    return cats


# =============================
# KPI Banner
# =============================

def _create_kpi_banner(total_epc, cost_per_kw, net_mw, gross_mw, benchmark_info):
    """Single-line KPI banner matching main dashboard style."""
    # CSS tooltip approach — Bokeh shadow DOM blocks native title attributes,
    # so we use a hover-visible child div for each tooltip.
    tooltip_css = """
    <style>
      .kpi-item { position:relative; display:inline-block; margin-right:28px; }
      .kpi-item .kpi-tip {
        visibility:hidden; opacity:0; transition:opacity 0.2s;
        position:absolute; bottom:110%; left:50%; transform:translateX(-50%);
        background:#001e3c; color:#ffffff; font-size:11px; font-weight:400;
        padding:6px 10px; border-radius:6px; white-space:nowrap;
        box-shadow:0 2px 8px rgba(0,0,0,0.3); z-index:10;
        pointer-events:none;
      }
      .kpi-item:hover .kpi-tip { visibility:visible; opacity:1; }
      .kpi-label {
        cursor:help; background:rgba(160,196,255,0.15); padding:2px 6px;
        border-radius:4px; transition:background 0.2s;
      }
      .kpi-item:hover .kpi-label { background:rgba(160,196,255,0.3); }
    </style>
    """

    html = f"""
    {tooltip_css}
    <div style='display:flex; align-items:center; flex-wrap:wrap; gap:6px 20px;
                font-size:15px; font-weight:800; padding:0 8px;'>
        <div class='kpi-item'>
            <span class='kpi-label'><b>Total<sup>?</sup>:</b></span>
            <span style='color:#ffffff; font-weight:800'> ${total_epc/1e9:.2f}B</span>
            <div class='kpi-tip'>Engineering, Procurement &amp; Construction — total capital cost</div>
        </div>
        <div class='kpi-item'>
            <span class='kpi-label'><b>Per kW<sup>?</sup>:</b></span>
            <span style='color:#ffffff; font-weight:800'> ${cost_per_kw:,.0f}</span>
            <div class='kpi-tip'>EPC cost &divide; net electric capacity ($/kW)</div>
        </div>
        <div class='kpi-item'>
            <span class='kpi-label'><b>Net<sup>?</sup>:</b></span>
            <span style='color:#ffffff; font-weight:800'> {net_mw:.0f}&thinsp;MW</span>
            <div class='kpi-tip'>Net electric power delivered to the grid</div>
        </div>
        <div class='kpi-item'>
            <span class='kpi-label'><b>Gross<sup>?</sup>:</b></span>
            <span style='color:#ffffff; font-weight:800'> {gross_mw:.0f}&thinsp;MW</span>
            <div class='kpi-tip'>Gross generation before plant auxiliary loads</div>
        </div>
        <div class='kpi-item' style='margin-right:0;'>
            <span class='kpi-label'><b>CATF<sup>?</sup>:</b></span>
            <span style='color:#60A5FA; font-weight:800'> {benchmark_info["current_position"]}</span>
            <div class='kpi-tip'>Position in CATF cost benchmark distribution</div>
        </div>
    </div>
    """
    return Div(
        text=html,
        sizing_mode="stretch_width",
        styles={
            "background": "#00375b",
            "border-radius": "16px",
            "padding": "18px 24px 14px 24px",
            "margin-bottom": "18px",
            "box-shadow": "0 2px 8px rgba(0,0,0,0.15)",
            "border": "1px solid rgba(255,255,255,0.1)",
            "color": "#ffffff",
            "font-family": "Inter, Helvetica, Arial, sans-serif",
            "overflow": "visible",
            "min-height": "50px",
        },
    )



# =============================
# Waterfall Chart
# =============================

def _create_waterfall_chart(categories, total_epc):
    """Vertical waterfall chart showing cost buildup from CAS 10 → Total."""

    labels = []
    costs_b = []
    groups = []
    for cat in categories:
        labels.append(f"CAS {cat['cas']}")
        costs_b.append(cat["cost"] / 1e9)
        groups.append(cat["group"])

    # Add total bar
    labels.append("Total")
    costs_b.append(total_epc / 1e9)
    groups.append("total")

    # Compute waterfall positions
    bottoms = []
    tops = []
    running = 0.0
    for i, cost in enumerate(costs_b):
        if groups[i] == "total":
            bottoms.append(0.0)
            tops.append(cost)
        else:
            bottoms.append(running)
            tops.append(running + cost)
            running += cost

    colors = [GROUP_COLORS.get(g, "#60A5FA") for g in groups]

    source = ColumnDataSource(data=dict(
        labels=labels,
        costs=costs_b,
        bottoms=bottoms,
        tops=tops,
        colors=colors,
        names=[c["name"] for c in categories] + ["Total EPC"],
        pcts=[f"{c['pct']:.1f}%" for c in categories] + ["100%"],
    ))

    p = figure(
        x_range=labels,
        height=420,
        sizing_mode="stretch_width",
        toolbar_location=None,
        title="",
    )

    # Bars
    p.vbar(
        x="labels",
        top="tops",
        bottom="bottoms",
        width=0.65,
        source=source,
        color="colors",
        alpha=0.88,
        line_color="rgba(0,55,91,0.15)",
        line_width=1,
    )

    # Connector lines between bars (except before Total)
    for i in range(len(labels) - 2):
        p.line(
            x=[labels[i], labels[i + 1]],
            y=[tops[i], tops[i]],
            line_color="rgba(0,55,91,0.25)",
            line_width=1,
            line_dash="dotted",
        )

    # White theme styling
    p.background_fill_color = "#ffffff"
    p.border_fill_color = "#ffffff"
    p.outline_line_color = None

    p.yaxis.axis_label = "Cost ($B)"
    p.yaxis.axis_label_text_font_style = "bold"
    p.yaxis.axis_label_text_color = "#00375b"
    p.yaxis.axis_label_text_font_size = "12pt"
    p.yaxis.major_label_text_color = "#374151"
    p.yaxis.axis_line_color = "rgba(0,55,91,0.2)"
    p.yaxis.major_tick_line_color = "rgba(0,55,91,0.2)"
    p.yaxis.minor_tick_line_color = None

    p.xaxis.major_label_text_color = "#00375b"
    p.xaxis.major_label_text_font_size = "9pt"
    p.xaxis.major_label_orientation = 0.7
    p.xaxis.axis_line_color = "rgba(0,55,91,0.2)"
    p.xaxis.major_tick_line_color = "rgba(0,55,91,0.2)"
    p.xaxis.minor_tick_line_color = None

    p.grid.grid_line_color = "rgba(0,55,91,0.06)"
    p.xgrid.grid_line_color = None

    hover = HoverTool(tooltips=[
        ("Category", "@names"),
        ("Cost", "$@costs{0.00}B"),
        ("Share", "@pcts"),
    ])
    p.add_tools(hover)

    title_div = Div(
        text="<h3 style='color:#1a1a1a; font-size:16px; font-weight:700; margin:20px 0 8px 0; "
             "font-family:Inter, Helvetica, Arial, sans-serif;'>EPC Cost Waterfall</h3>",
        sizing_mode="stretch_width",
    )

    return BokehColumn(title_div, p, sizing_mode="stretch_width")


# =============================
# Summary Table
# =============================

def _create_summary_table(categories, total_epc, net_mw):
    """HTML summary table with inline bars and CAS 21/22 sub-rows."""

    max_pct = max((c["pct"] for c in categories), default=1)

    def _bar(pct, color="#60A5FA"):
        width = max(2, pct / max_pct * 100)
        return (
            f"<div style='background:{color}; height:8px; border-radius:4px; "
            f"width:{width:.0f}%; min-width:2px;'></div>"
        )

    def _row(cas_label, name, cost, per_kw, pct, bar_html, indent=False):
        pad = "padding-left:28px;" if indent else ""
        name_style = (
            f"font-size:12px; color:#6b7280; {pad}"
            if indent
            else f"font-size:13px; color:#1a1a1a; font-weight:600; {pad}"
        )
        cost_str = f"${cost/1e9:.3f}B" if cost < 1e9 else f"${cost/1e9:.2f}B"
        return f"""
        <tr style="border-bottom:1px solid rgba(0,0,0,0.06);">
            <td style="padding:10px 12px; color:#6b7280; font-size:12px; white-space:nowrap;">{cas_label}</td>
            <td style="padding:10px 8px; {name_style}">{name}</td>
            <td style="padding:10px 8px; color:#1a1a1a; font-weight:600; text-align:right; white-space:nowrap;">{cost_str}</td>
            <td style="padding:10px 8px; color:#4b5563; text-align:right; white-space:nowrap;">${per_kw:,.0f}</td>
            <td style="padding:10px 8px; color:#2563EB; font-weight:600; text-align:right; white-space:nowrap;">{pct:.1f}%</td>
            <td style="padding:10px 12px; width:120px;">{bar_html}</td>
        </tr>
        """

    rows_html = ""
    for cat in categories:
        bar = _bar(cat["pct"], GROUP_COLORS.get(cat["group"], "#60A5FA"))
        rows_html += _row(
            f"CAS {cat['cas']}", cat["name"], cat["cost"], cat["per_kw"], cat["pct"], bar,
        )
        for child in cat.get("children", []):
            child_bar = _bar(child["pct"], "rgba(96,165,250,0.5)")
            rows_html += _row(
                f"&nbsp;&nbsp;{child['cas']}", child["name"],
                child["cost"], child["per_kw"], child["pct"], child_bar, indent=True,
            )

    # Total row
    total_per_kw = (total_epc / (net_mw * 1000)) if net_mw > 0 else 0
    total_str = f"${total_epc/1e9:.2f}B"
    rows_html += f"""
    <tr style="border-top:2px solid rgba(0,0,0,0.15);">
        <td style="padding:12px; color:#059669; font-weight:700;"></td>
        <td style="padding:12px 8px; color:#059669; font-weight:700; font-size:14px;">Total EPC</td>
        <td style="padding:12px 8px; color:#059669; font-weight:700; text-align:right; font-size:14px;">{total_str}</td>
        <td style="padding:12px 8px; color:#059669; font-weight:700; text-align:right;">${total_per_kw:,.0f}</td>
        <td style="padding:12px 8px; color:#059669; font-weight:700; text-align:right;">100%</td>
        <td style="padding:12px;"></td>
    </tr>
    """

    html = f"""
    <div style="margin-top:24px; font-family:Inter, Helvetica, Arial, sans-serif;">
        <h3 style="color:#1a1a1a; font-size:16px; font-weight:700; margin:0 0 12px 0;">
            CAS Cost Summary
        </h3>
        <div style="overflow-x:auto; border-radius:12px; border:1px solid rgba(0,0,0,0.08);
                    background:#fafafa;">
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead>
                    <tr style="border-bottom:2px solid rgba(0,0,0,0.1);">
                        <th style="padding:12px; text-align:left; color:#6b7280; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">CAS</th>
                        <th style="padding:12px 8px; text-align:left; color:#6b7280; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Category</th>
                        <th style="padding:12px 8px; text-align:right; color:#6b7280; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Cost</th>
                        <th style="padding:12px 8px; text-align:right; color:#6b7280; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">$/kW</th>
                        <th style="padding:12px 8px; text-align:right; color:#6b7280; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">Share</th>
                        <th style="padding:12px; color:#6b7280; font-weight:600; font-size:12px;"></th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """
    return Div(text=html, sizing_mode="stretch_width")


# =============================
# Benchmark Bands
# =============================

def _get_benchmark_bands(net_mw, cost_per_kw, tech):
    """CATF P10/P50/P90 benchmarks and current position."""
    try:
        from fusion_cashflow.core.power_to_epc import CATF_COST_DISTRIBUTION
        catf_p10 = CATF_COST_DISTRIBUTION["P10"]
        catf_p50 = CATF_COST_DISTRIBUTION["P50"]
        catf_p90 = CATF_COST_DISTRIBUTION["P90"]
    except (ImportError, KeyError, AttributeError):
        catf_p10, catf_p50, catf_p90 = 8500, 12500, 18000

    if cost_per_kw <= catf_p10:
        position = "Below P10 (optimistic)"
        percentile = 5
    elif cost_per_kw <= catf_p50:
        percentile = 10 + 40 * (cost_per_kw - catf_p10) / max(catf_p50 - catf_p10, 1)
        position = f"~P{int(percentile)} (competitive)"
    elif cost_per_kw <= catf_p90:
        percentile = 50 + 40 * (cost_per_kw - catf_p50) / max(catf_p90 - catf_p50, 1)
        position = f"~P{int(percentile)} (moderate)"
    else:
        position = "Above P90 (conservative)"
        percentile = 95

    return {
        "catf_p10": catf_p10,
        "catf_p50": catf_p50,
        "catf_p90": catf_p90,
        "current_position": position,
        "percentile_estimate": percentile,
    }





def update_costing_panel(epc_results, config=None):
    """Update costing panel with new simulation results."""
    return create_costing_panel(epc_results, config)

