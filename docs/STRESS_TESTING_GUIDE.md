# Stress Testing Guide for Fusion Cashflow Engine

## Overview
This directory contains comprehensive stress testing tools for the Fusion Cashflow Engine. The tests validate performance, reliability, edge cases, and data integrity under various load conditions.

## Quick Start

### Option 1: Basic Stress Test (No Dependencies)
```bash
python run_stress_tests.py
# Choose option 1 for quick test
```

### Option 2: Full Stress Test Suite
```bash
python run_stress_tests.py  
# Choose option 2 for full test with dependency installation
```

### Option 3: Manual Installation
```bash
pip install -r requirements-test.txt
pytest tests/test_stress.py -v
```

## Test Categories

### 1. Performance Testing (`TestStressPerformance`)
- **Benchmark tests**: Measure execution time for scenarios
- **Memory usage tests**: Monitor memory consumption and detect leaks
- **Parallel execution tests**: Validate thread safety and concurrent performance
- **Load testing**: High-volume scenario execution

**Key Commands:**
```bash
# Run performance benchmarks
pytest tests/test_stress.py::TestStressPerformance --benchmark-only

# Run with memory profiling
pytest tests/test_stress.py::TestStressPerformance::test_memory_usage_large_scenario -s
```

### 2. Property-Based Testing (`TestPropertyBasedStress`)
Uses **Hypothesis** library to generate random valid inputs and verify system properties:
- Financial parameter ranges (power, price, debt ratios)
- Time parameter combinations (lifetime, construction years)
- Invariant validation (LCOE > 0, reasonable IRR ranges)

**Key Commands:**
```bash
# Run property-based tests with more examples
pytest tests/test_stress.py::TestPropertyBasedStress --hypothesis-show-statistics
```

### 3. Edge Case Testing (`TestEdgeCaseStress`)
- Extreme power values (micro to mega reactors)
- Extreme financial parameters (zero debt, high leverage)
- Invalid configurations (negative values, impossible ratios)
- Boundary conditions

### 4. Data Integrity Testing (`TestDataIntegrityStress`)
- DataFrame consistency across runs
- Numerical stability with precision-sensitive calculations
- Cash flow conservation laws
- Data type validation

### 5. Scenario Testing (`TestScenarioStress`)
- All power methods (MFE, IFE, PWR) under stress
- Sensitivity analysis stress testing
- Multi-configuration testing

## Load Testing

### Standalone Load Testing
```bash
python tests/load_test.py
```
This runs direct function calls with concurrent execution to measure throughput.

### Web API Load Testing (if you have a web server)
```bash
pip install locust
locust -f tests/load_test.py --host=http://localhost:8000
```

## Monitoring & Analysis

### Performance Benchmarking
```bash
# Run benchmarks and save results
pytest tests/test_stress.py --benchmark-only --benchmark-json=benchmark_results.json

# Compare benchmarks over time
pytest-benchmark compare benchmark_results.json
```

### Code Coverage
```bash
# Run with coverage analysis
pytest tests/test_stress.py --cov=fusion_cashflow_app --cov-report=html

# View coverage report
open htmlcov/index.html  # On Windows: start htmlcov/index.html
```

### Memory Profiling
```bash
# Profile memory usage line by line
python -m memory_profiler tests/test_stress.py
```

## Expected Performance Metrics

### Baseline Performance (on modern hardware):
- **Single scenario**: < 0.1 seconds
- **Sensitivity analysis**: < 5 seconds  
- **100 parallel scenarios**: < 10 seconds
- **Memory usage**: < 50MB increase for 20 scenarios
- **Throughput**: > 10 scenarios/second

### Performance Red Flags:
- Single scenario > 1 second
- Memory increase > 100MB for 20 scenarios
- Parallel execution slower than sequential
- Any NaN or infinite results
- Inconsistent results for identical inputs

## Common Test Scenarios

### 1. Quick Health Check
```python
# Run this in Python to verify basic functionality
from fusion_cashflow_app.cashflow_engine import get_default_config, run_cashflow_scenario

config = get_default_config()
result = run_cashflow_scenario(config)
print(f"NPV: ${result['npv']:,.0f}, IRR: {result['irr']:.2%}")
```

### 2. Parameter Sweep Test
```python
# Test multiple power levels
powers = [100, 500, 1000, 2000, 5000]
for power in powers:
    config = get_default_config()
    config["net_electric_power_mw"] = power
    result = run_cashflow_scenario(config)
    print(f"{power}MW: LCOE=${result['lcoe_val']:.2f}/MWh")
```

### 3. Regional Stress Test
```python
# Test different locations
locations = ["United States", "Germany", "China", "India", "South Africa"]
for location in locations:
    config = get_default_config()
    config["project_location"] = location
    result = run_cashflow_scenario(config)
    print(f"{location}: NPV=${result['npv']:,.0f}")
```

## Troubleshooting

### Common Issues:

1. **Import Errors**: 
   - Ensure you're running from the correct directory
   - Check that `fusion_cashflow_app` is in your Python path

2. **Slow Performance**:
   - Check if running in debug mode
   - Verify no other heavy processes are running
   - Consider running fewer parallel workers

3. **Memory Issues**:
   - Monitor with Task Manager/Activity Monitor
   - Check for circular references in test data
   - Run garbage collection explicitly if needed

4. **Test Failures**:
   - Check input parameter ranges
   - Verify expected output ranges for your use case
   - Review error messages for numerical stability issues

## Integration with CI/CD

### GitHub Actions Example:
```yaml
- name: Run Stress Tests
  run: |
    pip install -r requirements-test.txt
    pytest tests/test_stress.py --benchmark-skip -x
```

### Performance Regression Detection:
```bash
# Store baseline performance
pytest tests/test_stress.py --benchmark-only --benchmark-save=baseline

# Compare against baseline in CI
pytest tests/test_stress.py --benchmark-only --benchmark-compare=baseline
```

## Advanced Usage

### Custom Property-Based Tests
```python
from hypothesis import given, strategies as st

@given(power=st.floats(min_value=1, max_value=10000))
def test_custom_property(power):
    config = get_default_config()
    config["net_electric_power_mw"] = power
    result = run_cashflow_scenario(config)
    assert result["lcoe_val"] > 0  # LCOE should always be positive
```

### Custom Load Testing Scenarios
```python
# Add to tests/load_test.py
def custom_stress_scenario():
    """Your specific stress test scenario"""
    config = get_default_config()
    # Add your specific parameter variations
    return run_cashflow_scenario(config)
```

## Support

For issues with stress testing:
1. Check this guide first
2. Review test output for specific error messages
3. Run `python run_stress_tests.py` for automated diagnostics
4. Consider running tests individually to isolate issues

Remember: Stress testing should be run regularly (daily/weekly) to catch performance regressions early!
