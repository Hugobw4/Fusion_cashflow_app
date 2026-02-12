"""Test if changing materials affects estimated costs"""
from src.fusion_cashflow.costing import compute_total_epc_cost

base_config = {
    'thermal_power_mw': 2000,
    'net_electric_mw': 500,
    'q_plasma': 10,
    'reactor_type': 'tokamak',
    'fuel_type': 'DT',
    'major_radius': 3.0,
    'minor_radius': 1.0,
    'elongation': 1.7,
    'blanket_thickness': 0.5,
    'shield_thickness': 0.6,
    'first_wall_material': 'tungsten',
    'magnet_type': 'HTS',
    'availability': 0.85,
}

# Test different blanket materials
blanket_materials = ['lithium orthosilicate', 'lithium', 'liquid lithium', 'flibe']
print("=== Testing Blanket Material Changes ===\n")

results = []
for mat in blanket_materials:
    config = base_config.copy()
    config['blanket_material'] = mat
    config['shield_material'] = 'stainless steel'  # Keep constant
    
    try:
        result = compute_total_epc_cost(config)
        blanket_cost = result.get('blanket', 0)
        total_mat = result.get('firstwall', 0) + blanket_cost + result.get('shield', 0)
        results.append((mat, blanket_cost, total_mat))
        print(f"{mat:25s} → Blanket: ${blanket_cost:6.1f}M  Total: ${total_mat:6.1f}M")
    except Exception as e:
        print(f"{mat:25s} → ERROR: {e}")

# Test different structure materials
structure_materials = ['stainless steel', 'ferritic steel', 'inconel', 'vanadium']
print("\n=== Testing Structure Material Changes ===\n")

for mat in structure_materials:
    config = base_config.copy()
    config['blanket_material'] = 'lithium orthosilicate'  # Keep constant
    config['shield_material'] = mat
    
    try:
        result = compute_total_epc_cost(config)
        shield_cost = result.get('shield', 0)
        total_mat = result.get('firstwall', 0) + result.get('blanket', 0) + shield_cost
        print(f"{mat:25s} → Shield: ${shield_cost:6.1f}M  Total: ${total_mat:6.1f}M")
    except Exception as e:
        print(f"{mat:25s} → ERROR: {e}")

# Check if costs changed
if len(results) > 1:
    blanket_costs = [r[1] for r in results]
    if len(set(blanket_costs)) > 1:
        print(f"\n✓ Blanket material DOES affect cost (range: ${min(blanket_costs):.1f}M - ${max(blanket_costs):.1f}M)")
    else:
        print(f"\n✗ Blanket material does NOT affect cost (all ${blanket_costs[0]:.1f}M)")
