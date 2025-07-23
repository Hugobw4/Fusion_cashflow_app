
from bokeh.io import output_file, save
from bokeh.layouts import column, Spacer
from bokeh.models import Div
from datetime import datetime
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, LabelSet, HoverTool, Range1d
from bokeh.themes import Theme
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os


def fmt_metric(k, v):
    if (
        k.lower().endswith("irr")
        or k.lower().endswith("avg")
        or k.lower().endswith("min")
    ):
        return f"{v:.2%}" if v is not None else "—"
    elif k.lower().startswith("lcoe"):
        return f"${v:,.2f}/MWh" if v is not None else "—"
    elif isinstance(v, (int, float)):
        return f"${v:,.0f}" if v is not None else "—"
    else:
        return "—" if v is None else str(v)



def add_section(layout, heading: str, figure, table=None, csv=None):
    """
    Appends a section with heading, figure, optional table, and optional CSV download link to the layout list.
    """
    layout.append(Div(text=f"<div class='section'><h2>{heading}</h2></div>", width=900))
    if figure is not None:
        layout.append(figure)
    if table is not None:
        layout.append(table)
    if csv is not None:
        layout.append(Div(text=f'<a href="{csv}" download style="font-size:14px;">Download CSV</a>', width=900))


def save_bokeh_report(
    figures,
    metrics,
    filename,
    title="Fusion Plant Whole-Life Cash Flow Report",
    sankey=None,
    project_name="Fusion Project",
    scenario_name="Base Case",
    sections=None,
    csv_exports=None,
):
    """
    Save a single HTML report with a modern, premium layout: title block, summary metrics, Sankey, all Bokeh plots, and a footer.
    Args:
        figures (list): List of Bokeh figures/layouts (now: plot, table pairs, plus download link at end).
        metrics (dict or pd.DataFrame): Summary metrics to display at the top.
        filename (str): Output HTML file path.
        title (str): Report title.
        sankey (holoviews Sankey or None): Optional Holoviews Sankey object to embed.
        project_name (str): Project name for the title block.
        scenario_name (str): Scenario name for the title block.
        sections (list): List of (heading, figure, table, csv) tuples for DRY section generation.
        csv_exports (list): List of CSV file paths for download links.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    # Render title block
    header_template = env.get_template("report_header.html")
    title_html = header_template.render(
        title=title,
        project_name=project_name,
        scenario_name=scenario_name,
        now=now,
    )
    title_div = Div(text=title_html, width=1000)
    # Render summary metrics table
    if hasattr(metrics, "to_dict"):
        metrics_dict = (
            metrics.to_dict(orient="records")[0]
            if hasattr(metrics, "to_dict")
            else dict(metrics)
        )
    elif isinstance(metrics, dict):
        metrics_dict = metrics
    else:
        metrics_dict = dict(metrics)
    summary_template = env.get_template("summary_table.html")
    # Format metrics values for display
    formatted_metrics = {k: fmt_metric(k, v) for k, v in metrics_dict.items()}
    metrics_html = summary_template.render(metrics=formatted_metrics)
    metrics_div = Div(text=metrics_html, width=900)
    # Sankey section
    sankey_layout = []
    if sankey is not None:
        sankey_bokeh = sankey  # Already a Bokeh Figure
        sankey_layout = [
            Div(text="<div class='section'><h2>Project Lifetime Cash Flow Sankey</h2></div>"),
            sankey_bokeh,
            Spacer(height=16),
        ]
    # Compose layout using add_section and sections list
    layout_items = [
        title_div,
        metrics_div,
        Spacer(height=16),
        *sankey_layout,
        Spacer(height=8),
    ]
    # If no sections provided, fallback to old behavior
    if sections is None:
        section_titles = [
            "Annual Cash Flow Curves",
            "Cumulative Cash Flow",
            "DSCR Profile",
            "Funding & Uses",
            "Sensitivity Analysis",
        ]
        for i, heading in enumerate(section_titles):
            plot_idx = 2 * i
            table_idx = 2 * i + 1
            add_section(
                layout_items,
                heading,
                figures[plot_idx] if plot_idx < len(figures) else None,
                figures[table_idx] if table_idx < len(figures) else None,
                f"table{i+1}.csv" if csv_exports and i < len(csv_exports) else None,
            )
        # If there is a download link at the end, add it
        if len(figures) > 2 * len(section_titles):
            layout_items.append(figures[-1])
    else:
        for section in sections:
            # section: (heading, figure, table, csv)
            add_section(layout_items, *section)
    layout_items.append(Spacer(height=24))
    # Footer
    footer_html = f"<div class='footer'>Generated by Fusion Plant Cash Flow Tool — {now}</div>"
    footer_div = Div(text=footer_html, width=1000)
    layout_items.append(footer_div)
    # Output with external CSS and Bokeh theme
    output_file(filename, title=title)
    from bokeh.io import curdoc
    curdoc().theme = Theme(filename=os.path.join(os.path.dirname(__file__), "bokeh_theme.yaml"))
    save(column(*layout_items))


    # (deleted: plot_sankey_diagram)


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
    node_defs = [
        ("Revenue", 0, 0.5, revenue, "#27ae60"),
        ("O&M", 1, 0.8, om, "#f39c12"),
        ("Taxes", 1, 0.2, taxes, "#e74c3c"),
        ("NOI", 2, 0.5, noi, "#2980b9"),
        ("Debt Service", 3, 0.5, debt_service, "#2980b9"),
        ("Interest", 4, 0.8, interest, "#8e44ad"),
        ("Principal", 4, 0.2, principal, "#8e44ad"),
        ("Residual", 5, 0.5, residual, "#00b894"),
        ("Equity Return", 6, 0.5, equity_return, "#00b894"),
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
        dict(source="Revenue", target="O&M", value=om, color="#f39c12"),
        dict(source="O&M", target="Taxes", value=taxes, color="#e74c3c"),
        dict(source="Taxes", target="NOI", value=noi, color="#2980b9"),
        dict(source="NOI", target="Debt Service", value=debt_service, color="#2980b9"),
        dict(source="Debt Service", target="Interest", value=interest, color="#8e44ad"),
        dict(
            source="Debt Service", target="Principal", value=principal, color="#8e44ad"
        ),
        dict(source="NOI", target="Residual", value=residual, color="#00b894"),
        dict(
            source="Residual",
            target="Equity Return",
            value=equity_return,
            color="#00b894",
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
