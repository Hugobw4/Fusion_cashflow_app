"""
Detailed costing panel showing ARPA-E cost hierarchy with drill-down capabilities.

Modern layout with:
- Enhanced KPI banner with CATF benchmark bands
- Top reduction levers card for decision support
- Baseline comparison mode
- Expandable accordion with driver chips and maturity tags
- Dynamic detail panel with cost driver explanations
- Square pie chart visualization
"""

import numpy as np
from bokeh.models import (
    ColumnDataSource,
    Div,
    Column as BokehColumn,
    Row as BokehRow,
    HoverTool,
    Button,
    CustomJS,
)
from bokeh.plotting import figure
from bokeh.palettes import Category20_20


def create_costing_panel(epc_results, config=None):
    """
    Create detailed costing panel with enhanced decision support.
    
    Args:
        epc_results: Dictionary from power_to_epc.compute_epc() containing:
            - 'total_epc': Total EPC cost ($)
            - 'epc_per_kw': Cost per kilowatt ($/kW)
            - 'breakdown': Dict of top-level category costs
            - 'detailed_result': Full ARPA-E breakdown with subcategories
        config: Configuration dictionary with project parameters (optional)
    
    Returns:
        bokeh.models.Column: Enhanced panel with decision support features
    """
    
    # Extract cost data
    total_epc = epc_results.get('total_epc', 0)
    cost_per_kw = epc_results.get('epc_per_kw', 0)
    
    # Get net MW and tech for context
    power_balance = epc_results.get('power_balance', {})
    net_mw = power_balance.get('PNET', 0) if 'PNET' in power_balance else power_balance.get('net_mw', 0)
    gross_mw = power_balance.get('PET', 0) if 'PET' in power_balance else power_balance.get('gross_mw', 0)
    
    # Get tech from config if available
    tech = config.get('power_method', 'MFE') if config else 'MFE'
    
    # Build enhanced hierarchical data structure with drivers
    tree_data = _build_enhanced_cost_tree(epc_results, total_epc, config)
    
    # Get benchmark bands
    benchmark_info = _get_benchmark_bands(net_mw, cost_per_kw, tech)
    
    # Compute reduction levers
    reduction_levers = _compute_reduction_levers(epc_results, config) if config else []
    
    # 1. TOP: Enhanced KPI banner with benchmark
    summary_div = _create_kpi_banner(total_epc, cost_per_kw, net_mw, gross_mw, benchmark_info)
    
    # 2. Top reduction levers card
    levers_card = _create_reduction_levers_card(reduction_levers)
    
    # 3. Horizontal bar chart (better than pie for comparing values)
    chart_title = Div(text="<h3 style='color: #ffffff; font-size: 16px; font-weight: 700; margin: 20px 0 8px 0; font-family: Inter, Helvetica, Arial, sans-serif;'>Cost Distribution by Category</h3>", sizing_mode='stretch_width')
    bar_chart = _create_horizontal_bar_chart(tree_data, total_epc)
    
    # 4. Enhanced accordion with drivers (Bokeh-native widgets)
    accordion_container = _create_bokeh_accordion(tree_data)
    
    # 5. Detail panel (initially shows first category)
    detail_div = _create_detail_panel(tree_data[0] if tree_data else None, config, epc_results)
    
    # Wrap in container with padding and max-width for better layout
    content_column = BokehColumn(
        summary_div,
        levers_card,
        chart_title,
        bar_chart,
        accordion_container,
        detail_div,
        sizing_mode='stretch_width',
        styles={'padding': '0 40px', 'max-width': '1400px', 'margin': '0 auto', 'background': '#001e3c', 'border-radius': '16px', 'color': '#ffffff'}
    )
    
    return content_column


def _estimate_reactor_equipment_breakdown(total_reactor_cost):
    """
    Estimate reactor equipment breakdown based on typical fusion reactor component proportions.
    
    This provides a conceptual breakdown since ARPA-E methodology doesn't provide detailed
    reactor equipment subcategories. Proportions based on tokamak/stellarator cost studies.
    
    Args:
        total_reactor_cost: Total reactor equipment cost ($)
        
    Returns:
        Dictionary with component names and estimated costs
    """
    if total_reactor_cost <= 0:
        return {}
    
    # Typical component proportions for fusion reactors
    # Based on ARIES and ITER cost breakdowns
    proportions = {
        'Magnet Systems (TF, PF, CS)': 0.35,  # Toroidal field, poloidal field, central solenoid
        'First Wall & Blanket': 0.25,          # Plasma-facing components and tritium breeding
        'Vacuum Vessel & Support': 0.15,       # Primary vacuum boundary and structural support
        'Divertor & Heat Exhaust': 0.10,       # Power and particle exhaust systems
        'Auxiliary Heating Systems': 0.08,     # RF heating, neutral beams, etc.
        'Diagnostics & Instrumentation': 0.07  # Measurement and control systems
    }
    
    return {name: total_reactor_cost * proportion for name, proportion in proportions.items()}


