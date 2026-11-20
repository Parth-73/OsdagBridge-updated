from .inputs import design_lane_count
from .tables import load_longtable, repeated_header

# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_A,
    KEY_BL_IRC_AA_TRACKED,
    KEY_BL_IRC_AA_WHEELED,
    KEY_BL_IRC_70R_BOGIE,
    KEY_BL_IRC_70R_TRACKED,
    KEY_BL_IRC_70R_WHEELED,
    KEY_BL_IRC_CLASS_FATIGUE,
    KEY_BL_IRC_CLASS_SV,
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_ECCENTRICITY,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
)

from osdagbridge.core.reports.report_utils import quantity, _finite_number, _tex, _render_value

_VEHICLE_CLASSES = (
    ("Class A", KEY_LL_IRC_CLASS_A, KEY_BL_IRC_CLASS_A, "A"),
    ("Class 70R (Wheeled)", KEY_LL_IRC_70R_WHEELED, KEY_BL_IRC_70R_WHEELED, "Heavy"),
    ("Class 70R (Tracked)", KEY_LL_IRC_70R_TRACKED, KEY_BL_IRC_70R_TRACKED, "Heavy"),
    ("Class AA (Wheeled)", KEY_LL_IRC_AA_WHEELED, KEY_BL_IRC_AA_WHEELED, "Heavy"),
    ("Class AA (Tracked)", KEY_LL_IRC_AA_TRACKED, KEY_BL_IRC_AA_TRACKED, "Heavy"),
    ("Class SV", KEY_LL_IRC_CLASS_SV, KEY_BL_IRC_CLASS_SV, None),
    ("Class 70R (Bogie)", KEY_LL_IRC_70R_BOGIE, KEY_BL_IRC_70R_BOGIE, "Heavy"),
    ("Class Fatigue", KEY_LL_IRC_CLASS_FATIGUE, KEY_BL_IRC_CLASS_FATIGUE, None),
)


def _enabled(value):
    return str(value).strip().lower() in {"true", "yes", "1", "1.0", "on"}


def _load_rows(rows):
    return "".join(
        " & ".join(cells) + r" \\[6pt]" + "\n\\hline\n"
        for cells in rows
    )


def _vehicle_rows(inputs, code):
    span = _finite_number(inputs.get(KEY_SPAN))
    rows = []
    braking = []
    has_heavy = False
    for label, selected_key, brake_key, impact_class in _VEHICLE_CLASSES:
        if not _enabled(inputs.get(selected_key)):
            continue
        factor = "---"
        if impact_class == "Heavy":
            has_heavy = True
            factor = "See Class AA/70R factor"
        elif impact_class == "A" and span is not None and span > 0:
            factor = f"{1.0 + code.cl_208_2_impact_factor(span):.3f}"
        brake = inputs.get(brake_key)
        if brake in (None, ""):
            brake_status = "---"
        elif _enabled(brake):
            brake_status = "Yes"
        else:
            brake_status = "No"
        braking.append(brake_status)
        rows.append((_tex(label), factor, brake_status))

    custom = inputs.get(KEY_LL_CUSTOM_VEHICLES)
    if isinstance(custom, list):
        for vehicle in custom:
            name = vehicle.get("name") if isinstance(vehicle, dict) else vehicle
            if isinstance(name, str) and name.strip():
                rows.append((_tex(name), "---", "---"))

    if not rows:
        rows.append(("No vehicle classes selected", "---", "---"))

    lanes = design_lane_count(inputs)

    parameters = []
    if has_heavy:
        value = f"{1.0 + code.cl_208_3_impact_factor(span):.3f}" if span and span > 0 else "Unavailable"
        parameters.append(("Class AA/70R impact factor (IRC 6 Cl. 208.3)", value, "---"))
    can_apply_braking = any(status in {"Yes", "---"} for status in braking)
    force = "Not selected" if not can_apply_braking else "Unavailable"
    if can_apply_braking and lanes:
        force = f"{code.cl_211_2_braking_force(lanes) * 9.81:.2f}"
    parameters.append(("Lane-based braking load (IRC 6 Cl. 211.2)", force, "kN"))
    eccentricity = _render_value(inputs, KEY_LL_ECCENTRICITY)
    if eccentricity and can_apply_braking:
        parameters.append(("Braking load eccentricity", eccentricity, "m"))

    # Current bridge geometry has no horizontal curve input or force output.
    parameters.append(("Centrifugal force", "Unavailable (no horizontal curvature data)", "kN"))
    return _load_rows(rows), _load_rows(parameters)


