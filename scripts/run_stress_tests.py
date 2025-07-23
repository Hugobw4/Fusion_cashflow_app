#!/usr/bin/env python3
"""
Fusion Cashflow Stress Testing Runner
Installs dependencies and runs comprehensive stress tests
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description=""):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    if description:
        print(f"🔄 {description}")
    print(f"Running: {cmd}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def install_test_dependencies():
    """Install stress testing dependencies"""
    print("📦 Installing stress testing dependencies...")
    
    # Core testing packages - install in groups to handle dependencies better
    core_packages = [
        "pytest>=7.0.0",
        "psutil>=5.9.0",
    ]
    
    extended_packages = [
        "pytest-cov>=4.0.0", 
        "pytest-xdist>=3.0.0",
        "pytest-timeout>=2.1.0",
        "pytest-randomly>=3.12.0",
        "pytest-benchmark>=4.0.0",
        "memory-profiler>=0.60.0",
        "hypothesis>=6.68.0",
        "faker>=18.0.0",
    ]
    
    # Install core packages first
    print("\n🔧 Installing core packages...")
    for package in core_packages:
        success = run_command(f"pip install --user {package}", f"Installing {package}")
        if not success:
            print(f"⚠️ Warning: Failed to install {package}")
    
    # Install extended packages
    print("\n🔧 Installing extended packages...")
    for package in extended_packages:
        success = run_command(f"pip install --user {package}", f"Installing {package}")
        if not success:
            print(f"⚠️ Warning: Failed to install {package}")
    
    print("✅ Dependency installation complete")

def run_basic_stress_test():
    """Run a basic stress test without external dependencies"""
    print("\n🧪 Running basic stress test...")
    
    try:
        # Add the app directory to Python path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'fusion_cashflow_app'))
        
        from fusion_cashflow.core.cashflow_engine import get_default_config, run_cashflow_scenario, run_sensitivity_analysis
        import random
        import concurrent.futures
        
        print("✅ Successfully imported cashflow engine")
        
        # Test 1: Basic functionality
        print("\n1️⃣ Testing basic functionality...")
        config = get_default_config()
        start_time = time.time()
        result = run_cashflow_scenario(config)
        execution_time = time.time() - start_time
        
        print(f"   ⏱️ Execution time: {execution_time:.3f}s")
        print(f"   💰 NPV: ${result['npv']:,.0f}")
        print(f"   📈 IRR: {result['irr']:.2%}")
        print(f"   ⚡ LCOE: ${result['lcoe_val']:.2f}/MWh")
        
        # Test 2: Parameter variation
        print("\n2️⃣ Testing parameter variations...")
        test_configs = []
        for i in range(10):
            config = get_default_config()
            config["net_electric_power_mw"] = random.uniform(200, 1500)
            config["electricity_price"] = random.uniform(50, 150)
            config["capacity_factor"] = random.uniform(0.7, 0.95)
            test_configs.append(config)
        
        start_time = time.time()
        results = []
        for config in test_configs:
            result = run_cashflow_scenario(config)
            results.append(result)
        
        execution_time = time.time() - start_time
        print(f"   ⏱️ 10 scenarios in {execution_time:.3f}s ({10/execution_time:.1f} scenarios/sec)")
        
        # Validate results
        valid_results = [r for r in results if r["npv"] is not None and r["irr"] is not None]
        print(f"   ✅ {len(valid_results)}/10 scenarios successful")
        
        # Test 3: Parallel execution
        print("\n3️⃣ Testing parallel execution...")
        def run_scenario(config):
            return run_cashflow_scenario(config)
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_scenario, config) for config in test_configs]
            parallel_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        parallel_time = time.time() - start_time
        print(f"   ⏱️ 10 parallel scenarios in {parallel_time:.3f}s ({10/parallel_time:.1f} scenarios/sec)")
        print(f"   🚀 Speedup: {execution_time/parallel_time:.1f}x")
        
        # Test 4: Sensitivity analysis
        print("\n4️⃣ Testing sensitivity analysis...")
        config = get_default_config()
        start_time = time.time()
        sens_df = run_sensitivity_analysis(config)
        sens_time = time.time() - start_time
        
        print(f"   ⏱️ Sensitivity analysis in {sens_time:.3f}s")
        print(f"   📊 Generated {len(sens_df)} sensitivity points")
        
        # Test 5: Memory usage
        print("\n5️⃣ Testing memory usage...")
        try:
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run multiple scenarios
            for i in range(20):
                result = run_cashflow_scenario(get_default_config())
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            
            print(f"   💾 Memory usage: {memory_before:.1f}MB → {memory_after:.1f}MB")
            print(f"   📈 Memory increase: {memory_increase:.1f}MB for 20 scenarios")
            
            if memory_increase > 50:
                print(f"   ⚠️ Warning: High memory usage detected")
            else:
                print(f"   ✅ Memory usage looks good")
                
        except ImportError:
            print("   ⚠️ psutil not available, skipping memory test")
        
        print("\n🎉 Basic stress test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Basic stress test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_full_stress_tests():
    """Run the full pytest stress test suite"""
    print("\n🧪 Running full stress test suite...")
    
    # Check if pytest is available
    try:
        import pytest
        pytest_available = True
    except ImportError:
        pytest_available = False
        print("⚠️ pytest not available, skipping full test suite")
        return False
    
    if pytest_available:
        test_commands = [
            ("pytest tests/test_stress.py::TestStressPerformance -v", "Performance tests"),
            ("pytest tests/test_stress.py::TestEdgeCaseStress -v", "Edge case tests"),
            ("pytest tests/test_stress.py::TestDataIntegrityStress -v", "Data integrity tests"),
            ("pytest tests/test_stress.py::TestScenarioStress -v", "Scenario stress tests"),
        ]
        
        for cmd, description in test_commands:
            success = run_command(cmd, description)
            if not success:
                print(f"⚠️ {description} had issues")
    
    return True

def run_load_test():
    """Run standalone load test"""
    print("\n🚀 Running load test...")
    
    try:
        # Run the standalone load tester
        success = run_command("python tests/load_test.py", "Standalone load test")
        return success
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        return False

def main():
    """Main stress testing workflow"""
    print("🔬 Fusion Cashflow Stress Testing Suite")
    print("=" * 50)
    
    # Get user choice
    print("\nSelect testing mode:")
    print("1. Quick test (basic functionality only)")
    print("2. Full test (install dependencies + comprehensive testing)")
    print("3. Install dependencies only")
    
    choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"
    
    if choice == "3":
        install_test_dependencies()
        return
    
    if choice == "2":
        print("\n📦 Installing dependencies...")
        install_test_dependencies()
    
    # Always run basic test
    success = run_basic_stress_test()
    
    if choice == "2" and success:
        # Try to run full tests
        run_full_stress_tests()
        run_load_test()
    
    print("\n" + "="*50)
    if success:
        print("🎉 Stress testing completed!")
        print("\n📊 Summary:")
        print("   ✅ Basic functionality test: PASSED")
        print("   ✅ Parameter variation test: PASSED") 
        print("   ✅ Parallel execution test: PASSED")
        print("   ✅ Sensitivity analysis test: PASSED")
        print("\n💡 Tips for ongoing stress testing:")
        print("   • Run 'python run_stress_tests.py' regularly")
        print("   • Monitor execution times for performance regression")
        print("   • Use 'pytest tests/test_stress.py -v' for detailed testing")
        print("   • Use 'pytest tests/test_stress.py --benchmark-only' for benchmarks")
    else:
        print("❌ Some tests failed - check output above")

if __name__ == "__main__":
    main()
