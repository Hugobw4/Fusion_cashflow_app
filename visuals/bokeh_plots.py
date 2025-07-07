from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    BoxAnnotation,
    Span,
    Label,
    Range1d,
    NumeralTickFormatter,
    FactorRange,
    LabelSet,
)
from bokeh.palettes import RdYlGn
from bokeh.layouts import row
from bokeh.io import curdoc

# Premium color palette for Sankey
SANKEY_COLORS = {
    "Revenue": "#27ae60",  # Green
    "O&M": "#f39c12",  # Orange
    "NOI": "#16a085",  # Teal
    "Taxes": "#e74c3c",  # Red
    "Debt Service": "#2980b9",  # Blue
    "Interest": "#5dade2",  # Light Blue
    "Principal": "#154360",  # Navy
    "Residual": "#7f8c8d",  # Gray
    "Equity Return": "#00b894",  # Teal/Green
}


def plot_annual_cashflow_bokeh(outputs, config):
    """
    Create a Bokeh Figure for Annual Cash Flow Curves (Project vs. Equity) with phase shading.
    Args:
        outputs (dict): Output from cashflow_engine.run_cashflow_scenario
        config (dict): Model configuration
    Returns:
        bokeh.plotting.Figure: Bokeh figure object
    TODO: Add interactive phase toggles for Bokeh Server deployment.
    """
    years = outputs["year_labels_int"]
    unlevered = outputs["unlevered_cf_vec"]
    levered = outputs["levered_cf_vec"]
    source = ColumnDataSource(
        data=dict(
            year=years,
            unlevered=unlevered,
            levered=levered,
            revenue=outputs["revenue_vec"],
            om=outputs["om_vec"],
            fuel=outputs["fuel_vec"],
            tax=outputs["tax_vec"],
            noi=outputs["noi_vec"],
        )
    )
    # Use theme palette or fallback
    palette = curdoc().theme._json.get(
        "palette",
        [
            "#007aff",
            "#00b894",
            "#222",
            "#f8f8fa",
            "#e0e0e0",
            "#16a085",
            "#27ae60",
            "#f39c12",
            "#e74c3c",
            "#2980b9",
        ],
    )
    p = figure(
        title="Annual Cash Flows",
        x_axis_label="Year",
        y_axis_label="Annual Cash Flow ($)",
        width=800,
        height=350,
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )
    p.line(
        "year",
        "unlevered",
        source=source,
        legend_label="Unlevered CF (Project)",
        color=palette[0],
        line_width=2,
    )
    p.scatter(
        "year", "unlevered", source=source, color=palette[0], size=5, marker="circle"
    )
    p.line(
        "year",
        "levered",
        source=source,
        legend_label="Levered CF (Equity)",
        color=palette[1],
        line_width=2,
        line_dash="dashed",
    )
    p.scatter(
        "year", "levered", source=source, color=palette[1], size=5, marker="circle"
    )
    hover = HoverTool(
        tooltips=[
            ("Year", "@year"),
            ("Unlevered CF", "@unlevered{$0,0}"),
            ("Levered CF", "@levered{$0,0}"),
            ("Revenue", "@revenue{$0,0}"),
            ("O&M", "@om{$0,0}"),
            ("Fuel", "@fuel{$0,0}"),
            ("Tax", "@tax{$0,0}"),
            ("NOI", "@noi{$0,0}"),
        ],
        mode="vline",
    )
    p.add_tools(hover)
    # Phase shading using palette
    y_min = min(min(unlevered), min(levered))
    y_max = max(max(unlevered), max(levered))
    # Construction
    p.add_layout(
        BoxAnnotation(
            left=years[0],
            right=years[outputs["years_construction"] - 1],
            fill_alpha=0.15,
            fill_color=palette[4],
            line_color=None,
            line_width=0,
            bottom=y_min,
            top=y_max,
            level="underlay",
        )
    )
    # Ramp-up
    if config["ramp_up"]:
        p.add_layout(
            BoxAnnotation(
                left=years[outputs["years_construction"]],
                right=years[
                    outputs["years_construction"] + config["ramp_up_years"] - 1
                ],
                fill_alpha=0.10,
                fill_color=palette[5],
                line_color=None,
                level="underlay",
            )
        )
    # Operation
    op_start = outputs["years_construction"] + (
        config["ramp_up_years"] if config["ramp_up"] else 0
    )
    op_end = outputs["years_construction"] + config["plant_lifetime"] - 2
    p.add_layout(
        BoxAnnotation(
            left=years[op_start],
            right=years[op_end],
            fill_alpha=0.08,
            fill_color=palette[6],
            line_color=None,
            level="underlay",
        )
    )
    # Decommission
    p.add_layout(
        BoxAnnotation(
            left=years[-2],
            right=years[-1],
            fill_alpha=0.10,
            fill_color=palette[7],
            line_color=None,
            level="underlay",
        )
    )
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    # Format y-axis for big numbers
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")
    return p


