
# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
from .charts import generate_utilization_charts
from .styles import UR_LIMIT, break_long_words
from .design_results import DEFLECTION_CRITERIA, Status, governing, grillage_deflections, girder_design_checks, deck_detail_checks
from .tables import completed_rows, repeated_header
from .report_utils import _chart_figure, _finite_number, quantity
from typing import TYPE_CHECKING

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_D_BOT,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_MP_ED_TYPE,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries

if TYPE_CHECKING:
    pass
def ch5_design_checks(checks_data, bridge, *, image_dir=None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (currently unused; data is sourced from bridge).
    bridge : ReportDataBridge
        Provides input_dict, output_dict, and helper methods.
    """
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    n_girders = len(girder_entries)

    # Deck slab design report values (Tables 5.17(a)-(g)), keyed to
    # common.KEY_DD_*. Populated by deckdesign.design_deck_slab(); empty
    # dict when deck design has not been run. Look up with deck_rpt.get(KEY_...).
    deck_rpt = bridge.output_dict.get("deck_report_values", {}) or {}

    # Each girder gets its own solved section record. Older snapshots can
    # still show the normalized input dimensions without assigning shared capacities.
    t51_rows = []
    sections = (bridge.output_dict.get("design_results") or {}).get("per_girder") or {}
    for index, (label, _) in enumerate(girder_entries, 1):
        props = (sections.get(f"G{index}") or {}).get("section_report_values") or {}
        rows = []
        for title, key, source_key, unit, scale in (
            ("Depth, $D$", "depth_mm", KEY_MP_GIRDER_DEPTH, "mm", 1),
            ("Top Flange Width, $b_f$", "top_width_mm", KEY_MP_GIRDER_TOP_FLANGE_WIDTH, "mm", 1),
            ("Bottom Flange Width, $b_f$", "bottom_width_mm", KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, "mm", 1),
            ("Top Flange Thickness, $t_f$", "top_thickness_mm", KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, "mm", 1),
            ("Bottom Flange Thickness, $t_f$", "bottom_thickness_mm", KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, "mm", 1),
            ("Web Thickness, $t_w$", "web_mm", KEY_MP_GIRDER_WEB_THICKNESS, "mm", 1),
            ("Gross Area, $A$", "area_mm2", None, r"cm$^2$", 0.01),
            ("Moment of Inertia, $I_z$", "iz_mm4", None, r"cm$^4$", 0.0001),
            ("Elastic Section Modulus, $Z_{ez}$", "ze_mm3", None, r"cm$^3$", 0.001),
            ("Plastic Section Modulus, $Z_{pz}$", "zp_mm3", None, r"cm$^3$", 0.001),
            ("Effective Slab Width, $b_{eff}$", "beff_mm", None, "mm", 1),
            ("Transformed Composite $I_z$", "composite_iz_mm4", None, r"cm$^4$", 0.0001),
            ("Depth to Plastic Neutral Axis", "pna_mm", None, "mm", 1),
        ):
            value = props.get(key)
            if value is None and source_key is not None:
                value = bridge.input_dict.get(f"{source_key}.G{index}.M1", bridge.input_dict.get(source_key))
                scale = 1000
            rows.append(f" & {title} ({unit}) & " + quantity(value, scale=scale))
        header = r"\multirow{" + str(len(rows)) + r"}{*}{" + _tex(label) + "}"
        t51_rows.append(header + (r" \\*[3pt]\reportcline{2-3}" + "\n").join(rows)
                        + r" \\[3pt]" + "\n\\hline")
    t51_content = "\n".join(t51_rows)

    # Generate Table 5.2 rows
    t52_rows = []
    for lbl, _ in girder_entries:
        t52_rows.append(
            r"\multirow{3}{*}{\makecell{" + _tex(lbl) + r"""}} & Top Flange & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_FLANGE) + r""" \\*[6pt]
\reportcline{2-5}
 & Web & """ + _render_value(bridge.output_dict, KEY_SD_WEB_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_WEB_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_WEB) + r""" \\*[6pt]
\reportcline{2-5}
 & Overall Section & --- & --- & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_CLASS) + r""" \\[6pt]
\hline"""
        )
    t52_content = "\n".join(t52_rows)

    girder_checks = list(girder_design_checks(bridge.output_dict))

    def capacity_rows(check_id):
        rows = []
        for check in girder_checks:
            if check.check_id != check_id:
                continue
            cells = (
                _tex(check.member), break_long_words(check.combination or check.source),
                quantity(check.demand, _tex(check.unit), decimals=2),
                quantity(check.capacity, _tex(check.capacity_unit), decimals=2),
                f"{check.ratio:.2f}" if check.ratio is not None else "---",
                check.status.value,
            )
            rows.append(" & ".join(cells) + r" \\[6pt]" + "\n\\hline")
        return "\n".join(rows) or r"--- & Not calculated & --- & --- & --- & NOT EVALUATED \\"

    t53_content = capacity_rows(1)
    t54_content = capacity_rows(2)
    # Generate Table 5.5 rows
    # Interaction DCRs use the engine bands: PASS <0.90, WARN <1.00, FAIL ≥1.00.
    def _interaction_status(ratio):
        if ratio < 0.90:
            return "PASS"
        elif ratio < 1.00:
            return "WARN"
        return r"\textcolor{red}{FAIL}"
    # M-V interaction UR stored as percent → show ratio (2 dp).
    try:
        _mv_ur = float(bridge.output_dict.get(KEY_UTIL_INTERACTION)) / 100.0
        _mv_ur_str = f"{_mv_ur:.2f}"
        _mv_status = _interaction_status(_mv_ur)
    except (TypeError, ValueError):
        _mv_ur_str = ""
        _mv_status = "---"
    # M-N interaction: None → no axial load → N/A.
    _mn_r  = bridge.output_dict.get(KEY_SD_MN_RATIO)
    _mn_ax = bridge.output_dict.get(KEY_SD_MN_AXIAL)
    _mn_mo = bridge.output_dict.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        _mn_cond = _mn_val = _mn_status = "N/A"
    else:
        _mn_cond   = f"{_mn_ax:.2f} + {_mn_mo:.2f} = {_mn_r:.3f}"
        _mn_val    = f"{_mn_r:.3f}"
        _mn_status = _interaction_status(_mn_r)
    t55_rows = []
    for lbl, _ in girder_entries:
        t55_rows.append(
            r"\multirow{4}{*}{\makecell{" + _tex(lbl) + r"""}} & High Shear Condition? & $V_u > 0.6\,V_d$ & """ + _render_value(bridge.output_dict, KEY_SD_HIGH_SHEAR) + r""" & --- \\*[6pt]
\reportcline{2-5}
 & Reduced Moment Capacity, $M_{dv}$ & IRC 22 Cl. 603.3.3.3 & """ + _render_value(bridge.output_dict, KEY_SD_MDV, " kN-m") + r""" & --- \\*[6pt]
\reportcline{2-5}
 & Interaction Check: $M_u \leq M_{dv}$ & --- & """ + _mv_ur_str + r""" & """ + _mv_status + r""" \\*[6pt]
\reportcline{2-5}
 & Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$ & """ + _mn_cond + r""" & """ + _mn_val + r""" & """ + _mn_status + r""" \\[6pt]
\hline"""
        )
    t55_content = "\n".join(t55_rows)

    # Generate Table 5.6 rows
    # LTB UR stored as percent → show ratio (2 dp); engine bands via _interaction_status.
    try:
        _ltb_ur = float(bridge.output_dict.get(KEY_UTIL_LTB)) / 100.0
        _ltb_ur_str = f"{_ltb_ur:.2f}"
        _ltb_status = _interaction_status(_ltb_ur)
    except (TypeError, ValueError):
        _ltb_ur_str = ""
        _ltb_status = "---"
    t56_rows = []
    for lbl, _ in girder_entries:
        t56_rows.append(
            r"\multirow{5}{*}{\makecell{" + _tex(lbl) + r"""}} & Elastic Critical Moment, $M_{cr}$ & IRC 22 Cl. 603.3.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MCR, " kN-m") + r""" & --- \\*[6pt]
\reportcline{2-5}
 & Non-dim. Slenderness, $\bar{\lambda}_{LT}$ & $\sqrt{M_p / M_{cr}}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_LAMBDA) + r""" & --- \\*[6pt]
