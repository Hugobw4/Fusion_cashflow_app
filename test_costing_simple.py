#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for costing panel functionality - simplified version
"""

from src.fusion_cashflow.core.cashflow_engine import run_cashflow_scenario, get_default_config
from src.fusion_cashflow.ui.costing_panel import create_costing_panel

def test_costing_panel():
    """Test costing panel with a sample MFE configuration."""
    
    # Get default config and customize for testing
    config = get_default_config()
    config["net_electric_power_mw"] = 1000
    config["power_method"] = "MFE"
    config["override_epc"] = False
    
    print("="*60)
    print("Testing Costing Panel")
    print("="*60)
    
    # Run cashflow scenario
    print("\n1. Running cashflow scenario...")
    outputs = run_cashflow_scenario(config)
    print(f"   Total EPC: ${outputs['total_epc_cost']/1e9:.2f}B")
    
    # Check for EPC breakdown  
    epc_breakdown = outputs.get("epc_breakdown", {})
    print(f"\n2. EPC breakdown present: {bool(epc_breakdown)}")
    
    if epc_breakdown:
        print(f"   - Total: ${epc_breakdown['total_epc']/1e9:.2f}B")
        print(f"   - Per kW: ${epc_breakdown['epc_per_kw']:,.0f}/kW")
        
        # Create costing panel
        print(f"\n3. Creating costing panel...")
        panel = create_costing_panel(epc_breakdown)
        print(f"   Panel created: {type(panel).__name__}")
        return True
    else:
        print("   ERROR: No breakdown available")
        print(f"   Config has _epc_breakdown: {'_epc_breakdown' in config}")
        if '_epc_breakdown' in config:
            bd = config['_epc_breakdown']
            print(f"   Breakdown keys: {list(bd.keys())}")
        return False

if __name__ == "__main__":
    success = test_costing_panel()
    print(f"\n{'='*60}")
    print(f"Test {'PASSED' if success else 'FAILED'}")
    print(f"{'='*60}")
    exit(0 if success else 1)
