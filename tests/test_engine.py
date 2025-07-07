def test_run_cashflow_scenario_basic():
    from fusion_cashflow_app.cashflow_engine import (
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
