"""Comprehensive test: verify all dashboard inputs are mapped to costing system."""
from src.fusion_cashflow.costing import compute_total_epc_cost
from src.fusion_cashflow.costing.adapter import _config_to_costing_data
import inspect

# ===== PART 1: Configuration Keys That Dashboard Sends =====
# Based on power_to_epc.py lines 98-172

DASHBOARD_COSTING_KEYS = {
    # Basic parameters (from power_to_epc.py)
    'reactor_type': ['tokamak', 'mirror', 'laser'],
    'fuel_type': ['DT', 'DD', 'DHe3', 'pB11'],
    'is_foak': [True, False],
    
    # Power parameters
    'thermal_power_mw': [500, 2000, 5000],
    'net_electric_mw': [100, 500, 1000],
    'heating_power_mw': [50, 100, 200],
    'thermal_efficiency': [0.35, 0.46, 0.55],
    
    # Material selections
    'first_wall_material': ['Tungsten', 'tungsten', 'W', 'Beryllium'],
    'blanket_type': [
        'Solid Breeder (Li2TiO3)',
        'Solid Breeder (Li4SiO4)',
        'Flowing Liquid Breeder (PbLi)',
    ],
    'structure_material': [
        'Stainless Steel (SS)',
        'Ferritic Steel (FMS)',
        'Vanadium',
    ],
    
    # Magnet parameters
    'magnet_type': ['HTS', 'LTS', 'Copper'],
    'n_tf_coils': [12, 16, 18],
    
    # Geometry - tokamak
    'major_radius': [2.0, 3.0, 5.0],
    'minor_radius': [0.5, 1.0, 1.5],
    'elongation': [1.5, 1.7, 2.0],
    'blanket_thickness': [0.3, 0.5, 0.8],
    'shield_thickness': [0.4, 0.6, 1.0],
    'first_wall_thickness': [0.01, 0.02, 0.03],
    
    # Geometry - mirror/IFE
    'chamber_length': [5.0, 10.0, 15.0],
    'chamber_radius': [3.0, 5.0, 8.0],
    
    # Physics
    'q_plasma': [5, 10, 20],
    'availability': [0.75, 0.85, 0.95],
    'neutron_multiplication': [1.1, 1.15, 1.2],
    
    # Blanket configuration
    'blanket_coolant': ['H2O', 'He', 'FLiBe', 'PbLi'],
    'blanket_multiplier': ['Be', 'Pb', 'None'],
}

# Keys we KNOW the adapter should handle
EXPECTED_ADAPTER_KEYS = [
    'thermal_power_mw',
    'net_electric_mw', 
    'q_plasma',
    'reactor_type',
    'fuel_type',
    'is_foak',
    'availability',
    'heating_power_mw',
    'neutron_multiplication',
    'thermal_efficiency',
    'major_radius',
    'minor_radius', 
    'elongation',
    'chamber_length',
    'first_wall_thickness',
    'blanket_thickness',
    'shield_thickness',
    'first_wall_material',
    'blanket_type',
    'structure_material',
    'blanket_structural_material',
    'shield_material',
    'blanket_coolant',
    'blanket_multiplier',
    'magnet_type',
    'n_tf_coils',
]

# ===== PART 2: Check What Adapter Actually Looks For =====
print("=" * 80)
print("COSTING INPUT MAPPING VALIDATION TEST")
print("=" * 80)

# Get adapter source code
adapter_source = inspect.getsource(_config_to_costing_data)

# Find all config lookups
import re
config_accesses = re.findall(r"config(?:\.get)?\[['\"]([\w_]+)['\"]\]", adapter_source)
unique_keys = sorted(set(config_accesses))

print(f"\n✓ Adapter checks for {len(unique_keys)} unique config keys:")
for key in unique_keys:
    print(f"  - {key}")

# ===== PART 3: Check for Missing Mappings =====
print("\n" + "=" * 80)
print("COVERAGE CHECK: Are all expected keys handled?")
print("=" * 80)

missing_keys = []
for key in EXPECTED_ADAPTER_KEYS:
    if key not in unique_keys:
        missing_keys.append(key)
        print(f"  ✗ MISSING: '{key}' is NOT checked by adapter")
    else:
        print(f"  ✓ '{key}' is handled")

if missing_keys:
    print(f"\n⚠ WARNING: {len(missing_keys)} expected keys are not mapped!")
else:
    print(f"\n✓ All {len(EXPECTED_ADAPTER_KEYS)} expected keys are mapped!")

# ===== PART 4: Functional Test - Verify Changes Propagate =====
print("\n" + "=" * 80)
print("FUNCTIONAL TEST: Do input changes affect outputs?")
print("=" * 80)

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
    'magnet_type': 'HTS',
    'n_tf_coils': 12,
    'availability': 0.85,
}

# Run baseline
baseline = compute_total_epc_cost(base_config)
baseline_cost = baseline['total_epc_cost']
baseline_blanket = baseline.get('blanket', 0)

print(f"\nBaseline: Total EPC = ${baseline_cost:.1f}M, Blanket = ${baseline_blanket:.1f}M")

# Test sensitivity to key parameters
tests = [
    ('thermal_power_mw', 4000, 'power'),
    ('major_radius', 5.0, 'geometry'),
    ('blanket_type', 'Solid Breeder (Li2TiO3)', 'materials'),
    ('structure_material', 'Vanadium', 'materials'),
    ('magnet_type', 'LTS', 'magnets'),
    ('q_plasma', 20, 'physics'),
]

changes_detected = 0
for key, value, category in tests:
    test_config = base_config.copy()
    test_config[key] = value
    
    result = compute_total_epc_cost(test_config)
    test_cost = result['total_epc_cost']
    test_blanket = result.get('blanket', 0)
    
    cost_change = abs(test_cost - baseline_cost) / baseline_cost * 100
    
    if cost_change > 0.1:  # >0.1% change
        print(f"  ✓ {category:12s} | {key:25s} = {value:30} → ΔCost: {cost_change:5.1f}%")
        changes_detected += 1
    else:
        print(f"  ✗ {category:12s} | {key:25s} = {value:30} → NO CHANGE")

print(f"\n{'='*80}")
if changes_detected == len(tests):
    print(f"✓ ALL TESTS PASSED: {changes_detected}/{len(tests)} input changes affected outputs")
elif changes_detected > len(tests) * 0.7:
    print(f"⚠ MOSTLY PASSED: {changes_detected}/{len(tests)} input changes affected outputs")
else:
    print(f"✗ FAILED: Only {changes_detected}/{len(tests)} input changes affected outputs")

print(f"{'='*80}\n")

# ===== PART 5: Summary =====
print("SUMMARY:")
print(f"  • Adapter handles {len(unique_keys)} config keys")
print(f"  • Expected {len(EXPECTED_ADAPTER_KEYS)} keys, missing {len(missing_keys)}")
print(f"  • {changes_detected}/{len(tests)} functional tests passed")

if not missing_keys and changes_detected == len(tests):
    print("\n✓✓✓ COMPLETE SUCCESS: Full mapping coverage and functional validation!")
elif not missing_keys:
    print("\n✓ GOOD: All keys mapped, but some changes don't propagate")
else:
    print("\n⚠ INCOMPLETE: Some dashboard inputs may be ignored")