def plot_cumulative_cashflow_bokeh(outputs, config):
    """
    Create a Bokeh Figure for Cumulative Cash Flow (Project vs. Equity), marking payback year and phases.
    """
    years = outputs["year_labels_int"]
    cum_unlevered = outputs["cumulative_unlevered_cf_vec"]
    cum_levered = outputs["cumulative_levered_cf_vec"]
    payback = outputs["payback"]
    source = ColumnDataSource(
        data=dict(year=years, cum_unlevered=cum_unlevered, cum_levered=cum_levered)
    )
    palette = curdoc().theme._json.get(
        "palette",
        [
            "#007aff",
            "#00b894",
            "#222",
            "#f8f8fa",
            "#e0e0e0",
            "#16a085",
            "#27ae60",
            "#f39c12",
            "#e74c3c",
            "#2980b9",
        ],
    )
    p = figure(
        title="Cumulative Cash Flows",
        x_axis_label="Year",
        y_axis_label="Cumulative Cash Flow ($)",
        width=800,
        height=350,
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )
    p.line(
        "year",
        "cum_unlevered",
        source=source,
        legend_label="Cumulative Unlevered CF",
        color=palette[0],
        line_width=2,
    )
    p.scatter(
        "year",
        "cum_unlevered",
        source=source,
        color=palette[0],
        size=5,
        marker="circle",
    )
    p.line(
        "year",
        "cum_levered",
        source=source,
        legend_label="Cumulative Levered CF",
        color=palette[1],
        line_width=2,
        line_dash="dashed",
    )
    p.scatter(
        "year", "cum_levered", source=source, color=palette[1], size=5, marker="circle"
    )
    hover = HoverTool(
        tooltips=[
            ("Year", "@year"),
            ("Cumulative Unlevered CF", "@cum_unlevered{$0,0}"),
            ("Cumulative Levered CF", "@cum_levered{$0,0}"),
        ],
        mode="vline",
    )
    p.add_tools(hover)
    # Phase shading using palette
    y_min = min(min(cum_unlevered), min(cum_levered))
    y_max = max(max(cum_unlevered), max(cum_levered))
    p.add_layout(
        BoxAnnotation(
            left=years[0],
            right=years[outputs["years_construction"] - 1],
            fill_alpha=0.15,
            fill_color=palette[4],
            line_color=None,
            level="underlay",
        )
    )
    if config["ramp_up"]:
        p.add_layout(
            BoxAnnotation(
                left=years[outputs["years_construction"]],
                right=years[
                    outputs["years_construction"] + config["ramp_up_years"] - 1
                ],
                fill_alpha=0.10,
                fill_color=palette[5],
                line_color=None,
                level="underlay",
            )
        )
    op_start = outputs["years_construction"] + (
        config["ramp_up_years"] if config["ramp_up"] else 0
    )
    op_end = outputs["years_construction"] + config["plant_lifetime"] - 2
    p.add_layout(
        BoxAnnotation(
            left=years[op_start],
            right=years[op_end],
            fill_alpha=0.08,
            fill_color=palette[6],
            line_color=None,
            level="underlay",
        )
    )
    p.add_layout(
        BoxAnnotation(
            left=years[-2],
            right=years[-1],
            fill_alpha=0.10,
            fill_color=palette[7],
            line_color=None,
            level="underlay",
        )
    )
    # Payback marker
    if payback is not None and 0 <= payback < len(years):
        payback_span = Span(
            location=years[payback],
            dimension="height",
            line_color="black",
            line_dash="dashed",
            line_width=2,
        )
        p.add_layout(payback_span)
        label = Label(
            x=years[payback],
            y=y_max,
            text=f"Payback: Year {years[payback]}",
            text_font_size="10pt",
            text_color="black",
            y_offset=-10,
        )
        p.add_layout(label)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")
    return p