\reportcline{2-5}
 & LTB Reduction Factor, $\chi_{LT}$ & IS 800 Cl. 8.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_CHI) + r""" & --- \\*[6pt]
\reportcline{2-5}
 & LTB Resistance, $M_b$ & $\chi_{LT}\,M_p / \gamma_{m0}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MB, " kN-m") + r""" & --- \\*[6pt]
\reportcline{2-5}
 & $M_u \leq M_b$ & $M_u / M_b$ & """ + _ltb_ur_str + r""" & """ + _ltb_status + r""" \\[6pt]
\hline"""
        )
    t56_content = "\n".join(t56_rows)

    # Generate Table 5.7 rows
    t57_rows = []
    for lbl, _ in girder_entries:
        t57_rows.append(
            r"\multirow{6}{*}{\makecell{" + _tex(lbl) + r"""}} & \textnormal{Shear Buckling Design Method} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_METHOD) + r""" \\*[6pt]
\reportcline{2-3}
 & \textnormal{Intermediate Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_THICK) + r""" \\*[6pt]
\reportcline{2-3}
 & \textnormal{Intermediate Stiffener Spacing (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_SPACING) + r""" \\*[6pt]
\reportcline{2-3}
 & \textnormal{End Panel Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_THICK) + r""" \\*[6pt]
\reportcline{2-3}
 & \textnormal{No. of End Panel Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_COUNT) + r""" \\*[6pt]
\reportcline{2-3}
 & \textnormal{Longitudinal Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_LONG) + r""" \\[6pt]
\hline"""
        )
    t57_content = "\n".join(t57_rows)

    # Generate table - intermediate stiffener checks (IS 800 CL. 8.7.1.2)
    # Status: PASS when Provided ≥ Required.
    def _ge_status(provided, required):
        try:
            return "PASS" if float(provided) >= float(required) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"
    _iys_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_IYS_PROV),
                             bridge.output_dict.get(KEY_SD_IS_IYS_MIN))
    _fqd_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_FQD),
                             bridge.output_dict.get(KEY_SD_IS_FQ))
    t58_rows = []
    for lbl, _ in girder_entries:
        t58_rows.append(
            r"\multirow{2}{*}{\makecell{" + _tex(lbl) + r"""}} & Min. Moment of Inertia, $I_s$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_MIN, " mm$^4$") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_PROV, " mm$^4$") + r""" & """ + _iys_status + r""" \\*[6pt]
\reportcline{2-5}
 & Buckling Resistance, $F_{qd} \geq F_q$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQ, " kN") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQD, " kN") + r""" & """ + _fqd_status + r""" \\[6pt]
\hline"""
        )
    t58_content = "\n".join(t58_rows)

    # (Intermediate Stiffener Checks) is a verification table — it only
    # has data when the user supplied stiffener sizes (Design Type = Custom). In
    # Optimized mode the stiffeners are auto-sized (nothing to verify), so the
    # whole table is omitted from the report.
    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    if _is_custom:
        t58_block = r"""
\reportTableGap

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Intermediate Stiffener Checks}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]") + completed_rows(t58_content) + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.7.1.2}
"""
    else:
        t58_block = ""

    # Generate Table 5.9 rows — bearing stiffener checks (IS 800 Cl.8.7.3).
    # End panel == bearing stiffener for this bridge. Each resistance vs reaction R.
    # Resistances are 0 in guidance-only mode (optimized w/o outstand) → N/A until
    # the designer defaults outstand to (bf−tw)/2.
    _bs_r = bridge.output_dict.get(KEY_SD_BS_R)
    def _bs_check(resist_key):
        prov = bridge.output_dict.get(resist_key)
        # Resistance not computed (guidance mode) → N/A.
        if prov is None or float(prov) <= 0.0 or _bs_r is None:
            return ("N/A", "N/A", "N/A")
        req_s  = f"{_bs_r} kN"
        prov_s = f"{prov} kN"
        status = "PASS" if float(prov) >= float(_bs_r) else r"\textcolor{red}{FAIL}"
        return (req_s, prov_s, status)
    _wb_req, _wb_prov, _wb_st = _bs_check(KEY_SD_BS_FCDW_WB)
    _lc_req, _lc_prov, _lc_st = _bs_check(KEY_SD_BS_FCDW_LC)
    _ps_req, _ps_prov, _ps_st = _bs_check(KEY_SD_BS_FPSD)
    _cb_req, _cb_prov, _cb_st = _bs_check(KEY_SD_BS_FCD)
    t59_rows = []
    for lbl, _ in girder_entries:
        t59_rows.append(
            r"\multirow{4}{*}{\makecell{" + _tex(lbl) + r"""}} & Web Buckling Resistance & """ + _wb_req + r""" & """ + _wb_prov + r""" & """ + _wb_st + r""" \\*[6pt]
\reportcline{2-5}
 & Local Crushing Resistance & """ + _lc_req + r""" & """ + _lc_prov + r""" & """ + _lc_st + r""" \\*[6pt]
\reportcline{2-5}
 & Bearing Capacity & """ + _ps_req + r""" & """ + _ps_prov + r""" & """ + _ps_st + r""" \\*[6pt]
\reportcline{2-5}
 & Column Buckling Resistance & """ + _cb_req + r""" & """ + _cb_prov + r""" & """ + _cb_st + r""" \\[6pt]
\hline"""
        )
    t59_content = "\n".join(t59_rows)

    # ── Table 5.10: Serviceability — Deflection Checks (IRC 22 Cl. 604.3.2) ──────
    # Allowable limits: span-dependent, same for all girders, from output_dict.
    # Actual deflections: per-girder from bridge._deflections_cache — the same
    # source used by resolve_deflection_live_load/total in generate_results_values_builder.py.
    # Keys: {"G1": {"live_mm": X, "total_mm": Y}, ...}
    # lbl from girder_entries is "G1", "G2", ... which matches cache keys exactly.

    def _defl_status(actual, allowable):
        """PASS / red FAIL for deflection; '---' when values are missing."""
        try:
            return "PASS" if float(actual) <= float(allowable) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    def _dfmt(v, nd=2):
        """Format a numeric value to nd decimal places; empty string when None."""
        try:
            number = _finite_number(v)
            return f"{number:.{nd}f}" if number is not None else ""
        except (TypeError, ValueError):
            return ""

    displacement_rows = list(grillage_deflections(bridge.input_dict, bridge.output_dict))
    t510_rows = []
    for check in displacement_rows:
        demand = _dfmt(check.demand, 3) or "Not calculated"
        allowable = _dfmt(check.capacity, 2) or "Not provided"
        status = (r"\textcolor{reportFailure}{FAIL}" if check.status == Status.FAIL else check.status.value)
        detail = _tex(check.name + " / " + (check.combination or "Case unavailable"))
        t510_rows.append(
            " & ".join((_tex(check.member), detail, allowable, demand, status))
            + r" \\[6pt]" + "\n\\hline"
        )
    t510_content = "\n".join(t510_rows)

    # Generate Table 5.11 rows — SLS steel stress limitation (IRC 22 Cl. 604.3.1).
    # Concrete & rebar deck stresses are deck-global and belong with the deck
    # checks, so this table shows only the per-girder steel check. Steel stress is
    # a single envelope-SLS value (same for every girder); allowable = 0.9·fy.
    # Both live in the nested output_dict["design_results"] dict, not as flat keys.
    def _mpa(v):
        s = _dfmt(v, nd=2)
        return (s + " MPa") if s else ""

    def _stress_status(actual, allow):
        try:
            return "PASS" if float(actual) <= float(allow) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    _dr_511        = bridge.output_dict.get("design_results", {}) or {}
    _steel_sigma   = _dr_511.get(KEY_SD_STRESS_STEEL)
    _steel_allow   = _dr_511.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    _steel_sig_str = _mpa(_steel_sigma)
    _steel_alw_str = _mpa(_steel_allow)
    _steel_status  = _stress_status(_steel_sigma, _steel_allow)

    t511_rows = []
    for lbl, _ in girder_entries:
        t511_rows.append(
            r"\makecell{" + _tex(lbl) + r"""} & Structural Steel ($0.9\,f_y$) & """
            + _steel_alw_str + r""" & """
            + _steel_sig_str + r""" & """
            + _steel_status + r""" \\[6pt]
