#!/usr/bin/env python3
"""
Stress Test Analysis Script
Analyzes the performance and results of the fusion cashflow stress testing suite
"""

import time
import sys
import os

# Add the path to import the test modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'fusion_cashflow_app'))

def analyze_stress_tests():
    """Run comprehensive stress test analysis"""
    print("=" * 60)
    print("🔬 FUSION CASHFLOW STRESS TEST ANALYSIS")
    print("=" * 60)
    
    try:
        import test_stress as ts
        from fusion_cashflow.core.cashflow_engine import get_default_config, run_cashflow_scenario
    except ImportError as e:
        print(f"❌ Failed to import test modules: {e}")
        return
    
    # Test results tracking
    results = {
        "edge_cases": {},
        "performance": {},
        "property_based": {},
        "data_integrity": {},
        "scenario_stress": {}
    }
    
    print("\n🧪 1. EDGE CASE TESTING")
    print("-" * 30)
    
    # Edge case tests
    try:
        tester = ts.TestEdgeCaseStress()
        
        # Test extreme power values
        try:
            tester.test_extreme_power_values()
            results["edge_cases"]["extreme_power"] = "✅ PASSED"
            print("✅ Extreme power values: PASSED")
        except Exception as e:
            results["edge_cases"]["extreme_power"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ Extreme power values: FAILED - {str(e)[:100]}")
        
        # Test extreme financial parameters
        try:
            tester.test_extreme_financial_parameters()
            results["edge_cases"]["extreme_financial"] = "✅ PASSED"
            print("✅ Extreme financial parameters: PASSED")
        except Exception as e:
            results["edge_cases"]["extreme_financial"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ Extreme financial parameters: FAILED - {str(e)[:100]}")
        
        # Test zero capacity factor
        try:
            tester.test_zero_capacity_factor()
            results["edge_cases"]["zero_capacity"] = "✅ PASSED (handles error gracefully)"
            print("✅ Zero capacity factor: PASSED (handles error gracefully)")
        except Exception as e:
            results["edge_cases"]["zero_capacity"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ Zero capacity factor: FAILED - {str(e)[:100]}")
        
        # Test invalid configurations
        try:
            tester.test_invalid_configurations()
            results["edge_cases"]["invalid_configs"] = "✅ PASSED (handles errors gracefully)"
            print("✅ Invalid configurations: PASSED (handles errors gracefully)")
        except Exception as e:
            results["edge_cases"]["invalid_configs"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ Invalid configurations: FAILED - {str(e)[:100]}")
    
    except Exception as e:
        print(f"❌ Failed to initialize edge case tester: {e}")
    
    print("\n⚡ 2. PERFORMANCE TESTING")
    print("-" * 30)
    
    # Performance tests
    try:
        perf_tester = ts.TestStressPerformance()
        
        # Benchmark default scenario
        try:
            start_time = time.time()
            perf_tester.test_benchmark_default_scenario()
            exec_time = time.time() - start_time
            results["performance"]["default_scenario"] = f"✅ PASSED ({exec_time:.2f}s)"
            print(f"✅ Default scenario benchmark: PASSED ({exec_time:.2f}s)")
        except Exception as e:
            results["performance"]["default_scenario"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ Default scenario benchmark: FAILED - {str(e)[:100]}")
        
        # Memory usage test (if psutil available)
        try:
            perf_tester.test_memory_usage_large_scenario()
            results["performance"]["memory_usage"] = "✅ PASSED"
            print("✅ Memory usage test: PASSED")
        except ImportError:
            results["performance"]["memory_usage"] = "⚠️ SKIPPED (psutil not available)"
            print("⚠️ Memory usage test: SKIPPED (psutil not available)")
        except Exception as e:
            results["performance"]["memory_usage"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ Memory usage test: FAILED - {str(e)[:100]}")
    
    except Exception as e:
        print(f"❌ Failed to initialize performance tester: {e}")
    
    print("\n🔄 3. DATA INTEGRITY TESTING")
    print("-" * 30)
    
    # Data integrity tests
    try:
        data_tester = ts.TestDataIntegrityStress()
        
        # DataFrame consistency
        try:
            data_tester.test_dataframe_consistency()
            results["data_integrity"]["dataframe_consistency"] = "✅ PASSED"
            print("✅ DataFrame consistency: PASSED")
        except Exception as e:
            results["data_integrity"]["dataframe_consistency"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ DataFrame consistency: FAILED - {str(e)[:100]}")
        
        # Numerical stability
        try:
            data_tester.test_numerical_stability()
            results["data_integrity"]["numerical_stability"] = "✅ PASSED"
            print("✅ Numerical stability: PASSED")
        except Exception as e:
            results["data_integrity"]["numerical_stability"] = f"❌ FAILED: {str(e)[:100]}"
            print(f"❌ Numerical stability: FAILED - {str(e)[:100]}")
    
    except Exception as e:
        print(f"❌ Failed to initialize data integrity tester: {e}")
    
    print("\n🎯 4. BASIC ENGINE VALIDATION")
    print("-" * 30)
    
    # Basic engine validation
    try:
        config = get_default_config()
        start_time = time.time()
        result = run_cashflow_scenario(config)
        exec_time = time.time() - start_time
        
        print(f"✅ Basic engine test: PASSED ({exec_time:.3f}s)")
        print(f"   NPV: ${result['npv']:,.0f}")
        print(f"   IRR: {result['irr']:.2%}")
        print(f"   LCOE: ${result['lcoe_val']:.2f}/MWh")
        results["basic_engine"] = "✅ PASSED"
    except Exception as e:
        print(f"❌ Basic engine test: FAILED - {str(e)[:100]}")
        results["basic_engine"] = f"❌ FAILED: {str(e)[:100]}"
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, tests in results.items():
        if isinstance(tests, dict):
            for test_name, result in tests.items():
                total_tests += 1
                if "✅ PASSED" in result:
                    passed_tests += 1
        else:
            total_tests += 1
            if "✅ PASSED" in tests:
                passed_tests += 1
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT: Stress testing suite is highly robust!")
    elif success_rate >= 75:
        print("👍 GOOD: Most tests pass, minor improvements needed")
    elif success_rate >= 50:
        print("⚠️ FAIR: Significant improvements needed")
    else:
        print("❌ POOR: Major issues need addressing")
    
    print("\n💡 IMPROVEMENT RECOMMENDATIONS:")
    
    # Specific recommendations based on results
    failed_tests = [test for category in results.values() 
                   if isinstance(category, dict) 
                   for test, result in category.items() 
                   if "❌ FAILED" in result]
    
    if any("memory" in test.lower() for test in failed_tests):
        print("• Install psutil for memory monitoring: pip install psutil")
    
    if any("zero_capacity" in str(results.get("edge_cases", {})).lower()):
        print("• Consider adding zero-division protection in fuel calculations")
    
    if any("invalid" in str(results.get("edge_cases", {})).lower()):
        print("• Add input validation for negative lifetimes and invalid parameters")
    
    if success_rate < 100:
        print("• Review failed tests and add error handling for edge cases")
        print("• Consider adding more graceful degradation for invalid inputs")
    
    print("• Add more property-based tests when hypothesis is available")
    print("• Consider adding load testing for concurrent scenarios")
    print("• Implement continuous performance monitoring")
    
    return results

if __name__ == "__main__":
    analyze_stress_tests()