def plot_dscr_profile_bokeh(outputs, config):
    """
    Create a Bokeh Figure for DSCR Profile (Debt Service Coverage Ratio), with phase shading and DSCR covenant line.
    """
    years = outputs["year_labels_int"]
    dscr_vec = outputs["dscr_vec"]
    dscr_masked = [
        v if (v is not None and v != float("inf") and v < 1e6) else None
        for v in dscr_vec
    ]
    noi = outputs["noi_vec"]
    debt_service = [
        a + b
        for a, b in zip(outputs["principal_paid_vec"], outputs["interest_paid_vec"])
    ]
    source = ColumnDataSource(
        data=dict(year=years, dscr=dscr_masked, noi=noi, debt_service=debt_service)
    )
    palette = curdoc().theme._json.get(
        "palette",
        [
            "#007aff",
            "#00b894",
            "#222",
            "#f8f8fa",
            "#e0e0e0",
            "#16a085",
            "#27ae60",
            "#f39c12",
            "#e74c3c",
            "#2980b9",
        ],
    )
    p = figure(
        title="Debt Service Coverage Ratio (DSCR) Profile",
        x_axis_label="Year",
        y_axis_label="DSCR",
        width=800,
        height=350,
        tools="pan,wheel_zoom,box_zoom,reset,save",
        y_range=Range1d(0, 5),
    )
    p.line(
        "year",
        "dscr",
        source=source,
        legend_label="DSCR",
        color=palette[2],
        line_width=2,
    )
    p.scatter("year", "dscr", source=source, color=palette[2], size=5, marker="circle")
    hover = HoverTool(
        tooltips=[
            ("Year", "@year"),
            ("DSCR", "@dscr{0.00}"),
            ("NOI", "@noi{$0,0}"),
            ("Debt Service", "@debt_service{$0,0}"),
        ],
        mode="vline",
    )
    p.add_tools(hover)
    # Interest-only period
    io_start = outputs["years_construction"]
    io_end = io_start + config["grace_period_years"] - 1
    p.add_layout(
        BoxAnnotation(
            left=years[io_start],
            right=years[io_end],
            fill_alpha=0.10,
            fill_color=palette[4],
            line_color=None,
            level="underlay",
        )
    )
    # DSCR covenant line
    covenant = Span(
        location=1.2,
        dimension="width",
        line_color=palette[8],
        line_dash="dashed",
        line_width=2,
    )
    p.add_layout(covenant)
    label = Label(
        x=years[0],
        y=1.22,
        text="DSCR = 1.2 (Covenant)",
        text_font_size="10pt",
        text_color=palette[8],
    )
    p.add_layout(label)
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    return p



