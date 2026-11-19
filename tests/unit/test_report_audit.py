"""Regression cases for report evidence, units, and missing data."""

import pytest

from osdagbridge.core.reports.chap2 import _girder_tables, bracing_selection_table
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap6 import ch6_drawings
from osdagbridge.core.reports.design_results import (
    Status, aggregate_status, collect_design_checks, deck_detail_checks, grillage_deflections,
)
from osdagbridge.core.reports.executive_summary import executive_summary
from osdagbridge.core.reports.inputs import prepare_report_inputs
from osdagbridge.core.reports.report_generator import ReportDataBridge
from osdagbridge.core.reports.report_utils import quantity
from osdagbridge.core.utils import common as keys


def test_fatigue_and_grillage_deflections_are_independent_and_mandatory():
    inputs = {keys.KEY_SPAN: 20, keys.KEY_TS_NO_OF_GIRDERS: 1}
    outputs = {
        f"{keys.KEY_SD_DEFL_LIVE}.G1": 38.791,
        f"{keys.KEY_SD_DEFL_TOTAL}.G1": 72.736,
        "report_deflection_cases": {keys.KEY_SD_DEFL_LIVE: "1.0 LL",
                                    keys.KEY_SD_DEFL_TOTAL: "1.0 DL + 1.0 LL"},
        "design_results": {"per_girder": {"G1": {
            "checks": [{"check_id": 8, "name": "Fatigue Normal Stress", "dcr": 2.6055,
                        "status": "FAIL", "demand": 240.98, "capacity": 92.49}],
            "per_lc": {"1.0 DL + 1.0 LL": {"checks": [
                {"id": 14, "label": "SLS Deflection (Total)", "demand": 25.10,
                 "capacity": 33.33, "dcr": 0.753, "status": "PASS"},
            ]}},
        }}},
    }
    checks = list(collect_design_checks(inputs, outputs))
    assert aggregate_status(checks) == Status.FAIL
    live, total = grillage_deflections(inputs, outputs)
    assert live.capacity == 25
    assert total.ratio == pytest.approx(2.18208)
    assert total.combination == "1.0 DL + 1.0 LL"
    assert live.status == total.status == Status.FAIL
    assert any(check.ratio == 0.753 and "stiffness-adjusted" in check.name for check in checks)
    report = executive_summary(inputs, outputs, {})
    assert "Live-load deflection" in report and "Total-load deflection" in report
    assert "2.61" in report and "72.736" in report
    detail = ch5_design_checks([], ReportDataBridge(outputs, inputs, None))
    assert "72.736" in detail and "2.18" in detail and "38.791" in detail


def test_missing_inputs_do_not_imply_pass():
    inputs = {keys.KEY_TS_NO_OF_GIRDERS: 1, keys.KEY_SPAN: 20,
              keys.KEY_PROJECT_LOCATION: {"data": {"latitude": 0}, "weather_data": {"wind_speed": 44}}}
    values = prepare_report_inputs(inputs, {}, "Bridge site")
    assert values["latitude"] == 0 and values["wind_speed"] == 44
    assert "latitude" not in inputs
    assert any("longitude" in warning for warning in values["report_input_warnings"])
    assert "wind_speed_used" not in values
    assert aggregate_status(collect_design_checks(values, {})) == Status.NOT_EVALUATED
    assert {check.status for check in deck_detail_checks({})} == {Status.NOT_EVALUATED}
    assert all(check.demand is None for check in grillage_deflections(values, {}))


def test_girder_dimensions_have_one_conversion_and_consistent_precision():
    data = {
        f"{keys.KEY_MP_GIRDER_DEPTH}.G1.M1": 1.12,
        f"{keys.KEY_MP_GIRDER_WEB_THICKNESS}.G1.M1": 0.008,
        f"{keys.KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G1.M1": 0.34,
        f"{keys.KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G1.M1": 0.016,
        keys.KEY_TS_NO_OF_GIRDERS: 1,
    }
    source = _girder_tables(data, 1)
    assert "1120 & 8 & 340, 16" in source
    assert quantity(10.274999999999999, "m") == "10.275 m"
    assert quantity("nan", "mm") == "Calculation failed"
    assert quantity(None, "kN") == "Not calculated"


def test_initial_and_design_selected_bracing_are_distinct():
    inputs = {f"{keys.KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G1G2.B1M1": "IS 100 x 100 x 10"}
    outputs = {"crossbracing_design_results": {
        "G1-G2": {"diagonal": {"compression": {"Optimum.Designation": "40 x 40 x 3"}}},
    }}
    table = bracing_selection_table(inputs, outputs)
    assert "Initial Section" in table and "Design Section" in table
    assert "IS 100 x 100 x 10 & 40 x 40 x 3" in table


def test_diaphragm_status_never_inherits_cross_bracing_results():
    outputs = {"crossbracing_design_results": {
        "G1-G2": {"diagonal": {"compression": {"Optimum.UR": 1.2, "Design.Strength": 10}}},
    }}
    checks = list(collect_design_checks({}, outputs))
    assert aggregate_status(check for check in checks if check.component == "Cross Bracing") == Status.FAIL
    diaphragm = [check for check in checks if check.component == "End Diaphragm"]
    assert len(diaphragm) == 1 and diaphragm[0].status == Status.NOT_EVALUATED
    assert diaphragm[0].capacity is None


def test_optional_drawings_have_captions_only_when_present():
    source = ch6_drawings({"girder_top": "images/top.png"})
    assert r"\caption{Top View}" in source
    assert "Drawing unavailable: Typical Cross Section" in source
    assert r"\caption{Typical Cross Section}" not in source
    assert "PLACEHOLDER" not in source
