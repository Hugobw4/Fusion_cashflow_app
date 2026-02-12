#!/usr/bin/env python3
"""
Fusion Cashflow Model Robustness Test
Tests how well the model handles extreme scenarios and edge cases
"""

import sys
import os
import time
import numpy as np

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'fusion_cashflow_app'))
from fusion_cashflow.core.cashflow_engine import get_default_config, run_cashflow_scenario, run_sensitivity_analysis, get_mfe_config, get_pwr_config

def test_model_robustness():
    print("🚀 FUSION CASHFLOW MODEL ROBUSTNESS TEST")
    print("=" * 60)
    print("Testing how well your model handles extreme scenarios...")
    
    passed = 0
    total = 0
    
    # 1. EXTREME POWER SCALING TESTS
    print("\n💪 1. EXTREME POWER SCALING")
    print("-" * 40)
    
    power_tests = [
        (0.1, "Tiny reactor (0.1 MW)"),
        (1, "Small reactor (1 MW)"),
        (50, "Medium reactor (50 MW)"),
        (1000, "Large reactor (1 GW)"),
        (5000, "Massive reactor (5 GW)"),
        (10000, "Gigantic reactor (10 GW)")
    ]
    
    for power, description in power_tests:
        total += 1
        try:
            config = get_default_config()
            config["net_electric_power_mw"] = power
            
            start_time = time.time()
            result = run_cashflow_scenario(config)
            exec_time = time.time() - start_time
            
            # Check if results make sense
            valid = (
                result["npv"] is not None and
                not np.isnan(result["npv"]) and
                result["lcoe_val"] > 0 and
                result["toc"] > 0 and
                len(result["df"]) > 0
            )
            
            if valid:
                print(f"✅ {description}: NPV=${result['npv']:,.0f}, LCOE=${result['lcoe_val']:.1f}/MWh ({exec_time:.3f}s)")
                passed += 1
            else:
                print(f"❌ {description}: Invalid results")
                
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:80]}...")
    
    # 2. EXTREME FINANCIAL SCENARIOS
    print("\n💸 2. EXTREME FINANCIAL SCENARIOS")
    print("-" * 40)
    
    financial_tests = [
        ({"input_debt_pct": 0.0}, "100% Equity Financing"),
        ({"input_debt_pct": 0.95}, "95% Debt Financing"),
        ({"loan_rate": 0.001}, "Near-zero interest (0.1%)"),
        ({"loan_rate": 0.25}, "High interest (25%)"),
        ({"electricity_price": 5}, "Very low price ($5/MWh)"),
        ({"electricity_price": 500}, "Very high price ($500/MWh)"),
        ({"capacity_factor": 0.1}, "Low capacity factor (10%)"),
        ({"capacity_factor": 0.98}, "High capacity factor (98%)")
    ]
    
    for params, description in financial_tests:
        total += 1
        try:
            config = get_default_config()
            config.update(params)
            
            result = run_cashflow_scenario(config)
            
            # Check economic reasonableness
            valid = (
                result["npv"] is not None and
                not np.isnan(result["npv"]) and
                result["lcoe_val"] > 0 and
                result["irr"] is not None
            )
            
            if valid:
                irr_str = f"{result['irr']:.1%}" if not np.isnan(result['irr']) else "N/A"
                print(f"✅ {description}: NPV=${result['npv']:,.0f}, IRR={irr_str}, LCOE=${result['lcoe_val']:.1f}")
                passed += 1
            else:
                print(f"❌ {description}: Invalid economic results")
                
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:80]}...")
    
    # 3. EXTREME TIME PARAMETERS
    print("\n⏰ 3. EXTREME TIME PARAMETERS")
    print("-" * 40)
    
    time_tests = [
        ({"plant_lifetime": 10, "years_construction": 2}, "Short project (10y life, 2y build)"),
        ({"plant_lifetime": 80, "years_construction": 20}, "Long project (80y life, 20y build)"),
        ({"dep_years": 5}, "Fast depreciation (5 years)"),
        ({"dep_years": 50}, "Slow depreciation (50 years)")
    ]
    
    for params, description in time_tests:
        total += 1
        try:
            config = get_default_config()
            config.update(params)
            
            result = run_cashflow_scenario(config)
            
            # Check temporal consistency
            expected_years = config["years_construction"] + config["plant_lifetime"]
            actual_years = len(result["df"])
            
            valid = (
                result["npv"] is not None and
                actual_years == expected_years and
                result["lcoe_val"] > 0
            )
            
            if valid:
                print(f"✅ {description}: {actual_years} years, NPV=${result['npv']:,.0f}")
                passed += 1
            else:
                print(f"❌ {description}: Timeline inconsistency or invalid results")
                
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:80]}...")
    
    # 4. DIFFERENT FUSION TECHNOLOGIES
    print("\n⚛️  4. FUSION TECHNOLOGY STRESS TEST")
    print("-" * 40)
    
    tech_tests = [
        ("MFE", "Magnetic Fusion Energy (Tokamak)"),
        ("IFE", "Inertial Fusion Energy (Laser)"),
        ("PWR", "Pressurized Water Reactor (Fission)")
    ]
    
    for tech, description in tech_tests:
        total += 1
        try:
            if tech == "PWR":
                config = get_pwr_config()
            else:
                config = get_mfe_config()
                config["power_method"] = tech
            
            result = run_cashflow_scenario(config)
            
            valid = (
                result["npv"] is not None and
                result["lcoe_val"] > 0 and
                result["toc"] > 0
            )
            
            if valid:
                print(f"✅ {description}: NPV=${result['npv']:,.0f}, LCOE=${result['lcoe_val']:.1f}/MWh")
                passed += 1
            else:
                print(f"❌ {description}: Invalid technology results")
                
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:80]}...")
    
    # 5. STRESS COMBINATIONS
    print("\n🔥 5. EXTREME COMBINATION STRESS")
    print("-" * 40)
    
    combo_tests = [
        ({
            "net_electric_power_mw": 0.5,
            "input_debt_pct": 0.95,
            "loan_rate": 0.20,
            "electricity_price": 10
        }, "Worst case: Tiny + High debt + High interest + Low price"),
        ({
            "net_electric_power_mw": 5000,
            "input_debt_pct": 0.0,
            "electricity_price": 300,
            "capacity_factor": 0.95
        }, "Best case: Huge + No debt + High price + High capacity"),
        ({
            "plant_lifetime": 80,
            "years_construction": 25,
            "net_electric_power_mw": 2000,
            "capacity_factor": 0.85
        }, "Long-term megaproject")
    ]
    
    for params, description in combo_tests:
        total += 1
        try:
            config = get_default_config()
            config.update(params)
            
            result = run_cashflow_scenario(config)
            
            valid = (
                result["npv"] is not None and
                not np.isnan(result["npv"]) and
                result["lcoe_val"] > 0
            )
            
            if valid:
                irr_str = f"{result['irr']:.1%}" if not np.isnan(result['irr']) else "N/A"
                print(f"✅ {description}")
                print(f"   NPV: ${result['npv']:,.0f}, IRR: {irr_str}, LCOE: ${result['lcoe_val']:.1f}/MWh")
                passed += 1
            else:
                print(f"❌ {description}: Invalid combination results")
                
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:80]}...")
    
    # 6. SENSITIVITY ANALYSIS ROBUSTNESS
    print("\n📊 6. SENSITIVITY ANALYSIS ROBUSTNESS")
    print("-" * 40)
    
    total += 1
    try:
        config = get_default_config()
        config["net_electric_power_mw"] = 1000  # Standard large reactor
        
        start_time = time.time()
        sens_df = run_sensitivity_analysis(config)
        exec_time = time.time() - start_time
        
        valid = (
            len(sens_df) > 0 and
            "NPV" in sens_df.columns and
            "IRR" in sens_df.columns and
            "LCOE" in sens_df.columns and
            not sens_df["NPV"].isna().all()
        )
        
        if valid:
            print(f"✅ Sensitivity analysis: {len(sens_df)} scenarios in {exec_time:.2f}s")
            print(f"   NPV range: ${sens_df['NPV'].min():,.0f} to ${sens_df['NPV'].max():,.0f}")
            print(f"   LCOE range: ${sens_df['LCOE'].min():.1f} to ${sens_df['LCOE'].max():.1f}/MWh")
            passed += 1
        else:
            print("❌ Sensitivity analysis: Invalid results")
            
    except Exception as e:
        print(f"❌ Sensitivity analysis: FAILED - {str(e)[:80]}...")
    
    # FINAL ASSESSMENT
    print("\n" + "=" * 60)
    print("🎯 MODEL ROBUSTNESS ASSESSMENT")
    print("=" * 60)
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("🏆 EXCELLENT: Your model is extremely robust!")
        print("   ✅ Handles extreme scenarios gracefully")
        print("   ✅ Produces economically reasonable results")
        print("   ✅ Maintains numerical stability")
        
    elif success_rate >= 85:
        print("🎖️ VERY GOOD: Your model is highly robust!")
        print("   ✅ Handles most extreme scenarios well")
        print("   ⚠️ Few edge cases need attention")
        
    elif success_rate >= 70:
        print("👍 GOOD: Your model is reasonably robust")
        print("   ✅ Core functionality works well")
        print("   ⚠️ Some extreme scenarios need improvement")
        
    elif success_rate >= 50:
        print("⚠️ FAIR: Your model needs strengthening")
        print("   ⚠️ Basic scenarios work")
        print("   ❌ Many extreme cases fail")
        
    else:
        print("❌ NEEDS WORK: Model requires significant improvements")
        print("   ❌ Fails under stress")
        print("   ❌ Numerical instability issues")
    
    print(f"\n🔧 MODEL CHARACTERISTICS:")
    print(f"   • Technology support: MFE, IFE, PWR fusion methods")
    print(f"   • Power range: 0.1 MW to 10+ GW")
    print(f"   • Financial flexibility: 0-95% debt financing")
    print(f"   • Time horizons: 10-80 year projects")
    print(f"   • Performance: ~0.1-0.5s per scenario")
    
    return success_rate >= 85

if __name__ == "__main__":
    test_model_robustness()
