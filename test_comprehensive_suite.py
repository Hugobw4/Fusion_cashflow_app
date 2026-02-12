"""Comprehensive test suite for PyFECONS port - Phase 7 validation.

Tests all reactor types, material combinations, CAS accounts, LCOE, and edge cases.
"""

import sys
from typing import Dict, Any
from fusion_cashflow.costing.adapter import compute_total_epc_cost


class TestResults:
    """Track test results and provide summary."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.failures = []
    
    def record_pass(self, test_name: str):
        self.passed += 1
        print(f"  ✓ {test_name}")
    
    def record_fail(self, test_name: str, reason: str):
        self.failed += 1
        self.failures.append((test_name, reason))
        print(f"  ✗ {test_name}: {reason}")
    
    def record_warning(self, test_name: str, reason: str):
        self.warnings += 1
        print(f"  ⚠ {test_name}: {reason}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Passed:   {self.passed}")
        print(f"Failed:   {self.failed}")
        print(f"Warnings: {self.warnings}")
        
        if self.failures:
            print("\nFailed Tests:")
            for name, reason in self.failures:
                print(f"  - {name}: {reason}")
        
        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED")
            return 0
        else:
            print(f"\n✗ {self.failed} TEST(S) FAILED")
            return 1


results = TestResults()


def validate_output_structure(result: Dict[str, Any], test_name: str) -> bool:
    """Validate that result dict has all required keys."""
    required_keys = [
        'power_balance', 'q_eng', 'volumes',
        'cas_21_total', 'cas_22_total', 'cas_23_turbine',
        'cas_24_electrical', 'cas_26_cooling', 'cas_27_materials',
        'total_epc_cost', 'lcoe'
    ]
    
    missing = [k for k in required_keys if k not in result]
    
    if missing:
        results.record_fail(test_name, f"Missing keys: {missing}")
        return False
    
    results.record_pass(f"{test_name} - Structure")
    return True


def validate_power_balance(result: Dict[str, Any], test_name: str, 
                          min_q_eng: float = 0.5, max_q_eng: float = 20.0):
    """Validate power balance calculations."""
    pb = result.get('power_balance', {})
    q_eng = result.get('q_eng', 0)
    
    # Check key power values exist
    required_pb_keys = ['p_fusion', 'p_thermal', 'p_electric_gross', 'p_net', 'p_recirculating']
    missing_pb = [k for k in required_pb_keys if k not in pb]
    
    if missing_pb:
        results.record_fail(f"{test_name} - Power Balance", f"Missing keys: {missing_pb}")
        return False
    
    # Validate physical relationships
    if pb['p_thermal'] <= 0:
        results.record_fail(f"{test_name} - Power Balance", "P_thermal must be > 0")
        return False
    
    if pb['p_electric_gross'] > pb['p_thermal']:
        results.record_fail(f"{test_name} - Power Balance", "P_gross > P_thermal (violates 2nd law)")
        return False
    
    if pb['p_net'] > pb['p_electric_gross']:
        results.record_fail(f"{test_name} - Power Balance", "P_net > P_gross (impossible)")
        return False
    
    # Check Q_eng range
    if not (min_q_eng <= q_eng <= max_q_eng):
        results.record_warning(f"{test_name} - Power Balance", 
                              f"Q_eng={q_eng:.2f} outside range [{min_q_eng}, {max_q_eng}]")
    
    results.record_pass(f"{test_name} - Power Balance")
    return True


def validate_costs(result: Dict[str, Any], test_name: str):
    """Validate cost calculations."""
    total_epc = result.get('total_epc_cost', 0)
    
    if total_epc <= 0:
        results.record_fail(f"{test_name} - Costs", "Total EPC must be > 0")
        return False
    
    # Validate CAS 21-27 sum to reasonable fraction of total
    cas_sum = sum([
        result.get('cas_21_total', 0),
        result.get('cas_22_total', 0),
        result.get('cas_23_turbine', 0),
        result.get('cas_24_electrical', 0),
        result.get('cas_26_cooling', 0),
        result.get('cas_27_materials', 0),
    ])
    
    if cas_sum <= 0:
        results.record_fail(f"{test_name} - Costs", "CAS 21-27 sum is zero")
        return False
    
    # CAS 21-27 should be 40-70% of total EPC (rest is indirect, owner, contingency)
    direct_fraction = cas_sum / total_epc
    if not (0.3 <= direct_fraction <= 0.8):
        results.record_warning(f"{test_name} - Costs", 
                              f"Direct costs = {direct_fraction*100:.1f}% of EPC (expected 30-80%)")
    
    results.record_pass(f"{test_name} - Costs")
    return True


def validate_lcoe(result: Dict[str, Any], test_name: str, 
                  min_lcoe: float = 20.0, max_lcoe: float = 500.0):
    """Validate LCOE calculation."""
    lcoe = result.get('lcoe', 0)
    
    if lcoe <= 0:
        results.record_fail(f"{test_name} - LCOE", "LCOE must be > 0")
        return False
    
    if not (min_lcoe <= lcoe <= max_lcoe):
        results.record_warning(f"{test_name} - LCOE", 
                              f"LCOE={lcoe:.1f} $/MWh outside range [{min_lcoe}, {max_lcoe}]")
    
    results.record_pass(f"{test_name} - LCOE")
    return True


# =============================================================================
# TEST SUITE 1: REACTOR TYPE VALIDATION
# =============================================================================

def test_mfe_tokamak_baseline():
    """Test MFE tokamak with standard parameters."""
    print("\n" + "="*70)
    print("TEST SUITE 1.1: MFE Tokamak Baseline")
    print("="*70)
    
    config = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DT",
        "plasma_power": 450.0,
        "thermal_power": 2000.0,
        "q_plasma": 10.0,
        "thermal_efficiency": 0.40,
        "major_radius": 6.2,
        "minor_radius": 2.0,
        "plasma_height": 4.0,
        "blanket_thickness": 0.85,
        "shield_thickness": 0.75,
        "first_wall_thickness": 0.01,
        "blanket_type": "Solid Breeder (Li4SiO4)",
        "structure_material": "Ferritic Steel (FMS)",
        "first_wall_material": "Tungsten (W)",
        "magnet_type": "LTS",
        "toroidal_field_coil_current": 50.0,
    }
    
    result = compute_total_epc_cost(config)
    
    validate_output_structure(result, "MFE Tokamak")
    validate_power_balance(result, "MFE Tokamak", min_q_eng=1.0, max_q_eng=5.0)
    validate_costs(result, "MFE Tokamak")
    validate_lcoe(result, "MFE Tokamak", min_lcoe=50.0, max_lcoe=200.0)
    
    return result


def test_mfe_mirror():
    """Test MFE mirror configuration."""
    print("\n" + "="*70)
    print("TEST SUITE 1.2: MFE Mirror")
    print("="*70)
    
    config = {
        "reactor_type": "MFE Mirror",
        "fuel_type": "DT",
        "plasma_power": 400.0,
        "thermal_power": 1800.0,
        "q_plasma": 8.0,
        "thermal_efficiency": 0.38,
        "chamber_radius": 2.5,
        "chamber_length": 20.0,
        "blanket_thickness": 0.80,
        "shield_thickness": 0.70,
        "first_wall_thickness": 0.01,
        "blanket_type": "Solid Breeder (Li2TiO3)",
        "structure_material": "Ferritic Steel (FMS)",
        "first_wall_material": "Tungsten (W)",
        "magnet_type": "LTS",
    }
    
    result = compute_total_epc_cost(config)
    
    validate_output_structure(result, "MFE Mirror")
    validate_power_balance(result, "MFE Mirror", min_q_eng=0.8, max_q_eng=4.0)
    validate_costs(result, "MFE Mirror")
    validate_lcoe(result, "MFE Mirror", min_lcoe=50.0, max_lcoe=250.0)
    
    return result


def test_ife_laser():
    """Test IFE laser fusion."""
    print("\n" + "="*70)
    print("TEST SUITE 1.3: IFE Laser")
    print("="*70)
    
    config = {
        "reactor_type": "IFE Laser",
        "fuel_type": "DT",
        "plasma_power": 450.0,
        "thermal_power": 2000.0,
        "target_yield_mj": 500.0,
        "rep_rate_hz": 10.0,
        "driver_efficiency": 0.10,
        "thermal_efficiency": 0.40,
        "chamber_radius": 8.0,
        "blanket_thickness": 0.85,
        "shield_thickness": 0.75,
        "first_wall_thickness": 0.01,
        "blanket_type": "Liquid Lithium Lead (PbLi)",
        "structure_material": "Ferritic Steel (FMS)",
        "first_wall_material": "Tungsten (W)",
        "magnet_type": "Copper",  # Not used in IFE
    }
    
    result = compute_total_epc_cost(config)
    
    validate_output_structure(result, "IFE Laser")
    validate_power_balance(result, "IFE Laser", min_q_eng=0.5, max_q_eng=3.0)
    validate_costs(result, "IFE Laser")
    validate_lcoe(result, "IFE Laser", min_lcoe=40.0, max_lcoe=300.0)
    
    # IFE should have driver and target factory costs
    driver_cost = result.get('cas_2202', 0)
    target_cost = result.get('cas_2204', 0)
    
    if driver_cost > 0 and target_cost > 0:
        results.record_pass("IFE Laser - Driver & Target Costs")
    else:
        results.record_fail("IFE Laser - Driver & Target Costs", 
                          f"Driver={driver_cost}, Target={target_cost}")
    
    return result


# =============================================================================
# TEST SUITE 2: MATERIAL COMBINATIONS
# =============================================================================

def test_material_combinations():
    """Test different blanket and structure material combinations."""
    print("\n" + "="*70)
    print("TEST SUITE 2: Material Combinations")
    print("="*70)
    
    base_config = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DT",
        "plasma_power": 450.0,
        "thermal_power": 2000.0,
        "q_plasma": 10.0,
        "major_radius": 6.2,
        "minor_radius": 2.0,
        "blanket_thickness": 0.85,
        "shield_thickness": 0.75,
        "magnet_type": "LTS",
    }
    
    test_cases = [
        {
            "name": "Li4SiO4 + FS",
            "blanket_type": "Solid Breeder (Li4SiO4)",
            "structure_material": "Ferritic Steel (FMS)",
        },
        {
            "name": "Li2TiO3 + FS",
            "blanket_type": "Solid Breeder (Li2TiO3)",
            "structure_material": "Ferritic Steel (FMS)",
        },
        {
            "name": "PbLi + FS",
            "blanket_type": "Liquid Lithium Lead (PbLi)",
            "structure_material": "Ferritic Steel (FMS)",
        },
        {
            "name": "Li4SiO4 + SS",
            "blanket_type": "Solid Breeder (Li4SiO4)",
            "structure_material": "Stainless Steel (SS316)",
        },
        {
            "name": "Li4SiO4 + V",
            "blanket_type": "Solid Breeder (Li4SiO4)",
            "structure_material": "Vanadium Alloy (V)",
        },
    ]
    
    costs = []
    for case in test_cases:
        config = {**base_config, **case}
        result = compute_total_epc_cost(config)
        
        blanket_cost = result.get('cas_2201', 0)
        costs.append((case['name'], blanket_cost))
        
        if blanket_cost > 0:
            results.record_pass(f"Material - {case['name']}")
        else:
            results.record_fail(f"Material - {case['name']}", "Zero blanket cost")
    
    # Check that materials produce different costs
    costs_sorted = sorted(costs, key=lambda x: x[1])
    min_cost = costs_sorted[0][1]
    max_cost = costs_sorted[-1][1]
    
    if max_cost > min_cost * 1.1:  # At least 10% variation
        results.record_pass("Material - Cost Variation")
        print(f"\n  Material cost range: ${min_cost:.1f}M - ${max_cost:.1f}M")
        print(f"  Variation: {(max_cost/min_cost - 1)*100:.1f}%")
    else:
        results.record_warning("Material - Cost Variation", 
                              "Materials show <10% cost variation")


# =============================================================================
# TEST SUITE 3: MAGNET TYPE VALIDATION
# =============================================================================

def test_magnet_types():
    """Test all magnet types (HTS, LTS, Copper)."""
    print("\n" + "="*70)
    print("TEST SUITE 3: Magnet Types")
    print("="*70)
    
    base_config = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DT",
        "plasma_power": 450.0,
        "thermal_power": 2000.0,
        "q_plasma": 10.0,
        "major_radius": 6.2,
        "minor_radius": 2.0,
        "blanket_thickness": 0.85,
        "shield_thickness": 0.75,
        "blanket_type": "Solid Breeder (Li4SiO4)",
        "structure_material": "Ferritic Steel (FMS)",
    }
    
    magnet_types = ["HTS", "LTS", "Copper"]
    magnet_costs = []
    
    for mag_type in magnet_types:
        config = {**base_config, "magnet_type": mag_type}
        result = compute_total_epc_cost(config)
        
        magnet_cost = result.get('cas_2203', 0)
        magnet_costs.append((mag_type, magnet_cost))
        
        if magnet_cost > 0:
            results.record_pass(f"Magnet - {mag_type}")
        else:
            results.record_fail(f"Magnet - {mag_type}", "Zero magnet cost")
    
    # HTS should be most expensive, then Copper, then LTS
    magnet_costs_sorted = sorted(magnet_costs, key=lambda x: x[1], reverse=True)
    
    print(f"\n  Magnet costs:")
    for mag_type, cost in magnet_costs_sorted:
        print(f"    {mag_type}: ${cost:.1f}M")
    
    # Check reasonable cost ordering (HTS > others)
    hts_cost = next(c for t, c in magnet_costs if t == "HTS")
    lts_cost = next(c for t, c in magnet_costs if t == "LTS")
    
    if hts_cost > lts_cost * 2:  # HTS should be significantly more expensive
        results.record_pass("Magnet - Cost Ordering")
    else:
        results.record_warning("Magnet - Cost Ordering", 
                              f"HTS ({hts_cost:.1f}) not significantly > LTS ({lts_cost:.1f})")


# =============================================================================
# TEST SUITE 4: EDGE CASES
# =============================================================================

def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "="*70)
    print("TEST SUITE 4: Edge Cases")
    print("="*70)
    
    # Test 4.1: Low Q_plasma
    print("\n  Testing low Q_plasma (Q=5)...")
    config_low_q = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DT",
        "plasma_power": 250.0,
        "thermal_power": 1500.0,
        "q_plasma": 5.0,
        "major_radius": 5.0,
        "minor_radius": 1.5,
        "blanket_thickness": 0.80,
        "shield_thickness": 0.70,
        "blanket_type": "Solid Breeder (Li4SiO4)",
        "structure_material": "Ferritic Steel (FMS)",
        "magnet_type": "LTS",
    }
    
    try:
        result = compute_total_epc_cost(config_low_q)
        q_eng = result.get('q_eng', 0)
        if q_eng > 0:
            results.record_pass("Edge - Low Q_plasma")
            print(f"    Q_eng = {q_eng:.2f}")
        else:
            results.record_fail("Edge - Low Q_plasma", f"Q_eng={q_eng}")
    except Exception as e:
        results.record_fail("Edge - Low Q_plasma", str(e))
    
    # Test 4.2: High thermal power
    print("\n  Testing high thermal power (5000 MW)...")
    config_high_power = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DT",
        "plasma_power": 800.0,
        "thermal_power": 5000.0,
        "q_plasma": 15.0,
        "major_radius": 8.0,
        "minor_radius": 2.5,
        "blanket_thickness": 1.0,
        "shield_thickness": 0.85,
        "blanket_type": "Solid Breeder (Li4SiO4)",
        "structure_material": "Ferritic Steel (FMS)",
        "magnet_type": "HTS",
    }
    
    try:
        result = compute_total_epc_cost(config_high_power)
        total_epc = result.get('total_epc_cost', 0)
        if total_epc > 0:
            results.record_pass("Edge - High Power")
            print(f"    Total EPC = ${total_epc:.1f}M")
        else:
            results.record_fail("Edge - High Power", f"EPC={total_epc}")
    except Exception as e:
        results.record_fail("Edge - High Power", str(e))
    
    # Test 4.3: Non-DT fuel (DD)
    print("\n  Testing DD fuel...")
    config_dd = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DD",
        "plasma_power": 450.0,
        "thermal_power": 2000.0,
        "q_plasma": 10.0,
        "major_radius": 6.2,
        "minor_radius": 2.0,
        "blanket_thickness": 0.85,
        "shield_thickness": 0.75,
        "blanket_type": "Solid Breeder (Li4SiO4)",
        "structure_material": "Ferritic Steel (FMS)",
        "magnet_type": "LTS",
    }
    
    try:
        result = compute_total_epc_cost(config_dd)
        # DD should have lower tritium handling costs
        total_epc = result.get('total_epc_cost', 0)
        if total_epc > 0:
            results.record_pass("Edge - DD Fuel")
            print(f"    Total EPC = ${total_epc:.1f}M")
        else:
            results.record_fail("Edge - DD Fuel", f"EPC={total_epc}")
    except Exception as e:
        results.record_fail("Edge - DD Fuel", str(e))


# =============================================================================
# TEST SUITE 5: FULL CAS ACCOUNT COVERAGE
# =============================================================================

def test_cas_accounts():
    """Validate all CAS accounts are computed and non-zero."""
    print("\n" + "="*70)
    print("TEST SUITE 5: CAS Account Coverage")
    print("="*70)
    
    config = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DT",
        "plasma_power": 450.0,
        "thermal_power": 2000.0,
        "q_plasma": 10.0,
        "major_radius": 6.2,
        "minor_radius": 2.0,
        "blanket_thickness": 0.85,
        "shield_thickness": 0.75,
        "blanket_type": "Solid Breeder (Li4SiO4)",
        "structure_material": "Ferritic Steel (FMS)",
        "magnet_type": "LTS",
    }
    
    result = compute_total_epc_cost(config)
    
    cas_accounts = {
        "CAS 10": "cas_10_preconstruction",
        "CAS 21": "cas_21_total",
        "CAS 22": "cas_22_total",
        "CAS 22.01": "cas_2201",
        "CAS 22.02": "cas_2202",
        "CAS 22.03": "cas_2203",
        "CAS 22.04": "cas_2204",
        "CAS 23": "cas_23_turbine",
        "CAS 24": "cas_24_electrical",
        "CAS 26": "cas_26_cooling",
        "CAS 27": "cas_27_materials",
        "CAS 29": "cas_29_contingency",
        "CAS 30": "cas_30_indirect_costs",
    }
    
    print("\n  CAS Account Values:")
    for name, key in cas_accounts.items():
        value = result.get(key, 0)
        print(f"    {name}: ${value:.1f}M")
        
        if value > 0:
            results.record_pass(f"CAS - {name}")
        else:
            # Some accounts can legitimately be zero (CAS 10, CAS 29)
            if name in ["CAS 10", "CAS 29"]:
                results.record_warning(f"CAS - {name}", "Zero (may be intentional)")
            else:
                results.record_fail(f"CAS - {name}", "Zero cost")


# =============================================================================
# TEST SUITE 6: LCOE VALIDATION
# =============================================================================

def test_lcoe_calculation():
    """Validate LCOE calculation methodology."""
    print("\n" + "="*70)
    print("TEST SUITE 6: LCOE Validation")
    print("="*70)
    
    config = {
        "reactor_type": "MFE Tokamak",
        "fuel_type": "DT",
        "plasma_power": 450.0,
        "thermal_power": 2000.0,
        "net_electric_mw": 500.0,
        "q_plasma": 10.0,
        "major_radius": 6.2,
        "minor_radius": 2.0,
        "blanket_thickness": 0.85,
        "shield_thickness": 0.75,
        "blanket_type": "Solid Breeder (Li4SiO4)",
        "structure_material": "Ferritic Steel (FMS)",
        "magnet_type": "LTS",
    }
    
    result = compute_total_epc_cost(config)
    
    lcoe = result.get('lcoe', 0)
    total_epc = result.get('total_epc_cost', 0)
    pb = result.get('power_balance', {})
    p_net = pb.get('p_net', 0)
    
    print(f"\n  Total EPC:     ${total_epc:.1f}M")
    print(f"  P_net:         {p_net:.1f} MW")
    print(f"  LCOE:          {lcoe:.1f} $/MWh")
    
    # Rough check: LCOE should correlate with EPC/P_net
    if p_net > 0:
        simple_lcoe_estimate = (total_epc * 1e6 * 0.09) / (8760 * p_net * 0.75)
        print(f"  Simple estimate: {simple_lcoe_estimate:.1f} $/MWh (9% CRF, 75% avail)")
        
        # Should be within 50% (rough check - includes O&M, fuel, etc.)
        if 0.5 * simple_lcoe_estimate < lcoe < 2.0 * simple_lcoe_estimate:
            results.record_pass("LCOE - Calculation")
        else:
            results.record_warning("LCOE - Calculation", 
                                  f"LCOE significantly different from simple estimate")
    else:
        results.record_fail("LCOE - Calculation", "P_net is zero")
    
    # Check LCOE is in reasonable range for fusion
    if 30 < lcoe < 300:
        results.record_pass("LCOE - Range")
    else:
        results.record_warning("LCOE - Range", 
                              f"LCOE={lcoe:.1f} outside typical fusion range (30-300 $/MWh)")


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all test suites."""
    print("="*70)
    print("PyFECONS PORT - COMPREHENSIVE TEST SUITE (Phase 7)")
    print("="*70)
    
    try:
        # Suite 1: Reactor types
        test_mfe_tokamak_baseline()
        test_mfe_mirror()
        test_ife_laser()
        
        # Suite 2: Materials
        test_material_combinations()
        
        # Suite 3: Magnets
        test_magnet_types()
        
        # Suite 4: Edge cases
        test_edge_cases()
        
        # Suite 5: CAS accounts
        test_cas_accounts()
        
        # Suite 6: LCOE
        test_lcoe_calculation()
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    return results.print_summary()


if __name__ == "__main__":
    sys.exit(run_all_tests())