def _footpath_rows(inputs, code):
    configuration = inputs.get(KEY_FOOTPATH)
    count = _finite_number(inputs.get(KEY_TS_NO_OF_FOOTPATHS))
    width = _finite_number(inputs.get(KEY_TS_FOOTPATH_WIDTH))
    explicit_absence = configuration is not None and str(configuration).strip().lower() in {"none", "no"}
    if explicit_absence or count == 0 or (not configuration and count is None and width == 0):
        return _load_rows([("Applicability", "Not Applicable (no footpath)", "---")])

    rows = []
    if configuration:
        rows.append(("Configuration", _tex(configuration), "---"))
    elif count is not None:
        rows.append(("Number of footpaths", f"{count:g}", "---"))
    if width is not None and width > 0:
        rows.append(("Footpath width", f"{width:g}", "m"))

    mode = str(inputs.get(KEY_LL_FOOTPATH_PRESSURE_MODE) or "").strip()
    automatic = mode.lower() in {"as per irc 6", "as per irc6", "automatic"}
    if mode:
        rows.append(("Loading mode", _tex(mode), "---"))
    if automatic:
        if configuration or count or (width and width > 0):
            load = code.cl_206_1_footway_load()
            rows.append(("Live-load intensity (IRC 6 Cl. 206.1)", f"{load:.3f}", r"kN/m\textsuperscript{2}"))
        else:
            rows.append(("Applicability", "Unavailable", "---"))
    else:
        load = _finite_number(inputs.get(KEY_LL_FOOTPATH_PRESSURE_VALUE))
        if load is None:
            rows.append(("Live-load intensity", "Unavailable", "---"))
        else:
            rows.append(("Configured live-load intensity", _tex(inputs[KEY_LL_FOOTPATH_PRESSURE_VALUE]),
                         r"kN/mm\textsuperscript{2}"))
    return _load_rows(rows)


def ch3_loads(input_dict, output_dict=None):
    applied = (output_dict or {}).get("applied_dead_loads") or {}
    steel_rows = []
    for line in applied.get("steel_lines") or []:
        position = _render_value(line, "z_m", " m", missing="Not reported")
        load = _render_value(line, "load_kN_m", " kN/m", missing="Not reported")
        steel_rows.append(f"Steel self-weight at $z$ = {position} & {load}")
    if not steel_rows:
        steel_rows.append("Steel self-weight applied & Not reported")
    steel_tex = "\n".join(row + r" \\ \hline" for row in steel_rows)

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    vehicle_rows, vehicle_parameters = _vehicle_rows(input_dict, IRC6_2017)
    footpath_rows = _footpath_rows(input_dict, IRC6_2017)

    vehicle_table = load_longtable(
        "Vehicle Live Loads (LL)", "|L{6.5cm}|C{4.5cm}|C{4.5cm}|",
        r"\textbf{Selected vehicle class} & \textbf{Impact factor (IRC 6)} & \textbf{Braking selected} \\",
        vehicle_rows,
    )
    load_columns = "|L{6.5cm}|L{6.5cm}|C{2.5cm}|"
    load_heading = r"\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\"
    vehicle_parameters_table = load_longtable("Vehicle Live Load Parameters", load_columns, load_heading, vehicle_parameters)
    footpath_table = load_longtable("Footpath Live Loads", load_columns, load_heading, footpath_rows)

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\reportTableGap
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\", footer=True) + steel_tex + r"""
\textnormal{Steel unit weight (material input)} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}', missing='Not reported')) + r""" \\[6pt]
\hline
\textnormal{Concrete unit weight (material input)} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}', missing='Not reported')) + r""" \\[6pt]
\hline
\textnormal{Concrete deck self-weight per unit area} & """ + _render_value(applied, "deck_kN_m2", r" kN/m$^2$", missing="Not reported") + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR, missing="Not reported")) + r""" \\[6pt]
\end{longtable}

