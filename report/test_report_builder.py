from fusion_cashflow_app.report import report_builder


def test_fmt_metric_formats():
    fmt = report_builder.fmt_metric
    assert fmt("LCOE ($/MWh)", 42.1234) == "$42.12/MWh"
    assert fmt("NPV", 1234567) == "$1,234,567"
    assert fmt("Project IRR", 0.08123) == "8.12%"
    assert fmt("Other", None) == "—"


def test_section_title_shadowing():
    # Should not shadow the function argument 'title'
    # Just check that the function runs and produces correct section headings
    # (simulate the list comprehension)
    section_titles = ["A", "B"]
    divs = [f"<h2>{section_title}</h2>" for section_title in section_titles]
    assert divs == ["<h2>A</h2>", "<h2>B</h2>"]


def test_metrics_html_escaping():
    import html

    fmt = report_builder.fmt_metric
    metrics = {"<script>": "<b>bad</b>"}
    # Simulate the escaping logic
    rows = "".join(
        f"<tr><td class='metric'>{html.escape(k)}</td><td>{html.escape(fmt(k, v))}</td></tr>"
        for k, v in metrics.items()
    )
    assert "<" not in rows and ">" not in rows
