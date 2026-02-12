"""Test Phase 3.1: Detailed magnet costing with HTS/LTS sensitivity."""
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
    'blanket_type': 'Solid Breeder (Li4SiO4)',
    'structure_material': 'Ferritic Steel (FMS)',
    'n_tf_coils': 12,
    'availability': 0.85,
}

print("=" * 80)
print("PHASE 3.1 TEST: Material-Based Magnet Costing")
print("=" * 80)

# Test HTS vs LTS vs Copper
magnet_types = ['HTS', 'LTS', 'Copper']
results = []

for mag_type in magnet_types:
    config = base_config.copy()
    config['magnet_type'] = mag_type
    
    result = compute_total_epc_cost(config)
    magnet_cost = result.get('cas_2203', 0)
    total_epc = result.get('total_epc_cost', 0)
    magnet_pct = (magnet_cost / total_epc * 100) if total_epc > 0 else 0
    
    results.append((mag_type, magnet_cost, total_epc, magnet_pct))
    print(f"\n{mag_type:10s} magnets:")
    print(f"  Magnet Cost (CAS 22.03):  ${magnet_cost:6.1f} M")
    print(f"  Total EPC Cost:           ${total_epc:6.1f} M")
    print(f"  Magnets as % of EPC:      {magnet_pct:5.1f}%")

# Check cost variation
magnet_costs = [r[1] for r in results]
min_cost = min(magnet_costs)
max_cost = max(magnet_costs)
cost_range = max_cost - min_cost
cost_variation_pct = (cost_range / min_cost * 100) if min_cost > 0 else 0

print("\n" + "=" * 80)
print("SENSITIVITY ANALYSIS")
print("=" * 80)
print(f"Magnet cost range: ${min_cost:.1f}M - ${max_cost:.1f}M")
print(f"Cost variation: ${cost_range:.1f}M ({cost_variation_pct:.1f}%)")

if cost_variation_pct > 10:
    print("\n✓ SUCCESS: Magnet type affects cost significantly!")
    print(f"  Cost varies by {cost_variation_pct:.0f}% between magnet types")
elif cost_variation_pct > 1:
    print("\n✓ GOOD: Magnet type affects cost moderately")
    print(f"  Cost varies by {cost_variation_pct:.1f}% between magnet types")
else:
    print("\n✗ FAILED: Magnet type does NOT affect cost")
    print("  All magnet types have same cost - calculation may not be working")

# Compare to old system 
print("\n" + "=" * 80)
print("COMPARISON TO OLD SYSTEM")
print("=" * 80)
print("Old simplified costing: ~100 $/kW flat rate")
p_thermal = base_config['thermal_power_mw']
old_estimate = p_thermal * 100.0 / 1000.0  # Convert to M$
print(f"Old estimate: ${old_estimate:.1f} M for {p_thermal} MW thermal")
print(f"")
for mag_type, cost, _, _ in results:
    diff = cost - old_estimate
    diff_pct = (diff / old_estimate * 100)
    print(f"New {mag_type:10s} cost: ${cost:6.1f}M  (old: ${old_estimate:.1f}M, diff: {diff_pct:+5.1f}%)")

print("\n" + "=" * 80)
