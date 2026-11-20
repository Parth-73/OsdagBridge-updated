from .inputs import design_lane_count
from .tables import load_longtable, repeated_header

# Chapter 2: Input Parameters — exact LaTeX template match


from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex, quantity

def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    # Median row only shown when the user included a median
    median_row = ""
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        median_row = (r"\textnormal{Median Type} & "
                      + _render_value(input_dict, KEY_MD_TYPE)
                      + r""" \\[6pt]
\hline
""")
    return r"""
\chapter{Input Parameters}

\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Documented software defaults are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Location values come from the stored project data. Missing values are identified explicitly.}

\begin{table}[H]
\caption{\textbf{Project Location}}
\label{subsec:project-location}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Parameter} & \textbf{Value} \\
\hline
\textnormal{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textnormal{Latitude / Longitude} & """ + (_render_value(input_dict, 'latitude', missing='Not provided')) + ', ' + (_render_value(input_dict, 'longitude', missing='Not provided')) + r""" \\
\hline
\textnormal{Seismic Zone (IRC 6)} & """ + (_render_value(input_dict, 'seismic_zone', missing='Not provided')) + r""" \\
\hline
\textnormal{Basic Wind Speed (IRC 6)} & """ + (_render_value(input_dict, 'wind_speed', ' m/s', missing='Not provided')) + r""" \\
\hline
\textnormal{Shade Temp. Max / Min (IRC 6)} & """ + (_render_value(input_dict, 'shade_temp_max','', missing='Not provided')) + r""" °C / """ + (_render_value(input_dict, 'shade_temp_min','', missing='Not provided')) + r""" °C \\
\hline
\end{tabular}
\vspace{0.4cm}
\end{table}

\begin{table}[H]
\caption{\textbf{Bridge Geometry}}
\label{subsec:bridge-geometry}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Parameter} & \textbf{Value} \\
\hline
\textnormal{Type of Structure} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textnormal{Span (m)} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textnormal{Carriageway Width (m)} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textnormal{Include Median} & """ + (_render_value(input_dict, KEY_INCLUDE_MEDIAN)) + r""" \\
\hline
\textnormal{Footpath} & """ + (_render_value(input_dict, KEY_FOOTPATH)) + r""" \\
\hline
\textnormal{Skew Angle (degrees)} & """ + (_render_value(input_dict, KEY_SKEW_ANGLE, '°')) + r""" (IRC 24 Cl. 504.8 limit: $\pm$15°) \\
\hline
\end{tabular}
\end{table}
\vspace{0.4cm}

\begin{table}[H]
\caption{\textbf{Material Selection}}
\label{subsec:material}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Parameter} & \textbf{Value} \\
\hline
\textnormal{Girder Steel Grade (IS 2062)} & """ + (_render_value(input_dict, KEY_GIRDER)) + r""" \\
\hline
\textnormal{Cross Bracing Steel Grade} & """ + (_render_value(input_dict, KEY_CROSS_BRACING)) + r""" \\
\hline
\textnormal{End Diaphragm Steel Grade} & """ + (_render_value(input_dict, KEY_END_DIAPHRAGM)) + r""" \\
\hline
\textnormal{Concrete Deck Grade (IRC 22)} & """ + (_render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)) + r""" \\
\hline
\end{tabular}
\end{table}
\vspace{0.4cm}

\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\reportSmallGap

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Typical Section Details}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} \\") + r"""\textnormal{Overall Bridge Width (m)} & """ + (_render_value(input_dict, KEY_TS_OVERALL_WIDTH)) + r""" \\[6pt]
\hline
\textnormal{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\[6pt]
\hline
\textnormal{Girder Spacing (m)} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING, ' m')) + r""" \\[6pt]
\hline
\textnormal{Deck Overhang Width (m)} & """ + (_render_value(input_dict, KEY_TS_DECK_OVERHANG, ' m')) + r""" \\[6pt]
\hline
\textnormal{Deck Thickness (mm)} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Footpath Width (m)} & """ + (_render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, ' m')) + r""" (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]
\hline
\textnormal{No. of Traffic Lanes} & """ + str(design_lane_count(input_dict) or "Unavailable") + r""" (IRC 6 Table 6 basis) \\[6pt]
\hline
\end{longtable}

\vspace{0.8em}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Components Details}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} \\") + r"""\textnormal{Crash Barrier Type} & """ + (_render_value(input_dict, KEY_CB_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Crash Barrier Load (kN/m)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" \\[6pt]
\hline
""" + median_row + r"""
\textnormal{Railing Type} & """ + (_render_value(input_dict, KEY_RL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Railing Load (kN/m)} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" \\[6pt]
\hline
\textnormal{Wearing Course Material} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" \\[6pt]
\hline
\textnormal{Wearing Course Thickness (mm)} & """ + (_render_value(input_dict, KEY_WC_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\end{longtable}

""" + _girder_tables(input_dict, n_girders) + r"""

""" + _bracing_tables(input_dict, n_girders) + "\n" + bracing_selection_table(input_dict, output_dict or {}) + r"""

""" + _shear_connector_table(input_dict, output_dict) + r"""

""" + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    # Fetch backend-populated labels via exact suffix pattern (defaults.py)
    # KEY_MP_GD_SELECT_GIRDER.G{i}    = 'G{i}'
    # KEY_MP_GD_MEMBER_ID.G{i}.M1     = 'G{i}M1'
    # All other girder/stiffener keys: {BASE_KEY}.G{i}.M1
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    
    entries_for_table = [
        (lbl, mid, i)
        for i, (lbl, mid) in enumerate(
            girder_entries,
            start=1,
        )
    ]

    # Helper: one girder-dimension row
    def _dim_row(g_lbl, i):
        return (g_lbl + r""" & """
                + (quantity(input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1"), scale=1000, missing="Not provided"))
                + r""" & """
                + (quantity(input_dict.get(f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1"), scale=1000, missing="Not provided"))
                + r""" & """
                + (quantity(input_dict.get(f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1"), scale=1000, missing="Not provided"))
                + ', '
                + (quantity(input_dict.get(f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1"), scale=1000, missing="Not provided"))
                + r""" & """
                + (quantity(input_dict.get(f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1"), scale=1000, missing="Not provided"))
                + ', '
                + (quantity(input_dict.get(f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1"), scale=1000, missing="Not provided"))
                + r""" \\[8pt]
\hline
""")

    # Helper: one general-info row
    def _gen_row(g_lbl, m_id, i):
        return (g_lbl + r""" & """ + m_id + r""" & """
                + (_render_value(input_dict, KEY_DESIGN_MODE))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1"))
                + r""" \\[8pt]
\hline
""")

    def _rst_row(label, i):
        fields = (
            ("Torsional restraint", KEY_MP_GIRDER_TORSIONAL_RESTRAINT, ""),
            ("Warping restraint", KEY_MP_GIRDER_WARPING_RESTRAINT, ""),
            ("Web philosophy", KEY_MP_GIRDER_WEB_TYPE, ""),
            ("Intermediate stiffeners", KEY_MP_STIFFENER_INTERMEDIATE, ""),
            ("Intermediate spacing", KEY_MP_STIFFENER_INTERMEDIATE_SPACING, " mm"),
            ("Intermediate thickness", KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, " mm"),
            ("Longitudinal stiffeners", KEY_MP_STIFFENER_LONGITUDINAL, ""),
            ("Bearing stiffener count", KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, ""),
            ("Bearing spacing", KEY_MP_STIFFENER_SPACING, " mm"),
            ("Bearing thickness", KEY_MP_STIFFENER_BEARING_THICKNESS, " mm"),
        )
        rows = []
        for name, key, unit in fields:
            value = _render_value(input_dict, f"{key}.G{i}.M1", unit, missing="Not reported")
            rows.append(f"{_tex(label)} & {name} & {value}" + r" \\ \hline")
        return "\n".join(rows) + "\n"

    gen_rows = "".join([_gen_row(g_lbl, m_id, i) for g_lbl, m_id, i in entries_for_table])
    dim_rows = "".join([_dim_row(g_lbl, i) for g_lbl, _, i in entries_for_table])
    rst_rows = "".join([_rst_row(g_lbl, i) for g_lbl, _, i in entries_for_table])

    return (r"""

\reportSmallGap
\noindent
            
\vspace{4pt}
\begin{longtable}{|L{2.2cm}|L{1.8cm}|p{3.8cm}|p{3.8cm}|p{3.8cm}|}
\caption{\textbf{Girder General Information}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Member ID} & \textbf{Design Mode} & \textbf{Girder Type} & \textbf{Girder Symmetry} \\[6pt]")
            + gen_rows
            + r"""\end{longtable}

\vspace{0.6em}

\vspace{4pt}
\begin{longtable}{|L{2cm}|R{3cm}|R{3cm}|R{3.6cm}|R{3.6cm}|}
\caption{\textbf{Girder Section Dimensions}}\\
""" + repeated_header(r"\textbf{Girder} & \makecell[r]{Total depth\\$D$ (mm)} & \makecell[r]{Web thickness\\$t_w$ (mm)} & \makecell[r]{Top flange\\$(b_{tf}, t_{tf})$ (mm)} & \makecell[r]{Bottom flange\\$(b_{bf}, t_{bf})$ (mm)} \\[6pt]")
            + dim_rows
            + r"""\end{longtable}

\vspace{0.6em}

\vspace{4pt}
\begin{longtable}{|L{2.2cm}|L{6cm}|L{6cm}|}
\caption{\textbf{Girder Restraint and Stiffener Details}}\\
""" + repeated_header(r"\textbf{Girder} & \textbf{Parameter} & \textbf{Value} \\[6pt]")
            + rst_rows
            + r"""\end{longtable}
""")


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    panels = [
        (
            _render_value(input_dict, f"{KEY_MP_CB_SELECT_GIRDERS}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_CB_MEMBER_ID}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_SELECT_GIRDERS}.G{i}G{i+1}.E{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_MEMBER_ID}.G{i}G{i+1}.E{i}M1"),
            i
        )
        for i in range(1, n)
    ]

    # Helper: one cross-bracing row (all locations share same bracing config)
    def _cb_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_TYPE}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_SPACING}.G{i}G{i+1}.B{i}M1", ' m'))
                + r""" \\[6pt]
\hline
""")

    # Helper: one end-diaphragm row (all locations share same config)
    def _ed_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_TYPE}.G{i}G{i+1}.E{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.E{i}M1"))
                + r""" \\[6pt]
\hline
""")

    cb_rows = "".join([_cb_row(cb_loc, cb_ids, i) for cb_loc, cb_ids, _, _, i in panels])
    ed_rows = "".join([_ed_row(ed_loc, ed_ids, i) for _, _, ed_loc, ed_ids, i in panels])

    return (r"""

\begingroup
\reportSmallGap

\reportLeftTable

\begin{longtable}{|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|C{1.8cm}|}
\caption{\textbf{Member Properties: Cross Bracing Details}}\\
""" + repeated_header(r"\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Initial Bracing Section} & \textbf{Spacing (m)} \\")
+ cb_rows
+ r"""\end{longtable}

\reportSmallGap
\noindent

\begin{longtable}{|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|}
\caption{\textbf{Member Properties: End Diaphragm Details}}\\
""" + repeated_header(r"\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} \\")
+ ed_rows
+ r"""\end{longtable}
\endgroup
""")


def bracing_selection_table(inputs, outputs):
    """Compare seed sections with the section used by each stored direction check."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    rows = []
    pairs = outputs.get("crossbracing_design_results") or {}
    for pair, members in pairs.items():
        left = pair.split("-", 1)[0]
        if not left.startswith("G") or not left[1:].isdigit():
            continue
        index = int(left[1:])
        suffix = f".{pair.replace('-', '')}.B{index}M1"
        for member, results in members.items():
            keys = ((KEY_MP_CB_BRACING_SECTION_DESIGNATION,) if member == "diagonal" else
                    (KEY_MP_CB_TOP_CHORD_SECTION_DESIG, KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG))
            initial = list(dict.fromkeys(str(inputs[key + suffix]) for key in keys if inputs.get(key + suffix)))
            for direction, raw in results.items():
                design = _extract_osdag_summary(raw or {})
                final = design.get("section")
                if not final:
                    status = "Not evaluated"
                elif not initial:
                    status = "Design selection returned"
                else:
                    status = "Retained" if final in initial else "Changed by design"
                rows.append(" & ".join(map(_tex, (
                    pair, f"{member.capitalize()} / {direction}", " / ".join(initial) or "Not provided",
                    final or "Not calculated", status,
                ))) + r" \\" + "\n\\hline\n")
    if not rows:
        return r"\par\noindent Cross-bracing section selection results were not recorded."
    return load_longtable(
        "Cross Bracing: Initial and Design-Selected Sections",
        "|L{1.8cm}|L{3.1cm}|L{3.5cm}|L{3.5cm}|L{3.2cm}|",
        r"\textbf{Pair} & \textbf{Check} & \textbf{Initial Section} & \textbf{Design Section} & \textbf{Selection Status} \\",
        "".join(rows),
    )


def _shear_connector_table(input_dict, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return r"""
\label{subsec:shear-connectors}

\vspace{2.2em}

\reportSmallGap
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Shear Connector Details}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} \\") + r"""\textnormal{Stud Diameter (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_DIAMETER, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Stud Height (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_HEIGHT, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Stud $f_y$ (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textnormal{Stud $f_u$ (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textnormal{No. of Studs per Section} & """ + (_render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION)) + r""" \\[6pt]
\hline
\end{longtable}
"""

def _safety_factors_table(input_dict):
    return r"""
\label{subsec:safety-factors}

\reportSmallGap
\noindent\textit{Note: All values are per IRC 22 Table 1 unless user-modified.}

\reportSmallGap
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Partial Safety Factors}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} \\") + r"""\textnormal{$\gamma_{M0}$ (Yielding / Buckling)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M0)) + r""" \\[2pt]
\hline
\textnormal{$\gamma_{M1}$ (Ultimate Stress)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M1)) + r""" \\[2pt]
\hline
\textnormal{$\gamma_C$ (Concrete, Basic)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_C_BASIC)) + r""" \\[2pt]
\hline
\textnormal{$\gamma_s$ (Reinforcement)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_S)) + r""" \\[2pt]
\hline
\textnormal{$\gamma_v$ (Shear Connectors)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_V)) + r""" \\[2pt]
\hline
\textnormal{$\gamma_{fft}$ (Fatigue Load)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_FLT)) + r""" \\[2pt]
\hline
\textnormal{$\gamma_{Mft}$ (Fatigue Strength)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_MF)) + r""" \\[2pt]
\hline
\end{longtable}
"""

