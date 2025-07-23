#!/usr/bin/env python3
"""
Test script to validate the LCOE fix using Vogtle configuration.
Expected LCOE: ~$180-200/MWh based on Lazard methodology.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fusion_cashflow.core.cashflow_engine import run_cashflow_scenario, get_pwr_config

def test_vogtle_lcoe():
    """Test LCOE calculation with Vogtle configuration."""
    print("Testing LCOE calculation with Vogtle configuration...")
    
    # Get PWR configuration (Vogtle-based)
    config = get_pwr_config()
    
    # Print key parameters
    print(f"EPC Cost: ${config['total_epc_cost']/1e9:.1f} billion")
    print(f"Net Power: {config['net_electric_power_mw']} MW")
    print(f"Capacity Factor: {config['capacity_factor']:.1%}")
    print(f"Plant Lifetime: {config['plant_lifetime']} years")
    print(f"Fixed O&M: ${config['fixed_om_per_mw']:,.0f}/MW/year")
    print(f"Variable O&M: ${config['variable_om']:.2f}/MWh")
    print(f"Decommissioning: ${config['decommissioning_cost']/1e9:.1f} billion")
    
    # Run cashflow scenario
    results = run_cashflow_scenario(config)
    
    # Print results
    print(f"\n=== LCOE Results ===")
    print(f"LCOE: ${results['lcoe_val']:.2f}/MWh")
    print(f"NPV: ${results['npv']/1e9:.2f} billion")
    print(f"IRR: {results['irr']:.2%}")
    print(f"WACC: {results['wacc']:.2%}")
    
    # Validate LCOE is in expected range
    expected_min = 180
    expected_max = 200
    
    if expected_min <= results['lcoe_val'] <= expected_max:
        print(f"✅ LCOE is within expected range (${expected_min}-${expected_max}/MWh)")
    else:
        print(f"❌ LCOE is outside expected range (${expected_min}-${expected_max}/MWh)")
        print(f"   Actual: ${results['lcoe_val']:.2f}/MWh")
    
    return results

def test_zero_opex_toy_plant():
    """Test LCOE calculation with zero O&M and fuel costs."""
    print("\n" + "="*50)
    print("Testing zero O&M, zero fuel toy plant...")
    
    # Create a simple configuration
    config = {
        "construction_start_year": 2020,
        "years_construction": 5,
        "project_energy_start_year": 2025,
        "plant_lifetime": 30,
        "power_method": "MFE",
        "net_electric_power_mw": 1000,
        "capacity_factor": 1.0,  # 100% capacity factor
        "fuel_type": "Lithium-Solid",
        "input_debt_pct": 0.0,  # No debt
        "cost_of_debt": 0.05,
        "loan_rate": 0.05,
        "financing_fee": 0.0,
        "repayment_term_years": 20,
        "grace_period_years": 0,
        "total_epc_cost": 10000000000,  # $10 billion
        "extra_capex_pct": 0.0,
        "project_contingency_pct": 0.0,
        "process_contingency_pct": 0.0,
        "fixed_om_per_mw": 0,  # Zero O&M
        "variable_om": 0,  # Zero O&M
        "electricity_price": 100,
        "dep_years": 30,
        "salvage_value": 0,
        "decommissioning_cost": 0,
        "use_real_dollars": False,
        "price_escalation_active": False,
        "escalation_rate": 0.0,
        "include_fuel_cost": False,  # Zero fuel cost
        "apply_tax_model": False,
        "ramp_up": False,
        "ramp_up_years": 0,
        "ramp_up_rate_per_year": 0.0,
        "project_location": "USA",
    }
    
    # Run cashflow scenario
    results = run_cashflow_scenario(config)
    
    # Calculate expected LCOE: EPC / lifetime energy
    annual_energy = config['net_electric_power_mw'] * 8760 * config['capacity_factor']
    lifetime_energy = annual_energy * config['plant_lifetime']
    expected_lcoe = config['total_epc_cost'] / lifetime_energy
    
    print(f"EPC Cost: ${config['total_epc_cost']/1e9:.1f} billion")
    print(f"Annual Energy: {annual_energy/1e6:.1f} million MWh")
    print(f"Lifetime Energy: {lifetime_energy/1e6:.1f} million MWh")
    print(f"Expected LCOE: ${expected_lcoe:.2f}/MWh")
    print(f"Actual LCOE: ${results['lcoe_val']:.2f}/MWh")
    
    # Check if they match (within 1% tolerance)
    if abs(results['lcoe_val'] - expected_lcoe) / expected_lcoe < 0.01:
        print("✅ Zero O&M/fuel test passed!")
    else:
        print("❌ Zero O&M/fuel test failed!")
        print(f"   Difference: {abs(results['lcoe_val'] - expected_lcoe):.2f}/MWh")
    
    return results

if __name__ == "__main__":
    # Test Vogtle LCOE
    vogtle_results = test_vogtle_lcoe()
    
    # Test zero O&M toy plant
    toy_results = test_zero_opex_toy_plant()
    
    print("\n" + "="*50)
    print("LCOE Fix Testing Complete!")
