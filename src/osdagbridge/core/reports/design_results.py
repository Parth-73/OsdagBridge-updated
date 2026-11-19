"""Structured engineering evidence shared by the report sections."""

from dataclasses import dataclass
from enum import Enum

from osdagbridge.core.utils import common as keys

from .report_utils import _finite_number


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT EVALUATED"
    NOT_APPLICABLE = "NOT APPLICABLE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DesignCheck:
    component: str
    member: str
    name: str
    combination: str | None
    demand: float | None
    capacity: float | None
    ratio: float | None
    status: Status
    unit: str
    capacity_unit: str
    clause: str
    source: str
    mandatory: bool = True
    check_id: int | None = None


def _check(component, member, name, *, combination=None, demand=None, capacity=None,
           ratio=None, status=None, unit="", capacity_unit=None, clause="", source,
           limits_use_ratio=False, mandatory=True, check_id=None):
    actual = _finite_number(demand)
    limit = _finite_number(capacity)
    ur = _finite_number(ratio)
    raw = str(status or "").strip().upper().replace("_", " ")
    if raw in {"N/A", "NOT APPLICABLE", "SKIPPED"}:
        result = Status.NOT_APPLICABLE
    elif raw == "ERROR" or (ratio is not None and (ur is None or ur < 0)) or (
        limits_use_ratio and capacity is not None and (limit is None or limit <= 0)
    ):
        result = Status.ERROR
        ur = None
    elif "FAIL" in raw or (ur is not None and ur > 1 and limits_use_ratio):
        result = Status.FAIL
    elif ur is not None and (limits_use_ratio or raw in {"PASS", "WARN", "WARNING"}):
        result = Status.PASS
    elif status is True:
        result = Status.PASS
    elif status is False:
        result = Status.FAIL
    else:
        result = Status.NOT_EVALUATED
    return DesignCheck(component, member, name, combination, actual, limit, ur, result,
                       unit, unit if capacity_unit is None else capacity_unit, clause, source, mandatory, check_id)


DEFLECTION_CRITERIA = (
    ("Live-load deflection", keys.KEY_SD_DEFL_LIVE, "1.0 LL", 800),
    ("Total-load deflection", keys.KEY_SD_DEFL_TOTAL, "1.0 DL + 1.0 LL", 600),
)


def grillage_deflections(inputs, outputs):
    """Maximum absolute nodal displacement in the selected unfactored cases."""
    span = _finite_number(inputs.get(keys.KEY_SPAN))
    count = int(_finite_number(inputs.get(keys.KEY_TS_NO_OF_GIRDERS)) or 0)
    cases = outputs.get("report_deflection_cases") or {}
    for girder in range(1, count + 1):
        member = f"G{girder}"
        for name, key, legacy_case, divisor in DEFLECTION_CRITERIA:
            value = outputs.get(f"{key}.{member}")
            demand = _finite_number(value)
            capacity = span * 1000 / divisor if span and span > 0 else None
            yield _check(
                "Plate Girder", member, name, combination=cases.get(key) or (legacy_case if key not in cases else None),
                demand=demand, capacity=capacity,
                ratio=abs(demand) / capacity if demand is not None and capacity else None,
                status="ERROR" if value is not None and demand is None else None,
                unit="mm", clause=f"IRC 22 Cl.604.3.2 (L/{divisor})",
                source="Grillage nodal displacement cache", limits_use_ratio=True,
            )


def governing(checks):
    """Prefer failures, then the highest valid utilization within that status."""
    order = {Status.FAIL: 4, Status.ERROR: 3, Status.NOT_EVALUATED: 2,
             Status.PASS: 1, Status.NOT_APPLICABLE: 0}
    return max(checks, key=lambda c: (order[c.status], c.ratio is not None, c.ratio or 0), default=None)


def aggregate_status(checks):
    checks = [check for check in checks if check.mandatory]
    statuses = {check.status for check in checks}
    for status in (Status.FAIL, Status.ERROR, Status.NOT_EVALUATED, Status.PASS):
        if status in statuses:
            return status
    return Status.NOT_APPLICABLE if checks else Status.NOT_EVALUATED


