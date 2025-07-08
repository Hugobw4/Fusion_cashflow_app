import os
import re
import tempfile
from bokeh.models import Div, Spacer
from fusion_cashflow_app.report import report_builder
from jinja2 import Environment, FileSystemLoader

def test_external_css_link_present():
    # Render the header template and check for CSS link
    template_dir = os.path.join(os.path.dirname(report_builder.__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_header.html")
    html = template.render(title="Test", project_name="Proj", scenario_name="Base", now="2025-07-04 12:00")
    assert '<link rel="stylesheet" href="../static/report_style.css">' in html

def test_jinja_title_render():
    template_dir = os.path.join(os.path.dirname(report_builder.__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_header.html")
    html = template.render(title="TestTitle", project_name="FusionX", scenario_name="ScenarioY", now="2025-07-04 12:00")
    assert "FusionX — Whole-Life Cash Flow Report" in html
    assert "Scenario: <b>ScenarioY</b>" in html

def test_add_section_appends_correct_children():
    layout = []
    fig = Div(text="<div>plot</div>")
    tbl = Div(text="<div>table</div>")
    csv = "test.csv"
    report_builder.add_section(layout, "Section Heading", fig, tbl, csv)
    # Should append heading, fig, tbl, csv-link
    assert any(isinstance(x, Div) and "Section Heading" in x.text for x in layout)
    assert fig in layout
    assert tbl in layout
    assert any(isinstance(x, Div) and "Download CSV" in x.text for x in layout)

def test_save_bokeh_report_runs(tmp_path):
    # Minimal smoke test: should not error and should output a file
    metrics = {"LCOE per MWh": 42.1, "NPV": 1234567}
    fig = Div(text="<div>plot</div>")
    tbl = Div(text="<div>table</div>")
    out_html = tmp_path / "test_report.html"
    report_builder.save_bokeh_report(
        figures=[fig, tbl],
        metrics=metrics,
        filename=str(out_html),
        project_name="FusionX",
        scenario_name="ScenarioY",
    )
    assert out_html.exists()
    # Check for CSS link in output file
    with open(out_html, encoding="utf-8") as f:
        html = f.read()
    assert "report_style.css" in html
    assert "FusionX" in html and "Whole-Life Cash Flow Report" in html
    assert "ScenarioY" in html