\hline"""
        )
    t511_content = "\n".join(t511_rows)

    # Generate Table 5.12 rows — per-girder fatigue assessment (IRC 22 Cl. 605),
    # mirroring the Generate Results dialog: one row per girder showing the
    # GOVERNING fatigue check (worst of normal/shear by DCR). Source is the nested
    # design_results["steeldesign.uls_per_girder"]["fatigue"][G{i}] dict, keyed by
    # the canonical girder index, with {demand, capacity, ur, status}.
    _fat_cat = ((bridge.output_dict.get("design_results", {}) or {})
                .get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}

    def _fat_status(s):
        if s is None or str(s).strip() == "":
            return "---"
        return r"\textcolor{red}{" + str(s) + "}" if "FAIL" in str(s).upper() else str(s)

    t512_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _g = _fat_cat.get(f"G{_gi}", {}) or {}
        t512_rows.append(
            r"\makecell{" + _tex(lbl) + r"""} & """
            + _mpa(_g.get("demand")) + r""" & """
            + _mpa(_g.get("capacity")) + r""" & """
            + _dfmt(_g.get("ur"), nd=2) + r""" & """
            + _fat_status(_g.get("status")) + r""" \\[6pt]
\hline"""
        )
    t512_content = "\n".join(t512_rows)

    # Use the same traceable result record as the executive summary.
    g_summary_rows = []
    for label, _ in girder_entries:
        result = governing(row for row in (*girder_checks, *displacement_rows) if row.member == label)
        if result is None:
            cells = (_tex(label), "---", "---", "---", "---", "---", Status.NOT_EVALUATED.value)
        else:
            def value(number, unit):
                return f"{number:.2f} {_tex(unit)}".strip() if number is not None else "---"
            cells = (_tex(label), break_long_words(result.combination or result.source), _tex(result.name),
                     value(result.demand, result.unit), value(result.capacity, result.capacity_unit),
                     _dfmt(result.ratio, 3) or "---", result.status.value)
        g_summary_rows.append(" & ".join(cells) + r" \\[6pt]" + "\n\\hline")
    g_summary_table_content = "\n".join(g_summary_rows)

    # ── Table 5.14: Shear Connector Capacity (bridge-level) ──────────────────
    # Qu (Cl.606.3.1, Eq.6.1) and Qr (Cl.606.3.2, Table 8) are single per-stud
    # values for the bridge, stored flat inside output_dict["design_results"].
    _dr_sc = bridge.output_dict.get("design_results", {}) or {}

    def _kn(v):
        s = _dfmt(v, nd=2)
        return (s + " kN") if s else ""

    t514_content = (
        r"Design Resistance, $Q_u$ & \footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[3pt]$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$\\[3pt]$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$} & "
        + _kn(_dr_sc.get(KEY_SD_SC_Qu_kN)) + r""" & IRC 22 Cl. 606.3.1 (Eq. 6.1) \\[6pt]
\hline
Fatigue Shear Resistance, $Q_r$ & IRC 22 Table 8 ($\phi d$, $N_{sc}$) & """
        + _kn(_dr_sc.get(KEY_SD_SC_Qr_kN)) + r""" & IRC 22 Cl. 606.3.2 (Table 8) \\[6pt]
\hline"""
    )

    # ── Table 5.15: Shear Connector Spacing (bridge-level) ───────────────────
    # Required spacings SL1/SL2/SR and the max-spacing limit are single bridge
    # values in design_results. Each criterion passes when the provided spacing
    # is no larger than that criterion's required spacing (denser = safe).
    def _mm(v):
        s = _dfmt(v, nd=1)
        return (s + " mm") if s else ""

    _sc_prov     = _dr_sc.get("stud_spacing_provided_mm")
    _sc_prov_str = _mm(_sc_prov)

    def _sp_row(crit, req):
        return (crit + r" & " + _mm(req) + r" & " + _sc_prov_str + r" & "
                + _defl_status(_sc_prov, req) + r" \\[6pt]")

    t515_content = (
        _sp_row("ULS Shear (SL1)",            _dr_sc.get(KEY_SD_SC_SL1)) + "\n\\hline\n"
        + _sp_row("Full Composite (SL2)",       _dr_sc.get(KEY_SD_SC_SL2)) + "\n\\hline\n"
        + _sp_row("SLS Fatigue (SR)",           _dr_sc.get(KEY_SD_SC_SR)) + "\n\\hline\n"
        + _sp_row("Max Spacing Limit (IRC 22)", _dr_sc.get("stud_spacing_max_mm")) + "\n\\hline"
    )

    # ── Table 5.16: Transverse Shear & Detailing Checks (bridge-level) ───────
    # Transverse shear (Cl.606.10): VL vs slab capacity VRd. Detailing (Cl.606.6):
    # min transverse reinforcement, stud diameter ≤ 2·tf, edge distance ≥ 25 mm.
    # All single bridge values in design_results; stud diameter from input_dict.
    def _cm2m(v):
        s = _dfmt(v, nd=2)
        return (s + r" cm$^2$/m") if s else ""

    def _knm(v):
        s = _dfmt(v, nd=2)
        return (s + " kN/m") if s else ""

    _ts_vl  = _dr_sc.get(KEY_SD_TS_VL)
    _ts_vrd = _dr_sc.get(KEY_SD_TS_VRD)
    if _ts_vl is not None and _ts_vrd is not None:
        try:
            _ts_vl_f = float(_ts_vl)
            _ts_vrd_f = float(_ts_vrd)
            if _ts_vrd_f > 0.0:
                _ts_ur_str = f"{_ts_vl_f / _ts_vrd_f:.2f}"
            else:
                _ts_ur_str = "---"
        except (TypeError, ValueError):
            _ts_ur_str = "---"
    else:
        _ts_ur_str = "---"
    _ts_ok = _dr_sc.get("transverse_shear_ok")
    _ts_status = (r"\textcolor{red}{FAIL}" if _ts_ok is False else "PASS") if _ts_ok is not None else "---"

    _ast_req  = _dr_sc.get("Ast_required_cm2_per_m")
    # Provided transverse steel = the deck's main (bottom + top) bars, which run
    # transversely between girders and cross the shear plane. The deck design
    # computes these (>= minimum) and they are what is actually provided. The
    # steel designer's own Ast_provided is 0 because its transverse-shear check
    # runs before design_deck_slab(), so read the deck-design value here instead.
    _dd_516 = bridge.output_dict.get("deck_design_results", {}) or {}
    try:
        _ast_prov = (float(_dd_516.get("rebar_bottom_area") or 0)
                     + float(_dd_516.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        _ast_prov = None
    _stud_d   = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    _d_lim    = _dr_sc.get(KEY_SD_SC_D_LIMIT)
    _edge     = _dr_sc.get(KEY_SD_SC_EDGE_DIST)
    _edge_req = _dr_sc.get(KEY_SD_SC_REQ_EDGE_DIST)

    def _row516(check, value, status):
        return check + r" & " + value + r" & " + status + r" \\[6pt]"

    t516_content = (
        _row516(r"\textnormal{Longitudinal Shear per unit length, $V_L$}", _knm(_ts_vl), "---") + "\n\\hline\n"
        + _row516(r"\textnormal{Transverse Shear Capacity of Slab, $V_{Rd}$}", _knm(_ts_vrd), "---") + "\n\\hline\n"
        + _row516(r"\textnormal{Transverse Shear Check}", r"$V_L/V_{Rd}$ = " + _ts_ur_str, _ts_status) + "\n\\hline\n"
        + _row516(r"\textnormal{Min. Transverse Reinforcement, $A_{st,min}$}",
                  r"Required " + _cm2m(_ast_req) + r", Provided " + _cm2m(_ast_prov),
                  _defl_status(_ast_req, _ast_prov)) + "\n\\hline\n"
        + _row516(r"\textnormal{Stud Diameter $\leq 2\,t_f$}",
                  r"$d$ = " + _mm(_stud_d) + r" $\leq 2t_f$ = " + _mm(_d_lim),
                  _defl_status(_stud_d, _d_lim)) + "\n\\hline\n"
        + _row516(r"\textnormal{Stud Edge Distance}",
                  r"Provided " + _mm(_edge) + r" (req. $\geq$ " + _mm(_edge_req) + r")",
                  _defl_status(_edge_req, _edge)) + "\n\\hline"
    )

    # Generate Table 5.20(a) rows
    cb_forces_rows = []
    pairs = bridge.get_cb_pairs()

    if not pairs:
        # fallback: one placeholder row
        cb_forces_rows.append(
            r"""Between Girders & Diagonal &  &  &  &  \\[6pt]
