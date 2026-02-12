"""
Quick test of the new PyFECONS adapter.

This script tests that the adapter successfully:
1. Accepts legacy config dict
2. Runs calculations without errors
3. Returns expected output keys
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Direct import to avoid loading full package (which has missing deps)
    from fusion_cashflow.costing.adapter import compute_total_epc_cost
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test config (minimal tokamak)
test_config = {
    # Power
    'thermal_power_mw': 2000.0,
    'net_electric_mw': 500.0,
    'q_plasma': 10.0,
    'heating_power_mw': 50.0,
    
    # Reactor
    'reactor_type': 'tokamak',
    'fuel_type': 'DT',
    'major_radius': 3.0,
    'minor_radius': 1.0,
    'elongation': 1.7,
    
    # Components
    'first_wall_thickness': 0.02,
    'blanket_thickness': 0.50,
    'shield_thickness': 0.50,
    
    # Materials
    'first_wall_material': 'W',
    'blanket_structural_material': 'FS',
    'blanket_coolant': 'H2O',
    'blanket_multiplier': 'Be',
    
    # Magnets
    'magnet_type': 'HTS',
    'n_tf_coils': 18,
    
    # Economics
    'thermal_efficiency': 0.40,
    'neutron_multiplication': 1.15,
    'is_foak': False,
    'lsa_level': 1,
    'availability': 0.75,
}

print("\nRunning compute_total_epc_cost()...")
try:
    results = compute_total_epc_cost(test_config)
    print("✓ Calculation completed")
except Exception as e:
    print(f"✗ Calculation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check required keys
required_keys = [
    'power_balance', 'q_eng', 'volumes',
    'cas_21_total', 'cas_22_total', 'cas_2201', 'cas_2203',
    'total_capital_cost', 'total_epc_cost',
    'cost_per_kw_net', 'epc_per_kw_net'
]

print("\nValidating output keys:")
missing = []
for key in required_keys:
    if key in results:
        print(f"  ✓ {key}")
    else:
        print(f"  ✗ {key} MISSING")
        missing.append(key)

if missing:
    print(f"\n✗ Missing keys: {missing}")
    sys.exit(1)

# Print summary
print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
print(f"Net Electric Power:    {results['power_balance']['p_net']:.1f} MW")
print(f"Engineering Q:         {results['q_eng']:.2f}")
print(f"Total Capital Cost:    ${results['total_capital_cost']:.1f} M")
print(f"  CAS 21 (Buildings):  ${results['cas_21_total']:.1f} M")
print(f"  CAS 22 (Reactor):    ${results['cas_22_total']:.1f} M")
print(f"Cost per kW:           ${results['cost_per_kw_net']:.0f}/kW")
if 'lcoe_usd_per_mwh' in results:
    print(f"LCOE:                  ${results['lcoe_usd_per_mwh']:.1f}/MWh")
print("="*60)

print("\n✓ All tests passed!")
