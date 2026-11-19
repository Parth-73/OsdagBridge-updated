"""Report presentation and LaTeX compilation regressions."""

from pathlib import Path
import re
import shutil
import subprocess

from matplotlib.axes import Axes
import pytest

from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.charts import generate_quantity_chart, generate_utilization_charts
from osdagbridge.core.reports.report_generator import (
    ReportDataBridge, ReportMetadata, ReportOptions, ReportRequest,
    build_report_payload, generate_report,
)
from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.common import (
    KEY_DD_MU_BOT, KEY_FOOTPATH, KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_TRACKED, KEY_LL_IRC_CLASS_A, KEY_SPAN,
    KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH, KEY_WC_LD_LANE_TABLE_COUNT,
)


def _table(source, caption):
    start = source.index(caption)
    return source[start:source.index(r"\end{longtable}", start)]


def test_headers_repeat_without_copying_combination_rows():
    table = _table(ch3_loads({}), "caption{\\textbf{Load Combinations}")
    first_page, continuation = table.split(r"\endfirsthead")
    continuation, body = continuation.split(r"\endhead")
    assert "Combination ID" in first_page and "Combination ID" in continuation
    assert table.count(r"\endhead") == 1
    for combination in ("ULS-01", "SLS-07"):
        assert body.count(combination) == table.count(combination) == 1


def test_vehicle_selections_and_automatic_footpath():
    source = ch3_loads({
        KEY_LL_IRC_CLASS_A: True, KEY_LL_IRC_70R_TRACKED: "False", KEY_SPAN: 20,
        KEY_LL_CUSTOM_VEHICLES: [{"name": r"Custom & transport_#1\trial"}],
        KEY_FOOTPATH: "Single Side", KEY_TS_FOOTPATH_WIDTH: 1.5,
        KEY_LL_FOOTPATH_PRESSURE_MODE: "Automatic", KEY_LL_FOOTPATH_PRESSURE_VALUE: 99,
    })
    vehicle = _table(source, "Vehicle Live Loads (LL)}")
    footpath = _table(source, "Footpath Live Loads}")
    assert "Class A &" in vehicle
    assert "Class 70R (Tracked)" not in vehicle
    assert r"Custom \& transport\_\allowbreak{}\#1\textbackslash{}trial" in vehicle
    assert f"{IRC6_2017.cl_206_1_footway_load():.3f}" in footpath
    assert "99" not in footpath
    assert "1.5 & m" in footpath


def test_braking_helper_missing_value_does_not_break_report():
    source = ch3_loads({KEY_LL_IRC_CLASS_A: True, KEY_WC_LD_LANE_TABLE_COUNT: 2})
    assert "Lane-based braking load (IRC 6 Cl. 211.2): unavailable." in source


@pytest.mark.parametrize("configuration,value,expected", [
    ({KEY_FOOTPATH: "None"}, 8, "Not Applicable"),
    ({KEY_FOOTPATH: "Both Sides"}, 0, r"0 & kN/mm\textsuperscript{2}"),
    ({KEY_FOOTPATH: "Both Sides"}, None, "Unavailable"),
    ({}, None, "Unavailable"),
])
def test_optional_and_custom_footpath(configuration, value, expected):
    source = ch3_loads({**configuration, KEY_LL_FOOTPATH_PRESSURE_MODE: "Custom",
                       KEY_LL_FOOTPATH_PRESSURE_VALUE: value})
    assert expected in _table(source, "Footpath Live Loads}")


def test_utilization_chart_threshold_and_files(tmp_path, monkeypatch):
    observed = {}
    barh, axvline = Axes.barh, Axes.axvline

    def bars(self, labels, values, **kwargs):
        observed["bars"] = (labels, values, kwargs["color"])
        return barh(self, labels, values, **kwargs)

    def line(self, x, **kwargs):
        observed["line"] = (x, kwargs["linestyle"])
        return axvline(self, x, **kwargs)

    monkeypatch.setattr(Axes, "barh", bars)
    monkeypatch.setattr(Axes, "axvline", line)
    paths = generate_utilization_charts([("Zero", 0), ("Limit", 1.0), ("Fail", 1.001),
                                        ("Unknown", None), ("Invalid", float("nan"))], tmp_path)
    labels, values, colors = observed["bars"]
    assert labels == ("Zero", "Limit", "Fail")
    assert values == (0, 1.0, 1.001)
    assert colors[0] == colors[1] != colors[2]
    assert observed["line"] == (1.0, "--")
    assert (tmp_path / Path(paths[0]).name).read_bytes().startswith(b"\x89PNG")
    assert generate_utilization_charts([("Unknown", None)], tmp_path) == []
    assert len(generate_utilization_charts([(f"Check {i}", i / 10) for i in range(14)], tmp_path)) == 2


