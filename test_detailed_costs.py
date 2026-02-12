"""Test detailed cost breakdown"""
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
    'blanket_material': 'lithium orthosilicate',
    'shield_material': 'stainless steel',
    'magnet_type': 'HTS',
    'availability': 0.85,
}

print("Testing detailed cost breakdown...\n")
result = compute_total_epc_cost(config)

# Check component costs
print("=== CAS 22.01.01 - First Wall/Blanket/Shield ===")
print(f"First Wall:  ${result.get('firstwall', 0):.1f} M")
print(f"Blanket:     ${result.get('blanket', 0):.1f} M")
print(f"Shield:      ${result.get('shield', 0):.1f} M")
print(f"Divertor:    ${result.get('divertor', 0):.1f} M")
print(f"CAS 2201:    ${result.get('cas_2201', 0):.1f} M")

print("\n=== CAS 21 - Buildings ===")
print(f"Reactor Building:  ${result.get('building_reactor_building', 0):.1f} M")
print(f"Turbine Building:  ${result.get('building_turbine_building', 0):.1f} M")
print(f"Auxiliary Bldgs:   ${result.get('building_auxiliary_buildings', 0):.1f} M")
print(f"CAS 21 Total:      ${result.get('cas_21_total', 0):.1f} M")

print("\n=== Other CAS 22 Components ===")
print(f"Magnets (2203):       ${result.get('cas_2203', 0):.1f} M")
print(f"Heating (2204):       ${result.get('heating_systems', 0):.1f} M")
print(f"Coolant (2202):       ${result.get('coolant_system', 0):.1f} M")
print(f"Vacuum (2205):        ${result.get('vacuum_system', 0):.1f} M")

material_sum = result.get('firstwall', 0) + result.get('blanket', 0) + result.get('shield', 0)
print(f"\n✓ Material cost sum: ${material_sum:.1f} M")

if material_sum > 0:
    print("✓ Material costs are non-zero!")
else:
    print("✗ Material costs are still zero - check calculation")