def girder_design_checks(outputs):
    results = (outputs.get("design_results") or {}).get("per_girder") or {}
    for member, data in results.items():
        if str(member).startswith("EB"):
            continue
        by_id = {}
        envelope = {row.get("check_id"): row for row in data.get("checks") or []}
        sources = [("Designer envelope", None, envelope.values())]
        sources.extend(
            ("Designer per-load-case", case, (entry.get("checks") or []))
            for case, entry in (data.get("per_lc") or {}).items()
            if not str(case).lower().startswith("envelope")
        )
        for source, case, rows in sources:
            for raw in rows:
                identifier = raw.get("check_id", raw.get("id"))
                if identifier is None and not (raw.get("name") or raw.get("label")):
                    continue
                ident = identifier if identifier is not None else (raw.get("name") or raw.get("label"))
                known = envelope.get(identifier, {})
                name = raw.get("name") or raw.get("label") or f"Check {identifier}"
                if identifier in (13, 14):
                    name += " (designer stiffness-adjusted)"
                row = _check(
                    "Plate Girder", member, name, combination=case,
                    demand=raw.get("demand"), capacity=raw.get("capacity"), ratio=raw.get("dcr"),
                    status=raw.get("status"), unit=raw.get("demand_unit") or known.get("demand_unit") or ("mm" if identifier in (13, 14) else ""),
                    capacity_unit=raw.get("capacity_unit") or known.get("capacity_unit") or None,
                    clause=raw.get("clause") or "", source=source, check_id=identifier,
                    limits_use_ratio=identifier in {1, 2, 5, 8, 9, 11, 13, 14},
                )
                previous = by_id.get(ident)
                if previous is None or governing((row, previous)) is row:
                    by_id[ident] = row
        for identifier, name in ((1, "ULS Flexure"), (2, "ULS Shear")):
            if identifier not in by_id:
                yield _check("Plate Girder", member, name, source="Girder designer", check_id=identifier)
        yield from by_id.values()


_DECK_RATIOS = {
    "bot_uls": "Sagging flexure", "top_uls": "Hogging flexure",
    "bot_sls_c": "Sagging concrete stress", "top_sls_c": "Hogging concrete stress",
    "bot_sls_s": "Sagging reinforcement stress", "top_sls_s": "Hogging reinforcement stress",
    "bot_crack": "Sagging crack width", "top_crack": "Hogging crack width",
    "bot_shear": "One-way shear", "bot_punch": "Punching shear",
    "oh_uls": "Overhang flexure", "oh_sls_c": "Overhang concrete stress",
    "oh_sls_s": "Overhang reinforcement stress", "oh_crack": "Overhang crack width",
    "oh_shear": "Overhang one-way shear", "oh_punch": "Overhang punching shear",
    "composite_trans_shear": "Composite transverse shear", "composite_crack": "Composite crack reinforcement",
    "composite_conc_stress": "Composite concrete stress", "composite_rebar_stress": "Composite reinforcement stress",
}


def deck_detail_checks(values):
    """Use the same required/provided criteria as the detailed reinforcement table."""
    provided = _finite_number(values.get(keys.KEY_DD_AS_BOT))
    minimum = _finite_number(values.get(keys.KEY_DD_AS_MIN))
    distribution_limit = max(0.20 * provided, minimum) if provided is not None and minimum is not None else None
    for name, demand_key, limit, unit, lower_bound in (
        ("Bottom reinforcement area", keys.KEY_DD_AS_BOT, values.get(keys.KEY_DD_AS_REQ_BOT), "mm2/m", True),
        ("Minimum reinforcement area", keys.KEY_DD_AS_BOT, minimum, "mm2/m", True),
        ("Maximum bar spacing", keys.KEY_DD_SPC_BOT, values.get(keys.KEY_DD_SPACING_MAX), "mm", False),
        ("Distribution reinforcement area", keys.KEY_DD_AS_LONG, distribution_limit, "mm2/m", True),
        ("Top reinforcement area", keys.KEY_DD_AS_TOP, values.get(keys.KEY_DD_AS_REQ_TOP), "mm2/m", True),
    ):
        demand = _finite_number(values.get(demand_key))
        limit = _finite_number(limit)
        status = None
        if demand is not None and limit is not None:
            status = demand >= limit if lower_bound else 0 < demand <= limit
        yield _check("Deck Slab", "Deck slab", name, demand=demand, capacity=limit,
                     unit=unit, status=status, source="Deck reinforcement detailing")


