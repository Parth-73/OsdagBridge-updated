from .tables import repeated_header

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
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _finite_number, _tex, _render_value

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

    # The available braking force is a lane-based value, not a per-vehicle result.
    lanes = _finite_number(inputs.get(KEY_WC_LD_LANE_TABLE_COUNT))
    notes = []
    if has_heavy:
        if span is not None and span > 0:
            factor = 1.0 + code.cl_208_3_impact_factor(span)
            notes.append(f"Class AA/70R impact factor (IRC 6 Cl. 208.3): {factor:.3f}.")
        else:
            notes.append("Class AA/70R impact factor: unavailable.")
    if any(status in {"Yes", "---"} for status in braking) and lanes and lanes.is_integer() and lanes > 0:
        try:
            force_t = _finite_number(code.cl_211_2_braking_force(int(lanes)))
        except UnboundLocalError:
            # The existing IRC helper does not initialize its additional-lane
            # term for a one- or two-lane bridge.
            force_t = None
        if force_t is None:
            notes.append("Lane-based braking load (IRC 6 Cl. 211.2): unavailable.")
        else:
            notes.append(f"Lane-based braking load (IRC 6 Cl. 211.2): {force_t * 9.81:.2f} kN ({force_t:.2f} tonnes).")
        eccentricity = _render_value(inputs, KEY_LL_ECCENTRICITY, " m")
        if eccentricity:
            notes.append("Braking load eccentricity: " + eccentricity + ".")
    return _load_rows(rows), " ".join(notes)


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


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    vehicle_rows, vehicle_notes = _vehicle_rows(input_dict, IRC6_2017)
    footpath_rows = _footpath_rows(input_dict, IRC6_2017)

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean   = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise     = f"{_bt_max - _mean:.2f}"
            tl_fall     = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

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

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\", footer=True) + r"""\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\", footer=True) + r"""\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{6.5cm}|C{4.5cm}|C{4.5cm}|}
\caption{\textbf{Vehicle Live Loads (LL)}}\\
""" + repeated_header(r"\textbf{Selected vehicle class} & \textbf{Impact factor (IRC 6)} & \textbf{Braking selected} \\", footer=True) + vehicle_rows.rstrip().removesuffix(r"\hline") + r"""
\end{longtable}
\noindent """ + vehicle_notes + r"""

\begin{longtable}{|L{6.5cm}|L{6.5cm}|C{2.5cm}|}
\caption{\textbf{Footpath Live Loads}}\\
""" + repeated_header(r"\textbf{Parameter} & \textbf{Value} & \textbf{Unit} \\", footer=True) + footpath_rows.rstrip().removesuffix(r"\hline") + r"""
\end{longtable}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\", footer=True) + r"""\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict,'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}')) + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\", footer=True) + r"""\textnormal{Seismic Zone} & """ + (_render_value(input_dict,'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + '' + r""" kN \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + '' + r""" kN \\[6pt]
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}\\
""" + repeated_header(r"\textbf{parameter} & \textbf{value} \\", footer=True) + r"""\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}\\
""" + repeated_header(r"\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]", footer=True) + lc_rows_str.rstrip().removesuffix(r"\hline") + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