# --- New: Cash Flow Waterfall ---
def plot_cashflow_waterfall_bokeh(outputs, config, width=700, height=380):
    """
    Create a Bokeh waterfall chart narrating full cash-flow from sources to uses.
    """
    # Build labels and amounts (same order as old bar chart)
    debt_drawdown = sum(outputs["debt_drawdown_vec"][:outputs["years_construction"]])
    construction_capex = outputs["toc"]
    equity_contribution = construction_capex - debt_drawdown
    labels = [
        "Debt",
        "Equity",
        "EPC",
        "Extra CapEx",
        "Project Contingency",
        "Process Contingency",
        "Financing Fees",
    ]
    amounts = [
        debt_drawdown,
        equity_contribution,
        -config["total_epc_cost"],
        -config["total_epc_cost"] * config["extra_capex_pct"],
        -config["total_epc_cost"] * config["project_contingency_pct"],
        -config["total_epc_cost"] * config["process_contingency_pct"],
        -config["total_epc_cost"] * config["financing_fee"],
    ]
    base = [0]
    for v in amounts[:-1]:
        base.append(base[-1] + v)
    top = [b + v for b, v in zip(base, amounts)]
    colors = ["#27ae60" if v > 0 else "#e74c3c" for v in amounts]
    x = list(range(len(labels)))
    src = ColumnDataSource(dict(x=x, label=labels, base=base, top=top, amt=amounts, color=colors))
    p = figure(x_range=labels, width=width, height=height, title="Project Sources & Uses Waterfall", toolbar_location=None, tools="")
    p.vbar(x='x', top='top', bottom='base', color='color', source=src, width=0.6)
    # Add connectors between bars using integer indices
    for i in range(len(labels) - 1):
        p.segment(x0=i, x1=i+1, y0=top[i], y1=base[i+1], line_color="#7f7f7f", line_width=2)
    p.xaxis.major_label_overrides = {i: label for i, label in enumerate(labels)}
    p.yaxis.formatter = NumeralTickFormatter(format="$0.0a")
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    hover = HoverTool(tooltips=[("Label", "@label"), ("Amount", "@amt{$0.00a}")])
    p.add_tools(hover)
    return p


def plot_sensitivity_bokeh(outputs, config, sensitivity_df):
    """
    Create a Bokeh horizontal bar chart for NPV/IRR deltas by scenario.
    """
    from bokeh.transform import dodge
    from bokeh.models import FactorRange

    base_npv = sensitivity_df[sensitivity_df["Scenario"] == "Base"]["NPV"].values[0]
    base_irr = sensitivity_df[sensitivity_df["Scenario"] == "Base"]["IRR"].values[0]
    scenarios = sensitivity_df["Scenario"].tolist()[1:]
    npv_deltas = sensitivity_df["NPV"].tolist()[1:]
    npv_deltas = [v - base_npv for v in npv_deltas]
    irr_deltas = sensitivity_df["IRR"].tolist()[1:]
    irr_deltas = [v - base_irr for v in irr_deltas]
    src = ColumnDataSource(
        data=dict(scenarios=scenarios, npv=npv_deltas, irr=irr_deltas)
    )
    p = figure(
        y_range=FactorRange(*scenarios[::-1]),
        x_axis_label="Delta from Base",
        title="Sensitivity of NPV and IRR",
        width=800,
        height=350,
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )
    palette = curdoc().theme._json.get(
        "palette",
        [
            "#007aff",
            "#00b894",
            "#222",
            "#f8f8fa",
            "#e0e0e0",
            "#16a085",
            "#27ae60",
            "#f39c12",
            "#e74c3c",
            "#2980b9",
        ],
    )
    p.hbar(
        y=dodge("scenarios", -0.15, range=p.y_range),
        right="npv",
        height=0.3,
        source=src,
        color=palette[0],
        legend_label="NPV Delta",
    )
    p.hbar(
        y=dodge("scenarios", 0.15, range=p.y_range),
        right="irr",
        height=0.3,
        source=src,
        color=palette[1],
        legend_label="IRR Delta",
    )
    hover = HoverTool(
        tooltips=[
            ("Scenario", "@scenarios"),
            ("NPV Δ", "@npv{$0,0}"),
            ("IRR Δ", "@irr{0.000}"),
        ]
    )
    p.add_tools(hover)
    p.legend.location = "top_right"
    p.legend.orientation = "vertical"
    p.xaxis.formatter = NumeralTickFormatter(format="0,0")
    return p


