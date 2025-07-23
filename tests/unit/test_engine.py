def test_run_cashflow_scenario_basic():
    import sys
    import os
    # Add src to path for proper imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    
    from fusion_cashflow.core.cashflow_engine import (
        get_default_config,
        run_cashflow_scenario,
    )

    config = get_default_config()
    outputs = run_cashflow_scenario(config)
    # Check for key outputs
    assert "npv" in outputs
    assert "irr" in outputs
    assert "df" in outputs
    assert isinstance(outputs["npv"], (int, float))
    assert isinstance(outputs["irr"], (int, float))
    assert hasattr(outputs["df"], "to_csv")
