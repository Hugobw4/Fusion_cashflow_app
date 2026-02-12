"""Test material sensitivity using dashboard config keys"""
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
    'first_wall_material': 'Tungsten',
    'magnet_type': 'HTS',
    'availability': 0.85,
}

# Test different blanket types (as dashboard sends)
print("=== Testing Blanket Type Changes (Dashboard Keys) ===\n")
blanket_types = [
    'Solid Breeder (Li2TiO3)',
    'Solid Breeder (Li4SiO4)',
    'Flowing Liquid Breeder (PbLi)',
]

results = []
for btype in blanket_types:
    config = base_config.copy()
    config['blanket_type'] = btype
    config['structure_material'] = 'Ferritic Steel (FMS)'  # Keep constant
    
    result = compute_total_epc_cost(config)
    blanket_cost = result.get('blanket', 0)
    shield_cost = result.get('shield', 0)
    total_mat = result.get('firstwall', 0) + blanket_cost + shield_cost
    results.append((btype, blanket_cost, total_mat))
    print(f"{btype:35s} → Blanket: ${blanket_cost:6.1f}M  Total: ${total_mat:6.1f}M")

# Test different structure materials
print("\n=== Testing Structure Material Changes ===\n")
structure_materials = [
    'Stainless Steel (SS)',
    'Ferritic Steel (FMS)',
    'Vanadium',
]

for smat in structure_materials:
    config = base_config.copy()
    config['blanket_type'] = 'Solid Breeder (Li4SiO4)'  # Keep constant
    config['structure_material'] = smat
    
    result = compute_total_epc_cost(config)
    blanket_cost = result.get('blanket', 0)
    shield_cost = result.get('shield', 0)
    total_mat = result.get('firstwall', 0) + blanket_cost + shield_cost
    print(f"{smat:35s} → Blanket: ${blanket_cost:6.1f}M  Shield: ${shield_cost:6.1f}M  Total: ${total_mat:6.1f}M")

# Check if costs changed
if len(results) > 1:
    blanket_costs = [r[1] for r in results]
    total_costs = [r[2] for r in results]
    if len(set(blanket_costs)) > 1:
        print(f"\n✓ Blanket Type DOES affect cost!")
        print(f"  Range: ${min(blanket_costs):.1f}M - ${max(blanket_costs):.1f}M")
    else:
        print(f"\n✗ Blanket Type does NOT affect cost (all ${blanket_costs[0]:.1f}M)")
    
    if len(set(total_costs)) > 1:
        print(f"✓ Total material cost varies: ${min(total_costs):.1f}M - ${max(total_costs):.1f}M")