def _prepare_nodes(outputs):
    """
    Assigns x/y, width, color, and label for each node.
    Returns: nodes (list of dict), links (list of dict), total_inflow (float)
    """
    # Calculate values
    years_construction = outputs["years_construction"]
    plant_lifetime = outputs["plant_lifetime"]
    op_slice = slice(years_construction, years_construction + plant_lifetime)
    revenue = sum(outputs["revenue_vec"][op_slice])
    om = sum(outputs["om_vec"][op_slice])
    taxes = sum(outputs["tax_vec"][op_slice])
    noi = revenue - om - taxes
    debt_service = sum(
        [
            a + b
            for a, b in zip(
                outputs["principal_paid_vec"][op_slice],
                outputs["interest_paid_vec"][op_slice],
            )
        ]
    )
    interest = sum(outputs["interest_paid_vec"][op_slice])
    principal = sum(outputs["principal_paid_vec"][op_slice])
    residual = noi - debt_service
    equity_return = sum(outputs["equity_cf_vec"][op_slice])

    # Node order and positions
    palette = curdoc().theme._json.get(
        "palette", ["#27ae60", "#f39c12", "#e74c3c", "#2980b9", "#8e44ad", "#00b894"]
    )
    node_defs = [
        ("Revenue", 0, 0.5, revenue, palette[0]),
        ("O&M", 1, 0.8, om, palette[1]),
        ("Taxes", 1, 0.2, taxes, palette[2]),
        ("NOI", 2, 0.5, noi, palette[3]),
        ("Debt Service", 3, 0.5, debt_service, palette[3]),
        ("Interest", 4, 0.8, interest, palette[4]),
        ("Principal", 4, 0.2, principal, palette[4]),
        ("Residual", 5, 0.5, residual, palette[5]),
        ("Equity Return", 6, 0.5, equity_return, palette[5]),
    ]
    nodes = []
    for name, x, y, value, color in node_defs:
        label = f"{name}\n${value/1e9:,.1f} B"
        nodes.append(
            dict(
                name=name, x=x, y=y, value=value, color=color, label=label, w=0.7, h=30
            )
        )
    # Links: source, target, value, color
    links = [
        dict(source="Revenue", target="O&M", value=om, color=palette[1]),
        dict(source="O&M", target="Taxes", value=taxes, color=palette[2]),
        dict(source="Taxes", target="NOI", value=noi, color=palette[3]),
        dict(source="NOI", target="Debt Service", value=debt_service, color=palette[3]),
        dict(
            source="Debt Service", target="Interest", value=interest, color=palette[4]
        ),
        dict(
            source="Debt Service", target="Principal", value=principal, color=palette[4]
        ),
        dict(source="NOI", target="Residual", value=residual, color=palette[5]),
        dict(
            source="Residual",
            target="Equity Return",
            value=equity_return,
            color=palette[5],
        ),
    ]
    total_inflow = revenue
    return nodes, links, total_inflow


def _prepare_links(nodes, links, total_inflow):
    """
    Computes stacking offsets for each source-target, and percent of total.
    Returns: updated links with y0/y1 offsets and percent.
    """
    # For each stage, stack outgoing links
    node_map = {n["name"]: n for n in nodes}
    stage_links = {}
    for l in links:
        stage_links.setdefault(l["source"], []).append(l)
    # For each source, assign y0/y1 offsets for stacking
    for src, out_links in stage_links.items():
        y = node_map[src]["y"]
        total = sum(l["value"] for l in out_links)
        offset = y - 0.5 * (total / total_inflow)
        for l in out_links:
            l["y0"] = offset + 0.5 * l["value"] / total_inflow
            offset += l["value"] / total_inflow
            l["percent"] = l["value"] / total_inflow
    # For each target, assign y1
    for l in links:
        l["y1"] = node_map[l["target"]]["y"]
    return links


def _build_patches(nodes, links, scale):
    """
    For each link, builds a smooth 4–6-point patch (polygon) for the ribbon.
    Returns: lists for xs, ys, colors, labels, percents, values, sources, targets.
    """
    node_map = {n["name"]: n for n in nodes}
    xs, ys, colors, labels, percents, values, sources, targets = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for l in links:
        x0 = node_map[l["source"]]["x"] + 0.35
        x1 = node_map[l["target"]]["x"] - 0.35
        y0 = l["y0"] * scale * 1.5 * 450  # scale to canvas
        y1 = l["y1"] * scale * 1.5 * 450
        thickness = l["value"] * scale
        # Top and bottom y
        y0_top = y0 + 0.5 * thickness
        y0_bot = y0 - 0.5 * thickness
        y1_top = y1 + 0.5 * thickness
        y1_bot = y1 - 0.5 * thickness
        # Smooth curve: control points
        ctrl_x = (x0 + x1) / 2
        # 6-point patch for smoothness
        xs_patch = [x0, ctrl_x, x1, x1, ctrl_x, x0]
        ys_patch = [y0_top, y0_top, y1_top, y1_bot, y0_bot, y0_bot]
        xs.append(xs_patch)
        ys.append(ys_patch)
        colors.append(l["color"])
        labels.append(f"${l['value']/1e9:,.1f} B")
        percents.append(l["percent"])
        values.append(l["value"])
        sources.append(l["source"])
        targets.append(l["target"])
    return xs, ys, colors, labels, percents, values, sources, targets


