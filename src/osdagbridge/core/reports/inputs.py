"""Resolve recorded report inputs and report data availability without rerunning design."""

import ast
from collections.abc import Mapping

from osdagbridge.core.utils import common as keys

from .report_utils import _finite_number


def design_lane_count(inputs):
    """Resolve the configured lane count or derive it from the carriageway width using IRC 6."""
    lanes = _finite_number(inputs.get(keys.KEY_WC_LD_LANE_TABLE_COUNT))
    if lanes is not None and lanes > 0 and lanes.is_integer():
        return int(lanes)
    width = _finite_number(inputs.get(keys.KEY_CARRIAGEWAY_WIDTH))
    if width is not None and width > 0:
        from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

        return IRC6_2017.table_6(width)
    return None


def _location(value):
    if isinstance(value, str) and value.lstrip().startswith("{"):
        try:
            value = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return {}
    return value if isinstance(value, Mapping) else {}


def prepare_report_inputs(inputs, outputs, display_location):
    values = dict(inputs)
    # Display metadata can be a free-form label while project.location holds the design data.
    location = _location(values.get(keys.KEY_PROJECT_LOCATION)) or _location(display_location)
    coordinates = _location(location.get("data"))
    weather = _location(location.get("weather_data"))
    for k, value in {
        "latitude": coordinates.get("latitude", weather.get("latitude")),
        "longitude": coordinates.get("longitude", weather.get("longitude")),
        "seismic_zone": values.get(keys.KEY_SL_SEISMIC_ZONE) or weather.get("zone"),
        "wind_speed": weather.get("wind_speed"),
        "shade_temp_max": values.get(keys.KEY_TL_HIGHEST_MAX_TEMP, weather.get("max_temp")),
        "shade_temp_min": values.get(keys.KEY_TL_LOWEST_MIN_TEMP, weather.get("min_temp")),
    }.items():
        if values.get(k) in (None, ""):
            values[k] = value

    stored_keys = (
        keys.KEY_TL_BRIDGE_TEMP_MIN, keys.KEY_TL_BRIDGE_TEMP_MAX,
        keys.KEY_TL_TEMP_RISE, keys.KEY_TL_TEMP_FALL,
    )
    for key in stored_keys:
        if key in outputs:
            values[key] = outputs[key]
    actual = outputs.get("environmental_load_results") or {}
    values.update(actual)
    missing = []
    invalid = []
    for key, label in (
        ("latitude", "latitude"), ("longitude", "longitude"),
        ("seismic_zone", "seismic zone"), ("wind_speed", "site basic wind speed"),
        ("shade_temp_min", "minimum shade temperature"), ("shade_temp_max", "maximum shade temperature"),
    ):
        value = values.get(key)
        if value in (None, ""):
            missing.append(label)
        elif key != "seismic_zone":
            number = _finite_number(value)
            limit = {"latitude": 90, "longitude": 180}.get(key)
            if number is None or (limit is not None and abs(number) > limit):
                invalid.append(label)
                values[key] = "Calculation failed"

    warnings = []
    if missing:
        warnings.append("Not provided: " + ", ".join(missing) + ".")
    if invalid:
        warnings.append("Invalid recorded inputs: " + ", ".join(invalid) + ".")
    if "wind_force_transverse_kN" not in actual or "seismic_force_transverse_kN" not in actual:
        warnings.append("Wind or seismic force results were not recorded in this design snapshot.")
    if actual.get("wind_used_default"):
        warnings.append("Wind analysis used the software default of 33 m/s. Site wind data may differ.")
    site_speed = _finite_number(values.get("wind_speed"))
    used_speed = _finite_number(actual.get("wind_speed_used"))
    if site_speed is not None and used_speed is not None and site_speed != used_speed:
        warnings.append(f"Site wind speed is {site_speed:g} m/s and the analysis used {used_speed:g} m/s.")
    if actual.get("seismic_used_default"):
        warnings.append("Seismic analysis used the software default zone factor Z = 0.10. Check against site data.")
    values["report_input_warnings"] = warnings
    return values