\hline"""
        )
    else:
        for pair in pairs:
            pair_id = pair.replace("-", "")
            for member, label in [("diagonal", "Diagonal"),
                                ("chord", "Top / Bottom chord")]:
                force_str, ftype = bridge.get_cb_governing_force(pair, member)
                conn_type = bridge.get_cb_connection(pair, member, ftype)
                section  = bridge.get_cb_section(pair, member, ftype)

                # Fetch properties from output_dict
                if member == "diagonal":
                    pfx = f"transverse_member_design.cb.section_properties.bracing.{pair_id}"
                else:
                    pfx = f"transverse_member_design.cb.section_properties.bottom_chord.{pair_id}"
                    if bridge.output_dict.get(f"{pfx}.A") is None:
                        pfx = f"transverse_member_design.cb.section_properties.top_chord.{pair_id}"

                area_cm2 = bridge.output_dict.get(f"{pfx}.A")
                rv_cm = bridge.output_dict.get(f"{pfx}.rv")

                # Convert Area: cm² -> mm²
                area_str = f"{float(area_cm2) * 100:.1f}" if area_cm2 is not None else ""
                # Convert rv: cm -> mm
                rmin_str = f"{float(rv_cm) * 10:.1f}" if rv_cm is not None else ""
                cb_forces_rows.append(
                    (r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}} & " if member == "diagonal" else " & ")
                    + label + r" & " + conn_type + r" & " + section
                    + r" & " + area_str + r" & " + rmin_str
                    + (r" \\*[6pt]\reportcline{2-6}" if member == "diagonal" else r" \\[6pt]")
                )
            cb_forces_rows.append(r"\hline")
    cb_forces_content = "\n".join(cb_forces_rows)

    # Generate Table 5.20(b) rows
    def get_status_str(slnd_str, limit):
        try:
            v = float(slnd_str)
            return r"\textcolor{black}{PASS}" if v <= limit else r"\textcolor{red}{FAIL}"
        except (ValueError, TypeError):
            return ""
    cb_slenderness_rows = []
    if not pairs:
        cb_slenderness_rows.append(
            r"""Between Girders & Diagonal & C &  &  &  ---  \\[6pt]
