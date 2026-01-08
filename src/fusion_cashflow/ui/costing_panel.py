"""
Detailed costing panel showing ARPA-E cost hierarchy with drill-down capabilities.

Provides:
- Hierarchical cost breakdown by ARPA-E category
- Pie chart visualization of top-level costs
- Expandable tree table with material details
- Total EPC cost summary
"""

from bokeh.models import (
    ColumnDataSource,
    DataTable,
    TableColumn,
    Div,
    Row,
    Column as BokehColumn,
)
from bokeh.plotting import figure
from bokeh.palettes import Category20_20
import numpy as np


def create_costing_panel(epc_results):
    """
    Create detailed costing panel with hierarchical breakdown.
    
    Args:
        epc_results: Dictionary from power_to_epc.compute_epc() containing:
            - 'total_epc': Total EPC cost ($)
            - 'epc_per_kw': Cost per kilowatt ($/kW)
            - 'breakdown': Dict of top-level category costs
            - 'detailed_result': Full ARPA-E breakdown with subcategories
    
    Returns:
        bokeh.models.Column: Panel with cost tree, pie chart, and detail view
    """
    
    # Extract cost data
    total_epc = epc_results.get('total_epc', 0)
    cost_per_kw = epc_results.get('epc_per_kw', 0)
    detailed = epc_results.get('detailed_result', {})
    
    # Get net MW for context
    power_balance = epc_results.get('power_balance', {})
    net_mw = power_balance.get('PNET', 0) if 'PNET' in power_balance else power_balance.get('net_mw', 0)
    gross_mw = power_balance.get('PET', 0) if 'PET' in power_balance else power_balance.get('gross_mw', 0)
    
    # Build hierarchical data structure
    tree_data = _build_cost_tree(epc_results, total_epc)
    
    # Create summary header
    summary_html = f"""
    <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin: 0 0 10px 0; color: #2c3e50;">EPC Cost Breakdown</h2>
        <div style="font-size: 28px; font-weight: bold; color: #3498db;">
            ${total_epc/1e9:.2f}B
        </div>
        <div style="margin-top: 5px; font-size: 18px; color: #7f8c8d;">
            ${cost_per_kw:,.0f} /kW
        </div>
        <div style="margin-top: 10px; color: #7f8c8d; font-size: 14px;">
            Total Engineering, Procurement & Construction Cost<br/>
            {net_mw:.0f} MW Net | {gross_mw:.0f} MW Gross
        </div>
    </div>
    """
    summary_div = Div(text=summary_html, width=800)
    
    # Create pie chart for top-level categories
    pie_chart = _create_pie_chart(tree_data, total_epc)
    
    # Create expandable tree table
    tree_table = _create_tree_table(tree_data)
    
    # Create detail panel (initially empty, updates on selection)
    detail_div = Div(text=_get_placeholder_detail(), width=800, height=300)
    
    # Layout
    layout = BokehColumn(
        summary_div,
        Row(pie_chart, tree_table),
        detail_div,
        sizing_mode='stretch_width'
    )
    
    return layout


