"""
Test embedded costing calculations
Tests the internal costing module without PyFECONS dependency
"""
import pytest
from src.fusion_cashflow.costing import compute_total_epc_cost


def test_mfe_tokamak_basic():
    """Test basic MFE tokamak costing calculation"""
    config = {
        "reactor_type": "MFE",
        "confinement_type": "tokamak",
        "fuel_type": "DT",
        "noak": True,
        
        # Power parameters
        "p_nrl_fusion_power_mw": 500.0,
        "auxiliary_power_mw": 50.0,
        "thermal_efficiency": 0.46,
        
        # Geometry
        "major_radius_m": 3.0,
        "plasma_t": 0.5,
        "vacuum_t": 0.1,
        "firstwall_t": 0.02,
        "blanket_t": 0.6,
        "reflector_t": 0.05,
        "ht_shield_t": 0.4,
        "structure_t": 0.3,
        "gap_t": 0.05,
        "vessel_t": 0.1,
        "coil_t": 0.8,
        "elongation": 1.8,
        
        # Materials
        "first_wall_material": "tungsten",
        "blanket_type": "solid_breeder",
        "structure_material": "ODS",
        
        # Magnets
        "magnet_technology": "HTS",
        "toroidal_field_tesla": 9.0,
        "n_tf_coils": 18,
        "tape_width_m": 0.004,
        "coil_thickness_m": 0.8,
    }
    
    result = compute_total_epc_cost(config)
    
    # Basic sanity checks
    assert result is not None
    assert "total_epc_cost" in result
    assert "power_balance" in result
    assert "q_eng" in result
    
    # Check Q_eng is reasonable (should be > 1 for viable reactor)
    q_eng = result["q_eng"]
    assert q_eng > 1.0, f"Q_eng should be > 1.0, got {q_eng}"
    assert q_eng < 50.0, f"Q_eng suspiciously high: {q_eng}"
    
    # Check total cost is reasonable (ballpark $2-20B for 500MW reactor)
    total_cost_billions = result["total_epc_cost"] / 1000.0  # Convert M$ to B$
    assert total_cost_billions > 0.5, f"Total cost too low: ${total_cost_billions:.1f}B"
    assert total_cost_billions < 50.0, f"Total cost too high: ${total_cost_billions:.1f}B"
    
    # Check cost per kW is in fusion range ($5k-$15k/kW)
    cost_per_kw = result["epc_per_kw_net"]
    assert cost_per_kw > 2000, f"Cost/kW too low: ${cost_per_kw:.0f}/kW"
    assert cost_per_kw < 30000, f"Cost/kW too high: ${cost_per_kw:.0f}/kW"
    
    # Check major cost categories exist
    assert "cas_21_total" in result, "Missing buildings cost"
    assert "cas_22_total" in result, "Missing reactor equipment cost"
    assert result["cas_22_total"] > 0, "Reactor equipment cost should be positive"
    
    print(f"\n✅ MFE Test Results:")
    print(f"   Q_eng: {q_eng:.2f}")
    print(f"   Net Power: {result['power_balance']['p_electric_net']:.1f} MW")
    print(f"   Total EPC: ${total_cost_billions:.2f}B")
    print(f"   Cost/kW: ${cost_per_kw:.0f}/kW")
    print(f"   Buildings: ${result['cas_21_total']:.0f}M")
    print(f"   Reactor Equipment: ${result['cas_22_total']:.0f}M")
    print(f"   Magnets: ${result.get('cas_2203', 0):.0f}M")


def test_ife_basic():
    """Test basic IFE costing calculation"""
    config = {
        "reactor_type": "IFE",
        "confinement_type": "laser",
        "fuel_type": "DT",
        "noak": True,
        
        # Power parameters
        "p_nrl_fusion_power_mw": 1000.0,
        "auxiliary_power_mw": 100.0,
        "thermal_efficiency": 0.46,
        
        # IFE geometry
        "chamber_radius_m": 5.0,
        "firstwall_t": 0.5,
        "blanket_t": 0.8,
        "reflector_t": 0.1,
        "ht_shield_t": 0.6,
        "structure_t": 0.4,
        "vessel_t": 0.15,
        
        # Materials
        "first_wall_material": "tungsten",
        "blanket_type": "solid_breeder",
        "structure_material": "FMS",
        
        # IFE specific
        "driver_energy_mj": 2.0,
    }
    
    result = compute_total_epc_cost(config)
    
    # Basic checks
    assert result is not None
    assert result["total_epc_cost"] > 0
    
    # IFE should not have magnet costs
    magnet_cost = result.get("cas_2203", 0)
    assert magnet_cost == 0 or magnet_cost < 1.0, f"IFE should have zero/minimal magnet costs, got ${magnet_cost}M"
    
    print(f"\n✅ IFE Test Results:")
    print(f"   Q_eng: {result['q_eng']:.2f}")
    print(f"   Net Power: {result['power_balance']['p_electric_net']:.1f} MW")
    print(f"   Total EPC: ${result['total_epc_cost']/1000:.2f}B")
    print(f"   Cost/kW: ${result['epc_per_kw_net']:.0f}/kW")


def test_power_scaling():
    """Test that costs scale reasonably with power"""
    base_config = {
        "reactor_type": "MFE",
        "fuel_type": "DT",
        "noak": True,
        "p_nrl_fusion_power_mw": 500.0,
        "auxiliary_power_mw": 50.0,
        "thermal_efficiency": 0.46,
        "major_radius_m": 3.0,
        "magnet_technology": "HTS",
        "toroidal_field_tesla": 9.0,
    }
    
    result_500mw = compute_total_epc_cost(base_config)
    
    # Double the power
    high_power_config = base_config.copy()
    high_power_config["p_nrl_fusion_power_mw"] = 1000.0
    result_1000mw = compute_total_epc_cost(high_power_config)
    
    # Cost should increase, but not linearly (should scale like ~P^0.6 due to economies of scale)
    cost_ratio = result_1000mw["total_epc_cost"] / result_500mw["total_epc_cost"]
    assert cost_ratio > 1.0, "Higher power should cost more"
    assert cost_ratio < 2.0, "Cost should not scale linearly with power"
    
    print(f"\n✅ Power Scaling Test:")
    print(f"   500MW cost: ${result_500mw['total_epc_cost']:.0f}M")
    print(f"   1000MW cost: ${result_1000mw['total_epc_cost']:.0f}M")
    print(f"   Cost ratio: {cost_ratio:.2f}x (should be 1.0-2.0x)")


if __name__ == "__main__":
    print("Testing embedded costing calculations...\n")
    test_mfe_tokamak_basic()
    test_ife_basic()
    test_power_scaling()
    print("\n✅ All tests passed!")