def _estimate_indirect_costs_breakdown(total_indirect):
    """Estimate indirect costs breakdown based on typical nuclear project proportions."""
    if total_indirect <= 0:
        return {}
    
    proportions = {
        'Engineering & Design': 0.35,          # Detailed engineering and technical design
        'Construction Management': 0.25,       # Project management and oversight
        'Quality Assurance': 0.15,             # QA/QC programs and testing
        'Licensing & Permitting': 0.12,        # Regulatory compliance costs
        'Insurance & Bonding': 0.08,           # Construction insurance and performance bonds
        'Commissioning & Startup': 0.05        # Initial testing and startup activities
    }
    
    return {name: total_indirect * proportion for name, proportion in proportions.items()}


def _estimate_owners_costs_breakdown(total_owners):
    """Estimate owner's costs breakdown based on typical nuclear project proportions."""
    if total_owners <= 0:
        return {}
    
    proportions = {
        'Project Development & Planning': 0.30,  # Early-stage development costs
        'Site Investigation & Studies': 0.20,     # Geotechnical, environmental studies
        'Legal & Financial Services': 0.18,       # Legal fees, financial advisory
        'Regulatory & Licensing Fees': 0.15,      # NRC fees, licensing applications
        'Owner Oversight & Management': 0.12,     # Owner's project management team
        'Contingency Reserve': 0.05               # Owner's contingency for changes
    }
    
    return {name: total_owners * proportion for name, proportion in proportions.items()}