\hline"""
        )
    else:
        for pair in pairs:
            kl_diag = bridge.get_cb_effective_length("diagonal")
            slnd_diag = bridge.get_cb_slenderness(pair, "diagonal")
            status_diag = get_status_str(slnd_diag, 250)
            
            kl_tc = bridge.get_cb_effective_length("chord")
            slnd_tc = bridge.get_cb_slenderness(pair, "chord")
            status_tc = get_status_str(slnd_tc, 250)
            
            kl_bc = bridge.get_cb_effective_length("chord")
            slnd_bc = bridge.get_cb_slenderness(pair, "chord")
            status_bc = get_status_str(slnd_bc, 400)
            
            top_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
            bottom_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)
            
            rows = [f" & Diagonal & C & {kl_diag} & {slnd_diag} & 250 --- {status_diag}"]
            if top_chord_enabled:
                rows.append(f" & Top chord & C & {kl_tc} & {slnd_tc} & 250 --- {status_tc}")
            if bottom_chord_enabled:
                rows.append(f" & Bottom chord & T & {kl_bc} & {slnd_bc} & 400 --- {status_bc}")

            label = r"\multirow{" + str(len(rows)) + r"}{*}{\makecell{" + _tex(pair) + r"}}"
            body = (r" \\*[6pt]\reportcline{2-6}" + "\n").join(rows)
            cb_slenderness_rows.append(label + body + r" \\[6pt]" + "\n\\hline")
    cb_slenderness_content = "\n".join(cb_slenderness_rows)

    # Generate Table 5.20(c) rows
    cb_capacity_rows = []
    for pair in pairs:
        rows_for_pair = []
        for member, label in [("diagonal", "Diagonal"),
                            ("chord", "Chord")]:
            force_str, ftype = bridge.get_cb_governing_force(pair, member)
            section  = bridge.get_cb_section(pair, member, ftype)
            gov_lc   = bridge.get_cb_gov_lc(pair, member, ftype)
            capacity = bridge.get_cb_capacity(pair, member, ftype)
            ur       = bridge.get_cb_efficiency(pair, member, ftype)
            status   = bridge.get_cb_status(pair, member, ftype)
            rows_for_pair.append(
                r" & " + label + r" & " + section
                + r" & " + gov_lc + r" & " + force_str + r" & " + capacity
                + r" & " + ur + r" & " + status + (r" \\*[6pt]\reportcline{2-8}" if member == "diagonal" else r" \\[6pt]")
            )
        first = r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}}" + rows_for_pair[0]
        rest  = rows_for_pair[1:]
        cb_capacity_rows.append(first)
        cb_capacity_rows.extend(rest)
        cb_capacity_rows.append(r"\hline")
    cb_capacity_content = "\n".join(cb_capacity_rows)



    # ── Deck slab design value helpers (Tables 5.17 a/b/c/e/g) ────────────────
    # Read from deck_rpt = output_dict["deck_report_values"] (common.KEY_DD_*).
    # Tables 5.17(d) punching shear and 5.17(f) one-way shear stay as
    # placeholders — those are not computed by design_deck_slab().
    _dk_has = bool(deck_rpt)
    _dk_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    _DKPH = r"\placeholder{---}"

    def _dkv(key, default=0.0):
        """Raw float for status comparisons (0.0 if missing/non-numeric)."""
        v = deck_rpt.get(key)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _dkf(key, nd=2, scale=1.0):
        """Formatted display string; placeholder when deck design not run."""
        if not _dk_has:
            return _DKPH
        v = deck_rpt.get(key)
        if v is None or v == "":
            return _DKPH
        try:
            return f"{float(v) * scale:.{nd}f}"
        except (TypeError, ValueError):
            return str(v)

    def _dks(ok):
        """PASS/FAIL status; '---' when deck design not run."""
        return Status.NOT_EVALUATED.value if ok is None else "PASS" if ok else "FAIL"

    def _deck_upper(demand_key, capacity_key):
        demand = _finite_number(deck_rpt.get(demand_key))
        capacity = _finite_number(deck_rpt.get(capacity_key))
        if demand is None or capacity is None:
            return Status.NOT_EVALUATED.value
        if capacity <= 0:
            return Status.ERROR.value
        return _dks(demand <= capacity)

    deck_details = {check.name: check.status.value for check in deck_detail_checks(deck_rpt)}

    def _dkoh(key, nd=2, scale=1.0, unit=""):
        """Overhang value; 'N/A' when there is no overhang."""
        if not _dk_has:
            return _DKPH
        if not _dk_oh:
            return "N/A"
        return _dkf(key, nd=nd, scale=scale) + unit

    # Governing crack width = max(bottom, top[, overhang]) vs the limit.
    _dk_wks = [_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP)]
    if _dk_oh:
        _dk_wks.append(_dkv(KEY_DD_WK_OH))
    _dk_gov_wk = max(_dk_wks)
    _dk_gov_wk_str = (f"{_dk_gov_wk:.4f}" if _dk_has else _DKPH)

    # The summary table and chart share the same governing utilization values.
    _pg_522 = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    chart_rows = []

    def _vu_522(v, unit):
        s = _dfmt(v, nd=2)
        if not s:
            return ""
        u = (unit or "").strip()
        return (s + " " + u) if u else s

    def _ur_522(value):
        if value is None:
            return "---"
        label = f"{value:.2f}"
        return r"\textcolor{reportFailure}{" + label + "}" if value > UR_LIMIT else label

    def _lc_short(lc):
        return break_long_words(str(lc).strip())

    def _result_cells(check, fallback_unit=""):
        if check is None:
            return ("---", "---", "---", None, Status.NOT_EVALUATED)
        case = check.combination or ("Designer envelope" if check.source == "Designer envelope" else "---")
        return (_lc_short(case), _vu_522(check.demand, check.unit or fallback_unit) or "---",
                _vu_522(check.capacity, check.capacity_unit or fallback_unit) or "---", check.ratio, check.status)

    def _dcr_row(check_ids, fallback_unit=""):
        candidates = [check for check in girder_checks if check.check_id in check_ids]
        result = governing(candidates)
        return _result_cells(result, fallback_unit)

    # (3) Cross bracing — worst pair/member by UR for the given force type.
    _cb_pairs_522 = bridge.get_cb_pairs()

    def _axial_row(force_type, *, end_diaphragm=False):
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        if end_diaphragm:
            forces = bridge.output_dict.get("end_diaphragm_forces_dict") or {}
            designs = bridge.output_dict.get("end_diaphragm_design_results") or {}
            pairs = forces.get("pairs") or {}
        else:
            pairs = _cb_pairs_522

        best = None
        for pair in pairs:
            for member in ("diagonal", "chord"):
                if end_diaphragm:
                    design = ((designs.get(pair) or {}).get(member) or {}).get(force_type)
                    result = _extract_osdag_summary(design or {})
                else:
                    result = bridge.get_cb_member_result(pair, member, force_type)
                ur = _finite_number(result.get("efficiency"))
                if ur is not None and (best is None or ur > best[0]):
                    best = (ur, pair, member, _finite_number(result.get("capacity_kN")))
        if best is None:
            return ("---", "---", "---", None)

        ur, pair, member, cap = best
        if end_diaphragm:
            prefix = "diag" if member == "diagonal" else "chord"
            values = pairs[pair]
            gov = _tex(values.get(f"{prefix}_{force_type}_gov_lc"))
            demand = _finite_number(values.get(f"{prefix}_{force_type}_kN"))
            dem = f"{abs(demand):.2f} kN" if demand is not None else "---"
        else:
            gov = bridge.get_cb_gov_lc(pair, member, force_type)
            dem = bridge.get_cb_force(pair, member, force_type)
            dem = f"{abs(float(dem)):.2f} kN" if dem else "---"
        return (gov or "---", dem, f"{cap:.3f} kN" if cap is not None else "---", ur)

    def _cb_slender_row():
        best = None  # (ratio, slend, limit)
        for pair in _cb_pairs_522:
            for member in ("diagonal", "chord"):
                sf = _finite_number(bridge.get_cb_slenderness_value(pair, member))
                if sf is None:
                    continue
                lim = 400.0 if member == "chord" else 250.0
                ratio = sf / lim
                if best is None or ratio > best[0]:
                    best = (ratio, sf, lim)
        if best is None:
            return ("---", "---", "---", None)
        ratio, sf, lim = best
        return ("---", f"{sf:.1f}", f"{lim:.0f}", ratio)

    def _row522(label, cells):
        combination, demand, capacity, ratio, *explicit_status = cells
        status = explicit_status[0] if explicit_status else (
            Status.NOT_EVALUATED if ratio is None else Status.FAIL if ratio > UR_LIMIT else Status.PASS
        )
        chart_rows.append((label.replace(" --- ", " – "), ratio))
        columns = (label, combination, demand, capacity, _ur_522(ratio), status.value)
        return " & ".join(columns) + r" \\[6pt]" + "\n\\hline"

    # Deck rows: Demand/Capacity from deck_report_values (KEY_DD_*, the same dict
    # the 5.17 tables use); UR = Demand/Capacity. The deck is designed for the
    # IRC:6 Basic ULS combination — build that combo string from the stored
    # partial factors (gamma_dl, gamma_ll).
    _deck_combo = (
        r"Basic ULS: " + _tex(f"{_dkv(KEY_DD_GAMMA_DL):g}DL + {_dkv(KEY_DD_GAMMA_LL):g}LL")
    ) if _dk_has else "---"

    def _deck_row(dem_key, cap_key, unit, is_oh=False):
        if not _dk_has:
            return ("---", "---", "---", None)
        if is_oh and not _dk_oh:
            return (_deck_combo, "N/A", "N/A", None, Status.NOT_APPLICABLE)
        dem = _finite_number(deck_rpt.get(dem_key))
        cap = _finite_number(deck_rpt.get(cap_key))
        ur = dem / cap if dem is not None and cap is not None and cap > 0 else None
        return (_deck_combo, _vu_522(dem, unit) or "---", _vu_522(cap, unit) or "---", ur)

    def _row522_msg(label, msg):
        # Single message spanning the 5 data columns.
        return label + r" & \multicolumn{5}{l|}{" + msg + r"} \\[6pt]" + "\n\\hline"

    # A braced end diaphragm has its own axial design results. Beam-type
    # diaphragms retain the moment/shear availability message.
    _ed_is_cb = any(
        str(key).startswith(KEY_MP_ED_TYPE + ".") and "brac" in str(value).lower()
        for key, value in bridge.input_dict.items()
    ) or any((bridge.output_dict.get("end_diaphragm_design_results") or {}).values())
    if _ed_is_cb:
        _ed_moment_row = _row522(r"End Diaphragm --- Compression", _axial_row("compression", end_diaphragm=True))
        _ed_shear_row  = _row522(r"End Diaphragm --- Tension", _axial_row("tension", end_diaphragm=True))
    else:
        _ed_msg = r"Rolled / Welded section --- design to be added"
        _ed_moment_row = _row522_msg(r"End Diaphragm --- Moment", _ed_msg)
        _ed_shear_row  = _row522_msg(r"End Diaphragm --- Shear",  _ed_msg)

    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    diaphragm_rows = []
    diaphragm_designs = bridge.output_dict.get("end_diaphragm_design_results") or {}
    diaphragm_forces = (bridge.output_dict.get("end_diaphragm_forces_dict") or {}).get("pairs") or {}
    for pair, members in diaphragm_designs.items():
        for member, force_types in members.items():
            for force_type, raw in force_types.items():
                result = _extract_osdag_summary(raw or {})
                ratio = _finite_number(result.get("efficiency"))
                if ratio is None:
                    continue
                prefix = "diag" if member == "diagonal" else "chord"
                values = diaphragm_forces.get(pair, {})
                demand = _finite_number(values.get(f"{prefix}_{force_type}_kN"))
                capacity = _finite_number(result.get("capacity_kN"))
                cells = (_tex(pair), _tex(f"{member.capitalize()} / {force_type}"),
                         _tex(result.get("section")) or "---",
                         f"{abs(demand):.2f}" if demand is not None else "---",
                         f"{capacity:.2f}" if capacity is not None else "---",
                         _ur_522(ratio))
                diaphragm_rows.append(" & ".join(cells) + r" \\" + "\n\\hline")
    diaphragm_detail = r"\noindent NOT EVALUATED --- End-diaphragm design results unavailable."
    if diaphragm_rows:
        diaphragm_detail = (
            r"\begin{longtable}{|L{2cm}|L{4cm}|L{2.8cm}|C{2.3cm}|C{2.3cm}|C{1.4cm}|}"
            "\n" + r"\caption{\textbf{End Diaphragm Capacity Checks}}\\" + "\n"
            + repeated_header(r"\textbf{Pair} & \textbf{Check} & \textbf{Section} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} \\")
            + completed_rows("\n".join(diaphragm_rows))
            + r"\end{longtable}"
        )

    # Crack width (slab): governing crack width vs limit from the deck designer
    # (frequent SLS combination). _dk_gov_wk is the max of bottom/top/overhang wk.
    # The governing load combo is the SLS-frequent combination with the highest
    # DCR (its full expression comes straight from the per_lc keys).
    def _gov_sls_frequent():
        best = None  # (dcr, lc)
        for _g, _gd in _pg_522.items():
            if str(_g).startswith("EB"):
                continue
            for _lc, _ld in (_gd.get("per_lc") or {}).items():
                if "frequent" not in str(_lc).lower():
                    continue
                _d = _ld.get("max_dcr") or 0.0
                if best is None or _d > best[0]:
                    best = (_d, _lc)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    _wk_keys = (KEY_DD_WK_BOT, KEY_DD_WK_TOP, KEY_DD_WK_OH) if _dk_oh else (KEY_DD_WK_BOT, KEY_DD_WK_TOP)
    _wk_values = [_finite_number(deck_rpt.get(key)) for key in _wk_keys]
    _wk_actual = max((value for value in _wk_values if value is not None), default=None)
    _wk_lim = _finite_number(deck_rpt.get(KEY_DD_WK_LIMIT))
    _crack_cells = (
        _gov_sls_frequent() if _dk_has else "---",
        f"{_wk_actual:.3f} mm" if _wk_actual is not None else "---",
        f"{_wk_lim:.3f} mm" if _wk_lim is not None else "---",
        _wk_actual / _wk_lim if _wk_actual is not None and _wk_lim is not None and _wk_lim > 0 else None,
    )

    _t522 = [
        _row522(r"Girder --- Moment",             _dcr_row({1})),
        _row522(r"Girder --- Shear",              _dcr_row({2})),
        _row522(r"Girder --- LTB (constr.)",      _dcr_row({5})),
        *(_row522(f"Girder --- {name}", _result_cells(
            governing(check for check in displacement_rows if check.name == name)
        )) for name, _, _, _ in DEFLECTION_CRITERIA),
        _row522(r"Girder --- Stress",             _dcr_row({11}, fallback_unit="MPa")),
        _row522(r"Girder --- Fatigue",            _dcr_row({8, 9}, fallback_unit="MPa")),
        _row522(r"Transverse Shear (slab)",       _dcr_row({16})),
        _row522(r"Crack Width (slab)",            _crack_cells),
        _row522(r"Deck --- Flexure (sagging)",    _deck_row(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m")),
        _row522(r"Deck --- Flexure (hogging)",    _deck_row(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m")),
        _row522(r"Deck --- Cantilever Overhang",  _deck_row(KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True)),
        _row522(r"Deck --- Punching Shear",       _deck_row(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa")),
        _row522(r"Deck --- One-Way Shear",        _deck_row(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m")),
        _row522(r"Cross Bracing --- Compression", _axial_row("compression")),
        _row522(r"Cross Bracing --- Tension",     _axial_row("tension")),
        _row522(r"Cross Bracing --- Slenderness", _cb_slender_row()),
        _ed_moment_row,
        _ed_shear_row,
    ]
    t522_content = "\n".join(_t522)
    chart_tex = ""
    if image_dir is not None:
        chart_tex = "".join(_chart_figure(path) for path in generate_utilization_charts(chart_rows, image_dir))
        if not chart_tex:
            chart_tex = r"\noindent\textit{Utilization ratios are unavailable for charting.}"

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}

\reportTableGap
\begin{longtable}{|C{2.5cm}|L{8.0cm}|>{\centering\arraybackslash}p{5.0cm}|}
\caption{\textbf{Girder Section Properties (Final Optimized / User-selected)}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Property} & \textbf{Value} \\[6pt]") + completed_rows(t51_content) + r"""
\end{longtable}

