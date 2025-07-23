# Fusion Cashflow App

A comprehensive financial modeling engine and interactive dashboard for analyzing fusion power plant lifetime cash flows. This application provides advanced financial modeling capabilities with integrated ARPA-E cost models, Q-engineering calculations, and professional-grade visualization tools.

## Features

- ** Multi-Technology Support**: MFE (Magnetic Fusion Energy), IFE (Inertial Fusion Energy), and PWR (Pressurized Water Reactor) power methods
- ** Interactive Dashboard**: Real-time Bokeh-based dashboard with comprehensive controls
- ** ARPA-E Integration**: Automated EPC cost calculations using ARPA-E methodologies
- ** Q-Engineering Models**: Advanced plasma physics calculations for fusion scenarios
- ** Sensitivity Analysis**: Multi-parameter sensitivity analysis with heatmap visualizations
- ** Financial Modeling**: Complete LCOE, IRR, NPV, payback, and DSCR calculations
- ** Stress Testing**: Comprehensive test suite with 100% model robustness validation

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd fusion_cashflow_app
```

2. **Create and activate a virtual environment** (recommended):
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. **Install required packages**:
```bash
pip install -r requirements.txt
```

## Usage

### Launch the Interactive Dashboard

The main way to use the application is through the interactive Bokeh dashboard:

```bash
python -m bokeh serve src\fusion_cashflow\ui\dashboard.py --show
```

This opens a browser window with:
- **Real-time financial calculations** as you adjust parameters
- **Multi-tab interface** with main results and sensitivity analysis
- **Professional visualizations** including cash flow plots, DSCR profiles, and waterfall charts
- **Data export capabilities** with CSV download buttons

### Generate Static HTML Reports

For batch processing or report generation:

```bash
python src/fusion_cashflow/reporting/report_builder.py
```

This generates comprehensive HTML reports with all financial analysis and visualizations.

## Project Structure

```
fusion_cashflow_app/
├── src/fusion_cashflow/           # Main package
│   ├── core/                      # Financial engine & models
│   │   ├── cashflow_engine.py     # Main financial calculations
│   │   ├── power_to_epc.py        # ARPA-E cost models
│   │   └── q_model.py             # Q-engineering calculations
│   ├── ui/                        # User interfaces
│   │   └── dashboard.py           # Interactive Bokeh dashboard
│   ├── visualization/             # Plotting functions
│   │   └── bokeh_plots.py         # Professional visualizations
│   └── reporting/                 # Report generation
│       └── report_builder.py      # HTML report generator
├── tests/                         # Comprehensive test suite
│   ├── stress/                    # Stress testing (15 tests)
│   └── unit/                      # Unit tests (core functionality)
├── examples/                      # Usage examples
└── requirements.txt               # Dependencies
```

## Testing

The application includes a comprehensive test suite with 100% model robustness validation:

```bash
# Run all tests
python -m pytest tests/ -v

# Run stress tests only
python -m pytest tests/stress/ -v

# Run unit tests only  
python -m pytest tests/unit/ -v
```

**Test Coverage:**
-  Stress testing with extreme scenarios
-  Property-based testing with random inputs
-  Memory usage and performance validation
-  All power methods (MFE, IFE, PWR) validated

## Configuration

The application supports multiple power methods with automatic parameter switching:

- **MFE (Magnetic Fusion Energy)**: ITER-class tokamak configurations
- **IFE (Inertial Fusion Energy)**: Laser-driven fusion systems  
- **PWR (Pressurized Water Reactor)**: Fission benchmark comparison

Each power method has optimized default parameters and fuel type configurations.

## Key Financial Metrics

The application calculates all standard project finance metrics:

- **LCOE** (Levelized Cost of Energy)
- **IRR** (Internal Rate of Return)
- **NPV** (Net Present Value)
- **Payback Period**
- **DSCR** (Debt Service Coverage Ratio)
- **Total Overnight Cost (TOC)**

## Advanced Features

### ARPA-E Cost Integration
- Automated EPC cost calculations based on net power output
- Regional cost factors for global project locations
- FOAK (First of a Kind) vs NOAK (Nth of a Kind) cost models

### Q-Engineering Models
- Physics-based Q calculations for fusion scenarios
- Technology-specific Q optimization
- Manual override capabilities for advanced users

### Sensitivity Analysis
- Multi-parameter sensitivity analysis
- Interactive heatmap visualizations
- Parameter correlation analysis

## Development

### Adding New Features
1. Core financial logic goes in `src/fusion_cashflow/core/`
2. Visualization functions in `src/fusion_cashflow/visualization/`
3. UI components in `src/fusion_cashflow/ui/`
4. Add tests in appropriate `tests/` subdirectory

### Dependencies
All required packages are listed in [`requirements.txt`](requirements.txt). Key dependencies include:
- `bokeh` - Interactive visualizations
- `pandas` - Data manipulation
- `numpy` - Numerical calculations
- `pytest` - Testing framework
- `hypothesis` - Property-based testing
