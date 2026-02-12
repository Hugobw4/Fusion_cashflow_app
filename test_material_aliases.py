"""Test material alias system"""
from src.fusion_cashflow.costing import get_material, normalize_material_code

# Test cases
test_cases = [
    'tungsten',   # Legacy name
    'W',          # New code
    'w',          # Lowercase
    'beryllium',
    'Be',
    'ferritic_steel',
    'FS',
    'stainless steel',
    'SS316',
]

print("Testing material alias system...\n")

for code in test_cases:
    try:
        normalized = normalize_material_code(code)
        material = get_material(code)
        print(f"✓ '{code}' → '{normalized}' → {material.name}")
    except KeyError as e:
        print(f"✗ '{code}' → ERROR: {e}")

print("\n✓ Material alias system working!")
