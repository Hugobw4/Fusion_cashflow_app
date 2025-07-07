# Fusion Cashflow App

This repository contains a basic finance engine and Bokeh visualizations for modelling a fusion plant's lifetime cash flow.

## Installation

Create a virtual environment (optional) and install the required packages:

```bash
pip install -r requirements.txt
```

## Generate the HTML report

Running the application will produce an HTML report with plots and tables.

```bash
python app.py
```

The output file `whole_life_cashflow_report.html` will appear in the project directory.

## Launch the interactive dashboard

To explore the cash‑flow model interactively, start the Bokeh server:

```bash
bokeh serve --show dashboard.py
```

This opens a browser window with sliders and controls for the model.

## Development

The required Python packages are listed in [`requirements.txt`](requirements.txt).  Tests can be executed with `pytest`.