\reportTableGap
\begin{longtable}{|C{2.5cm}|L{3cm}|C{3.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{4.0cm}|}
\caption{\textbf{Girder Section Classification}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Element} & \textbf{Slenderness Ratio} & \textbf{Class Limit} & \textbf{Classification} \\[6pt]") + completed_rows(t52_content) + r"""
\end{longtable}
\noindent\textit{Note: IS 800:2007 Table 2}

\reportTableGap
\begin{longtable}{|L{1.7cm}|L{5cm}|R{2.5cm}|R{2.5cm}|R{1.2cm}|C{2.5cm}|}
\caption{\textbf{Moment Capacity Check}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Governing Case / Source} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[6pt]") + completed_rows(t53_content) + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1}

\reportTableGap
\begin{longtable}{|L{1.7cm}|L{5cm}|R{2.5cm}|R{2.5cm}|R{1.2cm}|C{2.5cm}|}
\caption{\textbf{Shear Capacity Check}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Governing Case / Source} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[6pt]") + completed_rows(t54_content) + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2}

\reportTableGap
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Interaction Checks (M-V and M-N)}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Check} & \textbf{Condition} & \textbf{Value} & \textbf{Status} \\[6pt]") + completed_rows(t55_content) + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.3}

\reportTableGap
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Lateral Torsional Buckling Check -- Construction Stage}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]") + completed_rows(t56_content) + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2}

\reportTableGap
\begin{longtable}{|C{2.5cm}|L{6.5cm}|>{\arraybackslash}p{6.5cm}|}
\caption{\textbf{Stiffener Design Summary}}\\
\hline
""" + completed_rows(t57_content) + r"""
\end{longtable}
""" + t58_block + r"""
\reportTableGap

\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{End Panel Stiffener Checks}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]") + completed_rows(t59_content) + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4.2.2}

\reportTableGap
\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{\textbf{Serviceability -- Deflection Checks}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Check} & \textbf{Allowable} & \textbf{Actual} & \textbf{Status} \\[6pt]") + completed_rows(t510_content) + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 604.3.2}

\reportTableGap
\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{\textbf{Serviceability -- Maximum Stress Limitation}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Element} & \textbf{Allowable Stress} & \textbf{Actual Stress} & \textbf{Status} \\[6pt]") + completed_rows(t511_content) + r"""
\end{longtable}

\reportTableGap
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{\textbf{Serviceability -- Fatigue Assessment}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Stress Range, $\Delta\sigma$ (MPa)} & \textbf{Fatigue Limit, $f_{fd}$ (MPa)} & \textbf{Utilization Ratio} & \textbf{Status} \\[6pt]") + completed_rows(t512_content) + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity reduction factor $\mu_r$ applied where plate thickness > 25 mm.}

