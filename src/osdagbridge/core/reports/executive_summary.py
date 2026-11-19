# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


from .design_results import COMPONENTS, Status, aggregate_status, collect_design_checks, governing
from .tables import load_longtable


def _result_tables(checks):
    rows = []
    for component in COMPONENTS:
        items = [check for check in checks if check.component == component]
        check = governing(items)
        maximum = max((item.ratio for item in items if item.ratio is not None), default=None)
        name = (f"{check.member}: {check.name}" if check.member != component else check.name) if check else "Unavailable"
        status = aggregate_status(items).value
        if component == "End Diaphragm" and status == Status.NOT_EVALUATED.value:
            name = "End-diaphragm design results unavailable"
        ratio = f"{maximum:.2f}" if maximum is not None else "---"
        rows.append((_tex(component), _tex(name), ratio, _tex(status)))

    failures = []
    for check in checks:
        if not check.mandatory or check.status not in {Status.FAIL, Status.ERROR}:
            continue
        detail = ", ".join(filter(None, (check.clause, check.combination, check.source)))
        demand = f"{check.demand:.3f} {check.unit}".strip() if check.demand is not None else "---"
        capacity = (f"{check.capacity:.3f} {check.capacity_unit}".strip()
                    if check.capacity is not None else "---")
        failures.append((_tex(check.member), _tex(check.name + " / " + detail),
                         _tex(demand), _tex(capacity),
                         f"{check.ratio:.2f}" if check.ratio is not None else "---", check.status.value))
    return rows, failures


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    '3D View of Bridge Superstructure')

    checks = list(collect_design_checks(input_dict, output_dict))
    status = aggregate_status(checks)
    maximum = max((check for check in checks if check.ratio is not None),
                  key=lambda check: check.ratio, default=None)
    gov = _tex(f"{maximum.member}: {maximum.name}") if maximum else "Not evaluated"
    ur = f"{maximum.ratio:.2f}" if maximum else "Not evaluated"
    overall_design_status = status.value if status != Status.NOT_EVALUATED else "NOT EVALUATED (incomplete)"
    rows, failures = _result_tables(checks)

    def latex_rows(data):
        return "".join(" & ".join(row) + r" \\" + "\n\\hline\n" for row in data)

    outcomes = load_longtable(
        "Consolidated Design Results", "|L{3.1cm}|L{6.3cm}|R{2.2cm}|C{3.1cm}|",
        r"\textbf{Component} & \textbf{Governing Check} & \textbf{Maximum UR} & \textbf{Status} \\",
        latex_rows(rows),
    )
    warnings = list(input_dict.get("report_input_warnings") or [])
    unavailable = {}
    for check in checks:
        if check.mandatory and check.status == Status.NOT_EVALUATED:
            unavailable.setdefault(check.component, set()).add(check.name)
    warnings.extend(f"{component}: NOT EVALUATED — {', '.join(sorted(names))}"
                    for component, names in unavailable.items())
    if any(check.ratio is not None and "stiffness-adjusted" in check.name for check in checks):
        warnings.append("Grillage deflections are direct maximum nodal displacements. Designer deflection DCRs use stiffness-adjusted demand; these results describe separate methods.")
    if any(check.component in {"Cross Bracing", "End Diaphragm"}
           and check.demand is not None and check.capacity and check.capacity > 0
           and check.ratio is not None and abs(check.demand / check.capacity - check.ratio) > 0.015
           for check in checks):
        warnings.append(
            "Some transverse-member utilization values differ from the displayed demand divided by member capacity. "
            "These are the stored Osdag designer efficiencies. The report retains the recorded force and member capacity separately."
        )
    warning_tex = ""
    if warnings:
        warning_tex = r"\begin{itemize}" + "\n" + "\n".join(r"\item " + _tex(w) for w in warnings) + "\n" + r"\end{itemize}"
    failure_tex = load_longtable(
        "Failed or Invalid Mandatory Checks", "|L{2.2cm}|L{6.3cm}|R{2.1cm}|R{2.1cm}|R{1cm}|C{1.4cm}|",
        r"\textbf{Member} & \textbf{Check and source} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\",
        latex_rows(failures),
    ) if failures else r"\noindent No failures were recorded in the available mandatory checks."

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\phantomsection
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\phantomsection
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}


\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Bridge Type} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textbf{Design Standard} & IRC 5, IRC 6, IRC 22, IRC 24, IS 800 \\
\hline
\textbf{Span} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textbf{Carriageway Width} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textbf{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\
\hline
\textbf{Girder Spacing} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING, " m")) + r""" \\
\hline
\textbf{Deck Thickness} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS, " mm")) + r""" \\
\hline
\textbf{Overall Design Status} & """ + (_tex(overall_design_status)) + r""" \\
\hline
\textbf{Governing Check} & """ + gov + r""" \\
\hline
\textbf{Overall Utilization Ratio (max)} & """ + ur + r""" \\
\hline
\end{tabular}


""" + plan_fig + r"""

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + r"""

\reportSmallGap
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. The applicable design check determines the acceptance criterion. An optimized section is an attempt and may retain failed or unevaluated checks.}

\reportTableGap

\section*{Key Design Outcomes Summary}
\phantomsection
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

""" + outcomes + r"""

\section*{Critical Design Failures and Warnings}
\phantomsection
\addcontentsline{toc}{section}{Critical Design Failures and Warnings}

""" + failure_tex + "\n" + warning_tex + r"""

\section*{Design Assumptions and Limitations}
\phantomsection
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:executive-assumptions}

\begin{itemize}
\item Asterisks identify software defaults where the input or result exposes their provenance.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}

% Restore numbered chapter format
\titleformat{\chapter}[block]{\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{-30pt}{10pt}
"""
