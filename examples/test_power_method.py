#!/usr/bin/env python3

# Test script for power method functionality

from fusion_cashflow.core.cashflow_engine import get_default_config, run_cashflow_scenario

def test_power_methods():
    """Test all three power methods: MFE, IFE, PWR"""
    
    print("Testing Power Method Functionality")
    print("=" * 40)
    
    # Test MFE (default)
    print("\n1. Testing MFE (Magnetic Fusion Energy)")
    config_mfe = get_default_config()
    config_mfe['power_method'] = 'MFE'
    print(f"   Power Method: {config_mfe['power_method']}")
    print(f"   Initial Fuel Type: {config_mfe['fuel_type']}")
    
    try:
        result_mfe = run_cashflow_scenario(config_mfe)
        print(f"   NPV: ${result_mfe['npv']:,.0f}")
        print(f"   IRR: {result_mfe['irr']:.2%}")
        print(f"   LCOE: ${result_mfe['lcoe_val']:.2f}/MWh")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test IFE
    print("\n2. Testing IFE (Inertial Fusion Energy)")
    config_ife = get_default_config()
    config_ife['power_method'] = 'IFE'
    print(f"   Power Method: {config_ife['power_method']}")
    print(f"   Initial Fuel Type: {config_ife['fuel_type']}")
    
    try:
        result_ife = run_cashflow_scenario(config_ife)
        print(f"   NPV: ${result_ife['npv']:,.0f}")
        print(f"   IRR: {result_ife['irr']:.2%}")
        print(f"   LCOE: ${result_ife['lcoe_val']:.2f}/MWh")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test PWR
    print("\n3. Testing PWR (Pressurized Water Reactor)")
    config_pwr = get_default_config()
    config_pwr['power_method'] = 'PWR'
    print(f"   Power Method: {config_pwr['power_method']}")
    print(f"   Initial Fuel Type: {config_pwr['fuel_type']}")
    
    try:
        result_pwr = run_cashflow_scenario(config_pwr)
        print(f"   NPV: ${result_pwr['npv']:,.0f}")
        print(f"   IRR: {result_pwr['irr']:.2%}")
        print(f"   LCOE: ${result_pwr['lcoe_val']:.2f}/MWh")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 40)
    print("Power Method Testing Complete")

if __name__ == "__main__":
    test_power_methods()