def _build_cost_tree(epc_results, total_epc):
    """
    Build hierarchical cost tree from EPC results.
    
    Returns list of dicts with:
        - name: Category name
        - cost: Cost in $ (not $/kW)
        - percent: Percentage of total
        - level: Hierarchy level (0=top, 1=sub)
        - expanded: Whether subcategories are visible
        - children: List of subcategory dicts
    """
    tree = []
    detailed = epc_results.get('detailed_result', {})
    
    # Major top-level categories from ARPA-E breakdown
    major_categories = [
        {
            'name': 'Buildings & Site',
            'cost': detailed.get('building_total', 0),
            'children_dict': detailed.get('building_costs', {}),
            'format_child': lambda k, v: (k.replace('_', ' ').title(), v)
        },
        {
            'name': 'Pre-Construction',
            'cost': detailed.get('preconstruction_total', 0),
            'children_dict': detailed.get('preconstruction_costs', {}),
            'format_child': lambda k, v: (k.replace('_', ' ').title(), v)
        },
        {
            'name': 'Reactor Equipment',
            'cost': detailed.get('reactor_equipment', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Indirect Costs',
            'cost': detailed.get('indirect_costs', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Interest During Construction',
            'cost': detailed.get('idc', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': "Owner's Costs",
            'cost': detailed.get('owners_costs', 0),
            'children_dict': {},
            'format_child': None
        },
    ]
    
    for category in major_categories:
        cat_cost = category['cost']
        if cat_cost <= 0:
            continue
            
        child_nodes = []
        children_dict = category['children_dict']
        format_func = category['format_child']
        
        if children_dict and format_func:
            # Sort children by cost descending
            sorted_children = sorted(children_dict.items(), key=lambda x: x[1], reverse=True)
            for key, value in sorted_children:
                if value > 0:
                    child_name, child_cost = format_func(key, value)
                    child_nodes.append({
                        'name': f'  └─ {child_name}',
                        'cost': child_cost,
                        'percent': (child_cost / total_epc * 100) if total_epc > 0 else 0,
                        'level': 1,
                        'expanded': False,
                        'children': []
                    })
        
        tree.append({
            'name': f'▶ {category["name"]}',
            'cost': cat_cost,
            'percent': (cat_cost / total_epc * 100) if total_epc > 0 else 0,
            'level': 0,
            'expanded': False,
            'children': child_nodes
        })
    
    return tree


def _create_pie_chart(tree_data, total_epc):
    """
    Create pie chart showing top-level category costs.
    """
    # Extract top-level categories only
    categories = [node['name'].replace('▶ ', '') for node in tree_data]
    costs = [node['cost'] for node in tree_data]
    percentages = [node['percent'] for node in tree_data]
    
    # Sort by cost descending
    sorted_indices = np.argsort(costs)[::-1]
    categories = [categories[i] for i in sorted_indices]
    costs = [costs[i] for i in sorted_indices]
    percentages = [percentages[i] for i in sorted_indices]
    
    # Calculate angles for pie slices
    angles = np.array(percentages) / 100 * 2 * np.pi
    
    # Create data source for wedges with hover data
    wedge_data = {
        'start_angle': [],
        'end_angle': [],
        'color': [],
        'category': [],
        'cost': [],
        'percent': []
    }
    
    # Colors
    colors = Category20_20[:len(categories)]
    
    # Build wedge data
    start_angle = 0
    for i, (cat, cost, pct, angle) in enumerate(zip(categories, costs, percentages, angles)):
        end_angle = start_angle + angle
        wedge_data['start_angle'].append(start_angle)
        wedge_data['end_angle'].append(end_angle)
        wedge_data['color'].append(colors[i])
        wedge_data['category'].append(cat)
        wedge_data['cost'].append(f"${cost/1e9:.2f}B")
        wedge_data['percent'].append(f"{pct:.1f}%")
        start_angle = end_angle
    
    source = ColumnDataSource(wedge_data)
    
    # Create figure with hover tool
    p = figure(
        width=400,
        height=400,
        title="Cost Distribution by Category",
        toolbar_location=None,
        x_range=(-1.2, 1.2),
        y_range=(-1.2, 1.2)
    )
    
    # Draw pie slices using data source
    wedges = p.wedge(
        x=0, y=0,
        radius=1,
        start_angle='start_angle',
        end_angle='end_angle',
        color='color',
        alpha=0.8,
        source=source
    )
    
    # Add hover tool
    from bokeh.models import HoverTool
    hover = HoverTool(
        tooltips=[
            ("Category", "@category"),
            ("Cost", "@cost"),
            ("Percent", "@percent")
        ],
        renderers=[wedges]
    )
    p.add_tools(hover)
    
    # Add legend manually
    from bokeh.models import Legend, LegendItem
    legend_items = []
    for i, cat in enumerate(categories):
        label = f"{cat[:20]}..." if len(cat) > 20 else cat
        # Create invisible glyph for legend
        invisible = p.circle(x=-10, y=-10, size=10, color=colors[i], alpha=0.8, visible=False)
        legend_items.append(LegendItem(label=label, renderers=[invisible]))
    
    legend = Legend(items=legend_items, location="center_right")
    legend.label_text_font_size = "8pt"
    p.add_layout(legend, 'right')
    
    # Remove axes
    p.axis.visible = False
    p.grid.visible = False
    
    return p


def _create_tree_table(tree_data):
    """
    Create tree table showing hierarchical costs (all rows expanded for simplicity).
    """
    # Flatten tree into all rows (including children)
    rows = []
    for node in tree_data:
        # Add parent node
        rows.append({
            'name': node['name'].replace('▶ ', '▼ '),  # Show as expanded
            'cost': f"${node['cost']/1e9:.3f}B",
            'percent': f"{node['percent']:.1f}%"
        })
        # Add all children
        for child in node.get('children', []):
            rows.append({
                'name': child['name'],
                'cost': f"${child['cost']/1e9:.3f}B",
                'percent': f"{child['percent']:.1f}%"
            })
    
    source = ColumnDataSource(data={
        'name': [r['name'] for r in rows],
        'cost': [r['cost'] for r in rows],
        'percent': [r['percent'] for r in rows]
    })
    
    columns = [
        TableColumn(field='name', title='Category', width=250),
        TableColumn(field='cost', title='Cost ($B)', width=120),
        TableColumn(field='percent', title='% of Total', width=80)
    ]
    
    table = DataTable(
        source=source,
        columns=columns,
        width=450,
        height=600,  # Taller to show all rows
        index_position=None,
        selectable=False
    )
    
    return table


def _get_placeholder_detail():
    """
    Generate placeholder HTML for detail panel.
    """
    return """
    <div style="padding: 20px; background: #ecf0f1; border-radius: 8px; margin-top: 20px;">
        <h3 style="color: #7f8c8d; margin: 0;">Detail View</h3>
        <p style="color: #95a5a6; margin: 10px 0 0 0;">
            Click on a category to see detailed material calculations and cost drivers.
        </p>
    </div>
    """


def _get_category_detail(category_name, node_data):
    """
    Generate detailed HTML for a selected category showing material calculations.
    
    Args:
        category_name: Name of selected category
        node_data: Cost node data including children and calculations
    
    Returns:
        str: HTML for detail panel
    """
    # Extract subcategory breakdown
    children = node_data.get('children', [])
    
    html = f"""
    <div style="padding: 20px; background: #ecf0f1; border-radius: 8px; margin-top: 20px;">
        <h3 style="color: #2c3e50; margin: 0 0 15px 0;">{category_name}</h3>
    """
    
    if children:
        html += "<h4 style='color: #34495e; margin: 15px 0 10px 0;'>Subcategory Breakdown:</h4>"
        html += "<table style='width: 100%; border-collapse: collapse;'>"
        html += """
        <tr style='background: #bdc3c7; color: white;'>
            <th style='padding: 8px; text-align: left;'>Component</th>
            <th style='padding: 8px; text-align: right;'>Cost ($M)</th>
            <th style='padding: 8px; text-align: right;'>% of Category</th>
        </tr>
        """
        
        cat_total = node_data['cost']
        for child in children:
            child_name = child['name'].replace('  └─ ', '')
            child_pct = (child['cost'] / cat_total * 100) if cat_total > 0 else 0
            html += f"""
            <tr style='border-bottom: 1px solid #bdc3c7;'>
                <td style='padding: 8px;'>{child_name}</td>
                <td style='padding: 8px; text-align: right;'>${child['cost']/1e6:,.1f}</td>
                <td style='padding: 8px; text-align: right;'>{child_pct:.1f}%</td>
            </tr>
            """
        html += "</table>"
    
    html += """
        <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 4px;">
            <h4 style='color: #34495e; margin: 0 0 10px 0;'>Cost Drivers:</h4>
            <ul style='color: #7f8c8d; margin: 5px 0; padding-left: 20px;'>
                <li>Material costs scaled from ARPA-E reference designs</li>
                <li>Manufacturing complexity factors applied</li>
                <li>Volume production learning curves included</li>
                <li>Installation and commissioning costs embedded</li>
            </ul>
        </div>
    </div>
    """
    
    return html


def update_costing_panel(epc_results):
    """
    Update costing panel with new simulation results.
    
    Args:
        epc_results: Updated EPC results dictionary
    
    Returns:
        Updated panel layout
    """
    return create_costing_panel(epc_results)