def _build_enhanced_cost_tree(epc_results, total_epc, config):
    """
    Build hierarchical cost tree with enhanced driver metadata.
    
    Returns list of dicts with:
        - name: Category name
        - cost: Cost in $ (not $/kW)
        - percent: Percentage of total
        - level: Hierarchy level (0=top, 1=sub)
        - expanded: Whether subcategories are visible
        - children: List of subcategory dicts
        - category_id: Unique identifier for DOM/callbacks
        - drivers: List of driver chip labels
        - maturity_tag: "High" | "Medium" | "Low"
        - tooltip_text: Explanation of cost drivers
        - sensitivity_rank: 1-6 ranking for reduction potential
    """
    tree = []
    detailed = epc_results.get('detailed_result', {})
    
    # Major top-level categories from new costing breakdown
    # Extract component costs for detailed breakdown
    cas_22_components = {
        'Reactor Core': detailed.get('cas_2201', 0),
        'Magnets': detailed.get('cas_2203', 0),
        'Heating Systems': detailed.get('heating_systems', 0),
        'Coolant System': detailed.get('coolant_system', 0),
        'Tritium Systems': detailed.get('tritium_systems', 0),
        'Instrumentation': detailed.get('instrumentation', 0),
    }
    
    major_categories = [
        {
            'name': 'Buildings & Site (CAS 21)',
            'category_id': 'buildings_site',
            'cost': detailed.get('cas_21_total', 0),
            'children_dict': {},  # Could add building subcategories if available
            'format_child': lambda k, v: (k.replace('_', ' ').title(), v)
        },
        {
            'name': 'Reactor Plant Equipment (CAS 22)',
            'category_id': 'reactor_equipment',
            'cost': detailed.get('cas_22_total', 0),
            'children_dict': cas_22_components,
            'format_child': lambda k, v: (k, v)
        },
        {
            'name': 'Turbine Plant (CAS 23)',
            'category_id': 'turbine',
            'cost': detailed.get('cas_23_turbine', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Electrical Equipment (CAS 24)',
            'category_id': 'electrical',
            'cost': detailed.get('cas_24_electrical', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Heat Rejection (CAS 26)',
            'category_id': 'cooling',
            'cost': detailed.get('cas_26_cooling', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Special Materials (CAS 27)',
            'category_id': 'materials',
            'cost': detailed.get('cas_27_materials', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Contingency (CAS 29)',
            'category_id': 'contingency',
            'cost': detailed.get('cas_29_contingency', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Indirect Costs (CAS 30)',
            'category_id': 'indirect_costs',
            'cost': detailed.get('cas_30_indirect', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': 'Pre-Construction (CAS 10)',
            'category_id': 'preconstruction',
            'cost': detailed.get('cas_10_preconstruction', 0),
            'children_dict': {},
            'format_child': None
        },
        {
            'name': "Owner's Costs (CAS 40)",
            'category_id': 'owners_costs',
            'cost': detailed.get('cas_40_owner_costs', 0),
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
                        'name': child_name,
                        'cost': child_cost,
                        'percent': (child_cost / total_epc * 100) if total_epc > 0 else 0,
                        'level': 1,
                        'expanded': False,
                        'children': []
                    })
        
        # Compute driver metadata for this category
        driver_info = _compute_category_drivers(category['name'], epc_results, config)
        
        tree.append({
            'name': category["name"],
            'category_id': category['category_id'],
            'cost': cat_cost,
            'percent': (cat_cost / total_epc * 100) if total_epc > 0 else 0,
            'level': 0,
            'expanded': False,
            'children': child_nodes,
            **driver_info  # Add drivers, maturity, tooltip, sensitivity_rank
        })
    
    return tree


def _compute_category_drivers(category_name, epc_results, config):
    """
    Determine key cost drivers for a category using heuristic logic.
    
    Returns dict with:
        - drivers: List of driver chip labels
        - tooltip: Explanation text
        - sensitivity_rank: 1-6 (1=highest reduction potential)
        - maturity: "High" | "Medium" | "Low"
    """
    if not config:
        return {
            'drivers': [],
            'tooltip': 'No configuration available',
            'sensitivity_rank': 6,
            'maturity': 'Medium'
        }
    
    drivers = []
    tooltip = ""
    sensitivity_rank = 5
    maturity = "Medium"
    
    # Buildings & Site
    if category_name == "Buildings & Site":
        drivers.append("MW scaling")
        net_mw = config.get('net_electric_power_mw', 1000)
        if net_mw > 1000:
            drivers.append("High MW")
        region_factor = config.get('_region_factor', 1.0)
        if region_factor > 1.0:
            drivers.append("Region factor")
        tooltip = "Scales with gross MW (square-cube law) and regional cost multiplier. Higher power = larger structures."
        sensitivity_rank = 3
        maturity = "High"
    
    # Interest During Construction
    elif category_name == "Interest During Construction":
        years = config.get('project_energy_start_year', 2030) - config.get('construction_start_year', 2024)
        leverage = config.get('input_debt_pct', 0.7)
        rate = config.get('loan_rate', 0.045)
        if years >= 6:
            drivers.append("Long build")
        if leverage >= 0.6:
            drivers.append("High leverage")
        drivers.append(f"{rate*100:.1f}% rate")
        tooltip = f"IDC accumulates over {years} years at {leverage*100:.0f}% debt, {rate*100:.1f}% rate. Sensitive to build duration and financing terms."
        sensitivity_rank = 1  # Top priority for reduction
        maturity = "High"
    
    # Reactor Equipment
    elif category_name == "Reactor Equipment":
        if config.get('override_q_eng'):
            q_val = config.get('manual_q_eng', 4.0)
            drivers.append(f"Q={q_val:.1f}")
        else:
            drivers.append("Auto Q")
        tech = config.get('power_method', 'MFE')
        drivers.append(tech)
        tooltip = "Reactor complexity driven by Q_eng (energy gain), blanket design, and confinement approach. Higher Q = simpler balance-of-plant."
        sensitivity_rank = 4
        maturity = "Medium"
    
    # Pre-Construction
    elif category_name == "Pre-Construction":
        drivers.append("Fixed costs")
        tooltip = "Licensing, permitting, site prep - largely independent of plant size. Dominated by regulatory requirements."
        sensitivity_rank = 6  # Low leverage
        maturity = "High"
    
    # Indirect Costs
    elif category_name == "Indirect Costs":
        drivers.append("% of direct")
        tooltip = "Engineering, construction management, owner's costs - typically 15-25% of direct costs."
        sensitivity_rank = 5
        maturity = "Medium"
    
    # Owner's Costs
    elif category_name == "Owner's Costs":
        drivers.append("Fixed admin")
        tooltip = "Owner oversight, startup, initial spare parts. Scales modestly with plant complexity."
        sensitivity_rank = 6
        maturity = "High"
    
    return {
        'drivers': drivers,
        'tooltip': tooltip,
        'sensitivity_rank': sensitivity_rank,
        'maturity': maturity
    }


def _compute_reduction_levers(epc_results, config):
    """
    Auto-generate top reduction recommendations based on cost drivers.
    
    Returns list of dicts with:
        - lever: Description of the action
        - impact_category: Which cost category is affected
        - est_savings: Absolute $ savings estimate
        - est_savings_pct: Percentage of total EPC
        - feasibility: "High" | "Medium" | "Low"
    """
    if not config:
        return []
    
    levers = []
    total_epc = epc_results.get('total_epc', 0)
    detailed = epc_results.get('detailed_result', {})
    
    # 1. IDC reduction via shorter build
    years = config.get('project_energy_start_year', 2030) - config.get('construction_start_year', 2024)
    if years > 5:
        idc_cost = detailed.get('idc', 0)
        # Heuristic: Each year saved reduces IDC by ~15%
        est_savings = idc_cost * 0.15
        levers.append({
            'lever': f"Reduce construction from {years}yr to {years-1}yr",
            'impact_category': "Interest During Construction",
            'est_savings': est_savings,
            'est_savings_pct': (est_savings / total_epc) * 100 if total_epc > 0 else 0,
            'feasibility': "Medium"
        })
    
    # 2. Region optimization
    region_factor = config.get('_region_factor', 1.0)
    if region_factor > 0.9:
        # Moving to low-cost region (e.g., SE Asia at 0.50)
        region_savings = total_epc * (region_factor - 0.65)
        levers.append({
            'lever': "Relocate to lower-cost region (e.g., Southeast Asia)",
            'impact_category': "All categories",
            'est_savings': region_savings,
            'est_savings_pct': (region_savings / total_epc) * 100 if total_epc > 0 else 0,
            'feasibility': "Low"
        })
    
    # 3. Q_eng optimization (if not overridden and low Q)
    if not config.get('override_q_eng'):
        # Assume Q improvement possible for MFE/IFE
        tech = config.get('power_method', 'MFE')
        if tech in ['MFE', 'IFE']:
            reactor_cost = detailed.get('reactor_equipment', 0)
            building_cost = detailed.get('building_total', 0)
            # Higher Q → less recirc power → smaller power supplies and cooling
            est_savings = (reactor_cost + building_cost) * 0.08
            levers.append({
                'lever': "Improve Q_eng through advanced confinement R&D",
                'impact_category': "Reactor Equipment + Buildings",
                'est_savings': est_savings,
                'est_savings_pct': (est_savings / total_epc) * 100 if total_epc > 0 else 0,
                'feasibility': "High"
            })
    
    # 4. Leverage optimization (reduce IDC via lower debt)
    leverage = config.get('input_debt_pct', 0.7)
    if leverage > 0.6:
        idc_cost = detailed.get('idc', 0)
        # Reducing debt by 10% → ~20% IDC reduction
        est_savings = idc_cost * 0.20
        levers.append({
            'lever': f"Reduce debt from {leverage*100:.0f}% to {(leverage-0.1)*100:.0f}%",
            'impact_category': "Interest During Construction",
            'est_savings': est_savings,
            'est_savings_pct': (est_savings / total_epc) * 100 if total_epc > 0 else 0,
            'feasibility': "Medium"
        })
    
    # 5. Modular construction (if high MW)
    net_mw = config.get('net_electric_power_mw', 1000)
    if net_mw > 1500:
        building_cost = detailed.get('building_total', 0)
        # Modular approach: ~12% building cost reduction via factory fabrication
        est_savings = building_cost * 0.12
        levers.append({
            'lever': "Adopt modular construction for Buildings & Site",
            'impact_category': "Buildings & Site",
            'est_savings': est_savings,
            'est_savings_pct': (est_savings / total_epc) * 100 if total_epc > 0 else 0,
            'feasibility': "High"
        })
    
    # Sort by savings potential, take top 5
    levers.sort(key=lambda x: x['est_savings'], reverse=True)
    return levers[:5]


def _get_benchmark_bands(net_mw, cost_per_kw, tech):
    """
    Fetch CATF P10/P50/P90 benchmarks and position current cost.
    
    Returns dict with:
        - catf_p10, catf_p50, catf_p90: Benchmark values in $/kW
        - current_position: Text description
        - percentile_estimate: Estimated percentile (0-100)
    """
    # Import CATF distribution
    try:
        from fusion_cashflow.core.power_to_epc import CATF_COST_DISTRIBUTION
        catf_p10 = CATF_COST_DISTRIBUTION['P10']
        catf_p50 = CATF_COST_DISTRIBUTION['P50']
        catf_p90 = CATF_COST_DISTRIBUTION['P90']
    except ImportError:
        # Fallback values if import fails
        catf_p10 = 8500
        catf_p50 = 12500
        catf_p90 = 18000
    
    # Estimate percentile position
    if cost_per_kw <= catf_p10:
        position = "Below P10 (highly optimistic)"
        percentile = 5
    elif cost_per_kw <= catf_p50:
        # Linear interpolation between P10 and P50
        percentile = 10 + 40 * (cost_per_kw - catf_p10) / (catf_p50 - catf_p10)
        position = f"~P{int(percentile)} (competitive)"
    elif cost_per_kw <= catf_p90:
        percentile = 50 + 40 * (cost_per_kw - catf_p50) / (catf_p90 - catf_p50)
        position = f"~P{int(percentile)} (moderate)"
    else:
        position = "Above P90 (conservative)"
        percentile = 95
    
    return {
        'catf_p10': catf_p10,
        'catf_p50': catf_p50,
        'catf_p90': catf_p90,
        'current_position': position,
        'percentile_estimate': percentile
    }





def _create_kpi_banner(total_epc, cost_per_kw, net_mw, gross_mw, benchmark_info):
    """Create single-line KPI banner matching main dashboard style with tooltips."""
    
    html = f"""
    <div style='display: flex; justify-content: space-between; align-items: center; font-size: 18px; font-weight: 800; white-space: nowrap; padding: 0 20px;'>
        <div style='margin-right: 30px;'>
            <span title='Engineering, Procurement, and Construction Cost - The total capital cost to build the fusion power plant' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>Total<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> ${total_epc/1e9:.2f}B</span>
        </div>
        <div style='margin-right: 30px;'>
            <span title='Capital Cost Per Kilowatt - The EPC cost divided by net electric capacity ($/kW)' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>Per kW<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> ${cost_per_kw:,.0f}</span>
        </div>
        <div style='margin-right: 30px;'>
            <span title='Net Electric Power - The power delivered to the grid after plant auxiliary loads' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>Net<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> {net_mw:.0f} MW</span>
        </div>
        <div>
            <span title='Gross Electric Power - The total power generated before auxiliary loads' 
                  style='cursor: help; background: rgba(160, 196, 255, 0.1); padding: 2px 4px; border-radius: 4px; transition: background 0.2s;'
                  onmouseover="this.style.background='rgba(160, 196, 255, 0.2)'" 
                  onmouseout="this.style.background='rgba(160, 196, 255, 0.1)'">
                <b>Gross<sup>?</sup>:</b>
            </span> 
            <span style='color:#ffffff;font-weight:800'> {gross_mw:.0f} MW</span>
        </div>
    </div>
    """
    
    return Div(
        text=html,
        sizing_mode='stretch_width',
        styles={
            "background": "#00375b",
            "border-radius": "16px",
            "padding": "18px 24px 12px 24px",
            "margin-bottom": "18px",
            "box-shadow": "0 2px 8px rgba(0,0,0,0.04)",
            "border": "1px solid rgba(255,255,255,0.1)",
            "color": "#ffffff",
            "font-family": "Inter, Helvetica, Arial, sans-serif",
        }
    )



def _create_reduction_levers_card(levers):
    """Create top reduction levers recommendation card."""
    
    if not levers:
        html = """
        <div style="background: rgba(255,255,255,0.06); border-radius: 12px; padding: 16px 20px; 
                    margin-bottom: 16px; border-left: 4px solid #60A5FA;
                    font-family: Inter, Helvetica, Arial, sans-serif;">
            <h3 style="margin: 0 0 8px 0; color: #ffffff; font-size: 14px; font-weight: 700;">
                🎯 Top EPC Reduction Levers
            </h3>
            <p style="margin: 0; color: #a0c4ff; font-size: 12px;">
                No configuration data available for lever analysis.
            </p>
        </div>
        """
    else:
        levers_html = ""
        for i, lever in enumerate(levers, 1):
            feasibility_color = {
                'High': '#10B981',
                'Medium': '#F59E0B',
                'Low': '#EF4444'
            }.get(lever['feasibility'], '#6B7280')
            
            levers_html += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; 
                        padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <div style="flex: 1;">
                    <div style="font-size: 13px; color: #ffffff; font-weight: 600; margin-bottom: 2px;">
                        {i}. {lever['lever']}
                    </div>
                    <div style="font-size: 11px; color: #a0c4ff;">
                        Impact: {lever['impact_category']} • 
                        Feasibility: <span style="color: {feasibility_color}; font-weight: 600;">{lever['feasibility']}</span>
                    </div>
                </div>
                <div style="text-align: right; margin-left: 16px;">
                    <div style="font-size: 16px; font-weight: 700; color: #10B981;">
                        -${lever['est_savings']/1e9:.2f}B
                    </div>
                    <div style="font-size: 11px; color: #a0c4ff;">
                        ({lever['est_savings_pct']:.1f}%)
                    </div>
                </div>
            </div>
            """
        
        html = f"""
        <div style="background: rgba(255,255,255,0.06); border-radius: 12px; padding: 16px 20px; 
                    margin-bottom: 16px; border-left: 4px solid #60A5FA;
                    font-family: Inter, Helvetica, Arial, sans-serif;">
            <h3 style="margin: 0 0 12px 0; color: #ffffff; font-size: 14px; font-weight: 700;">
                🎯 Top EPC Reduction Levers
            </h3>
            {levers_html}
        </div>
        """
    
    return Div(text=html, sizing_mode='stretch_width')


def _create_bokeh_accordion(tree_data):
    """Create Bokeh-native accordion using Button widgets with CustomJS callbacks."""
    
    # Maturity emoji mapping
    maturity_emoji = {
        'High': '🟢',
        'Medium': '🟡',
        'Low': '🔴'
    }
    
    # Title
    title_div = Div(
        text="<h3 style='color: #ffffff; font-size: 16px; font-weight: 700; margin: 20px 0 12px 0; font-family: Inter, Helvetica, Arial, sans-serif;'>Cost Categories (Click to Expand)</h3>",
        sizing_mode='stretch_width'
    )
    
    # Container for all accordion rows
    accordion_rows = []
    
    for i, node in enumerate(tree_data):
        name = node['name']
        cost_b = node['cost'] / 1e9
        percent = node['percent']
        drivers = node.get('drivers', [])
        maturity = node.get('maturity', 'Medium')
        children = node.get('children', [])
        
        has_children = len(children) > 0
        
        # Expand button (only if has children)
        if has_children:
            expand_btn = Button(
                label="▶",
                width=30,
                height=30,
                button_type="light",
                styles={'font-size': '14px', 'padding': '4px'}
            )
        else:
            expand_btn = Div(text="<div style='width: 30px;'></div>", width=30, height=30)
        
        # Driver chips HTML
        drivers_html = ""
        if drivers:
            chips = " ".join([f'<span style="background: rgba(96,165,250,0.2); color: #60A5FA; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 4px;">{d}</span>' for d in drivers[:3]])
            drivers_html = f'<div style="display: flex; gap: 4px; flex-wrap: wrap; margin-left: 12px;">{chips}</div>'
        
        # Category info Div
        info_div = Div(
            text=f"""
            <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                <span style="font-weight: 600; color: #ffffff; font-size: 14px;">{name}</span>
                {drivers_html}
            </div>
            """,
            sizing_mode='stretch_width',
            styles={'display': 'flex', 'align-items': 'center'}
        )
        
        # Cost and percent Divs
        cost_div = Div(
            text=f"<div style='font-weight: 700; color: #60A5FA; font-size: 14px; text-align: right; min-width: 80px;'>${cost_b:.2f}B</div>",
            width=80
        )
        
        percent_div = Div(
            text=f"<div style='color: #60A5FA; font-weight: 700; font-size: 14px; text-align: right; min-width: 60px;'>{percent:.1f}%</div>",
            width=60
        )
        
        maturity_div = Div(
            text=f"<div style='font-size: 16px; margin-left: 8px;'>{maturity_emoji.get(maturity, '🟡')}</div>",
            width=30
        )
        
        # Create row for this category
        category_row = BokehRow(
            expand_btn,
            info_div,
            cost_div,
            percent_div,
            maturity_div,
            sizing_mode='stretch_width',
            styles={
                'padding': '12px 16px',
                'margin': '6px 0',
                'border-radius': '8px',
                'border': '1px solid rgba(255,255,255,0.1)',
                'background': 'rgba(255,255,255,0.06)'
            }
        )
        
        # Children container (initially hidden)
        if has_children:
            children_divs = []
            for child in children:
                child_name = child['name']
                child_cost_b = child['cost'] / 1e9
                child_pct = child['percent']
                
                child_div = Div(
                    text=f"""
                    <div style="padding: 8px 12px; margin: 4px 0; background: rgba(255,255,255,0.04); 
                                border-left: 3px solid #60A5FA; border-radius: 4px; 
                                display: flex; justify-content: space-between; font-size: 12px; color: #e0e0e0;">
                        <span>{child_name}</span>
                        <span style="font-weight: 600; color: #60A5FA;">${child_cost_b:.3f}B ({child_pct:.1f}%)</span>
                    </div>
                    """,
                    sizing_mode='stretch_width'
                )
                children_divs.append(child_div)
            
            children_container = BokehColumn(
                *children_divs,
                visible=False,  # Initially hidden
                sizing_mode='stretch_width',
                styles={'padding-left': '46px', 'margin-top': '8px'}
            )
            
            # CustomJS callback to toggle visibility
            callback = CustomJS(
                args=dict(children=children_container, btn=expand_btn),
                code="""
                if (children.visible) {
                    children.visible = false;
                    btn.label = '▶';
                } else {
                    children.visible = true;
                    btn.label = '▼';
                }
                """
            )
            
            # Attach callback to button
            expand_btn.js_on_click(callback)
            
            # Add both row and children to accordion
            accordion_rows.append(category_row)
            accordion_rows.append(children_container)
        else:
            # Just add the row
            accordion_rows.append(category_row)
    
    # Wrap all rows in a container
    accordion_container = BokehColumn(
        title_div,
        *accordion_rows,
        sizing_mode='stretch_width',
        styles={
            'background': 'rgba(255,255,255,0.04)',
            'border-radius': '12px',
            'padding': '12px',
            'box-shadow': '0 2px 8px rgba(0,0,0,0.2)',
            'border': '1px solid rgba(255,255,255,0.1)'
        }
    )
    
    return accordion_container


def _create_detail_panel(category_node, config, epc_results):
    """Create dynamic detail panel showing selected category information."""
    
    if not category_node:
        html = """
        <div style="background: rgba(255,255,255,0.06); border-radius: 12px; padding: 20px; 
                    margin-top: 16px; font-family: Inter, Helvetica, Arial, sans-serif;
                    border: 1px solid rgba(255,255,255,0.1);">
            <p style="color: #a0c4ff; font-size: 13px; margin: 0;">
                Click a category above to view detailed cost drivers and analysis.
            </p>
        </div>
        """
        return Div(text=html, sizing_mode='stretch_width')
    
    name = category_node['name']
    cost_b = category_node['cost'] / 1e9
    percent = category_node['percent']
    drivers = category_node.get('drivers', [])
    maturity = category_node.get('maturity', 'Medium')
    tooltip = category_node.get('tooltip', 'No additional information available.')
    sensitivity_rank = category_node.get('sensitivity_rank', 6)
    
    # Sensitivity description
    sensitivity_desc = {
        1: "Very High - Top priority for cost reduction",
        2: "High - Significant reduction potential",
        3: "Medium-High - Moderate reduction opportunity",
        4: "Medium - Some reduction potential",
        5: "Medium-Low - Limited reduction opportunity",
        6: "Low - Minimal reduction potential"
    }.get(sensitivity_rank, "Unknown")
    
    # Driver bullets
    drivers_html = ""
    if drivers:
        bullets = "".join([f"<li>{d}</li>" for d in drivers])
        drivers_html = f"<ul style='margin: 8px 0; padding-left: 24px;'>{bullets}</ul>"
    
    html = f"""
    <div style="background: rgba(255,255,255,0.06); border-radius: 12px; padding: 20px; 
                margin-top: 16px; font-family: Inter, Helvetica, Arial, sans-serif;
                border: 1px solid rgba(255,255,255,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div>
                <h3 style="margin: 0 0 4px 0; color: #ffffff; font-size: 16px; font-weight: 700;">
                    {name}
                </h3>
                <div style="font-size: 13px; color: #a0c4ff;">
                    Cost Maturity: <b style="color: #60A5FA;">{maturity}</b>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 24px; font-weight: 700; color: #60A5FA;">
                    ${cost_b:.2f}B
                </div>
                <div style="font-size: 14px; color: #a0c4ff; font-weight: 600;">
                    {percent:.1f}% of total
                </div>
            </div>
        </div>
        
        <div style="margin-bottom: 16px;">
            <h4 style="margin: 0 0 8px 0; color: #60A5FA; font-size: 13px; font-weight: 700;">
                Cost Drivers:
            </h4>
            <p style="margin: 0; font-size: 13px; color: #e0e0e0; line-height: 1.5;">
                {tooltip}
            </p>
            {drivers_html}
        </div>
        
        <div style="padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; font-size: 12px;">
                <div>
                    <b style="color: #60A5FA;">Reduction Sensitivity:</b> <span style="color: #e0e0e0;">{sensitivity_desc}</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    return Div(text=html, sizing_mode='stretch_width')


def _create_horizontal_bar_chart(tree_data, total_epc):
    """Create horizontal bar chart showing cost distribution with brand colors."""
    
    # Extract data
    categories = []
    costs_b = []
    percents = []
    colors_list = []
    
    # Brand color palette - primary blue with complementary colors
    colors = ['#60A5FA', '#00375b', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899']
    
    for i, node in enumerate(tree_data):
        if node['cost'] > 0:
            categories.append(node['name'])
            costs_b.append(node['cost'] / 1e9)
            percents.append(node['percent'])
            colors_list.append(colors[i % len(colors)])
    
    # Sort by cost descending
    sorted_indices = np.argsort(costs_b)[::-1]
    categories = [categories[i] for i in sorted_indices]
    costs_b = [costs_b[i] for i in sorted_indices]
    percents = [percents[i] for i in sorted_indices]
    colors_list = [colors_list[i] for i in sorted_indices]
    
    # Create source
    source = ColumnDataSource(data=dict(
        categories=categories,
        costs=costs_b,
        percents=percents,
        colors=colors_list
    ))
    
    # Create figure
    p = figure(
        y_range=categories,
        height=max(300, len(categories) * 60),
        width=800,
        toolbar_location=None,
        title="",
        min_border=0,
        min_border_left=10,
        min_border_right=10
    )
    
    # Add bars
    p.hbar(
        y='categories',
        right='costs',
        height=0.6,
        source=source,
        color='colors',
        alpha=0.85
    )
    
    # Styling with dark theme
    p.background_fill_color = "#00375b"
    p.border_fill_color = "#001e3c"
    p.outline_line_color = None
    p.xaxis.axis_label = "Cost (Billions $)"
    p.xaxis.axis_label_text_font_style = "bold"
    p.xaxis.axis_label_text_color = "#ffffff"
    p.xaxis.axis_label_text_font_size = "12pt"
    p.xaxis.major_label_text_color = "#e0e0e0"
    p.xaxis.axis_line_color = "rgba(255,255,255,0.2)"
    p.xaxis.major_tick_line_color = "rgba(255,255,255,0.2)"
    p.xaxis.minor_tick_line_color = None
    p.yaxis.major_label_text_font_style = "bold"
    p.yaxis.major_label_text_color = "#ffffff"
    p.yaxis.major_label_text_font_size = "11pt"
    p.yaxis.axis_line_color = "rgba(255,255,255,0.2)"
    p.yaxis.major_tick_line_color = "rgba(255,255,255,0.2)"
    p.yaxis.minor_tick_line_color = None
    p.grid.grid_line_color = "rgba(255,255,255,0.1)"
    p.grid.grid_line_alpha = 0.3
    p.xgrid.grid_line_color = "rgba(255,255,255,0.1)"
    p.xgrid.grid_line_alpha = 0.2
    
    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Category", "@categories"),
        ("Cost", "$@costs{0.00}B"),
        ("Percent", "@percents{0.0}%")
    ])
    p.add_tools(hover)
    
    return p


def _create_modern_pie_chart(tree_data, total_epc):
    """
    Create square pie chart using same percentages as tree for consistency.
    """
    # Extract top-level categories only (filter out zero-cost items)
    categories = []
    costs = []
    percents = []
    for node in tree_data:
        if node['cost'] > 0:
            categories.append(node['name'])
            costs.append(node['cost'])
            percents.append(node['percent'])  # Use same percent as tree
    
    # Sort by cost descending
    sorted_indices = np.argsort(costs)[::-1]
    categories = [categories[i] for i in sorted_indices]
    costs = [costs[i] for i in sorted_indices]
    percents = [percents[i] for i in sorted_indices]
    
    # Calculate angles from the consistent percentages
    angles = [pct / 100 * 2 * np.pi for pct in percents]
    
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
    
    # Build wedge data - start at top and go clockwise
    start_angle = 0
    for i, (cat, cost, pct, angle) in enumerate(zip(categories, costs, percents, angles)):
        end_angle = start_angle + angle
        wedge_data['start_angle'].append(start_angle)
        wedge_data['end_angle'].append(end_angle)
        wedge_data['color'].append(colors[i])
        wedge_data['category'].append(cat)
        wedge_data['cost'].append(f"${cost/1e9:.2f}B")
        wedge_data['percent'].append(f"{pct:.1f}%")
        start_angle = end_angle
    
    source = ColumnDataSource(wedge_data)
    
    # Create square figure without title (title is in separate Div above)
    p = figure(
        width=500,
        height=500,
        title="",
        toolbar_location=None,
        x_range=(-1.2, 1.2),
        y_range=(-1.2, 1.2),
        min_border=0,
        min_border_top=0,
        min_border_left=0,
        min_border_right=0,
        min_border_bottom=0
    )
    
    # Remove visible border for modern look
    p.outline_line_color = None
    
    # Draw pie slices using data source
    wedges = p.wedge(
        x=0, y=0,
        radius=1,
        start_angle='start_angle',
        end_angle='end_angle',
        color='color',
        alpha=0.8,
        line_color='white',
        line_width=2,
        source=source
    )
    
    # Add hover tool
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
    legend.label_text_font_size = "11pt"
    legend.label_text_font = "Inter"
    p.add_layout(legend, 'right')
    
    # Style title - minimal space above chart
    p.title.text_font_size = "15pt"
    p.title.text_font = "Inter"
    p.title.text_color = "#00375b"
    p.title.align = "center"
    p.title.offset = -10
    p.title.text_font_style = "normal"
    
    # Remove axes and minimize whitespace
    p.axis.visible = False
    p.grid.visible = False
    p.min_border = 20
    
    return p


def update_costing_panel(epc_results, config=None):
    """
    Update costing panel with new simulation results.
    
    Args:
        epc_results: Updated EPC results dictionary
        config: Updated configuration dictionary (optional)
    
    Returns:
        Updated panel layout
    """
    return create_costing_panel(epc_results, config)

