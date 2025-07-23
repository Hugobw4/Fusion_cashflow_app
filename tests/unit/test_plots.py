def test_plot_functions():
    import sys
    import os
    # Add src to path for proper imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
    
    from fusion_cashflow.core.cashflow_engine import (
        get_default_config,
        run_cashflow_scenario,
        run_sensitivity_analysis,
    )
    from fusion_cashflow.visualization import bokeh_plots

    config = get_default_config()
    outputs = run_cashflow_scenario(config)
    sensitivity_df = run_sensitivity_analysis(config)
    # Test all plot functions
    figs = [
        bokeh_plots.plot_annual_cashflow_bokeh(outputs, config),
        bokeh_plots.plot_cumulative_cashflow_bokeh(outputs, config),
        bokeh_plots.plot_dscr_profile_bokeh(outputs, config),
        bokeh_plots.plot_cashflow_waterfall_bokeh(outputs, config),
        bokeh_plots.plot_sensitivity_heatmap(outputs, config, sensitivity_df),
    ]
    for fig in figs:
        assert fig is not None
        # Bokeh figures/layouts have a 'select' method
        assert hasattr(fig, "select")