def plot_sensitivity_heatmap(outputs, config, sensitivity_df):
    """
    Create a Bokeh categorical heatmap for sensitivity analysis (ΔNPV by driver and scenario band).
    Args:
        outputs (dict): Output from cashflow_engine.run_cashflow_scenario
        config (dict): Model configuration
        sensitivity_df (pd.DataFrame): DataFrame from run_sensitivity_analysis
    Returns:
        bokeh.plotting.Figure: Bokeh heatmap figure
    """
    from bokeh.models import (
        ColumnDataSource,
        ColorBar,
        BasicTicker,
        PrintfTickFormatter,
        FactorRange,
    )
    from bokeh.transform import linear_cmap

    # Calculate deltas per driver
    base_npv = sensitivity_df[sensitivity_df["Band"] == "0%"].set_index("Driver")["NPV"]
    base_irr = sensitivity_df[sensitivity_df["Band"] == "0%"].set_index("Driver")["IRR"]

    def delta_npv(row):
        return row["NPV"] - base_npv[row["Driver"]]

    def delta_irr(row):
        return row["IRR"] - base_irr[row["Driver"]]

    sensitivity_df["ΔNPV"] = sensitivity_df.apply(delta_npv, axis=1)
    sensitivity_df["ΔIRR"] = sensitivity_df.apply(delta_irr, axis=1)
    # Now assign heatmap_df after delta columns are present
    heatmap_df = sensitivity_df.copy()
    # Categorical axes
    drivers = list(heatmap_df["Driver"].unique())

    # Sort bands numerically so 0% is between -2% and +2%
    def band_sort_key(b):
        try:
            return int(b.replace("%", ""))
        except:
            return 0

    bands = sorted(heatmap_df["Band"].unique(), key=band_sort_key)
    # Prepare data for Bokeh
    source = ColumnDataSource(heatmap_df)
    # Custom diverging palette: blue to white to red
    # RdBu[11] is blue-white-red, with white at the center
    palette = RdYlGn[11]
    # Symmetric color mapping: 0 always maps to white
    max_abs = max(abs(heatmap_df["ΔNPV"].min()), abs(heatmap_df["ΔNPV"].max()))
    mapper = linear_cmap(
        field_name="ΔNPV", palette=palette, low=-max_abs, high=+max_abs
    )
    p = figure(
        title="Sensitivity Analysis: ΔNPV by Driver and Scenario",
        x_range=FactorRange(*bands),
        y_range=FactorRange(*drivers[::-1]),
        x_axis_location="above",
        width=800,
        height=350,
        tools="hover,save",
        toolbar_location="right",
        tooltips=[
            ("Driver", "@Driver"),
            ("Scenario", "@Scenario"),
            ("ΔNPV", "@{ΔNPV}{$0,0}"),
            ("ΔIRR", "@{ΔIRR}{0.000}"),
        ],
    )
    p.rect(
        x="Band",
        y="Driver",
        width=1,
        height=1,
        source=source,
        line_color=None,
        fill_color=mapper,
    )
    # Colorbar
    color_bar = ColorBar(
        color_mapper=mapper["transform"],
        major_label_text_font_size="10pt",
        ticker=BasicTicker(desired_num_ticks=7),
        formatter=PrintfTickFormatter(format="$%d"),
        label_standoff=8,
        border_line_color=None,
        location=(0, 0),
    )
    p.add_layout(color_bar, "right")
    # Axis polish
    p.xaxis.axis_label = "Scenario Band"
    p.yaxis.axis_label = "Driver"
    p.xaxis.major_label_orientation = 0.8
    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "12pt"
    p.outline_line_color = None
    return p