\reportTableGap
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\", footer=True) + r"""\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\end{longtable}

\reportTableGap
""" + vehicle_table + "\n" + vehicle_parameters_table + "\n" + footpath_table + r"""

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} \\", footer=True) + r"""Site basic wind speed & """ + _render_value(input_dict, "wind_speed", " m/s", missing="Not provided") + r""" \\
\hline
Basic speed used in analysis & """ + quantity(input_dict.get("wind_speed_used"), "m/s") + (" (software default)" if input_dict.get("wind_used_default") else "") + r""" \\
\hline
Terrain used in analysis & """ + _render_value(input_dict, "wind_terrain_used", missing="Not calculated") + r""" \\
\hline
Average exposed height & """ + quantity(input_dict.get("wind_height_used"), "m") + (" (software default)" if input_dict.get("wind_height_default") else "") + r""" \\
\hline
Hourly mean wind speed, $V_z$ & """ + quantity(input_dict.get("wind_hourly_speed"), "m/s") + r""" \\
\hline
Hourly wind pressure, $P_z$ & """ + quantity(input_dict.get("wind_pressure"), r"N/m\textsuperscript{2}") + r""" \\
\hline
Transverse design force & """ + quantity(input_dict.get("wind_force_transverse_kN"), "kN") + r""" \\
\hline
Longitudinal design force & """ + quantity(input_dict.get("wind_force_longitudinal_kN"), "kN") + r""" \\
\hline
Vertical uplift & """ + quantity(input_dict.get("wind_force_vertical_kN"), "kN") + r""" \\
\end{longtable}

\reportTableGap
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Seismic Load (EL) --- per IRC 6}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} \\", footer=True) + r"""Site seismic zone & """ + _render_value(input_dict, "seismic_zone", missing="Not provided") + r""" \\
\hline
Zone factor used, $Z$ & """ + quantity(input_dict.get("seismic_factor_used")) + (" (software default)" if input_dict.get("seismic_used_default") else "") + r""" \\
\hline
Horizontal coefficient, $A_h$ & """ + quantity(input_dict.get("seismic_Ah"), decimals=4) + r""" \\
\hline
Vertical coefficient, $A_v$ & """ + quantity(input_dict.get("seismic_Av"), decimals=4) + r""" \\
\hline
Horizontal seismic force (longitudinal) & """ + quantity(input_dict.get("seismic_force_longitudinal_kN"), "kN") + r""" \\
\hline
Horizontal seismic force (transverse) & """ + quantity(input_dict.get("seismic_force_transverse_kN"), "kN") + r""" \\
\hline
Vertical seismic force & """ + quantity(input_dict.get("seismic_force_vertical_kN"), "kN") + r""" \\
\end{longtable}

\reportTableGap
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} \\", footer=True) + r"""Maximum shade temperature & """ + quantity(input_dict.get("shade_temp_max"), r"$^\circ$C", missing="Not provided") + r""" \\
\hline
Minimum shade temperature & """ + quantity(input_dict.get("shade_temp_min"), r"$^\circ$C", missing="Not provided") + r""" \\
\hline
Effective bridge temperature (min. / max.) & """ + quantity(input_dict.get(KEY_TL_BRIDGE_TEMP_MIN), r"$^\circ$C") + r""" / """ + quantity(input_dict.get(KEY_TL_BRIDGE_TEMP_MAX), r"$^\circ$C") + r""" \\
\hline
Design temperature rise / fall & """ + quantity(input_dict.get(KEY_TL_TEMP_RISE), r"$^\circ$C") + r""" / """ + quantity(input_dict.get(KEY_TL_TEMP_FALL), r"$^\circ$C") + r""" \\
\hline
Applied temperature load & """ + quantity(input_dict.get("temperature_load_kN_m2"), r"kN/m\textsuperscript{2}", missing="Not provided (optional load omitted)") + r""" \\
\end{longtable}

\reportTableGap
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}\\
""" + repeated_header(r"\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]", footer=True) + lc_rows_str.rstrip().removesuffix(r"\hline") + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