\reportTableGap
\reportSmallGap
\begin{longtable}{|C{1.6cm}|>{\centering\arraybackslash}p{3.6cm}|C{2.4cm}|C{2.0cm}|C{2.1cm}|C{1.7cm}|C{1.5cm}|}
\caption{\textbf{Girder Design Summary (DCR / Utilization Ratio)}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Controlling LC / Combination} & \textbf{Controlling Check} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[6pt]") + completed_rows(g_summary_table_content) + r"""
\end{longtable}
\noindent\textit{Note: UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling check is the criterion with the highest UR for each girder, with the real load case/combination that drives it.}

\reportTableGap

\begin{longtable}{|L{3.6cm}|C{5.6cm}|>{\centering\arraybackslash}p{2.6cm}|L{3.0cm}|}
\caption{\textbf{Shear Connector Capacity}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Reference} \\[6pt]") + completed_rows(t514_content) + r"""
\end{longtable}

\reportTableGap

\reportLeftTable

\begin{longtable}{|L{3.2cm}|>{\centering\arraybackslash}p{4.3cm}|>{\centering\arraybackslash}p{4.3cm}|C{2.0cm}|}
\caption{\textbf{Shear Connector Spacing}}\\
""" + repeated_header(r"\textbf{Criterion} & \textbf{Governing Spacing} & \textbf{Actual Spacing Provided} & \textbf{Status} \\[6pt]") + completed_rows(t515_content) + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.}

\reportTableGap
\begin{longtable}{|L{5.3cm}|>{\arraybackslash}p{7.2cm}|C{2.0cm}|}
\caption{\textbf{Transverse Shear and Detailing Checks}}\\
""" + repeated_header(r"\textbf{Check} & \textbf{Value} & \textbf{Status} \\[6pt]") + completed_rows(t516_content) + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 606.6, 606.10.}

% ===========================
\section{Deck Slab Design}
\label{sec:deck-design}
% ===========================

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.

\reportTableGap
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Deck Slab --- Loading and Geometry}}\\
\hline
\textnormal{Effective Span of Deck Slab, $l_{eff}$} & """ + _dkf(KEY_DD_SPAN, nd=0, scale=1000.0) + r""" mm (girder spacing, c/c) \\[6pt]
\hline
\textnormal{Deck Thickness, $t_s$} & """ + _render_value(bridge.input_dict, KEY_TS_DECK_THICKNESS) + r""" mm \\[6pt]
\hline
\textnormal{Clear Cover (IRC 112 Cl. 15.2)} & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm \\[6pt]
\hline
\textnormal{Concrete Grade (IRC 112 Cl. 6.4)} & """ + _render_value(bridge.input_dict, KEY_DECK_CONCRETE_GRADE_BASIC) + r""" ($f_{ck}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCK) + r""" MPa, $f_{ctm}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCTM) + r""" MPa) \\[6pt]
\hline
\textnormal{Reinforcement Grade (IRC 112 Cl. 6.2)} & """ + _render_value(bridge.input_dict, KEY_DS_REINF_MATERIAL) + r""" ($f_y$ = """ + _dkf(KEY_DD_FY, nd=0) + r""" MPa) \\[6pt]
\hline
\textnormal{Dead Load per Unit Area, $w_{DL}$} & """ + _dkf(KEY_DD_WDL, nd=2) + r""" kN/m² (slab self-weight) \\[6pt]
\hline
\textnormal{IRC 6 Wheel Load (Class A / 70R)} & """ + _dkf(KEY_DD_WHEEL_LOAD, nd=1) + r""" kN \\[6pt]
\hline
\textnormal{Tyre Contact Width (IRC 6 Annex~A)} & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" mm (transverse) \\[6pt]
\hline
\textnormal{Impact Factor (IRC 6 Cl. 208.2)} & """ + _dkf(KEY_DD_IMPACT_FACTOR, nd=3) + r""" \\[6pt]
\hline
\textnormal{Governing Live Load Case} & """ + _dkf(KEY_DD_VEHICLE) + r""" \\[6pt]
\hline
\end{longtable}

\reportTableGap
\begin{longtable}{|C{3.0cm}|C{3.5cm}|C{3.0cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)}}\\
""" + repeated_header(r"\textbf{Location} & \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]") + r"""\multirow{5}{*}{\makecell{At Midspan\\(Sagging)}} & Transverse BM (DL), $M_{T,DL}$ & $w_{DL}\,l_{eff}^2/10$ & """ + _dkf(KEY_DD_M_DL, nd=2) + r""" kN-m/m & --- \\*[6pt]
\reportcline{2-5}
 & Transverse BM (LL), $M_{T,LL}$ & Effective width (IRC 112 B3.1) & """ + _dkf(KEY_DD_M_LL, nd=2) + r""" kN-m/m & --- \\*[6pt]
\reportcline{2-5}
 & Total Design BM, $M_{u,sag}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL & """ + _dkf(KEY_DD_M_ULS_SAG, nd=2) + r""" kN-m/m & --- \\*[6pt]
\reportcline{2-5}
 & Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\*[6pt]
