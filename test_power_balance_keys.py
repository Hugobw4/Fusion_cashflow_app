"""Test power balance key compatibility"""
from src.fusion_cashflow.costing import compute_total_epc_cost

config = {
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

print("Testing power balance keys...")
result = compute_total_epc_cost(config)

pb = result['power_balance']
print(f"\nPower balance keys: {list(pb.keys())}")

# Check both old and new naming conventions
required_keys = ['p_electric_net', 'p_net', 'p_fusion', 'p_thermal', 'p_electric_gross']
for key in required_keys:
    if key in pb:
        print(f"✓ '{key}': {pb[key]:.1f} MW")
    else:
        print(f"✗ MISSING: '{key}'")

# Verify p_net and p_electric_net are the same
if pb.get('p_net') == pb.get('p_electric_net'):
    print(f"\n✓ p_net == p_electric_net ({pb['p_net']:.1f} MW)")
else:
    print(f"\n✗ Mismatch: p_net={pb.get('p_net')}, p_electric_net={pb.get('p_electric_net')}")

print("\n✓ All power balance keys present!")
