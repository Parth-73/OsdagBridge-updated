from .charts import generate_quantity_chart
from .report_utils import _chart_figure
from .tables import repeated_header

_MATERIAL_CHARTS = (
    ("structural_steel.png", "Structural steel", "Total mass (t)", (
        ("Girders", "steel_girders_wt_total"),
        ("Cross bracing – top chord", "bracing_top_wt_total"),
        ("Cross bracing – bottom chord", "bracing_bot_wt_total"),
        ("Cross bracing – diagonal chord", "bracing_diag_wt_total"),
        ("End diaphragms", "end_diaphragm_wt_total"),
        ("Shear stud connectors", "shear_studs_wt_total"),
    )),
    ("concrete.png", "Concrete", "Total volume (m³)", (
        ("Deck slab", "concrete_deck_vol_total"),
        ("Crash barrier", "crash_barrier_vol_total"),
    )),
    ("reinforcement.png", "Reinforcement steel", "Total mass (t)", (
        ("Deck reinforcement", "rebar_deck_wt_total"),
    )),
)


def ch7_quantities(input_dict, *, image_dir=None):
    chart_tex = ""
    if image_dir is not None:
        for file_name, title, axis_label, items in _MATERIAL_CHARTS:
            rows = [(label, input_dict.get(key)) for label, key in items]
            path = generate_quantity_chart(rows, image_dir, file_name, title, axis_label)
            if path:
                chart_tex += _chart_figure(path)
        if not chart_tex:
            chart_tex = r"\noindent\textit{Material quantities are unavailable for charting.}"

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\begingroup
\reportDenseTable
\begin{longtable}{|C{1cm}|L{3.6cm}|L{3.3cm}|R{1.3cm}|R{2.3cm}|R{2.0cm}|R{2.0cm}|}
\caption{\textbf{Bill of Materials}}\\
""" + repeated_header(r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume basis} & \textbf{Qty.} & \makecell[r]{\textbf{Total volume}\\\textbf{(m³)}} & \makecell[r]{\textbf{Unit mass}\\\textbf{(t)}} & \makecell[r]{\textbf{Total mass}\\\textbf{(t)}} \\") + r"""1 & Structural Steel (IS 2062) for Girders & """ + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\
\hline
3 & Concrete for Deck Slab & """ + str(input_dict.get("concrete_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r""" \\
\hline
4 & Deck Reinforcement Steel & """ + str(input_dict.get("rebar_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r""" \\
\hline
5 & Shear Stud Connectors & """ + str(input_dict.get("shear_studs_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_qty", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_total", "N.A.")) + r""" \\
\hline
6 & Crash Barrier & """ + str(input_dict.get("crash_barrier_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_qty", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r""" \\
\hline
7 & End Diaphragms & --- & """ + str(input_dict.get("end_diaphragm_qty", "N.A.")) + r""" & --- & --- & """ + str(input_dict.get("end_diaphragm_wt_total", "N.A.")) + r""" \\
\hline
\end{longtable}
\endgroup
""" + chart_tex