\reportcline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_BOT, nd=2) + r""" kN-m/m & """ + _deck_upper(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT) + r""" \\[6pt]
\hline
\multirow{3}{*}{\makecell{At Support\\(Hogging)}} & Total Design BM, $M_{u,hog}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL (at support) & """ + _dkf(KEY_DD_M_ULS_HOG, nd=2) + r""" kN-m/m & --- \\*[6pt]
\reportcline{2-5}
 & Required Top Steel, $A_{st,top}$ & $M_u / (0.87\,f_y\,d)$ & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & --- \\*[6pt]
\reportcline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_TOP, nd=2) + r""" kN-m/m & """ + _deck_upper(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\% of main steel moment (IRC 21 Cl. 305.18).}

\reportTableGap
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{\textbf{Deck Slab --- Cantilever Overhang Flexure Check}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]") + r"""Overhang Length, $l_{oh}$ & --- & """ + _render_value(bridge.input_dict, KEY_TS_DECK_OVERHANG, " m") + r""" & --- \\[6pt]
\hline
Crash Barrier Load Moment & IRC 6 Cl. 206.4 & """ + _dkoh(KEY_DD_M_BARRIER, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Dead Load Moment & $w_{DL}\,l_{oh}^2/2$ + railing & """ + _dkoh(KEY_DD_M_DL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Live Load Moment (eccentric wheel) & Wheel load $\times$ arm & """ + _dkoh(KEY_DD_M_LL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Total Hogging Moment, $M_{u,oh}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" (LL + CB) & """ + _dkoh(KEY_DD_M_ULS_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Moment Capacity (top steel), $M_{Rd,oh}$ & IRC 112 Cl. 12.2 & """ + _dkoh(KEY_DD_MU_OH, nd=2, unit=" kN-m/m") + r""" & """ + (_deck_upper(KEY_DD_M_ULS_OH, KEY_DD_MU_OH) if _dk_oh else ("N/A" if _dk_has else "---")) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.}

\reportTableGap
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{\textbf{Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]") + r"""Design Wheel Load (ULS), $V_{Ed}$ & $\gamma_Q\,(1+IF)\,P_w$ & """ + _dkf(KEY_DD_PUNCH_VED_KN, nd=1) + r""" kN & --- \\[6pt]
\hline
Tyre Contact Area & $a \times b$ (IRC 6 Annex~A) & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" $\times$ """ + _dkf(KEY_DD_TYRE_LENGTH, nd=0) + r""" mm & --- \\[6pt]
\hline
Loaded Area at mid-depth, $b_0$ & $c_1 \times c_2$ (incl.\ WC dispersion) & """ + _dkf(KEY_DD_PUNCH_C1, nd=0) + r""" $\times$ """ + _dkf(KEY_DD_PUNCH_C2, nd=0) + r""" mm & --- \\[6pt]
\hline
Control Perimeter, $u_1$ & $2(c_1+c_2) + 4\pi d$ & """ + _dkf(KEY_DD_PUNCH_U1, nd=0) + r""" mm & --- \\[6pt]
\hline
Punching Shear Stress, $v_{Ed}$ & $V_{Ed} / (u_1\,d)$ & """ + _dkf(KEY_DD_PUNCH_VED, nd=3) + r""" MPa & --- \\[6pt]
\hline
Punching Resistance, $v_{Rd,c}$ & IRC 112 Eq.\ 10.1 & """ + _dkf(KEY_DD_VRD_C_MPA, nd=3) + r""" MPa & --- \\[6pt]
\hline
Punching Shear Check & $v_{Ed} \leq v_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_PUNCH_VED) / _dkv(KEY_DD_VRD_C_MPA):.2f}" if (_dk_has and _dkv(KEY_DD_VRD_C_MPA) > 0) else _DKPH) + r""" & """ + _dks(deck_rpt.get(KEY_DD_PUNCH_OK)) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and adequate longitudinal reinforcement.}

\reportTableGap
\begin{longtable}{|L{7cm}|>{\arraybackslash}p{8.5cm}|}
\caption{\textbf{Crack Width Check (Deck Slab)}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value / Reference} \\[6pt]") + r"""\textnormal{Min. Reinforcement for Crack Control, $A_{s,min}$} & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m [IRC 112 Cl. 16.5.1] \\[6pt]
\hline
\textnormal{Provided Reinforcement (bottom)} & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c (""" + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m) \\[6pt]
\hline
\textnormal{Max. Permissible Crack Width} & """ + _dkf(KEY_DD_WK_LIMIT, nd=2) + r""" mm \\[6pt]
\hline
\textnormal{Calculated Crack Width, $w_k$ (governing)} & """ + _dk_gov_wk_str + r""" mm \\[6pt]
\hline
\textnormal{Crack Width Check} & """ + _dks(_wk_actual <= _wk_lim if _wk_actual is not None and _wk_lim is not None and _wk_lim > 0 else None) + r""" \\[6pt]
\hline
\end{longtable}

\reportTableGap
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{\textbf{One-Way (Beam) Shear Check (Deck Slab)}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]") + r"""Design Shear per unit width, $V_{Ed}$ & $\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$ & """ + _dkf(KEY_DD_SHEAR_VED, nd=2) + r""" kN/m & --- \\[6pt]
\hline
Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\[6pt]
\hline
Size factor, $k$ & $1 + \sqrt{200/d} \leq 2.0$ & """ + (f"{min(1.0 + (200.0 / _dkv(KEY_DD_D_BOT)) ** 0.5, 2.0):.3f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[6pt]
\hline
Long.\ reinforcement ratio, $\rho_l$ & $A_{sl}/(b_w\,d) \leq 0.02$ & """ + (f"{min(_dkv(KEY_DD_AS_BOT) / (1000.0 * _dkv(KEY_DD_D_BOT)), 0.02):.4f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[6pt]
\hline
Shear resistance (no stirrups), $V_{Rd,c}$ & $v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2) & """ + _dkf(KEY_DD_SHEAR_VRDC, nd=2) + r""" kN/m & --- \\[6pt]
\hline
One-Way Shear Check & $V_{Ed} \leq V_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_SHEAR_VED) / _dkv(KEY_DD_SHEAR_VRDC):.2f}" if (_dk_has and _dkv(KEY_DD_SHEAR_VRDC) > 0) else _DKPH) + r""" & """ + _dks(deck_rpt.get(KEY_DD_SHEAR_OK)) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.}

\reportTableGap
\begin{longtable}{|L{5.5cm}|>{\centering\arraybackslash}p{4.1cm}|>{\centering\arraybackslash}p{4.1cm}|C{1.8cm}|}
\caption{\textbf{Reinforcement Detailing Summary (Deck Slab)}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Required / Limit} & \textbf{Provided} & \textbf{Status} \\[6pt]") + r"""\multicolumn{4}{|l|}{\textbf{Main Reinforcement --- Bottom (Transverse)}} \\[6pt]
\hline
Required Area, $A_{st,req}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_BOT, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + deck_details["Bottom reinforcement area"] + r""" \\[6pt]
\hline
Bar Diameter $\times$ Spacing & $\phi \geq 10$ mm (IRC 112) & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c & --- \\[6pt]
\hline
Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1) & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + deck_details["Minimum reinforcement area"] + r""" \\[6pt]
\hline
Max.\ Bar Spacing (IRC 112 Cl. 16.3.2) & """ + _dkf(KEY_DD_SPACING_MAX, nd=0) + r""" mm & """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm & """ + deck_details["Maximum bar spacing"] + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Distribution Reinforcement --- Longitudinal}} \\[6pt]
\hline
Required Area, $A_{st,dist}$ (mm²/m) & $\geq 20\%$ of main steel & """ + _dkf(KEY_DD_AS_LONG, nd=0) + r""" mm²/m & """ + deck_details["Distribution reinforcement area"] + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Top Reinforcement (Support / Cantilever Overhang)}} \\[6pt]
\hline
Required Area, $A_{st,top}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_TOP, nd=0) + r""" mm²/m & """ + deck_details["Top reinforcement area"] + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Cover and Detailing}} \\[6pt]
\hline
Clear Cover (IRC 112 Cl. 15.2) & $\geq$ """ + _dkf(KEY_DD_MIN_COVER, nd=0) + r""" mm (Table 14.2) & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm & """ + _dks(deck_rpt.get(KEY_DD_COVER_OK)) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and detailing requirements.}

% ===========================
\section{Cross Bracing Design}
\label{sec:cross-bracing}
% ===========================

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination  (DL + LL + WL).

Chapter 2 lists the initial section. The checks below use the section returned by the member designer for each pair and force direction. An available design-selected section represents the result of section selection and does not establish overall design compliance.

\reportTableGap

\reportSmallGap
\noindent
\reportLeftTable

\begin{longtable}{|C{2.0cm}|L{2.0cm}|L{2.5cm}|C{2.2cm}|C{2.0cm}|C{2.0cm}|}
\caption{\textbf{Cross Bracing --- Design-Selected Sections and Properties}}\\
""" + repeated_header(r"\textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[6pt]") + completed_rows(cb_forces_content) + r"""
\end{longtable}
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\reportTableGap
\begin{longtable}{|C{2.2cm}|L{2.2cm}|L{2.5cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{3.6cm}|}
\caption{\textbf{Cross Bracing --- Slenderness Ratio Check (IS~800 Cl.~3.8 )}}\\
""" + repeated_header(r"\textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[6pt]") + completed_rows(cb_slenderness_content) + r"""
\end{longtable}
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

\reportTableGap
\begin{longtable}{|C{1.8cm}|L{1.8cm}|C{2.1cm}|C{2.9cm}|C{1.8cm}|C{1.95cm}|C{1.2cm}|C{1.8cm}|}
\caption{\textbf{Cross Bracing Design --- Capacity Summary}}\\
""" + repeated_header(r"\textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[6pt]") + completed_rows(cb_capacity_content) + r"""
\end{longtable}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{End Diaphragm Design}
\label{sec:end-diaphragm}
% ===========================

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.

\reportTableGap
""" + diaphragm_detail + r"""

% ===========================
\section{Overall Design Check Summary}
\label{sec:overall-summary}
% ===========================

\reportTableGap
\begin{longtable}{|L{3.3cm}|L{3.7cm}|R{2.2cm}|R{2.2cm}|R{1.1cm}|C{2.6cm}|}
\caption{\textbf{Overall Design Check Summary --- All Members}}\\
""" + repeated_header(r"\textbf{Member / Check} & \textbf{Governing Load Combo} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[6pt]") + completed_rows(t522_content) + r"""
\end{longtable}
\noindent\textit{Note: UR is demand / capacity for upper-bound checks. The reported status follows the applicable criterion. Transverse-member ratios are stored Osdag designer efficiencies.}

""" + chart_tex
