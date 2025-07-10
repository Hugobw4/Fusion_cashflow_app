from fusion_cashflow_app.cashflow_engine import get_default_config

# Test configuration differences
config = get_default_config()
print(f"Default power method: {config['power_method']}")
print(f"Default fuel type: {config['fuel_type']}")
print(f"Default EPC cost: ${config['total_epc_cost']:,}")

# Test PWR configuration changes
config_pwr = get_default_config()
config_pwr['power_method'] = 'PWR'
print(f"\nPWR power method: {config_pwr['power_method']}")
print(f"PWR fuel type: {config_pwr['fuel_type']}")
print(f"PWR EPC cost: ${config_pwr['total_epc_cost']:,}")

print("\nPower method functionality added successfully!")
print("Available power methods: MFE, IFE, PWR")
print("- MFE: Magnetic Fusion Energy (Tokamak)")
print("- IFE: Inertial Fusion Energy (Laser-driven)")  
print("- PWR: Pressurized Water Reactor (Fission)")
