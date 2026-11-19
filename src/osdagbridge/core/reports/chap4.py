from .tables import load_longtable, repeated_header
from .design_results import DEFLECTION_CRITERIA, governing, grillage_deflections

from typing import TYPE_CHECKING
from osdagbridge.core.reports.report_utils import _tex, _fig_embed, _finite_number

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        number = _finite_number(val)
        return f"{number:.{nd}f}" if number is not None else "Not calculated"

    def _merged_row(lc, bm_d, rxn_d):
        bm_d  = bm_d  or {}
        rxn_d = rxn_d or {}
        return (
            _tex(lc)                              + r" & "
            + _fmt(bm_d.get('max_bm'))           + r" & "
            + _tex(bm_d.get('bm_girder', '---')) + r" & "
            + _fmt(bm_d.get('bm_location'))      + r" & "
            + _fmt(bm_d.get('max_sf'))           + r" & "
            + _tex(bm_d.get('sf_girder', '---')) + r" & "
            + _fmt(bm_d.get('sf_location'))      + r" & "
            + _fmt(rxn_d.get('left_kN'))         + r" & "
            + _fmt(rxn_d.get('right_kN'))        + r" \\[6pt]"
        )

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

    merged_body = ("\n\\hline\n").join(
        _merged_row(lc, lc_summary.get(lc), rxn_summary.get(lc))
        for lc in all_lcs
    ) if all_lcs else r"--- & --- & --- & --- & --- & --- & --- & --- & --- \\[6pt]"

    reaction_body = "".join(
        " & ".join((_tex(case), _fmt(row.get("left_kN")), _fmt(row.get("right_kN"))))
        + r" \\" + "\n\\hline\n" for case, row in rxn_summary.items()
    ) or r"Not calculated & --- & --- \\"
    reactions = load_longtable(
        "Reactions at Supports", "|L{7.4cm}|R{4cm}|R{4cm}|",
        r"\textbf{Load Case} & \textbf{Left Support (kN)} & \textbf{Right Support (kN)} \\",
        reaction_body,
    )
    displacement = list(grillage_deflections(bridge.input_dict, bridge.output_dict))

    def deflection(name):
        row = governing(check for check in displacement if check.name == name)
        if row is None:
            return "Not calculated", "Not calculated", "NOT EVALUATED"
        measured = f"{row.demand:.3f} mm ({row.member})" if row.demand is not None else "Not calculated"
        limit = f"{row.capacity:.2f} mm" if row.capacity is not None else "Not provided"
        return measured, limit, row.status.value

    _live_str, _allow_live_str, _live_status = deflection(DEFLECTION_CRITERIA[0][0])
    _total_str, _allow_total_str, _total_status = deflection(DEFLECTION_CRITERIA[1][0])
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

\reportTableGap
\begingroup
\reportDenseTable

\begin{longtable}{|
>{\centering\arraybackslash}p{3.1cm}|
>{\centering\arraybackslash}p{1.7cm}|
>{\centering\arraybackslash}p{1.2cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.7cm}|
>{\centering\arraybackslash}p{1.2cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.6cm}|
>{\centering\arraybackslash}p{1.6cm}|}

\caption{\textbf{Summary of Maximum Demands}}\\
\hline
\multirow{2}{*}{\makecell{\textbf{Load case /}\\\textbf{Combination}}}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\textbf{Reaction at Supports}}\\
\cline{2-9}

& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Left}}
& \makecell{\textbf{Right }}\\
\hline
\endfirsthead

\hline
\multirow{2}{*}{\makecell{\textbf{Load case /}\\\textbf{Combination}}}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\textbf{Reaction at Supports}}\\
\cline{2-9}

& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Left}}
& \makecell{\textbf{Right}}\\
\hline
\endhead

""" + merged_body + r"""

\hline
\end{longtable}
\endgroup

\reportTableGap
""" + reactions + r"""

\reportTableGap
\begin{longtable}{|L{7cm}|p{8.5cm}|}
\caption{\textbf{Deflection Summary (Live Load \& Total Load)}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\") + r"""\textnormal{Deflection due to Live Load, $\delta_{LL}$} & """ + _live_str + r""" \\[6pt]
\hline
\textnormal{Allowable Live Load Deflection ($\Delta_{allow}$)} & """ + _allow_live_str + r""" \\[6pt]
\hline
\textnormal{Live Load Deflection Check Status} & """ + _live_status + r""" \\[6pt]
\hline
\textnormal{Deflection due to Total Load, $\delta_{total}$} & """ + _total_str + r""" \\[6pt]
\hline
\textnormal{Allowable Total Deflection ($\Delta_{allow}$)} & """ + _allow_total_str + r""" \\[6pt]
\hline
\textnormal{Total Load Deflection Check Status} & """ + _total_status + r""" \\[6pt]
\hline
\end{longtable}

\reportTableGap
\noindent
""" + _fig_embed(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('defl_ll'), 'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=r'0.75\textwidth') + r"""
"""