def deck_design_checks(outputs):
    deck = outputs.get("deck_design_results") or {}
    values = outputs.get("deck_report_values") or {}
    measured = {
        "bot_uls": (keys.KEY_DD_M_ULS_SAG, keys.KEY_DD_MU_BOT, "kN-m/m", "Basic ULS"),
        "top_uls": (keys.KEY_DD_M_ULS_HOG, keys.KEY_DD_MU_TOP, "kN-m/m", "Basic ULS"),
        "oh_uls": (keys.KEY_DD_M_ULS_OH, keys.KEY_DD_MU_OH, "kN-m/m", "Basic ULS"),
        "bot_shear": (keys.KEY_DD_SHEAR_VED, keys.KEY_DD_SHEAR_VRDC, "kN/m", "Basic ULS"),
        "bot_punch": (keys.KEY_DD_PUNCH_VED, keys.KEY_DD_VRD_C_MPA, "MPa", "Basic ULS"),
        "bot_crack": (keys.KEY_DD_WK_BOT, keys.KEY_DD_WK_LIMIT, "mm", "Frequent SLS"),
        "top_crack": (keys.KEY_DD_WK_TOP, keys.KEY_DD_WK_LIMIT, "mm", "Frequent SLS"),
        "oh_crack": (keys.KEY_DD_WK_OH, keys.KEY_DD_WK_LIMIT, "mm", "Frequent SLS"),
    }
    for key, name in _DECK_RATIOS.items():
        if key.startswith("oh_") and values.get(keys.KEY_DD_HAS_OVERHANG) is False:
            continue
        ratio_key = f"ur_{key}"
        if ratio_key not in deck and key not in measured:
            continue
        demand_key, capacity_key, unit, case = measured.get(key, (None, None, "", None))
        demand, capacity = values.get(demand_key), values.get(capacity_key)
        ratio = deck.get(ratio_key)
        # The legacy designer uses 9.999 as an invalid-resistance sentinel.
        invalid = ratio == 9.999 and not (_finite_number(capacity) or 0) > 0
        yield _check("Deck Slab", "Deck slab", name, ratio=None if invalid else ratio,
                     status="ERROR" if invalid else None, demand=demand, capacity=capacity,
                     unit=unit, combination=case, limits_use_ratio=True,
                     source=f"Deck designer ({ratio_key})")
    yield from deck_detail_checks(values)
    if not deck:
        yield _check("Deck Slab", "Deck slab", "Deck design results unavailable", source="Deck designer")
    for key, name in (
        (keys.KEY_DD_COVER_OK, "Minimum concrete cover"),
        (keys.KEY_DD_PUNCH_OK, "Punching shear resistance"),
        (keys.KEY_DD_SHEAR_OK, "One-way shear resistance"),
    ):
        yield _check("Deck Slab", "Deck slab", name, status=values.get(key),
                     source=f"Deck report values ({key})")


def transverse_checks(outputs, component, design_key, force_key):
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    forces = (outputs.get(force_key) or {}).get("pairs") or {}
    designs = outputs.get(design_key) or {}
    for pair in sorted(forces.keys() | designs.keys()):
        pair_forces = forces.get(pair) or {}
        pair_designs = designs.get(pair) or {}
        for member, prefix in (("diagonal", "diag"), ("chord", "chord")):
            for direction in ("compression", "tension"):
                stem = f"{prefix}_{direction}"
                demand = _finite_number(pair_forces.get(f"{stem}_kN"))
                raw = (pair_designs.get(member) or {}).get(direction)
                if raw is None and demand is None:
                    continue
                properties = _extract_osdag_summary(raw or {})
                yield _check(component, f"{pair} {member}", direction.capitalize(),
                             combination=pair_forces.get(f"{stem}_gov_lc"),
                             demand=abs(demand) if demand is not None else None,
                             capacity=properties.get("capacity_kN"), ratio=properties.get("efficiency"),
                             limits_use_ratio=True, unit="kN", source=design_key)


COMPONENTS = ("Plate Girder", "Deck Slab", "Cross Bracing", "End Diaphragm")


def collect_design_checks(inputs, outputs):
    groups = [
        list(girder_design_checks(outputs)),
        list(deck_design_checks(outputs)),
        list(transverse_checks(outputs, COMPONENTS[2], "crossbracing_design_results", "crossbracing_forces_dict")),
        list(transverse_checks(outputs, COMPONENTS[3], "end_diaphragm_design_results", "end_diaphragm_forces_dict")),
    ]
    if not groups[0]:
        groups[0].append(_check(COMPONENTS[0], COMPONENTS[0], "Girder design results unavailable",
                                source="Girder designer"))
    groups[0].extend(grillage_deflections(inputs, outputs))
    for component, checks in zip(COMPONENTS, groups):
        yield from checks
        if not checks or all(check.status == Status.NOT_APPLICABLE for check in checks):
            yield _check(component, component, "Design results unavailable", source="Design output")
