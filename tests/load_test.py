"""
Load testing configuration for Fusion Cashflow Engine
Run this with: locust -f load_test.py --host=http://localhost:8000
"""

# Optional locust import for web API load testing
try:
    from locust import HttpUser, task, between
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False
    # Create dummy classes for when locust is not available
    class HttpUser:
        pass
    def task(weight=1):
        def decorator(func):
            return func
        return decorator
    def between(min_wait, max_wait):
        return None

import json
import random

class CashflowUser(HttpUser):
    """Simulated user for load testing the cashflow API"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        self.base_config = {
            "project_name": "Load Test Project",
            "project_location": "United States",
            "construction_start_year": 2025,
            "years_construction": 7,
            "project_energy_start_year": 2032,
            "plant_lifetime": 30,
            "power_method": "MFE",
            "net_electric_power_mw": 500,
            "capacity_factor": 0.9,
            "fuel_type": "Lithium-Solid",
            "input_debt_pct": 0.70,
            "cost_of_debt": 0.055,
            "electricity_price": 100,
            "total_epc_cost": 13000000000,
            "override_epc": False
        }
    
    @task(3)
    def run_basic_scenario(self):
        """Test basic scenario execution (most common use case)"""
        config = self.base_config.copy()
        
        # Add some variation
        config["net_electric_power_mw"] = random.uniform(200, 1000)
        config["electricity_price"] = random.uniform(50, 150)
        
        response = self.client.post("/api/scenario", json=config)
        
        if response.status_code == 200:
            result = response.json()
            assert "npv" in result
            assert "irr" in result
            assert "lcoe_val" in result
    
    @task(1)
    def run_sensitivity_analysis(self):
        """Test sensitivity analysis (less common but more intensive)"""
        config = self.base_config.copy()
        
        response = self.client.post("/api/sensitivity", json=config)
        
        if response.status_code == 200:
            result = response.json()
            assert len(result) > 0
    
    @task(2)
    def run_mfe_scenario(self):
        """Test MFE-specific scenarios"""
        config = self.base_config.copy()
        config["power_method"] = "MFE"
        config["net_electric_power_mw"] = random.uniform(100, 2000)
        
        response = self.client.post("/api/scenario", json=config)
        
        if response.status_code == 200:
            result = response.json()
            assert result["npv"] is not None
    
    @task(1)
    def run_pwr_scenario(self):
        """Test PWR scenarios"""
        config = {
            "project_name": "PWR Load Test",
            "project_location": "United States",
            "power_method": "PWR",
            "net_electric_power_mw": random.uniform(1000, 3000),
            "plant_lifetime": 60,
            "electricity_price": random.uniform(40, 80),
            "override_epc": True,
            "total_epc_cost": random.uniform(20e9, 40e9)
        }
        
        response = self.client.post("/api/scenario", json=config)
        
        if response.status_code == 200:
            result = response.json()
            assert result["irr"] is not None


# Standalone load testing without web server
class StandaloneCashflowTester:
    """Load testing without HTTP - direct function calls"""
    
    def __init__(self):
        import sys
        import os
        import warnings
        
        # Suppress ARPA-E cost warnings during stress testing
        warnings.filterwarnings("ignore", message="ARPA-E Cost Warning*")
        
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'fusion_cashflow_app'))
        
        from cashflow_engine import get_default_config, run_cashflow_scenario, run_sensitivity_analysis
        self.get_default_config = get_default_config
        self.run_cashflow_scenario = run_cashflow_scenario
        self.run_sensitivity_analysis = run_sensitivity_analysis
    
    def load_test_scenarios(self, num_iterations=100):
        """Run load test with direct function calls"""
        import time
        import random
        import concurrent.futures
        import warnings
        
        # Suppress ARPA-E cost warnings during stress testing
        warnings.filterwarnings("ignore", category=UserWarning, module="power_to_epc")
        
        print(f"Starting load test with {num_iterations} iterations...")
        
        def run_single_test():
            config = self.get_default_config()
            
            # Add variation
            config["net_electric_power_mw"] = random.uniform(200, 1500)
            config["electricity_price"] = random.uniform(50, 200)
            config["capacity_factor"] = random.uniform(0.7, 0.95)
            config["input_debt_pct"] = random.uniform(0.3, 0.8)
            
            start_time = time.time()
            result = self.run_cashflow_scenario(config)
            execution_time = time.time() - start_time
            
            return {
                "execution_time": execution_time,
                "npv": result["npv"],
                "irr": result["irr"],
                "lcoe": result["lcoe_val"],
                "config_power": config["net_electric_power_mw"]
            }
        
        # Sequential test
        print("Running sequential test...")
        sequential_start = time.time()
        sequential_results = []
        
        for i in range(min(20, num_iterations)):
            result = run_single_test()
            sequential_results.append(result)
            if i % 5 == 0:
                print(f"Sequential: {i+1}/20 complete")
        
        sequential_time = time.time() - sequential_start
        
        # Parallel test
        print("Running parallel test...")
        parallel_start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_single_test) for _ in range(num_iterations)]
            parallel_results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        parallel_time = time.time() - parallel_start
        
        # Analysis
        all_times = [r["execution_time"] for r in parallel_results]
        avg_time = sum(all_times) / len(all_times)
        max_time = max(all_times)
        min_time = min(all_times)
        
        print(f"\n=== LOAD TEST RESULTS ===")
        print(f"Total scenarios: {len(parallel_results)}")
        print(f"Sequential time (20 runs): {sequential_time:.2f}s")
        print(f"Parallel time ({num_iterations} runs): {parallel_time:.2f}s")
        print(f"Average execution time: {avg_time:.3f}s")
        print(f"Min execution time: {min_time:.3f}s")
        print(f"Max execution time: {max_time:.3f}s")
        print(f"Throughput: {len(parallel_results)/parallel_time:.1f} scenarios/second")
        
        # Check for any failures
        failed_results = [r for r in parallel_results if r["npv"] is None or r["irr"] is None]
        if failed_results:
            print(f"WARNING: {len(failed_results)} scenarios failed!")
        else:
            print("SUCCESS: All scenarios completed successfully")
        
        return parallel_results


if __name__ == "__main__":
    # Run standalone load test
    tester = StandaloneCashflowTester()
    results = tester.load_test_scenarios(50)