def test_summary_reuses_raw_values_and_skips_missing(tmp_path, monkeypatch):
    outputs = {"design_results": {"per_girder": {"G1": {"checks": [
        {"check_id": 1, "dcr": 1.001, "demand": 100.1, "capacity": 100},
        {"check_id": 2, "dcr": None},
    ]}}}, "deck_report_values": {KEY_DD_MU_BOT: 100.0}}
    chart_values = {}
    def capture(rows, directory):
        chart_values.update(rows)
        return []
    monkeypatch.setattr("osdagbridge.core.reports.chap5.generate_utilization_charts", capture)
    bridge = ReportDataBridge(outputs, {KEY_TS_NO_OF_GIRDERS: 1}, None)
    report = ch5_design_checks([], bridge, image_dir=tmp_path)
    summary = _table(report, "Overall Design Check Summary --- All Members")
    assert chart_values["Girder – Moment"] == 1.001
    assert chart_values["Girder – Shear"] is None
    assert chart_values["Deck – Flexure (sagging)"] is None
    assert r"\textcolor{reportFailure}{1.00}" in summary
    for caption in ("Girder Section Properties", "Shear Capacity Check", "Interaction Checks"):
        assert r"\endfirsthead" in _table(report, caption)


def test_material_charts_reuse_bill_of_materials_keys(tmp_path):
    source = ch7_quantities({"steel_girders_wt_total": "14.06", "concrete_deck_vol_total": "43.12",
                            "rebar_deck_wt_total": "0.00"}, image_dir=tmp_path)
    for name in ("structural_steel", "concrete", "reinforcement"):
        assert f"images/{name}.png" in source
        assert (tmp_path / f"{name}.png").read_bytes().startswith(b"\x89PNG")
    assert generate_quantity_chart([("Unknown", "N.A.")], tmp_path, "empty.png", "Empty", "MT") is None
    assert not (tmp_path / "empty.png").exists()


def test_tex_escapes_special_characters_once():
    assert _tex(r"\{_%$#&^~}") == (
        r"\textbackslash{}\{\_\allowbreak{}\%\$\#\&\textasciicircum{}\textasciitilde{}\}"
    )


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex is unavailable")
@pytest.mark.parametrize("long_report", [False, True])
def test_generate_report_compiles(tmp_path, long_report):
    metadata = ReportMetadata("Project_" + "W" * 70 + " & Co", "", "", "", "")
    sections = ["loads", "analysis", "design_checks"] if long_report else ["loads"]
    options = ReportOptions(sections, long_report, long_report, True)
    request = ReportRequest(metadata, options, str(tmp_path), "Verification")
    inputs = {KEY_TS_NO_OF_GIRDERS: 4 if long_report else 0, KEY_SPAN: 20,
              KEY_FOOTPATH: "Single Side" if long_report else "None",
              KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6"}
    if long_report:
        inputs.update({KEY_TS_OVERALL_WIDTH: 9.5, KEY_TS_DECK_THICKNESS: 200})
    results = {"design_results": {"per_girder": {"G1": {"checks": [
        {"check_id": 1, "dcr": 1.25, "demand": 125, "capacity": 100},
    ]}}}}
    report = generate_report(build_report_payload(request, inputs, results), request)
    assert report.tex_path and Path(report.tex_path).is_file()
    assert report.pdf_path and Path(report.pdf_path).read_bytes().startswith(b"%PDF-")
    if shutil.which("pdftotext"):
        extracted = subprocess.check_output(["pdftotext", report.pdf_path, "-"], text=True)
        pages = [page for page in extracted.split("\f") if page.strip()]
        assert [int(re.search(r"Page (\d+) of", page)[1]) for page in pages] == list(range(1, len(pages) + 1))
        assert "Vehicle Live Loads" in extracted and "Footpath Live Loads" in extracted
    if long_report and shutil.which("pdfimages"):
        images = subprocess.check_output(["pdfimages", "-list", report.pdf_path], text=True)
        assert sum(line.split()[2] == "image" for line in images.splitlines()[2:]) >= 4
        source = Path(report.tex_path).read_text()
        for name in ("utilization_1", "concrete", "reinforcement"):
            assert f"images/{name}.png" in source
